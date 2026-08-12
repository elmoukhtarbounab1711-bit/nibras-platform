"""
خدمات نظام الإعلانات (المرحلة 9 — إتمام Roadmap Phase 6، قرار D-027).

نموذج حسب الوثيقة 15 وقاعدة البيانات §11: فتحات ثابتة تُبذر، حملات بثلاثة
أنواع (general/sponsored/professional_promotion) واستهداف v1 (فتحة + نطاق
تواريخ فقط)، وأحداث انطباع/نقرة للتتبع (§6). الخدمة تعيد الحملة النشطة
للفتحة أو None، وتتابع الأحداث، وتُدير الحملات إداريًا (مع إحصائيات
impressions/clicks/ctr). الإدارة تُسجَّل في admin_audit_log (Security §8)
بنمط ads.*. الفصل البصري للإعلان عن المحتوى القانوني (وثيقة 15 §7)
مسؤولية الواجهة؛ هنا يُكشف نوع الحملة (sponsored) في استجابة الخدمة.
"""
from urllib.parse import urlparse

from . import tenant_scope
from .database import db_session
from .services_admin import _log_admin_action, bulk_summary, parse_bulk_ids

# فتحات الواجهة (وثيقة 15 §2) — تُبذر في ensure_defaults (قرار D-027)
SLOT_SEED = (
    ("library_sidebar", "شريط المكتبة الجانبي"),
    ("search_results_top", "أعلى نتائج البحث"),
    ("directory_listing_top", "أعلى قائمة الدليل"),
)

CAMPAIGN_TYPES = ("general", "sponsored", "professional_promotion")
CAMPAIGN_STATUSES = ("active", "paused", "ended")

# الاستهداف الفئوي (المرحلة 19 — قرار D-037): أنواع الفئات المستهدفة
# (فئتا الدليل/المجتمع عامتان بلا استهداف فئوي — تُفعَّل لاحقًا).
TARGET_CATEGORY_TYPES = ("library", "marketplace", "jurisprudence")


class AdError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def ensure_defaults():
    """بذر فتحات الإعلانات إن كانت فارغة (idempotent — نمط ensure_defaults)."""
    with db_session() as conn:
        count = conn.execute(
            "SELECT COUNT(*) AS c FROM ad_slots"
        ).fetchone()["c"]
        if count == 0:
            for slug, name in SLOT_SEED:
                conn.execute(
                    "INSERT INTO ad_slots (slug, name) VALUES (?, ?)",
                    (slug, name),
                )


def _slot_exists(conn, slot_id) -> bool:
    return conn.execute(
        "SELECT 1 FROM ad_slots WHERE id = ?", (slot_id,)
    ).fetchone() is not None


def _validate_url(value, field: str) -> str:
    """رابط http/https فقط (يستبعد javascript: وغيرها — Security §7)."""
    url = (value or "").strip()
    if not url:
        raise AdError(f"{field} مطلوب.", 400)
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise AdError(f"{field} يجب أن يكون رابطًا http/https صالحًا.", 400)
    return url


def _normalize_dt(value):
    """يوحّد صيغة التاريخ للقارنة النصية (T → مسافة) ويُفرغ القيم الفارغة."""
    if value is None:
        return None
    value = str(value).strip()
    return value.replace("T", " ") or None


def _validate_dates(data: dict) -> tuple:
    starts_at = _normalize_dt(data.get("starts_at"))
    ends_at = _normalize_dt(data.get("ends_at"))
    if starts_at and ends_at and ends_at < starts_at:
        raise AdError("ends_at يجب أن لا يسبق starts_at.", 400)
    return starts_at, ends_at


def _check_profile(conn, profile_id: int):
    query = (
        "SELECT verification_status FROM professional_profiles WHERE id = ?"
    )
    params = [profile_id]
    cond, vals = tenant_scope.tenant_eq()
    if cond:
        query += " AND " + cond
        params.extend(vals)
    profile = conn.execute(query, params).fetchone()
    if profile is None:
        raise AdError("الملف المهني غير موجود.", 400)
    if profile["verification_status"] != "verified":
        raise AdError("الملف المهني يجب أن يكون محقَّقًا (verified).", 400)


