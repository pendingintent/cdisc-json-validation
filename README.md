# Validate USDM JSON file against USDM v3.x or v4.x schema #
This utility will validate a USDM JSON study design file against the USDM schema version 3.11.0 or 4.0.0

## To convert a YAML schema into JSON ##
```
/Users/dmoreland/projects/cdisc-json-validation/venv/bin/python convert.py schema/USDM_API_v3.11.0.yaml -o output.json
```

## To validate a USDM JSON file againt the schema ##
```
/Users/dmoreland/projects/cdisc-json-validation/venv/bin/python convert.py validate usdm-json/te.json
```