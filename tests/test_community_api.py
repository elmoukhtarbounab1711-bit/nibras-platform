"""
اختبارات مجتمع نبراس (API) — المرحلة 6 (قرار D-024).

القراءة عامة (فئات/منشورات/تفصيل مع my_reactions للمُصادَق)، الكتابة
بمصادقة وحدّ معدل، تعديل/حذف لمالك المحتوى فقط، التفاعلات تبديلية،
والبلاغات تدخل طابور إشراف إداري بإجراءات hide/remove/dismiss مسجَّلة.
"""
import pytest

from app import config, services_auth
from app.routes.community import _attempts as _community_attempts

PASSWORD = "test-password-123"
POST = {"category_id": 1, "title": "سؤال حول العقد", "body": "محتوى السؤال الكامل"}


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    _community_attempts.clear()
    yield
    _community_attempts.clear()


def _headers(user):
    token = services_auth.create_access_token(user.id)[0]
    return {"Authorization": f"Bearer {token}"}


def _user(email, role_code="citizen"):
    return services_auth.create_user_with_role(
        email=email, password=PASSWORD, full_name="مستخدم مجتمع",
        role_code=role_code, role_status="active", user_status="active",
    )


def _admin():
    return _user("admin-community@nibras.test", "admin")


def _create_post(client, headers, **overrides):
    data = dict(POST)
    data.update(overrides)
    return client.post("/api/community/posts", json=data, headers=headers)


def _create_user_post(client, email="author@nibras.test"):
    user = _user(email)
    post = _create_post(client, _headers(user)).get_json()
    return user, post


def test_categories_public(client):
    resp = client.get("/api/community/categories")
    assert resp.status_code == 200
    items = resp.get_json()
    assert len(items) == 6
    assert items[0]["slug"] == "dostouri"
    assert all("post_count" in i for i in items)


def test_posts_list_empty(client):
    assert client.get("/api/community/posts").get_json() == []


def test_create_post_requires_auth(client):
    assert client.post("/api/community/posts", json=POST).status_code == 401


def test_create_post_validation(client):
    h = _headers(_user("v@nibras.test"))
    assert client.post("/api/community/posts", json={"title": "x", "body": ""},
                       headers=h).status_code == 400
    assert client.post("/api/community/posts", json={"title": "", "body": "y"},
                       headers=h).status_code == 400
    assert client.post("/api/community/posts",
                       json={**POST, "category_id": 999}, headers=h).status_code == 400


def test_create_post_and_read(client):
    h = _headers(_user("author@nibras.test"))
    resp = _create_post(client, h)
    assert resp.status_code == 201
    post = resp.get_json()
    assert post["author_is_verified"] is False
    assert post["comment_count"] == 0
    assert post["reactions"] == {}
    assert post["my_reactions"] == []

    listed = client.get("/api/community/posts").get_json()
    assert len(listed) == 1
    assert listed[0]["id"] == post["id"]
    assert "my_reactions" not in listed[0]

    detail = client.get(f"/api/community/posts/{post['id']}").get_json()
    assert detail["comments"] == []

    cats = client.get("/api/community/categories").get_json()
    assert cats[0]["post_count"] == 1


def test_post_edit_delete_owner_only(client):
    author, post = _create_user_post(client)
    other = _user("other@nibras.test")

    assert client.put(f"/api/community/posts/{post['id']}",
                      json={"title": "معدَّل", "body": "محتوى جديد"},
                      headers=_headers(other)).status_code == 403
    resp = client.put(f"/api/community/posts/{post['id']}",
                      json={"title": "معدَّل", "body": "محتوى جديد"},
                      headers=_headers(author))
    assert resp.status_code == 200 and resp.get_json()["title"] == "معدَّل"

    assert client.delete(f"/api/community/posts/{post['id']}",
                         headers=_headers(other)).status_code == 403
    resp = client.delete(f"/api/community/posts/{post['id']}", headers=_headers(author))
    assert resp.status_code == 200 and resp.get_json()["status"] == "removed"

    assert client.get(f"/api/community/posts/{post['id']}").status_code == 404
    assert client.get("/api/community/posts").get_json() == []
    # المؤلف يرى منشوره المحذوف في التفصيل (قرار D-024)
    owner_view = client.get(f"/api/community/posts/{post['id']}",
                            headers=_headers(author)).get_json()
    assert owner_view["status"] == "removed"


