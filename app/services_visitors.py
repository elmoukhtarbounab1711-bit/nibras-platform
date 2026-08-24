"""
خدمات تتبع الزوار (Visitor Analytics) — متقدمة ودقيقة.

تتبع كل طلب واجهة عامة (API) ويحفظ:
- مسار الطلب (path)
- عنوان IP (مشفر)
- User-Agent
- معرّف المستخدم (إن كان مسجلاً)
- وقت الطلب
- الإشارة المرجعية (referrer)
- الدولة (من header country أو geoip مبسّط)

تجمع الإحصائيات:
- عدد الزوار الكلي / اليوم / هذا الأسبوع
- الزوار الفريدون (IP)
- أكثر الصفحات زيارة
- مصادر الزيارات
- التوزيع الزمني (ساعي / يومي)
- الأجهزة والمتصفحات
"""
import hashlib
import logging
import time
import threading
from datetime import datetime, timedelta

from . import config
from .database import db_session

_log = logging.getLogger("nibras.visitors")

# جدول الانتظار للregistrations الدفعية
_queue: list[dict] = []
_queue_lock = threading.Lock()
_flush_interval = 5  # ثوانٍ

# مسارات تُستثنى من التتبع (API internals, static, health)
_EXCLUDED_PREFIXES = (
    "/api/health", "/api/ready", "/assets/", "/vendor/",
    "/sw.js", "/favicon.ico", "/manifest.json",
)
_EXCLUDED_PATHS = frozenset({
    "/api/admin/visitors/track",  # لا نتتبع طلبات التتبع نفسها
})


def _hash_ip(ip: str) -> str:
    """تشفير IP بـ SHA-256 للخصوصية (لا نخزّن IPs حقيقية)."""
    salt = config.SECRET_KEY[:16] if hasattr(config, "SECRET_KEY") else "nibras"
    return hashlib.sha256(f"{salt}{ip}".encode()).hexdigest()[:32]


def _parse_user_agent(ua: str) -> dict:
    """تحليل مبسّط لـ User-Agent لاستخراج المتصفح والجهاز."""
    ua_lower = (ua or "").lower()

    # المتصفح
    browser = "unknown"
    if "edg/" in ua_lower or "edge/" in ua_lower:
        browser = "Edge"
    elif "opr/" in ua_lower or "opera" in ua_lower:
        browser = "Opera"
    elif "chrome" in ua_lower and "safari" in ua_lower:
        browser = "Chrome"
    elif "firefox" in ua_lower:
        browser = "Firefox"
    elif "safari" in ua_lower:
        browser = "Safari"
    elif "curl" in ua_lower:
        browser = "curl"

    # الجهاز
    device = "desktop"
    if "mobile" in ua_lower or "android" in ua_lower or "iphone" in ua_lower:
        device = "mobile"
    elif "tablet" in ua_lower or "ipad" in ua_lower:
        device = "tablet"

    # نظام التشغيل
    os_name = "unknown"
    if "windows" in ua_lower:
        os_name = "Windows"
    elif "mac os" in ua_lower or "macintosh" in ua_lower:
        os_name = "macOS"
    elif "linux" in ua_lower and "android" not in ua_lower:
        os_name = "Linux"
    elif "android" in ua_lower:
        os_name = "Android"
    elif "iphone" in ua_lower or "ipad" in ua_lower:
        os_name = "iOS"

    return {"browser": browser, "device": device, "os": os_name}


