"""
خدمات بوابة المقالات القانونية (مرحلة الواجهة — وحدة إضافية غير مُغيِّرة).

مقالات كاملة (عنوان/غلاف/تصنيف/كلمات مفتاحية/جسم) بحالة نشر إدارية
(pending|published|hidden) وعدّادات مشاهدات/إعجابات/تعليقات، وردود فعل
(إعجاب بتّ، تعليقات، بلاغات) بنمط موحّد. أي مستخدم مسجَّل ينشئ مقالًا
(يبدأ pending)؛ النشر (published) إداري حصري. شارة "مهني موثق" في بطاقة
المقال تُستقى من حالة التحقق المهني للمؤلِّف (professional_profiles).
"""
import sqlite3

from . import tenant_scope
from .database import db_session

# فئات بوابة المقالات (مستقلة عن فئات مكتبة النصوص والمجتمع — قرار D-024)
# فئات قانونية موضوعية + فئة "الدراسات المقارنة" المرتبطة بالدول.
CATEGORY_SEED = (
    ("madani", "المدني"),
    ("jinai", "الجنائي"),
    ("idari", "الإداري"),
    ("tijari", "التجاري"),
    ("dostouri", "الدستوري"),
    ("ijtimai", "الاجتماعي"),
    ("ahwal-shakhsiya", "الأحوال الشخصية"),
    ("mali", "المالي"),
    ("ijrai-aqari", "الإجرائي العقاري"),
    ("comparative", "الدراسات المقارنة"),
)

COMPARATIVE_CATEGORY_SLUG = "comparative"

DEFAULT_LIST_LIMIT = 12
MAX_LIST_LIMIT = 100

STATUSES = ("pending", "published", "hidden")


class BlogError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def ensure_defaults():
    """بذر فئات المقالات الناقصة (idempotent — تُدرج المفقود فقط)."""
    with db_session() as conn:
        existing = {
            r["slug"] for r in conn.execute(
                "SELECT slug FROM blog_categories"
            ).fetchall()
        }
        for slug, name in CATEGORY_SEED:
            if slug not in existing:
                conn.execute(
                    "INSERT INTO blog_categories (slug, name, tenant_id) "
                    "VALUES (?, ?, ?)",
                    (slug, name, tenant_scope.insert_tenant_id()),
                )


def _category_exists(conn, category_id) -> bool:
    query = "SELECT 1 FROM blog_categories WHERE id = ?"
    params = [category_id]
    cond, vals = tenant_scope.tenant_eq()
    if cond:
        query += " AND " + cond
        params.extend(vals)
    return conn.execute(query, params).fetchone() is not None


def _category_slug(conn, category_id) -> str:
    query = "SELECT slug FROM blog_categories WHERE id = ?"
    params = [category_id]
    cond, vals = tenant_scope.tenant_eq()
    if cond:
        query += " AND " + cond
        params.extend(vals)
    row = conn.execute(query, params).fetchone()
    return row["slug"] if row else None


def _comparative_jurisdiction_exists(conn, jurisdiction_id) -> bool:
    query = ("SELECT 1 FROM law_jurisdictions "
             "WHERE id = ? AND is_comparative = 1")
    params = [jurisdiction_id]
    cond, vals = tenant_scope.tenant_eq()
    if cond:
        query += " AND " + cond
        params.extend(vals)
    return conn.execute(query, params).fetchone() is not None


def _resolve_jurisdiction(conn, category_slug, raw):
    """يجعل اختيار الدولة حصرًا على فئة «الدراسات المقارنة».

    عودة: jurisdiction_id (عدد أو None) أو IOException للفئة غير المقارنة.
    """
    if raw in (None, ""):
        jurisdiction_id = None
    else:
        try:
            jurisdiction_id = int(raw)
        except (TypeError, ValueError):
            raise BlogError("jurisdiction_id يجب أن يكون رقمًا.", 400)
    if category_slug == COMPARATIVE_CATEGORY_SLUG:
        if jurisdiction_id is None:
            raise BlogError(
                "أخبر الدولة القضائية عند اختيار فئة الدراسات المقارنة.", 400)
        if not _comparative_jurisdiction_exists(conn, jurisdiction_id):
            raise BlogError("الدولة القضائية غير موجودة.", 400)
    elif jurisdiction_id is not None:
        raise BlogError(
            "اختيار الدولة مخصص لفئة الدراسات المقارنة فقط.", 400)
    return jurisdiction_id


