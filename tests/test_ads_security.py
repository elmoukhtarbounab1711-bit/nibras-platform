"""
اختبارات أمان نظام الإعلانات (Security §7).

تغطي: إدارة المزوّدين، التحقق الأمني للسكريبتات، الإعدادات العامة،
ربط الفتحات بالمزوّدين، والحماية من حقن السكريبتات الضارة.
"""
import pytest

from app import services_ads
from app.database import db_session
from app.services_ads import (
    AdError, APPROVED_AD_DOMAINS, BLOCKED_AD_PATTERNS,
    ADULT_CONTENT_PATTERNS,
)
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
        "script_url": "https://adsterra.com/ad.js",
    })
    assert pid > 0
    providers = services_ads.list_providers()
    assert any(p["id"] == pid for p in providers)


def test_create_provider_with_script_tag(fresh_db):
    admin = _admin()
    pid = services_ads.create_provider(admin.id, {
        "name": "Custom Ad",
        "slug": "custom-ad",
        "script_tag": "<script src='https://adsterra.com/ad.js'></script>",
    })
    assert pid > 0


def test_create_provider_duplicate_slug_raises(fresh_db):
    admin = _admin()
    services_ads.create_provider(admin.id, {
        "name": "Provider A", "slug": "prov-a",
        "script_url": "https://adsterra.com/ad-a.js",
    })
    with pytest.raises(AdError):
        services_ads.create_provider(admin.id, {
            "name": "Provider B", "slug": "prov-a",
            "script_url": "https://adsterra.com/ad-b.js",
        })


def test_create_provider_no_script_raises(fresh_db):
    admin = _admin()
    with pytest.raises(AdError):
        services_ads.create_provider(admin.id, {
            "name": "No Script", "slug": "no-script",
        })


def test_create_provider_unapproved_domain_raises(fresh_db):
    admin = _admin()
    with pytest.raises(AdError):
        services_ads.create_provider(admin.id, {
            "name": "Evil", "slug": "evil",
            "script_url": "https://evil-domain.com/payload.js",
        })


def test_update_provider(fresh_db):
    admin = _admin()
    pid = services_ads.create_provider(admin.id, {
        "name": "Old Name", "slug": "old",
        "script_url": "https://adsterra.com/old.js",
    })
    services_ads.update_provider(admin.id, pid, {"name": "New Name"})
    providers = services_ads.list_providers()
    p = next((x for x in providers if x["id"] == pid), None)
    assert p is not None
    assert p["name"] == "New Name"


def test_delete_provider(fresh_db):
    admin = _admin()
    pid = services_ads.create_provider(admin.id, {
        "name": "To Delete", "slug": "del",
        "script_url": "https://adsterra.com/del.js",
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
        "name": "P1", "slug": "p1",
        "script_url": "https://adsterra.com/p1.js",
    })
    p2 = services_ads.create_provider(admin.id, {
        "name": "P2", "slug": "p2",
        "script_url": "https://adsterra.com/p2.js",
    })
    result = services_ads.set_provider_status_bulk(admin.id, [p1, p2], False)
    assert result["succeeded"] == 2
    providers = services_ads.list_providers()
    for p in providers:
        if p["id"] in (p1, p2):
            assert p["enabled"] == 0


# =====================================================================
# ربط الفتحات بالمزوّدين
# =====================================================================

def test_link_provider_to_slot(fresh_db):
    admin = _admin()
    pid = services_ads.create_provider(admin.id, {
        "name": "Link Test", "slug": "link-test",
        "script_url": "https://adsterra.com/link.js",
    })
    link_id = services_ads.link_provider_to_slot(1, pid, "{}", 0)
    assert link_id > 0
    sp = services_ads.list_slot_providers(1)
    assert any(x["provider_id"] == pid for x in sp)


