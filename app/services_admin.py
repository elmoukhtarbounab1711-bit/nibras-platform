"""
طبقة خدمة الإدارة (المرحلة 2 — لوحة الإدارة).

تتولى إدارة المحتوى (إنشاء/تعديل/حذف النصوص والمواد) وطابور التحقق من
الطلبات المهنية، مع تسجيل كل إجراء إداري في admin_audit_log وفق وثيقة
الأمان §8 (المسؤول، الفعل، الهدف، التوقيت). كل التحقق من المدخلات يتم
في هذه الطبقة لا في المسارات (وثيقة الأمان §5).

النطاق (§ وثيقة 20):
- 3.1 إدارة المحتوى: النصوص والمواد (القسم والفهارس تُقرأ عامة؛ إنشاء
  الأقسام خارج النطاق لأن الوثيقة 08 لا تعرّفه).
- 3.2 طابور التحقق: القبول والرفض مع سبب (وثيقة المصادقة §3).
"""
from .database import db_session
from .services_auth import PROFESSIONAL_ROLES

# أنواع النصوص المقبولة (وثيقة API: constitution|code|law|decree|gazette|treaty|ruling)
LEGAL_TEXT_TYPES = frozenset(
    {"constitution", "code", "law", "decree", "gazette", "treaty", "ruling"}
)

# ترتيب ثابت للاستعلام عن الأدوار المهنية (sets غير مرتبة — نُرتِّب للاستقرار)
_PROFESSIONAL_ROLES = tuple(sorted(PROFESSIONAL_ROLES))

_TEXT_FIELDS = (
    "category_id", "type", "title", "official_ref",
    "enacted_date", "last_amended", "source_note",
)
_ARTICLE_FIELDS = ("number", "label", "content", "plain_explanation", "keywords")


class AdminError(Exception):
    """خطأ تجاري في الإدارة يُترجم إلى استجابة HTTP مناسبة في routes."""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


# ---------------------------------------------------------------------------
# أدوات مساعدة
# ---------------------------------------------------------------------------

def _log_admin_action(conn, admin_id, action, target_type, target_id, details=None):
    """يُسجّل إجراءً إداريًا في نفس معاملة العملية (تكاملي)."""
    conn.execute(
        "INSERT INTO admin_audit_log (admin_id, action, target_type, target_id, details)"
        " VALUES (?,?,?,?,?)",
        (admin_id, action, target_type, target_id, details),
    )


def _require_fields(data, fields):
    missing = [f for f in fields if data.get(f) in (None, "")]
    if missing:
        raise AdminError(f"حقول ناقصة: {', '.join(missing)}", 400)


def _coerce_sample_flag(value):
    if value in (1, "1", True, "true", "yes", "on"):
        return 1
    if value in (0, "0", False, "false", "no", "off"):
        return 0
    raise AdminError("قيمة is_sample_data غير صالحة", 400)


# ---------------------------------------------------------------------------
# إدارة النصوص القانونية
# ---------------------------------------------------------------------------

