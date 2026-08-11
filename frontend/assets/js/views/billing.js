// نبراس — المحفظة والاشتراكات (نقاط + ظهور مميز) عبر سير عمل الطلبات اليدوية
import { tr, currentLang } from "../i18n.js";
import { api, session } from "../api.js";
import { el, toast, fmtDate, openModal, closeModal } from "../ui.js";
import { navigate } from "../router.js";
import { icon } from "../icons.js";

const state = { plans: [], orders: [], balance: 0, premium: null };

async function loadPlans() {
  try { const d = await api.get("/api/plans"); state.plans = d.plans || []; }
  catch (e) { state.plans = []; }
}

async function loadWallet() {
  if (!session.token) { state.balance = 0; state.premium = null; return; }
  try {
    const w = await api.get("/api/wallet");
    state.balance = w.balance || 0;
    state.premium = w.premium_until || null;
  } catch { state.balance = 0; state.premium = null; }
}

async function loadOrders() {
  if (!session.token) { state.orders = []; return; }
  try { const d = await api.get("/api/orders/mine?limit=50"); state.orders = d.orders || []; }
  catch { state.orders = []; }
}

const price = (p) => `${p.price} ${tr("currency")}`;

/* ---------------- حصة باقة قابلة لإعادة الاستخدام (شارة + وصف + سعر) ---------------- */
export const planBadge = (p) => el("span", {
  class: `badge-pill ${p.kind === "premium_listing" ? "badge-gold" : "badge-green"}`,
}, [
  icon(p.kind === "premium_listing" ? "star" : "coins", 12),
  " " + tr(p.kind === "premium_listing" ? "planKindPremium" : "planKindCredits"),
]);

export const planMeta = (p) => {
  const items = [];
  if (p.kind === "credits" && p.credits) items.push(`${p.credits} ${tr("includesCredits")}`);
  if (p.kind === "premium_listing" && p.duration_days) items.push(`${p.duration_days} ${tr("includesDays")}`);
  if (p.kind === "premium_listing") items.push(tr("needVerifiedPro"));
  return items;
};

/* ---- شراء باقة (ينشئ طلب pending ثم يعرض التعليمات) ---- */
export function buyPlan(plan) {
  if (!session.token) {
    toast(tr("unauthorized"), "warn");
    document.dispatchEvent(new CustomEvent("nibras:need-auth"));
    return;
  }
  openModal(planModal(plan));
}

function planModal(plan) {
  const body = el("div", {});
  const payBtn = el("button", {
    class: "btn btn-gold btn-block mt-16",
    text: tr("payNowTitle"),
    onclick: async () => {
      payBtn.disabled = true;
      payBtn.textContent = tr("loading");
      try {
        const order = await api.post("/api/orders", { plan: plan.slug });
        body.replaceChildren(
          el("div", { class: "ta-center", style: "padding:8px 0" }, [
            el("div", { style: "font-size:42px;color:var(--gold)" }, [
              icon("checkCircle", 42),
            ]),
            el("p", { class: "small muted", style: "margin:10px 0" }, [tr("orderCreated")]),
            el("div", { class: "order-id", style: "font-size:22px;font-weight:700;color:var(--gold)", text: `#${order.id}` }),
            el("div", { class: "small", style: "margin-top:8px;font-weight:700", text: `${order.amount} ${tr("currency")}` }),
          ]),
          el("div", { class: "notice", style: "margin-top:14px" }, [tr("paymentManualNote")]),
        );
        toast(tr("orderCreated"), "success");
      } catch (err) {
        body.replaceChildren(el("div", { class: "notice error", text: err.message }));
        payBtn.disabled = false;
        payBtn.textContent = tr("payNowTitle");
      }
    },
  });

  body.append(
    el("div", { class: "flex", style: "gap:8px;align-items:center;margin-bottom:10px" }, [planBadge(plan)]),
    el("div", { style: "font-weight:700;font-size:18px", text: plan.name }),
    plan.description ? el("p", { class: "small muted", text: plan.description }) : null,
    el("div", { class: "flex", style: "gap:6px;flex-wrap:wrap;margin:10px 0" },
      planMeta(plan).map((t) => el("div", { class: "small", style: "display:flex;gap:4px;align-items:center" }, [icon("check", 12), " " + t]))),
    el("div", { class: "pc-price", text: price(plan) }),
  );

  return el("div", {}, [
    el("h3", { text: tr("payNowTitle") }),
    body,
    payBtn,
  ]);
}

