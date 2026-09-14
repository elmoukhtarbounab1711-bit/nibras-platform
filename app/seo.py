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
import logging as _logging
import re
from pathlib import Path

from flask import request

from . import config
from .database import db_session

SITE = config.SITE_URL


def _log(level: int, msg: str) -> None:
    """تسجيل بسيط آمن الترميز لرسائل نبراس SEO."""
    _logging.getLogger("nibras.seo").log(level, "%s", msg)


# --------------------------------------------------------------------
# حارس نطاق (P2-final): لو ضُبط NIBRAS_SITE_URL بيئةً على نطاق متوقف
# يتبقّى منه سوى صفحة استضافة ميتة، يُرفض الحرفيًّا عند البث بدل
# canonical متوفٍّ (سقوط فهرسة كامل سابقًا — تقرير التدقيق §P2).
# # النطاق الحالي الحي يُزاح إلى الأمام دائمًا مهما حاولت البيئة.
# --------------------------------------------------------------------
_DEAD_DOMAINS = ('nibraslaw.com',)

if SITE and any(_d in SITE for _d in _DEAD_DOMAINS):
    _log(_logging.WARNING, "... راقى متغيّر NIBRAS_SITE_URL إلى نطاق متوقف "
              + "لا يخدم الآن إلا صفحة استضافة؛ أثبت canonical إلى النطاق الحي.")
    SITE = 'https://nibras-law-platform.vercel.app/'.rstrip("/")
    _log(_logging.INFO, f"[seo] canonical forced LIVE => {SITE}")

_TEMPLATE = None


