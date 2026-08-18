"""
خدمات القانون المقارن (المرحلة 20 — قرار D-038).

دراسة مقارنة (comparative_studies) ينشئها أي مستخدم مسجَّل (تبدأ draft)؛
النشر (published)/الإخفاء (hidden) إداري حصري. كل دراسة تضم مقارنات
(comparative_entries) ترجع إلى ولاية قضائية (law_jurisdictions — دول أو
أنظمة مبذورة) وأحيانًا إلى نص ومادة في مكتبة النصوص (legal_texts/articles)
مع ملاحظة الباحث. التصفح العام يرى المنشور فقط؛ مالك الدراسة (أو الإشراف)
يرى كل حالاتها.
"""
from . import tenant_scope
from .database import db_session
from .services_admin import _log_admin_action

# ولايات قضائية مبذورة (idempotent — نمط ensure_defaults)
JURISDICTION_SEED = (
    ("morocco", "المغرب"),
    ("egypt", "مصر"),
    ("france", "فرنسا"),
    ("tunisia", "تونس"),
    ("saudi-arabia", "المملكة العربية السعودية"),
    ("united-arab-emirates", "الإمارات العربية المتحدة"),
    ("jordan", "الأردن"),
    ("qatar", "قطر"),
)

STUDY_STATUSES = ("draft", "published", "hidden")


class ComparativeError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def ensure_defaults():
    """بذر الولايات القضائية إن كانت فارغة (idempotent — نمط ensure_defaults)."""
    with db_session() as conn:
        count = conn.execute(
            "SELECT COUNT(*) AS c FROM law_jurisdictions"
        ).fetchone()["c"]
        if count == 0:
            for slug, name in JURISDICTION_SEED:
                conn.execute(
                    "INSERT INTO law_jurisdictions (slug, name, tenant_id) "
                    "VALUES (?, ?, ?)",
                    (slug, name, tenant_scope.insert_tenant_id()),
                )


def _jurisdiction_exists(conn, jurisdiction_id) -> bool:
    query = "SELECT 1 FROM law_jurisdictions WHERE id = ?"
    params = [jurisdiction_id]
    cond, vals = tenant_scope.tenant_eq()
    if cond:
        query += " AND " + cond
        params.extend(vals)
    return conn.execute(query, params).fetchone() is not None


def _legal_reference_valid(conn, legal_text_id, article_id) -> bool:
    """يتحقق من صحة الإسناد النصي (نص و/أو مادة) ضمن نطاق المستأجر.

    كلاهما فارغ: مقارنة بلا إسناد نصي (ملاحظة الباحث كافية) — صحيحة.
    مادة فقط: تتحقق المادة ووجود نصها.
    نص فقط: يتحقق النص.
    الاثنان: تتحقق المادة وتطابق نصها.
    """
    if legal_text_id is None and article_id is None:
        return True
    if article_id is not None:
        query = (
            "SELECT a.id, a.legal_text_id FROM articles a "
            "JOIN legal_texts lt ON lt.id = a.legal_text_id "
            "WHERE a.id = ?"
        )
        params = [article_id]
        cond, vals = tenant_scope.tenant_eq("a")
        if cond:
            query += " AND " + cond
            params.extend(vals)
        row = conn.execute(query, params).fetchone()
        if row is None:
            return False
        return legal_text_id is None or row["legal_text_id"] == legal_text_id
    # نص فقط
    query = "SELECT 1 FROM legal_texts WHERE id = ?"
    params = [legal_text_id]
    cond, vals = tenant_scope.tenant_eq()
    if cond:
        query += " AND " + cond
        params.extend(vals)
    return conn.execute(query, params).fetchone() is not None


