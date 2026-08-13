"""
اختبارات العزل الكامل لبيانات multi-tenant (المرحلة 18 — قرار D-036).

عزل 15 جدولًا موزعة على 5 وحدات (المكتبة، المجتمع، المحترفون، السوق،
الإعلانات) مع فرض X-Tenant-Id المركزي. التركيز هنا على نطاق الخدمات:
كل مستأجر يقرأ ويكتب بياناته فقط، والإحصاءات الفرعية لا تُسرِّب الأرقام
عبر المستأجرين، والعمليات على صفوف مستأجر آخر تُرفض (404/رفض)، وكتابة
التحليلات تُقيَّد بمستأجر الطلب.
"""
from contextlib import contextmanager

import pytest

from app import (
    config,
    services,
    services_admin,
    services_ads,
    services_analytics,
    services_auth,
    services_community,
    services_comparative,
    services_marketplace,
    services_professionals,
    services_tenants,
    tenant_scope,
)
from app.database import db_session
from app.services_ads import AdError
from app.services_community import CommunityError
from app.services_comparative import ComparativeError
from app.services_marketplace import MarketplaceError

PASSWORD = "test-password-123"

_email_seq = 0


def _unique_email(prefix):
    global _email_seq
    _email_seq += 1
    return f"{prefix}-{_email_seq}@nibras.test"


@pytest.fixture(autouse=True)
def _multitenant(monkeypatch):
    monkeypatch.setattr(config, "MULTI_TENANT", True)
    yield
    tenant_scope.clear_current_tenant()


@pytest.fixture()
def _uploads(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "UPLOAD_DIR", str(tmp_path / "uploads"))
    yield


class _Tenants:
    """مستأجران (acme/globex) مع مستخدمي أدوار داخل كل مستأجر."""

    def __init__(self):
        admin = services_auth.create_user_with_role(
            email=_unique_email("root"), password=PASSWORD, full_name="جذر",
            role_code="admin", role_status="active", user_status="active",
        )
        self.acme = services_tenants.create_tenant(admin.id, "أكسي", "acme")
        self.globex = services_tenants.create_tenant(admin.id, "غلوبكس", "globex")

    def user(self, tenant, email, role="citizen", role_status="active"):
        return services_auth.create_user_with_role(
            email=email, password=PASSWORD, full_name="مستخدم",
            role_code=role, role_status=role_status, user_status="active",
            tenant_id=tenant["id"],
        )

    def admin(self, tenant):
        return self.user(tenant, _unique_email("adm"), "admin")


@contextmanager
def _scope(tenant_id):
    tenant_scope.set_current_tenant(tenant_id)
    try:
        yield
    finally:
        tenant_scope.clear_current_tenant()


# ---------------------------------------------------------------------------
# المكتبة (categories, legal_texts, articles)
# ---------------------------------------------------------------------------

def _insert_library_category(tenant_id, slug, name):
    with db_session() as conn:
        return conn.execute(
            "INSERT INTO categories (slug, name, description, tenant_id) "
            "VALUES (?,?,?,?)",
            (slug, name, "وصف", tenant_id),
        ).lastrowid


def test_library_categories_isolated(fresh_db):
    tns = _Tenants()
    _insert_library_category(tns.acme["id"], "acme-cat", "فئة أكسي")
    _insert_library_category(tns.globex["id"], "globex-cat", "فئة غلوبكس")
    with _scope(tns.acme["id"]):
        slugs = [c["slug"] for c in services.list_categories()]
    with _scope(tns.globex["id"]):
        g_slugs = [c["slug"] for c in services.list_categories()]
    assert slugs == ["acme-cat"]
    assert g_slugs == ["globex-cat"]


def test_library_texts_articles_and_search_isolated(fresh_db):
    tns = _Tenants()
    for tenant, slug, word, number in (
        (tns.acme, "acme-cat", "الوضوح", "10"),
        (tns.globex, "globex-cat", "الشموخ", "20"),
    ):
        with _scope(tenant["id"]):
            cat = _insert_library_category(tenant["id"], slug, f"فئة {slug}")
            text_id = services_admin.create_text(
                tns.admin(tenant).id,
                {"category_id": cat, "type": "code", "title": f"نص {slug}",
                 "official_ref": f"ref-{slug}"},
            )
            services_admin.create_article(
                tns.admin(tenant).id, text_id,
                {"number": number, "label": f"المادة {number}",
                 "content": f"محتوى {word} للمستأجر {slug}",
                 "keywords": word},
            )

    with _scope(tns.acme["id"]):
        texts = services.list_texts()
        assert [t["title"] for t in texts] == ["نص acme-cat"]
        assert texts[0]["article_count"] == 1
        text_id = texts[0]["id"]
        assert services.get_text(text_id)["articles"]
        hits = services.search_articles("الوضوح")
        assert len(hits) == 1 and hits[0]["legal_text_title"] == "نص acme-cat"
    with _scope(tns.globex["id"]):
        assert [t["title"] for t in services.list_texts()] == ["نص globex-cat"]
        assert services.search_articles("الوضوح") == []
        assert [a["label"] for a in services.search_articles("الشموخ")] == ["المادة 20"]


