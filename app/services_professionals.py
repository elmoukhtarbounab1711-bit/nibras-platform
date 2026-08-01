"""
خدمات النظام البيئي المهني (المرحلة 5) — قرار D-023.

دليل مهني واحد (نوع المهنة كمعرّف تمييز، وثيقة 17 §1) لا يظهر في البحث
العام إلا للملفات verified + مستخدمين نشطين — مُنفَّذ عند مستوى الاستعلام
(وثيقة 17 §2/§7). الملف مهني ذاتي (POST /profile) يبدأ pending، ورفع وثيقة
التحقق (POST /verify-document) محلي في uploads/ (قرار D-023)، وقبول/رفض
الأدمن (الطابور القائم) يزامن verification_status. التقييمات مفتوحة بمراجعة
واحدة لكل مقيِّم (upsert) وبلا تقييم ذاتي. تدرجات الاشتراك مؤجَّلة لحسم
بوابة الدفع.
"""
import os
import secrets
from pathlib import Path

from . import config, services_auth
from .database import db_session

# أنواع مهنة الدليل (وثيقة 17 §1) — company/institution خارج قائمة الدليل
PROFESSION_TYPES = (
    "lawyer", "notary", "adoul", "judicial_commissioner",
    "sworn_translator", "judicial_expert",
)
CONTACT_PREFERENCES = ("visible", "platform")
MAX_SPECIALTIES = 10
DEFAULT_LIST_LIMIT = 20
MAX_LIST_LIMIT = 100

_CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}


class ProfessionalError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _uploads_dir() -> Path:
    if config.UPLOAD_DIR:
        base = Path(config.UPLOAD_DIR)
    else:
        base = Path(__file__).resolve().parent.parent / "uploads"
    return base / "verification"


def _has_usable_professional_role(conn, user_id: int) -> bool:
    """دور مهني غير مرفوض (pending أو active) — أهلية إنشاء الملف/الرفع."""
    rows = conn.execute(
        """SELECT r.code, ur.role_status
           FROM user_roles ur JOIN roles r ON r.id = ur.role_id
           WHERE ur.user_id = ?""",
        (user_id,),
    ).fetchall()
    return any(
        row["code"] in services_auth.PROFESSIONAL_ROLES
        and row["role_status"] != "rejected"
        for row in rows
    )


def _normalize_specialties(value) -> list:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ProfessionalError("التخصصات يجب أن تكون قائمة (specialties).", 400)
    cleaned = []
    for item in value:
        text = str(item).strip()
        if text:
            cleaned.append(text[:80])
    seen = []
    for item in cleaned:
        if item not in seen:
            seen.append(item)
    if len(seen) > MAX_SPECIALTIES:
        raise ProfessionalError(f"لا يمكن إضافة أكثر من {MAX_SPECIALTIES} تخصصًا.", 400)
    return seen


def _specialties_map(conn, profile_ids: list) -> dict:
    if not profile_ids:
        return {}
    placeholders = ",".join("?" for _ in profile_ids)
    rows = conn.execute(
        f"SELECT profile_id, specialty FROM professional_specialties "
        f"WHERE profile_id IN ({placeholders}) ORDER BY id",
        profile_ids,
    ).fetchall()
    out = {}
    for row in rows:
        out.setdefault(row["profile_id"], []).append(row["specialty"])
    return out


def _public_profile(row, specialties: list, reviews=None) -> dict:
    item = {
        "id": row["id"],
        "full_name": row["full_name"],
        "profession_type": row["profession_type"],
        "city": row["city"],
        "bio": row["bio"],
        "specialties": specialties,
        "rating": round(row["rating"], 1) if row["rating"] else 0,
        "review_count": row["review_count"],
        "contact_preference": row["contact_preference"],
    }
    if row["contact_preference"] == "visible":
        item["phone"] = row["phone"]
    if reviews is not None:
        item["reviews"] = reviews
    return item


def _list_columns() -> str:
    return (
        "SELECT p.id, u.full_name, p.profession_type, p.city, p.bio, "
        "p.contact_preference, p.phone, "
        "COALESCE((SELECT ROUND(AVG(r.rating), 1) FROM professional_reviews r "
        "          WHERE r.profile_id = p.id), 0) AS rating, "
        "(SELECT COUNT(*) FROM professional_reviews r "
        " WHERE r.profile_id = p.id) AS review_count "
        "FROM professional_profiles p JOIN users u ON u.id = p.user_id"
    )


