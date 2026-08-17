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
import json
import sqlite3

from . import config, tenant_scope
from .database import db_session
from .services_auth import PROFESSIONAL_ROLES
from .services_notifications import notify

# أنواع النصوص المقبولة (وثيقة API: constitution|code|law|decree|gazette|treaty|ruling)
LEGAL_TEXT_TYPES = frozenset(
    {"constitution", "code", "law", "decree", "gazette", "treaty", "ruling"}
)

# ترتيب ثابت للاستعلام عن الأدوار المهنية (sets غير مرتبة — نُرتِّب للاستقرار)
_PROFESSIONAL_ROLES = tuple(sorted(PROFESSIONAL_ROLES))

_TEXT_FIELDS = (
    "category_id", "type", "title", "official_ref",
    "enacted_date", "last_amended", "source_note",
    "description", "issuing_body", "jurisdiction_id",
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

# سقف الحجم للعمليات الإدارية الجماعية (المرحلة 15 — قرار D-033)
MAX_BULK_ITEMS = 200


def parse_bulk_ids(raw_ids, field="ids"):
    """يحوّل قائمة معرّفات من الحمولة إلى قائمة أرقام موجبة فريدة (max MAX_BULK_ITEMS).

    يرفض الحمولة غير الصالحة (غير قائمة / فارغة / قيم غير رقمية / تجاوز
    السقف) برمز 400 — يُطبَّق قبل أي كتابة في المعاملة."""
    if raw_ids is None or not isinstance(raw_ids, list) or not raw_ids:
        raise AdminError(f"{field} يجب أن يكون قائمة بأرقام المعرّفات", 400)
    parsed = []
    seen = set()
    for raw in raw_ids:
        try:
            value = int(raw)
        except (TypeError, ValueError):
            raise AdminError(f"{field} يجب أن تحتوي أرقامًا صالحة فقط", 400)
        if value <= 0:
            raise AdminError(f"{field} يجب أن تحتوي أرقامًا موجبة فقط", 400)
        if value not in seen:
            seen.add(value)
            parsed.append(value)
    if not parsed:
        raise AdminError(f"{field} يجب أن تحتوي رقمًا واحدًا على الأقل", 400)
    if len(parsed) > MAX_BULK_ITEMS:
        raise AdminError(
            f"الحد الأقصى للعمليات الجماعية {MAX_BULK_ITEMS} عنصرًا", 400
        )
    return parsed


def bulk_summary(action, results):
    """يبني شكل استجابة العملية الجماعية الموحّد {action,total,succeeded,failed,results}.

    كل نتيجة عنصر {id, status: ok|error, message} — النجاح الجزئي
    مقصود (يُسجَّل كل عنصر فشل بسببه بينما تُلتزم الناجحة في معاملة واحدة)."""
    return {
        "action": action,
        "total": len(results),
        "succeeded": sum(1 for r in results if r["status"] == "ok"),
        "failed": len(results) - sum(1 for r in results if r["status"] == "ok"),
        "results": results,
    }

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


def _coerce_jurisdiction_id(data):
    """يعيد معرّف الولاية القضائية كعدد صحيح أو None (فارغ/غائب)."""
    value = data.get("jurisdiction_id")
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        raise AdminError("jurisdiction_id يجب أن يكون رقمًا.", 400)


def _jurisdiction_exists(conn, jurisdiction_id):
    query = "SELECT 1 FROM law_jurisdictions WHERE id = ?"
    params = [jurisdiction_id]
    cond, vals = tenant_scope.tenant_eq()
    if cond:
        query += " AND " + cond
        params.extend(vals)
    return conn.execute(query, params).fetchone() is not None


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
        cat_q = "SELECT id FROM categories WHERE id = ?"
        cat_params = [category_id]
        cat_cond, cat_vals = tenant_scope.tenant_eq()
        if cat_cond:
            cat_q += " AND " + cat_cond
            cat_params.extend(cat_vals)
        category = conn.execute(cat_q, cat_params).fetchone()
        if category is None:
            raise AdminError("القسم غير موجود", 404)
        cur = conn.execute(
            """INSERT INTO legal_texts
               (category_id, type, title, official_ref, enacted_date, last_amended, source_note, is_sample_data, jurisdiction_id, tenant_id)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                category_id, text_type, title,
                data.get("official_ref"), data.get("enacted_date"),
                data.get("last_amended"), data.get("source_note"), is_sample_data,
                _coerce_jurisdiction_id(data), tenant_scope.insert_tenant_id(),
            ),
        )
        new_id = cur.lastrowid
        _log_admin_action(conn, admin_id, "text.create", "legal_text", new_id)
    return new_id


def _compute_text_updates(conn, data):
    """يحسب حقول تحديث نص قانوني (تحقق موحَّد تُستخدمه التحديثات الفردية والجماعية)."""
    updates = {}
    for field in _TEXT_FIELDS:
        if field in data:
            updates[field] = data[field]
    if "is_sample_data" in data:
        updates["is_sample_data"] = _coerce_sample_flag(data["is_sample_data"])
    if "jurisdiction_id" in updates:
        jid = _coerce_jurisdiction_id(updates)
        if jid is not None and not _jurisdiction_exists(conn, jid):
            raise AdminError("الولاية القضائية غير موجودة", 404)
        updates["jurisdiction_id"] = jid
    if "category_id" in updates:
        cat_q = "SELECT id FROM categories WHERE id = ?"
        cat_params = [updates["category_id"]]
        cat_cond, cat_vals = tenant_scope.tenant_eq()
        if cat_cond:
            cat_q += " AND " + cat_cond
            cat_params.extend(cat_vals)
        category = conn.execute(cat_q, cat_params).fetchone()
        if category is None:
            raise AdminError("القسم غير موجود", 404)
    if "type" in updates and updates["type"] not in LEGAL_TEXT_TYPES:
        raise AdminError("نوع النص غير معروف", 400)
    if "title" in updates and not (updates["title"] or "").strip():
        raise AdminError("العنوان مطلوب", 400)
    if not updates:
        raise AdminError("لا توجد حقول للتحديث", 400)
    return updates


def _update_text_row(conn, admin_id, text_id, updates):
    sel_q = "SELECT id FROM legal_texts WHERE id = ?"
    sel_params = [text_id]
    cond, vals = tenant_scope.tenant_eq()
    if cond:
        sel_q += " AND " + cond
        sel_params.extend(vals)
    row = conn.execute(sel_q, sel_params).fetchone()
    if row is None:
        raise AdminError("النص القانوني غير موجود", 404)
    sets = ", ".join(f"{k} = ?" for k in updates)
    upd_q = f"UPDATE legal_texts SET {sets} WHERE id = ?"
    upd_params = list(updates.values()) + [text_id]
    if cond:
        upd_q += " AND " + cond
        upd_params.extend(vals)
    conn.execute(upd_q, upd_params)
    _log_admin_action(conn, admin_id, "text.update", "legal_text", text_id)
    return text_id


def update_text(admin_id, text_id, data):
    if not isinstance(data, dict) or not data:
        raise AdminError("لا توجد حقول للتحديث", 400)
    with db_session() as conn:
        updates = _compute_text_updates(conn, data)
        _update_text_row(conn, admin_id, text_id, updates)
    return text_id


def bulk_update_texts(admin_id, ids, data):
    """تطبيق حقول مشتركة على عدة نصوص في معاملة واحدة (المرحلة 15 — D-033).

    يُتحقق من الحمولة المشتركة مرة واحدة قبل أي كتابة؛ إن كانت غير صالحة
    يُرفض الطلب كله (400). العناصر غير الموجودة تُسجَّل فشلًا جزئيًا."""
    if not isinstance(data, dict) or not data:
        raise AdminError("لا توجد حقول للتحديث", 400)
    text_ids = parse_bulk_ids(ids)
    with db_session() as conn:
        updates = _compute_text_updates(conn, data)
        results = []
        for text_id in text_ids:
            try:
                _update_text_row(conn, admin_id, text_id, updates)
                results.append(
                    {"id": text_id, "status": "ok", "message": "تم تحديث النص"}
                )
            except AdminError as exc:
                results.append(
                    {"id": text_id, "status": "error", "message": exc.message}
                )
    return bulk_summary("text.update", results)


def _delete_text_row(conn, admin_id, text_id):
    sel_q = "SELECT id FROM legal_texts WHERE id = ?"
    sel_params = [text_id]
    cond, vals = tenant_scope.tenant_eq()
    if cond:
        sel_q += " AND " + cond
        sel_params.extend(vals)
    row = conn.execute(sel_q, sel_params).fetchone()
    if row is None:
        raise AdminError("النص القانوني غير موجود", 404)
    # المواد تُحذف تسلسليًا (ON DELETE CASCADE + مشغّلات FTS)
    del_q = "DELETE FROM legal_texts WHERE id = ?"
    del_params = [text_id]
    if cond:
        del_q += " AND " + cond
        del_params.extend(vals)
    conn.execute(del_q, del_params)
    _log_admin_action(conn, admin_id, "text.delete", "legal_text", text_id)
    return text_id


def delete_text(admin_id, text_id):
    with db_session() as conn:
        _delete_text_row(conn, admin_id, text_id)
    return text_id


def bulk_delete_texts(admin_id, ids):
    """حذف جماعي لنصوص قانونية (CASCADE على المواد/FTS) في معاملة واحدة."""
    text_ids = parse_bulk_ids(ids)
    with db_session() as conn:
        results = []
        for text_id in text_ids:
            try:
                _delete_text_row(conn, admin_id, text_id)
                results.append(
                    {"id": text_id, "status": "ok", "message": "تم حذف النص"}
                )
            except AdminError as exc:
                results.append(
                    {"id": text_id, "status": "error", "message": exc.message}
                )
    return bulk_summary("text.delete", results)


# ---------------------------------------------------------------------------
# رفع ملف PDF للقوانين (مرحلة الواجهة — مرحلة إضافية غير مُغيِّرة)
# ---------------------------------------------------------------------------

def _laws_upload_dir():
    from pathlib import Path

    from . import config

    if config.UPLOAD_DIR:
        base = Path(config.UPLOAD_DIR)
    else:
        base = Path(__file__).resolve().parent.parent / "uploads"
    return base / "laws"


def update_text_pdf(admin_id, text_id, file):
    """يرفع ملف PDF بديلًا لنص قانوني (يُفضَّل على الملف المولَّد عند العرض).

    تخزين محلي في uploads/laws (نمط uploads/verification — D-023). استبدال
    الملف السابق: يحذف القديم من القرص ويحدّث المفتاح في نفس المعاملة."""
    import os
    import secrets

    filename = (file.filename or "").strip()
    ext = os.path.splitext(filename)[1].lower()
    if ext != ".pdf":
        raise AdminError("صيغة الملف غير مسموح بها (pdf فقط).", 400)
    content = file.read()
    if not content:
        raise AdminError("الملف فارغ.", 400)
    if len(content) > config.MAX_UPLOAD_BYTES:
        raise AdminError(
            f"الملف يتجاوز الحد الأقصى ({config.MAX_UPLOAD_BYTES // (1024 * 1024)}MB).",
            400,
        )
    with db_session() as conn:
        sel_q = "SELECT id, uploaded_pdf_key FROM legal_texts WHERE id = ?"
        sel_params = [text_id]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            sel_q += " AND " + cond
            sel_params.extend(vals)
        row = conn.execute(sel_q, sel_params).fetchone()
        if row is None:
            raise AdminError("النص القانوني غير موجود", 404)
        old_key = row["uploaded_pdf_key"]
        storage_name = f"text-{text_id}-{secrets.token_urlsafe(10)}.pdf"
        uploads = _laws_upload_dir()
        uploads.mkdir(parents=True, exist_ok=True)
        (uploads / storage_name).write_bytes(content)
        if old_key:
            try:
                (uploads / os.path.basename(old_key)).unlink(missing_ok=True)
            except OSError:
                pass
        upd_q = "UPDATE legal_texts SET uploaded_pdf_key = ? WHERE id = ?"
        upd_params = [storage_name, text_id]
        if cond:
            upd_q += " AND " + cond
            upd_params.extend(vals)
        conn.execute(upd_q, upd_params)
        _log_admin_action(
            conn, admin_id, "text.pdf.update", "legal_text", text_id,
            f"bytes={len(content)}",
        )
    return {"id": text_id, "message": "تم رفع ملف PDF القانون."}


def delete_text_pdf(admin_id, text_id):
    """يزيل ملف PDF المرفوع — يعود العرض إلى الملف المولَّد تلقائيًا."""
    import os

    with db_session() as conn:
        sel_q = "SELECT id, uploaded_pdf_key FROM legal_texts WHERE id = ?"
        sel_params = [text_id]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            sel_q += " AND " + cond
            sel_params.extend(vals)
        row = conn.execute(sel_q, sel_params).fetchone()
        if row is None:
            raise AdminError("النص القانوني غير موجود", 404)
        old_key = row["uploaded_pdf_key"]
        if not old_key:
            raise AdminError("لا يوجد ملف PDF مرفوع لهذا النص.", 404)
        upd_q = "UPDATE legal_texts SET uploaded_pdf_key = NULL WHERE id = ?"
        upd_params = [text_id]
        if cond:
            upd_q += " AND " + cond
            upd_params.extend(vals)
        conn.execute(upd_q, upd_params)
        try:
            (_laws_upload_dir() / os.path.basename(old_key)).unlink(missing_ok=True)
        except OSError:
            pass
        _log_admin_action(conn, admin_id, "text.pdf.delete", "legal_text", text_id)
    return {"id": text_id, "message": "تم حذف ملف PDF المرفوع."}


# ---------------------------------------------------------------------------
# إدارة المساطر القانونية (مرحلة الواجهة — رسوم وأسئلة شائعة + CRUD)
# ---------------------------------------------------------------------------

def _procedure_steps(data, required=True):
    """يتحقق من خطوات المسطرة ويعيدها قائمة منظمة (step_number تلقائي)."""
    steps = data.get("steps") if isinstance(data, dict) else None
    if steps is None:
        return None
    if not isinstance(steps, list):
        raise AdminError("steps يجب أن تكون قائمة خطوات.", 400)
    cleaned = []
    for index, raw in enumerate(steps, start=1):
        if not isinstance(raw, dict):
            raise AdminError("كل خطوة يجب أن تكون كائنًا.", 400)
        title = (raw.get("title") or "").strip()
        description = (raw.get("description") or "").strip()
        if not title:
            raise AdminError(f"عنوان الخطوة {index} مطلوب.", 400)
        cleaned.append({
            "step_number": index,
            "title": title,
            "description": description,
            "required_documents": (raw.get("required_documents") or "").strip() or None,
        })
    if required and not cleaned:
        raise AdminError("المسطرة تتطلب خطوة واحدة على الأقل.", 400)
    return cleaned or None


def _procedure_faq(data):
    """يتحقق من الأسئلة الشائعة ويعيدها نص JSON (أو None عند الغياب)."""

    faq = data.get("faq")
    if faq is None:
        return None
    if not isinstance(faq, list):
        raise AdminError("faq يجب أن تكون قائمة أسئلة.", 400)
    cleaned = []
    for raw in faq:
        if not isinstance(raw, dict):
            raise AdminError("كل سؤال في faq يجب أن يكون كائنًا.", 400)
        q = (raw.get("q") or "").strip()
        a = (raw.get("a") or "").strip()
        if q and a:
            cleaned.append({"q": q, "a": a})
    return json.dumps(cleaned, ensure_ascii=False) if cleaned else None


def list_procedures_admin():
    query = (
        """SELECT p.*,
                  (SELECT COUNT(*) FROM procedure_steps s
                   WHERE s.procedure_id = p.id) AS step_count
           FROM procedures p ORDER BY p.title"""
    )
    params = []
    cond, vals = tenant_scope.tenant_eq("p")
    if cond:
        query = (
            """SELECT p.*,
                      (SELECT COUNT(*) FROM procedure_steps s
                       WHERE s.procedure_id = p.id) AS step_count
               FROM procedures p WHERE """
            + cond + " ORDER BY p.title"
        )
        params.extend(vals)
    with db_session() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def create_procedure(admin_id, data):
    slug = (data.get("slug") or "").strip()
    title = (data.get("title") or "").strip()
    if not slug or not title:
        raise AdminError("slug و title مطلوبان.", 400)
    steps = _procedure_steps(data)
    if steps is None:
        raise AdminError("المسطرة تتطلب خطوات (steps).", 400)
    faq = _procedure_faq(data)
    with db_session() as conn:
        try:
            cur = conn.execute(
                """INSERT INTO procedures
                   (slug, title, category, responsible_authority, typical_timeframe,
                    fees, faq)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    slug, title,
                    (data.get("category") or "").strip() or None,
                    (data.get("responsible_authority") or "").strip() or None,
                    (data.get("typical_timeframe") or "").strip() or None,
                    (data.get("fees") or "").strip() or None,
                    faq,
                ),
            )
        except sqlite3.IntegrityError:
            raise AdminError("مسطرة بنفس slug موجودة مسبقًا.", 400)
        procedure_id = cur.lastrowid
        _insert_steps(conn, procedure_id, steps)
        _log_admin_action(
            conn, admin_id, "procedure.create", "procedure", procedure_id
        )
    return procedure_id