# جدول الفئات لكل نوع استهداف (المرحلة 19 — D-037)
_TARGET_TABLE = {
    "library": "categories",
    "marketplace": "marketplace_categories",
    "jurisprudence": "jurisprudence_categories",
}


def _parse_target(conn, data: dict) -> tuple:
    """يحلّل الاستهداف الفئوي إلى (target_category_type, target_category_id).

    غياب الحقلين = حملة عامة (None, None). حضور أحدهما فقط يرفض. نوعٌ غير
    مدعوم أو فئة غير موجودة ضمن مستأجر الطلب يرفض (تحقق عبر الجدول المعني).
    """
    dtype = (data.get("target_category_type") or "").strip() or None
    if "target_category_type" in data and not dtype:
        # قيمة فارغة صراحة = إلغاء الاستهداف (تحويل حملة مستهدفة إلى عامة)
        if (data.get("target_category_id") or "") not in ("", None):
            raise AdError("target_category_id يتطلب target_category_type.", 400)
        return None, None
    if dtype is None:
        if data.get("target_category_id") not in (None, ""):
            raise AdError(
                "target_category_id يتطلب target_category_type.", 400
            )
        return None, None
    if dtype not in TARGET_CATEGORY_TYPES:
        raise AdError(
            "target_category_type يجب أن يكون library أو marketplace أو "
            "jurisprudence.",
            400,
        )
    try:
        cid = int(data.get("target_category_id"))
    except (TypeError, ValueError):
        raise AdError("target_category_id مطلوب للاستهداف الفئوي.", 400)
    query = f"SELECT 1 FROM {_TARGET_TABLE[dtype]} WHERE id = ?"
    params = [cid]
    cond, vals = tenant_scope.tenant_eq()
    if cond:
        query += " AND " + cond
        params.extend(vals)
    if conn.execute(query, params).fetchone() is None:
        raise AdError("الفئة المستهدفة غير موجودة.", 400)
    return dtype, cid


# ---------------------------------------------------------------------------
# الخدمة العامة
# ---------------------------------------------------------------------------

def serve(slot_slug: str, category_type: str | None = None,
          category_id: int | None = None):
    """يعيد الحملة النشطة للفتحة أو None (بلا أي كتابة — التتبع منفصل).

    الاستهداف الفئوي (المرحلة 19 — D-037): عند تمرير سياق الفئة
    (category_type/category_id) تُفضَّل الحملات المستهدفة لنفس الفئة أولًا
    ثم تُعاد العامة بلا استهداف؛ ودون سياق تُرسَل الحملات العامة فقط —
    المستهدفة لا تظهر إلا في سياق فئة مطابقة."""
    with db_session() as conn:
        slot = conn.execute(
            "SELECT id FROM ad_slots WHERE slug = ?", (slot_slug,)
        ).fetchone()
        if slot is None:
            raise AdError("الفتحة غير موجودة.", 400)
        query = (
            """SELECT id, campaign_type, advertiser_name, creative_url,
                      target_url, profile_id
               FROM ad_campaigns
               WHERE slot_id = ? AND status = 'active'
                 AND (starts_at IS NULL OR starts_at <= datetime('now'))
                 AND (ends_at IS NULL OR ends_at >= datetime('now'))
                 AND (target_category_type IS NULL OR ? = target_category_type
                      AND ? = target_category_id)"""
        )
        params = [slot["id"]]
        if category_type is not None:
            params.extend([category_type, category_id])
        else:
            # دون سياق فئة: لا تُعرض المستهدفة إلا العامة
            params.extend([None, None])
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            query += " AND " + cond
            params.extend(vals)
        # تفصيلية: المستهدفة المطابقة أولًا ثم العامة ثم الأحدث (id)
        query += (
            " ORDER BY CASE WHEN target_category_type IS NULL THEN 1 "
            "ELSE 0 END, id LIMIT 1"
        )
        row = conn.execute(query, params).fetchone()
        if row is None:
            return None
        return {
            "campaign_id": row["id"],
            "type": row["campaign_type"],
            "advertiser_name": row["advertiser_name"],
            "creative_url": row["creative_url"],
            "target_url": row["target_url"],
            "profile_id": row["profile_id"],
            "sponsored": row["campaign_type"] != "general",
        }


