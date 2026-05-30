import os

import xmind
from ruamel.yaml import YAML

requestName = {}
nextRequestName = {}


def dict_ite(data, topic, parent):
    if isinstance(data, dict) and 'scene' in data:
        subtopic = topic.addSubTopic()
        subtopic.setTitle(data['name'])
        dict_ite(data['scene'], subtopic, data)
    elif isinstance(data, list):
        for item in data:
            dict_ite(item, topic, parent)
    elif isinstance(data, dict):
        for key in data:
            subtopic = topic.addSubTopic()
            subtopic.setTitle(key)
            dict_ite(data[key], subtopic, key)
            if 'scene' in parent:
                requestName[key] = subtopic.getID()

    elif isinstance(data, str) or isinstance(data, int):
        subtopic = topic.addSubTopic()
        subtopic.setTitle(data)
        if 'requestName' in parent:
            nextRequestName[data] = subtopic.getID()


def dict2xmind(dicts, filename, path):
    file_path = os.path.join(os.path.abspath(path), filename + ".xmind")
    if os.path.exists(file_path):
        os.remove(file_path)
    workbook = xmind.load(file_path)

    sheet = workbook.getPrimarySheet()
    sheet.setTitle(dicts['name'])
    root_topic = sheet.getRootTopic()
    root_topic.setTitle(dicts['name'])

    dict_ite(dicts['scene'], root_topic, {})

    for next_ in nextRequestName:
        if next_ in requestName:
            sheet.createRelationship(nextRequestName[next_], requestName[next_], '')
    xmind.save(workbook, file_path)


# demo
# if __name__ == '__main__':
#     file = open('../src/yaml/demo.yaml', 'r', encoding='utf-8')
#     yaml = YAML()
#     script = yaml.load(file)
#     dict2xmind(script, "demo", path="../")
