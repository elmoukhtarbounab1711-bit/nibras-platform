"""
اختبارات العمليات الإدارية الجماعية (المرحلة 15 — قرار D-033).

تغطي حزم العمليات عبر واجهة HTTP: قبول/رفض جماعي للتحقق، معالجة جماعية
لبلاغات الإشراف، حذف/تحديث جماعي للنصوص والمواد، تغيير حالة جماعي
لحملات الإعلانات، وحذف جماعي لقوالب السوق — مع شكل الاستجابة الموحّد
{action,total,succeeded,failed,results} والنجاح الجزئي لكل معرّف،
وتسجيل كل عنصر في admin_audit_log.
"""
import io

import pytest

from app import config, services_admin, services_auth
from app.database import db_session

PASSWORD = "test-password-123"
POST = {"category_id": 1, "title": "سؤال حول العقد", "body": "محتوى السؤال الكامل"}


@pytest.fixture(autouse=True)
def _isolate_uploads(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "UPLOAD_DIR", str(tmp_path / "uploads"))
    yield


@pytest.fixture()
def admin_headers(fresh_db):
    admin = services_auth.create_user_with_role(
        email="admin-bulk@nibras.test", password=PASSWORD, full_name="مسؤول",
        role_code="admin", role_status="active", user_status="active",
    )
    token = services_auth.create_access_token(admin.id)[0]
    return {"Authorization": f"Bearer {token}"}


def _headers(user):
    token = services_auth.create_access_token(user.id)[0]
    return {"Authorization": f"Bearer {token}"}


def _user(email, role_code="citizen"):
    return services_auth.create_user_with_role(
        email=email, password=PASSWORD, full_name="مستخدم",
        role_code=role_code, role_status="active", user_status="active",
    )


def _professional(email):
    return services_auth.create_user_with_role(
        email=email, password=PASSWORD, full_name="محامي",
        role_code="lawyer", role_status="pending_verification", user_status="active",
    )


def _text_ids(client):
    return [t["id"] for t in client.get("/api/texts").get_json()]


def _notifications(user_id):
    with db_session() as conn:
        rows = conn.execute(
            "SELECT type FROM notifications WHERE user_id = ? ORDER BY id",
            (user_id,),
        ).fetchall()
        return [r["type"] for r in rows]


# ---------------------------------------------------------------------------
# قبول/رفض جماعي للتحقق
# ---------------------------------------------------------------------------

def test_bulk_approve_multiple_pending(client, admin_headers):
    ids = [_professional(f"b-approve-{i}@nibras.test").id for i in range(3)]

    r = client.post("/api/admin/verification/bulk",
                    json={"action": "approve", "user_ids": ids},
                    headers=admin_headers)
    assert r.status_code == 200
    data = r.get_json()
    assert data["action"] == "verification.approve"
    assert data["total"] == 3 and data["succeeded"] == 3 and data["failed"] == 0

    statuses = {
        r["code"]: r["status"]
        for uid in ids for r in services_auth.get_user_roles(uid)
    }
    assert statuses["lawyer"] == "active"
    queue = client.get("/api/admin/verification-queue",
                       headers=admin_headers).get_json()["requests"]
    assert queue == []
    for uid in ids:
        assert "verification.approved" in _notifications(uid)


def test_bulk_approve_partial_when_already_decided(client, admin_headers):
    approved = _professional("b-approve-done@nibras.test")
    pending = _professional("b-approve-pending@nibras.test")
    client.post(f"/api/admin/verification/{approved.id}/approve",
                headers=admin_headers)

    r = client.post("/api/admin/verification/bulk",
                    json={"action": "approve",
                          "user_ids": [approved.id, pending.id]},
                    headers=admin_headers)
    data = r.get_json()
    assert data["succeeded"] == 1 and data["failed"] == 1
    by_id = {res["id"]: res for res in data["results"]}
    assert by_id[pending.id]["status"] == "ok"
    assert by_id[approved.id]["status"] == "error"
    assert "لم يعد" in by_id[approved.id]["message"]


