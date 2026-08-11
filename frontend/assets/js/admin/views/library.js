// نبراس — إدارة المكتبة القانونية (نصوص + مواد + مساطر + استيعاب)
import {
  el, api, t, head, panel, body, badge, tabs, confirmDialog,
  openModal, closeModal, toast, emptyState, skeleton, pagination,
  fmtDt, input, select, field, typeLabel,
} from "../ui.js";
import { icon } from "../../icons.js";

function textTypeOptions(sel) {
  return ["constitution", "code", "law", "decree", "gazette", "treaty", "ruling",
          "organic_law", "dahir", "dahir_law", "royal_decree", "decision"].map((v) =>
    el("option", { value: v, text: typeLabel(v) }));
}

const paginate = (arr, page, per) => arr.slice((page - 1) * per, page * per);
const PER = 10;

// =====================================================================
// القسم الرئيسي
// =====================================================================
export function libraryView(initial = "texts") {
  let active = initial;
  const container = el("div", { class: "flex-col", style: "gap:16px" });
  const swap = (node) => {
    container.replaceChildren(container.firstChild, node);
  };
  function render() {
    container.replaceChildren(tabs([
      { key: "texts", label: t("textsTitle") },
      { key: "procedures", label: t("procedures") },
      { key: "ingestion", label: t("ingestion") },
    ], active, (k) => { active = k; render(); }));
    swap(skeleton(3, 90));
    const p = active === "texts" ? textsPanel()
      : active === "procedures" ? proceduresPanel() : ingestionPanel();
    p.then(swap).catch((e) => swap(el("div", { class: "adm-404", text: String(e?.message || e) })));
  }
  render();
  return container;
}

// =====================================================================
// النصوص القانونية
// =====================================================================
async function textsPanel() {
  const [data, cats] = await Promise.all([
    api.get("/api/texts?limit=100"),
    api.get("/api/categories").catch(() => []),
  ]);
  const rows = data.texts || data || [];
  const catsList = Array.isArray(cats) ? cats : (cats?.categories || []);

  let page = 1;
  let q = "", typeF = "", catF = "";
  const box = el("div", { class: "flex-col", style: "gap:14px" });

  const searchI = el("input", {
    type: "search", placeholder: t("search"), "aria-label": t("search"),
    oninput: (e) => { q = e.target.value.trim().toLowerCase(); page = 1; draw(); },
  });
  const typeS = select({ onchange: (e) => { typeF = e.target.value; page = 1; draw(); } },
    [el("option", { value: "", text: t("all") + " — " + t("type") }), ...textTypeOptions()]);
  const catS = select({ onchange: (e) => { catF = e.target.value; page = 1; draw(); } },
    [el("option", { value: "", text: t("all") + " — " + t("category") }),
     ...catsList.map((c) => el("option", { value: String(c.id), text: c.name }))]);
  const newBtn = el("button", { class: "btn btn-primary btn-sm", text: "+ " + t("newText"),
    onclick: () => textModal(null, catsList, () => draw()) });
  const refreshBtn = el("button", { class: "btn btn-ghost btn-sm", text: "↻ " + t("refresh"), onclick: () => draw() });

  const tbody = el("tbody");
  const table = el("table", { class: "adm-tbl" }, [
    el("thead", {}, el("tr", {}, [
      el("th", { text: t("title") }), el("th", { text: t("category") }),
      el("th", { text: t("type") }), el("th", { text: t("articlesCount") }),
      el("th", { text: t("officialRef") }), el("th", { text: t("enactedDate") }),
      el("th", { text: t("status") }), el("th", { text: t("actions") }),
    ])),
    tbody,
  ]);
  const pager = el("div", { class: "adm-pager" });
  const listPanel = panel([head(t("textsTitle"), [refreshBtn, newBtn]), body(el("div", { class: "adm-tbl-wrap" }, [table])), pager]);

  function filtered() {
    return rows.filter((r) => {
      if (q && !((r.title || "").toLowerCase().includes(q))) return false;
      if (typeF && r.type !== typeF) return false;
      if (catF && String(r.category_id) !== catF) return false;
      return true;
    });
  }
  function draw() {
    const f = filtered();
    tbody.replaceChildren(...paginate(f, page, PER).map(textRow));
    pager.replaceChildren(
      el("span", { class: "meta", text: `${f.length} ${t("total")}` }),
      f.length > PER ? pagination(f.length, page, PER, (p) => { page = p; draw(); }) : null,
    );
  }
  draw();
  box.append(
    el("div", { class: "adm-toolbar" }, [searchI, typeS, catS, el("span", { class: "spacer" })]),
    listPanel,
  );
  return box;

  function textRow(r) {
    return el("tr", {}, [
      el("td", { class: "cell-main" }, [
        el("span", { class: "t", text: r.title }),
        el("span", { class: "s", text: [r.official_ref, r.last_amended].filter(Boolean).join(" · ") }),
      ]),
      el("td", { text: r.category_name || r.category_slug || "—" }),
      el("td", { text: typeLabel(r.type) }),
      el("td", { class: "num", text: String(r.article_count ?? 0) }),
      el("td", { class: "sub", text: r.official_ref || "—" }),
      el("td", { class: "sub", text: r.enacted_date || "—" }),
      el("td", {}, Number(r.is_sample_data) === 1 ? badge(t("sampleData"), "gold") : badge(t("realData"), "green")),
      el("td", {}, el("div", { class: "adm-actions" }, [
        el("a", { class: "btn btn-ghost btn-sm", href: `/api/texts/${r.id}/pdf`, target: "_blank", rel: "noopener", text: "PDF" }),
        el("button", { class: "btn btn-ghost btn-sm", text: t("manageArticles"), onclick: () => articlesModal(r) }),
        el("button", { class: "btn btn-ghost btn-sm", text: t("replacePdf"), onclick: () => pdfModal(r, () => draw()) }),
        el("button", { class: "btn btn-ghost btn-sm", text: t("edit"), onclick: () => textModal(r, catsList, () => draw()) }),
        el("button", { class: "btn btn-danger btn-sm", text: t("delete"), onclick: async () => {
          if (!(await confirmDialog({ title: t("deleteText"), text: `${r.title}؟`, danger: true }))) return;
          try { await api.del(`/api/admin/texts/${r.id}`); toast(t("saved"), "success"); draw(); }
          catch (e) { toast(e.message, "error"); }
        } }),
      ])),
    ]);
  }
}

