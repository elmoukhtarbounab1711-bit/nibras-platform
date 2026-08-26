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
  "pagead2.googlesyndication.com",
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

async function fetchSlotProviders(slotSlug) {
  try {
    const resp = await fetch(`/api/ads/slot/${encodeURIComponent(slotSlug)}`, {
      headers: session.token ? { Authorization: `Bearer ${session.token}` } : {},
    });
    if (!resp.ok) return [];
    const data = await resp.json();
    if (!data.enabled) return [];
    return data.providers || [];
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
    if (provider.script_url) {
      const src = provider.script_url;
      if (isApprovedDomain(src) && !LOADED_SCRIPTS.has(src)) {
        LOADED_SCRIPTS.add(src);
        const s = document.createElement("script");
        s.src = src;
        s.async = true;
        wrapper.appendChild(s);
      }
    } else if (provider.script_tag) {
      const temp = document.createElement("div");
      temp.innerHTML = provider.script_tag;
      const scripts = temp.querySelectorAll("script");
      for (const s of scripts) {
        const src = s.getAttribute("src");
        if (src) {
          if (!isApprovedDomain(src)) continue;
          if (LOADED_SCRIPTS.has(src)) continue;
          LOADED_SCRIPTS.add(src);
          const clone = document.createElement("script");
          clone.src = src;
          clone.async = true;
          for (const attr of s.attributes) {
            if (attr.name !== "src") clone.setAttribute(attr.name, attr.value);
          }
          wrapper.appendChild(clone);
        } else if (s.textContent) {
          const clone = document.createElement("script");
          clone.textContent = s.textContent;
          wrapper.appendChild(clone);
        }
      }
    }
  }

  if (wrapper.children.length === 0) return null;
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
  } else {
    slotElement.remove();
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
  OBSERVED_SLOTS.clear();
}

export function resetAdObserver() {
  OBSERVED_SLOTS.clear();
}
