from post_scene.models import Models


class BuiltFunction:
    @staticmethod
    def smart_split(s: str, delimiter: str = ','):
        """感知括号深度的参数分割，支持嵌套函数"""
        parts = []
        bracket_level = 0
        current_part = []
        for char in s:
            if char == '(':
                bracket_level += 1
            elif char == ')':
                bracket_level -= 1
            if char == delimiter and bracket_level == 0:
                parts.append("".join(current_part).strip())
                current_part = []
            else:
                current_part.append(char)
        parts.append("".join(current_part).strip())
        return [p for p in parts if p]

    @staticmethod
    def parse_built_function(value: str):
        if not isinstance(value, str) or not value.startswith('$'):
            return value

        value = value.strip()
        last_idx = BuiltFunction.get_last_paren_idx(value)
        if last_idx == -1:
            value += '()'
            last_idx = value.rfind(')')

        function_call = value[:last_idx + 1]
        field = value[last_idx + 1:]

        open_idx = function_call.find('(')
        function_name = function_call[1:open_idx]
        raw_params = function_call[open_idx + 1:-1]

        # 递归解析参数
        params = [BuiltFunction.parse_built_function(p) for p in BuiltFunction.smart_split(raw_params)]

        func_map = {
            'find': lambda p, f: Models.check_find.format(p[0], p[1], f),
            'filter': lambda p, f: Models.check_filter.format(p[0], p[1],
                                                              (f'it{f}' if f.startswith('.') else f) or 'it'),
            'uuid32': lambda p, f: 'CryptoJS.MD5(new Date().getTime().toString()).toString()',
            'md5': lambda p, f: f'CryptoJS.MD5({p[0]}).toString()',
            'dateFormat': lambda p, f: Models.date_format.format(p[0], p[1]),
            'weekStart': lambda p, f: Models.get_week_start,
            'monthEnd': lambda p, f: Models.get_month_end
        }

        if function_name in func_map:
            return func_map[function_name](params, field)
        return value

    @staticmethod
    def get_last_paren_idx(value):
        """精确定位外层括号索引"""
        stack = []
        for i, char in enumerate(value):
            if char == '(':
                stack.append(i)
            elif char == ')':
                if len(stack) == 1: return i
                if stack: stack.pop()
        return -1