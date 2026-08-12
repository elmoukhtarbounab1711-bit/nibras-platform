"""
اختبارات نظام الإعلانات (API) — المرحلة 9 (قرار D-027).

خدمة عامة (serve) + تتبع انطباع/نقرة بمصادقة اختيارية، وإدارة حملات إدارية
(إنشاء/تعديل/حذف) مع إحصائيات، واستهداف v1 (فتحة + تواريخ فقط — وثيقة 15 §5).
"""
import pytest

from app import services_auth
from app.database import db_session

PASSWORD = "test-password-123"


@pytest.fixture(autouse=True)
def _isolate_uploads(tmp_path, monkeypatch):
    from app import config
    monkeypatch.setattr(config, "UPLOAD_DIR", str(tmp_path / "uploads"))
    yield


def _headers(user):
    token = services_auth.create_access_token(user.id)[0]
    return {"Authorization": f"Bearer {token}"}


def _user(email, role_code="citizen"):
    return services_auth.create_user_with_role(
        email=email, password=PASSWORD, full_name="مستخدم إعلانات",
        role_code=role_code, role_status="active", user_status="active",
    )


def _admin():
    return _user("admin-ads@nibras.test", "admin")


def _campaign_data(**overrides):
    data = {
        "slot_id": 1,
        "campaign_type": "general",
        "advertiser_name": "شركة نبراس",
        "creative_url": "https://ads.nibras.ma/banner.png",
        "target_url": "https://nibras.ma/landing",
    }
    data.update(overrides)
    return data


def _create_campaign(client, headers, **overrides):
    resp = client.post("/api/admin/ads/campaigns",
                       json=_campaign_data(**overrides), headers=headers)
    assert resp.status_code == 201
    return resp.get_json()["id"]


def _serve(client, slot="library_sidebar"):
    resp = client.get(f"/api/ads/serve?slot={slot}")
    assert resp.status_code == 200
    return resp.get_json()["campaign"]


def test_serve_requires_slot(client):
    assert client.get("/api/ads/serve").status_code == 400


def test_serve_unknown_slot(client):
    assert client.get("/api/ads/serve?slot=nope").status_code == 400


def test_serve_empty(client):
    assert _serve(client) is None


def test_admin_routes_require_admin(client):
    assert client.get("/api/admin/ads/campaigns").status_code == 401
    citizen_h = _headers(_user("cit@nibras.test"))
    assert client.get("/api/admin/ads/campaigns",
                      headers=citizen_h).status_code == 403
    assert client.post("/api/admin/ads/campaigns", json={},
                       headers=citizen_h).status_code == 403


def test_admin_slots(client):
    admin_h = _headers(_admin())
    _create_campaign(client, admin_h)
    resp = client.get("/api/admin/ads/slots", headers=admin_h)
    slots = resp.get_json()["slots"]
    assert len(slots) == 3
    assert [s["slug"] for s in slots] == [
        "library_sidebar", "search_results_top", "directory_listing_top",
    ]
    assert slots[0]["active_campaigns"] == 1


def test_create_and_serve_campaign(client):
    admin_h = _headers(_admin())
    cid = _create_campaign(client, admin_h)
    campaign = _serve(client)
    assert campaign["campaign_id"] == cid
    assert campaign["type"] == "general"
    assert campaign["sponsored"] is False
    assert campaign["creative_url"] == "https://ads.nibras.ma/banner.png"
    assert campaign["profile_id"] is None


def test_sponsored_flag_for_non_general(client):
    admin_h = _headers(_admin())
    _create_campaign(client, admin_h, campaign_type="sponsored")
    assert _serve(client)["sponsored"] is True


def test_serve_prefers_oldest_active(client):
    admin_h = _headers(_admin())
    first = _create_campaign(client, admin_h)
    _create_campaign(client, admin_h, advertiser_name="ثانية")
    assert _serve(client)["campaign_id"] == first


def test_invalid_campaign_type(client):
    admin_h = _headers(_admin())
    resp = client.post("/api/admin/ads/campaigns",
                       json=_campaign_data(campaign_type="bogus"),
                       headers=admin_h)
    assert resp.status_code == 400


def test_invalid_url_rejected(client):
    admin_h = _headers(_admin())
    resp = client.post("/api/admin/ads/campaigns",
                       json=_campaign_data(creative_url="javascript:alert(1)"),
                       headers=admin_h)
    assert resp.status_code == 400
    resp = client.post("/api/admin/ads/campaigns",
                       json=_campaign_data(target_url="not-a-url"),
                       headers=admin_h)
    assert resp.status_code == 400