def list_professionals(profession_type=None, specialty=None, city=None,
                       limit: int = DEFAULT_LIST_LIMIT, offset: int = 0):
    limit = max(1, min(int(limit or DEFAULT_LIST_LIMIT), MAX_LIST_LIMIT))
    offset = max(0, int(offset or 0))
    query = _list_columns()
    conditions = ["p.verification_status = 'verified'", "u.status = 'active'"]
    params = []
    if profession_type:
        if profession_type not in PROFESSION_TYPES:
            raise ProfessionalError("نوع المهنة غير صالح.", 400)
        conditions.append("p.profession_type = ?")
        params.append(profession_type)
    if city:
        conditions.append("p.city = ?")
        params.append(city)
    if specialty:
        conditions.append(
            "EXISTS (SELECT 1 FROM professional_specialties s "
            "        WHERE s.profile_id = p.id AND s.specialty = ?)"
        )
        params.append(specialty)
    query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY u.full_name LIMIT ? OFFSET ?"
    params += [limit, offset]
    with db_session() as conn:
        rows = conn.execute(query, params).fetchall()
        ids = [r["id"] for r in rows]
        specs = _specialties_map(conn, ids)
        return [_public_profile(dict(r), specs.get(r["id"], [])) for r in rows]


def get_profile_public(profile_id: int):
    query = _list_columns()
    query += (
        " WHERE p.id = ? AND p.verification_status = 'verified' "
        "AND u.status = 'active'"
    )
    with db_session() as conn:
        row = conn.execute(query, (profile_id,)).fetchone()
        if not row:
            return None
        specs = _specialties_map(conn, [profile_id]).get(profile_id, [])
        reviews = conn.execute(
            """SELECT r.rating, r.comment, r.created_at, u.full_name AS reviewer_name
               FROM professional_reviews r JOIN users u ON u.id = r.reviewer_id
               WHERE r.profile_id = ? ORDER BY r.created_at DESC, r.id DESC""",
            (profile_id,),
        ).fetchall()
        return _public_profile(
            dict(row), specs, reviews=[dict(r) for r in reviews]
        )


