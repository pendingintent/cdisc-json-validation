# Validate USDM JSON file against USDM v3.x or v4.x schema #
This utility will validate a USDM JSON study design file against the USDM schema version 3.11.0 or 4.0.0

## To convert a YAML schema into JSON ##
```
python convert.py schema/USDM_API_v3.11.0.yaml -o schema/USDM_API_v3.11.0.json
```

## To validate a USDM JSON file with the version 4.0.0 schema ##
```
python validate.py usdm-json/te.json
```

## To validate a USDM JSON file with the version 3.11.0 schema ##
```
python validate.py usdm-json/te.json --schema-version v3
```

## To validate against a specific schema file and schema name ##
```
python validate.py usdm-json/te.json --schema-file path/to/schema.json --schema-name Wrapper-Input
```

### Usage Note
You can use `--schema-file` to specify any OpenAPI JSON or YAML schema file, and `--schema-name` to select the schema object within that file. This allows validation against custom or alternate USDM schema files.

### Schema Files
All USDM API files contained in the schema directory are from the DDF github repository https://github.com/cdisc-org/DDF-RA


# Using Docker #
A docker compose file exists to create a Jupyter Lab environment.

From the ./cdisc-json-validation directory, run:
```
docker compose up --build
```

Accesss the Jupyter Lab environment
```
http://localhost:8888/lab?token=my-token
```