"""
طبقة الخدمة (Service Layer): تُترجم منطق العمل إلى استعلامات قاعدة بيانات،
وتُبقي الدوال في routes.py رفيعة ومقتصرة على HTTP فقط.
"""
import sqlite3

from . import arabic_text, tenant_scope
from .database import db_session


def row_to_dict(row):
    return dict(row) if row else None


def list_categories():
    # فئات المكتبة هي فات المغرب الخاص فقط (القانون المقارن معزول في صفحته).
    cond, vals = tenant_scope.tenant_eq()
    sub_count = (
        "SELECT COUNT(*) FROM legal_texts lt2 "
        "WHERE lt2.category_id = c.id AND lt2.jurisdiction_id IS NULL"
    )
    sub_cond, sub_vals = tenant_scope.tenant_eq("lt2")
    if sub_cond:
        sub_count += " AND " + sub_cond
    query = f"""SELECT c.*, ({sub_count}) AS text_count FROM categories c"""
    if cond:
        query += " WHERE " + cond
    query += " ORDER BY c.name"
    # ترتيب العلامات في SQL: أولاً علامة العدّ الفرعي (في SELECT) ثم
    # علامة التصفية الخارجية (في WHERE) — فتُقدَّم قيم الفرعي أولًا.
    params = list(sub_vals) + list(vals)
    with db_session() as conn:
        rows = conn.execute(query, params).fetchall()
        return [row_to_dict(r) for r in rows]


def list_texts(category_slug=None, text_type=None, jurisdiction_id=None,
               limit=None, offset=0):
    # عدد مواد النص يُعد ضمن مستأجر النص نفسه (لا يختلط عبر المستأجرين)
    sub_count = "SELECT COUNT(*) FROM articles a WHERE a.legal_text_id = lt.id"
    sub_cond, sub_vals = tenant_scope.tenant_eq("a")
    if sub_cond:
        sub_count += " AND " + sub_cond

    query = f"""
        SELECT lt.*, c.slug AS category_slug, c.name AS category_name,
               ({sub_count}) AS article_count
        FROM legal_texts lt
        JOIN categories c ON c.id = lt.category_id
        WHERE 1=1
    """
    params = list(sub_vals)
    for alias in ("lt", "c"):
        cond, vals = tenant_scope.tenant_eq(alias)
        if cond:
            query += " AND " + cond
            params.extend(vals)
    if category_slug:
        query += " AND c.slug = ?"
        params.append(category_slug)
    if text_type:
        query += " AND lt.type = ?"
        params.append(text_type)
    if jurisdiction_id:
        query += " AND lt.jurisdiction_id = ?"
        params.append(int(jurisdiction_id))
    else:
        # المكتبة العامة حكر على المغرب (بلا ولاية = الخاص بالدولة الأم).
        query += " AND lt.jurisdiction_id IS NULL"

    # العدد يُحسب على الصفوف نفسها لكن دون تشغيل COUNT الفرعي (يكفي نطاق
    # التصفية والانضمام) — يتجنب تنفيذ COUNT لكل نص عند عدِّ كل الصفحات.
    # فلا تُضمَّن قيم الفرعي (articles) هنا: علامات هذه الجملة هي نطاقات
    # lt و c وفلاتر التصنيف/النوع فقط، بنفس ترتيب بنائها أدناه.
    count_q = """
        SELECT COUNT(*) FROM legal_texts lt
        JOIN categories c ON c.id = lt.category_id
        WHERE 1=1
    """
    count_params = []
    for alias in ("lt", "c"):
        cond, vals = tenant_scope.tenant_eq(alias)
        if cond:
            count_q += " AND " + cond
            count_params.extend(vals)
    if category_slug:
        count_q += " AND c.slug = ?"
        count_params.append(category_slug)
    if text_type:
        count_q += " AND lt.type = ?"
        count_params.append(text_type)
    if jurisdiction_id:
        count_q += " AND lt.jurisdiction_id = ?"
        count_params.append(int(jurisdiction_id))
    else:
        count_q += " AND lt.jurisdiction_id IS NULL"

    order_q = query + " ORDER BY lt.title"
    page_params = list(params)
    if limit is not None:
        order_q += " LIMIT ? OFFSET ?"
        page_params.extend([int(limit), int(offset)])

    with db_session() as conn:
        total = conn.execute(count_q, count_params).fetchone()[0]
        rows = conn.execute(order_q, page_params).fetchall()
        result = [row_to_dict(r) for r in rows]
    for item in result:
        item.pop("uploaded_pdf_key", None)
    if limit is not None:
        return {"count": total, "texts": result}
    return result


