// نبراس — أدوات مشتركة للوحة التحكم الإدارية
import { api, session } from "../api.js";
import { tr } from "../i18n.js";
import { icon } from "../icons.js";
import {
  el, esc, toast, openModal, closeModal, showConfirm,
  pagination, skeleton, emptyState, fmtDate, truncate, typeLabel,
} from "../ui.js";

export { el, esc, toast, openModal, closeModal, pagination, skeleton, emptyState, fmtDate, truncate, typeLabel };
export { icon };
export { api };

// ---------- لغة قصيرة ----------
export const t = (key) => tr("admin." + key);

// ---------- حالة ----------
export const state = {
  lang: () => localStorage.getItem("nibras_lang") || "ar",
  theme: () => document.documentElement.dataset.theme || "light",
  section: "dashboard",
};

// ---------- تنقل ----------
export const go = (section) => {
  location.hash = "#/admin/" + section;
};

export const reload = () => {
  const fn = SectionViews[state.section];
  if (!fn) return;
  const out = fn();
  if (out && typeof out.then === "function") {
    content().replaceChildren(skeleton(3, 70));
    out.then((node) => content().replaceChildren(node)).catch((e) => fail(e));
  } else {
    content().replaceChildren(out);
  }
};

let _contentEl = null;
export const content = () => {
  _contentEl = _contentEl || document.getElementById("adm-content");
  return _contentEl;
};

export function fail(err) {
  content().replaceChildren(
    el("div", { class: "adm-404" }, [
      el("div", { class: "ic" }, [icon("alertTriangle", 42)]),
      el("p", { text: String(err?.message || err) }),
    ])
  );
}

// ---------- نافذة تأكيد (Promise) ----------
export function confirmDialog({ title, text, danger = true, okLabel }) {
  return new Promise((resolve) => {
    const modal = document.getElementById("confirm-modal");
    const ok = document.getElementById("confirm-ok");
    const cancel = document.getElementById("confirm-cancel");
    document.getElementById("confirm-title").textContent = title;
    document.getElementById("confirm-text").textContent = text || "";
    ok.className = danger ? "btn btn-danger" : "btn btn-primary";
    ok.textContent = okLabel || tr("admin.confirm");
    cancel.textContent = tr("admin.cancel");
    modal.hidden = false;
    const done = (v) => {
      modal.hidden = true;
      ok.onclick = cancel.onclick = backdropHandler = null;
      resolve(v);
    };
    const backdropHandler = (e) => { if (e.target === modal) done(false); };
    ok.onclick = () => done(true);
    cancel.onclick = () => done(false);
    modal.addEventListener("click", backdropHandler, { once: true });
  });
}

// ---------- رأس قسم ----------
export function head(title, actions = []) {
  return el("div", { class: "adm-panel-head" }, [
    el("h3", { text: title }),
    actions.length ? el("div", { class: "tools" }, actions) : null,
  ]);
}

export function panel(children, opts = {}) {
  return el("div", { class: "adm-panel" + (opts.flush ? " flush" : "") }, children);
}

export function body(children) {
  return el("div", { class: "adm-panel-body" }, children);
}

// ---------- مؤشر ----------
export function kpi({ icon: iconName = "barChart", label, value, sub = "", tone = "info" }) {
  const tones = {
    info: "var(--info-bg)", green: "var(--success-bg)", gold: "var(--warn-bg)",
    red: "var(--danger-bg)", navy: "var(--surface-2)",
  };
  return el("div", { class: "adm-kpi" }, [
    el("div", { class: "k-ic", style: `background:${tones[tone] || tones.info}` }, [icon(iconName, 22)]),
    el("div", { class: "k-val", text: String(value ?? 0) }),
    el("div", { class: "k-label", text: label }),
    sub ? el("div", { class: "k-sub", text: sub }) : null,
  ]);
}

export function kpiGrid(items) {
  return el("div", { class: "adm-kpi-grid" }, items.map((it) => (it && it.nodeType ? it : kpi(it))));
}

// ---------- شارة ----------
export function badge(text, kind = "gray") {
  return el("span", { class: `adm-badge ${kind}`, text });
}

