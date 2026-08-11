// نبراس — القوالب + الفئات + الإعلانات + المستأجرون
import {
  el, api, t, head, panel, body, badge, tabs, confirmDialog,
  openModal, closeModal, toast, emptyState, skeleton, pagination,
  fmtDt, input, select, field, money, num, downloadFile, kpiGrid,
} from "../ui.js";
import { icon } from "../../icons.js";

const paginate = (arr, page, per) => arr.slice((page - 1) * per, page * per);
const PER = 8;

export function commerceView(initial = "templates") {
  let active = initial;
  const container = el("div", { class: "flex-col", style: "gap:16px" });
  const swap = (node) => container.replaceChildren(container.firstChild, node);
  function render() {
    container.replaceChildren(tabs([
      { key: "templates", label: t("templatesTitle") },
      { key: "categories", label: t("categories") },
      { key: "ads", label: t("ads") },
      { key: "tenants", label: t("tenants") },
    ], active, (k) => { active = k; render(); }));
    swap(skeleton(3, 90));
    const p = active === "templates" ? templatesPanel()
      : active === "categories" ? categoriesPanel()
      : active === "ads" ? adsPanel() : tenantsPanel();
    p.then(swap).catch((e) => swap(el("div", { class: "adm-404", text: String(e?.message || e) })));
  }
  render();
  return container;
}

// =====================================================================
// القوالب
// =====================================================================
async function templatesPanel() {
  const [data, catsData] = await Promise.all([
    api.get("/api/admin/marketplace/templates"),
    api.get("/api/marketplace/categories").catch(() => []),
  ]);
  const rows = data.templates || data || [];
  const cats = Array.isArray(catsData) ? catsData : (catsData?.categories || []);
  const box = el("div", { class: "flex-col", style: "gap:14px" });
  let page = 1, q = "";
  const tbody = el("tbody");
  const searchI = el("input", { type: "search", placeholder: t("search"), oninput: (e) => { q = e.target.value.trim().toLowerCase(); page = 1; draw(); } });
  const pager = el("div", { class: "adm-pager" });
  function filtered() {
    return rows.filter((r) => !q || (r.title || "").toLowerCase().includes(q));
  }
  function draw() {
    const f = filtered();
    tbody.replaceChildren(f.length ? paginate(f, page, PER).map((r) =>
      el("tr", {}, [
        el("td", { class: "cell-main" }, [
          el("span", { class: "t", text: r.title }),
          el("span", { class: "s", text: r.description || "" }),
        ]),
        el("td", { text: r.category_name || "—" }),
        el("td", { class: "num", text: money(r.price_cents) }),
        el("td", { class: "num", text: String(r.download_count ?? 0) }),
        el("td", { class: "num" }, [icon("star", 14, { filled: true }), " " + (r.rating || 0)]),
        el("td", {}, r.has_file ? badge(t("hasFile"), "green") : badge("—", "gray")),
        el("td", {}, el("div", { class: "adm-actions" }, [
          r.has_file ? el("button", { class: "btn btn-ghost btn-sm", text: t("download"), onclick: () => downloadFile(`/api/admin/marketplace/templates/${r.id}/file`, `${r.title}.pdf`) }) : null,
          el("button", { class: "btn btn-ghost btn-sm", text: t("edit"), onclick: () => templateModal(r, cats, () => draw()) }),
          el("button", { class: "btn btn-danger btn-sm", text: t("delete"), onclick: async () => {
            if (!(await confirmDialog({ title: t("delete"), text: `${r.title}؟` }))) return;
            try { await api.del(`/api/admin/marketplace/templates/${r.id}`); rows.splice(rows.indexOf(r), 1); draw(); }
            catch (e) { toast(e.message, "error"); }
          } }),
        ])),
      ])) : el("tr", {}, el("td", { colspan: 7 }, emptyState(t("noTemplates"), "clipboard"))));
    pager.replaceChildren(
      el("span", { class: "meta", text: `${f.length} ${t("total")}` }),
      f.length > PER ? pagination(f.length, page, PER, (p) => { page = p; draw(); }) : null,
    );
  }
  draw();
  box.append(
    el("div", { class: "adm-toolbar" }, [
      searchI, el("span", { class: "spacer" }),
      el("button", { class: "btn btn-ghost btn-sm", text: "↻ " + t("refresh"), onclick: () => templatesPanel().then((n) => box.replaceWith(n)) }),
      el("button", { class: "btn btn-primary btn-sm", text: "+ " + t("newTemplate"), onclick: () => templateModal(null, cats, () => draw()) }),
    ]),
    panel([body(el("div", { class: "adm-tbl-wrap" }, [el("table", { class: "adm-tbl" }, [
      el("thead", {}, el("tr", {}, [
        el("th", { text: t("title") }), el("th", { text: t("category") }), el("th", { text: t("price") }),
        el("th", { text: t("downloads") }), el("th", { text: t("rating") }), el("th", { text: t("hasFile") }),
        el("th", { text: t("actions") }),
      ])),
      tbody,
    ])])), pager]),
  );
  return box;
}

