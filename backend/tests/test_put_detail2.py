import urllib.request, json
url = "http://localhost:8001/api/pi/items/1"
req = urllib.request.Request(url, data=json.dumps({'detail_desc_en': 'TestEN456'}).encode(), method='PUT', headers={'Content-Type': 'application/json'})
try:
    r = urllib.request.urlopen(req)
    print(r.status, r.read().decode())
except Exception as e:
    print("ERR", e, getattr(e, 'code', None))
    print(e.read().decode() if hasattr(e, 'read') else '')
