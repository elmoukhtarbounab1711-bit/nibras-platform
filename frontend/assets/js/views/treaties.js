// نبراس — الاتفاقيات والنصوص القانونية الدولية بالفرنسية
import { tr } from "../i18n.js";
import { api } from "../api.js";
import { el, emptyState } from "../ui.js";

const esc = (s) => { const d = document.createElement("div"); d.textContent = s; return d.innerHTML; };

const CATEGORY_COLORS = {
  "حقوق الإنسان": "#2563eb",
  "القانون الدولي الإنساني": "#dc2626",
  "العمل والضمان الاجتماعي": "#059669",
  "التجارة والاقتصاد": "#d97706",
  "البيئة والتنمية": "#16a34a",
  "الجرائم المنظمة": "#7c3aed",
};

function categoryBadge(cat) {
  const color = CATEGORY_COLORS[cat] || "#6b7280";
  return el("span", {
    class: "tr-badge",
    style: `background:${color}`,
  }, [document.createTextNode(cat)]);
}

function formatDate(d) {
  if (!d) return "";
  const parts = d.split("-");
  if (parts.length === 3) return `${parts[2]}/${parts[1]}/${parts[0]}`;
  return d;
}

function treatyCard(t) {
  const card = el("div", { class: "tr-card" }, [
    el("div", { class: "tr-card-header" }, [
      categoryBadge(t.category),
      el("span", { class: "tr-card-date", text: formatDate(t.ratification_date) }),
    ]),
    el("h3", { class: "tr-card-title", text: t.title }),
    el("p", { class: "tr-card-title-ar", text: t.title_ar }),
    el("p", { class: "tr-card-desc", text: t.description }),
    el("div", { class: "tr-card-footer" }, [
      el("span", { class: "tr-card-source", text: t.source_name || "" }),
      el("button", {
        class: "btn btn-sm btn-primary",
        text: "النص الكامل",
        onclick: () => { location.hash = `#/treaties/${t.id}`; },
      }),
    ]),
  ]);
  card.addEventListener("click", (e) => {
    if (e.target.tagName === "BUTTON") return;
    location.hash = `#/treaties/${t.id}`;
  });
  card.style.cursor = "pointer";
  return card;
}

function formatFullText(text) {
  if (!text) return "";
  const lines = text.split("\n");
  const formatted = lines.map((line) => {
    const trimmed = line.trim();
    if (trimmed.match(/^(Article|PRÉAMBULE|DEUXIÈME PARTIE|PREMIÈRE PARTIE)/)) {
      return `<h4 class="tr-article-heading">${esc(trimmed)}</h4>`;
    }
    if (trimmed === "") return "<br>";
    return `<p>${esc(trimmed)}</p>`;
  });
  return formatted.join("\n");
}