/* ---- جدول الحالة ---- */
const statusBadge = (o) => {
  if (o.status === "paid") return el("span", { class: "badge-pill badge-green", text: tr("orderStatusPaid") });
  if (o.status === "cancelled") return el("span", { class: "badge-pill badge-red", text: tr("orderStatusCancelled") });
  return el("span", { class: "badge-pill badge-gold", text: tr("orderStatusPending") });
};

/* ---- بطاقة إعلانية Compact ---- */
export function orderCard(o) {
  return el("tr", {}, [
    el("td", { text: `#${o.id}` }),
    el("td", { text: o.plan_name || "—" }),
    el("td", { text: `${o.amount} ${tr("currency")}` }),
    el("td", { text: o.payment_method === "manual" ? tr("manualPayment") : o.payment_method }),
    el("td", { text: fmtDate(o.created_at, currentLang()) }),
    el("td", {}, [statusBadge(o)]),
  ]);
}

/* ---------- الصفحة الرئيسية للمحفظة ---------- */
export async function billingView() {
  await Promise.all([loadPlans(), loadWallet(), loadOrders()]).catch(() => {});

  const walletCard = session.token
    ? el("div", { class: "card" }, [
        el("h3", {}, [icon("wallet", 16), " " + tr("wallet")]),
        el("div", { class: "flex", style: "align-items:baseline;gap:10px;margin:12px 0" }, [
          el("div", { style: "font-size:34px;font-weight:700;color:var(--gold)", text: String(state.balance) }),
          el("div", { class: "small muted", text: tr("walletBalance") }),
        ]),
        state.premium
          ? el("div", { class: "badge-pill badge-gold", text: `${tr("premiumTitle")}: ${state.premium}` })
          : el("div", { class: "small muted", text: tr("needVerifiedPro") }),
        el("button", {
          class: "btn btn-ghost btn-sm mt-12", text: tr("myOrders"),
          onclick: () => navigate("/billing/orders"),
        }),
      ])
    : el("div", { class: "card" }, [
        el("h3", { text: tr("wallet") }),
        el("p", { class: "small muted", style: "margin:8px 0" }, [tr("buyCreditsSub")]),
        el("button", { class: "btn btn-primary btn-sm", text: tr("login"), onclick: () => navigate("/login") }),
      ]);

  const plansGrid = el("div", { class: "grid grid-3" });
  for (const p of state.plans || []) {
    plansGrid.append(el("div", { class: "card card-hover" }, [
      el("div", { class: "flex", style: "gap:8px;align-items:center;margin-bottom:10px" }, [planBadge(p)]),
      el("div", { style: "font-weight:700;font-size:18px", text: p.name }),
      el("div", { class: "pc-price", text: price(p) }),
      el("p", { class: "small muted", text: p.description }),
      el("div", { class: "flex mt-12", style: "gap:6px;flex-wrap:wrap" },
        planMeta(p).map((t) => el("span", { class: "spec-tag", text: t }))),
      el("button", { class: "btn btn-gold btn-block mt-16", text: tr("buyNow"), onclick: () => buyPlan(p) }),
    ]));
  }

  return el("div", {}, [
    el("div", { class: "section-head" }, [
      el("div", {}, [
        el("div", { class: "eyebrow", text: tr("wallet") }),
        el("h2", { text: tr("myCredits") }),
      ]),
    ]),
    walletCard,
    el("h3", { style: "margin:24px 0 12px", text: tr("choosePlan") }),
    plansGrid,
  ]);
}

/* ---------- صفحة طلباتي ---------- */
export async function myOrdersView() {
  await loadOrders().catch(() => {});
  const rows = (state.orders || []).length
    ? (state.orders || []).map(orderCard)
    : [el("tr", {}, [el("td", { colspan: 6, class: "ta-center muted", text: tr("noOrders") })])];

  return el("div", {}, [
    el("div", { class: "section-head" }, [
      el("div", {}, [
        el("div", { class: "eyebrow", text: tr("wallet") }),
        el("h2", { text: tr("myOrders") }),
      ]),
    ]),
    el("div", { class: "card" }, [
      el("div", { class: "table-wrap" }, [
        el("table", { class: "table" }, [
          el("thead", {}, [el("tr", {}, [
            el("th", { text: tr("orderIdLabel") }),
            el("th", { text: tr("choosePlan") }),
            el("th", { text: tr("amount") }),
            el("th", { text: tr("orderPayment") }),
            el("th", { text: tr("orderDate") }),
            el("th", { text: tr("orderStatus") }),
          ])]),
          el("tbody", {}, rows),
        ]),
      ]),
    ]),
  ]);
}