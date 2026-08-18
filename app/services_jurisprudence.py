"""
خدمات الاجتهادات القضائية (مرحلة الفقه القضائي — وحدة غير مُغيِّرة).

فئات الاجتهادات (jurisprudence_categories: مدني، جنائي، إداري، عقاري، ...)
وقرارات/اجتهادات المحاكم (jurisprudence: العنوان، مبدأ الحكم، نص الاجتهاد،
المحكمة، رقم/تاريخ القرار، المصدر). بحث نصي كامل عبر FTS5 (نفس نمط
articles_fts في المرحلة 14) للبحث بالكلمة في العنوان والمبدأ والنص والمصدر،
مع تصفية حسب الفئة، ترتيب الأحدث أولًا، وجرد المشاهدات. النشر (published)
إداري حصري؛ العموم يقرؤون المنشور فقط.
"""
import sqlite3

from . import arabic_text, tenant_scope
from .database import db_session

# فئات الاجتهادات الافتراضية (داخل نطاق كل مستأجر — بذر idempotent)
CATEGORY_SEED = (
    ("madani", "القانون المدني"),
    ("jinai", "القانون الجنائي"),
    ("idari", "القانون الإداري"),
    ("aqari", "القانون العقاري"),
    ("usra", "قانون الأسرة"),
    ("tijari", "القانون التجاري"),
    ("mcostara-madaniya", "قانون المسطرة المدنية"),
    ("mcostara-jinaiya", "قانون المسطرة الجنائية"),
    ("shari3a", "قانون الشغل"),
    ("dariba", "الجبايات والضرائب"),
    ("mnawaa", "مواضيع أخرى"),
)

DEFAULT_LIST_LIMIT = 12
MAX_LIST_LIMIT = 100


class JurisprudenceError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def ensure_defaults():
    """بذر فئات الاجتهادات إن كانت فارغة (idempotent — نمط ensure_defaults)."""
    with db_session() as conn:
        count = conn.execute(
            "SELECT COUNT(*) AS c FROM jurisprudence_categories"
        ).fetchone()["c"]
        if count == 0:
            for slug, name in CATEGORY_SEED:
                conn.execute(
                    "INSERT INTO jurisprudence_categories (slug, name, tenant_id) "
                    "VALUES (?, ?, ?)",
                    (slug, name, tenant_scope.insert_tenant_id()),
                )


def _category_slug_to_id(conn, slug: str, jurisdiction_id=None):
    """يعثر على فئة بسلugها ضمن نطاق ولاية (أو الفئات العامة NULL للمغرب)."""
    query = "SELECT id FROM jurisprudence_categories WHERE slug = ?"
    params = [slug]
    if jurisdiction_id is not None:
        query += " AND jurisdiction_id = ?"
        params.append(int(jurisdiction_id))
    else:
        query += " AND jurisdiction_id IS NULL"
    cond, vals = tenant_scope.tenant_eq()
    if cond:
        query += " AND " + cond
        params.extend(vals)
    row = conn.execute(query, params).fetchone()
    return row["id"] if row else None


def _jurisdiction_exists(conn, jurisdiction_id):
    query = "SELECT 1 FROM law_jurisdictions WHERE id = ?"
    params = [jurisdiction_id]
    cond, vals = tenant_scope.tenant_eq()
    if cond:
        query += " AND " + cond
        params.extend(vals)
    return conn.execute(query, params).fetchone() is not None


def _decision_columns() -> str:
    return (
        """SELECT j.id, j.category_id, j.title, j.principles, j.content,
                 j.court, j.decision_number, j.decision_date, j.source_note,
                 j.pdf_url, j.published, j.views, j.created_at, j.updated_at,
                 j.jurisdiction_id,
                 c.slug AS category_slug, c.name AS category_name
           FROM jurisprudence j
           JOIN jurisprudence_categories c ON c.id = j.category_id"""
    )


