// نبراس — المساعد الذكي + الإشعارات + الإعدادات
import {
  el, api, t, head, panel, body, badge, tabs, kpi, kpiGrid,
  toast, emptyState, skeleton, fmtDt, num, barChart, hBars,
  field, select, input, openModal, closeModal, confirmDialog,
} from "../ui.js";
import { icon } from "../../icons.js";
import { setLang } from "../../i18n.js";

export function systemView(initial = "ai") {
  let active = initial;
  const container = el("div", { class: "flex-col", style: "gap:16px" });
  const swap = (node) => container.replaceChildren(container.firstChild, node);
  function render() {
    container.replaceChildren(tabs([
      { key: "ai", label: t("ai") },
      { key: "notifications", label: t("notifications") },
      { key: "settings", label: t("settings") },
    ], active, (k) => { active = k; render(); }));
    swap(skeleton(3, 90));
    const p = active === "ai" ? aiPanel() : active === "notifications" ? notifPanel() : settingsPanel();
    p.then(swap).catch((e) => swap(el("div", { class: "adm-404", text: String(e?.message || e) })));
  }
  render();
  return container;
}

// =====================================================================
// المساعد الذكي
// =====================================================================
async function aiPanel() {
  const s = await api.get("/api/admin/analytics/summary");
  const ai = s.ai || {};
  const calcs = s.calculators || {};
  const docs = s.documents || {};
  const byMode = Object.entries(ai.by_mode || {});
  const modeItems = byMode.map(([m, c]) => ({ label: modeName(m), value: c }));
  const total = modeItems.reduce((a, b) => a + b.value, 0) || ai.total || 0;

  const chart = modeItems.length
    ? barChart(modeItems, { width: 620, height: 200 })
    : emptyState(t("noData"), "cpu");

  return el("div", { class: "flex-col", style: "gap:16px" }, [
    kpiGrid([
      kpi({ icon: "cpu", label: t("totalQueries"), value: num(ai.total), tone: "info" }),
      kpi({ icon: "zap", label: t("todayQueries"), value: num(ai.today), tone: "green" }),
      kpi({ icon: "calculator", label: t("kpiCalculators"), value: num(calcs.total_runs), sub: t("today") + ": " + num(calcs.today), tone: "navy" }),
      kpi({ icon: "file", label: t("kpiDocs"), value: num(docs.generated_total), sub: t("today") + ": " + num(docs.generated_today), tone: "gold" }),
    ]),
    panel([head(t("ai") + " — " + t("byMode"), [badge(String(total), "blue")]), body(chart)]),
    el("div", { class: "adm-notice info" }, [
      el("span", { class: "ic" }, [icon("info", 20)]),
      el("div", {}, [el("h4", { text: t("ai") }), el("p", { text: t("aiNote") })]),
    ]),
    await providersPanel(),
  ]);
}

// =====================================================================
// إدارة مزوّدي الذكاء الاصطناعي (مجاني/مدفوع/محلي) من لوحة التحكم
// =====================================================================
const TYPE_LABELS = {
  noop: "احتياطي (noop)",
  gemini: "Google Gemini",
  openai_compatible: "OpenAI-compatible (Groq/OpenRouter/NVIDIA/Mistral…)",
  ollama: "Ollama محلي",
  anthropic: "Anthropic",
};

let providerCatalog = [];

async function providersPanel() {
  const box = el("div", { class: "flex-col", style: "gap:16px" });
  const listEl = el("div", { class: "adm-list", style: "margin-top:8px" });
  const refresh = async () => {
    listEl.replaceChildren(skeleton(2, 60));
    try {
      const { providers } = await api.get("/api/admin/ai/providers");
      const { catalog } = await api.get("/api/admin/ai/providers/catalog");
      providerCatalog = catalog || [];
      listEl.replaceChildren(
        providers.length ? providers.map((p) => providerRow(p, refresh))
          : emptyState("لا توجد مزوّدات بعد — أضِف مزوّدًا (مثلاً Gemini المجاني).", "cpu"),
      );
    } catch (e) {
      listEl.replaceChildren(el("div", { class: "adm-404", text: String(e?.message || e) }));
    }
  };
  const addBtn = el("button", { class: "btn btn-primary" }, [icon("plus", 16), " " + t("addProvider")]);
  addBtn.onclick = () => providerModal(null, refresh);
  box.append(
    panel([
      head("مزوّدو الذكاء الاصطناعي", [addBtn]),
      body(listEl),
    ]),
  );
  refresh();
  return box;
}

