"""
اختبارات تسليم الإشعارات الخارجية (المرحلة 16 — قرار D-034).

تغطي: اصطفاف صفوف صندوق البريد/الدفع ضمن معاملة notify() وفق التفضيلات
(الغياب = مُفعَّل)، واجهة التفضيلات (قراءة/تحديث مع تحقق صارم وعزل بين
المستخدمين)، أجهزة الدفع (تسجيل/إعادة تسجيل/حذف بعزل الملكية)، وتفريغ
الصندوق عبر deliver_pending() (نجاح/فشل/إعادة محاولة/سقف) ونقاط الإدارة
(deliver + delivery-stats بدور admin فقط).
"""
import logging

import pytest

from app import config, services_auth
from app.database import db_session

PASSWORD = "test-password-123"


def _headers(user):
    token = services_auth.create_access_token(user.id)[0]
    return {"Authorization": f"Bearer {token}"}


def _user(email, role_code="citizen"):
    return services_auth.create_user_with_role(
        email=email, password=PASSWORD, full_name="مستخدم إشعارات",
        role_code=role_code, role_status="active", user_status="active",
    )


def _notify(user_id, type_="community.comment", title="عنوان"):
    from app.services_notifications import notify

    with db_session() as conn:
        return notify(conn, user_id, type_, title, body="نص الإشعار",
                      link="/posts/1")


def _outbox():
    with db_session() as conn:
        rows = conn.execute(
            "SELECT channel, recipient, status, attempts, last_error "
            "FROM notification_outbox ORDER BY id"
        ).fetchall()
    return [dict(r) for r in rows]


def _register(user_id, platform="android", token="dev-token-1"):
    from app.services_notifications import register_device

    return register_device(user_id, platform, token)


@pytest.fixture()
def admin_headers(fresh_db):
    admin = _user("nadmin@nibras.test", role_code="admin")
    return _headers(admin)


# ---------------------------------------------------------------------------
# اصطفاف الصندوق الخارجي ضمن notify()
# ---------------------------------------------------------------------------

def test_notify_queues_email_and_push_per_device(client):
    user = _user("queue@nibras.test")
    _register(user.id, token="tok-1")
    _register(user.id, platform="ios", token="tok-2")
    _notify(user.id)

    rows = _outbox()
    channels = [r["channel"] for r in rows]
    assert channels.count("email") == 1
    assert channels.count("push") == 2
    email = next(r for r in rows if r["channel"] == "email")
    assert email["recipient"] == user.email
    push = [r for r in rows if r["channel"] == "push"]
    assert {r["recipient"] for r in push} == {"tok-1", "tok-2"}
    assert all(r["status"] == "pending" for r in rows)


def test_notify_no_device_queues_email_only(client):
    user = _user("no-device@nibras.test")
    _notify(user.id)
    rows = _outbox()
    assert len(rows) == 1
    assert rows[0]["channel"] == "email"


def test_notify_outbox_transactional_with_notification(client):
    user = _user("txn@nibras.test")
    _register(user.id, token="tok-1")

    class _Boom(Exception):
        pass

    with pytest.raises(_Boom), db_session() as conn:
        from app.services_notifications import notify

        notify(conn, user.id, "community.comment", "عنوان")
        assert len(_outbox()) == 0  # لم تُلتَزم المعاملة بعد (قراءة جلسة مستقلة)
        raise _Boom()

    with db_session() as conn:
        n_count = conn.execute(
            "SELECT COUNT(*) AS c FROM notifications WHERE user_id = ?",
            (user.id,),
        ).fetchone()["c"]
        o_count = conn.execute(
            "SELECT COUNT(*) AS c FROM notification_outbox"
        ).fetchone()["c"]
    assert n_count == 0 and o_count == 0


# ---------------------------------------------------------------------------
# التفضيلات (get/set + عزل + أثر على الصندوق)
# ---------------------------------------------------------------------------

def test_preferences_requires_auth(client):
    assert client.get("/api/notifications/preferences").status_code == 401
    assert client.put("/api/notifications/preferences").status_code == 401


def test_preferences_defaults_all_enabled(client):
    user = _user("prefs@nibras.test")
    body = client.get("/api/notifications/preferences",
                      headers=_headers(user)).get_json()
    prefs = body["preferences"]
    assert set(prefs) == {"email", "push"}
    assert all(prefs["email"].values()) and all(prefs["push"].values())
    assert set(prefs["email"]) == {
        "verification.approved", "verification.rejected",
        "community.comment", "community.reaction",
        "moderation.content_hidden", "moderation.content_removed",
    }


def test_preferences_update_reflected(client):
    user = _user("prefs-update@nibras.test")
    h = _headers(user)
    resp = client.put("/api/notifications/preferences", json={
        "preferences": [
            {"channel": "email", "notification_type": "community.comment",
             "enabled": False},
            {"channel": "push", "notification_type": "verification.approved",
             "enabled": False},
        ],
    }, headers=h)
    assert resp.status_code == 200
    prefs = resp.get_json()["preferences"]
    assert prefs["email"]["community.comment"] is False
    assert prefs["push"]["verification.approved"] is False
    # البقية بقيمها الافتراضية
    assert prefs["email"]["verification.approved"] is True
    # قراءة لاحقة مطابقة
    body = client.get("/api/notifications/preferences", headers=h).get_json()
    assert body["preferences"] == prefs


