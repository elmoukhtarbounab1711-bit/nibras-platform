// نبراس — الاجتهادات القضائية: بحث نصي كامل بالكلمة + فئات + قائمة + تفصيل
import { tr, currentLang } from "../i18n.js";
import { api } from "../api.js";
import { el, esc, truncate, emptyState, pagination, fmtDate, toast } from "../ui.js";
import { icon } from "../icons.js";
import { navigate } from "../router.js";
import { createAdPlaceholder } from "../components/ads.js";

const PER_PAGE = 12;

/* أيقونة لكل فئة اجتهاد (slug → icon) */
const CAT_META = {
  madani: ["book"],
  jinai: ["shield"],
  idari: ["building"],
  aqari: ["mapPin"],
  usra: ["heart"],
  tijari: ["shoppingCart"],
  "mcostara-madaniya": ["scale"],
  "mcostara-jinaiya": ["shield"],
  shari3a: ["clipboard"],
  dariba: ["creditCard"],
  mnawaa: ["file"],
};
const catIconOf = (slug) => (CAT_META[slug] || ["book"])[0];

/* الصفحة الرئيسية: Hero + فئات + أحدث الاجتهادات، ومع الفئة/البحث → قائمة نتائج */
export async function jurisprudenceView(params) {
  const page = Math.max(1, parseInt(params.page || "1", 10) || 1);
  const activeCat = params.category || "";
  const q = params.q || "";

  const [cats, data, stats] = await Promise.all([
    api.get("/api/jurisprudence/categories"),
    q
      ? api.get(`/api/jurisprudence/search?q=${encodeURIComponent(q)}${activeCat ? `&category=${encodeURIComponent(activeCat)}` : ""}&limit=${PER_PAGE}&offset=${(page - 1) * PER_PAGE}`)
      : api.get(`/api/jurisprudence?limit=${PER_PAGE}&offset=${(page - 1) * PER_PAGE}${activeCat ? `&category=${encodeURIComponent(activeCat)}` : ""}`),
    api.get("/api/jurisprudence/stats"),
  ]);

  let decisions = [], total = 0;
  if (q) {
    decisions = Array.isArray(data) ? data : (data.results || []);
    total = (Array.isArray(data) ? decisions.length : (data.total ?? data.count ?? 0));
  } else {
    decisions = Array.isArray(data) ? data : (data.decisions || []);
    total = Array.isArray(data) ? decisions.length : (data.count ?? 0);
  }

  const cat = cats.find((c) => c.slug === activeCat);

  // ---------- Hero + بحث ----------
  const hero = el("section", { class: "lib-hero" }, [
    el("div", { class: "hero-bg" }),
    el("span", { class: "hero-crown" }, [icon("scale", 30)]),
    el("span", { class: "hero-eyebrow" }, [icon("book", 15), tr("jurisEyebrow")]),
    el("h1", { text: tr("jurisTitle") }),
    el("p", { class: "hero-sub", text: tr("jurisSub") }),
    el("div", { class: "lib-search" }, [
      el("div", { class: "search-field" }, [
        icon("search", 18),
        el("input", {
          type: "search",
          placeholder: tr("jurisSearchPh"),
          id: "juris-search-input",
          value: q,
          onkeydown: (e) => { if (e.key === "Enter") goSearch(e.target.value); },
        }),
        el("button", {
          class: "search-btn", type: "button", title: tr("search"),
          onclick: () => goSearch(document.getElementById("juris-search-input")?.value),
        }, [icon("search", 20)]),
      ]),
    ]),
  ]);

  const statsDef = [
    { n: stats.decisions ?? 0, l: tr("jurisStatsDecisions"), i: "scale" },
    { n: cats.length, l: tr("jurisStatsCategories"), i: "folder" },
    { n: stats.last_update ? fmtDate(stats.last_update, currentLang()) : "—", l: tr("jurisStatsUpdated"), i: "clock" },
  ];
  const statsRow = el("div", { class: "stats-row" }, statsDef.map((s) =>
    el("div", { class: "stat-chip" }, [
      el("div", { class: "sc-icon" }, [icon(s.i, 22)]),
      el("div", { style: "line-height:1.25" }, [
        el("div", { class: "sc-num", text: String(s.n) }),
        el("div", { class: "sc-lbl", text: s.l }),
      ]),
    ])));

  // ---------- Sidebar الفئات ----------
  const catList = el("aside", { class: "lib-side" }, [
    el("div", { class: "side-card" }, [
      el("h3", {}, [el("span", { class: "sl-dot", style: "display:grid;place-items:center" }, [icon("folder", 16)]), tr("jurisCategories")]),
      ...cats.map((c) =>
        el("a", {
          class: "side-link",
          href: `#/jurisprudence/cat/${c.slug}`,
          style: activeCat === c.slug ? "background:var(--gold-soft, rgba(200,155,60,.12))" : "",
        }, [
          el("span", { class: "sl-dot" }, [icon(catIconOf(c.slug), 15)]),
          el("span", { style: "flex:1" }, [el("span", { text: c.name })]),
          el("span", { class: "small muted", text: `(${c.decision_count ?? 0})` }),
        ])),
    ]),
    createAdPlaceholder("library_sidebar"),
  ]);

  // ---------- المحتوى الرئيسي ----------
  let main;
  if (q) {
    main = el("div", { class: "lib-main" }, [
      el("div", { class: "lib-section-title" }, [el("span", { class: "lst-rule" }), `${tr("search")}: ${q}`]),
      el("p", { class: "small muted mb-16", text: `${total} ${tr("jurisResultCount")}` }),
      decisions.length
        ? el("div", { class: "juris-list" }, decisions.map(decisionCard))
        : emptyState(tr("noResults"), "scale"),
      pagination(total, page, PER_PAGE, (p) =>
        navigate(`/jurisprudence/q/${encodeURIComponent(q)}${p > 1 ? `/page/${p}` : ""}`)),
    ]);
  } else if (activeCat) {
    main = el("div", { class: "lib-main" }, [
      el("div", { class: "lib-section-title" }, [el("span", { class: "lst-rule" }), cat ? cat.name : activeCat]),
      decisions.length
        ? el("div", { class: "juris-list" }, decisions.map(decisionCard))
        : emptyState(tr("noResults"), "scale"),
      pagination(total, page, PER_PAGE, (p) =>
        navigate(`/jurisprudence/cat/${encodeURIComponent(activeCat)}${p > 1 ? `/page/${p}` : ""}`)),
    ]);
  } else {
    main = el("div", { class: "lib-main" }, [
      el("div", { class: "lib-section-title" }, [el("span", { class: "lst-rule" }), tr("jurisLatest")]),
      el("p", { class: "small muted mb-16", text: tr("jurisLatestSub") }),
      decisions.length
        ? el("div", { class: "juris-list" }, decisions.map(decisionCard))
        : emptyState(tr("noResults"), "scale"),
      pagination(total, page, PER_PAGE, (p) => navigate(`/jurisprudence${p > 1 ? `/page/${p}` : ""}`)),
    ]);
  }

  return el("div", { class: "lib-page" }, [
    hero,
    el("div", { class: "lib-divider", "aria-hidden": "true" }, [
      el("span", { class: "ld-line" }),
      el("span", { class: "ld-mark" }, [icon("scale", 16)]),
      el("span", { class: "ld-line" }),
    ]),
    statsRow,
    el("div", { class: "lib-layout" }, [main, catList]),
  ]);

  function goSearch(v) {
    v = (v || "").trim();
    if (v) navigate(`/jurisprudence/q/${encodeURIComponent(v)}`);
    else navigate("/jurisprudence");
  }
}

