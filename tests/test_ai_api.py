"""
اختبارات واجهة الذكاء الاصطناعي (API) — المرحلة 3.

المزوّد يُحاكى (monkeypatch لـ get_provider) فلا شبكة ولا مفاتيح — قرار
D-021. يغطي: المصادقة، التحقق من المدخلات، حصرية الاستشهاد بالمسترجَع
فقط، غياب المصدر (لا رد صامت)، فشل المزوّد (503)، حد المعدل، وتسجيل
ai_queries.
"""
import io

import pytest

from app import config, services_ai, services_auth
from app.database import db_session
from app.routes.ai import _attempts as _ai_attempts
from app.services_ai import AIProviderError

PASSWORD = "test-password-123"


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    _ai_attempts.clear()
    yield
    _ai_attempts.clear()


class FakeProvider:
    name = "fake"

    def __init__(self, answer="الجواب وفق المادة 230"):
        self.answer = answer
        self.calls = []

    def generate(self, question, context_articles, mode, system=None, user_prompt=None, images=None):
        self.calls.append({"mode": mode, "system": system, "user_prompt": user_prompt,
                           "context_count": len(context_articles)})
        return self.answer


def _register(client, email="citizen@example.com"):
    return services_auth.create_user_with_role(
        email=email, password=PASSWORD, full_name="مواطن اختبار",
        role_code="citizen", role_status="active", user_status="active",
    )


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def _login_token(client):
    profile = _register(client)
    return services_auth.create_access_token(profile.id)[0]


def _explain(client, token, question="التزام", mode="grounded"):
    return client.post(
        "/api/ai/explain",
        json={"question": question, "mode": mode},
        headers=_auth_headers(token),
    )


def _patch_providers(monkeypatch, *providers):
    """يستبدل قائمة المزوّدين المفعّلين بمزوّدات محاكاة (بدل get_provider)."""
    monkeypatch.setattr(services_ai, "_enabled_providers", lambda: list(providers))


def test_explain_public_without_auth(client, monkeypatch):
    _patch_providers(monkeypatch, FakeProvider("الرد موجَّه بالمادة 230"))
    resp = client.post("/api/ai/explain", json={"question": "التزام"})
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_explain_missing_question(client):
    token = _login_token(client)
    resp = client.post("/api/ai/explain", json={"mode": "grounded"}, headers=_auth_headers(token))
    assert resp.status_code == 400


def test_explain_invalid_mode(client):
    token = _login_token(client)
    resp = _explain(client, token, mode="bogus")
    assert resp.status_code == 400


def test_grounded_cites_only_retrieved(client, monkeypatch):
    _patch_providers(monkeypatch, FakeProvider("الرد موجَّه بالمادة 230"))
    token = _login_token(client)
    resp = _explain(client, token, question="التزام")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["mode"] == "grounded"
    assert data["status"] == "ok"
    assert len(data["cited_article_ids"]) == 1
    assert "المادة 230" in data["answer"]


def test_grounded_cites_decisions_from_jurisprudence(client, monkeypatch):
    """اجتهاد قضائي يستشهد برقم قراره يُسقط في cited_decision_ids.

    الاجتهاد يُسترجع من جدول jurisprudence (فئة قانونية موجودة) ويُرفق
    بترويسة «— رقم 2021/158» فيجب التقاطه حصرًا من المسترجَع.
    """
    provider = FakeProvider("الرد يستند إلى اجتهاد محكمة النقض 2021/158")
    _patch_providers(monkeypatch, provider)
    token = _login_token(client)
    resp = _explain(client, token, question="طلب النقض")
    data = resp.get_json()
    assert data["status"] == "ok"
    assert any(did in data["cited_decision_ids"] for did in (1, 2, 3))
    assert data["mode"] == "grounded"
    prompt_sent = provider.calls[0]["user_prompt"]
    assert "اجتهادات قضائية مسترجعة" in prompt_sent


def test_grounded_drops_citation_not_in_retrieval(client, monkeypatch):
    """المادة 999 غير مسترجعة فلا تُسقط في الاستشهاد أبدًا (حصرية الموجَّه)."""
    _patch_providers(monkeypatch, FakeProvider("الرد يستشهد بالمادة 999"))
    token = _login_token(client)
    data = _explain(client, token, question="التزام").get_json()
    assert data["cited_article_ids"] == []


def test_grounded_no_source_no_silent_fallback(client, monkeypatch):
    _patch_providers(monkeypatch, FakeProvider())
    token = _login_token(client)
    resp = _explain(client, token, question="كسكس قنطرة 884433221100")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "no_source"
    assert data["cited_article_ids"] == []
    assert "لم نعثر" in data["answer"]


def test_general_mode(client, monkeypatch):
    _patch_providers(monkeypatch, FakeProvider("رد تعليمي عام لا يعد استشارة قانونية."))
    token = _login_token(client)
    resp = _explain(client, token, mode="general")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["mode"] == "general"
    assert data["cited_article_ids"] == []


