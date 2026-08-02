"""
اختبارات تحسينات البحث العربي (المرحلة 14 — قرار D-032).

تغطي: تطبيع النص (تشكيل/ألف/تاء مربوطة/ألف مقصورة)، متغيّرات "ال"
التعريفية وحروف العطف الملتصقة، استبعاد الكلمات الوظيفية، ترحيل فهرس
FTS القديم (المرتبط بجدول خارجي) إلى الصيغة المطبَّعة، وسلوك البحث
عبر واجهة المكتبة.
"""
import sqlite3

from app import arabic_text, database, services
from app.database import db_session

# ---------------------------------------------------------------------------
# تطبيع النص
# ---------------------------------------------------------------------------

def test_normalize_removes_diacritics_and_tatweel():
    assert arabic_text.normalize_arabic("الْعَمَلِ") == "العمل"
    assert arabic_text.normalize_arabic("قانونـ") == "قانون"


def test_normalize_unifies_alef_hamza():
    assert arabic_text.normalize_arabic("إسلام أَحْمَد آدم") == "اسلام احمد ادم"


def test_normalize_taa_marbuta_and_alef_maqsura():
    assert arabic_text.normalize_arabic("مؤسسة مدينة") == "موسسه مدينه"


def test_normalize_handles_none():
    assert arabic_text.normalize_arabic(None) == ""
    assert arabic_text.normalize_arabic(42) == "42"


# ---------------------------------------------------------------------------
# متغيّرات التعريف وحروف العطف
# ---------------------------------------------------------------------------

def test_article_variants_bare_and_defined():
    assert "العقد" in arabic_text.article_variants("عقد")
    assert "عقد" in arabic_text.article_variants("العقد")
    assert arabic_text.article_variants("عقد")[0] == "عقد"


def test_article_variants_prefixed_and_conjunctions():
    variants = arabic_text.article_variants("بالعمل")
    assert variants[0] == "بالعمل"
    assert "عمل" in variants
    assert "العمل" in variants
    assert "والعمل" in variants
    assert "البالعمل" not in variants
    assert "بالمشغل" in arabic_text.article_variants("مشغل")
    assert "والمشغل" in arabic_text.article_variants("مشغل")


def test_article_variants_no_broken_lam_alef():
    variants = arabic_text.article_variants("للمادة")
    assert "لالعمل" not in variants
    assert "الللمادة" not in variants
    assert "للعمل" in arabic_text.article_variants("عمل")


def test_build_search_terms_filters_stopwords():
    groups = arabic_text.build_search_terms("في على من مبدأ العقد")
    words = {term for group in groups for term in group}
    assert "في" not in words and "علي" not in words and "من" not in words
    assert "مبدا" in words and "العقد" in words


def test_build_fts_query_groups_or_and_and():
    query = arabic_text.build_fts_query([["عقد", "العقد"], ["عمل"]])
    assert '"عقد"*' in query and '"العقد"*' in query
    assert '"عمل"*' in query
    assert " OR " in query and " AND " in query


# ---------------------------------------------------------------------------
# سلوك البحث
# ---------------------------------------------------------------------------

def _insert_article(content, keywords=""):
    with db_session() as conn:
        cid = conn.execute(
            "INSERT INTO categories (slug, name) VALUES ('c','مدني')"
        ).lastrowid
        lt = conn.execute(
            "INSERT INTO legal_texts (category_id, type, title) VALUES (?, 'code', 'قانون')",
            (cid,),
        ).lastrowid
        return conn.execute(
            """INSERT INTO articles (legal_text_id, number, label, content, keywords)
               VALUES (?, '1', 'المادة 1', ?, ?)""",
            (lt, content, keywords),
        ).lastrowid


def test_search_finds_bare_query_against_defined_content(fresh_db):
    _insert_article("العامل في القطاع الخاص يستحق أجرا")
    results = services.search_articles("عامل")
    assert any(r["content"] == "العامل في القطاع الخاص يستحق أجرا"
               for r in results)


def test_search_finds_defined_query_against_bare_content(fresh_db):
    _insert_article("يعتبر العقد العمل التزاما بين الطرفين")
    results = services.search_articles("العقد")
    assert any(r["content"].startswith("يعتبر") for r in results)


def test_search_handles_conjoined_content_token(fresh_db):
    _insert_article("تنظم العلاقة بين الأجير والمشغل")
    results = services.search_articles("أجير مشغل")
    assert any(r["content"].startswith("تنظم") for r in results)


