import uuid

from post_scene.BuiltFunction import BuiltFunction
from post_scene.models import Models


def check_none_default(content, default):
    return content if content is not None else default


class SetMethod:

    @staticmethod
    def create_get_json():
        return 'json = pm.response.json();'

    @staticmethod
    def create_get_text():
        return 'text = pm.response.text();'

    @staticmethod
    def create_vars():
        return 'vars = pm.variables;'

    @staticmethod
    def set_env_var(key, value):
        key, value = SetMethod.handle(key, value)
        return 'pm.environment.set({0}, {1});'.format(key, value)

    @staticmethod
    def set_collect_var(key, value):
        key, value = SetMethod.handle(key, value)
        return 'pm.collectionVariables.set({0}, {1});'.format(key, value)

    @staticmethod
    def set_global_var(key, value):
        key, value = SetMethod.handle(key, value)
        return 'pm.globals.set({0}, {1});'.format(key, value)

    @staticmethod
    def set_var(key, value):
        key, value = SetMethod.handle(key, value) #[set_value是parser.py里的set_var。然后调用handle方法]
        return 'pm.variables.set({0}, {1});'.format(key, value)

    @staticmethod
    def unset_env_var(key, value):
        return 'pm.environment.unset({0}, {1});'.format(key, value)

    @staticmethod
    def unset_collect_var(key, value):
        return 'pm.collectionVariables.unset({0}, {1});'.format(key, value)

    @staticmethod
    def unset_global_var(key, value):
        return 'pm.globals.unset({0}, {1});'.format(key, value)

    @staticmethod
    def unset_var(key, value):
        return 'pm.variables.unset({0}, {1});'.format(key, value)

    @staticmethod
    def handle(key: str, value: str):#[set_value是creator.py里的set_var。然后调用handle方法]
        return key, BuiltFunction.parse_built_function(value)

    @staticmethod
    def check_find(key: str, value: str):
        if isinstance(value, str) and value.startswith('$find'):
            index = SetMethod.check_style(value)
            script = value[:index + 1]
            script1 = value[index + 1:]

            values = script.strip()[script.index('(') + 1:-1].split(',')
            value = Models.check_find.format(values[0], values[1], script1)
            return key, value
        return key, value

    @staticmethod
    def check_builtin_vars(value):
        if isinstance(value, str):
            if value.strip().replace('"', "").replace("'", '') == '$uuid32':
                return 'CryptoJS.MD5(new Date().toLocaleTimeString()).toString()'
        return value

    @staticmethod
    def check_style(value):
        stack = []
        index = 0
        for char in value:
            if char == '(':
                stack.append(index)
            elif char == ')':
                if len(stack) == 1:
                    return index
                else:
                    stack.pop()
            index = index + 1
        return -1

    @staticmethod
    def get_method(method_name):
        return getattr(SetMethod, method_name)


