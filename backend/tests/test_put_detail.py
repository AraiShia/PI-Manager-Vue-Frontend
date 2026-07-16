import urllib.request
import json

BASE = "http://localhost:8001"
ITEM_ID = 1

def api(method, path, body=None):
    url = BASE + path
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read()), r.status

# PUT
payload = {"detail_desc_en": "TestEN123"}
resp, status = api("PUT", f"/api/pi/items/{ITEM_ID}", payload)
print(f"PUT /api/pi/items/{ITEM_ID} status={status}")
print("  resp:", json.dumps(resp, ensure_ascii=False))

# GET
resp2, _ = api("GET", f"/api/pi/items/{ITEM_ID}")
print(f"\nGET /api/pi/items/{ITEM_ID}")
print("  detail_desc_en:", resp2.get("detail_desc_en"))
print("  保存成功:", resp2.get("detail_desc_en") == "TestEN123")
