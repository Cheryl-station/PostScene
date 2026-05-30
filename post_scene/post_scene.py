import json
import logging
from pathlib import Path
from ruamel.yaml import YAML
from post_scene.api_document import load_api_document
from post_scene.creator import PostmanJson
from post_scene.parser import Utils, Parse


class PostScene:
    @staticmethod
    def check_postman_url(source: str):
        """获取接口文档数据（支持 Postman/OpenAPI/Swagger，本地文件或 URL）"""
        try:
            return load_api_document(source)
        except Exception as e:
            logging.error(f"加载接口文档失败: {e}")
            return None

    @staticmethod
    def package(scenes_val, postman_data):
        """构建 Postman Collection 层级结构"""
        new_items = []
        for scene in scenes_val:
            if 'scene' in scene:
                folder = {
                    'name': scene['name'],
                    'item': PostScene.package(scene['scene'], postman_data)
                }
                if scene.get('auth'):
                    folder['auth'] = scene['auth']
                new_items.append(folder)
            else:
                item = Utils.find_postman_item_by_name(scene['name'], postman_data['item'])
                if item:
                    # 使用深拷贝确保数据独立性
                    target = json.loads(json.dumps(item))
                    target['request'] = Utils.replace_params_name(target['request'], scene['params-name'])
                    Utils.replace_auth_data(target['request'], scene['auth'])
                    target['event'] = []
                    if 'pre-scripts' in scene:
                        target['event'].append(PostmanJson.create_script(scene['pre-scripts']))
                    if 'scripts' in scene:
                        target['event'].append(PostmanJson.create_script(scene['scripts'], 'test'))
                    new_items.append(target)
        return new_items

    @staticmethod
    def generate(yaml_path, postman_data_path, scene_dirs='../scene'):
        """执行生成流程"""
        yaml_file = Path(yaml_path)
        if not yaml_file.exists():
            raise FileNotFoundError(f"场景脚本不存在: {yaml_path}")

        with open(yaml_file, 'r', encoding='utf-8') as f:
            script = YAML().load(f)

        if not isinstance(script, dict) or 'name' not in script or 'scene' not in script:
            raise ValueError("场景脚本必须包含 name 和 scene 字段")

        scenes = Parse.parse_scene(script['scene'])
        postman_data = PostScene.check_postman_url(postman_data_path)
        if not postman_data:
            return None
        if 'item' not in postman_data:
            raise ValueError("接口文档缺少可用 item 字段")

        new_collection = {
            "info": PostmanJson.create_info(script['name']),
            "item": PostScene.package(scenes, postman_data)
        }

        if 'auth' in script:
            new_collection['auth'] = {}
            Parse.parse_auth(script, new_collection['auth'])
        if 'variable' in postman_data:
            new_collection['variable'] = postman_data['variable']

        output_dir = Path(scene_dirs)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{script['name']}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(new_collection, f, indent=4, ensure_ascii=False)
        return str(output_file)

    @staticmethod
    def covert(script_path, postman_data_path, scene_dirs='./scene'):
        """统一转换入口"""
        path_obj = Path(script_path)
        suffix = path_obj.suffix.lower()
        if suffix in ('.yaml', '.yml'):
            return PostScene.generate(script_path, postman_data_path, scene_dirs)
        elif suffix == '.xmind':
            from post_scene.Xmind2Yaml import xmind2Yaml

            xmind2Yaml(str(path_obj.parent), path_obj.stem)
            return PostScene.generate(str(path_obj.with_suffix('.yaml')), postman_data_path, scene_dirs)
        raise ValueError("script_path 仅支持 .yaml、.yml 或 .xmind")

    @staticmethod
    def convert(script_path, postman_data_path, scene_dirs='./scene'):
        """`covert` 的正确拼写别名（保持向后兼容）"""
        return PostScene.covert(script_path, postman_data_path, scene_dirs)