function textModal(r, cats, onDone) {
  const title = input({ value: r?.title || "", placeholder: t("title") });
  const typeS = select({}, textTypeOptions());
  if (r?.type) typeS.value = r.type;
  const catS = select({}, [
    el("option", { value: "", text: t("category") + "..." }),
    ...(cats || []).map((c) => el("option", { value: String(c.id), text: c.name })),
  ]);
  if (r?.category_id) catS.value = String(r.category_id);
  const officialRef = input({ value: r?.official_ref || "", placeholder: t("officialRef") });
  const enacted = el("input", { type: "date", value: r?.enacted_date || "" });
  const amended = el("input", { type: "date", value: r?.last_amended || "" });
  const source = el("textarea", { text: r?.source_note || "", placeholder: t("sourceNote") });
  const sampleCb = el("input", { type: "checkbox" });
  sampleCb.checked = r ? Number(r.is_sample_data) === 1 : true;

  openModal(el("div", {}, [
    el("h2", { text: r ? t("editText") : t("newText") }),
    field(t("title") + " *", title),
    el("div", { class: "adm-grid-2" }, [
      field(t("category") + " *", catS),
      field(t("type") + " *", typeS),
    ]),
    field(t("officialRef"), officialRef),
    el("div", { class: "adm-grid-2" }, [
      field(t("enactedDate"), enacted),
      field(t("lastAmended"), amended),
    ]),
    field(t("sourceNote"), source),
    el("div", { class: "field" }, [
      el("label", { class: "flex", style: "gap:8px;align-items:center;cursor:pointer" }, [
        sampleCb, el("span", { text: t("sampleData") }),
      ]),
    ]),
    el("div", { class: "modal-actions" }, [
      el("button", { class: "btn btn-ghost", text: t("cancel"), onclick: closeModal }),
      el("button", { class: "btn btn-primary", text: t("save"), onclick: async () => {
        if (!title.value.trim() || !catS.value || !typeS.value) return toast(t("required"), "warn");
        const payload = {
          title: title.value.trim(), category_id: Number(catS.value), type: typeS.value,
          official_ref: officialRef.value.trim() || undefined,
          enacted_date: enacted.value || undefined, last_amended: amended.value || undefined,
          source_note: source.value.trim() || undefined,
          is_sample_data: sampleCb.checked ? 1 : 0,
        };
        try {
          if (r) await api.put(`/api/admin/texts/${r.id}`, payload);
          else await api.post("/api/admin/texts", payload);
          closeModal(); toast(t("saved"), "success"); onDone && onDone();
        } catch (e) { toast(e.message, "error"); }
      } }),
    ]),
  ]));
}

