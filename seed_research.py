"""Delete empty categories and reseed ad slots + research."""
import hashlib
import gzip
import shutil
import sqlite3
import sys
sys.path.insert(0, ".")
from app.arabic_text import normalize_arabic

conn = sqlite3.connect("nibras.db")
conn.create_function("nbr_normalize", 1, normalize_arabic, deterministic=True)
conn.execute("PRAGMA foreign_keys = ON")

# 1. Delete empty categories (0 texts)
rows = conn.execute("""
    SELECT c.id, c.slug, c.name, COUNT(t.id) as cnt
    FROM categories c LEFT JOIN legal_texts t ON t.category_id = c.id
    GROUP BY c.id HAVING cnt = 0
""").fetchall()
deleted_ids = []
for r in rows:
    conn.execute("DELETE FROM categories WHERE id = ?", (r[0],))
    deleted_ids.append(r[0])
conn.commit()
print(f"Deleted {len(deleted_ids)} empty categories")

# 2. Seed ad slots (new slot types)
AD_SLOTS = [
    ("header", "الرأسية"),
    ("article_top", "أعلى المقال"),
    ("article_middle", "وسط المقال"),
    ("article_bottom", "أسفل المقال"),
    ("sidebar", "الشريط الجانبي"),
    ("search_results", "نتائج البحث"),
    ("mobile", "الجوال"),
]
existing = [r[0] for r in conn.execute("SELECT slug FROM ad_slots").fetchall()]
for slug, name in AD_SLOTS:
    if slug not in existing:
        conn.execute("INSERT INTO ad_slots (slug, name) VALUES (?, ?)", (slug, name))
conn.commit()

# 3. Verify
total_texts = conn.execute("SELECT COUNT(*) FROM legal_texts").fetchone()[0]
total_cats = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
empty_cats = conn.execute("""
    SELECT c.id, c.slug, c.name FROM categories c
    LEFT JOIN legal_texts t ON t.category_id = c.id
    GROUP BY c.id HAVING COUNT(t.id) = 0
""").fetchall()
total_research = conn.execute("SELECT COUNT(*) FROM research_books").fetchone()[0]
total_slots = conn.execute("SELECT COUNT(*) FROM ad_slots").fetchall()

print(f"\nCategories: {total_cats} ({len(empty_cats)} empty remaining)")
print(f"Texts: {total_texts}")
print(f"Research books: {total_research}")
print(f"Ad slots: {conn.execute('SELECT COUNT(*) FROM ad_slots').fetchone()[0]}")

# List remaining categories with counts
rows = conn.execute("""
    SELECT c.id, c.slug, c.name, COUNT(t.id) as cnt
    FROM categories c LEFT JOIN legal_texts t ON t.category_id = c.id
    GROUP BY c.id ORDER BY cnt DESC
""").fetchall()
for r in rows:
    print(f"  [{r[0]}] {r[1]} ({r[2]}): {r[3]} texts")

conn.close()

# 4. Re-create the gzipped prod DB
print("\nRecreating nibras_prod.db.gz...")
shutil.copyfileobj(
    open("nibras.db", "rb"),
    gzip.open("nibras_prod.db.gz", "wb"),
)
print("Done!")