def get_text(text_id):
    where = "WHERE lt.id = ?"
    params = [text_id]
    for alias in ("lt", "c"):
        cond, vals = tenant_scope.tenant_eq(alias)
        if cond:
            where += " AND " + cond
            params.extend(vals)
    with db_session() as conn:
        text = conn.execute(
            f"""SELECT lt.*, c.slug AS category_slug, c.name AS category_name
                FROM legal_texts lt JOIN categories c ON c.id = lt.category_id
                {where}""",
            params,
        ).fetchone()
        if not text:
            return None
        articles_q = (
            "SELECT id, number, label FROM articles WHERE legal_text_id = ?"
        )
        articles_params = [text_id]
        a_cond, a_vals = tenant_scope.tenant_eq()
        if a_cond:
            articles_q += " AND " + a_cond
            articles_params.extend(a_vals)
        articles = conn.execute(
            articles_q + " ORDER BY id", articles_params
        ).fetchall()
        result = row_to_dict(text)
        result.pop("uploaded_pdf_key", None)
        result["articles"] = [row_to_dict(a) for a in articles]
        return result


def get_article(article_id):
    where = "WHERE a.id = ?"
    params = [article_id]
    for alias in ("a", "lt", "c"):
        cond, vals = tenant_scope.tenant_eq(alias)
        if cond:
            where += " AND " + cond
            params.extend(vals)
    with db_session() as conn:
        article = conn.execute(
            f"""SELECT a.*, lt.title AS legal_text_title, lt.official_ref, lt.is_sample_data,
                      c.name AS category_name
                FROM articles a
                JOIN legal_texts lt ON lt.id = a.legal_text_id
                JOIN categories c ON c.id = lt.category_id
                {where}""",
            params,
        ).fetchone()
        if not article:
            return None
        related_q = """SELECT a2.id, a2.label, lt2.title AS legal_text_title
                       FROM related_articles ra
                       JOIN articles a2 ON a2.id = ra.related_article_id
                       JOIN legal_texts lt2 ON lt2.id = a2.legal_text_id
                       WHERE ra.article_id = ?"""
        related_params = [article_id]
        a2_cond, a2_vals = tenant_scope.tenant_eq("a2")
        if a2_cond:
            related_q += " AND " + a2_cond
            related_params.extend(a2_vals)
        related = conn.execute(related_q, related_params).fetchall()
        result = row_to_dict(article)
        result["related_articles"] = [row_to_dict(r) for r in related]
        return result


def list_articles(limit=12, offset=0):
    """قائمة المواد الأحدث عبر المكتبة — تُغذي قسم المقالات في الواجهة."""
    query = """
        SELECT a.id, a.number, a.label, a.content, a.plain_explanation,
               a.keywords, COALESCE(a.views, 0) AS views,
               lt.id AS legal_text_id, lt.title AS legal_text_title,
               lt.official_ref, c.name AS category_name, c.slug AS category_slug
        FROM articles a
        JOIN legal_texts lt ON lt.id = a.legal_text_id
        JOIN categories c ON c.id = lt.category_id
        WHERE 1=1
    """
    params = []
    for alias in ("a", "lt", "c"):
        cond, vals = tenant_scope.tenant_eq(alias)
        if cond:
            query += " AND " + cond
            params.extend(vals)
    query += " AND lt.jurisdiction_id IS NULL"
    query += " ORDER BY a.id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    with db_session() as conn:
        return [row_to_dict(r) for r in conn.execute(query, params).fetchall()]


def count_articles():
    """عدد المواد الإجمالي (ضمن نطاق المستأجر الحالي والمغرب فقط)."""
    query = """SELECT COUNT(*) AS c FROM articles a
               JOIN legal_texts lt ON lt.id = a.legal_text_id
               WHERE lt.jurisdiction_id IS NULL"""
    params = []
    for alias in ("a", "lt"):
        cond, vals = tenant_scope.tenant_eq(alias)
        if cond:
            query += " AND " + cond
            params.extend(vals)
    with db_session() as conn:
        return conn.execute(query, params).fetchone()["c"]


