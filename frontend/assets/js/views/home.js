// نبراس — الصفحة الرئيسية (v2)
import { tr, currentLang } from "../i18n.js";
import { api } from "../api.js";
import { el, esc, emptyState, fmtDate, typeLabel, avatarColor, initials } from "../ui.js";
import { icon, iconHTML } from "../icons.js";
import { navigate } from "../router.js";

const truncate = (s, n = 120) => {
  s = String(s ?? "");
  return s.length > n ? s.slice(0, n).trimEnd() + "…" : s;
};

async function fetchTexts() {
  const d = await api.get("/api/texts?limit=8");
  return {
    list: (d.texts || d.items || []).slice(0, 8),
    total: d.count ?? (Array.isArray(d) ? d.length : 0),
  };
}
async function fetchArticles() {
  const d = await api.get("/api/blog/articles?limit=4");
  return d.articles || [];
}
async function fetchJuris() {
  const d = await api.get("/api/jurisprudence?limit=4");
  return { list: (d.decisions || []).slice(0, 4), total: d.count ?? 0 };
}

/* ---------- بطاقة صغيرة موحدة ---------- */
function tile(card) {
  return el("article", { class: "tile-card card-hover" }, card());
}

function lawTile(t) {
  return () => [
    el("div", { class: "tile-cover", text: typeLabel(t.type, currentLang()).charAt(0) }),
    el("a", { class: "t-title", href: `#/text/${t.id}`, text: t.title }),
    el("div", { class: "t-sub" }, [
      el("span", { class: "badge-pill badge-navy", text: typeLabel(t.type, currentLang()) }),
      el("span", { class: "small muted", text: t.category_name || "" }),
    ]),
    el("div", { class: "small muted", text: t.official_ref || fmtDate(t.enacted_date, currentLang()) || "" }),
  ];
}

function articleTile(a) {
  return () => [
    el("div", { class: "tile-cover", text: (a.category_name || "م").charAt(0) }),
    el("a", { class: "t-title", href: `#/blog/${a.id}`, text: a.title }),
    el("div", { class: "blog-meta" }, [
      el("span", { class: "avatar-sm", style: `background:${avatarColor(a.author?.full_name || "x")}`, text: initials(a.author?.full_name || "م") }),
      el("span", { text: a.author?.full_name || "" }),
    ]),
    el("div", { class: "t-sub" }, [
      el("span", { text: fmtDate(a.published_at, currentLang()) }),
      el("span", { text: `${a.views ?? 0} ${tr("views")}` }),
    ]),
  ];
}

function jurisTile(d) {
  return () => [
    el("div", { class: "tile-cover doc" }, [icon("scale", 28)]),
    el("a", { class: "t-title", href: `#/jurisprudence/${d.id}`, text: d.title || tr("jurisUntitled") }),
    el("div", { class: "t-sub" }, [
      d.category_name ? el("span", { class: "badge-pill badge-navy", text: d.category_name }) : null,
      d.decision_number ? el("span", { class: "small muted", text: `#${d.decision_number}` }) : null,
    ]),
    el("div", { class: "small muted", text: truncate(d.principles || d.content, 70) }),
  ];
}

function proTile(p) {
  return () => [
    el("div", { class: "flex", style: "gap:12px" }, [
      el("div", { class: "pro-avatar", style: `background:${avatarColor(p.full_name || "x")}` },
        p.photo_url
          ? el("img", { src: p.photo_url, alt: p.full_name })
          : el("span", { text: initials(p.full_name || "م") })),
      el("div", { class: "pro-meta" }, [
        el("a", { class: "pro-name", href: `#/professionals/${p.id}`, text: p.full_name }),
        el("div", { class: "pro-spec", text: p.profession_type }),
        el("div", { class: "flex", style: "gap:6px" }, [
          el("span", { class: "stars" }, [icon("star", 14, { filled: true })]),
          el("span", { class: "small muted", text: `${p.rating ?? 0} (${p.review_count ?? 0})` }),
        ]),
      ]),
    ]),
    el("div", { class: "t-sub" }, [el("span", {}, [icon("mapPin", 14), " " + (p.city || "—")])]),
  ];
}

