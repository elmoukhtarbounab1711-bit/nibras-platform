"""
اختبارات نقاط المصادقة (API) — المرحلة 1.

تغطي التسجيل، الدخول، تجديد التوكن، تسجيل الخروج، استعادة كلمة المرور،
ملف المستخدم، حماية مسارات require_role (بما فيها النقاط الإدارية المنقولة
من X-Admin-Key إلى Bearer JWT)، ورسالة الدخول العامة الموحدة.
"""
from datetime import timedelta

import pytest

from app import services_auth
from app.routes.auth import _attempts

PASSWORD = "test-password-123"


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    """تطهير حد معدل الطلبات بين الاختبارات (حالة في الذاكرة)."""
    _attempts.clear()
    yield
    _attempts.clear()


def _register(client, email="citizen@example.com", role="citizen", full_name="مواطن اختبار"):
    return client.post(
        "/api/auth/register",
        json={"email": email, "password": PASSWORD, "full_name": full_name, "role": role},
    )


def _login(client, email="citizen@example.com", password=PASSWORD):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def _make_admin_token(client):
    admin = services_auth.create_user_with_role(
        email="admin@nibras.test", password=PASSWORD, full_name="مسؤول",
        role_code="admin", role_status="active", user_status="active",
    )
    return services_auth.create_access_token(admin.id)[0]


def test_register_returns_tokens_and_profile(client):
    resp = _register(client)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["user"]["email"] == "citizen@example.com"
    assert data["user"]["roles"] == ["citizen"]


def test_register_rejects_admin_role(client):
    resp = _register(client, email="hacker@example.com", role="admin")
    assert resp.status_code == 403
    assert "مسؤول" in resp.get_json()["error"]


def test_register_duplicate_email(client):
    _register(client)
    resp = _register(client)
    assert resp.status_code == 409


def test_login_returns_tokens(client):
    _register(client)
    resp = _login(client)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["access_token"] and data["refresh_token"]
    assert data["user"]["roles"] == ["citizen"]


def test_login_generic_error_message(client):
    _register(client)
    resp = _login(client, password="totally-wrong-password")
    assert resp.status_code == 401
    assert resp.get_json()["error"] == "بيانات الدخول غير صحيحة"
    # نفس الرسالة لعنوان غير مسجل (لا نكشف سبب الفشل)
    resp2 = _login(client, email="unknown@example.com")
    assert resp2.status_code == 401
    assert resp2.get_json()["error"] == "بيانات الدخول غير صحيحة"


def test_me_requires_auth(client):
    assert client.get("/api/auth/me").status_code == 401
    _register(client)
    token = _login(client).get_json()["access_token"]
    resp = client.get("/api/auth/me", headers=_auth_headers(token))
    assert resp.status_code == 200
    assert resp.get_json()["user"]["email"] == "citizen@example.com"


def test_refresh_rotates_token(client):
    _register(client)
    refresh_token = _login(client).get_json()["refresh_token"]
    resp = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    new_refresh = resp.get_json()["refresh_token"]
    assert new_refresh != refresh_token
    # القديم مرفوض بعد الدوران
    resp2 = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert resp2.status_code == 401
    # الجديد مقبول
    assert client.post("/api/auth/refresh", json={"refresh_token": new_refresh}).status_code == 200


def test_refresh_with_invalid_token(client):
    resp = client.post("/api/auth/refresh", json={"refresh_token": "garbage"})
    assert resp.status_code == 401


def test_logout_revokes_refresh_token(client):
    _register(client)
    data = _login(client).get_json()
    token, refresh_token = data["access_token"], data["refresh_token"]
    resp = client.post("/api/auth/logout", json={"refresh_token": refresh_token}, headers=_auth_headers(token))
    assert resp.status_code == 200
    assert client.post("/api/auth/refresh", json={"refresh_token": refresh_token}).status_code == 401


