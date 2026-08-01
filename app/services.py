"""
طبقة الخدمة (Service Layer): تُترجم منطق العمل إلى استعلامات قاعدة بيانات،
وتُبقي الدوال في routes.py رفيعة ومقتصرة على HTTP فقط.
"""
import sqlite3

from .database import db_session


def row_to_dict(row):
    return dict(row) if row else None


def list_categories():
    with db_session() as conn:
        rows = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
        return [row_to_dict(r) for r in rows]


def list_texts(category_slug=None, text_type=None):
    query = """
        SELECT lt.*, c.slug AS category_slug, c.name AS category_name,
               (SELECT COUNT(*) FROM articles a WHERE a.legal_text_id = lt.id) AS article_count
        FROM legal_texts lt
        JOIN categories c ON c.id = lt.category_id
        WHERE 1=1
    """
    params = []
    if category_slug:
        query += " AND c.slug = ?"
        params.append(category_slug)
    if text_type:
        query += " AND lt.type = ?"
        params.append(text_type)
    query += " ORDER BY lt.title"

    with db_session() as conn:
        rows = conn.execute(query, params).fetchall()
        return [row_to_dict(r) for r in rows]


def get_text(text_id):
    with db_session() as conn:
        text = conn.execute(
            """SELECT lt.*, c.slug AS category_slug, c.name AS category_name
               FROM legal_texts lt JOIN categories c ON c.id = lt.category_id
               WHERE lt.id = ?""",
            (text_id,),
        ).fetchone()
        if not text:
            return None
        articles = conn.execute(
            "SELECT id, number, label FROM articles WHERE legal_text_id = ? ORDER BY id",
            (text_id,),
        ).fetchall()
        result = row_to_dict(text)
        result["articles"] = [row_to_dict(a) for a in articles]
        return result


def get_article(article_id):
    with db_session() as conn:
        article = conn.execute(
            """SELECT a.*, lt.title AS legal_text_title, lt.official_ref, lt.is_sample_data,
                      c.name AS category_name
               FROM articles a
               JOIN legal_texts lt ON lt.id = a.legal_text_id
               JOIN categories c ON c.id = lt.category_id
               WHERE a.id = ?""",
            (article_id,),
        ).fetchone()
        if not article:
            return None
        related = conn.execute(
            """SELECT a2.id, a2.label, lt2.title AS legal_text_title
               FROM related_articles ra
               JOIN articles a2 ON a2.id = ra.related_article_id
               JOIN legal_texts lt2 ON lt2.id = a2.legal_text_id
               WHERE ra.article_id = ?""",
            (article_id,),
        ).fetchall()
        result = row_to_dict(article)
        result["related_articles"] = [row_to_dict(r) for r in related]
        return result


def search_articles(query_text, limit=20):
    """بحث نصي كامل في المواد القانونية باستخدام FTS5.

    ملاحظة: FTS5 لا يتعامل جيدًا مع بعض حروف العلة العربية إن اختلف التشكيل،
    لذلك نطهّر الاستعلام ونحوّله لصيغة بحث عن العبارة كاملة مع بادئة (*)
    لدعم البحث الجزئي عن الكلمات.
    """
    if not query_text or not query_text.strip():
        return []

    # بناء استعلام FTS: كل كلمة منفصلة + بحث بادئة لدعم النتائج الجزئية
    terms = [t.strip() for t in query_text.strip().split() if t.strip()]
    fts_query = " ".join(f'"{t}"*' for t in terms)

    with db_session() as conn:
        try:
            rows = conn.execute(
                """SELECT a.id, a.label, a.content, a.plain_explanation,
                          lt.title AS legal_text_title, c.name AS category_name,
                          bm25(articles_fts) AS rank
                   FROM articles_fts
                   JOIN articles a ON a.id = articles_fts.rowid
                   JOIN legal_texts lt ON lt.id = a.legal_text_id
                   JOIN categories c ON c.id = lt.category_id
                   WHERE articles_fts MATCH ?
                   ORDER BY rank
                   LIMIT ?""",
                (fts_query, limit),
            ).fetchall()
        except sqlite3.OperationalError:
            # fallback: بحث بسيط بـ LIKE إن فشل استعلام FTS (مثلاً لرموز خاصة)
            like_q = f"%{query_text.strip()}%"
            rows = conn.execute(
                """SELECT a.id, a.label, a.content, a.plain_explanation,
                          lt.title AS legal_text_title, c.name AS category_name, 0 AS rank
                   FROM articles a
                   JOIN legal_texts lt ON lt.id = a.legal_text_id
                   JOIN categories c ON c.id = lt.category_id
                   WHERE a.content LIKE ? OR a.keywords LIKE ? OR a.label LIKE ?
                   LIMIT ?""",
                (like_q, like_q, like_q, limit),
            ).fetchall()
        return [row_to_dict(r) for r in rows]
