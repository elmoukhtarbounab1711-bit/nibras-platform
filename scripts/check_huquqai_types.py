import requests, sys, io, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Check what document_type values exist in huquqai data
types = collections.Counter()
for page in range(1, 10):
    r = requests.get(f"https://huquqai.ma/api/laws?page={page}&limit=100", timeout=15)
    data = r.json()
    for item in data.get("data", []):
        types[item.get("document_type", "UNKNOWN")] += 1
    print(f"Page {page}: {len(data.get('data',[]))} items")

print(f"\nDocument types ({sum(types.values())} total from {sum(1 for _ in range(9))} pages):")
for t, cnt in types.most_common():
    print(f"  {t}: {cnt}")
