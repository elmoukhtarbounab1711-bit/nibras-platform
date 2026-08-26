"""
خدمات نظام الإعلانات (المرحلة 9 — إتمام Roadmap Phase 6، قرار D-027).

نموذج حسب الوثيقة 15 وقاعدة البيانات §11: فتحات ثابتة تُبذر، حملات بثلاثة
أنواع (general/sponsored/professional_promotion) واستهداف v1 (فتحة + نطاق
تواريخ فقط)، وأحداث انطباع/نقرة للتتبع (§6). الخدمة تعيد الحملة النشطة
لفتحة أو None، وتتابع الأحداث، وتُدير الحملات إداريًا (مع إحصائيات
impressions/clicks/ctr). الإدارة تُسجَّل في admin_audit_log (Security §8)
بنمط ads.*. الفصل البصري للإعلان عن المحتوى القانوني (وثيقة 15 §7)
مسؤولية الواجهة؛ هنا يُكشف نوع الحملة (sponsored) في استجابة الخدمة.

الأمان §7 (النظام الإعلاني الجديد): مزوّدون مُعتمدون فقط، Domain allowlist،
تفعيل/تعطيل عالمي، لا إعلانات للمشتركين المميزين، لا popunders/interstitials.
"""
import json
import logging
import re
from urllib.parse import urlparse

from . import tenant_scope
from .database import db_session
from .services_admin import _log_admin_action, bulk_summary, parse_bulk_ids

logger = logging.getLogger(__name__)

# فتحات الواجهة (وثيقة 15 §2 + توسيع الأمني §7)
SLOT_SEED = (
    ("library_sidebar", "شريط المكتبة الجانبي"),
    ("search_results_top", "أعلى نتائج البحث"),
    ("directory_listing_top", "أعلى قائمة الدليل"),
    ("header", "الرأسية"),
    ("article_top", "أعلى المقال"),
    ("article_middle", "وسط المقال"),
    ("article_bottom", "أسفل المقال"),
    ("sidebar", "الشريط الجانبي"),
    ("search_results", "نتائج البحث"),
    ("mobile", "الجوال"),
)

CAMPAIGN_TYPES = ("general", "sponsored", "professional_promotion")
CAMPAIGN_STATUSES = ("active", "paused", "ended")

# أنواع الإعلانات المدعومة
AD_FORMATS = ("banner", "native", "display", "in-article")
AD_BANNER_SIZES = (
    "728x90", "320x50", "300x250", "160x600",
    "320x100", "468x60", "970x250", "fluid",
)

# الاستهداف الفئوي (المرحلة 19 — قرار D-037): أنواع الفئات المستهدفة
TARGET_CATEGORY_TYPES = ("library", "marketplace", "jurisprudence")

# ═══════════════════════════════════════════════════════════════════════
# الأمان §7: Domain allowlist — مزوّدون مُعتمدون فقط
# ═══════════════════════════════════════════════════════════════════════
APPROVED_AD_DOMAINS = {
    "profitableratecpmnetwork.com",
    "highrevenueformat.com",
    "googleadservices.com",
    "googlesyndication.com",
    "doubleclick.net",
    "adsense.google.com",
    "adsterra.com",
    "monetag.com",
    "propellerads.com",
    "media.net",
    "amazon-adsystem.com",
    "adroll.com",
    "outbrain.com",
    "taboola.com",
    "criteo.com",
    "pubmatic.com",
    "openx.com",
    "spotxchange.com",
    "indexww.com",
}

# نمط إعلانات محظورة (Security §7)
BLOCKED_AD_PATTERNS = (
    "popunder", "pop-under", "smartlink", "interstitial",
    "forced-click", "malvertising", "crypto-mining",
)

# نمط محتوى للبالغين — ممنوع تمامًا (Security §7)
ADULT_CONTENT_PATTERNS = (
    "porn", "xxx", "adult", "nude", "nsfw", "erotic",
    "sex-video", "cam-girl", "hookup", "dating-adult",
)


