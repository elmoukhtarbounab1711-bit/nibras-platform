// نبراس — المهنيون: تحقق + قوائم + إشراف + مستخدمون + تدقيق
import {
  el, api, t, head, panel, body, badge, tabs, kpi, kpiGrid,
  confirmDialog, openModal, closeModal, toast, emptyState,
  skeleton, pagination, fmtDt, field, downloadFile, num,
} from "../ui.js";
import { icon } from "../../icons.js";

const paginate = (arr, page, per) => arr.slice((page - 1) * per, page * per);
const PER = 8;

export function peopleView(initial = "verification") {
  let active = initial;
  const container = el("div", { class: "flex-col", style: "gap:16px" });
  const swap = (node) => container.replaceChildren(container.firstChild, node);
  function render() {
    container.replaceChildren(tabs([
      { key: "verification", label: t("verificationQueue") },
      { key: "verified", label: t("verifiedList") },
      { key: "moderation", label: t("moderation") },
      { key: "users", label: t("users") },
      { key: "audit", label: t("audit") },
    ], active, (k) => { active = k; render(); }));
    swap(skeleton(3, 90));
    const p = active === "verification" ? verificationPanel()
      : active === "verified" ? verifiedPanel()
      : active === "moderation" ? moderationPanel()
      : active === "users" ? usersPanel() : auditPanel();
    p.then(swap).catch((e) => swap(el("div", { class: "adm-404", text: String(e?.message || e) })));
  }
  render();
  return container;
}

// =====================================================================
// طابور التحقق
// =====================================================================
async function verificationPanel() {
  const data = await api.get("/api/admin/verification-queue");
  const reqs = data.requests || [];
  const box = el("div", { class: "flex-col", style: "gap:14px" });
  const selected = new Set();

  const approveBtn = el("button", { class: "btn btn-primary btn-sm", disabled: true, text: t("approveSelected") });
  const rejectBtn = el("button", { class: "btn btn-danger btn-sm", disabled: true, text: t("rejectSelected") });
  approveBtn.onclick = async () => {
    if (!(await confirmDialog({ title: t("approveSelected"), text: `${selected.size}`, danger: false }))) return;
    try { await api.post("/api/admin/verification/bulk", { action: "approve", user_ids: [...selected] }); toast(t("saved"), "success"); box.parentNode && renderAll(); }
    catch (e) { toast(e.message, "error"); }
  };
  rejectBtn.onclick = async () => {
    rejectModal(async (reason) => {
      try { await api.post("/api/admin/verification/bulk", { action: "reject", user_ids: [...selected], reason }); toast(t("saved"), "success"); renderAll(); }
      catch (e) { toast(e.message, "error"); }
    });
  };
  function renderAll() { return verificationPanel().then((n) => box.replaceWith(n)); }
  function sync() {
    approveBtn.disabled = rejectBtn.disabled = selected.size === 0;
    approveBtn.textContent = `${t("approveSelected")} (${selected.size})`;
    rejectBtn.textContent = `${t("rejectSelected")} (${selected.size})`;
  }
  const tbody = el("tbody");
  const checkAll = el("input", { type: "checkbox", class: "adm-check", onchange: (e) => {
    tbody.querySelectorAll("input.adm-check[data-id]").forEach((c) => { c.checked = e.target.checked; });
    selected.clear();
    tbody.querySelectorAll("input.adm-check[data-id]:checked").forEach((c) => selected.add(c.dataset.id));
    sync();
  } });
  tbody.replaceChildren(reqs.length ? reqs.map((r) => {
    const cb = el("input", { type: "checkbox", class: "adm-check", "data-id": String(r.user_id), onchange: (e) => {
      e.target.checked ? selected.add(String(r.user_id)) : selected.delete(String(r.user_id));
      sync();
    } });
    return el("tr", {}, [
      el("td", {}, cb),
      el("td", { class: "cell-main" }, [
        el("span", { class: "t", text: r.full_name }),
        el("span", { class: "s", text: r.email }),
      ]),
      el("td", {}, badge(t("professionType") + ": " + (r.role_name || r.role_code || ""), "blue")),
      el("td", {}, r.has_profile ? badge(t("hasProfile"), "green") : badge("—", "gray")),
      el("td", {}, r.has_document ? badge(t("hasDocument"), "green") : badge("—", "gray")),
      el("td", { class: "sub", text: fmtDt(r.requested_at) }),
      el("td", {}, el("div", { class: "adm-actions" }, [
        r.has_document ? el("button", { class: "btn btn-ghost btn-sm", text: t("document"), onclick: () => downloadFile(`/api/admin/verification/${r.user_id}/document`, r.document_name || `document-${r.user_id}`) }) : null,
        el("button", { class: "btn btn-primary btn-sm", text: t("approve"), onclick: async () => {
          try { await api.post(`/api/admin/verification/${r.user_id}/approve`); toast(t("saved"), "success"); renderAll(); }
          catch (e) { toast(e.message, "error"); }
        } }),
        el("button", { class: "btn btn-danger btn-sm", text: t("reject"), onclick: () => rejectModal(async (reason) => {
          try { await api.post(`/api/admin/verification/${r.user_id}/reject`, { reason }); toast(t("saved"), "success"); renderAll(); }
          catch (e) { toast(e.message, "error"); }
        }) }),
      ])),
    ]);
  }) : []);

  box.append(
    el("div", { class: "adm-toolbar" }, [
      approveBtn, rejectBtn,
      el("span", { class: "spacer" }),
      el("span", { class: "meta", style: "font-size:12.5px;color:var(--ink-3)", text: `${reqs.length} ${t("pendingVerification")}` }),
    ]),
    panel([body(reqs.length ? el("div", { class: "adm-tbl-wrap" }, [el("table", { class: "adm-tbl" }, [
      el("thead", {}, el("tr", {}, [
        el("th", {}, checkAll), el("th", { text: t("name") }), el("th", { text: t("role") }),
        el("th", { text: t("hasProfile") }), el("th", { text: t("hasDocument") }),
        el("th", { text: t("requestedAt") }), el("th", { text: t("actions") }),
      ])),
      tbody,
    ])]) : emptyState(t("noQueue"), "check"))]),
  );
  return box;
}

