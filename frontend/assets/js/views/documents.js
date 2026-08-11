// نبراس — مولّد الوثائق القانونية
import { tr } from "../i18n.js";
import { api, session } from "../api.js";
import { el, esc, emptyState, toast, openModal, closeModal, truncate, downloadFile } from "../ui.js";
import { openAuth } from "./auth.js";
import { icon } from "../icons.js";

// ذاكرة مؤقتة لإعادة التوليد: {docId, templateSlug, answers}
let editDraft = null;

export function setEditDraft(draft) { editDraft = draft; }

function fieldInput(f, value) {
  let input;
  if (f.type === "textarea") {
    input = el("textarea", { required: !!f.required, rows: 3, placeholder: f.placeholder || f.label, value: value ?? "" });
  } else if (f.type === "select") {
    const opts = (f.options || []).map((o) =>
      el("option", { value: o, text: o, selected: value === o }));
    input = el("select", { required: !!f.required }, [el("option", { value: "", text: "— اختر —" }), ...opts]);
  } else if (f.type === "boolean") {
    input = el("select", { required: !!f.required },
      [el("option", { value: "", text: "—" }),
       el("option", { value: "true", text: "نعم", selected: value === true }),
       el("option", { value: "false", text: "لا", selected: value === false })]);
  } else {
    input = el("input", { type: f.type === "number" ? "number" : "text", required: !!f.required, placeholder: f.placeholder || f.label, value: value ?? "" });
    if (f.type === "date") input.type = "date";
    if (f.type === "number") {
      if (f.min != null) input.min = f.min;
      if (f.max != null) input.max = f.max;
      if (f.step != null) input.step = f.step;
    }
  }
  if (f.help) input.setAttribute("aria-describedby", "help-" + f.name);
  input.dataset.fieldType = f.type;
  return input;
}

function collectAnswers(inputs) {
  const answers = {};
  for (const [name, input] of Object.entries(inputs)) {
    let v = input.value.trim();
    if (input.type === "number" && v !== "") v = Number(v);
    else if (input.dataset.fieldType === "boolean") v = v === "true";
    answers[name] = v;
  }
  return answers;
}

export async function documentsView() {
  const list = await api.get("/api/documents/templates");
  const data = Array.isArray(list) ? list : list.templates || [];

  const cats = [...new Set(data.map((t) => t.category).filter(Boolean))];

  return el("div", {}, [
    el("div", { class: "section-head" }, [
      el("div", {}, [el("h2", { text: tr("documentsTitle") }), el("div", { class: "sub", text: tr("documentsSub") })]),
    ]),
    data.length ? el("div", { class: "grid grid-3" }, data.map((t) =>
      el("article", { class: "card card-hover" }, [
        el("div", { class: "flex-between mb-8" }, [
          t.category ? el("span", { class: "badge-pill badge-navy", text: t.category }) : null,
          el("span", { class: "badge-pill badge-gold", text: `${(t.fields ? t.fields.length : 0)} ${tr("fieldsCount")}` }),
        ]),
        el("h3", { class: "card-title", text: t.name }),
        t.description ? el("p", { class: "small muted", text: truncate(t.description, 110) }) : null,
        el("div", { class: "flex mt-10", style: "gap:8px" }, [
          el("button", { class: "btn btn-outline btn-sm", onclick: () => location.hash = `#/documents/${t.slug}` }, [icon("pen", 14), " " + tr("fill")]),
        ]),
      ]))) : emptyState(tr("noResults"), "file"),
    cats.length ? el("div", { class: "small muted mt-8", text: cats.join(" · ") }) : null,
  ]);
}

export async function myDocumentsView() {
  const data = await api.get("/api/documents/my");
  const docs = Array.isArray(data) ? data : data.documents || [];
  return el("div", {}, [
    el("div", { class: "section-head" }, [el("h2", {}, [icon("file", 18), " " + tr("myDocuments")])]),
    docs.length ? el("div", { class: "grid grid-2" }, docs.map((d) =>
      el("article", { class: "card card-hover" }, [
        el("div", { class: "flex-between mb-8" }, [
          el("strong", { class: "small", text: d.template_name }),
          el("span", { class: "badge-pill badge-gold", text: `v${d.version}` }),
        ]),
        el("pre", { class: "small muted", style: "white-space:pre-wrap;max-height:120px;overflow:auto", text: d.doc_text }),
        el("div", { class: "flex", style: "gap:8px;margin-top:10px;flex-wrap:wrap" }, [
          el("button", { class: "btn btn-primary btn-sm", onclick: () => downloadFile(`/api/documents/${d.id}/export?format=pdf`, `${d.template_slug}-v${d.version}.pdf`) }, [icon("download", 14), " PDF"]),
          el("button", { class: "btn btn-ghost btn-sm", onclick: () => downloadFile(`/api/documents/${d.id}/export?format=docx`, `${d.template_slug}-v${d.version}.docx`) }, [icon("download", 14), " DOCX"]),
          el("button", { class: "btn btn-outline btn-sm", onclick: () => { setEditDraft({ docId: d.id, templateSlug: d.template_slug, answers: d.answers || {} }); location.hash = `#/documents/${d.template_slug}`; } }, [icon("edit", 14), " " + tr("edit")]),
        ]),
      ]))) : emptyState(tr("noResults"), "file"),
  ]);
}

