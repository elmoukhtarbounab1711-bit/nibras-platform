import {
  el, api, t, head, panel, body, badge, tabs,
  kpi, kpiGrid,
  listItem, barChart, hBars, emptyState, skeleton, num, fmtDt,
  icon, go, content,
} from "../ui.js";

const PERIODS = [
  { key: "7", label: "7 أيام" },
  { key: "30", label: "30 يوم" },
  { key: "90", label: "90 يوم" },
];

let currentPeriod = "30";
let _liveTimer = null;

export async function visitorsView() {
  if (_liveTimer) { clearInterval(_liveTimer); _liveTimer = null; }

  const root = el("div", { class: "flex-col", style: "gap:20px" });

  // عنوان + فلتر الفترة
  const periodTabs = tabs(PERIODS, currentPeriod, (key) => {
    currentPeriod = key;
    loadAnalytics(root);
  });

  let autoRefresh = false;
  const refreshBtn = el("button", { class: "adm-auto-refresh", type: "button" }, [
    el("span", { class: "pulse-dot" }),
    el("span", { text: "تحديث مباشر" }),
  ]);
  refreshBtn.onclick = () => {
    autoRefresh = !autoRefresh;
    refreshBtn.classList.toggle("active", autoRefresh);
    if (autoRefresh) {
      _liveTimer = setInterval(() => loadAnalytics(root), 15000);
    } else if (_liveTimer) {
      clearInterval(_liveTimer);
      _liveTimer = null;
    }
  };

  root.append(
    el("div", { class: "flex-between", style: "align-items:center" }, [
      periodTabs,
      refreshBtn,
    ]),
  );
  root.append(el("div", { id: "visitors-content", class: "flex-col", style: "gap:20px" }, [skeleton(3, 90)]));

  await loadAnalytics(root);
  return root;
}

async function loadAnalytics(root) {
  const container = root.querySelector("#visitors-content");
  if (!container) return;
  container.replaceChildren(skeleton(3, 90));

  try {
    const data = await api.get(`/api/admin/visitors/all?days=${currentPeriod}`);
    container.replaceChildren(...buildDashboard(data));
  } catch (e) {
    container.replaceChildren(
      el("div", { class: "adm-404" }, [
        el("div", { class: "ic" }, [icon("alertTriangle", 42)]),
        el("p", { text: `خطأ في تحميل البيانات: ${e.message}` }),
      ])
    );
  }
}

