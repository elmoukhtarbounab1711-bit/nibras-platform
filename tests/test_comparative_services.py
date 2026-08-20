"""
اختبارات خدمات القانون المقارن (services_comparative) — المرحلة 20.

دراسات مقارنة (draft→published إداري)، مقارنات ترجع لولايات قضائية ونصوص/
مواد في المكتبة، تحقق الإسناد النصي والصلاحيات (المالك/الإدارة فقط)،
وعزل multi-tenant (قرار D-036).
"""
import pytest

from app import services_comparative
from app.database import db_session
from app.services_auth import create_user_with_role
from app.services_comparative import ComparativeError

PASSWORD = "test-password-123"


def _admin():
    return create_user_with_role(
        "admin-cmp@nibras.test", PASSWORD, "مدير", "admin",
    )


def _citizen(email="citizen-cmp@nibras.test"):
    return create_user_with_role(
        email, PASSWORD, "مواطن", "citizen", role_status="active",
        user_status="active",
    )


def _jurisdiction(slug="morocco"):
    with db_session() as conn:
        return conn.execute(
            "SELECT id FROM law_jurisdictions WHERE slug = ?", (slug,)
        ).fetchone()["id"]


def _article_id():
    with db_session() as conn:
        return conn.execute("SELECT id FROM articles LIMIT 1").fetchone()["id"]


def _study(owner=None):
    owner = owner or _citizen()
    return services_comparative.create_study(owner.id, {"title": "دراسة النفقة"})


def _add_entry(owner, study_id, jurisdiction_id, article_id):
    return services_comparative.add_entry(
        owner.id, study_id,
        {"jurisdiction_id": jurisdiction_id, "article_id": article_id,
         "note": "مقارنة"},
    )


def test_jurisdictions_seeded(fresh_db):
    jurisdictions = services_comparative.list_jurisdictions()
    slugs = {j["slug"] for j in jurisdictions}
    # المغرب مرجع مستقل (is_comparative=0) ومعزول عن ولايات المقارن
    assert "france" in slugs and "egypt" in slugs
    assert "morocco" not in slugs
    assert len(jurisdictions) >= 7


def test_create_study_starts_draft(fresh_db):
    owner = _citizen()
    result = _study(owner)
    with db_session() as conn:
        row = conn.execute(
            "SELECT status, user_id FROM comparative_studies WHERE id = ?",
            (result["id"],),
        ).fetchone()
    assert row["status"] == "draft"
    assert row["user_id"] == owner.id


def test_create_study_requires_title(fresh_db):
    owner = _citizen()
    with pytest.raises(ComparativeError):
        services_comparative.create_study(owner.id, {})


def test_study_not_public_until_published(fresh_db):
    owner = _citizen()
    study = _study(owner)
    # العموم لا يرون مسودة
    assert services_comparative.list_studies()["count"] == 0
    assert services_comparative.get_study(study["id"]) is None
    # المالك يراها
    assert services_comparative.get_study(
        study["id"], viewer_id=owner.id
    )["status"] == "draft"


def test_admin_publishes_study(fresh_db):
    admin = _admin()
    owner = _citizen()
    study = _study(owner)
    services_comparative.set_study_status(admin.id, study["id"], "published")
    published = services_comparative.list_studies()
    assert published["count"] == 1
    assert published["studies"][0]["id"] == study["id"]
    detail = services_comparative.get_study(study["id"])
    assert detail["status"] == "published"
    assert detail["creator_name"] == "مواطن"


def test_set_status_validation(fresh_db):
    admin = _admin()
    owner = _citizen()
    study = _study(owner)
    with pytest.raises(ComparativeError):
        services_comparative.set_study_status(admin.id, study["id"], "bogus")
    with pytest.raises(ComparativeError):
        services_comparative.set_study_status(admin.id, 999, "published")


def test_only_owner_or_admin_manage(fresh_db):
    admin = _admin()
    owner = _citizen()
    intruder = _citizen("intruder@nibras.test")
    study = _study(owner)
    with pytest.raises(ComparativeError):
        services_comparative.update_study(intruder.id, study["id"],
                                          {"title": "خاطف"})
    with pytest.raises(ComparativeError):
        services_comparative.delete_study(intruder.id, study["id"])
    # الإدارة تسمح
    services_comparative.update_study(admin.id, study["id"],
                                      {"title": "مُدار"}, is_admin=True)
    assert services_comparative.get_study(
        study["id"], viewer_id=owner.id
    )["title"] == "مُدار"


def test_add_entry_roundtrip(fresh_db):
    owner = _citizen()
    study = _study(owner)
    jid = _jurisdiction()
    aid = _article_id()
    _add_entry(owner, study["id"], jid, aid)
    detail = services_comparative.get_study(
        study["id"], viewer_id=owner.id
    )
    assert len(detail["entries"]) == 1
    assert detail["entries"][0]["jurisdiction_id"] == jid
    assert detail["entries"][0]["article_id"] == aid
    assert detail["entry_count"] == 1