def list_categories(jurisdiction_id=None):
    """فئات الاجتهادات مع عدد الاجتهادات المنشورة في كل واحدة.

    jurisdiction_id=أي ولاية → فئاتها المستقلة؛ بلا تحديد → الفئات العامة
    (تراث المغرب). كلُّ دولة مرتبة بفئات مستقلة عن غيرها (قرار D-042).
    """
    sub_count = (
        "SELECT COUNT(*) FROM jurisprudence j2 WHERE j2.category_id = c.id "
        "AND j2.published = 1"
    )
    sub_cond, sub_vals = tenant_scope.tenant_eq("j2")
    if sub_cond:
        sub_count += " AND " + sub_cond
    query = f"SELECT c.*, ({sub_count}) AS decision_count FROM jurisprudence_categories c"
    params = list(sub_vals)
    conditions = []
    if jurisdiction_id is not None:
        conditions.append("c.jurisdiction_id = ?")
        params.append(int(jurisdiction_id))
    else:
        conditions.append("c.jurisdiction_id IS NULL")
    cond, vals = tenant_scope.tenant_eq("c")
    if cond:
        conditions.append(cond)
        params.extend(vals)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY c.id"
    with db_session() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def list_decisions(category_slug=None, jurisdiction_id=None,
                   limit: int = DEFAULT_LIST_LIMIT, offset: int = 0):
    """قائمة الاجتهادات المنشورة (المخصصة للعموم)، الأحدث أولًا."""
    limit = max(1, min(int(limit or DEFAULT_LIST_LIMIT), MAX_LIST_LIMIT))
    offset = max(0, int(offset or 0))
    conditions = ["j.published = 1"]
    params = []
    cond, vals = tenant_scope.tenant_eq("j")
    if cond:
        conditions.append(cond)
        params.extend(vals)
    if category_slug:
        conditions.append("c.slug = ?")
        params.append(category_slug)
    if jurisdiction_id:
        conditions.append("j.jurisdiction_id = ?")
        params.append(int(jurisdiction_id))
    else:
        # صفحة الاجتهادات العامة حكر على المغرب (القانون المقارن معزول).
        conditions.append("j.jurisdiction_id IS NULL")
    where = " WHERE " + " AND ".join(conditions)
    count_q = (
        "SELECT COUNT(*) AS c FROM jurisprudence j "
        "JOIN jurisprudence_categories c ON c.id = j.category_id" + where
    )
    query = _decision_columns() + where
    query += " ORDER BY j.created_at DESC, j.id DESC LIMIT ? OFFSET ?"
    with db_session() as conn:
        total = conn.execute(count_q, params).fetchone()["c"]
        rows = conn.execute(query, params + [limit, offset]).fetchall()
        decisions = [dict(r) for r in rows]
        return {"count": total, "decisions": decisions}


def get_decision(decision_id: int):
    """تفصيل قرار؛ فقط المنشور يُعاد للعموم، مع زيادة عدّاد المشاهدات."""
    query = _decision_columns() + " WHERE j.id = ? AND j.published = 1"
    params = [decision_id]
    cond, vals = tenant_scope.tenant_eq("j")
    if cond:
        query += " AND " + cond
        params.extend(vals)
    with db_session() as conn:
        row = conn.execute(query, params).fetchone()
        if not row:
            return None
        upd = "UPDATE jurisprudence SET views = views + 1 WHERE id = ?"
        upd_params = [decision_id]
        u_cond, u_vals = tenant_scope.tenant_eq()
        if u_cond:
            upd += " AND " + u_cond
            upd_params.extend(u_vals)
        conn.execute(upd, upd_params)
        decision = dict(row)
        decision["views"] += 1
        return decision


