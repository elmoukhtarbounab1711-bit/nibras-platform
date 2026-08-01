"""
اختبارات نقاط الحاسبات القانونية (API) — المرحلة 3.

GET /api/calculators يعرض الحاسبات (idempotent من ensure_defaults)، و
POST /api/calculators/<slug>/run يعيد {result, legal_basis} ويُسجّل
calculator_runs. أخطاء المدخلات 400 والمسارات المجهولة 404.
"""
from app.database import db_session


def _run(client, payload):
    return client.post("/api/calculators/inheritance/run", json=payload)


def test_list_calculators_includes_inheritance(client):
    resp = client.get("/api/calculators")
    assert resp.status_code == 200
    slugs = [c["slug"] for c in resp.get_json()]
    assert "inheritance" in slugs


def test_run_inheritance_returns_result_and_legal_basis(client):
    resp = _run(
        client, {"estate_value": 1000, "spouse": "wife", "sons": 1}
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["result"]["total_estate"] == 1000
    assert data["result"]["heirs"][0]["heir"] == "الزوجة"
    assert data["result"]["heirs"][0]["amount"] == 125.0
    assert any("344" in b for b in data["legal_basis"])


def test_run_inheritance_validation_error(client):
    resp = _run(client, {"estate_value": 1000, "grandfather": True})
    assert resp.status_code == 400
    assert "غير مدعومة" in resp.get_json()["error"]


def test_run_unknown_calculator_404(client):
    resp = client.post("/api/calculators/nonexistent/run", json={"estate_value": 1})
    assert resp.status_code == 404


def test_run_logs_calculator_run(client):
    _run(client, {"estate_value": 1000, "spouse": "husband", "full_sisters": 1})
    with db_session() as conn:
        count = conn.execute("SELECT COUNT(*) AS n FROM calculator_runs").fetchone()["n"]
    assert count == 1
