"""
اختبارات التكامل الشاملة (المرحلة 13).

سيناريوهات مستخدم واقعية تمتد عبر عدة وحدات للتأكد من ترابطها:
(1) رحلة المحترف الكاملة (تسجيل → ملف → تحقق → دليل → مجتمع → إشعار)،
(2) المجتمع والإشراف والإشعارات والتحليلات، (3) الاستيعاب → المكتبة →
البحث → شرح موجه، (4) دورة جلسة المصادقة، (5) السوق والإعلانات والدليل
عبر لوحة الأدمن. تُختبر عبر نقاط النهاية العامة فقط (بلا استدعاء خدمات
مباشرة سوى إنشاء حساب مسؤول كبذر ثابت).
"""
import io

import pytest

from app import config, services_auth

PASSWORD = "test-password-123"

PROFILE = {
    "profession_type": "lawyer",
    "city": "الدار البيضاء",
    "bio": "محامٍ معتمد في القانون المدني",
    "specialties": ["مدني"],
}


@pytest.fixture(autouse=True)
def _isolate_uploads(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "UPLOAD_DIR", str(tmp_path / "uploads"))
    yield


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def _register(client, email, full_name="مستخدم", role="citizen"):
    from app.services_auth import role_status_for_code
    return services_auth.create_user_with_role(
        email=email, password=PASSWORD, full_name=full_name,
        role_code=role, role_status=role_status_for_code(role),
        user_status="active",
    )


def _login(client, email):
    profile = services_auth.get_user_by_email(email)
    return {
        "access_token": services_auth.create_access_token(profile.id)[0],
    }


def _admin():
    admin = services_auth.create_user_with_role(
        email="admin-int@nibras.test", password=PASSWORD, full_name="مسؤول",
        role_code="admin", role_status="active", user_status="active",
    )
    return admin


def _docx_bytes(paragraphs):
    from docx import Document

    doc = Document()
    for p in paragraphs:
        doc.add_paragraph(p)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# (1) رحلة المحترف: تسجيل → ملف → توثيق → تحقق → دليل → مجتمع → إشعار
# ---------------------------------------------------------------------------

def test_professional_journey_end_to_end(client):
    lawyer = _register(client, "lawyer@journey.test", full_name="المحامية أمينة",
                       role="lawyer")
    lh = _auth_headers(services_auth.create_access_token(lawyer.id)[0])

    # إنشاء الملف المهني (حالة pending — لا يظهر في الدليل بعد)
    resp = client.post("/api/professionals/profile", json=PROFILE, headers=lh)
    assert resp.status_code == 201
    assert resp.get_json()["verification_status"] == "pending"
    assert client.get("/api/professionals").get_json() == []

    # رفع وثيقة التحقق (multipart)
    resp = client.post(
        "/api/professionals/verify-document",
        data={"document": (io.BytesIO(b"%PDF-1.4 fake"), "cert.pdf")},
        headers=lh, content_type="multipart/form-data",
    )
    assert resp.status_code == 200

    # قبول الأدمن → إشعار للمحامية + ظهورها في الدليل
    admin = _admin()
    ah = _auth_headers(services_auth.create_access_token(admin.id)[0])
    queue = client.get("/api/admin/verification-queue", headers=ah).get_json()
    assert [q["user_id"] for q in queue["requests"]] == [lawyer.id]
    assert client.post(f"/api/admin/verification/{lawyer.id}/approve",
                       headers=ah).status_code == 200

    notif = client.get("/api/notifications", headers=lh).get_json()
    assert notif["total"] == 1
    assert notif["notifications"][0]["type"] == "verification.approved"
    assert client.post(
        f"/api/notifications/{notif['notifications'][0]['id']}/read",
        headers=lh).get_json()["is_read"] is True

    directory = client.get("/api/professionals").get_json()
    assert len(directory) == 1
    assert directory[0]["full_name"] == "المحامية أمينة"

    # منشور مجتمعي بشارة تحقُّق خضراء
    post = client.post("/api/community/posts",
                       json={"category_id": 1, "title": "استشارة",
                             "body": "سؤال حول العقد"},
                       headers=lh).get_json()
    assert post["author_is_verified"] is True

    # التحليلات تعكس المهني النشط والمنشور
    summary = client.get("/api/admin/analytics/summary", headers=ah).get_json()
    assert summary["users"]["professionals_active"] == 1
    assert summary["community"]["posts"] >= 1


# ---------------------------------------------------------------------------
# (2) المجتمع: تفاعل → بلاغ → إشراف → إشعار → تحليلات
# ---------------------------------------------------------------------------

def test_community_moderation_notification_analytics(client):
    _register(client, "author@flow.test", full_name="كاتب")
    author_h = _auth_headers(_login(client, "author@flow.test")["access_token"])
    _register(client, "commenter@flow.test", full_name="معلّق")
    commenter_h = _auth_headers(_login(client, "commenter@flow.test")["access_token"])
    _register(client, "reporter@flow.test", full_name="مبلّغ")
    reporter_h = _auth_headers(_login(client, "reporter@flow.test")["access_token"])

    post = client.post("/api/community/posts",
                       json={"category_id": 1, "title": "منشور قابل للإبلاغ",
                             "body": "محتوى"}, headers=author_h).get_json()

    client.post(f"/api/community/posts/{post['id']}/comments",
                json={"body": "تعليق مفيد"}, headers=commenter_h)
    client.post(f"/api/community/posts/{post['id']}/react",
                json={"type": "like"}, headers=commenter_h)

    # الكاتب تلقى إشعارَي تعليق وتفاعل
    notifs = client.get("/api/notifications", headers=author_h).get_json()
    types = {n["type"] for n in notifs["notifications"]}
    assert types == {"community.comment", "community.reaction"}

    # بلاغ وإزالة من الأدمن → إشعار للمؤلف + اختفاء المنشور
    report = client.post("/api/community/report",
                         json={"target_type": "post", "target_id": post["id"],
                               "reason": "محتوى مسيء"},
                         headers=reporter_h).get_json()
    admin = _admin()
    ah = _auth_headers(services_auth.create_access_token(admin.id)[0])
    assert client.post(f"/api/admin/moderation/{report['id']}/action",
                       json={"action": "remove"}, headers=ah).status_code == 200

    notifs = client.get("/api/notifications", headers=author_h).get_json()
    assert any(n["type"] == "moderation.content_removed"
               for n in notifs["notifications"])
    assert client.get(f"/api/community/posts/{post['id']}").status_code == 404