def search_decisions(query_text: str, category_slug=None, limit: int = 20):
    """بحث نصي بالكلمة عبر FTS5 في الاجتهادات (نمط search_articles من المكتبة).

    يستخدم نفس مسار التطبيع (nbr_normalize) وبناء المصطلحات
    (build_search_terms / build_fts_query) الخاص ببحث المواد — يطابق فقط
    الاجتهادات المنشورة.
    """
    if not query_text or not query_text.strip():
        return []

    term_groups = arabic_text.build_search_terms(query_text)
    if not term_groups:
        return []

    with db_session() as conn:
        try:
            probe = " OR ".join(
                arabic_text.group_fts_or(candidates) for candidates in term_groups
            )
            hits = {
                row[0]
                for row in conn.execute(
                    "SELECT rowid FROM jurisprudence_fts "
                    "WHERE jurisprudence_fts MATCH ?",
                    (probe,),
                ).fetchall()
            }
        except sqlite3.OperationalError:
            hits = set()
        if not hits:
            return []
        term_groups = [
            g for g in term_groups
            if conn.execute(
                "SELECT 1 FROM jurisprudence_fts WHERE jurisprudence_fts MATCH ? LIMIT 1",
                (arabic_text.group_fts_or(g),),
            ).fetchone()
        ]
        if not term_groups:
            return []
        fts_query = arabic_text.build_fts_query(term_groups)
        try:
            base = """SELECT j.id, j.title, j.principles, j.content, j.court,
                             j.decision_number, j.decision_date, j.source_note,
                             j.pdf_url, j.views, c.name AS category_name,
                             c.slug AS category_slug,
                             bm25(jurisprudence_fts) AS rank
                      FROM jurisprudence_fts
                      JOIN jurisprudence j ON j.id = jurisprudence_fts.rowid
                      JOIN jurisprudence_categories c ON c.id = j.category_id
                      WHERE jurisprudence_fts MATCH ? AND j.published = 1"""
            params = [fts_query]
            for alias in ("j", "c"):
                cond, vals = tenant_scope.tenant_eq(alias)
                if cond:
                    base += " AND " + cond
                    params.extend(vals)
            base += " AND j.jurisdiction_id IS NULL"
            if category_slug:
                base += " AND c.slug = ?"
                params.append(category_slug)
            base += " ORDER BY rank LIMIT ?"
            params.append(limit)
            rows = conn.execute(base, params).fetchall()
            if not rows and len(term_groups) >= 2:
                group_scores = []
                for g in term_groups:
                    cnt = conn.execute(
                        "SELECT COUNT(*) FROM jurisprudence_fts "
                        "WHERE jurisprudence_fts MATCH ?",
                        (arabic_text.group_fts_or(g),),
                    ).fetchone()[0]
                    group_scores.append((g, 1.0 / (1.0 + cnt)))
                fts_or = " OR ".join(
                    f"({arabic_text.group_fts_or(g)})" for g in term_groups
                )
                or_rows = conn.execute(
                    base, [fts_or] + params[1:-1] + [limit * 20]
                ).fetchall()
                scored = []
                for row in or_rows:
                    score = 0.0
                    for g, w in group_scores:
                        hit = conn.execute(
                            "SELECT 1 FROM jurisprudence_fts WHERE rowid=? AND "
                            "jurisprudence_fts MATCH ? LIMIT 1",
                            (row[0], arabic_text.group_fts_or(g)),
                        ).fetchone()
                        if hit:
                            score += w
                    if score:
                        scored.append((score, row))
                scored.sort(key=lambda x: x[0], reverse=True)
                rows = [r for _, r in scored][:limit] or rows
        except sqlite3.OperationalError:
            like_q = f"%{arabic_text.normalize_arabic(query_text.strip())}%"
            base = """SELECT j.id, j.title, j.principles, j.content, j.court,
                             j.decision_number, j.decision_date, j.source_note,
                             j.pdf_url, j.views, c.name AS category_name,
                             c.slug AS category_slug, 0 AS rank
                      FROM jurisprudence j
                      JOIN jurisprudence_categories c ON c.id = j.category_id
                      WHERE j.published = 1 AND (
                          j.title LIKE ? OR j.principles LIKE ?
                          OR j.content LIKE ? OR j.source_note LIKE ?)"""
            params = [like_q, like_q, like_q, like_q]
            for alias in ("j", "c"):
                cond, vals = tenant_scope.tenant_eq(alias)
                if cond:
                    base += " AND " + cond
                    params.extend(vals)
            base += " AND j.jurisdiction_id IS NULL"
            if category_slug:
                base += " AND c.slug = ?"
                params.append(category_slug)
            base += " ORDER BY j.views DESC LIMIT ?"
            params.append(limit)
            rows = conn.execute(base, params).fetchall()
        return [dict(r) for r in rows]


def jurisprudence_stats():
    """إحصائيات عامة للاجتهادات: الفئات، عدد الاجتهادات، آخر تحديث."""
    cat_cond, cat_vals = tenant_scope.tenant_eq("c")
    dec_cond, dec_vals = tenant_scope.tenant_eq("j")
    with db_session() as conn:
        q = "SELECT COUNT(*) FROM jurisprudence_categories c"
        if cat_cond:
            q += " WHERE " + cat_cond
        categories = conn.execute(q, cat_vals).fetchone()[0]

        q = "SELECT COUNT(*) FROM jurisprudence j WHERE j.published = 1 AND j.jurisdiction_id IS NULL"
        if dec_cond:
            q += " AND " + dec_cond
        decisions = conn.execute(q, dec_vals).fetchone()[0]

        row = conn.execute(
            "SELECT MAX(COALESCE(decision_date, created_at)) FROM jurisprudence "
            "WHERE jurisdiction_id IS NULL"
        ).fetchone()[0]
    return {"categories": categories, "decisions": decisions,
            "last_update": row or None}


# ---------------------------------------------------------------------------
# إدارة الاجتهادات والفئات (admin فقط)
# ---------------------------------------------------------------------------

def create_decision(admin_id: int, data: dict) -> dict:
    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()
    if not title:
        raise JurisprudenceError("عنوان الاجتهاد (title) مطلوب.", 400)
    if not content:
        raise JurisprudenceError("نص الاجتهاد (content) مطلوب.", 400)
    published = 1 if data.get("published", True) else 0
    jurisdiction_id = None
    if data.get("jurisdiction_id") not in (None, ""):
        try:
            jurisdiction_id = int(data.get("jurisdiction_id"))
        except (TypeError, ValueError):
            raise JurisprudenceError("jurisdiction_id يجب أن يكون رقمًا.", 400)
    with db_session() as conn:
        category_slug = (data.get("category_slug") or "").strip() or None
        category_id = None
        if category_slug:
            category_id = _category_slug_to_id(conn, category_slug, jurisdiction_id)
            if category_id is None:
                category_id = _category_slug_to_id(conn, category_slug, None)
            if category_id is None:
                raise JurisprudenceError("الفئة غير موجودة.", 400)
        if jurisdiction_id is not None and not _jurisdiction_exists(conn, jurisdiction_id):
            raise JurisprudenceError("الولاية القضائية غير موجودة.", 400)
        cur = conn.execute(
            """INSERT INTO jurisprudence
               (category_id, title, principles, content, court, decision_number,
                decision_date, source_note, pdf_url, published, views,
                jurisdiction_id, tenant_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)""",
            (category_id, title, (data.get("principles") or ""),
             content, (data.get("court") or ""),
             (data.get("decision_number") or ""),
             (data.get("decision_date") or None),
             (data.get("source_note") or ""),
             (data.get("pdf_url") or ""), published,
             jurisdiction_id, tenant_scope.insert_tenant_id()),
        )
        decision_id = cur.lastrowid
        from .services_admin import _log_admin_action

        _log_admin_action(
            conn, admin_id, "jurisprudence.create", "jurisprudence",
            decision_id, f"title={title[:60]}",
        )
    return {"id": decision_id, "message": "تم إنشاء الاجتهاد."}


def update_decision(admin_id: int, decision_id: int, data: dict) -> dict:
    updates = {}
    for field in ("title", "principles", "content", "court",
                  "decision_number", "source_note", "pdf_url"):
        if field in data:
            value = (data.get(field) or "").strip()
            updates[field] = value or None
    if "decision_date" in data:
        value = (data.get("decision_date") or "").strip()
        updates["decision_date"] = value or None
    if "published" in data:
        updates["published"] = 1 if data["published"] else 0
    if "jurisdiction_id" in data:
        value = data.get("jurisdiction_id")
        if value in (None, ""):
            updates["jurisdiction_id"] = None
        else:
            try:
                jid = int(value)
            except (TypeError, ValueError):
                raise JurisprudenceError("jurisdiction_id يجب أن يكون رقمًا.", 400)
            with db_session() as conn:
                if not _jurisdiction_exists(conn, jid):
                    raise JurisprudenceError("الولاية القضائية غير موجودة.", 404)
            updates["jurisdiction_id"] = jid
    if not updates:
        raise JurisprudenceError("لا توجد حقول للتحديث.", 400)
    with db_session() as conn:
        row = conn.execute(
            "SELECT id, jurisdiction_id FROM jurisprudence WHERE id = ?",
            (decision_id,),
        ).fetchone()
        if row is None:
            raise JurisprudenceError("الاجتهاد غير موجود.", 404)
        if "category_slug" in data:
            slug = (data.get("category_slug") or "").strip() or None
            if slug:
                cat_id = _category_slug_to_id(conn, slug, row["jurisdiction_id"])
                if cat_id is None:
                    cat_id = _category_slug_to_id(conn, slug, None)
                if cat_id is None:
                    raise JurisprudenceError("الفئة غير موجودة.", 400)
                updates["category_id"] = cat_id
            else:
                updates["category_id"] = None
        sets = ", ".join(f"{k} = ?" for k in updates)
        upd_q = (
            f"UPDATE jurisprudence SET {sets}, updated_at = datetime('now') "
            "WHERE id = ?"
        )
        upd_params = list(updates.values()) + [decision_id]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            upd_q += " AND " + cond
            upd_params.extend(vals)
        conn.execute(upd_q, upd_params)
    return {"id": decision_id, "message": "تم تحديث الاجتهاد."}


def delete_decision(admin_id: int, decision_id: int) -> dict:
    del_q = "DELETE FROM jurisprudence WHERE id = ?"
    del_params = [decision_id]
    cond, vals = tenant_scope.tenant_eq()
    if cond:
        del_q += " AND " + cond
        del_params.extend(vals)
    with db_session() as conn:
        cur = conn.execute(del_q, del_params)
    if cur.rowcount == 0:
        raise JurisprudenceError("الاجتهاد غير موجود.", 404)
    return {"id": decision_id, "message": "تم حذف الاجتهاد."}


