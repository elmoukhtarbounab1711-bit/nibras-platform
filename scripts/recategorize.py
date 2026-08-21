import sqlite3, requests, sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB = "nibras.db"
API = "https://huquqai.ma/api/laws"

DOC_TYPE_MAP = {
    "قانون": "qawanin",
    "مرسوم": "marasim",
    "ظهير شريف": "dhawahir",
    "قرار": "qararat",
    "اتفاقية": "dawli",
    "رسالة ملكية": "marasim-malakiya",
    "خطاب": "qawanin",
    "رأي": "qadhai",
    "تقرير": "qawanin",
    "دورية": "idari",
    "منشور": "qawanin",
    "أخرى": "qawanin",
}

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

# Get category mapping
cat_rows = conn.execute("SELECT id, slug FROM categories").fetchall()
cat_map = {r["slug"]: r["id"] for r in cat_rows}
print(f"Categories: {len(cat_map)}")

# Build title → text_id map from DB
db_texts = conn.execute("SELECT id, title, category_id FROM legal_texts WHERE category_id = 1852").fetchall()
title_map = {}
for t in db_texts:
    title_map[t["title"]] = t["id"]
print(f"Texts in qawanin: {len(title_map)}")

# Fetch all huquqai data
huquqai = {}
page = 1
while True:
    print(f"Fetching huquqai page {page}...")
    r = requests.get(f"{API}?page={page}&limit=100", timeout=30)
    data = r.json()
    items = data.get("data", [])
    if not items:
        break
    for item in items:
        huquqai[item["title"]] = item.get("document_type", "")
    if page * 100 >= data.get("totalCount", 0):
        break
    page += 1
    time.sleep(0.5)

print(f"Huquqai docs: {len(huquqai)}")

# Match and update
updated = 0
skipped = 0
type_counts = {}
for title, doc_type in huquqai.items():
    if title not in title_map:
        skipped += 1
        continue
    slug = DOC_TYPE_MAP.get(doc_type, "qawanin")
    cat_id = cat_map.get(slug)
    if not cat_id:
        cat_id = cat_map["qawanin"]
    text_id = title_map[title]
    type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
    conn.execute("UPDATE legal_texts SET category_id = ? WHERE id = ?", (cat_id, text_id))
    updated += 1

conn.commit()
print(f"\nUpdated: {updated}, Skipped: {skipped}")
print("\nCategory distribution:")
for dt, cnt in sorted(type_counts.items(), key=lambda x: -x[1]):
    slug = DOC_TYPE_MAP.get(dt, "qawanin")
    print(f"  {dt} → {slug}: {cnt}")

# Verify
print("\nPost-migration counts:")
rows = conn.execute("""
    SELECT c.slug, c.name, COUNT(*) as cnt
    FROM legal_texts lt
    JOIN categories c ON c.id = lt.category_id
    GROUP BY c.slug
    ORDER BY cnt DESC
""").fetchall()
for r in rows:
    print(f"  {r['slug']} ({r['name']}): {r['cnt']}")

conn.close()