export async function documentDetailView(params) {
  const tmpl = await api.get(`/api/documents/templates/${params.slug}`);
  const fields = tmpl.fields || [];

  // استرجاع مسودة إعادة التوليد إن وُجدت
  const draft = editDraft && editDraft.templateSlug === tmpl.slug ? editDraft : null;
  const editing = !!draft;
  const isRegenerating = editing;
  const draftValues = draft?.answers || {};
  const hasPrefill = editing;

  const inputs = {};
  const form = el("form", { class: "card article-view" }, [
    el("div", { class: "flex-between" }, [
      el("button", { class: "btn btn-ghost btn-sm mb-16", text: `← ${tr("back")}`, onclick: () => location.hash = "#/documents" }),
      hasPrefill ? el("span", { class: "badge-pill badge-gold", text: tr("editingMode") }) : null,
    ]),
    el("h2", { text: tmpl.name }),
    tmpl.description ? el("p", { class: "sub", text: tmpl.description }) : null,
    ...fields.map((f) => {
      const value = draftValues[f.name];
      const input = fieldInput(f, value);
      inputs[f.name] = input;
      const help = f.help ? el("small", { class: "field-help", id: "help-" + f.name, text: f.help }) : null;
      return el("div", { class: "field" }, [el("label", { text: `${f.label}${f.required ? " *" : ""}` }), input, help]);
    }),
    el("div", { class: "field" }, [
      el("label", { text: tr("specialConditions") }),
      el("textarea", { id: "special-conditions", rows: 3, placeholder: tr("specialConditionsPh"), value: draftValues.special_conditions || "" }),
    ]),
    el("div", { class: "modal-actions" }, [
      el("button", { class: "btn btn-primary btn-block", type: "submit", text: isRegenerating ? tr("regenerate") : tr("generateDoc") }),
    ]),
    el("div", { id: "doc-result", class: "mt-16" }),
  ]);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!session.token) return openAuth("login");
    const answers = collectAnswers(inputs);
    const cond = form.querySelector("#special-conditions");
    if (cond && cond.value.trim()) answers.special_conditions = cond.value.trim();
    try {
      const url = isRegenerating ? `/api/documents/${draft.docId}/regenerate` : "/api/documents/generate";
      const payload = isRegenerating ? { answers } : { template_slug: tmpl.slug, answers };
      const doc = await api.post(url, payload);
      const box = form.querySelector("#doc-result");
      box.replaceChildren(
        el("div", { class: "legal-block" }, [
          el("div", { class: "flex-between" }, [
            el("strong", { text: `${doc.template_name} — v${doc.version}` }),
            el("button", { class: "btn btn-ghost btn-sm", text: tr("fillAgain"), onclick: () => { setEditDraft(null); location.hash = `#/documents/${tmpl.slug}`; } }),
          ]),
          el("pre", { style: "white-space:pre-wrap;font:inherit;margin:10px 0", text: doc.doc_text }),
          el("div", { class: "flex", style: "flex-wrap:wrap;gap:8px" }, [
            el("button", { class: "btn btn-primary btn-sm", onclick: () => downloadFile(`/api/documents/${doc.id}/export?format=pdf`, `${doc.template_slug}-v${doc.version}.pdf`) }, [icon("download", 14), " " + tr("download") + " PDF"]),
            el("button", { class: "btn btn-ghost btn-sm", onclick: () => downloadFile(`/api/documents/${doc.id}/export?format=docx`, `${doc.template_slug}-v${doc.version}.docx`) }, [icon("download", 14), " DOCX"]),
          ]),
        ]),
      );
      box.scrollIntoView({ behavior: "smooth", block: "nearest" });
      toast(tr("sent"), "success");
      if (isRegenerating) setEditDraft(null);
    } catch (err) { toast(err.message, "error"); }
  });

  return form;
}