function pdfModal(r, onDone) {
  const file = el("input", { type: "file", accept: "application/pdf" });
  openModal(el("div", {}, [
    el("h2", { text: `${t("replacePdf")} — ${r.title}` }),
    field(t("templateFile"), file),
    el("div", { class: "modal-actions" }, [
      el("button", { class: "btn btn-ghost", text: t("cancel"), onclick: closeModal }),
      el("button", { class: "btn btn-primary", text: t("upload"), onclick: async () => {
        if (!file.files[0]) return toast(t("fileRequired"), "warn");
        try {
          await api.upload(`/api/admin/texts/${r.id}/pdf`, file.files[0]);
          closeModal(); toast(t("saved"), "success"); onDone && onDone();
        } catch (e) { toast(e.message, "error"); }
      } }),
    ]),
  ]));
}

async function articlesModal(text) {
  let data;
  try { data = await api.get(`/api/texts/${text.id}`); } catch (e) { return toast(e.message, "error"); }
  const arts = data.articles || data || [];
  const listWrap = el("div", { class: "flex-col", style: "gap:8px" });
  function draw() {
    listWrap.replaceChildren(
      arts.length ? arts.map((a) =>
        el("div", { class: "adm-list-item", style: "border:1px solid var(--line);border-radius:10px" }, [
          el("div", { class: "grow" }, [
            el("div", { class: "t", text: `${a.label || a.number || ""}` }),
            el("div", { class: "s", text: String(a.content || "").slice(0, 120) + (String(a.content || "").length > 120 ? "…" : "") }),
          ]),
          el("div", { class: "adm-actions" }, [
            el("button", { class: "btn btn-ghost btn-sm", text: t("edit"), onclick: () => articleModal(a, () => draw(), text.id) }),
            el("button", { class: "btn btn-danger btn-sm", text: t("delete"), onclick: async () => {
              if (!(await confirmDialog({ title: t("deleteArticle"), text: `${a.label || a.number || ""}؟` }))) return;
              try { await api.del(`/api/admin/articles/${a.id}`); arts.splice(arts.indexOf(a), 1); draw(); }
              catch (e) { toast(e.message, "error"); }
            } }),
          ]),
        ])) : emptyState(t("noData"), "file"),
      el("button", { class: "btn btn-primary btn-sm", style: "align-self:flex-start", text: "+ " + t("newArticle"),
        onclick: () => articleModal(null, (created) => { arts.push(created); draw(); }, text.id) }),
    );
  }
  draw();
  openModal(el("div", {}, [
    el("h2", { text: `${t("manageArticles")} — ${text.title}` }),
    listWrap,
    el("div", { class: "modal-actions" }, [el("button", { class: "btn btn-ghost", text: t("close"), onclick: closeModal })]),
  ]));
}

function articleModal(a, onDone, textId) {
  const number = input({ value: a?.number || "", placeholder: t("articleNumber") });
  const label = input({ value: a?.label || "", placeholder: t("articleLabel") });
  const content = el("textarea", { text: a?.content || "", placeholder: t("articleContent") });
  const plain = el("textarea", { text: a?.plain_explanation || "", placeholder: t("plainExplanation") });
  const keywords = input({ value: a?.keywords || "", placeholder: t("keywords") });
  openModal(el("div", {}, [
    el("h2", { text: a ? t("editArticle") : t("newArticle") }),
    el("div", { class: "adm-grid-2" }, [
      field(t("articleNumber"), number),
      field(t("articleLabel"), label),
    ]),
    field(t("articleContent") + " *", content),
    field(t("plainExplanation"), plain),
    field(t("keywords"), keywords),
    el("div", { class: "modal-actions" }, [
      el("button", { class: "btn btn-ghost", text: t("cancel"), onclick: closeModal }),
      el("button", { class: "btn btn-primary", text: t("save"), onclick: async () => {
        if (!content.value.trim()) return toast(t("required"), "warn");
        const payload = {
          number: number.value.trim() || "0", label: label.value.trim() || t("articleLabel"),
          content: content.value.trim(), plain_explanation: plain.value.trim() || undefined,
          keywords: keywords.value.trim() || undefined,
        };
        try {
          if (a) { await api.put(`/api/admin/articles/${a.id}`, payload); Object.assign(a, payload); }
          else { const created = await api.post(`/api/admin/texts/${textId}/articles`, payload); payload.id = created.id; }
          closeModal(); toast(t("saved"), "success"); onDone && onDone();
        } catch (e) { toast(e.message, "error"); }
      } }),
    ]),
  ]));
}