def test_bulk_approve_partial_when_missing(client, admin_headers):
    pending = _professional("b-approve-only@nibras.test")
    r = client.post("/api/admin/verification/bulk",
                    json={"action": "approve", "user_ids": [pending.id, 99999]},
                    headers=admin_headers)
    data = r.get_json()
    assert data["succeeded"] == 1 and data["failed"] == 1
    missing = next(x for x in data["results"] if x["id"] == 99999)
    assert missing["status"] == "error" and "غير موجود" in missing["message"]


def test_bulk_reject_requires_shared_reason(client, admin_headers):
    p = _professional("b-reject-noreason@nibras.test")
    r = client.post("/api/admin/verification/bulk",
                    json={"action": "reject", "user_ids": [p.id]},
                    headers=admin_headers)
    assert r.status_code == 400
    assert "سبب" in r.get_json()["error"]
    assert client.get("/api/admin/verification-queue",
                      headers=admin_headers).get_json()["requests"] != []


def test_bulk_reject_multiple_with_reason(client, admin_headers):
    ids = [_professional(f"b-reject-{i}@nibras.test").id for i in range(2)]
    r = client.post("/api/admin/verification/bulk",
                    json={"action": "reject", "user_ids": ids,
                          "reason": "وثائق ناقصة"},
                    headers=admin_headers)
    assert r.status_code == 200
    assert r.get_json()["succeeded"] == 2
    with db_session() as conn:
        rows = conn.execute(
            "SELECT user_id, role_status, rejection_reason FROM user_roles "
            "JOIN roles ON roles.id = user_roles.role_id "
            "WHERE roles.code = 'lawyer' AND user_id IN (?, ?)",
            (ids[0], ids[1]),
        ).fetchall()
    assert all(row["role_status"] == "rejected"
               and row["rejection_reason"] == "وثائق ناقصة" for row in rows)
    for uid in ids:
        assert "verification.rejected" in _notifications(uid)


def test_bulk_verification_invalid_action(client, admin_headers):
    r = client.post("/api/admin/verification/bulk",
                    json={"action": "bogus", "user_ids": [1]},
                    headers=admin_headers)
    assert r.status_code == 400


def test_bulk_verification_invalid_payload(client, admin_headers):
    cases = [
        {},
        {"action": "approve"},
        {"action": "approve", "user_ids": []},
        {"action": "approve", "user_ids": "1,2"},
        {"action": "approve", "user_ids": [1, "x"]},
        {"action": "approve", "user_ids": [0, -1]},
        {"action": "approve", "user_ids": list(range(1, services_admin.MAX_BULK_ITEMS + 2))},
    ]
    for payload in cases:
        r = client.post("/api/admin/verification/bulk", json=payload,
                        headers=admin_headers)
        assert r.status_code == 400, payload


def test_bulk_verification_requires_admin(client):
    citizen = _headers(_user("bulk-cit@nibras.test"))
    assert client.post("/api/admin/verification/bulk",
                       json={"action": "approve", "user_ids": [1]}).status_code == 401
    assert client.post("/api/admin/verification/bulk",
                       json={"action": "approve", "user_ids": [1]},
                       headers=citizen).status_code == 403


# ---------------------------------------------------------------------------
# معالجة جماعية لبلاغات الإشراف
# ---------------------------------------------------------------------------

def _report_post(client, email):
    author = _user(email)
    post = client.post("/api/community/posts", json=POST,
                       headers=_headers(author)).get_json()
    report = client.post("/api/community/report",
                         json={"target_type": "post", "target_id": post["id"],
                               "reason": "إساءة"},
                         headers=_headers(_user(f"rep-{email}"))).get_json()
    return author, post, report


def test_bulk_dismiss_multiple(client, admin_headers):
    reports = [_report_post(client, f"d-{i}@nibras.test")[2]["id"] for i in range(3)]
    r = client.post("/api/admin/moderation/bulk",
                    json={"action": "dismiss", "report_ids": reports},
                    headers=admin_headers)
    assert r.status_code == 200
    assert r.get_json()["action"] == "moderation.dismiss"
    assert r.get_json()["succeeded"] == 3
    assert client.get("/api/admin/moderation-queue",
                      headers=admin_headers).get_json()["reports"] == []


def test_bulk_hide_posts_hides_content_and_notifies_owner(client, admin_headers):
    author, post, report = _report_post(client, "hide@nibras.test")
    r = client.post("/api/admin/moderation/bulk",
                    json={"action": "hide", "report_ids": [report["id"]]},
                    headers=admin_headers)
    assert r.get_json()["succeeded"] == 1
    assert client.get(f"/api/community/posts/{post['id']}").status_code == 404
    assert "moderation.content_hidden" in _notifications(author.id)


