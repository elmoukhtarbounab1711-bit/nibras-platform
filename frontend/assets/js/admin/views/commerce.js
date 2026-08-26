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
  const box = el("div", { class: "flex-col", style: "gap:16px" });
  let subTab = "campaigns";

  function render() {
    const subTabs = el("div", { class: "adm-tabs", role: "tablist" }, [
      el("button", {
        class: "adm-tab" + (subTab === "campaigns" ? " active" : ""),
        type: "button", text: t("campaigns"), role: "tab",
        onclick: () => { subTab = "campaigns"; render(); },
      }),
      el("button", {
        class: "adm-tab" + (subTab === "providers" ? " active" : ""),
        type: "button", text: t("adProviders") || "المزوّدون الإعلانيون", role: "tab",
        onclick: () => { subTab = "providers"; render(); },
      }),
      el("button", {
        class: "adm-tab" + (subTab === "settings" ? " active" : ""),
        type: "button", text: t("adSettings") || "إعدادات الإعلانات", role: "tab",
        onclick: () => { subTab = "settings"; render(); },
      }),
    ]);

    box.replaceChildren(subTabs, skeleton(3, 90));
    const p = subTab === "campaigns" ? campaignsSubPanel()
      : subTab === "providers" ? providersSubPanel()
      : settingsSubPanel();
    p.then((n) => { box.replaceChildren(subTabs, n); }).catch((e) => {
      box.replaceChildren(subTabs, el("div", { class: "adm-404", text: String(e?.message || e) }));
    });
  }
  render();
  return box;
}

