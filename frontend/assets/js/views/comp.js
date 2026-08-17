// نبراس — قانون مقارن مستقل: دول + قوانين + اجتهادات + بحث
import { tr } from "../i18n.js";
import { api } from "../api.js";
import { el, esc, emptyState, pagination, toast } from "../ui.js";
import { icon } from "../icons.js";
import { navigate } from "../router.js";

const PER_PAGE = 20;

// ── Countries List ──────────────────────────────────────────────
export async function compCountriesView() {
  const data = await api.get("/api/comp/countries");
  const countries = data.countries || [];
  const stats = await api.get("/api/comp/stats");

  return el("div", { class: "container" }, [
    el("div", { class: "flex-between", style: "margin-bottom:1.5rem" }, [
      el("h2", { text: "\u0627\u0644\u0642\u0627\u0646\u0648\u0646 \u0627\u0644\u0645\u0642\u0627\u0631\u0646" }),
      el("div", { class: "badge-pill", text: `${stats.countries} \u062f\u0648\u0644\u0629` }),
    ]),
    el("div", { class: "grid grid-3" }, countries.map((c) =>
      el("article", {
        class: "card card-hover",
        style: "cursor:pointer;padding:1.5rem",
        onclick: () => navigate(`/foreign-law/${c.code}`),
      }, [
        el("div", { style: "font-size:2rem;margin-bottom:0.5rem", text: c.flag_emoji || "\ud83c\udf0d" }),
        el("h3", { style: "margin:0 0 0.3rem", text: c.name }),
        el("div", { class: "text-muted", text: c.name_ar || c.name }),
        el("div", {
          style: "margin-top:0.8rem;display:flex;gap:1rem;font-size:0.85rem;color:var(--text-muted,#666)"
        }, [
          el("span", { text: `\u2022 ${stats.laws || 0} \u0642\u0627\u0646\u0648\u0646` }),
          el("span", { text: `\u2022 ${stats.courts || 0} \u0645\u062d\u0643\u0645\u0629` }),
        ]),
      ])
    )),
  ]);
}

// ── Country Detail ──────────────────────────────────────────────
export async function compCountryView(params) {
  const code = params.code;
  const [country, lawsData, courtsData, jurData, catsData] = await Promise.all([
    api.get(`/api/comp/countries/${code}`),
    api.get(`/api/comp/countries/${code}/laws`),
    api.get(`/api/comp/countries/${code}/courts`),
    api.get(`/api/comp/countries/${code}/jurisprudence`),
    api.get(`/api/comp/countries/${code}/categories`),
  ]);

  let activeTab = params.tab || "laws";
  const container = el("div", {});

  async function renderTab() {
    const tabs = [
      { id: "laws", label: "\u0627\u0644\u0642\u0648\u0627\u0646\u064a\u0646", icon: "book-open" },
      { id: "courts", label: "\u0627\u0644\u0645\u062d\u0627\u0643\u0645", icon: "gavel" },
      { id: "jurisprudence", label: "\u0627\u0644\u0627\u062c\u062a\u0647\u0627\u062f\u0627\u062a", icon: "search" },
    ];

    let panel;
    if (activeTab === "laws") {
      panel = lawsData.laws.length
        ? el("div", { class: "grid grid-2" }, lawsData.laws.map((l) =>
            el("article", {
              class: "card card-hover",
              style: "cursor:pointer;padding:1.2rem",
              onclick: () => navigate(`/foreign-law/${code}/law/${l.id}`),
            }, [
              el("div", { class: "badge-pill", text: l.category || "general", style: "margin-bottom:0.5rem" }),
              el("h4", { text: l.title }),
              l.title_original ? el("div", { class: "text-muted", text: l.title_original }) : null,
              l.enacted_date ? el("div", { class: "text-muted", style: "font-size:0.85rem", text: l.enacted_date }) : null,
            ])
          ))
        : emptyState("\u0644\u0645 \u064a\u062a\u0645 \u0625\u0636\u0627\u0641\u0629 \u0642\u0648\u0627\u0646\u064a\u0646 \u0644\u0647\u0630\u0647 \u0627\u0644\u062f\u0648\u0644\u0629");
    } else if (activeTab === "courts") {
      panel = courtsData.courts.length
        ? el("div", { class: "grid grid-2" }, courtsData.courts.map((c) =>
            el("div", { class: "card", style: "padding:1rem" }, [
              el("h4", { text: c.name }),
              c.name_ar ? el("div", { class: "text-muted", text: c.name_ar }) : null,
              c.description ? el("p", { text: c.description }) : null,
            ])
          ))
        : emptyState("\u0644\u0645 \u062a\u0648\u062c\u062f \u0645\u062d\u0627\u0643\u0645 \u0644\u0647\u0630\u0647 \u0627\u0644\u062f\u0648\u0644\u0629");
    } else {
      panel = jurData.decisions.length
        ? el("div", { class: "grid grid-2" }, jurData.decisions.map((d) =>
            el("article", { class: "card", style: "padding:1rem" }, [
              el("h4", { text: d.title }),
              d.court_name ? el("div", { class: "text-muted", text: d.court_name }) : null,
              d.decision_date ? el("div", { class: "text-muted", style: "font-size:0.85rem", text: d.decision_date }) : null,
              el("p", { style: "margin-top:0.5rem", text: (d.content || "").slice(0, 200) + "\u2026" }),
            ])
          ))
        : emptyState("\u0644\u0645 \u062a\u0648\u062c\u062f \u0627\u062c\u062a\u0647\u0627\u062f\u0627\u062a \u0644\u0647\u0630\u0647 \u0627\u0644\u062f\u0648\u0644\u0629");
    }

    container.replaceChildren(
      el("div", { style: "margin-bottom:1.5rem" }, [
        el("button", {
          class: "btn btn-ghost btn-sm",
          style: "margin-bottom:1rem",
          onclick: () => navigate("/foreign-law"),
          html: "\u2192 \u0627\u0644\u0639\u0648\u062f\u0629 \u0644\u0644\u062f\u0648\u0644",
        }),
        el("div", { style: "display:flex;align-items:center;gap:1rem" }, [
          el("span", { style: "font-size:2rem", text: country.flag_emoji || "\ud83c\udf0d" }),
          el("h2", { text: country.name }),
        ]),
        el("div", { class: "text-muted", style: "margin-bottom:1rem", text: country.name_ar || "" }),
        el("div", { class: "tabs" }, tabs.map((t) =>
          el("button", {
            class: `tab-btn ${activeTab === t.id ? "active" : ""}`,
            onclick: () => { activeTab = t.id; renderTab(); },
            text: t.label,
          })
        )),
      ]),
      el("div", { style: "margin-top:1rem" }, [panel]),
    );
  }

  renderTab();
  return container;
}