def test_bulk_remove_comment(client, admin_headers):
    _author, post, _ = _report_post(client, "rmc@nibras.test")
    comment = client.post(f"/api/community/posts/{post['id']}/comments",
                          json={"body": "تعليق مسيء"},
                          headers=_headers(_user("cmt@nibras.test"))).get_json()
    report = client.post("/api/community/report",
                         json={"target_type": "comment",
                               "target_id": comment["id"], "reason": "إساءة"},
                         headers=_headers(_user("rmc-rep@nibras.test"))).get_json()
    r = client.post("/api/admin/moderation/bulk",
                    json={"action": "remove", "report_ids": [report["id"]]},
                    headers=admin_headers)
    assert r.get_json()["succeeded"] == 1
    detail = client.get(f"/api/community/posts/{post['id']}").get_json()
    assert detail["comments"] == []


def test_bulk_hide_on_professional_target_partial(client, admin_headers):
    _author, _post, report = _report_post(client, "mix@nibras.test")
    lawyer = _professional("b-prof-target@nibras.test")
    profile = client.post("/api/professionals/profile",
                          json={"profession_type": "lawyer", "city": "الرباط",
                                "bio": "محامٍ", "specialties": []},
                          headers=_headers(lawyer)).get_json()
    prof_report = client.post("/api/community/report",
                              json={"target_type": "professional_profile",
                                    "target_id": profile["id"],
                                    "reason": "بيانات مضللة"},
                              headers=_headers(_user("pp-rep@nibras.test"))).get_json()

    r = client.post("/api/admin/moderation/bulk",
                    json={"action": "hide",
                          "report_ids": [report["id"], prof_report["id"]]},
                    headers=admin_headers)
    data = r.get_json()
    assert data["succeeded"] == 1 and data["failed"] == 1
    failed = next(x for x in data["results"] if x["id"] == prof_report["id"])
    assert failed["status"] == "error"
    assert "hide/remove" in failed["message"]


def test_bulk_moderation_already_processed_partial(client, admin_headers):
    _author, _post, report = _report_post(client, "twice@nibras.test")
    client.post("/api/admin/moderation/bulk",
                json={"action": "dismiss", "report_ids": [report["id"]]},
                headers=admin_headers)
    r = client.post("/api/admin/moderation/bulk",
                    json={"action": "dismiss", "report_ids": [report["id"], 99999]},
                    headers=admin_headers)
    data = r.get_json()
    assert data["succeeded"] == 0 and data["failed"] == 2
    assert {x["id"] for x in data["results"]} == {report["id"], 99999}


def test_bulk_moderation_invalid_action(client, admin_headers):
    r = client.post("/api/admin/moderation/bulk",
                    json={"action": "explode", "report_ids": [1]},
                    headers=admin_headers)
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# حذف/تحديث جماعي للنصوص والمواد
# ---------------------------------------------------------------------------

def test_bulk_delete_texts_cascades(client, admin_headers):
    ids = _text_ids(client)
    r = client.post("/api/admin/texts/bulk-delete", json={"ids": ids},
                    headers=admin_headers)
    assert r.status_code == 200
    assert r.get_json()["succeeded"] == len(ids)
    assert client.get("/api/texts").get_json() == []
    with db_session() as conn:
        n = conn.execute("SELECT COUNT(*) AS n FROM articles").fetchone()["n"]
    assert n == 0


def test_bulk_delete_texts_partial_missing(client, admin_headers):
    ids = _text_ids(client)
    r = client.post("/api/admin/texts/bulk-delete",
                    json={"ids": ids + [99999]}, headers=admin_headers)
    data = r.get_json()
    assert data["succeeded"] == len(ids) and data["failed"] == 1
    assert client.get(f"/api/texts/{ids[0]}").status_code == 404


