"""
اختبارات طبقة خدمات المجتمع (المرحلة 6 — قرار D-024).

بذر الفئات، حد الترقيم والتصفية، شارة تحقُّق المحترفين، حالة المحتوى
بلا حذف فعلي، دلالات إجراءات الإشراف مع تسجيل التدقيق، وإعادة البلاغ
بعد المعالجة.
"""
import pytest

from app import services_admin, services_auth, services_community
from app.database import db_session
from app.services_admin import AdminError, moderate_report
from app.services_community import (
    CommunityError,
    add_comment,
    create_post,
    create_report,
    delete_comment,
    get_post,
    list_posts,
    toggle_reaction,
)

PASSWORD = "test-password-123"


def _user(email, role_code="citizen", role_status="active"):
    return services_auth.create_user_with_role(
        email=email, password=PASSWORD, full_name="مستخدم",
        role_code=role_code, role_status=role_status, user_status="active",
    )


def _admin():
    return _user("adm@nibras.test", "admin")


def _post(author, category_id=1):
    return create_post(author.id, {
        "category_id": category_id, "title": "عنوان", "body": "محتوى",
    })


def test_categories_seeded(fresh_db):
    cats = services_community.list_categories()
    assert [c["slug"] for c in cats] == [
        "dostouri", "madani", "usra", "jinai", "shughl", "tijari",
    ]
    # ensure_defaults idempotent
    services_community.ensure_defaults()
    assert len(services_community.list_categories()) == 6


def test_verified_badge_on_posts(fresh_db):
    lawyer = _user("lawyer@nibras.test", "lawyer", role_status="pending_verification")
    _create_profile(lawyer.id)
    services_admin.approve_verification(_admin().id, lawyer.id)
    post = _post(lawyer)
    assert post["author_is_verified"] is True
    listed = list_posts()
    assert listed[0]["author_is_verified"] is True


def _create_profile(user_id):
    from app.services_professionals import upsert_profile

    return upsert_profile(user_id, {
        "profession_type": "lawyer", "city": "الرباط", "bio": "محامٍ",
        "specialties": [],
    })


def test_plain_user_not_verified(fresh_db):
    citizen = _user("cit@nibras.test")
    assert _post(citizen)["author_is_verified"] is False


def test_pagination_and_category_filter(fresh_db):
    for i in range(3):
        _post(_user(f"a{i}@nibras.test"))
    _post(_user("b@nibras.test"), category_id=2)
    assert len(list_posts()) == 4
    assert len(list_posts(category_id=2)) == 1
    assert len(list_posts(limit=2, offset=2)) == 2
    assert len(list_posts(limit=200)) == 4  # يُقصّر إلى MAX
    assert len(list_posts(limit=1)) == 1


def test_owner_visibility_and_no_hard_delete(fresh_db):
    author = _user("own@nibras.test")
    post = _post(author)
    from app.services_community import delete_post

    delete_post(author.id, post["id"])
    assert get_post(post["id"]) is None
    assert get_post(post["id"], viewer_id=author.id)["status"] == "removed"
    with db_session() as conn:
        row = conn.execute(
            "SELECT status FROM posts WHERE id = ?", (post["id"],)
        ).fetchone()
    assert row["status"] == "removed"


def test_comment_removed_preserved(fresh_db):
    author = _user("co@nibras.test")
    post = _post(author)
    commenter = _user("cm@nibras.test")
    comment = add_comment(commenter.id, post["id"], {"body": "تعليق"})
    delete_comment(commenter.id, post["id"], comment["id"])
    detail = get_post(post["id"], viewer_id=author.id)
    assert detail["comment_count"] == 0
    assert detail["comments"] == []


def test_reaction_toggle_counts(fresh_db):
    author = _user("ra@nibras.test")
    post = _post(author)
    u1, u2 = _user("r1@nibras.test"), _user("r2@nibras.test")
    toggle_reaction(u1.id, post["id"], "like")
    toggle_reaction(u2.id, post["id"], "like")
    toggle_reaction(u1.id, post["id"], "helpful")
    assert toggle_reaction(u1.id, post["id"], "like")["reacted"] is False
    detail = get_post(post["id"])
    assert detail["reactions"] == {"like": 1, "helpful": 1}
    assert detail["reaction_count"] == 2


