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

from . import config, services_auth, tenant_scope
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
    query = (
        f"SELECT profile_id, specialty FROM professional_specialties "
        f"WHERE profile_id IN ({placeholders}) ORDER BY id"
    )
    params = list(profile_ids)
    cond, vals = tenant_scope.tenant_eq()
    if cond:
        query += " AND " + cond
        params.extend(vals)
    rows = conn.execute(query, params).fetchall()
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
        "photo_url": row.get("photo_url"),
        "registration_number": row.get("registration_number"),
        "address": row.get("address"),
        "website": row.get("website"),
        "years_of_experience": row.get("years_of_experience"),
        "work_hours": row.get("work_hours"),
        "map_embed": row.get("map_embed"),
    }
    if row.get("social_links"):
        import json

        try:
            item["social_links"] = json.loads(row["social_links"])
        except (TypeError, ValueError):
            item["social_links"] = {}
    else:
        item["social_links"] = {}
    if row["contact_preference"] == "visible":
        item["phone"] = row["phone"]
        item["email"] = row.get("email")
    if reviews is not None:
        item["reviews"] = reviews
    return item


def _list_columns() -> str:
    # عزل المستأجر (D-036): إحصاءات التقييمات تُحسب ضمن مستأجر الملف فقط
    review_scope = " AND r.tenant_id IS p.tenant_id" if tenant_scope.active() else ""
    return (
        "SELECT p.id, u.full_name, u.email, p.profession_type, p.city, p.bio, "
        "p.contact_preference, p.phone, p.photo_url, p.registration_number, "
        "p.address, p.website, p.years_of_experience, p.work_hours, "
        "p.social_links, p.map_embed, "
        "COALESCE((SELECT ROUND(AVG(r.rating), 1) FROM professional_reviews r "
        f"          WHERE r.profile_id = p.id{review_scope}), 0) AS rating, "
        f"(SELECT COUNT(*) FROM professional_reviews r "
        f" WHERE r.profile_id = p.id{review_scope}) AS review_count "
        "FROM professional_profiles p JOIN users u ON u.id = p.user_id"
    )


def list_professionals(profession_type=None, specialty=None, city=None,
                       limit: int = DEFAULT_LIST_LIMIT, offset: int = 0):
    limit = max(1, min(int(limit or DEFAULT_LIST_LIMIT), MAX_LIST_LIMIT))
    offset = max(0, int(offset or 0))
    query = _list_columns()
    conditions = ["p.verification_status = 'verified'", "u.status = 'active'"]
    params = []
    p_cond, p_vals = tenant_scope.tenant_eq("p")
    if p_cond:
        conditions.append(p_cond)
        params.extend(p_vals)
    if profession_type:
        if profession_type not in PROFESSION_TYPES:
            raise ProfessionalError("نوع المهنة غير صالح.", 400)
        conditions.append("p.profession_type = ?")
        params.append(profession_type)
    if city:
        conditions.append("p.city = ?")
        params.append(city)
    if specialty:
        s_cond, s_vals = tenant_scope.tenant_eq("s")
        spec_q = (
            "EXISTS (SELECT 1 FROM professional_specialties s "
            "        WHERE s.profile_id = p.id AND s.specialty = ?)"
        )
        params.append(specialty)
        if s_cond:
            spec_q = (
                "EXISTS (SELECT 1 FROM professional_specialties s "
                f"        WHERE s.profile_id = p.id AND s.specialty = ? AND {s_cond})"
            )
            params.extend(s_vals)
        conditions.append(spec_q)
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
    conditions = [
        "p.id = ?", "p.verification_status = 'verified'", "u.status = 'active'",
    ]
    params = [profile_id]
    p_cond, p_vals = tenant_scope.tenant_eq("p")
    if p_cond:
        conditions.append(p_cond)
        params.extend(p_vals)
    query += " WHERE " + " AND ".join(conditions)
    with db_session() as conn:
        row = conn.execute(query, params).fetchone()
        if not row:
            return None
        specs = _specialties_map(conn, [profile_id]).get(profile_id, [])
        reviews_q = (
            """SELECT r.rating, r.comment, r.created_at, u.full_name AS reviewer_name
               FROM professional_reviews r JOIN users u ON u.id = r.reviewer_id
               WHERE r.profile_id = ? ORDER BY r.created_at DESC, r.id DESC"""
        )
        reviews_params = [profile_id]
        r_cond, r_vals = tenant_scope.tenant_eq("r")
        if r_cond:
            reviews_q = (
                """SELECT r.rating, r.comment, r.created_at, u.full_name AS reviewer_name
                   FROM professional_reviews r JOIN users u ON u.id = r.reviewer_id
                   WHERE r.profile_id = ? AND """
                + r_cond
                + " ORDER BY r.created_at DESC, r.id DESC"
            )
            reviews_params.extend(r_vals)
        reviews = conn.execute(reviews_q, reviews_params).fetchall()
        return _public_profile(
            dict(row), specs, reviews=[dict(r) for r in reviews]
        )


