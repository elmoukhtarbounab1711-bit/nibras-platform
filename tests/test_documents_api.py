"""
اختبارات مولّد الوثائق (API) — المرحلة 4 (قرار D-022).

التصفح عام، والتوليد/الملكية/التصدير بمصادقة ومالك فقط. القوالب النموذجية
تُبذَر عبر ensure_defaults (تُستدعى من init_db). يغطي: التحقق من الإجابات،
الملكية (الغير يرى 404)، التدرج عند إعادة التوليد، تصدير PDF/DOCX، حد المعدل.
"""
import io

import pytest

from app import config
from app.routes.auth import _attempts as _auth_attempts
from app.routes.documents import _attempts as _doc_attempts

PASSWORD = "test-password-123"

ANSWERS = {
    "landlord_name": "علي العلوي",
    "tenant_name": "فاطمة الزهراء",
    "property_address": "شارع الحسن الثاني، الدار البيضاء",
    "monthly_rent": 2500,
    "start_date": "2026-09-01",
    "duration_months": 12,
    "deposit_amount": 5000,
}


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    _doc_attempts.clear()
    _auth_attempts.clear()
    yield
    _doc_attempts.clear()
    _auth_attempts.clear()


def _register(client, email="citizen@example.com"):
    return client.post(
        "/api/auth/register",
        json={"email": email, "password": PASSWORD, "full_name": "مواطن اختبار"},
    )


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def _login_token(client, email="citizen@example.com"):
    _register(client, email=email)
    return client.post(
        "/api/auth/login", json={"email": email, "password": PASSWORD}
    ).get_json()["access_token"]


def _generate(client, token, answers=None, template_id=None, template_slug="rental-contract"):
    payload = {"answers": answers if answers is not None else ANSWERS}
    if template_id is not None:
        payload["template_id"] = template_id
    else:
        payload["template_slug"] = template_slug
    return client.post("/api/documents/generate", json=payload, headers=_auth_headers(token))


def _rental_template_id(client):
    data = client.get("/api/documents/templates").get_json()
    return next(t for t in data if t["slug"] == "rental-contract")["id"]


def test_templates_public(client):
    resp = client.get("/api/documents/templates")
    assert resp.status_code == 200
    slugs = {t["slug"] for t in resp.get_json()}
    assert {"rental-contract", "power-of-attorney", "debt-acknowledgment"} <= slugs


def test_templates_filter_by_category(client):
    resp = client.get("/api/documents/templates", query_string={"category": "التوثيق"})
    assert resp.status_code == 200
    items = resp.get_json()
    assert items and all(t["category"] == "التوثيق" for t in items)
    assert all(t["slug"] == "power-of-attorney" for t in items)


def test_template_detail_fields(client):
    resp = client.get("/api/documents/templates/rental-contract")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["name"] == "عقد كراء سكني"
    assert isinstance(data["fields"], list)
    labels = {f["label"] for f in data["fields"]}
    assert "اسم المكتري" in labels
    assert data["body_template"].strip()


def test_template_unknown_404(client):
    resp = client.get("/api/documents/templates/nonexistent")
    assert resp.status_code == 404


def test_generate_requires_auth(client):
    resp = client.post("/api/documents/generate", json={"template_slug": "rental-contract"})
    assert resp.status_code == 401


def test_generate_missing_template_param(client):
    token = _login_token(client)
    resp = client.post("/api/documents/generate", json={"answers": ANSWERS}, headers=_auth_headers(token))
    assert resp.status_code == 400


def test_generate_happy_path(client):
    token = _login_token(client)
    resp = _generate(client, token)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["template_slug"] == "rental-contract"
    assert data["version"] == 1
    assert "علي العلوي" in data["doc_text"]
    assert "2500" in data["doc_text"]
    assert data["doc_text"].startswith("عقد كراء سكني")


def test_generate_by_template_id(client):
    token = _login_token(client)
    resp = _generate(client, token, template_id=_rental_template_id(client))
    assert resp.status_code == 201
    assert resp.get_json()["template_slug"] == "rental-contract"


def test_generate_unknown_template(client):
    token = _login_token(client)
    resp = _generate(client, token, template_slug="nonexistent")
    assert resp.status_code == 404


def test_generate_missing_required(client):
    token = _login_token(client)
    bad = dict(ANSWERS)
    bad.pop("tenant_name")
    resp = _generate(client, token, answers=bad)
    assert resp.status_code == 400
    assert "اسم المكتري" in resp.get_json()["error"]