def list_jurisdictions(limit: int = 100, offset: int = 0, include_all: bool = False):
    """ولايات القانون المقارن؛ يستثني المغرب المستقل (is_comparative=0).

    include_all=True يعيد الكل بما فيه المغرب (للوحة الإدارة فقط).
    """
    limit = max(1, min(int(limit or 100), 200))
    offset = max(0, int(offset or 0))
    # عدّادات لكل ولاية (عزل المستأجر D-036): نصوص، اجتهادات منشورة،
    # دراسات فيها مقارنة واحدة على الأقل لهذه الولاية.
    with db_session() as conn:
        query = "SELECT id, slug, name, is_comparative FROM law_jurisdictions"
        conditions = []
        params = []
        if not include_all:
            conditions.append("is_comparative = 1")
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            conditions.append(cond)
            params.extend(vals)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY id LIMIT ? OFFSET ?"
        params += [limit, offset]
        rows = conn.execute(query, params).fetchall()
        jurisdictions = []
        for r in rows:
            item = dict(r)
            jid = item["id"]
            j_scope, j_vals = tenant_scope.tenant_eq("j")
            tq = ("SELECT COUNT(*) FROM legal_texts j "
                  "WHERE j.jurisdiction_id = ?")
            if j_scope:
                tq += " AND " + j_scope
            item["text_count"] = conn.execute(
                tq, [jid] + list(j_vals)).fetchone()[0]
            dq = ("SELECT COUNT(*) FROM jurisprudence j "
                  "WHERE j.jurisdiction_id = ? AND j.published = 1")
            if j_scope:
                dq += " AND " + j_scope
            item["decision_count"] = conn.execute(
                dq, [jid] + list(j_vals)).fetchone()[0]
            sq = ("SELECT COUNT(DISTINCT e.study_id) "
                  "FROM comparative_entries e WHERE e.jurisdiction_id = ?")
            e_scope, e_vals = tenant_scope.tenant_eq("e")
            if e_scope:
                sq += " AND " + e_scope
            item["study_count"] = conn.execute(
                sq, [jid] + list(e_vals)).fetchone()[0]
            jurisdictions.append(item)
        return jurisdictions


def get_jurisdiction_by_slug(slug: str, include_all: bool = False):
    """ولاية قضائية واحدة بسلاugها (لصفحة الولاية في القانون المقارن)."""
    query = ("SELECT id, slug, name, is_comparative FROM law_jurisdictions "
             "WHERE slug = ?")
    params = [slug]
    if not include_all:
        query += " AND is_comparative = 1"
    cond, vals = tenant_scope.tenant_eq()
    if cond:
        query += " AND " + cond
        params.extend(vals)
    with db_session() as conn:
        row = conn.execute(query, params).fetchone()
        if row is None:
            return None
        return dict(row)


def list_jurisdiction_text_categories(jurisdiction_id: int):
    """فئات نصوص الولاية (خاصة بصفحتها): مشتقة من نصوص ديولاية فقط.

    تعيد كل فئة من فئات نصوص هذه الولاية مع عدد نصوصها، دون خلط مع
    الفئات العامة (المغرب) — القواعد والاجتهادات تبقى معزولة (نبراس D-…).
    """
    try:
        jurisdiction_id = int(jurisdiction_id)
    except (TypeError, ValueError):
        raise ComparativeError("jurisdiction_id يجب أن يكون رقمًا.", 400)
    query = (
        "SELECT c.id, c.slug, c.name, COUNT(*) AS count "
        "FROM legal_texts lt JOIN categories c ON c.id = lt.category_id "
        "WHERE lt.jurisdiction_id = ?"
    )
    params = [jurisdiction_id]
    cond, vals = tenant_scope.tenant_eq("lt")
    if cond:
        query += " AND " + cond
        params.extend(vals)
    query += " GROUP BY c.id, c.slug, c.name ORDER BY c.name"
    with db_session() as conn:
        return [dict(r) for r in conn.execute(query, params).fetchall()]


