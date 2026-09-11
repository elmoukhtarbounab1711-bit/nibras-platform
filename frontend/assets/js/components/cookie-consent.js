// نبراس — شريط موافقة ملفات تعريف الارتباط + إدارة التفضيلات (Law 09-08 + EU User Consent Policy)
import { currentLang } from "../i18n.js";
import { el } from "../ui.js";

const STORAGE_KEY = "nibras_cookie_consent";
const EVENT_NAME = "nibras:cookie-consent-change";
let _onConsentCallback = null;

/* ── helpers ── */

function getConsent() {
  try { const v = localStorage.getItem(STORAGE_KEY); return v ? JSON.parse(v) : null; }
  catch { return null; }
}

function saveConsent(consent) {
  consent.necessary = true;               // لا يمكن إلغاء الضرورية
  consent.timestamp = Date.now();
  localStorage.setItem(STORAGE_KEY, JSON.stringify(consent));
  window.dispatchEvent(new CustomEvent(EVENT_NAME, { detail: consent }));
  if (_onConsentCallback) _onConsentCallback(consent);
}

function consentFromAll(on) {
  return { necessary: true, functional: on, analytics: on, advertising: on };
}

/* ── public API ── */

export function onCookieConsent(fn) { _onConsentCallback = fn; }

export function hasCookieConsent() {
  const c = getConsent(); return c && c.necessary === true;
}

export function hasAdvertisingConsent() {
  const c = getConsent(); return !!(c && c.advertising);
}

export function getCurrentConsent() { return getConsent(); }

export function initCookieConsent() {
  if (hasCookieConsent()) return;           // اختار المستخدم مسبقًا

  const isFr = currentLang() === "fr";
  const banner = el("div", { id: "cookie-consent-banner", class: "cookie-banner" }, [
    el("div", { class: "cookie-banner-inner" }, [
      el("div", { class: "cookie-banner-text" }, [
        el("div", { class: "cookie-banner-icon" }, [el("span", { text: "🍪" })]),
        el("div", {}, [
          el("h3", { text: isFr ? "Nous utilisons des cookies" : "نستخدم ملفات تعريف الارتباط" }),
          el("p", { class: "small muted", text: isFr
            ? "Nous utilisons des cookies pour assurer le bon fonctionnement et améliorer votre expérience. Conformément à la Loi 09-08, nous sollicitons votre consentement."
            : "نستخدم ملفات تعريف الارتباط لضمان عمل المنصة وتحسين تجربتك. وفقاً للقانون 09-08، نطلب موافقتك. يمكنك رفض الإعلانات والتحليلات." }),
        ]),
      ]),
      el("div", { class: "cookie-banner-actions" }, [
        el("button", { class: "btn btn-ghost btn-sm", text: isFr ? "Gérer" : "إدارة",
          onclick: () => { removeBanner(); openManager(); } }),
        el("button", { class: "btn btn-ghost btn-sm", text: isFr ? "Refuser" : "رفض",
          onclick: () => { saveConsent(consentFromAll(false)); removeBanner(); } }),
        el("button", { class: "btn btn-primary btn-sm", text: isFr ? "Accepter tous" : "قبول الكل",
          onclick: () => { saveConsent(consentFromAll(true));  removeBanner(); } }),
      ]),
    ]),
  ]);
  document.body.append(banner);
  requestAnimationFrame(() => banner.classList.add("show"));
}

export function showCookieManager() {
  const existing = document.getElementById("cookie-prefs-backdrop");
  if (existing) existing.remove();
  openManager();
}

/* ── internals ── */

function removeBanner() {
  const b = document.getElementById("cookie-consent-banner");
  if (!b) return;
  b.classList.remove("show");
  setTimeout(() => b.remove(), 300);
}

