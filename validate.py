import bisect
import yaml
import json
import sys
import argparse
from pathlib import Path
import jsonschema
from jsonschema import exceptions as jsonschema_exceptions
import openpyxl
from openpyxl.styles import Font


def build_path_line_map(text):
    """Return a dict mapping JSON path tuples to line numbers.

    Walks the raw JSON text with a recursive descent parser so every
    object key and array element is associated with the line on which
    its value starts.
    """
    newline_offsets = [i for i, c in enumerate(text) if c == "\n"]

    def offset_to_line(offset):
        return bisect.bisect_right(newline_offsets, offset) + 1

    result = {}
    dec = json.JSONDecoder()

    def skip_ws(idx):
        while idx < len(text) and text[idx] in " \t\r\n":
            idx += 1
        return idx

    def parse(idx, path):
        idx = skip_ws(idx)
        if idx >= len(text):
            return idx
        result[tuple(path)] = offset_to_line(idx)
        c = text[idx]
        if c == "{":
            idx += 1
            first = True
            while True:
                idx = skip_ws(idx)
                if text[idx] == "}":
                    idx += 1
                    break
                if not first:
                    idx += 1  # consume ','
                first = False
                key, idx = dec.raw_decode(text, skip_ws(idx))
                idx = skip_ws(idx) + 1  # consume ':'
                idx = parse(idx, path + [key])
        elif c == "[":
            idx += 1
            i = 0
            first = True
            while True:
                idx = skip_ws(idx)
                if text[idx] == "]":
                    idx += 1
                    break
                if not first:
                    idx += 1  # consume ','
                first = False
                idx = parse(idx, path + [i])
                i += 1
        else:
            _, idx = dec.raw_decode(text, idx)
        return idx

    try:
        parse(0, [])
    except Exception:
        pass  # best-effort; missing entries fall back to None
    return result


def load_openapi_and_entry_schema(openapi_path, schema_name):
    with open(openapi_path, "r", encoding="utf-8") as f:
        if str(openapi_path).endswith((".yaml", ".yml")):
            openapi = yaml.safe_load(f)
        else:
            openapi = json.load(f)
    try:
        entry_schema = openapi["components"]["schemas"][schema_name]
        return openapi, entry_schema
    except KeyError:
        print(f"Schema '{schema_name}' not found in {openapi_path}")
        sys.exit(1)


