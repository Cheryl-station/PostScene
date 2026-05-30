support_auth = ['apikey', 'bearer', 'basic', 'digest', 'oauth1', 'oauth2', 'hawk', 'awsv4', 'edgegrid']

key_alias_name = {
    'Key': 'key',
    'qop': 'qop',
    'User': 'user',
    'Addto': 'key',
    'Realm': 'realm',
    'Nonce': 'nonce',
    'Value': 'value',
    'Token': 'token',
    'Opaque': 'opaque',
    'ext': 'extraData',
    'dlg': 'delegation',
    'Version': 'version',
    'BaseURL': 'baseURL',
    'Username': 'username',
    'AWSRegion': 'region',
    'Password': 'password',
    'AccessToken': 'token',
    'Algorithm': 'algorithm',
    'Timestamp': 'timestamp',
    'HawkAuthID': 'authId',
    'AccessKey': 'accessKey',
    'SecretKey': 'secretKey',
    'ServiceName': 'service',
    'HawkAuthKey': 'authKey',
    'NonceCount': 'nonceCount',
    'ClientNonce': 'clientNonce',
    'ConsumerKey': 'consumerKey',
    'TokenSecret': 'tokenSecret',
    'ClientToken': 'clientToken',
    'ClientSecret': 'clientSecret',
    'SessionToken': 'sessionToken',
    'Headerstosign': 'headersToSign',
    'AccessTokenOauth2': 'accessToken',
    'ConsumerSecret': 'consumerSecret',
    'SignatureMethod': 'signatureMethod',
    'AccessTokenEdgegrid': 'accessToken',
}


def parse_default_value(key, item, default, value_type='boolean'):
    bool_value = {'key': key, 'value': default, 'type': value_type}
    if key in item:
        bool_value['value'] = item[bool(item[key].capitalize())]
    return bool_value


def default_parse(auth):
    auth_items = []
    for auth_item_key in auth:
        auth_item = auth[auth_item_key]
        if isinstance(auth_item, dict):
            auth_item = '{{{{{0}}}}}'.format(auth_item['ref'])
        if auth_item_key in key_alias_name:
            auth_item_key = key_alias_name[auth_item_key]
        item = {'key': auth_item_key, 'value': auth_item, 'type': 'string'}
        auth_items.append(item)
    return auth_items


def parse_simple(key, item):
    auth_items = []
    if isinstance(item, str):
        auth_items.append({'key': key, 'value': item, 'type': 'string'})
    elif 'ref' in item:
        auth_items.append({'key': key, 'value': '{{{{{0}}}}}'.format(item['ref']), 'type': 'string'})
    else:
        auth_items.extend(default_parse(item))
    return auth_items


def parse_item(item, auth_name, auth_items):
    if 'bearer' == auth_name:
        auth_items.extend(parse_simple('token', item))
    elif 'apikey' == auth_name:
        auth_items.append(parse_default_value('in', item, 'header', 'string'))
        auth_items.extend(default_parse(item))
    elif 'digest' == auth_name:
        auth_items.append(parse_default_value('disableRetryRequest', item, False))
        auth_items.extend(default_parse(item))
    elif 'oauth1' == auth_name:
        auth_items.append(parse_default_value('addParamsToHeader', item, False))
        auth_items.append(parse_default_value('addEmptyParamsToSign', item, False))
        auth_items.extend(default_parse(item))
    elif 'oauth2' == auth_name:
        if 'AccessToken' in item:
            item['AccessTokenOauth2'] = item['AccessToken']
            item.pop('AccessToken')
        auth_items.append(parse_default_value('addTokenTo', item, 'header', 'string'))  # queryParams
        auth_items.extend(parse_simple('accessToken', item))
    elif 'hawk' == auth_name:
        auth_items.append(parse_default_value('includePayloadHash', item, False))
        auth_items.append(parse_default_value('algorithm', item, 'sha256','string'))
        auth_items.extend(default_parse(item))
    elif 'edgegrid' == auth_name:
        if 'AccessToken' in item:
            item['AccessTokenEdgegrid'] = item['AccessToken']
            item.pop('AccessToken')
        auth_items.extend(default_parse(item))
    else:
        auth_items.extend(default_parse(item))


def parse_auth(pre, auth_bean):#验证pre里面是否有auth
    if 'auth' in pre:
        if isinstance(pre['auth'], dict):
            for key in pre['auth']:
                if key in support_auth:
                    auth_bean['type'] = key
                    auth_items = []
                    auth_bean[key] = auth_items
                    auth = pre['auth'][key]
                    parse_item(auth, key, auth_items)
        elif pre['auth'] in ['None', 'none', 'null', 'no', 'No', 'false', 'False','noauth']:
            auth_bean['type'] = 'noauth'