/* ---------- مربع البحث ---------- */
function searchBox() {
  const input = el("input", {
    type: "search",
    placeholder: tr("homeSearchPh"),
    "aria-label": tr("homeSearchPh"),
    autocomplete: "off",
  });
  const dropdown = el("div", { class: "search-typeahead", role: "listbox" });
  const box = el("form", { class: "search-box" }, [
    el("div", { class: "search-inner" }, [
      input,
      el("button", { class: "btn btn-primary", type: "submit", text: tr("homeSearchBtn") }),
    ]),
    dropdown,
  ]);

  let timer = null;
  const doSearch = async (q) => {
    try {
      const d = await api.get(`/api/search?q=${encodeURIComponent(q)}`);
      const results = (d.results || []).slice(0, 7);
      dropdown.replaceChildren();
      if (!results.length) {
        dropdown.replaceChildren(el("div", { class: "st-item", text: tr("noResults") }));
      } else {
        for (const r of results) {
          dropdown.append(el("button", {
            type: "button",
            class: "st-item",
            onclick: () => { dropdown.classList.remove("open"); navigate(`/text/${r.legal_text_id || ""}`); },
          }, [
            el("span", { class: "st-title", text: `${r.label || "مادة"} — ${truncate(r.content, 80)}` }),
            el("span", { class: "st-type", text: tr("materials") }),
          ]));
        }
      }
      dropdown.classList.add("open");
    } catch { dropdown.classList.remove("open"); }
  };

  input.addEventListener("input", () => {
    const q = input.value.trim();
    clearTimeout(timer);
    if (q.length < 2) { dropdown.classList.remove("open"); return; }
    timer = setTimeout(() => doSearch(q), 280);
  });
  box.addEventListener("submit", (e) => {
    e.preventDefault();
    const q = input.value.trim();
    if (q) navigate(`/library/q/${encodeURIComponent(q)}`);
  });
  document.addEventListener("click", (e) => { if (!box.contains(e.target)) dropdown.classList.remove("open"); });
  return box;
}

/* ---------- الأسئلة الشائعة ---------- */
function faqSection() {
  const items = [1, 2, 3, 4, 5, 6].map((n) => ({
    q: tr(`faq${n}q`), a: tr(`faq${n}a`),
  }));
  return el("section", { class: "home-section" }, [
    el("div", { class: "section-head" }, [
      el("div", {}, [
        el("div", { class: "eyebrow", text: tr("faqSub") }),
        el("h2", { text: tr("faqTitle") }),
      ]),
    ]),
    el("div", {}, items.map((it, i) => {
      const body = el("div", { class: "accordion-body", text: it.a });
      const acc = el("div", { class: "accordion" }, [
        el("button", {
          class: "accordion-head",
          onclick: (e) => {
            const open = acc.classList.toggle("open");
            if (open) { const others = acc.parentElement.querySelectorAll(".accordion.open"); others.forEach(o => { if (o !== acc) o.classList.remove("open"); }); }
          },
        }, [
          el("span", { class: "flex", style: "gap:10px" }, [el("span", { class: "q-mark", text: "؟" }), it.q]),
          el("span", { class: "acc-chevron", text: "▾" }),
        ]),
        body,
      ]);
      return acc;
    })),
  ]);
}

