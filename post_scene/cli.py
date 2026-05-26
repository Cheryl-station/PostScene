import argparse
import sys

from post_scene.post_scene import PostScene


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="postscene",
        description="将 Xmind/Yaml 场景脚本转换为 Postman Collection（json）",
    )
    p.add_argument(
        "script",
        help="脚本路径，支持 .yaml、.yml 或 .xmind",
    )
    p.add_argument(
        "postman",
        help="Postman collection 源数据（本地 json 路径或 share URL）",
    )
    p.add_argument(
        "-o",
        "--out-dir",
        default="./scene",
        help="输出目录（默认: ./scene）",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        out = PostScene.convert(args.script, args.postman, args.out_dir)
    except Exception as exc:
        print(f"生成失败：{exc}", file=sys.stderr)
        return 2
    if not out:
        print("生成失败：未能加载 Postman 源数据或脚本解析失败。", file=sys.stderr)
        return 2
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