def test_library_cross_tenant_reads_are_null(fresh_db):
    tns = _Tenants()
    with _scope(tns.acme["id"]):
        cat = _insert_library_category(tns.acme["id"], "acme-cat", "فئة أكسي")
        text_id = services_admin.create_text(
            tns.admin(tns.acme).id,
            {"category_id": cat, "type": "code", "title": "نص أكسي"},
        )
        article_id = services_admin.create_article(
            tns.admin(tns.acme).id, text_id,
            {"number": "1", "label": "المادة 1", "content": "محتوى أكسي"},
        )
    with _scope(tns.globex["id"]):
        assert services.get_text(text_id) is None
        assert services.get_article(article_id) is None
        assert services.list_texts() == []
    with _scope(tns.acme["id"]):
        assert services.get_text(text_id) is not None
        assert services.get_article(article_id) is not None


# ---------------------------------------------------------------------------
# المجتمع (posts, comments, reactions, reports)
# ---------------------------------------------------------------------------

def _post(tns, tenant):
    return services_community.create_post(tns.user(tenant, _unique_email("post")).id, {
        "category_id": 1, "title": f"عنوان {tenant['slug']}", "body": "محتوى",
    })


def test_community_posts_isolated(fresh_db):
    tns = _Tenants()
    with _scope(tns.acme["id"]):
        a_post = _post(tns, tns.acme)
    with _scope(tns.globex["id"]):
        b_post = _post(tns, tns.globex)
    with _scope(tns.acme["id"]):
        listed = services_community.list_posts()
        assert [p["id"] for p in listed] == [a_post["id"]]
        assert services_community.get_post(b_post["id"]) is None
    with _scope(tns.globex["id"]):
        assert [p["id"] for p in services_community.list_posts()] == [b_post["id"]]
        assert services_community.get_post(a_post["id"]) is None


def test_community_comment_counts_do_not_leak(fresh_db):
    tns = _Tenants()
    with _scope(tns.acme["id"]):
        a_post = _post(tns, tns.acme)
        for i in range(2):
            services_community.add_comment(
                tns.user(tns.acme, _unique_email("c")).id, a_post["id"],
                {"body": f"تعليق {i}"},
            )
    with _scope(tns.globex["id"]):
        b_post = _post(tns, tns.globex)
        services_community.add_comment(
            tns.user(tns.globex, _unique_email("c")).id, b_post["id"],
            {"body": "تعليق"},
        )
    with _scope(tns.acme["id"]):
        assert services_community.list_posts()[0]["comment_count"] == 2
        assert services_community.get_post(a_post["id"])["comment_count"] == 2
    with _scope(tns.globex["id"]):
        assert services_community.list_posts()[0]["comment_count"] == 1
        # تعليق مستأجر آخر على منشور أكسي مرفوض (المنشور خارج النطاق)
        with pytest.raises(CommunityError) as exc:
            services_community.add_comment(
                tns.user(tns.globex, _unique_email("x")).id, a_post["id"],
                {"body": "اختراق"},
            )
        assert exc.value.status_code == 404


