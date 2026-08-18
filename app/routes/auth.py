"""
مسارات الهوية (Blueprint) — تسجيل دخول/إنشاء حساب مع امتثال القانون 09-08.

التحقق بخطوتين (TOTP) إلزامي للمشرفين. حماية من التخمين لجميع الحسابات.
حق الوصول والمحو وفق القانون 09-08 المتعلق بالمعالجة الآلية للمعطيات الشخصية.
"""
import time

from flask import Blueprint, jsonify, request

from .. import config
from ..middleware.auth_middleware import public_auth, require_auth
from ..services_auth import (
    AuthError,
    authenticate_user_safe,
    create_access_token,
    create_refresh_token,
    create_user,
    decode_access_token,
    delete_user_data,
    export_user_data,
    get_user_profile,
    has_active_role,
    is_2fa_enabled,
    log_auth_event,
    revoke_refresh_token,
    rotate_refresh_token,
    setup_2fa,
    verify_2fa_code,
    verify_and_enable_2fa,
)

auth_bp = Blueprint("auth", __name__)

# حد معدل في الذاكرة لكل عنوان IP — يحمي النقاط الحساسة
_attempts = {}


def _rate_limited(key: str) -> bool:
    now = time.time()
    window = config.RATE_LIMIT_WINDOW_SECONDS
    bucket = _attempts.setdefault(key, [])
    bucket[:] = [t for t in bucket if now - t < window]
    if len(bucket) >= config.RATE_LIMIT_MAX_ATTEMPTS:
        return True
    bucket.append(now)
    return False


def _client_ip() -> str:
    return request.remote_addr or "unknown"


def _user_agent() -> str:
    return (request.headers.get("User-Agent") or "")[:200]


# ──────────────────────────────────────────────────────────────────────
# التسجيل (القانون 09-08 — موافقة صريحة على المعالجة)
# ──────────────────────────────────────────────────────────────────────

@auth_bp.route("/api/auth/register", methods=["POST"])
@public_auth
def register():
    """إنشاء حساب جديد مع موافقة صريحة على معالجة المعطيات الشخصية."""
    client = _client_ip()
    if _rate_limited(f"auth:{client}"):
        return jsonify({"error": "طلبات كثيرة جدًا. حاول لاحقًا."}), 429

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    full_name = (data.get("full_name") or "").strip()
    role = (data.get("role") or "citizen").strip().lower()
    consent_processing = data.get("consent_data_processing") is True
    consent_terms = data.get("consent_terms") is True

    if not email or not password or not full_name:
        return jsonify({"error": "البريد الإلكتروني وكلمة المرور والاسم الكامل مطلوبة"}), 400

    if not consent_processing or not consent_terms:
        return jsonify({
            "error": "يجب الموافقة على شروط معالجة المعطيات الشخصية وشروط الاستخدام",
        }), 400

    try:
        user = create_user(
            email=email, password=password, full_name=full_name, role_code=role,
            consent_data_processing=consent_processing, consent_terms=consent_terms,
        )
    except AuthError as e:
        return jsonify({"error": e.message}), e.status_code

    access_token, expires = create_access_token(user.id)
    refresh_token, refresh_expires = create_refresh_token(user.id)
    log_auth_event("register.success", user_id=user.id, ip_address=client,
                   user_agent=_user_agent())

    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires": expires.isoformat(),
        "refresh_expires": refresh_expires,
        "user": user.to_dict(),
    }), 201


# ──────────────────────────────────────────────────────────────────────
# تسجيل الدخول (حماية من التخمين + سجل مصادقة)
# ──────────────────────────────────────────────────────────────────────