def test_missing_advertiser_name(client):
    admin_h = _headers(_admin())
    resp = client.post("/api/admin/ads/campaigns",
                       json=_campaign_data(advertiser_name=""), headers=admin_h)
    assert resp.status_code == 400


def test_unknown_slot_id(client):
    admin_h = _headers(_admin())
    resp = client.post("/api/admin/ads/campaigns",
                       json=_campaign_data(slot_id=99), headers=admin_h)
    assert resp.status_code == 400


def test_professional_promotion_requires_verified(client, fresh_db):
    admin_h = _headers(_admin())
    resp = client.post(
        "/api/admin/ads/campaigns",
        json=_campaign_data(campaign_type="professional_promotion"),
        headers=admin_h,
    )
    assert resp.status_code == 400

    lawyer = services_auth.create_user_with_role(
        email="lawyer-ads@nibras.test", password=PASSWORD,
        full_name="محامية", role_code="lawyer", role_status="active",
        user_status="active",
    )
    with db_session() as conn:
        pid = conn.execute(
            "INSERT INTO professional_profiles (user_id, profession_type, "
            "verification_status, created_at) "
            "VALUES (?, 'lawyer', 'pending', datetime('now'))",
            (lawyer.id,),
        ).lastrowid

    resp = client.post(
        "/api/admin/ads/campaigns",
        json=_campaign_data(campaign_type="professional_promotion",
                            profile_id=pid),
        headers=admin_h,
    )
    assert resp.status_code == 400

    with db_session() as conn:
        conn.execute(
            "UPDATE professional_profiles SET verification_status = "
            "'verified' WHERE id = ?", (pid,),
        )
    cid = _create_campaign(client, admin_h,
                           campaign_type="professional_promotion",
                           profile_id=pid)
    campaign = _serve(client)
    assert campaign["campaign_id"] == cid
    assert campaign["profile_id"] == pid
    assert campaign["type"] == "professional_promotion"


def test_impression_click_stats(client):
    admin_h = _headers(_admin())
    cid = _create_campaign(client, admin_h)
    assert client.post(f"/api/ads/{cid}/impression").status_code == 201
    assert client.post(f"/api/ads/{cid}/impression").status_code == 201
    assert client.post(f"/api/ads/{cid}/click").status_code == 201
    resp = client.get("/api/admin/ads/campaigns", headers=admin_h)
    campaign = next(c for c in resp.get_json()["campaigns"] if c["id"] == cid)
    assert campaign["impressions"] == 2
    assert campaign["clicks"] == 1
    assert campaign["ctr"] == 0.5
    assert campaign["slot_name"] == "شريط المكتبة الجانبي"


def test_track_unknown_campaign(client):
    assert client.post("/api/ads/9999/impression").status_code == 404
    assert client.post("/api/ads/9999/click").status_code == 404


def test_impression_logs_user_id_when_authenticated(client):
    admin_h = _headers(_admin())
    cid = _create_campaign(client, admin_h)
    user = _user("viewer@nibras.test")
    resp = client.post(f"/api/ads/{cid}/impression",
                       headers=_headers(user))
    assert resp.status_code == 201
    with db_session() as conn:
        row = conn.execute(
            "SELECT user_id FROM ad_events WHERE campaign_id = ? "
            "AND event_type = 'impression'", (cid,),
        ).fetchone()
    assert row["user_id"] == user.id


def test_date_range_gating(client):
    admin_h = _headers(_admin())
    cid = _create_campaign(client, admin_h, starts_at="2099-01-01")
    assert _serve(client) is None
    resp = client.put(f"/api/admin/ads/campaigns/{cid}",
                      json={"starts_at": None}, headers=admin_h)
    assert resp.status_code == 200
    assert _serve(client)["campaign_id"] == cid


def test_update_date_conflict(client):
    admin_h = _headers(_admin())
    cid = _create_campaign(client, admin_h)
    resp = client.put(
        f"/api/admin/ads/campaigns/{cid}",
        json={"starts_at": "2026-09-10", "ends_at": "2026-09-01"},
        headers=admin_h,
    )
    assert resp.status_code == 400


def test_pause_hides_campaign(client):
    admin_h = _headers(_admin())
    cid = _create_campaign(client, admin_h)
    resp = client.put(f"/api/admin/ads/campaigns/{cid}",
                      json={"status": "paused"}, headers=admin_h)
    assert resp.status_code == 200
    assert _serve(client) is None


