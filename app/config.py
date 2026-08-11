"""
إعدادات التطبيق عبر متغيرات البيئة.

يُقرأ كل إعداد من بيئة التشغيل ولا يُثبَّت في الكود المصدري، وفق مبدأ
الأمان في وثيقة هندسة نبراس (§10) والوثيقة 12 (Security Architecture §1):
المفتاح الثابت debug=True و CORS الشامل يُستبدلان بإعدادات بيئة صريحة.

القيم الافتراضية هنا آمنة للتطوير المحلي فقط؛ بيئة الإنتاج يجب أن تضبطها صراحة.
"""
import os
from pathlib import Path


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


# ---------------------------------------------------------------------------
# السجلات المهيكلة والصحة (المرحلة 11 — الصلابة التشغيلية)
# ---------------------------------------------------------------------------

# مستوى سجلات الجذر (DEBUG|INFO|WARNING|ERROR)
LOG_LEVEL = os.environ.get("NIBRAS_LOG_LEVEL", "INFO")

# صيغة السجلات: "json" (سطر JSON مهيكل) أو "text" (key=value للمراجعة المحلية)
LOG_FORMAT = os.environ.get("NIBRAS_LOG_FORMAT", "json")

# تسجيل كل طلب HTTP (method/path/status/duration_ms/request_id/remote_addr/user_id)
LOG_ACCESS = _env_bool("NIBRAS_LOG_ACCESS", "1")

# إصدار التطبيق يُعرض في /api/ready (لمرجعية نشر سريعة في السجلات/المراقبة)
APP_VERSION = os.environ.get("NIBRAS_APP_VERSION", "1.0.0")


def _safe_warn(text: str) -> None:
    """طباعة إنذار لا ينهار على وحدات تحكم لا تدعم العربية (مثل cp1252)."""
    import logging as _logging

    if any(
        getattr(h, "_nibras", False) for h in _logging.root.handlers
    ):
        # السجل المهيكل مفعّل (المرحلة 11) — معالجه آمن الترميز
        _logging.getLogger("nibras.config").warning(text)
        return
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

# مجلد ملفات الواجهة الأمامية الذي يخدمه الخادم نفسه على / و/admin
# (الواجهة الجديدة متعددة الملفات — تُفتح عبر localhost:8000 مباشرة).
FRONTEND_DIR = os.environ.get(
    "NIBRAS_FRONTEND_DIR",
    str(Path(__file__).resolve().parent.parent / "frontend"),
)

# ---------------------------------------------------------------------------
# الذكاء الاصطناعي (المرحلة 3) — وفق وثيقة 13 (AI Architecture)
# ---------------------------------------------------------------------------

# المزوّد: "noop" افتراضي للتطوير والاختبار (استجابة حتمية بلا شبكة)، و
# "anthropic" للإنتاج (يتطلب ANTHROPIC_API_KEY). المزوّد قابل للاستبدال
# بواجهة generate() موحّدة (قرار D-021).
AI_PROVIDER = os.environ.get("NIBRAS_AI_PROVIDER", "noop")

# نموذج فئة Sonnet وفق وثيقة 13 §5 (يُعاود التحقق من المستوى في الإنتاج).
AI_MODEL = os.environ.get("NIBRAS_AI_MODEL", "claude-sonnet-4-5")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
AI_MAX_TOKENS = _env_int("NIBRAS_AI_MAX_TOKENS", 2048)

# عدد المواد المسترجعة كسياق موجَّه لكل سؤال (وثيقة 13 §2) — رُفع ليلائم
# مكتبة نبراس الواسعة (أكثر من 1600 نص قانوني / 24 ألف مادة) فيُتاح للمزوّد
# سياق أوسع للإجابة انطلاقًا من المكتبة.
AI_RETRIEVAL_LIMIT = _env_int("NIBRAS_AI_RETRIEVAL_LIMIT", 12)

# عدد الاجتهادات القضائية المسترجعة كسياق إضافي (فقه قضائي) لكل سؤال.
# تُسترجَع اجتهادات محكمة النقض المتصلة بسؤال المستخدم وتُرفَق بالمواد في
# الإجابة الموجَّهة كمرجع ثانٍ (المواد ملزمة، الاجتهاد مؤيِّد). صفر = تعطيل.
AI_JURISPRUDENCE_LIMIT = _env_int("NIBRAS_AI_JURISPRUDENCE_LIMIT", 5)