def test_comments_flow(client):
    _author, post = _create_user_post(client)
    c1 = _user("c1@nibras.test")
    c2 = _user("c2@nibras.test")
    h1, h2 = _headers(c1), _headers(c2)

    resp = client.post(f"/api/community/posts/{post['id']}/comments",
                       json={"body": "تعليق أول"}, headers=h1)
    assert resp.status_code == 201
    assert resp.get_json()["author_name"] == "مستخدم مجتمع"
    cid1 = resp.get_json()["id"]
    client.post(f"/api/community/posts/{post['id']}/comments",
                json={"body": "تعليق ثان"}, headers=h2)

    detail = client.get(f"/api/community/posts/{post['id']}").get_json()
    assert detail["comment_count"] == 2
    assert [c["body"] for c in detail["comments"]] == ["تعليق أول", "تعليق ثان"]

    assert client.put(f"/api/community/posts/{post['id']}/comments/{cid1}",
                      json={"body": "معدَّل"}, headers=h2).status_code == 403
    resp = client.put(f"/api/community/posts/{post['id']}/comments/{cid1}",
                      json={"body": "معدَّل"}, headers=h1)
    assert resp.status_code == 200 and resp.get_json()["body"] == "معدَّل"

    assert client.delete(f"/api/community/posts/{post['id']}/comments/{cid1}",
                         headers=h2).status_code == 403
    resp = client.delete(f"/api/community/posts/{post['id']}/comments/{cid1}",
                         headers=h1)
    assert resp.status_code == 200

    detail = client.get(f"/api/community/posts/{post['id']}").get_json()
    assert detail["comment_count"] == 1
    assert [c["id"] for c in detail["comments"]] == [detail["comments"][0]["id"]]


def test_comment_body_required(client):
    author, post = _create_user_post(client)
    resp = client.post(f"/api/community/posts/{post['id']}/comments",
                       json={"body": "  "}, headers=_headers(author))
    assert resp.status_code == 400


def test_reactions_toggle_and_my_reactions(client):
    _author, post = _create_user_post(client)
    reactor = _user("reactor@nibras.test")
    h = _headers(reactor)

    resp = client.post(f"/api/community/posts/{post['id']}/react",
                       json={"type": "like"}, headers=h)
    assert resp.status_code == 200
    assert resp.get_json() == {"reacted": True, "reactions": {"like": 1}}

    resp = client.post(f"/api/community/posts/{post['id']}/react",
                       json={"type": "like"}, headers=h)
    assert resp.get_json()["reacted"] is False
    assert resp.get_json()["reactions"] == {}

    client.post(f"/api/community/posts/{post['id']}/react",
                json={"type": "helpful"}, headers=h)
    detail = client.get(f"/api/community/posts/{post['id']}",
                        headers=_headers(reactor)).get_json()
    assert detail["my_reactions"] == ["helpful"]
    assert detail["reactions"] == {"helpful": 1}
    assert detail["reaction_count"] == 1

    assert client.post(f"/api/community/posts/{post['id']}/react",
                       json={"type": "wow"}, headers=h).status_code == 400


def test_detail_without_token_has_no_my_reactions(client):
    _author, post = _create_user_post(client)
    detail = client.get(f"/api/community/posts/{post['id']}").get_json()
    assert "my_reactions" not in detail


def test_post_list_filter_and_pagination(client):
    cat2 = _user("cat2@nibras.test")
    for i in range(3):
        _create_user_post(client, email=f"p{i}@nibras.test")
    _create_post(client, _headers(cat2), category_id=2)

    all_posts = client.get("/api/community/posts").get_json()
    assert len(all_posts) == 4
    filtered = client.get("/api/community/posts", query_string={"category": 2}).get_json()
    assert len(filtered) == 1 and filtered[0]["category_id"] == 2
    page = client.get("/api/community/posts", query_string={"limit": 2, "offset": 2}).get_json()
    assert len(page) == 2
    assert client.get("/api/community/posts",
                      query_string={"category": "abc"}).status_code == 400


