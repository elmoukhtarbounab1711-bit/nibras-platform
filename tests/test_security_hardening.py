"""
 اختبارات التصلّب الأمني (P0 + P1):
  P0-1 — لا بيانات اعتماد حقيقية في seed.py
  P0-2 — .env.example لا يحتوي على CORS wildcard أو JWT ضعيف
  P1-1 — rate limiting على نقاط المصادقة
  P1-2 — HSTS header عند التفعيل
  P1-3 — Cache-Control: no-store على المسارات الحساسة
  P1-4 — حدطول سؤال الذكاء الاصطناعي
"""
from pathlib import Path

import pytest

from app import config
from app.routes.ai import _attempts as _ai_attempts

REPO_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# P0-1: لا بيانات اعتماد حقيقية في الكود المصدري
# ---------------------------------------------------------------------------

class TestP01NoHardcodedCredentials:
    """يتأكد أن seed.py لا يحتوي بريد أو كلمة مرور حقيقية في الكود المصدري."""

    def test_seed_source_has_no_real_admin_email(self):
        seed_src = (REPO_ROOT / "app" / "seed.py").read_text(encoding="utf-8")
        assert "elmoukhtar.bounab1711@gmail.com" not in seed_src, (
            "seed.py لا يزال يحتوي بريدًا حقيقيًا — يجب إزالته"
        )

    def test_seed_source_has_no_hardcoded_admin_password(self):
        seed_src = (REPO_ROOT / "app" / "seed.py").read_text(encoding="utf-8")
        assert "@#Nibras@#$" not in seed_src, (
            "seed.py لا يزال يحتوي كلمة مرور حقيقية — يجب إزالتها"
        )

    def test_admin_seeding_requires_env_vars(self):
        """الحساب الإداري يُنشأ فقط عند توفر NIBRAS_ADMIN_EMAIL + NIBRAS_ADMIN_PASSWORD."""
        seed_src = (REPO_ROOT / "app" / "seed.py").read_text(encoding="utf-8")
        assert 'os.environ.get("NIBRAS_ADMIN_EMAIL"' in seed_src
        assert 'os.environ.get("NIBRAS_ADMIN_PASSWORD"' in seed_src

    def test_demo_users_do_not_include_admin(self):
        """DEMO_USERS لا يحتوي دور admin — يُنشأ فقط عبر env vars."""
        seed_src = (REPO_ROOT / "app" / "seed.py").read_text(encoding="utf-8")
        # يتحقق أن DEMO_USERS لا يحتوي "admin" كدور
        in_demo = seed_src.split("DEMO_USERS = [")[1].split("]")[0]
        assert '"admin"' not in in_demo, (
            "DEMO_USERS لا يجب أن يحتوي دور admin"
        )


# ---------------------------------------------------------------------------
# P0-2: .env.example آمن
# ---------------------------------------------------------------------------

class TestP02EnvExampleSafe:
    """يتأكد أن .env.example لا يحتوي قيم خطيرة يمكن نسخها للإنتاج."""

    def test_no_wildcard_cors(self):
        env_example = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")
        # يتحقق أن النطاقات المسموحة لا تحتوي wildcard
        for line in env_example.splitlines():
            if line.startswith("NIBRAS_CORS_ORIGINS="):
                value = line.split("=", 1)[1].strip()
                assert value != "*", (
                    ".env.example لا يجب أن يحتوي NIBRAS_CORS_ORIGINS=*"
                )
                break

    def test_jwt_secret_is_placeholder(self):
        env_example = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")
        for line in env_example.splitlines():
            if line.startswith("NIBRAS_JWT_SECRET="):
                value = line.split("=", 1)[1].strip()
                # لا يجب أن يكون سرًا حقيقيًا — يجب أن يحتوي تلميح تغيير
                assert "CHANGE" in value or "غيّر" in value or "example" in value.lower(), (
                    "NIBRAS_JWT_SECRET في .env.example يجب أن يكون نموذجًا واضحًا"
                )
                break

    def test_debug_disabled(self):
        env_example = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")
        for line in env_example.splitlines():
            if line.startswith("NIBRAS_DEBUG="):
                assert line.strip() == "NIBRAS_DEBUG=0"
                break


# ---------------------------------------------------------------------------
# P1-1: Auth rate limiting
# ---------------------------------------------------------------------------


