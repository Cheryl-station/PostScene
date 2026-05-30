# PostScene

PostScene 是一个接口场景测试生成工具：用 YAML 或 XMind 管理接口流程，再结合接口文档生成可导入 Postman 的场景 Collection。

它也提供 Codex skill 包，可以让 Codex 帮你从 Postman / Apifox 接口文档推荐业务场景、校验 YAML，并生成 Postman 场景集合。

## 支持格式

- 场景脚本：YAML / XMind
- 接口文档：Postman Collection JSON、Postman share URL
- Apifox：建议导出 OpenAPI / Swagger JSON 或 YAML

## 安装

```bash
pip install -U PostScene
```

本地开发：

```bash
pip install -r requirements.txt
pip install -e .
```

## 快速开始

一键完成推荐 YAML、校验和转换：

```bash
postscene-auto ./src/api_document/demo.postman_collection.json -o ./src/scene
```

如果接口文档来自 Apifox，先在 Apifox 中导出 OpenAPI / Swagger JSON，然后运行：

```bash
postscene-auto ./src/api_document/apifox-openapi.json -o ./src/scene
```

输出内容：

- `suggested-scenes.yaml`：推荐的 YAML 场景草稿
- `*-suggested-scenes.json`：可导入 Postman 的场景 Collection
- `postscene-auto-report.json`：自动流程报告

## 常用命令

把已有 YAML / XMind 场景转为 Postman Collection：

```bash
postscene ./src/yaml/demo.yaml ./src/api_document/demo.postman_collection.json -o ./src/scene
```

根据接口文档生成基础 YAML 模板：

```bash
postscene-template ./src/api_document/demo.postman_collection.json -o ./src/yaml/scene-template.yaml
```

根据接口名称和路径推荐业务场景 YAML：

```bash
postscene-suggest ./src/api_document/demo.postman_collection.json -o ./src/yaml/suggested-scenes.yaml
```

校验 YAML 与接口文档是否匹配：

```bash
postscene-lint ./src/yaml/suggested-scenes.yaml ./src/api_document/demo.postman_collection.json
```

严格校验：

```bash
postscene-lint ./src/yaml/suggested-scenes.yaml ./src/api_document/demo.postman_collection.json --strict
```

## YAML 示例

```yaml
name: order-flow
scene:
  - name: 下单流程
    scene:
      - 登陆:
          pre:
            set:
              userName: user
              password: user123
          tests:
            assert:
              express:
                content: $json.code === '1'
                set:
                  token: $json.data.token
                  uid: $json.data.uid
      - 通过商品名字搜索商品:
          pre:
            ref: canteenId
            set:
              goodsName: 苹果
          tests:
            assert:
              expect:
                content: $json.data.goodsList
                item: $it.name
                include: 苹果
                set:
                  goodsId: $$find(json.data.goodsList, it.name == '苹果').goodsId
```

常用字段：

- `pre.set`：设置请求参数或变量
- `pre.ref`：引用前面步骤保存的变量
- `tests.assert.status`：断言响应状态码
- `tests.assert.express`：写 Postman 测试表达式
- `tests.assert.expect`：对列表内容做预期断言
- `tests.assert.*.set`：从响应中保存变量，供后续步骤引用

## Python 调用

```python
from post_scene.post_scene import PostScene

PostScene.convert(
    "./src/yaml/demo.yaml",
    "./src/api_document/demo.postman_collection.json",
    scene_dirs="./src/scene",
)
```

## Codex Skill

本仓库包含可发布的 Codex skill 包：

```text
skills/post-scene
```

从 GitHub 安装：

```bash
python scripts/install-skill-from-github.py \
  --repo Cheryl-station/PostScene \
  --path skills/post-scene
```

安装后重启 Codex，即可通过 `$post-scene` 调用。

## 开发验证

```bash
pytest
python3 /Users/tangyajun/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/post-scene
```
