import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from ruamel.yaml import YAML


SUPPORTED_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}


def load_postman_collection(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_request_items(items: Iterable[Dict[str, Any]]) -> Iterable[Dict[str, Any]]:
    for item in items:
        if "item" in item:
            yield from iter_request_items(item.get("item") or [])
        elif "request" in item and "name" in item:
            yield item


def extract_body_values(request: Dict[str, Any]) -> Dict[str, Any]:
    body = request.get("body") or {}
    mode = body.get("mode")
    if mode == "raw":
        raw = body.get("raw") or ""
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return flatten_json_values(parsed)
    if mode in {"formdata", "urlencoded"}:
        values = {}
        for param in body.get(mode) or []:
            key = param.get("key")
            if key:
                values[key] = param.get("value", "")
        return values
    return {}


def extract_query_values(request: Dict[str, Any]) -> Dict[str, Any]:
    url = request.get("url") or {}
    values = {}
    for param in url.get("query") or []:
        key = param.get("key")
        if key:
            values[key] = param.get("value", "")
    return values


def flatten_json_values(data: Any, prefix: str = "") -> Dict[str, Any]:
    if isinstance(data, dict):
        values = {}
        for key, value in data.items():
            name = f"{prefix}.{key}" if prefix else key
            values.update(flatten_json_values(value, name))
        return values
    if isinstance(data, list):
        values = {}
        for index, value in enumerate(data):
            name = f"{prefix}[{index}]"
            values.update(flatten_json_values(value, name))
        return values
    return {prefix: data} if prefix else {}


def build_step(item: Dict[str, Any], include_params: bool = True) -> Dict[str, Any]:
    request = item.get("request") or {}
    method = str(request.get("method") or "GET").upper()
    step_body: Dict[str, Any] = {
        "tests": {
            "assert": {
                "status": 200,
            }
        }
    }
    if include_params:
        params = {}
        params.update(extract_query_values(request))
        params.update(extract_body_values(request))
        if params:
            step_body["pre"] = {"set": params}
    if method not in SUPPORTED_METHODS:
        step_body.setdefault("pre", {})["code"] = f"// TODO: check unsupported method {method}"
    return {item["name"]: step_body}


def build_template(
    collection: Dict[str, Any],
    name: Optional[str] = None,
    scene_name: str = "默认接口流程",
    include_params: bool = True,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    collection_name = collection.get("info", {}).get("name") or "postman"
    items = list(iter_request_items(collection.get("item") or []))
    if limit is not None:
        items = items[:limit]
    return {
        "name": name or f"{collection_name}-scene-template",
        "scene": [{
            "name": scene_name,
            "scene": [build_step(item, include_params) for item in items],
        }],
    }


def write_yaml_template(template: Dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    yaml = YAML()
    yaml.default_flow_style = False
    yaml.indent(mapping=2, sequence=4, offset=2)
    with output_path.open("w", encoding="utf-8") as file:
        yaml.dump(template, file)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="postscene-template",
        description="根据 Postman Collection 生成 PostScene YAML 场景模板",
    )
    parser.add_argument("postman", type=Path, help="Postman collection JSON 文件路径")
    parser.add_argument("-o", "--output", type=Path, default=Path("scene-template.yaml"), help="输出 YAML 路径")
    parser.add_argument("--name", help="模板 collection 名称")
    parser.add_argument("--scene-name", default="默认接口流程", help="默认场景名称")
    parser.add_argument("--no-params", action="store_true", help="不从请求参数生成 pre.set")
    parser.add_argument("--limit", type=int, help="最多生成多少个接口步骤")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        collection = load_postman_collection(args.postman)
        template = build_template(
            collection,
            name=args.name,
            scene_name=args.scene_name,
            include_params=not args.no_params,
            limit=args.limit,
        )
        write_yaml_template(template, args.output)
    except Exception as exc:
        print(f"模板生成失败：{exc}", file=sys.stderr)
        return 2
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
