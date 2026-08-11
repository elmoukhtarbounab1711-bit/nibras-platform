// نبراس — أدوات واجهة مشتركة (وسوم، توست، نوافذ، ترقيم، تنسيق)
import { tr } from "./i18n.js";
import { icon } from "./icons.js";
import { session } from "./api.js";

export const el = (tag, attrs = {}, children = []) => {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else if (k === "html") node.innerHTML = v;
    else if (k === "text") node.textContent = v;
    else if (k.startsWith("on") && typeof v === "function") node.addEventListener(k.slice(2), v);
    else if (v !== false && v != null) node.setAttribute(k, v === true ? "" : v);
  }
  for (const c of [].concat(children)) {
    if (c == null || c === false) continue;
    node.append(c.nodeType ? c : document.createTextNode(c));
  }
  return node;
};

export const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (m) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[m]);

export const truncate = (s, n = 140) => {
  s = String(s ?? "");
  return s.length > n ? s.slice(0, n).trimEnd() + "…" : s;
};

const AR_MONTHS = ["يناير","فبراير","مارس","أبريل","ماي","يونيو","يوليو","غشت","شتنبر","أكتوبر","نونبر","دجنبر"];
const FR_MONTHS = ["janv","févr","mars","avr","mai","juin","juil","août","sept","oct","nov","déc"];

export function fmtDate(value, lang) {
  if (!value) return "—";
  const d = new Date(value);
  if (isNaN(d)) return String(value).slice(0, 10);
  const l = lang === "fr" ? "fr-FR" : "ar-MA";
  try {
    if (lang === "fr") return d.toLocaleDateString("fr-FR", { day: "numeric", month: "short", year: "numeric" });
    return `${d.getDate()} ${AR_MONTHS[d.getMonth()]} ${d.getFullYear()}`;
  } catch { return `${d.getDate()} ${FR_MONTHS[d.getMonth()]} ${d.getFullYear()}`; }
}

export const initials = (name) => {
  const parts = String(name || "").trim().split(/\s+/).filter(Boolean);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return (parts[0]?.[0] || "م").toUpperCase();
};

const AVATAR_COLORS = ["#1f3a93", "#0f766e", "#9a3412", "#4f46e5", "#0e7490", "#b45309"];
export const avatarColor = (seed) => {
  let h = 0;
  for (const ch of String(seed)) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return AVATAR_COLORS[h % AVATAR_COLORS.length];
};

export function downloadFile(url, filename = "document") {
  const headers = {};
  if (session.token) headers.Authorization = `Bearer ${session.token}`;
  fetch(url, { headers })
    .then(async (resp) => {
      if (!resp.ok) {
        const d = await resp.json().catch(() => ({}));
        throw new Error(d.error || resp.statusText);
      }
      return resp.blob();
    })
    .then((blob) => {
      const objectUrl = URL.createObjectURL(blob);
      const a = el("a", { href: objectUrl, download: filename });
      document.body.append(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(objectUrl), 4000);
    })
    .catch((e) => toast(e.message, "error"));
}

export function toast(message, type = "info") {  const stack = document.getElementById("toast-stack");
  const node = el("div", { class: `toast ${type}`, role: "status" }, [message]);
  stack.append(node);
  setTimeout(() => {
    node.style.opacity = "0";
    node.style.transition = "opacity .3s";
    setTimeout(() => node.remove(), 320);
  }, 3800);
}

export function showConfirm({ title, text, onOk, danger = true }) {
  const modal = document.getElementById("confirm-modal");
  document.getElementById("confirm-title").textContent = title;
  document.getElementById("confirm-text").textContent = text || "";
  document.getElementById("confirm-ok").className = danger ? "btn btn-danger" : "btn btn-primary";
  modal.hidden = false;
  const cleanup = () => {
    modal.hidden = true;
    okBtn.onclick = cancelBtn.onclick = backdrop.onclick = null;
  };
  const okBtn = document.getElementById("confirm-ok");
  const cancelBtn = document.getElementById("confirm-cancel");
  const backdrop = modal;
  okBtn.onclick = () => { cleanup(); onOk && onOk(); };
  cancelBtn.onclick = cleanup;
  backdrop.addEventListener("click", (e) => { if (e.target === backdrop) cleanup(); }, { once: true });
}

export function openModal(node) {
  const modal = document.getElementById("auth-modal");
  const body = document.getElementById("auth-modal-body");
  body.replaceChildren();
  if (node && node.nodeType) body.appendChild(node);
  else body.innerHTML = node || "";
  modal.hidden = false;
  const closeBtns = modal.querySelectorAll("[data-close-modal]");
  closeBtns.forEach((b) => (b.onclick = closeModal));
  modal.addEventListener("click", (e) => { if (e.target === modal) closeModal(); }, { once: true });
  return modal;
}

export function closeModal() {
  const modal = document.getElementById("auth-modal");
  modal.hidden = true;
  modal.querySelectorAll("[data-close-modal]").forEach((b) => (b.onclick = null));
}

export function pagination(total, page, perPage, onGo) {
  const pages = Math.max(1, Math.ceil(total / perPage));
  const wrap = el("div", { class: "pagination" });
  wrap.append(el("button", { class: "page-btn", disabled: page <= 1, text: "‹", onclick: () => onGo(page - 1) }));
  const start = Math.max(1, Math.min(page - 2, pages - 4));
  const end = Math.min(pages, start + 4);
  for (let p = start; p <= end; p++) {
    wrap.append(el("button", { class: `page-btn${p === page ? " active" : ""}`, text: p, onclick: () => onGo(p) }));
  }
  wrap.append(el("button", { class: "page-btn", disabled: page >= pages, text: "›", onclick: () => onGo(page + 1) }));
  return wrap;
}

export function skeleton(count = 3, height = 90) {
  return el("div", { class: "flex-col" },
    Array.from({ length: count }, () => el("div", { class: "skeleton", style: `height:${height}px` })));
}

export function emptyState(message, iconName = "folder") {
  return el("div", { class: "empty" }, [
    el("div", { class: "empty-icon" }, [icon(iconName, 40)]),
    el("div", { text: message }),
  ]);
}

export const typeLabel = (type, lang) => {
  const key = type ? { constitution: "typeConstitution", code: "typeCode", law: "typeLaw", decree: "typeDecree", gazette: "typeGazette", treaty: "typeTreaty", ruling: "typeRuling", organic_law: "typeOrganicLaw", dahir: "typeDahir", dahir_law: "typeDahirLaw", royal_decree: "typeRoyalDecree", decision: "typeDecision" }[type] : null;
  return key ? tr(key) : (type || "—");
};

export function slugifyAr(s) {
  return String(s).trim().toLowerCase()
    .replace(/[^\w\u0600-\u06FF\s-]/g, "")
    .replace(/\s+/g, "-").replace(/-+/g, "-");
}
