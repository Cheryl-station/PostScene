---
name: post-scene
description: Convert API scenario designs written in YAML or XMind into Postman Collection JSON using an existing Postman API document collection. Use when the user asks to generate Postman scenario collections, convert XMind/YAML API flows, validate PostScene scripts, or work with Postman interface automation scenarios.
---

# PostScene

Use this skill to help users recommend business-oriented YAML scenarios from Postman collections, draft simple YAML templates, then turn YAML or XMind API scenario designs into Postman Collection files.

## Workflow

1. Identify the Postman API document source: a local collection JSON file or a Postman share URL.
2. If the user asks for a useful first draft, generate recommended business scenarios with `scripts/postscene_suggest.py`.
3. If the user asks only for a neutral skeleton, generate a simple YAML template with `scripts/postscene_template.py`.
4. Help the user adjust the generated YAML scenario order, parameters, assertions, variable extraction, and `ref` links.
5. Before converting, lint the YAML against the Postman collection with `scripts/postscene_lint.py`.
6. When a scenario script is valid enough to proceed, convert it with `scripts/postscene.py`.
7. Choose an output directory, defaulting to `./scene` when the user does not specify one.
8. After conversion, tell the user the generated collection path and any warnings or errors.

## Recommend Business Scenarios

Generate a useful YAML draft from an existing Postman collection:

```bash
python /path/to/post-scene/scripts/postscene_suggest.py \
  path/to/postman_collection.json \
  -o path/to/suggested-scenes.yaml
```

Limit the number of recommended scenarios:

```bash
python /path/to/post-scene/scripts/postscene_suggest.py \
  path/to/postman_collection.json \
  -o path/to/suggested-scenes.yaml \
  --max-scenes 2
```

The recommended YAML tries to identify login, user info, search, cart, order, and payment APIs from interface names and URL paths. It adds common assertions, token/uid extraction for login, and `ref` links such as `canteenId`, `goodsId`, `pocketId`, and `orderId` when the flow can be inferred. Treat the result as an editable first draft, not a guaranteed final test design.

## Lint A Scenario

Check a YAML scenario before converting it:

```bash
python /path/to/post-scene/scripts/postscene_lint.py \
  path/to/scene.yaml \
  path/to/postman_collection.json
```

Use strict mode in CI or before final conversion:

```bash
python /path/to/post-scene/scripts/postscene_lint.py \
  path/to/scene.yaml \
  path/to/postman_collection.json \
  --strict
```

The linter checks whether YAML step names exist in the Postman collection, whether `ref` variables were saved by earlier steps, whether `next.requestName` points to a known YAML step, and whether assertion types are recognized. Warnings mean the file may still convert but needs review; errors should be fixed first.

## Generate A YAML Template

Generate a starter scenario file from an existing Postman collection:

```bash
python /path/to/post-scene/scripts/postscene_template.py \
  path/to/postman_collection.json \
  -o path/to/scene-template.yaml
```

Limit the number of generated steps for a focused draft:

```bash
python /path/to/post-scene/scripts/postscene_template.py \
  path/to/postman_collection.json \
  -o path/to/login-flow.yaml \
  --scene-name "登录流程" \
  --limit 5
```

The generated YAML uses Postman item names as step names, adds a default `status: 200` assertion, and fills `pre.set` from query, form, urlencoded, and JSON body parameters when possible.

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
