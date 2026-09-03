"""
Server-Side Rendering (SSR) لصفحات SEO الحقيقية في نبراس.

يحوّل المسارات الحقيقية — /laws/<id>، /jurisprudence/<id>، /procedures/<slug>،
والقوائم/النطاقات ذات الصلة — إلى صفحات HTML كاملة تحتوي فعليًا على:
  * عنوان فريد (<title>) ووصف فريد وcanonical
  * Open Graph + Twitter Card
  * BreadcrumbList + JSON-LD مناسب لنوع الصفحة
  * H1 واحد ومحتوى HTML قابل للقراءة من طرف الـcrawler دون JavaScript

يُبقي على غلاف SPA نفسه (نفس الـ scripts في index.html) حتى يحتفظ المستخدم
بالتجربة الكاملة، بينما يحصل محرك البحث على HTML غني بالمحتوى أولًا.

كل البيانات مستخرجة فعلًا من قاعدة البيانات — لا تُختلق أي بيانات قانونية.
"""
import html as _html
import re
from pathlib import Path

from . import config
from .database import db_session

SITE = "https://nibras-law-platforme.vercel.app"
_TEMPLATE = None

# ---------------------------------------------------------------------------
# ملاحظة التطبيع: نستخرج فقط الحقول الموجودة فعلًا في قاعدة البيانات.
# قانون (legal_texts): title, type, official_ref, source_url + PDF.
# اجتهاد (jurisprudence): title, principles, content, court, decision_number,
#   decision_date, category.
# مسطرة (procedures): title, description, responsible_authority, typical_timeframe,
#   fees, faq + steps.
# ---------------------------------------------------------------------------


def _template():
    global _TEMPLATE
    if _TEMPLATE is None:
        p = Path(config.FRONTEND_DIR) / "index.html"
        if p.exists():
            _TEMPLATE = p.read_text(encoding="utf-8")
        else:
            _TEMPLATE = "<!DOCTYPE html><html lang='ar' dir='rtl'><head><title>نبراس</title></head><body><main id='view'></main></body></html>"
    return _TEMPLATE


def _slugify(name: str) -> str:
    """تحويل اسم عربي/فرنسي إلى slug بسيط من الحروف اللاتينية (علني فقط)."""
    s = re.sub(r"[^a-zA-Z0-9]+", "-", str(name or "").strip().lower())
    return s.strip("-") or "page"


def _esc(v) -> str:
    return _html.escape(str(v or ""))


def _art_label(text: str, limit: int = 130) -> str:
    s = str(text or "").strip()
    if not s:
        return ""
    if len(s) > limit:
        return s[: limit - 1].rstrip() + "…"
    return s


BREADCRUMB_SCHEMA = "application/ld+json"