class AdError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _validate_script_security(script_url: str = "", script_tag: str = "") -> None:
    """يتحقق من أمن السكريبت الإعلاني (Security §7).

    - لا scripts تحتوي على أنماط JS خطيرة (eval, document.write, outerHTML...)
    - domains ضمن القائمة البيضاء فقط — يُرفض النطاق غير المعتمد
    - لا popunders, interstitials, أو محتوى للبالغين
    """
    script_url = script_url or ""
    script_tag = script_tag or ""
    combined = (script_url + " " + script_tag).lower()
    # حظر أنماط محظورة
    for pattern in BLOCKED_AD_PATTERNS:
        if pattern in combined:
            raise AdError(
                f"نمط الإعلان محظور: {pattern}. "
                "الإعلانات المنبثقة والأكراهية غير مسموحة.", 400
            )
    # حظر محتوى للبالغين
    for pattern in ADULT_CONTENT_PATTERNS:
        if pattern in combined:
            raise AdError(
                "الإعلانات المحتوية على محتوى للبالغين محظورة.", 400
            )
    # التحقق من النطاق — يُرفض أي نطاق غير معتمد
    if script_url:
        _validate_url_domain(script_url)
    if script_tag:
        _validate_script_tag_domains(script_tag)
    # حظر JavaScript خطير
    dangerous_patterns = (
        "document.write", "eval(", "innerhtml",
        "window.location", "document.cookie",
        "outerhtml", "insertadjacenthtml",
    )
    for dp in dangerous_patterns:
        if dp in combined:
            raise AdError(
                f"الكود يحتوي على نمط غير آمن: {dp}", 400
            )
    # حظر setTimeout/setInterval مع سلسلة نصية (ليس دالة)
    _block_string_timers(combined)


def _is_approved_domain(hostname: str) -> bool:
    """يتحقق من أن النطاق معتمد بشكل آمن (لا يقبل تضليل adsterra.com.evil.com)."""
    h = hostname.lower().strip().split(":")[0]
    base_domain = ".".join(h.split(".")[-2:])
    if base_domain in APPROVED_AD_DOMAINS:
        return True
    for approved in APPROVED_AD_DOMAINS:
        if h.endswith("." + approved):
            return True
    return False


