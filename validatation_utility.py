# Deprecated: Use validate.py


import yaml
import json
import sys
from pathlib import Path
import argparse


def load_openapi_and_entry_schema(openapi_path, schema_name):
    """
    Load the full OpenAPI document and return both the document and the entry schema (by reference).
    Args:
        openapi_path (str or Path): Path to the OpenAPI file.
        schema_name (str): Name of the schema to extract (e.g., 'Wrapper-Input').
    Returns:
        (dict, dict): (openapi_doc, entry_schema_dict)
    """
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
    """
    Validate a JSON file against a JSON schema or a schema extracted from OpenAPI.
    Args:
        json_path (str or Path): Path to the JSON file to validate.
        schema_path (str or Path, optional): Path to the JSON schema file (YAML or JSON).
        openapi_doc (dict, optional): Full OpenAPI document.
        entry_schema (dict, optional): Schema dict extracted from OpenAPI.
        schema_name (str, optional): Name of the schema (for error messages).
    Raises:
        SystemExit: If validation fails or files are not found.
    """
    import jsonschema

    with open(json_path, "r", encoding="utf-8") as jf:
        data = json.load(jf)
    if openapi_doc is not None and entry_schema is not None:
        # Use the full OpenAPI doc as the schema root, and validate against the entry schema
        # by using the $ref to the entry schema
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
            print(f"Validation failed: {ve.message}")
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
            print(f"Validation failed: {ve.message}")
            sys.exit(1)
        except jsonschema.SchemaError as se:
            print(f"Schema error: {se.message}")
            sys.exit(1)
    else:
        print("No schema provided for validation.")
        sys.exit(1)


def yaml_to_json(yaml_path, json_path=None):
    """
    Convert a YAML file to JSON format.
    Args:
        yaml_path (str or Path): Path to the input YAML file.
        json_path (str or Path, optional): Path to the output JSON file. If None, prints to stdout.
    """
    with open(yaml_path, "r", encoding="utf-8") as yf:
        data = yaml.safe_load(yf)
    if json_path:
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(data, jf, indent=2)
    else:
        print(json.dumps(data, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="YAML/JSON utilities: convert YAML to JSON or validate JSON against a schema."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subparser for conversion
    convert_parser = subparsers.add_parser(
        "convert", help="Convert a YAML file to JSON format."
    )
    convert_parser.add_argument(
        "yaml_file",
        type=str,
        help="Path to the input YAML file (e.g., schema/USDM_API_v3.11.0.yaml)",
    )
    convert_parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Path to the output JSON file. If not provided, prints to stdout.",
    )

    # Subparser for validation
    validate_parser = subparsers.add_parser(
        "validate", help="Validate a JSON file against a USDM schema (v4 default)."
    )
    validate_parser.add_argument(
        "json_file", type=str, help="Path to the JSON file to validate."
    )
    validate_parser.add_argument(
        "--schema-version",
        type=str,
        choices=["v3", "v4"],
        default="v4",
        help="USDM schema version to use (default: v4).",
    )
    validate_parser.add_argument(
        "--schema-file",
        type=str,
        default=None,
        help="Path to the schema file (OpenAPI JSON/YAML). Overrides default if provided.",
    )
    validate_parser.add_argument(
        "--schema-name",
        type=str,
        default="Wrapper-Input",
        help="Schema name to extract from OpenAPI (default: Wrapper-Input).",
    )

    args = parser.parse_args()

    if args.command == "convert":
        yaml_to_json(args.yaml_file, args.output)
    elif args.command == "validate":
        # Determine schema file path
        if args.schema_file:
            schema_file = args.schema_file
        elif args.schema_version == "v4":
            schema_file = "schema/USDM_API_v4.0.0.json"
        else:
            schema_file = "schema/USDM_API_v3.11.0.yaml"
        # If OpenAPI, use full doc and entry schema for $ref resolution
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
