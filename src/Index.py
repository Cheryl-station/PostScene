import sys
import os
from pathlib import Path


# 获取 Index.py 的绝对路径，再向上退两级找到项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from post_scene.post_scene import PostScene

# 动态定位文件路径，防止找不到 demo 文件
YAML_PATH = BASE_DIR / 'src' / 'yaml' / 'demo.yaml'
API_DOC_PATH = BASE_DIR / 'src' / 'api_document' / 'demo.postman_collection.json'

def main():
    print("🚀 PostScene 启动转换与生成...")
    try:
        # 使用统一入口进行转换
        PostScene.convert(
            script_path=str(YAML_PATH),
            postman_data_path=str(API_DOC_PATH),
            scene_dirs=str(BASE_DIR / 'src' / 'scene')
        )
        print(f"✅ 执行成功！结果保存在: {BASE_DIR / 'src' / 'scene'}")
    except Exception as e:
        print(f"❌ 运行出错: {e}")

if __name__ == "__main__":
    main()
