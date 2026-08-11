// نبراس — لوحة التحكم الإدارية (الواجهة الرئيسية + التوجيه + لوحة القيادة)
import { api, session } from "../api.js";
import { el, toast } from "../ui.js";
import { tr, currentLang, setLang } from "../i18n.js";
import {
  t, go, content, fail, head, panel, body, kpi, kpiGrid, badge,
  tabs, listItem, lineChart, hBars, emptyState, skeleton, num, fmtDt,
  icon, SectionViews,
} from "./ui.js";
import { libraryView } from "./views/library.js";
import { blogView } from "./views/blog.js";
import { peopleView } from "./views/people.js";
import { commerceView } from "./views/commerce.js";
import { systemView } from "./views/system.js";
import { billingView } from "./views/billing.js";
import { jurisprudenceAdminView } from "./views/jurisprudence.js";

// ---------- أقسام الشريط الجانبي (12 قسمًا) ----------
const NAV = [
  { key: "dashboard", icon: "barChart", label: "dashboard" },
  { key: "library", icon: "book", label: "library" },
  { key: "blog", icon: "pen", label: "blog" },
  { key: "professionals", icon: "scale", label: "professionals" },
  { key: "templates", icon: "clipboard", label: "templates" },
  { key: "ads", icon: "megaphone", label: "ads" },
  { key: "billing", icon: "wallet", label: "billing" },
  { key: "jurisprudence", icon: "scale", label: "jurisprudence" },
  { key: "tenants", icon: "building", label: "tenants" },
  { key: "ai", icon: "cpu", label: "ai" },
  { key: "notifications", icon: "bell", label: "notifications" },
  { key: "users", icon: "users", label: "users" },
  { key: "audit", icon: "eye", label: "audit" },
  { key: "settings", icon: "settings", label: "settings" },
];

SectionViews.dashboard = dashboardView;
SectionViews.library = () => libraryView("texts");
SectionViews.blog = blogView;
SectionViews.professionals = () => peopleView("verification");
SectionViews.templates = () => commerceView("templates");
SectionViews.ads = () => commerceView("ads");
SectionViews.billing = billingView;
SectionViews.jurisprudence = jurisprudenceAdminView;
SectionViews.tenants = () => commerceView("tenants");
SectionViews.ai = () => systemView("ai");
SectionViews.notifications = () => systemView("notifications");
SectionViews.users = () => peopleView("users");
SectionViews.audit = () => peopleView("audit");
SectionViews.settings = () => systemView("settings");

function sectionTitle(key) {
  const nav = NAV.find((n) => n.key === key);
  return nav ? t(nav.label) : t("dashboard");
}

// ---------- الإقلاع ----------
async function boot() {
  document.documentElement.dataset.theme = localStorage.getItem("nibras_theme") || "light";
  setLang(currentLang());

  let me = null;
  try {
    me = await api.get("/api/auth/me");
    const roles = me.user?.roles || me.roles || [];
    if (!roles.includes("admin")) throw new Error("forbidden");
  } catch {
    location.href = "/#/home";
    return;
  }

  const user = me.user || session.user || {};
  document.getElementById("adm-user-name").textContent = user.full_name || user.email || "";
  const avatar = document.getElementById("adm-avatar");
  avatar.textContent = (user.full_name || user.email || "م").trim().charAt(0);

  wireSidebar();
  wireTopbar();
  router();

  window.addEventListener("hashchange", router);
  window.addEventListener("keydown", (e) => {
    if (e.target && /^(input|textarea|select)$/i.test(e.target.tagName)) return;
    if (e.altKey && e.key >= "1" && e.key <= "9") {
      const nav = NAV[Number(e.key) - 1];
      if (nav) { e.preventDefault(); go(nav.key); }
    }
    if (e.key === "?") {
      toast(`${t("shortcutsHint")}: Alt+1..9`, "info");
    }
  });
}

