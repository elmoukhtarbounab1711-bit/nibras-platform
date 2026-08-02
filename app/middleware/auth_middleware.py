"""
وسيط المصادقة والتفويض (المرحلة 1).

تنفيذ موحَّد لـ require_auth و require_role(*roles) وفق وثيقة المصادقة
والتفويض (§2.2) والمواصفة التقنية (§2: مجلد middleware/auth_middleware.py).
يحمل هذا الوسيط المسارات الإدارية السابقة من مفتاح X-Admin-Key إلى
مصادقة Bearer JWT + دور admin (الترحيل §2.5).
"""
from functools import wraps

from flask import jsonify, request

from .. import config, services_auth, services_tenants


def _bearer_token() -> str | None:
    """يستخرج التوكن من رأس Authorization وفق صيغة Bearer (RFC 6750)."""
    header = request.headers.get("Authorization", "")
    parts = header.split(None, 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        token = parts[1].strip()
        return token or None
    return None


class _TenantDenied(Exception):
    """رفض نطاق المستأجر في طلب مُصادَق (يُترجم إلى 403)."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def _resolve_tenant(user_id: int) -> int:
    """يحدد مستأجر الطلب الفعّال وفق وضع multi-tenant ورأس X-Tenant-Id.

    الوضع غير مفعّل (الافتراضي): يُتجاهل الرأس — كل المستخدمين في
    مستأجرهم (الافتراضي) كما في السلوك أحادي المستأجر الحالي.
    الوضع مفعّل (NIBRAS_MULTI_TENANT=1): رأس X-Tenant-Id إلزامي —
    غيابه، أو تعطله (غير معروف/معلّق)، أو تعارضه مع مستأجر المستخدم
    يرفض الطلب (403) — يضبط request.tenant_id لاستخدامات المرحلة اللاحقة.
    """
    tenant_id = services_tenants.get_user_tenant_id(user_id)
    if not config.MULTI_TENANT:
        return tenant_id or services_tenants.default_tenant_id()
    header = request.headers.get("X-Tenant-Id")
    if not header:
        raise _TenantDenied("رأس X-Tenant-Id مطلوب في الوضع متعدد المستأجرين.")
    tenant = services_tenants.resolve_tenant(header)
    if tenant is None or tenant["status"] != "active":
        raise _TenantDenied("مستأجر غير معروف أو غير نشط.")
    if tenant_id is not None and tenant["id"] != tenant_id:
        raise _TenantDenied("لا تملك صلاحية داخل هذا المستأجر.")
    return tenant["id"]


def require_auth(fn):
    """يتطلب توكن وصول JWT صالحًا. يضبط request.user بملف المستخدم."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = _bearer_token()
        if token is None:
            return jsonify({"error": "غير مصرح. يلزم تسجيل الدخول."}), 401
        user_id = services_auth.decode_access_token(token)
        if user_id is None:
            return jsonify({"error": "غير مصرح. الجلسة غير صالحة أو منتهية."}), 401
        profile = services_auth.get_user_profile(user_id)
        if profile is None or profile.status != "active":
            return jsonify({"error": "غير مصرح. الحساب غير نشط."}), 401
        request.user = profile
        try:
            request.tenant_id = _resolve_tenant(user_id)
        except _TenantDenied as exc:
            return jsonify({"error": exc.message}), 403
        return fn(*args, **kwargs)
    return wrapper


def optional_auth(fn):
    """يمرِّر دائمًا؛ يضبط request.user فقط عند وجود توكن صالح وحساب نشط.

    يستخدم في المسارات العامة التي تُثري الاستجابة بمعلومات المُصادَق إن
    وُجد (مثل my_reactions في تفاصيل منشور المجتمع — قرار D-024).
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = _bearer_token()
        if token is not None:
            user_id = services_auth.decode_access_token(token)
            if user_id is not None:
                profile = services_auth.get_user_profile(user_id)
                if profile is not None and profile.status == "active":
                    request.user = profile
        return fn(*args, **kwargs)
    return wrapper


def require_role(*roles):
    """يتطلب دورًا واحدًا على الأقل من الأدوار المعطاة بحالة active."""
    def decorator(fn):
        @wraps(fn)
        @require_auth
        def wrapper(*args, **kwargs):
            if not services_auth.has_active_role(request.user.id, roles):
                return jsonify({"error": "غير مصرح. الصلاحية مطلوبة لهذا الإجراء."}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