def create_text(admin_id, data):
    _require_fields(data, ["category_id", "type", "title"])
    category_id = data["category_id"]
    text_type = data["type"]
    title = (data.get("title") or "").strip()
    if text_type not in LEGAL_TEXT_TYPES:
        raise AdminError("نوع النص غير معروف", 400)
    if not title:
        raise AdminError("حقول ناقصة: title", 400)
    is_sample_data = (
        _coerce_sample_flag(data.get("is_sample_data", 1))
        if "is_sample_data" in data
        else 1
    )
    with db_session() as conn:
        category = conn.execute(
            "SELECT id FROM categories WHERE id = ?", (category_id,)
        ).fetchone()
        if category is None:
            raise AdminError("القسم غير موجود", 404)
        cur = conn.execute(
            """INSERT INTO legal_texts
               (category_id, type, title, official_ref, enacted_date, last_amended, source_note, is_sample_data)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                category_id, text_type, title,
                data.get("official_ref"), data.get("enacted_date"),
                data.get("last_amended"), data.get("source_note"), is_sample_data,
            ),
        )
        new_id = cur.lastrowid
        _log_admin_action(conn, admin_id, "text.create", "legal_text", new_id)
    return new_id


def update_text(admin_id, text_id, data):
    if not isinstance(data, dict) or not data:
        raise AdminError("لا توجد حقول للتحديث", 400)
    with db_session() as conn:
        row = conn.execute(
            "SELECT id FROM legal_texts WHERE id = ?", (text_id,)
        ).fetchone()
        if row is None:
            raise AdminError("النص القانوني غير موجود", 404)
        updates = {}
        for field in _TEXT_FIELDS:
            if field in data:
                updates[field] = data[field]
        if "is_sample_data" in data:
            updates["is_sample_data"] = _coerce_sample_flag(data["is_sample_data"])
        if "category_id" in updates:
            category = conn.execute(
                "SELECT id FROM categories WHERE id = ?", (updates["category_id"],)
            ).fetchone()
            if category is None:
                raise AdminError("القسم غير موجود", 404)
        if "type" in updates and updates["type"] not in LEGAL_TEXT_TYPES:
            raise AdminError("نوع النص غير معروف", 400)
        if "title" in updates and not (updates["title"] or "").strip():
            raise AdminError("العنوان مطلوب", 400)
        if not updates:
            raise AdminError("لا توجد حقول للتحديث", 400)
        sets = ", ".join(f"{k} = ?" for k in updates)
        conn.execute(
            f"UPDATE legal_texts SET {sets} WHERE id = ?",
            (*updates.values(), text_id),
        )
        _log_admin_action(conn, admin_id, "text.update", "legal_text", text_id)
    return text_id


def delete_text(admin_id, text_id):
    with db_session() as conn:
        row = conn.execute(
            "SELECT id FROM legal_texts WHERE id = ?", (text_id,)
        ).fetchone()
        if row is None:
            raise AdminError("النص القانوني غير موجود", 404)
        # المواد تُحذف تسلسليًا (ON DELETE CASCADE + مشغّلات FTS)
        conn.execute("DELETE FROM legal_texts WHERE id = ?", (text_id,))
        _log_admin_action(conn, admin_id, "text.delete", "legal_text", text_id)
    return text_id


# ---------------------------------------------------------------------------
# إدارة المواد
# ---------------------------------------------------------------------------

def create_article(admin_id, text_id, data):
    _require_fields(data, ["number", "label", "content"])
    with db_session() as conn:
        text = conn.execute(
            "SELECT id FROM legal_texts WHERE id = ?", (text_id,)
        ).fetchone()
        if text is None:
            raise AdminError("النص القانوني غير موجود", 404)
        cur = conn.execute(
            """INSERT INTO articles
               (legal_text_id, number, label, content, plain_explanation, keywords)
               VALUES (?,?,?,?,?,?)""",
            (
                text_id, data["number"], data["label"], data["content"],
                data.get("plain_explanation"), data.get("keywords", ""),
            ),
        )
        new_id = cur.lastrowid
        _log_admin_action(conn, admin_id, "article.create", "article", new_id)
    return new_id


def update_article(admin_id, article_id, data):
    if not isinstance(data, dict) or not data:
        raise AdminError("لا توجد حقول للتحديث", 400)
    with db_session() as conn:
        row = conn.execute(
            "SELECT id FROM articles WHERE id = ?", (article_id,)
        ).fetchone()
        if row is None:
            raise AdminError("المادة غير موجودة", 404)
        updates = {f: data[f] for f in _ARTICLE_FIELDS if f in data}
        if "content" in updates and not (updates["content"] or "").strip():
            raise AdminError("محتوى المادة مطلوب", 400)
        if not updates:
            raise AdminError("لا توجد حقول للتحديث", 400)
        sets = ", ".join(f"{k} = ?" for k in updates)
        conn.execute(
            f"UPDATE articles SET {sets} WHERE id = ?",
            (*updates.values(), article_id),
        )
        _log_admin_action(conn, admin_id, "article.update", "article", article_id)
    return article_id


def delete_article(admin_id, article_id):
    with db_session() as conn:
        row = conn.execute(
            "SELECT id FROM articles WHERE id = ?", (article_id,)
        ).fetchone()
        if row is None:
            raise AdminError("المادة غير موجودة", 404)
        # الروابط ذات الصلة تُحذف تسلسليًا + مشغّلات FTS
        conn.execute("DELETE FROM articles WHERE id = ?", (article_id,))
        _log_admin_action(conn, admin_id, "article.delete", "article", article_id)
    return article_id


# ---------------------------------------------------------------------------
# طابور التحقق من الطلبات المهنية (وثيقة 20 §3.2 / وثيقة المصادقة §3)
# ---------------------------------------------------------------------------

def list_verification_queue():
    placeholders = ",".join("?" for _ in _PROFESSIONAL_ROLES)
    with db_session() as conn:
        rows = conn.execute(
            f"""SELECT u.id AS user_id, u.email, u.full_name,
                       r.code AS role_code, r.name AS role_name,
                       ur.role_status, ur.rejection_reason,
                       ur.created_at AS requested_at
                FROM user_roles ur
                JOIN users u ON u.id = ur.user_id
                JOIN roles r ON r.id = ur.role_id
                WHERE ur.role_status = 'pending_verification'
                  AND r.code IN ({placeholders})
                ORDER BY ur.created_at, u.id""",
            _PROFESSIONAL_ROLES,
        ).fetchall()
        return [dict(r) for r in rows]


def _verification_row(conn, user_id):
    placeholders = ",".join("?" for _ in _PROFESSIONAL_ROLES)
    return conn.execute(
        f"""SELECT ur.user_id, ur.role_id, ur.role_status, r.code
            FROM user_roles ur
            JOIN roles r ON r.id = ur.role_id
            WHERE ur.user_id = ? AND r.code IN ({placeholders})""",
        (user_id, *_PROFESSIONAL_ROLES),
    ).fetchone()


def approve_verification(admin_id, user_id):
    with db_session() as conn:
        row = _verification_row(conn, user_id)
        if row is None:
            raise AdminError("طلب التحقق غير موجود", 404)
        if row["role_status"] != "pending_verification":
            raise AdminError("هذا الطلب لم يعد في انتظار التحقق", 409)
        conn.execute(
            "UPDATE user_roles SET role_status = 'active', rejection_reason = NULL"
            " WHERE user_id = ? AND role_id = ?",
            (user_id, row["role_id"]),
        )
        _log_admin_action(
            conn, admin_id, "verification.approve", "user", user_id,
            f"role={row['code']}",
        )
    return user_id


def reject_verification(admin_id, user_id, reason):
    reason = (reason or "").strip()
    if not reason:
        raise AdminError("سبب الرفض مطلوب", 400)
    with db_session() as conn:
        row = _verification_row(conn, user_id)
        if row is None:
            raise AdminError("طلب التحقق غير موجود", 404)
        if row["role_status"] != "pending_verification":
            raise AdminError("هذا الطلب لم يعد في انتظار التحقق", 409)
        conn.execute(
            "UPDATE user_roles SET role_status = 'rejected', rejection_reason = ?"
            " WHERE user_id = ? AND role_id = ?",
            (reason, user_id, row["role_id"]),
        )
        _log_admin_action(
            conn, admin_id, "verification.reject", "user", user_id,
            f"role={row['code']}; reason={reason}",
        )
    return user_id