def _inject(title, description, path, content_html, jsonld_blocks=(), schema_type="WebPage"):
    """يبني كامل HTML من قالب SPA مع حقن العنوان والوصف وcanonical والمحتوى."""
    tpl = _template()
    clean_path = path.split("?")[0]
    if clean_path == "/home":
        clean_path = "/"
    canonical = SITE + clean_path

    # عنوان/وصف
    tpl = re.sub(r"<title>.*?</title>", _esc(title) and f"<title>{_esc(title)}</title>", tpl, count=1, flags=re.S)

    # إزالة وسوم meta السابقة التي قد تتعارض (وصف/OG/Twitter/canonical)
    tpl = re.sub(r'<meta\s+name="description"[^>]*>', "", tpl, flags=re.I)
    tpl = re.sub(r'<meta\s+property="og:[^"]*"[^>]*>', "", tpl, flags=re.I)
    tpl = re.sub(r'<meta\s+name="twitter:[^"]*"[^>]*>', "", tpl, flags=re.I)
    tpl = re.sub(r'<link\s+rel="canonical"[^>]*>', "", tpl, flags=re.I)

    head_block = f"""
<meta name="description" content="{_esc(description)}">
<link rel="canonical" href="{_esc(canonical)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="نبراس">
<meta property="og:title" content="{_esc(title)}">
<meta property="og:description" content="{_esc(description)}">
<meta property="og:url" content="{_esc(canonical)}">
<meta property="og:image" content="{SITE}/assets/img/og-cover.png">
<meta property="og:image:alt" content="نبراس — منصة القانون المغربي">
<meta property="og:locale" content="ar_MA">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{_esc(title)}">
<meta name="twitter:description" content="{_esc(description)}">
<meta name="twitter:image" content="{SITE}/assets/img/og-cover.png">
"""

    blocks = []
    blocks.append({
        "@context": "https://schema.org",
        "@type": schema_type,
        "name": title,
        "url": canonical,
        "description": description,
        "inLanguage": "ar",
        "isPartOf": {"@type": "WebSite", "url": SITE, "name": "نبراس"},
        "breadcrumb": {"@type": "BreadcrumbList", "itemListElement": []},
    })
    blocks.extend(jsonld_blocks)
    ld = "[\n" + ",\n".join(_json(blocks)) + "\n]"
    head_block += f'\n<script type="application/ld+json">{ld}</script>\n'

    tpl = tpl.replace("</head>", head_block + "</head>", 1)

    # حقن المحتوى داخل #view (إن وُجد)
    if re.search(r'<main[^>]*id="view"[^>]*>\s*</main>', tpl):
        tpl = re.sub(
            r'(<main[^>]*id="view"[^>]*>\s*)</main>',
            lambda m: m.group(1) + content_html + "</main>",
            tpl,
            count=1,
            flags=re.S,
        )
    elif "id=\"view\"" in tpl:
        tpl = re.sub(
            r'(id="view"[^>]*>)(.*?)(</main>)',
            lambda m: m.group(1) + content_html + m.group(3),
            tpl,
            count=1,
            flags=re.S,
        )
    return tpl


def _json(obj):
    """تسلسل JSON آمن داخل script (يمنع كسر الوسم ولا يستخدم HTML entities)."""
    import json
    out = []
    for o in obj:
        s = json.dumps(o, ensure_ascii=False)
        s = s.replace("</", "<\\/")
        out.append(s)
    return out


def _crumb(path, name):
    return {"@type": "ListItem", "position": path.count("/") + 1, "name": name,
            "item": SITE + (path if path != "/" else "/")}


def _breadcrumb_html(crumbs):
    items = []
    for label, href in crumbs:
        if href:
            items.append(f'<li><a href="{_esc(href)}">{_esc(label)}</a></li>')
        else:
            items.append(f'<li aria-current="page">{_esc(label)}</li>')
    return f'<nav aria-label="Breadcrumb" class="seo-breadcrumb"><ol>{ "".join(items) }</ol></nav>'


# ---------------------------------------------------------------------------
# استعلامات البيانات (بلا آثار جانبية)
# ---------------------------------------------------------------------------

def _has_table(conn, name):
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone() is not None


def _get_law(law_id):
    with db_session() as conn:
        has_domains = _has_table(conn, "legal_domains")
        if has_domains:
            row = conn.execute(
                "SELECT lt.*, c.name AS category_name, d.name_ar AS domain_name, "
                "d.slug AS domain_slug "
                "FROM legal_texts lt "
                "LEFT JOIN categories c ON c.id = lt.category_id "
                "LEFT JOIN legal_domains d ON d.id = lt.domain_id "
                "WHERE lt.id = ?", (law_id,)
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT lt.*, c.name AS category_name, NULL AS domain_name, NULL AS domain_slug "
                "FROM legal_texts lt LEFT JOIN categories c ON c.id = lt.category_id "
                "WHERE lt.id = ?", (law_id,)
            ).fetchone()
        if not row:
            return None
        law = dict(row)
        # قوانين ذات صلة (نفس الفئة والنطاق)
        related = conn.execute(
            "SELECT id, title FROM legal_texts WHERE category_id=? AND id<>? "
            "ORDER BY title LIMIT 8", (law.get("category_id"), law_id)
        ).fetchall()
        law["_related"] = [dict(r) for r in related]
        return law


