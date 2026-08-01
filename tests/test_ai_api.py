"""
اختبارات واجهة الذكاء الاصطناعي (API) — المرحلة 3.

المزوّد يُحاكى (monkeypatch لـ get_provider) فلا شبكة ولا مفاتيح — قرار
D-021. يغطي: المصادقة، التحقق من المدخلات، حصرية الاستشهاد بالمسترجَع
فقط، غياب المصدر (لا رد صامت)، فشل المزوّد (503)، حد المعدل، وتسجيل
ai_queries.
"""
import pytest

from app import config, services_ai
from app.database import db_session
from app.routes.ai import _attempts as _ai_attempts
from app.routes.auth import _attempts as _auth_attempts
from app.services_ai import AIProviderError

PASSWORD = "test-password-123"


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    _ai_attempts.clear()
    _auth_attempts.clear()
    yield
    _ai_attempts.clear()
    _auth_attempts.clear()


class FakeProvider:
    name = "fake"

    def __init__(self, answer="الجواب وفق المادة 230"):
        self.answer = answer

    def generate(self, question, context_articles, mode):
        return self.answer


def _register(client, email="citizen@example.com"):
    return client.post(
        "/api/auth/register",
        json={"email": email, "password": PASSWORD, "full_name": "مواطن اختبار"},
    )


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def _login_token(client):
    _register(client)
    return client.post(
        "/api/auth/login", json={"email": "citizen@example.com", "password": PASSWORD}
    ).get_json()["access_token"]


def _explain(client, token, question="التزام", mode="grounded"):
    return client.post(
        "/api/ai/explain",
        json={"question": question, "mode": mode},
        headers=_auth_headers(token),
    )


def test_explain_requires_auth(client):
    resp = client.post("/api/ai/explain", json={"question": "التزام"})
    assert resp.status_code == 401


def test_explain_missing_question(client):
    token = _login_token(client)
    resp = client.post("/api/ai/explain", json={"mode": "grounded"}, headers=_auth_headers(token))
    assert resp.status_code == 400


def test_explain_invalid_mode(client):
    token = _login_token(client)
    resp = _explain(client, token, mode="bogus")
    assert resp.status_code == 400


def test_grounded_cites_only_retrieved(client, monkeypatch):
    monkeypatch.setattr(
        services_ai, "get_provider", lambda: FakeProvider("الرد موجَّه بالمادة 230")
    )
    token = _login_token(client)
    resp = _explain(client, token, question="التزام")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["mode"] == "grounded"
    assert data["status"] == "ok"
    assert len(data["cited_article_ids"]) == 1
    assert "المادة 230" in data["answer"]


def test_grounded_drops_citation_not_in_retrieval(client, monkeypatch):
    """المادة 999 غير مسترجعة فلا تُسقط في الاستشهاد أبدًا (حصرية الموجَّه)."""
    monkeypatch.setattr(
        services_ai, "get_provider", lambda: FakeProvider("الرد يستشهد بالمادة 999")
    )
    token = _login_token(client)
    data = _explain(client, token, question="التزام").get_json()
    assert data["cited_article_ids"] == []


def test_grounded_no_source_no_silent_fallback(client, monkeypatch):
    monkeypatch.setattr(services_ai, "get_provider", lambda: FakeProvider())
    token = _login_token(client)
    resp = _explain(client, token, question="كسكس قنطرة 884433221100")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "no_source"
    assert data["cited_article_ids"] == []
    assert "لم نعثر" in data["answer"]


def test_general_mode(client, monkeypatch):
    monkeypatch.setattr(
        services_ai, "get_provider",
        lambda: FakeProvider("رد تعليمي عام لا يعد استشارة قانونية."),
    )
    token = _login_token(client)
    resp = _explain(client, token, mode="general")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["mode"] == "general"
    assert data["cited_article_ids"] == []


def test_provider_failure_returns_503(client, monkeypatch):
    class UnavailableProvider:
        name = "down"

        def generate(self, question, context_articles, mode):
            raise AIProviderError("تعذر الاتصال بمزوّد الذكاء الاصطناعي. حاول لاحقًا.", 503)

    monkeypatch.setattr(services_ai, "get_provider", UnavailableProvider)
    token = _login_token(client)
    resp = _explain(client, token, question="التزام")
    assert resp.status_code == 503
    assert "مزوّد" in resp.get_json()["error"]


def test_ai_rate_limited_per_user(client, monkeypatch):
    monkeypatch.setattr(config, "AI_RATE_LIMIT_MAX_REQUESTS", 1)
    monkeypatch.setattr(config, "AI_RATE_LIMIT_WINDOW_SECONDS", 3600)
    monkeypatch.setattr(services_ai, "get_provider", FakeProvider)
    token = _login_token(client)
    assert _explain(client, token).status_code == 200
    assert _explain(client, token).status_code == 429


def test_ai_query_logged(client, monkeypatch):
    monkeypatch.setattr(
        services_ai, "get_provider", lambda: FakeProvider("الرد موجَّه بالمادة 230")
    )
    token = _login_token(client)
    _explain(client, token, question="التزام")
    with db_session() as conn:
        row = conn.execute("SELECT * FROM ai_queries").fetchone()
    assert row is not None
    assert row["mode"] == "grounded"
    assert row["question"] == "التزام"
    assert row["provider"] == "fake"
    assert row["user_id"] is not None
