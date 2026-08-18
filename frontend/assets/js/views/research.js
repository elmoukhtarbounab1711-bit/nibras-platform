// نبراس — مكتبة الباحث: كتب PDF مقسمة حسب التصنيف القانوني ونوع الكتاب
import { api } from "../api.js";
import { el, esc, emptyState, pagination, toast } from "../ui.js";
import { icon, iconHTML } from "../icons.js";
import { navigate } from "../router.js";
import { tr } from "../i18n.js";

const PER_PAGE = 24;

const BOOK_TYPES = [
  { key: "thesis", label: "أطروحة دكتوراه", icon: "graduation" },
  { key: "dissertation", label: "رسالة ماستر", icon: "book-open" },
  { key: "book", label: "كتاب", icon: "book" },
  { key: "article", label: "بحث علمي", icon: "file-text" },
  { key: "research", label: "بحث", icon: "search" },
];

const LEGAL_CATEGORIES = [
  { key: "civil", label: "المدني", color: "#2563eb" },
  { key: "criminal", label: "الجنائي", color: "#dc2626" },
  { key: "labor", label: "الشغل", color: "#059669" },
  { key: "personal_status", label: "الأحوال الشخصية", color: "#7c3aed" },
  { key: "administrative", label: "الإداري", color: "#d97706" },
  { key: "constitutional", label: "الدستوري", color: "#0891b2" },
  { key: "commercial", label: "التجاري", color: "#be185d" },
  { key: "general", label: "عام", color: "#6b7280" },
];

const catMap = Object.fromEntries(LEGAL_CATEGORIES.map((c) => [c.key, c]));
const typeMap = Object.fromEntries(BOOK_TYPES.map((t) => [t.key, t]));