function wireSidebar() {
  const navEl = document.getElementById("adm-nav");
  const render = (current) => {
    navEl.replaceChildren(...NAV.map((n) =>
      el("a", {
        class: "adm-item" + (n.key === current ? " active" : ""),
        href: `#/admin/${n.key}`, onclick: () => closeSidebar(),
      }, [
        el("span", { class: "ic" }, [icon(n.icon, 18)]),
        el("span", { text: t(n.label) }),
      ])));
  };
  navEl._render = render;
  navEl.dataset.current = "";

  document.getElementById("adm-logout").onclick = async () => {
    try { await api.post("/api/auth/logout", { refresh_token: session.refresh }); } catch { /* تجاهل */ }
    session.clear();
    location.href = "/#/home";
  };
}

function closeSidebar() {
  document.body.classList.remove("side-open");
}

function wireTopbar() {
  const burger = document.getElementById("adm-burger");
  burger.onclick = () => document.body.classList.toggle("side-open");

  const themeBtn = document.getElementById("adm-theme-btn");
  const langBtn = document.getElementById("adm-lang-btn");
  const paint = () => {
    const dark = document.documentElement.dataset.theme === "dark";
    themeBtn.replaceChildren(icon(dark ? "sun" : "moon", 16), " " + t(dark ? "light" : "dark"));
    langBtn.textContent = currentLang() === "ar" ? "FR" : "ع";
  };
  paint();
  themeBtn.onclick = () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    localStorage.setItem("nibras_theme", next);
    paint();
  };
  langBtn.onclick = () => {
    setLang(currentLang() === "ar" ? "fr" : "ar");
    location.reload();
  };
}

// ---------- التوجيه ----------
function router() {
  let section = location.hash.replace("#/admin/", "") || "dashboard";
  if (!SectionViews[section]) section = "dashboard";
  state_section = section;

  document.getElementById("adm-title").textContent = sectionTitle(section);
  document.getElementById("adm-crumb").textContent = t("section") + " / " + sectionTitle(section);

  const navEl = document.getElementById("adm-nav");
  if (navEl._render) navEl._render(section);

  const out = SectionViews[section]();
  if (out && typeof out.then === "function") {
    content().replaceChildren(skeleton(3, 90));
    out.then((node) => content().replaceChildren(node)).catch((e) => fail(e));
  } else {
    content().replaceChildren(out);
  }
}

let state_section = "dashboard";