def test_delete_campaign(client):
    admin_h = _headers(_admin())
    cid = _create_campaign(client, admin_h)
    client.post(f"/api/ads/{cid}/impression")
    resp = client.delete(f"/api/admin/ads/campaigns/{cid}", headers=admin_h)
    assert resp.status_code == 200
    assert _serve(client) is None
    assert client.get("/api/admin/ads/campaigns",
                      headers=admin_h).get_json()["campaigns"] == []


# ---------------------------------------------------------------------------
# الاستهداف الفئوي (المرحلة 19 — قرار D-037)
# ---------------------------------------------------------------------------

def _cat_id(table, slug):
    with db_session() as conn:
        return conn.execute(
            f"SELECT id FROM {table} WHERE slug = ?", (slug,)
        ).fetchone()["id"]


def _serve_ctx(client, category_type, category_id, slot="library_sidebar"):
    resp = client.get(
        f"/api/ads/serve?slot={slot}&category_type={category_type}"
        f"&category_id={category_id}"
    )
    assert resp.status_code == 200
    return resp.get_json()["campaign"]


def test_create_campaign_with_category_target(client):
    admin_h = _headers(_admin())
    lib_cat = _cat_id("categories", "madani")
    cid = _create_campaign(client, admin_h,
                           target_category_type="library",
                           target_category_id=lib_cat)
    with db_session() as conn:
        row = conn.execute(
            "SELECT target_category_type, target_category_id "
            "FROM ad_campaigns WHERE id = ?", (cid,),
        ).fetchone()
    assert (row["target_category_type"], row["target_category_id"]) == \
        ("library", lib_cat)


def test_serve_with_category_context(client):
    admin_h = _headers(_admin())
    lib_cat = _cat_id("categories", "madani")
    _create_campaign(client, admin_h, advertiser_name="مستهدفة",
                     target_category_type="library",
                     target_category_id=lib_cat)
    assert _serve(client) is None
    campaign = _serve_ctx(client, "library", lib_cat)
    assert campaign["advertiser_name"] == "مستهدفة"
    other = _cat_id("marketplace_categories", "tijari")
    assert _serve_ctx(client, "marketplace", other) is None


def test_serve_falls_back_to_general(client):
    admin_h = _headers(_admin())
    lib_cat = _cat_id("categories", "madani")
    _create_campaign(client, admin_h, advertiser_name="عامة")
    campaign = _serve_ctx(client, "library", lib_cat)
    assert campaign["advertiser_name"] == "عامة"


def test_targeted_wins_over_general_api(client):
    admin_h = _headers(_admin())
    lib_cat = _cat_id("categories", "madani")
    generic = _create_campaign(client, admin_h, advertiser_name="عامة")
    targeted = _create_campaign(client, admin_h, advertiser_name="مستهدفة",
                                target_category_type="library",
                                target_category_id=lib_cat)
    campaign = _serve_ctx(client, "library", lib_cat)
    assert campaign["campaign_id"] == targeted
    assert campaign["campaign_id"] != generic


def test_update_targeting_via_api(client):
    admin_h = _headers(_admin())
    lib_cat = _cat_id("categories", "madani")
    cid = _create_campaign(client, admin_h)
    resp = client.put(
        f"/api/admin/ads/campaigns/{cid}",
        json={"target_category_type": "library",
              "target_category_id": lib_cat},
        headers=admin_h,
    )
    assert resp.status_code == 200
    assert _serve(client) is None
    assert _serve_ctx(client, "library", lib_cat)["campaign_id"] == cid
    resp = client.put(
        f"/api/admin/ads/campaigns/{cid}",
        json={"target_category_type": ""}, headers=admin_h,
    )
    assert resp.status_code == 200
    assert _serve(client)["campaign_id"] == cid


def test_invalid_targeting_rejected(client):
    admin_h = _headers(_admin())
    resp = client.post("/api/admin/ads/campaigns",
                       json=_campaign_data(target_category_type="bogus",
                                           target_category_id=1),
                       headers=admin_h)
    assert resp.status_code == 400
    resp = client.post("/api/admin/ads/campaigns",
                       json=_campaign_data(target_category_type="library"),
                       headers=admin_h)
    assert resp.status_code == 400
    resp = client.post("/api/admin/ads/campaigns",
                       json=_campaign_data(target_category_type="library",
                                           target_category_id=9999),
                       headers=admin_h)
    assert resp.status_code == 400
