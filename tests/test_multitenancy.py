"""
اختبارات جاهزية multi-tenant (المرحلة 17 — قرار D-035).

عزل الهوية فقط: المستأجر الافتراضي يُبذر عند الإقلاع، كل مستخدم مرتبط
بمستأجره عبر users.tenant_id (ترحيل آمن للموجودين)، والتوكن JWT يحمل
Claim tenant_id، والوسيط يحل المستأجر من رأس X-Tenant-Id (إلزامي في
الوضع المفعّل ورفض 403 عند الغياب/الجهل/التعليق/التعارض — ودائمًا
مُتجاهَل في الوضع أحادي المستأجر الافتراضي). لوحة إدارية دنيا (قائمة/
إنشاء مع تدقيق). عزل بيانات الوحدات مؤجَّل لمرحلة multi-tenancy الفعلية.
"""
import pytest

from app import config, services_auth, services_tenants
from app.database import db_session

PASSWORD = "test-password-123"

_email_seq = 0


def _unique_email(prefix):
    global _email_seq
    _email_seq += 1
    return f"{prefix}-{_email_seq}@nibras.test"


def _admin():
    return services_auth.create_user_with_role(
        email=_unique_email("admin-mt"), password=PASSWORD, full_name="مسؤول",
        role_code="admin", role_status="active", user_status="active",
    )


def _citizen():
    return services_auth.create_user_with_role(
        email=_unique_email("citizen-mt"), password=PASSWORD, full_name="مواطن",
        role_code="citizen", role_status="active", user_status="active",
    )


def _bearer(profile):
    return {"Authorization": f"Bearer {services_auth.create_access_token(profile.id)[0]}"}


def _audit_actions():
    with db_session() as conn:
        rows = conn.execute(
            "SELECT admin_id, action, target_type, target_id FROM admin_audit_log"
            " ORDER BY id"
        ).fetchall()
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# البذر والترحيل على مستوى الخدمة
# ---------------------------------------------------------------------------

def test_default_tenant_seeded_at_init(fresh_db):
    tenant = services_tenants.get_tenant_by_slug(config.DEFAULT_TENANT_SLUG)
    assert tenant is not None
    assert tenant["status"] == "active"


def test_new_user_binds_default_tenant(fresh_db):
    profile = _citizen()
    assert profile.tenant_id == services_tenants.default_tenant_id()


def test_tenant_id_in_user_profile(fresh_db):
    profile = _citizen()
    assert profile.to_dict()["tenant_id"] == services_tenants.default_tenant_id()


def test_backfill_legacy_users_to_default_tenant(fresh_db):
    profile = _citizen()
    with db_session() as conn:
        conn.execute("UPDATE users SET tenant_id = NULL WHERE id = ?", (profile.id,))
    assert services_tenants.get_user_tenant_id(profile.id) is None
    services_tenants.backfill_default_tenant()
    assert services_tenants.get_user_tenant_id(profile.id) == services_tenants.default_tenant_id()


def test_backfill_is_idempotent(fresh_db):
    before = services_tenants.get_user_tenant_id(_citizen().id)
    services_tenants.backfill_default_tenant()
    services_tenants.backfill_default_tenant()
    assert services_tenants.get_user_tenant_id(_citizen().id) == before


# ---------------------------------------------------------------------------
# إدارة المستأجرين (خدمة)
# ---------------------------------------------------------------------------

def test_create_tenant_requires_name(fresh_db):
    with pytest.raises(Exception) as exc:
        services_tenants.create_tenant(_admin().id, "", "acme")
    assert exc.value.status_code == 400


def test_create_tenant_rejects_bad_slug(fresh_db):
    admin = _admin()
    for bad in ("Acme!", "-start", "end-", "has space", "x" * 64):
        with pytest.raises(Exception) as exc:
            services_tenants.create_tenant(admin.id, "اسم", bad)
        assert exc.value.status_code == 400


def test_create_tenant_normalizes_slug_case(fresh_db):
    tenant = services_tenants.create_tenant(_admin().id, "مستأجر", "ACME")
    assert tenant["slug"] == "acme"


def test_create_tenant_duplicate_slug_is_409(fresh_db):
    admin = _admin()
    slug = "acme"
    services_tenants.create_tenant(admin.id, "مستأجر", slug)
    with pytest.raises(Exception) as exc:
        services_tenants.create_tenant(admin.id, "مستأجر مكرر", slug)
    assert exc.value.status_code == 409


def test_create_tenant_audit_logged(fresh_db):
    admin = _admin()
    tenant = services_tenants.create_tenant(admin.id, "مستأجر", "acme")
    actions = _audit_actions()
    assert any(
        a["admin_id"] == admin.id and a["action"] == "tenant.create"
        and a["target_type"] == "tenant" and a["target_id"] == tenant["id"]
        for a in actions
    )