/* ---------- الصفحة ---------- */
export async function homeView() {
  const [textsData, articles, jurisData] = await Promise.all([
    fetchTexts(), fetchArticles(), fetchJuris(),
  ]);
  const texts = textsData.list;
  const juris = jurisData.list;
  const jurisTotal = jurisData.total;

  const portals = [
    ["scale", "portalLibrary", "portalLibraryD", "/library"],
    ["shield", "portalJurisprudence", "portalJurisprudenceD", "/jurisprudence"],
    ["globe", "portalComparative", "portalComparativeD", "/comparative"],
    ["pen", "portalBlog", "portalBlogD", "/blog"],
    ["map", "portalProcedures", "portalProceduresD", "/procedures"],
    ["book", "portalLegalFrench", "portalLegalFrenchD", "/legal-french"],
    ["cpu", "portalAssistant", "portalAssistantD", "/assistant"],
    ["messageCircle", "portalCommunity", "portalCommunityD", "/community"],
    ["calculator", "portalCalculators", "portalCalculatorsD", "/calculators"],
  ];

  return el("div", {}, [
    /* Hero + بحث */
    el("section", { class: "hero" }, [
      el("span", { class: "hero-glow", "aria-hidden": "true" }),
      el("div", { class: "eyebrow", text: tr("brandSub") }),
      el("h1", { text: tr("heroTitle") }),
      el("p", { text: tr("heroText") }),
      searchBox(),
      el("div", { class: "hero-actions mt-16" }, [
        el("button", { class: "btn btn-ghost", style: "border-color:rgba(255,255,255,.4);color:#fff", text: tr("heroCta3"), onclick: () => navigate("/assistant") }),
      ]),
    ]),

    /* الإحصائيات */
    el("section", { class: "home-section" }, [
      el("div", { class: "section-head" }, [
        el("div", {}, [el("div", { class: "eyebrow", text: tr("homeStats") }), el("h2", { text: tr("portalTitle") })]),
      ]),
      el("div", { class: "stats-strip" }, [
        [textsData.total, "scale", "statLaws"],
        [jurisTotal, "shield", "statJuris"],
        [articles.length, "pen", "statArticles"],
      ].map(([n, ic, lbl]) => el("div", { class: "stat-tile" }, [
        el("div", { class: "st-icon" }, [icon(ic, 22)]),
        el("div", {}, [
          el("div", { class: "st-val", text: String(n) }),
          el("div", { class: "st-lbl", text: tr(lbl) }),
        ]),
      ]))),
    ]),

    /* أحدث القوانين — الأولوية للمكتبة القانونية */
    el("section", { class: "home-section" }, [
      el("div", { class: "section-head" }, [
        el("div", {}, [el("div", { class: "eyebrow", text: tr("latestLawsSub") }), el("h2", { text: tr("latestLaws") })]),
        el("button", { class: "btn btn-ghost btn-sm", text: tr("viewAll"), onclick: () => navigate("/library") }),
      ]),
      texts.length
        ? el("div", { class: "tile-grid" }, texts.map((t) => tile(() => lawTile(t)())))
        : emptyState(tr("noResults"), "book"),
    ]),

    /* بوابات الوصول السريع */
    el("section", { class: "home-section" }, [
      el("div", { class: "portal-grid" }, portals.map(([ic, t, d, route]) =>
        el("a", { class: "portal-card", href: `#${route}` }, [
          el("div", { class: "p-icon" }, [icon(ic, 26)]),
          el("div", { class: "p-title", text: tr(t) }),
          el("div", { class: "p-desc", text: tr(d) }),
          el("span", { class: "p-link" }, [tr("viewAll"), icon("arrowLeft", 14)]),
        ]))),
    ]),

    /* أحدث المقالات */
    el("section", { class: "home-section" }, [
      el("div", { class: "section-head" }, [
        el("div", {}, [el("div", { class: "eyebrow", text: tr("latestArticlesSub") }), el("h2", { text: tr("latestArticles") })]),
        el("button", { class: "btn btn-ghost btn-sm", text: tr("viewAll"), onclick: () => navigate("/blog") }),
      ]),
      articles.length
        ? el("div", { class: "tile-grid" }, articles.map((a) => tile(() => articleTile(a)())))
        : emptyState(tr("noResults"), "pen"),
    ]),

    /* أحدث الاجتهادات */
    el("section", { class: "home-section" }, [
      el("div", { class: "section-head" }, [
        el("div", {}, [el("div", { class: "eyebrow", text: tr("jurisLatestSub") }), el("h2", { text: tr("jurisLatest") })]),
        el("button", { class: "btn btn-ghost btn-sm", text: tr("viewAll"), onclick: () => navigate("/jurisprudence") }),
      ]),
      juris.length
        ? el("div", { class: "tile-grid" }, juris.map((d) => tile(() => jurisTile(d)())))
        : emptyState(tr("noResults"), "shield"),
    ]),

    /* الأسئلة الشائعة */
    faqSection(),

    /* CTA */
    el("section", { class: "home-section" }, [
      el("div", { class: "hero", style: "display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap" }, [
        el("div", {}, [
          el("h2", { style: "color:#fff", text: tr("portalLegalFrench") }),
          el("p", { text: tr("portalLegalFrenchD") }),
        ]),
        el("div", { class: "hero-actions" }, [
          el("button", {
            class: "btn btn-gold",
            text: tr("viewAll"),
            onclick: () => navigate("/legal-french"),
          }),
        ]),
      ]),
    ]),
  ]);
}