def test_bulk_update_texts_shared_fields(client, admin_headers):
    ids = _text_ids(client)
    r = client.post("/api/admin/texts/bulk-update",
                    json={"ids": ids, "type": "law",
                          "title": "عنوان جماعي", "source_note": "تحديث جماعي"},
                    headers=admin_headers)
    assert r.status_code == 200
    assert r.get_json()["succeeded"] == len(ids)
    for tid in ids:
        detail = client.get(f"/api/texts/{tid}").get_json()
        assert detail["type"] == "law"
        assert detail["title"] == "عنوان جماعي"
        assert detail["source_note"] == "تحديث جماعي"


def test_bulk_update_texts_invalid_shared_payload(client, admin_headers):
    ids = _text_ids(client)
    r = client.post("/api/admin/texts/bulk-update",
                    json={"ids": ids, "type": "bogus"}, headers=admin_headers)
    assert r.status_code == 400
    with db_session() as conn:
        n = conn.execute("SELECT COUNT(*) AS n FROM legal_texts").fetchone()["n"]
    assert n == len(ids)  # لم تُكتب أي تغييرات


def test_bulk_update_texts_partial_missing(client, admin_headers):
    ids = _text_ids(client)
    r = client.post("/api/admin/texts/bulk-update",
                    json={"ids": ids + [777], "title": "جديد"}, headers=admin_headers)
    data = r.get_json()
    assert data["succeeded"] == len(ids) and data["failed"] == 1


def test_bulk_delete_articles_clears_related(client, admin_headers):
    article_ids = [
        a["id"]
        for tid in _text_ids(client)
        for a in client.get(f"/api/texts/{tid}").get_json()["articles"]
    ]
    assert len(article_ids) == 2
    r = client.post("/api/admin/articles/bulk-delete", json={"ids": article_ids},
                    headers=admin_headers)
    assert r.status_code == 200
    assert r.get_json()["succeeded"] == len(article_ids)
    with db_session() as conn:
        n = conn.execute("SELECT COUNT(*) AS n FROM related_articles").fetchone()["n"]
    assert n == 0


def test_bulk_delete_articles_partial(client, admin_headers):
    tid = _text_ids(client)[0]
    aid = client.get(f"/api/texts/{tid}").get_json()["articles"][0]["id"]
    r = client.post("/api/admin/articles/bulk-delete",
                    json={"ids": [aid, 12345]}, headers=admin_headers)
    data = r.get_json()
    assert data["succeeded"] == 1 and data["failed"] == 1


def test_content_bulk_requires_admin(client):
    citizen = _headers(_user("content-bulk-cit@nibras.test"))
    for path, payload in [
        ("/api/admin/texts/bulk-delete", {"ids": [1]}),
        ("/api/admin/texts/bulk-update", {"ids": [1], "title": "x"}),
        ("/api/admin/articles/bulk-delete", {"ids": [1]}),
    ]:
        assert client.post(path, json=payload).status_code == 401
        assert client.post(path, json=payload, headers=citizen).status_code == 403


# ---------------------------------------------------------------------------
# تغيير حالة جماعي لحملات الإعلانات
# ---------------------------------------------------------------------------

def _create_campaign(client, headers, **overrides):
    data = {
        "slot_id": 1, "campaign_type": "general",
        "advertiser_name": "شركة نبراس",
        "creative_url": "https://ads.nibras.ma/b.png",
        "target_url": "https://nibras.ma/landing",
    }
    data.update(overrides)
    resp = client.post("/api/admin/ads/campaigns", json=data, headers=headers)
    assert resp.status_code == 201
    return resp.get_json()["id"]


def test_bulk_campaign_status(client, admin_headers):
    ids = [_create_campaign(client, admin_headers) for _ in range(3)]
    r = client.post("/api/admin/ads/campaigns/bulk-status",
                    json={"ids": ids, "status": "paused"}, headers=admin_headers)
    assert r.status_code == 200
    assert r.get_json()["action"] == "ads.bulk_status.paused"
    assert r.get_json()["succeeded"] == 3
    campaigns = client.get("/api/admin/ads/campaigns",
                           headers=admin_headers).get_json()["campaigns"]
    assert all(c["status"] == "paused" for c in campaigns if c["id"] in ids)


def test_bulk_campaign_status_invalid_state(client, admin_headers):
    r = client.post("/api/admin/ads/campaigns/bulk-status",
                    json={"ids": [1], "status": "archived"}, headers=admin_headers)
    assert r.status_code == 400