def test_password_reset_request_and_confirm(client):
    _register(client)
    resp = client.post("/api/auth/password-reset/request", json={"email": "citizen@example.com"})
    assert resp.status_code == 202
    # نُنشئ توكن استعادة صريحًا للاختبار (البث الفعلي يمر عبر المريلر)
    profile = services_auth.get_user_by_email("citizen@example.com")
    token = services_auth.generate_random_token()
    with services_auth.db_session() as conn:
        conn.execute(
            "INSERT INTO password_reset_tokens (token_hash, user_id, expires_at) VALUES (?,?,?)",
            (
                services_auth.hash_token(token),
                profile.id,
                (services_auth._now() + timedelta(hours=1)).isoformat(),
            ),
        )
    resp = client.post(
        "/api/auth/password-reset/confirm",
        json={"token": token, "new_password": "brand-new-password-1"},
    )
    assert resp.status_code == 200
    # الدخول بكلمة المرور الجديدة
    assert _login(client, password="brand-new-password-1").status_code == 200


def test_password_reset_confirm_invalid_token(client):
    resp = client.post(
        "/api/auth/password-reset/confirm",
        json={"token": "not-a-real-token", "new_password": "some-new-password-1"},
    )
    assert resp.status_code == 400


def test_password_reset_request_does_not_reveal_email(client):
    resp = client.post("/api/auth/password-reset/request", json={"email": "ghost@example.com"})
    assert resp.status_code == 202


def test_rate_limit_on_login(client):
    for _ in range(5):
        _login(client, password="wrong")
    resp = _login(client, password="wrong")
    assert resp.status_code == 429


def test_admin_endpoint_requires_admin_role(client):
    # بدون توكن
    assert client.post("/api/admin/texts", json={}).status_code == 401
    # مستخدم عادي
    _register(client)
    token = _login(client).get_json()["access_token"]
    resp = client.post("/api/admin/texts", json={}, headers=_auth_headers(token))
    assert resp.status_code == 403
    # مسؤول
    admin_token = _make_admin_token(client)
    resp = client.post("/api/admin/texts", json={}, headers=_auth_headers(admin_token))
    assert resp.status_code == 400  # الحقول الناقصة — وصلنا لطبقة التحقق، المصادقة نجحت


def test_admin_can_create_text_and_article(client):
    admin_token = _make_admin_token(client)
    text = client.post(
        "/api/admin/texts",
        json={"category_id": 1, "type": "code", "title": "نص اختبار إداري"},
        headers=_auth_headers(admin_token),
    )
    assert text.status_code == 201
    text_id = text.get_json()["id"]
    article = client.post(
        f"/api/admin/texts/{text_id}/articles",
        json={"number": "1", "label": "المادة 1", "content": "نص المادة"},
        headers=_auth_headers(admin_token),
    )
    assert article.status_code == 201


def test_old_admin_key_header_is_rejected(client):
    resp = client.post(
        "/api/admin/texts", json={}, headers={"X-Admin-Key": "nibras-dev-key"}
    )
    assert resp.status_code == 401


def test_register_validation_returns_400(client):
    resp = client.post(
        "/api/auth/register",
        json={"email": "bad", "password": "short", "full_name": "x", "role": "citizen"},
    )
    assert resp.status_code == 400
    assert "error" in resp.get_json()
    # دور غير معروف
    resp = client.post(
        "/api/auth/register",
        json={"email": "x@example.com", "password": "valid-password-1",
              "full_name": "x", "role": "pharaoh"},
    )
    assert resp.status_code == 400


def test_suspended_user_me_rejected(client):
    _register(client)
    token = _login(client).get_json()["access_token"]
    profile = services_auth.get_user_by_email("citizen@example.com")
    with services_auth.db_session() as conn:
        conn.execute("UPDATE users SET status = 'suspended' WHERE id = ?", (profile.id,))
    resp = client.get("/api/auth/me", headers=_auth_headers(token))
    assert resp.status_code == 401


def test_register_rate_limited(client):
    for i in range(5):
        client.post(
            "/api/auth/register",
            json={"email": f"r{i}@example.com", "password": "valid-password-1",
                  "full_name": "x", "role": "citizen"},
        )
    resp = client.post(
        "/api/auth/register",
        json={"email": "last@example.com", "password": "valid-password-1",
              "full_name": "x", "role": "citizen"},
    )
    assert resp.status_code == 429
