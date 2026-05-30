import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set

from ruamel.yaml import YAML

from post_scene.api_document import load_api_document
from post_scene.parser import Utils


SET_KEYS = {
    "set",
    "set-global",
    "set-env",
    "set-collect",
}
ASSERT_KEYS = {
    "status",
    "body",
    "jsonBody",
    "tobe",
    "notTobe",
    "tohave",
    "notTohave",
    "express",
    "expect",
    "header",
}


def load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = YAML().load(file)
    if not isinstance(data, dict):
        raise ValueError("YAML 根节点必须是对象")
    return data


def load_postman(path: Path) -> Dict[str, Any]:
    return load_api_document(str(path))


def iter_postman_names(items: Iterable[Dict[str, Any]]) -> Iterable[str]:
    for item in items:
        if "item" in item:
            yield from iter_postman_names(item.get("item") or [])
        elif "name" in item and "request" in item:
            yield item["name"]


def normalize_ref_names(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, dict):
        return [str(name) for name in value.values()]
    if isinstance(value, list):
        return [str(item) for item in value]
    return [name.strip() for name in str(value).split(",") if name.strip()]


def collect_set_names(data: Any) -> Set[str]:
    names = set()
    if isinstance(data, dict):
        for key, value in data.items():
            if key in SET_KEYS and isinstance(value, dict):
                names.update(str(name) for name in value.keys())
            else:
                names.update(collect_set_names(value))
    elif isinstance(data, list):
        for item in data:
            names.update(collect_set_names(item))
    return names


def collect_request_names(scenes: Any) -> Set[str]:
    names = set()
    if isinstance(scenes, list):
        for item in scenes:
            if isinstance(item, dict):
                if "name" in item and "scene" in item:
                    names.update(collect_request_names(item.get("scene")))
                else:
                    names.update(str(name) for name in item.keys())
    return names


def lint_step(
    name: str,
    body: Any,
    path: str,
    postman_names: Set[str],
    scene_request_names: Set[str],
    available_vars: Set[str],
) -> List[Dict[str, str]]:
    issues = []
    if name not in postman_names:
        issues.append({
            "level": "error",
            "path": path,
            "message": f"步骤名 `{name}` 在 Postman Collection 中不存在",
        })
    if not isinstance(body, dict):
        issues.append({
            "level": "error",
            "path": path,
            "message": "步骤内容必须是对象",
        })
        return issues

    pre = body.get("pre") or {}
    if pre and not isinstance(pre, dict):
        issues.append({
            "level": "error",
            "path": f"{path}.pre",
            "message": "pre 必须是对象",
        })
    elif isinstance(pre, dict):
        for ref_name in normalize_ref_names(pre.get("ref")):
            if ref_name not in available_vars:
                issues.append({
                    "level": "warning",
                    "path": f"{path}.pre.ref",
                    "message": f"引用变量 `{ref_name}` 之前没有在前置步骤中通过 set 保存",
                })

    tests = body.get("tests") or body.get("textTests")
    if tests is None:
        issues.append({
            "level": "warning",
            "path": path,
            "message": "步骤缺少 tests/textTests，生成后不会有断言脚本",
        })
    elif not isinstance(tests, dict):
        issues.append({
            "level": "error",
            "path": f"{path}.tests",
            "message": "tests/textTests 必须是对象",
        })
    else:
        assertion = tests.get("assert")
        if assertion is not None:
            issues.extend(lint_assertion(assertion, f"{path}.tests.assert"))
        next_data = tests.get("next")
        if next_data is not None:
            issues.extend(lint_next(next_data, f"{path}.tests.next", scene_request_names))

    return issues


def lint_assertion(assertion: Any, path: str) -> List[Dict[str, str]]:
    issues = []
    entries = assertion if isinstance(assertion, list) else [assertion]
    for index, entry in enumerate(entries):
        entry_path = f"{path}[{index}]" if isinstance(assertion, list) else path
        if not isinstance(entry, dict):
            issues.append({
                "level": "error",
                "path": entry_path,
                "message": "assert 条目必须是对象",
            })
            continue
        for key in entry:
            if key not in ASSERT_KEYS:
                issues.append({
                    "level": "warning",
                    "path": entry_path,
                    "message": f"未知断言类型 `{key}`",
                })
    return issues


