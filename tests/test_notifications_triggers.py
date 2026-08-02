"""
اختبارات محفِّزات الإشعارات (المرحلة 12 — قرار D-030).

تُنشأ الإشعارات تلقائيًا ضمن معاملة الفعل: نتائج التحقق المهني
(قبول/رفض)، تفاعلات المجتمع (تعليق/تفاعل) بلا إشعار لفعل الذات،
وقرارات الإشراف (حجب/إزالة). تُفحص عبر تدفقات API كاملة.
"""

from app import services_auth

PASSWORD = "test-password-123"
POST = {"category_id": 1, "title": "سؤال حول العقد", "body": "محتوى السؤال"}


def _headers(user):
    token = services_auth.create_access_token(user.id)[0]
    return {"Authorization": f"Bearer {token}"}


def _user(email, role_code="citizen"):
    return services_auth.create_user_with_role(
        email=email, password=PASSWORD, full_name="مستخدم",
        role_code=role_code, role_status="active", user_status="active",
    )


def _admin():
    return _user("admin-notif@nibras.test", "admin")


def _pending_professional(email):
    return services_auth.create_user_with_role(
        email=email, password=PASSWORD, full_name="محامٍ",
        role_code="lawyer", role_status="pending_verification",
        user_status="active",
    )


def _notifications(client, user):
    return client.get("/api/notifications", headers=_headers(user)).get_json()


# ---------------------------------------------------------------------------
# التحقق المهني
# ---------------------------------------------------------------------------

def test_approve_verification_creates_notification(client):
    lawyer = _pending_professional("law-appr@nibras.test")
    client.post("/api/professionals/profile",
                json={"profession_type": "lawyer", "city": "الرباط",
                      "bio": "محامٍ", "specialties": []},
                headers=_headers(lawyer))
    resp = client.post(f"/api/admin/verification/{lawyer.id}/approve",
                       headers=_headers(_admin()))
    assert resp.status_code == 200

    body = _notifications(client, lawyer)
    assert body["total"] == 1
    item = body["notifications"][0]
    assert item["type"] == "verification.approved"
    assert item["is_read"] is False
    assert item["actor_id"] is not None


def test_reject_verification_creates_notification_with_reason(client):
    lawyer = _pending_professional("law-rej@nibras.test")
    client.post("/api/professionals/profile",
                json={"profession_type": "lawyer", "city": "فاس",
                      "bio": "محامٍ", "specialties": []},
                headers=_headers(lawyer))
    resp = client.post(f"/api/admin/verification/{lawyer.id}/reject",
                       json={"reason": "الوثيقة غير مقروءة"},
                       headers=_headers(_admin()))
    assert resp.status_code == 200

    item = _notifications(client, lawyer)["notifications"][0]
    assert item["type"] == "verification.rejected"
    assert "الوثيقة غير مقروءة" in item["body"]


# ---------------------------------------------------------------------------
# المجتمع: تعليق وتفاعل
# ---------------------------------------------------------------------------

def test_comment_creates_notification_to_post_author(client):
    author = _user("author-c@nibras.test")
    post = client.post("/api/community/posts", json=POST,
                       headers=_headers(author)).get_json()

    commenter = _user("commenter@nibras.test")
    resp = client.post(f"/api/community/posts/{post['id']}/comments",
                       json={"body": "تعليق جديد"}, headers=_headers(commenter))
    assert resp.status_code == 201

    body = _notifications(client, author)
    assert body["total"] == 1
    item = body["notifications"][0]
    assert item["type"] == "community.comment"
    assert item["link"] == f"/posts/{post['id']}"
    assert item["actor_id"] == commenter.id
    # المعلِّق نفسه لا يتلقى إشعارًا عن تعليقه
    assert _notifications(client, commenter)["total"] == 0


def test_reaction_creates_notification_to_post_author(client):
    author = _user("author-r@nibras.test")
    post = client.post("/api/community/posts", json=POST,
                       headers=_headers(author)).get_json()

    reactor = _user("reactor@nibras.test")
    resp = client.post(f"/api/community/posts/{post['id']}/react",
                       json={"type": "like"}, headers=_headers(reactor))
    assert resp.status_code == 200 and resp.get_json()["reacted"] is True

    item = _notifications(client, author)["notifications"][0]
    assert item["type"] == "community.reaction"
    assert item["actor_id"] == reactor.id
    assert _notifications(client, reactor)["total"] == 0


def test_no_notification_for_own_comment_or_reaction(client):
    author = _user("self@nibras.test")
    h = _headers(author)
    post = client.post("/api/community/posts", json=POST, headers=h).get_json()
    client.post(f"/api/community/posts/{post['id']}/comments",
                json={"body": "تعليقي على منشوري"}, headers=h)
    client.post(f"/api/community/posts/{post['id']}/react",
                json={"type": "helpful"}, headers=h)
    assert _notifications(client, author)["total"] == 0


def test_unreact_does_not_duplicate_notification(client):
    author = _user("author-ur@nibras.test")
    post = client.post("/api/community/posts", json=POST,
                       headers=_headers(author)).get_json()
    reactor = _user("reactor-ur@nibras.test")
    h = _headers(reactor)

    client.post(f"/api/community/posts/{post['id']}/react",
                json={"type": "like"}, headers=h)
    # إلغاء التفاعل لا يُنشئ إشعارًا
    resp = client.post(f"/api/community/posts/{post['id']}/react",
                       json={"type": "like"}, headers=h)
    assert resp.get_json()["reacted"] is False
    assert _notifications(client, author)["total"] == 1


# ---------------------------------------------------------------------------
# الإشراف
# ---------------------------------------------------------------------------

def test_moderation_remove_notifies_content_owner(client):
    author = _user("author-mod@nibras.test")
    post = client.post("/api/community/posts", json=POST,
                       headers=_headers(author)).get_json()
    report = client.post("/api/community/report",
                         json={"target_type": "post", "target_id": post["id"],
                               "reason": "محتوى مسيء"},
                         headers=_headers(_user("rep-mod@nibras.test"))).get_json()

    admin = _admin()
    admin_h = _headers(admin)
    resp = client.post(f"/api/admin/moderation/{report['id']}/action",
                       json={"action": "remove"}, headers=admin_h)
    assert resp.status_code == 200

    item = _notifications(client, author)["notifications"][0]
    assert item["type"] == "moderation.content_removed"
    assert item["actor_id"] == admin.id


def test_moderation_dismiss_does_not_notify(client):
    author = _user("author-dis@nibras.test")
    post = client.post("/api/community/posts", json=POST,
                       headers=_headers(author)).get_json()
    report = client.post("/api/community/report",
                         json={"target_type": "post", "target_id": post["id"],
                               "reason": "بلاغ بلا أساس"},
                         headers=_headers(_user("rep-dis@nibras.test"))).get_json()
    client.post(f"/api/admin/moderation/{report['id']}/action",
                json={"action": "dismiss"}, headers=_headers(_admin()))
    assert _notifications(client, author)["total"] == 0
