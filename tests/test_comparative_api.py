"""
اختبارات القانون المقارن (API) — المرحلة 20 (قرار D-038).

تصفح عام للولايات والدراسات المنشورة، إنشاء/إدارة دراسات ومقارنات
بمصادقة، نفاذ إداري للحالة والحالات/معرّفات الولايات.
"""
from app import services_auth
from app.database import db_session

PASSWORD = "test-password-123"


def _headers(user):
    token = services_auth.create_access_token(user.id)[0]
    return {"Authorization": f"Bearer {token}"}


def _user(email, role_code="citizen"):
    return services_auth.create_user_with_role(
        email=email, password=PASSWORD, full_name="مقارن قانوني",
        role_code=role_code, role_status="active", user_status="active",
    )


def _admin():
    return _user("admin-cmp@nibras.test", "admin")


def _jurisdiction(client, slug="france"):
    resp = client.get("/api/comparative/jurisdictions")
    assert resp.status_code == 200
    return next(
        j["id"] for j in resp.get_json()["jurisdictions"]
        if j["slug"] == slug
    )


def _article_id():
    with db_session() as conn:
        return conn.execute("SELECT id FROM articles LIMIT 1").fetchone()["id"]


def _create_study(client, headers, title="دراسة"):
    resp = client.post("/api/comparative/studies",
                       json={"title": title}, headers=headers)
    assert resp.status_code == 201
    return resp.get_json()["id"]


def test_public_jurisdictions(client):
    resp = client.get("/api/comparative/jurisdictions")
    assert resp.status_code == 200
    data = resp.get_json()["jurisdictions"]
    assert len(data) >= 7
    assert all("name" in j and "slug" in j for j in data)


def test_public_studies_only_published(client):
    h = _headers(_user("owner@nibras.test"))
    study_id = _create_study(client, h)
    assert client.get("/api/comparative/studies").get_json()["count"] == 0
    assert client.get(f"/api/comparative/studies/{study_id}").status_code == 404

    admin_h = _headers(_admin())
    resp = client.put(
        f"/api/admin/comparative/studies/{study_id}/status",
        json={"status": "published"}, headers=admin_h,
    )
    assert resp.status_code == 200
    listing = client.get("/api/comparative/studies").get_json()
    assert listing["count"] == 1
    detail = client.get(f"/api/comparative/studies/{study_id}").get_json()
    assert detail["status"] == "published"


def test_create_study_requires_auth(client):
    assert client.post("/api/comparative/studies",
                       json={"title": "x"}).status_code == 401
    assert client.get("/api/comparative/my").status_code == 401


def test_owner_manages_own_study(client):
    h = _headers(_user("owner@nibras.test"))
    other_h = _headers(_user("other@nibras.test"))
    study_id = _create_study(client, h, "دراسة الملكية")
    resp = client.put(f"/api/comparative/studies/{study_id}",
                      json={"title": "دراسة الملكية (محدثة)"}, headers=h)
    assert resp.status_code == 200
    assert client.put(f"/api/comparative/studies/{study_id}",
                      json={"title": "اختراق"}, headers=other_h).status_code == 403
    assert client.delete(f"/api/comparative/studies/{study_id}",
                         headers=other_h).status_code == 403
    assert client.delete(f"/api/comparative/studies/{study_id}",
                         headers=h).status_code == 200


def test_add_entry_api(client):
    h = _headers(_user("owner@nibras.test"))
    study_id = _create_study(client, h)
    jid = _jurisdiction(client)
    aid = _article_id()
    resp = client.post(
        f"/api/comparative/studies/{study_id}/entries",
        json={"jurisdiction_id": jid, "article_id": aid,
              "note": "مقارنة"}, headers=h,
    )
    assert resp.status_code == 201
    entry_id = resp.get_json()["id"]
    detail = client.get(f"/api/comparative/studies/{study_id}",
                        headers=h).get_json()
    assert len(detail["entries"]) == 1
    assert detail["entries"][0]["article_id"] == aid
    resp = client.put(f"/api/comparative/entries/{entry_id}",
                      json={"note": "معدلة"}, headers=h)
    assert resp.status_code == 200
    assert client.delete(f"/api/comparative/entries/{entry_id}",
                         headers=h).status_code == 200


def test_entry_validation_api(client):
    h = _headers(_user("owner@nibras.test"))
    study_id = _create_study(client, h)
    assert client.post(
        f"/api/comparative/studies/{study_id}/entries",
        json={"jurisdiction_id": 1, "article_id": 99999}, headers=h,
    ).status_code == 400
    assert client.post(
        f"/api/comparative/studies/{study_id}/entries",
        json={"jurisdiction_id": 99999}, headers=h,
    ).status_code == 400


def test_admin_jurisdictions(client):
    admin_h = _headers(_admin())
    resp = client.post(
        "/api/admin/comparative/jurisdictions",
        json={"slug": "algeria", "name": "الجزائر"}, headers=admin_h,
    )
    assert resp.status_code == 201
    listing = client.get("/api/admin/comparative/jurisdictions",
                         headers=admin_h).get_json()["jurisdictions"]
    assert any(j["slug"] == "algeria" for j in listing)
    jid = next(j["id"] for j in listing if j["slug"] == "algeria")
    resp = client.put(f"/api/admin/comparative/jurisdictions/{jid}",
                      json={"name": "جمهورية الجزائر"}, headers=admin_h)
    assert resp.status_code == 200
    assert client.delete(f"/api/admin/comparative/jurisdictions/{jid}",
                         headers=admin_h).status_code == 200


def test_admin_routes_require_admin(client):
    assert client.get(
        "/api/admin/comparative/studies"
    ).status_code == 401
    h = _headers(_user("cit@nibras.test"))
    assert client.get("/api/admin/comparative/studies",
                      headers=h).status_code == 403
    assert client.post("/api/admin/comparative/jurisdictions",
                       json={"slug": "x", "name": "X"}, headers=h).status_code == 403


def test_admin_study_status_and_list(client):
    admin_h = _headers(_admin())
    owner_h = _headers(_user("owner@nibras.test"))
    study_id = _create_study(client, owner_h)
    listing = client.get("/api/admin/comparative/studies",
                         headers=admin_h).get_json()["studies"]
    assert any(s["id"] == study_id for s in listing)
    resp = client.put(
        f"/api/admin/comparative/studies/{study_id}/status",
        json={"status": "published"}, headers=admin_h,
    )
    assert resp.status_code == 200
    resp = client.put(
        f"/api/admin/comparative/studies/{study_id}/status",
        json={"status": "bogus"}, headers=admin_h,
    )
    assert resp.status_code == 400
    filtered = client.get(
        "/api/admin/comparative/studies?status=published", headers=admin_h,
    ).get_json()["studies"]
    assert any(s["id"] == study_id for s in filtered)