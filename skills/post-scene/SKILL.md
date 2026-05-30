---
name: post-scene
description: Convert API scenario designs written in YAML or XMind into Postman Collection JSON using an existing Postman API document collection. Use when the user asks to generate Postman scenario collections, convert XMind/YAML API flows, validate PostScene scripts, or work with Postman interface automation scenarios.
---

# PostScene

Use this skill to help users turn YAML or XMind API scenario designs into Postman Collection files.

## Workflow

1. Identify the scenario script file: `.yaml`, `.yml`, or `.xmind`.
2. Identify the Postman API document source: a local collection JSON file or a Postman share URL.
3. Choose an output directory, defaulting to `./scene` when the user does not specify one.
4. Prefer the bundled `scripts/postscene.py` command for deterministic conversion.
5. After conversion, tell the user the generated collection path and any warnings or errors.

## Command Pattern

Run from the user's project directory:

```bash
python /path/to/post-scene/scripts/postscene.py \
  path/to/scenario.yaml \
  path/to/postman_collection.json \
  -o path/to/output-dir
```

XMind input works the same way:

```bash
python /path/to/post-scene/scripts/postscene.py \
  path/to/scenario.xmind \
  path/to/postman_collection.json \
  -o path/to/output-dir
```

Postman share URLs can be used as the second argument when available:

```bash
python /path/to/post-scene/scripts/postscene.py \
  path/to/scenario.yaml \
  "https://www.getpostman.com/collections/..." \
  -o path/to/output-dir
```

## Script Format Notes

- The top-level YAML should usually contain `name` and `scene`.
- Scenario step names must match interface names in the source Postman collection.
- Request setup belongs under `pre`; response checks belong under `tests`.
- Common `pre` fields include `set`, `ref`, and `sign`.
- Common assertion styles include `status`, `tobe`, `notTobe`, `tohave`, `notTohave`, `express`, and `expect`.
- Use built-in helper functions such as `$uuid32`, `$md5`, `$times`, `$dateFormat`, `$find`, and `$filter` when the scenario needs generated values.

## Dependencies

The bundled converter expects these Python packages:

```bash
pip install -r /path/to/post-scene/scripts/requirements.txt
```

If conversion fails with an import error, install the missing package and rerun the same command.

## Operating Notes

- Do not overwrite a user's original scenario script or Postman collection.
- If the generated collection is empty, check that scenario step names match the Postman collection item names.
- If the user only asks for help writing a scenario file, inspect their Postman collection first and produce YAML that uses matching interface names.
- Keep output paths explicit in the final response so the user can import the generated JSON into Postman.