def test_list_tenants_with_user_counts(fresh_db):
    admin = _admin()
    tenant = services_tenants.create_tenant(admin.id, "مستأجر", "acme")
    with db_session() as conn:
        conn.execute(
            "UPDATE users SET tenant_id = ? WHERE id = ?", (tenant["id"], _citizen().id)
        )
    rows = {r["slug"]: r for r in services_tenants.list_tenants()}
    assert rows[config.DEFAULT_TENANT_SLUG]["user_count"] >= 1
    assert rows["acme"]["user_count"] == 1


def test_resolve_tenant_by_id_and_slug(fresh_db):
    tenant = services_tenants.create_tenant(_admin().id, "مستأجر", "acme")
    assert services_tenants.resolve_tenant(tenant["id"])["id"] == tenant["id"]
    assert services_tenants.resolve_tenant("acme")["id"] == tenant["id"]
    assert services_tenants.resolve_tenant("ACME")["id"] == tenant["id"]


def test_resolve_unknown_tenant_returns_none(fresh_db):
    assert services_tenants.resolve_tenant("no-such-tenant") is None
    assert services_tenants.resolve_tenant(99999) is None
    assert services_tenants.resolve_tenant("") is None


def test_tenant_slug_case_insensitive_unique(fresh_db):
    admin = _admin()
    services_tenants.create_tenant(admin.id, "مستأجر", "acme")
    with pytest.raises(Exception) as exc:
        services_tenants.create_tenant(admin.id, "مستأجر مكرر", "ACME")
    assert exc.value.status_code == 409


# ---------------------------------------------------------------------------
# التوكن JWT وربطه بالمستأجر
# ---------------------------------------------------------------------------

def test_access_token_carries_tenant_claim(fresh_db):
    profile = _citizen()
    token = services_auth.create_access_token(profile.id)[0]
    assert services_auth.get_token_tenant_id(token) == profile.tenant_id
    assert services_auth.decode_access_token(token) == profile.id


def test_token_tenant_id_unknown_token_is_none(fresh_db):
    assert services_auth.get_token_tenant_id("not-a-jwt") is None