def get_profile_for_user(user_id: int):
    """ملف المستخدم المهني بحالة تحققه — للاستجابة الذاتية (يرى وثيقته)."""
    with db_session() as conn:
        row = conn.execute(
            """SELECT p.*, u.full_name,
                      (SELECT COUNT(*) FROM professional_reviews r
                       WHERE r.profile_id = p.id) AS review_count
               FROM professional_profiles p JOIN users u ON u.id = p.user_id
               WHERE p.user_id = ?""",
            (user_id,),
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["specialties"] = _specialties_map(conn, [d["id"]]).get(d["id"], [])
        d["has_document"] = bool(d.pop("verification_document_key"))
        d.pop("verification_document_key", None)
        d.pop("verification_document_name", None)
        return d


def upsert_profile(user_id: int, data: dict) -> dict:
    profession_type = (data.get("profession_type") or "").strip()
    if profession_type not in PROFESSION_TYPES:
        raise ProfessionalError("نوع المهنة غير صالح.", 400)
    bio = (data.get("bio") or "").strip()
    city = (data.get("city") or "").strip()
    phone = (data.get("phone") or "").strip()
    contact_pref = (data.get("contact_preference") or "platform").strip()
    if contact_pref not in CONTACT_PREFERENCES:
        raise ProfessionalError("contact_preference يجب أن يكون visible أو platform.", 400)
    specialties = _normalize_specialties(data.get("specialties"))
    with db_session() as conn:
        if not _has_usable_professional_role(conn, user_id):
            raise ProfessionalError("يتطلب حسابًا مهنيًا.", 403)
        existing = conn.execute(
            "SELECT id FROM professional_profiles WHERE user_id = ?", (user_id,)
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE professional_profiles SET profession_type = ?, bio = ?, "
                "city = ?, phone = ?, contact_preference = ?, "
                "updated_at = datetime('now') WHERE id = ?",
                (profession_type, bio, city, phone, contact_pref, existing["id"]),
            )
            profile_id = existing["id"]
            conn.execute(
                "DELETE FROM professional_specialties WHERE profile_id = ?",
                (profile_id,),
            )
        else:
            cur = conn.execute(
                "INSERT INTO professional_profiles "
                "(user_id, profession_type, bio, city, contact_preference, phone, "
                "created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, "
                "datetime('now'), datetime('now'))",
                (user_id, profession_type, bio, city, contact_pref, phone),
            )
            profile_id = cur.lastrowid
        for specialty in specialties:
            conn.execute(
                "INSERT INTO professional_specialties (profile_id, specialty) "
                "VALUES (?, ?)",
                (profile_id, specialty),
            )
    return get_profile_for_user(user_id)


def upload_verification_document(user_id: int, file) -> dict:
    """يرفع وثيقة التحقق (multipart) ويستبدل السابقة إن وُجدت — التخزين
    محلي في uploads/verification (قرار D-023). لا يغيّر حالة التحقق."""
    filename = (file.filename or "").strip()
    ext = os.path.splitext(filename)[1].lower()
    if ext not in config.ALLOWED_UPLOAD_EXTENSIONS:
        raise ProfessionalError(
            "صيغة الملف غير مسموح بها (pdf أو jpg أو png).", 400
        )
    content = file.read()
    if not content:
        raise ProfessionalError("الملف فارغ.", 400)
    if len(content) > config.MAX_UPLOAD_BYTES:
        raise ProfessionalError(
            f"الملف يتجاوز الحد الأقصى ({config.MAX_UPLOAD_BYTES // (1024 * 1024)}MB).",
            400,
        )
    with db_session() as conn:
        if not _has_usable_professional_role(conn, user_id):
            raise ProfessionalError("يتطلب حسابًا مهنيًا.", 403)
        row = conn.execute(
            "SELECT id, verification_document_key FROM professional_profiles "
            "WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if not row:
            raise ProfessionalError(
                "أنشئ ملفك المهني أولًا (POST /api/professionals/profile).", 400
            )
        old_key = row["verification_document_key"]
        storage_name = f"{user_id}_{secrets.token_urlsafe(12)}{ext}"
        uploads = _uploads_dir()
        uploads.mkdir(parents=True, exist_ok=True)
        (uploads / storage_name).write_bytes(content)
        if old_key:
            try:
                (uploads / os.path.basename(old_key)).unlink(missing_ok=True)
            except OSError:
                pass
        conn.execute(
            "UPDATE professional_profiles SET verification_document_key = ?, "
            "verification_document_name = ?, updated_at = datetime('now') "
            "WHERE id = ?",
            (storage_name, filename, row["id"]),
        )
        profile_id = row["id"]
    return {
        "id": profile_id,
        "document_name": filename,
        "message": "تم رفع وثيقة التحقق.",
    }


def get_verification_document(user_id: int):
    """مسار/اسم وثيقة التحقق المخزنة لمستخدم — يُستخدم من المسار الإداري فقط."""
    with db_session() as conn:
        row = conn.execute(
            "SELECT verification_document_key, verification_document_name "
            "FROM professional_profiles WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    if not row or not row["verification_document_key"]:
        raise ProfessionalError("لا توجد وثيقة تحقق لهذا المستخدم.", 404)
    path = _uploads_dir() / os.path.basename(row["verification_document_key"])
    if not path.exists():
        raise ProfessionalError("ملف الوثيقة غير موجود على القرص.", 404)
    ext = os.path.splitext(row["verification_document_key"])[1].lower()
    content_type = _CONTENT_TYPES.get(ext, "application/octet-stream")
    return str(path), row["verification_document_name"] or "verification", content_type


def add_review(reviewer_id: int, profile_id: int, rating, comment=None) -> dict:
    try:
        rating = int(rating)
    except (TypeError, ValueError):
        raise ProfessionalError("التقييم (rating) مطلوب بين 1 و 5.", 400)
    if rating < 1 or rating > 5:
        raise ProfessionalError("التقييم (rating) يجب أن يكون بين 1 و 5.", 400)
    comment = (comment or "").strip()
    with db_session() as conn:
        row = conn.execute(
            """SELECT p.user_id, p.verification_status
               FROM professional_profiles p JOIN users u ON u.id = p.user_id
               WHERE p.id = ? AND u.status = 'active'""",
            (profile_id,),
        ).fetchone()
        if not row or row["verification_status"] != "verified":
            raise ProfessionalError("الملف المهني غير موجود.", 404)
        if row["user_id"] == reviewer_id:
            raise ProfessionalError("لا يمكنك تقييم ملفك الخاص.", 403)
        conn.execute(
            """INSERT INTO professional_reviews
               (profile_id, reviewer_id, rating, comment, created_at, updated_at)
               VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
               ON CONFLICT(profile_id, reviewer_id) DO UPDATE SET
                 rating = excluded.rating,
                 comment = excluded.comment,
                 updated_at = datetime('now')""",
            (profile_id, reviewer_id, rating, comment or None),
        )
        review_id = conn.execute(
            "SELECT id FROM professional_reviews "
            "WHERE profile_id = ? AND reviewer_id = ?",
            (profile_id, reviewer_id),
        ).fetchone()["id"]
        agg = conn.execute(
            """SELECT ROUND(AVG(rating), 1) AS avg_rating, COUNT(*) AS count
               FROM professional_reviews WHERE profile_id = ?""",
            (profile_id,),
        ).fetchone()
    return {
        "id": review_id,
        "rating": agg["avg_rating"] if agg["avg_rating"] else 0,
        "review_count": agg["count"],
        "message": "تم تسجيل التقييم.",
    }