/* بطاقة اجتهاد (في قوائم الفئة/البحث/الأحدث) */
function decisionCard(d) {
  return el("article", { class: "law-card card-hover" }, [
    el("div", { class: "law-ic" }, [icon("scale", 20)]),
    el("div", { class: "law-body" }, [
      el("div", { class: "flex-between mb-8" }, [
        d.category_name ? el("span", { class: "badge-pill badge-navy", text: d.category_name }) : null,
        el("span", { class: "small muted", text: d.decision_date ? fmtDate(d.decision_date, currentLang()) : "" }),
      ]),
      el("h3", { class: "card-title" },
        el("a", { href: `#/jurisprudence/${d.id}`, text: d.title || tr("jurisUntitled") })),
      d.highlighted
        ? el("p", { class: "small muted srch-sum", html: d.highlighted })
        : (d.principles ? el("p", { class: "small muted", text: esc(truncate(d.principles, 110)) }) : null),
      el("div", { class: "flex-between mt-8" }, [
        el("div", { class: "flex", style: "gap:8px" }, [
          d.court ? el("span", { class: "small muted", text: d.court }) : null,
          d.decision_number ? el("span", { class: "small muted", text: `#${d.decision_number}` }) : null,
        ]),
        el("button", { class: "btn btn-outline btn-sm", text: tr("view"), onclick: () => navigate(`/jurisprudence/${d.id}`) }),
      ]),
    ]),
  ]);
}