def test_community_reactions_and_reports_isolated(fresh_db):
    tns = _Tenants()
    with _scope(tns.acme["id"]):
        a_post = _post(tns, tns.acme)
    with _scope(tns.globex["id"]):
        b_post = _post(tns, tns.globex)
    with _scope(tns.acme["id"]):
        # تفاعل مستأجر أكسي على منشور غلوبكس مرفوض
        with pytest.raises(CommunityError):
            services_community.toggle_reaction(
                tns.user(tns.acme, _unique_email("r")).id, b_post["id"])
        res = services_community.toggle_reaction(
            tns.user(tns.acme, _unique_email("r")).id, a_post["id"])
        assert res["reacted"] is True
        services_community.create_report(
            tns.user(tns.acme, _unique_email("rep")).id,
            {"target_type": "post", "target_id": a_post["id"], "reason": "سبب"},
        )
    with _scope(tns.globex["id"]):
        # إحصاءات التفاعلات تُحسب ضمن مستأجر الصف فقط
        assert services_community.get_post(b_post["id"])["reaction_count"] == 0
        assert services_community.list_posts()[0]["reaction_count"] == 0
        # بلاغ على منشور أكسي مرفوض
        with pytest.raises(CommunityError) as exc:
            services_community.create_report(
                tns.user(tns.globex, _unique_email("rep")).id,
                {"target_type": "post", "target_id": a_post["id"], "reason": "سبب"},
            )
        assert exc.value.status_code == 404
    with _scope(tns.acme["id"]):
        assert services_community.get_post(a_post["id"])["reaction_count"] == 1
    with db_session() as conn:
        rows = conn.execute("SELECT tenant_id FROM reports").fetchall()
        assert len(rows) == 1 and rows[0]["tenant_id"] == tns.acme["id"]


def test_community_post_counts_in_categories_scoped(fresh_db):
    tns = _Tenants()
    with _scope(tns.acme["id"]):
        _post(tns, tns.acme)
        _post(tns, tns.acme)
    with _scope(tns.globex["id"]):
        _post(tns, tns.globex)
    with _scope(tns.acme["id"]):
        by_count = {c["id"]: c["post_count"] for c in services_community.list_categories()}
        assert by_count[1] == 2
    with _scope(tns.globex["id"]):
        by_count = {c["id"]: c["post_count"] for c in services_community.list_categories()}
        assert by_count[1] == 1


# ---------------------------------------------------------------------------
# المحترفون (professional_profiles, professional_specialties, professional_reviews)
# ---------------------------------------------------------------------------

_PROFILE = {"profession_type": "lawyer", "city": "الرباط",
            "bio": "محامٍ", "specialties": ["جنائي"]}


def _verified_lawyer(tns, tenant):
    lawyer = tns.user(tenant, _unique_email("law"), "lawyer",
                      role_status="pending_verification")
    services_professionals.upsert_profile(lawyer.id, _PROFILE)
    services_admin.approve_verification(tns.admin(tenant).id, lawyer.id)
    return lawyer


def test_professionals_directory_isolated(fresh_db, _uploads):
    tns = _Tenants()
    with _scope(tns.acme["id"]):
        a_law = _verified_lawyer(tns, tns.acme)
        a_profile = services_professionals.get_profile_for_user(a_law.id)
    with _scope(tns.globex["id"]):
        b_law = _verified_lawyer(tns, tns.globex)
        b_profile = services_professionals.get_profile_for_user(b_law.id)
    with _scope(tns.acme["id"]):
        ids = [p["id"] for p in services_professionals.list_professionals()]
        assert ids == [a_profile["id"]]
        assert services_professionals.get_profile_public(a_profile["id"]) is not None
    with _scope(tns.globex["id"]):
        assert [p["id"] for p in services_professionals.list_professionals()] \
            == [b_profile["id"]]


def test_professionals_reviews_isolated(fresh_db, _uploads):
    tns = _Tenants()
    with _scope(tns.acme["id"]):
        a_law = _verified_lawyer(tns, tns.acme)
        a_profile = services_professionals.get_profile_for_user(a_law.id)
        services_professionals.add_review(
            tns.user(tns.acme, _unique_email("rv")).id, a_profile["id"], 5, "ممتاز")
    with _scope(tns.globex["id"]):
        b_law = _verified_lawyer(tns, tns.globex)
        b_profile = services_professionals.get_profile_for_user(b_law.id)
        services_professionals.add_review(
            tns.user(tns.globex, _unique_email("rv")).id, b_profile["id"], 1, "ضعيف")
    with _scope(tns.acme["id"]):
        pub = services_professionals.get_profile_public(a_profile["id"])
        assert pub["review_count"] == 1
        # متوسط تقييم لا يشمل مراجعة غلوبكس
        assert pub["rating"] == 5.0
        assert services_professionals.get_profile_public(b_profile["id"]) is None
    with _scope(tns.globex["id"]):
        pub = services_professionals.get_profile_public(b_profile["id"])
        assert pub["review_count"] == 1 and pub["rating"] == 1.0
        # مراجعة عبر المستأجر مرفوضة (الملف خارج النطاق)
        with pytest.raises(Exception) as exc:
            services_professionals.add_review(
                tns.user(tns.globex, _unique_email("rv")).id,
                a_profile["id"], 3, "خارج النطاق")
        assert getattr(exc.value, "status_code", 400) in (400, 404)


