// نبراس — نقطة دخول SPA: تسجيل المسارات وربط واجهة الرأس
import { applyLang, setLang, tr } from "./i18n.js";
import { api, session, setUnauthorizedHandler } from "./api.js";
import { el, toast } from "./ui.js";
import { icon } from "./icons.js";
import { register, setNotFound, initRouter, render, navigate } from "./router.js";
import { openAuth, authForm, logout } from "./views/auth.js";
import { initCookieConsent, onCookieConsent, hasCookieConsent } from "./components/cookie-consent.js";
import { initDownloadAppButton } from "./components/download-app.js";

// ---------- مساعد تحميل كسول ----------
function lazy(mod) {
  return (...args) => mod.then(m => m.default ? m.default(...args) : Object.values(m)[0](...args));
}

function lazyMulti(mod, fnName) {
  return (...args) => mod.then(m => m[fnName](...args));
}

// ---------- تحميل Modules ----------
const _home = import("./views/home.js");
const _library = import("./views/library.js");
const _jurisprudence = import("./views/jurisprudence.js");
const _blog = import("./views/blog.js");
const _procedures = import("./views/procedures.js");
const _professionals = import("./views/professionals.js");
const _documents = import("./views/documents.js");
const _legalFrench = import("./views/legal_french.js");
const _community = import("./views/community.js");
const _calculators = import("./views/calculators.js");
const _notifications = import("./views/notifications.js");
const _profile = import("./views/profile.js");
const _assistant = import("./views/assistant.js");
const _billing = import("./views/billing.js");
const _comparative = import("./views/comparative.js");
const _research = import("./views/research.js");
const _legal = import("./views/legal.js");

// ---------- مسارات ثابتة ----------
register("/home", (...a) => _home.then(m => m.homeView(...a)));
register("/", (...a) => _home.then(m => m.homeView(...a)));

register("/library", (...a) => _library.then(m => m.libraryView(...a)));
register("/text/:id", (...a) => _library.then(m => m.textView(...a)));
register("/pdf/:id", (...a) => _library.then(m => m.pdfView(...a)));

register("/jurisprudence", (...a) => _jurisprudence.then(m => m.jurisprudenceView(...a)));
register("/jurisprudence/cat/:category", (...a) => _jurisprudence.then(m => m.jurisprudenceView(...a)));
register("/jurisprudence/cat/:category/page/:page", (...a) => _jurisprudence.then(m => m.jurisprudenceView(...a)));
register("/jurisprudence/q/:q", (...a) => _jurisprudence.then(m => m.jurisprudenceView(...a)));
register("/jurisprudence/q/:q/page/:page", (...a) => _jurisprudence.then(m => m.jurisprudenceView(...a)));
register("/jurisprudence/page/:page", (...a) => _jurisprudence.then(m => m.jurisprudenceView(...a)));
register("/jurisprudence/:id", (...a) => _jurisprudence.then(m => m.jurisprudenceDetailView(...a)));

register("/procedures", (...a) => _procedures.then(m => m.proceduresView(...a)));
register("/procedures/:slug", (...a) => _procedures.then(m => m.procedureDetailView(...a)));
register("/professionals", (...a) => _professionals.then(m => m.professionalsView(...a)));
register("/professionals/q/:q", (...a) => _professionals.then(m => m.professionalsView(...a)));
register("/professionals/me", (...a) => _professionals.then(m => m.myProfessionalView(...a)), { auth: true });
register("/professionals/:id", (...a) => _professionals.then(m => m.professionalDetailView(...a)));

register("/comparative", (...a) => _comparative.then(m => m.comparativeView(...a)));
register("/comparative/new", (...a) => _comparative.then(m => m.comparativeNewView(...a)));
register("/comparative/study/:id", (...a) => _comparative.then(m => m.comparativeDetailView(...a)));
register("/comparative/jurisdiction/:slug", (...a) => _comparative.then(m => m.jurisdictionView(...a)));
register("/comparative/jurisdiction/:slug/:tab", (...a) => _comparative.then(m => m.jurisdictionView(...a)));
register("/comparative/:id", (...a) => _comparative.then(m => m.comparativeDetailView(...a)));

register("/research", (...a) => _research.then(m => m.researchView(...a)));
register("/research/category/:category", (...a) => _research.then(m => m.researchView(...a)));
register("/research/type/:type", (...a) => _research.then(m => m.researchView(...a)));
register("/research/:id", (...a) => _research.then(m => m.researchBookView(...a)));