// =====================================================================
// المساطر
// =====================================================================
async function proceduresPanel() {
  const data = await api.get("/api/admin/procedures");
  const rows = data.procedures || data || [];
  const box = el("div", { class: "flex-col", style: "gap:14px" });
  const tbody = el("tbody");
  const newBtn = el("button", { class: "btn btn-primary btn-sm", text: "+ " + t("new"),
    onclick: () => procedureModal(null, () => draw()) });
  function draw() {
    tbody.replaceChildren(rows.length ? rows.map((p) =>
      el("tr", {}, [
        el("td", { class: "cell-main" }, [
          el("span", { class: "t", text: p.title }),
          el("span", { class: "s", text: [p.category, p.slug].filter(Boolean).join(" · ") }),
        ]),
        el("td", { text: t("procedures") + ": " + String(p.step_count ?? 0) }),
        el("td", { class: "sub", text: p.fees || "—" }),
        el("td", { class: "sub", text: fmtDt(p.created_at) }),
        el("td", {}, el("div", { class: "adm-actions" }, [
          el("button", { class: "btn btn-ghost btn-sm", text: t("edit"), onclick: () => procedureModal(p, () => draw()) }),
          el("button", { class: "btn btn-danger btn-sm", text: t("delete"), onclick: async () => {
            if (!(await confirmDialog({ title: t("delete"), text: `${p.title}؟` }))) return;
            try { await api.del(`/api/admin/procedures/${p.id}`); rows.splice(rows.indexOf(p), 1); draw(); }
            catch (e) { toast(e.message, "error"); }
          } }),
        ])),
      ])) : emptyState(t("noData"), "scale"));
  }
  draw();
  box.append(panel([head(t("procedures"), [newBtn]), body(el("div", { class: "adm-tbl-wrap" }, [el("table", { class: "adm-tbl" }, [
    el("thead", {}, el("tr", {}, [
      el("th", { text: t("title") }), el("th", { text: t("stepTitle") }),
      el("th", { text: t("fees") }), el("th", { text: t("createdAt") }), el("th", { text: t("actions") }),
    ])),
    tbody,
  ])]))]));
  return box;
}

function procedureModal(p, onDone) {
  const slug = input({ value: p?.slug || "", placeholder: t("slug") });
  const title = input({ value: p?.title || "", placeholder: t("title") });
  const category = input({ value: p?.category || "", placeholder: t("category") });
  const fees = input({ value: p?.fees || "", placeholder: t("fees") });
  const desc = el("textarea", { text: p?.description || "", placeholder: t("description") });
  const stepRows = el("div", { class: "flex-col", style: "gap:0" });
  const stepData = [];
  function addStep(st = {}) {
    const sTitle = input({ value: st.title || "", placeholder: t("stepTitle") });
    const sDesc = el("textarea", { style: "min-height:52px", text: st.description || "", placeholder: t("stepDesc") });
    const row = el("div", { class: "adm-step-row" }, [
      sTitle, sDesc,
      el("button", { class: "btn btn-danger btn-sm", type: "button", text: "×",
        onclick: () => { row.remove(); stepData.splice(stepData.indexOf(rec), 1); } }),
    ]);
    const rec = { title: sTitle, desc: sDesc };
    stepData.push(rec);
    stepRows.append(row);
  }
  let steps = [];
  try { steps = Array.isArray(p?.steps) ? p.steps : (typeof p?.steps === "string" ? JSON.parse(p.steps || "[]") : []); } catch { steps = []; }
  (steps.length ? steps : [{}]).forEach(addStep);

  openModal(el("div", {}, [
    el("h2", { text: p ? t("editProcedure") || t("edit") : t("addProcedure") }),
    el("div", { class: "adm-grid-2" }, [
      field(t("slug") + " *", slug),
      field(t("category"), category),
    ]),
    field(t("title") + " *", title),
    field(t("fees"), fees),
    field(t("description"), desc),
    field(t("stepTitle"), stepRows),
    el("button", { class: "btn btn-ghost btn-sm", type: "button", text: "+ " + t("addStep"), onclick: () => addStep() }),
    el("div", { class: "modal-actions" }, [
      el("button", { class: "btn btn-ghost", text: t("cancel"), onclick: closeModal }),
      el("button", { class: "btn btn-primary", text: t("save"), onclick: async () => {
        if (!slug.value.trim() || !title.value.trim()) return toast(t("required"), "warn");
        const stepsPayload = stepData.map((s, i) => ({
          step_number: i + 1, title: s.title.value.trim(), description: s.desc.value.trim(),
        })).filter((s) => s.title);
        if (!stepsPayload.length) return toast(t("required"), "warn");
        const payload = {
          slug: slug.value.trim(), title: title.value.trim(), category: category.value.trim() || undefined,
          fees: fees.value.trim() || undefined, description: desc.value.trim() || undefined,
          steps: stepsPayload,
        };
        try {
          if (p) await api.put(`/api/admin/procedures/${p.id}`, payload);
          else await api.post("/api/admin/procedures", payload);
          closeModal(); toast(t("saved"), "success"); onDone && onDone();
        } catch (e) { toast(e.message, "error"); }
      } }),
    ]),
  ]));
}