def test_report_and_moderation_flow(client):
    author, post = _create_user_post(client)
    reporter = _user("reporter@nibras.test")
    rh = _headers(reporter)

    assert client.post("/api/community/report",
                       json={"target_type": "post", "target_id": post["id"],
                             "reason": "محتوى مسيء"},
                       headers=_headers(author)).status_code == 403

    resp = client.post("/api/community/report",
                       json={"target_type": "post", "target_id": post["id"],
                             "reason": "محتوى مسيء"}, headers=rh)
    assert resp.status_code == 201
    report_id = resp.get_json()["id"]

    dup = client.post("/api/community/report",
                      json={"target_type": "post", "target_id": post["id"],
                            "reason": "مرة أخرى"}, headers=rh)
    assert dup.status_code == 200 and dup.get_json()["already_reported"] is True

    assert client.post("/api/community/report",
                       json={"target_type": "post", "target_id": 999,
                             "reason": "x"}, headers=rh).status_code == 404
    assert client.post("/api/community/report",
                       json={"target_type": "post", "target_id": post["id"],
                             "reason": ""}, headers=rh).status_code == 400
    assert client.post("/api/community/report",
                       json={"target_type": "bad", "target_id": 1,
                             "reason": "x"}, headers=rh).status_code == 400
    assert client.post("/api/community/report", json={}).status_code == 401

    admin_h = _headers(_admin())
    queue = client.get("/api/admin/moderation-queue", headers=admin_h).get_json()["reports"]
    assert len(queue) == 1
    assert queue[0]["target"]["title"] == POST["title"]
    assert queue[0]["reason"] == "محتوى مسيء"
    assert queue[0]["reporter_name"] == "مستخدم مجتمع"

    resp = client.post(f"/api/admin/moderation/{report_id}/action",
                       json={"action": "hide"}, headers=admin_h)
    assert resp.status_code == 200
    assert client.get(f"/api/community/posts/{post['id']}").status_code == 404
    assert client.get("/api/community/posts").get_json() == []
    assert client.get("/api/admin/moderation-queue", headers=admin_h).get_json()["reports"] == []

    resp = client.post(f"/api/admin/moderation/{report_id}/action",
                       json={"action": "dismiss"}, headers=admin_h)
    assert resp.status_code == 409
    assert client.post("/api/admin/moderation/999/action",
                       json={"action": "dismiss"}, headers=admin_h).status_code == 404
    assert client.post(f"/api/admin/moderation/{report_id}/action",
                       json={"action": "dismiss"}, headers=_headers(_user("cit@nibras.test"))).status_code == 403
    assert client.post(f"/api/admin/moderation/{report_id}/action",
                       json={"action": "dismiss"}).status_code == 401


def test_report_comment_then_remove(client):
    _author, post = _create_user_post(client)
    commenter = _user("cc@nibras.test")
    comment = client.post(f"/api/community/posts/{post['id']}/comments",
                          json={"body": "تعليق مسيء"},
                          headers=_headers(commenter)).get_json()
    report = client.post("/api/community/report",
                         json={"target_type": "comment", "target_id": comment["id"],
                               "reason": "إساءة"},
                         headers=_headers(_user("rep2@nibras.test"))).get_json()

    admin_h = _headers(_admin())
    queue = client.get("/api/admin/moderation-queue", headers=admin_h).get_json()["reports"]
    assert queue[0]["target"]["body"] == "تعليق مسيء"

    client.post(f"/api/admin/moderation/{report['id']}/action",
                json={"action": "remove"}, headers=admin_h)
    detail = client.get(f"/api/community/posts/{post['id']}").get_json()
    assert [c["id"] for c in detail["comments"]] == []
    assert detail["comment_count"] == 0


def test_report_professional_profile_and_moderation_limits(client):
    lawyer = services_auth.create_user_with_role(
        email="prof@nibras.test", password=PASSWORD, full_name="محامٍ",
        role_code="lawyer", role_status="pending_verification", user_status="active",
    )
    profile = client.post("/api/professionals/profile",
                          json={"profession_type": "lawyer", "city": "الرباط",
                                "bio": "محامٍ", "specialties": []},
                          headers=_headers(lawyer)).get_json()

    report = client.post("/api/community/report",
                         json={"target_type": "professional_profile",
                               "target_id": profile["id"], "reason": "بيانات مضللة"},
                         headers=_headers(_user("rp3@nibras.test"))).get_json()
    admin_h = _headers(_admin())
    assert client.post(f"/api/admin/moderation/{report['id']}/action",
                       json={"action": "hide"}, headers=admin_h).status_code == 400
    resp = client.post(f"/api/admin/moderation/{report['id']}/action",
                       json={"action": "dismiss"}, headers=admin_h)
    assert resp.status_code == 200 and resp.get_json()["status"] == "dismissed"


def test_post_rate_limit(client, monkeypatch):
    monkeypatch.setattr(config, "COMMUNITY_RATE_LIMIT_MAX_REQUESTS", 2)
    h = _headers(_user("spam@nibras.test"))
    assert _create_post(client, h).status_code == 201
    assert _create_post(client, h).status_code == 201
    assert _create_post(client, h).status_code == 429