def test_report_duplicate_and_rereport_after_resolution(fresh_db):
    author = _user("da@nibras.test")
    post = _post(author)
    reporter = _user("dr@nibras.test")

    first = create_report(reporter.id, {
        "target_type": "post", "target_id": post["id"], "reason": "سبب",
    })
    second = create_report(reporter.id, {
        "target_type": "post", "target_id": post["id"], "reason": "سبب آخر",
    })
    assert second["already_reported"] is True
    assert second["id"] == first["id"]

    admin = _admin()
    moderate_report(admin.id, first["id"], "dismiss")
    reopened = create_report(reporter.id, {
        "target_type": "post", "target_id": post["id"], "reason": "سبب جديد",
    })
    assert reopened.get("already_reported") is not True


def test_moderate_report_hide_and_audit(fresh_db):
    author = _user("ma@nibras.test")
    post = _post(author)
    report = create_report(_user("mr@nibras.test").id, {
        "target_type": "post", "target_id": post["id"], "reason": "إساءة",
    })
    admin = _admin()
    result = moderate_report(admin.id, report["id"], "hide")
    assert result["status"] == "actioned"
    assert get_post(post["id"]) is None
    with db_session() as conn:
        audit = conn.execute(
            "SELECT action, target_type, target_id FROM admin_audit_log "
            "WHERE action = 'moderation.hide'"
        ).fetchone()
    assert audit["target_id"] == report["id"]
    with pytest.raises(AdminError) as exc:
        moderate_report(admin.id, report["id"], "dismiss")
    assert exc.value.status_code == 409


def test_moderate_report_remove_comment(fresh_db):
    author = _user("sa@nibras.test")
    post = _post(author)
    comment = add_comment(_user("sc@nibras.test").id, post["id"], {"body": "سيئ"})
    report = create_report(_user("sr@nibras.test").id, {
        "target_type": "comment", "target_id": comment["id"], "reason": "إساءة",
    })
    moderate_report(_admin().id, report["id"], "remove")
    detail = get_post(post["id"], viewer_id=author.id)
    assert detail["comment_count"] == 0


def test_moderate_report_professional_profile_dismiss_only(fresh_db):
    lawyer = _user("pp@nibras.test", "lawyer", role_status="pending_verification")
    profile = _create_profile(lawyer.id)
    report = create_report(_user("pr@nibras.test").id, {
        "target_type": "professional_profile", "target_id": profile["id"],
        "reason": "بيانات مضللة",
    })
    admin = _admin()
    with pytest.raises(AdminError) as exc:
        moderate_report(admin.id, report["id"], "hide")
    assert exc.value.status_code == 400
    assert moderate_report(admin.id, report["id"], "dismiss")["status"] == "dismissed"


def test_moderate_report_validation(fresh_db):
    admin = _admin()
    with pytest.raises(AdminError) as exc:
        moderate_report(admin.id, 1, "warn")
    assert exc.value.status_code == 400
    with pytest.raises(AdminError) as exc:
        moderate_report(admin.id, 1, "dismiss")
    assert exc.value.status_code == 404


def test_create_report_validation(fresh_db):
    author = _user("cv@nibras.test")
    post = _post(author)
    reporter = _user("crv@nibras.test")
    with pytest.raises(CommunityError) as exc:
        create_report(reporter.id, {"target_type": "post", "target_id": post["id"],
                                    "reason": "  "})
    assert exc.value.status_code == 400
    with pytest.raises(CommunityError) as exc:
        create_report(reporter.id, {"target_type": "post", "target_id": "abc",
                                    "reason": "x"})
    assert exc.value.status_code == 400
    with pytest.raises(CommunityError) as exc:
        create_report(author.id, {"target_type": "post", "target_id": post["id"],
                                  "reason": "x"})
    assert exc.value.status_code == 403


def test_comment_on_hidden_post_requires_author(fresh_db):
    author = _user("h@nibras.test")
    post = _post(author)
    from app.services_community import delete_post

    delete_post(author.id, post["id"])
    outsider = _user("ho@nibras.test")
    with pytest.raises(CommunityError) as exc:
        add_comment(outsider.id, post["id"], {"body": "تعليق"})
    assert exc.value.status_code == 404