def _extract_referrer(ref: str) -> str:
    """استخراج المصدر من Referrer URL."""
    if not ref:
        return "direct"
    ref_lower = ref.lower()
    if "google" in ref_lower:
        return "Google"
    if "facebook" in ref_lower or "fb.com" in ref_lower:
        return "Facebook"
    if "twitter" in ref_lower or "x.com" in ref_lower:
        return "Twitter/X"
    if "instagram" in ref_lower:
        return "Instagram"
    if "linkedin" in ref_lower:
        return "LinkedIn"
    if "youtube" in ref_lower:
        return "YouTube"
    if "t.me" in ref_lower or "telegram" in ref_lower:
        return "Telegram"
    if "whatsapp" in ref_lower:
        return "WhatsApp"
    # استخراج النطاق
    try:
        from urllib.parse import urlparse
        parsed = urlparse(ref)
        domain = parsed.netloc or parsed.path
        return domain[:50]
    except Exception:
        return "other"


def should_track(path: str, method: str) -> bool:
    """هل يجب تتبع هذا الطلب؟"""
    if method not in ("GET", "POST", "PUT", "DELETE"):
        return False
    if any(path.startswith(p) for p in _EXCLUDED_PREFIXES):
        return False
    if path in _EXCLUDED_PATHS:
        return False
    if path.startswith("/api/"):
        return True
    # تتبع تحميل الصفحة الرئيسية والـ SPA
    if path in ("/", "/admin", "/admin/"):
        return True
    return False


