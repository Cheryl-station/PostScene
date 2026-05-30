import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

from post_scene.lint import format_issues, lint_script
from post_scene.post_scene import PostScene
from post_scene.template import build_suggested_template, load_postman_collection, write_yaml_template


def run_auto(
    postman_path: Path,
    out_dir: Path,
    yaml_output: Optional[Path] = None,
    report_output: Optional[Path] = None,
    max_scenes: int = 3,
    strict: bool = False,
) -> Dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    yaml_path = yaml_output or out_dir / "suggested-scenes.yaml"
    report_path = report_output or out_dir / "postscene-auto-report.json"

    collection = load_postman_collection(postman_path)
    template = build_suggested_template(collection, max_scenes=max_scenes)
    write_yaml_template(template, yaml_path)

    issues = lint_script(yaml_path, postman_path)
    has_error = any(issue["level"] == "error" for issue in issues)
    has_warning = any(issue["level"] == "warning" for issue in issues)

    generated_collection = None
    if not has_error and not (strict and has_warning):
        generated_collection = PostScene.convert(str(yaml_path), str(postman_path), scene_dirs=str(out_dir))

    report = {
        "postman_file": str(postman_path),
        "yaml_file": str(yaml_path),
        "collection_file": generated_collection,
        "report_file": str(report_path),
        "max_scenes": max_scenes,
        "strict": strict,
        "issues": issues,
        "status": "converted" if generated_collection else "blocked",
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="postscene-auto",
        description="根据 Postman Collection 推荐 YAML、校验并转换为 Postman 场景 Collection",
    )
    parser.add_argument("postman", type=Path, help="Postman collection JSON 文件路径")
    parser.add_argument("-o", "--out-dir", type=Path, default=Path("scene"), help="输出目录")
    parser.add_argument("--yaml-output", type=Path, help="推荐 YAML 输出路径")
    parser.add_argument("--report-output", type=Path, help="自动流程报告 JSON 输出路径")
    parser.add_argument("--max-scenes", type=int, default=3, help="最多生成多少个推荐场景")
    parser.add_argument("--strict", action="store_true", help="有 warning 时不执行转换")
    return parser


def print_report(report: Dict[str, object]) -> None:
    print(f"YAML 场景草稿：{report['yaml_file']}")
    if report["collection_file"]:
        print(f"Postman 场景集合：{report['collection_file']}")
    else:
        print("Postman 场景集合：未生成")
    print(f"自动流程报告：{report['report_file']}")
    print(format_issues(report["issues"]))


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = run_auto(
            args.postman,
            args.out_dir,
            yaml_output=args.yaml_output,
            report_output=args.report_output,
            max_scenes=args.max_scenes,
            strict=args.strict,
        )
    except Exception as exc:
        print(f"自动生成失败：{exc}", file=sys.stderr)
        return 2
    print_report(report)
    return 0 if report["collection_file"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