def increment_article_views(article_id):
    """زيادة عدّاد مشاهدات المادة عند عرضها (قسم المقالات)."""
    query = "UPDATE articles SET views = COALESCE(views, 0) + 1 WHERE id = ?"
    params = [article_id]
    cond, vals = tenant_scope.tenant_eq()
    if cond:
        query += " AND " + cond
        params.extend(vals)
    with db_session() as conn:
        conn.execute(query, params)


# ---------------------------------------------------------------------------
# ملف PDF المرفوع للقوانين (مرحلة الواجهة): المشرف يرفع ملفًا اختياريًا
# يُفضَّل على الملف المولَّد تلقائيًا عند عرض/تحميل PDF النص القانوني.
# ---------------------------------------------------------------------------

def _laws_upload_dir():
    from pathlib import Path

    from . import config

    if config.UPLOAD_DIR:
        base = Path(config.UPLOAD_DIR)
    else:
        base = Path(__file__).resolve().parent.parent / "uploads"
    return base / "laws"


def get_uploaded_pdf(text_id: int):
    """مسار ملف PDF المرفوع لنص (إن وُجد) — بلا تغيير لحالة التخزين."""
    import os

    query = "SELECT uploaded_pdf_key FROM legal_texts WHERE id = ?"
    params = [text_id]
    cond, vals = tenant_scope.tenant_eq()
    if cond:
        query += " AND " + cond
        params.extend(vals)
    with db_session() as conn:
        row = conn.execute(query, params).fetchone()
    if not row or not row["uploaded_pdf_key"]:
        return None
    key = row["uploaded_pdf_key"]
    path = _laws_upload_dir() / os.path.basename(key)
    if not path.exists():
        return None
    ext = os.path.splitext(key)[1].lower()
    content_type = "application/pdf" if ext == ".pdf" else "application/octet-stream"
    return str(path), key, content_type


def list_text_articles_full(text_id):
    """مواد نص كاملة (content/plain_explanation) — لتوليد PDF النص."""
    query = (
        "SELECT id, number, label, content, plain_explanation, keywords "
        "FROM articles WHERE legal_text_id = ?"
    )
    params = [text_id]
    cond, vals = tenant_scope.tenant_eq()
    if cond:
        query += " AND " + cond
        params.extend(vals)
    query += " ORDER BY id"
    with db_session() as conn:
        return [row_to_dict(r) for r in conn.execute(query, params).fetchall()]


