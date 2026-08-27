// نبراس — زر تحميل/تثبيت التطبيق (PWA) — قبلinstallprompt + تعليمات iOS
import { currentLang } from "../i18n.js";
import { el } from "../ui.js";

const STORAGE_KEY = "nibras_pwa_prompt";
let deferredPrompt = null;

function storedVal() {
  try { return localStorage.getItem(STORAGE_KEY); } catch { return null; }
}
function setStoredVal(v) {
  try { localStorage.setItem(STORAGE_KEY, v); } catch { /* ok */ }
}

function isStandalone() {
  return window.matchMedia("(display-mode: standalone)").matches
    || window.navigator.standalone === true;
}

const isIOS = () => /iPhone|iPad|iPod/.test(navigator.userAgent) && !window.MSStream;

function isMobile() {
  return /Android|iPhone|iPad|iPod|Mobile/.test(navigator.userAgent);
}

function dismiss() {
  setStoredVal("dismissed");
  const btn = document.getElementById("download-app-btn");
  if (btn) {
    btn.style.opacity = "0";
    btn.style.transform = "translateY(20px) scale(0.9)";
    setTimeout(() => btn.remove(), 300);
  }
  const sheet = document.getElementById("pwa-install-sheet");
  if (sheet) closeSheet();
}

function runInstall() {
  if (deferredPrompt) {
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then((choice) => {
      if (choice.outcome === "accepted") {
        setStoredVal("installed");
        dismiss();
      }
      deferredPrompt = null;
    });
    return;
  }
  if (isIOS()) showIOSSheet();
  else showIOSSheet(); // fallback: instructions
}

/* ---------- ورقة تعليمات iOS (أو عامة) ---------- */
let sheetRemoved = false;
function closeSheet() {
  const sheet = document.getElementById("pwa-install-sheet");
  const veil = document.getElementById("pwa-install-veil");
  const remove = () => { sheet && sheet.remove(); veil && veil.remove(); };
  if (sheet) sheet.style.transform = "translateY(105%)";
  if (veil) veil.style.opacity = "0";
  setTimeout(remove, 250);
}

function showIOSSheet() {
  if (document.getElementById("pwa-install-sheet")) return;
  sheetRemoved = false;

  const fr = currentLang() === "fr";

  const veil = el("div", {
    id: "pwa-install-veil",
    class: "pwa-veil",
    onclick: closeSheet,
  });

  const sheet = el("div", { id: "pwa-install-sheet", class: "pwa-sheet" }, [
    el("div", { class: "pwa-sheet-head" }, [
      el("img", { src: "/icons/apple-touch-icon.png", alt: "نبراس", class: "pwa-sheet-icon" }),
      el("div", { class: "pwa-sheet-title", text: fr ? "Installer l'application Nibras" : "تثبيت تطبيق نبراس" }),
      el("button", { class: "pwa-sheet-close", onclick: () => { setStoredVal("dismissed"); closeSheet(); } }, ["✕"]),
    ]),
    el("ol", { class: "pwa-sheet-steps" }, [
      el("li", {}, [
        el("strong", { text: fr ? "Appuyez sur le bouton Partager" : "اضغط على زر المشاركة" }),
        el("span", { class: "pwa-sheet-hint", text: fr ? "dans Safari (en bas de l'écran)" : "في سفاري Safari (أسفل الشاشة)" }),
      ]),
      el("li", {}, [
        el("strong", { text: fr ? "Appuyez sur « Ajouter à l'écran d'accueil »" : "اضغط على «إضافة إلى الشاشة الرئيسية»" }),
      ]),
      el("li", {}, [
        el("strong", { text: fr ? "Appuyez sur « Ajouter »" : "اضغط على «إضافة»" }),
        el("span", { class: "pwa-sheet-hint", text: fr ? "Puis retrouvez Nibras sur votre écran d'accueil" : "ثم ستفقد تطبيق نبراس على شاشتك الرئيسية" }),
      ]),
    ]),
    el("button", { class: "btn btn-primary pwa-sheet-btn", onclick: closeSheet }, [fr ? "Compris" : "فهمت"]),
  ]);

  document.body.append(veil, sheet);
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      sheet.style.transform = "translateY(0)";
      veil.style.opacity = "1";
    });
  });
}

/* ---------- زر عائم ---------- */
function showButton(installLabel) {
  if (document.getElementById("download-app-btn") || storedVal() === "dismissed") return;

  const fr = currentLang() === "fr";

  const dlIcon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  dlIcon.setAttribute("viewBox", "0 0 24 24");
  dlIcon.setAttribute("width", "18");
  dlIcon.setAttribute("height", "18");
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
    onclick: runInstall,
  }, [
    el("span", { class: "download-app-icon" }, [dlIcon]),
    el("span", { class: "download-app-text", text: installLabel || (fr ? "Installer l'app" : "تثبيت التطبيق") }),
    el("button", {
      class: "download-app-close",
      title: fr ? "Fermer" : "إغلاق",
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

/* ---------- التهيئة المبكرة: التقاط حدث التثبيت بأسرع وقت ممكن ---------- */
export function initDownloadAppButton() {
  if (isStandalone()) return;              // مثبّت بالفعل → لا نعرض شيئاً
  if (storedVal() === "installed") return; // ثبّته سابقاً
  if (storedVal() === "dismissed") return; // أغلقه سابقاً → احترام اختياره

  const fr = currentLang() === "fr";

  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferredPrompt = e;
    if (!document.getElementById("download-app-btn")) {
      showButton(fr ? "Installer l'app" : "تثبيت التطبيق");
    }
  });

  window.addEventListener("appinstalled", () => {
    setStoredVal("installed");
    dismiss();
  });

  // iOS : لا يوجد beforeinstallprompt → دليل الإضافة إلى الشاشة الرئيسية
  if (isIOS() || (isMobile() && !window.chrome)) {
    setTimeout(() => {
      if (document.getElementById("download-app-btn")) return;
      showButton(fr ? "Installer l'app" : "تثبيت التطبيق");
    }, 2500);
  }

  // وقع الحدث قبل اكتمال تحميل الوحدة (شبكة بطيئة) → أظهر فوراً
  if (deferredPrompt) showButton(fr ? "Installer l'app" : "تثبيت التطبيق");
}

// لا ننتظر موافقة الكوكيز ولا نفوّت الحدث — نبدأ فور تحميل الوحدة
initDownloadAppButton();