function templateModal(r, cats, onDone) {
  const title = input({ value: r?.title || "", placeholder: t("title") });
  const description = el("textarea", { text: r?.description || "", placeholder: t("templateDesc") });
  const price = input({ type: "number", min: "0", step: "0.01", value: r ? (r.price_cents / 100) : "", placeholder: t("templatePrice") });
  const catS = select({}, [
    el("option", { value: "", text: t("category") + "..." }),
    ...(cats || []).map((c) => el("option", { value: String(c.id), text: c.name })),
  ]);
  if (r?.category_id) catS.value = String(r.category_id);
  const file = el("input", { type: "file", accept: ".pdf,application/pdf" });

  openModal(el("div", {}, [
    el("h2", { text: r ? t("editTemplate") : t("newTemplate") }),
    field(t("title") + " *", title),
    field(t("templateDesc"), description),
    el("div", { class: "adm-grid-2" }, [
      field(t("templatePrice") + " *", price),
      field(t("templateCategory") + " *", catS),
    ]),
    field(t("templateFile"), file, r ? t("replacePdf") : t("fileRequired")),
    el("div", { class: "modal-actions" }, [
      el("button", { class: "btn btn-ghost", text: t("cancel"), onclick: closeModal }),
      el("button", { class: "btn btn-primary", text: t("save"), onclick: async () => {
        if (!title.value.trim() || !catS.value) return toast(t("required"), "warn");
        const fd = new FormData();
        fd.append("title", title.value.trim());
        fd.append("description", description.value.trim());
        fd.append("price_cents", String(Math.round((Number(price.value) || 0) * 100)));
        fd.append("category_id", catS.value);
        try {
          if (r) {
            if (file.files[0]) fd.append("file", file.files[0]);
            await api.uploadFields(`/api/admin/marketplace/templates/${r.id}`, fd, "PUT");
          } else {
            if (!file.files[0]) return toast(t("fileRequired"), "warn");
            fd.append("file", file.files[0]);
            await api.uploadFields("/api/admin/marketplace/templates", fd);
          }
          closeModal(); toast(t("saved"), "success"); onDone && onDone();
        } catch (e) { toast(e.message, "error"); }
      } }),
    ]),
  ]));
}

// =====================================================================
// الفئات
// =====================================================================
async function categoriesPanel() {
  const cats = await api.get("/api/marketplace/categories").catch(() => []);
  const rows = Array.isArray(cats) ? cats : (cats?.categories || []);
  const box = el("div", { class: "flex-col", style: "gap:14px" });
  const tbody = el("tbody");
  function draw() {
    tbody.replaceChildren(rows.length ? rows.map((c) =>
      el("tr", {}, [
        el("td", { class: "cell-main" }, [
          el("span", { class: "t", text: c.name }),
          el("span", { class: "s", text: c.slug }),
        ]),
        el("td", { class: "num", text: String(c.template_count ?? 0) }),
        el("td", {}, el("div", { class: "adm-actions" }, [
          el("button", { class: "btn btn-ghost btn-sm", text: t("edit"), onclick: () => categoryModal(c, () => draw()) }),
          el("button", { class: "btn btn-danger btn-sm", text: t("delete"), onclick: async () => {
            if (!(await confirmDialog({ title: t("deleteCategory"), text: `${c.name}؟` }))) return;
            try { await api.del(`/api/admin/marketplace/categories/${c.id}`); rows.splice(rows.indexOf(c), 1); draw(); }
            catch (e) { toast(e.message, "error"); }
          } }),
        ])),
      ])) : el("tr", {}, el("td", { colspan: 3 }, emptyState(t("noCategories"), "folder"))));
  }
  draw();
  box.append(panel([head(t("categories"), [
    el("button", { class: "btn btn-ghost btn-sm", text: "↻ " + t("refresh"), onclick: () => categoriesPanel().then((n) => box.replaceWith(n)) }),
    el("button", { class: "btn btn-primary btn-sm", text: "+ " + t("newCategory"), onclick: () => categoryModal(null, () => draw()) }),
  ]), body(el("div", { class: "adm-tbl-wrap" }, [el("table", { class: "adm-tbl" }, [
    el("thead", {}, el("tr", {}, [
      el("th", { text: t("categoryName") }), el("th", { text: t("templatesCount") }), el("th", { text: t("actions") }),
    ])),
    tbody,
  ])]))]));
  return box;
}

