// نبراس — المقالات (Blog) + البلاغات
import {
  el, api, t, head, panel, body, badge, statusBadge, tabs,
  toast, emptyState, skeleton, fmtDt, num, pagination,
  select, input, debounce, confirmDialog,
} from "../ui.js";
import { icon } from "../../icons.js";

export function blogView(initial = "articles") {
  let active = initial;
  const container = el("div", { class: "flex-col", style: "gap:16px" });
  const swap = (node) => container.replaceChildren(container.firstChild, node);
  function render() {
    container.replaceChildren(tabs([
      { key: "articles", label: t("articles") },
      { key: "reports", label: t("reports") },
    ], active, (k) => { active = k; render(); }));
    swap(skeleton(3, 90));
    const p = active === "articles" ? articlesPanel() : reportsPanel();
    p.then(swap).catch((e) => swap(el("div", { class: "adm-404", text: String(e?.message || e) })));
  }
  render();
  return container;
}

// =====================================================================
// المقالات
// =====================================================================
async function articlesPanel() {
  const PER = 10;
  let page = 1, status = "", q = "";
  const box = el("div", { class: "flex-col", style: "gap:16px" });
  const listBox = el("div");

  const statusSel = select({ class: "field", style: "width:170px" }, [
    el("option", { value: "", text: t("filterStatus") }),
    el("option", { value: "published", text: t("published") }),
    el("option", { value: "pending", text: t("pending") }),
    el("option", { value: "hidden", text: t("hidden") }),
  ]);
  statusSel.value = status;
  statusSel.onchange = () => { status = statusSel.value; page = 1; renderList(); };
  const searchIn = input({ class: "field", placeholder: t("search") + "…" });
  searchIn.oninput = debounce(() => { q = searchIn.value.trim(); page = 1; renderList(); }, 300);

  let articles = [];
  async function load() {
    const p = new URLSearchParams();
    if (status) p.set("status", status);
    if (q) p.set("q", q);
    p.set("limit", "200");
    const r = await api.get(`/api/admin/blog/articles?${p}`);
    articles = r.articles || [];
  }
  function renderList() {
    const total = articles.length;
    const pages = Math.max(1, Math.ceil(total / PER));
    if (page > pages) page = pages;
    const rows = articles.slice((page - 1) * PER, page * PER);
    if (!rows.length) {
      listBox.replaceChildren(emptyState(t("noData"), "pen"));
      return;
    }
    const trs = rows.map((a) => el("tr", {}, [
      el("td", {}, [el("strong", { text: a.title || "—" }), a.category_name ? el("div", { class: "sub", text: a.category_name }) : null]),
      el("td", { text: a.author?.full_name || "—" }),
      el("td", { class: "num", text: num(a.views) }),
      el("td", {}, [statusBadge(a.status)]),
      el("td", { text: fmtDt(a.updated_at || a.created_at) }),
      el("td", { class: "actions" }, [
        a.status !== "published"
          ? el("button", { class: "btn btn-ghost", text: t("publishArticle"), onclick: () => setStatus(a.id, "published") })
          : el("button", { class: "btn btn-ghost", text: t("hideArticle"), onclick: () => setStatus(a.id, "hidden") }),
      ]),
    ]));
    listBox.replaceChildren(el("div", { class: "adm-table", style: "overflow:auto" }, [
      el("table", { class: "adm-tbl" }, [
        el("thead", {}, el("tr", {}, [
          el("th", { text: t("title") }), el("th", { text: t("author") }),
          el("th", { text: t("views") }), el("th", { text: t("articleStatus") }),
          el("th", { text: t("updatedAt") }), el("th", {}),
        ])),
        el("tbody", {}, trs),
      ]),
      pagination(total, page, PER, (p) => { page = p; renderList(); }),
    ]));
  }
  async function setStatus(id, s) {
    if (!(await confirmDialog({ title: t("confirm"), text: t("confirmAction") }))) return;
    try {
      await api.put(`/api/admin/blog/articles/${id}/status`, { status: s });
      toast(t("done"), "success");
      await load(); renderList();
    } catch (e) { toast(e.message, "error"); }
  }

  box.append(
    panel([head(t("articles"), [el("div", { class: "adm-toolbar" }, [searchIn, statusSel])])]),
    listBox,
  );
  listBox.replaceChildren(skeleton(3, 90));
  try {
    await load(); renderList();
  } catch (e) {
    listBox.replaceChildren(el("div", { class: "adm-404", text: String(e?.message || e) }));
  }
  return box;
}

// =====================================================================
// البلاغات
// =====================================================================
async function reportsPanel() {
  const statusSel = select({ class: "field", style: "width:170px" }, [
    el("option", { value: "", text: t("filterStatus") }),
    el("option", { value: "open", text: t("open") }),
    el("option", { value: "actioned", text: t("actioned") }),
    el("option", { value: "dismissed", text: t("dismissed") }),
  ]);
  let status = "";
  const listBox = el("div");
  let reports = [];
  async function load() {
    const p = status ? `?status=${status}` : "";
    const r = await api.get(`/api/admin/blog/reports${p}`);
    reports = r.reports || [];
  }
  function renderList() {
    if (!reports.length) { listBox.replaceChildren(emptyState(t("noReports"), "shield")); return; }
    const trs = reports.map((r) => el("tr", {}, [
      el("td", {}, [el("strong", { text: r.article_title || "—" })]),
      el("td", { text: r.reason || "—" }),
      el("td", { text: r.reporter_name || "—" }),
      el("td", { text: fmtDt(r.created_at) }),
      el("td", {}, [statusBadge(r.status)]),
      el("td", { class: "actions" }, r.status === "open" ? [
        el("button", { class: "btn btn-danger", text: t("actioned"), onclick: () => act(r.id, "actioned") }),
        el("button", { class: "btn btn-ghost", text: t("dismissed"), onclick: () => act(r.id, "dismissed") }),
      ] : [badge(t("done"), "gray")]),
    ]));
    listBox.replaceChildren(el("div", { class: "adm-table", style: "overflow:auto" }, [
      el("table", { class: "adm-tbl" }, [
        el("thead", {}, el("tr", {}, [
          el("th", { text: t("title") }), el("th", { text: t("reportReason") }),
          el("th", { text: t("author") }), el("th", { text: t("createdAt") }),
          el("th", { text: t("articleStatus") }), el("th", {}),
        ])),
        el("tbody", {}, trs),
      ]),
    ]));
  }
  async function act(id, decision) {
    try {
      await api.post(`/api/admin/blog/reports/${id}/action`, { decision });
      toast(t("done"), "success");
      await load(); renderList();
    } catch (e) { toast(e.message, "error"); }
  }
  statusSel.onchange = async () => { status = statusSel.value; await load(); renderList(); };
  listBox.replaceChildren(skeleton(3, 90));
  try {
    await load(); renderList();
  } catch (e) {
    listBox.replaceChildren(el("div", { class: "adm-404", text: String(e?.message || e) }));
  }
  return el("div", { class: "flex-col", style: "gap:16px" }, [
    panel([head(t("reports"), [statusSel])]),
    listBox,
  ]);
}
