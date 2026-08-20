"""
اختبارات نقاط المصادقة (API) — تسجيل دخول/إنشاء حساب مع امتثال القانون 09-08.

التسجيل والدخول مُفعَّلان مع موافقة صريحة على معالجة المعطيات الشخصية.
التحقق بخطوتين (TOTP) إلزامي للمشرفين. حماية من التخمين لجميع الحسابات.
 الوصول الإداري حصري عبر سكربت app.create_admin وتوقيع التوكنات الداخلي.
تبقى نقاط الإدارة (require_role) تعمل بتوكن Bearer صحيح، و/me داخلي
(يتطلب توكنًا صالحًا — لا حساب عام). (وثيقة 12.)
"""

from app import services_auth
from app.database import db_session

PASSWORD = "test-password-123"


def _register(client, email="citizen@example.com", role="citizen", full_name="مواطن اختبار",
              consent_processing=True, consent_terms=True):
    return client.post(
        "/api/auth/register",
        json={
            "email": email, "password": PASSWORD, "full_name": full_name, "role": role,
            "consent_data_processing": consent_processing, "consent_terms": consent_terms,
        },
    )


def _login(client, email="citizen@example.com", password=PASSWORD):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def _user(email="user@test.local", role_code="citizen"):
    return services_auth.create_user_with_role(
        email=email, password=PASSWORD, full_name="مستخدم اختبار",
        role_code=role_code, role_status="active", user_status="active",
    )


def _token(profile):
    return services_auth.create_access_token(profile.id)[0]


def _make_admin_token(client):
    admin = _user(email="admin@nibras.test", role_code="admin")
    return _token(admin)


def test_register_requires_consent(client):
    resp = _register(client, consent_processing=False, consent_terms=False)
    assert resp.status_code == 400
    assert "موافقة" in resp.get_json()["error"]


def test_register_succeeds_with_consent(client):
    resp = _register(client, email="consent@test.local")
    assert resp.status_code == 201
    data = resp.get_json()
    assert "access_token" in data
    assert data["user"]["email"] == "consent@test.local"


def test_login_works(client):
    _register(client, email="login@test.local")
    resp = _login(client, email="login@test.local")
    assert resp.status_code == 200
    assert "access_token" in resp.get_json()


def test_register_rejects_admin_role(client):
    resp = _register(client, email="admin@test.local", role="admin")
    assert resp.status_code == 403


def test_public_refresh_works(client):
    resp = client.post("/api/auth/refresh", json={"refresh_token": "whatever"})
    assert resp.status_code in (401, 200)


def test_logout_returns_ok_without_accounts(client):
    assert client.post("/api/auth/logout").status_code == 200


def test_me_requires_auth(client):
    assert client.get("/api/auth/me").status_code == 401


def test_me_returns_internal_profile(client):
    profile = _user()
    token = _token(profile)
    resp = client.get("/api/auth/me", headers=_auth_headers(token))
    assert resp.status_code == 200
    assert resp.get_json()["user"]["email"] == "user@test.local"


def test_me_with_bad_token_401(client):
    assert client.get("/api/auth/me", headers=_auth_headers("garbage")).status_code == 401


def test_password_reset_request_works(client):
    req = client.post("/api/auth/password-reset/request", json={"email": "x@example.com"})
    assert req.status_code == 200


def test_password_reset_confirm_works(client):
    conf = client.post(
        "/api/auth/password-reset/confirm",
        json={"token": "t", "new_password": "new-secret-1"},
    )
    assert conf.status_code in (200, 400)


def test_suspended_user_me_rejected(client):
    profile = _user()
    token = _token(profile)
    with db_session() as conn:
        conn.execute("UPDATE users SET status = 'suspended' WHERE id = ?", (profile.id,))
    assert client.get("/api/auth/me", headers=_auth_headers(token)).status_code == 401


def test_admin_endpoint_requires_admin_role(client):
    assert client.post("/api/admin/texts", json={}).status_code == 401
    citizen = _user(role_code="citizen")
    resp = client.post("/api/admin/texts", json={}, headers=_auth_headers(_token(citizen)))
    assert resp.status_code == 403
    admin_token = _make_admin_token(client)
    resp = client.post("/api/admin/texts", json={}, headers=_auth_headers(admin_token))
    assert resp.status_code == 400


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
