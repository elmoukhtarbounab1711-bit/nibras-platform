"""
اختبارات مولد الوثائق والعقود (API + المحرّك) — ميزة مكتبة القوالب.

المكتبة (data/legal_docs) عُزلت من git (تُرسَب عبر
scripts/ingest_legal_docs.py) لذلك اختبارات المحرّك تتخطى إن غابت
الملفات، بينما اختبارات بنية الـ API (catalog/health/templates/أمان
المسارات) تعمل دائمًا.
"""
import zipfile

import pytest

from app import generator
from app.generator import GeneratorError


def _any_fillable_doc():
    for d in generator.list_docs():
        if d["fillable"]:
            return d["file"]
    return None


FILLABLE_DOC = _any_fillable_doc()


@pytest.fixture
def sample_fields():
    if not FILLABLE_DOC:
        pytest.skip("مكتبة الوثائق غير منزّلة في هذه البيئة")
    return generator.extract_fields(FILLABLE_DOC)


# ---------------------------------------------------------------------------
# البنية (تعمل بدون الملفات)
# ---------------------------------------------------------------------------

def test_generator_health(client):
    resp = client.get("/api/generator/health")
    assert resp.status_code == 200
    body = resp.get_json()
    assert "indexed_files" in body
    assert "max_fields" in body


def test_generator_catalog_shape(client):
    resp = client.get("/api/generator/catalog")
    assert resp.status_code == 200
    body = resp.get_json()
    assert "categories" in body
    assert "docs" in body
    assert isinstance(body["categories"], list)
    assert isinstance(body["docs"], list)


def test_generator_catalog_filter_by_category(client):
    resp = client.get("/api/generator/catalog", query_string={"category": "__none__"})
    assert resp.status_code == 200
    assert resp.get_json()["docs"] == []


def test_generator_templates_shape(client):
    resp = client.get("/api/generator/templates")
    assert resp.status_code == 200
    assert isinstance(resp.get_json()["templates"], list)


def test_generator_fields_unknown_404(client):
    resp = client.get("/api/generator/fields", query_string={"file": "__missing__.docx"})
    assert resp.status_code == 404


def test_generator_fields_traversal_guard(client):
    resp = client.get("/api/generator/fields", query_string={"file": "../secret"})
    assert resp.status_code in (400, 404)


def test_generator_missing_file_param(client):
    resp = client.get("/api/generator/fields")
    assert resp.status_code == 400
    resp2 = client.post("/api/generator/render", json={})
    assert resp2.status_code == 400


# ---------------------------------------------------------------------------
# المحرّك (يتطلب ملفات المكتبة المنزّلة)
# ---------------------------------------------------------------------------

def test_extract_fields_in_document_order(sample_fields):
    assert isinstance(sample_fields, list) and sample_fields
    keys = [f["key"] for f in sample_fields]
    assert keys == sorted(keys)
    assert all("label" in f and "type" in f for f in sample_fields)


def test_generate_docx_bytes_valid_zip(sample_fields):
    values = {f["key"]: "قيمة اختبارية" for f in sample_fields}
    data, name = generator.generate_docx_bytes(FILLABLE_DOC, sample_fields, values)
    assert data and data[:2] == b"PK"
    with zipfile.ZipFile(__import__("io").BytesIO(data)) as zf:
        assert "word/document.xml" in zf.namelist()
    assert name


def test_generate_docx_fills_blank_runs(sample_fields):
    from docx import Document
    values = {f["key"]: "X-ي" for f in sample_fields}
    data, _ = generator.generate_docx_bytes(FILLABLE_DOC, sample_fields, values)
    doc = Document(__import__("io").BytesIO(data))
    full = "".join(p.text or "" for p in doc.paragraphs)
    # لا يجب بقاء فراغات نقاط الثلاث فما فوق بعد التعبئة
    assert "..." not in full


def test_preview_html_contains_filled_values(sample_fields):
    values = {f["key"]: "قيمة_مميزة" for f in [sample_fields[0]]}
    html, _ = generator.preview_html(FILLABLE_DOC, sample_fields, values)
    assert "<html" in html
    assert "قيمة_مميزة" in html


def test_preview_recommended_template(client):
    templates = generator.recommended_templates()
    if not templates:
        pytest.skip("لا توجد قوالب موصى بها في هذه البيئة")
    t = templates[0]
    resp = client.get("/api/generator/fields",
                      query_string={"template": t["id"], "file": t["file"]})
    assert resp.status_code == 200
    fields = resp.get_json()["fields"]
    vals = {f["key"]: "نبراس" for f in fields}
    resp = client.post("/api/generator/render",
                       json={"template": t["id"], "file": t["file"], "values": vals})
    assert resp.status_code == 200
    assert "preview" in resp.get_json()


def test_download_returns_docx(client, sample_fields):
    vals = {f["key"]: "نبراس" for f in sample_fields}
    resp = client.post("/api/generator/download",
                       json={"file": FILLABLE_DOC, "values": vals})
    assert resp.status_code == 200
    assert "wordprocessingml" in resp.headers.get("Content-Type", "")
    assert resp.data[:2] == b"PK"


def test_resolve_file_rejects_escape():
    with pytest.raises(GeneratorError) as exc:
        generator._resolve_file("..\\outside.docx")
    assert exc.value.status_code == 400