function rejectModal(onSubmit) {
  const reason = el("textarea", { placeholder: t("rejectReason") + " *" });
  openModal(el("div", {}, [
    el("h2", { text: t("reject") }),
    field(t("rejectReason") + " *", reason),
    el("div", { class: "modal-actions" }, [
      el("button", { class: "btn btn-ghost", text: t("cancel"), onclick: closeModal }),
      el("button", { class: "btn btn-danger", text: t("confirm"), onclick: async () => {
        if (!reason.value.trim()) return toast(t("required"), "warn");
        closeModal(); await onSubmit(reason.value.trim());
      } }),
    ]),
  ]));
}

// =====================================================================
// المهنيون الموثقون (قراءة)
// =====================================================================
async function verifiedPanel() {
  const data = await api.get("/api/professionals?limit=200");
  const rows = data.professionals || data || [];
  const box = el("div", { class: "flex-col", style: "gap:14px" });
  let page = 1;
  let q = "";
  const tbody = el("tbody");
  const searchI = el("input", { type: "search", placeholder: t("search"), oninput: (e) => { q = e.target.value.trim().toLowerCase(); page = 1; draw(); } });
  const pager = el("div", { class: "adm-pager" });
  function filtered() {
    return rows.filter((r) => !q || (r.full_name || "").toLowerCase().includes(q) || (r.city || "").toLowerCase().includes(q));
  }
  function draw() {
    const f = filtered();
    tbody.replaceChildren(f.length ? paginate(f, page, PER).map((r) =>
      el("tr", {}, [
        el("td", { class: "cell-main" }, [
          el("span", { class: "t", text: r.full_name }),
          el("span", { class: "s", text: [r.registration_number, r.city].filter(Boolean).join(" · ") }),
        ]),
        el("td", {}, badge(r.profession_type || "—", "blue")),
        el("td", { class: "sub", text: r.city || "—" }),
        el("td", {}, el("span", {}, [icon("star", 14, { filled: true }), " " + (r.rating || 0)])),
        el("td", { class: "num", text: String(r.review_count ?? 0) }),
        el("td", {}, badge(t("verifiedList"), "green")),
      ])) : el("tr", {}, el("td", { colspan: 6 }, emptyState(t("noProfessionals"), "scale"))));
    pager.replaceChildren(
      el("span", { class: "meta", text: `${f.length} ${t("total")}` }),
      f.length > PER ? pagination(f.length, page, PER, (p) => { page = p; draw(); }) : null,
    );
  }
  draw();
  box.append(
    el("div", { class: "adm-toolbar" }, [searchI, el("span", { class: "spacer" }), el("button", { class: "btn btn-ghost btn-sm", text: "↻ " + t("refresh"), onclick: () => verifiedPanel().then((n) => box.replaceWith(n)) })]),
    panel([head(t("verifiedList"), []), body(el("div", { class: "adm-tbl-wrap" }, [el("table", { class: "adm-tbl" }, [
      el("thead", {}, el("tr", {}, [
        el("th", { text: t("name") }), el("th", { text: t("professionType") }), el("th", { text: t("city") }),
        el("th", { text: t("rating") }), el("th", { text: t("reviews") }), el("th", { text: t("status") }),
      ])),
      tbody,
    ])])), pager]),
  );
  return box;
}

