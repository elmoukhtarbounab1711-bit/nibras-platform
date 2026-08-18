// نبراس — شريط موافقة ملفات تعريف الارتباط (Law 09-08)
import { tr, currentLang } from "../i18n.js";
import { el } from "../ui.js";
import { navigate } from "../router.js";

const STORAGE_KEY = "nibras_cookie_consent";
let _onConsentCallback = null;

export function onCookieConsent(fn) {
  _onConsentCallback = fn;
}

function getConsent() {
  try {
    const v = localStorage.getItem(STORAGE_KEY);
    return v ? JSON.parse(v) : null;
  } catch { return null; }
}

function saveConsent(consent) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(consent));
  if (_onConsentCallback) _onConsentCallback(consent);
}

export function hasCookieConsent() {
  const c = getConsent();
  return c && c.necessary && c.functional;
}

export function initCookieConsent() {
  if (hasCookieConsent()) return;

  const isFr = currentLang() === "fr";

  const banner = el("div", {
    id: "cookie-consent-banner",
    class: "cookie-banner",
  }, [
    el("div", { class: "cookie-banner-inner" }, [
      el("div", { class: "cookie-banner-text" }, [
        el("div", { class: "cookie-banner-icon" }, [
          el("span", { text: "🍪" }),
        ]),
        el("div", {}, [
          el("h3", { text: isFr ? "Nous utilisons des cookies" : "نستخدم ملفات تعريف الارتباط" }),
          el("p", { class: "small muted", text: isFr
            ? "Nous utilisons des cookies pour assurer le bon fonctionnement de la Plateforme et améliorer votre expérience. Conformément à la Loi 09-08, nous sollicitons votre consentement."
            : "نستخدم ملفات تعريف الارتباط لضمان عمل المنصة بشكل صحيح وتحسين تجربتك. وفقاً للقانون 09-08، نطلب موافقتك."
          }),
        ]),
      ]),
      el("div", { class: "cookie-banner-actions" }, [
        el("button", {
          class: "btn btn-ghost btn-sm",
          text: isFr ? "Gérer" : "إدارة",
          onclick: () => {
            removeBanner();
            navigate("/cookie-policy");
          },
        }),
        el("button", {
          class: "btn btn-ghost btn-sm",
          text: isFr ? "Refuser" : "رفض",
          onclick: () => {
            saveConsent({ necessary: true, functional: false, analytics: false, advertising: false, timestamp: Date.now() });
            removeBanner();
          },
        }),
        el("button", {
          class: "btn btn-primary btn-sm",
          text: isFr ? "Accepter tous" : "قبول الكل",
          onclick: () => {
            saveConsent({ necessary: true, functional: true, analytics: true, advertising: true, timestamp: Date.now() });
            removeBanner();
          },
        }),
      ]),
    ]),
  ]);

  document.body.append(banner);
  requestAnimationFrame(() => banner.classList.add("show"));
}

function removeBanner() {
  const b = document.getElementById("cookie-consent-banner");
  if (b) {
    b.classList.remove("show");
    setTimeout(() => b.remove(), 300);
  }
}
