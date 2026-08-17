// نبراس — إدارة الاجتهادات القضائية (لوحة الإدارة): قائمة + إضافة/تعديل + نشر/حذف + فئات
import {
  el, api, t, head, panel, body, badge, confirmDialog,
  openModal, closeModal, toast, emptyState, skeleton,
  fmtDt, input, select, field, num, tabs,
} from "../ui.js";

export function jurisprudenceAdminView() {
  let active = "decisions";
  const container = el("div", { class: "flex-col", style: "gap:16px" });
  function render() {
    container.replaceChildren(tabs([
      { key: "decisions", label: t("jurisAdminTitle") },
      { key: "categories", label: t("jurisAdminCategories") },
    ], active, (k) => { active = k; render(); }));
    const p = active === "decisions" ? decisionsPanel() : categoriesPanel();
    p.then((node) => container.replaceChildren(node)).catch((e) =>
      container.replaceChildren(el("div", { class: "adm-404", text: String(e?.message || e) })));
  }
  render();
  return container;
}

async function decisionsPanel() {
  const box = el("div", { class: "flex-col", style: "gap:16px" });
  const tbody = el("tbody", {});
  const searchIn = input({ placeholder: t("search") });

  async function draw() {
    tbody.replaceChildren(el("tr", {}, el("td", { colspan: 8 }, skeleton(2, 60))));
    const params = new URLSearchParams();
    if (searchIn.value.trim()) params.set("q", searchIn.value.trim());
    let list = [];
    try { list = (await api.get(`/admin/jurisprudence?${params.toString()}`)) || []; }
    catch (e) { list = []; }
    tbody.replaceChildren(list.length
      ? list.map((d) => el("tr", {}, [
          el("td", { text: `#${d.id}` }),
          el("td", {}, el("strong", { text: d.title || "—" })),
          el("td", { text: d.category_name || "—" }),
          el("td", { text: d.court || "—" }),
          el("td", { text: d.decision_date ? fmtDt(d.decision_date) : "—" }),
          el("td", {}, [d.published ? badge(t("published"), "green") : badge(t("draft"), "gray")]),
          el("td", { text: num(d.views) }),
          el("td", {}, [
            el("div", { class: "flex", style: "gap:6px" }, [
              el("button", { class: "btn btn-ghost btn-sm", text: t("edit"), onclick: () => decisionModal(d, draw) }),
              el("button", { class: "btn btn-ghost btn-sm", text: d.published ? t("unpublish") : t("publish"), onclick: async () => {
                try {
                  await api.post(`/api/admin/jurisprudence/${d.id}/publish`, { published: !d.published });
                  toast(t("saved"), "success"); draw();
                } catch (e) { toast(e.message, "error"); }
              } }),
              el("button", { class: "btn btn-danger btn-sm", text: t("delete"), onclick: async () => {
                if (!(await confirmDialog({ title: t("deleteConfirm"), text: `#${d.id}` }))) return;
                try { await api.del(`/api/admin/jurisprudence/${d.id}`); toast(t("deleted"), "success"); draw(); }
                catch (e) { toast(e.message, "error"); }
              } }),
            ]),
          ]),
        ]))
      : el("tr", {}, el("td", { colspan: 8 }, emptyState(t("noData"), "scale"))));
  }
  searchIn.addEventListener("input", () => draw());

  box.append(
    el("div", { class: "adm-toolbar" }, [
      searchIn,
      el("span", { class: "spacer" }),
      el("button", { class: "btn btn-primary btn-sm", text: "+ " + t("jurisAdminAdd"), onclick: () => decisionModal(null, draw) }),
    ]),
    panel([head(t("jurisAdminTitle"), []), body(el("div", { class: "adm-tbl-wrap" }, [el("table", { class: "adm-tbl" }, [
      el("thead", {}, el("tr", {}, [
        el("th", { text: t("id") }), el("th", { text: t("title") }), el("th", { text: t("category") }),
        el("th", { text: t("court") }), el("th", { text: t("date") }), el("th", { text: t("status") }),
        el("th", { text: t("views") }), el("th", { text: t("actions") }),
      ])),
      tbody,
    ])]))]),
  );
  await draw();
  return box;
}

