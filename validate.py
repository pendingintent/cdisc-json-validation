import yaml
import json
import sys
import argparse
from pathlib import Path
import jsonschema


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


def validate_json_with_schema(
    json_path, schema_path=None, openapi_doc=None, entry_schema=None, schema_name=None
):

    with open(json_path, "r", encoding="utf-8") as jf:
        data = json.load(jf)

    def print_error_details(error):
        print(f"Validation failed: {error.message}")
        print(
            f"Location in JSON: {'/'.join(str(p) for p in error.absolute_path) if error.absolute_path else '<root>'}"
        )
        print(f"Schema path: {'/'.join(str(p) for p in error.absolute_schema_path)}")

    if openapi_doc is not None and entry_schema is not None:
        schema_ref = {"$ref": f"#/components/schemas/{schema_name}"}
        try:
            jsonschema.validate(
                instance=data,
                schema=schema_ref,
                resolver=jsonschema.RefResolver.from_schema(openapi_doc),
            )
            print(
                f"Validation successful: {json_path} is valid against {schema_name} in OpenAPI schema."
            )
        except jsonschema.ValidationError as ve:
            print_error_details(ve)
            sys.exit(1)
        except jsonschema.SchemaError as se:
            print(f"Schema error: {se.message}")
            sys.exit(1)
    elif schema_path:
        with open(schema_path, "r", encoding="utf-8") as sf:
            if schema_path.endswith(".yaml") or schema_path.endswith(".yml"):
                schema = yaml.safe_load(sf)
            else:
                schema = json.load(sf)
        try:
            jsonschema.validate(instance=data, schema=schema)
            print(f"Validation successful: {json_path} is valid against {schema_path}")
        except jsonschema.ValidationError as ve:
            print_error_details(ve)
            sys.exit(1)
        except jsonschema.SchemaError as se:
            print(f"Schema error: {se.message}")
            sys.exit(1)
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
        )
    else:
        validate_json_with_schema(args.json_file, schema_path=schema_file)