/* ── Main List View ─────────────────────────────────────────────────── */
export async function treatiesView() {
  const container = el("div", { class: "tr-page" });

  // breadcrumb
  container.append(el("div", { class: "tr-breadcrumb" }, [
    el("a", { href: "#/home", text: "الرئيسية" }),
    document.createTextNode(" / "),
    el("span", { text: "النصوص والاتفاقيات" }),
  ]));

  // hero
  container.append(el("div", { class: "tr-hero" }, [
    el("div", { class: "tr-hero-icon" }),
    el("h1", { text: "النصوص القانونية والاتفاقيات الدولية بالفرنسية" }),
    el("p", { class: "tr-hero-sub", text: "اتفاقيات ومواثيق دولية رسمية صادرة عن الأمم المتحدة ومنظماتها — باللغة الفرنسية الأصلية" }),
  ]));

  // search
  const searchWrap = el("div", { class: "tr-search-wrap" }, [
    el("input", {
      class: "tr-search-input",
      type: "text",
      placeholder: "ابحث في عناوين الاتفاقيات...",
      id: "tr-search",
    }),
    el("button", { class: "btn btn-primary btn-sm", text: "بحث", id: "tr-search-btn" }),
  ]);
  container.append(searchWrap);

  // categories
  let categories = [];
  let items = [];
  try {
    const data = await api.get("/api/treaties");
    categories = data.categories || [];
    items = data.treaties || [];
  } catch { /* fallback */ }

  const chipWrap = el("div", { class: "tr-chips" });
  const allChip = el("button", { class: "tr-chip active", text: "الكل", "data-cat": "" });
  chipWrap.append(allChip);
  for (const cat of categories) {
    chipWrap.append(el("button", {
      class: "tr-chip",
      text: cat,
      "data-cat": cat,
    }));
  }
  container.append(chipWrap);

  // grid
  const grid = el("div", { class: "tr-grid" });
  for (const t of items) grid.append(treatyCard(t));
  container.append(grid);

  const noResults = el("div", { class: "tr-no-results hidden" }, [
    emptyState("لا توجد نتائج مطابقة", "search"),
  ]);
  container.append(noResults);

  // filtering
  let activeCategory = "";
  let searchQuery = "";

  function renderGrid(list) {
    grid.innerHTML = "";
    if (list.length === 0) {
      noResults.classList.remove("hidden");
      grid.style.display = "none";
    } else {
      noResults.classList.add("hidden");
      grid.style.display = "";
      for (const t of list) grid.append(treatyCard(t));
    }
  }

  function applyFilters() {
    let filtered = items;
    if (activeCategory) filtered = filtered.filter((t) => t.category === activeCategory);
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      filtered = filtered.filter((t) =>
        (t.title && t.title.toLowerCase().includes(q)) ||
        (t.title_ar && t.title_ar.includes(searchQuery)) ||
        (t.description && t.description.toLowerCase().includes(q))
      );
    }
    renderGrid(filtered);
  }

  chipWrap.addEventListener("click", (e) => {
    const chip = e.target.closest(".tr-chip");
    if (!chip) return;
    chipWrap.querySelectorAll(".tr-chip").forEach((c) => c.classList.remove("active"));
    chip.classList.add("active");
    activeCategory = chip.dataset.cat;
    applyFilters();
  });

  const searchInput = container.querySelector("#tr-search");
  const searchBtn = container.querySelector("#tr-search-btn");
  function doSearch() { searchQuery = searchInput.value.trim(); applyFilters(); }
  searchBtn.addEventListener("click", doSearch);
  searchInput.addEventListener("keydown", (e) => { if (e.key === "Enter") doSearch(); });

  return container;
}

/* ── Detail View ─────────────────────────────────────────────────────── */
export async function treatiesDetailView(params) {
  const id = parseInt(params.id, 10);
  const container = el("div", { class: "tr-page" });

  // breadcrumb
  container.append(el("div", { class: "tr-breadcrumb" }, [
    el("a", { href: "#/home", text: "الرئيسية" }),
    document.createTextNode(" / "),
    el("a", { href: "#/treaties", text: "النصوص والاتفاقيات" }),
    document.createTextNode(" / "),
    el("span", { text: "تفاصيل" }),
  ]));

  let treaty;
  try {
    treaty = await api.get(`/api/treaties/${id}`);
  } catch {
    container.append(emptyState("الاتفاقية غير موجودة", "file"));
    return container;
  }

  container.append(el("div", { class: "tr-detail-hero" }, [
    categoryBadge(treaty.category),
    el("h1", { text: treaty.title }),
    el("p", { class: "tr-detail-title-ar", text: treaty.title_ar }),
  ]));

  // metadata
  container.append(el("div", { class: "tr-meta-grid" }, [
    el("div", { class: "tr-meta-card" }, [
      el("div", { class: "tr-meta-label", text: "تاريخ التصديق" }),
      el("div", { class: "tr-meta-value", text: formatDate(treaty.ratification_date) }),
    ]),
    el("div", { class: "tr-meta-card" }, [
      el("div", { class: "tr-meta-label", text: "المصدر" }),
      el("div", { class: "tr-meta-value", text: treaty.source_name || "—" }),
    ]),
    el("div", { class: "tr-meta-card" }, [
      el("div", { class: "tr-meta-label", text: "اللغة" }),
      el("div", { class: "tr-meta-value", text: "Français" }),
    ]),
  ]));

  // description
  if (treaty.description) {
    container.append(el("div", { class: "tr-desc-box" }, [
      el("h3", { text: "الوصف" }),
      el("p", { text: treaty.description }),
    ]));
  }

  // source link
  if (treaty.source_url) {
    container.append(el("div", { class: "tr-source-link" }, [
      el("a", {
        href: treaty.source_url,
        target: "_blank",
        rel: "noopener noreferrer",
        text: "🔗 الاطلاع على النص الأصلي في المصدر",
      }),
    ]));
  }

  // full text
  container.append(el("div", { class: "tr-fulltext-section" }, [
    el("h2", { text: "النص الكامل" }),
    el("div", {
      class: "tr-fulltext-body",
      html: formatFullText(treaty.full_text),
    }),
  ]));

  return container;
}