function buildDashboard(data) {
  const s = data.summary || {};
  const trend = data.daily_trend || [];
  const hourly = data.hourly_distribution || [];
  const pages = data.top_pages || [];
  const referrers = data.referrers || [];
  const browsers = data.browsers || [];
  const devices = data.devices || [];
  const osList = data.os || [];
  const live = data.live || {};
  const nodes = [];

  // ── KPIs الأساسية ──
  nodes.push(kpiGrid([
    kpi({ icon: "eye", label: "إجمالي الزيارات", value: num(s.total_visits), sub: `آخر ${currentPeriod} يوم`, tone: "info" }),
    kpi({ icon: "users", label: "الزوار الفريدون", value: num(s.unique_visitors), sub: `اليوم: ${num(s.today_visits)}`, tone: "green" }),
    kpi({ icon: "userCheck", label: "مستخدمون مسجلون", value: num(s.unique_users), sub: `هذا الأسبوع: ${num(s.week_visits)}`, tone: "gold" }),
    kpi({ icon: "activity", label: "الزوار النشطون الآن", value: num(live.active_now), sub: "آخر 5 دقائق", tone: "red" }),
  ]));

  // ── الاتجاه اليومي + التوزيع الساعي ──
  nodes.push(el("div", { class: "adm-grid-2" }, [
    panel([
      head("اتجاه الزيارات اليومية", [badge(`آخر ${currentPeriod} يوم`, "gray")]),
      body(trend.length
        ? buildDualLineChart(trend)
        : emptyState("لا توجد بيانات", "trendingUp")),
    ]),
    panel([
      head("التوزيع الساعي", [badge("آخر 7 أيام", "blue")]),
      body(hourly.length
        ? barChart(hourly.map((h) => ({
            label: `${h.hour}`,
            value: h.visits,
            accent: h.hour >= 9 && h.hour <= 21,
          })), { width: 620, height: 200 })
        : emptyState("لا توجد بيانات", "clock")),
    ]),
  ]));

  // ── مصادر الزيارات + المتصفحات ──
  nodes.push(el("div", { class: "adm-grid-2" }, [
    panel([
      head("مصادر الزيارات", [badge(`${referrers.length} مصدر`, "green")]),
      body(referrers.length
        ? buildDonutChart(referrers.slice(0, 6).map((r) => ({
            label: sourceLabel(r.source),
            value: r.visits,
          })), ["#071a36", "#c89b3c", "#1e7e5a", "#2b6cb0", "#b7791f", "#c0392b"])
        : emptyState("لا توجد بيانات", "link")),
    ]),
    panel([
      head("الأجهزة والمتصفحات", [badge("توزيع", "blue")]),
      body(el("div", { class: "adm-grid-2", style: "gap:20px" }, [
        buildDonutChart(devices.map((d) => ({
          label: deviceLabel(d.device),
          value: d.visits,
        })), ["#071a36", "#c89b3c", "#1e7e5a"]),
        buildDonutChart(browsers.slice(0, 5).map((b) => ({
          label: b.browser,
          value: b.visits,
        })), ["#2b6cb0", "#c89b3c", "#071a36", "#1e7e5a", "#b7791f"]),
      ])),
    ]),
  ]));

  // ── أنظمة التشغيل + أكثر الصفحات ──
  nodes.push(el("div", { class: "adm-grid-2" }, [
    panel([
      head("أنظمة التشغيل", [badge(`${osList.length} نظام`, "gold")]),
      body(osList.length
        ? hBars(osList.map((o) => ({
            label: o.os,
            value: o.visits,
            accent: o.os === "Windows",
          })))
        : emptyState("لا توجد بيانات", "monitor")),
    ]),
    panel([
      head("مصادر الزيارات — تفصيل", [badge(`${referrers.length} مصدر`, "gray")]),
      body(referrers.length
        ? el("div", { class: "adm-list" }, referrers.map((r, i) =>
            listItem({
              icon: "link",
              title: sourceLabel(r.source),
              sub: `${num(r.unique_visitors)} زائر فريد`,
              val: num(r.visits),
            })
          ))
        : emptyState("لا توجد بيانات", "link")),
    ]),
  ]));

  // ── أكثر الصفحات زيارة ──
  nodes.push(panel([
    head("أكثر الصفحات زيارة", [badge(`${pages.length} صفحة`, "gray")]),
    body(pages.length
      ? el("div", { class: "adm-list" }, pages.slice(0, 15).map((p, i) =>
          listItem({
            icon: i < 3 ? "star" : "file",
            title: p.path,
            sub: `${num(p.unique_visitors)} زائر فريد`,
            val: num(p.visits),
          })
        ))
      : emptyState("لا توجد بيانات", "list")),
  ]));

  // ── الزوار النشطون الآن ──
  nodes.push(panel([
    head("الزوار النشطون الآن", [
      live.active_now > 0
        ? badge(`${live.active_now} نشط`, "green")
        : badge("لا يوجد", "gray"),
    ]),
    body(live.recent && live.recent.length
      ? el("div", { class: "adm-list" }, live.recent.map((r) =>
          listItem({
            icon: r.device === "mobile" ? "smartphone" : "monitor",
            title: r.path,
            sub: `${r.browser} · ${deviceLabel(r.device)}`,
            val: r.time ? fmtDt(r.time) : "",
          })
        ))
      : emptyState("لا يوجد زوار نشطون", "activity")),
  ]));

  return nodes;
}

