import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from post_scene.post_scene import PostScene
from post_scene.template import build_template, load_postman_collection, main


DEMO_COLLECTION = ROOT_DIR / "src" / "api_document" / "demo.postman_collection.json"


def test_build_template_from_demo_collection():
    collection = load_postman_collection(DEMO_COLLECTION)

    template = build_template(collection, name="demo-template", scene_name="自动模板", limit=2)

    assert template["name"] == "demo-template"
    assert template["scene"][0]["name"] == "自动模板"
    steps = template["scene"][0]["scene"]
    assert list(steps[0].keys()) == ["登陆"]
    assert steps[0]["登陆"]["pre"]["set"]["userName"] == "user"
    assert steps[0]["登陆"]["tests"]["assert"]["status"] == 200
    assert list(steps[1].keys()) == ["获取用户信息"]
    assert steps[1]["获取用户信息"]["pre"]["set"]["uid"] == "1234567"


def test_template_cli_output_can_convert(tmp_path):
    output = tmp_path / "template.yaml"

    return_code = main([str(DEMO_COLLECTION), "-o", str(output), "--limit", "2"])

    assert return_code == 0
    assert output.exists()
    generated = PostScene.convert(str(output), str(DEMO_COLLECTION), scene_dirs=str(tmp_path / "scene"))
    assert generated
    generated_data = json.loads(Path(generated).read_text(encoding="utf-8"))
    generated_names = [item["name"] for item in generated_data["item"][0]["item"]]
    assert generated_names == ["登陆", "获取用户信息"]