// =====================================================================
// حملات الإعلانات (ال㞖 فرعي)
// =====================================================================
async function campaignsSubPanel() {
  const [slotsData, campsData] = await Promise.all([
    api.get("/api/admin/ads/slots"),
    api.get("/api/admin/ads/campaigns"),
  ]);
  const slots = slotsData.slots || [];
  const camps = campsData.campaigns || campsData || [];
  const box = el("div", { class: "flex-col", style: "gap:14px" });
  let page = 1, q = "";
  const tbody = el("tbody");
  const searchI = el("input", { type: "search", placeholder: t("search"), oninput: (e) => { q = e.target.value.trim().toLowerCase(); page = 1; draw(); } });
  const pager = el("div", { class: "adm-pager" });

  const catNames = {};
  (async () => {
    const sources = { library: "/api/categories", marketplace: "/api/marketplace/categories", jurisprudence: "/api/admin/jurisprudence/categories" };
    for (const [dtype, url] of Object.entries(sources)) {
      try { const data = await api.get(url); for (const c of (data.categories || data || [])) catNames[`${dtype}:${c.id}`] = c.name; } catch {}
    }
    draw();
  })();

  const catLabel = (c) => c.target_category_type
    ? `${t("targetCategory")}: ${catNames[`${c.target_category_type}:${c.target_category_id}`] || c.target_category_type} (#${c.target_category_id})`
    : t("targetCategoryNone");

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
          c.target_category_type ? el("span", { class: "s", text: catLabel(c) }) : null,
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

// =====================================================================
// المزوّدون الإعلانيون (Security §7)
// =====================================================================
async function providersSubPanel() {
  const data = await api.get("/api/admin/ads/providers");
  const providers = data.providers || data || [];
  const box = el("div", { class: "flex-col", style: "gap:14px" });
  const tbody = el("tbody");

  function draw() {
    tbody.replaceChildren(providers.length ? providers.map((p) =>
      el("tr", {}, [
        el("td", { class: "cell-main" }, [
          el("span", { class: "t", text: p.name }),
          el("span", { class: "s", text: p.slug }),
        ]),
        el("td", { text: p.provider_type || "—" }),
        el("td", {}, badge(p.is_enabled ? (t("activeUsers") || "مفعّل") : (t("hidden") || "معطّل"), p.is_enabled ? "green" : "red")),
        el("td", { class: "num", text: String(p.slot_count ?? 0) }),
        el("td", {}, el("div", { class: "adm-actions" }, [
          el("button", { class: "btn btn-ghost btn-sm", text: t("edit"), onclick: () => providerModal(p, () => draw()) }),
          el("button", {
            class: "btn btn-ghost btn-sm",
            text: p.is_enabled ? (t("hidden") || "تعطيل") : (t("activeUsers") || "تفعيل"),
            onclick: async () => {
              try { await api.post("/api/admin/ads/providers/bulk-status", { ids: [p.id], enabled: !p.is_enabled }); toast(t("saved"), "success"); p.is_enabled = !p.is_enabled; draw(); }
              catch (e) { toast(e.message, "error"); }
            },
          }),
          el("button", { class: "btn btn-danger btn-sm", text: t("delete"), onclick: async () => {
            if (!(await confirmDialog({ title: t("delete"), text: `${p.name}؟` }))) return;
            try { await api.del(`/api/admin/ads/providers/${p.id}`); providers.splice(providers.indexOf(p), 1); draw(); }
            catch (e) { toast(e.message, "error"); }
          } }),
        ])),
      ])) : el("tr", {}, el("td", { colspan: 5 }, emptyState(t("noProviders") || "لا يوجد مزوّدون", "users"))));
  }
  draw();
  box.append(
    el("div", { class: "adm-toolbar" }, [
      el("button", { class: "btn btn-ghost btn-sm", text: "↻ " + t("refresh"), onclick: () => providersSubPanel().then((n) => box.replaceWith(n)) }),
      el("button", { class: "btn btn-primary btn-sm", text: "+ " + (t("newProvider") || "مزوّد جديد"), onclick: () => providerModal(null, () => draw()) }),
    ]),
    panel([head(t("adProviders") || "المزوّدون الإعلانيون", []), body(el("div", { class: "adm-tbl-wrap" }, [el("table", { class: "adm-tbl" }, [
      el("thead", {}, el("tr", {}, [
        el("th", { text: t("name") || "الاسم" }), el("th", { text: t("type") || "النوع" }),
        el("th", { text: t("status") }), el("th", { text: t("slots") || "الفتحات" }), el("th", { text: t("actions") }),
      ])),
      tbody,
    ])]))]),
  );
  return box;
}

function providerModal(p, onDone) {
  const nameI = input({ value: p?.name || "", placeholder: t("name") || "اسم المزوّد" });
  const slugI = input({ value: p?.slug || "", placeholder: t("slug") || "الرمز" });
  const typeS = select({}, [
    el("option", { value: "adsense", text: "Google AdSense" }),
    el("option", { value: "adsterra", text: "Adsterra" }),
    el("option", { value: "propellerads", text: "PropellerAds" }),
    el("option", { value: "monetag", text: "Monetag" }),
    el("option", { value: "media_net", text: "Media.net" }),
    el("option", { value: "custom", text: t("custom") || "مخصّص" }),
  ]);
  if (p?.provider_type) typeS.value = p.provider_type;
  const apiKey = input({ value: p?.api_key || "", placeholder: t("apiKey") || "مفتاح API (اختياري)" });
  const scriptHtml = el("textarea", {
    text: p?.script_html || "",
    placeholder: t("scriptHtml") || "كود السكريبت الإعلاني HTML...",
    rows: "6",
    style: "font-family:monospace;font-size:12px;min-height:120px",
  });

  openModal(el("div", {}, [
    el("h2", { text: p ? (t("editProvider") || "تعديل المزوّد") : (t("newProvider") || "مزوّد جديد") }),
    field(t("name") || "الاسم" + " *", nameI),
    el("div", { class: "adm-grid-2" }, [
      field(t("slug") || "الرمز", slugI),
      field(t("type") || "النوع", typeS),
    ]),
    field(t("apiKey") || "مفتاح API", apiKey),
    field(t("scriptHtml") || "كود السكريبت", scriptHtml, t("scriptHint") || "HTML — يُحقّق تلقائيًا من النطاقات المعتمدة"),
    el("div", { class: "modal-actions" }, [
      el("button", { class: "btn btn-ghost", text: t("cancel"), onclick: closeModal }),
      el("button", { class: "btn btn-primary", text: t("save"), onclick: async () => {
        if (!nameI.value.trim()) return toast(t("required"), "warn");
        const payload = {
          name: nameI.value.trim(),
          slug: slugI.value.trim() || nameI.value.trim().toLowerCase().replace(/\s+/g, "-"),
          provider_type: typeS.value,
          api_key: apiKey.value.trim() || undefined,
          script_html: scriptHtml.value.trim() || undefined,
        };
        try {
          if (p) await api.put(`/api/admin/ads/providers/${p.id}`, payload);
          else await api.post("/api/admin/ads/providers", payload);
          closeModal(); toast(t("saved"), "success"); onDone && onDone();
        } catch (e) { toast(e.message, "error"); }
      } }),
    ]),
  ]));
}

// =====================================================================
// إعدادات الإعلانات العامة
// =====================================================================
async function settingsSubPanel() {
  const data = await api.get("/api/admin/ads/settings");
  const settings = data.settings || data || {};
  const box = el("div", { class: "flex-col", style: "gap:16px" });

  const enabledCheck = el("input", { type: "checkbox", checked: settings.ads_enabled === "true" ? "" : undefined });
  enabledCheck.checked = settings.ads_enabled === "true";
  const noPremiumCheck = el("input", { type: "checkbox", checked: settings.ads_no_premium === "true" ? "" : undefined });
  noPremiumCheck.checked = settings.ads_no_premium === "true";
  const lazyCheck = el("input", { type: "checkbox", checked: settings.ads_lazy_load !== "false" ? "" : undefined });
  lazyCheck.checked = settings.ads_lazy_load !== "false";
  const allowlistI = el("textarea", {
    text: (settings.ads_domain_allowlist || "").replace(/,/g, "\n"),
    rows: "5",
    placeholder: t("domainAllowlist") || "قائمة النطاقات (كل نطاق في سطر)",
    style: "font-family:monospace;font-size:12px",
  });

  async function saveSetting(key, value) {
    try { await api.put("/api/admin/ads/settings", { key, value }); }
    catch (e) { toast(e.message, "error"); }
  }

  box.append(
    panel([
      head(t("adSettings") || "إعدادات الإعلانات العامة", []),
      body(el("div", { class: "flex-col", style: "gap:14px" }, [
        el("label", { class: "adm-checkbox-row" }, [
          enabledCheck,
          el("span", { text: t("adsEnabled") || "تفعيل الإعلانات على المنصة" }),
        ]),
        el("label", { class: "adm-checkbox-row" }, [
          noPremiumCheck,
          el("span", { text: t("adsNoPremium") || "إخفاء الإعلانات عن المشتركين المدفوعين" }),
        ]),
        el("label", { class: "adm-checkbox-row" }, [
          lazyCheck,
          el("span", { text: t("adsLazyLoad") || "التحميل الكسول (IntersectionObserver)" }),
        ]),
        field(t("domainAllowlist") || "قائمة النطاقات المعتمدة", allowlistI, t("allowlistHint") || "كل نطاق في سطر منفصل"),
        el("div", { class: "modal-actions" }, [
          el("button", { class: "btn btn-primary", text: t("save"), onclick: async () => {
            await saveSetting("ads_enabled", String(enabledCheck.checked));
            await saveSetting("ads_no_premium", String(noPremiumCheck.checked));
            await saveSetting("ads_lazy_load", String(lazyCheck.checked));
            const domains = allowlistI.value.split("\n").map((l) => l.trim()).filter(Boolean).join(",");
            await saveSetting("ads_domain_allowlist", domains);
            toast(t("saved"), "success");
          } }),
        ]),
      ])),
    ]),
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

  // ---- الاستهداف الفئوي (المرحلة 19 — D-037) ----
  const CAT_SOURCES = {
    library: "/api/categories",
    marketplace: "/api/marketplace/categories",
    jurisprudence: "/api/admin/jurisprudence/categories",
  };
  const targetTypeS = select({}, [
    el("option", { value: "", text: t("targetCategoryNone") }),
    el("option", { value: "library", text: t("library") }),
    el("option", { value: "marketplace", text: t("templatesTitle") }),
    el("option", { value: "jurisprudence", text: t("jurisprudence") }),
  ]);
  const targetCatS = select({ disabled: true }, [el("option", { value: "", text: "--" })]);
  if (c?.target_category_type) targetTypeS.value = c.target_category_type;

  async function loadTargetCategories(dtype) {
    targetCatS.replaceChildren(el("option", { value: "", text: "--" }));
    targetCatS.disabled = true;
    if (!dtype) return;
    try {
      const data = await api.get(CAT_SOURCES[dtype]);
      const cats = data.categories || data || [];
      targetCatS.replaceChildren(
        el("option", { value: "", text: "--" }),
        ...cats.map((x) => el("option", { value: String(x.id), text: x.name })),
      );
      targetCatS.disabled = false;
      if (c?.target_category_type === dtype && c?.target_category_id != null) {
        targetCatS.value = String(c.target_category_id);
      }
    } catch (e) {
      toast(e.message, "error");
    }
  }
  loadTargetCategories(targetTypeS.value);
  targetTypeS.addEventListener("change", () => loadTargetCategories(targetTypeS.value));
  const targetWrap = el("div", { class: "adm-grid-2" }, [
    field(t("targetCategoryType"), targetTypeS),
    field(t("targetCategoryId"), targetCatS),
  ]);
  const targetHint = el("div", { class: "small muted", style: "margin-top:-6px", text: t("targetHint") });

  openModal(el("div", {}, [
    el("h2", { text: c ? t("editCampaign") : t("newCampaign") }),
    field(t("advertiserName") + " *", advertiser),
    el("div", { class: "adm-grid-2" }, [
      field(t("campaignType"), typeS),
      field(t("slots") + " *", slotS),
    ]),
    field(t("creativeUrl"), creative),
    field(t("targetUrl"), target),
    targetWrap,
    targetHint,
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
        if (targetTypeS.value) {
          payload.target_category_type = targetTypeS.value;
          payload.target_category_id = Number(targetCatS.value);
          if (!targetCatS.value) return toast(t("required"), "warn");
        } else {
          payload.target_category_type = "";
          payload.target_category_id = undefined;
        }
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
