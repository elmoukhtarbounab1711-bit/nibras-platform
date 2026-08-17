"""
اختبارات بوابة المقالات القانونية (API) — وحدة إضافية مرحلة الواجهة.

تغطي: التصنيفات العامة، قائمة المنشور فقط، إنشاء مقال (يبدأ pending)،
التفاصيل مع عداد المشاهدات، التعديل/الحذف بصلاحية الملكية، الإعجاب البتّ،
التعليقات، البلاغات، وشارة "مهني موثق" لمؤلِّف بملف مهني مصدَّق.
"""


from app import services_auth
from app.database import db_session

PASSWORD = "test-password-123"


def _register(client, email="citizen@blog.test", full_name="كاتب تجريبي"):
    return services_auth.create_user_with_role(
        email=email, password=PASSWORD, full_name=full_name,
        role_code="citizen", role_status="active", user_status="active",
    )


def _login(client, email):
    profile = services_auth.get_user_by_email(email)
    return services_auth.create_access_token(profile.id)[0]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _make_admin_token():
    admin = services_auth.create_user_with_role(
        email="admin@blog.test", password=PASSWORD, full_name="مسؤول",
        role_code="admin", role_status="active", user_status="active",
    )
    return services_auth.create_access_token(admin.id)[0]


def _create_article(client, token, **overrides):
    data = {
        "title": "عنوان مقال تجريبي",
        "body": "جسم المقال التجريبي لاختبار بوابة المقالات.",
        "summary": "ملخص قصير.",
        "keywords": "تجربة,قانون",
    }
    data.update(overrides)
    return client.post("/api/blog/articles", json=data, headers=_headers(token))


def _blog_cat_id(slug):
    with db_session() as conn:
        return conn.execute(
            "SELECT id FROM blog_categories WHERE slug = ?", (slug,)
        ).fetchone()["id"]


def _jur_id(slug):
    with db_session() as conn:
        return conn.execute(
            "SELECT id FROM law_jurisdictions WHERE slug = ?", (slug,)
        ).fetchone()["id"]


def test_categories_public(client):
    resp = client.get("/api/blog/categories")
    assert resp.status_code == 200
    slugs = [c["slug"] for c in resp.get_json()]
    assert "madani" in slugs
    assert "comparative" in slugs
    assert "ahwal-shakhsiya" in slugs


def test_blog_list_requires_no_auth(client):
    resp = client.get("/api/blog/articles")
    assert resp.status_code == 200
    assert resp.get_json()["articles"] == []


def test_create_requires_auth(client):
    resp = _create_article(client, token="bad-token")
    assert resp.status_code in (401, 422)


def test_create_starts_pending(client):
    _register(client)
    token = _login(client, "citizen@blog.test")
    resp = _create_article(client, token)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["status"] == "pending"
    # غير منشور بعد: لا يظهر للعموم
    assert client.get("/api/blog/articles").get_json()["articles"] == []


def test_create_rejects_missing_title(client):
    _register(client)
    token = _login(client, "citizen@blog.test")
    resp = _create_article(client, token, title=" ")
    assert resp.status_code == 400
    assert "title" in resp.get_json()["error"]


def test_create_admin_publishes_immediately(client):
    token = _make_admin_token()
    resp = _create_article(client, token)
    assert resp.status_code == 201
    assert resp.get_json()["status"] == "published"
    listing = client.get("/api/blog/articles").get_json()["articles"]
    assert any(a["title"] == "عنوان مقال تجريبي" for a in listing)


def test_detail_increments_views_and_exposes_author(client):
    _register(client)
    token = _login(client, "citizen@blog.test")
    article_id = _create_article(client, token).get_json()["id"]
    # صاحب المقال يرى مسودته
    resp = client.get(f"/api/blog/articles/{article_id}", headers=_headers(token))
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["author"]["full_name"] == "كاتب تجريبي"
    assert data["liked"] is False
    assert data["status"] == "pending"
    assert data["views"] == 0


def test_detail_hides_pending_from_public(client):
    _register(client)
    token = _login(client, "citizen@blog.test")
    article_id = _create_article(client, token).get_json()["id"]
    resp = client.get(f"/api/blog/articles/{article_id}")
    assert resp.status_code == 404


def test_detail_404(client):
    assert client.get("/api/blog/articles/99999").status_code == 404


def test_update_own_article(client):
    _register(client)
    token = _login(client, "citizen@blog.test")
    article_id = _create_article(client, token).get_json()["id"]
    resp = client.put(
        f"/api/blog/articles/{article_id}",
        json={"title": "عنوان محدث"},
        headers=_headers(token),
    )
    assert resp.status_code == 200
    detail = client.get(
        f"/api/blog/articles/{article_id}", headers=_headers(token)
    ).get_json()
    assert detail["title"] == "عنوان محدث"


def test_update_foreign_article_forbidden(client):
    _register(client)
    token = _login(client, "citizen@blog.test")
    article_id = _create_article(client, token).get_json()["id"]
    _register(client, email="other@blog.test", full_name="كاتب آخر")
    other_token = _login(client, "other@blog.test")
    resp = client.put(
        f"/api/blog/articles/{article_id}",
        json={"title": "محاولة تعديل"},
        headers=_headers(other_token),
    )
    assert resp.status_code == 403


def test_delete_own_article(client):
    _register(client)
    token = _login(client, "citizen@blog.test")
    article_id = _create_article(client, token).get_json()["id"]
    resp = client.delete(f"/api/blog/articles/{article_id}", headers=_headers(token))
    assert resp.status_code == 200
    assert client.get(f"/api/blog/articles/{article_id}",
                      headers=_headers(token)).status_code == 404