def log_event(campaign_id: int, event_type: str, user_id=None) -> int:
    """يسجّل انطباعًا أو نقرة لحملة موجودة (مستخدم اختياري — قد يكون مجهولًا)."""
    if event_type not in ("impression", "click"):
        raise AdError("نوع الحدث يجب أن يكون impression أو click.", 400)
    with db_session() as conn:
        campaign_q = "SELECT 1 FROM ad_campaigns WHERE id = ?"
        campaign_params = [campaign_id]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            campaign_q += " AND " + cond
            campaign_params.extend(vals)
        campaign = conn.execute(campaign_q, campaign_params).fetchone()
        if campaign is None:
            raise AdError("الحملة غير موجودة.", 404)
        conn.execute(
            "INSERT INTO ad_events (campaign_id, user_id, event_type, tenant_id) "
            "VALUES (?, ?, ?, ?)",
            (campaign_id, user_id, event_type, tenant_scope.insert_tenant_id()),
        )
    return campaign_id


# ---------------------------------------------------------------------------
# الإدارة (تُستدعى من مسارات admin — دور admin)
# ---------------------------------------------------------------------------

def list_slots():
    # عدّ الحملات النشطة ضمن مستأجر الطلب (عزل D-036): ad_slots عام بلا
    # tenant_id، فتُقيَّد الحملات مباشرة بمستأجر الطلب الحالي.
    count_sub = (
        "(SELECT COUNT(*) FROM ad_campaigns c "
        " WHERE c.slot_id = s.id AND c.status = 'active')"
    )
    params = []
    c_cond, c_vals = tenant_scope.tenant_eq("c")
    if c_cond:
        count_sub = (
            f"(SELECT COUNT(*) FROM ad_campaigns c "
            f" WHERE c.slot_id = s.id AND c.status = 'active' AND {c_cond})"
        )
        params = list(c_vals)
    with db_session() as conn:
        rows = conn.execute(
            f"""SELECT s.id, s.slug, s.name, {count_sub} AS active_campaigns
                FROM ad_slots s ORDER BY s.id""",
            params,
        ).fetchall()
        return [dict(r) for r in rows]


def _campaign_stats(conn, campaign_id: int) -> tuple:
    def _count(event: str) -> int:
        query = "SELECT COUNT(*) AS c FROM ad_events " \
                "WHERE campaign_id = ? AND event_type = ?"
        params = [campaign_id, event]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            query += " AND " + cond
            params.extend(vals)
        return conn.execute(query, params).fetchone()["c"]

    return _count("impression"), _count("click")


def list_campaigns_admin():
    # الملف المهني مرتبط بحملة في مستأجرها نفسه (عزل D-036)
    p_scope = " AND p.tenant_id IS c.tenant_id" if tenant_scope.active() else ""
    query = (
        f"""SELECT c.*, s.name AS slot_name,
                   p.profession_type AS profile_profession,
                   u.full_name AS profile_name
            FROM ad_campaigns c
            JOIN ad_slots s ON s.id = c.slot_id
            LEFT JOIN professional_profiles p ON p.id = c.profile_id{p_scope}
            LEFT JOIN users u ON u.id = p.user_id
            ORDER BY c.id DESC"""
    )
    params = []
    cond, vals = tenant_scope.tenant_eq("c")
    if cond:
        query = (
            f"""SELECT c.*, s.name AS slot_name,
                       p.profession_type AS profile_profession,
                       u.full_name AS profile_name
                FROM ad_campaigns c
                JOIN ad_slots s ON s.id = c.slot_id
                LEFT JOIN professional_profiles p ON p.id = c.profile_id{p_scope}
                LEFT JOIN users u ON u.id = p.user_id
                WHERE {cond}
                ORDER BY c.id DESC"""
        )
        params = list(vals)
    with db_session() as conn:
        rows = conn.execute(query, params).fetchall()
        campaigns = []
        for row in rows:
            item = dict(row)
            impressions, clicks = _campaign_stats(conn, row["id"])
            item["impressions"] = impressions
            item["clicks"] = clicks
            item["ctr"] = round(clicks / impressions, 4) if impressions else 0.0
            campaigns.append(item)
        return campaigns