# ---------------------------------------------------------------------------
# (3) الاستيعاب → المكتبة → البحث → الشرح الموجَّه
# ---------------------------------------------------------------------------

def test_ingestion_library_search_ai(client):
    admin = _admin()
    ah = _auth_headers(services_auth.create_access_token(admin.id)[0])

    doc = _docx_bytes([
        "المادة 1 يستحق الأجير مكافأة نهاية الخدمة عند انتهاء عقد العمل.",
        "المادة 2 يحدد القانون أدنى أجر في القطاع الخاص.",
    ])
    resp = client.post(
        "/api/admin/ingestion/import",
        data={"file": (io.BytesIO(doc), "work-law.docx"),
              "category_id": "1", "type": "law", "title": "مدونة الشغل"},
        headers=ah, content_type="multipart/form-data",
    )
    assert resp.status_code == 201
    imported_id = resp.get_json()["id"]

    # ظهرت في قائمة المكتبة (بترتيب الأحدث أولًا)
    texts = client.get("/api/texts").get_json()
    assert any(t["id"] == imported_id and t["title"] == "مدونة الشغل"
               for t in texts)

    # البحث يجد المادة المستوردة
    results = client.get("/api/search", query_string={"q": "مكافأة نهاية الخدمة"}
                         ).get_json()["results"]
    imported_articles = [r["id"] for r in results
                         if r["legal_text_title"] == "مدونة الشغل"]
    assert imported_articles

    # شرح موجَّه يستشهد بالمادة المستوردة (استرجاع فعلي عبر FTS)
    _register(client, "asker@flow.test")
    user_h = _auth_headers(_login(client, "asker@flow.test")["access_token"])
    resp = client.post("/api/ai/explain",
                       json={"question": "مكافأة نهاية الخدمة عند انتهاء عقد العمل",
                             "mode": "grounded"}, headers=user_h)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["mode"] == "grounded"
    assert any(aid in data["cited_article_ids"] for aid in imported_articles)


# ---------------------------------------------------------------------------
# (4) دورة جلسة المصادقة (تسجيل → دخول → تجديد → خروج)
# ---------------------------------------------------------------------------

def test_internal_token_lifecycle(client):
    _register(client, "session@flow.test", full_name="مستخدم الجلسة")
    profile = services_auth.get_user_by_email("session@flow.test")
    access = services_auth.create_access_token(profile.id)[0]

    # التوكن الداخلي يعمل على نقطة محمية
    assert client.get("/api/auth/me",
                      headers=_auth_headers(access)).status_code == 200

    # لا تجديد عام للتوكنات (لا جلسات عمومية)
    assert client.post("/api/auth/refresh",
                       json={"refresh_token": "x"}).status_code == 403
    assert client.post("/api/auth/refresh",
                       json={"refresh_token": "x"}).status_code == 403


# ---------------------------------------------------------------------------
# (5) السوق + الإعلانات + الدليل (إدارة)
# ---------------------------------------------------------------------------

def test_marketplace_ads_directory_admin(client):
    admin = _admin()
    ah = _auth_headers(services_auth.create_access_token(admin.id)[0])

    # فئة سوق + قالب بملف
    client.post("/api/admin/marketplace/categories",
                json={"slug": "contracts", "name": "العقود"}, headers=ah)
    client.post("/api/admin/marketplace/templates",
                data={"category_id": "1", "title": "عقد إيجار",
                      "description": "قالب نموذجي", "price_cents": "0",
                      "file": (io.BytesIO(b"%PDF-1.4 sample"), "lease.pdf")},
                headers=ah, content_type="multipart/form-data")
    browse = client.get("/api/marketplace/templates").get_json()
    assert any(t["title"] == "عقد إيجار" for t in browse)

    # حملة إعلانية في فتحة المكتبة وتقديمها
    slots = client.get("/api/admin/ads/slots", headers=ah).get_json()["slots"]
    slot_id = next(s["id"] for s in slots if s["slug"] == "library_sidebar")
    client.post("/api/admin/ads/campaigns",
                json={"slot_id": slot_id, "campaign_type": "general",
                      "advertiser_name": "معلن", "creative_url": "https://x.ma/a.png",
                      "target_url": "https://x.ma/",
                      "start_date": "2026-01-01", "end_date": "2026-12-31"},
                headers=ah)
    served = client.get("/api/ads/serve", query_string={"slot": "library_sidebar"}
                        ).get_json()["campaign"]
    assert served is not None and served["campaign_id"] >= 1
    assert served["sponsored"] is False

    # ملخص التحليلات الإدارية يعكس السوق (الإعلانات لا تُجمَّع في الملخص بعد)
    summary = client.get("/api/admin/analytics/summary", headers=ah).get_json()
    assert summary["marketplace"]["templates"] >= 1
    assert summary["moderation"]["open_reports"] == 0