def _base_url() -> str:
    """القاعدة (protocol+host) من طلب HTTP الفعلي، مع سقوط احتياطي على SITE.

    يسمح بتحديث نطاق mخصص تلقائيًا دون تعديل الكود: عند ربط domain جديد
    على Vercel تأتي قيمة X-Forwarded-Host باسمه فيستخدمه هنا فورًا."""
    try:
        host = (request.headers.get("X-Forwarded-Host") or request.headers.get("Host") or "").strip()
    except RuntimeError:
        return SITE
    if not host:
        return SITE
    host = host.split(",")[0].strip()
    proto = "https"
    if request.headers.get("X-Forwarded-Proto"):
        proto = request.headers["X-Forwarded-Proto"].split(",")[0].strip().lower()
    elif request.scheme:
        proto = request.scheme.lower()
    return f"{proto}://{host}".rstrip("/")

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
    site = _base_url()
    canonical = site + clean_path

    # عنوان/وصف
    tpl = re.sub(r"<title>.*?</title>", _esc(title) and f"<title>{_esc(title)}</title>", tpl, count=1, flags=re.DOTALL)

    # إزالة وسوم meta السابقة التي قد تتعارض (وصف/OG/Twitter/canonical)
    tpl = re.sub(r'<meta\s+name="description"[^>]*>', "", tpl, flags=re.IGNORECASE)
    tpl = re.sub(r'<meta\s+property="og:[^"]*"[^>]*>', "", tpl, flags=re.IGNORECASE)
    tpl = re.sub(r'<meta\s+name="twitter:[^"]*"[^>]*>', "", tpl, flags=re.IGNORECASE)
    tpl = re.sub(r'<link\s+rel="canonical"[^>]*>', "", tpl, flags=re.IGNORECASE)

    head_block = f"""
<meta name="description" content="{_esc(description)}">
<link rel="canonical" href="{_esc(canonical)}">
<link rel="alternate" hreflang="ar" href="{_esc(canonical)}">
<link rel="alternate" hreflang="x-default" href="{_esc(canonical)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="نبراس">
<meta property="og:title" content="{_esc(title)}">
<meta property="og:description" content="{_esc(description)}">
<meta property="og:url" content="{_esc(canonical)}">
<meta property="og:image" content="{site}/assets/img/og-cover.png">
<meta property="og:image:alt" content="نبراس — منصة القانون المغربي">
<meta property="og:locale" content="ar_MA">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{_esc(title)}">
<meta name="twitter:description" content="{_esc(description)}">
<meta name="twitter:image" content="{site}/assets/img/og-cover.png">
"""

    blocks = []
    blocks.append({
        "@context": "https://schema.org",
        "@type": schema_type,
        "name": title,
        "url": canonical,
        "description": description,
        "inLanguage": "ar",
        "isPartOf": {"@type": "WebSite", "url": site, "name": "نبراس"},
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
            flags=re.DOTALL,
        )
    elif "id=\"view\"" in tpl:
        tpl = re.sub(
            r'(id="view"[^>]*>)(.*?)(</main>)',
            lambda m: m.group(1) + content_html + m.group(3),
            tpl,
            count=1,
            flags=re.DOTALL,
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


def _get_article(article_id):
    """مقال مدوّنة منشور واحد فقط (SSR للزحف — لا internal ولا مسوّدة)."""
    with db_session() as conn:
        row = conn.execute(
            "SELECT a.id, a.title, a.summary, a.body, a.keywords, a.cover_url, "
            "a.published_at, a.updated_at, a.views, "
            "u.full_name AS author_name, "
            "bc.name AS category_name, bc.slug AS category_slug, "
            "j.name AS jurisdiction_name "
            "FROM blog_articles a "
            "JOIN users u ON u.id = a.user_id "
            "LEFT JOIN blog_categories bc ON bc.id = a.category_id "
            "LEFT JOIN law_jurisdictions j ON j.id = a.jurisdiction_id "
            "WHERE a.id = ? AND a.status = 'published'",
            (article_id,),
        ).fetchone()
        return dict(row) if row else None


def _type_label(t):
    return {
        "law": "قانون", "decree": "مرسوم", "dahir": "ظهير", "decision": "قرار",
        "constitution": "دستور", "code": "مدونة", "agreement": "اتفاقية", "circular": "منشور",
    }.get(t, t)


def _cat_roots(names):
    """جذور الكلمات العربية المعنوية من أسماء فئات/نطاقات للمطابقة المتبادلة."""
    roots = set()
    for name in names or ():
        for w in re.findall(r"[\u0621-\u064A]{3,}", str(name or "")):
            w = w.lstrip("ال")
            if w and w != "قانون":
                roots.add(w[:4] if len(w) >= 4 else w)
    return roots


def _related_mixed(seed_names, kinds=("law", "juris", "proc"), exclude=(),
                   max_items=8):
    """رابط داخلي مختلط (قانون ↔ اجتهاد ↔ مسطرة) حسب تقاطع أسماء الفئات.

    لا يخترع بيانات: يطابق الكلمات الجذرية بين أسماء النطاقات/الفئات
    الحقيقية ويعيد روابط لصفحات قائمة فعلًا في DB."""
    seeds = _cat_roots(seed_names)
    if not seeds:
        return ""
    items = []
    with db_session() as conn:
        if "law" in kinds and _has_table(conn, "legal_domains"):
            rows = conn.execute(
                "SELECT id, name_ar FROM legal_domains WHERE name_ar IS NOT NULL"
            ).fetchall()
            dom_ids = [r["id"] for r in rows if _cat_roots([r["name_ar"]]) & seeds]
            if dom_ids:
                ph = ",".join("?" * len(dom_ids))
                q = ("SELECT id, title FROM legal_texts WHERE domain_id IN (%s) "
                     "ORDER BY title LIMIT 4") % ph
                items += [("law", r["id"], r["title"])
                          for r in conn.execute(q, tuple(dom_ids)).fetchall()
                          if r["id"] not in exclude]
        if "juris" in kinds:
            if _has_table(conn, "jurisprudence_categories"):
                rows = conn.execute(
                    "SELECT id, name FROM jurisprudence_categories WHERE name IS NOT NULL"
                ).fetchall()
                cat_ids = [r["id"] for r in rows if _cat_roots([r["name"]]) & seeds]
                if cat_ids:
                    ph = ",".join("?" * len(cat_ids))
                    q = ("SELECT id, title FROM jurisprudence WHERE category_id IN (%s) "
                         "AND published=1 ORDER BY id DESC LIMIT 4") % ph
                    items += [("juris", r["id"], r["title"])
                              for r in conn.execute(q, tuple(cat_ids)).fetchall()
                              if r["id"] not in exclude]
        if "proc" in kinds:
            if _has_table(conn, "procedures"):
                rows = conn.execute(
                    "SELECT DISTINCT category FROM procedures "
                    "WHERE category IS NOT NULL AND category<>''"
                ).fetchall()
                cat_sel = [r["category"] for r in rows
                           if _cat_roots([r["category"]]) & seeds]
                if cat_sel:
                    ph = ",".join("?" * len(cat_sel))
                    q = ("SELECT slug, title FROM procedures WHERE category IN (%s) "
                         "ORDER BY title LIMIT 3") % ph
                    items += [("proc", r["slug"], r["title"])
                              for r in conn.execute(q, tuple(cat_sel)).fetchall()
                              if r["slug"] not in exclude]
        if not items and seed_names:
            for sn in seed_names:
                if items:
                    break
                same_j = conn.execute(
                    "SELECT id, name FROM jurisprudence_categories "
                    "WHERE name IS NOT NULL AND name=?", (sn,)
                ).fetchall()
                if same_j:
                    same_ids = [r["id"] for r in same_j]
                    ph = ",".join("?" * len(same_ids))
                    q = ("SELECT id, title FROM jurisprudence WHERE category_id IN (%s) "
                         "AND published=1 ORDER BY id DESC LIMIT 4") % ph
                    items += [("juris", r["id"], r["title"])
                              for r in conn.execute(q, tuple(same_ids)).fetchall()
                              if r["id"] not in exclude]
                if not items:
                    same_p = conn.execute(
                        "SELECT slug, title FROM procedures WHERE category=? "
                        "ORDER BY title LIMIT 4", (sn,)
                    ).fetchall()
                    items += [("proc", r["slug"], r["title"]) for r in same_p
                              if r["slug"] not in exclude]
    if not items:
        return ""
    labels = {"law": "قانون", "juris": "اجتهاد", "proc": "مسطرة"}
    urls = {"law": lambda ref: f"/laws/{ref}",
            "juris": lambda ref: f"/jurisprudence/{ref}",
            "proc": lambda ref: f"/procedures/{ref}"}
    bits = ['<h2>ما يتصل بهذا المحتوى</h2><ul class="seo-links">']
    for kind, ref, ttl in items[:max_items]:
        lk = f'<span class="seo-badge seo-badge-sm">{labels[kind]}</span> '
        bits.append(f'<li>{lk}<a href="{urls[kind](ref)}">{_esc(_art_label(ttl, 100))}</a></li>')
    bits.append("</ul>")
    return "".join(bits)


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

    bits.append(_related_mixed(
        [law.get("domain_name"), law.get("category_name")],
        kinds=("juris", "proc"), exclude=(law_id,)))

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

    bits.append(_related_mixed(
        [cat], kinds=("law", "proc"), exclude=(decision_id,)))

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

    bits.append(_related_mixed(
        [cat], kinds=("law", "juris"), exclude=(slug,)))

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


def _home_page():
    """الصفحة الرئيسية (SSR): إحصائيات حقيقية + أحدث المحتوى + روابط الأقسام."""
    from . import generator as _gen
    with db_session() as conn:
        laws_count = conn.execute("SELECT COUNT(*) FROM legal_texts").fetchone()[0]
        juris_count = conn.execute(
            "SELECT COUNT(*) FROM jurisprudence WHERE published=1").fetchone()[0]
        proc_count = conn.execute("SELECT COUNT(*) FROM procedures").fetchone()[0]
        laws = conn.execute(
            "SELECT id, title FROM legal_texts ORDER BY id DESC LIMIT 8").fetchall()
        juris = conn.execute(
            "SELECT id, title FROM jurisprudence WHERE published=1 "
            "ORDER BY id DESC LIMIT 8").fetchall()
        blogs = conn.execute(
            "SELECT id, title FROM blog_articles WHERE status='published' "
            "ORDER BY published_at DESC, id DESC LIMIT 8").fetchall()
    docs_count = _gen.read_index().get("total_files", 0)

    numerals = {"0": "٠", "1": "١", "2": "٢", "3": "٣", "4": "٤",
                "5": "٥", "6": "٦", "7": "٧", "8": "٨", "9": "٩"}
    def fmt(n):
        return "".join(numerals.get(c, c) for c in str(n))

    title = "نبراس — المنصة القانونية المغربية"
    desc = ("المكتبة القانونية المغربية في متناول الجميع: نصوص قانونية، اجتهادات "
            "قضائية، مساطر إدارية وقضائية، مولد وثائق وعقود، ومدوّنة قانونية.")

    stats = [
        ("نصًا قانونيًا", laws_count, "/laws"),
        ("اجتهادًا قضائيًا", juris_count, "/jurisprudence"),
        ("مسطرة وإجراء", proc_count, "/procedures"),
        ("مستندًا للتعبيئة", docs_count, "/generator"),
    ]
    bits = ['<section class="home-hero"><h1>نبراس — منصة القانون المغربي</h1>',
            f"<p>{_esc(desc)}</p>"
            '<p class="seo-small">ابحث في كل المحتوى من الصفحة الرئيسية أو من شريط البحث.</p>'
            '<div class="home-stats">']
    for label, val, href in stats:
        bits.append(f'<a class="seo-stat" href="{href}"><strong>{fmt(val)}</strong>'
                    f'<span>{_esc(label)}</span></a>')
    bits.append("</div></section>")

    sections = [
        (("أحدث النصوص القانونية", "/laws"),
         [f'<li><a href="/laws/{r["id"]}">{_esc(_art_label(r["title"], 100))}</a></li>'
          for r in laws] or ["<li>لا نتائج.</li>"]),
        (("أحدث الاجتهادات القضائية", "/jurisprudence"),
         [f'<li><a href="/jurisprudence/{r["id"]}">{_esc(_art_label(r["title"], 100))}</a></li>'
          for r in juris] or ["<li>لا نتائج.</li>"]),
        (("أحدث مقالات المدوّنة", "/blog"),
         [f'<li><a href="/blog/{r["id"]}">{_esc(_art_label(r["title"], 100))}</a></li>'
          for r in blogs] or ["<li>لا نتائج.</li>"]),
    ]
    for (heading, link), items in sections:
        bits.append(f'<section class="home-section"><h2>'
                    f'<a href="{link}">{_esc(heading)}</a></h2><ul class="seo-links">{ "".join(items) }</ul></section>')

    bits.append('<section class="home-section"><h2>بوابات الوصول السريع</h2><ul class="seo-links">'
                '<li><a href="/laws">المكتبة القانونية</a></li>'
                '<li><a href="/jurisprudence">الاجتهادات القضائية</a></li>'
                '<li><a href="/procedures">المساطر</a></li>'
                '<li><a href="/generator">مولد الوثائق والعقود</a></li>'
                '<li><a href="/blog">المدوّنة</a></li>'
                '<li><a href="/about">من نحن</a></li>'
                '<li><a href="/contact">اتصل بنا</a></li>'
                '<li><a href="/disclaimer">إخلاء المسؤولية</a></li>'
                '</ul></section>')

    content = "".join(bits)
    site = _base_url()
    ld = [{
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": title,
        "url": site + "/",
        "inLanguage": "ar",
        "potentialAction": {
            "@type": "SearchAction",
            "target": {"@type": "EntryPoint",
                       "urlTemplate": site + "/library/q/{search_term_string}"},
            "query-input": "required name=search_term_string",
        },
        "publisher": {"@type": "Organization", "name": "نبراس", "url": site},
    }]
    return content, title, {"description": desc, "path": "/", "jsonld": ld}


def _list_laws():
    with db_session() as conn:
        rows = conn.execute(
            "SELECT lt.id, lt.title, lt.official_ref, c.name AS category_name "
            "FROM legal_texts lt LEFT JOIN categories c ON c.id=lt.category_id "
            "ORDER BY lt.title LIMIT 200").fetchall()
    bits = [('<nav aria-label="Breadcrumb" class="seo-breadcrumb"><ol>'
             '<li><a href="/">الرئيسية</a></li><li aria-current="page">المكتبة</li></ol></nav>'),
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
    bits = [('<nav aria-label="Breadcrumb" class="seo-breadcrumb"><ol>'
             '<li><a href="/">الرئيسية</a></li><li aria-current="page">الاجتهادات</li></ol></nav>'),
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
            "SELECT p.slug, p.title, p.category "
            "FROM procedures p "
            "ORDER BY p.title").fetchall()
    bits = [('<nav aria-label="Breadcrumb" class="seo-breadcrumb"><ol>'
             '<li><a href="/">الرئيسية</a></li><li aria-current="page">المساطر</li></ol></nav>'),
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
        if not _has_table(conn, "legal_domains"):
            return None
        d = conn.execute("SELECT * FROM legal_domains WHERE slug=?", (slug,)).fetchone()
        if not d:
            return None
        d = dict(d)
        rows = conn.execute(
            "SELECT lt.id, lt.title FROM legal_texts lt LEFT JOIN categories c ON c.id=lt.category_id "
            "WHERE lt.domain_id=? ORDER BY lt.title LIMIT 200", (d["id"],)).fetchall()
    title = d.get("name_ar") or "المكتبة"
    desc = d.get("description_ar") or f"نصوص قانونية ضمن مجال {title}."
    bits = [('<nav aria-label="Breadcrumb" class="seo-breadcrumb"><ol>'
             f'<li><a href="/">الرئيسية</a></li><li><a href="/laws">المكتبة</a></li>'
             f'<li aria-current="page">{_esc(title)}</li></ol></nav>'),
            f"<h1>{_esc(title)}</h1>", f"<p>{_esc(desc)}</p>",
            '<ul class="seo-links">']
    for r in rows:
        bits.append(f'<li><a href="/laws/{r["id"]}">{_esc(r["title"])}</a></li>')
    bits.append("</ul>")
    return "".join(bits), title, {"description": desc}


def _about_page():
    """صفحة «من نحن» (SSR) — الشفافية والمصداقية (متطلبات المراجعة الآلية AdSense)."""
    title = "من نحن — نبراس | المنصة القانونية المغربية"
    desc = ("نبراس منصة رقمية للمعلومات القانونية المغربية: مكتبة النصوص، الاجتهادات، "
            "المساطر، مولد الوثائق والعقود، وحاسبات قانونية. رسالتنا ومنهجيتنا التحريرية.")
    bits = [
        ('<nav aria-label="Breadcrumb" class="seo-breadcrumb"><ol>'
         '<li><a href="/">الرئيسية</a></li>'
         '<li aria-current="page">من نحن</li></ol></nav>'),
        "<h1>من نحن</h1>",
        "<p>نبراس منصة رقمية للمعلومات القانونية المغربية، أُنشئت لجعل القانون في المتناول: مفهوماً وقابلاً للاستعمال. نجمع في فضاء واحد: مكتبة النصوص القانونية المغربية، الاجتهادات القضائية، المساطر، حاسبات قانونية، نماذج وثائق، مولد العقود، ومساعداً ذكياً قانونياً.</p>",
        "<h2>رسالتنا</h2>",
        "<p>تيسير الوصول إلى المعلومات القانونية في المغرب: البحث عن نص قانوني، أو قراءة مبدأ قضائي، أو إعداد وثيقة في نقرة، دون حاجة لخلفية قانونية مسبقة.</p>",
        "<h2>ما الذي تقدمه المنصة؟</h2>",
        ("<ul>"
         "<li>مكتبة النصوص القانونية المغربية منظمة حسب مجالات وفئات مع بحث نصي كامل.</li>"
         "<li>الاجتهادات: قرارات ومبادئ مستمدة من القضاء المغربي مصنفة حسب المجال.</li>"
         "<li>المساطر: إجراءات إدارية وقضائية مشروحة خطوة بخطوة.</li>"
         "<li>مولد الوثائق والعقود: أكثر من 1900 وثيقة تُعبّأ عبر الخط.</li>"
         "<li>حاسبات قانونية ومساعدة لتعلّم المصطلحات القانونية.</li>"
         "</ul>"),
        "<h2>منهجية التحرير</h2>",
        "<p>يُعد المحتوى انطلاقاً من مصادر رسمية (الجريدة الرسمية، المنشورات القضائية) ويُنظم تحت إشراف تحريري. يمر كل محتوى عبر تدقيق المصادر قبل النشر. الوثائق الرسمية تُعاد لأغراض إعلامية؛ وعند أي اختلاف تعتمد النسخة المنشورة بالجريدة الرسمية.</p>",
        "<h2>استخدام مسؤول</h2>",
        "<p>نبراس منصة معلومات وتوعية قانونية. المعلومات المقدمة ليست رأياً قانونياً ولا تغني عن استشارة مهني معتمد (محامٍ، موثق، عدل، مفوض قضائي). راجع صفحة <a href='/disclaimer'>إخلاء المسؤولية</a> للمزيد.</p>",
        "<h2>الشفافية</h2>",
        ("<ul>"
         "<li>الاستشهاد بالمصادر الرسمية لكل نص قانوني.</li>"
         "<li>تصحيح أي خطأ يُبلَّغ عنه بسرعة.</li>"
         "<li>توضيح أن المحتوى لأغراض إعلامية وتعليمية.</li>"
         "</ul>"),
    ]
    return "".join(bits), title, {"description": desc}


def _contact_page():
    """صفحة «اتصل بنا» (SSR) — قناة تواصل فعّالة (متطلبات الشفافية AdSense)."""
    from . import config as _cfg

    email = getattr(_cfg, "CONTACT_EMAIL", "") or "elmoukhtar.bounab1711@gmail.com"
    title = "اتصل بنا — نبراس | المنصة القانونية المغربية"
    desc = "تواصل مع فريق نبراس: سؤال، ملاحظة، تبليغ عن خطأ في نص أو قرار، أو طلب يتعلق بمعطياتك الشخصية."
    bits = [
        ('<nav aria-label="Breadcrumb" class="seo-breadcrumb"><ol>'
         '<li><a href="/">الرئيسية</a></li>'
         '<li aria-current="page">اتصل بنا</li></ol></nav>'),
        "<h1>اتصل بنا</h1>",
        f"<p>عنوان التواصل لدينا هو: <strong><a href=\"mailto:{_esc(email)}\" rel=\"noopener\">{_esc(email)}</a></strong>. نرد عادةً خلال 48 ساعة عمل.</p>",
        "<h2>موضوع الرسالة</h2>",
        ("<ul>"
         "<li>التبليغ عن خطأ أو طلب تصحيح في نص أو قرار.</li>"
         "<li>طلب حذف محتوى (حقوق المؤلف، معطيات شخصية).</li>"
         "<li>اقتراح تحسين المنصة (وظائف، محتوى).</li>"
         "<li>الصحافة: طلبات الحوار أو الشراكات.</li>"
         "</ul>"),
        "<h2>الخصوصية</h2>",
        "<p>لا نشارك بريدك الإلكتروني أبداً مع أي طرف ثالث. تُعالج الرسائل وفق سياسة الخصوصية (القانون 09-08). لأي طلب يتعلق بمعطياتك الشخصية (الوصول، التصحيح، المحو)، اكتب مع تحديد «معطيات شخصية» في موضوع الرسالة.</p>",
    ]
    return "".join(bits), title, {"description": desc}


def _legal_ssr(slug):
    """صفحات الثقة (SSR للزحف): الخصوصية/الشروط/الكوكيز/الإخلاء/الدليل."""
    from . import config as _cfg

    email = getattr(_cfg, "CONTACT_EMAIL", "") or "elmoukhtar.bounab1711@gmail.com"
    pages = {
        "privacy": {
            "title": "سياسة الخصوصية — نبراس",
            "desc": "كيف تتعامل منصة نبراس مع معطياتك الشخصية وفق القانون 09-08: البيانات المجمعة، حقوقك، التخزين، والمشاركة مع الأطراف الثالثة.",
            "intro": "نحترم خصوصيتك ونلتزم بالقانون رقم 09-08 المتعلق بحماية الأشخاص الذاتيين في معالجة المعطيات ذات الطابع الشخصي.",
            "sections": [
                ("البيانات التي نجمعها", [
                    "بيانات الحساب عند التسجيل (الاسم، البريد الإلكتروني، كلمة المرور بصيغة مشفرة).",
                    "سجل تفاعلات المنصة: عمليات البحث، توليد الوثائق، تفضيلات اللغة والسمة.",
                    "بيانات تقنية: نوع المتصفح، الحالة، الوقت، وعنوان IP بصيغة مجهولة عند الضرورة.",
                ]),
                ("الأساس القانوني والأغراض", [
                    "تنفيذ الخدمات المطلوبة (تسجيل، توثيق، مولد العقود، الإخطارات).",
                    "تحسين تجربة الاستخدام ومراقبة كفاءة المنصة بأدوات قياس اختيارية.",
                    "الرد على طلباتك عبر صفحة الاتصال للحفاظ على قناة تواصل فعّالة.",
                ]),
                ("حقوقك", [
                    "حق الوصول إلى معطياتك، وطلب تصحيحها أو محوها أو تقييد معالجتها.",
                    "حق سحب الموافقة في أي وقت (مثال: ملفات الإعلان أو التحليل المخصصة).",
                    "لأي طلب راسلنا على <a href='mailto:EMAIL'>EMAIL</a> مع تحديد «معطيات شخصية» في الموضوع.",
                ]),
                ("التخزين والحفظ", [
                    "تُخزَّن كلمة المرور مشفرة فقط (لا تُحفظ كنص صريح أبداً).",
                    "تُحتفظ بالبيانات للمدة اللازمة للأغراض المذكورة وبما يقتضيه القانون.",
                    "المدفوعات والاشتراكات تُؤمَّن عبر معالجات دفع خارجية معتمدة دون تخزين بطاقاتك.",
                ]),
                ("المشاركة مع الأطراف الثالثة", [
                    "لا نبيع معطياتك الشخصية إطلاقاً.",
                    "قد نستخدم خبرات تابعة (استضافة، دفع، تحليل) تتعامل مع البيانات وفق اتفاقيات حماية.",
                    "ملفات الإعلان المخصصة (عند موافقتك) قد تُعالج من Google AdSense وفق سياساتها.",
                ]),
                ("ملفات تعريف الارتباط والإعلان", [
                    "راجع صفحة <a href='/cookie-policy'>سياسة ملفات تعريف الارتباط</a> لتفاصيل الأنواع والغرض والمدة.",
                    "يمكنك إدارة موافقتك في أي وقت عبر زر «إدارة» في شريط الملفات.",
                ]),
            ],
        },
        "terms": {
            "title": "شروط الاستخدام — نبراس",
            "desc": "شروط استخدام منصة نبراس القانونية: الاستخدام المسموح، الملكية الفكرية، المسؤولية، تحديد الخدمات، والقانون الحاكم.",
            "intro": "باستخدامك منصة نبراس فأنت توافق على الشروط التالية. يرجى قراءتها بعناية قبل استخدام الخدمات.",
            "sections": [
                ("قبول الشروط", [
                    "استخدام المنصة يعني موافقتك على هذه الشروط وسياسة الخصوصية ذات الصلة.",
                    "يمكن تعديل الشروط متى اقتضى الأمر، ويُنشر أي تعديل جوهري في هذه الصفحة.",
                ]),
                ("الاستخدام المسموح والممنوع", [
                    "استخدام المنصة لأغراض مشروعة ضمن إطار الاستعمال الشخصي أو المهني العادي.",
                    "يُمنع إساءة استعمال الخدمات، أو محاولة اختراق الأنظمة، أو استخراج محتوى آلياً بما يخل بجودة الخدمة.",
                    "يحظر انتحال شخصية الغير أو نشر محتوى مخالف للقانون أو للآداب.",
                ]),
                ("المحتوى والملكية الفكرية", [
                    "المحتوى التحريري والأدوات المطورة للمنصة ملكيتها لنبراس وفق القوانين المعمول بها.",
                    "النصوص القانونية تُقدَّم انطلاقاً من مصادر رسمية (الجريدة الرسمية) لأغراض إعلامية.",
                    "الاستشهاد بالمحتوى لأغراض تعليمية مسموح مع ذكر المصدر.",
                ]),
                ("طبيعة المعلومات القانونية", [
                    "المعلومات المنشورة إرشادية ولا تُعدّ رأياً قانونياً أو استشارة مهنية.",
                    "لا تنشئ المنصة علاقة محامٍ-موكّل ولا تغني عن مراجعة مهني معتمد.",
                    "عند تعارض أي مقتضى، تعتمد النسخة الرسمية المنشورة بالجريدة الرسمية أو في مرجعها الرسمي.",
                ]),
                ("الحسابات والاشتراكات", [
                    "أنت مسؤول عن سرية بيانات حسابك وجلساتك.",
                    "قد تُوفَّر خدمات مجانية وخدمات باشتراك، وتُوضَّح شروط كل عرض في صفحته.",
                    "نحتفظ بحق إنهاء أي حساب مسيء أو مخالف للشروط.",
                ]),
                ("الروابط الخارجية والإخبار", [
                    "قد يتضمن المحتوى روابط لمواقع خارجية؛ لا نتحمل مسؤولية مضمونها.",
                    "البيانات المُخلة والمحتوى المُوَلَّد آلياً تنخره مسؤولية مستخدمها.",
                ]),
            ],
        },
        "cookie-policy": {
            "title": "سياسة ملفات تعريف الارتباط — نبراس",
            "desc": "أنواع ملفات تعريف الارتباط التي تستخدمها نبراس، الغرض منها ومدتها، وكيفية إدارة موافقتك وفق القانون 09-08.",
            "intro": "تُستخدم ملفات تعريف الارتباط لضمان عمل المنصة، وحفظ تفضيلاتك، وقياس الأداء، وعرض الإعلانات عند موافقتك فقط.",
            "sections": [
                ("ما هي ملفات تعريف الارتباط", [
                    "ملفات نصية صغيرة تُخزَّن على جهازك ليتذكر الموقع إجراءاتك وتفضيلاتك لفترة معينة.",
                ]),
                ("الأنواع والغرض والمدة", [
                    "الضرورية: المصادقة وجلسة المستخدم والتفضيلات (الجلسة / حتى 30 يوماً).",
                    "الوظيفية: تذكّر خيارات العرض والتنقل (حتى 30 يوماً).",
                    "التحليل: قياس الأداء واقتصاديات الاستخدام (فقط عند موافقتك).",
                    "الإعلانية: عرض إعلانات ذات صلة عبر Google AdSense (فقط عند موافقتك).",
                ]),
                ("إدارة الموافقة", [
                    " شريط ملفات تعريف الارتباط يتيح لك القبول الكلي، الرفض، أو التخصيص الفئوي.",
                    "زر «إدارة» يعيد فتح لوحة التفضيلات في أي وقت دون حذف بيانات التصفح.",
                ]),
                ("ملفات الأطراف الثالثة والإعلان", [
                    "عند موافقتك على ملفات الإعلان تُعالج إعلانات Google AdSense معطيات غير دقيقة وفق شروط Google.",
                    "تعطيل الإعلانات المخصصة: <a href='https://adssettings.google.com' rel='noopener'>إعدادات إعلانات Google</a> و<a href='https://optout.aboutads.info' rel='noopener'>optout.aboutads.info</a>.",
                ]),
                ("القانون الحاكم", [
                    "تخضع هذه السياسة للقانون 09-08 والتنظيمات المغربية المعمول بها.",
                ]),
            ],
        },
        "disclaimer": {
            "title": "إخلاء المسؤولية — نبراس",
            "desc": "حدود المسؤولية: المنصة معلومات وتوعية قانونية ولا تُغني عن استشارة مهني معتمد. توضيح طبيعة المحتوى ومصادره.",
            "intro": "يرجى قراءة هذا الإخلاء بعناية قبل الاعتماد على أي محتوى منشور على المنصة.",
            "sections": [
                ("طبيعة المحتوى", [
                    "هذا المحتوى إعلامي/توعوي ويُقدَّم لأغراض تعليمية عامة.",
                    "لا يشكّل رأياً قانونياً، ولا استشارة، ولا تمثيلاً قضائياً.",
                ]),
                ("لا علاقة محامٍ-موكّل", [
                    "استخدام المنصة لا يُنشئ علاقة مهنية بينك وبين فريقها.",
                    "المساعد الذكي وتوليد الوثائق أدوات مساعدة لا تستبدل توقيعك أو مراجعة المهني.",
                ]),
                ("الدقة والمصادر", [
                    "نسعى لمطابقة المنشور مع المصادر الرسمية (الجريدة الرسمية، المنشورات القضائية).",
                    "عند أي اختلاف، تعتمد النسخة الرسمية، ويُصحَّح ما يُبلَّغ عنه بسرعة.",
                ]),
                ("حدود المسؤولية", [
                    "لا نضمن خلو الخدمات من أخطاء تقنية أو انقطاع مؤقت.",
                    "لا نتحمل أضراراً ناتجة عن الاعتماد على المحتوى دون مراجعة مهنية مختصة.",
                    "الوثائق المولَّدة عبر المولد قوالب معبأة؛ تحقق من ملاءمتها لحالتك وعرضها على مهني.",
                ]),
                ("التواصل والتصحيح", [
                    "للإبلاغ عن خطأ أو طلب تصحيح راسلنا على <a href='mailto:EMAIL'>EMAIL</a>.",
                ]),
            ],
        },
        "guide": {
            "title": "دليل الاستخدام — نبراس",
            "desc": "دليل عملي لاستخدام منصة نبراس: البحث في النصوص، قراءة الاجتهادات، مولد العقود، المساعد الذكي، والحساب.",
            "intro": "دليل موجز يشرح كيفية الاستفادة المثلى من خدمات منصة نبراس في دقائق.",
            "sections": [
                ("التصفح والبحث", [
                    "استخدم البحث النصي الكامل للعثور على نصوص قانونية وقرارات في مجالاتها.",
                    "صفحات المكتبة والاجتهادات مصنفة حسب المجالات والفئات مع ترشيح سهلة.",
                ]),
                ("قراءة الاجتهادات", [
                    "كل قرار يُعرض مع مضمونه ومصدره وسنده، ومصنف حسب المجال القانوني.",
                    "استخدم روابط النصوص المرتبطة للانتقال من المبدأ إلى النص المطبق.",
                ]),
                ("مولد الوثائق والعقود", [
                    "اختر قالب العقد أو الوثيقة، عبّئ خانات النموذج، واحصل على مستند Word جاهز.",
                    "راجع الوثيقة الناتجة دائماً، وحدِّثها وفق وضعك قبل الاعتماد عليها.",
                ]),
                ("المساعد الذكي والموارد", [
                    "اسأل مساعد المنصة بلغة طبيعية واحصل على إجابات بمصادر محددة.",
                    "تصفح الحاسبات القانونية والأدلة التعليمية ضمن مساحة التعلم.",
                ]),
                ("الحساب والاشتراك", [
                    "بدون حساب يمكنك تصفح المحتوى وتوليد الوثائق العام.",
                    "أنشئ حساباً لحفظ وثائقك، وإدارة إشعاراتك، والوصول لخدمات الاشتراك.",
                ]),
            ],
        },
    }
    p = pages.get(slug.strip("/"))
    if p is None:
        return None, None, None
    bits = [
        ('<nav aria-label="Breadcrumb" class="seo-breadcrumb"><ol>'
         '<li><a href="/">الرئيسية</a></li>'
         f'<li aria-current="page">{_esc(p["title"].split(" — ", 1)[0])}</li></ol></nav>'),
        f"<h1>{_esc(p['title'].split(' — ', 1)[0])}</h1>",
        f"<p>{_esc(p['intro'])}</p>",
    ]
    for h, items in p["sections"]:
        bits.append(f"<h2>{_esc(h)}</h2><ul>")
        for it in items:
            content = it.replace("EMAIL", _esc(email))
            bits.append(f"<li>{content}</li>")
        bits.append("</ul>")
    return "".join(bits), p["title"], {"description": p["desc"]}


def _list_generator():
    """صفحة مولد العقود (SSR): القوالب الموصى بها + الأصناف من مكتبة الوثائق."""
    from . import generator as _gen

    templates = _gen.recommended_templates()
    cats = _gen.categories()
    total = _gen.read_index().get("total_files", 0)
    title = "مولد الوثائق والعقود — قوالب معبأة جاهزة"
    desc = (f"مولّد وثائق وعقود مغربية: عبّئ قالبًا قانونيًا (وكالة، عقد كراء، "
            f"تنازل، إشهاد...) واحصل على مستند Word جاهز. مكتبة تضم {total} قالبًا.")
    bits = [('<nav aria-label="Breadcrumb" class="seo-breadcrumb"><ol>'
             '<li><a href="/">الرئيسية</a></li>'
             '<li aria-current="page">مولد العقود</li></ol></nav>'),
            "<h1>مولد الوثائق والعقود</h1>",
            f"<p>{_esc(desc)}</p>"]
    if templates:
        bits.append("<h2>قوالب موصى بها</h2><ul class='seo-links'>")
        for t in templates[:30]:
            tid = t.get("id")
            target = f"/generator/template/{_esc(tid)}" if tid else "/generator"
            bits.append(f'<li><a href="{target}">{_esc(t["title"])}</a>'
                        f' <span class="seo-small">({_esc(t["category"])})</span></li>')
        bits.append("</ul>")
    if cats:
        bits.append("<h2>أصناف الوثائق</h2><ul class='seo-links'>")
        for c in cats:
            bits.append(f'<li><strong>{_esc(c["name"])}</strong> — {_esc(c["count"])} قالب</li>')
        bits.append("</ul>")
    return "".join(bits), title, {"description": desc}


_GEN_FIELD_TYPES = {"text": "نص", "textarea": "نص طويل", "date": "تاريخ",
                    "money": "مبلغ", "number": "رقم"}


def _gen_field_count_label(n):
    if not n or n <= 0:
        return ""
    if n == 1:
        return "حقل واحد للتعبئة"
    return f"{n} حقول للتعبئة" if n <= 10 else f"{n} حقلًا للتعبئة"


def _template_page(template_id):
    """صفحة قالب موصى به من مولد العقود (SSR): الاسم/الوصف/الحقول + JSON-LD."""
    from . import generator as _gen
    tpl = _gen.get_recommended(template_id)
    if not tpl or not tpl.get("file"):
        return None, None, None
    title = tpl.get("title") or "قالب وثيقة"
    category = tpl.get("category") or ""
    desc = tpl.get("description") or f"قالب «{title}» من مكتبة الوثائق المغربية."
    fields = tpl.get("fields") or []
    path = f"/generator/template/{template_id}"

    crumbs = [("الرئيسية", "/"), ("مولد العقود", "/generator")]
    if category:
        crumbs.append((category, None))
    crumbs.append((title, None))
    bc_html = _breadcrumb_html(crumbs)

    bits = [bc_html, f"<h1>{_esc(title)}</h1>", '<div class="seo-meta">']
    if category:
        bits.append(f'<a class="seo-badge" href="/generator">{_esc(category)}</a>')
    if fields:
        bits.append(f'<span class="seo-badge">{_esc(_gen_field_count_label(len(fields)))}</span>')
    bits.append("</div>")
    if desc:
        bits.append(f"<p class='seo-text'>{_esc(desc)}</p>")
    if fields:
        bits.append("<h2>حقول التعبئة</h2><ul class='seo-links'>")
        for f in fields:
            label = f.get("label") or f.get("key") or ""
            ftype = _GEN_FIELD_TYPES.get(f.get("type"), f.get("type") or "نص")
            bits.append(f'<li>{_esc(label)} <span class="seo-small">({_esc(ftype)})</span></li>')
        bits.append("</ul>")
    content = "".join(bits)

    site = _base_url()
    ld_bc = [{
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "الرئيسية", "item": site + "/"},
            {"@type": "ListItem", "position": 2, "name": "مولد العقود", "item": site + "/generator"},
            {"@type": "ListItem", "position": 3, "name": title, "item": site + path},
        ],
    }]
    ld_article = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "url": site + path,
        "description": desc,
        "inLanguage": "ar",
        "author": {"@type": "Organization", "name": "نبراس", "url": site},
        "publisher": {"@type": "Organization", "name": "نبراس", "url": site},
        "mainEntityOfPage": {"@type": "WebPage", "@id": site + path},
    }
    return content, title, {"description": desc, "path": path,
                            "jsonld": ld_bc + [ld_article]}


def _blog_page(article_id):
    """صفحة مقال واحد من المدوّنة (SSR) مع JSON-LD نوع BlogPosting."""
    a = _get_article(article_id)
    if not a:
        return None, None, None
    title = a.get("title") or "مقال"
    cat = a.get("category_name")
    author = a.get("author_name") or "نبراس"
    desc = _art_label(a.get("summary") or f"{title} — من مدوّنة نبراس القانونية.", 160)
    crumbs = [("الرئيسية", "/"), ("المدونة", "/blog"), (cat or "المقال", None)]
    bc_html = _breadcrumb_html(crumbs)

    bits = [bc_html, f"<h1>{_esc(title)}</h1>", '<div class="seo-meta">']
    if cat:
        bits.append(f'<a class="seo-badge" href="/blog?cat={_esc(a.get("category_slug") or "")}">{_esc(cat)}</a>')
    if a.get("published_at"):
        bits.append(f'<span class="seo-badge">{_esc(a["published_at"][:10])}</span>')
    if author:
        bits.append(f'<span class="seo-badge">بقلم {_esc(author)}</span>')
    bits.append("</div>")
    if a.get("summary"):
        bits.append(f"<p class='seo-text'>{_esc(a['summary'])}</p>")
    if a.get("body"):
        bits.append(f"<div class='seo-text'>{_esc(a['body'])}</div>")

    content = "".join(bits)
    site = _base_url()
    ld_bc = [{
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "الرئيسية", "item": site + "/"},
            {"@type": "ListItem", "position": 2, "name": "المدونة", "item": site + "/blog"},
            {"@type": "ListItem", "position": 3, "name": title, "item": site + f"/blog/{article_id}"},
        ],
    }]
    ld_article = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": title,
        "url": site + f"/blog/{article_id}",
        "description": desc,
        "inLanguage": "ar",
        "author": {"@type": "Person", "name": author},
        "publisher": {"@type": "Organization", "name": "نبراس", "url": site},
        "mainEntityOfPage": {"@type": "WebPage", "@id": site + f"/blog/{article_id}"},
    }
    if a.get("published_at"):
        ld_article["datePublished"] = a["published_at"].replace(" ", "T")
    if a.get("updated_at"):
        ld_article["dateModified"] = a["updated_at"].replace(" ", "T")
    if a.get("cover_url"):
        ld_article["image"] = {"@type": "ImageObject", "url": a["cover_url"]}
    if a.get("keywords"):
        ld_article["keywords"] = a["keywords"]

    return content, title, {"description": desc, "path": f"/blog/{article_id}",
                             "jsonld": ld_bc + [ld_article], "type": "BlogPosting"}