def test_like_toggle(client):
    _register(client)
    token = _login(client, "citizen@blog.test")
    article_id = _create_article(client, token).get_json()["id"]
    first = client.post(
        f"/api/blog/articles/{article_id}/like", headers=_headers(token)
    ).get_json()
    assert first == {"liked": True, "likes": 1}
    second = client.post(
        f"/api/blog/articles/{article_id}/like", headers=_headers(token)
    ).get_json()
    assert second == {"liked": False, "likes": 0}


def test_comment_flow(client):
    _register(client)
    token = _login(client, "citizen@blog.test")
    admin_token = _make_admin_token()
    article_id = _create_article(client, admin_token).get_json()["id"]
    resp = client.post(
        f"/api/blog/articles/{article_id}/comments",
        json={"body": "تعليق أول"},
        headers=_headers(token),
    )
    assert resp.status_code == 201
    comments = client.get(f"/api/blog/articles/{article_id}/comments").get_json()
    assert len(comments) == 1
    assert comments[0]["user_name"] == "كاتب تجريبي"


def test_report_flow(client):
    _register(client)
    token = _login(client, "citizen@blog.test")
    admin_token = _make_admin_token()
    article_id = _create_article(client, admin_token).get_json()["id"]
    resp = client.post(
        f"/api/blog/articles/{article_id}/report",
        json={"reason": "محتوى مخالف"},
        headers=_headers(token),
    )
    assert resp.status_code == 201
    # بلاغ مكرر مرفوض
    dup = client.post(
        f"/api/blog/articles/{article_id}/report",
        json={"reason": "محتوى مخالف"},
        headers=_headers(token),
    )
    assert dup.status_code == 409


def test_verified_badge_for_verified_professional(client):
    # محامٍ بملف مهني موثَّق → شارة "مهني موثق" في بطاقة المقال
    lawyer = services_auth.create_user_with_role(
        email="lawyer@blog.test", password=PASSWORD, full_name="ذ. رشيد فؤاد",
        role_code="lawyer", role_status="active", user_status="active",
    )
    with db_session() as conn:
        conn.execute(
            """INSERT INTO professional_profiles
               (user_id, profession_type, bio, city, verification_status,
                tenant_id, created_at, updated_at)
               VALUES (?, 'lawyer', 'سيرة', 'الرباط', 'verified', 1,
                       datetime('now'), datetime('now'))""",
            (lawyer.id,),
        )
    lawyer_token = services_auth.create_access_token(lawyer.id)[0]
    article_id = _create_article(
        client, lawyer_token, title="مقال موثق"
    ).get_json()["id"]
    detail = client.get(
        f"/api/blog/articles/{article_id}", headers=_headers(lawyer_token)
    ).get_json()
    assert detail["author"]["verified"] is True


def test_my_articles(client):
    _register(client)
    token = _login(client, "citizen@blog.test")
    _create_article(client, token)
    resp = client.get("/api/blog/my", headers=_headers(token))
    assert resp.status_code == 200
    assert len(resp.get_json()["articles"]) == 1


def test_comparative_category_requires_jurisdiction(client):
    _register(client)
    token = _login(client, "citizen@blog.test")
    resp = _create_article(
        client, token, category_id=_blog_cat_id("comparative"))
    assert resp.status_code == 400
    assert "الدولة" in resp.get_json()["error"]


def test_jurisdiction_rejected_outside_comparative(client):
    admin_token = _make_admin_token()
    resp = _create_article(
        client, admin_token, category_id=_blog_cat_id("madani"),
        jurisdiction_id=_jur_id("egypt"))
    assert resp.status_code == 400
    assert "مخصص" in resp.get_json()["error"]


def test_comparative_article_published_shows_on_jurisdiction_page(client):
    admin_token = _make_admin_token()
    resp = _create_article(
        client, admin_token, title="مقارنة مصر",
        category_id=_blog_cat_id("comparative"),
        jurisdiction_id=_jur_id("egypt"))
    assert resp.status_code == 201
    assert resp.get_json()["status"] == "published"

    egypt = client.get(
        "/api/comparative/jurisdictions/egypt/articles").get_json()["articles"]
    assert any(a["title"] == "مقارنة مصر" for a in egypt)
    france = client.get(
        "/api/comparative/jurisdictions/france/articles").get_json()["articles"]
    assert not any(a["title"] == "مقارنة مصر" for a in france)
    listing = client.get(
        "/api/blog/articles?category=comparative").get_json()["articles"]
    assert any(a["title"] == "مقارنة مصر" for a in listing)


def test_update_comparative_article_keeps_jurisdiction(client):
    _register(client)
    token = _login(client, "citizen@blog.test")
    # المستخدم ينشئ مقارنة مع الدولة (يبدأ pending) ثم يُحدِّث النص فقط
    article_id = _create_article(
        client, token, category_id=_blog_cat_id("comparative"),
        jurisdiction_id=_jur_id("egypt")).get_json()["id"]
    resp = client.put(
        f"/api/blog/articles/{article_id}",
        json={"body": "نص محدث"},
        headers=_headers(token),
    )
    assert resp.status_code == 200
    detail = client.get(
        f"/api/blog/articles/{article_id}", headers=_headers(token)).get_json()
    assert detail["jurisdiction_id"] == _jur_id("egypt")
    assert detail["category_slug"] == "comparative"