def _author_fields(conn, user_id: int) -> dict:
    """اسم المؤلِّف وشارة التحقق المهني (من ملفه المهني المصدَّق)."""
    verified_q = (
        """SELECT EXISTS (
               SELECT 1 FROM professional_profiles p
               JOIN user_roles ur ON ur.user_id = p.user_id
               JOIN roles r ON r.id = ur.role_id
               WHERE p.user_id = ? AND p.verification_status = 'verified'
                 AND r.code IN ('lawyer','notary','adoul','judicial_commissioner',
                                'sworn_translator','judicial_expert')
           ) AS ok"""
    )
    params = [user_id]
    cond, vals = tenant_scope.tenant_eq("p")
    if cond:
        verified_q = (
            """SELECT EXISTS (
                   SELECT 1 FROM professional_profiles p
                   JOIN user_roles ur ON ur.user_id = p.user_id
                   JOIN roles r ON r.id = ur.role_id
                   WHERE p.user_id = ? AND p.verification_status = 'verified'
                     AND r.code IN ('lawyer','notary','adoul','judicial_commissioner',
                                    'sworn_translator','judicial_expert')"""
            + f" AND {cond}"
            + "           ) AS ok"
        )
        params.extend(vals)
    verified = conn.execute(verified_q, params).fetchone()["ok"]
    return {"verified": bool(verified)}


def _base_columns(extra: str = "") -> str:
    """أعمدة المقال مع المؤلِّف والتصنيف وعدّادات التفاعلات (عزل D-036)."""
    like_scope = " AND l.tenant_id IS a.tenant_id" if tenant_scope.active() else ""
    com_scope = " AND c.tenant_id IS a.tenant_id" if tenant_scope.active() else ""
    return (
        "SELECT a.id, a.user_id, a.category_id, a.jurisdiction_id, a.title, "
        "a.cover_url, a.summary, "
        "a.body, a.keywords, a.status, a.views, a.published_at, a.created_at, "
        "a.updated_at, u.full_name AS author_name, "
        "COALESCE((SELECT COUNT(*) FROM blog_likes l "
        f"          WHERE l.article_id = a.id{like_scope}), 0) AS like_count, "
        "COALESCE((SELECT COUNT(*) FROM blog_comments c "
        f"          WHERE c.article_id = a.id AND c.status = 'visible'{com_scope}), 0) "
        "AS comment_count, "
        "bc.name AS category_name, bc.slug AS category_slug, "
        "j.name AS jurisdiction_name, j.slug AS jurisdiction_slug"
        + extra
        + " FROM blog_articles a "
        "JOIN users u ON u.id = a.user_id "
        "LEFT JOIN blog_categories bc ON bc.id = a.category_id "
        "LEFT JOIN law_jurisdictions j ON j.id = a.jurisdiction_id"
    )


def _scoped(conn, article: dict) -> dict:
    """يُلحق بيانات المؤلِّف والحالة الذاتية للمقال الواحد."""
    if article is None:
        return None
    article = dict(article)
    article["author"] = {
        "id": article["user_id"],
        "full_name": article.pop("author_name"),
        **_author_fields(conn, article["user_id"]),
    }
    return article


def list_categories():
    query = "SELECT id, slug, name FROM blog_categories"
    params = []
    cond, vals = tenant_scope.tenant_eq()
    if cond:
        query += " WHERE " + cond
        params.extend(vals)
    query += " ORDER BY id"
    with db_session() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def list_articles(category=None, q=None, jurisdiction_id=None,
                  limit: int = DEFAULT_LIST_LIMIT, offset: int = 0):
    """قائمة المقالات المنشورة فقط (الخاصة بالعموم)."""
    limit = max(1, min(int(limit or DEFAULT_LIST_LIMIT), MAX_LIST_LIMIT))
    offset = max(0, int(offset or 0))
    conditions = ["a.status = 'published'"]
    params = []
    cond, vals = tenant_scope.tenant_eq("a")
    if cond:
        conditions.append(cond)
        params.extend(vals)
    if category:
        conditions.append("bc.slug = ?")
        params.append(category)
    if jurisdiction_id:
        conditions.append("a.jurisdiction_id = ?")
        params.append(int(jurisdiction_id))
    if q:
        like = f"%{q.strip()}%"
        conditions.append("(a.title LIKE ? OR a.summary LIKE ? OR a.body LIKE ? "
                          "OR a.keywords LIKE ?)")
        params += [like, like, like, like]
    query = _base_columns() + " WHERE " + " AND ".join(conditions)
    count_q = (
        f"SELECT COUNT(*) AS c FROM blog_articles a "
        f"LEFT JOIN blog_categories bc ON bc.id = a.category_id "
        f"WHERE {' AND '.join(conditions)}"
    )
    query += " ORDER BY a.published_at DESC, a.id DESC LIMIT ? OFFSET ?"
    with db_session() as conn:
        total = conn.execute(count_q, params[: len(conditions)]).fetchone()["c"]
        rows = conn.execute(query, params + [limit, offset]).fetchall()
        articles = [_scoped(conn, dict(r)) for r in rows]
        return {"count": total, "articles": articles}


def list_comparative_articles(jurisdiction_id: int,
                              limit: int = 100, offset: int = 0):
    """مقالات «الدراسات المقارنة» المنشورة لدولة قضائية معينة.

    تُغذّي صفحة الدراسات المقارنة داخل صفحة الولاية في القانون المقارن.
    """
    limit = max(1, min(int(limit or 100), 200))
    offset = max(0, int(offset or 0))
    conditions = [
        "a.status = 'published'",
        "a.jurisdiction_id = ?",
        "bc.slug = ?",
    ]
    params = [int(jurisdiction_id), COMPARATIVE_CATEGORY_SLUG]
    cond, vals = tenant_scope.tenant_eq("a")
    if cond:
        conditions.append(cond)
        params.extend(vals)
    query = _base_columns() + " WHERE " + " AND ".join(conditions)
    query += " ORDER BY a.published_at DESC, a.id DESC LIMIT ? OFFSET ?"
    params += [limit, offset]
    with db_session() as conn:
        rows = conn.execute(query, params).fetchall()
        articles = [_scoped(conn, dict(r)) for r in rows]
        return {"count": len(articles) if offset == 0 else None,
                "articles": articles}


def get_article(article_id: int, viewer_id=None, include_internal=False):
    """تفصيل مقال. العموم لا يرون إلا المنشور؛ صاحبه/المشرف يرون الكل."""
    query = _base_columns() + " WHERE a.id = ?"
    params = [article_id]
    cond, vals = tenant_scope.tenant_eq("a")
    if cond:
        query += " AND " + cond
        params.extend(vals)
    with db_session() as conn:
        row = conn.execute(query, params).fetchone()
        if not row:
            return None
        article = _scoped(conn, dict(row))
        can_manage = include_internal or article["user_id"] == viewer_id
        if article["status"] != "published" and not can_manage:
            return None
        if article["status"] == "published":
            upd = "UPDATE blog_articles SET views = views + 1 WHERE id = ?"
            upd_params = [article_id]
            if cond:
                upd += " AND " + cond
                upd_params.extend(vals)
            conn.execute(upd, upd_params)
            article["views"] += 1
        if viewer_id is not None:
            like_q = (
                "SELECT 1 FROM blog_likes WHERE user_id = ? AND article_id = ?"
            )
            like_params = [viewer_id, article_id]
            l_cond, l_vals = tenant_scope.tenant_eq()
            if l_cond:
                like_q += " AND " + l_cond
                like_params.extend(l_vals)
            article["liked"] = conn.execute(like_q, like_params).fetchone() is not None
        else:
            article["liked"] = False
        return article


