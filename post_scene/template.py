import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from ruamel.yaml import YAML

from post_scene.api_document import load_api_document


SUPPORTED_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}
LOGIN_KEYWORDS = ("登录", "登陆", "login", "signin", "auth")
USER_KEYWORDS = ("用户", "user", "profile", "member")
SEARCH_KEYWORDS = ("搜索", "查询", "列表", "search", "list", "query", "get")
ORDER_KEYWORDS = ("订单", "order")
PRODUCT_KEYWORDS = ("商品", "goods", "product", "sku")
CANTEEN_KEYWORDS = ("餐厅", "canteen", "restaurant", "shop", "store")
CART_KEYWORDS = ("购物车", "cart", "pocket", "basket")
PAY_KEYWORDS = ("支付", "结算", "pay", "settle", "checkout")


def load_postman_collection(path: Path) -> Dict[str, Any]:
    return load_api_document(str(path))


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


def get_request_path(request: Dict[str, Any]) -> str:
    url = request.get("url") or {}
    if isinstance(url, str):
        return url
    raw = url.get("raw")
    if raw:
        return str(raw)
    path = url.get("path") or []
    return "/" + "/".join(str(part) for part in path)


def item_text(item: Dict[str, Any]) -> str:
    request = item.get("request") or {}
    return f"{item.get('name', '')} {get_request_path(request)}".lower()


def has_any(text: str, keywords: tuple) -> bool:
    return any(keyword.lower() in text for keyword in keywords)


def item_params(item: Dict[str, Any]) -> Dict[str, Any]:
    request = item.get("request") or {}
    params = {}
    params.update(extract_query_values(request))
    params.update(extract_body_values(request))
    return params


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


def first_matching(items: List[Dict[str, Any]], keywords: tuple) -> Optional[Dict[str, Any]]:
    for item in items:
        if has_any(item_text(item), keywords):
            return item
    return None


def matching_items(items: List[Dict[str, Any]], *keyword_groups: tuple) -> List[Dict[str, Any]]:
    matches = []
    for item in items:
        text = item_text(item)
        if all(has_any(text, group) for group in keyword_groups):
            matches.append(item)
    return matches