register("/documents", (...a) => _documents.then(m => m.documentsView(...a)));
register("/documents/:slug", (...a) => _documents.then(m => m.documentDetailView(...a)));
register("/my-documents", (...a) => _documents.then(m => m.myDocumentsView(...a)), { auth: true });

register("/legal-french", (...a) => _legalFrench.then(m => m.legalFrenchView(...a)));
register("/legal-french/treaties", (...a) => _legalFrench.then(m => m.legalFrenchTreatiesView(...a)));
register("/legal-french/treaty/:id", (...a) => _legalFrench.then(m => m.legalFrenchTreatyDetailView(...a)));
register("/legal-french/lesson/:id", (...a) => _legalFrench.then(m => m.legalFrenchLessonView(...a)));
register("/legal-french/quiz/:lessonId", (...a) => _legalFrench.then(m => m.legalFrenchQuizView(...a)), { auth: true });
register("/legal-french/:id", (...a) => _legalFrench.then(m => m.legalFrenchLevelView(...a)));

register("/assistant", (...a) => _assistant.then(m => m.assistantView(...a)), { auth: true });

register("/community", (...a) => _community.then(m => m.communityView(...a)));
register("/community/new", (...a) => _community.then(m => m.communityNewView(...a)), { auth: true });
register("/community/:id", (...a) => _community.then(m => m.communityDetailView(...a)));

register("/calculators", (...a) => _calculators.then(m => m.calculatorsView(...a)));
register("/calculators/:slug", (...a) => _calculators.then(m => m.calculatorView(...a)));

register("/notifications", (...a) => _notifications.then(m => m.notificationsView(...a)), { auth: true });
register("/notifications/settings", (...a) => _notifications.then(m => m.notificationsSettingsView(...a)), { auth: true });
register("/profile", (...a) => _profile.then(m => m.profileView(...a)), { auth: true });

register("/billing", (...a) => _billing.then(m => m.billingView(...a)), { auth: true });
register("/billing/orders", (...a) => _billing.then(m => m.myOrdersView(...a)), { auth: true });

register("/blog", (...a) => _blog.then(m => m.blogView(...a)));
register("/blog/my", (...a) => _blog.then(m => m.myArticlesView(...a)), { auth: true });
register("/blog/new", (...a) => _blog.then(m => m.blogEditorView(...a)), { auth: true });
register("/blog/edit/:id", (...a) => _blog.then(m => m.blogEditorView(...a)), { auth: true });
register("/blog/:id", (...a) => _blog.then(m => m.blogDetailView(...a)));

register("/admin", () => { location.href = "/admin"; }, { auth: true, admin: true });

register("/privacy", (...a) => _legal.then(m => m.privacyView(...a)));
register("/terms", (...a) => _legal.then(m => m.termsView(...a)));
register("/cookie-policy", (...a) => _legal.then(m => m.cookiePolicyView(...a)));
register("/disclaimer", (...a) => _legal.then(m => m.disclaimerView(...a)));
register("/guide", (...a) => _legal.then(m => m.guideView(...a)));

// ---------- مسارات مكتبة/مدونة متعددة الأجزاء ----------
function regMulti(base, loader, opts = {}) {
  const combos = [
    "", "/cat/:category", "/q/:q", "/cat/:category/q/:q",
    "/page/:page", "/cat/:category/page/:page", "/q/:q/page/:page",
    "/cat/:category/q/:q/page/:page",
  ];
  for (const c of combos) register(base + c, loader, opts);
}
regMulti("/library", (...a) => _library.then(m => m.libraryView(...a)));
regMulti("/blog", (...a) => _blog.then(m => m.blogView(...a)));

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

// شريط موافقة ملفات تعريف الارتباط (القانون 09-08)
initCookieConsent();

// زر تحميل التطبيق — يظهر بعد عرض شريط الكوكيز
onCookieConsent(() => initDownloadAppButton());
if (hasCookieConsent()) {
  initDownloadAppButton();
}

setInterval(() => { if (session.token) refreshNotifBadge(); }, 60000);

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js").catch(() => {});
}

window.addEventListener("DOMContentLoaded", () => {
  document.getElementById("year").textContent = new Date().getFullYear();
});