# ---------------------------------------------------------------------------
# السوق (marketplace_categories, marketplace_templates, purchases)
# ---------------------------------------------------------------------------

class _FakeFile:
    def __init__(self, content=b"%PDF-1.4", name="t.pdf"):
        self.content = content
        self.filename = name

    def read(self):
        return self.content


def _marketplace_category(tns, tenant):
    return services_marketplace.create_category(
        tns.admin(tenant).id,
        {"slug": f"cat-{tenant['slug']}", "name": f"فئة {tenant['slug']}"},
    )


def test_marketplace_isolated(fresh_db, _uploads):
    tns = _Tenants()
    with _scope(tns.acme["id"]):
        a_cat = _marketplace_category(tns, tns.acme)
        a_admin = tns.admin(tns.acme)
        a_tpl = services_marketplace.create_template(
            a_admin.id,
            {"category_id": a_cat, "title": "قالب أكسي",
             "description": "وصف", "price_cents": 100},
            _FakeFile(),
        )
    with _scope(tns.globex["id"]):
        b_cat = _marketplace_category(tns, tns.globex)
        b_admin = tns.admin(tns.globex)
        b_tpl = services_marketplace.create_template(
            b_admin.id,
            {"category_id": b_cat, "title": "قالب غلوبكس",
             "description": "وصف", "price_cents": 200},
            _FakeFile(),
        )
    with _scope(tns.acme["id"]):
        assert [c["slug"] for c in services_marketplace.list_categories()] \
            == ["cat-acme"]
        assert [t["title"] for t in services_marketplace.list_templates()] \
            == ["قالب أكسي"]
        assert services_marketplace.get_template(b_tpl["id"]) is None
        assert services_marketplace.list_templates_admin()[0]["id"] == a_tpl["id"]
    with _scope(tns.globex["id"]):
        assert [t["title"] for t in services_marketplace.list_templates()] \
            == ["قالب غلوبكس"]
        assert services_marketplace.get_template(a_tpl["id"]) is None
        with pytest.raises(MarketplaceError) as exc:
            services_marketplace.update_template(b_admin.id, a_tpl["id"],
                                                 {"title": "اختراق"}, None)
        assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# الإعلانات (ad_campaigns, ad_events)
# ---------------------------------------------------------------------------

def _campaign(tns, tenant):
    return services_ads.create_campaign(tns.admin(tenant).id, {
        "slot_id": 1,
        "campaign_type": "general",
        "advertiser_name": f"معلن {tenant['slug']}",
        "creative_url": f"https://ads.example.com/{tenant['slug']}.png",
        "target_url": "https://example.com/",
    })


def test_ads_campaigns_isolated(fresh_db):
    tns = _Tenants()
    with _scope(tns.acme["id"]):
        a_cid = _campaign(tns, tns.acme)
    with _scope(tns.globex["id"]):
        b_cid = _campaign(tns, tns.globex)
    with _scope(tns.acme["id"]):
        served = services_ads.serve("library_sidebar")
        assert served["campaign_id"] == a_cid
        assert services_ads.list_campaigns_admin()[0]["id"] == a_cid
        services_ads.log_event(a_cid, "impression")
    with _scope(tns.globex["id"]):
        served = services_ads.serve("library_sidebar")
        assert served["campaign_id"] == b_cid
        assert services_ads.list_campaigns_admin()[0]["id"] == b_cid
        # حدث على حملة مستأجر آخر مرفوض
        with pytest.raises(AdError) as exc:
            services_ads.log_event(a_cid, "impression")
        assert exc.value.status_code == 404
    with db_session() as conn:
        events = conn.execute(
            "SELECT campaign_id, tenant_id FROM ad_events ORDER BY id"
        ).fetchall()
        assert len(events) == 1
        assert events[0]["campaign_id"] == a_cid
        assert events[0]["tenant_id"] == tns.acme["id"]


def test_ads_list_slots_counts_scoped(fresh_db):
    tns = _Tenants()
    with _scope(tns.acme["id"]):
        _campaign(tns, tns.acme)
        _campaign(tns, tns.acme)
    with _scope(tns.globex["id"]):
        _campaign(tns, tns.globex)
    with _scope(tns.acme["id"]):
        assert services_ads.list_slots()[0]["active_campaigns"] == 2
    with _scope(tns.globex["id"]):
        assert services_ads.list_slots()[0]["active_campaigns"] == 1


# ---------------------------------------------------------------------------
# التحليلات (تجميعات مُقيَّدة بمستأجر الطلب)
# ---------------------------------------------------------------------------

