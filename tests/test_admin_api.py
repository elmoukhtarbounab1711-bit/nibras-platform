"""
اختبارات لوحة الإدارة (المرحلة 2) عبر HTTP.

تغطي إدارة المحتوى (تعديل/حذف النصوص والمواد) وطابور التحقق من الطلبات
المهنية، والتفويض (admin فقط)، وسجل تدقيق الإجراءات الإدارية
(Security Architecture §8)، وفق وثيقة API ووثيقة 20 (Admin Panel).
"""
import pytest

from app import services_auth
from app.database import db_session

PASSWORD = "test-password-123"


@pytest.fixture()
def admin_headers(fresh_db):
    """توكن مسؤول عبر JWT."""
    admin = services_auth.create_user_with_role(
        email="admin@nibras.test", password=PASSWORD, full_name="مسؤول",
        role_code="admin", role_status="active", user_status="active",
    )
    token = services_auth.create_access_token(admin.id)[0]
    return {"Authorization": f"Bearer {token}"}


def _bearer(client, role_code):
    profile = services_auth.create_user_with_role(
        email=f"{role_code}-{id(client)}@nibras.test", password=PASSWORD,
        full_name="مستخدم", role_code=role_code, role_status="active",
        user_status="active",
    )
    token = services_auth.create_access_token(profile.id)[0]
    return {"Authorization": f"Bearer {token}"}


def _professional(email):
    return services_auth.create_user_with_role(
        email=email, password=PASSWORD, full_name="محامي",
        role_code="lawyer", role_status="pending_verification", user_status="active",
    )


def _text_id(client, title):
    for t in client.get("/api/texts").get_json():
        if t["title"] == title:
            return t["id"]
    raise AssertionError(f"النص '{title}' غير موجود")


def _first_article_id(client, text_id):
    return client.get(f"/api/texts/{text_id}").get_json()["articles"][0]["id"]


def _audit_rows():
    with db_session() as conn:
        rows = conn.execute(
            "SELECT admin_id, action, target_type, target_id FROM admin_audit_log"
            " ORDER BY id"
        ).fetchall()
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# طابور التحقق
# ---------------------------------------------------------------------------

def test_verification_queue_lists_only_pending_professionals(client, admin_headers):
    _professional("lawyer-pending@nibras.test")
    services_auth.create_user_with_role(
        email="citizen-active@nibras.test", password=PASSWORD, full_name="مواطن",
        role_code="citizen", role_status="active", user_status="active",
    )
    _professional("lawyer-pending2@nibras.test")

    r = client.get("/api/admin/verification-queue", headers=admin_headers)
    assert r.status_code == 200
    items = r.get_json()["requests"]
    emails = [i["email"] for i in items]
    assert set(emails) == {
        "lawyer-pending@nibras.test", "lawyer-pending2@nibras.test",
    }
    assert "citizen-active@nibras.test" not in emails
    assert all(i["role_code"] == "lawyer" for i in items)
    assert all(i["role_status"] == "pending_verification" for i in items)
    assert set(items[0].keys()) == {
        "user_id", "email", "full_name", "role_code", "role_name",
        "role_status", "rejection_reason", "requested_at",
    }


def test_verification_queue_requires_admin(client):
    r = client.get("/api/admin/verification-queue")
    assert r.status_code == 401

    citizen = _bearer(client, "citizen")
    r = client.get("/api/admin/verification-queue", headers=citizen)
    assert r.status_code == 403


def test_verification_approve(client, admin_headers):
    lawyer = _professional("approve@nibras.test")

    r = client.post(f"/api/admin/verification/{lawyer.id}/approve", headers=admin_headers)
    assert r.status_code == 200
    assert r.get_json()["id"] == lawyer.id

    statuses = {
        r["code"]: r["status"] for r in services_auth.get_user_roles(lawyer.id)
    }
    assert statuses["lawyer"] == "active"
    assert client.get("/api/admin/verification-queue",
                      headers=admin_headers).get_json()["requests"] == []


def test_verification_approve_already_decided_conflicts(client, admin_headers):
    lawyer = _professional("twice@nibras.test")
    client.post(f"/api/admin/verification/{lawyer.id}/approve", headers=admin_headers)

    r = client.post(f"/api/admin/verification/{lawyer.id}/approve", headers=admin_headers)
    assert r.status_code == 409