class TestP11AuthRateLimiting:
    """نقاط المصادقة محمية بحد معدل في الذاكرة."""

    def test_login_rate_limited(self, client):
        monkeypatch_limit = 3
        original_max = config.RATE_LIMIT_MAX_ATTEMPTS
        config.RATE_LIMIT_MAX_ATTEMPTS = monkeypatch_limit
        try:
            for _ in range(monkeypatch_limit):
                resp = client.post("/api/auth/login", json={
                    "email": "test@example.com", "password": "x"
                })
                assert resp.status_code == 403
            resp = client.post("/api/auth/login", json={
                "email": "test@example.com", "password": "x"
            })
            assert resp.status_code == 429
        finally:
            config.RATE_LIMIT_MAX_ATTEMPTS = original_max

    def test_register_rate_limited(self, client):
        monkeypatch_limit = 2
        original_max = config.RATE_LIMIT_MAX_ATTEMPTS
        config.RATE_LIMIT_MAX_ATTEMPTS = monkeypatch_limit
        try:
            for _ in range(monkeypatch_limit):
                resp = client.post("/api/auth/register", json={
                    "email": "test@example.com", "password": "x",
                    "full_name": "Test",
                })
                assert resp.status_code == 403
            resp = client.post("/api/auth/register", json={
                "email": "test@example.com", "password": "x",
                "full_name": "Test",
            })
            assert resp.status_code == 429
        finally:
            config.RATE_LIMIT_MAX_ATTEMPTS = original_max

    def test_password_reset_request_rate_limited(self, client):
        monkeypatch_limit = 2
        original_max = config.RATE_LIMIT_MAX_ATTEMPTS
        config.RATE_LIMIT_MAX_ATTEMPTS = monkeypatch_limit
        try:
            for _ in range(monkeypatch_limit):
                resp = client.post("/api/auth/password-reset/request", json={
                    "email": "test@example.com"
                })
                assert resp.status_code == 403
            resp = client.post("/api/auth/password-reset/request", json={
                "email": "test@example.com"
            })
            assert resp.status_code == 429
        finally:
            config.RATE_LIMIT_MAX_ATTEMPTS = original_max

    def test_auth_rate_limit_returns_arabic_error(self, client):
        original_max = config.RATE_LIMIT_MAX_ATTEMPTS
        config.RATE_LIMIT_MAX_ATTEMPTS = 1
        try:
            client.post("/api/auth/login", json={
                "email": "x@x.com", "password": "x"
            })
            resp = client.post("/api/auth/login", json={
                "email": "x@x.com", "password": "x"
            })
            assert resp.status_code == 429
            assert "طلبات كثيرة" in resp.get_json()["error"]
        finally:
            config.RATE_LIMIT_MAX_ATTEMPTS = original_max


# ---------------------------------------------------------------------------
# P1-2: HSTS header
# ---------------------------------------------------------------------------

class TestP12HSTS:
    """Strict-Transport-Security يُضاف فقط عند NIBRAS_HSTS_ENABLED=1."""

    def test_hsts_absent_by_default(self, client):
        r = client.get("/api/health")
        assert "Strict-Transport-Security" not in r.headers

    def test_hsts_present_when_enabled(self, client, monkeypatch):
        monkeypatch.setattr(config, "HSTS_ENABLED", True)
        r = client.get("/api/health")
        assert "Strict-Transport-Security" in r.headers
        assert "max-age=31536000" in r.headers["Strict-Transport-Security"]
        assert "includeSubDomains" in r.headers["Strict-Transport-Security"]


# ---------------------------------------------------------------------------
# P1-3: Cache-Control: no-store
# ---------------------------------------------------------------------------

class TestP13CacheControl:
    """المسارات الحساسة تحصل على Cache-Control: no-store."""

    def test_auth_me_has_no_store(self, client):
        from app import services_auth

        profile = services_auth.create_user_with_role(
            email="cache-test@test.local", password="test-password-123",
            full_name="اختبار التخزين", role_code="citizen",
            role_status="active", user_status="active",
        )
        token = services_auth.create_access_token(profile.id)[0]
        r = client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert r.status_code == 200
        assert "no-store" in r.headers.get("Cache-Control", "")

    def test_notifications_has_no_store(self, client):
        from app import services_auth

        profile = services_auth.create_user_with_role(
            email="cache-notif@test.local", password="test-password-123",
            full_name="اختبار الإشعارات", role_code="citizen",
            role_status="active", user_status="active",
        )
        token = services_auth.create_access_token(profile.id)[0]
        r = client.get("/api/notifications", headers={
            "Authorization": f"Bearer {token}"
        })
        assert r.status_code == 200
        assert "no-store" in r.headers.get("Cache-Control", "")

    def test_admin_endpoints_have_no_store(self, client):
        from app import services_auth

        admin = services_auth.create_user_with_role(
            email="cache-admin@test.local", password="test-password-123",
            full_name="إدارة اختبار", role_code="admin",
            role_status="active", user_status="active",
        )
        token = services_auth.create_access_token(admin.id)[0]
        r = client.get("/api/admin/texts", headers={
            "Authorization": f"Bearer {token}"
        })
        assert "no-store" in r.headers.get("Cache-Control", "")

    def test_public_endpoints_no_cache_header(self, client):
        """المسارات العامة (مثل المكتبة) لا تحصل على no-store."""
        r = client.get("/api/health")
        assert "Cache-Control" not in r.headers


# ---------------------------------------------------------------------------
# P1-4: AI question length limit
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_ai_rate_limits():
    _ai_attempts.clear()
    yield
    _ai_attempts.clear()


class TestP14AILengthLimit:
    """سؤال الذكاء الاصطناعي محصور بحد أقصى 2000 حرف."""

    def test_short_question_accepted(self, client):
        r = client.post("/api/ai/explain", json={
            "question": "ما هو القانون المدني؟",
            "mode": "grounded",
        })
        assert r.status_code != 400

    def test_empty_question_rejected(self, client):
        r = client.post("/api/ai/explain", json={
            "question": "",
            "mode": "grounded",
        })
        assert r.status_code == 400

    def test_oversized_question_rejected(self, client):
        long_question = "سؤال " * 500  # ~3000 chars
        r = client.post("/api/ai/explain", json={
            "question": long_question,
            "mode": "grounded",
        })
        assert r.status_code == 400
        assert "2000" in r.get_json()["error"]

    def test_exact_limit_question_accepted(self, client):
        exact_question = "أ" * 2000
        r = client.post("/api/ai/explain", json={
            "question": exact_question,
            "mode": "general",
        })
        # قد يرجع 200 أو 503 (fail-open مع noop provider) لكن ليس 400
        assert r.status_code != 400

    def test_configurable_limit(self, client, monkeypatch):
        monkeypatch.setattr(config, "AI_QUESTION_MAX_LENGTH", 10)
        r = client.post("/api/ai/explain", json={
            "question": "أ" * 11,
            "mode": "general",
        })
        assert r.status_code == 400