def test_provider_failure_returns_503(client, monkeypatch):
    class UnavailableProvider:
        name = "down"

        def generate(self, question, context_articles, mode, system=None, user_prompt=None, images=None):
            raise AIProviderError("تعذر الاتصال بمزوّد الذكاء الاصطناعي. حاول لاحقًا.", 503)

    _patch_providers(monkeypatch, UnavailableProvider())
    token = _login_token(client)
    resp = _explain(client, token, question="التزام")
    assert resp.status_code == 503
    assert "مزوّد" in resp.get_json()["error"]


def test_ai_rate_limited_per_user(client, monkeypatch):
    monkeypatch.setattr(config, "AI_RATE_LIMIT_MAX_REQUESTS", 1)
    monkeypatch.setattr(config, "AI_RATE_LIMIT_WINDOW_SECONDS", 3600)
    _patch_providers(monkeypatch, FakeProvider())
    token = _login_token(client)
    assert _explain(client, token).status_code == 200
    assert _explain(client, token).status_code == 429


def test_ai_query_logged(client, monkeypatch):
    _patch_providers(monkeypatch, FakeProvider("الرد موجَّه بالمادة 230"))
    token = _login_token(client)
    _explain(client, token, question="التزام")
    with db_session() as conn:
        row = conn.execute("SELECT * FROM ai_queries").fetchone()
    assert row is not None
    assert row["mode"] == "grounded"
    assert row["provider"] == "fake"
    assert row["user_id"] is None  # زائر بلا حساب
    # الخصوصية: لا يُحفظ نص السؤال/الإجابة (وثيقة الخصوصية §٦)
    assert row["question"] == ""


def test_research_mode_returns_external_sources(client, monkeypatch):
    """وضع المقارنة يسترجع مواد نبراس + مصادر خارجية ويعيدهما معًا."""
    _patch_providers(monkeypatch, FakeProvider())
    fake_results = [
        {"title": "مقال خارجي عن الطلاق", "url": "https://example.com/divorce",
         "snippet": "شرح المسطرة", "source": "example.com"}
    ]
    monkeypatch.setattr(services_ai, "search_web", lambda q, limit: fake_results)
    token = _login_token(client)
    resp = _explain(client, token, question="التزام", mode="research")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["mode"] == "research"
    assert data["status"] == "ok"
    assert len(data["external_sources"]) == 1
    assert data["external_sources"][0]["url"] == "https://example.com/divorce"


def test_research_web_failure_degrades_to_nibras_only(client, monkeypatch):
    """إخفاق البحث الخارجي (شبكة/تحليل) لا يُفشل الإجابة من نبراس."""
    provider = FakeProvider("إجابة من نبراس")
    _patch_providers(monkeypatch, provider)
    monkeypatch.setattr(services_ai, "search_web", lambda q, limit: [])

    def boom(q, limit):
        raise RuntimeError("شبكة")
    monkeypatch.setattr(services_ai, "search_web", boom)
    token = _login_token(client)
    resp = _explain(client, token, question="التزام", mode="research")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert data["mode"] == "research"
    assert data["external_sources"] == []
    assert provider.calls and provider.calls[0]["mode"] == "research"
    assert "نبراس" in provider.calls[0]["system"]


def test_research_no_source_when_nothing_found(client, monkeypatch):
    """لا نبراس ولا ويب → رسالة صريحة بلا رد صامت."""
    _patch_providers(monkeypatch, FakeProvider())
    monkeypatch.setattr(services_ai, "search_web", lambda q, limit: [])
    token = _login_token(client)
    resp = _explain(client, token, question="كسكس قنطرة 884433221100", mode="research")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "no_source"
    assert data["external_sources"] == []
    assert "لم نعثر" in data["answer"]


def test_research_provider_failure_returns_503(client, monkeypatch):
    class Down:
        name = "down"

        def generate(self, question, context_articles, mode, system=None, user_prompt=None, images=None):
            raise AIProviderError("تعذر الاتصال", 503)

    _patch_providers(monkeypatch, Down())
    monkeypatch.setattr(services_ai, "search_web", lambda q, limit: [])
    token = _login_token(client)
    resp = _explain(client, token, question="التزام", mode="research")
    assert resp.status_code == 503


def test_quota_error_falls_back_to_second_provider(client, monkeypatch):
    """استنفاد الحصة (429) على المزوّد الأول يدفع لتجربة الثاني بدل الفشل."""
    class QuotaProvider:
        name = "quota"

        def generate(self, question, context_articles, mode, system=None, user_prompt=None, images=None):
            raise AIProviderError("You exceeded your current quota", 429)

    second = FakeProvider("جواب من المزوّد الثاني")
    _patch_providers(monkeypatch, QuotaProvider(), second)
    token = _login_token(client)
    resp = _explain(client, token, question="التزام")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert "جواب من المزوّد الثاني" in data["answer"]
    assert second.calls and second.calls[0]["mode"] == "grounded"