def test_verification_reject_requires_reason(client, admin_headers):
    lawyer = _professional("reject-noreason@nibras.test")
    r = client.post(f"/api/admin/verification/{lawyer.id}/reject", headers=admin_headers)
    assert r.status_code == 400
    assert "سبب" in r.get_json()["error"]


def test_verification_reject_with_reason(client, admin_headers):
    lawyer = _professional("reject@nibras.test")
    r = client.post(
        f"/api/admin/verification/{lawyer.id}/reject",
        json={"reason": "الوثيقة غير مقروءة"},
        headers=admin_headers,
    )
    assert r.status_code == 200

    with db_session() as conn:
        row = conn.execute(
            """SELECT ur.role_status, ur.rejection_reason
               FROM user_roles ur JOIN roles r ON r.id = ur.role_id
               WHERE ur.user_id = ? AND r.code = 'lawyer'""",
            (lawyer.id,),
        ).fetchone()
    assert row["role_status"] == "rejected"
    assert row["rejection_reason"] == "الوثيقة غير مقروءة"


def test_verification_not_found(client, admin_headers):
    r = client.post("/api/admin/verification/99999/approve", headers=admin_headers)
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# إدارة المحتوى: النصوص
# ---------------------------------------------------------------------------

def test_update_text(client, admin_headers):
    tid = _text_id(client, "قانون الالتزامات والعقود")
    r = client.put(
        f"/api/admin/texts/{tid}",
        json={"title": "قانون الالتزامات والعقود (منقح)", "type": "law",
              "source_note": "محدث"},
        headers=admin_headers,
    )
    assert r.status_code == 200
    detail = client.get(f"/api/texts/{tid}").get_json()
    assert detail["title"] == "قانون الالتزامات والعقود (منقح)"
    assert detail["type"] == "law"
    assert detail["source_note"] == "محدث"


def test_update_text_missing_not_found(client, admin_headers):
    r = client.put("/api/admin/texts/99999", json={"title": "x"}, headers=admin_headers)
    assert r.status_code == 404


def test_update_text_validation(client, admin_headers):
    tid = _text_id(client, "قانون الالتزامات والعقود")

    r = client.put(f"/api/admin/texts/{tid}", json={"type": "bogus"},
                   headers=admin_headers)
    assert r.status_code == 400

    r = client.put(f"/api/admin/texts/{tid}", json={"title": "  "}, headers=admin_headers)
    assert r.status_code == 400

    r = client.put(f"/api/admin/texts/{tid}", json={"category_id": 99999},
                   headers=admin_headers)
    assert r.status_code == 404

    r = client.put(f"/api/admin/texts/{tid}", json={}, headers=admin_headers)
    assert r.status_code == 400


def test_create_text_validates_type_and_category(client, admin_headers):
    r = client.post("/api/admin/texts", json={"category_id": 1, "type": "bogus",
                                              "title": "نص"}, headers=admin_headers)
    assert r.status_code == 400

    r = client.post("/api/admin/texts", json={"category_id": 99999, "type": "law",
                                              "title": "نص"}, headers=admin_headers)
    assert r.status_code == 404


def test_delete_text_cascades_articles(client, admin_headers):
    tid = _text_id(client, "قانون الالتزامات والعقود")
    assert len(client.get(f"/api/texts/{tid}").get_json()["articles"]) > 0

    r = client.delete(f"/api/admin/texts/{tid}", headers=admin_headers)
    assert r.status_code == 200

    assert client.get(f"/api/texts/{tid}").status_code == 404
    with db_session() as conn:
        count = conn.execute(
            "SELECT COUNT(*) AS n FROM articles WHERE legal_text_id = ?", (tid,)
        ).fetchone()["n"]
    assert count == 0


def test_delete_text_missing_not_found(client, admin_headers):
    r = client.delete("/api/admin/texts/99999", headers=admin_headers)
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# إدارة المحتوى: المواد
# ---------------------------------------------------------------------------

def test_update_article(client, admin_headers):
    tid = _text_id(client, "قانون الالتزامات والعقود")
    aid = _first_article_id(client, tid)
    r = client.put(
        f"/api/admin/articles/{aid}",
        json={"content": "محتوى معدل", "plain_explanation": "شرح معدل"},
        headers=admin_headers,
    )
    assert r.status_code == 200
    detail = client.get(f"/api/articles/{aid}").get_json()
    assert detail["content"] == "محتوى معدل"
    assert detail["plain_explanation"] == "شرح معدل"