def create_jurisdiction(admin_id: int, data: dict) -> int:
    slug = (data.get("slug") or "").strip().lower()
    name = (data.get("name") or "").strip()
    if not slug or not name:
        raise ComparativeError("slug و name مطلوبان.", 400)
    with db_session() as conn:
        dup = "SELECT 1 FROM law_jurisdictions WHERE slug = ?"
        dup_params = [slug]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            dup += " AND " + cond
            dup_params.extend(vals)
        if conn.execute(dup, dup_params).fetchone():
            raise ComparativeError("يوجد نظام قضائي بنفس slug.", 409)
        cur = conn.execute(
            "INSERT INTO law_jurisdictions (slug, name, tenant_id) "
            "VALUES (?, ?, ?)",
            (slug, name, tenant_scope.insert_tenant_id()),
        )
        jurisdiction_id = cur.lastrowid
        _log_admin_action(
            conn, admin_id, "comparative.jurisdiction.create",
            "law_jurisdiction", jurisdiction_id, f"slug={slug}",
        )
    return jurisdiction_id


def update_jurisdiction(admin_id: int, jurisdiction_id: int, data: dict) -> int:
    updates = {}
    if "slug" in data:
        slug = (data.get("slug") or "").strip().lower()
        if not slug:
            raise ComparativeError("slug مطلوب.", 400)
        updates["slug"] = slug
    if "name" in data:
        name = (data.get("name") or "").strip()
        if not name:
            raise ComparativeError("name مطلوب.", 400)
        updates["name"] = name
    if not updates:
        raise ComparativeError("لا توجد حقول للتحديث.", 400)
    with db_session() as conn:
        sel_q = "SELECT id FROM law_jurisdictions WHERE id = ?"
        sel_params = [jurisdiction_id]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            sel_q += " AND " + cond
            sel_params.extend(vals)
        if conn.execute(sel_q, sel_params).fetchone() is None:
            raise ComparativeError("النظام القضائي غير موجود.", 404)
        if "slug" in updates:
            dup = "SELECT 1 FROM law_jurisdictions WHERE slug = ? AND id != ?"
            dup_params = [updates["slug"], jurisdiction_id]
            if cond:
                dup += " AND " + cond
                dup_params.extend(vals)
            if conn.execute(dup, dup_params).fetchone():
                raise ComparativeError("يوجد نظام قضائي بنفس slug.", 409)
        sets = ", ".join(f"{k} = ?" for k in updates)
        upd_q = f"UPDATE law_jurisdictions SET {sets} WHERE id = ?"
        upd_params = list(updates.values()) + [jurisdiction_id]
        if cond:
            upd_q += " AND " + cond
            upd_params.extend(vals)
        conn.execute(upd_q, upd_params)
        _log_admin_action(
            conn, admin_id, "comparative.jurisdiction.update",
            "law_jurisdiction", jurisdiction_id,
        )
    return jurisdiction_id


def delete_jurisdiction(admin_id: int, jurisdiction_id: int) -> int:
    with db_session() as conn:
        sel_q = "SELECT id FROM law_jurisdictions WHERE id = ?"
        sel_params = [jurisdiction_id]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            sel_q += " AND " + cond
            sel_params.extend(vals)
        if conn.execute(sel_q, sel_params).fetchone() is None:
            raise ComparativeError("النظام القضائي غير موجود.", 404)
        in_use = (
            "SELECT 1 FROM comparative_entries WHERE jurisdiction_id = ? "
            "LIMIT 1"
        )
        in_use_params = [jurisdiction_id]
        e_cond, e_vals = tenant_scope.tenant_eq()
        if e_cond:
            in_use += " AND " + e_cond
            in_use_params.extend(e_vals)
        if conn.execute(in_use, in_use_params).fetchone():
            raise ComparativeError(
                "لا يمكن حذف نظام قضائي مستخدم في دراسات مقارنة.", 409
            )
        del_q = "DELETE FROM law_jurisdictions WHERE id = ?"
        del_params = [jurisdiction_id]
        if cond:
            del_q += " AND " + cond
            del_params.extend(vals)
        conn.execute(del_q, del_params)
        _log_admin_action(
            conn, admin_id, "comparative.jurisdiction.delete",
            "law_jurisdiction", jurisdiction_id,
        )
    return jurisdiction_id


