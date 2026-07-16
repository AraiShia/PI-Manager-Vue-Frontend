"""手动测试 detail_desc_en 保存链路。

用法（从 backend/ 目录）：
    python tests/test_save_detail.py

步骤：
1. GET 当前 detail_desc_en
2. PUT 新值
3. GET 验证
4. 恢复原值（可选）
"""
import urllib.request
import urllib.error
import json

BASE = "http://localhost:8001"

def api(method, path, body=None):
    url = BASE + path
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method,
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "body": e.read().decode()}

# 找一个有 product_id 的 item
items_resp = api("GET", "/api/pi/items/1")
print("GET /api/pi/items/1:", json.dumps(items_resp, indent=2, ensure_ascii=False)[:300])

# 找第一个有 id 的 item
if isinstance(items_resp, list) and items_resp:
    item = items_resp[0]
    item_id = item["id"]
    print(f"\n使用 item_id={item_id}")

    # Step 1: 读取
    get1 = api("GET", f"/api/pi/items/{item_id}")
    en_before = get1.get("detail_desc_en", "N/A")
    print(f"保存前 detail_desc_en = {en_before!r}")

    # Step 2: 写入
    put_resp = api("PUT", f"/api/pi/items/{item_id}", {"detail_desc_en": "Test English Name 123"})
    print(f"PUT 响应: code={put_resp.get('code')} msg={put_resp.get('message')}")

    # Step 3: 再次读取验证
    get2 = api("GET", f"/api/pi/items/{item_id}")
    en_after = get2.get("detail_desc_en", "N/A")
    print(f"保存后 detail_desc_en = {en_after!r}")
    print(f"保存成功: {en_after == 'Test English Name 123'}")