// =====================================================================
// استيعاب الوثائق
// =====================================================================
async function ingestionPanel() {
  const cats = await api.get("/api/categories").catch(() => []);
  const catsList = Array.isArray(cats) ? cats : (cats?.categories || []);
  const box = el("div", { class: "flex-col", style: "gap:14px" });
  const result = el("div");

  const file = el("input", { type: "file", accept: ".pdf,.docx,application/pdf" });
  const title = input({ placeholder: t("title") + " *" });
  const catS = select({}, [
    el("option", { value: "", text: t("category") + "..." }),
    ...catsList.map((c) => el("option", { value: String(c.id), text: c.name })),
  ]);
  const typeS = select({}, textTypeOptions());
  const dryCb = el("input", { type: "checkbox" });
  dryCb.checked = true;
  const submitBtn = el("button", { class: "btn btn-primary", text: t("preview"), type: "submit" });
  const form = el("form", { class: "adm-panel-body flex-col", style: "gap:14px" }, [
    el("h3", { text: t("importDoc") }),
    el("div", { class: "adm-grid-2" }, [
      field(t("title") + " *", title),
      field(t("category") + " *", catS),
    ]),
    field(t("type") + " *", typeS),
    field(t("templateFile"), file, ".pdf · .docx"),
    el("div", { class: "field" }, [
      el("label", { class: "flex", style: "gap:8px;align-items:center;cursor:pointer" }, [
        dryCb, el("span", { text: t("dryRun") }),
      ]),
    ]),
    el("div", { class: "modal-actions" }, [submitBtn]),
  ]);
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!title.value.trim() || !catS.value || !typeS.value) return toast(t("required"), "warn");
    if (!file.files[0]) return toast(t("fileRequired"), "warn");
    submitBtn.disabled = true;
    try {
      const fd = new FormData();
      fd.append("file", file.files[0]);
      fd.append("title", title.value.trim());
      fd.append("category_id", catS.value);
      fd.append("type", typeS.value);
      if (dryCb.checked) fd.append("dry_run", "1");
      const res = await api.uploadFields("/api/admin/ingestion/import", fd);
      const notes = [];
      if (res.warnings?.length) notes.push(el("div", {}, [
        el("strong", { text: t("importWarnings") }), el("ul", {}, res.warnings.map((w) => el("li", { text: String(w) }))),
      ]));
      result.replaceChildren(el("div", { class: "adm-notice info" }, [
        el("span", { class: "ic" }, [icon("checkCircle", 20)]),
        el("div", {}, [
          el("h4", { text: t("importResult") }),
          el("p", { text: `${t("title")}: ${res.title} · ${t("articlesCount")}: ${res.article_count}` }),
          notes,
          dryCb.checked ? el("button", { class: "btn btn-primary btn-sm", style: "margin-top:10px", text: t("commitImport"), onclick: async () => {
            dryCb.checked = false;
            form.requestSubmit();
          } }) : null,
        ]),
      ]));
    } catch (err) { toast(err.message, "error"); }
    finally { submitBtn.disabled = false; }
  });

  box.append(panel([body(form)]), result);
  return box;
}