function categoryModal(c, onDone) {
  const name = input({ value: c?.name || "", placeholder: t("categoryName") });
  const slug = input({ value: c?.slug || "", placeholder: t("categorySlug") });
  openModal(el("div", {}, [
    el("h2", { text: c ? t("editCategory") : t("newCategory") }),
    field(t("categoryName") + " *", name),
    field(t("categorySlug"), slug, "ex: contrats"),
    el("div", { class: "modal-actions" }, [
      el("button", { class: "btn btn-ghost", text: t("cancel"), onclick: closeModal }),
      el("button", { class: "btn btn-primary", text: t("save"), onclick: async () => {
        if (!name.value.trim()) return toast(t("required"), "warn");
        try {
          if (c) await api.put(`/api/admin/marketplace/categories/${c.id}`, { name: name.value.trim(), slug: slug.value.trim() || undefined });
          else await api.post("/api/admin/marketplace/categories", { name: name.value.trim(), slug: slug.value.trim() });
          closeModal(); toast(t("saved"), "success"); onDone && onDone();
        } catch (e) { toast(e.message, "error"); }
      } }),
    ]),
  ]));
}

// =====================================================================
// الإعلانات
// =====================================================================
async function adsPanel() {
  const [slotsData, campsData] = await Promise.all([
    api.get("/api/admin/ads/slots"),
    api.get("/api/admin/ads/campaigns"),
  ]);
  const slots = slotsData.slots || [];
  const camps = campsData.campaigns || campsData || [];
  const box = el("div", { class: "flex-col", style: "gap:16px" });
  let page = 1, q = "";
  const tbody = el("tbody");
  const searchI = el("input", { type: "search", placeholder: t("search"), oninput: (e) => { q = e.target.value.trim().toLowerCase(); page = 1; draw(); } });
  const pager = el("div", { class: "adm-pager" });

  async function setBulkStatus(status) {
    const ids = camps.map((c) => c.id);
    if (!ids.length) return;
    if (!(await confirmDialog({ title: status === "active" ? t("resume") : status === "paused" ? t("pause") : t("endCampaign"), text: `${ids.length}`, danger: false }))) return;
    try { await api.post("/api/admin/ads/campaigns/bulk-status", { ids, status }); toast(t("saved"), "success"); adsPanel().then((n) => box.replaceWith(n)); }
    catch (e) { toast(e.message, "error"); }
  }
  async function setStatus(c, status) {
    try { await api.put(`/api/admin/ads/campaigns/${c.id}`, { status }); toast(t("saved"), "success"); adsPanel().then((n) => box.replaceWith(n)); }
    catch (e) { toast(e.message, "error"); }
  }
  function ctrBadge(c) {
    const pct = ((c.ctr || 0) * 100).toFixed(2) + "%";
    return badge(pct, c.ctr > 0.03 ? "green" : c.ctr > 0.01 ? "gold" : "gray");
  }
  function draw() {
    const f = camps.filter((c) => !q || (c.advertiser_name || "").toLowerCase().includes(q) || (c.campaign_type || "").includes(q));
    tbody.replaceChildren(f.length ? paginate(f, page, PER).map((c) =>
      el("tr", {}, [
        el("td", { class: "cell-main" }, [
          el("span", { class: "t", text: c.advertiser_name || `#${c.id}` }),
          el("span", { class: "s", text: [c.campaign_type, c.slot_name].filter(Boolean).join(" · ") }),
        ]),
        el("td", {}, badge(c.status || "—", c.status === "active" ? "green" : c.status === "paused" ? "gold" : "red")),
        el("td", { class: "num", text: num(c.impressions) }),
        el("td", { class: "num", text: num(c.clicks) }),
        el("td", {}, ctrBadge(c)),
        el("td", { class: "sub", text: [c.starts_at, c.ends_at].filter(Boolean).join(" → ") }),
        el("td", {}, el("div", { class: "adm-actions" }, [
          c.status === "active"
            ? el("button", { class: "btn btn-ghost btn-sm", text: t("pause"), onclick: () => setStatus(c, "paused") })
            : el("button", { class: "btn btn-primary btn-sm", text: t("resume"), onclick: () => setStatus(c, "active") }),
          el("button", { class: "btn btn-ghost btn-sm", text: t("edit"), onclick: () => campaignModal(c, slots, () => draw()) }),
          el("button", { class: "btn btn-danger btn-sm", text: t("delete"), onclick: async () => {
            if (!(await confirmDialog({ title: t("deleteCampaign"), text: `${c.advertiser_name || c.id}؟` }))) return;
            try { await api.del(`/api/admin/ads/campaigns/${c.id}`); camps.splice(camps.indexOf(c), 1); draw(); }
            catch (e) { toast(e.message, "error"); }
          } }),
        ])),
      ])) : el("tr", {}, el("td", { colspan: 7 }, emptyState(t("noCampaigns"), "megaphone"))));
    pager.replaceChildren(
      el("span", { class: "meta", text: `${f.length} ${t("total")}` }),
      f.length > PER ? pagination(f.length, page, PER, (p) => { page = p; draw(); }) : null,
    );
  }
  draw();
  box.append(
    kpiGrid(slots.map((s) => ({ icon: "megaphone", label: s.name, value: num(s.active_campaigns), sub: t("activeCampaigns"), tone: "info" }))),
    el("div", { class: "adm-toolbar" }, [
      searchI, el("span", { class: "spacer" }),
      el("button", { class: "btn btn-ghost btn-sm", text: t("pause"), onclick: () => setBulkStatus("paused") }),
      el("button", { class: "btn btn-primary btn-sm", text: t("resume"), onclick: () => setBulkStatus("active") }),
      el("button", { class: "btn btn-primary btn-sm", text: "+ " + t("newCampaign"), onclick: () => campaignModal(null, slots, () => draw()) }),
    ]),
    panel([head(t("campaigns"), []), body(el("div", { class: "adm-tbl-wrap" }, [el("table", { class: "adm-tbl" }, [
      el("thead", {}, el("tr", {}, [
        el("th", { text: t("advertiserName") }), el("th", { text: t("status") }), el("th", { text: t("impressions") }),
        el("th", { text: t("clicks") }), el("th", { text: t("ctr") }), el("th", { text: t("date") }), el("th", { text: t("actions") }),
      ])),
      tbody,
    ])])), pager]),
  );
  return box;
}