@auth_bp.route("/api/auth/login", methods=["POST"])
@public_auth
def login():
    """تسجيل دخول مع حماية من التخمين والتحقق بخطوتين للمشرفين."""
    client = _client_ip()
    if _rate_limited(f"auth:{client}"):
        return jsonify({"error": "طلبات كثيرة جدًا. حاول لاحقًا."}), 429

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    totp_code = (data.get("totp_code") or "").strip()

    if not email or not password:
        return jsonify({"error": "البريد الإلكتروني وكلمة المرور مطلوبة"}), 400

    try:
        user = authenticate_user_safe(email, password, client, _user_agent())
    except AuthError as e:
        return jsonify({"error": e.message}), e.status_code

    if user is None:
        return jsonify({"error": "البريد الإلكتروني أو كلمة المرور غير صحيحة"}), 401

    if is_2fa_enabled(user.id):
        if not totp_code:
            return jsonify({
                "error": "التحقق بخطوتين مطلوب",
                "requires_2fa": True,
            }), 200
        if not verify_2fa_code(user.id, totp_code):
            log_auth_event("login.2fa_failed", user_id=user.id, ip_address=client,
                           user_agent=_user_agent())
            return jsonify({"error": "رمز التحقق غير صحيح"}), 401

    access_token, expires = create_access_token(user.id)
    refresh_token, refresh_expires = create_refresh_token(user.id)

    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires": expires.isoformat(),
        "refresh_expires": refresh_expires,
        "user": user.to_dict(),
    }), 200


# ──────────────────────────────────────────────────────────────────────
# تحديث التوكن
# ──────────────────────────────────────────────────────────────────────

@auth_bp.route("/api/auth/refresh", methods=["POST"])
@public_auth
def refresh():
    client = _client_ip()
    if _rate_limited(f"auth:{client}"):
        return jsonify({"error": "طلبات كثيرة جدًا. حاول لاحقًا."}), 429

    data = request.get_json(silent=True) or {}
    token = data.get("refresh_token") or ""
    if not token:
        return jsonify({"error": "توكن التحديث مطلوب"}), 400

    result = rotate_refresh_token(token)
    if result is None:
        return jsonify({"error": "توكن التحديث غير صالح أو منتهي الصلاحية"}), 401

    new_token, expires, user_id = result
    access_token, access_expires = create_access_token(user_id)
    user = get_user_profile(user_id)

    return jsonify({
        "access_token": access_token,
        "refresh_token": new_token,
        "expires": access_expires.isoformat(),
        "refresh_expires": expires,
        "user": user.to_dict() if user else None,
    }), 200


# ──────────────────────────────────────────────────────────────────────
# تسجيل الخروج
# ──────────────────────────────────────────────────────────────────────

@auth_bp.route("/api/auth/logout", methods=["POST"])
@public_auth
def logout():
    data = request.get_json(silent=True) or {}
    token = data.get("refresh_token") or ""
    if token:
        revoke_refresh_token(token)
    client = _client_ip()
    user_id = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        uid = decode_access_token(auth_header[7:])
        user_id = uid
    log_auth_event("logout", user_id=user_id, ip_address=client, user_agent=_user_agent())
    return jsonify({"message": "تم تسجيل الخروج"}), 200


# ──────────────────────────────────────────────────────────────────────
# ملف المستخدم
# ──────────────────────────────────────────────────────────────────────

@auth_bp.route("/api/auth/me", methods=["GET"])
@require_auth
def me():
    return jsonify({"user": request.user.to_dict()}), 200


# ──────────────────────────────────────────────────────────────────────
# استعادة كلمة المرور
# ──────────────────────────────────────────────────────────────────────

@auth_bp.route("/api/auth/password-reset/request", methods=["POST"])
@public_auth
def password_reset_request():
    from ..services_auth import request_password_reset as _req

    client = _client_ip()
    if _rate_limited(f"auth:{client}"):
        return jsonify({"error": "طلبات كثيرة جدًا. حاول لاحقًا."}), 429

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    if not email:
        return jsonify({"error": "البريد الإلكتروني مطلوب"}), 400

    _req(email)
    return jsonify({"message": "إذا كان البريد مسجّلًا، ستتلقى رسالة استعادة"}), 200


