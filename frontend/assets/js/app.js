// نبراس — نقطة دخول SPA: تسجيل المسارات وربط واجهة الرأس
import { applyLang, setLang, tr } from "./i18n.js";
import { api, session, setUnauthorizedHandler } from "./api.js";
import { el, toast } from "./ui.js";
import { icon } from "./icons.js";
import { register, setNotFound, initRouter, render, navigate } from "./router.js";
import { openAuth, authForm, logout } from "./views/auth.js";
import { homeView } from "./views/home.js";
import { libraryView, textView, pdfView } from "./views/library.js";
import { jurisprudenceView, jurisprudenceDetailView } from "./views/jurisprudence.js";
import { blogView, blogDetailView, myArticlesView, blogEditorView } from "./views/blog.js";
import { proceduresView, procedureDetailView } from "./views/procedures.js";
import { professionalsView, professionalDetailView, myProfessionalView } from "./views/professionals.js";
import { documentsView, documentDetailView, myDocumentsView } from "./views/documents.js";
import { marketplaceView } from "./views/marketplace.js";
import { communityView, communityDetailView, communityNewView } from "./views/community.js";
import { calculatorsView, calculatorView } from "./views/calculators.js";
import { notificationsView, notificationsSettingsView } from "./views/notifications.js";
import { profileView } from "./views/profile.js";
import { assistantView } from "./views/assistant.js";
import { billingView, myOrdersView } from "./views/billing.js";
import { comparativeView, jurisdictionView, comparativeDetailView, comparativeNewView } from "./views/comparative.js";
import { compCountriesView, compCountryView, compLawView, compSearchView, compStatsView } from "./views/comp.js";

// ---------- مسارات ثابتة ----------
register("/home", homeView);
register("/", homeView);

register("/library", libraryView);
register("/text/:id", textView);
register("/pdf/:id", pdfView);

register("/jurisprudence", jurisprudenceView);
register("/jurisprudence/cat/:category", jurisprudenceView);
register("/jurisprudence/cat/:category/page/:page", jurisprudenceView);
register("/jurisprudence/q/:q", jurisprudenceView);
register("/jurisprudence/q/:q/page/:page", jurisprudenceView);
register("/jurisprudence/page/:page", jurisprudenceView);
register("/jurisprudence/:id", jurisprudenceDetailView);

register("/procedures", proceduresView);
register("/procedures/:slug", procedureDetailView);
register("/professionals", professionalsView);
register("/professionals/q/:q", professionalsView);
register("/professionals/me", myProfessionalView, { auth: true });
register("/professionals/:id", professionalDetailView);

register("/comparative", comparativeView);
register("/comparative/new", comparativeNewView);
register("/comparative/study/:id", comparativeDetailView);
register("/comparative/jurisdiction/:slug", jurisdictionView);
register("/comparative/jurisdiction/:slug/:tab", jurisdictionView);
register("/comparative/:id", comparativeDetailView);

// قانون مقارن مستقل
register("/foreign-law", compCountriesView);
register("/foreign-law/:code", compCountryView);
register("/foreign-law/:code/:tab", compCountryView);
register("/foreign-law/:code/law/:lawId", compLawView);
register("/foreign-law/search/:q", compSearchView);
register("/foreign-law/stats", compStatsView);

register("/documents", documentsView);
register("/documents/:slug", documentDetailView);
register("/my-documents", myDocumentsView, { auth: true });

register("/marketplace", marketplaceView);
register("/marketplace/:id", marketplaceView);

register("/assistant", assistantView, { auth: true });

register("/community", communityView);
register("/community/new", communityNewView, { auth: true });
register("/community/:id", communityDetailView);

register("/calculators", calculatorsView);
register("/calculators/:slug", calculatorView);

register("/notifications", notificationsView, { auth: true });
register("/notifications/settings", notificationsSettingsView, { auth: true });
register("/profile", profileView, { auth: true });

register("/billing", billingView, { auth: true });
register("/billing/orders", myOrdersView, { auth: true });

// مسارات مقالات (قبل /blog/:id)
register("/blog", blogView);
register("/blog/my", myArticlesView, { auth: true });
register("/blog/new", blogEditorView, { auth: true });
register("/blog/edit/:id", blogEditorView, { auth: true });
register("/blog/:id", blogDetailView);

// لوحة الإدارة صفحة مستقلة
register("/admin", () => { location.href = "/admin"; }, { auth: true, admin: true });