export async function researchView() {
  let activeType = "all";
  let activeCat = "all";
  let searchQuery = "";
  let currentPage = 1;

  const hero = el("section", { class: "lib-hero" }, [
    el("div", { class: "hero-bg" }),
    el("span", { class: "hero-crown" }, [icon("book-open", 30)]),
    el("span", { class: "hero-eyebrow" }, [icon("book-open", 15), "مكتبة الباحث"]),
    el("h1", { text: "كتب وأبحاث علمية بالقانون" }),
    el("p", { class: "hero-sub", text: "أطروحتان ورسائل ماستر وكتب ومراجع قانونية — مرتّبة حسب النوع والتصنيف" }),
  ]);

  const section = el("div", {});
  section.appendChild(hero);

  const contentSection = el("section", { class: "content-section" });
  section.appendChild(contentSection);

  async function render() {
    const [booksData, statsData] = await Promise.all([
      api.get(buildUrl(currentPage)),
      api.get("/api/research/stats").catch(() => ({})),
    ]);

    const books = booksData.books || [];
    const total = booksData.total || 0;
    const totalPages = Math.ceil(total / PER_PAGE);

    contentSection.replaceChildren(
      el("div", { class: "section-head" }, [
        el("div", {}, [
          el("div", { class: "eyebrow", text: "التصنيفات" }),
          el("h2", { text: "اختر نوع الكتاب أو التصنيف القانوني" }),
        ]),
      ]),

      renderTypeTabs(),

      renderCategoryGrid(statsData),

      el("div", { class: "section-head", style: "margin-top:1.5rem" }, [
        el("div", {}, [
          el("div", { class: "eyebrow", text: "الكتب" }),
          el("h2", { text: searchQuery ? `نتائج البحث: "${searchQuery}"` : "جميع الكتب" }),
          el("div", { class: "sub", text: `${total} نتيجة` }),
        ]),
        renderSearchBar(),
      ]),

      books.length
        ? el("div", { class: "tile-grid" }, books.map(renderBookCard))
        : emptyState("لا توجد كتب في هذا التصنيف"),

      totalPages > 1
        ? el("div", { style: "margin-top:1.5rem;display:flex;justify-content:center" }, [
            pagination(total, PER_PAGE, currentPage, (p) => {
              currentPage = p;
              render();
            }),
          ])
        : null,
    );
  }

  function buildUrl(page) {
    const params = new URLSearchParams();
    params.set("limit", PER_PAGE);
    params.set("offset", (page - 1) * PER_PAGE);
    if (activeType !== "all") params.set("type", activeType);
    if (activeCat !== "all") params.set("category", activeCat);
    if (searchQuery) params.set("q", searchQuery);
    return `/api/research/books?${params.toString()}`;
  }

  function renderTypeTabs() {
    const tabs = [{ key: "all", label: "الكل" }, ...BOOK_TYPES];
    return el("div", { class: "tabs tabs-row", style: "margin-bottom:1.5rem" }, tabs.map((t) =>
      el("button", {
        class: "tab" + (activeType === t.key ? " active" : ""),
        text: t.label,
        onclick: () => { activeType = t.key; currentPage = 1; render(); },
      })
    ));
  }

  function renderCategoryGrid(stats) {
    const byCat = stats?.by_category || {};
    return el("div", {
      class: "grid grid-4", style: "gap:0.8rem;margin-bottom:1rem"
    }, LEGAL_CATEGORIES.map((cat) => {
      const count = byCat[cat.key] || 0;
      const isActive = activeCat === cat.key;
      return el("button", {
        class: `tile-card card-hover ${isActive ? "active" : ""}`,
        style: `cursor:pointer;padding:1rem;text-align:center;border:2px solid ${isActive ? cat.color : "var(--line,#e5e7eb)"};transition:border-color .2s`,
        onclick: () => { activeCat = isActive ? "all" : cat.key; currentPage = 1; render(); },
      }, [
        el("div", { style: `font-size:1.5rem;font-weight:700;color:${cat.color}`, text: String(count) }),
        el("div", { style: "font-size:0.85rem;margin-top:0.2rem", text: cat.label }),
      ]);
    }));
  }

  function renderSearchBar() {
    const input = el("input", {
      type: "search",
      class: "input",
      placeholder: "ابحث عن كتاب أو مؤلف...",
      value: searchQuery,
      style: "flex:1",
      onkeydown: (e) => {
        if (e.key === "Enter") {
          searchQuery = e.target.value.trim();
          currentPage = 1;
          render();
        }
      },
    });
    return el("div", { class: "flex", style: "gap:0.5rem" }, [
      input,
      el("button", {
        class: "btn btn-primary",
        text: "بحث",
        onclick: () => {
          searchQuery = input.value.trim();
          currentPage = 1;
          render();
        },
      }),
    ]);
  }

  function renderBookCard(book) {
    const cat = catMap[book.legal_category] || catMap.general;
    const type = typeMap[book.book_type] || typeMap.book;

    const card = el("article", {
      class: "tile-card card-hover",
      style: "cursor:pointer",
      onclick: () => navigate(`/research/${book.id}`),
    }, [
      book.cover_image
        ? el("div", { class: "tile-cover", style: "height:180px;overflow:hidden;border-radius:var(--radius) var(--radius) 0 0;margin:-18px -18px 0" }, [
            el("img", {
              src: `/api/research/books/${book.id}/cover`,
              style: "width:100%;height:100%;object-fit:cover",
              loading: "lazy",
            }),
          ])
        : el("div", { class: "tile-cover", style: "height:120px;background:linear-gradient(135deg,var(--navy,#1f3a93),var(--navy-light,#2563eb));border-radius:var(--radius) var(--radius) 0 0;margin:-18px -18px 0;display:flex;align-items:center;justify-content:center" }, [
            iconHTML("book-open", 40),
          ]),
      el("div", { class: "t-tag", style: "margin-top:8px" }, [
        el("span", {
          class: "badge-pill",
          style: `background:${cat.color}20;color:${cat.color};font-size:0.75rem;padding:0.2rem 0.6rem`,
          text: cat.label,
        }),
        el("span", {
          class: "badge-pill",
          style: "background:var(--surface-2,#f3f4f6);font-size:0.75rem;padding:0.2rem 0.6rem;margin-inline-start:4px",
          text: type.label,
        }),
      ]),
      el("h3", { class: "t-title", text: book.title }),
      book.author ? el("div", { class: "t-sub" }, [
        iconHTML("user", 13),
        el("span", { text: book.author }),
      ]) : null,
      el("div", { class: "t-sub", style: "margin-top:auto" }, [
        el("span", { text: book.year ? String(book.year) : "—" }),
        el("span", { text: "·" }),
        el("span", { text: `${book.downloads || 0} تحميل` }),
      ]),
    ]);
    return card;
  }

  await render();
  return section;
}