def _base_columns(extra: str = "") -> str:
    """أعمدة الدراسة مع المنشئ وعدد المقارنات (عزل D-036)."""
    return (
        "SELECT s.id, s.user_id, s.title, s.description, s.status, "
        "s.created_at, s.updated_at, u.full_name AS creator_name, "
        "COALESCE((SELECT COUNT(*) FROM comparative_entries e "
        "          WHERE e.study_id = s.id), 0) AS entry_count"
        + extra
        + " FROM comparative_studies s "
        "LEFT JOIN users u ON u.id = s.user_id"
    )


def list_studies(q=None, jurisdiction_id=None, limit: int = 12, offset: int = 0):
    """قائمة الدراسات المنشورة (الخاصة بالعموم)."""
    limit = max(1, min(int(limit or 12), 100))
    offset = max(0, int(offset or 0))
    conditions = ["s.status = 'published'"]
    params = []
    cond, vals = tenant_scope.tenant_eq("s")
    if cond:
        conditions.append(cond)
        params.extend(vals)
    if q:
        like = f"%{q.strip()}%"
        conditions.append("(s.title LIKE ? OR s.description LIKE ? "
                          "OR u.full_name LIKE ?)")
        params += [like, like, like]
    if jurisdiction_id:
        # دراسات تحتوي مقارنة واحدة على الأقل لهذه الولاية
        conditions.append(
            "EXISTS (SELECT 1 FROM comparative_entries je "
            " WHERE je.study_id = s.id AND je.jurisdiction_id = ?)"
        )
        params.append(int(jurisdiction_id))
    query = _base_columns() + " WHERE " + " AND ".join(conditions)
    count_q = (
        f"SELECT COUNT(*) AS c FROM comparative_studies s "
        f"LEFT JOIN users u ON u.id = s.user_id "
        f"WHERE {' AND '.join(conditions)}"
    )
    query += " ORDER BY s.updated_at DESC, s.id DESC LIMIT ? OFFSET ?"
    with db_session() as conn:
        total = conn.execute(count_q, params).fetchone()["c"]
        rows = conn.execute(query, params + [limit, offset]).fetchall()
        return {"count": total, "studies": [dict(r) for r in rows]}


def get_study(study_id: int, viewer_id=None, include_internal=False):
    """تفصيل دراسة بمقارناتها مصنفة بالولاية (العموم: المنشور فقط)."""
    query = _base_columns() + " WHERE s.id = ?"
    params = [study_id]
    cond, vals = tenant_scope.tenant_eq("s")
    if cond:
        query += " AND " + cond
        params.extend(vals)
    with db_session() as conn:
        row = conn.execute(query, params).fetchone()
        if not row:
            return None
        study = dict(row)
        can_manage = include_internal or study["user_id"] == viewer_id
        if study["status"] != "published" and not can_manage:
            return None
        entries_q = (
            """SELECT e.id, e.jurisdiction_id, j.slug AS jurisdiction_slug,
                      j.name AS jurisdiction_name, e.legal_text_id,
                      e.article_id, e.note, e.position, e.created_at,
                      a.label AS article_label, a.number AS article_number,
                      lt.title AS legal_text_title
               FROM comparative_entries e
               JOIN law_jurisdictions j ON j.id = e.jurisdiction_id
               LEFT JOIN articles a ON a.id = e.article_id
               LEFT JOIN legal_texts lt ON lt.id = e.legal_text_id
               WHERE e.study_id = ?"""
        )
        entries_params = [study_id]
        e_cond, e_vals = tenant_scope.tenant_eq("e")
        if e_cond:
            entries_q += " AND " + e_cond
            entries_params.extend(e_vals)
        entries_q += " ORDER BY e.position, e.id"
        rows = conn.execute(entries_q, entries_params).fetchall()
        study["entries"] = [dict(r) for r in rows]
        return study


