"""
اختبارات خدمات نظام الإعلانات (services_ads) — المرحلة 9 (قرار D-027).

خدمة (serve) بلا كتابة، تسجيل أحداث الانطباع/النقرة، وإدارة الحملات مع
إحصائيات، والتحقق من أنواع الحملات والروابط والتواريخ.
"""
import pytest

from app import services_ads
from app.database import db_session
from app.services_ads import AdError
from app.services_auth import create_user_with_role

PASSWORD = "test-password-123"


def _admin():
    return create_user_with_role(
        "admin-ads@nibras.test", PASSWORD, "مدير إعلانات", "admin",
    )


def _data(**overrides):
    data = {
        "slot_id": 1,
        "campaign_type": "general",
        "advertiser_name": "شركة اختبار",
        "creative_url": "https://ads.example.com/x.png",
        "target_url": "https://example.com/",
    }
    data.update(overrides)
    return data


def _create(admin=None, **overrides):
    admin = admin or _admin()
    return services_ads.create_campaign(admin.id, _data(**overrides))


def test_ensure_slots_seeded(fresh_db):
    slots = services_ads.list_slots()
    assert len(slots) == 3
    assert all(s["active_campaigns"] == 0 for s in slots)


def test_serve_none_when_empty(fresh_db):
    assert services_ads.serve("library_sidebar") is None


def test_serve_unknown_slot_raises(fresh_db):
    with pytest.raises(AdError):
        services_ads.serve("nope")


def test_create_serve_roundtrip(fresh_db):
    admin = _admin()
    cid = _create(admin)
    campaign = services_ads.serve("library_sidebar")
    assert campaign["campaign_id"] == cid
    assert campaign["sponsored"] is False


def test_serve_active_date_range(fresh_db):
    admin = _admin()
    _create(admin, starts_at="2099-01-01")
    assert services_ads.serve("library_sidebar") is None
    _create(admin, advertiser_name="مثالي")
    assert services_ads.serve("library_sidebar")["campaign_id"] == 2


def test_sponsored_and_professional_flags(fresh_db):
    admin = _admin()
    _create(admin, campaign_type="sponsored")
    assert services_ads.serve("library_sidebar")["sponsored"] is True


def test_log_event_and_stats(fresh_db):
    admin = _admin()
    cid = _create(admin)
    services_ads.log_event(cid, "impression")
    services_ads.log_event(cid, "impression", user_id=admin.id)
    services_ads.log_event(cid, "click")
    campaign = services_ads.list_campaigns_admin()[0]
    assert campaign["impressions"] == 2
    assert campaign["clicks"] == 1
    assert campaign["ctr"] == 0.5


def test_log_event_invalid_type(fresh_db):
    with pytest.raises(AdError):
        services_ads.log_event(1, "view")


def test_log_event_unknown_campaign(fresh_db):
    with pytest.raises(AdError):
        services_ads.log_event(999, "impression")


def test_create_validation(fresh_db):
    admin = _admin()
    with pytest.raises(AdError):
        services_ads.create_campaign(admin.id, {})
    with pytest.raises(AdError):
        _create(admin, campaign_type="bogus")
    with pytest.raises(AdError):
        _create(admin, creative_url="javascript:alert(1)")
    with pytest.raises(AdError):
        _create(admin, target_url="ftp://x")
    with pytest.raises(AdError):
        _create(admin, starts_at="2026-09-10", ends_at="2026-09-01")
    with pytest.raises(AdError):
        _create(admin, status="archived")


def test_professional_promotion_requires_verified_profile(fresh_db):
    admin = _admin()
    lawyer = create_user_with_role(
        "lawyer-ads@nibras.test", PASSWORD, "محام", "lawyer",
        role_status="active",
    )
    with db_session() as conn:
        pid = conn.execute(
            "INSERT INTO professional_profiles (user_id, profession_type, "
            "verification_status, created_at) "
            "VALUES (?, 'lawyer', 'pending', datetime('now'))",
            (lawyer.id,),
        ).lastrowid
    with pytest.raises(AdError):
        _create(admin, campaign_type="professional_promotion", profile_id=pid)
    with pytest.raises(AdError):
        _create(admin, campaign_type="professional_promotion")
    with db_session() as conn:
        conn.execute(
            "UPDATE professional_profiles SET verification_status = "
            "'verified' WHERE id = ?", (pid,),
        )
    cid = _create(admin, campaign_type="professional_promotion", profile_id=pid)
    campaign = services_ads.serve("library_sidebar")
    assert campaign["campaign_id"] == cid
    assert campaign["profile_id"] == pid


def test_update_campaign_and_delete(fresh_db):
    admin = _admin()
    cid = _create(admin)
    services_ads.log_event(cid, "impression")
    services_ads.update_campaign(admin.id, cid, {"status": "paused"})
    assert services_ads.serve("library_sidebar") is None
    services_ads.delete_campaign(admin.id, cid)
    with db_session() as conn:
        assert conn.execute(
            "SELECT COUNT(*) AS c FROM ad_events"
        ).fetchone()["c"] == 0
        assert conn.execute(
            "SELECT COUNT(*) AS c FROM ad_campaigns"
        ).fetchone()["c"] == 0


