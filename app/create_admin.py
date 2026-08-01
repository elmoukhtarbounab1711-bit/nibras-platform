"""
سكربت إنشاء أول حساب مسؤول (CLI) — المرحلة 1.

الاستخدام:
    python -m app.create_admin

يقرأ من متغيرات البيئة:
    NIBRAS_ADMIN_EMAIL (إلزامي)
    NIBRAS_ADMIN_PASSWORD (إلزامي، 8 أحرف على الأقل)
    NIBRAS_ADMIN_NAME (اختياري، افتراضي "مسؤول النظام")

الدور الإداري لا يُمنح عبر التسجيل العام (§2.1) — هذا هو المسار الداخلي
الوحيد لإنشائه، بجانب app.create_user_with_role في الاختبارات/الأدوات الداخلية.
"""
import os
import sys

from .database import init_db
from .services_auth import AuthError, create_user_with_role

USAGE = (
    "يجب ضبط متغيري البيئة NIBRAS_ADMIN_EMAIL و NIBRAS_ADMIN_PASSWORD "
    "(والاسم اختياري عبر NIBRAS_ADMIN_NAME)."
)


def _print(text: str) -> None:
    # تهيئة الترميز لأن stdout قد لا يدعم UTF-8 على بعض وحدات التحكم
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(text)


def create_admin_account() -> str:
    email = os.environ.get("NIBRAS_ADMIN_EMAIL", "").strip().lower()
    password = os.environ.get("NIBRAS_ADMIN_PASSWORD", "")
    name = os.environ.get("NIBRAS_ADMIN_NAME", "").strip() or "مسؤول النظام"
    if not email or not password:
        raise AuthError(USAGE, 400)
    profile = create_user_with_role(
        email=email, password=password, full_name=name,
        role_code="admin", role_status="active", user_status="active",
    )
    return profile.email


def main() -> int:
    init_db()
    try:
        email = create_admin_account()
    except AuthError as exc:
        _print(f"خطأ: {exc.message}")
        return 1
    _print(f"تم إنشاء حساب المسؤول بنجاح: {email}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