def update_procedure(admin_id, procedure_id, data):
    with db_session() as conn:
        sel_q = "SELECT id FROM procedures WHERE id = ?"
        sel_params = [procedure_id]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            sel_q += " AND " + cond
            sel_params.extend(vals)
        row = conn.execute(sel_q, sel_params).fetchone()
        if row is None:
            raise AdminError("المسطرة غير موجودة.", 404)
        updates = {}
        for field in ("title", "category", "responsible_authority",
                      "typical_timeframe", "fees"):
            if field in data:
                updates[field] = (data.get(field) or "").strip() or None
        if "slug" in data:
            updates["slug"] = (data.get("slug") or "").strip()
        if "title" in updates and not updates["title"]:
            raise AdminError("title مطلوب.", 400)
        if "slug" in updates and not updates["slug"]:
            raise AdminError("slug مطلوب.", 400)
        faq = _procedure_faq(data)
        if faq is not None:
            updates["faq"] = faq
        steps = _procedure_steps(data, required=False)
        try:
            if updates:
                sets = ", ".join(f"{k} = ?" for k in updates)
                upd_q = f"UPDATE procedures SET {sets} WHERE id = ?"
                upd_params = list(updates.values()) + [procedure_id]
                if cond:
                    upd_q += " AND " + cond
                    upd_params.extend(vals)
                conn.execute(upd_q, upd_params)
            if steps is not None:
                conn.execute(
                    "DELETE FROM procedure_steps WHERE procedure_id = ?",
                    (procedure_id,),
                )
                _insert_steps(conn, procedure_id, steps)
        except sqlite3.IntegrityError:
            raise AdminError("مسطرة بنفس slug موجودة مسبقًا.", 400)
        _log_admin_action(
            conn, admin_id, "procedure.update", "procedure", procedure_id
        )
    return procedure_id