@pytest.mark.parametrize("payload", [
    {"preferences": []},
    {"preferences": [{"channel": "sms", "notification_type": "community.comment",
                      "enabled": True}]},
    {"preferences": [{"channel": "email", "notification_type": "unknown.type",
                      "enabled": True}]},
    {"preferences": [{"channel": "email", "notification_type": "community.comment",
                      "enabled": "yes"}]},
    {"preferences": "not-a-list"},
])
def test_preferences_validation(client, payload):
    user = _user("prefs-bad@nibras.test")
    resp = client.put("/api/notifications/preferences", json=payload,
                      headers=_headers(user))
    assert resp.status_code == 400


def test_preferences_per_user_isolation(client):
    first = _user("prefs-a@nibras.test")
    second = _user("prefs-b@nibras.test")
    client.put("/api/notifications/preferences", json={
        "preferences": [
            {"channel": "email", "notification_type": "community.comment",
             "enabled": False},
        ],
    }, headers=_headers(first))
    prefs = client.get("/api/notifications/preferences",
                       headers=_headers(second)).get_json()["preferences"]
    assert prefs["email"]["community.comment"] is True


def test_preferences_disable_email_stops_email_outbox(client):
    user = _user("prefs-effect@nibras.test")
    _register(user.id, token="tok-1")
    client.put("/api/notifications/preferences", json={
        "preferences": [
            {"channel": "email", "notification_type": "community.comment",
             "enabled": False},
        ],
    }, headers=_headers(user))
    _notify(user.id)
    rows = _outbox()
    assert [r["channel"] for r in rows] == ["push"]


def test_preferences_disable_push_stops_push_outbox(client):
    user = _user("prefs-push-off@nibras.test")
    _register(user.id, token="tok-1")
    client.put("/api/notifications/preferences", json={
        "preferences": [
            {"channel": "push", "notification_type": "community.comment",
             "enabled": False},
        ],
    }, headers=_headers(user))
    _notify(user.id)
    rows = _outbox()
    assert [r["channel"] for r in rows] == ["email"]


# ---------------------------------------------------------------------------
# أجهزة الدفع
# ---------------------------------------------------------------------------

def test_devices_requires_auth(client):
    assert client.post("/api/notifications/devices").status_code == 401
    assert client.get("/api/notifications/devices").status_code == 401
    assert client.delete("/api/notifications/devices/1").status_code == 401


def test_register_and_list_device(client):
    user = _user("device-reg@nibras.test")
    h = _headers(user)
    resp = client.post("/api/notifications/devices",
                       json={"platform": "android", "token": "tok-x"},
                       headers=h)
    assert resp.status_code == 201
    device = resp.get_json()
    assert device["id"] > 0 and device["platform"] == "android"
    body = client.get("/api/notifications/devices", headers=h).get_json()
    assert [d["token"] for d in body["devices"]] == ["tok-x"]


def test_register_reuses_token_and_transfers_owner(client):
    first = _user("device-a@nibras.test")
    second = _user("device-b@nibras.test")
    first_reg = client.post("/api/notifications/devices",
                            json={"platform": "android", "token": "tok-shared"},
                            headers=_headers(first)).get_json()
    resp = client.post("/api/notifications/devices",
                       json={"platform": "ios", "token": "tok-shared"},
                       headers=_headers(second))
    assert resp.status_code == 201
    assert resp.get_json()["id"] == first_reg["id"]
    assert resp.get_json()["platform"] == "ios"
    assert client.get("/api/notifications/devices",
                      headers=_headers(first)).get_json()["devices"] == []
    assert len(client.get("/api/notifications/devices",
                          headers=_headers(second)).get_json()["devices"]) == 1


@pytest.mark.parametrize("payload", [
    {"platform": "desktop", "token": "tok"},
    {"platform": "android", "token": ""},
    {"platform": "android"},
    {"platform": "android", "token": "t" * 513},
])
def test_register_device_validation(client, payload):
    user = _user("device-bad@nibras.test")
    assert client.post("/api/notifications/devices", json=payload,
                       headers=_headers(user)).status_code == 400


def test_delete_device_own(client):
    user = _user("device-del@nibras.test")
    h = _headers(user)
    device = client.post("/api/notifications/devices",
                         json={"platform": "web", "token": "tok-del"},
                         headers=h).get_json()
    assert client.delete(f"/api/notifications/devices/{device['id']}",
                         headers=h).status_code == 200
    assert client.get("/api/notifications/devices",
                      headers=h).get_json()["devices"] == []
    assert client.delete(f"/api/notifications/devices/{device['id']}",
                         headers=h).status_code == 404


def test_delete_device_others_not_found(client):
    owner = _user("device-own@nibras.test")
    other = _user("device-thief@nibras.test")
    device = client.post("/api/notifications/devices",
                         json={"platform": "android", "token": "tok-own"},
                         headers=_headers(owner)).get_json()
    assert client.delete(f"/api/notifications/devices/{device['id']}",
                         headers=_headers(other)).status_code == 404


