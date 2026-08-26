// نبراس — نقطة دخول SPA: تسجيل المسارات وربط واجهة الرأس
import { applyLang, setLang, tr, preloadFr } from "./i18n.js";
import { api, session, setUnauthorizedHandler } from "./api.js";
import { el, toast } from "./ui.js";
import { icon } from "./icons.js";
import { register, setNotFound, initRouter, render, navigate } from "./router.js";
import { openAuth, logout } from "./views/auth.js";

// حمولة أولى فقط: الرئيسية + المكونات الأساسية (~35KB بدل ~450KB)
import { homeView } from "./views/home.js";

// ---------- حمولات كسولة: تُحمَّل عند أول طلب ----------
const lazy = (mod, fn) => (params) => import(mod).then((m) => m[fn](params));

register("/home", homeView);
register("/", homeView);
register("/login", () => { openAuth("login"); return el("div"); });

register("/library", lazy("./views/library.js", "libraryView"));
register("/text/:id", lazy("./views/library.js", "textView"));
register("/pdf/:id", lazy("./views/library.js", "pdfView"));

register("/jurisprudence", lazy("./views/jurisprudence.js", "jurisprudenceView"));
register("/jurisprudence/cat/:category", lazy("./views/jurisprudence.js", "jurisprudenceView"));
register("/jurisprudence/cat/:category/page/:page", lazy("./views/jurisprudence.js", "jurisprudenceView"));
register("/jurisprudence/q/:q", lazy("./views/jurisprudence.js", "jurisprudenceView"));
register("/jurisprudence/q/:q/page/:page", lazy("./views/jurisprudence.js", "jurisprudenceView"));
register("/jurisprudence/page/:page", lazy("./views/jurisprudence.js", "jurisprudenceView"));
register("/jurisprudence/:id", lazy("./views/jurisprudence.js", "jurisprudenceDetailView"));

register("/procedures", lazy("./views/procedures.js", "proceduresView"));
register("/procedures/:slug", lazy("./views/procedures.js", "procedureDetailView"));
register("/professionals", lazy("./views/professionals.js", "professionalsView"));
register("/professionals/q/:q", lazy("./views/professionals.js", "professionalsView"));
register("/professionals/me", lazy("./views/professionals.js", "myProfessionalView"), { auth: true });
register("/professionals/:id", lazy("./views/professionals.js", "professionalDetailView"));

register("/comparative", lazy("./views/comparative.js", "comparativeView"));
register("/comparative/new", lazy("./views/comparative.js", "comparativeNewView"));
register("/comparative/study/:id", lazy("./views/comparative.js", "comparativeDetailView"));
register("/comparative/jurisdiction/:slug", lazy("./views/comparative.js", "jurisdictionView"));
register("/comparative/jurisdiction/:slug/:tab", lazy("./views/comparative.js", "jurisdictionView"));
register("/comparative/:id", lazy("./views/comparative.js", "comparativeDetailView"));

register("/research", lazy("./views/research.js", "researchView"));
register("/research/category/:category", lazy("./views/research.js", "researchView"));
register("/research/type/:type", lazy("./views/research.js", "researchView"));
register("/research/:id", lazy("./views/research.js", "researchBookView"));

register("/documents", lazy("./views/documents.js", "documentsView"));
register("/documents/:slug", lazy("./views/documents.js", "documentDetailView"));
register("/my-documents", lazy("./views/documents.js", "myDocumentsView"), { auth: true });

register("/legal-french", lazy("./views/legal_french.js", "legalFrenchView"));
register("/legal-french/treaties", lazy("./views/legal_french.js", "legalFrenchTreatiesView"));
register("/legal-french/treaty/:id", lazy("./views/legal_french.js", "legalFrenchTreatyDetailView"));
register("/legal-french/lesson/:id", lazy("./views/legal_french.js", "legalFrenchLessonView"));
register("/legal-french/quiz/:lessonId", lazy("./views/legal_french.js", "legalFrenchQuizView"), { auth: true });
register("/legal-french/:id", lazy("./views/legal_french.js", "legalFrenchLevelView"));

register("/assistant", lazy("./views/assistant.js", "assistantView"), { auth: true });

register("/community", lazy("./views/community.js", "communityView"));
register("/community/new", lazy("./views/community.js", "communityNewView"), { auth: true });
register("/community/:id", lazy("./views/community.js", "communityDetailView"));

register("/calculators", lazy("./views/calculators.js", "calculatorsView"));
register("/calculators/:slug", lazy("./views/calculators.js", "calculatorView"));

register("/notifications", lazy("./views/notifications.js", "notificationsView"), { auth: true });
register("/notifications/settings", lazy("./views/notifications.js", "notificationsSettingsView"), { auth: true });
register("/profile", lazy("./views/profile.js", "profileView"), { auth: true });

register("/billing", lazy("./views/billing.js", "billingView"), { auth: true });
register("/billing/orders", lazy("./views/billing.js", "myOrdersView"), { auth: true });

register("/blog", lazy("./views/blog.js", "blogView"));
register("/blog/my", lazy("./views/blog.js", "myArticlesView"), { auth: true });
register("/blog/new", lazy("./views/blog.js", "blogEditorView"), { auth: true });
register("/blog/edit/:id", lazy("./views/blog.js", "blogEditorView"), { auth: true });
register("/blog/:id", lazy("./views/blog.js", "blogDetailView"));

register("/admin", () => { location.href = "/admin"; }, { auth: true, admin: true });

register("/privacy", lazy("./views/legal.js", "privacyView"));
register("/terms", lazy("./views/legal.js", "termsView"));
register("/cookie-policy", lazy("./views/legal.js", "cookiePolicyView"));
register("/disclaimer", lazy("./views/legal.js", "disclaimerView"));
register("/guide", lazy("./views/legal.js", "guideView"));

// ---------- مسارات مكتبة/مدونة متعددة الأجزاء ----------
function regMulti(base, mod, fn, opts = {}) {
  const combos = [
    "/cat/:category", "/q/:q", "/cat/:category/q/:q",
    "/page/:page", "/cat/:category/page/:page", "/q/:q/page/:page",
    "/cat/:category/q/:q/page/:page",
  ];
  for (const c of combos) register(base + c, lazy(mod, fn), opts);
}
regMulti("/library", "./views/library.js", "libraryView");
regMulti("/blog", "./views/blog.js", "blogView");

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
preloadFr().catch(() => {});  // خلفية — чтобы переводы FR были готовы мгновенно при переключении
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

// شريط موافقة ملفات تعريف الارتباط (القانون 09-08) — متأخر عن الإقلاع
requestAnimationFrame(() => {
  import("./components/cookie-consent.js").then(({ initCookieConsent, onCookieConsent, hasCookieConsent }) => {
    initCookieConsent();
    import("./components/download-app.js").then(({ initDownloadAppButton }) => {
      onCookieConsent(() => initDownloadAppButton());
      if (hasCookieConsent()) initDownloadAppButton();
    });
  });
});

// تهيئة الإعلانات بعد كل تغيير مسار
import { setAfterRender } from "./router.js";
import { initAdSlots, resetAdObserver } from "./components/ads.js";
setAfterRender(() => {
  resetAdObserver();
  setTimeout(initAdSlots, 100);
});

setInterval(() => { if (session.token) refreshNotifBadge(); }, 60000);

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js").catch(() => {});
}

window.addEventListener("DOMContentLoaded", () => {
  document.getElementById("year").textContent = new Date().getFullYear();
});