function providerRow(p, refresh) {
  const badges = [];
  if (p.is_default) badges.push(badge(t("default"), "navy"));
  if (p.enabled) badges.push(badge(t("enabled"), "green"));
  else badges.push(badge(t("disabled"), "gray"));
  const row = el("div", { class: "adm-list-item", style: "align-items:center" }, [
    el("span", { style: "display:flex;flex:none" }, [icon(providerTypeIcon(p.type), 18)]),
    el("div", { class: "grow" }, [
      el("div", { class: "t", text: p.name }),
      el("div", { class: "s", text: `${TYPE_LABELS[p.type] || p.type}${p.model ? " · " + p.model : ""}` }),
      el("div", { style: "display:flex;gap:6px;margin-top:4px" }, badges),
    ]),
    el("div", { style: "display:flex;gap:8px;flex-wrap:wrap;align-items:center" }, [
      p.enabled && !p.is_default
        ? el("button", { class: "btn btn-ghost btn-sm", text: t("setDefault"), onclick: async () => {
            try { await api.post(`/api/admin/ai/providers/${p.id}/default`, {}); toast(t("settingsSaved"), "success"); refresh(); }
            catch (e) { toast(e.message, "error"); }
          } })
        : null,
      el("button", { class: "btn btn-ghost btn-sm", text: t("edit"), onclick: () => providerModal(p, refresh, null) }),
      el("button", { class: "btn btn-ghost btn-sm", text: t("delete"), onclick: async () => {
        if (!(await confirmDialog({ title: t("delete"), text: p.name }))) return;
        try { await api.del(`/api/admin/ai/providers/${p.id}`); toast(t("settingsSaved"), "success"); refresh(); }
        catch (e) { toast(e.message, "error"); }
      } }),
    ]),
  ]);
  return row;
}

function providerTypeIcon(type) {
  return type === "gemini" ? "star" : type === "openai_compatible" ? "cpu" : type === "ollama" ? "smartphone" : type === "anthropic" ? "zap" : "shield";
}

function providerModal(provider, refresh) {
  const isEdit = !!provider;
  const typeS = select({}, Object.entries(TYPE_LABELS).map(([v, l]) => el("option", { value: v, text: l })));
  const nameInp = input({ placeholder: "مثال: Gemini مجاني" });
  const modelInp = input({ placeholder: "مثال: gemini-flash-latest" });
  const baseInp = input({ placeholder: "مثال: https://api.groq.com/openai/v1" });
  const keyInp = input({ type: "password", placeholder: "المفتاح (يُحفظ مشفّرًا في الخادم)" });
  const enabledBox = el("input", { type: "checkbox", style: "width:18px;height:18px" });
  const testResult = el("div", { class: "small muted", style: "margin-top:6px" });

  if (isEdit) {
    typeS.value = provider.type;
    nameInp.value = provider.name;
    modelInp.value = provider.model || "";
    baseInp.value = provider.base_url || "";
    enabledBox.checked = provider.enabled;
  }

  const catS = select({}, [
    el("option", { value: "", text: "— اختر من النماذج المجانية الجاهزة —" }),
    ...(providerCatalog || []).map((c) => el("option", { value: c.model, "data-type": c.type, "data-base": c.base_url, text: `${c.name}${c.free ? " (مجاني)" : ""}` })),
  ]);
  catS.onchange = () => {
    if (!catS.value) return;
    const opt = catS.selectedOptions[0];
    typeS.value = opt.dataset.type;
    modelInp.value = catS.value;
    baseInp.value = opt.dataset.base;
  };

  const bodyNode = el("div", { class: "flex-col", style: "gap:12px" }, [
    el("div", { class: "adm-notice info" }, [
      el("span", { class: "ic" }, [icon("info", 18)]),
      el("div", {}, [el("h4", { text: "أضِف بضغطة: اختر نموذجًا مجانيًا جاهزًا" }), el("p", { text: "ثم ألصق مفتاح API المجاني من موقع المزوّد. بعدها اضغط «اختبار» للتحقق قبل الحفظ." })]),
    ]),
    field("نموذج جاهز", catS),
    field("الاسم", nameInp),
    field("المزوّد", typeS),
    field("النموذج (model)", modelInp),
    field("عنوان API (base URL)", baseInp),
    field("مفتاح API", keyInp),
    el("div", { class: "flex-between", style: "align-items:center" }, [
      el("label", { style: "display:flex;gap:8px;align-items:center" }, [enabledBox, el("span", { text: t("enabled") })]),
      el("button", { class: "btn btn-ghost btn-sm", text: t("test") + " الاتصال", onclick: async (e) => {
        const btn = e.target.closest("button");
        btn.disabled = true;
        testResult.replaceChildren(el("span", { text: "جارٍ الاختبار…" }));
        try {
          const r = await api.post("/api/admin/ai/providers/test", {
            type: typeS.value, model: modelInp.value, base_url: baseInp.value, api_key: keyInp.value,
          });
          testResult.replaceChildren(el("span", {
            style: r.ok ? "color:var(--success);font-weight:600" : "color:var(--danger);font-weight:600",
            text: r.ok ? `نجح الاتصال (${r.provider}) · ${r.latency_ms}ms` : ("فشل: " + (r.error || "خطأ")),
          }));
        } catch (e) { testResult.replaceChildren(el("span", { style: "color:var(--danger)", text: "فشل: " + (e.message || e) })); }
        finally { btn.disabled = false; }
      } }),
    ]),
    testResult,
  ]);

  const save = async () => {
    const payload = {
      name: nameInp.value.trim() || "مزوّد غير مسمّى",
      type: typeS.value,
      model: modelInp.value.trim(),
      base_url: baseInp.value.trim(),
      api_key: keyInp.value.trim(),
      enabled: enabledBox.checked,
    };
    try {
      if (isEdit) await api.put(`/api/admin/ai/providers/${provider.id}`, payload);
      else await api.post("/api/admin/ai/providers", payload);
      toast(t("settingsSaved"), "success");
      closeModal();
      refresh();
    } catch (e) { toast(e.message, "error"); }
  };

  openModal(el("div", {}, [
    el("h2", { text: isEdit ? t("edit") + " — " + provider.name : t("addProvider") }),
    bodyNode,
    el("div", { class: "modal-actions" }, [
      el("button", { class: "btn btn-ghost", text: t("cancel"), onclick: closeModal }),
      el("button", { class: "btn btn-primary", text: t("save"), onclick: save }),
    ]),
  ]));
}

