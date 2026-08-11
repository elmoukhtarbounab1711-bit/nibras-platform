"""
اختبارات طبقة خدمات مولّد الوثائق (المرحلة 4) — قرار D-022.

تحقق الإجابات (نوع/خيارات/تاريخ)، حتمية البذر (idempotent)، صرامة
StrictUndefined (متغير مفقود = خطأ لا فراغ)، وحقيقة تصدير PDF/DOCX
(بايتات فعلية قابلة للقراءة).
"""
import json

import pytest

from app import services_auth
from app.database import db_session
from app.services_documents import (
    DocumentError,
    ensure_defaults,
    export_docx,
    export_pdf,
    generate_document,
    get_document,
    get_template,
    list_templates,
    regenerate_document,
)

RENTAL_ANSWERS = {
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


def _user_id(index: int = 1) -> int:
    """مستخدم حقيقي (FK users) — مواطن؛ إعادة الاستدعاء بنفس الفهرس ترجع ذات المستخدم."""
    email = f"doc-user-{index}@example.com"
    existing = services_auth.get_user_by_email(email)
    if existing:
        return existing.id
    profile = services_auth.create_user(
        email=email,
        password="test-password-123",
        full_name=f"مستخدم {index}",
        role_code="citizen",
    )
    return profile.id


def test_ensure_defaults_is_idempotent(fresh_db):
    with db_session() as conn:
        before = conn.execute("SELECT COUNT(*) AS n FROM document_templates").fetchone()["n"]
    ensure_defaults()
    with db_session() as conn:
        after = conn.execute("SELECT COUNT(*) AS n FROM document_templates").fetchone()["n"]
    assert before == after == len(list_templates()) == 23


def test_list_and_get_template(fresh_db):
    items = list_templates()
    assert {"rental-contract", "power-of-attorney", "debt-acknowledgment",
            "commercial-lease", "sales-contract", "work-contract"} <= {t["slug"] for t in items}
    tmpl = get_template("rental-contract")
    assert tmpl["name"] == "عقد كراء سكني"
    assert any(f["name"] == "tenant_name" and f["required"] for f in tmpl["fields"])


def test_all_seed_templates_are_renderable(fresh_db):
    """كل قالب في البذر: وصفه موجود، حقولُه ترجع لقوالب، والهيكل يشير فقط
    لحقول معرّفة (تحقق من قالب عن الإغفال القاتل بـ StrictUndefined)."""
    import re

    from app import services_documents as svc

    ensure_defaults()
    for tmpl in svc._SEED_TEMPLATES:
        names = {f["name"] for f in tmpl["field_schema"]}
        assert tmpl.get("description", "").strip(), f"{tmpl['slug']} بلا وصف"
        assert tmpl["body_template"].strip(), f"{tmpl['slug']} بلا هيكل"
        body = tmpl["body_template"]
        # متغيرات {{ var }} — أول معرّف لاتيني بعد الوسم (قبل or/filters)
        for m in re.findall(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)", body):
            assert m in names, f"{tmpl['slug']} متغير غير معروف: {m}"
        # شروط {% if var %} / {% elif var %} / {% if not var %}
        for m in re.findall(r"\{\%\s*(?:if|elif)\s+(?:not\s+)?([A-Za-z_][A-Za-z0-9_]*)", body):
            assert m in names, f"{tmpl['slug']} شرط غير معروف: {m}"
        assert tmpl["body_template"].count("{{") == tmpl["body_template"].count("}}"), f"{tmpl['slug']} وسوم غير متزنة"


def test_validation_lab_kept(fresh_db):
    """قالب تجريبي لا يُبذر ويُختبر مباشرة — ضمانة بقاء سلوك التحقق."""
    from app.services_documents import _validate_answers

    fields = [{"name": "kind", "label": "النوع", "type": "select",
               "required": True, "options": ["أ", "ب"]},
              {"name": "flag", "label": "علم", "type": "boolean", "required": False}]
    with pytest.raises(DocumentError) as exc:
        _validate_answers(fields, {"kind": "ج"})
    assert "غير مقبولة" in exc.value.message
    with pytest.raises(DocumentError) as exc:
        _validate_answers(fields, {"kind": "أ", "flag": "نعم"})
    assert "منطقية" in exc.value.message


def test_generate_and_owner_access(fresh_db):
    doc = generate_document(_user_id(1), "rental-contract", RENTAL_ANSWERS)
    assert doc["version"] == 1
    assert "علي العلوي" in doc["doc_text"]
    assert doc["answers"]["landlord_name"] == "علي العلوي"
    fetched = get_document(_user_id(1), doc["id"])
    assert fetched["doc_text"] == doc["doc_text"]
    with pytest.raises(DocumentError) as exc:
        get_document(_user_id(2), doc["id"])  # ليس المالك
    assert exc.value.status_code == 404


def test_validate_rejects_bad_select_and_boolean(fresh_db):
    with db_session() as conn:
        conn.execute(
            "INSERT INTO document_templates "
            "(slug, name, category, field_schema, body_template, created_at) "
            "VALUES (?, ?, ?, ?, ?, datetime('now'))",
            (
                "validation-lab",
                "قالب تحقق",
                "العقود",
                json.dumps(
                    [
                        {"name": "kind", "label": "النوع", "type": "select",
                         "required": True, "options": ["أ", "ب"]},
                        {"name": "flag", "label": "علم", "type": "boolean", "required": False},
                    ],
                    ensure_ascii=False,
                ),
                "النوع {{ kind }}{% if flag %} والخيار مفعل{% endif %}",
            ),
        )
    with pytest.raises(DocumentError) as exc:
        generate_document(_user_id(), "validation-lab", {"kind": "ج"})
    assert "غير مقبولة" in exc.value.message
    with pytest.raises(DocumentError) as exc:
        generate_document(_user_id(), "validation-lab", {"kind": "أ", "flag": "نعم"})
    assert "منطقية" in exc.value.message


def test_strict_undefined_is_an_error_not_blank(fresh_db):
    """متغير مفقود من القالب (مع إجابات صحيحة) → خطأ صريح لا نص بفراغ."""
    with db_session() as conn:
        conn.execute(
            "INSERT INTO document_templates "
            "(slug, name, category, field_schema, body_template, created_at) "
            "VALUES (?, ?, ?, ?, ?, datetime('now'))",
            (
                "broken-template",
                "قالب معطوب",
                "العقود",
                json.dumps([{"name": "name", "label": "الاسم", "type": "text", "required": True}],
                           ensure_ascii=False),
                "مرحبا {{ name }} — {{ missing_var }}",
            ),
        )
    with pytest.raises(DocumentError) as exc:
        generate_document(_user_id(), "broken-template", {"name": "أحمد"})
    assert exc.value.status_code == 400


def test_optional_fields_do_not_break_strict_undefined(fresh_db):
    """حقل اختياري غير مُدخل لا يكسر StrictUndefined داخل {% if %}."""
    doc = generate_document(_user_id(), "rental-contract", {**RENTAL_ANSWERS, "payment_date": ""})
    assert "عقد كراء سكني" in doc["doc_text"]
    assert "يُؤدى في" not in doc["doc_text"]


def test_regenerate_increments_version(fresh_db):
    user_id = _user_id()
    doc = generate_document(user_id, "rental-contract", RENTAL_ANSWERS)
    updated = regenerate_document(user_id, doc["id"], {**RENTAL_ANSWERS, "monthly_rent": 3200})
    assert updated["version"] == 2
    assert "3200" in updated["doc_text"]
    assert get_document(user_id, doc["id"])["version"] == 2


def test_export_docx_is_valid_zip(fresh_db):
    doc = generate_document(_user_id(), "rental-contract", RENTAL_ANSWERS)
    data = export_docx(doc)
    assert data[:2] == b"PK"
    assert b"word/document.xml" in data


def test_export_pdf_is_valid_pdf(fresh_db):
    doc = generate_document(_user_id(), "rental-contract", RENTAL_ANSWERS)
    data = export_pdf(doc)
    assert data.startswith(b"%PDF")
    assert data.rstrip().endswith(b"%%EOF")


def test_export_handles_arabic_text(fresh_db):
    """النص العربي يمر عبر إعادة الترتيب بلا استثناء ولا حروف مشوهة قاتلة."""
    doc = generate_document(_user_id(), "rental-contract", RENTAL_ANSWERS)
    for text in (export_pdf(doc), export_docx(doc)):
        assert isinstance(text, bytes) and len(text) > 500