# أقصى طول (حرف) يُقتبس من نص الاجتهاد الواحد في سياق المزوّد — معظم نصوص
# الاجتهادات حسَنة الحجم (وسيط ~277 حرفًا) لكن بعضها طويل جدًّا (حتى 11 ألف).
# القطع يمنع انفجار سياق الإجابة الموجَّهة دون إضعاف دلالة المبدأ المستشهد به.
AI_JURISPRUDENCE_MAX_CHARS = _env_int("NIBRAS_AI_JURISPRUDENCE_MAX_CHARS", 800)

# حد معدل طلبات الذكاء الاصطناعي لكل مستخدم (وثيقة 13 §7 / Security 12 §6)
AI_RATE_LIMIT_MAX_REQUESTS = _env_int("NIBRAS_AI_RATE_LIMIT_MAX_REQUESTS", 20)
AI_RATE_LIMIT_WINDOW_SECONDS = _env_int("NIBRAS_AI_RATE_LIMIT_WINDOW_SECONDS", 3600)

# البحث الخارجي في وضع المقارنة (research): عدد النتائج المسترجعة من الويب
# ومهلة كل طلب بالثواني. يُستخدم DuckDuckGo HTML بلا مفتاح — إخفاقه لا يُفشل
# الإجابة (تُعاد الإجابة من نبراس فقط). صفر = تعطيل البحث الخارجي.
AI_WEBSEARCH_LIMIT = _env_int("NIBRAS_AI_WEBSEARCH_LIMIT", 5)
AI_WEBSEARCH_TIMEOUT = _env_int("NIBRAS_AI_WEBSEARCH_TIMEOUT", 12)

# ---------------------------------------------------------------------------
# مولّد الوثائق (المرحلة 4) — وفق المواصفة التقنية §6 وقرار D-022
# ---------------------------------------------------------------------------

# مسار خط PDF عربي (reportlab). فارغ = حل تلقائي من قائمة مسارات شائعة:
# ويندوز Arial؛ لينكس Noto Naskh Arabic / Amiri. يَتعيّن في
# services_documents._resolve_pdf_font(). (وثيقة D-022 — قرار التصدير)
PDF_FONT_PATH = os.environ.get("NIBRAS_PDF_FONT", "")

# حد معدل التوليد لكل مستخدم (التوليد حساب + تخزين — نمط حدّ الذكاء
# الاصطناعي في D-021)
DOC_RATE_LIMIT_MAX_REQUESTS = _env_int("NIBRAS_DOC_RATE_LIMIT_MAX_REQUESTS", 10)
DOC_RATE_LIMIT_WINDOW_SECONDS = _env_int("NIBRAS_DOC_RATE_LIMIT_WINDOW_SECONDS", 3600)

# ---------------------------------------------------------------------------
# النظام البيئي المهني (المرحلة 5) — وفق وثيقة 17 وقرار D-023
# ---------------------------------------------------------------------------

# مجلد رفع وثائق التحقق المهنية (تخزين محلي ريثما يُنقل إلى مخزن كائنات —
# Architecture §10؛ قرار D-023)
UPLOAD_DIR = os.environ.get("NIBRAS_UPLOAD_DIR", "")

# حد الحجم الأقصى لوثيقة التحقق (بايت — افتراضيًا 5MB)
MAX_UPLOAD_BYTES = _env_int("NIBRAS_MAX_UPLOAD_BYTES", 5 * 1024 * 1024)

# الامتدادات المسموح بها لوثائق التحقق
ALLOWED_UPLOAD_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}

# ---------------------------------------------------------------------------
# المجتمع (المرحلة 6 — Roadmap Phase 5) — وفق وثيقة 16 وقرار D-024
# ---------------------------------------------------------------------------

# حد معدل إنشاء المنشورات/التعليقات لكل مستخدم (وثيقة 16 §4 — مكافحة
# الإساءة، نمط حدّ الذكاء الاصطناعي في D-021)
COMMUNITY_RATE_LIMIT_MAX_REQUESTS = _env_int("NIBRAS_COMMUNITY_RATE_LIMIT_MAX_REQUESTS", 30)
COMMUNITY_RATE_LIMIT_WINDOW_SECONDS = _env_int("NIBRAS_COMMUNITY_RATE_LIMIT_WINDOW_SECONDS", 3600)

# ---------------------------------------------------------------------------
# نظام الإعلانات (المرحلة 9 — Roadmap Phase 6) — وفق وثيقة 15 وقرار D-027
# ---------------------------------------------------------------------------