// =====================================================================
// الإشراف (بلاغات المجتمع والملفات)
// =====================================================================
async function moderationPanel() {
  const data = await api.get("/api/admin/moderation-queue");
  const reps = data.reports || [];
  const box = el("div", { class: "flex-col", style: "gap:14px" });
  const selected = new Set();
  const tbody = el("tbody");

  async function act(action, ids) {
    try {
      await api.post("/api/admin/moderation/bulk", { action, report_ids: ids });
      toast(t("saved"), "success");
      moderationPanel().then((n) => box.replaceWith(n));
    } catch (e) { toast(e.message, "error"); }
  }
  const removeBtn = el("button", { class: "btn btn-danger btn-sm", disabled: true, text: t("removeContent") });
  const hideBtn = el("button", { class: "btn btn-ghost btn-sm", disabled: true, text: t("hideContent") });
  const dismissBtn = el("button", { class: "btn btn-ghost btn-sm", disabled: true, text: t("dismissReport") });
  const sync = () => {
    const dis = selected.size === 0;
    removeBtn.disabled = hideBtn.disabled = dismissBtn.disabled = dis;
  };
  removeBtn.onclick = () => act("remove", [...selected]);
  hideBtn.onclick = () => act("hide", [...selected]);
  dismissBtn.onclick = () => act("dismiss", [...selected]);

  tbody.replaceChildren(reps.length ? reps.map((r) => {
    const cb = el("input", { type: "checkbox", class: "adm-check", "data-id": String(r.id), onchange: (e) => {
      e.target.checked ? selected.add(String(r.id)) : selected.delete(String(r.id)); sync();
    } });
    const targetText = r.target?.text || r.target?.title || `${r.target_type} #${r.target_id}`;
    return el("tr", {}, [
      el("td", {}, cb),
      el("td", { class: "num" }, el("strong", { text: `#${r.id}` })),
      el("td", { class: "cell-main" }, [
        el("span", { class: "t", text: String(targetText).slice(0, 90) }),
        el("span", { class: "s", text: `${r.target_type} · بواسطة ${r.reporter_name}` }),
      ]),
      el("td", { class: "sub", text: r.reason || "—" }),
      el("td", { class: "sub", text: fmtDt(r.created_at) }),
      el("td", {}, el("div", { class: "adm-actions" }, [
        el("button", { class: "btn btn-danger btn-sm", text: t("removeContent"), onclick: () => act("remove", [r.id]) }),
        el("button", { class: "btn btn-ghost btn-sm", text: t("hideContent"), onclick: () => act("hide", [r.id]) }),
        el("button", { class: "btn btn-ghost btn-sm", text: t("dismissReport"), onclick: () => act("dismiss", [r.id]) }),
      ])),
    ]);
  }) : []);

  box.append(
    el("div", { class: "adm-toolbar" }, [removeBtn, hideBtn, dismissBtn, el("span", { class: "spacer" }), el("button", { class: "btn btn-ghost btn-sm", text: "↻ " + t("refresh"), onclick: () => moderationPanel().then((n) => box.replaceWith(n)) })]),
    panel([body(reps.length ? el("div", { class: "adm-tbl-wrap" }, [el("table", { class: "adm-tbl" }, [
      el("thead", {}, el("tr", {}, [
        el("th"), el("th", { text: "ID" }), el("th", { text: t("section") }),
        el("th", { text: t("reportReason") }), el("th", { text: t("date") }), el("th", { text: t("actions") }),
      ])),
      tbody,
    ])]) : emptyState(t("noReports"), "flag"))]),
  );
  return box;
}

// =====================================================================
// المستخدمون (عرض فقط)
// =====================================================================
async function usersPanel() {
  const s = await api.get("/api/admin/analytics/summary");
  const u = s.users || {};
  return el("div", { class: "flex-col", style: "gap:16px" }, [
    kpiGrid([
      kpi({ icon: "users", label: t("kpiUsers"), value: num(u.total), tone: "info" }),
      kpi({ icon: "check", label: t("activeUsers"), value: num(u.active), tone: "green" }),
      kpi({ icon: "ban", label: t("suspendedUsers"), value: num(u.suspended), tone: "red" }),
      kpi({ icon: "shield", label: t("admins"), value: num(u.admins), tone: "navy" }),
      kpi({ icon: "scale", label: t("professionalsActive"), value: num(u.professionals_active), tone: "green" }),
      kpi({ icon: "clock", label: t("professionalsPending"), value: num(u.professionals_pending), tone: "gold" }),
      kpi({ icon: "userPlus", label: t("newToday"), value: num(u.new_today), tone: "info" }),
    ]),
    el("div", { class: "adm-notice warn" }, [
      el("span", { class: "ic" }, [icon("info", 20)]),
      el("div", {}, [
        el("h4", { text: t("usersReadOnly") }),
        el("p", { text: t("usersNote") }),
      ]),
    ]),
  ]);
}

// =====================================================================
// سجل التدقيق (عنصر إيضاحي)
// =====================================================================
async function auditPanel() {
  return el("div", { class: "adm-notice info" }, [
    el("span", { class: "ic" }, [icon("eye", 20)]),
    el("div", {}, [
      el("h4", { text: t("auditUnavailable") }),
      el("p", { text: t("auditNote") }),
    ]),
  ]);
}
