"""
اختبارات طبقة خدمة المصادقة (services_auth) — المرحلة 1.

تغطي إنشاء المستخدمين، التحقق من كلمات المرور (argon2id)، أدوار
pending_verification، رفض الدور الإداري، مصادقة الدخول، دوران توكنات
التحديث وإبطالها، واستعادة كلمة المرور.
"""
from datetime import timedelta

import pytest

from app import services_auth
from app.database import db_session
from app.services_auth import AuthError

PASSWORD = "test-password-123"


def _make_user(email="citizen@example.com", role="citizen", **kwargs):
    return services_auth.create_user(
        email=email, password=PASSWORD, full_name="مواطن اختبار", role_code=role, **kwargs
    )


def test_roles_seeded(fresh_db):
    with db_session() as conn:
        codes = {r["code"] for r in conn.execute("SELECT code FROM roles")}
    assert codes == set(services_auth.ROLE_CODES)


def test_create_user_and_verify_password(fresh_db):
    profile = _make_user()
    assert profile.roles == ["citizen"]
    with db_session() as conn:
        row = conn.execute("SELECT password_hash FROM users WHERE id = ?", (profile.id,)).fetchone()
    assert services_auth.verify_password(PASSWORD, row["password_hash"])
    assert not services_auth.verify_password("wrong-password", row["password_hash"])


def test_professional_role_starts_pending(fresh_db):
    profile = _make_user(email="lawyer@example.com", role="lawyer")
    with db_session() as conn:
        status = conn.execute(
            """SELECT role_status FROM user_roles WHERE user_id = ?
               AND role_id = (SELECT id FROM roles WHERE code = 'lawyer')""",
            (profile.id,),
        ).fetchone()["role_status"]
    assert status == "pending_verification"


def test_public_registration_rejects_admin(fresh_db):
    with pytest.raises(AuthError) as excinfo:
        _make_user(email="hacker@example.com", role="admin")
    assert excinfo.value.status_code == 403


def test_duplicate_email_rejected(fresh_db):
    _make_user(email="dup@example.com")
    with pytest.raises(AuthError) as excinfo:
        _make_user(email="dup@example.com")
    assert excinfo.value.status_code == 409


def test_invalid_password_too_short(fresh_db):
    with pytest.raises(AuthError) as excinfo:
        services_auth.create_user(
            email="short@example.com", password="short", full_name="م", role_code="citizen"
        )
    assert excinfo.value.status_code == 400


def test_authenticate_user(fresh_db):
    _make_user(email="auth@example.com")
    profile = services_auth.authenticate_user("auth@example.com", PASSWORD)
    assert profile is not None and profile.email == "auth@example.com"
    assert services_auth.authenticate_user("auth@example.com", "wrong") is None
    assert services_auth.authenticate_user("unknown@example.com", PASSWORD) is None


def test_access_token_roundtrip(fresh_db):
    profile = _make_user()
    token, _ = services_auth.create_access_token(profile.id)
    assert services_auth.decode_access_token(token) == profile.id
    assert services_auth.decode_access_token("not-a-jwt") is None


def test_refresh_token_rotation(fresh_db):
    profile = _make_user()
    token, _ = services_auth.create_refresh_token(profile.id)
    result = services_auth.rotate_refresh_token(token)
    assert result is not None
    new_token, _, user_id = result
    assert user_id == profile.id
    assert new_token != token
    # التوكن القديم لم يعد صالحًا بعد الدوران
    assert services_auth.rotate_refresh_token(token) is None
    # الجديد صالح
    assert services_auth.rotate_refresh_token(new_token) is not None


def test_revoke_refresh_token(fresh_db):
    profile = _make_user()
    token, _ = services_auth.create_refresh_token(profile.id)
    assert services_auth.revoke_refresh_token(token)
    assert services_auth.rotate_refresh_token(token) is None


def test_password_reset_flow(fresh_db):
    profile = _make_user(email="reset@example.com")
    services_auth.request_password_reset("reset@example.com")
    with db_session() as conn:
        row = conn.execute(
            "SELECT token_hash FROM password_reset_tokens WHERE user_id = ?", (profile.id,)
        ).fetchone()
    assert row is not None
    # التوكن الصريح لا يُخزَّن (فقط المجزأ)؛ نُنشئ توكنًا مباشرة لاختبار الإجراء
    token = services_auth.generate_random_token()
    with db_session() as conn:
        conn.execute(
            "INSERT INTO password_reset_tokens (token_hash, user_id, expires_at) VALUES (?,?,?)",
            (
                services_auth.hash_token(token),
                profile.id,
                (services_auth._now() + timedelta(hours=1)).isoformat(),
            ),
        )
    services_auth.reset_password_with_token(token, "new-password-456")
    # كلمة المرور الجديدة تعمل والقديمة لا
    assert services_auth.authenticate_user("reset@example.com", "new-password-456") is not None
    assert services_auth.authenticate_user("reset@example.com", PASSWORD) is None
    # التوكن لا يصلح للاستخدام مرتين
    with pytest.raises(AuthError):
        services_auth.reset_password_with_token(token, "another-password-789")


def test_password_reset_request_does_not_leak_email(fresh_db):
    # عنوان غير مسجل: لا يرفع خطأ — ينهي بهدوء بنفس السلوك
    services_auth.request_password_reset("ghost@example.com")


def test_password_reset_expired_token_rejected(fresh_db):
    profile = _make_user(email="expired@example.com")
    token = services_auth.generate_random_token()
    with db_session() as conn:
        conn.execute(
            "INSERT INTO password_reset_tokens (token_hash, user_id, expires_at) VALUES (?,?,?)",
            (
                services_auth.hash_token(token),
                profile.id,
                (services_auth._now() - timedelta(minutes=5)).isoformat(),
            ),
        )
    with pytest.raises(AuthError) as excinfo:
        services_auth.reset_password_with_token(token, "new-password-456")
    assert excinfo.value.status_code == 400
    # كلمة المرور القديمة ما زالت صالحة (التوكن المنتهي لم يغيّر شيئًا)
    assert services_auth.authenticate_user("expired@example.com", PASSWORD) is not None


def test_suspended_user_cannot_authenticate(fresh_db):
    profile = _make_user(email="suspended@example.com")
    with db_session() as conn:
        conn.execute("UPDATE users SET status = 'suspended' WHERE id = ?", (profile.id,))
    assert services_auth.authenticate_user("suspended@example.com", PASSWORD) is None


def test_password_reset_for_suspended_user_silent(fresh_db):
    profile = _make_user(email="sus-reset@example.com")
    with db_session() as conn:
        conn.execute("UPDATE users SET status = 'suspended' WHERE id = ?", (profile.id,))
    # لا يرفع خطأ ولا يُنشئ توكنًا (حماية من التعداد عبر سلوك مختلف)
    services_auth.request_password_reset("sus-reset@example.com")
    with db_session() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM password_reset_tokens WHERE user_id = ?", (profile.id,)
        ).fetchone()[0]
    assert count == 0


def test_has_active_role(fresh_db):
    profile = _make_user(role="citizen")
    assert services_auth.has_active_role(profile.id, ("citizen",))
    assert not services_auth.has_active_role(profile.id, ("admin",))
