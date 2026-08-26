// نبراس — المكتبة القانونية: لوحة (Hero + إحصاءات + تصنيفات + Sidebar) + قائمة نصوص + تفصيل + PDF
import { tr, currentLang } from "../i18n.js";
import { api } from "../api.js";
import { el, esc, emptyState, fmtDate, pagination, typeLabel, downloadFile, toast } from "../ui.js";
import { icon } from "../icons.js";
import { navigate } from "../router.js";
import { createAdPlaceholder } from "../components/ads.js";

const PER_PAGE = 12;

/* خريطة أيقونة لكل تصنيف (slug → [icon]) — اللون موحّد عبر النظام اللوني
   للهوية (navy-grad + gold-light) في CSS، لا ألوان cat-* متعددة. */
const CAT_META = {
  dostouri: ["star"],
  madani: ["book"],
  usra: ["heart"],
  jinai: ["shield"],
  shughl: ["clipboard"],
  tijari: ["shoppingCart"],
  moustara: ["file"],
  thaqafa: ["megaphone"],
  raqami: ["cpu"],
  filaha: ["globe"],
  qawanin: ["bookOpen"],
  diniya: ["compass"],
  taqa: ["zap"],
  biaa: ["globe"],
  dawli: ["globe"],
  ijtimai: ["users"],
  tarbiya: ["graduationCap"],
  marasim: ["file"],
  "dhawahir-kanun": ["file"],
  qararat: ["file"],
  naql: ["compass"],
  dhawahir: ["file"],
  madan_k: ["book"],
  mali: ["creditCard"],
  sihha: ["heart"],
  huquq: ["flag"],
  aqari: ["mapPin"],
  "qawanin-tanthim": ["clipboard"],
  iqtisadi: ["trendingUp"],
  "marasim-malakiya": ["flag"],
  qadhai: ["building"],
  idari: ["building"],
  mihan: ["idCard"],
  intikhab: ["checkCircle"],
  muassasat: ["building"],
};
const catMeta = (slug) => CAT_META[slug] || ["book"];

export async function libraryView(params) {
  const page = Math.max(1, parseInt(params.page || "1", 10) || 1);
  const activeCat = params.category || "";
  const q = params.q || "";

  // المسار الأساسي (/library) → لوحة التصميم الجديدة
  if (!q && !activeCat && page === 1) {
    return dashboardView();
  }

  const [cats, data] = await Promise.all([
    api.get("/api/categories"),
    api.get(q
      ? `/api/search?q=${encodeURIComponent(q)}`
      : `/api/texts?limit=${PER_PAGE}&offset=${(page - 1) * PER_PAGE}${activeCat ? `&category=${encodeURIComponent(activeCat)}` : ""}`),
  ]);

  let texts = [], total = 0;
  if (q) {
    const res = Array.isArray(data) ? data : (data.results || []);
    // تجميع نتائج البحث: نأخذ المادة الأولى من كل نص قانوني لتفادي تكرار النصوص
    const seen = new Set();
    texts = res.filter((r) => { const k = r.legal_text_id; if (k == null || seen.has(k)) return false; seen.add(k); return true; }).map((r) => ({
      id: r.legal_text_id, title: r.legal_text_title || r.title || "", type: r.text_type || "law",
      category_name: r.category_name || "", official_ref: r.official_ref || "",
      description: r.content || "", article_count: null,
    }));
    total = texts.length;
  } else {
    texts = Array.isArray(data) ? data : data.texts || [];
    total = Array.isArray(data) ? texts.length : (data.count ?? 0);
  }

  const cat = cats.find((c) => c.slug === activeCat);
  const [ic] = cat ? catMeta(activeCat) : ["search"];

  // بنر احترافي للفئة / البحث
  const banner = el("section", { class: "lib-cat-banner" }, [
    el("div", { class: "hero-bg" }),
    el("div", { class: "lcb-inner" }, [
      el("button", { class: "lcb-back", type: "button", onclick: () => navigate("/library") }, [icon("arrowLeft", 16), tr("back")]),
      el("div", { class: "lcb-ic", style: `color:var(--gold); background:linear-gradient(135deg, rgba(200,155,60,.25), rgba(200,155,60,.08))` }, [icon(ic, 30)]),
      el("div", { class: "lcb-text" }, [
        el("div", { class: "lcb-eyebrow", text: cat ? tr("libCategoriesTitle") : tr("search") }),
        el("h1", { text: cat ? cat.name : `"${q}"` }),
        el("p", { class: "lcb-sub", text: q ? `${total} ${tr("materials")}` : `${total} ${tr("libStatsTexts")}` }),
      ]),
    ]),
  ]);

  const searchBox = el("div", { class: "search-bar" }, [
    el("input", { type: "search", placeholder: tr("search"), value: q,
      onkeydown: (e) => { if (e.key === "Enter") navigate(`/library/q/${encodeURIComponent(e.target.value)}`); } }),
    el("button", { class: "btn btn-primary", text: tr("search"), onclick: () => navigate(`/library/q/${encodeURIComponent(searchBox.querySelector("input").value)}`) }),
  ]);

  const grid = texts.length ? el("div", { class: "grid grid-3" }, texts.map((t) =>
    el("article", { class: "law-card card-hover" }, [
      el("div", { class: "law-ic" }, [icon("file", 20)]),
      el("div", { class: "law-body" }, [
        el("div", { class: "flex-between mb-8" }, [
          el("span", { class: "badge-pill badge-navy", text: typeLabel(t.type, currentLang()) }),
          t.category_name ? el("span", { class: "small muted", text: t.category_name }) : null,
        ]),
        el("h3", { class: "card-title" }, el("a", { href: `#/text/${t.id}`, text: t.title })),
        t.description ? el("p", { class: "small muted", text: esc(truncate(t.description, 100)) }) : null,
        el("div", { class: "flex-between mt-8" }, [
          el("span", { class: "small muted", text: t.official_ref || fmtDate(t.enacted_date, currentLang()) }),
          el("div", { class: "flex", style: "gap:8px" }, [
            el("button", { class: "btn btn-ghost btn-sm", onclick: () => downloadFile(`/api/texts/${t.id}/pdf?download=1`, `${t.title || 'law'}.pdf`), title: tr("download") }, [icon("download", 14)]),
            el("button", { class: "btn btn-outline btn-sm", text: tr("view"), onclick: () => navigate(`/text/${t.id}`) }),
          ]),
        ]),
      ]),
    ]))) : emptyState(tr("noResults"), "book");

  return el("div", {}, [
    banner,
    searchBox,
    grid,
    pagination(total, page, PER_PAGE, (p) =>
      navigate(`/library${activeCat ? `/cat/${activeCat}` : ""}${q ? `/q/${encodeURIComponent(q)}` : ""}${p > 1 ? `/page/${p}` : ""}`)),
  ]);
}

