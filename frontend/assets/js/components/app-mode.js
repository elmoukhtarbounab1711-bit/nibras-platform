// نبراس — وضع التطبيق المثبّت (PWA App Mode)
// عند فتح نبراس كتطبيق مثبّت (standalone): تفعيل رأس مدمج + شريط سفلي.
function isStandalone() {
  return window.matchMedia("(display-mode: standalone)").matches
    || window.navigator.standalone === true;
}

const IMMERSIVE_ROUTES = ["pdf"];

export function initAppMode() {
  const apply = () => {
    document.documentElement.classList.toggle("app-mode", isStandalone());
  };
  apply();
  try {
    const mq = window.matchMedia("(display-mode: standalone)");
    if (mq.addEventListener) mq.addEventListener("change", apply);
    else if (mq.addListener) mq.addListener(apply);
  } catch { /* ok */ }
}

// يُستدعى بعد كل ترسيم مسار — يخفي الرأس والشريط في الشاشات الكاملة (PDF)
export function updateAppMode() {
  const hash = (location.hash || "#/home").replace(/^#/, "") || "/home";
  const base = hash.split("/").filter(Boolean)[0] || "home";
  document.documentElement.classList.toggle("immersive", IMMERSIVE_ROUTES.includes(base));
}