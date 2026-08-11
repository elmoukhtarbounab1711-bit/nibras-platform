// نبراس — الفوترة (لوحة الإدارة): الطلبات + الباقات + الجرد المالي
import {
  el, api, t, head, panel, body, badge, tabs, confirmDialog,
  openModal, closeModal, toast, emptyState, skeleton, pagination,
  fmtDt, input, select, field, num, kpiGrid, statusBadge,
} from "../ui.js";

const paginate = (arr, page, per) => arr.slice((page - 1) * per, page * per);
const PER = 10;

export function billingView() {
  let active = "orders";
  const container = el("div", { class: "flex-col", style: "gap:16px" });
  const swap = (node) => container.replaceChildren(node);
  function render() {
    container.replaceChildren(tabs([
      { key: "orders", label: t("orders") },
      { key: "plans", label: t("plans") },
    ], active, (k) => { active = k; render(); }));
    swap(skeleton(3, 90));
    const p = active === "orders" ? ordersPanel() : plansPanel();
    p.then(swap).catch((e) => swap(el("div", { class: "adm-404", text: String(e?.message || e) })));
  }
  render();
  return container;
}

async function ordersPanel() {
  const box = el("div", { class: "flex-col", style: "gap:16px" });
  const statusS = select({}, [
    el("option", { value: "", text: `-- ${t("all")} --` }),
    el("option", { value: "pending", text: t("orderStatusPending") }),
    el("option", { value: "paid", text: t("orderStatusPaid") }),
    el("option", { value: "cancelled", text: t("orderStatusCancelled") }),
  ]);
  let summary = null;
  try { summary = await api.get("/api/admin/billing/summary"); } catch { summary = null; }
  const tbody = el("tbody", {});

  async function draw() {
    const params = new URLSearchParams();
    if (statusS.value) params.set("status", statusS.value);
    params.set("limit", "200");
    let list = [];
    try { list = (await api.get(`/api/admin/orders?${params.toString()}`)).orders || []; }
    catch (e) { list = []; }
    tbody.replaceChildren(list.length
      ? list.map((o) => el("tr", {}, [
          el("td", { text: `#${o.id}` }),
          el("td", { text: o.user_name || o.user_email || "—" }),
          el("td", { text: o.plan_name || "—" }),
          el("td", { text: `${(o.amount ?? 0)} ${t("currency")}` }),
          el("td", { text: fmtDt(o.created_at) }),
          el("td", {}, [statusBadge(o.status)]),
          el("td", {}, [
            o.status === "pending"
              ? el("div", { class: "flex", style: "gap:6px" }, [
                  el("button", { class: "btn btn-primary btn-sm", text: t("confirm"), onclick: async () => {
                    try {
                      await api.post(`/api/admin/orders/${o.id}/confirm`);
                      toast(t("orderStatusPaid"), "success"); draw();
                    } catch (e) { toast(e.message, "error"); }
                  } }),
                  el("button", { class: "btn btn-danger btn-sm", text: t("reject"), onclick: async () => {
                    if (!(await confirmDialog({ title: t("confirmAction"), text: `#${o.id}?` }))) return;
                    try {
                      await api.post(`/api/admin/orders/${o.id}/cancel`);
                      toast(t("orderStatusCancelled"), "success"); draw();
                    } catch (e) { toast(e.message, "error"); }
                  } }),
                ])
              : el("span", { class: "small muted", text: o.processed_by ? `#${o.processed_by}` : "—" }),
          ]),
        ]))
      : el("tr", {}, el("td", { colspan: 7 }, emptyState(t("noOrders"), "receipt"))));
  }
  statusS.addEventListener("change", draw);

  const kpis = kpiGrid([
    { icon: "wallet", label: t("kpiRevenue"), value: `${(summary?.revenue || 0)}`, sub: t("orderStatusPaid"), tone: "green" },
    { icon: "clock", label: t("pending"), value: `${(summary?.pending || 0)}`, sub: t("orderStatusPending"), tone: "gold" },
    { icon: "creditCard", label: t("plans"), value: String(summary?.paid_orders || 0), sub: t("orders"), tone: "info" },
  ]);

await draw();
  box.append(
    kpis,
    el("div", { class: "adm-toolbar" }, [statusS, el("span", { class: "spacer" })]),
    panel([
      head(t("orders"), []),
      body(el("div", { class: "adm-tbl-wrap" }, [
        el("table", { class: "adm-tbl" }, [
          el("thead", {}, el("tr", {}, [
            el("th", { text: t("orderIdLabel") }), el("th", { text: t("user") }),
            el("th", { text: t("plan") }), el("th", { text: t("amount") }),
            el("th", { text: t("date") }), el("th", { text: t("status") }), el("th", { text: t("actions") }),
          ])),
          tbody,
        ]),
      ])),
    ]),
  );
  return box;
}