def create_article(user_id: int, data: dict, is_admin: bool = False) -> dict:
    title = (data.get("title") or "").strip()
    body = (data.get("body") or "").strip()
    if not title:
        raise BlogError("عنوان المقال (title) مطلوب.", 400)
    if not body:
        raise BlogError("نص المقال (body) مطلوب.", 400)
    category_id = data.get("category_id")
    if category_id not in (None, ""):
        try:
            category_id = int(category_id)
        except (TypeError, ValueError):
            raise BlogError("category_id يجب أن يكون رقمًا.", 400)
    summary = (data.get("summary") or "").strip()
    keywords = (data.get("keywords") or "").strip()
    cover_url = (data.get("cover_url") or "").strip() or None
    status = "published" if is_admin else "pending"
    with db_session() as conn:
        if category_id is not None and not _category_exists(conn, category_id):
            raise BlogError("التصنيف غير موجود.", 400)
        category_slug = _category_slug(conn, category_id) if category_id is not None else None
        jurisdiction_id = _resolve_jurisdiction(
            conn, category_slug, data.get("jurisdiction_id"))
        published_at = "datetime('now')" if status == "published" else "NULL"
        cur = conn.execute(
            f"""INSERT INTO blog_articles
                (user_id, category_id, title, cover_url, summary, body, keywords,
                 status, views, published_at, jurisdiction_id, tenant_id,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, {published_at}, ?, ?,
                        datetime('now'), datetime('now'))""",
            (user_id, category_id, title, cover_url, summary or None, body,
             keywords or None, status, jurisdiction_id,
             tenant_scope.insert_tenant_id()),
        )
        article_id = cur.lastrowid
    return {"id": article_id, "status": status, "message": "تم إنشاء المقال."}


def update_article(actor_id: int, article_id: int, data: dict,
                   is_admin: bool = False) -> dict:
    updates = {}
    for field in ("title", "body", "summary", "keywords", "cover_url"):
        if field in data:
            value = (data.get(field) or "").strip()
            updates[field] = value or None
    if "category_id" in data and data.get("category_id") not in (None, ""):
        updates["category_id"] = int(data["category_id"])
    if "title" in updates and not updates["title"]:
        raise BlogError("عنوان المقال (title) مطلوب.", 400)
    if "body" in updates and not updates["body"]:
        raise BlogError("نص المقال (body) مطلوب.", 400)
    if not updates:
        raise BlogError("لا توجد حقول للتحديث.", 400)
    with db_session() as conn:
        row = _ownership(conn, article_id)
        if row is None:
            raise BlogError("المقال غير موجود.", 404)
        if row["user_id"] != actor_id and not is_admin:
            raise BlogError("لا يمكنك تعديل مقال لا تملكه.", 403)
        cur_cat = conn.execute(
            "SELECT category_id FROM blog_articles WHERE id = ?",
            (article_id,),
        ).fetchone()["category_id"]
        if ("category_id" in updates and updates["category_id"] is not None
                and not _category_exists(conn, updates["category_id"])):
            raise BlogError("التصنيف غير موجود.", 400)
        if "jurisdiction_id" in data or "category_id" in updates:
            effective_slug = _category_slug(
                conn, updates.get("category_id", cur_cat))
            updates["jurisdiction_id"] = _resolve_jurisdiction(
                conn, effective_slug, data.get("jurisdiction_id"))
        sets = ", ".join(f"{k} = ?" for k in updates)
        upd_q = (
            f"UPDATE blog_articles SET {sets}, updated_at = datetime('now') "
            "WHERE id = ?"
        )
        upd_params = list(updates.values()) + [article_id]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            upd_q += " AND " + cond
            upd_params.extend(vals)
        conn.execute(upd_q, upd_params)
    return {"id": article_id, "message": "تم تحديث المقال."}


def delete_article(actor_id: int, article_id: int, is_admin: bool = False) -> dict:
    with db_session() as conn:
        row = _ownership(conn, article_id)
        if row is None:
            raise BlogError("المقال غير موجود.", 404)
        if row["user_id"] != actor_id and not is_admin:
            raise BlogError("لا يمكنك حذف مقال لا تملكه.", 403)
        del_q = "DELETE FROM blog_articles WHERE id = ?"
        del_params = [article_id]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            del_q += " AND " + cond
            del_params.extend(vals)
        conn.execute(del_q, del_params)
    return {"id": article_id, "message": "تم حذف المقال."}


def _ownership(conn, article_id: int):
    query = "SELECT id, user_id FROM blog_articles WHERE id = ?"
    params = [article_id]
    cond, vals = tenant_scope.tenant_eq()
    if cond:
        query += " AND " + cond
        params.extend(vals)
    return conn.execute(query, params).fetchone()


