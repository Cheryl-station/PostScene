class Models:
    status = """
pm.test({0}, function () {{
    pm.response.to.have.status({1});{2}
}});
"""

    not_to_have_status = """
pm.test({0}, function () {{
    pm.response.to.not.have.status({1});{2}
}});
"""

    body = """
pm.test({0}, function () {{
    pm.response.to.have.body({1});{2}
}});
 """
    not_to_have_body = """
pm.test({0}, function () {{
    pm.response.to.not.have.body({1});{2}
}});
     """

    include = """
pm.test({0}, function () {{
    pm.expect({1}).to.include({2});{3}
}});    
"""

    eql = """
pm.test({0}, function () {{
    pm.expect({1}).to.eql({2});{3}
}});    
"""

    below = """
pm.test({0}, function () {{
    pm.expect({1}).to.be.below({2});{3}
}});    
"""

    one_of = """
pm.test({0}, function () {{
    pm.expect({1}).to.be.oneOf({2});{3}
}});
"""
    try_if = """\ntry{{ if({2}){{ {3} }} }}catch(e){{ console.log(e) }};"""

    header = """
pm.test({0}, function () {{
    pm.response.to.have.header({1});{2}
}});    
"""

    not_to_have_header = """
pm.test({0}, function () {{
    pm.response.to.not.have.header({1});{2}
}});    
"""
    json_body = """
pm.test({0}, function () {{
    pm.response.to.have.jsonBody({1});{2}
}});    
"""

    not_to_json_body = """
pm.test({0}, function () {{
    pm.response.to.not.have.jsonBody({1});{2}
}});    
"""
    have = """
pm.test({0}, function () {{
    pm.response.to.have.{1};{2}
}});  
"""

    not_to_have = """
pm.test({0}, function () {{
    pm.response.to.not.have.{1};{2}
}});  
"""

    tobe = """
pm.test({0}, function () {{
    pm.response.to.be.{1};{2}
}});  
"""

    not_tobe = """
pm.test({0}, function () {{
    pm.response.to.not.be.{1};{2}
}});  
"""

    each_include = """
pm.test({0}, function () {{
    {1}.forEach(it=> pm.expect({4}).to.include({2}));{3}
}});    
"""

    each_eql = """
pm.test({0}, function () {{
    {1}.forEach(it=> pm.expect({4}).to.eql({2}));{3}
}});    
"""

    each_below = """
pm.test({0}, function () {{
    {1}.forEach(it=> pm.expect({4}).to.be.below({2}));{3}
}});    
"""

    each_one_of = """
pm.test({0}, function () {{
    {1}.forEach(it=> pm.expect({4}).to.be.oneOf({2}));{3}
}});
"""
    next_request = "try{{ if({0}) {{{2} postman.setNextRequest({1})}} }}catch(e){{console.log(e)}}"

    check_find = """(()=>{{
        let data = {0}.find(it=> {1})
        if (data) data = data{2}
        return data}})()
"""
    check_find_last = """(()=>{{
        let data = {0}.reverse().find(it=> {1})
        if (data) data = data{2}
        return data}})()
"""
    check_filter = """(()=>{{
        let data = {0}.filter(it=> {1})
        if (data) data = data.map(it=> {2}) 
        return data}})()
"""

    get_before_date = """(()=> {{
    //n为你要传入的参数，当前为0，前一天为-1，后一天为1
    const date = new Date();
    date.setDate(date.getDate() + {0});
    date.setHours(0);
    date.setMinutes(0);
    date.setSeconds(0);
    return date.getTime();
}})()
"""
    get_week_start = """(()=> {{
    const now = new Date();
    nowDayOfWeek = now.getDay();
    now.setDate(now.getDate() - nowDayOfWeek);
    now.setHours(0);
    now.setMinutes(0);
    now.setSeconds(0);
    return now.getTime();
}})()
"""

    get_week_end = """(()=> {{
    const now = new Date();
    nowDayOfWeek = now.getDay();
    now.setDate(now.getDate() + (6 - nowDayOfWeek))
    now.setHours(23);
    now.setMinutes(59);
    now.setSeconds(59);
    return now.getTime();
}})()
"""

    get_last_week_start = """(()=> {{
    const now = new Date();
    nowDayOfWeek = now.getDay();
    now.setDate(now.getDate() - nowDayOfWeek - 7)
    now.setHours(0);
    now.setMinutes(0);
    now.setSeconds(0);
    return now.getTime();
}})()
"""

    get_last_week_end = """(()=> {{
    const now = new Date();
    nowDayOfWeek = now.getDay();
    now.setDate(now.getDate() - nowDayOfWeek - 1);
    now.setHours(23);
    now.setMinutes(59);
    now.setSeconds(59);
    return now.getTime();
}})()
"""

    get_month_start = """(()=> {{
    const now = new Date();
    now.setDate(1);
    now.setHours(0);
    now.setMinutes(0);
    now.setSeconds(0);
    return now.getTime();
}})()
"""

    get_month_end = """(()=> {{
    const now = new Date();
    now.setMonth(now.getMonth() + 1);
    now.setDate(0);
    now.setHours(23);
    now.setMinutes(59);
    now.setSeconds(59);
    return now.getTime();
}})()
"""

    get_last_month_start = """(()=> {{
    const now = new Date();
    now.setMonth(now.getMonth() - 1);
    now.setDate(1);
    now.setHours(0);
    now.setMinutes(0);
    now.setSeconds(0);
    return now.getTime();
}})()
"""

    get_last_month_end = """(()=> {{
    const now = new Date();
    now.setDate(0);
    now.setHours(23);
    now.setMinutes(59);
    now.setSeconds(59);
    return now.getTime();
}})()
"""
    date_format = """((date, fmt) => {{
  date = new Date(date)
  const Format = {{
    'M+': date.getMonth() + 1,
    'd+': date.getDate(),
    'D+': date.getDate(),
    'H+': date.getHours(),
    'h+': date.getHours(),
    'm+': date.getMinutes(),
    's+': date.getSeconds(),
    'S+': date.getMilliseconds(),
  }};
  if (/(y+)/.test(fmt) || /(Y+)/.test(fmt))
    fmt = fmt.replace(RegExp.$1, date.getFullYear() + '');
  for (let k in Format)
    if (new RegExp('(' + k + ')').test(fmt))
      fmt = fmt.replace(
        RegExp.$1,
        RegExp.$1.length === 1
          ? Format[k]
          : ('00' + Format[k]).substr(Format[k].toString().length),
      );
  return fmt;
}})({0},{1})
"""

    sign = r"""
/*****          生成的代码请勿修改        ******/    
// 连接参数
function con_params(params){{
    if(typeof(params) == "string"){{
        if(/\{{\{{[\w]+\}}\}}/.test(params))
            return vars.get(params.match(/[\w]+/))
        return params;
    }}
    else {{
        let sort_keys = Object.keys(params).sort();
        let s = '';
        for(let i in sort_keys) {{
            let k = sort_keys[i];
            s += k + "=" + con_params(params[k]) + "&";
        }}
        return s;
    }}
}}

// 生成签名
function cal_sign(secret,params){{
    var s = con_params(params);
    return CryptoJS.MD5(s+"{2}="+secret).toString();
    
}}

var secret= {0} 
let params = {{}}
if (pm.request.method == 'GET')
    pm.request.url.query.map(it=> params[it.key] = it.value)
else
    params = typeof(request.data) === 'string' ? JSON.parse(request.data) : request.data
delete params['{1}'];             // 去掉sign, 得到元素请求参数
sign = cal_sign(secret, params); // 计算签名

vars.set('{1}',sign)
/*****  如需修改请修改python工程的models.sign   ******/   
"""