function decisionModal(d, onDone) {
  const titleI = input({ value: d?.title || "" });
  const contentI = input({ value: d?.content || "" });
  const principlesI = input({ value: d?.principles || "" });
  const catEl = select({}, [el("option", { value: "", text: "--" })]);
  const courtI = input({ value: d?.court || "" });
  const numI = input({ value: d?.decision_number || "" });
  const dateI = input({ type: "date", value: d?.decision_date || "" });
  const srcI = input({ value: d?.source_note || "" });
  const jurS = select({}, [el("option", { value: "", text: "—" })]);
  (async () => {
    try {
      const data = await api.get("/api/comparative/jurisdictions");
      const juris = data.jurisdictions || [];
      jurS.replaceChildren(el("option", { value: "", text: "—" }),
        ...juris.map((j) => el("option", { value: String(j.id), text: j.name })));
      if (d?.jurisdiction_id) jurS.value = String(d.jurisdiction_id);
    } catch { }
  })();

  (async () => {
    try {
      const cats = (await api.get("/api/admin/jurisprudence/categories")) || [];
      cats.forEach((c) => catEl.append(el("option", { value: c.slug, text: c.name })));
      if (d?.category_slug) catEl.value = d.category_slug;
    } catch { }
  })();

  openModal(el("div", {}, [
    el("h2", { text: d ? t("editDecision") : t("jurisAdminAdd") }),
    el("div", { class: "adm-grid-2" }, [
      field(t("title") + " *", titleI),
      field(t("category"), catEl),
    ]),
    field(t("jurisdiction") + " (" + t("comparative") + ")", jurS),
    field(t("court"), courtI),
    el("div", { class: "adm-grid-2" }, [
      field(t("decisionNr"), numI),
      field(t("decisionDate"), dateI),
    ]),
    field(t("jurisPrinciples"), principlesI),
    field(t("jurisContent") + " *", contentI),
    field(t("jurisSource"), srcI),
    el("div", { class: "modal-actions" }, [
      el("button", { class: "btn btn-ghost", text: t("cancel"), onclick: closeModal }),
      el("button", { class: "btn btn-primary", text: t("save"), onclick: async () => {
        if (!titleI.value.trim() || !contentI.value.trim()) return toast(t("required"), "warn");
        const payload = {
          title: titleI.value.trim(),
          content: contentI.value.trim(),
          principles: principlesI.value.trim() || "",
          category_slug: catEl.value || "",
          jurisdiction_id: jurS.value ? Number(jurS.value) : undefined,
          court: courtI.value.trim() || "",
          decision_number: numI.value.trim() || "",
          decision_date: dateI.value || "",
          source_note: srcI.value.trim() || "",
          published: d ? d.published : true,
        };
        try {
          if (d) await api.put(`/api/admin/jurisprudence/${d.id}`, payload);
          else await api.post("/api/admin/jurisprudence", payload);
          closeModal(); toast(t("saved"), "success"); onDone && onDone();
        } catch (e) { toast(e.message, "error"); }
      } }),
    ]),
  ]));
}

async function categoriesPanel() {
  const box = el("div", { class: "flex-col", style: "gap:16px" });
  const node = el("div", { class: "adm-grid-2" });
  async function draw() {
    node.replaceChildren(skeleton(2, 80));
    let cats = [];
    try { cats = (await api.get("/admin/jurisprudence/categories")) || []; }
    catch (e) { cats = []; }
    node.replaceChildren(cats.length
      ? cats.map((c) => panel([
          head(c.name, [
            el("button", { class: "btn btn-ghost btn-sm", text: t("edit"), onclick: () => catModal(c, draw) }),
            el("button", { class: "btn btn-danger btn-sm", text: t("delete"), onclick: async () => {
              if (!(await confirmDialog({ title: t("deleteConfirm"), text: c.name }))) return;
              try { await api.del(`/admin/jurisprudence/categories/${c.id}`); toast(t("deleted"), "success"); draw(); }
              catch (e) { toast(e.message, "error"); }
            } }),
          ]),
          body(el("div", { class: "flex-col", style: "gap:6px" }, [
            el("span", { class: "small muted", text: `slug: ${c.slug}` }),
            el("span", { class: "small muted", text: `${c.decision_count ?? 0} ${t("decisions")}` }),
            el("span", { class: "small muted", text: c.description || "" }),
          ])),
        ]))
      : emptyState(t("noData"), "folder"));
  }
  box.append(
    el("div", { class: "adm-toolbar" }, [
      el("span", { class: "spacer" }),
      el("button", { class: "btn btn-primary btn-sm", text: "+ " + t("addCategory"), onclick: () => catModal(null, draw) }),
    ]),
    node,
  );
  await draw();
  return box;
}

function catModal(c, onDone) {
  const nameI = input({ value: c?.name || "" });
  const slugI = input({ value: c?.slug || "" });
  const descI = input({ value: c?.description || "" });
  openModal(el("div", {}, [
    el("h2", { text: c ? t("editCategory") : t("addCategory") }),
    el("div", { class: "adm-grid-2" }, [
      field(t("name") + " *", nameI),
      field(t("slug") + " (a-z)", slugI),
    ]),
    field(t("description"), descI),
    el("div", { class: "modal-actions" }, [
      el("button", { class: "btn btn-ghost", text: t("cancel"), onclick: closeModal }),
      el("button", { class: "btn btn-primary", text: t("save"), onclick: async () => {
        if (!nameI.value.trim() || !slugI.value.trim()) return toast(t("required"), "warn");
        const payload = { name: nameI.value.trim(), slug: slugI.value.trim(), description: descI.value.trim() || "" };
        try {
          if (c) await api.put(`/admin/jurisprudence/categories/${c.id}`, payload);
          else await api.post("/admin/jurisprudence/categories", payload);
          closeModal(); toast(t("saved"), "success"); onDone && onDone();
        } catch (e) { toast(e.message, "error"); }
      } }),
    ]),
  ]));
}