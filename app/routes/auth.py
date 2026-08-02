"""
المسارات العامة للمصادقة (Blueprint) — المرحلة 1.

نقاط التسجيل والدخول وتجديد التوكن وتسجيل الخروج واستعادة كلمة المرور
وملف المستخدم، وفق وثيقة المصادقة والتفويض (§2). تنطبق الحماية من معدل
الطلبات على نقاط المصادقة والاستعادة (وثيقة 12 / Security Architecture).
"""
import time

from flask import Blueprint, jsonify, request

from .. import config, services_auth, services_tenants
from ..middleware.auth_middleware import require_auth
from ..services_auth import AuthError

auth_bp = Blueprint("auth", __name__)

# حد معدل طلبات بسيط في الذاكرة (لكل عنوان IP + نقطة). يكفي لمرحلة النشر
# أحادي العملية؛ بيئة متعددة العمليات/الخوادم تنقله إلى مخزن مشترك.
_attempts = {}


def _rate_limited(key: str) -> bool:
    """يسجل محاولة ويعيد True إذا تجاوزت الحد المسموح."""
    now = time.time()
    window = config.RATE_LIMIT_WINDOW_SECONDS
    bucket = _attempts.setdefault(key, [])
    bucket[:] = [t for t in bucket if now - t < window]
    if len(bucket) >= config.RATE_LIMIT_MAX_ATTEMPTS:
        return True
    bucket.append(now)
    return False


def _client_key() -> str:
    return request.remote_addr or "unknown"


def _handle_auth_error(exc: AuthError):
    return jsonify({"error": exc.message}), exc.status_code


def _auth_response(user_profile, refresh_token, refresh_expires, status_code=200):
    access_token, _access_expires = services_auth.create_access_token(user_profile.id)
    payload = {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": config.ACCESS_TOKEN_TTL_MINUTES * 60,
        "refresh_token": refresh_token,
        "refresh_expires_at": refresh_expires,
        "user": user_profile.to_dict(),
    }
    return jsonify(payload), status_code


@auth_bp.route("/api/auth/register", methods=["POST"])
def register():
    if _rate_limited(f"register:{_client_key()}"):
        return jsonify({"error": "طلبات كثيرة جدًا. حاول لاحقًا."}), 429
    data = request.get_json(force=True, silent=True) or {}
    try:
        tenant_id = _register_tenant_id()
        profile = services_auth.create_user(
            email=data.get("email"),
            password=data.get("password"),
            full_name=data.get("full_name"),
            role_code=data.get("role", "citizen"),
            tenant_id=tenant_id,
        )
    except AuthError as exc:
        return _handle_auth_error(exc)
    refresh_token, refresh_expires = services_auth.create_refresh_token(profile.id)
    return _auth_response(profile, refresh_token, refresh_expires, status_code=201)


def _register_tenant_id() -> int | None:
    """مستأجر التسجيل: رأس X-Tenant-Id في الوضع المفعّل، وإلا الافتراضي.

    جاهزية multi-tenant (D-035): لا يُقبل رأس في الوضع أحادي المستأجر؛
    وفي الوضع المفعّل يُرفض رأس لمستأجر غير معروف أو غير نشط (400).
    """
    if not config.MULTI_TENANT:
        return None
    header = request.headers.get("X-Tenant-Id")
    if not header:
        return None
    tenant = services_tenants.resolve_tenant(header)
    if tenant is None or tenant["status"] != "active":
        raise AuthError("مستأجر غير معروف أو غير نشط.", 400)
    return tenant["id"]


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    if _rate_limited(f"login:{_client_key()}"):
        return jsonify({"error": "طلبات كثيرة جدًا. حاول لاحقًا."}), 429
    data = request.get_json(force=True, silent=True) or {}
    profile = services_auth.authenticate_user(data.get("email"), data.get("password"))
    if profile is None:
        # رسالة عامة موحدة — لا تكشف عن سبب الفشل (وثيقة 12)
        return jsonify({"error": "بيانات الدخول غير صحيحة"}), 401
    refresh_token, refresh_expires = services_auth.create_refresh_token(profile.id)
    return _auth_response(profile, refresh_token, refresh_expires)


@auth_bp.route("/api/auth/refresh", methods=["POST"])
def refresh():
    if _rate_limited(f"refresh:{_client_key()}"):
        return jsonify({"error": "طلبات كثيرة جدًا. حاول لاحقًا."}), 429
    data = request.get_json(force=True, silent=True) or {}
    result = services_auth.rotate_refresh_token(data.get("refresh_token") or "")
    if result is None:
        return jsonify({"error": "توكن التحديث غير صالح أو منتهي"}), 401
    new_token, new_expires, user_id = result
    profile = services_auth.get_user_profile(user_id)
    if profile is None or profile.status != "active":
        return jsonify({"error": "غير مصرح. الحساب غير نشط."}), 401
    return _auth_response(profile, new_token, new_expires)


@auth_bp.route("/api/auth/logout", methods=["POST"])
@require_auth
def logout():
    data = request.get_json(force=True, silent=True) or {}
    if data.get("refresh_token"):
        services_auth.revoke_refresh_token(data["refresh_token"])
    return jsonify({"message": "تم تسجيل الخروج"}), 200


@auth_bp.route("/api/auth/me", methods=["GET"])
@require_auth
def me():
    return jsonify({"user": request.user.to_dict()}), 200


@auth_bp.route("/api/auth/password-reset/request", methods=["POST"])
def password_reset_request():
    if _rate_limited(f"reset_request:{_client_key()}"):
        return jsonify({"error": "طلبات كثيرة جدًا. حاول لاحقًا."}), 429
    data = request.get_json(force=True, silent=True) or {}
    services_auth.request_password_reset(data.get("email") or "")
    # استجابة موحدة — لا نكشف وجود البريد (مضاد للتعداد)
    return jsonify({"message": "إن كان البريد مسجلًا، ستصل رسالة الاستعادة."}), 202


@auth_bp.route("/api/auth/password-reset/confirm", methods=["POST"])
def password_reset_confirm():
    if _rate_limited(f"reset_confirm:{_client_key()}"):
        return jsonify({"error": "طلبات كثيرة جدًا. حاول لاحقًا."}), 429
    data = request.get_json(force=True, silent=True) or {}
    try:
        services_auth.reset_password_with_token(
            data.get("token") or "", data.get("new_password") or ""
        )
    except AuthError as exc:
        return _handle_auth_error(exc)
    return jsonify({"message": "تم تحديث كلمة المرور بنجاح"}), 200