def _list_blog():
    """قائمة المقالات المنشورة (SSR) — أول 50 مقالاً بأحدث النشر."""
    with db_session() as conn:
        rows = conn.execute(
            "SELECT a.id, a.title, a.summary, a.published_at, "
            "u.full_name AS author_name, bc.name AS category_name, bc.slug AS category_slug "
            "FROM blog_articles a "
            "JOIN users u ON u.id = a.user_id "
            "LEFT JOIN blog_categories bc ON bc.id = a.category_id "
            "WHERE a.status = 'published' "
            "ORDER BY a.published_at DESC, a.id DESC LIMIT 50"
        ).fetchall()
    bits = [
        ('<nav aria-label="Breadcrumb" class="seo-breadcrumb"><ol>'
         '<li><a href="/">الرئيسية</a></li>'
         '<li aria-current="page">المدونة</li></ol></nav>'),
        "<h1>مدوّنة نبراس القانونية</h1>",
        "<p>مقالات وشروحات قانونية مغربية: تفسير نصوص، مبادئ قضائية، ومقالات موضوعية.</p>",
        '<ul class="seo-links">',
    ]
    for r in rows:
        label = r["title"]
        meta_bits = []
        if r["category_name"]:
            meta_bits.append(_esc(r["category_name"]))
        if r["published_at"]:
            meta_bits.append(_esc(r["published_at"][:10]))
        suffix = f" ({', '.join(meta_bits)})" if meta_bits else ""
        bits.append(f'<li><a href="/blog/{r["id"]}">{_esc(label)}</a>{suffix}</li>')
    bits.append("</ul>")
    return "".join(bits), "مدوّنة نبراس القانونية", \
           {"description": "مقالات وشروحات قانونية مغربية من نبراس: تفسير النصوص، مبادئ قضائية، ودراسات موضوعية."}


