// نبراس — مكوّن الإعلانات مع التحميل الكسول (Security §7)
import { session } from "../api.js";
import { el } from "../ui.js";

const AD_SLOTS_CACHE = new Map();
const LOADED_SCRIPTS = new Set();
const OBSERVED_SLOTS = new Set();
let intersectionObserver = null;

const APPROVED_DOMAINS = [
  "profitableratecpmnetwork.com",
  "highrevenueformat.com",
  "adsterra.com",
  "monetag.com",
  "propellerads.com",
  "media.net",
  "amazon-adsystem.com",
  "googleadservices.com",
  "googlesyndication.com",
  "doubleclick.net",
  "adroll.com",
  "outbrain.com",
  "taboola.com",
  "criteo.com",
  "pubmatic.com",
  "openx.com",
  "indexww.com",
  "spotxchange.com",
];

function isApprovedDomain(url) {
  try {
    const hostname = new URL(url).hostname.toLowerCase();
    return APPROVED_DOMAINS.some(
      (d) => hostname === d || hostname.endsWith("." + d)
    );
  } catch {
    return false;
  }
}

function sanitizeScript(html) {
  const stripped = html
    .replace(/<script\b[^>]*>/gi, "")
    .replace(/<\/script>/gi, "")
    .replace(/on\w+\s*=\s*["'][^"']*["']/gi, "")
    .replace(/javascript\s*:/gi, "");
  return stripped;
}

function injectScript(scriptEl) {
  const src = scriptEl.getAttribute("src");
  if (src && LOADED_SCRIPTS.has(src)) return;
  if (src) LOADED_SCRIPTS.add(src);

  const clone = document.createElement("script");
  for (const attr of scriptEl.attributes) {
    if (attr.name === "src") {
      if (!isApprovedDomain(attr.value)) return;
      clone.src = attr.value;
    } else {
      clone.setAttribute(attr.name, attr.value);
    }
  }
  if (scriptEl.textContent) {
    clone.textContent = scriptEl.textContent;
  }
  scriptEl.replaceWith(clone);
}

async function fetchSlotProviders(slotSlug) {
  if (AD_SLOTS_CACHE.has(slotSlug)) {
    return AD_SLOTS_CACHE.get(slotSlug);
  }

  try {
    const resp = await fetch(`/api/ads/slot/${encodeURIComponent(slotSlug)}`, {
      headers: session.token ? { Authorization: `Bearer ${session.token}` } : {},
    });
    if (!resp.ok) return [];
    const data = await resp.json();
    if (!data.enabled) return [];
    const providers = data.providers || [];
    AD_SLOTS_CACHE.set(slotSlug, providers);
    return providers;
  } catch {
    return [];
  }
}

function createAdSlotNode(slotSlug, providers) {
  if (!providers || providers.length === 0) return null;

  const wrapper = el("div", {
    class: "nibras-ad-slot",
    "data-slot": slotSlug,
    "aria-label": "إعلان",
  });

  for (const provider of providers) {
    const raw = provider.script_html || "";
    if (!raw) continue;

    const cleaned = sanitizeScript(raw);
    const temp = document.createElement("div");
    temp.innerHTML = cleaned;
    const scripts = temp.querySelectorAll("script");
    if (scripts.length > 0) {
      for (const s of scripts) {
        const clone = document.createElement("script");
        for (const attr of s.attributes) {
          if (attr.name === "src") {
            if (isApprovedDomain(attr.value)) clone.src = attr.value;
          } else {
            clone.setAttribute(attr.name, attr.value);
          }
        }
        if (s.textContent) clone.textContent = s.textContent;
        wrapper.appendChild(clone);
      }
    } else {
      wrapper.innerHTML = cleaned;
    }
    break;
  }

  return wrapper;
}

async function loadSlot(slotElement) {
  const slug = slotElement.dataset.slot;
  if (!slug || slotElement.dataset.loaded) return;

  slotElement.dataset.loaded = "true";
  const providers = await fetchSlotProviders(slug);
  if (providers.length === 0) {
    slotElement.remove();
    return;
  }

  const node = createAdSlotNode(slug, providers);
  if (node) {
    slotElement.replaceWith(node);
  }
}

function getObserver() {
  if (intersectionObserver) return intersectionObserver;

  intersectionObserver = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          loadSlot(entry.target);
          intersectionObserver.unobserve(entry.target);
        }
      }
    },
    { rootMargin: "200px 0px", threshold: 0 }
  );

  return intersectionObserver;
}

export function initAdSlots() {
  const slots = document.querySelectorAll(".nibras-ad-slot:not([data-loaded])");
  if (!slots.length) return;

  const observer = getObserver();
  for (const slot of slots) {
    if (!OBSERVED_SLOTS.has(slot)) {
      OBSERVED_SLOTS.add(slot);
      observer.observe(slot);
    }
  }
}

export function createAdPlaceholder(slotSlug) {
  return el("div", {
    class: "nibras-ad-slot",
    "data-slot": slotSlug,
  });
}

export function clearAdCache() {
  AD_SLOTS_CACHE.clear();
  LOADED_SCRIPTS.clear();
}
