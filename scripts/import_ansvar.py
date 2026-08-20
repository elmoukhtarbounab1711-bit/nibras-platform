"""
استيراد القوانين المغربية الرسمية من قاعدة بيانات Ansvar MCP إلى نبراس.

المصدر: @ansvar/moroccan-law-mcp (GitHub) — بيانات مُستخرجة من sgg.gov.ma و legislation.gov.ma
الرخصة: Domain public (النشرات الرسمية المغربية)
3,946 قانون + 61,351 مادة + 106 تعريف قانوني
"""
import re
import sqlite3
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\Users\Bounab\Documents\Default Project\nibras-backend")

from app import tenant_scope
from app.database import db_session

ANSVAR_DB = r"C:\Users\Bounab\AppData\Local\Temp\opencode\ansvar\node_modules\@ansvar\moroccan-law-mcp\data\database.db"

SOURCE_NOTE = (
    "نص رسمي مستخرج من قاعدة بيانات Moroccan Law MCP "
    "(@ansvar/moroccan-law-mcp) — المصدر: sgg.gov.ma و legislation.gov.ma. "
    "البيانات مُوثّقة ومُتحقّقة من المصادر الرسمية."
)

# خريطة أنماط معرفات الوثائق -> (category_slug, category_name, text_type)
ID_PATTERNS = [
    # مدونات قانونية كبرى
    ("ma-code-penal",           "jinai",    "القانون الجنائي",           "code"),
    ("ma-doc",                  "madani",   "قانون الالتزامات والعقود",  "code"),
    ("ma-code-commerce",        "tijari",   "القانون التجاري",           "code"),
    ("ma-code-travail",         "shughl",   "قانون الشغل",              "code"),
    ("ma-droit-civil",          "madani",   "القانون المدني",            "code"),
    # أنماط معرفات عدالة
    ("ma-adala-administrative", "idari",    "القانون الإداري",           "law"),
    ("ma-adala-family",         "usra",     "قانون الأسرة",             "law"),
    ("ma-adala-criminal",       "jinai",    "القانون الجنائي",           "law"),
    ("ma-adala-commercial",     "tijari",   "القانون التجاري",           "law"),
    ("ma-adala-labor",          "shughl",   "قانون الشغل",              "law"),
    ("ma-adala-travail",        "shughl",   "قانون الشغل",              "law"),
    ("ma-adala-finance",        "mali",     "القانون المالي والجبائي",   "law"),
    ("ma-adala-education",      "tarbiya",  "قانون التربية والتعليم",    "law"),
    ("ma-adala-culture",        "thaqafa",  "قانون الثقافة والإعلام",     "law"),
    ("ma-adala-health",         "sihha",    "قانون الصحة والحماية الاجتماعية", "law"),
    ("ma-adala-environment",    "biaa",     "قانون البيئة",              "law"),
    ("ma-adala-transport",      "naql",     "قانون النقل",              "law"),
    ("ma-adala-energy",         "taqa",     "قانون الطاقة",              "law"),
    ("ma-adala-agriculture",    "filaha",   "قانون الفلاحة",            "law"),
    ("ma-adala-tax",            "mali",     "القانون المالي والجبائي",   "law"),
    ("ma-adala-housing",        "aqari",    "القانون العقاري",           "law"),
    ("ma-adala-justice",        "qadhai",   "القضاء والمحاكم",          "law"),
    ("ma-adala-constitutional", "dostouri", "القانون الدستوري",          "law"),
    ("ma-adala-rights",         "huquq",    "قانون الحقوق والحريات",     "law"),
    ("ma-adala-judiciary",      "qadhai",   "القضاء والمحاكم",          "law"),
    # أنماط معرفات عامة
    ("ma-loi",                  "qawanin",  "القوانين",                 "law"),
    ("ma-decret",               "marasim",  "المراسيم",                "decree"),
    ("ma-decree",               "marasim",  "المراسيم",                "decree"),
    ("ma-dahir",                "dhawahir", "الظهائر",                 "dahir"),
    ("ma-arrete",               "marasim",  "المراسيم",                "decree"),
    ("ma-decision",             "qararat",  "القرارات",                "decision"),
    ("ma-circulaire",           "idari",    "القانون الإداري",           "law"),
]

# فئات احتياطية (fallback)
FALLBACK_CATEGORIES = {
    "cybersecurity": ("raqami", "قانون المعاملات الإلكترونية"),
    "digital":       ("raqami", "قانون المعاملات الإلكترونية"),
    "tax":           ("mali",   "القانون المالي والجبائي"),
    "environmental": ("biaa",   "قانون البيئة"),
    "agricultural":  ("filaha", "قانون الفلاحة"),
    "education":     ("tarbiya", "قانون التربية والتعليم"),
    "health":        ("sihha",  "قانون الصحة والحماية الاجتماعية"),
}


def _classify(doc_id: str, title: str) -> tuple:
    """يُعيد (category_slug, category_name, text_type) بناءً على معرف الوثيقة والعنوان."""
    lower_id = doc_id.lower()
    for pattern, slug, name, ttype in ID_PATTERNS:
        if lower_id.startswith(pattern):
            return slug, name, ttype
    # fallback: تحليل العنوان
    title_lower = title.lower()
    for kw, (slug, name) in FALLBACK_CATEGORIES.items():
        if kw in title_lower or kw in lower_id:
            return slug, name, "law"
    return "qawanin", "القوانين", "law"