/* ---------- لوحة المكتبة الجديدة (Dashboard) ---------- */
async function dashboardView() {
  const [cats, stats] = await Promise.all([
    api.get("/api/categories"),
    api.get("/api/library/stats"),
  ]);

  const now = new Date();
  const lastDate = stats.last_update ? new Date(stats.last_update) : now;
  const isToday = lastDate.toDateString() === now.toDateString();

  const hero = el("section", { class: "lib-hero" }, [
    el("div", { class: "hero-bg" }),
    el("span", { class: "hero-crown" }, [icon("crown", 30)]),
    el("span", { class: "hero-eyebrow" }, [icon("shield", 15), tr("libEyebrow")]),
    el("h1", { text: tr("libHeroTitle") }),
    el("p", { class: "hero-sub", text: tr("libHeroSub") }),
    el("div", { class: "lib-search" }, [
      el("div", { class: "search-field" }, [
        icon("search", 18),
        el("input", {
          type: "search",
          placeholder: tr("libSearchPh"),
          id: "lib-search-input",
          onkeydown: (e) => { if (e.key === "Enter") navigate(`/library/q/${encodeURIComponent(e.target.value.trim())}`); },
        }),
        el("button", { class: "search-btn", type: "button", title: tr("search"),
          onclick: () => {
            const v = document.getElementById("lib-search-input").value.trim();
            if (v) navigate(`/library/q/${encodeURIComponent(v)}`);
          } }, [icon("search", 20)]),
      ]),
      el("button", { class: "advanced-btn", onclick: () => navigate("/library") }, tr("libAdvanced")),
    ]),
  ]);

  const statCards = [
    { n: stats.categories ?? cats.length, l: tr("libStatsCategories"), i: "folder" },
    { n: stats.texts ?? 0, l: tr("libStatsTexts"), i: "book" },
    { n: stats.articles ?? 0, l: tr("libStatsArticles"), i: "file" },
    { n: stats.decisions ?? 0, l: tr("libStatsDecisions"), i: "clipboard" },
    { n: isToday ? tr("libStatsToday") : fmtDate(stats.last_update, currentLang()), l: tr("libStatsUpdated"), i: "clock" },
  ];
  const statsRow = el("div", { class: "stats-row" }, statCards.map((s) =>
    el("div", { class: "stat-chip" }, [
      el("div", { class: "sc-icon" }, [icon(s.i, 22)]),
      el("div", { style: "line-height:1.25" }, [
        el("div", { class: "sc-num", text: String(s.n) }),
        el("div", { class: "sc-lbl", text: s.l }),
      ]),
    ])));

  const catCards = cats.length ? el("div", { class: "cat-grid" }, cats.map((c, idx) => {
    const [ic] = catMeta(c.slug);
    return el("button", { class: "cat-card", type: "button", style: `animation-delay:${(idx % 12) * 40}ms`,
      onclick: () => navigate(`/library/cat/${c.slug}`) }, [
      el("span", { class: "cc-arrow" }, [icon("arrowLeft", 14)]),
      el("div", { class: "cc-icon" }, [icon(ic, 20)]),
      el("div", { class: "cc-name", text: c.name }),
      el("div", { class: "cc-count", text: `(${c.text_count ?? 0})` }),
    ]);
  })) : emptyState(tr("noResults"), "book");

  const exploreList = [
    { label: tr("libExploreNew"), i: "plus", href: "/library" },
    { label: tr("libExplorePopular"), i: "eye", href: "/library" },
    { label: tr("libExploreFavs"), i: "heart", href: "/profile" },
    { label: tr("libExploreUpdates"), i: "clock", href: "/library" },
  ];
  const exploreCard = el("div", { class: "side-card" }, [
    el("h3", {}, [el("span", { class: "sl-dot", style: "display:grid;place-items:center" }, [icon("compass", 16)]), tr("libExploreTitle")]),
    ...exploreList.map((x) =>
      el("a", { class: "side-link", href: `#${x.href}` }, [
        el("span", { class: "sl-dot" }, [icon(x.i, 15)]),
        x.label,
      ])),
  ]);

  const typeList = [
    { label: tr("libTypeBasic"), i: "star", href: "/library/cat/dostouri" },
    { label: tr("libTypeCodes"), i: "book", href: "/library/cat/madan_k" },
    { label: tr("libTypeDahirs"), i: "file", href: "/library/cat/dhawahir" },
    { label: tr("libTypeDecisions"), i: "clipboard", href: "/library/cat/qararat" },
    { label: tr("libTypeSpecial"), i: "cpu", href: "/library" },
  ];
  const typeCard = el("div", { class: "side-card" }, [
    el("h3", {}, [el("span", { class: "sl-dot", style: "display:grid;place-items:center" }, [icon("folder", 16)]), tr("libByTypeTitle")]),
    ...typeList.map((x) =>
      el("a", { class: "side-link", href: `#${x.href}` }, [
        el("span", { class: "sl-dot" }, [icon(x.i, 15)]),
        x.label,
      ])),
  ]);

  const aiCard = el("div", { class: "side-card side-ai" }, [
    el("div", { class: "ai-orb" }, [icon("messageCircle", 30)]),
    el("h3", { text: tr("libAiTitle") }),
    el("p", { text: tr("libAiText") }),
    el("button", { class: "ai-cta", onclick: () => navigate("/assistant") }, "✨ " + tr("libAiCta")),
  ]);

  const sidebar = el("aside", { class: "lib-side" }, [exploreCard, typeCard, aiCard, createAdPlaceholder("library_sidebar")]);

  const main = el("div", { class: "lib-main" }, [
    el("div", { class: "lib-section-title" }, [el("span", { class: "lst-rule" }), tr("libCategoriesTitle")]),
    catCards,
  ]);

  const trust = el("div", { class: "lib-trust" }, [
    el("span", { class: "lt-shield" }, [icon("shield", 20)]),
    tr("libTrust"),
  ]);

  return el("div", { class: "lib-page" }, [
    hero,
    el("div", { class: "lib-divider", "aria-hidden": "true" }, [
      el("span", { class: "ld-line" }),
      el("span", { class: "ld-mark" }, [icon("scale", 16)]),
      el("span", { class: "ld-line" }),
    ]),
    statsRow,
    el("div", { class: "lib-layout" }, [main, sidebar]),
    trust,
  ]);
}

