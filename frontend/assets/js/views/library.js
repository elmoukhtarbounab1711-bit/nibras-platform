// نبراس — المكتبة القانونية: لوحة (Hero + إحصاءات + تصنيفات + Sidebar) + قائمة نصوص + تفصيل + PDF
import { tr, currentLang } from "../i18n.js";
import { api } from "../api.js";
import { el, esc, emptyState, fmtDate, pagination, typeLabel } from "../ui.js";
import { icon } from "../icons.js";
import { navigate } from "../router.js";

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
            el("a", { class: "btn btn-ghost btn-sm", href: `/api/texts/${t.id}/pdf?download=1`, download: true, title: tr("download") }, [icon("download", 14)]),
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

  const sidebar = el("aside", { class: "lib-side" }, [exploreCard, typeCard, aiCard]);

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
  const text = await api.get(`/api/texts/${params.id}`);
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

    el("div", { class: "pdf-toolbar mt-16" }, [
      el("button", { class: "btn btn-gold", onclick: () => navigate(`/pdf/${text.id}`) }, [icon("file", 16), " " + tr("viewPdf")]),
      el("a", { class: "btn btn-outline", href: `/api/texts/${text.id}/pdf?download=1`, download: true }, [icon("download", 16), " " + tr("download")]),
    ]),

    articles.length ? el("div", { class: "mt-24" }, [
      el("h2", { class: "section-head" }, [el("h2", { text: tr("materials") })]),
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
  const frame = el("div", { class: "card" });

  const toolbar = el("div", { class: "pdf-toolbar" }, [
    el("button", { class: "btn btn-ghost btn-sm", id: "pdf-back", text: `← ${tr("back")}` }),
    el("button", { class: "icon-btn", id: "pdf-prev", title: tr("prev"), text: "‹", style: "color:var(--ink)" }),
    el("span", { id: "pdf-page", class: "small muted", text: "1 / 1" }),
    el("button", { class: "icon-btn", id: "pdf-next", title: tr("next"), text: "›", style: "color:var(--ink)" }),
    el("span", { class: "divider-v" }),
    el("button", { class: "icon-btn", id: "pdf-zoom-out", title: tr("zoomOut"), text: "−", style: "color:var(--ink)" }),
    el("span", { id: "pdf-zoom", class: "small muted", text: "100%" }),
    el("button", { class: "icon-btn", id: "pdf-zoom-in", title: tr("zoomIn"), text: "+", style: "color:var(--ink)" }),
    el("button", { class: "btn btn-ghost btn-sm", id: "pdf-fit", text: tr("fitWidth") }),
    el("span", { style: "flex:1" }),
    el("input", { id: "pdf-find", type: "search", placeholder: tr("pdfSearchPh"), style: "width:180px;padding:7px 12px;border:1px solid var(--line);border-radius:8px;background:var(--surface);color:var(--ink)" }),
    el("button", { class: "btn btn-gold btn-sm", id: "pdf-share" }, [icon("link", 16), " " + tr("share")]),
    el("a", { class: "btn btn-outline btn-sm", href: `/api/texts/${textId}/pdf?download=1`, download: true }, [icon("download", 16), " " + tr("download")]),
  ]);
  const holder = el("div", { class: "pdf-viewer", id: "pdf-canvas-holder" }, [
    el("div", { class: "pdf-empty", text: tr("loading") }),
  ]);
  frame.append(toolbar, holder);

  queueMicrotask(() => {
    const pageLabel = toolbar.querySelector("#pdf-page");
    const prevBtn = toolbar.querySelector("#pdf-prev");
    const nextBtn = toolbar.querySelector("#pdf-next");
    const zoomIn = toolbar.querySelector("#pdf-zoom-in");
    const zoomOut = toolbar.querySelector("#pdf-zoom-out");
    const fitBtn = toolbar.querySelector("#pdf-fit");
    const zoomLabel = toolbar.querySelector("#pdf-zoom");
    const findInput = toolbar.querySelector("#pdf-find");
    const shareBtn = toolbar.querySelector("#pdf-share");
    toolbar.querySelector("#pdf-back").onclick = () => navigate(`/text/${textId}`);

    shareBtn.onclick = async () => {
      const link = location.origin + `/pdf/${textId}`;
      try {
        if (navigator.share) { await navigator.share({ title: "نبراس", url: link }); }
        else { await navigator.clipboard.writeText(link); toast(tr("copied"), "success"); }
      } catch { navigator.clipboard?.writeText(link); }
    };

    const showError = (msg) => {
      holder.innerHTML = `<div class="pdf-empty">${esc(msg || "تعذّر فتح الملف.")}</div>`;
    };

    if (typeof pdfjsLib === "undefined") {
      showError("PDF.js غير محمّل.");
      return;
    }

    // استرجاع محتوى النص لحالة فشل العرض
    let textTitle = "";
    api.get(`/api/texts/${textId}`).then((t) => { textTitle = t.title || ""; }).catch(() => {});

    // محاولة تحميل العامل (worker) مع تراجع آمن عند فشله
    const workerAttempt = () => {
      try {
        pdfjsLib.GlobalWorkerOptions.workerSrc = "/vendor/pdfjs/pdf.worker.min.js";
        return true;
      } catch { return false; }
    };
    workerAttempt();

    let pdfDoc = null;
    let pageNum = 1;
    let zoom = 1;
    let renderTask = null;

    async function renderPage(num) {
      if (!pdfDoc) return;
      const page = await pdfDoc.getPage(num);
      const holderW = holder.clientWidth || frame.clientWidth || 800;
      const base = Math.min(holderW * 0.9 * zoom, 1600);
      const baseVp = page.getViewport({ scale: 1 });
      const scale = base / baseVp.width;
      const viewport = page.getViewport({ scale });
      holder.querySelectorAll("canvas").forEach((c) => c.remove());
      const canvas = document.createElement("canvas");
      canvas.width = Math.floor(viewport.width);
      canvas.height = Math.floor(viewport.height);
      holder.append(canvas);
      if (renderTask) { try { renderTask.cancel(); } catch { /* تجاهل */ } }
      renderTask = page.render({ canvasContext: canvas.getContext("2d"), viewport });
      try {
        await renderTask.promise;
        pageLabel.textContent = `${num} / ${pdfDoc.numPages}`;
        prevBtn.disabled = num <= 1;
        nextBtn.disabled = num >= pdfDoc.numPages;
        zoomLabel.textContent = `${Math.round(scale * 100)}%`;
      } catch (e) {
        if (e?.name !== "RenderingCancelledException") { throw e; }
      }
    }

    const loadPdf = () => {
      holder.innerHTML = `<div class="pdf-empty">${esc(tr("loading"))}</div>`;
      const task = pdfjsLib.getDocument({
        url: `/api/texts/${textId}/pdf`,
        disableAutoFetch: true,
        stopAtErrors: false,
        isEvalSupported: false,
        cMapUrl: "/vendor/pdfjs/cmaps/",
        cMapPacked: true,
      });
      task.onProgress = (p) => {
        if (p.total) {
          const pct = Math.min(100, Math.round((p.loaded / p.total) * 100));
          if (pct < 100) holder.innerHTML = `<div class="pdf-empty">${esc(tr("loading"))} ${pct}%</div>`;
        }
      };
      task.promise.then((doc) => {
        pdfDoc = doc;
        return renderPage(1);
      }).catch((err) => {
        console.error("PDF load error:", err);
        showError("تعذّر فتح الملف. جرّب التحميل للعرض المباشر.");
      });
    };
    loadPdf();

    prevBtn.onclick = () => { if (pageNum > 1) { pageNum--; renderPage(pageNum); } };
    nextBtn.onclick = () => { if (pdfDoc && pageNum < pdfDoc.numPages) { pageNum++; renderPage(pageNum); } };
    zoomIn.onclick = () => { zoom = Math.min(zoom + 0.25, 3); renderPage(pageNum); };
    zoomOut.onclick = () => { zoom = Math.max(zoom - 0.25, 0.5); renderPage(pageNum); };
    fitBtn.onclick = () => { zoom = 1; renderPage(pageNum); };

    /* بحث داخل الوثيقة: يجد أول صفحة تحتوي العبارة */
    let findAbort = false;
    const findPage = async (term) => {
      if (!pdfDoc || !term) return;
      findAbort = true;
      await new Promise((r) => setTimeout(r, 0));
      findAbort = false;
      for (let i = 1; i <= pdfDoc.numPages; i++) {
        if (findAbort) return;
        try {
          const page = await pdfDoc.getPage(i);
          const content = await page.getTextContent();
          const text = content.items.map((it) => it.str || "").join(" ");
          if (text.toLowerCase().includes(term.toLowerCase())) {
            pageNum = i;
            await renderPage(i);
            toast(`${tr("search")} "${term}" → ${tr("pageOf")} ${i}`, "info");
            return;
          }
        } catch { /* صفحة غير قابلة للاستخراج — تابع البحث */ }
      }
      toast(tr("noResults"), "warn");
    };
    findInput.addEventListener("keydown", (e) => { if (e.key === "Enter") findPage(findInput.value.trim()); });
  });

  return frame;
}