def create_study(user_id: int, data: dict) -> dict:
    title = (data.get("title") or "").strip()
    if not title:
        raise ComparativeError("عنوان الدراسة (title) مطلوب.", 400)
    description = (data.get("description") or "").strip() or None
    with db_session() as conn:
        cur = conn.execute(
            """INSERT INTO comparative_studies
               (user_id, title, description, status, tenant_id,
                created_at, updated_at)
               VALUES (?, ?, ?, 'draft', ?, datetime('now'), datetime('now'))""",
            (user_id, title, description, tenant_scope.insert_tenant_id()),
        )
        study_id = cur.lastrowid
    return {"id": study_id, "status": "draft",
            "message": "تم إنشاء الدراسة."}


def _ownership(conn, study_id: int):
    query = "SELECT id, user_id, status FROM comparative_studies WHERE id = ?"
    params = [study_id]
    cond, vals = tenant_scope.tenant_eq()
    if cond:
        query += " AND " + cond
        params.extend(vals)
    return conn.execute(query, params).fetchone()


def update_study(actor_id: int, study_id: int, data: dict,
                 is_admin: bool = False) -> dict:
    updates = {}
    for field in ("title", "description"):
        if field in data:
            value = (data.get(field) or "").strip()
            if field == "title" and not value:
                raise ComparativeError("عنوان الدراسة مطلوب.", 400)
            updates[field] = value or None
    if not updates:
        raise ComparativeError("لا توجد حقول للتحديث.", 400)
    with db_session() as conn:
        row = _ownership(conn, study_id)
        if row is None:
            raise ComparativeError("الدراسة غير موجودة.", 404)
        if row["user_id"] != actor_id and not is_admin:
            raise ComparativeError("لا يمكنك تعديل دراسة لا تملكها.", 403)
        sets = ", ".join(f"{k} = ?" for k in updates)
        upd_q = (
            f"UPDATE comparative_studies SET {sets}, "
            "updated_at = datetime('now') WHERE id = ?"
        )
        upd_params = list(updates.values()) + [study_id]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            upd_q += " AND " + cond
            upd_params.extend(vals)
        conn.execute(upd_q, upd_params)
    return {"id": study_id, "message": "تم تحديث الدراسة."}


def delete_study(actor_id: int, study_id: int, is_admin: bool = False) -> dict:
    with db_session() as conn:
        row = _ownership(conn, study_id)
        if row is None:
            raise ComparativeError("الدراسة غير موجودة.", 404)
        if row["user_id"] != actor_id and not is_admin:
            raise ComparativeError("لا يمكنك حذف دراسة لا تملكها.", 403)
        del_q = "DELETE FROM comparative_studies WHERE id = ?"
        del_params = [study_id]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            del_q += " AND " + cond
            del_params.extend(vals)
        conn.execute(del_q, del_params)
    return {"id": study_id, "message": "تم حذف الدراسة."}


def set_study_status(admin_id: int, study_id: int, status: str) -> dict:
    if status not in STUDY_STATUSES:
        raise ComparativeError(
            f"status يجب أن يكون أحد: {', '.join(STUDY_STATUSES)}.", 400
        )
    with db_session() as conn:
        row = _ownership(conn, study_id)
        if row is None:
            raise ComparativeError("الدراسة غير موجودة.", 404)
        upd_q = (
            "UPDATE comparative_studies SET status = ?, "
            "updated_at = datetime('now') WHERE id = ?"
        )
        upd_params = [status, study_id]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            upd_q += " AND " + cond
            upd_params.extend(vals)
        conn.execute(upd_q, upd_params)
        _log_admin_action(
            conn, admin_id, "comparative.status", "comparative_study",
            study_id, f"status={status}",
        )
    return {"id": study_id, "status": status,
            "message": "تم تحديث حالة الدراسة."}


def list_studies_admin(status=None, q=None, limit: int = 50, offset: int = 0):
    limit = max(1, min(int(limit or 50), 200))
    offset = max(0, int(offset or 0))
    conditions = ["1=1"]
    params = []
    cond, vals = tenant_scope.tenant_eq("s")
    if cond:
        conditions.append(cond)
        params.extend(vals)
    if status:
        conditions.append("s.status = ?")
        params.append(status)
    if q:
        like = f"%{q.strip()}%"
        conditions.append("(s.title LIKE ? OR u.full_name LIKE ?)")
        params += [like, like]
    query = _base_columns() + " WHERE " + " AND ".join(conditions)
    query += " ORDER BY s.updated_at DESC, s.id DESC LIMIT ? OFFSET ?"
    params += [limit, offset]
    with db_session() as conn:
        rows = conn.execute(query, params).fetchall()
        return [_scoped_creator(dict(r)) for r in rows]