// ---------- لوحة القيادة ----------
async function dashboardView() {
  const [s, textsData, blogData, tplData] = await Promise.all([
    api.get("/api/admin/analytics/summary"),
    api.get("/api/texts?limit=5").catch(() => ({})),
    api.get("/api/admin/blog/articles?limit=5").catch(() => ({})),
    api.get("/api/admin/marketplace/templates").catch(() => ({})),
  ]);
  const users = s.users || {};
  const ai = s.ai || {};
  const calcs = s.calculators || {};
  const docs = s.documents || {};
  const comm = s.community || {};
  const prof = s.professionals || {};
  const mkt = s.marketplace || {};
  const verif = s.verification || {};
  const mod = s.moderation || {};

  const texts = textsData.texts || textsData || [];
  const articles = blogData.articles || blogData || [];
  const templates = tplData.templates || tplData || [];

  const trends = (s.trends || []).slice(-7).map((tr) => ({
    label: String(tr.date || "").slice(5),
    users: tr.new_users || 0, docs: tr.documents || 0, ai: tr.ai_queries || 0,
  }));

  const byMode = Object.entries(ai.by_mode || {});

  const latestList = (title, items, icon, viewKey) =>
    panel([
      head(title, [el("button", { class: "btn btn-ghost btn-sm", text: t("viewAll"), onclick: () => go(viewKey) })]),
      body(items.length
        ? el("div", { class: "adm-list" }, items.slice(0, 5).map((it) =>
          listItem({ icon, title: it.title || it.name || "—", sub: it.sub || "", val: it.val })))
        : emptyState(t("noData"), icon)),
    ]);

  const actions = [
    ["library", "book", t("library")], ["blog", "pen", t("blog")],
    ["templates", "clipboard", t("templates")], ["ads", "megaphone", t("ads")],
    ["professionals", "scale", t("professionals")], ["ai", "cpu", t("ai")],
  ];

  return el("div", { class: "flex-col", style: "gap:16px" }, [
    kpiGrid([
      kpi({ icon: "users", label: t("kpiUsers"), value: num(users.total), sub: `${t("newToday")}: ${num(users.new_today)}`, tone: "info" }),
      kpi({ icon: "cpu", label: t("kpiAi"), value: num(ai.total), sub: `${t("today")}: ${num(ai.today)}`, tone: "green" }),
      kpi({ icon: "file", label: t("kpiDocs"), value: num(docs.generated_total), sub: `${t("today")}: ${num(docs.generated_today)}`, tone: "gold" }),
      kpi({ icon: "messageSquare", label: t("kpiCommunity"), value: num(comm.posts), sub: `${t("comments")}: ${num(comm.comments)}`, tone: "navy" }),
      kpi({ icon: "calculator", label: t("kpiCalculators"), value: num(calcs.total_runs), sub: `${t("today")}: ${num(calcs.today)}`, tone: "info" }),
      kpi({ icon: "scale", label: t("kpiProfessionals"), value: num(prof.by_status?.verified ?? prof.total), sub: `${t("professionalsPending")}: ${num(verif.pending_requests)}`, tone: "gold" }),
      kpi({ icon: "clipboard", label: t("kpiTemplates"), value: num(mkt.templates), sub: `${t("downloads")}: ${num(mkt.purchases)}`, tone: "green" }),
      kpi({ icon: "creditCard", label: t("kpiRevenue"), value: money_cents(mkt.catalog_value_cents), sub: `${t("openReports")}: ${num(mod.open_reports)}`, tone: "red" }),
    ]),

    el("div", { class: "adm-grid-2" }, [
      panel([head(t("trendsTitle"), [badge(fmtDt(s.generated_at), "gray")]),
        body(trends.length
          ? lineChart(trends.map((x) => x.label), trends.map((x) => x.ai), { width: 620, height: 210 })
          : emptyState(t("noData"), "trendingUp"))]),
      panel([head(t("ai") + " — " + t("byMode"), [badge(num(ai.total), "blue")]),
        body(byMode.length
          ? hBars(byMode.map(([m, c]) => ({ label: modeLabel(m), value: c })))
          : emptyState(t("noData"), "cpu"))]),
    ]),

    latestList(t("recentTexts"), texts.map((x) => ({ title: x.title, sub: x.category_name || "", val: "" })), "book", "library"),
    el("div", { class: "adm-grid-3" }, [
      latestList(t("recentArticles"), articles.map((a) => ({ title: a.title, sub: fmtDt(a.updated_at || a.created_at), val: num(a.views) })), "pen", "blog"),
      latestList(t("recentProfessionals"), [], "scale", "professionals"),
      latestList(t("recentTemplates"), templates.map((x) => ({ title: x.title, sub: `${x.category_name || ""} · ${x.download_count ?? 0} ${t("downloads")}`, val: "" })), "clipboard", "templates"),
    ]),

    panel([head(t("quickActions")),
      body(el("div", { class: "adm-grid-3" }, actions.map(([key, icn, label]) =>
        el("button", { class: "btn btn-outline btn-sm", onclick: () => go(key) }, [icon(icn, 16), " " + label]))))]),
  ]);
}

function modeLabel(m) {
  const map = { chat: t("chat"), document: t("kpiDocs"), procedure: t("procedures"), search: t("search") };
  return map[m] || String(m || "—");
}

const money_cents = (c) => `${(Number(c) || 0) / 100} ${t("currency")}`;

boot();
