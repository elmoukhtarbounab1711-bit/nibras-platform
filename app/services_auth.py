"""
طبقة خدمة المصادقة والهوية (المرحلة 1).

تُنفَّذ هنا كل منطق الهوية وفق وثيقة المصادقة والتفويض والمواصفة التقنية §4:
argon2id لكلمات المرور، JWT قصير العمر للوصول، توكنات تحديث عشوائية تُخزَّن
مجزَّأةً بـ SHA-256، وتدويرها عند كل استخدام وإبطالها عند تسجيل الخروج،
واستعادة كلمة المرور بتوكن زمني يُسلَّم عبر واجهة مرسل بريد قابلة للاستبدال.

قائمة الأدوار ثابتة (§1) ولا يقبل التسجيل العام أي دور إداري — الدور الإداري
يُمنح حصريًا عبر السكربت الداخلي app.create_admin.
"""
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from hashlib import sha256

import jwt as pyjwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from . import config
from .database import db_session

_password_hasher = PasswordHasher()

# القائمة الثابتة للأدوار وفق وثيقة المصادقة والتفويض (§1)
ROLE_CODES = (
    "citizen", "student", "lawyer", "notary", "adoul",
    "judicial_commissioner", "sworn_translator", "judicial_expert",
    "company", "institution", "admin",
)

# الأدوار المهنية التي تبدأ بالحالة pending_verification إلى حين التحقق
# (وثيقة المصادقة والتفويض §2.1)
PROFESSIONAL_ROLES = {
    "lawyer", "notary", "adoul", "judicial_commissioner",
    "sworn_translator", "judicial_expert", "company", "institution",
}

ROLE_LABELS = {
    "citizen": "مواطن",
    "student": "طالب",
    "lawyer": "محامٍ",
    "notary": "موثق",
    "adoul": "عدل",
    "judicial_commissioner": "مفوض قضائي",
    "sworn_translator": "مترجم حلف",
    "judicial_expert": "خبير قضائي",
    "company": "شركة",
    "institution": "مؤسسة",
    "admin": "مسؤول النظام",
}

ROLE_CODES_SET = frozenset(ROLE_CODES)


class AuthError(Exception):
    """خطأ تجاري في المصادقة يُترجم إلى استجابة HTTP مناسبة في routes."""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass
class UserProfile:
    """تمثيل المستخدم للأغراض العامة (لا يحمل الحقول الحساسة)."""
    id: int
    email: str
    full_name: str
    roles: list = field(default_factory=list)
    status: str = "active"
    tenant_id: int | None = None

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "roles": self.roles,
            "status": self.status,
            "tenant_id": self.tenant_id,
        }


# ---------------------------------------------------------------------------
# أدوات التجزئة والتوكنات
# ---------------------------------------------------------------------------

# تجزئة argon2id حقيقية لعنصر نائب — يستخدمها مسار البريد غير المسجل في
# authenticate_user لموازنة التوقيت (Security §2). قيمة ثابتة بلا معنى.
_TIMING_DUMMY_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$ZOjoqTMtNwzJ2nQOEdebvA"
    "$cC9X9pp9NffrPwa1LyVKoURibOO6p1nNHELp6zaBBJg"
)


def hash_password(plain: str) -> str:
    """يجزّئ كلمة المرور بـ argon2id."""
    return _password_hasher.hash(plain)


def verify_password(plain: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, plain)
    except (VerifyMismatchError, ValueError):
        return False