def _insert_steps(conn, procedure_id, steps):
    for step in steps:
        conn.execute(
            """INSERT INTO procedure_steps
               (procedure_id, step_number, title, description, required_documents)
               VALUES (?, ?, ?, ?, ?)""",
            (
                procedure_id, step["step_number"], step["title"],
                step["description"], step["required_documents"],
            ),
        )


def delete_procedure(admin_id, procedure_id):
    with db_session() as conn:
        sel_q = "SELECT id FROM procedures WHERE id = ?"
        sel_params = [procedure_id]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            sel_q += " AND " + cond
            sel_params.extend(vals)
        row = conn.execute(sel_q, sel_params).fetchone()
        if row is None:
            raise AdminError("المسطرة غير موجودة.", 404)
        del_q = "DELETE FROM procedures WHERE id = ?"
        del_params = [procedure_id]
        if cond:
            del_q += " AND " + cond
            del_params.extend(vals)
        conn.execute(del_q, del_params)
        _log_admin_action(
            conn, admin_id, "procedure.delete", "procedure", procedure_id
        )
    return procedure_id


# ---------------------------------------------------------------------------
# إدارة المواد
# ---------------------------------------------------------------------------

def create_article(admin_id, text_id, data):
    _require_fields(data, ["number", "label", "content"])
    with db_session() as conn:
        text_q = "SELECT id FROM legal_texts WHERE id = ?"
        text_params = [text_id]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            text_q += " AND " + cond
            text_params.extend(vals)
        text = conn.execute(text_q, text_params).fetchone()
        if text is None:
            raise AdminError("النص القانوني غير موجود", 404)
        cur = conn.execute(
            """INSERT INTO articles
               (legal_text_id, number, label, content, plain_explanation, keywords, tenant_id)
               VALUES (?,?,?,?,?,?,?)""",
            (
                text_id, data["number"], data["label"], data["content"],
                data.get("plain_explanation"), data.get("keywords", ""),
                tenant_scope.insert_tenant_id(),
            ),
        )
        new_id = cur.lastrowid
        _log_admin_action(conn, admin_id, "article.create", "article", new_id)
    return new_id