# ---------------------------------------------------------------------------
# الراوتر الداخلي لصفحات SEO
# ---------------------------------------------------------------------------

def render_seo(path):
    """يردّ على مسار داخلي (بدون مخطط الوصف) بصفحة HTML أو None."""
    if not path:
        return None
    path = "/" + path.lstrip("/")
    path = path.split("?")[0]
    if path in ("/", "/index.html"):
        content, title, meta = _home_page()
        return _inject(title, meta["description"], "/", content,
                       jsonld_blocks=meta.get("jsonld", []))

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

    if path == "/generator":
        content, title, meta = _list_generator()
        return _inject(title, meta["description"], "/generator", content)

    m = re.match(r"^/generator/template/([^/]+)$", path)
    if m:
        content, title, meta = _template_page(m.group(1))
        if content is None:
            return None
        return _inject(title, meta["description"], meta["path"], content,
                       jsonld_blocks=meta.get("jsonld", []))

    m = re.match(r"^/blog/(\d+)$", path)
    if m:
        content, title, meta = _blog_page(int(m.group(1)))
        if content is None:
            return None
        return _inject(title, meta["description"], meta["path"], content,
                       jsonld_blocks=meta.get("jsonld", []))

    if path == "/blog":
        content, title, meta = _list_blog()
        return _inject(title, meta["description"], "/blog", content)

    m = re.match(r"^/domains/([^/]+)$", path)
    if m:
        page = _domain_page(m.group(1))
        if page is None:
            return None
        content, title, meta = page
        return _inject(title, meta["description"], path, content)

    if path == "/about":
        content, title, meta = _about_page()
        return _inject(title, meta["description"], "/about", content)
    if path == "/contact":
        content, title, meta = _contact_page()
        return _inject(title, meta["description"], "/contact", content)

    legal_pages = {"/privacy", "/terms", "/cookie-policy", "/disclaimer", "/guide"}
    if path in legal_pages:
        content, title, meta = _legal_ssr(path)
        return _inject(title, meta["description"], path, content)

    return None


