"""
اختبارات أمان نظام الإعلانات (Security §7).

تغطي: إدارة المزوّدين، التحقق الأمني للسكريبتات، الإعدادات العامة،
ربط الفتحات بالمزوّدين، والحماية من حقن السكريبتات الضارة.
"""
import pytest

from app import services_ads
from app.database import db_session
from app.services_ads import AdError, APPROVED_AD_DOMAINS, BLOCKED_AD_PATTERNS
from app.services_auth import create_user_with_role

PASSWORD = "test-password-123"


def _admin():
    return create_user_with_role(
        "admin-ads-sec@nibras.test", PASSWORD, "مدير إعلانات أمان", "admin",
    )


# =====================================================================
# إدارة المزوّدين
# =====================================================================

def test_create_provider(fresh_db):
    admin = _admin()
    pid = services_ads.create_provider(admin.id, {
        "name": "Adsterra",
        "slug": "adsterra",
        "provider_type": "adsterra",
        "script_html": "<script src='https://adsterra.com/ad.js'></script>",
    })
    assert pid > 0
    providers = services_ads.list_providers()
    assert any(p["id"] == pid for p in providers)


def test_create_provider_duplicate_slug_raises(fresh_db):
    admin = _admin()
    services_ads.create_provider(admin.id, {
        "name": "Provider A", "slug": "prov-a", "provider_type": "custom",
    })
    with pytest.raises(AdError):
        services_ads.create_provider(admin.id, {
            "name": "Provider B", "slug": "prov-a", "provider_type": "custom",
        })


def test_update_provider(fresh_db):
    admin = _admin()
    pid = services_ads.create_provider(admin.id, {
        "name": "Old Name", "slug": "old", "provider_type": "custom",
    })
    services_ads.update_provider(admin.id, pid, {"name": "New Name"})
    providers = services_ads.list_providers()
    p = next((x for x in providers if x["id"] == pid), None)
    assert p is not None
    assert p["name"] == "New Name"


def test_delete_provider(fresh_db):
    admin = _admin()
    pid = services_ads.create_provider(admin.id, {
        "name": "To Delete", "slug": "del", "provider_type": "custom",
    })
    services_ads.delete_provider(admin.id, pid)
    providers = services_ads.list_providers()
    assert not any(p["id"] == pid for p in providers)


def test_delete_nonexistent_provider_raises(fresh_db):
    admin = _admin()
    with pytest.raises(AdError):
        services_ads.delete_provider(admin.id, 99999)


def test_bulk_status_enable_disable(fresh_db):
    admin = _admin()
    p1 = services_ads.create_provider(admin.id, {
        "name": "P1", "slug": "p1", "provider_type": "custom",
    })
    p2 = services_ads.create_provider(admin.id, {
        "name": "P2", "slug": "p2", "provider_type": "custom",
    })
    result = services_ads.set_provider_status_bulk(admin.id, [p1, p2], False)
    assert result["updated"] == 2
    providers = services_ads.list_providers()
    for p in providers:
        if p["id"] in (p1, p2):
            assert p["is_enabled"] is False


# =====================================================================
# ربط الفتحات بالمزوّدين
# =====================================================================

def test_link_provider_to_slot(fresh_db):
    admin = _admin()
    pid = services_ads.create_provider(admin.id, {
        "name": "Link Test", "slug": "link-test", "provider_type": "custom",
        "script_html": "<script src='https://adsterra.com/ad.js'></script>",
    })
    link_id = services_ads.link_provider_to_slot(1, pid, "{}", 0)
    assert link_id > 0
    sp = services_ads.list_slot_providers(1)
    assert any(x["provider_id"] == pid for x in sp)


def test_unlink_provider_from_slot(fresh_db):
    admin = _admin()
    pid = services_ads.create_provider(admin.id, {
        "name": "Unlink", "slug": "unlink", "provider_type": "custom",
    })
    services_ads.link_provider_to_slot(1, pid, "{}", 0)
    services_ads.unlink_provider_from_slot(1, pid)
    sp = services_ads.list_slot_providers(1)
    assert not any(x["provider_id"] == pid for x in sp)


# =====================================================================
# الإعدادات العامة
# =====================================================================

def test_set_and_get_setting(fresh_db):
    services_ads.set_setting("ads_enabled", "true")
    settings = services_ads.get_settings()
    assert settings.get("ads_enabled") == "true"


def test_is_ads_enabled_default_false(fresh_db):
    assert services_ads.is_ads_enabled() is False


def test_is_ads_enabled_after_set(fresh_db):
    services_ads.set_setting("ads_enabled", "true")
    assert services_ads.is_ads_enabled() is True


def test_should_show_ads_premium_respects_no_premium(fresh_db):
    services_ads.set_setting("ads_enabled", "true")
    services_ads.set_setting("ads_no_premium", "true")
    assert services_ads.should_show_ads(is_premium=True) is False
    assert services_ads.should_show_ads(is_premium=False) is True


def test_should_show_ads_disabled(fresh_db):
    services_ads.set_setting("ads_enabled", "false")
    assert services_ads.should_show_ads(is_premium=False) is False


# =====================================================================
# التحقق الأمني للسكريبتات (Security §7)
# =====================================================================

def test_validate_script_security_clean(fresh_db):
    html = "<script src='https://adsterra.com/ad.js'></script>"
    services_ads._validate_script_security(html)


def test_validate_script_security_unapproved_domain(fresh_db):
    html = "<script src='https://malicious-site.com/payload.js'></script>"
    with pytest.raises(AdError):
        services_ads._validate_script_security(html)


def test_validate_script_security_blocked_pattern(fresh_db):
    html = "<script>eval('alert(1)')</script>"
    with pytest.raises(AdError):
        services_ads._validate_script_security(html)


def test_validate_script_security_popunder_blocked(fresh_db):
    html = "<script>popunder_init();</script>"
    with pytest.raises(AdError):
        services_ads._validate_script_security(html)


def test_validate_script_security_empty_ok(fresh_db):
    services_ads._validate_script_security("")
    services_ads._validate_script_security(None)


def test_approved_domains_list_not_empty(fresh_db):
    assert len(APPROVED_AD_DOMAINS) > 0
    assert "adsterra.com" in APPROVED_AD_DOMAINS


def test_blocked_patterns_list_not_empty(fresh_db):
    assert len(BLOCKED_AD_PATTERNS) > 0


# =====================================================================
# تسليم الإعلانات (serve_slot)
# =====================================================================

def test_serve_slot_returns_providers(fresh_db):
    admin = _admin()
    pid = services_ads.create_provider(admin.id, {
        "name": "Serve Test", "slug": "serve-test", "provider_type": "custom",
        "script_html": "<script src='https://adsterra.com/ad.js'></script>",
    })
    services_ads.link_provider_to_slot(1, pid, '{"width":300,"height":250}', 0)
    providers = services_ads.serve_slot("library_sidebar")
    assert len(providers) >= 1
    assert any(p["provider_id"] == pid for p in providers)


def test_serve_slot_empty_when_no_providers(fresh_db):
    providers = services_ads.serve_slot("library_sidebar")
    assert providers == []


def test_serve_slot_unknown_slug(fresh_db):
    providers = services_ads.serve_slot("nonexistent_slot")
    assert providers == []