def test_all_providers_quota_returns_friendly_429(client, monkeypatch):
    """كل المزوّدين مستنفدو الحصة → خطأ عربي واضح 429 لا كشف خام."""
    class QuotaProvider:
        name = "quota"

        def generate(self, question, context_articles, mode, system=None, user_prompt=None, images=None):
            raise AIProviderError("You exceeded your current quota", 429)

    _patch_providers(monkeypatch, QuotaProvider(), QuotaProvider())
    token = _login_token(client)
    resp = _explain(client, token, question="التزام")
    assert resp.status_code == 429
    err = resp.get_json()["error"]
    assert "مستنفدة" in err
    assert "لوحة التحكم" in err


def test_network_error_falls_back_to_next_provider(client, monkeypatch):
    """فشل شبكة/DNS عابر (getaddrinfo) على الأول لا يُسقط الطلب — يُجرب التالي."""
    class FlakyNetworkProvider:
        name = "flaky"

        def generate(self, question, context_articles, mode, system=None, user_prompt=None, images=None):
            raise AIProviderError(
                "[Errno 11001] getaddrinfo failed", 503
            )

    second = FakeProvider("جواب عبر المزوّد الاحتياطي بعد فشل الشبكة")
    _patch_providers(monkeypatch, FlakyNetworkProvider(), second)
    token = _login_token(client)
    resp = _explain(client, token, question="التزام")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert "الاحتياطي بعد فشل الشبكة" in data["answer"]
    assert second.calls and second.calls[0]["mode"] == "grounded"


def test_all_providers_network_error_returns_503_with_reason(client, monkeypatch):
    """كل المزوّدين فشلوا شبكة → 503 بشرح عربي واضح يرغب إعادة المحاولة."""
    class NetworkErrorProvider:
        name = "flaky"

        def generate(self, question, context_articles, mode, system=None, user_prompt=None, images=None):
            raise AIProviderError("[Errno 11001] getaddrinfo failed", 503)

    _patch_providers(monkeypatch, NetworkErrorProvider(), NetworkErrorProvider())
    token = _login_token(client)
    resp = _explain(client, token, question="التزام")
    assert resp.status_code == 503
    err = resp.get_json()["error"]
    assert "تعذر الاتصال" in err
    assert "الشبكة" in err or "اتصال" in err


# ---------------------------------------------------------------------------
# اختبارات رفع المرفقات (PDF / صور)
# ---------------------------------------------------------------------------

def test_attachment_no_file_returns_400(client):
    """بدون ملف → 400."""
    resp = client.post("/api/ai/explain-attachment", data={"question": "تحليل"})
    assert resp.status_code == 400
    assert "ملف" in resp.get_json()["error"]


def test_attachment_invalid_type_returns_400(client):
    """ملف بامتداد غير مدعوم → 400."""
    resp = client.post(
        "/api/ai/explain-attachment",
        data={"file": (io.BytesIO(b"test content"), "test.docx", "application/msword"),
              "question": "تحليل"},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400
    assert "غير مدعوم" in resp.get_json()["error"]


def test_attachment_pdf_no_text_returns_400(client, monkeypatch):
    """PDF فارغ أو بدون نص → 400."""
    def fake_extract(data):
        return ""
    monkeypatch.setattr(services_ai, "extract_pdf_text", fake_extract)
    resp = client.post(
        "/api/ai/explain-attachment",
        data={"file": (io.BytesIO(b"empty pdf"), "empty.pdf", "application/pdf"),
              "question": "حلّل"},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400


def test_attachment_pdf_success(client, monkeypatch):
    """PDF بنص → 200 مع إجابة."""
    _patch_providers(monkeypatch, FakeProvider("تحليل من الملف"))

    def fake_extract(data):
        return "نص المستند القانوني: المادة 1 تنص على..."
    monkeypatch.setattr(services_ai, "extract_pdf_text", fake_extract)

    resp = client.post(
        "/api/ai/explain-attachment",
        data={"file": (io.BytesIO(b"pdf content"), "law.pdf", "application/pdf"),
              "question": "ما هذا النص؟"},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert "تحليل من الملف" in data["answer"]
    assert data["mode"] == "attachment"


def test_attachment_image_success(client, monkeypatch):
    """صورة JPEG → 200 مع إجابة."""
    _patch_providers(monkeypatch, FakeProvider("تحليل الصورة"))

    resp = client.post(
        "/api/ai/explain-attachment",
        data={"file": (io.BytesIO(b"\xff\xd8\xff"), "photo.jpg", "image/jpeg"),
              "question": "ما في الصورة؟"},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert "تحليل الصورة" in data["answer"]
    assert data["mode"] == "attachment"


def test_attachment_png_success(client, monkeypatch):
    """صورة PNG → 200."""
    _patch_providers(monkeypatch, FakeProvider("تم تحليل الصورة"))

    resp = client.post(
        "/api/ai/explain-attachment",
        data={"file": (io.BytesIO(b"\x89PNG"), "scan.png", "image/png"),
              "question": "حلل"},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_attachment_image_no_question_uses_default(client, monkeypatch):
    """صورة بدون سؤال → يُستخدم سؤال افتراضي."""
    _patch_providers(monkeypatch, FakeProvider("تم التحليل"))

    resp = client.post(
        "/api/ai/explain-attachment",
        data={"file": (io.BytesIO(b"\xff\xd8\xff"), "doc.jpg", "image/jpeg")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"