# ---------------------------------------------------------------------------
# Sitemaps
# ---------------------------------------------------------------------------

def _sitemap_urls(rows, base):
    site = _base_url()
    out = []
    for r in rows:
        out.append(f"    <url><loc>{_esc(site + base + str(r[0]))}</loc></url>")
    return "".join(out)


def sitemap_index():
    site = _base_url()
    urls = [
        {"loc": f"{site}/sitemaps/main.xml", "changefreq": "daily"},
        {"loc": f"{site}/sitemaps/laws.xml", "changefreq": "weekly"},
        {"loc": f"{site}/sitemaps/jurisprudence.xml", "changefreq": "weekly"},
        {"loc": f"{site}/sitemaps/procedures.xml", "changefreq": "monthly"},
        {"loc": f"{site}/sitemaps/blog.xml", "changefreq": "weekly"},
        {"loc": f"{site}/sitemaps/documents.xml", "changefreq": "weekly"},
        {"loc": f"{site}/sitemap.xml", "changefreq": "daily"},
    ]
    # التقسيم عبر صفحات سايت ماب فرعية
    index = ["<?xml version='1.0' encoding='UTF-8'?>",
             "<sitemapindex xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"]
    for u in urls[:-1]:
        index.append(f"<sitemap><loc>{_esc(u['loc'])}</loc><changefreq>{u['changefreq']}</changefreq></sitemap>")
    index.append("</sitemapindex>")
    return "".join(index)


