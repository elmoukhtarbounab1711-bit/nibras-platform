"""
اختبارات صفحات SEO عبر تقديم الخادم (SSR) — مرحلة الروابط الحقيقية.

تتحقق من أن/:
  * مسارات /laws/<id>, /jurisprudence/<id>, /procedures/<slug> وقوائمها
    تُقدم HTML كاملًا من الخادم (title، description، canonical بلا hash،
    H1، محتوى حقيقي داخل #view، بيانات مهيكلة صالحة + BreadcrumbList).
  * الروابط الداخلية في الصفحة روابط حقيقية (ليست #).
  * خريطة الموقع index + المقسمات صالحة XML وتشمل الكيانات.
  * /robots.txt يمنع المنطقة الخاصة ويشير لخريطة الموقع.
  * المعرف غير الموجود يعيد 404 حقيقي (لا soft-404 بغلاف SPA)
    مع <meta name='robots' content='noindex'> حتى لا تفهرس محركات البحث صفحات فارغة.
"""
import json
import re
from urllib.parse import urlparse

import pytest


@pytest.fixture()
def ids(fresh_db):
    """معرّف نص واجتهاد من بيانات الاختبار النموذجية (قراءة مباشرة من DB)."""
    from app.database import db_session
    with db_session() as conn:
        law_id = conn.execute(
            "SELECT id FROM legal_texts WHERE is_sample_data=1 LIMIT 1"
        ).fetchone()[0]
        dec_id = conn.execute(
            "SELECT id FROM jurisprudence WHERE published=1 LIMIT 1"
        ).fetchone()[0]
    assert law_id and dec_id, "بيانات الاختبار لا تحتوي نصوصًا/اجتهادات"
    return law_id, dec_id


def _ld_blocks(html):
    return re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)


def _ld_objects(html):
    """يجمع كائنات JSON-LD من كل البلوكات (كل بلوك قد يكون مصفوفة)."""
    out = []
    for blk in _ld_blocks(html):
        data = json.loads(blk)
        items = data if isinstance(data, list) else [data]
        out.extend(o for o in items if isinstance(o, dict))
    return out


def _assert_ssr_html(html, expect_path):
    assert "<html" in html
    title = re.search(r"<title>(.*?)</title>", html, re.DOTALL)
    assert title and title.group(1).strip(), "title فارغ"
    canon = re.search(r'rel="canonical" href="([^"]+)"', html)
    assert canon, "لا يوجد canonical"
    assert "#" not in canon.group(1), "canonical يحتوي hash"
    assert urlparse(canon.group(1)).path.rstrip("/") == urlparse(expect_path).path.rstrip("/"), \
        f"canonical {canon.group(1)} لا يطابق {expect_path}"
    assert re.search(r"<h1>", html), "لا يوجد H1"
    assert 'id="view"' in html, "لا يوجد غلاف #view"
    # لا يترك skeleton فارغًا: يجب أن يكون المحتوى الحقيقي داخل #view
    view_match = re.search(r'id="view"[^>]*>(.*?)</main>', html, re.DOTALL)
    assert view_match and view_match.group(1).strip(), "محتوى #view فارغ (لم يُقدَّم SSR فعليًا)"
    # بيانات مهيكلة صالحة
    for blk in _ld_blocks(html):
        data = json.loads(blk)
        arr = data if isinstance(data, list) else [data]
        assert all(isinstance(o, dict) for o in arr)


@pytest.mark.parametrize("endpoint,label", [
    ("/laws", "laws"),
    ("/jurisprudence", "juris"),
    ("/procedures", "proc"),
])
def test_seo_list_pages_ssr(client, endpoint, label):
    r = client.get(endpoint)
    assert r.status_code == 200
    assert "text/html" in r.content_type
    _assert_ssr_html(r.get_data(as_text=True), endpoint)


def test_seo_law_page_ssr(client, ids):
    law_id, _ = ids
    r = client.get(f"/laws/{law_id}")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    _assert_ssr_html(html, f"/laws/{law_id}")
    # الروابط الداخلية حقيقية (بلا hash) — على الأقل رابط قائمة المكتبة في Breadcrumb
    assert 'href="/laws"' in html, "لا يوجد رابط حقيقي لمسار /laws في الصفحة"
    assert "#/laws" not in html and "//#/laws" not in html


def test_seo_jurisprudence_page_ssr(client, ids):
    _, dec_id = ids
    r = client.get(f"/jurisprudence/{dec_id}")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    _assert_ssr_html(html, f"/jurisprudence/{dec_id}")
    assert "مبدأ" in html or "اجتهاد" in html, "لا يوجد محتوى اجتهاد فعلي في الصفحة"