export async function textView(params) {
  let text;
  try {
    text = await api.get(`/api/texts/${params.id}`);
  } catch (e) {
    return el("div", { class: "card empty" }, [
      el("div", { class: "empty-icon" }, [icon("alertTriangle", 40)]),
      el("div", { text: tr("error") }),
      el("div", { class: "small muted", text: String(e.message || e) }),
      el("button", { class: "btn btn-primary mt-16", text: tr("back"), onclick: () => navigate("/library") }),
    ]);
  }
  const articles = text.articles || [];
  const related = text.related || [];

  return el("article", { class: "article-view" }, [
    el("button", { class: "btn btn-ghost btn-sm mb-16", text: `← ${tr("back")}`, onclick: () => navigate("/library") }),
    el("div", { class: "flex-between mb-8" }, [
      el("span", { class: "badge-pill badge-navy", text: typeLabel(text.type, currentLang()) }),
      el("span", { class: "badge-pill badge-gray", text: text.category_name || "" }),
    ]),
    el("h1", { class: "doc-title", text: text.title }),
    el("div", { class: "doc-meta" }, [
      text.official_ref ? el("span", { class: "badge-pill badge-blue", text: text.official_ref }) : null,
      text.issuing_body ? el("span", { class: "badge-pill badge-gold", text: text.issuing_body }) : null,
      text.enacted_date ? el("span", { class: "badge-pill badge-gray", text: fmtDate(text.enacted_date, currentLang()) }) : null,
    ]),
    text.description ? el("div", { class: "doc-desc", text: text.description }) : null,
    text.source_note ? el("p", { class: "small muted", text: text.source_note }) : null,
    // ═══ معلومات المصدر الرسمي ═══
    el("div", { class: "source-meta mt-8", style: "padding:10px 14px;background:#f8f9fa;border-radius:8px;border:1px solid #e2e8f0;font-size:13px;" }, [
      el("div", { style: "font-weight:600;margin-bottom:6px;color:#1a365d;" }, [tr("officialSource") || "المصدر الرسمي"]),
      el("div", { style: "display:flex;flex-wrap:wrap;gap:8px;align-items:center;" }, [
        text.source_name ? el("span", { class: "badge-pill badge-blue", text: text.source_name }) : null,
        text.official_source ? el("span", { class: "badge-pill badge-green", text: "✓ " + (tr("verified") || "مصدر رسمي") }) : null,
        text.version_type ? el("span", { class: "badge-pill badge-gold", text: text.version_type === "ORIGINAL_OFFICIAL" ? (tr("originalOfficial") || "نص أصلي رسمي") : text.version_type }) : null,
        text.verification_status ? el("span", { class: `badge-pill ${text.verification_status === "VERIFIED" ? "badge-green" : "badge-gray"}`, text: text.verification_status === "VERIFIED" ? (tr("verified") || "محقق") : text.verification_status }) : null,
      ]),
      text.source_url ? el("div", { style: "margin-top:4px;" }, [
        el("a", { href: text.source_url, target: "_blank", rel: "noopener", style: "color:#2b6cb0;text-decoration:underline;" }, [tr("viewSource") || "عرض المصدر الأصلي ↗"]),
      ]) : null,
      text.imported_at ? el("div", { style: "margin-top:4px;color:#718096;font-size:12px;" }, [
        (tr("importedAt") || "تاريخ الاستيراد") + ": " + (text.imported_at || "").slice(0, 10),
      ]) : null,
    ]),

    el("div", { class: "pdf-toolbar mt-16" }, [
      el("button", { class: "btn btn-gold", onclick: () => navigate(`/pdf/${text.id}`) }, [icon("file", 16), " " + tr("viewPdf")]),
      el("button", { class: "btn btn-outline", onclick: () => downloadFile(`/api/texts/${text.id}/pdf?download=1`, `${text.title || 'law'}.pdf`) }, [icon("download", 16), " " + tr("download")]),
    ]),

    createAdPlaceholder("article_top"),

    articles.length ? el("div", { class: "mt-24" }, [
      el("h2", { class: "section-head", text: tr("materials") }),
      ...articles.map((a) => el("div", { class: "article-block" }, [
        el("div", { class: "flex-between" }, [
          el("span", { class: "art-no", text: a.label || `المادة ${a.number}` }),
          el("a", { class: "btn btn-ghost btn-sm", href: `#/pdf/${text.id}`, text: "PDF" }),
        ]),
        el("div", { class: "art-content", text: a.content }),
        a.plain_explanation ? el("div", { class: "art-plain", text: a.plain_explanation }) : null,
        a.keywords ? el("div", { class: "art-keywords" }, a.keywords.split(",").filter(Boolean).map((k) =>
          el("span", { class: "chip", text: k.trim() }))) : null,
      ])),
    ]) : emptyState(tr("noResults"), "bookOpen"),

    createAdPlaceholder("article_bottom"),

    related.length ? el("div", { class: "related" }, [
      el("h3", { text: "مواد ذات صلة" }),
      ...related.map((r) => el("a", { class: "flex mb-8", href: `#/text/${text.id}` }, [
        el("span", { class: "badge-pill badge-navy", text: r.number || "" }),
        el("span", { text: r.content ? esc(truncate(r.content, 90)) : r.label }),
      ])),
    ]) : null,
  ]);
}

