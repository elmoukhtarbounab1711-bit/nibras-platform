"""
خدمات سوق القوالب (المرحلة 7 — إتمام Roadmap Phase 5، قرار D-025).

كتالوج قوالب (فئات + قوالب بسعر/وصف/ملف) بإدارة إدارية كاملة (وثيقة 19 §6
و Admin Panel 20 §3) وتصفح عام. الشراء والمراجعات مؤجَّلان لحسم بوابة الدفع
(BRD §5) — جدول purchases مُنشأ بلا نقطة نهاية (payment_id فارغ). ملف القالب
يُخزَّن محليًا في uploads/marketplace/ (نمط uploads/verification — D-023)
ولا يُنزَّل للعام إطلاقًا حتى الشراء؛ التنزيل إداري فقط. كل إجراء سوقي
يُسجَّل في admin_audit_log (Security §8).
"""
import os
import secrets
import sqlite3
from pathlib import Path

from . import config
from .database import db_session
from .services_admin import _log_admin_action

# امتدادات ملفات القوالب (وثيقة 19 §2: ملف قابل للتنزيل — pdf/docx)
TEMPLATE_FILE_EXTENSIONS = {".pdf", ".docx"}

# نفس تصنيف مكتبة النصوص والمجتمع (وثيقة 19 §2 — قرار D-025)
CATEGORY_SEED = (
    ("dostouri", "القانون الدستوري"),
    ("madani", "القانون المدني"),
    ("usra", "قانون الأسرة"),
    ("jinai", "القانون الجنائي"),
    ("shughl", "قانون الشغل"),
    ("tijari", "القانون التجاري"),
)

DEFAULT_LIST_LIMIT = 20
MAX_LIST_LIMIT = 100

_CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument."
             "wordprocessingml.document",
}


class MarketplaceError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _uploads_dir() -> Path:
    if config.UPLOAD_DIR:
        base = Path(config.UPLOAD_DIR)
    else:
        base = Path(__file__).resolve().parent.parent / "uploads"
    return base / "marketplace"


def ensure_defaults():
    """بذر فئات السوق إن كانت فارغة (idempotent — نمط ensure_defaults)."""
    with db_session() as conn:
        count = conn.execute(
            "SELECT COUNT(*) AS c FROM marketplace_categories"
        ).fetchone()["c"]
        if count == 0:
            for slug, name in CATEGORY_SEED:
                conn.execute(
                    "INSERT INTO marketplace_categories (slug, name) VALUES (?, ?)",
                    (slug, name),
                )


def _category_exists(conn, category_id) -> bool:
    return conn.execute(
        "SELECT 1 FROM marketplace_categories WHERE id = ?", (category_id,)
    ).fetchone() is not None


def _coerce_price(value) -> int:
    try:
        price = int(value)
    except (TypeError, ValueError):
        raise MarketplaceError("السعر (price_cents) يجب أن يكون رقمًا صحيحًا.", 400)
    if price < 0:
        raise MarketplaceError("السعر (price_cents) لا يمكن أن يكون سالبًا.", 400)
    return price


def _validate_file(file):
    """يتحقق من ملف القالب ويعيد محتواه — بلا تخزين."""
    if file is None:
        raise MarketplaceError("الرجاء رفع ملف القالب (file).", 400)
    filename = (file.filename or "").strip()
    ext = os.path.splitext(filename)[1].lower()
    if ext not in TEMPLATE_FILE_EXTENSIONS:
        raise MarketplaceError("صيغة الملف غير مسموح بها (pdf أو docx).", 400)
    content = file.read()
    if not content:
        raise MarketplaceError("الملف فارغ.", 400)
    if len(content) > config.MAX_UPLOAD_BYTES:
        raise MarketplaceError(
            f"الملف يتجاوز الحد الأقصى "
            f"({config.MAX_UPLOAD_BYTES // (1024 * 1024)}MB).",
            400,
        )
    return filename, ext, content


def _store_file(filename: str, content: bytes) -> str:
    """يخزِّن الملف ويعيد storage_key (اسم الملف المحلي)."""
    ext = os.path.splitext(filename)[1].lower()
    storage_name = f"{secrets.token_urlsafe(12)}{ext}"
    uploads = _uploads_dir()
    uploads.mkdir(parents=True, exist_ok=True)
    (uploads / storage_name).write_bytes(content)
    return storage_name


def _remove_file(storage_key: str) -> None:
    try:
        (_uploads_dir() / os.path.basename(storage_key)).unlink(missing_ok=True)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# القراءة العامة (كتالوج)
# ---------------------------------------------------------------------------

def list_categories():
    with db_session() as conn:
        rows = conn.execute(
            """SELECT c.id, c.slug, c.name,
                      (SELECT COUNT(*) FROM marketplace_templates t
                       WHERE t.category_id = c.id) AS template_count
               FROM marketplace_categories c ORDER BY c.id"""
        ).fetchall()
        return [dict(r) for r in rows]