// ---------- مسارات مكتبة/مدونة متعددة الأجزاء ----------
function regMulti(base, handler, opts = {}) {
  const combos = [
    "", "/cat/:category", "/q/:q", "/cat/:category/q/:q",
    "/page/:page", "/cat/:category/page/:page", "/q/:q/page/:page",
    "/cat/:category/q/:q/page/:page",
  ];
  for (const c of combos) register(base + c, handler, opts);
}
regMulti("/library", libraryView);
regMulti("/blog", blogView);

setNotFound(() => el("div", { class: "card empty" }, [
  el("div", { class: "empty-icon" }, [icon("compass", 40)]),
  el("div", { text: tr("notFound") }),
  el("button", { class: "btn btn-ghost btn-sm", text: tr("back"), onclick: () => navigate("/home") }),
]));

setUnauthorizedHandler(() => {
  refreshHeader();
  toast(tr("unauthorized"), "warn");
  openAuth("login");
});

// ---------- ربط الرأس ----------
function refreshHeader() {
  const authBtns = document.getElementById("auth-buttons");
  const userMenu = document.getElementById("user-menu");
  const dropdown = document.getElementById("user-dropdown");
  const adminLink = document.getElementById("admin-link");
  const userName = document.getElementById("user-name");
  const avatar = document.getElementById("user-avatar");

  if (session.token) {
    authBtns.hidden = true;
    userMenu.hidden = false;
    adminLink.hidden = !session.isAdmin;
    const u = session.user || {};
    userName.textContent = u.full_name || u.email || "—";
    avatar.textContent = (u.full_name || u.email || "م").charAt(0);
  } else {
    authBtns.hidden = false;
    userMenu.hidden = true;
    dropdown.hidden = true;
  }
}

async function refreshNotifBadge() {
  const badge = document.getElementById("notif-badge");
  if (!badge) return;
  if (!session.token) { badge.hidden = true; return; }
  try {
    const data = await api.get("/api/notifications/unread-count");
    const n = Number(data?.unread_count ?? data?.count ?? 0);
    badge.hidden = n <= 0;
    badge.textContent = n > 99 ? "99+" : n;
  } catch { badge.hidden = true; }
}

function wireHeader() {
  document.getElementById("btn-login").addEventListener("click", () => openAuth("login"));
  document.getElementById("btn-register").addEventListener("click", () => openAuth("register"));
  document.getElementById("btn-logout").addEventListener("click", () => { logout(); });

  document.getElementById("btn-user").addEventListener("click", (e) => {
    e.stopPropagation();
    const dd = document.getElementById("user-dropdown");
    dd.hidden = !dd.hidden;
  });
  document.addEventListener("click", () => { document.getElementById("user-dropdown").hidden = true; });

  document.getElementById("lang-toggle").addEventListener("click", () => {
    setLang(currentLangIsFr() ? "ar" : "fr");
    syncLangUI();
    render();
  });

  document.getElementById("theme-toggle").addEventListener("click", () => {
    const root = document.documentElement;
    const next = root.dataset.theme === "dark" ? "light" : "dark";
    root.dataset.theme = next;
    localStorage.setItem("nibras_theme", next);
    syncThemeUI(next);
  });

  document.getElementById("nav-toggle").addEventListener("click", () => {
    document.getElementById("main-nav").classList.toggle("open");
  });
}

function currentLangIsFr() { return (localStorage.getItem("nibras_lang") || "ar") === "fr"; }

function syncLangUI() {
  document.getElementById("lang-label").textContent = currentLangIsFr() ? "ع" : "FR";
  document.querySelectorAll("[data-i18n]").forEach((n) => { n.textContent = tr(n.dataset.i18n); });
}

function syncThemeUI(theme) {
  const dark = theme === "dark";
  document.getElementById("theme-icon-sun").hidden = dark;
  document.getElementById("theme-icon-moon").hidden = !dark;
}

// ---------- إقلاع ----------
applyLang();
syncLangUI();
syncThemeUI(document.documentElement.dataset.theme || "light");
wireHeader();
refreshHeader();
refreshNotifBadge();

document.addEventListener("nibras:auth", () => { refreshHeader(); refreshNotifBadge(); });
document.addEventListener("nibras:need-auth", () => openAuth("login"));
document.addEventListener("nibras:lang", () => { syncLangUI(); });
window.addEventListener("nibras:route", refreshNotifBadge);

initRouter();
render();

setInterval(() => { if (session.token) refreshNotifBadge(); }, 60000);

window.addEventListener("DOMContentLoaded", () => {
  document.getElementById("year").textContent = new Date().getFullYear();
});
