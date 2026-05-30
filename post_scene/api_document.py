import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import requests
from ruamel.yaml import YAML


HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}


def load_api_document(source: str) -> Dict[str, Any]:
    if source.startswith("http"):
        response = requests.get(source, timeout=60)
        response.raise_for_status()
        data = response.json()
    else:
        path = Path(source)
        text = path.read_text(encoding="utf-8")
        if path.suffix.lower() in {".yaml", ".yml"}:
            data = YAML().load(text)
        else:
            data = json.loads(text)
    return normalize_to_postman_collection(data)


def normalize_to_postman_collection(data: Dict[str, Any]) -> Dict[str, Any]:
    if is_postman_collection(data):
        return data
    if is_openapi_document(data):
        return openapi_to_postman_collection(data)
    raise ValueError("暂不支持的接口文档格式：请提供 Postman Collection 或 OpenAPI/Swagger JSON/YAML")


def is_postman_collection(data: Dict[str, Any]) -> bool:
    return isinstance(data, dict) and "item" in data and "info" in data


def is_openapi_document(data: Dict[str, Any]) -> bool:
    return isinstance(data, dict) and "paths" in data and ("openapi" in data or "swagger" in data)


def openapi_to_postman_collection(data: Dict[str, Any]) -> Dict[str, Any]:
    info = data.get("info") or {}
    base_url = infer_base_url(data)
    items = []
    for path, path_item in (data.get("paths") or {}).items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            method_lower = method.lower()
            if method_lower not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            items.append(openapi_operation_to_postman_item(
                path,
                method_lower.upper(),
                operation,
                path_item.get("parameters") or [],
                base_url,
            ))
    return {
        "info": {
            "name": info.get("title") or "openapi",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "item": items,
    }


def infer_base_url(data: Dict[str, Any]) -> str:
    servers = data.get("servers") or []
    if servers and isinstance(servers[0], dict) and servers[0].get("url"):
        return str(servers[0]["url"]).rstrip("/")
    host = data.get("host")
    if host:
        schemes = data.get("schemes") or ["https"]
        base_path = str(data.get("basePath") or "").rstrip("/")
        return f"{schemes[0]}://{host}{base_path}"
    return "{{baseUrl}}"


def openapi_operation_to_postman_item(
    path: str,
    method: str,
    operation: Dict[str, Any],
    path_parameters: List[Dict[str, Any]],
    base_url: str,
) -> Dict[str, Any]:
    parameters = list(path_parameters) + list(operation.get("parameters") or [])
    query = []
    headers = []
    for parameter in parameters:
        if not isinstance(parameter, dict):
            continue
        target = query if parameter.get("in") == "query" else headers if parameter.get("in") == "header" else None
        if target is None:
            continue
        target.append({
            "key": parameter.get("name", ""),
            "value": example_value(parameter),
            "type": "text",
        })

    request: Dict[str, Any] = {
        "method": method,
        "header": headers,
        "url": build_postman_url(base_url, path, query),
    }
    body = build_request_body(operation)
    if body:
        request["body"] = body

    return {
        "name": operation_name(method, path, operation),
        "request": request,
        "response": [],
    }


def operation_name(method: str, path: str, operation: Dict[str, Any]) -> str:
    return operation.get("summary") or operation.get("operationId") or f"{method} {path}"


def build_postman_url(base_url: str, path: str, query: List[Dict[str, str]]) -> Dict[str, Any]:
    raw = f"{base_url}{path}"
    if query:
        raw += "?" + "&".join(f"{item['key']}={item['value']}" for item in query)
    return {
        "raw": raw,
        "query": query,
    }


def build_request_body(operation: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    request_body = operation.get("requestBody") or {}
    if not isinstance(request_body, dict):
        return None
    content = request_body.get("content") or {}
    json_media = content.get("application/json") or content.get("*/*")
    if isinstance(json_media, dict):
        example = json_media.get("example")
        if example is None and isinstance(json_media.get("examples"), dict):
            first_example = next(iter(json_media["examples"].values()), {})
            example = first_example.get("value") if isinstance(first_example, dict) else None
        if example is None:
            example = schema_example(json_media.get("schema") or {})
        return {
            "mode": "raw",
            "raw": json.dumps(example or {}, ensure_ascii=False, indent=2),
            "options": {
                "raw": {
                    "language": "json",
                }
            },
        }
    form_media = content.get("multipart/form-data") or content.get("application/x-www-form-urlencoded")
    if isinstance(form_media, dict):
        schema = form_media.get("schema") or {}
        properties = schema.get("properties") or {}
        mode = "formdata" if "multipart/form-data" in content else "urlencoded"
        return {
            "mode": mode,
            mode: [
                {"key": name, "value": schema_example(prop), "type": "text"}
                for name, prop in properties.items()
            ],
        }
    return None


def example_value(parameter: Dict[str, Any]) -> str:
    if "example" in parameter:
        return str(parameter["example"])
    schema = parameter.get("schema") or {}
    return str(schema_example(schema))


def schema_example(schema: Dict[str, Any]) -> Any:
    if not isinstance(schema, dict):
        return ""
    if "example" in schema:
        return schema["example"]
    if "default" in schema:
        return schema["default"]
    schema_type = schema.get("type")
    if schema_type == "integer":
        return 1
    if schema_type == "number":
        return 1
    if schema_type == "boolean":
        return True
    if schema_type == "array":
        return [schema_example(schema.get("items") or {})]
    if schema_type == "object" or "properties" in schema:
        return {
            name: schema_example(prop)
            for name, prop in (schema.get("properties") or {}).items()
        }
    return "example"