def track_request(path: str, ip: str, user_agent: str, referrer: str,
                  user_id: int | None = None, method: str = "GET",
                  status_code: int = 200, duration_ms: float = 0):
    """تسجيل طلب في جدول الانتظار (غير متزامن)."""
    if not should_track(path, method):
        return

    entry = {
        "path": path[:200],
        "ip_hash": _hash_ip(ip or "unknown"),
        "user_agent": (user_agent or "")[:500],
        "referrer": (referrer or "")[:500],
        "user_id": user_id,
        "method": method,
        "status_code": status_code,
        "duration_ms": int(duration_ms),
        "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    }
    entry.update(_parse_user_agent(user_agent))
    entry["referrer_source"] = _extract_referrer(referrer)

    with _queue_lock:
        _queue.append(entry)


def _flush_queue():
    """تفريغ جدول الانتظار إلى قاعدة البيانات."""
    with _queue_lock:
        if not _queue:
            return
        batch = list(_queue)
        _queue.clear()

    try:
        with db_session() as conn:
            conn.executemany(
                """INSERT INTO page_visits
                   (path, ip_hash, user_agent, referrer, referrer_source,
                    user_id, method, status_code, duration_ms,
                    browser, device, os, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [(e["path"], e["ip_hash"], e["user_agent"], e["referrer"],
                  e["referrer_source"], e["user_id"], e["method"],
                  e["status_code"], e["duration_ms"],
                  e["browser"], e["device"], e["os"], e["created_at"])
                 for e in batch],
            )
        _log.debug("Flushed %d visitor records", len(batch))
    except Exception:
        _log.exception("Failed to flush visitor records")


# مؤقت تفريغ دوري
_flush_timer = None


def _start_flush_timer():
    global _flush_timer
    if _flush_timer is not None:
        return
    import atexit

    def _periodic():
        _flush_queue()
        t = threading.Timer(_flush_interval, _periodic)
        t.daemon = True
        t.start()

    _periodic()
    atexit.register(_flush_queue)


def ensure_tracking_table():
    """إنشاء جدول page_visits إن لم يكن موجوداً."""
    with db_session() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS page_visits (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                path            TEXT NOT NULL,
                ip_hash         TEXT NOT NULL,
                user_agent      TEXT DEFAULT '',
                referrer        TEXT DEFAULT '',
                referrer_source TEXT DEFAULT 'direct',
                user_id         INTEGER REFERENCES users(id) ON DELETE SET NULL,
                method          TEXT NOT NULL DEFAULT 'GET',
                status_code     INTEGER NOT NULL DEFAULT 200,
                duration_ms     INTEGER NOT NULL DEFAULT 0,
                browser         TEXT DEFAULT 'unknown',
                device          TEXT DEFAULT 'desktop',
                os              TEXT DEFAULT 'unknown',
                created_at      TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_page_visits_created
            ON page_visits(created_at)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_page_visits_path
            ON page_visits(path)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_page_visits_ip
            ON page_visits(ip_hash, created_at)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_page_visits_user
            ON page_visits(user_id)
        """)
    _start_flush_timer()


# ──────────────────────────────────────────────────────
#  دوال الاستعلام (للواجهة الإدارية)
# ──────────────────────────────────────────────────────

def _time_range(where: str, params: list, days: int = 30) -> tuple[str, list]:
    """إضافة شرط النطاق الزمني."""
    where_parts = [where] if where else []
    where_parts.append("created_at >= date('now', ?)")
    params.append(f"-{days} days")
    return " AND ".join(where_parts), params


def summary_stats(days: int = 30) -> dict:
    """إحصائيات عامة للزوار."""
    with db_session() as conn:
        where, params = _time_range("", [], days)

        # العدد الكلي
        total = conn.execute(
            f"SELECT COUNT(*) AS c FROM page_visits WHERE {where}", params
        ).fetchone()["c"]

        # اليوم
        today = conn.execute(
            "SELECT COUNT(*) AS c FROM page_visits WHERE date(created_at) = date('now')"
        ).fetchone()["c"]

        # هذا الأسبوع
        week = conn.execute(
            "SELECT COUNT(*) AS c FROM page_visits WHERE created_at >= date('now', '-7 days')"
        ).fetchone()["c"]

        # الزوار الفريدون (IP فريد)
        unique_ips = conn.execute(
            f"SELECT COUNT(DISTINCT ip_hash) AS c FROM page_visits WHERE {where}", params
        ).fetchone()["c"]

        # المستخدمون المسجلون
        unique_users = conn.execute(
            f"SELECT COUNT(DISTINCT user_id) AS c FROM page_visits WHERE {where} AND user_id IS NOT NULL",
            params,
        ).fetchone()["c"]

        # متوسط مدة التحميل
        avg_duration = conn.execute(
            f"SELECT AVG(duration_ms) AS avg_ms FROM page_visits WHERE {where}", params
        ).fetchone()["avg_ms"]

        # إجمالي API calls vs page loads
        api_calls = conn.execute(
            f"SELECT COUNT(*) AS c FROM page_visits WHERE {where} AND path LIKE '/api/%'", params
        ).fetchone()["c"]

        return {
            "total_visits": total,
            "today_visits": today,
            "week_visits": week,
            "unique_visitors": unique_ips,
            "unique_users": unique_users,
            "avg_duration_ms": round(avg_duration or 0, 1),
            "api_calls": api_calls,
            "page_loads": total - api_calls,
        }


def daily_trend(days: int = 30) -> list[dict]:
    """الاتجاه اليومي للزيارات والزوار الفريدين."""
    with db_session() as conn:
        rows = conn.execute(
            """SELECT date(created_at) AS d,
                      COUNT(*) AS visits,
                      COUNT(DISTINCT ip_hash) AS unique_visitors
               FROM page_visits
               WHERE created_at >= date('now', ?)
               GROUP BY d ORDER BY d""",
            (f"-{days} days",),
        ).fetchall()
        return [{"date": r["d"], "visits": r["visits"],
                 "unique_visitors": r["unique_visitors"]} for r in rows]


def hourly_distribution(days: int = 7) -> list[dict]:
    """التوزيع الساعي للزيارات (آخر 7 أيام)."""
    with db_session() as conn:
        rows = conn.execute(
            """SELECT CAST(strftime('%H', created_at) AS INTEGER) AS hour,
                      COUNT(*) AS visits
               FROM page_visits
               WHERE created_at >= date('now', ?)
               GROUP BY hour ORDER BY hour""",
            (f"-{days} days",),
        ).fetchall()
        hours = {r["hour"]: r["visits"] for r in rows}
        return [{"hour": h, "visits": hours.get(h, 0)} for h in range(24)]


def top_pages(limit: int = 20, days: int = 30) -> list[dict]:
    """أكثر الصفحات زيارة."""
    with db_session() as conn:
        where, params = _time_range("", [], days)
        rows = conn.execute(
            f"""SELECT path, COUNT(*) AS visits,
                       COUNT(DISTINCT ip_hash) AS unique_visitors
                FROM page_visits
                WHERE {where}
                GROUP BY path
                ORDER BY visits DESC
                LIMIT ?""",
            (*params, limit),
        ).fetchall()
        return [{"path": r["path"], "visits": r["visits"],
                 "unique_visitors": r["unique_visitors"]} for r in rows]


def referrer_sources(days: int = 30) -> list[dict]:
    """مصادر الزيارات."""
    with db_session() as conn:
        where, params = _time_range("", [], days)
        rows = conn.execute(
            f"""SELECT referrer_source, COUNT(*) AS visits,
                       COUNT(DISTINCT ip_hash) AS unique_visitors
                FROM page_visits
                WHERE {where}
                GROUP BY referrer_source
                ORDER BY visits DESC
                LIMIT 15""",
            params,
        ).fetchall()
        return [{"source": r["referrer_source"], "visits": r["visits"],
                 "unique_visitors": r["unique_visitors"]} for r in rows]


def browser_stats(days: int = 30) -> list[dict]:
    """توزيع المتصفحات."""
    with db_session() as conn:
        where, params = _time_range("", [], days)
        rows = conn.execute(
            f"""SELECT browser, COUNT(*) AS visits
                FROM page_visits
                WHERE {where}
                GROUP BY browser
                ORDER BY visits DESC""",
            params,
        ).fetchall()
        return [{"browser": r["browser"], "visits": r["visits"]} for r in rows]


def device_stats(days: int = 30) -> list[dict]:
    """توزيع الأجهزة."""
    with db_session() as conn:
        where, params = _time_range("", [], days)
        rows = conn.execute(
            f"""SELECT device, COUNT(*) AS visits
                FROM page_visits
                WHERE {where}
                GROUP BY device
                ORDER BY visits DESC""",
            params,
        ).fetchall()
        return [{"device": r["device"], "visits": r["visits"]} for r in rows]


def os_stats(days: int = 30) -> list[dict]:
    """توزيع أنظمة التشغيل."""
    with db_session() as conn:
        where, params = _time_range("", [], days)
        rows = conn.execute(
            f"""SELECT os, COUNT(*) AS visits
                FROM page_visits
                WHERE {where}
                GROUP BY os
                ORDER BY visits DESC""",
            params,
        ).fetchall()
        return [{"os": r["os"], "visits": r["visits"]} for r in rows]


def live_visitors() -> dict:
    """الزوار النشطون الآن (آخر 5 دقائق)."""
    with db_session() as conn:
        active = conn.execute(
            """SELECT COUNT(DISTINCT ip_hash) AS c
               FROM page_visits
               WHERE created_at >= datetime('now', '-5 minutes')"""
        ).fetchone()["c"]
        recent = conn.execute(
            """SELECT path, created_at, browser, device
               FROM page_visits
               WHERE created_at >= datetime('now', '-5 minutes')
               ORDER BY created_at DESC
               LIMIT 20"""
        ).fetchall()
        return {
            "active_now": active,
            "recent": [{"path": r["path"], "time": r["created_at"],
                        "browser": r["browser"], "device": r["device"]}
                       for r in recent],
        }


def full_analytics(days: int = 30) -> dict:
    """تجميع كامل لتحليلات الزوار."""
    return {
        "summary": summary_stats(days),
        "daily_trend": daily_trend(days),
        "hourly_distribution": hourly_distribution(min(days, 7)),
        "top_pages": top_pages(20, days),
        "referrers": referrer_sources(days),
        "browsers": browser_stats(days),
        "devices": device_stats(days),
        "os": os_stats(days),
        "live": live_visitors(),
    }