def test_generate_invalid_number(client):
    token = _login_token(client)
    bad = dict(ANSWERS, monthly_rent="ليس رقما")
    resp = _generate(client, token, answers=bad)
    assert resp.status_code == 400
    assert "رقمًا" in resp.get_json()["error"]


def test_generate_invalid_date(client):
    token = _login_token(client)
    bad = dict(ANSWERS, start_date="01/09/2026")
    resp = _generate(client, token, answers=bad)
    assert resp.status_code == 400
    assert "تاريخًا" in resp.get_json()["error"]


def test_generate_rejects_negative_minimum(client):
    token = _login_token(client)
    bad = dict(ANSWERS, monthly_rent=-5)
    resp = _generate(client, token, answers=bad)
    assert resp.status_code == 400


def test_my_documents_lists_owned(client):
    token = _login_token(client)
    _generate(client, token)
    resp = client.get("/api/documents/my", headers=_auth_headers(token))
    assert resp.status_code == 200
    docs = resp.get_json()
    assert len(docs) == 1
    assert docs[0]["doc_text"].startswith("عقد كراء سكني")


def test_my_documents_requires_auth(client):
    resp = client.get("/api/documents/my")
    assert resp.status_code == 401


def test_document_is_owner_only(client):
    token_a = _login_token(client, email="a@example.com")
    token_b = _login_token(client, email="b@example.com")
    doc_id = _generate(client, token_a).get_json()["id"]

    for path in (f"/api/documents/{doc_id}/export", f"/api/documents/{doc_id}/regenerate"):
        resp = client.get(path, headers=_auth_headers(token_b))
        assert resp.status_code in (404, 405)
    resp = client.post(
        f"/api/documents/{doc_id}/regenerate",
        json={"answers": ANSWERS},
        headers=_auth_headers(token_b),
    )
    assert resp.status_code == 404


def test_export_docx(client):
    token = _login_token(client)
    doc_id = _generate(client, token).get_json()["id"]
    resp = client.get(f"/api/documents/{doc_id}/export", query_string={"format": "docx"}, headers=_auth_headers(token))
    assert resp.status_code == 200
    assert resp.mimetype == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert resp.headers.get("Content-Disposition", "").endswith(".docx")
    data = resp.data
    assert data[:2] == b"PK"  # OOXML = zip
    assert len(data) > 500


def test_export_pdf(client):
    token = _login_token(client)
    doc_id = _generate(client, token).get_json()["id"]
    resp = client.get(f"/api/documents/{doc_id}/export", query_string={"format": "pdf"}, headers=_auth_headers(token))
    assert resp.status_code == 200
    assert resp.mimetype == "application/pdf"
    assert resp.data.startswith(b"%PDF")
    assert len(resp.data) > 500


def test_export_invalid_format(client):
    token = _login_token(client)
    doc_id = _generate(client, token).get_json()["id"]
    resp = client.get(f"/api/documents/{doc_id}/export", query_string={"format": "txt"}, headers=_auth_headers(token))
    assert resp.status_code == 400


def test_export_requires_auth(client):
    resp = client.get("/api/documents/1/export")
    assert resp.status_code == 401


def test_regenerate_bumps_version(client):
    token = _login_token(client)
    doc_id = _generate(client, token).get_json()["id"]
    changed = dict(ANSWERS, monthly_rent=3000)
    resp = client.post(
        f"/api/documents/{doc_id}/regenerate",
        json={"answers": changed},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["version"] == 2
    assert "3000" in data["doc_text"]
    assert "2500" not in data["doc_text"]


def test_generate_rate_limited_per_user(client, monkeypatch):
    monkeypatch.setattr(config, "DOC_RATE_LIMIT_MAX_REQUESTS", 1)
    monkeypatch.setattr(config, "DOC_RATE_LIMIT_WINDOW_SECONDS", 3600)
    token = _login_token(client)
    assert _generate(client, token).status_code == 201
    assert _generate(client, token).status_code == 429


def test_stream_export_bytes_are_reusable(client):
    """البيانات تُصنع في الذاكرة (BytesIO) — قابلية إعادة القراءة لا تُفقد."""
    token = _login_token(client)
    doc_id = _generate(client, token).get_json()["id"]
    resp = client.get(f"/api/documents/{doc_id}/export", headers=_auth_headers(token))
    data = resp.data
    assert io.BytesIO(data).read().startswith(b"%PDF")