function modeName(m) {
  const map = { chat: "chat", document: t("kpiDocs"), procedure: t("procedures"), search: t("search") };
  return map[m] || String(m || "—");
}

// =====================================================================
// الإشعارات
// =====================================================================
async function notifPanel() {
  const stats = await api.get("/api/admin/notifications/delivery-stats");
  const box = el("div", { class: "flex-col", style: "gap:16px" });
  const result = el("div");
  const deliverBtn = el("button", { class: "btn btn-primary" }, [icon("send", 16), " " + t("deliverNow")]);
  deliverBtn.onclick = async () => {
    deliverBtn.disabled = true;
    try {
      const r = await api.post("/api/admin/notifications/deliver", {});
      result.replaceChildren(el("div", { class: "adm-notice info" }, [
        el("span", { class: "ic" }, [icon("checkCircle", 20)]),
        el("div", {}, [
          el("h4", { text: t("deliveryResult") }),
          el("p", { text: `${t("processed")}: ${r.processed ?? 0} · ${t("outboxSent")}: ${r.sent ?? 0} · ${t("outboxFailed")}: ${r.failed ?? 0}` }),
        ]),
      ]));
    } catch (e) { toast(e.message, "error"); }
    finally { deliverBtn.disabled = false; }
  };
  box.append(
    kpiGrid([
      kpi({ icon: "clock", label: t("outboxPending"), value: num(stats.pending), tone: "gold" }),
      kpi({ icon: "check", label: t("outboxSent"), value: num(stats.sent), tone: "green" }),
      kpi({ icon: "x", label: t("outboxFailed"), value: num(stats.failed), tone: "red" }),
    ]),
    panel([body(el("div", { class: "flex-col", style: "gap:14px" }, [deliverBtn, result]))]),
  );
  return box;
}

// =====================================================================
// الإعدادات
// =====================================================================
async function settingsPanel() {
  const langS = select({}, [
    el("option", { value: "ar", text: "العربية" }),
    el("option", { value: "fr", text: "Français" }),
  ]);
  langS.value = localStorage.getItem("nibras_lang") || "ar";
  const themeS = select({}, [
    el("option", { value: "light", text: t("light") }),
    el("option", { value: "dark", text: t("dark") }),
  ]);
  themeS.value = document.documentElement.dataset.theme || "light";

  const saveBtn = el("button", { class: "btn btn-primary", text: t("saveSettings") });
  saveBtn.onclick = () => {
    setLang(langS.value);
    document.documentElement.dataset.theme = themeS.value;
    localStorage.setItem("nibras_theme", themeS.value);
    toast(t("settingsSaved"), "success");
    setTimeout(() => location.reload(), 350);
  };

  return el("div", { class: "flex-col", style: "gap:16px" }, [
    panel([head(t("settings"), []), body(el("div", { class: "adm-grid-2" }, [
      field(t("interfaceLanguage"), langS),
      field(t("appearance"), themeS),
    ]))]),
    el("div", { style: "display:flex;justify-content:flex-end" }, [saveBtn]),
    panel([head(t("platformInfo"), []), body(el("div", { class: "adm-list" }, [
      el("div", { class: "adm-list-item" }, [el("div", { class: "grow" }, [
        el("div", { class: "t", text: "Nibras" }), el("div", { class: "s", text: t("title") }),
      ])]),
      el("div", { class: "adm-list-item" }, [el("div", { class: "grow" }, [
        el("div", { class: "t", text: t("adminRole") }), el("div", { class: "s", text: t("usersReadOnly") }),
      ])]),
    ]))]),
  ]);
}