def update_article(admin_id, article_id, data):
    if not isinstance(data, dict) or not data:
        raise AdminError("لا توجد حقول للتحديث", 400)
    with db_session() as conn:
        sel_q = "SELECT id FROM articles WHERE id = ?"
        sel_params = [article_id]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            sel_q += " AND " + cond
            sel_params.extend(vals)
        row = conn.execute(sel_q, sel_params).fetchone()
        if row is None:
            raise AdminError("المادة غير موجودة", 404)
        updates = {f: data[f] for f in _ARTICLE_FIELDS if f in data}
        if "content" in updates and not (updates["content"] or "").strip():
            raise AdminError("محتوى المادة مطلوب", 400)
        if not updates:
            raise AdminError("لا توجد حقول للتحديث", 400)
        sets = ", ".join(f"{k} = ?" for k in updates)
        upd_q = f"UPDATE articles SET {sets} WHERE id = ?"
        upd_params = list(updates.values()) + [article_id]
        if cond:
            upd_q += " AND " + cond
            upd_params.extend(vals)
        conn.execute(upd_q, upd_params)
        _log_admin_action(conn, admin_id, "article.update", "article", article_id)
    return article_id


def _delete_article_row(conn, admin_id, article_id):
    sel_q = "SELECT id FROM articles WHERE id = ?"
    sel_params = [article_id]
    cond, vals = tenant_scope.tenant_eq()
    if cond:
        sel_q += " AND " + cond
        sel_params.extend(vals)
    row = conn.execute(sel_q, sel_params).fetchone()
    if row is None:
        raise AdminError("المادة غير موجودة", 404)
    # الروابط ذات الصلة تُحذف تسلسليًا + مشغّلات FTS
    del_q = "DELETE FROM articles WHERE id = ?"
    del_params = [article_id]
    if cond:
        del_q += " AND " + cond
        del_params.extend(vals)
    conn.execute(del_q, del_params)
    _log_admin_action(conn, admin_id, "article.delete", "article", article_id)
    return article_id