def set_status(admin_id: int, article_id: int, status: str) -> dict:
    if status not in STATUSES:
        raise BlogError(f"status يجب أن يكون أحد: {', '.join(STATUSES)}.", 400)
    with db_session() as conn:
        query = "UPDATE blog_articles SET status = ?, updated_at = datetime('now')"
        params = [status]
        if status == "published":
            query += ", published_at = datetime('now')"
        query += " WHERE id = ?"
        params.append(article_id)
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            query += " AND " + cond
            params.extend(vals)
        cur = conn.execute(query, params)
        if cur.rowcount == 0:
            raise BlogError("المقال غير موجود.", 404)
        from .services_admin import _log_admin_action

        _log_admin_action(
            conn, admin_id, "blog.status", "blog_article", article_id,
            f"status={status}",
        )
    return {"id": article_id, "status": status, "message": "تم تحديث حالة المقال."}


def list_articles_for_user(user_id: int, limit: int = 100, offset: int = 0):
    limit = max(1, min(int(limit or 100), 200))
    offset = max(0, int(offset or 0))
    query = _base_columns() + " WHERE a.user_id = ?"
    params = [user_id]
    cond, vals = tenant_scope.tenant_eq("a")
    if cond:
        query += " AND " + cond
        params.extend(vals)
    query += " ORDER BY a.updated_at DESC, a.id DESC LIMIT ? OFFSET ?"
    params += [limit, offset]
    with db_session() as conn:
        rows = conn.execute(query, params).fetchall()
        return [_scoped(conn, dict(r)) for r in rows]


def list_articles_admin(status=None, q=None, limit: int = 50, offset: int = 0):
    limit = max(1, min(int(limit or 50), 200))
    offset = max(0, int(offset or 0))
    conditions = ["1=1"]
    params = []
    cond, vals = tenant_scope.tenant_eq("a")
    if cond:
        conditions.append(cond)
        params.extend(vals)
    if status:
        conditions.append("a.status = ?")
        params.append(status)
    if q:
        like = f"%{q.strip()}%"
        conditions.append("(a.title LIKE ? OR u.full_name LIKE ?)")
        params += [like, like]
    query = _base_columns() + " WHERE " + " AND ".join(conditions)
    query += " ORDER BY a.updated_at DESC, a.id DESC LIMIT ? OFFSET ?"
    params += [limit, offset]
    with db_session() as conn:
        rows = conn.execute(query, params).fetchall()
        return [_scoped(conn, dict(r)) for r in rows]


def toggle_like(user_id: int, article_id: int) -> dict:
    with db_session() as conn:
        row = _ownership(conn, article_id)
        if row is None:
            raise BlogError("المقال غير موجود.", 404)
        exists_q = "SELECT 1 FROM blog_likes WHERE user_id = ? AND article_id = ?"
        exists_params = [user_id, article_id]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            exists_q += " AND " + cond
            exists_params.extend(vals)
        if conn.execute(exists_q, exists_params).fetchone():
            del_q = "DELETE FROM blog_likes WHERE user_id = ? AND article_id = ?"
            del_params = [user_id, article_id]
            if cond:
                del_q += " AND " + cond
                del_params.extend(vals)
            conn.execute(del_q, del_params)
            liked = False
        else:
            conn.execute(
                "INSERT INTO blog_likes (user_id, article_id, tenant_id, created_at) "
                "VALUES (?, ?, ?, datetime('now'))",
                (user_id, article_id, tenant_scope.insert_tenant_id()),
            )
            liked = True
        count_q = "SELECT COUNT(*) AS c FROM blog_likes WHERE article_id = ?"
        count_params = [article_id]
        if cond:
            count_q += " AND " + cond
            count_params.extend(vals)
        count = conn.execute(count_q, count_params).fetchone()["c"]
    return {"liked": liked, "likes": count}