def test_update_article_validation(client, admin_headers):
    tid = _text_id(client, "قانون الالتزامات والعقود")
    aid = _first_article_id(client, tid)

    r = client.put(f"/api/admin/articles/{aid}", json={"content": "  "},
                   headers=admin_headers)
    assert r.status_code == 400

    r = client.put("/api/admin/articles/99999", json={"content": "x"},
                   headers=admin_headers)
    assert r.status_code == 404


def test_delete_article_clears_related_and_fts(client, admin_headers):
    tid = _text_id(client, "قانون الالتزامات والعقود")
    aid = _first_article_id(client, tid)

    r = client.delete(f"/api/admin/articles/{aid}", headers=admin_headers)
    assert r.status_code == 200
    assert client.get(f"/api/articles/{aid}").status_code == 404

    with db_session() as conn:
        n_related = conn.execute(
            "SELECT COUNT(*) AS n FROM related_articles WHERE article_id = ? OR related_article_id = ?",
            (aid, aid),
        ).fetchone()["n"]
    assert n_related == 0


# ---------------------------------------------------------------------------
# التفويض والتدقيق
# ---------------------------------------------------------------------------

def test_content_mutations_require_admin(client):
    tid = _text_id(client, "قانون الالتزامات والعقود")

    assert client.put(f"/api/admin/texts/{tid}", json={"title": "x"}).status_code == 401
    assert client.delete(f"/api/admin/texts/{tid}").status_code == 401

    citizen = _bearer(client, "citizen")
    assert client.put(f"/api/admin/texts/{tid}", json={"title": "x"},
                      headers=citizen).status_code == 403
    assert client.delete(f"/api/admin/texts/{tid}", headers=citizen).status_code == 403


def test_audit_log_records_all_admin_actions(client, admin_headers):
    r = client.post("/api/admin/texts", json={"category_id": 1, "type": "law",
                                              "title": "نص مُدقَّق"}, headers=admin_headers)
    new_text_id = r.get_json()["id"]
    r = client.post(f"/api/admin/texts/{new_text_id}/articles",
                    json={"number": "1", "label": "المادة 1", "content": "نص"},
                    headers=admin_headers)
    new_article_id = r.get_json()["id"]

    client.put(f"/api/admin/texts/{new_text_id}", json={"title": "عنوان جديد"},
               headers=admin_headers)
    client.put(f"/api/admin/articles/{new_article_id}", json={"content": "محدث"},
               headers=admin_headers)
    client.delete(f"/api/admin/articles/{new_article_id}", headers=admin_headers)
    client.delete(f"/api/admin/texts/{new_text_id}", headers=admin_headers)

    lawyer = _professional("audit-lawyer@nibras.test")
    client.post(f"/api/admin/verification/{lawyer.id}/approve", headers=admin_headers)
    lawyer2 = _professional("audit-lawyer2@nibras.test")
    client.post(f"/api/admin/verification/{lawyer2.id}/reject",
                json={"reason": "وثيقة ناقصة"}, headers=admin_headers)

    rows = _audit_rows()
    actions = [r["action"] for r in rows]
    assert actions == [
        "text.create", "article.create",
        "text.update", "article.update",
        "article.delete", "text.delete",
        "verification.approve", "verification.reject",
    ]
    assert all(r["admin_id"] is not None for r in rows)
    text_actions = [r for r in rows if r["target_type"] == "legal_text"]
    assert text_actions[0]["target_id"] == new_text_id
    assert text_actions[0]["action"] == "text.create"

    audit = [r for r in rows if r["target_type"] == "user"]
    assert audit[1]["target_id"] == lawyer2.id


def test_audit_log_keeps_rows_after_admin_deleted(fresh_db):
    """ON DELETE SET NULL: بقاء السجل للمساءلة حتى لو حُذف حساب المسؤول."""
    with db_session() as conn:
        conn.execute(
            "INSERT INTO users (email, full_name, password_hash) VALUES (?,?,?)",
            ("ghost@nibras.test", "شبح", "x"),
        )
        ghost_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute(
            "INSERT INTO admin_audit_log (admin_id, action, target_type, target_id)"
            " VALUES (?,?,?,?)",
            (ghost_id, "text.delete", "legal_text", 1),
        )
        conn.execute("DELETE FROM users WHERE id = ?", (ghost_id,))
        row = conn.execute(
            "SELECT admin_id FROM admin_audit_log WHERE action = 'text.delete'"
        ).fetchone()
        assert row["admin_id"] is None