def test_seo_procedure_detail_ssr(client, fresh_db):
    from app.database import db_session
    with db_session() as conn:
        row = conn.execute("SELECT slug FROM procedures LIMIT 1").fetchone()
    if not row:
        pytest.skip("لا توجد مساطر في بيانات الاختبار")
    slug = row["slug"]
    r = client.get(f"/procedures/{slug}")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    _assert_ssr_html(html, f"/procedures/{slug}")
    assert len(re.findall(r"<h1>", html)) == 1, "يجب أن يكون هناك H1 واحد فقط"


def test_seo_defaults_without_hash(client, ids):
    law_id, _ = ids
    html = client.get(f"/laws/{law_id}").get_data(as_text=True)
    assert "#/laws" not in html and "//#/laws" not in html
    canon = re.search(r'rel="canonical" href="([^"]+)"', html)
    assert canon and "#" not in canon.group(1)


def test_seo_sitemap_index_and_splits(client, ids):
    _, dec_id = ids
    idx = client.get("/sitemap.xml")
    assert idx.status_code == 200
    assert idx.content_type.startswith("application/xml")
    body = idx.get_data(as_text=True)
    assert "<sitemapindex" in body
    for name in ("laws.xml", "jurisprudence.xml", "procedures.xml", "blog.xml"):
        assert "/sitemaps/" + name in body

    j = client.get("/sitemaps/jurisprudence.xml")
    assert j.status_code == 200 and f"/jurisprudence/{dec_id}" in j.get_data(as_text=True)


def test_seo_robots_txt(client):
    r = client.get("/robots.txt")
    assert r.status_code == 200
    text = r.get_data(as_text=True)
    assert "Sitemap:" in text
    for disallow in ("/dashboard", "/admin", "/account", "/api/"):
        assert "Disallow: " + disallow in text, f"robots.txt لا يمنع {disallow}"


def test_seo_domain_page_ssr(client, fresh_db):
    from app.database import db_session
    with db_session() as conn:
        has_domains = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='legal_domains'"
        ).fetchone()
    if not has_domains:
        pytest.skip("قاعدة بيانات الاختبار لا تحتوي جدول legal_domains")
    with db_session() as conn:
        row = conn.execute("SELECT slug FROM legal_domains LIMIT 1").fetchone()
    if not row:
        pytest.skip("لا توجد نطاقات قانونية في بيانات الاختبار")
    slug = row["slug"]
    r = client.get(f"/domains/{slug}")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    _assert_ssr_html(html, f"/domains/{slug}")
    assert len(re.findall(r"<h1>", html)) == 1, "يجب أن يكون هناك H1 واحد فقط"


@pytest.mark.parametrize("url", [
    "/laws/999999999",
    "/jurisprudence/999999999",
    "/procedures/missing-slug-xyz",
    "/domains/missing-domain-xyz",
    "/laws/abc",
])
def test_seo_missing_returns_real_404(client, url):
    r = client.get(url)
    assert r.status_code == 404, f"{url} يجب أن يعيد 404 (لا soft-404): {r.status_code}"
    html = r.get_data(as_text=True)
    assert "text/html" in r.content_type
    assert "robots" in html and "noindex" in html, "صفحة 404 يجب أن تكون noindex"
    assert "<h1>" in html, "صفحة 404 يجب أن تحتوي عنوانًا"


def test_seo_home_canonical_redirect(client):
    r = client.get("/home")
    assert r.status_code == 301, f"/home يجب أن يحوّل 301 إلى الجذر: {r.status_code}"
    assert r.headers.get("Location", "").rstrip("/") == "/home".replace("/home", "") or \
        r.headers.get("Location", "").endswith("/")

def test_seo_index_serves_real_links(client):
    r = client.get("/")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert 'href="/library"' in html, "الواجهة الثابتة يجب أن تحمل روابط حقيقية"
    assert 'href="/about"' in html
    assert 'href="/generator"' in html
    assert 'href="#/' not in html, "الواجهة الثابتة يجب ألا تحمل روابط hash فعلية"


