"""
اختبارات مساعد المساطر (API) — المرحلة 3 (منصة عامة).

التصفح والتفصيل عامان (FR-6.1). بعد التحول إلى منصة عامة بلا حسابات لا
يُخزَّن تقدم شخصي (الخصوصية بالتصميم): POST progress يعيد اعترافًا فقط
دون كتابة، و GET يعيد تعريفًا عامًا. المسطرة النموذجية
succession-liquidation لها 5 خطوات.
"""


def test_list_procedures_with_step_count(client):
    resp = client.get("/api/procedures")
    assert resp.status_code == 200
    procs = resp.get_json()
    slugs = {p["slug"] for p in procs}
    assert "succession-liquidation" in slugs
    assert all(p["step_count"] >= 1 for p in procs)


def test_list_procedures_filter_by_category(client):
    resp = client.get("/api/procedures", query_string={"category": "الأسرة"})
    assert resp.status_code == 200
    procs = resp.get_json()
    assert procs and all(p["category"] == "الأسرة" for p in procs)


def test_procedure_detail_ordered_steps(client):
    resp = client.get("/api/procedures/succession-liquidation")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["responsible_authority"]
    assert data["typical_timeframe"]
    numbers = [s["step_number"] for s in data["steps"]]
    assert numbers == sorted(numbers)
    assert data["steps"][0]["required_documents"]


def test_procedure_unknown_404(client):
    resp = client.get("/api/procedures/nonexistent")
    assert resp.status_code == 404


def test_progress_public_no_persistence(client):
    resp = client.post(
        "/api/procedures/succession-liquidation/progress",
        json={"step_number": 1},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["progress"] == []
    assert "لا يُحفظ" in body["message"]


def test_progress_get_public_definition(client):
    resp = client.get("/api/procedures/succession-liquidation/progress")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["procedure_slug"] == "succession-liquidation"
    assert body["progress"] == []


def test_progress_unknown_procedure_public(client):
    resp = client.post(
        "/api/procedures/nonexistent/progress",
        json={"step_number": 1},
    )
    assert resp.status_code == 200