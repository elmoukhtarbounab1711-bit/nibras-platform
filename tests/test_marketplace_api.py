"""
اختبارات سوق القوالب (API) — المرحلة 7 (قرار D-025).

التصفح والتفصيل عامان بلا storage_key، إنشاء/تحديث/حذف القوالب والفئات
إداري (دور admin) مع رفع/تنزيل الملف، ومسار الشراء غير متاح بعد (مؤجَّل
لحسم بوابة الدفع — BRD §5).
"""
import io

import pytest

from app import config, services_auth

PASSWORD = "test-password-123"


@pytest.fixture(autouse=True)
def _isolate_uploads(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "UPLOAD_DIR", str(tmp_path / "uploads"))
    yield


def _headers(user):
    token = services_auth.create_access_token(user.id)[0]
    return {"Authorization": f"Bearer {token}"}


def _user(email, role_code="citizen"):
    return services_auth.create_user_with_role(
        email=email, password=PASSWORD, full_name="مستخدم سوق",
        role_code=role_code, role_status="active", user_status="active",
    )


def _admin():
    return _user("admin-marketplace@nibras.test", "admin")


def _template_data(**overrides):
    data = {
        "category_id": "1",
        "title": "نموذج عقد إيجار",
        "description": "عقد إيجار جاهز للتعبئة",
        "price_cents": "1500",
    }
    data.update(overrides)
    return data


def _create_template(client, headers, content=b"%PDF-1.4 template",
                     name="contract.pdf", **overrides):
    return client.post(
        "/api/admin/marketplace/templates",
        data={**_template_data(**overrides),
              "file": (io.BytesIO(content), name)},
        headers=headers,
        content_type="multipart/form-data",
    )


def test_categories_public_and_seeded(client):
    resp = client.get("/api/marketplace/categories")
    assert resp.status_code == 200
    items = resp.get_json()
    assert len(items) == 6
    assert items[0]["slug"] == "dostouri"
    assert all("template_count" in i for i in items)


def test_templates_list_empty(client):
    assert client.get("/api/marketplace/templates").get_json() == []


def test_marketplace_requires_admin(client):
    citizen_h = _headers(_user("cit@nibras.test"))
    assert client.post("/api/admin/marketplace/templates", data={},
                       headers=citizen_h,
                       content_type="multipart/form-data").status_code == 403
    assert client.post("/api/admin/marketplace/templates", data={},
                       content_type="multipart/form-data").status_code == 401
    assert client.get("/api/admin/marketplace/templates",
                      headers=citizen_h).status_code == 403
    assert client.delete("/api/admin/marketplace/templates/1",
                         headers=citizen_h).status_code == 403


def test_create_and_browse_template(client):
    admin_h = _headers(_admin())
    resp = _create_template(client, admin_h)
    assert resp.status_code == 201
    template_id = resp.get_json()["id"]

    listed = client.get("/api/marketplace/templates").get_json()
    assert len(listed) == 1
    item = listed[0]
    assert item["title"] == "نموذج عقد إيجار"
    assert item["price_cents"] == 1500
    assert "storage_key" not in item

    detail = client.get(f"/api/marketplace/templates/{template_id}").get_json()
    assert detail["description"] == "عقد إيجار جاهز للتعبئة"
    assert "storage_key" not in detail

    cats = client.get("/api/marketplace/categories").get_json()
    assert cats[0]["template_count"] == 1


def test_create_template_validation(client):
    admin_h = _headers(_admin())
    assert _create_template(client, admin_h, title=" ").status_code == 400
    assert _create_template(client, admin_h, price_cents="-1").status_code == 400
    assert _create_template(client, admin_h, price_cents="abc").status_code == 400
    assert _create_template(client, admin_h, category_id="999").status_code == 400
    assert _create_template(client, admin_h, name="doc.exe").status_code == 400
    assert client.post(
        "/api/admin/marketplace/templates",
        data=dict(_template_data()),
        headers=admin_h,
        content_type="multipart/form-data",
    ).status_code == 400


def test_create_template_too_large(client, monkeypatch):
    monkeypatch.setattr(config, "MAX_UPLOAD_BYTES", 100)
    resp = _create_template(client, _headers(_admin()), content=b"x" * 200)
    assert resp.status_code == 400


def test_update_template_and_replace_file(client):
    admin_h = _headers(_admin())
    template_id = _create_template(client, admin_h).get_json()["id"]

    resp = client.put(f"/api/admin/marketplace/templates/{template_id}",
                      json={"price_cents": 2000, "title": "نموذج محدث"},
                      headers=admin_h)
    assert resp.status_code == 200
    item = client.get(f"/api/marketplace/templates/{template_id}").get_json()
    assert item["price_cents"] == 2000 and item["title"] == "نموذج محدث"

    resp = client.put(f"/api/admin/marketplace/templates/{template_id}",
                      data={"file": (io.BytesIO(b"%PDF-1.4 new"), "v2.pdf")},
                      headers=admin_h, content_type="multipart/form-data")
    assert resp.status_code == 200

    assert client.put(f"/api/admin/marketplace/templates/{template_id}",
                      json={"title": "x"},
                      headers=_headers(_user("c2@nibras.test"))).status_code == 403
    assert client.put("/api/admin/marketplace/templates/999",
                      json={"title": "x"}, headers=admin_h).status_code == 404
    assert client.put(f"/api/admin/marketplace/templates/{template_id}",
                      json={}, headers=admin_h).status_code == 400