def search_articles(query_text, limit=20, min_terms=None):
    """بحث نصي كامل في المواد القانونية باستخدام FTS5 (المرحلة 14).

    الفهرس يخزّن نصًا مطبَّعًا (بلا تشكيل، ألف موحدة، ة→ه، ى→ي) ويُطبَّع
    الاستعلام بالطريقة نفسها. تُستبعد الكلمات الوظيفية (stopwords)،
    وتُولَّد لكل كلمة متغيّرات "ال" التعريفية (الكلمة / بلا ال / مع ال)
    لالتقاط المطابقات رغم اختلاف التعريف بين الاستعلام والمحتوى.

    min_terms: إن حُدِّد، تُعاد النتائج فقط إذا طابقت عددًا كافيًا من
    الكلمات الفريدة في الفهرس (لمنع "مصدر" واهٍ من كلمة واحدة — تُستخدمه
    واجهة الذكاء الاصطناعي لتفادي الرد على سؤال بمادة لا تغطّيه).
    """
    if not query_text or not query_text.strip():
        return []

    term_groups = arabic_text.build_search_terms(query_text)
    if not term_groups:
        return []

    # تكييف min_terms حسب عدد كلمات الاستعلام الأصلية (قبل حذف ما لا يطابق).
    # استعلام من كلمة واحدة («الطلاق») يكفيه min_terms=1، بينما استعلام من
    # 3 كلمات (كسكس قنطرة 884…) يبقى يشترط تطابق كلمتين على الأقل لرفضه.
    # غياب min_terms (None) يعني لا اشتراط.
    original_count = len(term_groups)
    if min_terms is None:
        min_terms = 1
    else:
        min_terms = min(min_terms, original_count)

    with db_session() as conn:
        try:
            probe = ' OR '.join(
                arabic_text.group_fts_or(candidates) for candidates in term_groups
            )
            hits = {
                row[0]
                for row in conn.execute(
                    "SELECT rowid FROM articles_fts WHERE articles_fts MATCH ?",
                    (probe,),
                ).fetchall()
            }
        except sqlite3.OperationalError:
            hits = set()
        # تُسقط مجموعات الكلمات التي لا تطابق أي مادة في الفهرس حتى لا تُسقط
        # كلمة غائبة عن المكتبة الاستعلامَ كاملًا (مثلاً "كيف" في سؤال طبيعي).
        # تُسقط فقط إذا لم يطابق أي مرادف/متغير في المجموعة — فيُحتفظ بمجموعة
        # «الطلاق» لأن «التطليق» موجود في الفهرس.
        if not hits:
            return []
        term_groups = [
            g for g in term_groups
            if conn.execute(
                "SELECT 1 FROM articles_fts WHERE articles_fts MATCH ? LIMIT 1",
                (arabic_text.group_fts_or(g),),
            ).fetchone()
        ]
        if not term_groups:
            return []
        if len(term_groups) < min_terms:
            return []
        fts_query = arabic_text.build_fts_query(term_groups)
        try:
            base = """SELECT a.id, a.label, a.content, a.plain_explanation,
                             lt.id AS legal_text_id, lt.title AS legal_text_title,
                             lt.type AS text_type, lt.official_ref,
                             c.name AS category_name,
                             bm25(articles_fts) AS rank
                      FROM articles_fts
                      JOIN articles a ON a.id = articles_fts.rowid
                      JOIN legal_texts lt ON lt.id = a.legal_text_id
                      JOIN categories c ON c.id = lt.category_id
                      WHERE articles_fts MATCH ?"""
            params = [fts_query]
            for alias in ("a", "lt", "c"):
                cond, vals = tenant_scope.tenant_eq(alias)
                if cond:
                    base += " AND " + cond
                    params.extend(vals)
            base += " AND lt.jurisdiction_id IS NULL"
            base += " ORDER BY rank LIMIT ?"
            params.append(limit)
            rows = conn.execute(base, params).fetchall()
            # احتياطي OR: إن أخفق الاستعلام الصارم (AND عبر كل الكلمات) ولم
            # تجتمع كل الكلمات في مادة واحدة، تُعاد النتائج الأقرب. تُقيَّم
            # كل مادة بوزن ندرة المجموعات التي تطابقها (idf): مادة تطابق
            # «الطلاق» (19 مادة) أولى من مادة تطابق «حكم»+«القانون» (آلاف)
            # مهما عددها — فيتصدر الطلاق. ويُكتفى بشرط min_terms على عدد
            # المجموعات الباقية أعلاه (كسكس قنطرة 884… أسقطه).
            if not rows and len(term_groups) >= 2:
                group_scores = []
                for g in term_groups:
                    cnt = conn.execute(
                        "SELECT COUNT(*) FROM articles_fts WHERE articles_fts "
                        "MATCH ?",
                        (arabic_text.group_fts_or(g),),
                    ).fetchone()[0]
                    group_scores.append(
                        (g, 1.0 / (1.0 + cnt))
                    )
                fts_or = ' OR '.join(
                    f'({arabic_text.group_fts_or(g)})' for g in term_groups
                )
                or_rows = conn.execute(
                    base, [fts_or] + params[1:-1] + [limit * 20]
                ).fetchall()
                scored = []
                for row in or_rows:
                    score = 0.0
                    for g, w in group_scores:
                        hit = conn.execute(
                            "SELECT 1 FROM articles_fts WHERE rowid=? AND "
                            "articles_fts MATCH ? LIMIT 1",
                            (row[0], arabic_text.group_fts_or(g)),
                        ).fetchone()
                        if hit:
                            score += w
                    if score:
                        scored.append((score, row))
                scored.sort(key=lambda x: x[0], reverse=True)
                rows = [r for _, r in scored][:limit] or rows
        except sqlite3.OperationalError:
            # fallback: بحث بسيط بـ LIKE إن فشل استعلام FTS (مثلاً لرموز خاصة)
            like_q = f"%{arabic_text.normalize_arabic(query_text.strip())}%"
            base = """SELECT a.id, a.label, a.content, a.plain_explanation,
                             lt.title AS legal_text_title, c.name AS category_name, 0 AS rank
                      FROM articles a
                      JOIN legal_texts lt ON lt.id = a.legal_text_id
                      JOIN categories c ON c.id = lt.category_id
                      WHERE a.content LIKE ? OR a.keywords LIKE ? OR a.label LIKE ?"""
            params = [like_q, like_q, like_q]
            for alias in ("a", "lt", "c"):
                cond, vals = tenant_scope.tenant_eq(alias)
                if cond:
                    base += " AND " + cond
                    params.extend(vals)
            base += " AND lt.jurisdiction_id IS NULL"
            base += " LIMIT ?"
            params.append(limit)
            rows = conn.execute(base, params).fetchall()
        return [row_to_dict(r) for r in rows]


