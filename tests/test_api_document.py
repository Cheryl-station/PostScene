import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from post_scene.api_document import load_api_document
from post_scene.auto import run_auto
from post_scene.template import build_suggested_template, load_postman_collection


def write_openapi(path: Path) -> None:
    path.write_text(json.dumps({
        "openapi": "3.0.3",
        "info": {
            "title": "Apifox Demo",
            "version": "1.0.0",
        },
        "servers": [{
            "url": "https://api.example.com",
        }],
        "paths": {
            "/login": {
                "post": {
                    "summary": "登录",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "userName": {"type": "string", "example": "user"},
                                        "password": {"type": "string", "example": "pass"},
                                    },
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "ok"}},
                }
            },
            "/goods/search": {
                "get": {
                    "summary": "搜索商品",
                    "parameters": [{
                        "name": "goodsName",
                        "in": "query",
                        "schema": {"type": "string", "example": "苹果"},
                    }],
                    "responses": {"200": {"description": "ok"}},
                }
            },
        },
    }), encoding="utf-8")


def test_load_openapi_as_postman_collection(tmp_path):
    openapi = tmp_path / "apifox-openapi.json"
    write_openapi(openapi)

    collection = load_api_document(str(openapi))

    assert collection["info"]["name"] == "Apifox Demo"
    names = [item["name"] for item in collection["item"]]
    assert names == ["登录", "搜索商品"]
    assert collection["item"][0]["request"]["body"]["mode"] == "raw"
    assert collection["item"][1]["request"]["url"]["query"][0]["key"] == "goodsName"


def test_suggest_and_auto_support_openapi(tmp_path):
    openapi = tmp_path / "apifox-openapi.json"
    write_openapi(openapi)

    collection = load_postman_collection(openapi)
    template = build_suggested_template(collection, max_scenes=2)
    scene_names = [scene["name"] for scene in template["scene"]]
    assert "登录与用户信息" in scene_names or "查询流程" in scene_names

    report = run_auto(openapi, tmp_path / "scene", max_scenes=2)
    assert report["status"] == "converted"
    assert Path(report["yaml_file"]).exists()
    assert Path(report["collection_file"]).exists()