def _validate_url_domain(url: str):
    """يتحقق من أن رابط السكريبت على نطاق معتمد."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise AdError(f"رابط السكريبت يجب أن يكون http/https: {url}", 400)
    if not parsed.netloc:
        raise AdError(f"رابط السكريبت غير صالح: {url}", 400)
    domain = parsed.netloc.split(":")[0]
    if not _is_approved_domain(domain):
        raise AdError(
            f"النطاق غير معتمد: {domain}. "
            "يجب أن يكون ضمن القائمة البيضاء للمزوّدين المعتمدين.", 400
        )


def _validate_script_tag_domains(script_tag: str):
    """يتحقق من أن جميع نطاقات script src في الكود معتمدة."""
    src_pattern = re.compile(r'<script\b[^>]*\bsrc=["\']([^"\']+)["\']', re.IGNORECASE)
    for match in src_pattern.finditer(script_tag):
        src_url = match.group(1)
        if src_url.startswith("//"):
            src_url = "https:" + src_url
        try:
            parsed = urlparse(src_url)
            if parsed.netloc:
                domain = parsed.netloc.split(":")[0]
                if not _is_approved_domain(domain):
                    raise AdError(
                        f"نطاق السكريبت غير معتمد في script_tag: {domain}", 400
                    )
        except AdError:
            raise
        except Exception:
            raise AdError(
                f"رابط غير صالح في script_tag: {src_url}", 400
            )


def _block_string_timers(combined: str):
    """يمنع setTimeout/setInterval مع سلسلة نصية (ليس دالة — متجه XSS)."""
    timer_pattern = re.compile(
        r'(?:setTimeout|setInterval)\s*\(\s*["\']', re.IGNORECASE
    )
    if timer_pattern.search(combined):
        raise AdError(
            "setTimeout/setInterval مع سلسلة نصية غير مسموح (مية أمان).", 400
        )


def ensure_defaults():
    """بذر فتحات الإعلانات والملفات الافتراضية (idempotent)."""
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
        # الإعدادات العامة الافتراضية
        defaults = {
            "ads_enabled": "1",
            "ads_no_premium": "1",
            "ads_lazy_load": "1",
            "ads_domain_allowlist": json.dumps(sorted(APPROVED_AD_DOMAINS)),
        }
        for key, val in defaults.items():
            exists = conn.execute(
                "SELECT 1 FROM ad_settings WHERE key = ?", (key,)
            ).fetchone()
            if exists is None:
                conn.execute(
                    "INSERT INTO ad_settings (key, value) VALUES (?, ?)",
                    (key, val),
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


_TARGET_TABLE = {
    "library": "categories",
    "marketplace": "marketplace_categories",
    "jurisprudence": "jurisprudence_categories",
}


def _parse_target(conn, data: dict) -> tuple:
    dtype = (data.get("target_category_type") or "").strip() or None
    if "target_category_type" in data and not dtype:
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
# الإعدادات العامة
# ---------------------------------------------------------------------------

def get_settings() -> dict:
    """يعيد جميع الإعدادات العامة كقاموس."""
    with db_session() as conn:
        rows = conn.execute("SELECT key, value FROM ad_settings").fetchall()
        return {r["key"]: r["value"] for r in rows}


def set_setting(key: str, value: str):
    """يحدّث إعدادًا عامًا."""
    allowed_keys = {
        "ads_enabled", "ads_no_premium", "ads_lazy_load",
        "ads_domain_allowlist",
    }
    if key not in allowed_keys:
        raise AdError(f"مفتاح الإعداد غير معروف: {key}", 400)
    with db_session() as conn:
        conn.execute(
            "INSERT INTO ad_settings (key, value, updated_at) "
            "VALUES (?, ?, datetime('now')) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value, "
            "updated_at = datetime('now')",
            (key, value),
        )


def is_ads_enabled() -> bool:
    """يتحقق مما إذا كانت الإعلانات مفعّلة عالميًا."""
    settings = get_settings()
    return settings.get("ads_enabled", "1").lower() in ("1", "true")


def should_show_ads(is_premium: bool = False) -> bool:
    """يقرر ما إذا يجب عرض الإعلانات للمستخدم.

    لا تُعرض الإعلانات إذا:
    - الإعلانات معطّلة عالميًا
    - المستخدم مشترك مميز (premium) والإعداد يمنع ذلك
    """
    if not is_ads_enabled():
        return False
    settings = get_settings()
    if is_premium and settings.get("ads_no_premium", "1").lower() in ("1", "true"):
        return False
    return True


# ---------------------------------------------------------------------------
# إدارة المزوّدين (Provider Management — Security §7)
# ---------------------------------------------------------------------------

def list_providers():
    """يعيد قائمة جميع مزوّدي الإعلانات مع إحصائياتهم."""
    with db_session() as conn:
        rows = conn.execute(
            "SELECT * FROM ad_providers ORDER BY id DESC"
        ).fetchall()
        providers = []
        for r in rows:
            item = dict(r)
            # عدد الفتحات المرتبطة
            slot_count = conn.execute(
                "SELECT COUNT(*) FROM ad_slot_providers WHERE provider_id = ?",
                (r["id"],),
            ).fetchone()[0]
            item["slot_count"] = slot_count
            providers.append(item)
        return providers


def create_provider(admin_id: int, data: dict) -> int:
    """يُنشئ مزوّد إعلانات جديدًا مع التحقق الأمني."""
    name = (data.get("name") or "").strip()
    if not name:
        raise AdError("اسم المزوّد مطلوب.", 400)
    slug = (data.get("slug") or "").strip()
    if not slug:
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    ad_format = (data.get("ad_format") or "banner").strip()
    if ad_format not in AD_FORMATS:
        raise AdError(
            f"نوع الإعلان غير مدعوم. يجب أن يكون: {', '.join(AD_FORMATS)}",
            400,
        )
    script_url = (data.get("script_url") or "").strip()
    script_tag = (data.get("script_tag") or "").strip()
    if not script_url and not script_tag:
        raise AdError("يجب تحديد script_url أو script_tag.", 400)
    # التحقق الأمني من السكريبت
    _validate_script_security(script_url, script_tag)

    with db_session() as conn:
        exists = conn.execute(
            "SELECT 1 FROM ad_providers WHERE slug = ?", (slug,)
        ).fetchone()
        if exists:
            raise AdError(f"مزوّد بهذا الـ slug موجود بالفعل: {slug}", 400)
        cur = conn.execute(
            """INSERT INTO ad_providers
            (name, slug, script_url, script_tag, ad_format,
             slot_default, enabled, is_approved, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                name, slug, script_url, script_tag, ad_format,
                data.get("slot_default"),
                1 if data.get("enabled") else 0,
                1 if data.get("is_approved") else 0,
                data.get("notes"),
            ),
        )
        provider_id = cur.lastrowid
        _log_admin_action(
            conn, admin_id, "ads.provider_create", "ad_providers",
            provider_id, f"name={name}",
        )
    return provider_id


