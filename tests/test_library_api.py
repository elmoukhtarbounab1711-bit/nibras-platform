"""
اختبارات تكامل للمكتبة القانونية عبر HTTP (request → response).

تُغطي جميع نقاط نهاية المكتبة الحالية (عامة وإدارية) وحالات الخطأ،
وتشكّل شبكة أمان الانحدار قبل أي ترحيل أو إضافة وحدة (Testing Strategy §2).
"""
import pytest

from app import services_auth

PASSWORD = "test-password-123"


@pytest.fixture()
def admin_headers(fresh_db):
    """توكن مسؤول عبر JWT (المرحلة 1) — حلَّ محل X-Admin-Key."""
    admin = services_auth.create_user_with_role(
        email="admin@nibras.test", password=PASSWORD, full_name="مسؤول",
        role_code="admin", role_status="active", user_status="active",
    )
    token = services_auth.create_access_token(admin.id)[0]
    return {"Authorization": f"Bearer {token}"}


def _find_text_id(client, title):
    texts = client.get("/api/texts").get_json()
    for t in texts:
        if t["title"] == title:
            return t["id"]
    raise AssertionError(f"النص '{title}' غير موجود في بيانات الاختبار")


# ---------- نقاط نهاية عامة ----------

def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok", "service": "nibras-backend"}


def test_categories_sorted(client):
    r = client.get("/api/categories")
    assert r.status_code == 200
    names = [c["name"] for c in r.get_json()]
    assert names == sorted(names)


def test_arabic_unescaped(client):
    r = client.get("/api/categories")
    assert "القانون المدني" in r.get_data(as_text=True)


def test_texts_list_and_filters(client):
    data = client.get("/api/texts").get_json()
    assert len(data) == 2
    assert {"article_count", "category_name", "category_slug"} <= set(data[0].keys())

    filtered = client.get("/api/texts?category=usra").get_json()
    assert len(filtered) == 1
    assert filtered[0]["category_slug"] == "usra"

    by_type = client.get("/api/texts?type=code").get_json()
    assert len(by_type) == 2


def test_text_detail(client):
    tid = _find_text_id(client, "قانون الالتزامات والعقود")
    r = client.get(f"/api/texts/{tid}")
    assert r.status_code == 200
    data = r.get_json()
    assert data["title"] == "قانون الالتزامات والعقود"
    assert len(data["articles"]) == 1
    assert set(data["articles"][0].keys()) == {"id", "number", "label"}


def test_text_detail_not_found(client):
    r = client.get("/api/texts/99999")
    assert r.status_code == 404
    assert "error" in r.get_json()


def test_article_detail(client):
    tid = _find_text_id(client, "قانون الالتزامات والعقود")
    aid = client.get(f"/api/texts/{tid}").get_json()["articles"][0]["id"]
    r = client.get(f"/api/articles/{aid}")
    assert r.status_code == 200
    data = r.get_json()
    assert data["label"] == "المادة 230"
    assert data["plain_explanation"]
    assert len(data["related_articles"]) == 1
    assert data["related_articles"][0]["label"] == "المادة 49"


def test_article_detail_not_found(client):
    r = client.get("/api/articles/99999")
    assert r.status_code == 404
    assert "error" in r.get_json()


def test_articles_list_public(client):
    r = client.get("/api/articles")
    assert r.status_code == 200
    data = r.get_json()
    assert data["count"] == 2
    assert len(data["articles"]) == 2
    item = data["articles"][0]
    assert {"id", "label", "legal_text_id", "legal_text_title", "views"} <= set(item.keys())
    assert item["views"] == 0


def test_articles_list_limit_and_offset(client):
    r = client.get("/api/articles?limit=1&offset=1")
    assert r.status_code == 200
    data = r.get_json()
    assert data["count"] == 2
    assert len(data["articles"]) == 1


def test_articles_list_limit_capped(client):
    r = client.get("/api/articles?limit=999")
    assert r.status_code == 200
    assert len(r.get_json()["articles"]) <= 100


def test_article_view_increments(client):
    tid = _find_text_id(client, "قانون الالتزامات والعقود")
    aid = client.get(f"/api/texts/{tid}").get_json()["articles"][0]["id"]
    before = client.get(f"/api/articles/{aid}").get_json()["views"]
    after = client.get(f"/api/articles/{aid}").get_json()["views"]
    assert after == before + 1


