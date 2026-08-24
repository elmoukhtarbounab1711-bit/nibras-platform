// نبراس — لوحة التحكم الإدارية (الواجهة الرئيسية + التوجيه + لوحة القيادة)
import { api, session } from "../api.js";
import { el, toast } from "../ui.js";
import { tr, currentLang, setLang } from "../i18n.js";
import {
  t, go, content, fail, head, panel, body, kpi, kpiGrid, badge,
  tabs, listItem, lineChart, hBars, emptyState, skeleton, num, fmtDt,
  icon, SectionViews, state,
} from "./ui.js";
import { libraryView } from "./views/library.js";
import { blogView } from "./views/blog.js";
import { peopleView } from "./views/people.js";
import { commerceView } from "./views/commerce.js";
import { systemView } from "./views/system.js";
import { billingView } from "./views/billing.js";
import { jurisprudenceAdminView } from "./views/jurisprudence.js";
import { comparativeAdminView } from "./views/comparative.js";
import { researchAdminView } from "./views/research.js";
import { visitorsView } from "./views/visitors.js";


// ---------- أقسام الشريط الجانبي (مع تصنيفات) ----------
const NAV = [
  { key: "dashboard", icon: "barChart", label: "dashboard", group: "overview" },
  { key: "visitors", icon: "eye", label: "visitors", group: "overview" },

  { key: "library", icon: "book", label: "library", group: "content" },
  { key: "blog", icon: "pen", label: "blog", group: "content" },
  { key: "professionals", icon: "scale", label: "professionals", group: "content" },
  { key: "templates", icon: "clipboard", label: "templates", group: "content" },
  { key: "ads", icon: "megaphone", label: "ads", group: "content" },

  { key: "billing", icon: "wallet", label: "billing", group: "legal" },
  { key: "jurisprudence", icon: "scale", label: "jurisprudence", group: "legal" },
  { key: "comparative", icon: "globe", label: "comparative", group: "legal" },
  { key: "research", icon: "book", label: "researchLibrary", group: "legal" },

  { key: "tenants", icon: "building", label: "tenants", group: "system" },
  { key: "ai", icon: "cpu", label: "ai", group: "system" },
  { key: "notifications", icon: "bell", label: "notifications", group: "system" },
  { key: "users", icon: "users", label: "users", group: "system" },
  { key: "audit", icon: "eye", label: "audit", group: "system" },
  { key: "settings", icon: "settings", label: "settings", group: "system" },
];

const NAV_GROUPS = {
  overview: "نظرة عامة",
  content: "المحتوى",
  legal: "قانوني",
  system: "النظام",
};

SectionViews.dashboard = dashboardView;
SectionViews.visitors = visitorsView;
SectionViews.library = () => libraryView("texts");
SectionViews.blog = blogView;
SectionViews.professionals = () => peopleView("verification");
SectionViews.templates = () => commerceView("templates");
SectionViews.ads = () => commerceView("ads");
SectionViews.billing = billingView;
SectionViews.jurisprudence = jurisprudenceAdminView;
SectionViews.comparative = comparativeAdminView;
SectionViews.research = researchAdminView;

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
    const nodes = [];
    let lastGroup = null;
    for (const n of NAV) {
      if (n.group !== lastGroup) {
        lastGroup = n.group;
        const groupLabel = NAV_GROUPS[n.group] || n.group;
        nodes.push(el("div", { class: "adm-nav-group", text: groupLabel }));
      }
      nodes.push(el("a", {
        class: "adm-item" + (n.key === current ? " active" : ""),
        href: `#/admin/${n.key}`, onclick: () => closeSidebar(),
      }, [
        el("span", { class: "ic" }, [icon(n.icon, 18)]),
        el("span", { text: t(n.label) }),
      ]));
    }
    navEl.replaceChildren(...nodes);
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
  state.section = section;

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


// ---------- لوحة القيادة ----------
let _dashTimer = null;