def search_texts_by_title(query_text, limit=20):
    """بحث عنوان النصوص القانونية (FTS أو LIKE) — يُستخدم كفهرسة بديلة
    عندما لا تكون هناك مواد في الفهرس."""
    if not query_text or not query_text.strip():
        return []
    normalized = arabic_text.normalize_arabic(query_text.strip())
    with db_session() as conn:
        like_q = f"%{normalized}%"
        where = "WHERE lt.title LIKE ?"
        params = [like_q]
        for alias in ("lt", "c"):
            cond, vals = tenant_scope.tenant_eq(alias)
            if cond:
                where += " AND " + cond
                params.extend(vals)
        where += " AND lt.jurisdiction_id IS NULL"
        q = f"""SELECT lt.id AS legal_text_id, lt.title AS legal_text_title,
                       lt.type AS text_type, lt.official_ref,
                       c.name AS category_name, 0 AS rank
                FROM legal_texts lt
                JOIN categories c ON c.id = lt.category_id
                {where}
                ORDER BY lt.title
                LIMIT ?"""
        params.append(limit)
        rows = conn.execute(q, params).fetchall()
        return [row_to_dict(r) for r in rows]


def library_stats():
    """إحصائيات عامة للمكتبة: الفئات، النصوص، المواد، القرارات/الوثائق، آخر تحديث."""
    cat_cond, cat_vals = tenant_scope.tenant_eq("c")
    txt_cond, txt_vals = tenant_scope.tenant_eq("lt")
    art_cond, art_vals = tenant_scope.tenant_eq("a")
    stats = {"categories": 0, "texts": 0, "articles": 0, "decisions": 0}
    with db_session() as conn:
        q = "SELECT COUNT(*) FROM categories c"
        if cat_cond:
            q += " WHERE " + cat_cond
        stats["categories"] = conn.execute(q, cat_vals).fetchone()[0]

        q = "SELECT COUNT(*) FROM legal_texts lt WHERE lt.jurisdiction_id IS NULL"
        if txt_cond:
            q += " AND " + txt_cond
        stats["texts"] = conn.execute(q, txt_vals).fetchone()[0]

        q = """SELECT COUNT(*) FROM articles a
               JOIN legal_texts lt ON lt.id = a.legal_text_id
               WHERE lt.jurisdiction_id IS NULL"""
        if art_cond:
            q += " AND " + art_cond
        stats["articles"] = conn.execute(q, art_vals).fetchone()[0]

        q = ("SELECT COUNT(*) FROM legal_texts lt "
             "WHERE lt.type IN ('decision', 'document') "
             "AND lt.jurisdiction_id IS NULL")
        if txt_cond:
            q += " AND " + txt_cond
        stats["decisions"] = conn.execute(q, txt_vals).fetchone()[0]

        row = conn.execute(
            "SELECT MAX(COALESCE(last_amended, enacted_date)) FROM legal_texts "
            "WHERE jurisdiction_id IS NULL"
        ).fetchone()[0]
        stats["last_update"] = row or None
    return stats