def get_profile_for_user(user_id: int):
    """ملف المستخدم المهني بحالة تحققه — للاستجابة الذاتية (يرى وثيقته)."""
    review_scope = " AND r.tenant_id IS p.tenant_id" if tenant_scope.active() else ""
    query = (
        f"""SELECT p.*, u.full_name, u.email,
                   (SELECT COUNT(*) FROM professional_reviews r
                    WHERE r.profile_id = p.id{review_scope}) AS review_count
            FROM professional_profiles p JOIN users u ON u.id = p.user_id
            WHERE p.user_id = ?"""
    )
    params = [user_id]
    p_cond, p_vals = tenant_scope.tenant_eq("p")
    if p_cond:
        query += " AND " + p_cond
        params.extend(p_vals)
    with db_session() as conn:
        row = conn.execute(query, params).fetchone()
        if not row:
            return None
        d = dict(row)
        d["specialties"] = _specialties_map(conn, [d["id"]]).get(d["id"], [])
        d["has_document"] = bool(d.pop("verification_document_key"))
        d.pop("verification_document_key", None)
        d.pop("verification_document_name", None)
        if d.get("social_links"):
            import json

            try:
                d["social_links"] = json.loads(d["social_links"])
            except (TypeError, ValueError):
                d["social_links"] = {}
        else:
            d["social_links"] = {}
        return d


def _optional_text(value) -> str | None:
    value = (value or "").strip()
    return value or None


def _optional_int(value) -> int | None:
    if value in (None, ""):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise ProfessionalError("years_of_experience يجب أن يكون رقمًا.", 400)
    if parsed < 0:
        raise ProfessionalError("years_of_experience لا يمكن أن يكون سالبًا.", 400)
    return parsed