def test_update_unknown_campaign(fresh_db):
    admin = _admin()
    with pytest.raises(AdError):
        services_ads.update_campaign(admin.id, 999, {"status": "paused"})
    with pytest.raises(AdError):
        services_ads.delete_campaign(admin.id, 999)


def test_audit_log_records_ads_actions(fresh_db):
    admin = _admin()
    cid = _create(admin)
    services_ads.update_campaign(admin.id, cid, {"status": "paused"})
    services_ads.delete_campaign(admin.id, cid)
    with db_session() as conn:
        actions = [
            r["action"]
            for r in conn.execute(
                "SELECT action FROM admin_audit_log WHERE action LIKE "
                "'ads.%' ORDER BY id"
            )
        ]
    assert actions == ["ads.create", "ads.update", "ads.delete"]


# ---------------------------------------------------------------------------
# الاستهداف الفئوي (المرحلة 19 — قرار D-037)
# ---------------------------------------------------------------------------

def _category_id(table: str, slug: str) -> int:
    with db_session() as conn:
        return conn.execute(
            f"SELECT id FROM {table} WHERE slug = ?", (slug,)
        ).fetchone()["id"]


def test_create_with_category_target(fresh_db):
    admin = _admin()
    lib_cat = _category_id("categories", "madani")
    cid = _create(
        admin, target_category_type="library",
        target_category_id=lib_cat,
    )
    with db_session() as conn:
        row = conn.execute(
            "SELECT target_category_type, target_category_id "
            "FROM ad_campaigns WHERE id = ?", (cid,),
        ).fetchone()
    assert row["target_category_type"] == "library"
    assert row["target_category_id"] == lib_cat


def test_targeted_served_only_in_matching_context(fresh_db):
    admin = _admin()
    lib_cat = _category_id("categories", "madani")
    _create(admin, advertiser_name="مستهدفة مدني",
            target_category_type="library", target_category_id=lib_cat)
    # بلا سياق فئة: لا تُعرض الحملة المستهدفة
    assert services_ads.serve("library_sidebar") is None
    # بسياق مطابق: تُعرض
    campaign = services_ads.serve(
        "library_sidebar", "library", lib_cat
    )
    assert campaign["advertiser_name"] == "مستهدفة مدني"
    # بسياق مختلف (نوع فئة آخر): لا تُعرض — حتى لو تطابق المعرّف رقميًا
    other_cat = _category_id("marketplace_categories", "tijari")
    assert services_ads.serve("library_sidebar", "marketplace", other_cat) is None


def test_targeted_wins_over_general(fresh_db):
    admin = _admin()
    lib_cat = _category_id("categories", "madani")
    _create(admin, advertiser_name="عامة", status="active")
    cid = _create(admin, advertiser_name="مستهدفة مدني",
                  target_category_type="library", target_category_id=lib_cat)
    campaign = services_ads.serve("library_sidebar", "library", lib_cat)
    assert campaign["advertiser_name"] == "مستهدفة مدني"
    assert campaign["campaign_id"] == cid


def test_general_fallback_to_untargeted(fresh_db):
    admin = _admin()
    lib_cat = _category_id("categories", "madani")
    _create(admin, advertiser_name="عامة عامة")
    campaign = services_ads.serve("library_sidebar", "library", lib_cat)
    assert campaign["advertiser_name"] == "عامة عامة"


def test_target_validation(fresh_db):
    admin = _admin()
    with pytest.raises(AdError):
        _create(admin, target_category_type="bogus",
                target_category_id=1)
    with pytest.raises(AdError):
        _create(admin, target_category_type="library")
    with pytest.raises(AdError):
        _create(admin, target_category_id=1)
    with pytest.raises(AdError):
        _create(admin, target_category_type="library",
                target_category_id=9999)
    with pytest.raises(AdError):
        _create(admin, target_category_type="library",
                target_category_id="madani")


def test_update_clears_target(fresh_db):
    admin = _admin()
    lib_cat = _category_id("categories", "madani")
    cid = _create(admin, target_category_type="library",
                  target_category_id=lib_cat)
    services_ads.update_campaign(admin.id, cid, {"target_category_type": ""})
    campaign = services_ads.serve("library_sidebar")
    assert campaign["advertiser_name"] == "شركة اختبار"
    services_ads.update_campaign(
        admin.id, cid, {"target_category_type": "jurisprudence",
                        "target_category_id": _category_id(
                            "jurisprudence_categories", "madani")}
    )
    with db_session() as conn:
        row = conn.execute(
            "SELECT target_category_type FROM ad_campaigns WHERE id = ?",
            (cid,),
        ).fetchone()
    assert row["target_category_type"] == "jurisprudence"
