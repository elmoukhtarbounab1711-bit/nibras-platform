"""
اختبارات محرك رفع المستندات (API) — المرحلة 10 (قرار D-028).

نقطة إدارية واحدة POST /api/admin/ingestion/import (multipart) بدور admin،
مع dry_run=1 لمعاينة التقسيم بلا كتابة، واستيعاب مُلتزَم يبني
legal_text + articles مفهرسة بحثيًا.
"""
import io

from app import services_auth
from app.database import db_session

PASSWORD = "test-password-123"


def _docx_bytes(paragraphs):
    from docx import Document

    doc = Document()
    for p in paragraphs:
        doc.add_paragraph(p)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _headers(user):
    token = services_auth.create_access_token(user.id)[0]
    return {"Authorization": f"Bearer {token}"}


def _user(email, role_code="citizen"):
    return services_auth.create_user_with_role(
        email=email, password=PASSWORD, full_name="مستخدم استيعاب",
        role_code=role_code, role_status="active", user_status="active",
    )


def _admin():
    return _user("admin-ingest@nibras.test", "admin")


def _form(file_name, content, **overrides):
    data = {
        "file": (io.BytesIO(content), file_name),
        "category_id": "1",
        "type": "code",
        "title": "نص مستورد",
    }
    data.update(overrides)
    return data


def test_requires_admin(client):
    admin = _admin()
    headers = _headers(admin)
    resp = client.post(
        "/api/admin/ingestion/import",
        data=_form("a.docx", _docx_bytes(["المادة 1 نص."])),
        headers=headers,
        content_type="multipart/form-data",
    )
    assert resp.status_code == 201


def test_unauthenticated_rejected(client):
    resp = client.post(
        "/api/admin/ingestion/import",
        data=_form("a.docx", _docx_bytes(["المادة 1 نص."])),
        content_type="multipart/form-data",
    )
    assert resp.status_code == 401


def test_citizen_forbidden(client):
    citizen = _user("citizen-ingest@nibras.test")
    resp = client.post(
        "/api/admin/ingestion/import",
        data=_form("a.docx", _docx_bytes(["المادة 1 نص."])),
        headers=_headers(citizen),
        content_type="multipart/form-data",
    )
    assert resp.status_code == 403


def test_import_without_file(client):
    admin = _admin()
    resp = client.post(
        "/api/admin/ingestion/import",
        data={"title": "بلا ملف", "category_id": "1", "type": "code"},
        headers=_headers(admin),
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400
    assert "file" in resp.get_json()["error"]


def test_import_wrong_extension(client):
    admin = _admin()
    resp = client.post(
        "/api/admin/ingestion/import",
        data=_form("doc.txt", b"hello"),
        headers=_headers(admin),
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400


def test_import_missing_title(client):
    admin = _admin()
    resp = client.post(
        "/api/admin/ingestion/import",
        data={"category_id": "1", "type": "code",
              "file": (io.BytesIO(_docx_bytes(["المادة 1 نص."])), "a.docx")},
        headers=_headers(admin),
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400
    assert "title" in resp.get_json()["error"]


def test_import_unknown_category(client):
    admin = _admin()
    resp = client.post(
        "/api/admin/ingestion/import",
        data=_form("a.docx", _docx_bytes(["المادة 1 نص."]), category_id="999"),
        headers=_headers(admin),
        content_type="multipart/form-data",
    )
    assert resp.status_code == 404


def test_dry_run_previews_without_writing(client):
    admin = _admin()
    content = _docx_bytes(["المادة 1 الزواج عقد.", "المادة 2 يقع الزواج."])
    with db_session() as conn:
        before = conn.execute("SELECT COUNT(*) AS c FROM legal_texts").fetchone()["c"]
    resp = client.post(
        "/api/admin/ingestion/import",
        data=_form("code.docx", content, dry_run="1"),
        headers=_headers(admin),
        content_type="multipart/form-data",
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["dry_run"] is True
    assert body["article_count"] == 2
    assert body["articles"][0]["content"] == "الزواج عقد."
    with db_session() as conn:
        after = conn.execute("SELECT COUNT(*) AS c FROM legal_texts").fetchone()["c"]
    assert after == before


def test_import_commits_and_searches(client):
    admin = _admin()
    content = _docx_bytes(["المادة 1 الزواج عقد رضائي.", "المادة 2 سن الرشد."])
    resp = client.post(
        "/api/admin/ingestion/import",
        data=_form("family.docx", content, title="مدونة الأسرة API"),
        headers=_headers(admin),
        content_type="multipart/form-data",
    )
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["article_count"] == 2
    text_id = body["id"]

    detail = client.get(f"/api/texts/{text_id}")
    assert detail.status_code == 200
    assert len(detail.get_json()["articles"]) == 2

    search = client.get("/api/search?q=سن الرشد")
    assert search.status_code == 200
    assert any(
        r["legal_text_title"] == "مدونة الأسرة API"
        for r in search.get_json()["results"]
    )


def test_import_audit_logged(client):
    admin = _admin()
    resp = client.post(
        "/api/admin/ingestion/import",
        data=_form("a.docx", _docx_bytes(["المادة 1 نص."])),
        headers=_headers(admin),
        content_type="multipart/form-data",
    )
    assert resp.status_code == 201
    with db_session() as conn:
        row = conn.execute(
            "SELECT admin_id, action, details FROM admin_audit_log "
            "WHERE action = 'ingestion.import' ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert row["admin_id"] == admin.id
    assert "a.docx" in row["details"]


def test_import_empty_text(client):
    admin = _admin()
    resp = client.post(
        "/api/admin/ingestion/import",
        data=_form("empty.docx", _docx_bytes([])),
        headers=_headers(admin),
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400


def test_import_pdf_fallback_single_article(client):
    admin = _admin()
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(72, 720, "A very short single document")
    c.save()
    resp = client.post(
        "/api/admin/ingestion/import",
        data=_form("short.pdf", buf.getvalue(), type="law"),
        headers=_headers(admin),
        content_type="multipart/form-data",
    )
    assert resp.status_code == 201
    assert resp.get_json()["article_count"] == 1