def _social_links_json(value) -> str | None:
    """يقبّل كائن JSON لوسائل التواصل (أو نص JSON) ويعيده نص JSON موحَّدًا."""
    import json

    if value in (None, ""):
        return None
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError):
            parsed = None
    else:
        parsed = value
    if not isinstance(parsed, dict):
        raise ProfessionalError("social_links يجب أن يكون كائنًا.", 400)
    allowed = ("facebook", "twitter", "linkedin", "instagram", "whatsapp")
    cleaned = {k: str(v).strip() for k, v in parsed.items()
               if k in allowed and str(v).strip()}
    return json.dumps(cleaned, ensure_ascii=False) if cleaned else None


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
    extra = {
        "photo_url": _optional_text(data.get("photo_url")),
        "registration_number": _optional_text(data.get("registration_number")),
        "address": _optional_text(data.get("address")),
        "website": _optional_text(data.get("website")),
        "years_of_experience": _optional_int(data.get("years_of_experience")),
        "work_hours": _optional_text(data.get("work_hours")),
        "social_links": _social_links_json(data.get("social_links")),
        "map_embed": _optional_text(data.get("map_embed")),
    }
    with db_session() as conn:
        if not _has_usable_professional_role(conn, user_id):
            raise ProfessionalError("يتطلب حسابًا مهنيًا.", 403)
        sel_q = "SELECT id FROM professional_profiles WHERE user_id = ?"
        sel_params = [user_id]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            sel_q += " AND " + cond
            sel_params.extend(vals)
        existing = conn.execute(sel_q, sel_params).fetchone()
        if existing:
            upd_q = (
                "UPDATE professional_profiles SET profession_type = ?, bio = ?, "
                "city = ?, phone = ?, contact_preference = ?, photo_url = ?, "
                "registration_number = ?, address = ?, website = ?, "
                "years_of_experience = ?, work_hours = ?, social_links = ?, "
                "map_embed = ?, updated_at = datetime('now') WHERE id = ?"
            )
            upd_params = [
                profession_type, bio, city, phone, contact_pref,
                extra["photo_url"], extra["registration_number"],
                extra["address"], extra["website"],
                extra["years_of_experience"], extra["work_hours"],
                extra["social_links"], extra["map_embed"], existing["id"],
            ]
            if cond:
                upd_q += " AND " + cond
                upd_params.extend(vals)
            conn.execute(upd_q, upd_params)
            profile_id = existing["id"]
            del_q = "DELETE FROM professional_specialties WHERE profile_id = ?"
            del_params = [profile_id]
            if cond:
                del_q += " AND " + cond
                del_params.extend(vals)
            conn.execute(del_q, del_params)
        else:
            cur = conn.execute(
                "INSERT INTO professional_profiles "
                "(user_id, profession_type, bio, city, contact_preference, phone, "
                "photo_url, registration_number, address, website, "
                "years_of_experience, work_hours, social_links, map_embed, "
                "tenant_id, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
                "datetime('now'), datetime('now'))",
                (user_id, profession_type, bio, city, contact_pref, phone,
                 extra["photo_url"], extra["registration_number"],
                 extra["address"], extra["website"],
                 extra["years_of_experience"], extra["work_hours"],
                 extra["social_links"], extra["map_embed"],
                 tenant_scope.insert_tenant_id()),
            )
            profile_id = cur.lastrowid
        for specialty in specialties:
            conn.execute(
                "INSERT INTO professional_specialties (profile_id, specialty, "
                "tenant_id) VALUES (?, ?, ?)",
                (profile_id, specialty, tenant_scope.insert_tenant_id()),
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
        sel_q = (
            "SELECT id, verification_document_key FROM professional_profiles "
            "WHERE user_id = ?"
        )
        sel_params = [user_id]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            sel_q += " AND " + cond
            sel_params.extend(vals)
        row = conn.execute(sel_q, sel_params).fetchone()
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
        upd_q = (
            "UPDATE professional_profiles SET verification_document_key = ?, "
            "verification_document_name = ?, updated_at = datetime('now') "
            "WHERE id = ?"
        )
        upd_params = [storage_name, filename, row["id"]]
        if cond:
            upd_q += " AND " + cond
            upd_params.extend(vals)
        conn.execute(upd_q, upd_params)
        profile_id = row["id"]
    return {
        "id": profile_id,
        "document_name": filename,
        "message": "تم رفع وثيقة التحقق.",
    }


def get_verification_document(user_id: int):
    """مسار/اسم وثيقة التحقق المخزنة لمستخدم — يُستخدم من المسار الإداري فقط."""
    query = (
        "SELECT verification_document_key, verification_document_name "
        "FROM professional_profiles WHERE user_id = ?"
    )
    params = [user_id]
    cond, vals = tenant_scope.tenant_eq()
    if cond:
        query += " AND " + cond
        params.extend(vals)
    with db_session() as conn:
        row = conn.execute(query, params).fetchone()
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
        sel_q = (
            """SELECT p.user_id, p.verification_status
               FROM professional_profiles p JOIN users u ON u.id = p.user_id
               WHERE p.id = ? AND u.status = 'active'"""
        )
        sel_params = [profile_id]
        p_cond, p_vals = tenant_scope.tenant_eq("p")
        if p_cond:
            sel_q += " AND " + p_cond
            sel_params.extend(p_vals)
        row = conn.execute(sel_q, sel_params).fetchone()
        if not row or row["verification_status"] != "verified":
            raise ProfessionalError("الملف المهني غير موجود.", 404)
        if row["user_id"] == reviewer_id:
            raise ProfessionalError("لا يمكنك تقييم ملفك الخاص.", 403)
        conn.execute(
            """INSERT INTO professional_reviews
               (profile_id, reviewer_id, rating, comment, tenant_id,
                created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
               ON CONFLICT(profile_id, reviewer_id) DO UPDATE SET
                 rating = excluded.rating,
                 comment = excluded.comment,
                 tenant_id = excluded.tenant_id,
                 updated_at = datetime('now')""",
            (profile_id, reviewer_id, rating, comment or None,
             tenant_scope.insert_tenant_id()),
        )
        rid_q = (
            "SELECT id FROM professional_reviews "
            "WHERE profile_id = ? AND reviewer_id = ?"
        )
        rid_params = [profile_id, reviewer_id]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            rid_q += " AND " + cond
            rid_params.extend(vals)
        review_id = conn.execute(rid_q, rid_params).fetchone()["id"]
        agg_q = (
            """SELECT ROUND(AVG(rating), 1) AS avg_rating, COUNT(*) AS count
               FROM professional_reviews WHERE profile_id = ?"""
        )
        agg_params = [profile_id]
        if cond:
            agg_q += " AND " + cond
            agg_params.extend(vals)
        agg = conn.execute(agg_q, agg_params).fetchone()
    return {
        "id": review_id,
        "rating": agg["avg_rating"] if agg["avg_rating"] else 0,
        "review_count": agg["count"],
        "message": "تم تسجيل التقييم.",
    }