def _get_decision(decision_id):
    with db_session() as conn:
        row = conn.execute(
            "SELECT j.*, c.name AS category_name, c.slug AS category_slug "
            "FROM jurisprudence j LEFT JOIN jurisprudence_categories c ON c.id=j.category_id "
            "WHERE j.id=? AND j.published=1", (decision_id,)
        ).fetchone()
        return dict(row) if row else None


def _get_procedure(slug):
    with db_session() as conn:
        row = conn.execute("SELECT * FROM procedures WHERE slug=?", (slug,)).fetchone()
        if not row:
            return None
        p = dict(row)
        p["_steps"] = [dict(r) for r in conn.execute(
            "SELECT step_number, title, description, required_documents "
            "FROM procedure_steps WHERE procedure_id=? ORDER BY step_number",
            (p["id"],)).fetchall()]
        return p


def _type_label(t):
    return {
        "law": "قانون", "decree": "مرسوم", "dahir": "ظهير", "decision": "قرار",
        "constitution": "دستور", "code": "مدونة", "agreement": "اتفاقية", "circular": "منشور",
    }.get(t, t)


# ---------------------------------------------------------------------------
# مكوّنات الصفحات
# ---------------------------------------------------------------------------

def _law_page(law_id):
    law = _get_law(law_id)
    if not law:
        return None, None, None
    title = law.get("title") or "نص قانوني"
    cat = law.get("category_name")
    dom = law.get("domain_name")
    type_label = _type_label(law.get("type"))
    desc = f"{_art_label(title, 90)} — {type_label} من أرشيف مكتبة نبراس القانونية المغربية."
    if dom:
        desc += f" ضمن مجال {dom}."

    crumbs = [("الرئيسية", "/"), ("المكتبة", "/laws"), (cat or "المواد", None)]
    bc_html = _breadcrumb_html(crumbs)
    ld_bc = [{
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "الرئيسية", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "المكتبة", "item": SITE + "/laws"},
            {"@type": "ListItem", "position": 3, "name": title, "item": SITE + f"/laws/{law_id}"},
        ],
    }]

    bits = [bc_html,
        f'<p class="seo-kicker">{_esc(type_label)}</p>',
        f"<h1>{_esc(title)}</h1>",
        '<div class="seo-meta">']
    if law.get("official_ref"):
        bits.append(f'<span class="seo-badge">{_esc(law["official_ref"])}</span>')
    if cat:
        bits.append(f'<span class="seo-badge">{_esc(cat)}</span>')
    if dom:
        bits.append(f'<span class="seo-badge">{_esc(dom)}</span>')
    bits.append("</div>")
    if law.get("source_url") or law.get("uploaded_pdf_key"):
        bits.append(f'<p class="seo-doc"><a href="{_esc(law["source_url"] or f"/api/texts/{law_id}/pdf")}" '
                    'target="_blank" rel="noopener">تحميل/عرض النص (PDF)</a></p>')

    related = law.get("_related") or []
    if related:
        bits.append('<h2>قوانين ذات صلة</h2><ul class="seo-links">')
        for r in related:
            bits.append(f'<li><a href="/laws/{r["id"]}">{_esc(r["title"])}</a></li>')
        bits.append("</ul>")

    content = "".join(bits)
    return content, title, {"description": desc, "path": f"/laws/{law_id}", "jsonld": ld_bc,
                            "crumb": crumbs, "type": "Article"}


