"""
اختبارات مساعد المساطر (API) — المرحلة 3.

التصفح والتفصيل عامان (FR-6.1)، وتحديث التقدم للمسجّلين فقط (FR-6.2).
المسطرة النموذجية succession-liquidation لها 5 خطوات.
"""
import pytest

from app.routes.auth import _attempts

PASSWORD = "test-password-123"


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    _attempts.clear()
    yield
    _attempts.clear()


def _register(client, email="citizen@example.com"):
    return client.post(
        "/api/auth/register",
        json={"email": email, "password": PASSWORD, "full_name": "مواطن اختبار"},
    )


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


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


def test_progress_requires_auth(client):
    resp = client.post(
        "/api/procedures/succession-liquidation/progress",
        json={"step_number": 1},
    )
    assert resp.status_code == 401


def test_progress_mark_and_unmark(client):
    _register(client)
    login = client.post(
        "/api/auth/login", json={"email": "citizen@example.com", "password": PASSWORD}
    )
    token = login.get_json()["access_token"]
    headers = _auth_headers(token)

    resp = client.post(
        "/api/procedures/succession-liquidation/progress",
        json={"step_number": 1},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.get_json()["progress"] == {"completed": 1, "total": 5}

    resp = client.post(
        "/api/procedures/succession-liquidation/progress",
        json={"step_number": 1, "completed": False},
        headers=headers,
    )
    assert resp.get_json()["progress"] == {"completed": 0, "total": 5}


def test_progress_invalid_step_number(client):
    _register(client)
    token = client.post(
        "/api/auth/login", json={"email": "citizen@example.com", "password": PASSWORD}
    ).get_json()["access_token"]
    headers = _auth_headers(token)

    resp = client.post(
        "/api/procedures/succession-liquidation/progress",
        json={"step_number": 0},
        headers=headers,
    )
    assert resp.status_code == 400


def test_progress_unknown_procedure_or_step(client):
    _register(client)
    token = client.post(
        "/api/auth/login", json={"email": "citizen@example.com", "password": PASSWORD}
    ).get_json()["access_token"]
    headers = _auth_headers(token)

    resp = client.post(
        "/api/procedures/nonexistent/progress",
        json={"step_number": 1},
        headers=headers,
    )
    assert resp.status_code == 404

    resp = client.post(
        "/api/procedures/succession-liquidation/progress",
        json={"step_number": 99},
        headers=headers,
    )
    assert resp.status_code == 404


def test_progress_is_per_user(client):
    _register(client, email="a@example.com")
    _register(client, email="b@example.com")
    token_a = client.post(
        "/api/auth/login", json={"email": "a@example.com", "password": PASSWORD}
    ).get_json()["access_token"]
    token_b = client.post(
        "/api/auth/login", json={"email": "b@example.com", "password": PASSWORD}
    ).get_json()["access_token"]

    client.post(
        "/api/procedures/succession-liquidation/progress",
        json={"step_number": 1},
        headers=_auth_headers(token_a),
    )
    resp = client.post(
        "/api/procedures/succession-liquidation/progress",
        json={"step_number": 2},
        headers=_auth_headers(token_b),
    )
    assert resp.get_json()["progress"] == {"completed": 1, "total": 5}

    # إعادة نفس الخطوة لا تكررها (idempotent)
    client.post(
        "/api/procedures/succession-liquidation/progress",
        json={"step_number": 2},
        headers=_auth_headers(token_b),
    )
    resp = client.post(
        "/api/procedures/succession-liquidation/progress",
        json={"step_number": 3},
        headers=_auth_headers(token_b),
    )
    assert resp.get_json()["progress"] == {"completed": 2, "total": 5}