def _fix_encoding(text: str) -> str:
    """إصلاح مشاكل الترميز الشائعة في بيانات Ansvar (Latin-1 mojibake)."""
    replacements = {
        "¶": "'", "\\": "'", "œ": "oe",
        "m": "é", "n": "è", "o": "ê", "p": "ë",
        "r": "à", "s": "â", "t": "ä", "u": "ã",
        "g": "é", "h": "è", "i": "ê",
        "À": "É", "Á": "É",
        "[": "è",
    }
    # لا نُصلح إلا إذا كان النص فرنسيًا (لا يحتوي على حروف عربية)
    if re.search(r"[\u0600-\u06FF]", text):
        return text
    result = text
    for old, new in replacements.items():
        result = result.replace(old, new)
    # إصلاح الأرقام المعكوسة
    def fix_num(m):
        return m.group(0)[::-1]
    result = re.sub(r"\d{2,}", fix_num, result)
    return result


def _ensure_categories(conn, needed_slugs: set):
    """يُنشئ الفئات المطلوبة إذا لم تكن موجودة."""
    for slug in needed_slugs:
        exists = conn.execute(
            "SELECT 1 FROM categories WHERE slug = ?", (slug,)
        ).fetchone()
        if not exists:
            # نبحث عن الاسم من ID_PATTERNS
            name = slug
            for _, s, n, _ in ID_PATTERNS:
                if s == slug:
                    name = n
                    break
            conn.execute(
                "INSERT OR IGNORE INTO categories (slug, name, description, tenant_id) "
                "VALUES (?, ?, ?, 1)",
                (slug, name, "قوانين رسمية مغربية مستخرجة من المصادر الحكومية"),
            )


def _text_exists(conn, title: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM legal_texts WHERE title = ? LIMIT 1", (title,)
    ).fetchone() is not None


def main():
    ansvar = sqlite3.connect(ANSVAR_DB)
    ansvar.row_factory = sqlite3.Row
    ac = ansvar.cursor()

    # جلب الوثائق التي لها مواد
    ac.execute("""
        SELECT d.id, d.title, d.type, d.issued_date, d.status,
               COUNT(p.id) as provision_count
        FROM legal_documents d
        JOIN legal_provisions p ON p.document_id = d.id
        WHERE p.content IS NOT NULL AND length(p.content) > 10
        GROUP BY d.id
        HAVING provision_count > 0
        ORDER BY provision_count DESC
    """)
    docs = ac.fetchall()
    print(f"وثائق في Ansvar لها مواد: {len(docs)}")

    # تحديد الفئات المطلوبة
    needed_slugs = set()
    for doc in docs:
        slug, _, _ = _classify(doc["id"], doc["title"])
        needed_slugs.add(slug)

    print(f"فئات مطلوبة: {len(needed_slugs)}")

    with db_session() as conn:
        _ensure_categories(conn, needed_slugs)

    # استيراد
    ok_count = 0
    skip_count = 0
    err_count = 0
    total_articles = 0
    t0 = time.monotonic()

    for i, doc in enumerate(docs, 1):
        doc_id = doc["id"]
        title = doc["title"]
        slug, cat_name, text_type = _classify(doc_id, title)

        with db_session() as conn:
            # تخطي إذا كان موجودًا
            if _text_exists(conn, title):
                skip_count += 1
                continue

            cat = conn.execute(
                "SELECT id FROM categories WHERE slug = ?", (slug,)
            ).fetchone()
            if not cat:
                err_count += 1
                continue

            # جلب المواد
            ac2 = ansvar.cursor()
            ac2.execute(
                "SELECT provision_ref, title, content, chapter, section "
                "FROM legal_provisions WHERE document_id = ? AND content IS NOT NULL "
                "AND length(content) > 10 ORDER BY id",
                (doc_id,),
            )
            provisions = ac2.fetchall()

            if not provisions:
                skip_count += 1
                continue

            # إدراج النص القانوني
            enacted = doc["issued_date"] or None
            cur = conn.execute(
                """INSERT INTO legal_texts
                   (category_id, type, title, official_ref, enacted_date,
                    last_amended, source_note, is_sample_data, tenant_id,
                    description)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    cat[0], text_type, title, doc_id, enacted,
                    None, SOURCE_NOTE, 0,
                    tenant_scope.insert_tenant_id(),
                    (doc["description"] if "description" in doc.keys() else None) or None,
                ),
            )
            text_id = cur.lastrowid

            # إدراج المواد
            art_count = 0
            for prov in provisions:
                ref = prov["provision_ref"] or ""
                # استخراج رقم المادة
                num_match = re.search(r"(\d+)", ref)
                number = num_match.group(1) if num_match else ref
                label = prov["title"] or f"المادة {number}"
                content = _fix_encoding(prov["content"] or "")
                if len(content.strip()) < 5:
                    continue
                conn.execute(
                    "INSERT INTO articles (legal_text_id, number, label, content, "
                    "plain_explanation, keywords, tenant_id) VALUES (?,?,?,?,?,?,?)",
                    (text_id, number, label, content, None, None,
                     tenant_scope.insert_tenant_id()),
                )
                art_count += 1

            total_articles += art_count
            ok_count += 1

        if i % 100 == 0 or i == len(docs):
            el = time.monotonic() - t0
            print(
                f"[{i}/{len(docs)}] ok={ok_count} skip={skip_count} "
                f"err={err_count} articles={total_articles} "
                f"elapsed={el/60:.1f}m",
                flush=True,
            )

    ansvar.close()
    print(f"\n=== ملخص الاستيراد ===")
    print(f"وثائق مستوردة: {ok_count}")
    print(f"مُتجاهَلة (موجودة مسبقًا): {skip_count}")
    print(f"أخطاء: {err_count}")
    print(f"مواد مستوردة: {total_articles}")


if __name__ == "__main__":
    main()