def _juris_page(decision_id):
    d = _get_decision(decision_id)
    if not d:
        return None, None, None
    title = _art_label(d.get("title") or "اجتهاد قضائي", 80)
    court = d.get("court")
    num = d.get("decision_number")
    cat = d.get("category_name")
    desc = f"{title} — {court or 'محكمة'} رقم {num or ''}".strip() + " المبدأ والنص الكامل في اجتهادات نبراس المغربية."
    crumbs = [("الرئيسية", "/"), ("الاجتهادات", "/jurisprudence"),
              (cat or "الاجتهادات", None)]
    bc_html = _breadcrumb_html(crumbs)

    bits = [bc_html, f"<h1>{_esc(title)}</h1>",
            '<div class="seo-meta">']
    if court:
        bits.append(f'<span class="seo-badge">{_esc(court)}</span>')
    if num:
        bits.append(f'<span class="seo-badge">رقم {_esc(num)}</span>')
    if d.get("decision_date"):
        bits.append(f'<span class="seo-badge">{_esc(d["decision_date"])}</span>')
    if cat:
        bits.append(f'<a class="seo-badge" href="/jurisprudence?cat={_esc(d.get("category_slug") or "")}">{_esc(cat)}</a>')
    bits.append("</div>")
    if d.get("principles"):
        bits.append(f"<h2>مبدأ الحكم</h2><p class='seo-text'>{_esc(d['principles'])}</p>")
    if d.get("content"):
        bits.append(f"<h2>نص الاجتهاد</h2><div class='seo-text'>{_esc(d['content'])}</div>")

    content = "".join(bits)
    ld_bc = [{
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "الرئيسية", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "الاجتهادات", "item": SITE + "/jurisprudence"},
            {"@type": "ListItem", "position": 3, "name": title, "item": SITE + f"/jurisprudence/{decision_id}"},
        ],
    }]
    return content, title, {"description": desc, "path": f"/jurisprudence/{decision_id}",
                            "jsonld": ld_bc, "type": "Article"}


def _procedure_page(slug):
    p = _get_procedure(slug)
    if not p:
        return None, None, None
    title = p.get("title") or "مسطرة"
    cat = p.get("category")
    desc = _art_label(f"{title} ({cat or 'إجراء'}): خطوات وإجراءات في نبراس.", 150)
    crumbs = [("الرئيسية", "/"), ("المساطر", "/procedures"), (title, None)]
    bc_html = _breadcrumb_html(crumbs)

    bits = [bc_html, f"<h1>{_esc(title)}</h1>", '<div class="seo-meta">']
    if cat:
        bits.append(f'<span class="seo-badge">{_esc(cat)}</span>')
    if p.get("responsible_authority"):
        bits.append(f'<span class="seo-badge">{_esc(p["responsible_authority"])}</span>')
    if p.get("typical_timeframe"):
        bits.append(f'<span class="seo-badge">الآجال: {_esc(p["typical_timeframe"])}</span>')
    bits.append("</div>")
    if p.get("fees"):
        bits.append(f"<h2>الرسوم</h2><p class='seo-text'>{_esc(p['fees'])}</p>")
    steps = p.get("_steps") or []
    if steps:
        bits.append("<h2>المراحل</h2><ol class='seo-steps'>")
        for s in steps:
            bits.append(f"<li><strong>{_esc(s.get('title') or '')}</strong>")
            if s.get("description"):
                bits.append(f" — {_esc(s['description'])}")
            if s.get("required_documents"):
                bits.append(f"<div class='seo-small'>الوثائق: {_esc(s['required_documents'])}</div>")
            bits.append("</li>")
        bits.append("</ol>")
    if p.get("faq"):
        bits.append(f"<h2>الأسئلة الشائعة</h2><p class='seo-text'>{_esc(p['faq'])}</p>")

    content = "".join(bits)
    ld_bc = [{
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "الرئيسية", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "المساطر", "item": SITE + "/procedures"},
            {"@type": "ListItem", "position": 3, "name": title, "item": SITE + f"/procedures/{slug}"},
        ],
    }]
    return content, title, {"description": desc, "path": f"/procedures/{slug}",
                            "jsonld": ld_bc, "type": "Article"}


def _list_laws():
    with db_session() as conn:
        rows = conn.execute(
            "SELECT lt.id, lt.title, lt.official_ref, c.name AS category_name "
            "FROM legal_texts lt LEFT JOIN categories c ON c.id=lt.category_id "
            "ORDER BY lt.title LIMIT 200").fetchall()
    bits = ['<nav aria-label="Breadcrumb" class="seo-breadcrumb"><ol>'
            '<li><a href="/">الرئيسية</a></li><li aria-current="page">المكتبة</li></ol></nav>',
            "<h1>المكتبة القانونية المغربية</h1>",
            "<p>مكتبة نصوص قانونية مغربية: قوانين وظهائر ومراسيم وقرارات.</p>",
            '<ul class="seo-links">']
    for r in rows:
        bits.append(f'<li><a href="/laws/{r["id"]}">{_esc(r["title"])}{" ("+_esc(r["official_ref"])+")" if r["official_ref"] else ""}</a></li>')
    bits.append("</ul>")
    return "".join(bits), "المكتبة القانونية المغربية", \
           {"description": "مكتبة نصوص قانونية مغربية قابلة للفهرسة: قوانين، ظهائر، مراسيم وقرارات مرتبة."}