def list_decisions_admin(status=None, q=None, limit: int = 50, offset: int = 0):
    """قائمة إدارية للاجتهادات (تشمل غير المنشورة) مع البحث بالعنوان/النص."""
    limit = max(1, min(int(limit or 50), 200))
    offset = max(0, int(offset or 0))
    conditions = ["1=1"]
    params = []
    cond, vals = tenant_scope.tenant_eq("j")
    if cond:
        conditions.append(cond)
        params.extend(vals)
    if status == "published":
        conditions.append("j.published = 1")
    elif status == "draft":
        conditions.append("j.published = 0")
    if q:
        like = f"%{q.strip()}%"
        conditions.append("(j.title LIKE ? OR j.content LIKE ? OR j.court LIKE ?)")
        params += [like, like, like]
    where = " WHERE " + " AND ".join(conditions)
    query = _decision_columns() + where
    query += " ORDER BY j.updated_at DESC, j.id DESC LIMIT ? OFFSET ?"
    params += [limit, offset]
    with db_session() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def set_published(admin_id: int, decision_id: int, published) -> dict:
    with db_session() as conn:
        upd_q = (
            "UPDATE jurisprudence SET published = ?, updated_at = datetime('now') "
            "WHERE id = ?"
        )
        upd_params = [1 if published else 0, decision_id]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            upd_q += " AND " + cond
            upd_params.extend(vals)
        cur = conn.execute(upd_q, upd_params)
    if cur.rowcount == 0:
        raise JurisprudenceError("الاجتهاد غير موجود.", 404)
    return {"id": decision_id, "published": bool(published),
            "message": "تم تحديث حالة النشر."}


def create_category(admin_id: int, data: dict) -> dict:
    name = (data.get("name") or "").strip()
    slug = (data.get("slug") or "").strip().lower()
    if not name:
        raise JurisprudenceError("اسم الفئة (name) مطلوب.", 400)
    if not slug:
        raise JurisprudenceError("slug مطلوب.", 400)
    jurisdiction_id = None
    if data.get("jurisdiction_id") not in (None, ""):
        try:
            jurisdiction_id = int(data.get("jurisdiction_id"))
        except (TypeError, ValueError):
            raise JurisprudenceError("jurisdiction_id يجب أن يكون رقمًا.", 400)
    with db_session() as conn:
        if jurisdiction_id is not None and not _jurisdiction_exists(conn, jurisdiction_id):
            raise JurisprudenceError("الولاية القضائية غير موجودة.", 400)
        if _category_slug_to_id(conn, slug, jurisdiction_id) is not None:
            raise JurisprudenceError("يوجد فئة بهذا slug في هذه الولاية بالفعل.", 409)
        cur = conn.execute(
            "INSERT INTO jurisprudence_categories "
            "(slug, name, description, jurisdiction_id, tenant_id) "
            "VALUES (?, ?, ?, ?, ?)",
            (slug, name, (data.get("description") or ""),
             jurisdiction_id, tenant_scope.insert_tenant_id()),
        )
        category_id = cur.lastrowid
    return {"id": category_id, "message": "تم إنشاء الفئة."}


def update_category(admin_id: int, category_id: int, data: dict) -> dict:
    updates = {}
    if "name" in data:
        name = (data.get("name") or "").strip()
        if not name:
            raise JurisprudenceError("الاسم مطلوب.", 400)
        updates["name"] = name
    if "description" in data:
        updates["description"] = (data.get("description") or "").strip()
    if not updates:
        raise JurisprudenceError("لا توجد حقول للتحديث.", 400)
    with db_session() as conn:
        upd_q = (
            f"UPDATE jurisprudence_categories SET "
            f"{', '.join(f'{k} = ?' for k in updates)} WHERE id = ?"
        )
        upd_params = list(updates.values()) + [category_id]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            upd_q += " AND " + cond
            upd_params.extend(vals)
        cur = conn.execute(upd_q, upd_params)
    if cur.rowcount == 0:
        raise JurisprudenceError("الفئة غير موجودة.", 404)
    return {"id": category_id, "message": "تم تحديث الفئة."}


def delete_category(admin_id: int, category_id: int) -> dict:
    del_q = "DELETE FROM jurisprudence_categories WHERE id = ?"
    del_params = [category_id]
    cond, vals = tenant_scope.tenant_eq()
    if cond:
        del_q += " AND " + cond
        del_params.extend(vals)
    with db_session() as conn:
        cur = conn.execute(del_q, del_params)
    if cur.rowcount == 0:
        raise JurisprudenceError("الفئة غير موجودة.", 404)
    return {"id": category_id, "message": "تم حذف الفئة."}