// ── Law Detail ──────────────────────────────────────────────────
export async function compLawView(params) {
  const code = params.code;
  const lawId = params.lawId;
  const law = await api.get(`/api/comp/laws/${lawId}`);

  return el("div", { class: "container" }, [
    el("button", {
      class: "btn btn-ghost btn-sm",
      style: "margin-bottom:1rem",
      onclick: () => navigate(`/foreign-law/${code}`),
      html: "\u2192 \u0627\u0644\u0639\u0648\u062f\u0629",
    }),
    el("div", { class: "card", style: "padding:2rem" }, [
      el("div", { class: "badge-pill", text: law.category || "general", style: "margin-bottom:0.5rem" }),
      el("h2", { text: law.title }),
      law.title_original ? el("div", { class: "text-muted", text: law.title_original }) : null,
      law.official_ref ? el("div", { class: "text-muted", style: "font-size:0.9rem", text: law.official_ref }) : null,
      law.enacted_date ? el("div", { class: "text-muted", style: "margin-top:0.5rem", text: `\u062a\u0627\u0631\u064a\u062e \u0627\u0644\u0635\u062f\u0648\u0631: ${law.enacted_date}` }) : null,
      law.source_name ? el("div", { class: "text-muted", style: "font-size:0.85rem;margin-top:0.3rem", text: `\u0627\u0644\u0645\u0635\u062f\u0631: ${law.source_name}` }) : null,
    ]),
    (law.articles || []).length
      ? el("div", { style: "margin-top:1.5rem" }, [
          el("h3", { style: "margin-bottom:1rem", text: "\u0627\u0644\u0645\u0648\u0627\u062f" }),
          ...law.articles.map((a) =>
            el("div", { class: "card", style: "padding:1rem;margin-bottom:0.8rem" }, [
              el("div", { style: "display:flex;gap:0.5rem;align-items:baseline" }, [
                el("strong", { text: a.number }),
                el("span", { class: "text-muted", text: a.label }),
              ]),
              el("p", { style: "margin-top:0.5rem;white-space:pre-wrap", text: a.content }),
              a.keywords ? el("div", { class: "text-muted", style: "font-size:0.8rem", text: `\u0645\u0641\u062a\u0627\u062a\u062d: ${a.keywords}` }) : null,
            ])
          ),
        ])
      : null,
  ]);
}