def _list_jurisprudence():
    with db_session() as conn:
        rows = conn.execute(
            "SELECT j.id, j.title, j.court, c.name AS category_name "
            "FROM jurisprudence j LEFT JOIN jurisprudence_categories c ON c.id=j.category_id "
            "WHERE j.published=1 ORDER BY j.id DESC LIMIT 200").fetchall()
    bits = ['<nav aria-label="Breadcrumb" class="seo-breadcrumb"><ol>'
            '<li><a href="/">الرئيسية</a></li><li aria-current="page">الاجتهادات</li></ol></nav>',
            "<h1>الاجتهادات القضائية المغربية</h1>",
            "<p>قرارات ومبادئ قضائية من المحاكم المغربية.</p>",
            '<ul class="seo-links">']
    for r in rows:
        bits.append(f'<li><a href="/jurisprudence/{r["id"]}">{_esc(_art_label(r["title"],110))}</a></li>')
    bits.append("</ul>")
    return "".join(bits), "الاجتهادات القضائية المغربية", \
           {"description": "اجتهادات قضائية مغربية بمبادئها ونصوصها الكاملة."}


def _list_procedures():
    with db_session() as conn:
        rows = conn.execute(
            "SELECT p.slug, p.title, p.category, c.name AS category_name "
            "FROM procedures p LEFT JOIN jurisprudence_categories c ON 1=0 "
            "ORDER BY p.title").fetchall()
    bits = ['<nav aria-label="Breadcrumb" class="seo-breadcrumb"><ol>'
            '<li><a href="/">الرئيسية</a></li><li aria-current="page">المساطر</li></ol></nav>',
            "<h1>المساطر والإجراءات</h1>",
            "<p>دليل عملي خطوة بخطوة للمساطر الإدارية والقانونية في المغرب.</p>",
            '<ul class="seo-links">']
    for r in rows:
        bits.append(f'<li><a href="/procedures/{r["slug"]}">{_esc(r["title"])}{" ("+_esc(r["category"])+")" if r["category"] else ""}</a></li>')
    bits.append("</ul>")
    return "".join(bits), "المساطر والإجراءات", \
           {"description": "دليل المساطر والإجراءات القانونية والإدارية في المغرب خطوة بخطوة."}


def _domain_page(slug):
    with db_session() as conn:
        d = conn.execute("SELECT * FROM legal_domains WHERE slug=?", (slug,)).fetchone()
        if not d:
            return _list_laws()
        d = dict(d)
        rows = conn.execute(
            "SELECT lt.id, lt.title FROM legal_texts lt LEFT JOIN categories c ON c.id=lt.category_id "
            "WHERE lt.domain_id=? ORDER BY lt.title LIMIT 200", (d["id"],)).fetchall()
    title = d.get("name_ar") or "المكتبة"
    desc = d.get("description_ar") or f"نصوص قانونية ضمن مجال {title}."
    bits = ['<nav aria-label="Breadcrumb" class="seo-breadcrumb"><ol>'
            f'<li><a href="/">الرئيسية</a></li><li><a href="/laws">المكتبة</a></li>'
            f'<li aria-current="page">{_esc(title)}</li></ol></nav>',
            f"<h1>{_esc(title)}</h1>", f"<p>{_esc(desc)}</p>",
            '<ul class="seo-links">']
    for r in rows:
        bits.append(f'<li><a href="/laws/{r["id"]}">{_esc(r["title"])}</a></li>')
    bits.append("</ul>")
    return "".join(bits), title, {"description": desc}


# ---------------------------------------------------------------------------
# الراوتر الداخلي لصفحات SEO
# ---------------------------------------------------------------------------

