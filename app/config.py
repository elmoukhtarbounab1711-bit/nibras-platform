"""
إعدادات التطبيق عبر متغيرات البيئة.

يُقرأ كل إعداد من بيئة التشغيل ولا يُثبَّت في الكود المصدري، وفق مبدأ
الأمان في وثيقة هندسة نبراس (§10) والوثيقة 12 (Security Architecture §1):
المفتاح الثابت debug=True و CORS الشامل يُستبدلان بإعدادات بيئة صريحة.

القيم الافتراضية هنا آمنة للتطوير المحلي فقط؛ بيئة الإنتاج يجب أن تضبطها صراحة.
"""
import os


def _env_bool(name: str, default: str = "0") -> bool:
    """يقرأ قيمة بيئية كقيمة منطقية (1/true/yes/on = صحيح)."""
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes", "on")


# وضع تصحيح Werkzeug: مُفعَّل محليًا فقط عبر NIBRAS_DEBUG=1
# (يجب أن يبقى مُعطَّلاً في أي نشر غير محلي).
DEBUG = _env_bool("NIBRAS_DEBUG")

# النطاقات المسموح لها بقراءة API (CORS). في الإنتاج تُضبط عبر
# NIBRAS_CORS_ORIGINS بقائمة مفصولة بفواصل للنطاقات الفعلية فقط.
# "null" يُدرج افتراضيًا لأنه أصل المتصفح عند فتح nibras.html محليًا من ملف.
_DEFAULT_CORS = (
    "http://localhost:8000,http://127.0.0.1:8000,"
    "http://localhost:3000,http://127.0.0.1:3000,"
    "http://localhost:5500,http://127.0.0.1:5500,null"
)
CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get("NIBRAS_CORS_ORIGINS", _DEFAULT_CORS).split(",")
    if o.strip()
]

# ---------------------------------------------------------------------------
# المصادقة (المرحلة 1) — وفق وثيقة المصادقة والتفويض والمواصفة التقنية §4
# ---------------------------------------------------------------------------

def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        return default


def _safe_warn(text: str) -> None:
    """طباعة إنذار لا تنهار على وحدات تحكم لا تدعم العربية (مثل cp1252)."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", "backslashreplace").decode("ascii"))


# سر توقيع JWT. يُولَّد عشوائيًا في كل إقلاع عند غياب NIBRAS_JWT_SECRET —
# وهذا آمن للتطوير المحلي فقط (الجلسات تنتهي عند إعادة التشغيل). بيئة
# الإنتاج يجب أن تضبط NIBRAS_JWT_SECRET قيمة ثابتة عشوائية طويلة.
_JWT_SECRET = os.environ.get("NIBRAS_JWT_SECRET")
if _JWT_SECRET is None:
    import secrets as _secrets

    _JWT_SECRET = _secrets.token_urlsafe(48)
    # إنذار دائم (وليس في التطوير فقط) حتى يظهر غياب السر في سجل الإنتاج
    _safe_warn(
        "[config] تحذير: NIBRAS_JWT_SECRET غير مضبوط — استُخدم سر عشوائي مؤقت "
        "(تنتهي الجلسات عند إعادة التشغيل)."
    )
JWT_SECRET = _JWT_SECRET
JWT_ALGORITHM = "HS256"

# صلاحيات التوكنات (المواصفة التقنية §4: JWT قصير العمر ~15 دقيقة)
ACCESS_TOKEN_TTL_MINUTES = _env_int("NIBRAS_ACCESS_TOKEN_TTL_MINUTES", 15)
REFRESH_TOKEN_TTL_DAYS = _env_int("NIBRAS_REFRESH_TOKEN_TTL_DAYS", 30)
PASSWORD_RESET_TOKEN_TTL_HOURS = _env_int("NIBRAS_PASSWORD_RESET_TOKEN_TTL_HOURS", 1)

# حد معدل الطلبات على نقاط المصادقة (وثيقة 12 / Security Architecture:
# rate limiting على المصادقة واستعادة كلمة المرور)
RATE_LIMIT_MAX_ATTEMPTS = _env_int("NIBRAS_RATE_LIMIT_MAX_ATTEMPTS", 5)
RATE_LIMIT_WINDOW_SECONDS = _env_int("NIBRAS_RATE_LIMIT_WINDOW_SECONDS", 900)

# عنوان الواجهة لبناء رابط استعادة كلمة المرور المرسَل (واجهة قابلة للتغيير)
FRONTEND_BASE_URL = os.environ.get("NIBRAS_FRONTEND_BASE_URL", "http://localhost:3000")