def delete_article(admin_id, article_id):
    with db_session() as conn:
        _delete_article_row(conn, admin_id, article_id)
    return article_id


def bulk_delete_articles(admin_id, ids):
    """حذف جماعي لمواد قانونية (تنظيف الروابط + FTS) في معاملة واحدة."""
    article_ids = parse_bulk_ids(ids)
    with db_session() as conn:
        results = []
        for article_id in article_ids:
            try:
                _delete_article_row(conn, admin_id, article_id)
                results.append(
                    {"id": article_id, "status": "ok", "message": "تم حذف المادة"}
                )
            except AdminError as exc:
                results.append(
                    {"id": article_id, "status": "error", "message": exc.message}
                )
    return bulk_summary("article.delete", results)


# ---------------------------------------------------------------------------
# طابور التحقق من الطلبات المهنية (وثيقة 20 §3.2 / وثيقة المصادقة §3)
# ---------------------------------------------------------------------------

def list_verification_queue():
    placeholders = ",".join("?" for _ in _PROFESSIONAL_ROLES)
    query = (
        f"""SELECT u.id AS user_id, u.email, u.full_name,
                   r.code AS role_code, r.name AS role_name,
                   ur.role_status, ur.rejection_reason,
                   ur.created_at AS requested_at,
                   CASE WHEN p.id IS NULL THEN 0 ELSE 1 END AS has_profile,
                   p.verification_status AS profile_status,
                   CASE WHEN p.verification_document_key IS NULL
                        THEN 0 ELSE 1 END AS has_document,
                   p.verification_document_name AS document_name
            FROM user_roles ur
            JOIN users u ON u.id = ur.user_id
            JOIN roles r ON r.id = ur.role_id
            LEFT JOIN professional_profiles p ON p.user_id = ur.user_id
            WHERE ur.role_status = 'pending_verification'
              AND r.code IN ({placeholders})"""
    )
    params = list(_PROFESSIONAL_ROLES)
    u_cond, u_vals = tenant_scope.tenant_eq("u")
    if u_cond:
        query += " AND " + u_cond
        params.extend(u_vals)
    query += " ORDER BY ur.created_at, u.id"
    with db_session() as conn:
        rows = conn.execute(query, params).fetchall()
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