def _lastmod(v):
    """تاريخ YYYY-MM-DD من قيمة قابلة للقراءة (None ⟹ إفراغ = تجاهل lastmod)."""
    s = str(v or "").strip()
    return _esc(s[:10]) if s else ""


def sitemap_main():
    """الصفحات الثابتة الرئيسية + صفحات الثقة (الخصوصية/الشروط/من نحن/اتصل بنا...)."""
    import datetime as _dt
    today = _dt.date.today().isoformat()
    site = _base_url()
    body = ["<?xml version='1.0' encoding='UTF-8'?>",
            "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"]
    for path in ("/", "/about", "/contact", "/privacy", "/terms",
                 "/cookie-policy", "/disclaimer", "/guide", "/generator"):
        body.append(f"<url><loc>{site}{path}</loc><lastmod>{today}</lastmod>"
                    "<changefreq>monthly</changefreq>"
                    "<priority>0.8</priority></url>")
    body.append("</urlset>")
    return "".join(body)


def sitemap_laws():
    site = _base_url()
    with db_session() as conn:
        rows = conn.execute(
            "SELECT id, COALESCE(updated_at, last_amended, enacted_date) AS lm "
            "FROM legal_texts ORDER BY id").fetchall()
    body = ["<?xml version='1.0' encoding='UTF-8'?>",
            "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"]
    for i, lm in rows:
        lastmod = f"<lastmod>{_lastmod(lm)}</lastmod>" if (lm and str(lm).strip()) else ""
        body.append(f"<url><loc>{site}/laws/{i}</loc>{lastmod}</url>")
    body.append("</urlset>")
    return "".join(body)