async function plansPanel() {
  const box = el("div", { class: "flex-col", style: "gap:16px" });
  const tbody = el("tbody", {});
  async function draw() {
    let list;
    try { list = (await api.get("/api/admin/plans")).plans || []; }
    catch (e) { list = []; }
    tbody.replaceChildren(list.length
      ? list.map((p) => el("tr", {}, [
          el("td", { text: p.slug }),
          el("td", { text: p.name }),
          el("td", {}, [el("span", { class: `badge-pill ${p.kind === "premium_listing" ? "badge-gold" : "badge-green"}`, text: p.kind === "premium_listing" ? t("planKindPremium") : t("planKindCredits") })]),
          el("td", { text: `${(p.price_cents / 100).toFixed(2)} ${t("currency")}` }),
          el("td", { text: p.credits ? `${p.credits} ${t("includesCredits")}` : p.duration_days ? `${p.duration_days} ${t("includesDays")}` : "—" }),
          el("td", {}, [statusBadge(p.enabled ? "active" : "paused")]),
          el("td", {}, [
            el("div", { class: "flex", style: "gap:6px" }, [
              el("button", { class: "btn btn-ghost btn-sm", text: t("edit"), onclick: () => planModal(p, draw) }),
              el("button", { class: "btn btn-ghost btn-sm", text: p.enabled ? t("pause") : t("resume"), onclick: async () => {
                try { await api.put(`/api/admin/plans/${p.id}`, { enabled: !p.enabled }); draw(); }
                catch (e) { toast(e.message, "error"); }
              } }),
              el("button", { class: "btn btn-danger btn-sm", text: t("delete"), onclick: async () => {
                if (!(await confirmDialog({ title: t("deletePlan"), text: p.slug }))) return;
                try { await api.del(`/api/admin/plans/${p.id}`); draw(); }
                catch (e) { toast(e.message, "error"); }
              } }),
            ]),
          ]),
        ]))
      : el("tr", {}, el("td", { colspan: 7 }, emptyState(t("noPlans"), "creditCard"))));
  }

  box.append(
    el("div", { class: "adm-toolbar" }, [
      el("span", { class: "spacer" }),
      el("button", { class: "btn btn-primary btn-sm", text: "+ " + t("newPlan"), onclick: () => planModal(null, draw) }),
    ]),
    panel([head(t("plans"), []), body(el("div", { class: "adm-tbl-wrap" }, [el("table", { class: "adm-tbl" }, [
      el("thead", {}, el("tr", {}, [
        el("th", { text: t("slug") }), el("th", { text: t("name") }), el("th", { text: t("type") }),
        el("th", { text: t("price") }), el("th", { text: t("benefit") }), el("th", { text: t("status") }),
        el("th", { text: t("actions") }),
      ])),
      tbody,
    ])]))]),
  );
  return box;
}

function planModal(p, onDone) {
  const name = input({ value: p?.name || "" });
  const slug = input({ value: p?.slug || "" });
  const typeS = select({}, [
    el("option", { value: "credits", text: t("planKindCredits") }),
    el("option", { value: "premium_listing", text: t("planKindPremium") }),
  ]);
  if (p?.kind) typeS.value = p.kind;
  const price = input({ type: "number", value: p ? p.price_cents : "", placeholder: "سنتيم" });
  const credits = input({ type: "number", value: p?.credits ?? "", placeholder: "0" });
  const days = input({ type: "number", value: p?.duration_days ?? "", placeholder: "0" });
  const desc = input({ value: p?.description || "", placeholder: t("description") });

  const toggleType = () => {
    credits.disabled = typeS.value !== "credits";
    days.disabled = typeS.value !== "premium_listing";
  };
  typeS.addEventListener("change", toggleType);
  toggleType();

  openModal(el("div", {}, [
    el("h2", { text: p ? t("editPlan") : t("newPlan") }),
    field(t("name") + " *", name),
    field(t("slug") + " *", slug),
    el("div", { class: "adm-grid-2" }, [
      field(t("type"), typeS),
      field(t("price") + " (centimes)", price),
    ]),
    el("div", { class: "adm-grid-2" }, [
      field(t("includesCredits"), credits),
      field(t("includesDays"), days),
    ]),
    field(t("description"), desc),
    el("div", { class: "modal-actions" }, [
      el("button", { class: "btn btn-ghost", text: t("cancel"), onclick: closeModal }),
      el("button", { class: "btn btn-primary", text: t("save"), onclick: async () => {
        if (!name.value.trim() || !slug.value.trim()) return toast(t("required"), "warn");
        const payload = {
          name: name.value.trim(),
          slug: slug.value.trim(),
          kind: typeS.value,
          price_cents: Number(price.value) || 0,
          credits: Number(credits.value) || 0,
          duration_days: typeS.value === "premium_listing" ? (Number(days.value) || 0) : undefined,
          description: desc.value.trim() || "",
        };
        try {
          if (p) await api.put(`/api/admin/plans/${p.id}`, payload);
          else await api.post("/api/admin/plans", payload);
          closeModal(); toast(t("saved"), "success"); onDone && onDone();
        } catch (e) { toast(e.message, "error"); }
      } }),
    ]),
  ]));
}