def _template_item(row) -> dict:
    return {
        "id": row["id"],
        "category_id": row["category_id"],
        "title": row["title"],
        "description": row["description"],
        "price_cents": row["price_cents"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def list_templates(category_id=None, q=None, limit: int = DEFAULT_LIST_LIMIT,
                   offset: int = 0):
    limit = max(1, min(int(limit or DEFAULT_LIST_LIMIT), MAX_LIST_LIMIT))
    offset = max(0, int(offset or 0))
    conditions = []
    params = []
    if category_id is not None:
        conditions.append("t.category_id = ?")
        params.append(int(category_id))
    if q:
        like = f"%{q.strip()}%"
        conditions.append("(t.title LIKE ? OR t.description LIKE ?)")
        params += [like, like]
    query = "SELECT * FROM marketplace_templates t"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY t.created_at DESC, t.id DESC LIMIT ? OFFSET ?"
    params += [limit, offset]
    with db_session() as conn:
        rows = conn.execute(query, params).fetchall()
        return [_template_item(dict(r)) for r in rows]


def get_template(template_id: int):
    with db_session() as conn:
        row = conn.execute(
            "SELECT * FROM marketplace_templates WHERE id = ?", (template_id,)
        ).fetchone()
        if not row:
            return None
        return _template_item(dict(row))


# ---------------------------------------------------------------------------
# الإدارة (تُستدعى من مسارات admin — دور admin)
# ---------------------------------------------------------------------------

def list_templates_admin():
    with db_session() as conn:
        rows = conn.execute(
            """SELECT t.*, c.name AS category_name
               FROM marketplace_templates t
               JOIN marketplace_categories c ON c.id = t.category_id
               ORDER BY t.id DESC"""
        ).fetchall()
        items = []
        for row in rows:
            item = dict(row)
            item["has_file"] = bool(item.get("storage_key"))
            item.pop("storage_key", None)
            items.append(item)
        return items


def create_template(admin_id: int, data: dict, file) -> dict:
    title = (data.get("title") or "").strip()
    if not title:
        raise MarketplaceError("عنوان القالب (title) مطلوب.", 400)
    category_id = data.get("category_id")
    try:
        category_id = int(category_id)
    except (TypeError, ValueError):
        raise MarketplaceError("category_id يجب أن يكون رقمًا.", 400)
    price_cents = _coerce_price(data.get("price_cents"))
    description = (data.get("description") or "").strip()
    filename, _ext, content = _validate_file(file)
    with db_session() as conn:
        if not _category_exists(conn, category_id):
            raise MarketplaceError("الفئة غير موجودة.", 400)
        storage_key = _store_file(filename, content)
        cur = conn.execute(
            "INSERT INTO marketplace_templates "
            "(category_id, title, description, price_cents, storage_key, "
            "created_at, updated_at) VALUES (?, ?, ?, ?, ?, "
            "datetime('now'), datetime('now'))",
            (category_id, title, description or None, price_cents, storage_key),
        )
        template_id = cur.lastrowid
        _log_admin_action(
            conn, admin_id, "marketplace.create", "marketplace_template",
            template_id, f"price_cents={price_cents}",
        )
    return {"id": template_id, "message": "تمت إضافة القالب إلى السوق."}


def update_template(admin_id: int, template_id: int, data: dict, file) -> dict:
    with db_session() as conn:
        row = conn.execute(
            "SELECT * FROM marketplace_templates WHERE id = ?", (template_id,)
        ).fetchone()
        if row is None:
            raise MarketplaceError("القالب غير موجود.", 404)
        updates = {}
        if "title" in data:
            title = (data.get("title") or "").strip()
            if not title:
                raise MarketplaceError("عنوان القالب (title) مطلوب.", 400)
            updates["title"] = title
        if "description" in data:
            description = (data.get("description") or "").strip()
            updates["description"] = description or None
        if "price_cents" in data and data.get("price_cents") not in (None, ""):
            updates["price_cents"] = _coerce_price(data.get("price_cents"))
        if "category_id" in data and data.get("category_id") not in (None, ""):
            category_id = int(data["category_id"])
            if not _category_exists(conn, category_id):
                raise MarketplaceError("الفئة غير موجودة.", 400)
            updates["category_id"] = category_id
        new_storage_key = None
        if file is not None:
            filename, _ext, content = _validate_file(file)
            new_storage_key = _store_file(filename, content)
            updates["storage_key"] = new_storage_key
        if not updates and file is None:
            raise MarketplaceError("لا توجد حقول للتحديث.", 400)
        sets = ", ".join(f"{k} = ?" for k in updates)
        conn.execute(
            f"UPDATE marketplace_templates SET {sets}, "
            "updated_at = datetime('now') WHERE id = ?",
            (*updates.values(), template_id),
        )
        if new_storage_key:
            _remove_file(row["storage_key"])
        _log_admin_action(
            conn, admin_id, "marketplace.update", "marketplace_template",
            template_id,
        )
    return {"id": template_id, "message": "تم تحديث القالب."}


def delete_template(admin_id: int, template_id: int) -> dict:
    with db_session() as conn:
        row = conn.execute(
            "SELECT id, storage_key FROM marketplace_templates WHERE id = ?",
            (template_id,),
        ).fetchone()
        if row is None:
            raise MarketplaceError("القالب غير موجود.", 404)
        purchased = conn.execute(
            "SELECT 1 FROM purchases WHERE template_id = ?", (template_id,)
        ).fetchone()
        if purchased:
            raise MarketplaceError(
                "لا يمكن حذف قالب له سجل شراءات.", 409
            )
        conn.execute(
            "DELETE FROM marketplace_templates WHERE id = ?", (template_id,)
        )
        _remove_file(row["storage_key"])
        _log_admin_action(
            conn, admin_id, "marketplace.delete", "marketplace_template",
            template_id,
        )
    return {"id": template_id, "message": "تم حذف القالب."}


def get_template_file(template_id: int):
    """مسار/اسم ملف القالب — يُستدعى من مسار إداري مصادق (دور admin) فقط."""
    with db_session() as conn:
        row = conn.execute(
            "SELECT storage_key, title FROM marketplace_templates WHERE id = ?",
            (template_id,),
        ).fetchone()
    if row is None:
        raise MarketplaceError("القالب غير موجود.", 404)
    path = _uploads_dir() / os.path.basename(row["storage_key"])
    if not path.exists():
        raise MarketplaceError("ملف القالب غير موجود على القرص.", 404)
    ext = os.path.splitext(row["storage_key"])[1].lower()
    content_type = _CONTENT_TYPES.get(ext, "application/octet-stream")
    name = (row["title"] or "template") + ext
    return str(path), name, content_type


# ---------------------------------------------------------------------------
# إدارة الفئات
# ---------------------------------------------------------------------------

def _category_fields(data: dict) -> tuple:
    slug = (data.get("slug") or "").strip()
    name = (data.get("name") or "").strip()
    if not slug or not name:
        raise MarketplaceError("slug و name مطلوبان.", 400)
    return slug, name


def create_category(admin_id: int, data: dict) -> int:
    slug, name = _category_fields(data)
    with db_session() as conn:
        try:
            cur = conn.execute(
                "INSERT INTO marketplace_categories (slug, name) VALUES (?, ?)",
                (slug, name),
            )
        except sqlite3.IntegrityError:
            raise MarketplaceError("فئة بنفس slug موجودة مسبقًا.", 400)
        category_id = cur.lastrowid
        _log_admin_action(
            conn, admin_id, "marketplace.category.create",
            "marketplace_category", category_id,
        )
    return category_id


def update_category(admin_id: int, category_id: int, data: dict) -> int:
    with db_session() as conn:
        row = conn.execute(
            "SELECT id FROM marketplace_categories WHERE id = ?", (category_id,)
        ).fetchone()
        if row is None:
            raise MarketplaceError("الفئة غير موجودة.", 404)
        updates = {}
        if "slug" in data:
            slug = (data.get("slug") or "").strip()
            if not slug:
                raise MarketplaceError("slug مطلوب.", 400)
            updates["slug"] = slug
        if "name" in data:
            name = (data.get("name") or "").strip()
            if not name:
                raise MarketplaceError("name مطلوب.", 400)
            updates["name"] = name
        if not updates:
            raise MarketplaceError("لا توجد حقول للتحديث.", 400)
        try:
            sets = ", ".join(f"{k} = ?" for k in updates)
            conn.execute(
                f"UPDATE marketplace_categories SET {sets} WHERE id = ?",
                (*updates.values(), category_id),
            )
        except sqlite3.IntegrityError:
            raise MarketplaceError("فئة بنفس slug موجودة مسبقًا.", 400)
        _log_admin_action(
            conn, admin_id, "marketplace.category.update",
            "marketplace_category", category_id,
        )
    return category_id


def delete_category(admin_id: int, category_id: int) -> int:
    with db_session() as conn:
        row = conn.execute(
            "SELECT id FROM marketplace_categories WHERE id = ?", (category_id,)
        ).fetchone()
        if row is None:
            raise MarketplaceError("الفئة غير موجودة.", 404)
        used = conn.execute(
            "SELECT 1 FROM marketplace_templates WHERE category_id = ?",
            (category_id,),
        ).fetchone()
        if used:
            raise MarketplaceError("لا يمكن حذف فئة تحتوي قوالب.", 409)
        conn.execute(
            "DELETE FROM marketplace_categories WHERE id = ?", (category_id,)
        )
        _log_admin_action(
            conn, admin_id, "marketplace.category.delete",
            "marketplace_category", category_id,
        )
    return category_id