@auth_bp.route("/api/auth/password-reset/confirm", methods=["POST"])
@public_auth
def password_reset_confirm():
    from ..services_auth import reset_password_with_token as _reset

    data = request.get_json(silent=True) or {}
    token = (data.get("token") or "").strip()
    new_password = data.get("new_password") or ""

    if not token or not new_password:
        return jsonify({"error": "التوكن وكلمة المرور الجديدة مطلوبة"}), 400

    try:
        _reset(token, new_password)
    except AuthError as e:
        return jsonify({"error": e.message}), e.status_code

    return jsonify({"message": "تم تغيير كلمة المرور بنجاح"}), 200


# ──────────────────────────────────────────────────────────────────────
# التحقق بخطوتين (TOTP) — حماية حساب المشرف
# ──────────────────────────────────────────────────────────────────────

@auth_bp.route("/api/auth/2fa/setup", methods=["POST"])
@require_auth
def two_factor_setup():
    """يولّد سر TOTP ويعرضه كـ URI لإضافته في تطبيق المصادقة."""
    user_id = request.user.id
    try:
        uri = setup_2fa(user_id)
    except AuthError as e:
        return jsonify({"error": e.message}), e.status_code
    return jsonify({"uri": uri, "message": "أضف هذا الرابط في تطبيق المصادقة ثم أكمل التحقق"}), 200


@auth_bp.route("/api/auth/2fa/verify", methods=["POST"])
@require_auth
def two_factor_verify():
    """يتحقق من رمز TOTP ويُفعّل التحقق بخطوتين."""
    data = request.get_json(silent=True) or {}
    code = (data.get("code") or "").strip()
    if not code:
        return jsonify({"error": "رمز التحقق مطلوب"}), 400

    ok = verify_and_enable_2fa(request.user.id, code)
    if not ok:
        return jsonify({"error": "رمز التحقق غير صحيح. تأكد من الساعة المزدوجة."}), 400

    log_auth_event("2fa.enabled", user_id=request.user.id, ip_address=_client_ip())
    return jsonify({"message": "تم تفعيل التحقق بخطوتين بنجاح"}), 200


# ──────────────────────────────────────────────────────────────────────
# قانون 09-08 — حق الوصول والمحو
# ──────────────────────────────────────────────────────────────────────

@auth_bp.route("/api/auth/data-export", methods=["GET"])
@require_auth
def data_export():
    """تصدير جميع معطيات المستخدم (حق الوصول — القانون 09-08)."""
    try:
        data = export_user_data(request.user.id)
    except AuthError as e:
        return jsonify({"error": e.message}), e.status_code
    return jsonify(data), 200


@auth_bp.route("/api/auth/data-delete", methods=["POST"])
@require_auth
def data_delete():
    """محو حساب المستخدم وجميع معطياته (حق المحو — القانون 09-08).

    لا يمكن للمشرف حذف حسابه عبر هذه النقطة (يُدار عبر CLI).
    """
    if has_active_role(request.user.id, ("admin",)):
        return jsonify({"error": "لا يمكن حذف حساب المشرف عبر الواجهة"}), 403
    try:
        delete_user_data(request.user.id)
    except AuthError as e:
        return jsonify({"error": e.message}), e.status_code
    log_auth_event("data.deleted", user_id=request.user.id, ip_address=_client_ip())
    return jsonify({"message": "تم حذف حسابك وجميع معطياتك بنجاح"}), 200


# ──────────────────────────────────────────────────────────────────────
# سياسة الخصوصية — القانون 09-08
# ──────────────────────────────────────────────────────────────────────

