import urllib.request, json, time

base = 'http://localhost:8001'

def post_put(item_id, payload):
    req = urllib.request.Request(
        f'{base}/api/pi/items/{item_id}',
        data=json.dumps(payload).encode(),
        method='PUT',
        headers={'Content-Type': 'application/json'},
    )
    with urllib.request.urlopen(req) as r:
        return r.status, r.read().decode()

def get(order_id):
    with urllib.request.urlopen(f'{base}/api/bff/orders/{order_id}/full-detail') as r:
        return json.loads(r.read().decode())

# 模拟用户保存后再打开：保存 -> 立即重新获取 -> 再保存
post_put(7, {'detail_desc_en': 'VISIBLE_TEST_EN_RACE'})
after1 = get(3)['data']['items']
print('after first put:', after1[0])

# 模拟另一端在保存前已经发出 GET
before_put = get(3)['data']['items']
print('before put (cached):', before_put[0])
post_put(7, {'detail_desc_en': 'VISIBLE_TEST_EN_RACE2'})
after2 = get(3)['data']['items']
print('after second put:', after2[0])

# 验证最终一致
final = get(3)['data']['items']
print('final:', final[0])