// ── رسم بياني مزدوج (زيارات + فريدون) ──
function buildDualLineChart(trend) {
  const labels = trend.map((t) => String(t.date || "").slice(5));
  const visits = trend.map((t) => t.visits || 0);
  const unique = trend.map((t) => t.unique_visitors || 0);

  const w = 620, h = 220;
  const pl = 34, pr = 10, pt = 14, pb = 26;
  const iw = w - pl - pr, ih = h - pt - pb;
  const max = Math.max(1, ...visits, ...unique);
  const n = labels.length;
  const stepX = n > 1 ? iw / (n - 1) : iw;

  const toPoints = (vals) => vals.map((v, i) => {
    const x = pl + (n > 1 ? i * stepX : 0);
    const y = pt + ih - ((Number(v) || 0) / max) * ih;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");

  const visitPts = toPoints(visits);
  const uniquePts = toPoints(unique);
  const areaPts = `${pl},${pt + ih} ${visitPts} ${pl + iw},${pt + ih}`;

  const gridLines = [0, 0.25, 0.5, 0.75, 1].map((f) => {
    const y = pt + ih - f * ih;
    return el("line", { class: "grid-line", x1: pl, x2: pl + iw, y1: y, y2: y });
  });

  const lbls = labels.map((lb, i) => {
    const x = pl + (n > 1 ? i * stepX : 0);
    return el("text", { class: "axis-label", x, y: pt + ih + 16, "text-anchor": "middle", text: String(lb) });
  });

  return el("div", {}, [
    el("svg", {
      class: "adm-chart", viewBox: `0 0 ${w} ${h}`, preserveAspectRatio: "none", role: "img",
    }, [
      ...gridLines,
      el("polygon", { class: "area", points: areaPts, fill: "var(--info-bg)", opacity: "0.3" }),
      el("polyline", { class: "line", points: visitPts, stroke: "var(--navy)", "stroke-width": "2", fill: "none" }),
      el("polyline", { class: "line", points: uniquePts, stroke: "var(--gold)", "stroke-width": "2", fill: "none", "stroke-dasharray": "6,3" }),
      ...lbls,
    ]),
    el("div", { class: "adm-legend", style: "padding:6px 34px 0" }, [
      el("span", { class: "sw", style: "background:var(--navy);border-radius:3px;display:inline-block;width:12px;height:3px;vertical-align:middle;margin-inline-end:5px" }),
      el("span", { text: "إجمالي الزيارات" }),
      el("span", { style: "margin-inline-start:12px" }, [
        el("span", { class: "sw", style: "background:var(--gold);border-radius:3px;display:inline-block;width:12px;height:3px;vertical-align:middle;margin-inline-end:5px;border-top:1px dashed var(--gold)" }),
        el("span", { text: "الزوار الفريدون" }),
      ]),
    ]),
  ]);
}

// ── مخطط دائري (Donut Chart) ──
function buildDonutChart(items, colors) {
  const total = items.reduce((s, it) => s + (Number(it.value) || 0), 0);
  if (!total) return emptyState("لا توجد بيانات", "pieChart");

  const size = 140;
  const stroke = 22;
  const r = (size - stroke) / 2;
  const circ = 2 * Math.PI * r;
  const cx = size / 2, cy = size / 2;

  let offset = 0;
  const segs = items.map((it, i) => {
    const pct = (Number(it.value) || 0) / total;
    const dash = pct * circ;
    const gap = circ - dash;
    const seg = el("circle", {
      cx, cy, r,
      fill: "none",
      stroke: colors[i % colors.length] || "#999",
      "stroke-width": stroke,
      "stroke-dasharray": `${dash.toFixed(2)} ${gap.toFixed(2)}`,
      "stroke-dashoffset": `${(-offset).toFixed(2)}`,
      style: "transition: stroke-dashoffset .3s",
    });
    offset += dash;
    return seg;
  });

  const legendNodes = items.map((it, i) => {
    const pct = total > 0 ? Math.round((Number(it.value) || 0) / total * 100) : 0;
    return el("div", { class: "dl-item" }, [
      el("span", { class: "dl-swatch", style: `background:${colors[i % colors.length] || "#999"}` }),
      el("span", { class: "dl-label", text: it.label }),
      el("span", { class: "dl-val", text: `${num(it.value)} (${pct}%)` }),
    ]);
  });

  return el("div", { class: "adm-donut-wrap" }, [
    el("div", { class: "adm-donut" }, [
      el("svg", { viewBox: `0 0 ${size} ${size}` }, segs),
      el("div", { class: "donut-center" }, [
        el("div", { class: "val", text: num(total) }),
        el("div", { class: "lbl", text: "إجمالي" }),
      ]),
    ]),
    el("div", { class: "adm-donut-legend" }, legendNodes),
  ]);
}

function sourceLabel(s) {
  const map = { direct: "مباشر", Google: "Google", Facebook: "Facebook", "Twitter/X": "Twitter/X", Instagram: "Instagram", LinkedIn: "LinkedIn", Telegram: "Telegram", WhatsApp: "WhatsApp" };
  return map[s] || s;
}

function deviceLabel(d) {
  const map = { desktop: "حاسوب", mobile: "جوال", tablet: "لوحي" };
  return map[d] || d;
}