def test_analytics_summary_scoped(fresh_db):
    tns = _Tenants()
    with _scope(tns.acme["id"]):
        _post(tns, tns.acme)
        _post(tns, tns.acme)
        _post(tns, tns.acme)
    with _scope(tns.globex["id"]):
        _post(tns, tns.globex)
    with _scope(tns.acme["id"]):
        summary = services_analytics.summary()
        assert summary["community"]["posts"] == 3
    with _scope(tns.globex["id"]):
        summary = services_analytics.summary()
        assert summary["community"]["posts"] == 1


# ---------------------------------------------------------------------------
# القانون المقارن (المرحلة 20 — D-038): ولايات/دراسات/مقارنات معزولة
# ---------------------------------------------------------------------------

def test_comparative_studies_isolated(fresh_db):
    tns = _Tenants()
    owner_a = tns.user(tns.acme, _unique_email("cmpa"), "citizen")
    with _scope(tns.acme["id"]):
        admin_a = tns.admin(tns.acme)
        services_comparative.create_jurisdiction(
            admin_a.id, {"slug": "acme-land", "name": "ولاية أكسي"}
        )
        a_study = services_comparative.create_study(
            owner_a.id, {"title": "دراسة المستأجر أ"}
        )
    owner_g = tns.user(tns.globex, _unique_email("cmpg"), "citizen")
    with _scope(tns.globex["id"]):
        admin_g = tns.admin(tns.globex)
        services_comparative.create_jurisdiction(
            admin_g.id, {"slug": "globex-land", "name": "ولاية غلوبكس"}
        )
        g_study = services_comparative.create_study(
            owner_g.id, {"title": "دراسة المستأجر ب"}
        )
    # كل مستأجر يرى دراسته وولاياته فقط (على مستوى الخدمة والتفاصيل)
    with _scope(tns.acme["id"]):
        studies = services_comparative.list_studies_admin()
        assert [s["id"] for s in studies] == [a_study["id"]]
        assert services_comparative.get_study(g_study["id"]) is None
        assert [j["slug"] for j in services_comparative.list_jurisdictions()] \
            == ["acme-land"]
    with _scope(tns.globex["id"]):
        assert services_comparative.get_study(a_study["id"]) is None
        assert [j["slug"] for j in services_comparative.list_jurisdictions()] \
            == ["globex-land"]


def test_comparative_cross_tenant_entries_hidden(fresh_db):
    tns = _Tenants()
    owner_a = tns.user(tns.acme, _unique_email("cmpa2"), "citizen")
    with db_session() as conn:
        # مادة في نطاق المستأجر (للإسناد)
        cat = conn.execute(
            "INSERT INTO categories (slug, name, tenant_id) VALUES (?,?,?)",
            ("acme-cmp-cat", "فئة", tns.acme["id"]),
        ).lastrowid
        lt = conn.execute(
            "INSERT INTO legal_texts (category_id, type, title, tenant_id) "
            "VALUES (?,?,?,?)",
            (cat, "code", "نص أكسي", tns.acme["id"]),
        ).lastrowid
        aid = conn.execute(
            "INSERT INTO articles (legal_text_id, number, label, content, "
            "tenant_id) VALUES (?,?,?,?,?)",
            (lt, "1", "المادة 1", "محتوى", tns.acme["id"]),
        ).lastrowid
    with _scope(tns.acme["id"]):
        admin_a = tns.admin(tns.acme)
        services_comparative.create_jurisdiction(
            admin_a.id, {"slug": "acme-land", "name": "ولاية أكسي"}
        )
        a_study = services_comparative.create_study(
            owner_a.id, {"title": "دراسة أكسي"}
        )
        jid = services_comparative.list_jurisdictions()[0]["id"]
        services_comparative.add_entry(
            owner_a.id, a_study["id"],
            {"jurisdiction_id": jid, "article_id": aid, "note": "مقارنة أكسي"},
        )
    # مستأجر آخر لا يرى مقارنات الدراسة ولا يستطيع تعديلها
    with _scope(tns.globex["id"]):
        assert services_comparative.get_study(a_study["id"]) is None
    # تعديل مقارنة أكسي عبر نطاق غلوبكس مرفوض (المقارنة غير موجودة في نطاقه)
    owner_g = tns.user(tns.globex, _unique_email("cmpg2"), "citizen")
    with _scope(tns.globex["id"]), pytest.raises(ComparativeError):
        services_comparative.update_entry(owner_g.id, 1, {"note": "مقتحم"})