/* تفصيل قرار: المحكمة + رقم/تاريخ + مبدأ + النص الكامل + المصدر */
export async function jurisprudenceDetailView(params) {
  const box = el("div", { class: "card" });
  const node = el("div", { class: "view-pad" });
  box.append(node);
  try {
    const d = await api.get(`/api/jurisprudence/${params.id}`);
    const backBtn = el("button", {
      class: "btn btn-ghost btn-sm mb-16", text: `← ${tr("back")}`,
      onclick: () => navigate(d.category_slug ? `/jurisprudence/cat/${d.category_slug}` : "/jurisprudence"),
    });
    const header = el("div", { class: "flex-between mb-8" }, [
      el("span", { class: "badge-pill badge-navy", text: d.category_name || "" }),
      el("span", { class: "small muted", text: `${d.views ?? 0} ${tr("jurisViews")}` }),
    ]);
    const title = el("h1", { class: "doc-title", text: d.title });
    const meta = el("div", { class: "doc-meta" }, [
      d.court ? el("span", { class: "badge-pill badge-gold", text: d.court }) : null,
      d.decision_number ? el("span", { class: "badge-pill badge-blue", text: `${tr("jurisNr")} ${d.decision_number}` }) : null,
      d.decision_date ? el("span", { class: "badge-pill badge-gray", text: fmtDate(d.decision_date, currentLang()) }) : null,
    ]);
    const sections = [];
    if (d.principles) {
      sections.push(el("div", { class: "article-block" }, [
        el("div", { class: "section-head" }, [el("h2", { text: tr("jurisPrinciples") })]),
        el("div", { class: "art-content", text: d.principles }),
      ]));
    }
    sections.push(el("div", { class: "article-block" }, [
      el("div", { class: "section-head" }, [el("h2", { text: tr("jurisContent") })]),
      el("div", { class: "art-content", text: d.content }),
    ]));
    if (d.source_note) {
      sections.push(el("p", { class: "small muted", text: `${tr("jurisSource")}: ${d.source_note}` }));
    }
    const downloadBtn = d.pdf_url
      ? el("a", { class: "btn btn-gold btn-sm mt-16", href: d.pdf_url, target: "_blank", rel: "noopener" }, [
          icon("download", 16), " " + tr("jurisDownloadPdf"),
        ])
      : null;
    const more = el("div", { class: "flex", style: "gap:8px;flex-wrap:wrap" }, [
      downloadBtn,
      el("a", { class: "btn btn-ghost btn-sm mt-16", href: "#/jurisprudence", text: tr("jurisMore") }),
    ]);
    node.append(backBtn, header, title, meta, ...sections, more, createAdPlaceholder("article_bottom"));
  } catch (e) {
    node.append(el("div", { class: "card empty" }, [
      el("div", { class: "empty-icon" }, [icon("alertTriangle", 30)]),
      tr("jurisNotFound"),
    ]));
  }
  return box;
}