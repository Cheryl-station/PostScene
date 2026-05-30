import sys
from pathlib import Path

from ruamel.yaml import YAML

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from post_scene.lint import lint_script, main
from post_scene.template import build_suggested_template, load_postman_collection


DEMO_COLLECTION = ROOT_DIR / "src" / "api_document" / "demo.postman_collection.json"


def write_yaml(path: Path, data) -> None:
    yaml = YAML()
    with path.open("w", encoding="utf-8") as file:
        yaml.dump(data, file)


def test_lint_suggested_template_has_no_errors(tmp_path):
    collection = load_postman_collection(DEMO_COLLECTION)
    script = tmp_path / "suggested.yaml"
    write_yaml(script, build_suggested_template(collection, max_scenes=2))

    issues = lint_script(script, DEMO_COLLECTION)

    assert not [issue for issue in issues if issue["level"] == "error"]


def test_lint_reports_missing_postman_item_and_ref(tmp_path):
    script = tmp_path / "bad.yaml"
    write_yaml(script, {
        "name": "bad-scene",
        "scene": [{
            "name": "错误流程",
            "scene": [{
                "不存在的接口": {
                    "pre": {"ref": "token"},
                    "tests": {"assert": {"status": 200}},
                }
            }],
        }],
    })

    issues = lint_script(script, DEMO_COLLECTION)
    messages = [issue["message"] for issue in issues]

    assert any("在 Postman Collection 中不存在" in message for message in messages)
    assert any("之前没有在前置步骤中通过 set 保存" in message for message in messages)


def test_lint_reports_bad_next_target(tmp_path):
    script = tmp_path / "bad-next.yaml"
    write_yaml(script, {
        "name": "bad-next",
        "scene": [{
            "name": "流程",
            "scene": [{
                "登陆": {
                    "tests": {
                        "assert": {"status": 200},
                        "next": {
                            "condition": "$true",
                            "requestName": "不存在的下一步",
                        },
                    },
                }
            }],
        }],
    })

    issues = lint_script(script, DEMO_COLLECTION)

    assert any("next.requestName" in issue["message"] for issue in issues)


def test_lint_cli_strict_returns_failure_on_warning(tmp_path):
    script = tmp_path / "warning.yaml"
    write_yaml(script, {
        "name": "warning-scene",
        "scene": [{"登陆": {"pre": {"ref": "token"}, "tests": {"assert": {"status": 200}}}}],
    })

    assert main([str(script), str(DEMO_COLLECTION)]) == 0
    assert main([str(script), str(DEMO_COLLECTION), "--strict"]) == 1