function campaignModal(c, slots, onDone) {
  const slotS = select({}, (slots || []).map((s) => el("option", { value: String(s.id), text: s.name })));
  if (c?.slot_id) slotS.value = String(c.slot_id);
  const typeS = select({}, [
    el("option", { value: "general", text: t("general") }),
    el("option", { value: "sponsored", text: t("sponsored") }),
    el("option", { value: "professional_promotion", text: t("professionalPromotion") }),
  ]);
  if (c?.campaign_type) typeS.value = c.campaign_type;
  const advertiser = input({ value: c?.advertiser_name || "", placeholder: t("advertiserName") });
  const creative = input({ type: "url", value: c?.creative_url || "", placeholder: t("creativeUrl") });
  const target = input({ type: "url", value: c?.target_url || "", placeholder: t("targetUrl") });
  const starts = el("input", { type: "datetime-local", value: c?.starts_at ? String(c.starts_at).slice(0, 16) : "" });
  const ends = el("input", { type: "datetime-local", value: c?.ends_at ? String(c.ends_at).slice(0, 16) : "" });
  const statusS = select({}, [
    el("option", { value: "active", text: t("activeUsers") || "active" }),
    el("option", { value: "paused", text: t("pause") }),
    el("option", { value: "ended", text: t("endCampaign") }),
  ]);
  if (c?.status) statusS.value = c.status;

  openModal(el("div", {}, [
    el("h2", { text: c ? t("editCampaign") : t("newCampaign") }),
    field(t("advertiserName") + " *", advertiser),
    el("div", { class: "adm-grid-2" }, [
      field(t("campaignType"), typeS),
      field(t("slots") + " *", slotS),
    ]),
    field(t("creativeUrl"), creative),
    field(t("targetUrl"), target),
    el("div", { class: "adm-grid-2" }, [
      field(t("startsAt"), starts),
      field(t("endsAt"), ends),
    ]),
    field(t("status"), statusS),
    el("div", { class: "modal-actions" }, [
      el("button", { class: "btn btn-ghost", text: t("cancel"), onclick: closeModal }),
      el("button", { class: "btn btn-primary", text: t("save"), onclick: async () => {
        if (!advertiser.value.trim() || !slotS.value) return toast(t("required"), "warn");
        const payload = {
          advertiser_name: advertiser.value.trim(),
          campaign_type: typeS.value, slot_id: Number(slotS.value), status: statusS.value,
          creative_url: creative.value.trim() || undefined, target_url: target.value.trim() || undefined,
          starts_at: starts.value || undefined, ends_at: ends.value || undefined,
        };
        try {
          if (c) await api.put(`/api/admin/ads/campaigns/${c.id}`, payload);
          else await api.post("/api/admin/ads/campaigns", payload);
          closeModal(); toast(t("saved"), "success"); onDone && onDone();
        } catch (e) { toast(e.message, "error"); }
      } }),
    ]),
  ]));
}