def lint_next(next_data: Any, path: str, scene_request_names: Set[str]) -> List[Dict[str, str]]:
    issues = []
    entries = next_data if isinstance(next_data, list) else [next_data]
    for index, entry in enumerate(entries):
        entry_path = f"{path}[{index}]" if isinstance(next_data, list) else path
        case = entry.get("case") if isinstance(entry, dict) and "case" in entry else entry
        if not isinstance(case, dict):
            issues.append({
                "level": "error",
                "path": entry_path,
                "message": "next 必须是对象，或包含 case 的对象列表",
            })
            continue
        request_name = case.get("requestName")
        if request_name in (None, "$null"):
            continue
        if request_name not in scene_request_names:
            issues.append({
                "level": "warning",
                "path": f"{entry_path}.requestName",
                "message": f"next.requestName `{request_name}` 不在当前 YAML 场景步骤中",
            })
    return issues


def lint_scenes(
    scenes: Any,
    postman_names: Set[str],
    scene_request_names: Set[str],
    available_vars: Optional[Set[str]] = None,
    path: str = "scene",
) -> List[Dict[str, str]]:
    issues = []
    available_vars = available_vars or set()
    if not isinstance(scenes, list):
        return [{
            "level": "error",
            "path": path,
            "message": "scene 必须是列表",
        }]
    for index, item in enumerate(scenes):
        item_path = f"{path}[{index}]"
        if not isinstance(item, dict):
            issues.append({
                "level": "error",
                "path": item_path,
                "message": "scene 条目必须是对象",
            })
            continue
        if "name" in item and "scene" in item:
            folder_vars = set(available_vars)
            issues.extend(lint_scenes(
                item.get("scene"),
                postman_names,
                scene_request_names,
                folder_vars,
                f"{item_path}.scene",
            ))
            available_vars.update(folder_vars)
            continue
        for name, body in item.items():
            step_path = f"{item_path}.{name}"
            issues.extend(lint_step(name, body, step_path, postman_names, scene_request_names, available_vars))
            available_vars.update(collect_set_names(body))
    return issues


def lint_script(script_path: Path, postman_path: Path) -> List[Dict[str, str]]:
    script = load_yaml(script_path)
    postman = load_postman(postman_path)
    issues = []
    if "name" not in script:
        issues.append({"level": "error", "path": "name", "message": "缺少 name 字段"})
    if "scene" not in script:
        issues.append({"level": "error", "path": "scene", "message": "缺少 scene 字段"})
        return issues
    postman_names = set(iter_postman_names(postman.get("item") or []))
    scene_request_names = collect_request_names(script.get("scene"))
    issues.extend(lint_scenes(script.get("scene"), postman_names, scene_request_names))
    return issues


def format_issues(issues: List[Dict[str, str]]) -> str:
    if not issues:
        return "校验通过：未发现问题。"
    lines = []
    for issue in issues:
        lines.append(f"[{issue['level'].upper()}] {issue['path']}: {issue['message']}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="postscene-lint",
        description="校验 PostScene YAML 与 Postman Collection 是否匹配",
    )
    parser.add_argument("script", type=Path, help="PostScene YAML 场景脚本")
    parser.add_argument("postman", type=Path, help="Postman collection JSON 文件路径")
    parser.add_argument("--strict", action="store_true", help="有 warning 时也返回失败")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出校验结果")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        issues = lint_script(args.script, args.postman)
    except Exception as exc:
        print(f"校验失败：{exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({"issues": issues}, ensure_ascii=False, indent=2))
    else:
        print(format_issues(issues))

    has_error = any(issue["level"] == "error" for issue in issues)
    has_warning = any(issue["level"] == "warning" for issue in issues)
    return 1 if has_error or (args.strict and has_warning) else 0


if __name__ == "__main__":
    raise SystemExit(main())
