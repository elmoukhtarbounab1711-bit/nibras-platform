// نبراس — زر تحميل التطبيق (PWA) — يظهر بعد موافقة الكوكيز
import { currentLang } from "../i18n.js";
import { el } from "../ui.js";

const STORAGE_KEY = "nibras_download_dismissed";

function isDismissed() {
  try { return localStorage.getItem(STORAGE_KEY) === "1"; }
  catch { return false; }
}

function dismiss() {
  try { localStorage.setItem(STORAGE_KEY, "1"); }
  catch { /* ok */ }
  const btn = document.getElementById("download-app-btn");
  if (btn) {
    btn.style.opacity = "0";
    btn.style.transform = "translateY(20px) scale(0.9)";
    setTimeout(() => btn.remove(), 300);
  }
}

function installPWA() {
  if (window._deferredInstallPrompt) {
    window._deferredInstallPrompt.prompt();
    window._deferredInstallPrompt.userChoice.then((choice) => {
      if (choice.outcome === "accepted") dismiss();
      window._deferredInstallPrompt = null;
    });
  } else {
    const isFr = currentLang() === "fr";
    alert(isFr
      ? "Pour installer, utilisez le menu du navigateur > Ajouter a l'ecran d'accueil."
      : "لتنزيل التطبيق، استخدم قائمة المتصفح > إضافة إلى الشاشة الرئيسية."
    );
  }
}

function showButton() {
  if (document.getElementById("download-app-btn") || isDismissed()) return;

  const isFr = currentLang() === "fr";

  const dlIcon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  dlIcon.setAttribute("viewBox", "0 0 24 24");
  dlIcon.setAttribute("width", "20");
  dlIcon.setAttribute("height", "20");
  dlIcon.setAttribute("fill", "none");
  dlIcon.setAttribute("stroke", "currentColor");
  dlIcon.setAttribute("stroke-width", "2");
  dlIcon.setAttribute("stroke-linecap", "round");
  dlIcon.setAttribute("stroke-linejoin", "round");
  dlIcon.innerHTML = '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>';

  const closeIcon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  closeIcon.setAttribute("viewBox", "0 0 24 24");
  closeIcon.setAttribute("width", "14");
  closeIcon.setAttribute("height", "14");
  closeIcon.setAttribute("fill", "none");
  closeIcon.setAttribute("stroke", "currentColor");
  closeIcon.setAttribute("stroke-width", "2.5");
  closeIcon.setAttribute("stroke-linecap", "round");
  closeIcon.innerHTML = '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>';

  const btn = el("button", {
    id: "download-app-btn",
    class: "download-app-btn",
    onclick: installPWA,
  }, [
    el("span", { class: "download-app-icon" }, [dlIcon]),
    el("span", { class: "download-app-text", text: isFr ? "Télécharger l'app" : "تنزيل التطبيق" }),
    el("button", {
      class: "download-app-close",
      title: isFr ? "Fermer" : "إغلاق",
      onclick: (e) => { e.stopPropagation(); dismiss(); },
    }, [closeIcon]),
  ]);

  document.body.append(btn);
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      btn.style.opacity = "1";
      btn.style.transform = "translateY(0) scale(1)";
    });
  });
}

export function initDownloadAppButton() {
  if (isDismissed()) return;

  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    window._deferredInstallPrompt = e;
    showButton();
  });

  setTimeout(() => {
    if (document.getElementById("download-app-btn")) return;
    showButton();
  }, 2000);
}