export function statusBadge(status) {
  const map = {
    active: ["green", "●"], published: ["green", "●"], verified: ["green", "●"],
    sent: ["green", "●"], approved: ["green", "●"],
    suspended: ["red", "●"], ended: ["red", "●"], failed: ["red", "●"],
    rejected: ["red", "●"], hidden: ["gray", "●"], dismissed: ["gray", "●"],
    paused: ["gold", "●"], pending: ["gold", "●"], pending_verification: ["gold", "●"],
    open: ["gold", "●"],
  };
  const [kind, dot] = map[status] || ["blue", "●"];
  const label = statusLabel(status);
  return badge(label, kind, dot);
}

const STATUS_LABELS = {
  active: "admin.active", suspended: "admin.suspended", ended: "admin.endCampaign",
  published: "admin.published", pending: "admin.pending", hidden: "admin.hidden",
  paused: "admin.pause", sent: "admin.outboxSent", failed: "admin.outboxFailed",
  dismissed: "admin.dismissReport", approved: "admin.approve", rejected: "admin.reject",
  pending_verification: "admin.pendingVerification", verified: "admin.verifiedList",
  open: "admin.openReports", general: "admin.general", sponsored: "admin.sponsored",
  professional_promotion: "admin.professionalPromotion",
};

export function statusLabel(status) {
  const k = STATUS_LABELS[status];
  return k ? tr(k) : String(status || "—");
}

export function badgeWith(text, kind) {
  return el("span", { class: `adm-badge ${kind}`, text });
}

// ---------- تبويبات ----------
export function tabs(items, active, onSelect) {
  return el("div", { class: "adm-tabs", role: "tablist" }, items.map((it) =>
    el("button", {
      class: "adm-tab" + (it.key === active ? " active" : ""),
      type: "button", text: it.label, role: "tab",
      onclick: () => onSelect(it.key),
    })));
}

// ---------- صفوف قوائم ----------
export function listItem({ title, sub, val, icon: iconName, extra }) {
  return el("div", { class: "adm-list-item" }, [
    iconName ? el("span", { style: "display:flex;flex:none" }, [icon(iconName, 18)]) : null,
    el("div", { class: "grow" }, [
      el("div", { class: "t", text: title }),
      sub ? el("div", { class: "s", text: sub }) : null,
    ]),
    extra || null,
    val != null ? el("div", { class: "val", text: String(val) }) : null,
  ]);
}

// ---------- مخطط خطي (SVG) ----------
export function lineChart(labels, values, opts = {}) {
  const w = opts.width || 620, h = opts.height || 200;
  const pl = 34, pr = 10, pt = 14, pb = 26;
  const iw = w - pl - pr, ih = h - pt - pb;
  const max = Math.max(1, ...values.map((v) => Number(v) || 0));
  const n = labels.length;
  const stepX = n > 1 ? iw / (n - 1) : iw;
  const pts = values.map((v, i) => {
    const x = pl + (n > 1 ? i * stepX : 0);
    const y = pt + ih - (Number(v) || 0) / max * ih;
    return [x, y];
  });
  const linePts = pts.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  const areaPts = `${pl},${pt + ih} ${linePts} ${pl + iw},${pt + ih}`;
  const gridLines = [0, 0.25, 0.5, 0.75, 1].map((f) => {
    const y = pt + ih - f * ih;
    return el("line", {
      class: "grid-line", x1: pl, x2: pl + iw, y1: y, y2: y,
    });
  });
  const lbls = labels.map((lb, i) => {
    const [x] = pts[i] || [pl, pt + ih];
    return el("text", { class: "axis-label", x, y: pt + ih + 16, "text-anchor": "middle", text: String(lb) });
  });
  return el("svg", {
    class: "adm-chart", viewBox: `0 0 ${w} ${h}`, preserveAspectRatio: "none",
    role: "img",
  }, [
    ...gridLines,
    el("polygon", { class: "area", points: areaPts }),
    el("polyline", { class: "line", points: linePts }),
    ...lbls,
  ]);
}