def render_seo(path):
    """يردّ على مسار داخلي (بدون مخطط الوصف) بصفحة HTML أو None."""
    if not path:
        return None
    path = "/" + path.lstrip("/")
    path = path.split("?")[0]

    m = re.match(r"^/laws/(\d+)$", path)
    if m:
        content, title, meta = _law_page(int(m.group(1)))
        if content is None:
            return None
        return _inject(title, meta["description"], meta["path"], content,
                       jsonld_blocks=meta.get("jsonld", []), schema_type=meta.get("type", "WebPage"))

    m = re.match(r"^/jurisprudence/(\d+)$", path)
    if m:
        content, title, meta = _juris_page(int(m.group(1)))
        if content is None:
            return None
        return _inject(title, meta["description"], meta["path"], content,
                       jsonld_blocks=meta.get("jsonld", []), schema_type=meta.get("type", "WebPage"))

    m = re.match(r"^/procedures/([^/]+)$", path)
    if m:
        content, title, meta = _procedure_page(m.group(1))
        if content is None:
            return None
        return _inject(title, meta["description"], meta["path"], content,
                       jsonld_blocks=meta.get("jsonld", []), schema_type=meta.get("type", "WebPage"))

    if path == "/laws":
        content, title, meta = _list_laws()
        return _inject(title, meta["description"], "/laws", content)
    if path == "/jurisprudence":
        content, title, meta = _list_jurisprudence()
        return _inject(title, meta["description"], "/jurisprudence", content)
    if path == "/procedures":
        content, title, meta = _list_procedures()
        return _inject(title, meta["description"], "/procedures", content)

    m = re.match(r"^/domains/([^/]+)$", path)
    if m:
        content, title, meta = _domain_page(m.group(1))
        return _inject(title, meta["description"], path, content)

    return None


# ---------------------------------------------------------------------------
# Sitemaps
# ---------------------------------------------------------------------------

def _sitemap_urls(rows, base):
    out = []
    for r in rows:
        out.append(f"    <url><loc>{_esc(SITE + base + str(r[0]))}</loc></url>")
    return "".join(out)


def sitemap_index():
    urls = [
        {"loc": f"{SITE}/sitemaps/laws.xml", "changefreq": "weekly"},
        {"loc": f"{SITE}/sitemaps/jurisprudence.xml", "changefreq": "weekly"},
        {"loc": f"{SITE}/sitemaps/procedures.xml", "changefreq": "monthly"},
        {"loc": f"{SITE}/sitemap.xml", "changefreq": "daily"},
    ]
    # التقسيم عبر صفحات سايت ماب فرعية
    index = ["<?xml version='1.0' encoding='UTF-8'?>",
             "<sitemapindex xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"]
    for u in urls[:-1]:
        index.append(f"<sitemap><loc>{_esc(u['loc'])}</loc><changefreq>{u['changefreq']}</changefreq></sitemap>")
    index.append("</sitemapindex>")
    return "".join(index)


def sitemap_laws():
    with db_session() as conn:
        ids = [r[0] for r in conn.execute("SELECT id FROM legal_texts ORDER BY id").fetchall()]
    body = ["<?xml version='1.0' encoding='UTF-8'?>",
            "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"]
    for i in ids:
        body.append(f"<url><loc>{SITE}/laws/{i}</loc></url>")
    body.append("</urlset>")
    return "".join(body)


def sitemap_jurisprudence():
    with db_session() as conn:
        ids = [r[0] for r in conn.execute(
            "SELECT id FROM jurisprudence WHERE published=1 ORDER BY id").fetchall()]
    body = ["<?xml version='1.0' encoding='UTF-8'?>",
            "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"]
    for i in ids:
        body.append(f"<url><loc>{SITE}/jurisprudence/{i}</loc></url>")
    body.append("</urlset>")
    return "".join(body)


def sitemap_procedures():
    with db_session() as conn:
        slugs = [r[0] for r in conn.execute("SELECT slug FROM procedures ORDER BY slug").fetchall()]
    body = ["<?xml version='1.0' encoding='UTF-8'?>",
            "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"]
    for s in slugs:
        body.append(f"<url><loc>{SITE}/procedures/{_esc(s)}</loc></url>")
    body.append("</urlset>")
    return "".join(body)
