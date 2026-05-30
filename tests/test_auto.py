import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from post_scene.auto import main, run_auto


DEMO_COLLECTION = ROOT_DIR / "src" / "api_document" / "demo.postman_collection.json"


def test_run_auto_generates_yaml_collection_and_report(tmp_path):
    report = run_auto(DEMO_COLLECTION, tmp_path, max_scenes=2, strict=True)

    assert report["status"] == "converted"
    assert Path(report["yaml_file"]).exists()
    assert Path(report["collection_file"]).exists()
    assert Path(report["report_file"]).exists()
    report_data = json.loads(Path(report["report_file"]).read_text(encoding="utf-8"))
    assert report_data["collection_file"] == report["collection_file"]


def test_auto_cli_returns_success(tmp_path):
    return_code = main([str(DEMO_COLLECTION), "-o", str(tmp_path), "--max-scenes", "1"])

    assert return_code == 0
    assert (tmp_path / "suggested-scenes.yaml").exists()
    assert (tmp_path / "postscene-auto-report.json").exists()
