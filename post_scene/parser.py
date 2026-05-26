import copy
import json
from typing import List

from post_scene import auth_parser
from post_scene.creator import SetMethod, AssertMethod
from post_scene.models import Models

set_mapping = {
    'set-global': 'set_global_var',  # 设置全局变量的值
    'set-env': 'set_env_var',  # 设置环境变量的值
    'set-collect': 'set_collect_var',  # 设置集合变量的值
    'set': 'set_var',  # 设置变量值
    'unset-global': 'unset_global_var',
    'unset-env': 'unset_env_var',
    'unset-collect': 'unset_collect_var',
    'unset': 'unset_var'
}
assert_mapping = {
    'status': 'parse_assert_status',
    'body': 'parse_assert_body',
    'jsonBody': 'parse_assert_json_body',
    'tobe': 'parse_assert_tobe',
    'notTobe': 'parse_assert_not_tobe',
    'tohave': 'parse_assert_to_have',
    'notTohave': 'parse_assert_not_to_have',
    'express': 'parse_assert_express',
    'expect': 'parse_assert_expect',
    'header': 'parse_assert_header',
}


class Utils:

    @staticmethod
    def format_value(value):
        if isinstance(value, str):
            if value.startswith('$'):
                return value[1:]
            else:
                return "\"{}\"".format(value)
        else:
            return value

    @staticmethod
    def get_value(dict):
        return Utils.format_value(dict['desc'] if 'desc' in dict else None), Utils.format_value(dict['content'])

    @staticmethod
    def replace_params_name(request_item, params_name):
        if request_item['method'] == 'GET':
            url = request_item['url']
            query = url['query'] if 'query' in url else []
            for name in params_name:
                name, value = next(iter(name.items()))
                items = [i for i in query if i['key'] == name]
                if len(items) == 0:
                    query.append({'key': name, 'value': '{{' + value + '}}'})
                else:
                    items[0]['value'] = '{{' + value + '}}'

        elif request_item['method'] == 'POST':
            body = request_item['body']
            if 'mode' in body and (body['mode'] == 'urlencoded' or body['mode'] == 'formdata'):
                key = 'urlencoded' if body['mode'] == 'urlencoded' else 'formdata'
                query = body[key]
                for name in params_name:
                    name, value = next(iter(name.items()))
                    items = [i for i in query if i['key'] == name]
                    if len(items) == 0:
                        query.append({'key': name, 'value': '{{' + value + '}}', "type": "text"})
                    else:
                        items[0]['value'] = '{{' + value + '}}'

            elif 'mode' in body and body['mode'] == 'raw':
                raw = body['raw']
                try:
                    json_data = json.loads(raw)
                    for name in params_name:
                        name, value = next(iter(name.items()))
                        Utils.parse_json_params(json_data, name, value)
                    body['raw'] = json.dumps(json_data, indent=4)
                except Exception:
                    return request_item
        return request_item

    @staticmethod
    def replace_auth_data(request, scene_auth):
        if len(scene_auth) == 0:
            return
        if 'auth' not in request:
            request['auth'] = scene_auth
            return
        request_auth = request['auth']
        if request_auth['type'] != scene_auth['type']:
            request['auth'] = scene_auth
            return
        auth: List = request_auth[request_auth['type']]
        scene_auth = scene_auth[scene_auth['type']]
        for scene_auth_item in scene_auth:
            found = False
            for item in auth:
                if item['key'] == scene_auth_item['key']:
                    item['value'] = scene_auth_item['value']
                    found = True
            if found is False:
                auth.append(scene_auth_item)

    @staticmethod
    def parse_json_params(json_data, name: str, value):
        curr_name = name.strip()
        next_name = None
        if "." in name:
            curr_name = name[:name.index('.')]
            next_name = name[name.index('.') + 1:]

        if '[' in curr_name:
            item_index = curr_name[curr_name.index('[') + 1:curr_name.index(']')]
            curr_name = curr_name[:curr_name.index('[')]
            json_data = json_data[curr_name] if curr_name != '' else json_data
            if next_name is None:
                json_data[int(item_index.strip())] = '{{' + value.strip() + '}}'
            else:
                Utils.parse_json_params(json_data[int(item_index.strip())], next_name, value)
        else:
            if next_name is None:
                json_data[curr_name] = '{{' + value.strip() + '}}'
            else:
                Utils.parse_json_params(json_data[curr_name], next_name, value)

    @staticmethod
    def find_postman_item_by_name(name, items):
        for item in items:
            if 'item' in item:
                result = Utils.find_postman_item_by_name(name, item['item'])
                if result is not None:
                    result = copy.deepcopy(result)
                    if '_postman_id' in result: result.pop('_postman_id')
                    return result
            else:
                if item['name'] == name:
                    item = copy.deepcopy(item)
                    if '_postman_id' in item: item.pop('_postman_id')
                    return item