// =====================================================================
// المستأجرون
// =====================================================================
async function tenantsPanel() {
  const data = await api.get("/api/admin/tenants");
  const rows = data.tenants || data || [];
  const box = el("div", { class: "flex-col", style: "gap:16px" });
  const tbody = el("tbody");
  const name = input({ placeholder: t("tenantName") });
  const slug = input({ placeholder: t("tenantSlug") });
  const createBtn = el("button", { class: "btn btn-primary btn-sm", text: t("newTenant"), type: "submit" });
  const form = el("form", { class: "adm-panel-body adm-toolbar" }, [name, slug, createBtn]);
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!name.value.trim() || !slug.value.trim()) return toast(t("required"), "warn");
    try { await api.post("/api/admin/tenants", { name: name.value.trim(), slug: slug.value.trim() }); toast(t("saved"), "success"); tenantsPanel().then((n) => box.replaceWith(n)); }
    catch (err) { toast(err.message, "error"); }
  });
  function draw() {
    tbody.replaceChildren(rows.length ? rows.map((ten) =>
      el("tr", {}, [
        el("td", { class: "cell-main" }, [
          el("span", { class: "t", text: ten.name }),
          el("span", { class: "s", text: ten.slug }),
        ]),
        el("td", {}, badge(ten.status || "—", ten.status === "active" ? "green" : "red")),
        el("td", { class: "num", text: String(ten.user_count ?? 0) }),
        el("td", { class: "sub", text: fmtDt(ten.created_at) }),
      ])) : el("tr", {}, el("td", { colspan: 4 }, emptyState(t("noTenants"), "building"))));
  }
  draw();
  box.append(
    panel([head(t("tenants"), [])]), form,
    panel([body(el("div", { class: "adm-tbl-wrap" }, [el("table", { class: "adm-tbl" }, [
      el("thead", {}, el("tr", {}, [
        el("th", { text: t("tenantName") }), el("th", { text: t("tenantStatus") }),
        el("th", { text: t("usersCount") }), el("th", { text: t("createdAt") }),
      ])),
      tbody,
    ])]))]),
    el("div", { class: "adm-notice info" }, [
      el("span", { class: "ic" }, [icon("info", 20)]),
      el("div", {}, [el("h4", { text: t("tenants") }), el("p", { text: t("multiTenantNote") })]),
    ]),
  );
  return box;
}