class AssertMethod:

    @staticmethod
    def tobe(desc, content, set, to_have):
        if to_have:
            desc = check_none_default(desc, "'断言请求是 {0}'".format(AssertMethod.format_quotation(content)))
            return Models.tobe.format(desc, content, set)
        else:
            desc = check_none_default(desc, "'断言请求不是 {0}'".format(AssertMethod.format_quotation(content)))
            return Models.not_tobe.format(desc, content, set)

    @staticmethod
    def to_have(desc, content, set, to_have):
        if isinstance(content, str):
            if content.index('(') == -1:
                content = content + "()"
        if to_have:
            desc = check_none_default(desc, "'断言请求是 {0}'".format(AssertMethod.format_quotation(content)))
            return Models.not_to_have.format(desc, content, set)
        else:
            desc = check_none_default(desc, "'断言请求不是 {0}'".format(AssertMethod.format_quotation(content)))
            return Models.not_to_have.format(desc, content, set)

    @staticmethod
    def status(desc, content, set, to_have):
        if to_have:
            desc = check_none_default(desc, "'断言 status 有{0}'".format(AssertMethod.format_quotation(content)))
            return Models.status.format(desc, content, set)
        else:
            desc = check_none_default(desc, "'断言 status 没有{0}'".format(AssertMethod.format_quotation(content)))
            return Models.not_to_have_status.format(desc, content, set)

    @staticmethod
    def body(desc, content, set, to_have):
        if to_have:
            desc = check_none_default(desc, "'断言 body 有{0}'".format(AssertMethod.format_quotation(content)))
            return Models.body.format(desc, content, set)
        else:
            desc = check_none_default(desc, "'断言 body 没有{0}'".format(AssertMethod.format_quotation(content)))
            return Models.not_to_have_body(desc, content, set)

    @staticmethod
    def express(desc, content,set):
        desc = check_none_default(desc, "'断言 {0} 成立'".format(AssertMethod.format_quotation(content)))
        additional = ""
        if isinstance(set,str) and len(set) > 0:
            additional = Models.try_if
        return ("tests[{0}] = {1}"+additional).format(desc, content,content,set)

    @staticmethod
    def expect_include(desc, content, obj, set, item=None):
        desc = check_none_default(desc, "'断言 {0} 是包含{1}'".format(AssertMethod.format_quotation(content),
                                                                 AssertMethod.format_quotation(obj)))
        if item is not None:
            return Models.each_include.format(desc, content, obj, set, item)
        return Models.include.format(desc, content, obj, set)

    @staticmethod
    def expect_eql(desc, content, obj, set, item=None):
        desc = check_none_default(desc, "'断言 {0} 是等于{1}'".format(AssertMethod.format_quotation(content),
                                                                 AssertMethod.format_quotation(obj)))
        if item is not None:
            return Models.each_eql.format(desc, content, obj, item,set)
        return Models.eql.format(desc, content, obj, set)

    @staticmethod
    def expect_below(desc, content, obj, set, item=None):
        desc = check_none_default(desc, "'断言 {0} 是小于{1}'".format(AssertMethod.format_quotation(content),
                                                                 AssertMethod.format_quotation(obj)))
        if item is not None:
            return Models.each_below.format(desc, content, obj, set, item)
        return Models.below.format(desc, content, obj, set)

    @staticmethod
    def expect_one_of(desc, content, obj, set, item=None):
        desc = check_none_default(desc,
                                  "'断言 {0} 存在{1}中的任意一个'".format(AssertMethod.format_quotation(content),
                                                                  AssertMethod.format_quotation(obj)))
        if item is not None:
            return Models.each_one_of.format(desc, content, obj, set, item)
        return Models.one_of.format(desc, content, obj, set)

    @staticmethod
    def header(desc, content, value, set, to_have):
        if value is not None:
            content = '{0},{1}'.format(content, value)
        if to_have:
            desc = check_none_default(desc, "'断言 header 有{0}'".format(AssertMethod.format_quotation(content)))
            return Models.header.format(desc, content, set)
        else:
            desc = check_none_default(desc, "'断言 header 没有{0}'".format(AssertMethod.format_quotation(content)))
            return Models.not_to_have_header.format(desc, content, set)

    @staticmethod
    def json_body(desc, content, value, set, to_have):
        if value is not None:
            content = '{0},{1}'.format(content, value)
        if to_have:
            desc = check_none_default(desc, "'断言 JsonBody 有{0}'".format(AssertMethod.format_quotation(content)))
            return Models.json_body.format(desc, content, set)
        else:
            desc = check_none_default(desc, "'断言 JsonBody 没有{0}'".format(AssertMethod.format_quotation(content)))
            return Models.not_to_json_body.format(desc, content, set)

    @staticmethod
    def format_quotation(data):
        if isinstance(data, str):
            return data.replace('\'', '"')
        return data


class PostmanJson:

    @staticmethod
    def create_info(name):
        return {"_postman_id": str(uuid.uuid4()), "name": name,
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"}

    @staticmethod
    def create_script(scripts, listen="prerequest"):
        return {
            "listen": listen,
            "script": {
                'id': str(uuid.uuid4()),
                "type": "text/javascript",
                'exec': scripts
            }
        }