def create_campaign(admin_id: int, data: dict) -> int:
    try:
        slot_id = int(data.get("slot_id"))
    except (TypeError, ValueError):
        raise AdError("slot_id يجب أن يكون رقمًا.", 400)
    campaign_type = (data.get("campaign_type") or "general").strip()
    if campaign_type not in CAMPAIGN_TYPES:
        raise AdError(
            "campaign_type يجب أن يكون general أو sponsored أو "
            "professional_promotion.",
            400,
        )
    advertiser_name = (data.get("advertiser_name") or "").strip()
    if not advertiser_name:
        raise AdError("advertiser_name مطلوب.", 400)
    creative_url = _validate_url(data.get("creative_url"), "creative_url")
    target_url = _validate_url(data.get("target_url"), "target_url")
    starts_at, ends_at = _validate_dates(data)
    status = (data.get("status") or "active").strip()
    if status not in CAMPAIGN_STATUSES:
        raise AdError("status يجب أن يكون active أو paused أو ended.", 400)
    profile_id = None
    if campaign_type == "professional_promotion":
        try:
            profile_id = int(data.get("profile_id"))
        except (TypeError, ValueError):
            raise AdError("profile_id مطلوب لنوع professional_promotion.", 400)
    with db_session() as conn:
        if not _slot_exists(conn, slot_id):
            raise AdError("الفتحة غير موجودة.", 400)
        if campaign_type == "professional_promotion":
            _check_profile(conn, profile_id)
        target_type, target_id = _parse_target(conn, data)
        cur = conn.execute(
            """INSERT INTO ad_campaigns (slot_id, campaign_type,
               advertiser_name, creative_url, target_url, profile_id,
               starts_at, ends_at, status, target_category_type,
               target_category_id, tenant_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (slot_id, campaign_type, advertiser_name, creative_url,
             target_url, profile_id, starts_at, ends_at, status,
             target_type, target_id, tenant_scope.insert_tenant_id()),
        )
        campaign_id = cur.lastrowid
        _log_admin_action(
            conn, admin_id, "ads.create", "ad_campaign", campaign_id,
            f"type={campaign_type}",
        )
    return campaign_id


def update_campaign(admin_id: int, campaign_id: int, data: dict) -> int:
    with db_session() as conn:
        sel_q = "SELECT starts_at, ends_at FROM ad_campaigns WHERE id = ?"
        sel_params = [campaign_id]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            sel_q += " AND " + cond
            sel_params.extend(vals)
        row = conn.execute(sel_q, sel_params).fetchone()
        if row is None:
            raise AdError("الحملة غير موجودة.", 404)
        updates = {}
        if "slot_id" in data and data.get("slot_id") not in (None, ""):
            try:
                slot_id = int(data["slot_id"])
            except (TypeError, ValueError):
                raise AdError("slot_id يجب أن يكون رقمًا.", 400)
            if not _slot_exists(conn, slot_id):
                raise AdError("الفتحة غير موجودة.", 400)
            updates["slot_id"] = slot_id
        if "campaign_type" in data:
            campaign_type = (data.get("campaign_type") or "").strip()
            if campaign_type not in CAMPAIGN_TYPES:
                raise AdError("campaign_type غير صالح.", 400)
            updates["campaign_type"] = campaign_type
        if "advertiser_name" in data:
            name = (data.get("advertiser_name") or "").strip()
            if not name:
                raise AdError("advertiser_name مطلوب.", 400)
            updates["advertiser_name"] = name
        if "creative_url" in data:
            updates["creative_url"] = _validate_url(
                data.get("creative_url"), "creative_url"
            )
        if "target_url" in data:
            updates["target_url"] = _validate_url(
                data.get("target_url"), "target_url"
            )
        if "status" in data:
            status = (data.get("status") or "").strip()
            if status not in CAMPAIGN_STATUSES:
                raise AdError("status غير صالح.", 400)
            updates["status"] = status
        if "starts_at" in data or "ends_at" in data:
            new_starts = _normalize_dt(data.get("starts_at")) \
                if "starts_at" in data else None
            new_ends = _normalize_dt(data.get("ends_at")) \
                if "ends_at" in data else None
            current_starts = new_starts if new_starts is not None \
                else row["starts_at"]
            current_ends = new_ends if new_ends is not None \
                else row["ends_at"]
            if current_starts and current_ends and current_ends < current_starts:
                raise AdError("ends_at يجب أن لا يسبق starts_at.", 400)
            if "starts_at" in data:
                updates["starts_at"] = new_starts
            if "ends_at" in data:
                updates["ends_at"] = new_ends
        if "profile_id" in data:
            pid = data.get("profile_id")
            if pid in (None, ""):
                updates["profile_id"] = None
            else:
                try:
                    profile_id = int(pid)
                except (TypeError, ValueError):
                    raise AdError("profile_id يجب أن يكون رقمًا.", 400)
                _check_profile(conn, profile_id)
                updates["profile_id"] = profile_id
        if "target_category_type" in data or "target_category_id" in data:
            target_type, target_id = _parse_target(conn, data)
            updates["target_category_type"] = target_type
            updates["target_category_id"] = target_id
        if not updates:
            raise AdError("لا توجد حقول للتحديث.", 400)
        sets = ", ".join(f"{k} = ?" for k in updates)
        upd_q = (
            f"UPDATE ad_campaigns SET {sets}, "
            "updated_at = datetime('now') WHERE id = ?"
        )
        upd_params = list(updates.values()) + [campaign_id]
        if cond:
            upd_q += " AND " + cond
            upd_params.extend(vals)
        conn.execute(upd_q, upd_params)
        _log_admin_action(
            conn, admin_id, "ads.update", "ad_campaign", campaign_id,
        )
    return campaign_id


def delete_campaign(admin_id: int, campaign_id: int) -> int:
    """حذف فعلي مع CASCADE على ad_events (أحداث تحليلات — قرار D-027)."""
    with db_session() as conn:
        sel_q = "SELECT id FROM ad_campaigns WHERE id = ?"
        sel_params = [campaign_id]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            sel_q += " AND " + cond
            sel_params.extend(vals)
        row = conn.execute(sel_q, sel_params).fetchone()
        if row is None:
            raise AdError("الحملة غير موجودة.", 404)
        del_q = "DELETE FROM ad_campaigns WHERE id = ?"
        del_params = [campaign_id]
        if cond:
            del_q += " AND " + cond
            del_params.extend(vals)
        conn.execute(del_q, del_params)
        _log_admin_action(
            conn, admin_id, "ads.delete", "ad_campaign", campaign_id,
        )
    return campaign_id


def set_campaign_status_bulk(admin_id: int, campaign_ids, status: str) -> dict:
    """تغيير حالة جماعي للحملات (إيقاف/استئناف/إنهاء) — المرحلة 15 (D-033).

    معاملة واحدة: كل حملة تُحدَّث حالتها مع تدقيق ads.update؛ حملة غير
    موجودة تُسجَّل فشلًا جزئيًا دون إيقاف الباقي. state صالح فقط
    (active|paused|ended) — يُرفض الطلب كله خلاف ذلك."""
    if status not in CAMPAIGN_STATUSES:
        raise AdError("status يجب أن يكون active أو paused أو ended.", 400)
    ids = parse_bulk_ids(campaign_ids, "campaign_ids")
    with db_session() as conn:
        results = []
        cond, vals = tenant_scope.tenant_eq()
        for campaign_id in ids:
            sel_q = "SELECT 1 FROM ad_campaigns WHERE id = ?"
            sel_params = [campaign_id]
            if cond:
                sel_q += " AND " + cond
                sel_params.extend(vals)
            row = conn.execute(sel_q, sel_params).fetchone()
            if row is None:
                results.append(
                    {"id": campaign_id, "status": "error",
                     "message": "الحملة غير موجودة."}
                )
                continue
            upd_q = (
                "UPDATE ad_campaigns SET status = ?, "
                "updated_at = datetime('now') WHERE id = ?"
            )
            upd_params = [status, campaign_id]
            if cond:
                upd_q += " AND " + cond
                upd_params.extend(vals)
            conn.execute(upd_q, upd_params)
            _log_admin_action(
                conn, admin_id, "ads.update", "ad_campaign", campaign_id,
                f"status={status}",
            )
            results.append(
                {"id": campaign_id, "status": "ok",
                 "message": "تم تحديث حالة الحملة."}
            )
    return bulk_summary(f"ads.bulk_status.{status}", results)