def test_entry_validation(fresh_db):
    owner = _citizen()
    study = _study(owner)
    aid = _article_id()
    with pytest.raises(ComparativeError):
        _add_entry(owner, study["id"], 1, 9999)
    with pytest.raises(ComparativeError):
        services_comparative.add_entry(
            owner.id, study["id"],
            {"jurisdiction_id": 9999, "article_id": aid},
        )
    with pytest.raises(ComparativeError):
        services_comparative.add_entry(owner.id, study["id"], {})


def test_entry_with_article_resolves_text(fresh_db):
    owner = _citizen()
    study = _study(owner)
    aid = _article_id()
    with db_session() as conn:
        expected_text = conn.execute(
            "SELECT legal_text_id FROM articles WHERE id = ?", (aid,)
        ).fetchone()["legal_text_id"]
    entry = _add_entry(owner, study["id"], _jurisdiction(), aid)
    with db_session() as conn:
        row = conn.execute(
            "SELECT legal_text_id, article_id FROM comparative_entries "
            "WHERE id = ?", (entry["id"],),
        ).fetchone()
    assert row["legal_text_id"] == expected_text
    assert row["article_id"] == aid


def test_entry_text_only(fresh_db):
    owner = _citizen()
    study = _study(owner)
    with db_session() as conn:
        lt = conn.execute("SELECT id FROM legal_texts LIMIT 1").fetchone()["id"]
    result = services_comparative.add_entry(
        owner.id, study["id"],
        {"jurisdiction_id": _jurisdiction(), "legal_text_id": lt},
    )
    assert result["id"]


def test_update_and_delete_entry(fresh_db):
    owner = _citizen()
    study = _study(owner)
    jid = _jurisdiction()
    aid = _article_id()
    entry = _add_entry(owner, study["id"], jid, aid)
    services_comparative.update_entry(
        owner.id, entry["id"], {"position": 3, "note": "معدلة"}
    )
    detail = services_comparative.get_study(study["id"], viewer_id=owner.id)
    assert detail["entries"][0]["position"] == 3
    assert detail["entries"][0]["note"] == "معدلة"
    services_comparative.delete_entry(owner.id, entry["id"])
    detail = services_comparative.get_study(study["id"], viewer_id=owner.id)
    assert detail["entries"] == []
    assert detail["entry_count"] == 0


def test_foreign_entry_managed_by_study_owner(fresh_db):
    owner = _citizen()
    other = _citizen("other@nibras.test")
    study = _study(owner)
    aid = _article_id()
    entry = _add_entry(owner, study["id"], _jurisdiction(), aid)
    with pytest.raises(ComparativeError):
        services_comparative.update_entry(other.id, entry["id"],
                                          {"note": "مقتحم"})
    with pytest.raises(ComparativeError):
        services_comparative.delete_entry(other.id, entry["id"])


def test_search_and_filter_by_jurisdiction(fresh_db):
    admin = _admin()
    owner = _citizen()
    study = _study(owner)
    ma = _jurisdiction("morocco")
    aid = _article_id()
    _add_entry(owner, study["id"], ma, aid)
    services_comparative.set_study_status(admin.id, study["id"], "published")
    assert services_comparative.list_studies(q="النفقة")["count"] == 1
    assert services_comparative.list_studies(
        jurisdiction_id=ma
    )["count"] == 1
    other = _jurisdiction("france")
    assert services_comparative.list_studies(
        jurisdiction_id=other
    )["count"] == 0


def test_jurisdiction_crud_and_guard(fresh_db):
    admin = _admin()
    jid = services_comparative.create_jurisdiction(
        admin.id, {"slug": "spain", "name": "إسبانيا"}
    )
    jurisdictions = services_comparative.list_jurisdictions()
    assert any(j["slug"] == "spain" for j in jurisdictions)
    services_comparative.update_jurisdiction(admin.id, jid, {"name": "المملكة"})
    with pytest.raises(ComparativeError):
        services_comparative.create_jurisdiction(
            admin.id, {"slug": "spain", "name": "مكرر"}
        )
    # نظام مستخدم في دراسة لا يُحذف
    owner = _citizen()
    study = _study(owner)
    aid = _article_id()
    _add_entry(owner, study["id"], jid, aid)
    with pytest.raises(ComparativeError):
        services_comparative.delete_jurisdiction(admin.id, jid)
    # غير المستخدم يُحذف
    jid2 = services_comparative.create_jurisdiction(
        admin.id, {"slug": "germany", "name": "ألمانيا"}
    )
    services_comparative.delete_jurisdiction(admin.id, jid2)
    assert not any(
        j["slug"] == "germany"
        for j in services_comparative.list_jurisdictions()
    )


def test_admin_audit_logged(fresh_db):
    admin = _admin()
    owner = _citizen()
    study = _study(owner)
    services_comparative.set_study_status(admin.id, study["id"], "published")
    services_comparative.create_jurisdiction(
        admin.id, {"slug": "belgium", "name": "بلجيكا"}
    )
    with db_session() as conn:
        actions = [
            r["action"]
            for r in conn.execute(
                "SELECT action FROM admin_audit_log WHERE action LIKE "
                "'comparative.%' ORDER BY id"
            )
        ]
    assert "comparative.status" in actions
    assert "comparative.jurisdiction.create" in actions