def unique_items(items: Iterable[Optional[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    seen = set()
    unique = []
    for item in items:
        if not item:
            continue
        key = id(item)
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def build_smart_step(item: Dict[str, Any]) -> Dict[str, Any]:
    name = item["name"]
    text = item_text(item)
    params = item_params(item)
    step = build_step(item, include_params=True)
    body = step[name]

    if has_any(text, LOGIN_KEYWORDS):
        body["tests"] = {
            "assert": {
                "express": {
                    "content": "$json.code === '1'",
                    "set": {
                        "token": "$json.data.token",
                        "uid": "$json.data.uid",
                    },
                }
            }
        }
    elif has_any(text, ORDER_KEYWORDS) and has_any(text, ("已支付", "paid")):
        body["tests"] = {
            "assert": {
                "status": 200,
                "expect": {
                    "content": "$json.data.orders",
                    "item": "$it.status",
                    "eql": 1,
                },
            }
        }
    elif has_any(text, ORDER_KEYWORDS) and has_any(text, ("未支付", "unpaid")):
        body["tests"] = {
            "assert": {
                "status": 200,
                "expect": {
                    "content": "$json.data.orders",
                    "item": "$it.status",
                    "eql": 0,
                },
            }
        }
    elif "orderId" in params and has_any(text, PAY_KEYWORDS):
        body.setdefault("pre", {})["ref"] = "orderId"
        body["tests"] = {"assert": {"express": "$json.code === '1'"}}
    elif has_any(text, ORDER_KEYWORDS) and has_any(text, PAY_KEYWORDS):
        body.setdefault("pre", {})["ref"] = "pocketId"
        body["tests"] = {
            "assert": {
                "express": {
                    "content": "$json.code === '1'",
                    "set": {
                        "orderId": "$json.data.orderId",
                    },
                }
            }
        }
    elif has_any(text, PAY_KEYWORDS):
        body.setdefault("pre", {})["ref"] = "orderId"
        body["tests"] = {"assert": {"express": "$json.code === '1'"}}
    elif has_any(text, CART_KEYWORDS):
        body.setdefault("pre", {})["ref"] = "goodsId"
        body["tests"] = {
            "assert": {
                "express": {
                    "content": "$json.code === '1'",
                    "set": {
                        "pocketId": "$json.data.pocketId",
                    },
                }
            }
        }
    elif has_any(text, SEARCH_KEYWORDS) and has_any(text, PRODUCT_KEYWORDS):
        include_value = params.get("goodsName") or params.get("productName") or params.get("name") or "TODO"
        if has_any(text, CANTEEN_KEYWORDS) or "canteenId" in params:
            body.setdefault("pre", {})["ref"] = "canteenId"
        body["tests"] = {
            "assert": {
                "expect": {
                    "content": "$json.data.goodsList",
                    "item": "$it.name",
                    "include": include_value,
                    "set": {
                        "goodsId": "$$find(json.data.goodsList, it.name == '{}').goodsId".format(include_value),
                    },
                }
            }
        }
    elif has_any(text, SEARCH_KEYWORDS) and has_any(text, CANTEEN_KEYWORDS):
        include_value = params.get("canteenName") or params.get("name") or "TODO"
        body["tests"] = {
            "assert": {
                "expect": {
                    "content": "$json.data.canteenList",
                    "item": "$it.name",
                    "include": include_value,
                    "set": {
                        "canteenId": "$$find(json.data.canteenList, it.name == '{}').canteenId".format(include_value),
                    },
                }
            }
        }
    return step


def build_suggested_template(
    collection: Dict[str, Any],
    name: Optional[str] = None,
    max_scenes: int = 3,
) -> Dict[str, Any]:
    collection_name = collection.get("info", {}).get("name") or "postman"
    items = list(iter_request_items(collection.get("item") or []))
    login = first_matching(items, LOGIN_KEYWORDS)
    user = first_matching(matching_items(items, USER_KEYWORDS), SEARCH_KEYWORDS) or first_matching(items, USER_KEYWORDS)
    canteen_search = first_matching(matching_items(items, CANTEEN_KEYWORDS), SEARCH_KEYWORDS)
    product_search = first_matching(matching_items(items, PRODUCT_KEYWORDS), SEARCH_KEYWORDS)
    cart = first_matching(items, CART_KEYWORDS)
    order_settle = first_matching(matching_items(items, ORDER_KEYWORDS), PAY_KEYWORDS)
    pay = first_matching([item for item in matching_items(items, PAY_KEYWORDS) if item is not order_settle], PAY_KEYWORDS)
    paid_order = first_matching(matching_items(items, ORDER_KEYWORDS), ("已支付", "paid"))
    unpaid_order = first_matching(matching_items(items, ORDER_KEYWORDS), ("未支付", "unpaid"))
    search_items = matching_items(items, SEARCH_KEYWORDS)

    candidates = [
        ("登录与用户信息", unique_items([login, user])),
        ("下单流程", unique_items([login, canteen_search, product_search, cart, order_settle, pay, paid_order, unpaid_order])),
        ("查询流程", unique_items(([login] if login else []) + search_items[:5])),
    ]
    scenes = []
    for scene_name, scene_items in candidates:
        if not scene_items:
            continue
        scenes.append({
            "name": scene_name,
            "scene": [build_smart_step(item) for item in scene_items],
        })
        if len(scenes) >= max_scenes:
            break

    if not scenes:
        scenes = build_template(collection, name=name, scene_name="默认接口流程")["scene"]

    return {
        "name": name or f"{collection_name}-suggested-scenes",
        "scene": scenes,
    }


def write_yaml_template(template: Dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    yaml = YAML()
    yaml.default_flow_style = False
    yaml.width = 4096
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


def build_suggest_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="postscene-suggest",
        description="根据 Postman Collection 推荐 PostScene YAML 业务场景",
    )
    parser.add_argument("postman", type=Path, help="Postman collection JSON 文件路径")
    parser.add_argument("-o", "--output", type=Path, default=Path("suggested-scenes.yaml"), help="输出 YAML 路径")
    parser.add_argument("--name", help="模板 collection 名称")
    parser.add_argument("--max-scenes", type=int, default=3, help="最多生成多少个推荐场景")
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


def suggest_main(argv: Optional[List[str]] = None) -> int:
    args = build_suggest_parser().parse_args(argv)
    try:
        collection = load_postman_collection(args.postman)
        template = build_suggested_template(collection, name=args.name, max_scenes=args.max_scenes)
        write_yaml_template(template, args.output)
    except Exception as exc:
        print(f"推荐场景生成失败：{exc}", file=sys.stderr)
        return 2
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
