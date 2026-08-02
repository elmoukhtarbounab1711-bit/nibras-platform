"""
اختبارات لوحة التحليلات الإدارية (API) — المرحلة 8 (قرار D-026).

نقطة واحدة GET /api/admin/analytics/summary بدور admin تعيد ملخصًا متداخلًا
قراءة-فقط من جداول الوحدات القائمة؛ الإيرادات والتحويل صفرية مؤجَّلة (BRD §5).
"""
import pytest

from app import config, services_auth
from app.database import db_session

PASSWORD = "test-password-123"

TOP_LEVEL_KEYS = {
    "generated_at", "users", "ai", "calculators", "documents", "community",
    "professionals", "marketplace", "verification", "moderation", "revenue",
    "trends",
}


@pytest.fixture(autouse=True)
def _isolate_uploads(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "UPLOAD_DIR", str(tmp_path / "uploads"))
    yield


def _headers(user):
    token = services_auth.create_access_token(user.id)[0]
    return {"Authorization": f"Bearer {token}"}


def _user(email, role_code="citizen"):
    return services_auth.create_user_with_role(
        email=email, password=PASSWORD, full_name="مستخدم تحليلات",
        role_code=role_code, role_status="active", user_status="active",
    )


def _admin():
    return _user("admin-analytics@nibras.test", "admin")


def _get_summary(client, headers):
    resp = client.get("/api/admin/analytics/summary", headers=headers)
    assert resp.status_code == 200
    return resp.get_json()


def test_summary_requires_admin(client):
    assert client.get("/api/admin/analytics/summary").status_code == 401
    citizen_h = _headers(_user("cit@nibras.test"))
    assert client.get(
        "/api/admin/analytics/summary", headers=citizen_h
    ).status_code == 403


def test_summary_empty_db_structure(client):
    admin = _admin()
    data = _get_summary(client, _headers(admin))
    assert set(data) == TOP_LEVEL_KEYS
    assert data["users"] == {
        "total": 1, "active": 1, "suspended": 0, "admins": 1,
        "professionals_pending": 0, "professionals_active": 0, "new_today": 1,
    }
    assert data["ai"]["total"] == 0
    assert data["ai"]["by_mode"] == {}
    assert data["calculators"]["total_runs"] == 0
    assert data["calculators"]["distinct_calculators"] == 0
    assert data["documents"]["generated_total"] == 0
    assert data["documents"]["templates"] == 3
    assert data["community"]["posts"] == 0
    assert data["community"]["reports_open"] == 0
    assert data["professionals"]["profiles_total"] == 0
    assert data["professionals"]["avg_rating"] is None
    assert data["marketplace"]["templates"] == 0
    assert data["marketplace"]["catalog_value_cents"] == 0
    assert data["marketplace"]["purchases"] == 0
    assert data["verification"]["pending_requests"] == 0
    assert data["moderation"]["open_reports"] == 0
    assert data["revenue"]["subscriptions_cents"] == 0
    assert data["revenue"]["marketplace_cents"] == 0
    assert data["revenue"]["ads_cents"] == 0
    assert "note" in data["revenue"]
    assert len(data["trends"]) == 7
    assert all(
        {"date", "ai_queries", "calculator_runs", "documents", "new_users"}
        <= set(entry) for entry in data["trends"]
    )


def test_summary_reflects_usage(client, fresh_db):
    admin = _admin()
    citizen = _user("user@nibras.test")
    headers = _headers(admin)

    with db_session() as conn:
        conn.execute(
            "INSERT INTO ai_queries (user_id, question, response, mode, "
            "provider) VALUES (?, ?, ?, 'grounded', 'test')",
            (citizen.id, "سؤال", "جواب"),
        )
        conn.execute(
            "INSERT INTO calculator_runs (calculator_id, user_id, input_json, "
            "result_json) VALUES (1, ?, '{}', '{}')",
            (citizen.id,),
        )
        conn.execute(
            "INSERT INTO generated_documents (user_id, template_id, "
            "answers_json, doc_text, created_at, updated_at) "
            "VALUES (?, 1, '{}', 'نص', datetime('now'), datetime('now'))",
            (citizen.id,),
        )
        post_id = conn.execute(
            "INSERT INTO posts (user_id, category_id, title, body, "
            "created_at, updated_at) "
            "VALUES (?, 1, 'عنوان', 'نص', datetime('now'), datetime('now'))",
            (citizen.id,),
        ).lastrowid
        conn.execute(
            "INSERT INTO comments (post_id, user_id, body, created_at, "
            "updated_at) VALUES (?, ?, 'تعليق', datetime('now'), "
            "datetime('now'))",
            (post_id, citizen.id),
        )
        conn.execute(
            "INSERT INTO reactions (user_id, post_id, type, created_at) "
            "VALUES (?, ?, 'like', datetime('now'))",
            (citizen.id, post_id),
        )
        conn.execute(
            "INSERT INTO reports (reporter_id, target_type, target_id, "
            "reason, status, created_at) VALUES (?, 'post', ?, 'سبب', "
            "'open', datetime('now'))",
            (citizen.id, post_id),
        )
        profile_id = conn.execute(
            "INSERT INTO professional_profiles (user_id, profession_type, "
            "verification_status, created_at, updated_at) "
            "VALUES (?, 'lawyer', 'verified', datetime('now'), "
            "datetime('now'))",
            (citizen.id,),
        ).lastrowid
        conn.execute(
            "INSERT INTO professional_reviews (profile_id, reviewer_id, "
            "rating, comment, created_at) "
            "VALUES (?, ?, 5, 'جيد', datetime('now'))",
            (profile_id, admin.id),
        )
        conn.execute(
            "INSERT INTO marketplace_templates (category_id, title, "
            "description, price_cents, storage_key, created_at, updated_at) "
            "VALUES (1, 'قالب', NULL, 1000, 'key.pdf', datetime('now'), "
            "datetime('now'))",
        )

    data = _get_summary(client, headers)
    assert data["users"]["total"] == 2
    assert data["users"]["admins"] == 1
    assert data["users"]["new_today"] == 2
    assert data["ai"]["total"] == 1
    assert data["ai"]["by_mode"] == {"grounded": 1}
    assert data["calculators"]["total_runs"] == 1
    assert data["calculators"]["distinct_calculators"] == 1
    assert data["calculators"]["by_calculator"] == {"inheritance": 1}
    assert data["documents"]["generated_total"] == 1
    assert data["documents"]["generated_today"] == 1
    assert data["community"]["posts"] == 1
    assert data["community"]["comments"] == 1
    assert data["community"]["reactions"] == 1
    assert data["community"]["reports_open"] == 1
    assert data["professionals"]["profiles_total"] == 1
    assert data["professionals"]["by_status"] == {"verified": 1}
    assert data["professionals"]["reviews"] == 1
    assert data["professionals"]["avg_rating"] == 5.0
    assert data["marketplace"]["templates"] == 1
    assert data["marketplace"]["catalog_value_cents"] == 1000
    assert data["marketplace"]["purchases"] == 0
    assert data["moderation"]["open_reports"] == 1
    assert data["trends"][-1]["ai_queries"] == 1
    assert data["trends"][-1]["calculator_runs"] == 1
    assert data["trends"][-1]["documents"] == 1
    assert data["trends"][-1]["new_users"] == 2