def generate_random_token() -> str:
    """توكن عشوائي صريح (لمرجع واحد فقط — يُخزَّن مجزأً بـ SHA-256)."""
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    """خوارزمية تخزين التوكنات: SHA-256 حسب المواصفة التقنية §4."""
    return sha256(token.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# الأدوار
# ---------------------------------------------------------------------------

def ensure_roles():
    """يبذر الأدوار الثابتة إن لم تكن موجودة (تُستدعى من init_db والإقلاع)."""
    with db_session() as conn:
        existing = {r["code"] for r in conn.execute("SELECT code FROM roles")}
        for code in ROLE_CODES:
            if code not in existing:
                conn.execute(
                    "INSERT INTO roles (code, name) VALUES (?,?)",
                    (code, ROLE_LABELS[code]),
                )


def role_status_for_code(code: str) -> str:
    """الحالة الافتراضية لدور: pending_verification للمهني، active لغيره."""
    return "pending_verification" if code in PROFESSIONAL_ROLES else "active"


def get_user_roles(user_id: int) -> list:
    """يرجع قائمة أدوار المستخدم بصيغة dict (code, name, status)."""
    with db_session() as conn:
        rows = conn.execute(
            """SELECT r.code, r.name, ur.role_status AS status
               FROM user_roles ur JOIN roles r ON r.id = ur.role_id
               WHERE ur.user_id = ? ORDER BY r.code""",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# المستخدمون
# ---------------------------------------------------------------------------

def validate_email(email: str) -> str:
    email = (email or "").strip().lower()
    if not email or "@" not in email:
        raise AuthError("عنوان البريد الإلكتروني غير صالح", 400)
    return email


def validate_password(password: str) -> None:
    if not password or len(password) < 8:
        raise AuthError("كلمة المرور يجب أن تتكون من 8 أحرف على الأقل", 400)


def validate_role_code(code: str) -> str:
    code = (code or "").strip().lower()
    if code not in ROLE_CODES_SET:
        raise AuthError("الدور غير معروف", 400)
    if code == "admin":
        raise AuthError("لا يمكن منح دور المسؤول عبر التسجيل العام", 403)
    return code


def create_user(email: str, password: str, full_name: str, role_code: str,
                tenant_id=None) -> UserProfile:
    """تسجيل عام وفق الشروط (§2.1) مع ربط المستأجر (الافتراضي إن لم يُحدَّد).

    يرفض الدور الإداري (يُمنح حصريًا عبر app.create_admin) ويطبق الحالة
    الافتراضية للتحقق (§2.1). يرمي AuthError عند تكرار البريد.
    """
    role_code = validate_role_code(role_code)
    return create_user_with_role(
        email=email, password=password, full_name=full_name, role_code=role_code,
        role_status=role_status_for_code(role_code), user_status="active",
        tenant_id=tenant_id,
    )


def _default_tenant_id() -> int:
    """معرّف المستأجر الافتراضي (مبذور في init_db عبر services_tenants)."""
    with db_session() as conn:
        row = conn.execute(
            "SELECT id FROM tenants WHERE slug = ?", (config.DEFAULT_TENANT_SLUG,)
        ).fetchone()
    return row["id"] if row else 1


def create_user_with_role(email, password, full_name, role_code, role_status="active",
                          user_status="active", tenant_id=None):
    """إنشاء مستخدم بدور محدد وحالة صريحة (للاستخدام الداخلي/CLI فقط)."""
    email = validate_email(email)
    validate_password(password)
    full_name = (full_name or "").strip()
    if not full_name:
        raise AuthError("الاسم الكامل مطلوب", 400)
    password_hash = hash_password(password)
    if tenant_id is None:
        tenant_id = _default_tenant_id()
    with db_session() as conn:
        exists = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if exists:
            raise AuthError("البريد الإلكتروني مسجل مسبقًا", 409)
        cur = conn.execute(
            "INSERT INTO users (email, full_name, password_hash, status, tenant_id)"
            " VALUES (?,?,?,?,?)",
            (email, full_name, password_hash, user_status, tenant_id),
        )
        user_id = cur.lastrowid
        role_id = conn.execute("SELECT id FROM roles WHERE code = ?", (role_code,)).fetchone()["id"]
        conn.execute(
            "INSERT INTO user_roles (user_id, role_id, role_status) VALUES (?,?,?)",
            (user_id, role_id, role_status),
        )
    return get_user_profile(user_id)


def get_user_profile(user_id: int) -> UserProfile | None:
    with db_session() as conn:
        row = conn.execute(
            "SELECT id, email, full_name, status, tenant_id FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if not row:
            return None
    return UserProfile(
        id=row["id"], email=row["email"], full_name=row["full_name"],
        status=row["status"], tenant_id=row["tenant_id"],
        roles=[r["code"] for r in get_user_roles(user_id)],
    )


def get_user_by_email(email: str) -> UserProfile | None:
    with db_session() as conn:
        row = conn.execute(
            "SELECT id, email, full_name, status, tenant_id FROM users WHERE email = ?",
            ((email or "").strip().lower(),),
        ).fetchone()
        if not row:
            return None
    return UserProfile(
        id=row["id"], email=row["email"], full_name=row["full_name"],
        status=row["status"], tenant_id=row["tenant_id"],
        roles=[r["code"] for r in get_user_roles(user_id=row["id"])],
    )


def authenticate_user(email: str, password: str) -> UserProfile | None:
    """يعيد ملف المستخدم عند صحة البريد وكلمة المرور، وإلا None.

    الاستعلام عن البريد ثم التحقق يحمي من توقيت الاختلاف (Security §2).
    لا يُكشف أي تفاصيل عن سبب الفشل (وثيقة 12: رسالة دخول عامة).
    """
    with db_session() as conn:
        row = conn.execute(
            "SELECT id, password_hash, status FROM users WHERE email = ?",
            ((email or "").strip().lower(),),
        ).fetchone()
    if row is None:
        # تجزئة حقيقية لعنصر نائب: تجعل زمن مسار البريد غير المسجل قريبًا من
        # زمن مسار كلمة المرور الخاطئة (مضاد لتسريب وجود البريد عبر التوقيت).
        verify_password("nibras-timing-equalizer-placeholder", _TIMING_DUMMY_HASH)
        return None
    if row["status"] != "active":
        return None
    if not verify_password(password, row["password_hash"]):
        return None
    return get_user_profile(row["id"])


# ---------------------------------------------------------------------------
# JWT والتوكنات
# ---------------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(user_id: int) -> tuple[str, datetime]:
    """ينشئ JWT قصير العمر (المواصفة التقنية §4) ويعيده مع زمن انتهائه.

    يحمل Claim `tenant_id` لمستأجر المستخدم (جاهزية multi-tenant D-035)
    لتمكين الربط/التحقق مستقبلًا دون تغيير صيغة التوكن.
    """
    expires = _now() + timedelta(minutes=config.ACCESS_TOKEN_TTL_MINUTES)
    payload = {"sub": str(user_id), "type": "access", "exp": expires}
    tenant_id = _user_tenant_id(user_id)
    if tenant_id is not None:
        payload["tenant_id"] = tenant_id
    token = pyjwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)
    return token, expires


def decode_access_token(token: str) -> int | None:
    """يعيد معرف المستخدم عند صحة التوكن وصلاحيته، وإلا None."""
    try:
        payload = pyjwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
    except pyjwt.InvalidTokenError:
        return None
    if payload.get("type") != "access":
        return None
    try:
        return int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        return None


def get_token_tenant_id(token: str) -> int | None:
    """يعيد معرف مستأجر التوكن (إن حمله) دون فحص اشتراك المستخدم (D-035)."""
    try:
        payload = pyjwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
    except pyjwt.InvalidTokenError:
        return None
    tenant_id = payload.get("tenant_id")
    if tenant_id is None:
        return None
    try:
        return int(tenant_id)
    except (TypeError, ValueError):
        return None


def _user_tenant_id(user_id: int) -> int | None:
    with db_session() as conn:
        row = conn.execute(
            "SELECT tenant_id FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    return row["tenant_id"] if row else None


def create_refresh_token(user_id: int) -> tuple[str, str]:
    """ينشئ توكن تحديث عشوائيًا، يخزن مجزأً، ويعيد (الصريح, انتهاء ISO)."""
    token = generate_random_token()
    expires = _now() + timedelta(days=config.REFRESH_TOKEN_TTL_DAYS)
    with db_session() as conn:
        conn.execute(
            "INSERT INTO refresh_tokens (token_hash, user_id, expires_at) VALUES (?,?,?)",
            (hash_token(token), user_id, expires.isoformat()),
        )
    return token, expires.isoformat()


def rotate_refresh_token(token: str) -> tuple[str, str, int] | None:
    """يدير توكن التحديث: يتحقق من صلاحيته ثم يستبدله بجديد (دوران §4).

    يعيد (توكن جديد, انتهاء ISO, user_id) أو None عند عدم الصلاحية.
    """
    token_hash = hash_token(token)
    with db_session() as conn:
        row = conn.execute(
            """SELECT id, user_id, expires_at FROM refresh_tokens WHERE token_hash = ?""",
            (token_hash,),
        ).fetchone()
        if row is None:
            return None
        # انتهاء الصلاحية يُبطِل التوكن ويحذفه
        try:
            expires = datetime.fromisoformat(row["expires_at"])
        except ValueError:
            expires = _now() - timedelta(days=1)
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires < _now():
            conn.execute("DELETE FROM refresh_tokens WHERE id = ?", (row["id"],))
            return None
        # دوران: حذف القديم وإنشاء جديد في نفس المعاملة
        conn.execute("DELETE FROM refresh_tokens WHERE id = ?", (row["id"],))
        new_token = generate_random_token()
        new_expires = _now() + timedelta(days=config.REFRESH_TOKEN_TTL_DAYS)
        conn.execute(
            "INSERT INTO refresh_tokens (token_hash, user_id, expires_at) VALUES (?,?,?)",
            (hash_token(new_token), row["user_id"], new_expires.isoformat()),
        )
        return new_token, new_expires.isoformat(), row["user_id"]


def revoke_refresh_token(token: str) -> bool:
    """يبطل جلسة تحديث (تسجيل الخروج). يعيد True عند نجاح الإبطال."""
    with db_session() as conn:
        cur = conn.execute(
            "DELETE FROM refresh_tokens WHERE token_hash = ?", (hash_token(token),)
        )
        return cur.rowcount > 0


# ---------------------------------------------------------------------------
# استعادة كلمة المرور
# ---------------------------------------------------------------------------

class Mailer:
    """واجهة مرسل البريد للاستعادة (وثيقة 12 §التحقق من الهوية والاستعادة).

    مزود البريد الفعلي غير محدد في الوثائق؛ هذه الواجهة القابلة للاستبدال
    تُسهِّل ربط أي مزود لاحقًا. التنفيذ الافتراضي يطبع رابط الاستعادة في
    سجل الخادم (لوضع التطوير فقط).
    """

    def send_password_reset(self, to_email: str, reset_url: str) -> None:
        # وضع التطوير: الرابط يُسجَّل مهيكلًا بدل إرسال بريد (مزوّد لاحق).
        # لا يُسجَّل بريد المستخدم نصًا — يُسجَّل في حقل منفصل عند الحاجة.
        import logging

        logging.getLogger("nibras.mailer").warning(
            "password_reset_dev_link",
            extra={"to_email": to_email, "reset_url": reset_url},
        )


_mailer = Mailer()


def request_password_reset(email: str) -> None:
    """ينشئ توكن استعادة ويطلب إرساله. لا يكشف وجود البريد (مضاد للتعداد)."""
    email = (email or "").strip().lower()
    profile = get_user_by_email(email) if email else None
    if profile is None or profile.status != "active":
        # استهلاك وهمي للمدة يمنع استنتاج وجود البريد من التوقيت
        generate_random_token()
        return
    token = generate_random_token()
    expires = _now() + timedelta(hours=config.PASSWORD_RESET_TOKEN_TTL_HOURS)
    with db_session() as conn:
        conn.execute(
            """INSERT INTO password_reset_tokens (token_hash, user_id, expires_at)
               VALUES (?,?,?)""",
            (hash_token(token), profile.id, expires.isoformat()),
        )
    reset_url = f"{config.FRONTEND_BASE_URL.rstrip('/')}/reset-password?token={token}"
    _mailer.send_password_reset(profile.email, reset_url)


def reset_password_with_token(token: str, new_password: str) -> None:
    """يطبق كلمة المرور الجديدة عند صحة التوكن وعدم انتهائه.

    يرفع AuthError برسالة عامة عند بطلان/انتهاء/استخدام التوكن.
    """
    validate_password(new_password)
    token_hash = hash_token(token)
    with db_session() as conn:
        row = conn.execute(
            """SELECT id, user_id, expires_at, used_at FROM password_reset_tokens
               WHERE token_hash = ?""",
            (token_hash,),
        ).fetchone()
        if row is None or row["used_at"] is not None:
            raise AuthError("رابط الاستعادة غير صالح أو منتهي الصلاحية", 400)
        try:
            expires = datetime.fromisoformat(row["expires_at"])
        except ValueError:
            expires = _now() - timedelta(days=1)
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires < _now():
            raise AuthError("رابط الاستعادة غير صالح أو منتهي الصلاحية", 400)
        conn.execute(
            "UPDATE users SET password_hash = ?, updated_at = datetime('now') WHERE id = ?",
            (hash_password(new_password), row["user_id"]),
        )
        conn.execute(
            "UPDATE password_reset_tokens SET used_at = datetime('now') WHERE id = ?",
            (row["id"],),
        )
        # إبطال كل جلسات التحديث بعد تغيير كلمة المرور
        conn.execute("DELETE FROM refresh_tokens WHERE user_id = ?", (row["user_id"],))


def has_active_role(user_id: int, roles: tuple) -> bool:
    """هل يملك المستخدم واحدًا من الأدوار المطلوبة وبحالة active؟"""
    required = set(roles)
    with db_session() as conn:
        rows = conn.execute(
            """SELECT r.code, ur.role_status FROM user_roles ur
               JOIN roles r ON r.id = ur.role_id WHERE ur.user_id = ?""",
            (user_id,),
        ).fetchall()
    return any(
        r["code"] in required and r["role_status"] == "active" for r in rows
    )