@auth_bp.route("/api/auth/privacy-policy", methods=["GET"])
@public_auth
def privacy_policy():
    """سياسة الخصوصية وفق القانون 09-08."""
    return jsonify({
        "title": "سياسة الخصوصية — القانون 09-08",
        "version": "1.0",
        "effective_date": "2025-01-01",
        "sections": [
            {
                "title": "جمع المعطيات",
                "content": "نجمع فقط المعطيات الضرورية لإنشاء الحساب: البريد الإلكتروني والاسم الكامل وكلمة المرور. كلمة المرور مُجزَّأة بـ argon2id ولا تُخزَّن أبدًا كنص.",
            },
            {
                "title": "استخدام المعطيات",
                "content": "تُستخدم معطياتك فقط لتوفير خدمات المنصة: المصادقة، إدارة الحساب، وتقديم المساعدة القانونية. لا نُشارك معطياتك مع أطراف ثالثة.",
            },
            {
                "title": "حماية المعطيات",
                "content": "نستخدم تشفير argon2id لكلمات المرور، JWT قصير العمر للجلسات، والتحقق بخطوتين للمشرفين. جميع الطلبات مُسجَّلة بشكل آمن.",
            },
            {
                "title": "حقوقك",
                "content": "لديك الحق في: الوصول لمعطياتك (/api/auth/data-export)، تعديلها عبر ملفك الشخصي، حذف حسابك وجميع معطياتك (/api/auth/data-delete).",
            },
            {
                "title": "الاحتفاظ بالمعطيات",
                "content": "تُحتفظ بمعطياتك طالما حسابك نشط. عند الحذف، تُمحو جميع المعطيات بشكل نهائي.",
            },
        ],
        "legal_basis": "القانون 09-08 المتعلق بالمعالجة الآلية للمعطيات الشخصية",
        "regulator": "الهيئة الوطنية لحماية المعطيات الشخصية (ANPDP)",
    }), 200


# ──────────────────────────────────────────────────────────────────────
# شروط الاستخدام
# ──────────────────────────────────────────────────────────────────────

@auth_bp.route("/api/auth/terms", methods=["GET"])
@public_auth
def terms_of_service():
    """شروط الاستخدام."""
    return jsonify({
        "title": "شروط الاستخدام — منصة نبراس",
        "version": "1.0",
        "effective_date": "2025-01-01",
        "sections": [
            {
                "title": "قبول الشروط",
                "content": "بإنشاء حساب أو استخدام المنصة، أنت توافق دون تحفظ على شروط الاستخدام هذه.",
            },
            {
                "title": "وصف الخدمة",
                "content": "نبراس منصة معلوماتية قانونية تقدم مكتبة نصوص، اجتهادات، حاسبات، نماذج وثائق، مساعد قانوني بالذكاء الاصطناعي، ومجتمع للمستخدمين.",
            },
            {
                "title": "قواعد الاستخدام",
                "content": "يُمنع نسخ أو توزيع المحتوى دون تفويض، ومحاولة الوصول إلى المناطق المحمية، واستخدام روبوتات لاستخراج البيانات.",
            },
            {
                "title": "الملكية الفكرية",
                "content": "المحتوى محمي بحقوق الملكية الفكرية. النصوص الرسمية في النطاق العام. الكود المصدري بترخيص مفتوح.",
            },
            {
                "title": "القانون الحاكم",
                "content": "تخضع الشروط للقانون المغربي. أي نزاع يخضع للمحاكم المختصة في المملكة المغربية.",
            },
        ],
    }), 200


# ──────────────────────────────────────────────────────────────────────
# سياسة ملفات تعريف الارتباط
# ──────────────────────────────────────────────────────────────────────

@auth_bp.route("/api/auth/cookie-policy", methods=["GET"])
@public_auth
def cookie_policy():
    """سياسة ملفات تعريف الارتباط."""
    return jsonify({
        "title": "سياسة ملفات تعريف الارتباط",
        "version": "1.0",
        "effective_date": "2025-01-01",
        "cookies": [
            {"name": "nibras_access", "purpose": "توكن مصادقة JWT", "duration": "الجلسة", "type": "ضروري"},
            {"name": "nibras_refresh", "purpose": "توكن تحديث", "duration": "30 يوماً", "type": "ضروري"},
            {"name": "nibras_user", "purpose": "بيانات الملف الشخصي", "duration": "الجلسة", "type": "ضروري"},
            {"name": "nibras_lang", "purpose": "التفضيل اللغوي", "duration": "دائم", "type": "وظيفي"},
            {"name": "nibras_theme", "purpose": "تفضيل السمة", "duration": "دائم", "type": "وظيفي"},
        ],
    }), 200
