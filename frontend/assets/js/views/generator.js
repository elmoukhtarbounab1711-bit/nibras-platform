// نبراس — مولد الوثائق والعقود: مكتبة قوالب + تعبئة + معاينة + تنزيل DOCX
import { tr } from "../i18n.js";
import { api } from "../api.js";
import { el, esc, emptyState, skeleton, toast } from "../ui.js";
import { icon } from "../icons.js";
import { navigate } from "../router.js";

function qs(name) {
  return new URLSearchParams(window.location.search).get(name) || "";
}

function fileParam(file) {
  return encodeURIComponent(file);
}

function fmtSize(bytes) {
  if (!bytes) return "";
  const kb = bytes / 1024;
  return kb >= 1024 ? `${(kb / 1024).toFixed(1)} MB` : `${Math.round(kb)} KB`;
}

// ---------------------------------------------------------------------------
// الصفحة الرئيسية: قوالب موصى بها + تصفح المكتبة
// ---------------------------------------------------------------------------

export async function generatorView() {
  const wrap = el("div", { class: "flex-col" });

  const head = el("div", { class: "section-head" }, [
    el("div", {}, [
      el("h2", { text: "مولد الوثائق والعقود" }),
      el("p", { class: "small muted", text: "قوالب وثائق مغربية جاهزة — عبِّئ البيانات وحمّل المستند بنسق Word أو اطبعه مباشرة" }),
    ]),
  ]);
  wrap.append(head);
  wrap.append(skeleton(3, 90));

  const [tplData, catalog] = await Promise.all([
    api.get("/api/generator/templates").catch(() => ({ templates: [] })),
    api.get("/api/generator/catalog").catch(() => ({ categories: [], docs: [] })),
  ]);

  const templates = (tplData.templates || []).filter((t) => t && t.file);
  const cats = catalog.categories || [];
  const docs = catalog.docs || [];
  const total = docs.length;

  if (!total) {
    wrap.replaceChildren(head);
    wrap.append(emptyState("لم تُرمَّز مكتبة الوثائق في هذا الخادم بعد.", "folder"));
    return wrap;
  }

  // --- القوالب الموصى بها
  if (templates.length) {
    const tGrid = el("div", { class: "grid-2" });
    templates.slice(0, 12).forEach((t) => {
      tGrid.append(el("div", { class: "card flex-between" }, [
        el("div", {}, [
          el("span", { class: "badge", text: t.category }),
          el("strong", { class: "mt-4", text: t.title }),
          el("p", { class: "small muted mt-4", text: t.description || "" }),
        ]),
        el("button", {
          class: "btn btn-sm btn-primary",
          onclick: () => navigate(`/generator/template?template=${encodeURIComponent(t.id)}&file=${fileParam(t.file)}`),
        }, [icon("pen", 16), " عبّئ القالب"]),
      ]));
    });
    wrap.append(el("div", { class: "section-head mt-8" }, [
      el("h3", { text: tr("templates") }),
    ]));
    wrap.append(tGrid);
  }

  // --- تصفح المكتبة
  const searchInput = el("input", {
    class: "input", type: "search",
    placeholder: "ابحث في 1900+ قالب وثيقة... (وكالة، عقد كراء، شكاية، تنازل...)",
  });
  const status = el("span", { class: "small muted", text: `${total} وثيقة` });
  let activeCat = "";
  const listEl = el("div", { class: "flex-col mt-8" });

  function renderLibrary() {
    const q = (searchInput.value || "").trim().toLowerCase();
    let filtered = docs;
    if (activeCat) filtered = filtered.filter((d) => d.category_slug === activeCat);
    if (q) filtered = filtered.filter((d) =>
      (d.title || "").toLowerCase().includes(q) || (d.category || "").toLowerCase().includes(q));
    listEl.replaceChildren();
    if (!filtered.length) {
      listEl.append(emptyState("لا توجد وثائق مطابقة.", "search"));
      status.textContent = "0 وثيقة";
      return;
    }
    status.textContent = `${filtered.length} وثيقة`;
    filtered.slice(0, 120).forEach((d) => {
      const row = el("div", { class: "card flex-between" }, [
        el("div", {}, [
          el("div", { class: "flex-wrap gap-6" }, [
            el("span", { class: "badge", text: d.category }),
            el("span", { class: "badge muted", text: d.ext || "doc" }),
            el("span", { class: "small muted", text: fmtSize(d.size) }),
          ]),
          el("strong", { class: "mt-4", text: d.title }),
          el("p", { class: "small muted mt-4", text: d.fillable ? "قابل للتعبئة" : "تنزيل الأصل فقط" }),
        ]),
        el("div", { class: "flex gap-6" }, [
          el("a", { class: "btn btn-ghost btn-sm", href: `/api/generator/file?file=${fileParam(d.file)}` }, [icon("download", 14), " الأصلي"]),
          d.fillable
            ? el("button", {
                class: "btn btn-sm btn-primary",
                onclick: () => navigate(`/generator/doc?file=${fileParam(d.file)}`),
              }, [icon("pen", 14), " عبّئ"])
            : null,
        ]),
      ]);
      listEl.append(row);
    });
  }

  const chipRow = el("div", { class: "flex-wrap gap-6 mt-8" });
  function setChips(target) {
    chipRow.querySelectorAll(".chip").forEach((c) => c.classList.remove("chip-active"));
    target.classList.add("chip-active");
  }
  chipRow.append(el("button", {
    class: "chip chip-active", text: tr("all"),
    onclick: (e) => { activeCat = ""; setChips(e.currentTarget); renderLibrary(); },
  }));
  cats.slice(0, 18).forEach((c) => {
    chipRow.append(el("button", {
      class: "chip", text: `${c.name} (${c.count})`,
      onclick: (e) => { activeCat = c.slug; setChips(e.currentTarget); renderLibrary(); },
    }));
  });
  searchInput.addEventListener("input", renderLibrary);

  wrap.append(el("div", { class: "section-head mt-8" }, [
    el("div", {}, [el("h3", { text: "مكتبة القوالب" }), status]),
  ]));
  wrap.append(searchInput);
  wrap.append(chipRow);
  wrap.append(listEl);

  return wrap;
}

