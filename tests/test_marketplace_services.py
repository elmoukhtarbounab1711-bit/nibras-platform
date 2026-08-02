"""
اختبارات طبقة خدمات سوق القوالب (المرحلة 7 — قرار D-025).

بذر الفئات، ترقيم/تصفية/بحث، تفصيل بلا storage_key، حذف فعلي للقالب،
منع حذف قالب له سجل شراءات، قيود الفئات، وتدقيق الإجراءات (Security §8).
"""
import pytest

from app import services_auth, services_marketplace
from app.database import db_session
from app.services_marketplace import (
    MarketplaceError,
    create_category,
    create_template,
    delete_category,
    delete_template,
    get_template,
    list_categories,
    list_templates,
    update_category,
    update_template,
)

PASSWORD = "test-password-123"


class _FakeFile:
    """محاكاة ملف مرفوع لطبقة الخدمة (filename + read)."""

    def __init__(self, content, name):
        self.content = content
        self.filename = name

    def read(self):
        return self.content


def _file(content=b"%PDF-1.4 t", name="t.pdf"):
    return _FakeFile(content, name)


def _admin():
    return services_auth.create_user_with_role(
        email="adm@nibras.test", password=PASSWORD, full_name="مسؤول",
        role_code="admin", role_status="active", user_status="active",
    )


def _create(admin, category_id=1, **overrides):
    data = {"category_id": category_id, "title": "قالب",
            "description": "وصف", "price_cents": 1000}
    data.update(overrides)
    return create_template(admin.id, data, _file())


def test_categories_seeded(fresh_db):
    cats = list_categories()
    assert [c["slug"] for c in cats] == [
        "dostouri", "madani", "usra", "jinai", "shughl", "tijari",
    ]
    services_marketplace.ensure_defaults()
    assert len(list_categories()) == 6


def test_create_and_public_item(fresh_db):
    result = _create(_admin())
    item = get_template(result["id"])
    assert item["title"] == "قالب"
    assert item["price_cents"] == 1000
    assert "storage_key" not in item
    assert len(list_templates()) == 1
    assert list_categories()[0]["template_count"] == 1


def test_filters_search_pagination(fresh_db):
    admin = _admin()
    _create(admin, title="عقد إيجار", category_id=1)
    _create(admin, title="عقد عمل", category_id=5)
    _create(admin, title="عقد زواج", category_id=3)
    _create(admin, title="وكالة", category_id=2)
    assert len(list_templates()) == 4
    assert len(list_templates(category_id=1)) == 1
    assert len(list_templates(q="عقد")) == 3
    assert len(list_templates(q="غير موجود")) == 0
    assert len(list_templates(limit=2, offset=2)) == 2
    assert len(list_templates(limit=200)) == 4


def test_create_validation(fresh_db):
    admin = _admin()
    with pytest.raises(MarketplaceError) as exc:
        _create(admin, title=" ")
    assert exc.value.status_code == 400
    with pytest.raises(MarketplaceError) as exc:
        _create(admin, price_cents=-5)
    assert exc.value.status_code == 400
    with pytest.raises(MarketplaceError) as exc:
        _create(admin, category_id=999)
    assert exc.value.status_code == 400
    with pytest.raises(MarketplaceError) as exc:
        create_template(admin.id, {"category_id": 1, "title": "x",
                                   "price_cents": 1}, None)
    assert exc.value.status_code == 400
    with pytest.raises(MarketplaceError) as exc:
        create_template(admin.id, {"category_id": 1, "title": "x",
                                   "price_cents": 1},
                        _file(name="doc.exe"))
    assert exc.value.status_code == 400


def test_update_fields_and_file_only(fresh_db):
    admin = _admin()
    template_id = _create(admin)["id"]

    update_template(admin.id, template_id, {"price_cents": 2500}, None)
    assert get_template(template_id)["price_cents"] == 2500

    update_template(admin.id, template_id, {}, _file(content=b"new", name="v2.pdf"))

    with pytest.raises(MarketplaceError) as exc:
        update_template(admin.id, template_id, {}, None)
    assert exc.value.status_code == 400
    with pytest.raises(MarketplaceError) as exc:
        update_template(admin.id, template_id, {"price_cents": -1}, None)
    assert exc.value.status_code == 400
    with pytest.raises(MarketplaceError) as exc:
        update_template(admin.id, 999, {"title": "x"}, None)
    assert exc.value.status_code == 404
    with pytest.raises(MarketplaceError) as exc:
        update_template(admin.id, template_id, {"title": " "}, None)
    assert exc.value.status_code == 400


def test_delete_template_and_purchases_guard(fresh_db):
    admin = _admin()
    template_id = _create(admin)["id"]
    assert delete_template(admin.id, template_id)["id"] == template_id
    assert get_template(template_id) is None
    with pytest.raises(MarketplaceError) as exc:
        delete_template(admin.id, template_id)
    assert exc.value.status_code == 404

    template_id = _create(admin)["id"]
    with db_session() as conn:
        conn.execute(
            "INSERT INTO purchases (user_id, template_id, purchased_at) "
            "VALUES (?, ?, datetime('now'))", (admin.id, template_id),
        )
    with pytest.raises(MarketplaceError) as exc:
        delete_template(admin.id, template_id)
    assert exc.value.status_code == 409


def test_category_lifecycle_and_constraints(fresh_db):
    admin = _admin()
    cat_id = create_category(admin.id, {"slug": "aoula", "name": "الأحوال"})
    assert list_categories()[-1]["slug"] == "aoula"
    update_category(admin.id, cat_id, {"name": "الأحوال الشخصية"})

    with pytest.raises(MarketplaceError) as exc:
        create_category(admin.id, {"slug": "aoula", "name": "مكرر"})
    assert exc.value.status_code == 400
    with pytest.raises(MarketplaceError) as exc:
        update_category(admin.id, cat_id, {"slug": "dostouri"})
    assert exc.value.status_code == 400

    _create(admin, category_id=cat_id)
    with pytest.raises(MarketplaceError) as exc:
        delete_category(admin.id, cat_id)
    assert exc.value.status_code == 409
    with pytest.raises(MarketplaceError) as exc:
        delete_category(admin.id, 999)
    assert exc.value.status_code == 404


def test_admin_actions_audited(fresh_db):
    admin = _admin()
    template_id = _create(admin)["id"]
    update_template(admin.id, template_id, {"price_cents": 2000}, None)
    delete_template(admin.id, template_id)
    with db_session() as conn:
        actions = [
            r["action"] for r in conn.execute(
                "SELECT action FROM admin_audit_log WHERE admin_id = ? ORDER BY id",
                (admin.id,),
            )
        ]
    assert "marketplace.create" in actions
    assert "marketplace.update" in actions
    assert "marketplace.delete" in actions