def test_bulk_campaign_status_partial_missing(client, admin_headers):
    cid = _create_campaign(client, admin_headers)
    r = client.post("/api/admin/ads/campaigns/bulk-status",
                    json={"ids": [cid, 888], "status": "ended"},
                    headers=admin_headers)
    data = r.get_json()
    assert data["succeeded"] == 1 and data["failed"] == 1
    campaigns = client.get("/api/admin/ads/campaigns",
                           headers=admin_headers).get_json()["campaigns"]
    assert next(c for c in campaigns if c["id"] == cid)["status"] == "ended"


# ---------------------------------------------------------------------------
# حذف جماعي لقوالب السوق
# ---------------------------------------------------------------------------

def _create_template(client, headers, title="نموذج عقد إيجار"):
    resp = client.post(
        "/api/admin/marketplace/templates",
        data={"category_id": "1", "title": title,
              "description": "وصف", "price_cents": "1500",
              "file": (io.BytesIO(b"%PDF-1.4 template"), "contract.pdf")},
        headers=headers, content_type="multipart/form-data",
    )
    assert resp.status_code == 201
    return resp.get_json()["id"]


def test_bulk_delete_templates_removes_files(client, admin_headers):
    ids = [_create_template(client, admin_headers, title=f"ق-{i}") for i in range(3)]
    files_before = set()
    for root, _dirs, files in __import__("os").walk(config.UPLOAD_DIR):
        files_before.update(files)
    assert len(files_before) == 3

    r = client.post("/api/admin/marketplace/templates/bulk-delete",
                    json={"ids": ids}, headers=admin_headers)
    assert r.status_code == 200
    assert r.get_json()["succeeded"] == 3
    assert client.get("/api/admin/marketplace/templates",
                      headers=admin_headers).get_json()["templates"] == []
    files_after = []
    for root, _dirs, files in __import__("os").walk(config.UPLOAD_DIR):
        files_after.extend(files)
    assert len(files_after) == 0


def test_bulk_delete_templates_purchased_partial(client, admin_headers):
    ok_id = _create_template(client, admin_headers, title="عادي")
    purchased_id = _create_template(client, admin_headers, title="مباع")
    buyer = _user("buyer-bulk@nibras.test")
    with db_session() as conn:
        conn.execute(
            "INSERT INTO purchases (user_id, template_id) VALUES (?, ?)",
            (buyer.id, purchased_id),
        )
    r = client.post("/api/admin/marketplace/templates/bulk-delete",
                    json={"ids": [ok_id, purchased_id]}, headers=admin_headers)
    data = r.get_json()
    assert data["succeeded"] == 1 and data["failed"] == 1
    failed = next(x for x in data["results"] if x["id"] == purchased_id)
    assert "شراءات" in failed["message"]
    with db_session() as conn:
        left = conn.execute(
            "SELECT id FROM marketplace_templates ORDER BY id"
        ).fetchall()
    assert [r["id"] for r in left] == [purchased_id]


# ---------------------------------------------------------------------------
# التدقيق
# ---------------------------------------------------------------------------

def test_bulk_actions_logged_per_item(client, admin_headers):
    ids = [_professional(f"audit-b-{i}@nibras.test").id for i in range(2)]
    client.post("/api/admin/verification/bulk",
                json={"action": "approve", "user_ids": ids},
                headers=admin_headers)
    tids = _text_ids(client)
    client.post("/api/admin/texts/bulk-delete", json={"ids": tids},
                headers=admin_headers)
    cid = _create_campaign(client, admin_headers)
    client.post("/api/admin/ads/campaigns/bulk-status",
                json={"ids": [cid], "status": "paused"}, headers=admin_headers)

    with db_session() as conn:
        rows = conn.execute(
            "SELECT action, target_type, target_id FROM admin_audit_log "
            "ORDER BY id"
        ).fetchall()
    actions = [dict(r) for r in rows]
    approve_rows = [r for r in actions if r["action"] == "verification.approve"]
    assert {r["target_id"] for r in approve_rows} == set(ids)
    delete_rows = [r for r in actions if r["action"] == "text.delete"]
    assert {r["target_id"] for r in delete_rows} == set(tids)
    ads_rows = [r for r in actions
                if r["action"] == "ads.update" and r["target_id"] == cid]
    assert len(ads_rows) == 1
