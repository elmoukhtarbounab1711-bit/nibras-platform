// نبراس — موجّه SPA قائم على hash مع حراسة الصلاحيات
import { tr } from "./i18n.js";
import { el, toast, skeleton } from "./ui.js";
import { icon } from "./icons.js";
import { session } from "./api.js";

const routes = [];
let notFound = null;
let afterRender = null;
let transitioning = false;

export function register(path, handler, { auth = false, admin = false } = {}) {
  const parts = path.split("/").filter(Boolean).map((p) =>
    p.startsWith(":") ? { param: p.slice(1) } : { literal: p });
  routes.push({ parts, handler, auth, admin });
}

export function setNotFound(h) { notFound = h; }
export function setAfterRender(h) { afterRender = h; }

// المسار الحقيقي الحالي (pathname) إن كان يعبّر عن مسار تطبيق معروف، وإلا يعود للـ hash.
function hashPath() {
  return decodeURIComponent((window.location.hash || "#/home").replace(/^#/, "") || "/home");
}

export function navigate(path) {
  const p = path.startsWith("#") ? path.slice(1) : path;
  const normalized = (p.startsWith("/") ? p : "/" + p) || "/home";
  if (window.location.pathname === normalized && window.location.hash === "") {
    render();
    return;
  }
  // التوجيه عبر الروابط الحقيقية (History API) مع توحيد canonical للروابط القديمة.
  window.history.pushState({}, "", normalized);
  render();
}

export function matchHash(hash) {
  let path = decodeURIComponent((hash || "#/home").replace(/^#/, "") || "/home");
  if (!path || path === "/") path = "/home";
  path = path.split("?")[0];
  const segments = path.split("/").filter(Boolean);
  for (const route of routes) {
    const params = {};
    if (route.parts.length !== segments.length) continue;
    let ok = true;
    for (let i = 0; i < route.parts.length; i++) {
      const rp = route.parts[i];
      if (rp.param) params[rp.param] = decodeURIComponent(segments[i]);
      else if (rp.literal !== segments[i]) { ok = false; break; }
    }
    if (ok) return { route, params };
  }
  return { route: { handler: notFound }, params: {} };
}

// يحددُ المسار الحالي:
//  - إذا وُجد hash (#/...) فهو الوجهة الصريحة الأخيرة للمستخدم (روابط قديمة #/...)
//    وتُنقَّل إلى روابط حقيقية عبر pushState.
//  - وإلا يفضّل pathname (روابط حقيقية /laws/:id …) ثم يعود للمنزل.
export function matchCurrent() {
  if (window.location.hash && window.location.hash.length > 0) {
    const m = matchHash(window.location.hash);
    // نقل الروابط القديمة #/... إلى روابط حقيقية قابلة للفهرسة
    if (m.route.handler && m.route.handler !== notFound && window.location.pathname.replace(/^\/+/, "") === "") {
      const target = (window.location.hash || "#/home").replace(/^#/, "");
      try {
        window.history.replaceState({}, "", (target || "/home"));
      } catch (_e) { /* تجاهل */ }
    }
    return m;
  }
  const pathname = window.location.pathname.replace(/^\/+/, "");
  if (pathname && pathname !== "index.html") {
    const m = matchHash("/" + pathname);
    if (m.route && m.route.handler && m.route.handler !== notFound) {
      return m;
    }
  }
  return matchHash("/home");
}

function prefersReducedMotion() {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

async function withTransition(view, fn) {
  if (prefersReducedMotion() || !document.startViewTransition) {
    return fn();
  }
  transitioning = true;
  try {
    await document.startViewTransition(fn).finished;
  } finally {
    transitioning = false;
  }
}

function showSkeleton(view) {
  view.replaceChildren(skeleton(4, 80));
}

export function render() {
  const { route, params } = matchCurrent();
  const view = document.getElementById("view");

  if (route.admin && !session.isAdmin) {
    if (session.token) {
      view.replaceChildren(el("div", { class: "card empty", text: tr("forbidden") }));
      return;
    }
    session.clear();
    toast(tr("unauthorized"), "warn");
    navigate("/login");
    return;
  }
  if (route.auth && !session.token) {
    toast(tr("unauthorized"), "warn");
    navigate("/home");
    document.dispatchEvent(new CustomEvent("nibras:need-auth"));
    return;
  }

  // تحديد القسم النشط من المسار الحالي (pathname أو hash)
  let rawPath;
  if (window.location.hash && window.location.hash.length > 0) {
    rawPath = decodeURIComponent((location.hash || "#/home").replace(/^#/, "") || "/home");
  } else {
    const pathname = window.location.pathname.replace(/^\/+/, "");
    if (pathname && pathname !== "index.html") {
      rawPath = "/" + pathname;
    } else {
      rawPath = decodeURIComponent((location.hash || "#/home").replace(/^#/, "") || "/home");
    }
  }
  const base = rawPath.split("/").filter(Boolean)[0] || "home";
  document.querySelectorAll("[data-route]").forEach((a) => {
    const r = a.dataset.route === "home" ? "home" : a.dataset.route;
    a.classList.toggle("active", base === r);
  });

  const start = performance.now();
  
  // Show skeleton immediately for perceived performance
  showSkeleton(view);

  Promise.resolve(route.handler(params)).then(async (html) => {
    await withTransition(view, () => {
      if (typeof html === "string") view.innerHTML = html;
      else if (html instanceof Node) { view.replaceChildren(html); }
      else view.innerHTML = "";
      view.scrollTop = 0;
      window.scrollTo({ top: 0, behavior: "instant" });
    });
    if (afterRender) afterRender(route, params, performance.now() - start);
  }).catch((err) => {
    console.error(err);
    view.replaceChildren(el("div", { class: "card empty" }, [
      el("div", { class: "empty-icon" }, [icon("alertTriangle", 40)]),
      el("div", { text: tr("error") }),
      el("div", { class: "small muted", text: err.message }),
    ]));
  });
}

export function initRouter() {
  window.addEventListener("hashchange", render);
  window.addEventListener("popstate", render);
}
