import urllib.request

url = "https://github.com/elmoukhtarbounab1711-bit/nibras-platform/releases/download/v1.0/nibras_prod.db.gz"
req = urllib.request.Request(url, headers={"User-Agent": "nibras-bootstrap/1.0"})
try:
    resp = urllib.request.urlopen(req, timeout=30)
    print(f"Status: {resp.status}")
    ct = resp.headers.get("Content-Type", "")
    print(f"Content-Type: {ct}")
    cl = resp.headers.get("Content-Length", "unknown")
    print(f"Content-Length: {cl}")
    data = resp.read(10)
    print(f"First bytes hex: {data[:2].hex()}")
    print("WORKS!")
except Exception as e:
    print(f"FAILED: {e}")
