// نبراس — الحاسبات القانونية
import { tr, currentLang } from "../i18n.js";
import { api } from "../api.js";
import { el, emptyState, toast } from "../ui.js";
import { icon } from "../icons.js";

const CALC_FIELDS = [
  ["estate_value", "قيمة التركة (درهم)", "number", 1],
  ["spouse", "الزوج/الزوجة", "select", 0, ["none", "husband", "wife"]],
  ["sons", "عدد الأبناء", "number", 0],
  ["daughters", "عدد البنات", "number", 0],
  ["father", "الأب حي؟", "boolean", 0],
  ["mother", "الأم حية؟", "boolean", 0],
  ["full_brothers", "إخوة أشقاء", "number", 0],
  ["full_sisters", "أخوات شقيقات", "number", 0],
  ["maternal_brothers", "إخوة لأم", "number", 0],
  ["maternal_sisters", "أخوات لأم", "number", 0],
];

export async function calculatorsView() {
  const list = await api.get("/api/calculators");
  const data = Array.isArray(list) ? list : list.calculators || [];

  return el("div", {}, [
    el("div", { class: "section-head" }, [
      el("div", {}, [el("h2", { text: tr("calculatorsTitle") }), el("div", { class: "sub", text: tr("calculatorsSub") })]),
    ]),
    data.length ? el("div", { class: "grid grid-3" }, data.map((c) =>
      el("article", { class: "card card-hover" }, [
        el("div", { class: "calc-icon" }, [icon("calculator", 28)]),
        el("h3", { class: "card-title", text: c.name }),
        el("p", { class: "small muted", text: esc(c.legal_basis) }),
        el("button", { class: "btn btn-primary btn-block mt-8 btn-sm", text: "فتح الحاسبة", onclick: () => location.hash = `#/calculators/${c.slug}` }),
      ]))) : emptyState(tr("noResults"), "calculator"),
  ]);
}

export async function calculatorView(params) {
  const form = el("form", { class: "card article-view" });
  const inputs = {};

  for (const [name, label, type, required, options] of CALC_FIELDS) {
    let input;
    if (type === "select") {
      input = el("select", {},
        [el("option", { value: "none", text: "لا يوجد" }),
         el("option", { value: "husband", text: "زوج" }),
         el("option", { value: "wife", text: "زوجة" })]);
    } else if (type === "boolean") {
      input = el("div", { class: "checkbox" },
        [el("input", { type: "checkbox" }), el("span", { text: "نعم" })]);
    } else {
      input = el("input", { type, min: 0, step: type === "number" && name === "estate_value" ? "0.01" : "1", required: !!required });
    }
    inputs[name] = input;
    form.append(el("div", { class: "field" }, [
      el("label", { text: `${label}${required ? " *" : ""}` }),
      input,
    ]));
  }

  form.append(
    el("div", { class: "modal-actions" }, [
      el("button", { class: "btn btn-primary btn-block", type: "submit", text: "حساب" }),
    ]),
    el("div", { id: "calc-result", class: "mt-16" }),
  );

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {};
    for (const [name] of CALC_FIELDS) {
      const input = inputs[name];
      if (input.tagName === "SELECT") payload[name] = input.value;
      else if (input.tagName === "DIV") payload[name] = !!input.querySelector("input").checked;
      else payload[name] = input.value.trim() === "" ? 0 : Number(input.value);
    }
    try {
      const { result, legal_basis } = await api.post(`/api/calculators/${params.slug}/run`, payload);
      const box = form.querySelector("#calc-result");
      box.replaceChildren(
        el("div", { class: "legal-block" }, [
          el("strong", { text: `التركة: ${result.total_estate} درهم` }),
          el("p", { class: "small", text: result.method }),
          el("table", { class: "data-table" }, [
            el("thead", {}, [el("tr", {}, [
              el("th", { text: "الوارث" }), el("th", { text: "العدد" }),
              el("th", { text: "السهم" }), el("th", { text: "المبلغ" }),
              el("th", { text: "للفرد" })] )]),
            el("tbody", {}, result.heirs.map((h) =>
              el("tr", {}, [
                el("td", { text: h.heir }), el("td", { text: h.count }),
                el("td", { text: h.share }), el("td", { text: h.amount }),
                el("td", { text: h.amount_per_capita })] ))),
          ]),
          el("div", { class: "small muted", style: "margin-top:8px" },
            (legal_basis || []).map((b) => el("div", { text: `• ${b}` }))),
          (result.notes || []).map((n) => el("div", { class: "small muted", text: n })),
        ]),
      );
    } catch (err) { toast(err.message, "error"); }
  });

  return el("div", {}, [
    el("button", { class: "btn btn-ghost btn-sm mb-16", text: `← ${tr("back")}`, onclick: () => location.hash = "#/calculators" }),
    form,
  ]);
}

function esc(s) { return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }
