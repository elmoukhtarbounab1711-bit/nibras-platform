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

const DONUT_COLORS = [
  "var(--navy)", "var(--gold)", "#1e7e5a",
  "var(--info)", "#b7791f", "var(--danger)",
];
const DONUT_COLORS_3 = ["var(--navy)", "var(--gold)", "#1e7e5a"];

let currentPeriod = "30";
let _liveTimer = null;

export async function visitorsView() {
  if (_liveTimer) { clearInterval(_liveTimer); _liveTimer = null; }

  const root = el("div", { class: "flex-col", style: "gap:20px" });

  const periodTabs = tabs(PERIODS, currentPeriod, (key) => {
    currentPeriod = key;
    loadAnalytics(root);
  });

  let autoRefresh = false;
  const refreshBtn = el("button", { class: "adm-auto-refresh", type: "button" }, [
    el("span", { class: "pulse-dot" }),
    el("span", { text: t("visitorsLive") }),
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
        el("p", { text: `${t("visitorsNoData")}: ${e.message}` }),
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

  // ── KPIs ──
  nodes.push(kpiGrid([
    kpi({
      icon: "eye",
      label: t("visitorsTotalVisits"),
      value: num(s.total_visits),
      sub: t("visitorsLastDays").replace("{d}", currentPeriod),
      tone: "info",
    }),
    kpi({
      icon: "users",
      label: t("visitorsUniqueVisitors"),
      value: num(s.unique_visitors),
      sub: t("visitorsToday") + num(s.today_visits),
      tone: "green",
    }),
    kpi({
      icon: "userCheck",
      label: t("visitorsRegisteredUsers"),
      value: num(s.unique_users),
      sub: t("visitorsThisWeek") + num(s.week_visits),
      tone: "gold",
    }),
    kpi({
      icon: "activity",
      label: t("visitorsActiveNow"),
      value: num(live.active_now),
      sub: t("visitorsLast5min"),
      tone: "red",
    }),
  ]));

  // ── الاتجاه اليومي + التوزيع الساعي ──
  nodes.push(el("div", { class: "adm-grid-2" }, [
    panel([
      head(t("visitorsTrendTitle"), [badge(t("visitorsLastDays").replace("{d}", currentPeriod), "gray")]),
      body(trend.length
        ? buildDualLineChart(trend)
        : emptyState(t("visitorsNoData"), "trendingUp")),
    ]),
    panel([
      head(t("visitorsHourlyTitle"), [badge(t("visitorsLastDays").replace("{d}", "7"), "blue")]),
      body(hourly.length
        ? barChart(hourly.map((h) => ({
            label: `${h.hour}`,
            value: h.visits,
            accent: h.hour >= 9 && h.hour <= 21,
          })), { width: 620, height: 200 })
        : emptyState(t("visitorsNoData"), "clock")),
    ]),
  ]));

  // ── مصادر الزيارات + المتصفحات ──
  nodes.push(el("div", { class: "adm-grid-2" }, [
    panel([
      head(t("visitorsSourcesTitle"), [badge(`${referrers.length}${t("visitorsSource")}`, "green")]),
      body(referrers.length
        ? buildDonutChart(referrers.slice(0, 6).map((r) => ({
            label: sourceLabel(r.source),
            value: r.visits,
          })), DONUT_COLORS)
        : emptyState(t("visitorsNoData"), "link")),
    ]),
    panel([
      head(t("visitorsDevicesBrowsersTitle"), [badge(t("visitorsDistribution"), "blue")]),
      body(el("div", { class: "adm-grid-2", style: "gap:20px" }, [
        buildDonutChart(devices.map((d) => ({
          label: deviceLabel(d.device),
          value: d.visits,
        })), DONUT_COLORS_3),
        buildDonutChart(browsers.slice(0, 5).map((b) => ({
          label: b.browser,
          value: b.visits,
        })), ["var(--info)", "var(--gold)", "var(--navy)", "#1e7e5a", "#b7791f"]),
      ])),
    ]),
  ]));

  // ── أنظمة التشغيل + أكثر الصفحات ──
  nodes.push(el("div", { class: "adm-grid-2" }, [
    panel([
      head(t("visitorsOssTitle"), [badge(`${osList.length} ${t("visitorsOS")}`, "gold")]),
      body(osList.length
        ? hBars(osList.map((o) => ({
            label: o.os,
            value: o.visits,
            accent: o.os === "Windows",
          })))
        : emptyState(t("visitorsNoData"), "monitor")),
    ]),
    panel([
      head(t("visitorsSourcesDetailTitle"), [badge(`${referrers.length}${t("visitorsSource")}`, "gray")]),
      body(referrers.length
        ? el("div", { class: "adm-list" }, referrers.map((r) =>
            listItem({
              icon: "link",
              title: sourceLabel(r.source),
              sub: t("visitorsUniqueCount").replace("{n}", num(r.unique_visitors)),
              val: num(r.visits),
            })
          ))
        : emptyState(t("visitorsNoData"), "link")),
    ]),
  ]));

  // ── أكثر الصفحات زيارة ──
  nodes.push(panel([
    head(t("visitorsTopPagesTitle"), [badge(`${pages.length} ${t("visitorsPage")}`, "gray")]),
    body(pages.length
      ? el("div", { class: "adm-list" }, pages.slice(0, 15).map((p, i) =>
          listItem({
            icon: i < 3 ? "star" : "file",
            title: p.path,
            sub: t("visitorsUniqueCount").replace("{n}", num(p.unique_visitors)),
            val: num(p.visits),
          })
        ))
      : emptyState(t("visitorsNoData"), "list")),
  ]));

  // ── الزوار النشطون الآن ──
  nodes.push(panel([
    head(t("visitorsActiveNowTitle"), [
      live.active_now > 0
        ? badge(`${live.active_now} ${t("visitorsActive")}`, "green")
        : badge(t("visitorsNone"), "gray"),
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
      : emptyState(t("visitorsNoActive"), "activity")),
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
      class: "adm-chart", viewBox: `0 0 ${w} ${h}`, preserveAspectRatio: "xMidYMid meet", role: "img",
    }, [
      ...gridLines,
      el("polygon", { class: "area", points: areaPts }),
      el("polyline", { class: "line", points: visitPts }),
      el("polyline", {
        class: "line", points: uniquePts,
        style: "stroke:var(--gold);stroke-dasharray:6,3",
      }),
      ...lbls,
    ]),
    el("div", { class: "adm-legend", style: "padding:6px 34px 0" }, [
      el("span", { class: "sw-line", style: "background:var(--navy)" }),
      el("span", { text: t("visitorsTotalVisits") }),
      el("span", { style: "margin-inline-start:12px" }, [
        el("span", { class: "sw-line", style: "background:var(--gold);border-top:1px dashed var(--gold)" }),
        el("span", { text: t("visitorsUniqueVisitors") }),
      ]),
    ]),
  ]);
}

// ── مخطط دائري (Donut Chart) ──
function buildDonutChart(items, colors) {
  const total = items.reduce((s, it) => s + (Number(it.value) || 0), 0);
  if (!total) return emptyState(t("visitorsNoData"), "pieChart");

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
    const col = colors[i % colors.length] || "#999";
    const seg = el("circle", {
      cx, cy, r,
      fill: "none",
      "stroke-width": stroke,
      "stroke-dasharray": `${dash.toFixed(2)} ${gap.toFixed(2)}`,
      "stroke-dashoffset": `${(-offset).toFixed(2)}`,
      style: `stroke:${col};transition:stroke-dashoffset .3s`,
    });
    offset += dash;
    return seg;
  });

  const legendNodes = items.map((it, i) => {
    const pct = total > 0 ? Math.round((Number(it.value) || 0) / total * 100) : 0;
    const col = colors[i % colors.length] || "#999";
    return el("div", { class: "dl-item" }, [
      el("span", { class: "dl-swatch", style: `background:${col}` }),
      el("span", { class: "dl-label", text: it.label }),
      el("span", { class: "dl-val", text: `${num(it.value)} (${pct}%)` }),
    ]);
  });

  return el("div", { class: "adm-donut-wrap" }, [
    el("div", { class: "adm-donut" }, [
      el("svg", { viewBox: `0 0 ${size} ${size}` }, segs),
      el("div", { class: "donut-center" }, [
        el("div", { class: "val", text: num(total) }),
        el("div", { class: "lbl", text: t("visitorsTotal") }),
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