def _approve_verification_row(conn, admin_id, user_id):
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
    # مزامنة مصدر الحقيقة لظهور الدليل (قرار D-023): إن وُجد ملف مهني
    prof_q = (
        "UPDATE professional_profiles SET verification_status = 'verified', "
        "updated_at = datetime('now') WHERE user_id = ?"
    )
    prof_params = [user_id]
    cond, vals = tenant_scope.tenant_eq()
    if cond:
        prof_q += " AND " + cond
        prof_params.extend(vals)
    conn.execute(prof_q, prof_params)
    _log_admin_action(
        conn, admin_id, "verification.approve", "user", user_id,
        f"role={row['code']}",
    )
    notify(
        conn, user_id, "verification.approved",
        "تم قبول طلب التحقق المهني",
        body="أصبح دورك المهني فعالًا ويمكنك الظهور في الدليل.",
        link=f"/professionals/{user_id}",
        actor_id=admin_id,
    )
    return user_id


def _reject_verification_row(conn, admin_id, user_id, reason):
    reason = (reason or "").strip()
    if not reason:
        raise AdminError("سبب الرفض مطلوب", 400)
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
    prof_q = (
        "UPDATE professional_profiles SET verification_status = 'rejected', "
        "updated_at = datetime('now') WHERE user_id = ?"
    )
    prof_params = [user_id]
    cond, vals = tenant_scope.tenant_eq()
    if cond:
        prof_q += " AND " + cond
        prof_params.extend(vals)
    conn.execute(prof_q, prof_params)
    _log_admin_action(
        conn, admin_id, "verification.reject", "user", user_id,
        f"role={row['code']}; reason={reason}",
    )
    notify(
        conn, user_id, "verification.rejected",
        "تم رفض طلب التحقق المهني",
        body=f"السبب: {reason}",
        actor_id=admin_id,
    )
    return user_id