# حد معدل أحداث التتبع (انطباع/نقرة) لكل مفتاح (مستخدم نشط أو عنوان IP)
# لمنع تضخيم الإحصائيات (وثيقة 15 §6 — حماية بيانات التقارير)
AD_RATE_LIMIT_MAX_REQUESTS = _env_int("NIBRAS_AD_RATE_LIMIT_MAX_REQUESTS", 100)
AD_RATE_LIMIT_WINDOW_SECONDS = _env_int("NIBRAS_AD_RATE_LIMIT_WINDOW_SECONDS", 3600)

# ---------------------------------------------------------------------------
# محرك رفع المستندات (المرحلة 10 — قرار D-028): استيعاب PDF/DOCX إلى المكتبة
# ---------------------------------------------------------------------------

# حد الحجم الأقصى لملف المستند (بايت — أكبر من حد وثائق التحقق لأن النصوص
# القانونية أطول؛ التوليد متزامن ضمن الطلب — قرار D-028)
INGESTION_MAX_BYTES = _env_int("NIBRAS_INGESTION_MAX_BYTES", 20 * 1024 * 1024)

# سقف المواد المستخرجة لكل استيعاب (حماية قاعدة البيانات من ملف هائل)
INGESTION_MAX_ARTICLES = _env_int("NIBRAS_INGESTION_MAX_ARTICLES", 1000)

# سقف حروف "المادة الواحدة" الاحتياطية عند غياب عناوين مواد (fallback)
INGESTION_SINGLE_ARTICLE_MAX_CHARS = _env_int(
    "NIBRAS_INGESTION_SINGLE_ARTICLE_MAX_CHARS", 4000
)

# ---------------------------------------------------------------------------
# تسليم الإشعارات الخارجية (المرحلة 16 — قرار D-034): بريد + دفع
# ---------------------------------------------------------------------------

# مزوّد البريد: "noop" افتراضي للتطوير والاختبار (يسجّل الإرسال بلا شبكة —
# يحاكي النجاح فقط في وضع التطوير، مثل مزوّد الذكاء الاصطناعي في D-021)، و
# "console" لطباعة سجل مهيكل للإرسال. الإنتاج يربط مزوّدًا حقيقيًا عبر واجهة
# _send_email الموحّدة. أي قيمة غير معروفة تُعامَل كفشل (تظهر في صندوق التسليم).
EMAIL_PROVIDER = os.environ.get("NIBRAS_EMAIL_PROVIDER", "noop")

# المرسل الافتراضي للبريد الخارجي (يستخدمه مزوّد الإنتاج لاحقًا)
EMAIL_FROM = os.environ.get("NIBRAS_EMAIL_FROM", "nibras@localhost")

# مزوّد الدفع: "noop" (تسجيل بلا شبكة) أو "console" (سجل مهيكل).
PUSH_PROVIDER = os.environ.get("NIBRAS_PUSH_PROVIDER", "noop")

# سقف صفوف صندوق التسليم المعالجة في كل تفريغ (deliver_pending)
NOTIFICATION_OUTBOX_LIMIT = _env_int("NIBRAS_NOTIFICATION_OUTBOX_LIMIT", 50)

# أقصى محاولات تسليم قبل إعلان فشل الصف نهائيًا
NOTIFICATION_OUTBOX_MAX_ATTEMPTS = _env_int(
    "NIBRAS_NOTIFICATION_OUTBOX_MAX_ATTEMPTS", 3
)

# ---------------------------------------------------------------------------
# جاهزية multi-tenant (المرحلة 17 — قرار D-035): عزل الهوية فقط
# ---------------------------------------------------------------------------

# وضع متعدد المستأجرين: معطَّل افتراضيًا (سلوك أحادي المستأجر الحالي
# تمامًا — يُتجاهل رأس X-Tenant-Id). عند التفعيل (1) يُتحقق المستأجر
# من الرأس ويُرفض التعارض مع مستأجر المستخدم (403). عزل بيانات الوحدات
# نفسه مؤجَّل لمرحلة multi-tenancy الفعلية — هذه الجاهزية البنيوية فقط.
MULTI_TENANT = _env_bool("NIBRAS_MULTI_TENANT")

# معرّف المستأجر الافتراضي (الرئيسي) المبذور تلقائيًا عند الإقلاع
DEFAULT_TENANT_SLUG = os.environ.get("NIBRAS_DEFAULT_TENANT_SLUG", "nibras")
