import urllib.request, json

base = 'http://localhost:8001'

def post_put(item_id, payload):
    req = urllib.request.Request(
        f'{base}/api/pi/items/{item_id}',
        data=json.dumps(payload).encode(),
        method='PUT',
        headers={'Content-Type': 'application/json'},
    )
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, r.read().decode()
    except Exception as e:
        return getattr(e, 'code', None), getattr(e, 'read', lambda: b'')().decode()

def get(order_id):
    with urllib.request.urlopen(f'{base}/api/bff/orders/{order_id}/full-detail') as r:
        return json.loads(r.read().decode())

# 初始
items = get(3)['data']['items']
for x in items:
    print('init', x['id'], 'pn=', repr(x['product_name']), 'pn_en=', repr(x['product_name_en']))

# 写入一个明确非空值
print('PUT 7 detail_desc_en=VISIBLE_TEST_EN', post_put(7, {'detail_desc_en': 'VISIBLE_TEST_EN'}))
items = get(3)['data']['items']
for x in items:
    print('after put', x['id'], 'pn_en=', repr(x['product_name_en']))

# 模拟前端重新加载弹窗再保存空字符串
print('PUT 7 detail_desc_en=""', post_put(7, {'detail_desc_en': ''}))
items = get(3)['data']['items']
for x in items:
    print('after blank put', x['id'], 'pn_en=', repr(x['product_name_en']))

# 用之前的 API 把值恢复成 CCC
print('RESTORE PUT 7 detail_desc_en=CCC', post_put(7, {'detail_desc_en': 'CCC'}))
items = get(3)['data']['items']
for x in items:
    print('after restore', x['id'], 'pn_en=', repr(x['product_name_en']))