async function dashboardView() {
  if (_dashTimer) { clearInterval(_dashTimer); _dashTimer = null; }

  const root = el("div", { class: "flex-col", style: "gap:20px" });

  // زر التحديث التلقائي
  let autoRefresh = false;
  const refreshBtn = el("button", { class: "adm-auto-refresh", type: "button" }, [
    el("span", { class: "pulse-dot" }),
    el("span", { text: "تحديث تلقائي" }),
  ]);
  refreshBtn.onclick = () => {
    autoRefresh = !autoRefresh;
    refreshBtn.classList.toggle("active", autoRefresh);
    if (autoRefresh) {
      _dashTimer = setInterval(() => loadDashboard(root), 30000);
    } else if (_dashTimer) {
      clearInterval(_dashTimer);
      _dashTimer = null;
    }
  };

  root.append(
    el("div", { class: "flex-between", style: "align-items:center" }, [
      el("div", {}, [
        el("h2", { style: "margin:0;font-family:var(--font-head);font-size:22px", text: t("dashboard") }),
        el("p", { style: "margin:4px 0 0;color:var(--ink-3);font-size:13px", text: "نظرة عامة على المنصة" }),
      ]),
      refreshBtn,
    ]),
  );

  root.append(el("div", { id: "dash-content", class: "flex-col", style: "gap:20px" }, [skeleton(3, 90)]));
  await loadDashboard(root);
  return root;
}

async function loadDashboard(root) {
  const container = root.querySelector("#dash-content");
  if (!container) return;

  try {
    const [s, textsData, blogData, tplData, visitorData] = await Promise.all([
      api.get("/api/admin/analytics/summary"),
      api.get("/api/texts?limit=5").catch(() => ({})),
      api.get("/api/admin/blog/articles?limit=5").catch(() => ({})),
      api.get("/api/admin/marketplace/templates").catch(() => ({})),
      api.get("/api/admin/visitors/summary?days=7").catch(() => ({})),
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

    const latestList = (title, items, iconName, viewKey) =>
      panel([
        head(title, [el("button", { class: "btn btn-ghost btn-sm", text: t("viewAll"), onclick: () => go(viewKey) })]),
        body(items.length
          ? el("div", { class: "adm-list" }, items.slice(0, 5).map((it) =>
            listItem({ icon: iconName, title: it.title || it.name || "—", sub: it.sub || "", val: it.val })))
          : emptyState(t("noData"), iconName)),
      ]);

    container.replaceChildren(
      // ── KPIs الرئيسية ──
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

      // ── صف الزوار السريع ──
      kpiGrid([
        kpi({ icon: "eye", label: "زيارات آخر أسبوع", value: num(visitorData.week_visits || 0), sub: `اليوم: ${num(visitorData.today_visits || 0)}`, tone: "info" }),
        kpi({ icon: "users", label: "زوار فريدون", value: num(visitorData.unique_visitors || 0), sub: `مسجلون: ${num(visitorData.unique_users || 0)}`, tone: "green" }),
        kpi({ icon: "activity", label: "الزوار النشطون", value: num(visitorData.active_now || 0), sub: "آخر 5 دقائق", tone: "red" }),
      ]),

      // ── الرسم البياني + استخدام الذكاء ──
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

      // ── أحدث المحتوى ──
      latestList(t("recentTexts"), texts.map((x) => ({ title: x.title, sub: x.category_name || "", val: "" })), "book", "library"),
      el("div", { class: "adm-grid-3" }, [
        latestList(t("recentArticles"), articles.map((a) => ({ title: a.title, sub: fmtDt(a.updated_at || a.created_at), val: num(a.views) })), "pen", "blog"),
        latestList(t("recentProfessionals"), [], "scale", "professionals"),
        latestList(t("recentTemplates"), templates.map((x) => ({ title: x.title, sub: `${x.category_name || ""} · ${x.download_count ?? 0} ${t("downloads")}`, val: "" })), "clipboard", "templates"),
      ]),

      // ── إجراءات سريعة ──
      panel([head(t("quickActions")),
        body(el("div", { class: "adm-grid-3" }, [
          ...[["library", "book", t("library")], ["blog", "pen", t("blog")],
            ["templates", "clipboard", t("templates")], ["ads", "megaphone", t("ads")],
            ["professionals", "scale", t("professionals")], ["ai", "cpu", t("ai")]].map(([key, icn, label]) =>
            el("button", { class: "btn btn-outline btn-sm", onclick: () => go(key) }, [icon(icn, 16), " " + label])),
        ]))]),
    );
  } catch (e) {
    container.replaceChildren(
      el("div", { class: "adm-404" }, [
        el("div", { class: "ic" }, [icon("alertTriangle", 42)]),
        el("p", { text: `خطأ في تحميل البيانات: ${e.message}` }),
      ])
    );
  }
}

function modeLabel(m) {
  const map = { chat: t("chat"), document: t("kpiDocs"), procedure: t("procedures"), search: t("search") };
  return map[m] || String(m || "—");
}

const money_cents = (c) => `${(Number(c) || 0) / 100} ${t("currency")}`;

boot();