function openManager() {
  const isFr = currentLang() === "fr";
  const current = getConsent() || consentFromAll(false);

  function toggle(key, disabled) {
    const wrap = el("label", { class: "cookie-toggle", style: "display:flex;align-items:center;gap:8px;" });
    const cb = el("input", { type: "checkbox", checked: current[key] === true });
    if (disabled) { cb.disabled = true; cb.checked = true; }
    cb.style.position = "absolute";
    cb.style.opacity = "0";
    cb.style.pointerEvents = "none";
    const track = el("span", { class: "cookie-toggle-track", style: "width:40px;height:22px;border-radius:11px;background:#ccc;position:relative;display:inline-block;cursor:" + (disabled ? "not-allowed" : "pointer"), tabindex: "0", role: "switch" });
    const thumb = el("span", { style: "width:18px;height:18px;border-radius:50%;background:#fff;position:absolute;top:2px;left:2px;transition:transform .15s" });
    if (current[key]) track.style.background = "#1f3a93";
    track.style.position = "relative";
    function sync() { thumb.style.transform = cb.checked ? "translateX(18px)" : "none"; track.style.background = cb.checked ? "#1f3a93" : "#ccc"; }
    sync();
    cb.addEventListener("change", () => { sync(); });
    if (!disabled) { track.addEventListener("click", () => { cb.checked = !cb.checked; sync(); }); track.addEventListener("keydown", e => { if (e.key === " " || e.key === "Enter") { e.preventDefault(); cb.checked = !cb.checked; sync(); } }); }
    wrap.append(cb, track);
    return wrap;
  }

  function row(label, key, disabled) {
    const desc = {
      necessary: isFr ? "Nécessaires au fonctionnement (authentification, session, thème, langue)." : "ضرورية للتشغيل (المصادقة، الجلسة، السمة، اللغة).",
      functional: isFr ? "Mémorisation des préférences d'affichage et de navigation." : "تذكّر تفضيلات العرض والتنقل.",
      analytics: isFr ? "Mesure d'audience pour améliorer le service." : "قياس الجمهور لتحسين الخدمة.",
      advertising: isFr ? "Cookies publicitaires (Google AdSense) — refus = aucune publicité ciblée." : "ملفات إعلانية (Google AdSense) — الرفض = لا إعلانات مخصصة.",
    }[key];
    return el("div", { style: "display:flex;justify-content:space-between;align-items:center;padding:12px 0;border-bottom:1px solid var(--border);gap:12px;" }, [
      el("div", { style: "flex:1" }, [
        el("div", { style: "font-weight:600", text: label }),
        el("div", { class: "small muted", text: desc }),
      ]),
      toggle(key, disabled),
    ]);
  }

  const backdrop = el("div", { id: "cookie-prefs-backdrop", class: "modal-backdrop", style: "z-index:9999" });
  const modal = el("div", { class: "modal", role: "dialog", "aria-modal": "true", style: "max-width:520px;width:95%;margin:10vh auto;" }, [
    el("h3", { text: isFr ? "Préférences de cookies" : "تفضيلات ملفات تعريف الارتباط" }),
    el("p", { class: "small muted", text: isFr ? "Gérez vos préférences ci-dessous. Les cookies strictement nécessaires ne peuvent pas être désactivés." : "حدد تفضيلاتك أدناه. الملفات الضرورية لا يمكن تعطيلها." }),
    row(isFr ? "Nécessaires" : "الضرورية", "necessary", true),
    row(isFr ? "Fonctionnalité" : "وظيفية", "functional", false),
    row(isFr ? "Analytiques" : "تحليلية", "analytics", false),
    row(isFr ? "Publicitaires (AdSense)" : "إعلانية (AdSense)", "advertising", false),
    el("div", { class: "small muted", style: "margin-top:12px" }, [
      el("div", { text: isFr ? "Pour en savoir plus sur l'utilisation des données par Google :" : "لمعرفة المزيد حول استخدام Google للبيانات:" }),
      el("a", { href: "https://policies.google.com/technologies/partner-sites", target: "_blank", rel: "noopener", text: isFr ? "Comment Google utilise les données" : "كيف تستخدم Google البيانات" }),
    ]),
    el("div", { class: "small muted", style: "margin-top:6px" }, [
      el("div", { text: isFr ? "Désactiver la publicité personnalisée :" : "تعطيل الإعلانات المخصصة:" }),
      el("a", { href: "https://adssettings.google.com/", target: "_blank", rel: "noopener", text: "Google Ads Settings" }),
      el("span", { text: " • " }),
      el("a", { href: "https://optout.aboutads.info/", target: "_blank", rel: "noopener", text: "Digital Advertising Alliance" }),
      el("span", { text: " • " }),
      el("a", { href: "https://www.youronlinechoices.com/", target: "_blank", rel: "noopener", text: "YourOnlineChoices" }),
    ]),
    el("div", { style: "display:flex;gap:8px;margin-top:18px;justify-content:flex-end" }, [
      el("button", { class: "btn btn-ghost btn-sm", text: isFr ? "Refuser tout" : "رفض الكل", onclick: () => { saveConsent(consentFromAll(false)); backdrop.remove(); } }),
      el("button", { class: "btn btn-primary btn-sm", text: isFr ? "Enregistrer" : "حفظ التفضيلات", onclick: () => {
        const vals = {};
        backdrop.querySelectorAll("input[type=checkbox]").forEach((cb, i) => {
          const keys = ["necessary","functional","analytics","advertising"];
          vals[keys[i]] = cb.checked;
        });
        vals.necessary = true;
        saveConsent(vals);
        backdrop.remove();
      }}),
    ]),
  ]);

  backdrop.addEventListener("click", (e) => { if (e.target === backdrop) backdrop.remove(); });
  backdrop.append(modal);
  document.body.append(backdrop);
  modal.querySelector("input[type=checkbox]")?.focus();
}