def update_provider(admin_id: int, provider_id: int, data: dict) -> int:
    """يحدّث مزوّد إعلانات مع التحقق الأمني."""
    with db_session() as conn:
        row = conn.execute(
            "SELECT id FROM ad_providers WHERE id = ?", (provider_id,)
        ).fetchone()
        if row is None:
            raise AdError("المزوّد غير موجود.", 404)
        updates = {}
        if "name" in data:
            name = (data["name"] or "").strip()
            if not name:
                raise AdError("اسم المزوّد مطلوب.", 400)
            updates["name"] = name
        if "slug" in data:
            slug = (data["slug"] or "").strip()
            if slug:
                exists = conn.execute(
                    "SELECT 1 FROM ad_providers WHERE slug = ? AND id != ?",
                    (slug, provider_id),
                ).fetchone()
                if exists:
                    raise AdError(f"slug مستخدم بالفعل: {slug}", 400)
                updates["slug"] = slug
        if "ad_format" in data:
            fmt = (data["ad_format"] or "").strip()
            if fmt and fmt not in AD_FORMATS:
                raise AdError("نوع الإعلان غير مدعوم.", 400)
            updates["ad_format"] = fmt
        if "script_url" in data:
            updates["script_url"] = (data["script_url"] or "").strip()
        if "script_tag" in data:
            updates["script_tag"] = (data["script_tag"] or "").strip()
        if "slot_default" in data:
            updates["slot_default"] = data["slot_default"]
        if "enabled" in data:
            updates["enabled"] = 1 if data["enabled"] else 0
        if "is_approved" in data:
            updates["is_approved"] = 1 if data["is_approved"] else 0
        if "notes" in data:
            updates["notes"] = data["notes"]
        # التحقق الأمني من السكريبت إذا تغيّر
        if "script_url" in updates or "script_tag" in updates:
            _validate_script_security(
                updates.get("script_url", ""),
                updates.get("script_tag", ""),
            )
        if not updates:
            raise AdError("لا توجد حقول للتحديث.", 400)
        sets = ", ".join(f"{k} = ?" for k in updates)
        conn.execute(
            f"UPDATE ad_providers SET {sets}, "
            "updated_at = datetime('now') WHERE id = ?",
            [*updates.values(), provider_id],
        )
        _log_admin_action(
            conn, admin_id, "ads.provider_update", "ad_providers",
            provider_id,
        )
    return provider_id


def delete_provider(admin_id: int, provider_id: int) -> int:
    """يحذف مزوّد وجميع ربطه بالفتحات."""
    with db_session() as conn:
        row = conn.execute(
            "SELECT id FROM ad_providers WHERE id = ?", (provider_id,)
        ).fetchone()
        if row is None:
            raise AdError("المزوّد غير موجود.", 404)
        conn.execute(
            "DELETE FROM ad_providers WHERE id = ?", (provider_id,)
        )
        _log_admin_action(
            conn, admin_id, "ads.provider_delete", "ad_providers",
            provider_id,
        )
    return provider_id


def set_provider_status_bulk(admin_id: int, provider_ids, enabled: bool) -> dict:
    """تفعيل/تعطيل جماعي للمزوّدين."""
    ids = parse_bulk_ids(provider_ids, "provider_ids")
    with db_session() as conn:
        results = []
        for pid in ids:
            row = conn.execute(
                "SELECT 1 FROM ad_providers WHERE id = ?", (pid,)
            ).fetchone()
            if row is None:
                results.append({"id": pid, "status": "error",
                                "message": "المزوّد غير موجود."})
                continue
            conn.execute(
                "UPDATE ad_providers SET enabled = ?, "
                "updated_at = datetime('now') WHERE id = ?",
                (1 if enabled else 0, pid),
            )
            _log_admin_action(
                conn, admin_id, "ads.provider_update", "ad_providers",
                pid, f"enabled={enabled}",
            )
            results.append({"id": pid, "status": "ok", "message": "تم التحديث."})
    action = "enable" if enabled else "disable"
    return bulk_summary(f"ads.providers.{action}", results)


