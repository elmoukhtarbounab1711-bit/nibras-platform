// نبراس — إدارة القانون المقارن (لوحة الإدارة): ولايات قضائية + دراسات (نشر/إخفاء/حذف)
import {
  el, api, t, head, panel, body, badge, confirmDialog,
  openModal, closeModal, toast, emptyState, skeleton,
  fmtDt, input, select, field, tabs, icon,
} from "../ui.js";

const STATUS_FILTERS = ["published", "draft"];

export function comparativeAdminView() {
  let active = "studies";
  const container = el("div", { class: "flex-col", style: "gap:16px" });
  function render() {
    container.replaceChildren(tabs([
      { key: "studies", label: t("comparativeStudiesAdmin") },
      { key: "jurisdictions", label: t("comparativeJurisdictions") },
    ], active, (k) => { active = k; render(); }));
    const p = active === "studies" ? studiesPanel() : jurisdictionsPanel();
    p.then((node) => container.replaceChildren(node)).catch((e) =>
      container.replaceChildren(el("div", { class: "adm-404", text: String(e?.message || e) })));
  }
  render();
  return container;
}

async function studiesPanel() {
  const box = el("div", { class: "flex-col", style: "gap:16px" });
  const tbody = el("tbody", {});
  const searchIn = input({ placeholder: t("search") });
  const statusS = select({}, [
    el("option", { value: "", text: t("all") }),
    ...STATUS_FILTERS.map((s) => el("option", { value: s, text: t(s) })),
  ]);

  async function draw() {
    tbody.replaceChildren(el("tr", {}, el("td", { colspan: 6 }, skeleton(2, 60))));
    const params = new URLSearchParams();
    if (searchIn.value.trim()) params.set("q", searchIn.value.trim());
    if (statusS.value) params.set("status", statusS.value);
    let list = [];
    try {
      const data = await api.get(`/api/admin/comparative/studies?${params.toString()}`);
      list = data.studies || [];
    } catch (e) { list = []; }
    tbody.replaceChildren(list.length
      ? list.map((d) => el("tr", {}, [
          el("td", { text: `#${d.id}` }),
          el("td", {}, el("strong", { text: d.title || "—" })),
          el("td", { text: d.creator_name || "—" }),
          el("td", { text: d.entry_count ?? 0 }),
          el("td", {}, [d.status === "published" ? badge(t("published"), "green") : badge(t("draft"), "gray")]),
          el("td", {}, [
            el("div", { class: "flex", style: "gap:6px" }, [
              d.status !== "published"
                ? el("button", { class: "btn btn-ghost btn-sm" }, [icon("eye", 14), " " + t("publish")],
                    { onclick: () => setStatus(d, "published", draw) })
                : el("button", { class: "btn btn-ghost btn-sm" }, [icon("eyeOff", 14), " " + t("unpublish")],
                    { onclick: () => setStatus(d, "draft", draw) }),
              el("button", { class: "btn btn-danger btn-sm", text: t("delete"), onclick: async () => {
                if (!(await confirmDialog({ title: t("deleteConfirm"), text: `#${d.id} ${d.title || ""}` }))) return;
                try { await api.del(`/api/comparative/studies/${d.id}`); toast(t("deleted"), "success"); draw(); }
                catch (e) { toast(e.message, "error"); }
              } }),
            ]),
          ]),
        ]))
      : el("tr", {}, el("td", { colspan: 6 }, emptyState(t("noData"), "globe"))));
  }
  searchIn.addEventListener("input", () => draw());
  statusS.addEventListener("change", () => draw());

  async function setStatus(d, status, redraw) {
    try { await api.put(`/api/admin/comparative/studies/${d.id}/status`, { status }); toast(t("saved"), "success"); redraw(); }
    catch (e) { toast(e.message, "error"); }
  }

  box.append(
    el("div", { class: "adm-toolbar" }, [
      searchIn,
      statusS,
      el("span", { class: "spacer" }),
    ]),
    panel([head(t("comparativeStudiesAdmin"), []), body(el("div", { class: "adm-tbl-wrap" }, [el("table", { class: "adm-tbl" }, [
      el("thead", {}, el("tr", {}, [
        el("th", { text: t("id") }), el("th", { text: t("title") }), el("th", { text: t("author") }),
        el("th", { text: t("comparativeEntries") }), el("th", { text: t("status") }), el("th", { text: t("actions") }),
      ])),
      tbody,
    ])]))]),
  );
  await draw();
  return box;
}

async function jurisdictionsPanel() {
  const box = el("div", { class: "flex-col", style: "gap:16px" });
  const node = el("div", { class: "adm-grid-2" });
  async function draw() {
    node.replaceChildren(skeleton(2, 80));
    let juris = [];
    try {
      const data = await api.get("/api/admin/comparative/jurisdictions");
      juris = data.jurisdictions || [];
    } catch (e) { juris = []; }
    node.replaceChildren(juris.length
      ? juris.map((j) => panel([
          head(j.name, [
            el("button", { class: "btn btn-ghost btn-sm", text: t("edit"), onclick: () => jurisModal(j, draw) }),
            el("button", { class: "btn btn-danger btn-sm", text: t("delete"), onclick: async () => {
              if (!(await confirmDialog({ title: t("deleteConfirm"), text: j.name }))) return;
              try { await api.del(`/api/admin/comparative/jurisdictions/${j.id}`); toast(t("deleted"), "success"); draw(); }
              catch (e) { toast(e.message, "error"); }
            } }),
          ]),
          body(el("div", { class: "flex-col", style: "gap:6px" }, [
            el("span", { class: "badge-pill badge-navy", text: j.slug }),
          ])),
        ]))
      : emptyState(t("noData"), "globe"));
  }
  box.append(
    el("div", { class: "adm-toolbar" }, [
      el("span", { class: "spacer" }),
      el("button", { class: "btn btn-primary btn-sm", text: "+ " + t("comparativeAddJurisdiction"), onclick: () => jurisModal(null, draw) }),
    ]),
    node,
  );
  await draw();
  return box;
}

function jurisModal(j, onDone) {
  const nameI = input({ value: j?.name || "", placeholder: t("jurisdictionNamePh") });
  const slugI = input({ value: j?.slug || "", placeholder: t("jurisdictionCodePh") });
  openModal(el("div", {}, [
    el("h2", { text: j ? t("comparativeEditJurisdiction") : t("comparativeAddJurisdiction") }),
    el("div", { class: "adm-grid-2" }, [
      field(t("jurisdictionName") + " *", nameI),
      field(t("jurisdictionCode") + " (a-z)", slugI),
    ]),
    el("div", { class: "modal-actions" }, [
      el("button", { class: "btn btn-ghost", text: t("cancel"), onclick: closeModal }),
      el("button", { class: "btn btn-primary", text: t("save"), onclick: async () => {
        if (!nameI.value.trim() || !slugI.value.trim()) return toast(t("required"), "warn");
        const payload = { name: nameI.value.trim(), slug: slugI.value.trim().toLowerCase() };
        try {
          if (j) await api.put(`/api/admin/comparative/jurisdictions/${j.id}`, payload);
          else await api.post("/api/admin/comparative/jurisdictions", payload);
          closeModal(); toast(t("saved"), "success"); onDone && onDone();
        } catch (e) { toast(e.message, "error"); }
      } }),
    ]),
  ]));
}