def test_admin_list_and_file_download(client):
    admin_h = _headers(_admin())
    content = b"%PDF-1.4 fake template"
    template_id = _create_template(client, admin_h, content=content,
                                   name="template.pdf").get_json()["id"]

    listed = client.get("/api/admin/marketplace/templates",
                        headers=admin_h).get_json()["templates"]
    assert len(listed) == 1
    assert listed[0]["has_file"] is True
    assert "storage_key" not in listed[0]

    assert client.get(f"/api/admin/marketplace/templates/{template_id}/file",
                      headers=_headers(_user("c3@nibras.test"))).status_code == 403
    dl = client.get(f"/api/admin/marketplace/templates/{template_id}/file",
                    headers=admin_h)
    assert dl.status_code == 200
    assert dl.data == content
    assert dl.mimetype == "application/pdf"
    assert client.get(f"/api/marketplace/templates/{template_id}/file").status_code == 404


def test_delete_template_hides_from_catalog(client):
    admin_h = _headers(_admin())
    template_id = _create_template(client, admin_h).get_json()["id"]
    assert client.delete(f"/api/admin/marketplace/templates/{template_id}",
                         headers=admin_h).status_code == 200
    assert client.get(f"/api/marketplace/templates/{template_id}").status_code == 404
    assert client.get("/api/marketplace/templates").get_json() == []
    assert client.delete(f"/api/admin/marketplace/templates/{template_id}",
                         headers=admin_h).status_code == 404


def test_category_management(client):
    admin_h = _headers(_admin())
    resp = client.post("/api/admin/marketplace/categories",
                       json={"slug": "aoula", "name": "قانون الأحوال الشخصية"},
                       headers=admin_h)
    assert resp.status_code == 201
    cat_id = resp.get_json()["id"]

    assert client.put(f"/api/admin/marketplace/categories/{cat_id}",
                      json={"name": "الأحوال الشخصية"},
                      headers=admin_h).status_code == 200
    assert client.delete(f"/api/admin/marketplace/categories/{cat_id}",
                         headers=admin_h).status_code == 200

    assert client.post("/api/admin/marketplace/categories",
                       json={"slug": "aoula", "name": "x"},
                       headers=admin_h).status_code == 201
    assert client.post("/api/admin/marketplace/categories",
                       json={"slug": "aoula", "name": "y"},
                       headers=admin_h).status_code == 400
    assert client.post("/api/admin/marketplace/categories",
                       json={"slug": "", "name": "z"},
                       headers=admin_h).status_code == 400
    assert client.post("/api/admin/marketplace/categories",
                       json={"slug": "x", "name": ""},
                       headers=admin_h).status_code == 400
    assert client.post("/api/admin/marketplace/categories",
                       json={"slug": "x", "name": "y"},
                       headers=_headers(_user("c4@nibras.test"))).status_code == 403


def test_delete_category_with_templates_blocked(client):
    admin_h = _headers(_admin())
    _create_template(client, admin_h, category_id="1")
    assert client.delete("/api/admin/marketplace/categories/1",
                         headers=admin_h).status_code == 409
    assert client.delete("/api/admin/marketplace/categories/999",
                         headers=admin_h).status_code == 404


def test_purchase_endpoint_not_implemented(client):
    admin_h = _headers(_admin())
    template_id = _create_template(client, admin_h).get_json()["id"]
    assert client.post(f"/api/marketplace/templates/{template_id}/purchase",
                       headers=_headers(_user("buyer@nibras.test"))).status_code == 404


def test_browse_filters_and_pagination(client):
    admin_h = _headers(_admin())
    _create_template(client, admin_h, title="عقد إيجار", category_id="1")
    _create_template(client, admin_h, title="عقد عمل", category_id="5")
    _create_template(client, admin_h, title="عقد زواج", category_id="3")

    assert len(client.get("/api/marketplace/templates").get_json()) == 3
    by_cat = client.get("/api/marketplace/templates",
                        query_string={"category": 1}).get_json()
    assert len(by_cat) == 1 and by_cat[0]["title"] == "عقد إيجار"
    search = client.get("/api/marketplace/templates",
                        query_string={"q": "عقد عمل"}).get_json()
    assert len(search) == 1 and search[0]["title"] == "عقد عمل"
    page = client.get("/api/marketplace/templates",
                      query_string={"limit": 2, "offset": 2}).get_json()
    assert len(page) == 1
    assert client.get("/api/marketplace/templates",
                      query_string={"category": "abc"}).status_code == 400
