// نبراس — المساطر القانونية
import { tr, currentLang } from "../i18n.js";
import { api } from "../api.js";
import { el, esc, emptyState, skeleton } from "../ui.js";
import { icon } from "../icons.js";

function renderSteps(steps) {
  return el("div", { class: "flex-col mt-8" },
    steps.map((s, i) => el("div", { class: "legal-block" }, [
      el("div", { class: "flex-between" }, [
        el("strong", { text: `${i + 1}. ${s.title}` }),
      ]),
      s.description ? el("p", { class: "small muted mb-8", text: s.description }) : null,
      s.required_documents ? el("div", { class: "small", style: "color:var(--navy)" }, [
        el("strong", { text: `${tr("requiredDocs")}: ` }),
        el("span", { text: s.required_documents }),
      ]) : null,
    ])));
}

function renderFaq(faq) {
  const list = Array.isArray(faq) ? faq : [];
  if (!list.length) return null;
  return el("div", { class: "mt-8" }, [
    el("h4", { text: tr("faq") }),
    ...list.map((f) => el("div", { class: "accordion" }, [
      el("button", { class: "accordion-head", onclick: (e) => e.currentTarget.closest(".accordion").classList.toggle("open") }, [icon("helpCircle", 16), " " + f.q]),
      el("div", { class: "accordion-body", text: f.a }),
    ])),
  ]);
}

export async function proceduresView() {
  const list = await api.get("/api/procedures");
  const data = Array.isArray(list) ? list : list.procedures || [];
  const wrap = el("div", { class: "flex-col" });

  if (!data.length) { return el("div", {}, [el("div", { class: "section-head" }, [el("h2", { text: tr("proceduresTitle") })]), emptyState(tr("noResults"), "compass")]); }

  const accordions = data.map((p) => {
    const bodyEl = el("div", { class: "accordion-body" }, [el("div", { class: "small muted", text: tr("loading") })]);
    const acc = el("div", { class: "accordion" }, [
      el("button", { class: "accordion-head" }, [
        el("span", { text: p.title }),
        el("span", { class: "flex" }, [
          p.step_count ? el("span", { class: "badge-pill badge-blue", text: `${p.step_count} ${tr("steps")}` }) : null,
          el("span", { class: "acc-chevron", text: "▾" }),
        ]),
      ]),
      bodyEl,
    ]);
    const renderInto = (detail) => {
      bodyEl.replaceChildren(
        detail.category ? el("span", { class: "badge-pill badge-gold mb-8", text: detail.category }) : null,
        el("div", { class: "flex mt-8 mb-8", style: "flex-wrap:gap:8px" }, [
          detail.responsible_authority ? el("span", { class: "small muted", text: `${tr("responsibleAuthority")}: ${detail.responsible_authority}` }) : null,
          detail.typical_timeframe ? el("span", { class: "small muted", text: `${tr("typicalTimeframe")}: ${detail.typical_timeframe}` }) : null,
          detail.fees ? el("span", { class: "small", style: "color:var(--warn);font-weight:700", text: `${tr("fees")}: ${detail.fees}` }) : null,
        ]),
        detail.description ? el("div", { class: "small muted", text: detail.description || "" }) : null,
        (detail.steps || []).length ? renderSteps(detail.steps) : null,
        renderFaq(detail.faq),
      );
    };
    if ((p.steps || []).length) renderInto(p);
    acc.querySelector(".accordion-head").addEventListener("click", () => acc.classList.toggle("open"));
    acc.dataset.slug = p.slug || p.id;
    acc.dataset.ready = (p.steps || []).length ? "1" : "0";
    acc._render = renderInto;
    return acc;
  });

  const detailLoader = async () => {
    for (const acc of accordions) {
      if (acc.dataset.ready === "1") continue;
      try {
        const detail = await api.get(`/api/procedures/${acc.dataset.slug}`);
        acc._render(detail.procedure || detail);
        acc.dataset.ready = "1";
      } catch { /* تجاهل */ }
    }
  };
  detailLoader();

  return el("div", {}, [
    el("div", { class: "section-head" }, [
      el("div", {}, [el("h2", { text: tr("proceduresTitle") }), el("div", { class: "sub", text: tr("proceduresSub") })]),
    ]),
    el("div", { class: "flex-col" }, accordions),
  ]);
}

export async function procedureDetailView(params) {
  try {
    const detail = await api.get(`/api/procedures/${params.slug}`);
    const p = detail.procedure || detail;
    return el("div", { class: "article-view" }, [
      el("button", { class: "btn btn-ghost btn-sm mb-16", text: `← ${tr("back")}`, onclick: () => location.hash = "#/procedures" }),
      el("h1", { text: p.title }),
      el("div", { class: "flex mt-8 mb-16", style: "flex-wrap:gap:8px" }, [
        p.category ? el("span", { class: "badge-pill badge-gold", text: p.category }) : null,
        p.typical_timeframe ? el("span", { class: "badge-pill badge-blue", text: p.typical_timeframe }) : null,
        p.fees ? el("span", { class: "badge-pill badge-warn", text: `${tr("fees")}: ${p.fees}` }) : null,
      ]),
      el("p", { class: "small muted", text: p.description || "" }),
      (p.steps || []).length ? el("div", { class: "mt-24" }, [
        el("h2", { text: tr("steps") }),
        renderSteps(p.steps),
      ]) : null,
      renderFaq(p.faq),
    ]);
  } catch {
    return el("div", { class: "card empty", text: tr("notFound") });
  }
}