// ---------------------------------------------------------------------------
// نموذج التعبئة
// ---------------------------------------------------------------------------

function inputFor(field, value) {
  const set = (val) => { value[field.key] = val; };
  if (field.type === "textarea") {
    return el("textarea", { class: "input", rows: 3, oninput: (e) => set(e.target.value) });
  }
  if (field.type === "date") {
    return el("input", { class: "input", type: "date", onchange: (e) => set(e.target.value) });
  }
  if (field.type === "money" || field.type === "number") {
    return el("input", { class: "input", type: "text", inputmode: "decimal", placeholder: "0", oninput: (e) => set(e.target.value) });
  }
  return el("input", { class: "input", type: "text", oninput: (e) => set(e.target.value) });
}

async function openTemplate(file, template, editable) {
  const wrap = el("div", { class: "flex-col" });
  wrap.append(skeleton(4, 90));
  let data;
  try {
    const qs = template ? `template=${encodeURIComponent(template)}&file=${fileParam(file)}` : `file=${fileParam(file)}`;
    data = await api.get(`/api/generator/fields?${qs}`);
  } catch (e) {
    wrap.replaceChildren(el("div", { class: "card empty" }, [
      el("div", { class: "empty-icon" }, [icon("alertTriangle", 40)]),
      el("div", { text: e.message }),
    ]));
    return wrap;
  }

  const fields = data.fields || [];
  const values = {};

  const titleRow = el("div", { class: "section-head" }, [
    el("div", {}, [
      el("button", { class: "btn btn-ghost btn-sm", onclick: () => navigate("/generator") }, [icon("arrowLeft", 16), " " + tr("back")]),
      el("h2", { class: "mt-4", text: data.title }),
      el("p", {
        class: "small muted mt-4",
        text: "عبِّئ الحقول التالية ثم نفّذ المعاينة والطباعة أو نزّل المستند. المحرّك يختار الحقول تلقائيًا من فراغات القالب الأصلي.",
      }),
    ]),
  ]);

  const form = el("div", { class: "card mt-8 flex-col" });
  fields.forEach((f) => {
    const labelNode = editable
      ? el("input", { class: "input", value: f.label || f.key, oninput: (e) => { f.label = e.target.value; } })
      : el("span", { text: f.label || f.key });
    const typeNode = editable
      ? el("select", { class: "input", onchange: (e) => { f.type = e.target.value; } },
          ["text", "textarea", "date", "money", "number"].map((t) =>
            el("option", { value: t, text: t, selected: f.type === t })))
      : el("span", { class: "badge muted", text: f.type });
    form.append(el("div", { class: "field mb-8" }, [
      el("label", { class: "small muted" }, [labelNode]),
      typeNode,
      inputFor(f, values),
    ]));
  });

  async function doRender() {
    toast("جارٍ توليد الوثيقة...", "info");
    const res = await fetch("/api/generator/render", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ file, template: template || null, values }),
    });
    const payload = await res.json();
    if (!res.ok) throw new Error(payload.error || "تعذر التوليد");
    const win = window.open("", "_blank");
    if (!win) { toast("اسمح بالنوافذ المنبثقة للمعاينة", "warn"); return; }
    win.document.open();
    win.document.write(payload.preview);
    win.document.close();
    win.focus();
    setTimeout(() => { try { win.print(); } catch (_e) { /* طباعة يدوية */ } }, 400);
  }

  async function doDownload() {
    toast("جارٍ إنشاء ملف DOCX...", "info");
    const res = await fetch("/api/generator/download", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ file, template: template || null, values }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || "تعذر التوليد");
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = (data.title || "document").replace(/[\\/:*?"<>|]+/g, "_") + ".docx";
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 4000);
    toast("تم تنزيل المستند", "success");
  }

  const actions = el("div", { class: "flex gap-6 mt-8" }, [
    el("button", {
      class: "btn btn-primary",
      onclick: () => doRender().catch((e) => toast(e.message, "error")),
    }, [icon("eye", 16), " معاينة وطباعة"]),
    el("button", {
      class: "btn",
      onclick: () => doDownload().catch((e) => toast(e.message, "error")),
    }, [icon("download", 16), " تنزيل DOCX"]),
  ]);

  wrap.replaceChildren(titleRow);
  wrap.append(form);
  wrap.append(actions);
  wrap.append(el("p", {
    class: "small muted mt-8",
    text: "التنبيه: المحتوى يولّده الخادم من القالب الرسمي الأصلي. تحقق من بياناتك قبل اعتماد أي وثيقة قانونية، ولا توقّع إلا على نسخة مطابقة لأصلك.",
  }));
  return wrap;
}

export function generatorTemplateView() {
  const file = qs("file");
  if (!file) return el("div", { class: "card empty", text: "قالب غير محدد." });
  return openTemplate(file, qs("template"), false);
}

export function generatorDocView() {
  const file = qs("file");
  if (!file) return el("div", { class: "card empty", text: "وثيقة غير محددة." });
  return openTemplate(file, "", true);
}