def _scoped_creator(study: dict) -> dict:
    study["creator"] = {
        "id": study["user_id"],
        "full_name": study.pop("creator_name"),
    }
    return study


def list_studies_for_user(user_id: int, limit: int = 100, offset: int = 0):
    limit = max(1, min(int(limit or 100), 200))
    offset = max(0, int(offset or 0))
    query = _base_columns() + " WHERE s.user_id = ?"
    params = [user_id]
    cond, vals = tenant_scope.tenant_eq("s")
    if cond:
        query += " AND " + cond
        params.extend(vals)
    query += " ORDER BY s.updated_at DESC, s.id DESC LIMIT ? OFFSET ?"
    params += [limit, offset]
    with db_session() as conn:
        rows = conn.execute(query, params).fetchall()
        return [_scoped_creator(dict(r)) for r in rows]


# ---------------------------------------------------------------------------
# المقارنات (تندرج تحت دراسة — يُعدّلها مالك الدراسة أو إدارة)
# ---------------------------------------------------------------------------

def add_entry(actor_id: int, study_id: int, data: dict,
              is_admin: bool = False) -> dict:
    with db_session() as conn:
        row = _ownership(conn, study_id)
        if row is None:
            raise ComparativeError("الدراسة غير موجودة.", 404)
        if row["user_id"] != actor_id and not is_admin:
            raise ComparativeError("لا يمكنك تعديل دراسة لا تملكها.", 403)
        try:
            jurisdiction_id = int(data.get("jurisdiction_id"))
        except (TypeError, ValueError):
            raise ComparativeError("jurisdiction_id مطلوب.", 400)
        if not _jurisdiction_exists(conn, jurisdiction_id):
            raise ComparativeError("الولاية القضائية غير موجودة.", 400)
        legal_text_id = data.get("legal_text_id")
        article_id = data.get("article_id")
        if legal_text_id not in (None, ""):
            try:
                legal_text_id = int(legal_text_id)
            except (TypeError, ValueError):
                raise ComparativeError("legal_text_id يجب أن يكون رقمًا.", 400)
        else:
            legal_text_id = None
        if article_id not in (None, ""):
            try:
                article_id = int(article_id)
            except (TypeError, ValueError):
                raise ComparativeError("article_id يجب أن يكون رقمًا.", 400)
        else:
            article_id = None
        if not _legal_reference_valid(conn, legal_text_id, article_id):
            raise ComparativeError("المادة/النص المقارن غير موجود.", 400)
        if article_id is not None and legal_text_id is None:
            # مادة بلا نص: نحل النص تلقائيًا من المادة ذاتها
            found = conn.execute(
                "SELECT legal_text_id FROM articles WHERE id = ?",
                (article_id,),
            ).fetchone()
            if found is None:
                raise ComparativeError("المادة غير موجودة.", 400)
            legal_text_id = found["legal_text_id"]
        note = (data.get("note") or "").strip() or None
        try:
            position = int(data.get("position", 0))
        except (TypeError, ValueError):
            position = 0
        cur = conn.execute(
            """INSERT INTO comparative_entries
               (study_id, jurisdiction_id, legal_text_id, article_id,
                note, position, tenant_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
            (study_id, jurisdiction_id, legal_text_id, article_id, note,
             position, tenant_scope.insert_tenant_id()),
        )
        entry_id = cur.lastrowid
    return {"id": entry_id, "message": "تمت إضافة المقارنة."}


def update_entry(actor_id: int, entry_id: int, data: dict,
                 is_admin: bool = False) -> dict:
    updates = {}
    with db_session() as conn:
        row = _entry_ownership(conn, entry_id)
        if row is None:
            raise ComparativeError("المقارنة غير موجودة.", 404)
        if row["user_id"] != actor_id and not is_admin:
            raise ComparativeError("لا يمكنك تعديل دراسة لا تملكها.", 403)
        if "jurisdiction_id" in data and data.get("jurisdiction_id") not in (None, ""):
            try:
                jid = int(data["jurisdiction_id"])
            except (TypeError, ValueError):
                raise ComparativeError("jurisdiction_id يجب أن يكون رقمًا.", 400)
            if not _jurisdiction_exists(conn, jid):
                raise ComparativeError("الولاية القضائية غير موجودة.", 400)
            updates["jurisdiction_id"] = jid
        if "note" in data:
            updates["note"] = (data.get("note") or "").strip() or None
        if "position" in data:
            try:
                updates["position"] = int(data["position"])
            except (TypeError, ValueError):
                raise ComparativeError("position يجب أن يكون رقمًا.", 400)
        if "legal_text_id" in data or "article_id" in data:
            legal_text_id = data.get("legal_text_id")
            article_id = data.get("article_id")
            if legal_text_id not in (None, ""):
                try:
                    legal_text_id = int(legal_text_id)
                except (TypeError, ValueError):
                    raise ComparativeError("legal_text_id يجب أن يكون رقمًا.", 400)
            else:
                legal_text_id = None
            if article_id not in (None, ""):
                try:
                    article_id = int(article_id)
                except (TypeError, ValueError):
                    raise ComparativeError("article_id يجب أن يكون رقمًا.", 400)
            else:
                article_id = None
            if not _legal_reference_valid(conn, legal_text_id, article_id):
                raise ComparativeError("المادة/النص المقارن غير موجود.", 400)
            if article_id is not None and legal_text_id is None:
                found = conn.execute(
                    "SELECT legal_text_id FROM articles WHERE id = ?",
                    (article_id,),
                ).fetchone()
                if found is None:
                    raise ComparativeError("المادة غير موجودة.", 400)
                legal_text_id = found["legal_text_id"]
            updates["legal_text_id"] = legal_text_id
            updates["article_id"] = article_id
        if not updates:
            raise ComparativeError("لا توجد حقول للتحديث.", 400)
        sets = ", ".join(f"{k} = ?" for k in updates)
        upd_q = f"UPDATE comparative_entries SET {sets} WHERE id = ?"
        upd_params = list(updates.values()) + [entry_id]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            upd_q += " AND " + cond
            upd_params.extend(vals)
        conn.execute(upd_q, upd_params)
    return {"id": entry_id, "message": "تم تحديث المقارنة."}


def delete_entry(actor_id: int, entry_id: int, is_admin: bool = False) -> dict:
    with db_session() as conn:
        row = _entry_ownership(conn, entry_id)
        if row is None:
            raise ComparativeError("المقارنة غير موجودة.", 404)
        if row["user_id"] != actor_id and not is_admin:
            raise ComparativeError("لا يمكنك تعديل دراسة لا تملكها.", 403)
        del_q = "DELETE FROM comparative_entries WHERE id = ?"
        del_params = [entry_id]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            del_q += " AND " + cond
            del_params.extend(vals)
        conn.execute(del_q, del_params)
    return {"id": entry_id, "message": "تم حذف المقارنة."}


def _entry_ownership(conn, entry_id: int):
    query = (
        """SELECT e.id, e.study_id, s.user_id
           FROM comparative_entries e
           JOIN comparative_studies s ON s.id = e.study_id
           WHERE e.id = ?"""
    )
    params = [entry_id]
    e_cond, e_vals = tenant_scope.tenant_eq("e")
    s_cond, s_vals = tenant_scope.tenant_eq("s")
    scopes = []
    if e_cond:
        scopes.append(e_cond)
    if s_cond:
        scopes.append(s_cond)
    if scopes:
        query += " AND " + " AND ".join(scopes)
        params.extend(e_vals or [])
        params.extend(s_vals or [])
    return conn.execute(query, params).fetchone()