function truncate(s, n) {
  s = String(s || "");
  return s.length > n ? s.slice(0, n).trimEnd() + "…" : s;
}

export async function pdfView(params) {
  const textId = params.id;
  const frame = el("div", { class: "pdf-frame" });

  const toolbar = el("div", { class: "pdf-toolbar" }, [
    el("button", { class: "btn btn-ghost btn-sm", id: "pdf-back", text: `← ${tr("back")}` }),
    el("div", { class: "pdf-toolbar-group" }, [
      el("button", { class: "icon-btn", id: "pdf-prev", title: tr("prev"), text: "‹", style: "color:var(--ink)" }),
      el("span", { id: "pdf-page", class: "small muted", text: "1 / 1" }),
      el("button", { class: "icon-btn", id: "pdf-next", title: tr("next"), text: "›", style: "color:var(--ink)" }),
    ]),
    el("div", { class: "pdf-toolbar-sep" }),
    el("div", { class: "pdf-toolbar-group" }, [
      el("button", { class: "icon-btn", id: "pdf-zoom-out", title: tr("zoomOut"), text: "−", style: "color:var(--ink)" }),
      el("span", { id: "pdf-zoom", class: "small muted", text: "100%" }),
      el("button", { class: "icon-btn", id: "pdf-zoom-in", title: tr("zoomIn"), text: "+", style: "color:var(--ink)" }),
      el("button", { class: "btn btn-ghost btn-sm", id: "pdf-fit", text: tr("fitWidth") }),
    ]),
    el("div", { class: "pdf-toolbar-sep" }),
    el("button", { class: "icon-btn", id: "pdf-search-toggle", title: tr("search"), style: "color:var(--ink)" }, [icon("search", 18)]),
    el("button", { class: "icon-btn", id: "pdf-fullscreen", title: tr("fullscreen") || "ملء الشاشة", style: "color:var(--ink)" }, [icon("maximize", 18)]),
    el("span", { style: "flex:1" }),
    el("div", { class: "pdf-toolbar-group pdf-find-bar", id: "pdf-find-bar", style: "display:none" }, [
      el("input", { id: "pdf-find", type: "search", placeholder: tr("pdfSearchPh"), style: "width:180px;padding:7px 12px;border:1px solid var(--line);border-radius:8px;background:var(--surface);color:var(--ink)" }),
      el("button", { class: "icon-btn", id: "pdf-find-prev", title: tr("prev"), text: "‹", style: "color:var(--ink)" }),
      el("button", { class: "icon-btn", id: "pdf-find-next", title: tr("next"), text: "›", style: "color:var(--ink)" }),
      el("span", { id: "pdf-find-count", class: "small muted" }),
    ]),
    el("button", { class: "btn btn-gold btn-sm", id: "pdf-share" }, [icon("link", 16), " " + tr("share")]),
    el("button", { class: "btn btn-outline btn-sm", id: "pdf-download" }, [icon("download", 16), " " + tr("download")]),
  ]);

  const scrollContainer = el("div", { class: "pdf-scroll-container", id: "pdf-scroll" });
  const progress = el("div", { class: "pdf-progress-bar", id: "pdf-progress" });
  frame.append(toolbar, scrollContainer, progress);

  let textData = null;
  try { textData = await api.get(`/api/texts/${textId}`); } catch {}

  const loadPdf = async () => {
    if (typeof pdfjsLib === "undefined") {
      try {
        await new Promise((resolve, reject) => {
          const s = document.createElement("script");
          s.src = "/vendor/pdfjs/pdf.min.js";
          s.onload = resolve;
          s.onerror = reject;
          document.head.appendChild(s);
        });
      } catch { showError("PDF.js غير محمّل."); return; }
      if (typeof pdfjsLib === "undefined") { showError("PDF.js غير محمّل."); return; }
    }
    try {
      pdfjsLib.GlobalWorkerOptions.workerSrc = "/vendor/pdfjs/pdf.worker.min.js";
    } catch {}

    const task = pdfjsLib.getDocument({
      url: `/api/texts/${textId}/pdf`,
      stopAtErrors: false,
      isEvalSupported: false,
    });
    task.onProgress = (p) => {
      if (p.total) {
        const pct = Math.min(100, Math.round((p.loaded / p.total) * 100));
        progress.style.width = pct + "%";
        progress.style.display = pct >= 100 ? "none" : "";
      }
    };
    return task.promise;
  };

  const showError = (msg) => {
    scrollContainer.innerHTML = `<div class="pdf-empty">${esc(msg || "تعذّر فتح الملف.")}</div>`;
  };

  const pdfDoc = await loadPdf();
  if (!pdfDoc) return frame;
  progress.style.display = "none";

  const totalPages = pdfDoc.numPages;
  let baseScale = 1.5;
  let currentScale = baseScale;
  let currentPage = 1;
  let renderedPages = new Map();
  let renderingPages = new Set();
  let searchText = "";
  let searchMatches = [];
  let searchIdx = -1;
  let destroyed = false;

  function destroy() { destroyed = true; }

  function getPageContainer(num) {
    let wrap = scrollContainer.querySelector(`[data-page="${num}"]`);
    if (!wrap) {
      wrap = el("div", { class: "pdf-page-wrap", "data-page": String(num) });
      wrap.innerHTML = `<div class="pdf-page-loading">${esc(tr("loading"))} ${num}</div>`;
      scrollContainer.appendChild(wrap);
    }
    return wrap;
  }

  async function renderPageToContainer(num) {
    if (destroyed || renderedPages.has(num) || renderingPages.has(num)) return;
    renderingPages.add(num);
    try {
      const page = await pdfDoc.getPage(num);
      if (destroyed) return;
      const viewport = page.getViewport({ scale: currentScale });
      const wrap = scrollContainer.querySelector(`[data-page="${num}"]`);
      if (!wrap) return;
      wrap.innerHTML = "";
      wrap.style.width = Math.floor(viewport.width) + "px";
      wrap.style.height = Math.floor(viewport.height) + "px";

      const canvas = document.createElement("canvas");
      canvas.width = Math.floor(viewport.width * (window.devicePixelRatio || 1));
      canvas.height = Math.floor(viewport.height * (window.devicePixelRatio || 1));
      canvas.style.width = Math.floor(viewport.width) + "px";
      canvas.style.height = Math.floor(viewport.height) + "px";
      const ctx = canvas.getContext("2d");
      ctx.scale(window.devicePixelRatio || 1, window.devicePixelRatio || 1);
      wrap.appendChild(canvas);

      const renderTask = page.render({ canvasContext: ctx, viewport });
      await renderTask.promise;
      if (destroyed) return;

      try {
        const textContent = await page.getTextContent();
        if (destroyed) return;
        const textLayer = el("div", { class: "pdf-text-layer" });
        const items = textContent.items.filter((it) => it.str);
        if (items.length) {
          const Y_TOL = 2;
          const lines = [];
          let curLine = { y: null, items: [] };
          items.forEach((item) => {
            const tx = pdfjsLib.Util.transform(textContent.transform, item.transform);
            const y = Math.round(tx[5] * 10) / 10;
            if (curLine.y === null || Math.abs(y - curLine.y) <= Y_TOL) {
              curLine.y = y;
              curLine.items.push({ tx, item });
            } else {
              lines.push(curLine);
              curLine = { y, items: [{ tx, item }] };
            }
          });
          lines.push(curLine);
          lines.forEach((line) => {
            line.items.sort((a, b) => b.tx[4] - a.tx[4]);
            const lineText = line.items.map((x) => x.item.str).join("");
            if (!lineText.trim()) return;
            const firstTx = line.items[0].tx;
            const lastItem = line.items[line.items.length - 1];
            const lineStartX = Math.min(...line.items.map((x) => x.tx[4]));
            const lineEndX = Math.max(...line.items.map((x) => x.tx[4] + (x.item.width || 0)));
            const fs = Math.hypot(firstTx[0], firstTx[1]);
            const span = document.createElement("span");
            span.textContent = lineText;
            span.style.left = lineStartX + "px";
            span.style.top = firstTx[5] - fs * 0.9 + "px";
            span.style.fontSize = fs + "px";
            span.style.width = Math.max(1, lineEndX - lineStartX) + "px";
            textLayer.appendChild(span);
          });
        }
        wrap.appendChild(textLayer);
      } catch {}

      renderedPages.set(num, { canvas, wrap });
    } catch (e) {
      if (e?.name !== "RenderingCancelledException") {
        const wrap = scrollContainer.querySelector(`[data-page="${num}"]`);
        if (wrap) wrap.innerHTML = `<div class="pdf-page-loading" style="color:#ef4444">${esc(tr("error"))} ${num}</div>`;
      }
    } finally {
      renderingPages.delete(num);
    }
  }

  const MARGIN = 3;
  function updateVisiblePages() {
    if (destroyed || !pdfDoc) return;
    const st = scrollContainer.scrollTop;
    const vh = scrollContainer.clientHeight;
    const lo = st - vh * MARGIN;
    const hi = st + vh * (1 + MARGIN);
    const children = scrollContainer.children;
    let nearPage = 1;
    for (let i = 0; i < children.length; i++) {
      const el = children[i];
      const mid = el.offsetTop + el.offsetHeight / 2;
      if (mid >= st && mid <= st + vh) { nearPage = parseInt(el.dataset.page) || 1; break; }
    }
    currentPage = nearPage;
    updatePageLabel();
    for (let i = 0; i < children.length; i++) {
      const child = children[i];
      const num = parseInt(child.dataset.page);
      if (!num) continue;
      const top = child.offsetTop;
      const bot = top + child.offsetHeight;
      if (bot >= lo && top <= hi) {
        if (!renderedPages.has(num) && !renderingPages.has(num)) renderPageToContainer(num);
      }
    }
  }

  function updatePageLabel() {
    const lbl = frame.querySelector("#pdf-page");
    if (lbl) lbl.textContent = `${currentPage} / ${totalPages}`;
    const zoomLbl = frame.querySelector("#pdf-zoom");
    if (zoomLbl) zoomLbl.textContent = `${Math.round(currentScale * 100)}%`;
    const prevBtn = frame.querySelector("#pdf-prev");
    const nextBtn = frame.querySelector("#pdf-next");
    if (prevBtn) prevBtn.disabled = currentPage <= 1;
    if (nextBtn) nextBtn.disabled = currentPage >= totalPages;
  }

  let scrollTimer = null;
  scrollContainer.addEventListener("scroll", () => {
    if (scrollTimer) cancelAnimationFrame(scrollTimer);
    scrollTimer = requestAnimationFrame(updateVisiblePages);
  }, { passive: true });

  function scrollToPage(num) {
    const wrap = scrollContainer.querySelector(`[data-page="${num}"]`);
    if (wrap) wrap.scrollIntoView({ behavior: "smooth", block: "start" });
    else {
      for (let i = Math.max(1, num - 2); i <= Math.min(totalPages, num + 2); i++) getPageContainer(i);
      updateVisiblePages();
      setTimeout(() => {
        const w = scrollContainer.querySelector(`[data-page="${num}"]`);
        if (w) w.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 100);
    }
  }

  async function rerenderAll() {
    renderedPages.clear();
    renderingPages.clear();
    scrollContainer.innerHTML = "";
    for (let i = 1; i <= totalPages; i++) getPageContainer(i);
    updateVisiblePages();
    updatePageLabel();
  }

  const prevBtn = frame.querySelector("#pdf-prev");
  const nextBtn = frame.querySelector("#pdf-next");
  const zoomIn = frame.querySelector("#pdf-zoom-in");
  const zoomOut = frame.querySelector("#pdf-zoom-out");
  const fitBtn = frame.querySelector("#pdf-fit");
  const backBtn = frame.querySelector("#pdf-back");
  const shareBtn = frame.querySelector("#pdf-share");
  const dlBtn = frame.querySelector("#pdf-download");
  const fsBtn = frame.querySelector("#pdf-fullscreen");
  const searchToggle = frame.querySelector("#pdf-search-toggle");
  const findBar = frame.querySelector("#pdf-find-bar");
  const findInput = frame.querySelector("#pdf-find");
  const findPrev = frame.querySelector("#pdf-find-prev");
  const findNext = frame.querySelector("#pdf-find-next");
  const findCount = frame.querySelector("#pdf-find-count");

  backBtn.onclick = () => navigate(`/text/${textId}`);

  dlBtn.onclick = () => downloadFile(`/api/texts/${textId}/pdf?download=1`, (textData?.title || `law-${textId}`) + ".pdf");

  shareBtn.onclick = async () => {
    const link = location.origin + `/pdf/${textId}`;
    try {
      if (navigator.share) await navigator.share({ title: textData?.title || "نبراس", url: link });
      else { await navigator.clipboard.writeText(link); toast(tr("copied"), "success"); }
    } catch { navigator.clipboard?.writeText(link); }
  };

  fsBtn.onclick = () => {
    if (document.fullscreenElement) document.exitFullscreen();
    else frame.requestFullscreen().catch(() => {});
  };

  prevBtn.onclick = () => { if (currentPage > 1) scrollToPage(currentPage - 1); };
  nextBtn.onclick = () => { if (currentPage < totalPages) scrollToPage(currentPage + 1); };

  zoomIn.onclick = () => { currentScale = Math.min(currentScale + 0.25, 4); rerenderAll(); };
  zoomOut.onclick = () => { currentScale = Math.max(currentScale - 0.25, 0.5); rerenderAll(); };
  fitBtn.onclick = () => { currentScale = baseScale; rerenderAll(); };

  searchToggle.onclick = () => {
    const visible = findBar.style.display !== "none";
    findBar.style.display = visible ? "none" : "";
    if (!visible) findInput.focus();
    else { findInput.value = ""; clearSearchHighlights(); }
  };

  function clearSearchHighlights() {
    scrollContainer.querySelectorAll(".pdf-search-hl").forEach((hl) => {
      const span = hl.parentNode;
      span.replaceChild(document.createTextNode(hl.textContent), hl);
      span.normalize();
    });
    searchMatches = [];
    searchIdx = -1;
    if (findCount) findCount.textContent = "";
  }

  async function runSearch(term) {
    clearSearchHighlights();
    if (!term || !pdfDoc) return;
    searchText = term;
    const lower = term.toLowerCase();
    for (let i = 1; i <= totalPages; i++) {
      try {
        const page = await pdfDoc.getPage(i);
        const tc = await page.getTextContent();
        tc.items.forEach((item) => {
          if (!item.str) return;
          let idx = item.str.toLowerCase().indexOf(lower);
          while (idx !== -1) {
            searchMatches.push({ page: i, charIdx: idx, len: term.length });
            idx = item.str.toLowerCase().indexOf(lower, idx + 1);
          }
        });
      } catch {}
    }
    if (searchMatches.length) {
      searchIdx = 0;
      findCount.textContent = `1/${searchMatches.length}`;
      scrollToSearchMatch();
    } else {
      findCount.textContent = tr("noResults");
      toast(tr("noResults"), "warn");
    }
  }

  function scrollToSearchMatch() {
    if (!searchMatches.length) return;
    const m = searchMatches[searchIdx];
    findCount.textContent = `${searchIdx + 1}/${searchMatches.length}`;
    scrollToPage(m.page);
  }

  findInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      if (e.shiftKey) { if (searchMatches.length) { searchIdx = (searchIdx - 1 + searchMatches.length) % searchMatches.length; scrollToSearchMatch(); } }
      else { if (searchMatches.length && searchText === findInput.value.trim()) { searchIdx = (searchIdx + 1) % searchMatches.length; scrollToSearchMatch(); } else runSearch(findInput.value.trim()); }
    }
    if (e.key === "Escape") { findBar.style.display = "none"; clearSearchHighlights(); }
    e.stopPropagation();
  });
  findPrev.onclick = () => { if (searchMatches.length) { searchIdx = (searchIdx - 1 + searchMatches.length) % searchMatches.length; scrollToSearchMatch(); } };
  findNext.onclick = () => { if (searchMatches.length) { searchIdx = (searchIdx + 1) % searchMatches.length; scrollToSearchMatch(); } };

  function onKey(e) {
    if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
    if (e.key === "ArrowLeft" || e.key === "ArrowUp") { e.preventDefault(); if (currentPage > 1) scrollToPage(currentPage - 1); }
    if (e.key === "ArrowRight" || e.key === "ArrowDown") { e.preventDefault(); if (currentPage < totalPages) scrollToPage(currentPage + 1); }
    if (e.key === "+" || e.key === "=") { e.preventDefault(); currentScale = Math.min(currentScale + 0.25, 4); rerenderAll(); }
    if (e.key === "-") { e.preventDefault(); currentScale = Math.max(currentScale - 0.25, 0.5); rerenderAll(); }
    if (e.key === "0") { e.preventDefault(); currentScale = baseScale; rerenderAll(); }
    if ((e.ctrlKey || e.metaKey) && e.key === "f") { e.preventDefault(); findBar.style.display = ""; findInput.focus(); }
  }
  document.addEventListener("keydown", onKey);
  frame.addEventListener("destroy", () => { document.removeEventListener("keydown", onKey); destroy(); });

  const BASE_CONTAINER_WIDTH = 820;
  function computeBaseScale() {
    const w = scrollContainer.clientWidth || 820;
    currentScale = baseScale = Math.min(3, Math.max(0.5, (w - 40) / BASE_CONTAINER_WIDTH * 1.5));
  }
  computeBaseScale();

  for (let i = 1; i <= Math.min(totalPages, 3); i++) getPageContainer(i);
  updateVisiblePages();
  updatePageLabel();

  return frame;
}