# ---------------------------------------------------------------------------
# تفريغ الصندوق (deliver_pending)
# ---------------------------------------------------------------------------

def test_deliver_pending_sends_and_marks_sent(client, monkeypatch):
    monkeypatch.setattr(config, "EMAIL_PROVIDER", "noop")
    user = _user("deliver@nibras.test")
    _register(user.id, token="tok-1")
    _notify(user.id)
    _notify(user.id, title="ثانٍ")

    from app.services_notifications import deliver_pending

    result = deliver_pending()
    # 2 إشعارات × (بريد + دفعة لجهاز واحد) = 4 صفوف
    assert result == {"processed": 4, "sent": 4, "failed": 0}
    assert all(r["status"] == "sent" for r in _outbox())
    assert deliver_pending() == {"processed": 0, "sent": 0, "failed": 0}


def test_deliver_console_provider_emits_log(client, monkeypatch, caplog):
    monkeypatch.setattr(config, "EMAIL_PROVIDER", "console")
    user = _user("console@nibras.test")
    _notify(user.id)

    from app.services_notifications import deliver_pending

    with caplog.at_level(logging.INFO, logger="nibras.mailer"):
        result = deliver_pending()
    assert result == {"processed": 1, "sent": 1, "failed": 0}
    assert _outbox()[0]["status"] == "sent"
    assert any("notification_email" in r.message for r in caplog.records)


def test_deliver_sends_push_rows(client, monkeypatch):
    monkeypatch.setattr(config, "PUSH_PROVIDER", "noop")
    user = _user("push-deliver@nibras.test")
    _register(user.id, token="tok-push")

    from app.services_notifications import deliver_pending

    _notify(user.id)
    result = deliver_pending()
    assert result == {"processed": 2, "sent": 2, "failed": 0}
    assert all(r["status"] == "sent" for r in _outbox())


def test_deliver_failure_retries_then_failed(client, monkeypatch):
    monkeypatch.setattr(config, "EMAIL_PROVIDER", "provider-bogus")
    user = _user("fail@nibras.test")
    _notify(user.id)

    from app.services_notifications import deliver_pending

    assert deliver_pending()["failed"] == 1
    assert _outbox()[0]["attempts"] == 1
    assert _outbox()[0]["status"] == "pending"
    assert _outbox()[0]["last_error"]

    assert deliver_pending()["failed"] == 1
    assert _outbox()[0]["attempts"] == 2
    assert _outbox()[0]["status"] == "pending"

    assert deliver_pending()["failed"] == 1
    assert _outbox()[0]["attempts"] == 3
    assert _outbox()[0]["status"] == "failed"

    assert deliver_pending() == {"processed": 0, "sent": 0, "failed": 0}


def test_deliver_respects_limit(client):
    user = _user("limit@nibras.test")
    for i in range(3):
        _notify(user.id, title=f"إشعار {i}")

    from app.services_notifications import deliver_pending

    result = deliver_pending(limit=2)
    assert result == {"processed": 2, "sent": 2, "failed": 0}
    rows = _outbox()
    assert [r["status"] for r in rows] == ["sent", "sent", "pending"]


def test_delivery_stats(client):
    user = _user("stats@nibras.test")
    _notify(user.id)

    from app.services_notifications import deliver_pending, delivery_stats

    assert delivery_stats() == {"pending": 1, "sent": 0, "failed": 0}
    deliver_pending()
    assert delivery_stats() == {"pending": 0, "sent": 1, "failed": 0}


# ---------------------------------------------------------------------------
# نقاط الإدارة (deliver + delivery-stats بدور admin فقط)
# ---------------------------------------------------------------------------

def test_admin_deliver_requires_admin(client):
    assert client.post("/api/admin/notifications/deliver").status_code == 401
    citizen = _user("admin-not@nibras.test")
    assert client.post("/api/admin/notifications/deliver",
                       headers=_headers(citizen)).status_code == 403
    assert client.get("/api/admin/notifications/delivery-stats",
                      headers=_headers(citizen)).status_code == 403


def test_admin_deliver_and_stats(client, admin_headers):
    user = _user("admin-flow@nibras.test")
    _notify(user.id)
    resp = client.post("/api/admin/notifications/deliver", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.get_json() == {"processed": 1, "sent": 1, "failed": 0}
    stats = client.get("/api/admin/notifications/delivery-stats",
                       headers=admin_headers).get_json()
    assert stats == {"pending": 0, "sent": 1, "failed": 0}


def test_admin_deliver_accepts_limit(client, admin_headers):
    user = _user("admin-limit@nibras.test")
    for _ in range(2):
        _notify(user.id)
    resp = client.post("/api/admin/notifications/deliver",
                       json={"limit": 1}, headers=admin_headers)
    assert resp.get_json() == {"processed": 1, "sent": 1, "failed": 0}
    resp = client.post("/api/admin/notifications/deliver",
                       json={"limit": "abc"}, headers=admin_headers)
    assert resp.status_code == 400
