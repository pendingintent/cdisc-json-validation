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
