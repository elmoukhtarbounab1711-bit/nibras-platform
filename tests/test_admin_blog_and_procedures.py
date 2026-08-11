"""
اختبارات نقاط الإدارة للوحدات الإضافية (مرحلة الواجهة).

تغطي: رفع/حذف ملف PDF للقوانين (مع رفض الصيغ الأخرى)، إدارة حالة مقالات
بوابة المقالات، معالجة بلاغات المقالات، و CRUD المساطر القانونية مع
الخطوات (steps) والأسئلة الشائعة (faq) ووصف الرسوم (fees).
"""
from io import BytesIO

import pytest

from app import services_auth

PASSWORD = "test-password-123"


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin_token():
    admin = services_auth.create_user_with_role(
        email="admin@panel.test", password=PASSWORD, full_name="مسؤول اللوحة",
        role_code="admin", role_status="active", user_status="active",
    )
    return services_auth.create_access_token(admin.id)[0]


def _citizen_token(client):
    citizen = services_auth.create_user_with_role(
        email="citizen@panel.test", password=PASSWORD,
        full_name="مواطن", role_code="citizen",
        role_status="active", user_status="active",
    )
    return services_auth.create_access_token(citizen.id)[0]


def _publish_article(client, token):
    resp = client.post(
        "/api/blog/articles",
        json={"title": "مقال لوحة", "body": "جسم المقال", "summary": "ملخص",
              "keywords": "قانون"},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 201
    return resp.get_json()["id"]


# ---------------------------------------------------------------------------
# ملف PDF للقوانين
# ---------------------------------------------------------------------------

def test_text_pdf_requires_admin(client, admin_token):
    resp = client.post(
        "/api/admin/texts/1/pdf",
        data={"file": (BytesIO(b"x"), "law.pdf")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 401
    resp2 = client.post(
        "/api/admin/texts/1/pdf",
        data={"file": (BytesIO(b"x"), "law.pdf")},
        content_type="multipart/form-data",
        headers=_auth_headers(admin_token),
    )
    assert resp2.status_code in (200, 400, 404)


def test_text_pdf_upload_then_serve_then_delete(client, admin_token):
    pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"
    resp = client.post(
        "/api/admin/texts/1/pdf",
        data={"file": (BytesIO(pdf_bytes), "القانون.pdf")},
        content_type="multipart/form-data",
        headers=_auth_headers(admin_token),
    )
    assert resp.status_code == 200
    serve = client.get("/api/texts/1/pdf")
    assert serve.status_code == 200
    assert serve.headers.get("Content-Type", "").startswith("application/pdf")
    assert pdf_bytes in serve.data
    # حذف الملف المرفوع → العودة إلى الملف المولَّد تلقائيًا
    resp = client.delete(
        "/api/admin/texts/1/pdf", headers=_auth_headers(admin_token)
    )
    assert resp.status_code == 200
    assert client.get("/api/texts/1/pdf").status_code == 200


def test_text_pdf_upload_rejects_non_pdf(client, admin_token):
    resp = client.post(
        "/api/admin/texts/1/pdf",
        data={"file": (BytesIO(b"plain"), "note.txt")},
        content_type="multipart/form-data",
        headers=_auth_headers(admin_token),
    )
    assert resp.status_code == 400
    assert "pdf" in resp.get_json()["error"]


def test_text_pdf_delete_without_upload(client, admin_token):
    resp = client.delete(
        "/api/admin/texts/1/pdf", headers=_auth_headers(admin_token)
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# إدارة بوابة المقالات
# ---------------------------------------------------------------------------

def test_blog_admin_list_requires_admin(client, admin_token):
    assert client.get("/api/admin/blog/articles").status_code == 401
    resp = client.get("/api/admin/blog/articles", headers=_auth_headers(admin_token))
    assert resp.status_code == 200
    assert "articles" in resp.get_json()


def test_blog_admin_publish_flow(client, admin_token):
    author = _citizen_token(client)
    article_id = _publish_article(client, author)
    # مؤلِّف عادي يبدأ pending
    admin_list = client.get(
        "/api/admin/blog/articles", headers=_auth_headers(admin_token)
    ).get_json()["articles"]
    entry = next(a for a in admin_list if a["id"] == article_id)
    assert entry["status"] == "pending"
    # نشر إداري → يظهر للعموم
    resp = client.put(
        f"/api/admin/blog/articles/{article_id}/status",
        json={"status": "published"},
        headers=_auth_headers(admin_token),
    )
    assert resp.status_code == 200
    titles = [a["title"] for a in client.get("/api/blog/articles").get_json()["articles"]]
    assert "مقال لوحة" in titles


def test_blog_admin_set_status_invalid(client, admin_token):
    article_id = _publish_article(client, admin_token)
    resp = client.put(
        f"/api/admin/blog/articles/{article_id}/status",
        json={"status": "banana"},
        headers=_auth_headers(admin_token),
    )
    assert resp.status_code == 400


def test_blog_report_action_hides_article(client, admin_token):
    author = _citizen_token(client)
    article_id = _publish_article(client, author)
    client.put(
        f"/api/admin/blog/articles/{article_id}/status",
        json={"status": "published"},
        headers=_auth_headers(admin_token),
    )
    # نفس المستخدم يكفي كمبلِّغ (لا يمنع)
    resp = client.post(
        f"/api/blog/articles/{article_id}/report",
        json={"reason": "محتوى غير لائق"},
        headers=_auth_headers(author),
    )
    assert resp.status_code == 201
    reports = client.get(
        "/api/admin/blog/reports", headers=_auth_headers(admin_token)
    ).get_json()["reports"]
    report = reports[0]
    resp = client.post(
        f"/api/admin/blog/reports/{report['id']}/action",
        json={"decision": "actioned"},
        headers=_auth_headers(admin_token),
    )
    assert resp.status_code == 200
    # المقال أصبح مخفيًا عن العموم
    assert client.get("/api/blog/articles").get_json()["articles"] == []
    hidden = client.get(
        f"/api/blog/articles/{article_id}", headers=_auth_headers(admin_token)
    ).get_json()
    assert hidden["status"] == "hidden"


# ---------------------------------------------------------------------------
# إدارة المساطر القانونية
# ---------------------------------------------------------------------------

def test_procedure_crud(client, admin_token):
    create = client.post(
        "/api/admin/procedures",
        json={
            "slug": "rent-contract",
            "title": "تحرير عقد كراء سكني",
            "category": "العقارات",
            "responsible_authority": "العدل المنفذ / الموثق",
            "typical_timeframe": "24 ساعة",
            "fees": "500 درهم كحد أقصى لموثق العدول",
            "steps": [
                {"title": "جمع الوثائق",
                 "description": "الهوية وعقد الكراء القديم",
                 "required_documents": "بطاقة التعريف، العقد السابق"},
                {"title": "التوثيق",
                 "description": "التحرير لدى عدلين.",
                 "required_documents": "وثائق المطابقة"},
            ],
            "faq": [{"q": "هل يمكن تجديد العقد؟", "a": "نعم باتفاق الطرفين."}],
        },
        headers=_auth_headers(admin_token),
    )
    assert create.status_code == 201
    proc_id = create.get_json()["id"]

    listing = client.get(
        "/api/admin/procedures", headers=_auth_headers(admin_token)
    ).get_json()["procedures"]
    entry = next(p for p in listing if p["id"] == proc_id)
    assert entry["fees"] == "500 درهم كحد أقصى لموثق العدول"
    assert entry["step_count"] == 2
    # يظهر للعموم في قائمة المساطر العامة مع الرسوم
    public_list = client.get("/api/procedures").get_json()
    assert any(p["id"] == proc_id for p in public_list)

    update = client.put(
        f"/api/admin/procedures/{proc_id}",
        json={"title": "تحرير عقد كراء سكني (معدل)",
              "fees": "600 درهم"},
        headers=_auth_headers(admin_token),
    )
    assert update.status_code == 200

    delete = client.delete(
        f"/api/admin/procedures/{proc_id}", headers=_auth_headers(admin_token)
    )
    assert delete.status_code == 200
    remaining = client.get(
        "/api/admin/procedures", headers=_auth_headers(admin_token)
    ).get_json()["procedures"]
    assert all(p["id"] != proc_id for p in remaining)


def test_procedure_create_requires_slug_and_steps(client, admin_token):
    resp = client.post(
        "/api/admin/procedures",
        json={"title": "بلا خطوات"},
        headers=_auth_headers(admin_token),
    )
    assert resp.status_code == 400
    resp = client.post(
        "/api/admin/procedures",
        json={"slug": "dup", "title": "بلا خطوات", "steps": []},
        headers=_auth_headers(admin_token),
    )
    assert resp.status_code == 400


def test_procedure_duplicate_slug(client, admin_token):
    payload = {
        "slug": "duplicate-proc",
        "title": "مسطرة مكررة",
        "steps": [{"title": "خطوة", "description": "وصف"}],
    }
    first = client.post(
        "/api/admin/procedures", json=payload, headers=_auth_headers(admin_token)
    )
    assert first.status_code == 201
    second = client.post(
        "/api/admin/procedures", json=payload, headers=_auth_headers(admin_token)
    )
    assert second.status_code == 400