export async function researchBookView(params) {
  const bookId = params.id;
  const book = await api.get(`/api/research/books/${bookId}`);

  const cat = catMap[book.legal_category] || catMap.general;
  const type = typeMap[book.book_type] || typeMap.book;

  const hero = el("section", { class: "lib-hero" }, [
    el("div", { class: "hero-bg" }),
    el("span", { class: "hero-crown" }, [icon("book-open", 30)]),
    el("span", { class: "hero-eyebrow" }, [
      icon("book-open", 15),
      cat.label,
    ]),
    el("h1", { text: book.title }),
    el("p", { class: "hero-sub", text: book.author || "" }),
  ]);

  return el("div", {}, [
    hero,
    el("section", { class: "content-section" }, [
      el("button", {
        class: "btn btn-ghost btn-sm mb-16",
        text: `← ${tr("back")}`,
        onclick: () => navigate("/research"),
      }),

      book.cover_image
        ? el("div", { style: "margin-bottom:1.5rem;text-align:center" }, [
            el("img", {
              src: `/api/research/books/${bookId}/cover`,
              style: "max-width:280px;width:100%;border-radius:var(--radius-lg);box-shadow:var(--shadow-lg);border:2px solid var(--line,#e5e7eb)",
            }),
          ])
        : null,

      el("div", { class: "card", style: "padding:2rem" }, [
        el("div", { class: "flex", style: "gap:0.5rem;margin-bottom:1rem" }, [
          el("span", {
            class: "badge-pill",
            style: `background:${cat.color}20;color:${cat.color};padding:0.3rem 0.8rem`,
            text: cat.label,
          }),
          el("span", {
            class: "badge-pill",
            style: "background:var(--surface-2,#f3f4f6);padding:0.3rem 0.8rem",
            text: type.label,
          }),
        ]),

        el("div", { class: "flex", style: "gap:1.5rem;margin:1rem 0;font-size:0.9rem;color:var(--ink-3,#666)" }, [
          book.year ? el("span", { text: `السنة: ${book.year}` }) : null,
          book.language ? el("span", { text: `اللغة: ${book.language === "ar" ? "عربية" : "إنجليزية"}` }) : null,
          el("span", { text: `${book.downloads || 0} تحميل` }),
        ]),

        book.description
          ? el("div", { style: "margin:1rem 0;line-height:1.8;color:var(--ink-2,#444)", text: book.description })
          : null,

        book.source_name
          ? el("div", { class: "t-sub", style: "font-size:0.85rem;margin-top:1rem" }, [
              iconHTML("external-link", 13),
              el("span", { text: "المصدر: " }),
              book.source_url
                ? el("a", { href: book.source_url, target: "_blank", style: "color:var(--gold)", text: book.source_name })
                : el("span", { text: book.source_name }),
            ])
          : null,

        book.file_path
          ? el("a", {
              class: "btn btn-primary",
              style: "margin-top:1.5rem",
              href: `/api/research/books/${bookId}/download`,
            }, [icon("download", 16), " تحميل PDF"])
          : null,
      ]),
    ]),
  ]);
}