def approve_verification(admin_id, user_id):
    with db_session() as conn:
        _approve_verification_row(conn, admin_id, user_id)
    return user_id


def reject_verification(admin_id, user_id, reason):
    with db_session() as conn:
        _reject_verification_row(conn, admin_id, user_id, reason)
    return user_id


def bulk_verification(admin_id, action, user_ids, reason=None):
    """قبول/رفض جماعي لطلبات التحقق المهنية (المرحلة 15 — D-033).

    معاملة واحدة: كل عنصر يُعالَج (حالة تحقق + ملف مهني + تدقيق + إشعار)؛
    عنصر غير معلَّق أو غير موجود يُسجَّل فشلًا جزئيًا دون إيقاف الباقي."""
    if action not in ("approve", "reject"):
        raise AdminError("action يجب أن يكون approve أو reject", 400)
    if action == "reject" and not (reason or "").strip():
        raise AdminError("سبب الرفض مطلوب", 400)
    ids = parse_bulk_ids(user_ids, "user_ids")
    with db_session() as conn:
        results = []
        for user_id in ids:
            try:
                if action == "approve":
                    _approve_verification_row(conn, admin_id, user_id)
                else:
                    _reject_verification_row(conn, admin_id, user_id, reason)
                results.append(
                    {"id": user_id, "status": "ok", "message": "تمت المعالجة"}
                )
            except AdminError as exc:
                results.append(
                    {"id": user_id, "status": "error", "message": exc.message}
                )
    return bulk_summary(f"verification.{action}", results)


def get_verification_document(user_id):
    """وثيقة تحقق مخزَّنة لمستخدم — يُستدعى من مسار إداري مصادق فقط (دور admin).

    التخزين محلي (uploads/verification) ريثما يُنقل لمخزن كائنات بمداخل
    موقَّعة (قرار D-023 / Architecture §10)."""
    from .services_professionals import ProfessionalError
    from .services_professionals import get_verification_document as _document

    try:
        return _document(user_id)
    except ProfessionalError as exc:
        raise AdminError(exc.message, exc.status_code) from exc


# ---------------------------------------------------------------------------
# طابور الإشراف المجتمعي (المرحلة 6 — قرار D-024، وثيقة 16 §3)
# ---------------------------------------------------------------------------

MODERATION_ACTIONS = ("dismiss", "hide", "remove")


def list_moderation_queue():
    """بلاغات open مع لمحة عن المحتوى والمبلِّغ — بنمط موحد لطابور الإشراف
    (post|comment|professional_profile، وثيقة API § Admin)."""
    query = (
        """SELECT r.id, r.target_type, r.target_id, r.reason, r.status,
                  r.created_at,
                  u.email AS reporter_email, u.full_name AS reporter_name
           FROM reports r JOIN users u ON u.id = r.reporter_id
           WHERE r.status = 'open'"""
    )
    params = []
    cond, vals = tenant_scope.tenant_eq("r")
    if cond:
        query += " AND " + cond
        params.extend(vals)
    query += " ORDER BY r.created_at, r.id"
    with db_session() as conn:
        rows = conn.execute(query, params).fetchall()
        items = []
        for row in rows:
            item = dict(row)
            item["target"] = _report_target_snapshot(conn, row)
            items.append(item)
        return items


def _report_target_snapshot(conn, report) -> dict:
    """لمحة عن الهدف المدان لإبلاغ المشرف بقراره — الحالة الحالية للمحتوى."""
    target_id = report["target_id"]
    cond, vals = tenant_scope.tenant_eq()
    if report["target_type"] == "post":
        query = (
            """SELECT p.id AS content_id, p.status AS content_status,
                      p.title, p.body, p.user_id AS author_id,
                      u.full_name AS author_name
               FROM posts p JOIN users u ON u.id = p.user_id WHERE p.id = ?"""
        )
        params = [target_id]
        if cond:
            query += " AND " + cond
            params.extend(vals)
        row = conn.execute(query, params).fetchone()
    elif report["target_type"] == "comment":
        query = (
            """SELECT c.id AS content_id, c.status AS content_status,
                      c.post_id, c.body, c.user_id AS author_id,
                      u.full_name AS author_name
               FROM comments c JOIN users u ON u.id = c.user_id WHERE c.id = ?"""
        )
        params = [target_id]
        if cond:
            query += " AND " + cond
            params.extend(vals)
        row = conn.execute(query, params).fetchone()
    else:
        query = (
            """SELECT pp.id AS content_id, pp.verification_status AS content_status,
                      pp.profession_type, u.full_name AS author_name
               FROM professional_profiles pp JOIN users u ON u.id = pp.user_id
               WHERE pp.id = ?"""
        )
        params = [target_id]
        if cond:
            query += " AND " + cond
            params.extend(vals)
        row = conn.execute(query, params).fetchone()
    return dict(row) if row else None