def list_comments(article_id: int):
    query = (
        """SELECT c.id, c.user_id, c.body, c.created_at, u.full_name AS user_name
           FROM blog_comments c JOIN users u ON u.id = c.user_id
           WHERE c.article_id = ? AND c.status = 'visible'"""
    )
    params = [article_id]
    cond, vals = tenant_scope.tenant_eq("c")
    if cond:
        query += " AND " + cond
        params.extend(vals)
    query += " ORDER BY c.created_at DESC, c.id DESC"
    with db_session() as conn:
        if _ownership(conn, article_id) is None:
            raise BlogError("المقال غير موجود.", 404)
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def add_comment(user_id: int, article_id: int, body: str) -> dict:
    body = (body or "").strip()
    if not body:
        raise BlogError("نص التعليق (body) مطلوب.", 400)
    with db_session() as conn:
        row = conn.execute(
            "SELECT status FROM blog_articles WHERE id = ?", (article_id,)
        ).fetchone()
        if row is None:
            raise BlogError("المقال غير موجود.", 404)
        if row["status"] != "published":
            raise BlogError("المقال غير منشور.", 403)
        cur = conn.execute(
            "INSERT INTO blog_comments (article_id, user_id, body, tenant_id, "
            "created_at) VALUES (?, ?, ?, ?, datetime('now'))",
            (article_id, user_id, body, tenant_scope.insert_tenant_id()),
        )
        comment_id = cur.lastrowid
    return {"id": comment_id, "message": "تمت إضافة التعليق."}


def add_report(reporter_id: int, article_id: int, reason: str) -> dict:
    reason = (reason or "").strip()
    if not reason:
        raise BlogError("سبب البلاغ (reason) مطلوب.", 400)
    with db_session() as conn:
        row = conn.execute(
            "SELECT id FROM blog_articles WHERE id = ?", (article_id,)
        ).fetchone()
        if row is None:
            raise BlogError("المقال غير موجود.", 404)
        try:
            conn.execute(
                "INSERT INTO blog_reports (reporter_id, article_id, reason, "
                "status, tenant_id, created_at) VALUES (?, ?, ?, 'open', ?, "
                "datetime('now'))",
                (reporter_id, article_id, reason,
                 tenant_scope.insert_tenant_id()),
            )
        except sqlite3.IntegrityError:
            raise BlogError("سبق أن بلّغت عن هذا المقال.", 409)
    return {"message": "تم إرسال البلاغ."}


def list_reports(status=None):
    conditions = ["1=1"]
    params = []
    cond, vals = tenant_scope.tenant_eq("br")
    if cond:
        conditions.append(cond)
        params.extend(vals)
    if status:
        conditions.append("br.status = ?")
        params.append(status)
    query = (
        """SELECT br.id, br.reporter_id, br.reason, br.status, br.created_at,
                  a.id AS article_id, a.title AS article_title,
                  ru.full_name AS reporter_name
           FROM blog_reports br
           JOIN blog_articles a ON a.id = br.article_id
           JOIN users ru ON ru.id = br.reporter_id
           WHERE """
        + " AND ".join(conditions)
        + " ORDER BY br.created_at DESC, br.id DESC"
    )
    with db_session() as conn:
        return [dict(r) for r in conn.execute(query, params).fetchall()]


def action_report(admin_id: int, report_id: int, decision: str) -> dict:
    if decision not in ("actioned", "dismissed"):
        raise BlogError("decision يجب أن يكون actioned أو dismissed.", 400)
    with db_session() as conn:
        query = (
            "UPDATE blog_reports SET status = ?, resolved_at = datetime('now'), "
            "resolved_by = ? WHERE id = ?"
        )
        params = [decision, admin_id, report_id]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            query += " AND " + cond
            params.extend(vals)
        cur = conn.execute(query, params)
        if cur.rowcount == 0:
            raise BlogError("البلاغ غير موجود.", 404)
        article_id = conn.execute(
            "SELECT article_id FROM blog_reports WHERE id = ?", (report_id,)
        ).fetchone()["article_id"]
        if decision == "actioned":
            a_upd = (
                "UPDATE blog_articles SET status = 'hidden', "
                "updated_at = datetime('now') WHERE id = ?"
            )
            a_params = [article_id]
            a_cond, a_vals = tenant_scope.tenant_eq()
            if a_cond:
                a_upd += " AND " + a_cond
                a_params.extend(a_vals)
            conn.execute(a_upd, a_params)
    return {"id": report_id, "status": decision, "message": "تمت معالجة البلاغ."}
