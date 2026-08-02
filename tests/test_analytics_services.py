"""
اختبارات خدمات لوحة التحليلات (services_analytics) — المرحلة 8 (قرار D-026).

تجميع قراءة-فقط من الجداول القائمة: بنية الملخص، الاتجاه، حسابات الأدوار
المهنية/المشرفين، الطابوران، الإيرادات الصفرية، وقيمة السوق.
"""
from app import services_analytics
from app.database import db_session
from app.services_auth import create_user_with_role

PASSWORD = "test-password-123"


def test_summary_top_level_keys(fresh_db):
    assert set(services_analytics.summary()) == {
        "generated_at", "users", "ai", "calculators", "documents",
        "community", "professionals", "marketplace", "verification",
        "moderation", "revenue", "trends",
    }


def test_trends_seven_days_zero_filled(fresh_db):
    trends = services_analytics.summary()["trends"]
    assert len(trends) == 7
    assert trends[6]["date"] is not None
    assert all(
        set(entry) == {"date", "ai_queries", "calculator_runs", "documents",
                       "new_users"}
        for entry in trends
    )
    assert trends[0]["ai_queries"] == 0


def test_users_roles_and_verification_aggregates(fresh_db):
    create_user_with_role("a@x.test", PASSWORD, "مدير", "admin")
    create_user_with_role(
        "l@x.test", PASSWORD, "محامية", "lawyer",
        role_status="pending_verification",
    )
    data = services_analytics.summary()
    assert data["users"]["total"] == 2
    assert data["users"]["admins"] == 1
    assert data["users"]["professionals_pending"] == 1
    assert data["users"]["professionals_active"] == 0
    assert data["verification"]["pending_requests"] == 1


def test_verified_professional_active(fresh_db):
    lawyer = create_user_with_role(
        "l@x.test", PASSWORD, "محام", "lawyer", role_status="active"
    )
    with db_session() as conn:
        conn.execute(
            "INSERT INTO professional_profiles (user_id, profession_type, "
            "verification_status, created_at) "
            "VALUES (?, 'lawyer', 'verified', datetime('now'))",
            (lawyer.id,),
        )
    data = services_analytics.summary()
    assert data["users"]["professionals_active"] == 1
    assert data["users"]["professionals_pending"] == 0
    assert data["verification"]["pending_requests"] == 0


def test_marketplace_value_and_purchases(fresh_db):
    with db_session() as conn:
        conn.execute(
            "INSERT INTO marketplace_templates (category_id, title, "
            "description, price_cents, storage_key, created_at) "
            "VALUES (1, 'ق1', NULL, 500, 'a.pdf', datetime('now'))",
        )
        conn.execute(
            "INSERT INTO marketplace_templates (category_id, title, "
            "description, price_cents, storage_key, created_at) "
            "VALUES (2, 'ق2', NULL, 1500, 'b.pdf', datetime('now'))",
        )
    data = services_analytics.summary()
    assert data["marketplace"]["templates"] == 2
    assert data["marketplace"]["catalog_value_cents"] == 2000
    assert data["marketplace"]["purchases"] == 0


def test_revenue_zeroed_pending_billing(fresh_db):
    revenue = services_analytics.summary()["revenue"]
    assert revenue["subscriptions_cents"] == 0
    assert revenue["marketplace_cents"] == 0
    assert revenue["ads_cents"] == 0
    assert "note" in revenue