// ---------- مخطط أعمدة (SVG) ----------
export function barChart(items, opts = {}) {
  const w = opts.width || 620, h = opts.height || 190;
  const pl = 8, pr = 8, pt = 18, pb = 24;
  const iw = w - pl - pr, ih = h - pt - pb;
  const max = Math.max(1, ...items.map((it) => Number(it.value) || 0));
  const n = items.length;
  const bw = n ? Math.min(54, (iw / n) * 0.62) : 0;
  const bars = items.map((it, i) => {
    const x = pl + (i + 0.5) * (iw / n) - bw / 2;
    const bh = (Number(it.value) || 0) / max * ih;
    const y = pt + ih - bh;
    return [
      el("rect", { class: "bar" + (it.accent ? " accent" : ""), x, y, width: bw, height: Math.max(bh, 1), rx: "3" }),
      el("text", { class: "lbl", x: x + bw / 2, y: Math.max(y - 5, 8), "text-anchor": "middle", text: String(it.value ?? 0) }),
      el("text", { class: "axis-label", x: x + bw / 2, y: pt + ih + 15, "text-anchor": "middle", text: String(it.label) }),
    ];
  });
  return el("svg", {
    class: "adm-chart", viewBox: `0 0 ${w} ${h}`, role: "img",
  }, [el("line", { class: "grid-line", x1: pl, x2: pl + iw, y1: pt + ih, y2: pt + ih }), ...bars.flat()]);
}

// ---------- أعمدة أفقية بتقنية CSS ----------
export function hBars(items, max) {
  const m = max || Math.max(1, ...items.map((it) => Number(it.value) || 0));
  return el("div", { class: "flex-col", style: "gap:10px" }, items.map((it) => {
    const pct = Math.max(2, Math.round((Number(it.value) || 0) / m * 100));
    return el("div", {}, [
      el("div", { class: "flex-between small", style: "font-size:12px;color:var(--ink-2)" }, [
        el("span", { text: it.label }), el("strong", { text: String(it.value ?? 0) }),
      ]),
      el("div", { style: "height:9px;background:var(--surface-2);border-radius:999px;overflow:hidden;margin-top:4px" }, [
        el("div", { style: `width:${pct}%;height:100%;background:${it.accent ? "var(--gold)" : "var(--navy)"};border-radius:999px` }),
      ]),
    ]);
  }));
}

// ---------- أدوات نصية ----------
export const money = (cents) => `${(Number(cents) || 0) / 100} د`;
export const num = (v) => Number(v ?? 0).toLocaleString("fr-MA");

// تنزيل ملف محمي بمصادقة (الترويسة Authorization مطلوبة لدور admin)
export async function downloadFile(url, filename) {
  try {
    const resp = await fetch(url, {
      headers: { Authorization: `Bearer ${session.token}` },
    });
    if (!resp.ok) {
      const d = await resp.json().catch(() => ({}));
      throw new Error(d.error || resp.statusText);
    }
    const blob = await resp.blob();
    const objectUrl = URL.createObjectURL(blob);
    const a = el("a", { href: objectUrl, download: filename || "document" });
    document.body.append(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(objectUrl), 4000);
  } catch (e) {
    toast(e.message, "error");
  }
}
export function fmtDt(value) {
  if (!value) return "—";
  const d = new Date(value);
  if (isNaN(d)) return String(value).slice(0, 10);
  const date = fmtDate(value, state.lang());
  const tme = d.toLocaleTimeString(state.lang() === "fr" ? "fr-FR" : "ar-MA", { hour: "2-digit", minute: "2-digit" });
  return `${date} · ${tme}`;
}

export function debounce(fn, ms = 320) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

export const input = (attrs) => el("input", { class: "adm-input", type: "text", ...attrs });
export const select = (attrs, options) => el("select", { class: "adm-select", ...attrs }, options);
export const field = (label, control, hint) =>
  el("div", { class: "field" }, [
    el("label", { text: label }),
    control,
    hint ? el("div", { class: "small muted", style: "margin-top:3px", text: hint }) : null,
  ]);

// معرّف الأقسام (يُعبّأ لاحقًا من admin.js)
export const SectionViews = {};
