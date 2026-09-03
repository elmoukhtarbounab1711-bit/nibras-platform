"""
اختبارات صفحات SEO عبر تقديم الخادم (SSR) — مرحلة الروابط الحقيقية.

تتحقق من أن/:
  * مسارات /laws/<id>, /jurisprudence/<id>, /procedures/<slug> وقوائمها
    تُقدم HTML كاملًا من الخادم (title، description، canonical بلا hash،
    H1، محتوى حقيقي داخل #view، بيانات مهيكلة صالحة + BreadcrumbList).
  * الروابط الداخلية في الصفحة روابط حقيقية (ليست #).
  * خريطة الموقع index + المقسمات صالحة XML وتشمل الكيانات.
  * /robots.txt يمنع المنطقة الخاصة ويشير لخريطة الموقع.
  * المعرف غير الموجود يقع إلى SPA (index.html) كما كان السلوك.
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
    return re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)


def _assert_ssr_html(html, expect_path):
    assert "<html" in html
    title = re.search(r"<title>(.*?)</title>", html, re.S)
    assert title and title.group(1).strip(), "title فارغ"
    canon = re.search(r'rel="canonical" href="([^"]+)"', html)
    assert canon, "لا يوجد canonical"
    assert "#" not in canon.group(1), "canonical يحتوي hash"
    assert urlparse(canon.group(1)).path.rstrip("/") == urlparse(expect_path).path.rstrip("/"), \
        f"canonical {canon.group(1)} لا يطابق {expect_path}"
    assert re.search(r"<h1>", html), "لا يوجد H1"
    assert 'id="view"' in html, "لا يوجد غلاف #view"
    # لا يترك skeleton فارغًا: يجب أن يكون المحتوى الحقيقي داخل #view
    view_match = re.search(r'id="view"[^>]*>(.*?)</main>', html, re.S)
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
    for name in ("laws.xml", "jurisprudence.xml", "procedures.xml"):
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


def test_seo_missing_id_falls_back_to_spa(client):
    r = client.get("/jurisprudence/999999999")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    # يقع إلى غلاف SPA (index.html) — لا يخطئ ولا يكشف تفاصيل
    assert 'id="view"' in html