def test_unlink_provider_from_slot(fresh_db):
    admin = _admin()
    pid = services_ads.create_provider(admin.id, {
        "name": "Unlink", "slug": "unlink",
        "script_url": "https://adsterra.com/unlink.js",
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


def test_is_ads_enabled_default_true(fresh_db):
    assert services_ads.is_ads_enabled() is True


def test_is_ads_enabled_after_set(fresh_db):
    services_ads.set_setting("ads_enabled", "false")
    assert services_ads.is_ads_enabled() is False
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
    services_ads._validate_script_security(
        "https://adsterra.com/ad.js", ""
    )
    services_ads._validate_script_security(
        "", "<script src='https://adsterra.com/ad.js'></script>"
    )


def test_validate_script_security_unapproved_domain_rejected(fresh_db):
    with pytest.raises(AdError):
        services_ads._validate_script_security(
            "https://malicious-site.com/payload.js", ""
        )


def test_validate_script_security_deceptive_domain_rejected(fresh_db):
    with pytest.raises(AdError):
        services_ads._validate_script_security(
            "https://adsterra.com.evil.com/payload.js", ""
        )


def test_validate_script_security_deceptive_suffix_rejected(fresh_db):
    with pytest.raises(AdError):
        services_ads._validate_script_security(
            "https://evil-adsterra.com/payload.js", ""
        )


def test_validate_script_security_deceptive_at_sign_rejected(fresh_db):
    with pytest.raises(AdError):
        services_ads._validate_script_security(
            "https://evil.com@adsterra.com/payload.js", ""
        )


def test_validate_script_security_blocked_pattern_popunder(fresh_db):
    with pytest.raises(AdError):
        services_ads._validate_script_security(
            "https://adsterra.com/popunder.js", ""
        )


def test_validate_script_security_popunder_in_tag(fresh_db):
    with pytest.raises(AdError):
        services_ads._validate_script_security(
            "", "<script>popunder_init();</script>"
        )


def test_validate_script_security_eval(fresh_db):
    with pytest.raises(AdError):
        services_ads._validate_script_security(
            "", "<script>eval('alert(1)')</script>"
        )


def test_validate_script_security_document_write(fresh_db):
    with pytest.raises(AdError):
        services_ads._validate_script_security(
            "", "<script>document.write('x')</script>"
        )


def test_validate_script_security_innerHTML(fresh_db):
    with pytest.raises(AdError):
        services_ads._validate_script_security(
            "", "<script>el.innerHTML = 'x'</script>"
        )


def test_validate_script_security_outerHTML(fresh_db):
    with pytest.raises(AdError):
        services_ads._validate_script_security(
            "", "<script>el.outerHTML = 'x'</script>"
        )


def test_validate_script_security_insertAdjacentHTML(fresh_db):
    with pytest.raises(AdError):
        services_ads._validate_script_security(
            "", "<script>el.insertAdjacentHTML('beforeend', 'x')</script>"
        )


def test_validate_script_security_window_location(fresh_db):
    with pytest.raises(AdError):
        services_ads._validate_script_security(
            "", "<script>window.location='https://evil.com'</script>"
        )


def test_validate_script_security_document_cookie(fresh_db):
    with pytest.raises(AdError):
        services_ads._validate_script_security(
            "", "<script>document.cookie='stolen'</script>"
        )


def test_validate_script_security_string_setTimeout(fresh_db):
    with pytest.raises(AdError):
        services_ads._validate_script_security(
            "", '<script>setTimeout("alert(1)", 0)</script>'
        )


def test_validate_script_security_string_setInterval(fresh_db):
    with pytest.raises(AdError):
        services_ads._validate_script_security(
            "", "<script>setInterval('x()', 1000)</script>"
        )


def test_validate_script_security_function_setTimeout_ok(fresh_db):
    services_ads._validate_script_security(
        "", "<script>setTimeout(function(){}, 0)</script>"
    )


def test_validate_script_security_empty_ok(fresh_db):
    services_ads._validate_script_security("")
    services_ads._validate_script_security(None)


def test_validate_script_security_adult_content_blocked(fresh_db):
    with pytest.raises(AdError):
        services_ads._validate_script_security(
            "https://adsterra.com/porn-ads.js", ""
        )


def test_validate_script_security_xxx_blocked(fresh_db):
    with pytest.raises(AdError):
        services_ads._validate_script_security(
            "https://adsterra.com/xxx-content.js", ""
        )


def test_validate_script_security_javascript_url(fresh_db):
    with pytest.raises(AdError):
        services_ads._validate_script_security(
            "javascript:alert(1)", ""
        )


def test_approved_domains_list_not_empty(fresh_db):
    assert len(APPROVED_AD_DOMAINS) > 0
    assert "adsterra.com" in APPROVED_AD_DOMAINS


def test_blocked_patterns_list_not_empty(fresh_db):
    assert len(BLOCKED_AD_PATTERNS) > 0


def test_adult_content_patterns_not_empty(fresh_db):
    assert len(ADULT_CONTENT_PATTERNS) > 0


def test_subdomains_of_approved_accepted(fresh_db):
    services_ads._validate_script_security(
        "https://cdn.adsterra.com/ad.js", ""
    )


# =====================================================================
# تسليم الإعلانات (serve_slot)
# =====================================================================

def test_serve_slot_returns_providers(fresh_db):
    admin = _admin()
    pid = services_ads.create_provider(admin.id, {
        "name": "Serve Test", "slug": "serve-test",
        "script_url": "https://adsterra.com/serve.js",
        "enabled": True,
        "is_approved": True,
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
