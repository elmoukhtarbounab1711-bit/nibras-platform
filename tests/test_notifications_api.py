"""
اختبارات إشعارات نبراس (API) — المرحلة 12 (قرار D-030).

قراءة الإشعارات الخاصة بالمستخدم: قائمة مرتَّبة (الأحدث أولًا) مع عدد
غير المقروء، عداد للشارة، تعليم مقروء منفردًا أو كلها، مع عزل الملكية
(لا يقرأ أحد إشعارات غيره) وشرط المصادقة.
"""

from app import services_auth

PASSWORD = "test-password-123"


def _headers(user):
    token = services_auth.create_access_token(user.id)[0]
    return {"Authorization": f"Bearer {token}"}


def _user(email, role_code="citizen"):
    return services_auth.create_user_with_role(
        email=email, password=PASSWORD, full_name="مستخدم إشعارات",
        role_code=role_code, role_status="active", user_status="active",
    )


def _make_notification(user_id, type_="community.comment", title="عنوان"):
    from app.database import db_session
    from app.services_notifications import notify

    with db_session() as conn:
        notify(conn, user_id, type_, title, body="نص الإشعار", link="/posts/1")


def test_requires_auth(client):
    assert client.get("/api/notifications").status_code == 401
    assert client.get("/api/notifications/unread-count").status_code == 401
    assert client.post("/api/notifications/1/read").status_code == 401
    assert client.post("/api/notifications/read-all").status_code == 401


def test_empty_list(client):
    user = _user("empty@nibras.test")
    resp = client.get("/api/notifications", headers=_headers(user))
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {"notifications": [], "total": 0, "unread_count": 0}


def test_list_and_unread_count(client):
    user = _user("list@nibras.test")
    _make_notification(user.id)
    _make_notification(user.id, type_="verification.approved", title="ثانٍ")
    h = _headers(user)

    body = client.get("/api/notifications", headers=h).get_json()
    assert body["total"] == 2
    assert body["unread_count"] == 2
    # الأحدث أولًا
    assert [n["title"] for n in body["notifications"]] == ["ثانٍ", "عنوان"]
    item = body["notifications"][0]
    assert item["is_read"] is False
    assert item["link"] == "/posts/1"
    assert "created_at" in item

    count = client.get("/api/notifications/unread-count", headers=h).get_json()
    assert count == {"unread_count": 2}


def test_mark_read_and_count(client):
    user = _user("mark@nibras.test")
    _make_notification(user.id)
    _make_notification(user.id, title="ثانٍ")
    h = _headers(user)

    items = client.get("/api/notifications", headers=h).get_json()["notifications"]
    resp = client.post(f"/api/notifications/{items[0]['id']}/read", headers=h)
    assert resp.status_code == 200
    assert resp.get_json()["is_read"] is True

    body = client.get("/api/notifications", headers=h).get_json()
    assert body["unread_count"] == 1
    assert body["notifications"][0]["is_read"] is True

    # تعليم المقروء مرارًا لا يغيّر النتيجة
    client.post(f"/api/notifications/{items[0]['id']}/read", headers=h)
    assert client.get("/api/notifications/unread-count",
                      headers=h).get_json() == {"unread_count": 1}


def test_mark_read_ownership(client):
    owner = _user("owner@nibras.test")
    other = _user("other@nibras.test")
    _make_notification(owner.id)
    nid = client.get("/api/notifications",
                     headers=_headers(owner)).get_json()["notifications"][0]["id"]

    assert client.post(f"/api/notifications/{nid}/read",
                       headers=_headers(other)).status_code == 404
    assert client.post("/api/notifications/99999/read",
                       headers=_headers(owner)).status_code == 404


def test_mark_all_read(client):
    user = _user("all@nibras.test")
    _make_notification(user.id)
    _make_notification(user.id, title="ثانٍ")
    h = _headers(user)

    resp = client.post("/api/notifications/read-all", headers=h)
    assert resp.get_json() == {"marked": 2}
    assert client.get("/api/notifications/unread-count",
                      headers=h).get_json() == {"unread_count": 0}
    assert client.post("/api/notifications/read-all",
                       headers=h).get_json() == {"marked": 0}


def test_unread_filter_and_pagination(client):
    user = _user("filt@nibras.test")
    for i in range(3):
        _make_notification(user.id, title=f"إشعار {i}")
    h = _headers(user)

    unread = client.get("/api/notifications",
                        query_string={"unread": 1}, headers=h).get_json()
    assert unread["total"] == 3 and len(unread["notifications"]) == 3

    resp = client.post("/api/notifications/read-all", headers=h)
    assert resp.get_json()["marked"] == 3

    unread = client.get("/api/notifications",
                        query_string={"unread": 1}, headers=h).get_json()
    assert unread["notifications"] == []

    page = client.get("/api/notifications",
                      query_string={"limit": 2, "offset": 1}, headers=h).get_json()
    assert len(page["notifications"]) == 2
    assert [n["title"] for n in page["notifications"]] == ["إشعار 1", "إشعار 0"]

    assert client.get("/api/notifications",
                      query_string={"limit": "abc"}, headers=h).status_code == 400