class Parse:

    @staticmethod
    def parse_sign(pre, params_name):
        if 'sign' in pre:
            sign = pre['sign']
            secret = sign['secret'] if 'secret' in sign else '$vars.get("api_sign_secret")'
            secret_name = sign['secretName'] if 'secretName' in sign else 'secret'
            sign_key = sign['signName'] if 'signName' in sign else 'sign'
            script = Models.sign.format(Utils.format_value(secret), sign_key, secret_name)
            params_name.append({sign_key: sign_key})
            return script
        return ''

    @staticmethod
    def parse_ref(pre, params_name):
        if 'ref' in pre:
            value = pre['ref']
            if isinstance(value, dict):
                for name in value:
                    params_name.append({name: value[name]})
            else:
                params_name.extend(map(lambda x: {x: x}, value.strip().split(",")))

    @staticmethod
    def parse_auth(pre, auth_bean):
        auth_parser.parse_auth(pre, auth_bean)

    @staticmethod
    def parse_pre(pre):
        script = []
        params_name = []
        for key in pre:
            if key in set_mapping:#set_mapping ，里的关键字，    'set': 'set_var',  # 设置变量值 key，关键字
                for name in pre[key]:
                    set_value = pre[key][name]
                    alisa_name = name
                    if isinstance(set_value, dict):
                        item = set_value.popitem()
                        alisa_name = item[0]
                        set_value = item[1]
                    script.append(
                        SetMethod.get_method(set_mapping[key])(Utils.format_value(alisa_name),
                                                               Utils.format_value(set_value)))#[set_value是creator.py里的set_var。然后调用handle方法，设置参数]
                    params_name.append({name: alisa_name})
            elif key == 'code':
                script.append(pre[key])
        return script, params_name

    @staticmethod
    def parse_next(next_data):
        scripts = []
        if isinstance(next_data, dict):
            scripts.append(Models.next_request.format(Utils.format_value(next_data['condition']),
                                                      Utils.format_value(next_data['requestName']),
                                                      Parse.parse_set_from_assert(next_data)))

        elif isinstance(next_data, list):
            for item in next_data:
                case = item['case']
                scripts.append(
                    Models.next_request.format(Utils.format_value(case['condition']),
                                               Utils.format_value(case['requestName']),
                                               Parse.parse_set_from_assert(next_data)))
        return scripts

    @staticmethod
    def parse_set_from_assert(item):
        script = ""
        for key in item:
            if key in set_mapping:
                for name in item[key]:
                    script += '\n\t{0}'.format(
                        getattr(SetMethod, set_mapping[key])(Utils.format_value(name),
                                                             Utils.format_value(item[key][name])))
        return script

    @staticmethod
    def parse_assert_expect(expect):
        script = []
        item = Utils.format_value(expect['item']) if 'item' in expect else None
        if 'include' in expect:
            script.append(
                getattr(AssertMethod, 'expect_include')(*Utils.get_value(expect), Utils.format_value(expect['include']),
                                                        Parse.parse_set_from_assert(expect), item))
        elif 'eql' in expect:
            script.append(
                getattr(AssertMethod, 'expect_eql')(*Utils.get_value(expect), Utils.format_value(expect['eql']),
                                                    Parse.parse_set_from_assert(expect), item))
        elif 'below' in expect:
            script.append(
                getattr(AssertMethod, 'expect_below')(*Utils.get_value(expect), Utils.format_value(expect['below']),
                                                      Parse.parse_set_from_assert(expect), item))
        elif 'oneOf' in expect:
            script.append(
                getattr(AssertMethod, 'expect_one_of')(*Utils.get_value(expect), Utils.format_value(expect['oneOf']),
                                                       Parse.parse_set_from_assert(expect), item))
        return script

    @staticmethod
    def parse_assert_body(body, to_have=True):
        body = {'content': body} if not isinstance(body, dict) else body
        script = [AssertMethod.body(*Utils.get_value(body), Parse.parse_set_from_assert(body), to_have)]
        return script

    @staticmethod
    def parse_assert_tobe(tobe):
        tobe = {'content': tobe} if not isinstance(tobe, dict) else tobe
        script = [AssertMethod.tobe(*Utils.get_value(tobe), Parse.parse_set_from_assert(tobe), True)]
        return script

    @staticmethod
    def parse_assert_not_tobe(not_tobe):
        not_tobe = {'content': not_tobe} if not isinstance(not_tobe, dict) else not_tobe
        script = [AssertMethod.tobe(*Utils.get_value(not_tobe), Parse.parse_set_from_assert(not_tobe), False)]
        return script

    @staticmethod
    def parse_assert_to_have(to_have):
        to_have = {'content': to_have} if not isinstance(to_have, dict) else to_have
        if 'status' in to_have:
            script = Parse.parse_assert_status(to_have['status'])
        elif 'body' in to_have:
            script = Parse.parse_assert_body(to_have['body'])
        elif 'header' in to_have:
            script = Parse.parse_assert_header(to_have['header'])
        elif 'jsonBody' in to_have:
            script = Parse.parse_assert_json_body(to_have['jsonBody'])
        else:
            script = [AssertMethod.to_have(*Utils.get_value(to_have), Parse.parse_set_from_assert(to_have), True)]
        return script

    @staticmethod
    def parse_assert_not_to_have(not_to_have):
        not_to_have = {'content': not_to_have} if not isinstance(not_to_have, dict) else not_to_have
        if 'status' in not_to_have:
            script = Parse.parse_assert_status(not_to_have['status'], False)
        elif 'body' in not_to_have:
            script = Parse.parse_assert_body(not_to_have['body'], False)
        elif 'header' in not_to_have:
            script = Parse.parse_assert_header(not_to_have['header'], False)
        elif 'jsonBody' in not_to_have:
            script = Parse.parse_assert_json_body(not_to_have['jsonBody'], False)
        else:
            script = [
                AssertMethod.to_have(*Utils.get_value(not_to_have), Parse.parse_set_from_assert(not_to_have), False)]
        return script

    @staticmethod
    def parse_assert_status(status, to_have=True):
        status = {'content': status} if not isinstance(status, dict) else status
        script = [AssertMethod.status(*Utils.get_value(status), Parse.parse_set_from_assert(status), to_have)]
        return script

    @staticmethod
    def parse_assert_express(express):
        express = {'content': express} if not isinstance(express, dict) else express
        script = [AssertMethod.express(*Utils.get_value(express), Parse.parse_set_from_assert(express))]
        return script

    @staticmethod
    def parse_assert_header(header, to_have=True):
        header = {'key': header} if not isinstance(header, dict) else header
        if 'content' in header: header['key'] = header['content']
        params = Utils.format_value(header['desc'] if 'desc' in header else None), Utils.format_value(
            header['key']), Utils.format_value(header['value'] if 'value' in header else None)
        script = [AssertMethod.header(*params, Parse.parse_set_from_assert(header), to_have)]
        return script

    @staticmethod
    def parse_assert_json_body(json_body, to_have=True):
        json_body = {'content': json_body} if not isinstance(json_body, dict) else json_body
        params = Utils.format_value(json_body['desc'] if 'desc' in json_body else None), Utils.format_value(
            json_body['content']), Utils.format_value(json_body['value'] if 'value' in json_body else None)
        script = [AssertMethod.json_body(*params, Parse.parse_set_from_assert(json_body), to_have)]
        return script

    @staticmethod
    def parse_tests(tests): #断言
        script = []
        for key in tests:
            if key == 'code':
                script.append(tests['code'])
            elif key == 'assert':
                assert_data = tests['assert']
                if isinstance(assert_data, list):
                    for item in assert_data:
                        for item_key in item:
                            script.extend(getattr(Parse, assert_mapping[item_key])(item[item_key]))
                else:
                    for assert_key in assert_data:
                        script.extend(
                            getattr(Parse, assert_mapping[assert_key])(assert_data[assert_key]))
            elif key == 'next':
                script.extend(Parse.parse_next(tests[key]))
            elif key in set_mapping:  # it from tests  it'sn't assert
                for name in tests[key]:
                    script.append(
                        getattr(SetMethod, set_mapping[key])(Utils.format_value(name),
                                                             Utils.format_value(tests[key][name])))
        return script