def test_text_pdf_generates(client):
    tid = _find_text_id(client, "قانون الالتزامات والعقود")
    r = client.get(f"/api/texts/{tid}/pdf")
    assert r.status_code == 200
    assert r.headers.get("Content-Type", "").startswith("application/pdf")
    assert "inline" in r.headers.get("Content-Disposition", "")
    assert r.data.startswith(b"%PDF")


def test_text_pdf_download_disposition(client):
    tid = _find_text_id(client, "مدونة الأسرة")
    r = client.get(f"/api/texts/{tid}/pdf?download=1")
    assert r.status_code == 200
    assert "attachment" in r.headers.get("Content-Disposition", "")
    assert r.data.startswith(b"%PDF")


def test_text_pdf_not_found(client):
    r = client.get("/api/texts/99999/pdf")
    assert r.status_code == 404
    assert "error" in r.get_json()


def test_search_requires_q(client):
    for url in ("/api/search", "/api/search?q=", "/api/search?q=%20"):
        r = client.get(url)
        assert r.status_code == 400
        assert "error" in r.get_json()


def test_search_result_shape_and_content(client):
    r = client.get("/api/search?q=عقد")
    assert r.status_code == 200
    data = r.get_json()
    assert set(data.keys()) == {"query", "count", "results"}
    assert data["count"] == len(data["results"])
    assert data["results"][0]["label"] == "المادة 230"


def test_search_limit_capped_at_fifty(client):
    r = client.get("/api/search?q=عقد&limit=999")
    assert r.status_code == 200
    assert len(r.get_json()["results"]) <= 50


def test_unknown_route_returns_404(client):
    r = client.get("/api/nonexistent")
    assert r.status_code == 404
    assert "error" in r.get_json()


# ---------- مسارات إدارية (مصادقة JWT + دور admin — المرحلة 1) ----------

def test_admin_create_text(client, admin_headers):
    r = client.post(
        "/api/admin/texts",
        json={"category_id": 1, "type": "law", "title": "قانون اختباري",
              "official_ref": "مرجع 1"},
        headers=admin_headers,
    )
    assert r.status_code == 201
    assert r.get_json()["id"]


def test_admin_create_text_missing_fields(client, admin_headers):
    r = client.post(
        "/api/admin/texts",
        json={"title": "ناقص"},
        headers=admin_headers,
    )
    assert r.status_code == 400
    assert "category_id" in r.get_json()["error"]


def test_admin_create_text_requires_jwt(client):
    r = client.post(
        "/api/admin/texts",
        json={"category_id": 1, "type": "law", "title": "x"},
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert r.status_code == 401


def test_admin_create_text_missing_auth_rejected(client):
    r = client.post("/api/admin/texts",
                    json={"category_id": 1, "type": "law", "title": "x"})
    assert r.status_code == 401


def test_admin_create_article(client, admin_headers):
    tid = _find_text_id(client, "قانون الالتزامات والعقود")
    r = client.post(
        f"/api/admin/texts/{tid}/articles",
        json={"number": "1", "label": "المادة 1", "content": "نص المادة",
              "plain_explanation": "شرح", "keywords": "كلمة"},
        headers=admin_headers,
    )
    assert r.status_code == 201
    assert r.get_json()["id"]


def test_admin_create_article_parent_missing(client, admin_headers):
    r = client.post(
        "/api/admin/texts/99999/articles",
        json={"number": "1", "label": "المادة 1", "content": "نص"},
        headers=admin_headers,
    )
    assert r.status_code == 404


def test_admin_create_article_legacy_key_rejected(client):
    tid = _find_text_id(client, "قانون الالتزامات والعقود")
    r = client.post(
        f"/api/admin/texts/{tid}/articles",
        json={"number": "1", "label": "المادة 1", "content": "نص"},
        headers={"X-Admin-Key": "wrong-key"},
    )
    assert r.status_code == 401


# ---------- الأمان: تقييد CORS (Security Architecture §1) ----------

def test_cors_allows_configured_origin(client):
    r = client.get("/api/health", headers={"Origin": "http://localhost:8000"})
    assert r.headers.get("Access-Control-Allow-Origin") == "http://localhost:8000"


def test_cors_rejects_unconfigured_origin(client):
    r = client.get("/api/health", headers={"Origin": "https://evil.example"})
    assert r.headers.get("Access-Control-Allow-Origin") is None


@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "DELETE"])
def test_cors_allows_expected_methods(client, method):
    r = client.open("/api/health", method=method,
                    headers={"Origin": "http://localhost:8000"})
    assert "OPTIONS" in r.headers.get("Access-Control-Allow-Methods", "")