def test_init_db_migrates_legacy_db_without_tenant(tmp_path):
    """قاعدة أُنشئت قبل المرحلة 17 (بلا tenants/users.tenant_id) تُهاجَر آمنًا."""
    import sqlite3

    from app import database

    old = database.DB_PATH
    path = tmp_path / "legacy.db"
    database.DB_PATH = path
    try:
        conn = sqlite3.connect(path)
        conn.executescript("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                full_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            INSERT INTO users (email, full_name, password_hash)
                VALUES ('legacy@nibras.test', 'مستخدم قديم', 'dummy-hash');
        """)
        conn.commit()
        conn.close()
        database.init_db(reset=False)
        with database.db_session() as db_conn:
            cols = {r["name"] for r in db_conn.execute("PRAGMA table_info(users)")}
            assert "tenant_id" in cols
            row = db_conn.execute(
                "SELECT tenant_id FROM users WHERE email = 'legacy@nibras.test'"
            ).fetchone()
            assert row["tenant_id"] == services_tenants.default_tenant_id()
    finally:
        database.DB_PATH = old


# ---------------------------------------------------------------------------
# وضع المستأجر الواحد الافتراضي (رأس مُتجاهَل)
# ---------------------------------------------------------------------------

def test_single_tenant_ignores_tenant_header(client):
    admin = _admin()
    r = client.get("/api/auth/me", headers={
        "Authorization": f"Bearer {services_auth.create_access_token(admin.id)[0]}",
        "X-Tenant-Id": "no-such-tenant",
    })
    assert r.status_code == 200


def test_single_tenant_public_register_requires_consent(client):
    r = client.post("/api/auth/register", json={
        "email": "new-single@nibras.test", "password": PASSWORD,
        "full_name": "جديد",
    })
    assert r.status_code == 400


def test_ready_reports_tenants_up(client):
    r = client.get("/api/ready")
    assert r.status_code == 200
    assert r.get_json()["checks"]["tenants"] == "up"


# ---------------------------------------------------------------------------
# الوضع متعدد المستأجرين (رأس X-Tenant-Id إلزامي)
# ---------------------------------------------------------------------------

def _enable_multitenant(monkeypatch):
    monkeypatch.setattr(config, "MULTI_TENANT", True)


def test_multitenant_missing_header_is_403(client, monkeypatch):
    _enable_multitenant(monkeypatch)
    profile = _citizen()
    r = client.get("/api/auth/me", headers=_bearer(profile))
    assert r.status_code == 403


def test_multitenant_unknown_header_is_403(client, monkeypatch):
    _enable_multitenant(monkeypatch)
    profile = _citizen()
    r = client.get("/api/auth/me", headers={
        **_bearer(profile), "X-Tenant-Id": "no-such-tenant",
    })
    assert r.status_code == 403


def test_multitenant_suspended_header_is_403(client, monkeypatch):
    _enable_multitenant(monkeypatch)
    admin = _admin()
    tenant = services_tenants.create_tenant(admin.id, "مستأجر", "acme")
    with db_session() as conn:
        conn.execute("UPDATE tenants SET status = 'suspended' WHERE id = ?", (tenant["id"],))
    profile = _citizen()
    with db_session() as conn:
        conn.execute("UPDATE users SET tenant_id = ? WHERE id = ?", (tenant["id"], profile.id))
    r = client.get("/api/auth/me", headers={
        **_bearer(profile), "X-Tenant-Id": "acme",
    })
    assert r.status_code == 403


def test_multitenant_mismatch_header_is_403(client, monkeypatch):
    _enable_multitenant(monkeypatch)
    admin = _admin()
    tenant = services_tenants.create_tenant(admin.id, "مستأجر", "acme")
    profile = _citizen()  # في المستأجر الافتراضي
    r = client.get("/api/auth/me", headers={
        **_bearer(profile), "X-Tenant-Id": tenant["slug"],
    })
    assert r.status_code == 403


def test_multitenant_valid_header_allowed_by_id_and_slug(client, monkeypatch):
    _enable_multitenant(monkeypatch)
    admin = _admin()
    tenant = services_tenants.create_tenant(admin.id, "مستأجر", "acme")
    profile = _citizen()
    with db_session() as conn:
        conn.execute("UPDATE users SET tenant_id = ? WHERE id = ?", (tenant["id"], profile.id))
    for header in (str(tenant["id"]), "acme"):
        r = client.get("/api/auth/me", headers={
            **_bearer(profile), "X-Tenant-Id": header,
        })
        assert r.status_code == 200
        assert r.get_json()["user"]["tenant_id"] == tenant["id"]


def test_multitenant_default_tenant_header_allowed(client, monkeypatch):
    _enable_multitenant(monkeypatch)
    profile = _citizen()  # في المستأجر الافتراضي
    default = services_tenants.default_tenant_id()
    for header in (str(default), config.DEFAULT_TENANT_SLUG):
        r = client.get("/api/auth/me", headers={
            **_bearer(profile), "X-Tenant-Id": header,
        })
        assert r.status_code == 200


def test_public_register_binds_no_tenant(client, monkeypatch):
    _enable_multitenant(monkeypatch)
    admin = _admin()
    services_tenants.create_tenant(admin.id, "مستأجر", "acme")
    r = client.post("/api/auth/register", headers={"X-Tenant-Id": "acme"}, json={
        "email": "acme-user@nibras.test", "password": PASSWORD, "full_name": "مستخدم",
    })
    assert r.status_code == 400


def test_register_rejects_unknown_tenant_header(client, monkeypatch):
    _enable_multitenant(monkeypatch)
    r = client.post("/api/auth/register", headers={"X-Tenant-Id": "no-such-tenant"}, json={
        "email": "unknown@nibras.test", "password": PASSWORD, "full_name": "مستخدم",
    })
    # الفرض المركزي (D-035) يرفض المستأجر المجهول قبل الوصول إلى المسار
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# اللوحة الإدارية
# ---------------------------------------------------------------------------

def _admin_headers():
    return _bearer(_admin())


def test_admin_tenants_list(client):
    admin = _admin()
    services_tenants.create_tenant(admin.id, "مستأجر", "acme")
    r = client.get("/api/admin/tenants", headers=_admin_headers())
    assert r.status_code == 200
    slugs = {t["slug"] for t in r.get_json()["tenants"]}
    assert config.DEFAULT_TENANT_SLUG in slugs
    assert "acme" in slugs


def test_admin_tenants_list_requires_admin(client):
    r = client.get("/api/admin/tenants", headers=_bearer(_citizen()))
    assert r.status_code == 403


def test_admin_tenants_list_requires_auth(client):
    assert client.get("/api/admin/tenants").status_code == 401


def test_admin_create_tenant(client):
    admin = _admin()
    r = client.post("/api/admin/tenants", headers=_bearer(admin), json={
        "name": "مستأجر", "slug": "acme",
    })
    assert r.status_code == 201
    tenant_id = r.get_json()["id"]
    assert services_tenants.get_tenant(tenant_id)["slug"] == "acme"
    actions = _audit_actions()
    assert any(a["action"] == "tenant.create" and a["target_id"] == tenant_id
               for a in actions)


def test_admin_create_tenant_duplicate_slug_409(client):
    admin = _admin()
    services_tenants.create_tenant(admin.id, "مستأجر", "acme")
    r = client.post("/api/admin/tenants", headers=_bearer(admin), json={
        "name": "مكرر", "slug": "acme",
    })
    assert r.status_code == 409


def test_admin_create_tenant_invalid_slug_400(client):
    r = client.post("/api/admin/tenants", headers=_admin_headers(), json={
        "name": "مستأجر", "slug": "BAD SLUG",
    })
    assert r.status_code == 400
