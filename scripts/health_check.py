import requests, sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = "https://nibras-law-platforme.vercel.app"

# Check categories
r = requests.get(f"{BASE}/api/categories", timeout=15)
cats = r.json()
print(f"Categories: {len(cats)}")
for c in cats[:5]:
    print(f"  {c.get('slug')}: text_count={c.get('text_count','MISSING')} name={c.get('name','')}")

# Check if text_count is populated for any category
has_count = [c for c in cats if c.get('text_count') and c.get('text_count') > 0]
print(f"\nCategories with text_count > 0: {len(has_count)}")

# Check category qawanin
qawanin = [c for c in cats if c.get('slug') == 'qawanin']
if qawanin:
    print(f"qawanin category: {json.dumps(qawanin[0], ensure_ascii=False)[:200]}")

# Test library cat page
r = requests.get(f"{BASE}/api/texts?limit=3&category=qawanin", timeout=15)
data = r.json()
print(f"\nTexts in qawanin: count={data.get('count')}")

# Check all API endpoints that frontend uses
print("\n--- Endpoint Status ---")
endpoints = [
    "/api/library/stats",
    "/api/categories",
    "/api/texts?limit=1",
    "/api/texts?limit=1&category=qawanin",
    "/api/jurisprudence?limit=1",
    "/api/search?q=قانون",
    "/api/texts/10049",
    "/api/texts/10049/pdf",
]
for ep in endpoints:
    try:
        r = requests.get(f"{BASE}{ep}", timeout=10, allow_redirects=False)
        status = r.status_code
        if ep.endswith("/pdf"):
            status = f"{status} -> {r.headers.get('Location','')[:50]}"
        print(f"  {ep}: {status}")
    except Exception as e:
        print(f"  {ep}: ERROR {e}")