def sitemap_jurisprudence():
    site = _base_url()
    with db_session() as conn:
        rows = conn.execute(
            "SELECT id, COALESCE(decision_date, updated_at, created_at) AS lm "
            "FROM jurisprudence WHERE published=1 ORDER BY id").fetchall()
    body = ["<?xml version='1.0' encoding='UTF-8'?>",
            "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"]
    for i, lm in rows:
        lastmod = f"<lastmod>{_lastmod(lm)}</lastmod>" if (lm and str(lm).strip()) else ""
        body.append(f"<url><loc>{site}/jurisprudence/{i}</loc>{lastmod}</url>")
    body.append("</urlset>")
    return "".join(body)


def sitemap_procedures():
    site = _base_url()
    with db_session() as conn:
        slugs = [r[0] for r in conn.execute("SELECT slug FROM procedures ORDER BY slug").fetchall()]
    body = ["<?xml version='1.0' encoding='UTF-8'?>",
            "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"]
    for s in slugs:
        body.append(f"<url><loc>{site}/procedures/{_esc(s)}</loc></url>")
    body.append("</urlset>")
    return "".join(body)


def sitemap_blog():
    """مقالات المدوّنة المنشورة فقط، مع lastmod من آخر تحديث/نشر."""
    site = _base_url()
    with db_session() as conn:
        rows = conn.execute(
            "SELECT id, COALESCE(updated_at, published_at) AS lm "
            "FROM blog_articles WHERE status='published' ORDER BY id").fetchall()
    body = ["<?xml version='1.0' encoding='UTF-8'?>",
            "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"]
    for i, lm in rows:
        lastmod = f"<lastmod>{_lastmod(lm)}</lastmod>" if (lm and str(lm).strip()) else ""
        body.append(f"<url><loc>{site}/blog/{i}</loc>{lastmod}</url>")
    body.append("</urlset>")
    return "".join(body)


def sitemap_documents():
    """صفحات قوالب مولد العقود الموصى بها (SSR) في documents.xml."""
    from . import generator as _gen
    site = _base_url()
    templates = _gen.recommended_templates()
    body = ["<?xml version='1.0' encoding='UTF-8'?>",
            "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"]
    for t in templates:
        tid = t.get("id")
        if not tid:
            continue
        body.append(f"<url><loc>{site}/generator/template/{_esc(tid)}</loc>"
                    "<changefreq>monthly</changefreq></url>")
    body.append("</urlset>")
    return "".join(body)