def test_search_conjoined_query_matches_defined_content(fresh_db):
    _insert_article("يحدد القانون التزامات الأجير والمشغل")
    results = services.search_articles("ومشغل")
    assert any(r["content"].startswith("يحدد") for r in results)


def test_search_diacritics_insensitive(fresh_db):
    article_id = _insert_article("القَانُونُ يُنظِّم الشَّغْلَ")
    results = services.search_articles("القانون")
    assert any(r["id"] == article_id for r in results)


def test_search_hamza_variant(fresh_db):
    _insert_article("يحدد القانون أدنى أجر في القطاع الخاص")
    results = services.search_articles("ادنى")
    assert any("القطاع" in r["content"] for r in results)


def test_search_taa_marbuta_variant(fresh_db):
    _insert_article("مكافأة نهاية الخدمة")
    results = services.search_articles("مكافاه")
    assert any("الخدمة" in r["content"] for r in results)


def test_search_stopwords_only_returns_empty(fresh_db):
    assert services.search_articles("في على من") == []


def test_search_match_through_keywords_column(fresh_db):
    article_id = _insert_article("بعض النص القانوني", keywords="إلغاء,فسخ")
    results = services.search_articles("فسخ")
    assert any(r["id"] == article_id for r in results)


# ---------------------------------------------------------------------------
# ترحيل الفهرس القديم
# ---------------------------------------------------------------------------

def test_fts_migration_rebuilds_external_content_index(fresh_db, tmp_path):
    old_path = tmp_path / "legacy.db"
    conn = sqlite3.connect(old_path)
    conn.executescript("""
        CREATE TABLE categories (id INTEGER PRIMARY KEY AUTOINCREMENT, slug TEXT,
            name TEXT, description TEXT);
        CREATE TABLE legal_texts (id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL REFERENCES categories(id), type TEXT NOT NULL,
            title TEXT NOT NULL, official_ref TEXT, enacted_date TEXT, last_amended TEXT,
            source_note TEXT, is_sample_data INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE articles (id INTEGER PRIMARY KEY AUTOINCREMENT,
            legal_text_id INTEGER NOT NULL REFERENCES legal_texts(id) ON DELETE CASCADE,
            number TEXT NOT NULL, label TEXT NOT NULL, content TEXT NOT NULL,
            plain_explanation TEXT, keywords TEXT);
        CREATE VIRTUAL TABLE articles_fts USING fts5(
            label, content, keywords, content='articles', content_rowid='id');
        CREATE TRIGGER articles_ai AFTER INSERT ON articles BEGIN
            INSERT INTO articles_fts(rowid,label,content,keywords)
            VALUES (new.id,new.label,new.content,new.keywords); END;
        CREATE TRIGGER articles_ad AFTER DELETE ON articles BEGIN
            INSERT INTO articles_fts(articles_fts,rowid,label,content,keywords)
            VALUES ('delete',old.id,old.label,old.content,old.keywords); END;
        CREATE TRIGGER articles_au AFTER UPDATE ON articles BEGIN
            INSERT INTO articles_fts(articles_fts,rowid,label,content,keywords)
            VALUES ('delete',old.id,old.label,old.content,old.keywords);
            INSERT INTO articles_fts(rowid,label,content,keywords)
            VALUES (new.id,new.label,new.content,new.keywords); END;
    """)
    conn.execute("INSERT INTO categories (slug,name) VALUES ('c','مدني')")
    cid = conn.execute("SELECT id FROM categories").fetchone()[0]
    conn.execute(
        "INSERT INTO legal_texts (category_id,type,title) VALUES (?,'code','قانون')",
        (cid,),
    )
    lt = conn.execute("SELECT id FROM legal_texts").fetchone()[0]
    conn.execute(
        "INSERT INTO articles (legal_text_id,number,label,content,keywords) "
        "VALUES (?, '1', 'المادة 1', 'الأجير والمشغل', '')",
        (lt,),
    )
    conn.commit()
    conn.close()

    saved = database.DB_PATH
    database.DB_PATH = old_path
    try:
        database.init_db(reset=False)
        sql = database.sqlite3.connect(old_path).execute(
            "SELECT sql FROM sqlite_master WHERE name='articles_fts'"
        ).fetchone()[0]
        assert "content='articles'" not in sql
        results = services.search_articles("أجير مشغل")
        assert [r["label"] for r in results] == ["المادة 1"]
    finally:
        database.DB_PATH = saved