# parse_scene  这里for循环的是 获取30天内订单记录
# parse_scene  这里for循环的是 demo-scene
    @staticmethod
    def parse_scene(scenes_val):

        scenes_of_processed = []
        for item in scenes_val:
            if 'name' in item:  # 文件夹
                folder = {
                    'name': item['name'],
                    'auth': {},
                    'scene': Parse.parse_scene(item['scene'])
                }
                Parse.parse_auth(item, folder['auth'])
                scenes_of_processed.append(folder)
            else:  # 请求
                for key in item:
                    scene_data = item[key]
                    pre_scripts = []
                    scripts = []
                    params_name = []
                    auth = {}
                    scene_bean = {'name': key, 'pre-scripts': pre_scripts, 'scripts': scripts,
                                  'params-name': params_name, 'auth': auth}
                    scenes_of_processed.append(scene_bean)
                    if 'pre' in scene_data:
                        Parse.parse_auth(scene_data['pre'], auth)
                        Parse.parse_ref(scene_data['pre'], params_name)
                        pre_parse_data = Parse.parse_pre(scene_data['pre'])
                        pre_scripts.extend(pre_parse_data[0])
                        pre_scripts.append(Parse.parse_sign(scene_data['pre'], params_name))
                        params_name.extend(pre_parse_data[1])
                    if 'tests' in scene_data:#断言
                        scripts.extend(Parse.parse_tests(scene_data['tests']))
                    if 'textTests' in scene_data:
                        scripts.extend(Parse.parse_tests(scene_data['textTests']))
                    if len(scripts) > 0:
                        scripts.insert(0, SetMethod.create_vars())
                        if 'tests' in scene_data:
                            scripts.insert(0, SetMethod.create_vars())
                        if 'textTests' in scene_data:
                            scripts.insert(0, SetMethod.create_get_text())
                        scripts.insert(0, "/** 自动生成的代码 **/")
                    if len(pre_scripts) > 0:
                        pre_scripts.insert(0, SetMethod.create_vars())
                        pre_scripts.insert(0, "/** 自动生成的代码 **/")

        return scenes_of_processed