# ---------------------------------------------------------------------------
# إدارة ربط المزوّد بالفتحة (Slot-Provider linking)
# ---------------------------------------------------------------------------

def link_provider_to_slot(slot_id: int, provider_id: int,
                          slot_config: str = "{}", priority: int = 0) -> int:
    """يربط مزوّدًا بفتحة معينة."""
    with db_session() as conn:
        if not _slot_exists(conn, slot_id):
            raise AdError("الفتحة غير موجودة.", 400)
        row = conn.execute(
            "SELECT 1 FROM ad_providers WHERE id = ?", (provider_id,)
        ).fetchone()
        if row is None:
            raise AdError("المزوّد غير موجود.", 400)
        exists = conn.execute(
            "SELECT 1 FROM ad_slot_providers "
            "WHERE slot_id = ? AND provider_id = ?",
            (slot_id, provider_id),
        ).fetchone()
        if exists:
            raise AdError("المزوّد مرتبط بالفعل بهذه الفتحة.", 400)
        cur = conn.execute(
            """INSERT INTO ad_slot_providers
            (slot_id, provider_id, slot_config, priority)
            VALUES (?, ?, ?, ?)""",
            (slot_id, provider_id, slot_config, priority),
        )
        return cur.lastrowid


def unlink_provider_from_slot(slot_id: int, provider_id: int):
    """يُلغي ربط مزوّد بفتحة."""
    with db_session() as conn:
        conn.execute(
            "DELETE FROM ad_slot_providers "
            "WHERE slot_id = ? AND provider_id = ?",
            (slot_id, provider_id),
        )


def list_slot_providers(slot_id: int):
    """يعيد المزوّدين المرتبطة بفتحة معينة مرتبين بالأولوية."""
    with db_session() as conn:
        rows = conn.execute(
            """SELECT sp.*, p.name AS provider_name, p.slug AS provider_slug,
                      p.ad_format, p.script_url, p.script_tag, p.enabled,
                      p.is_approved
               FROM ad_slot_providers sp
               JOIN ad_providers p ON p.id = sp.provider_id
               WHERE sp.slot_id = ?
               ORDER BY sp.priority DESC, sp.id""",
            (slot_id,),
        ).fetchall()
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# الخدمة العامة — تحميل آمن للإعلانات (Security §7)
# ---------------------------------------------------------------------------

def serve(slot_slug: str, category_type: str | None = None,
          category_id: int | None = None):
    """يعيد الحملة النشطة للفتحة أو None.

    الاستهداف الفئوي: المستهدفة المطابقة أولًا ثم العامة.
    """
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
            params.extend([None, None])
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            query += " AND " + cond
            params.extend(vals)
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


def serve_slot(slot_slug: str) -> list:
    """يعيد جميع المزوّدين النشطين لفتحة (للتحميل البرمجي).

    يُعيد قائمة بسكريبتات المزوّدين النشطة والمُعتمدة للفتحة المطلوبة.
    كل عنصر يحتوي على:
    - provider_id, name, slug, ad_format
    - script_url, script_tag
    - slot_config (حجم الإعلان، الموقع، إلخ)
    """
    with db_session() as conn:
        slot = conn.execute(
            "SELECT id FROM ad_slots WHERE slug = ?", (slot_slug,)
        ).fetchone()
        if slot is None:
            return []
        rows = conn.execute(
            """SELECT sp.slot_config, sp.priority,
                      p.id AS provider_id, p.name, p.slug, p.ad_format,
                      p.script_url, p.script_tag
               FROM ad_slot_providers sp
               JOIN ad_providers p ON p.id = sp.provider_id
               WHERE sp.slot_id = ? AND sp.enabled = 1
                 AND p.enabled = 1 AND p.is_approved = 1
               ORDER BY sp.priority DESC, sp.id""",
            (slot["id"],),
        ).fetchall()
        return [dict(r) for r in rows]


def log_event(campaign_id: int, event_type: str, user_id=None) -> int:
    """يسجّل انطباعًا أو نقرة لحملة موجودة."""
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