def write_xlsx(errors, output_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Validation Errors"
    headers = ["Line Number", "Error Message", "Location in JSON", "Schema Path"]
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for line_no, message, location, schema_path in errors:
        ws.append([line_no, message, location, schema_path])
    ws.column_dimensions["A"].width = 12
    ws.column_dimensions["B"].width = 60
    ws.column_dimensions["C"].width = 50
    ws.column_dimensions["D"].width = 80
    wb.save(output_path)


def validate_json_with_schema(
    json_path, schema_path=None, openapi_doc=None, entry_schema=None, schema_name=None,
    output_file=None
):

    with open(json_path, "r", encoding="utf-8") as jf:
        json_text = jf.read()
    data = json.loads(json_text)
    path_line_map = build_path_line_map(json_text)

    def resolve_ref(schema):
        """If schema is a $ref, walk openapi_doc to return the referenced schema."""
        if not (isinstance(schema, dict) and "$ref" in schema):
            return schema
        ref = schema["$ref"]
        if not ref.startswith("#/"):
            return schema
        parts = ref[2:].split("/")
        node = openapi_doc
        for part in parts:
            node = node[part]
        return node

    def is_wrong_branch(error, instance_type):
        """Return True if this context error belongs to a different anyOf branch."""
        schema = resolve_ref(error.schema)
        # The branch-level required/properties schema has instanceType.const set
        it_const = schema.get("properties", {}).get("instanceType", {}).get("const")
        if it_const is not None and it_const != instance_type:
            return True
        # Discriminator const/enum failure: instanceType value rejected by the wrong branch
        if (error.validator in ("const", "enum")
                and error.absolute_path
                and error.absolute_path[-1] == "instanceType"):
            return True
        return False

    def discriminator_best_match(errors, instance):
        """Filter out wrong-branch errors using instanceType, then apply best_match."""
        errors = list(errors)
        if isinstance(instance, dict) and "instanceType" in instance:
            instance_type = instance["instanceType"]
            filtered = [e for e in errors if not is_wrong_branch(e, instance_type)]
            if filtered:
                return jsonschema_exceptions.best_match(filtered)
        return jsonschema_exceptions.best_match(errors)

    def collect_error(error):
        """Resolve anyOf/oneOf/allOf to a leaf error and return (line_no, message, location, schema_path)."""
        if error.context:
            best = discriminator_best_match(error.context, error.instance)
            return collect_error(best)
        path = list(error.absolute_path)
        location = "/".join(str(p) for p in path) if path else "<root>"
        spath = "/".join(str(p) for p in error.absolute_schema_path)
        line_no = path_line_map.get(tuple(path))
        return (line_no, error.message, location, spath)

    def run_validation(validator):
        try:
            raw_errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
        except jsonschema.SchemaError as se:
            print(f"Schema error: {se.message}")
            sys.exit(1)
        if not raw_errors:
            print(f"Validation successful: {json_path} is valid against {schema_name or schema_path}.")
            return
        collected = [collect_error(e) for e in raw_errors]
        for line_no, message, location, spath in collected:
            line_str = f"line {line_no}" if line_no else "line unknown"
            print(f"Validation failed ({line_str}): {message}")
            print(f"Location in JSON: {location}")
            print(f"Schema path: {spath}")
            print()
        print(f"{len(collected)} error(s) found.")
        if output_file:
            write_xlsx(collected, output_file)
            print(f"Errors written to {output_file}")
        sys.exit(1)

    if openapi_doc is not None and entry_schema is not None:
        schema_ref = {"$ref": f"#/components/schemas/{schema_name}"}
        resolver = jsonschema.RefResolver.from_schema(openapi_doc)
        validator = jsonschema.Draft7Validator(schema_ref, resolver=resolver)
        run_validation(validator)
    elif schema_path:
        with open(schema_path, "r", encoding="utf-8") as sf:
            if schema_path.endswith(".yaml") or schema_path.endswith(".yml"):
                schema = yaml.safe_load(sf)
            else:
                schema = json.load(sf)
        validator = jsonschema.Draft7Validator(schema)
        run_validation(validator)
    else:
        print("No schema provided for validation.")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Validate a JSON file against a USDM schema (v4 default).",
        epilog="""
Examples:
  python validate.py my_usdm.json --schema-version v3
  python validate.py my_usdm.json --schema-file schema/USDM_API_v4.0.0.json --schema-name Wrapper-Input

Usage notes:
  --schema-file allows you to specify any OpenAPI JSON or YAML schema file.
  --schema-name selects the schema object within the file (default: Wrapper-Input).
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "json_file", type=str, help="Path to the JSON file to validate."
    )
    parser.add_argument(
        "--schema-version",
        type=str,
        choices=["v3", "v4"],
        default="v4",
        help="USDM schema version to use (default: v4).",
    )
    parser.add_argument(
        "--schema-file",
        type=str,
        default=None,
        help="Path to the schema file (OpenAPI JSON/YAML). Overrides default if provided.",
    )
    parser.add_argument(
        "--schema-name",
        type=str,
        default="Wrapper-Input",
        help="Schema name to extract from OpenAPI (default: Wrapper-Input).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        metavar="FILE.xlsx",
        help="Write validation errors to an XLSX file.",
    )

    args = parser.parse_args()

    if args.schema_file:
        schema_file = args.schema_file
    elif args.schema_version == "v4":
        schema_file = "schema/USDM_API_v4.0.0.json"
    else:
        schema_file = "schema/USDM_API_v3.13.0.json"
    if (
        schema_file.endswith(".json")
        or schema_file.endswith(".yaml")
        or schema_file.endswith(".yml")
    ):
        openapi_doc, entry_schema = load_openapi_and_entry_schema(
            schema_file, args.schema_name
        )
        validate_json_with_schema(
            args.json_file,
            openapi_doc=openapi_doc,
            entry_schema=entry_schema,
            schema_name=args.schema_name,
            output_file=args.output,
        )
    else:
        validate_json_with_schema(args.json_file, schema_path=schema_file, output_file=args.output)
