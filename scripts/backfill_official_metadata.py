"""
تسطير البصمات وبيانات المصدر للنصوص القانونية الموجودة.

هذا السكريبت يُشغَّل مرة واحدة لملء الحقول الجديدة:
- content_hash على legal_texts و articles
- source_name, official_source على legal_texts
- official_text_raw على articles ( = content الحالي)
"""
import hashlib
import sys
import os

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))

from app.database import db_session, DB_PATH

print(f"Database: {DB_PATH}")
print(f"Size: {os.path.getsize(str(DB_PATH)) / 1024 / 1024:.1f} MB")


def content_hash(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def main():
    # ═══════════════════════════════════════════════════════════════════════
    # 1. تسطير بصمات المواد (articles.content_hash + official_text_raw)
    # ═══════════════════════════════════════════════════════════════════════
    print("\n=== تسطير بصمات المواد ===")
    with db_session() as conn:
        articles = conn.execute(
            "SELECT id, content, official_text_raw FROM articles "
            "WHERE content_hash IS NULL"
        ).fetchall()
        print(f"مواد بلا بصمة: {len(articles)}")
        updated_articles = 0
        for art in articles:
            c_hash = content_hash(art["content"])
            raw = art["official_text_raw"] if art["official_text_raw"] else art["content"]
            conn.execute(
                "UPDATE articles SET content_hash = ?, official_text_raw = ? WHERE id = ?",
                (c_hash, raw, art["id"]),
            )
            updated_articles += 1
            if updated_articles % 5000 == 0:
                print(f"  ... {updated_articles}/{len(articles)}")
        print(f"  تم تحديث {updated_articles} مادة")

    # ═══════════════════════════════════════════════════════════════════════
    # 2. تسطير بصمات النصوص القانونية (legal_texts.content_hash)
    # ═══════════════════════════════════════════════════════════════════════
    print("\n=== تسطير بصمات النصوص القانونية ===")
    with db_session() as conn:
        texts = conn.execute(
            "SELECT id FROM legal_texts WHERE content_hash IS NULL"
        ).fetchall()
        print(f"نصوص بلا بصمة: {len(texts)}")
        updated_texts = 0
        for txt in texts:
            arts = conn.execute(
                "SELECT content FROM articles WHERE legal_text_id = ? ORDER BY number",
                (txt["id"],),
            ).fetchall()
            if arts:
                combined = "\n\n".join(a["content"] for a in arts)
                c_hash = content_hash(combined)
                conn.execute(
                    "UPDATE legal_texts SET content_hash = ? WHERE id = ?",
                    (c_hash, txt["id"]),
                )
                updated_texts += 1
            if updated_texts % 500 == 0 and updated_texts > 0:
                print(f"  ... {updated_texts}/{len(texts)}")
        print(f"  تم تحديث {updated_texts} نص قانوني")

    # ═══════════════════════════════════════════════════════════════════════
    # 3. ملء بيانات المصدر بناءً على source_note
    # ═══════════════════════════════════════════════════════════════════════
    print("\n=== ملء بيانات المصدر ===")
    source_patterns = {
        "ansvar": ("Ansvar MCP — sgg.gov.ma / legislation.gov.ma", 1),
        "عدالة": ("وزارة العدل المغربية — عدالة", 1),
        "وزارة العدل": ("وزارة العدل المغربية — عدالة", 1),
        "sgg.gov.ma": ("الأمانة العامة للحكومة — الجريدة الرسمية", 1),
        "الجريدة الرسمية": ("الأمانة العامة للحكومة — الجريدة الرسمية", 1),
        "legislation.gov.ma": ("منصة التشريع المغربي", 1),
    }
    with db_session() as conn:
        texts_no_source = conn.execute(
            "SELECT id, source_note, title FROM legal_texts "
            "WHERE source_name IS NULL AND is_sample_data = 0"
        ).fetchall()
        print(f"نصوص بلا مصدر مُسجَّل: {len(texts_no_source)}")
        updated_source = 0
        for txt in texts_no_source:
            note = (txt["source_note"] or "").lower()
            title = (txt["title"] or "").lower()
            for pattern, (source_name, is_official) in source_patterns.items():
                if pattern.lower() in note or pattern.lower() in title:
                    conn.execute(
                        "UPDATE legal_texts SET source_name = ?, official_source = ? WHERE id = ?",
                        (source_name, is_official, txt["id"]),
                    )
                    updated_source += 1
                    break
        print(f"  تم تحديث {updated_source} نص بمصدر رسمي")

    # ═══════════════════════════════════════════════════════════════════════
    # 4. إحصائيات نهائية
    # ═══════════════════════════════════════════════════════════════════════
    print("\n=== إحصائيات نهائية ===")
    with db_session() as conn:
        total_texts = conn.execute("SELECT COUNT(*) FROM legal_texts").fetchone()[0]
        total_articles = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        texts_with_hash = conn.execute(
            "SELECT COUNT(*) FROM legal_texts WHERE content_hash IS NOT NULL"
        ).fetchone()[0]
        articles_with_hash = conn.execute(
            "SELECT COUNT(*) FROM articles WHERE content_hash IS NOT NULL"
        ).fetchone()[0]
        articles_with_raw = conn.execute(
            "SELECT COUNT(*) FROM articles WHERE official_text_raw IS NOT NULL"
        ).fetchone()[0]
        texts_with_source = conn.execute(
            "SELECT COUNT(*) FROM legal_texts WHERE source_name IS NOT NULL AND is_sample_data = 0"
        ).fetchone()[0]
        texts_official = conn.execute(
            "SELECT COUNT(*) FROM legal_texts WHERE official_source = 1"
        ).fetchone()[0]

        print(f"نصوص قانونية: {total_texts}")
        print(f"  - بصمة محسوبة: {texts_with_hash}")
        print(f"  - مصدر مُسجَّل: {texts_with_source}")
        print(f"  - مصدر رسمي: {texts_official}")
        print(f"مواد قانونية: {total_articles}")
        print(f"  - بصمة محسوبة: {articles_with_hash}")
        print(f"  - نص أصلي محفوظ: {articles_with_raw}")

    print("\n✅ تم الانتهاء بنجاح")


if __name__ == "__main__":
    main()
