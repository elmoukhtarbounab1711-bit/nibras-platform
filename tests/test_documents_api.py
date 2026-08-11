"""
اختبارات مولّد الوثائق (API) — المرحلة 4 (قرار D-022) — منصة عامة.

التصفح عام والتوليد عام وعديم الحالة (stateless): لا تُخزَّن الوثيقة
والزائر لا يملك حسابًا. التصدير PDF/DOCX يتم فورًا عبر وسيط format في
نفس طلب التوليد (توليد في الذاكرة). القوالب النموذجية تُبذَر عبر
ensure_defaults. يغطي: التحقق من الإجابات، عدم التخزين (persisted=False)،
التصدير المباشر PDF/DOCX، حد المعدل، وصحة الاستدلال بالنمط.
"""
import io

import pytest

from app import config
from app.routes.documents import _attempts as _doc_attempts

PASSWORD = "test-password-123"

ANSWERS = {
    "landlord_name": "علي العلوي",
    "landlord_cin": "AB123456",
    "tenant_name": "فاطمة الزهراء",
    "tenant_cin": "CD789012",
    "property_address": "شارع الحسن الثاني، الدار البيضاء",
    "monthly_rent": 2500,
    "start_date": "2026-09-01",
    "duration_months": 12,
    "deposit_amount": 5000,
    "city": "الدار البيضاء",
    "contract_date": "2026-08-01",
}


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    _doc_attempts.clear()
    yield
    _doc_attempts.clear()


def _generate(client, answers=None, template_id=None,
              template_slug="rental-contract", fmt=None):
    payload = {"answers": answers if answers is not None else ANSWERS}
    if template_id is not None:
        payload["template_id"] = template_id
    else:
        payload["template_slug"] = template_slug
    if fmt is not None:
        payload["format"] = fmt
    return client.post("/api/documents/generate", json=payload)


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
    assert "power-of-attorney" in {t["slug"] for t in items}


def test_templates_include_description(client):
    resp = client.get("/api/documents/templates")
    assert resp.status_code == 200
    assert all("description" in t for t in resp.get_json())
    detail = client.get("/api/documents/templates/rental-contract").get_json()
    assert detail["description"].strip()


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


def test_generate_public_no_auth(client):
    resp = _generate(client)
    assert resp.status_code == 201


def test_generate_missing_template_param(client):
    resp = client.post("/api/documents/generate", json={"answers": ANSWERS})
    assert resp.status_code == 400


def test_generate_is_stateless(client):
    resp = _generate(client)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["template_slug"] == "rental-contract"
    assert data["persisted"] is False
    assert data["id"] is None


def test_generate_happy_path(client):
    resp = _generate(client)
    assert resp.status_code == 201
    data = resp.get_json()
    assert "علي العلوي" in data["doc_text"]
    assert "2500" in data["doc_text"]
    assert "بسم الله" in data["doc_text"] and "عقد كراء سكني" in data["doc_text"]


def test_generate_by_template_id(client):
    resp = _generate(client, template_id=_rental_template_id(client))
    assert resp.status_code == 201
    assert resp.get_json()["template_slug"] == "rental-contract"


def test_generate_unknown_template(client):
    resp = _generate(client, template_slug="nonexistent")
    assert resp.status_code == 404


def test_generate_missing_required(client):
    bad = dict(ANSWERS)
    bad.pop("tenant_name")
    resp = _generate(client, answers=bad)
    assert resp.status_code == 400
    assert "اسم المكتري" in resp.get_json()["error"]


def test_generate_invalid_number(client):
    bad = dict(ANSWERS, monthly_rent="ليس رقما")
    resp = _generate(client, answers=bad)
    assert resp.status_code == 400
    assert "رقمًا" in resp.get_json()["error"]


def test_generate_invalid_date(client):
    bad = dict(ANSWERS, start_date="01/09/2026")
    resp = _generate(client, answers=bad)
    assert resp.status_code == 400
    assert "تاريخًا" in resp.get_json()["error"]


def test_generate_rejects_negative_minimum(client):
    bad = dict(ANSWERS, monthly_rent=-5)
    resp = _generate(client, answers=bad)
    assert resp.status_code == 400


def test_export_docx_direct(client):
    resp = _generate(client, fmt="docx")
    assert resp.status_code == 200
    assert resp.mimetype == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert resp.headers.get("Content-Disposition", "").endswith(".docx")
    assert resp.data[:2] == b"PK"  # OOXML = zip
    assert len(resp.data) > 500


def test_export_pdf_direct(client):
    resp = _generate(client, fmt="pdf")
    assert resp.status_code == 200
    assert resp.mimetype == "application/pdf"
    assert resp.data.startswith(b"%PDF")
    assert len(resp.data) > 500


def test_export_bytes_are_reusable(client):
    """البيانات تُصنع في الذاكرة (BytesIO) — قابلية إعادة القراءة لا تُفقد."""
    resp = _generate(client, fmt="pdf")
    data = resp.data
    assert io.BytesIO(data).read().startswith(b"%PDF")


def test_generate_rate_limited_per_ip(client, monkeypatch):
    monkeypatch.setattr(config, "DOC_RATE_LIMIT_MAX_REQUESTS", 1)
    monkeypatch.setattr(config, "DOC_RATE_LIMIT_WINDOW_SECONDS", 3600)
    assert _generate(client).status_code == 201
    assert _generate(client).status_code == 429