def _moderate_report_row(conn, admin_id, report_id, action):
    if action not in MODERATION_ACTIONS:
        raise AdminError("action يجب أن يكون dismiss أو hide أو remove", 400)
    sel_q = "SELECT * FROM reports WHERE id = ?"
    sel_params = [report_id]
    cond, vals = tenant_scope.tenant_eq()
    if cond:
        sel_q += " AND " + cond
        sel_params.extend(vals)
    row = conn.execute(sel_q, sel_params).fetchone()
    if row is None:
        raise AdminError("البلاغ غير موجود", 404)
    if row["status"] != "open":
        raise AdminError("البلاغ مُعالَج مسبقًا", 409)

    if action == "dismiss":
        new_status = "dismissed"
    else:
        if row["target_type"] not in ("post", "comment"):
            raise AdminError(
                "hide/remove متاح لمحتوى المنشورات والتعليقات فقط", 400
            )
        new_status = "actioned"
        table = row["target_type"] + "s"
        upd_q = (
            f"UPDATE {table} SET status = ?, updated_at = datetime('now') "
            "WHERE id = ?"
        )
        upd_params = [action, row["target_id"]]
        if cond:
            upd_q += " AND " + cond
            upd_params.extend(vals)
        updated = conn.execute(upd_q, upd_params)
        if updated.rowcount == 0:
            raise AdminError("المحتوى الهدف غير موجود", 404)
        # إشعار صاحب المحتوى بقرار الإشراف (إزالة/حجب)
        owner_q = f"SELECT user_id FROM {table} WHERE id = ?"
        owner_params = [row["target_id"]]
        if cond:
            owner_q += " AND " + cond
            owner_params.extend(vals)
        owner = conn.execute(owner_q, owner_params).fetchone()
        if owner:
            if action == "remove":
                type_, title, body = (
                    "moderation.content_removed", "إزالة محتوى بقرار الإشراف",
                    "تمت إزالة محتواك من المجتمع بقرار من الإشراف.",
                )
            else:
                type_, title, body = (
                    "moderation.content_hidden", "حجب محتوى بقرار الإشراف",
                    "تم حجب محتواك عن الظهور بقرار من الإشراف.",
                )
            notify(conn, owner["user_id"], type_, title, body=body,
                   actor_id=admin_id)
    upd2_q = (
        "UPDATE reports SET status = ?, resolved_at = datetime('now'), "
        "resolved_by = ? WHERE id = ?"
    )
    upd2_params = [new_status, admin_id, report_id]
    if cond:
        upd2_q += " AND " + cond
        upd2_params.extend(vals)
    conn.execute(upd2_q, upd2_params)
    _log_admin_action(
        conn, admin_id, f"moderation.{action}", "report", report_id,
        f"target={row['target_type']}:{row['target_id']}",
    )
    return {"id": report_id, "status": new_status, "message": "تمت معالجة البلاغ."}


def moderate_report(admin_id, report_id, action):
    with db_session() as conn:
        return _moderate_report_row(conn, admin_id, report_id, action)


def bulk_moderation(admin_id, action, report_ids):
    """معالجة جماعية لبلاغات الإشراف (المرحلة 15 — D-033).

    معاملة واحدة: كل بلاغ يُعالَج وفق قواعد moderate_report الفردية؛
    بلاغ غير موجود/مُعالَج سابقًا، أو hide/remove على هدف غير مسموح،
    يُسجَّل فشلًا جزئيًا دون إيقاف الباقي."""
    if action not in MODERATION_ACTIONS:
        raise AdminError("action يجب أن يكون dismiss أو hide أو remove", 400)
    ids = parse_bulk_ids(report_ids, "report_ids")
    with db_session() as conn:
        results = []
        for report_id in ids:
            try:
                result = _moderate_report_row(conn, admin_id, report_id, action)
                results.append(
                    {"id": report_id, "status": "ok", "message": result["message"]}
                )
            except AdminError as exc:
                results.append(
                    {"id": report_id, "status": "error", "message": exc.message}
                )
    return bulk_summary(f"moderation.{action}", results)