def test_seo_sitemaps_have_lastmod(client, fresh_db):
    from app.database import db_session
    with db_session() as conn:
        law = conn.execute("SELECT id FROM legal_texts LIMIT 1").fetchone()
        dec = conn.execute("SELECT id FROM jurisprudence WHERE published=1 LIMIT 1").fetchone()
    if law:
        body = client.get("/sitemaps/laws.xml").get_data(as_text=True)
        assert f"/laws/{law[0]}" in body
        assert re.search(r"<lastmod>\d{4}-\d{2}-\d{2}</lastmod>", body), \
            "sitemap القوانين يجب أن يحوي lastmod"
    if dec:
        body = client.get("/sitemaps/jurisprudence.xml").get_data(as_text=True)
        assert f"/jurisprudence/{dec[0]}" in body
        assert re.search(r"<lastmod>\d{4}-\d{2}-\d{2}</lastmod>", body), \
            "sitemap الاجتهادات يجب أن يحوي lastmod"
    main = client.get("/sitemaps/main.xml").get_data(as_text=True)
    assert re.search(r"<lastmod>\d{4}-\d{2}-\d{2}</lastmod>", main), \
        "sitemap الرئيسي يجب أن يحوي lastmod بتاريخ اليوم"


@pytest.fixture()
def blog_post(fresh_db):
    """ينشئ مقالة مدوّنة منشورة في قاعدة الاختبار المعزولة ويعيد معرّفها."""
    from app.database import db_session

    with db_session() as conn:
        author_id = conn.execute(
            """INSERT INTO users (email, full_name, password_hash, status, tenant_id,
                                  consent_data_processing, consent_terms)
               VALUES (?, ?, ?, 'active', NULL, 1, 1)""",
            ("blog@seo.test", "كاتب تجريبي", "seed-only-hash-not-for-login"),
        ).lastrowid
        madani = conn.execute(
            "SELECT id FROM blog_categories WHERE slug='madani'"
        ).fetchone()
        if not madani:
            pytest.skip("فئة المدونة madani غير متاحة في بيانات الاختبار")
        article_id = conn.execute(
            """INSERT INTO blog_articles
               (user_id, category_id, title, summary, body, keywords, status,
                published_at, created_at)
               VALUES (?, ?, ?, ?, ?, ?, 'published', datetime('now'), datetime('now'))""",
            (author_id, madani[0],
             "شرح المادة 230 من قانون الالتزامات والعقود",
             "شرح مبسط لمبدأ العقد شريعة المتعاقدين.",
             "المادة 230 من قانون الالتزامات والعقود تقر أن العقد شريعة المتعاقدين.",
             "عقد,التزامات,قانون مدني"),
        ).lastrowid
    return article_id


def test_seo_blog_list_ssr(client, blog_post):
    r = client.get("/blog")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    _assert_ssr_html(html, "/blog")
    assert "المدونة" in html or "مدوّنة" in html, "صفحة المدونة يجب أن تذكر المدونة"
    assert len(re.findall(r"<h1>", html)) == 1, "يجب أن يكون هناك H1 واحد فقط"
    assert f"/blog/{blog_post}" in html, "قائمة المدونة يجب أن تدرج المقال المنشور"


def test_seo_blog_article_ssr(client, blog_post):
    article_id = blog_post
    r = client.get(f"/blog/{article_id}")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    _assert_ssr_html(html, f"/blog/{article_id}")
    assert len(re.findall(r"<h1>", html)) == 1, "يجب أن يكون هناك H1 واحد فقط"
    blogs = [o for o in _ld_objects(html) if o.get("@type") == "BlogPosting"]
    assert blogs, "لا توجد بيانات مهيكلة BlogPosting في صفحة المقال"
    assert "headline" in blogs[0], "BlogPosting يجب أن يحوي headline"
    assert "الالتزامات والعقود" in html, "الصفحة يجب أن تعرض محتوى المقال"


def test_seo_blog_sitemap(client, blog_post):
    idx = client.get("/sitemap.xml")
    assert idx.status_code == 200
    idx_body = idx.get_data(as_text=True)
    assert "/sitemaps/blog.xml" in idx_body, "فهرس الخرائط يجب أن يشمل blog.xml"
    body = client.get("/sitemaps/blog.xml")
    assert body.status_code == 200
    xml = body.get_data(as_text=True)
    assert "<urlset" in xml and "<loc>" in xml
    assert f"/blog/{blog_post}" in xml, "blog.xml يجب أن يتضمن المقالات المنشورة"


def test_seo_blog_missing_returns_real_404(client):
    r = client.get("/blog/999999999")
    assert r.status_code == 404
    html = r.get_data(as_text=True)
    assert "text/html" in r.content_type
    assert "robots" in html and "noindex" in html