// ── Search ──────────────────────────────────────────────────────
export async function compSearchView(params) {
  const q = params.q || "";
  let results = [];
  let searched = false;

  if (q) {
    const data = await api.get(`/api/comp/search?q=${encodeURIComponent(q)}`);
    results = data.results || [];
    searched = true;
  }

  const container = el("div", { class: "container" }, []);

  async function render() {
    container.replaceChildren(
      el("h2", { text: "\u0628\u062d\u062b \u0641\u064a \u0627\u0644\u0642\u0627\u0646\u0648\u0646 \u0627\u0644\u0645\u0642\u0627\u0631\u0646" }),
      el("div", { class: "search-bar", style: "margin:1rem 0" }, [
        el("input", {
          id: "comp-search-input",
          type: "search",
          class: "input",
          placeholder: "\u0627\u0643\u062a\u0628 \u0645\u0635\u0637\u0644\u062d\u0627\u064b...",
          value: q,
          onkeydown: (e) => {
            if (e.key === "Enter") {
              const v = e.target.value.trim();
              if (v) navigate(`/foreign-law/search/${encodeURIComponent(v)}`);
            }
          },
        }),
        el("button", {
          class: "btn btn-primary",
          text: "\u0628\u062d\u062b",
          onclick: () => {
            const input = document.getElementById("comp-search-input");
            const v = input?.value?.trim();
            if (v) navigate(`/foreign-law/search/${encodeURIComponent(v)}`);
          },
        }),
      ]),
      searched
        ? el("div", { class: "text-muted", style: "margin-bottom:1rem", text: `${results.length} \u0646\u062a\u064a\u062c\u0629` })
        : null,
    );

    if (searched && results.length) {
      container.append(el("div", { class: "grid grid-2" }, results.map((r) =>
        el("article", { class: "card", style: "padding:1rem" }, [
          el("div", { class: "badge-pill", text: r.result_type === "law" ? "\u0642\u0627\u0646\u0648\u0646" : "\u0627\u062c\u062a\u0647\u0627\u062f", style: "margin-bottom:0.4rem" }),
          el("div", { class: "text-muted", style: "font-size:0.85rem", text: `${r.country_name || ""} \u2022 ${r.law_title || r.court_name || ""}` }),
          el("h4", { text: r.title || r.label || "" }),
          r.snippet ? el("p", { style: "margin-top:0.4rem;font-size:0.9rem", text: r.snippet }) : null,
        ])
      )));
    } else if (searched) {
      container.append(emptyState("\u0644\u0645 \u062a\u0639\u0631\u0636 \u0646\u062a\u0627\u0626\u062c \u0644\u0647\u0630\u0627 \u0627\u0644\u0628\u062d\u062b"));
    }
  }

  render();
  return container;
}

// ── Stats ───────────────────────────────────────────────────────
export async function compStatsView() {
  const stats = await api.get("/api/comp/stats");

  const items = [
    { label: "\u0627\u0644\u062f\u0648\u0644", value: stats.countries, icon: "globe" },
    { label: "\u0627\u0644\u0642\u0648\u0627\u0646\u064a\u0646", value: stats.laws, icon: "book-open" },
    { label: "\u0627\u0644\u0645\u0648\u0627\u062f", value: stats.articles, icon: "file-text" },
    { label: "\u0627\u0644\u0645\u062d\u0627\u0643\u0645", value: stats.courts, icon: "gavel" },
    { label: "\u0627\u0644\u0627\u062c\u062a\u0647\u0627\u062f\u0627\u062a", value: stats.decisions, icon: "search" },
  ];

  return el("div", { class: "container" }, [
    el("h2", { text: "\u0625\u062d\u0635\u0627\u0626\u064a\u0627\u062a \u0627\u0644\u0642\u0627\u0646\u0648\u0646 \u0627\u0644\u0645\u0642\u0627\u0631\u0646" }),
    el("div", { class: "grid grid-3", style: "margin-top:1rem" }, items.map((item) =>
      el("div", { class: "card", style: "padding:1.5rem;text-align:center" }, [
        el("div", { style: "font-size:2rem;margin-bottom:0.5rem", text: String(item.value) }),
        el("div", { class: "text-muted", text: item.label }),
      ])
    )),
  ]);
}
