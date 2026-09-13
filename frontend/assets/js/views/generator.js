// نبراس — مولد الوثائق والعقود: مكتبة قوالب + تعبئة + معاينة + تنزيل DOCX
// نسخة احترافية: مسودات محفوظة، المبلغ كتابةً، مجموعات، تحقق فوري، معاينة الأصل.
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

function fmtFields(n) {
  if (!n) return "";
  return n === 1 ? "حقل واحد" : n <= 10 ? `${n} حقول` : `${n} حقلًا`;
}

const TYPE_LABELS = {
  text: "نص",
  textarea: "نص طويل",
  date: "تاريخ",
  money: "مبلغ",
  number: "رقم",
};

const TYPE_HINTS = {
  money: "أدخل المبلغ بالأرقام فقط — يمكنك كتابة الفواصل: 15000 أو 15.000 أو 15000.50",
  number: "أدخل القيمة بالأرقام فقط",
  date: "اختر التاريخ، أو اتركه فارغًا إن لم يكن مطلوبًا",
};

function isRequired(f) {
  if (f.required === true) return true;
  if (f.required === false) return false;
  return f.type !== "date";
}

// ---------------------------------------------------------------------------
// المسودات المحفوظة (localStorage لكل وثيقة)
// ---------------------------------------------------------------------------

const DRAFT_PREFIX = "gen:draft:";

function draftKey(file) {
  return DRAFT_PREFIX + file;
}

function loadDraft(file) {
  try {
    const raw = localStorage.getItem(draftKey(file));
    if (!raw) return null;
    const d = JSON.parse(raw);
    return d && typeof d === "object" ? d : null;
  } catch (_e) {
    return null;
  }
}

function saveDraft(file, payload) {
  try {
    localStorage.setItem(draftKey(file), JSON.stringify(payload));
  } catch (_e) {
    /* مساحة التخزين ممتلئة — نتجاهل */
  }
}

function clearDraft(file) {
  try {
    localStorage.removeItem(draftKey(file));
  } catch (_e) {
    /* ignore */
  }
}

// ---------------------------------------------------------------------------
// الصفحة الرئيسية: كيف يعمل + قوالب موصى بها + تصفح المكتبة
// ---------------------------------------------------------------------------

export async function generatorView() {
  const wrap = el("div", { class: "flex-col" });

  const head = el("div", { class: "section-head" }, [
    el("div", {}, [
      el("h2", { text: "مولد الوثائق والعقود" }),
      el("p", { class: "small muted", text: "قوالب وثائق مغربية جاهزة — عبِّئ هي فقط وعاين، ثم اطبع أو نزّل نسخة Word" }),
    ]),
  ]);
  wrap.append(head);

  wrap.append(el("div", { class: "gen-steps" }, [
    el("div", { class: "gen-step" }, [
      el("span", { class: "gen-step-num", text: "1" }),
      el("div", {}, [
        el("strong", { text: "اختر الوثيقة" }),
        el("p", { class: "small muted", text: "من القوالب الموصى بها أو ابحث في مكتبة الوثائق" }),
      ]),
    ]),
    el("div", { class: "gen-step" }, [
      el("span", { class: "gen-step-num", text: "2" }),
      el("div", {}, [
        el("strong", { text: "عبِّئ البيانات" }),
        el("p", { class: "small muted", text: "فقط الحقول المطلوبة في العقد — مع شرح لكل حقل، وتُحفظ المسودة تلقائيًا" }),
      ]),
    ]),
    el("div", { class: "gen-step" }, [
      el("span", { class: "gen-step-num", text: "3" }),
      el("div", {}, [
        el("strong", { text: "عاين، اطبع أو نزّل" }),
        el("p", { class: "small muted", text: "راجع المعاينة (المبلغ كتابةً تلقائيًا) ثم اطبع أو نزّل Word" }),
      ]),
    ]),
  ]));

  wrap.append(skeleton(3, 90));

  const [tplData, catalog] = await Promise.all([
    api.get("/api/generator/templates").catch(() => ({ templates: [] })),
    api.get("/api/generator/catalog").catch(() => ({ categories: [], docs: [] })),
  ]);

  const templates = (tplData.templates || []).filter((t) => t && t.file);
  const cats = catalog.categories || [];
  const docs = catalog.docs || [];
  const total = docs.length;
  const fillableCount = docs.filter((d) => d.fillable).length;

  if (!total) {
    wrap.replaceChildren(head);
    wrap.append(emptyState("لم تُرمَّز مكتبة الوثائق في هذا الخادم بعد.", "folder"));
    return wrap;
  }

  // --- القوالب الموصى بها
  if (templates.length) {
    const tGrid = el("div", { class: "flex-col mt-8" });
    const cards = el("div", { class: "grid-2" });
    templates.slice(0, 10).forEach((t) => {
      const go = () => navigate(`/generator/template?template=${encodeURIComponent(t.id)}&file=${fileParam(t.file)}`);
      const badge = t.field_count
        ? el("span", { class: "badge badge-green", text: `${fmtFields(t.field_count)} للتعبئة` })
        : null;
      cards.append(el("div", { class: "card flex-between gen-card", role: "link", tabindex: "0", onclick: go, onkeydown: (e) => { if (e.key === "Enter") go(); } }, [
        el("div", {}, [
          el("span", { class: "badge", text: t.category }),
          ...(badge ? [badge] : []),
          el("div", { class: "mt-4" }, [el("strong", { text: t.title })]),
          el("p", { class: "small muted mt-4", text: t.description || "" }),
        ]),
        el("button", {
          class: "btn btn-sm btn-primary",
          onclick: (e) => { e.stopPropagation(); go(); },
        }, [icon("pen", 16), " عبّئ القالب"]),
      ]));
    });
    tGrid.append(el("div", { class: "section-head mt-24" }, [
      el("h3", { text: "قوالب موصى بها" }),
      el("span", { class: "small muted", text: `من أصل ${total} وثيقة في المكتبة` }),
    ]));
    tGrid.append(cards);
    wrap.append(tGrid);
  }

  // --- تصفح المكتبة
  const searchInput = el("input", {
    class: "input", type: "search",
    placeholder: `ابحث في ${total} وثيقة... (وكالة، عقد كراء، شكاية، تنازل...)`,
  });
  const status = el("span", {
    class: "small muted",
    text: `${total} وثيقة · ${fillableCount} منها قابلة للتعبئة`,
  });
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
      const go = () => navigate(`/generator/doc?file=${fileParam(d.file)}`);
      const row = el("div", {
        class: "card flex-between" + (d.fillable ? " gen-card" : ""),
        role: d.fillable ? "link" : undefined,
        tabindex: d.fillable ? "0" : undefined,
        onclick: d.fillable ? go : null,
        onkeydown: d.fillable ? (e) => { if (e.key === "Enter") go(); } : null,
      }, [
        el("div", {}, [
          el("div", { class: "flex-wrap" }, [
            el("span", { class: "badge", text: d.category }),
            el("span", { class: "badge muted", text: d.ext || "doc" }),
            el("span", { class: "small muted", text: fmtSize(d.size) }),
          ]),
          el("strong", { class: "mt-4", style: "display:block", text: d.title }),
          el("p", { class: "small mt-4", text: d.fillable ? "قابل للتعبئة مباشرة" : "تنزيل الأصل فقط" }),
        ]),
        el("div", { class: "flex" }, [
          el("a", {
            class: "btn btn-ghost btn-sm",
            href: `/api/generator/file?file=${fileParam(d.file)}`,
            onclick: (e) => { e.stopPropagation(); },
          }, [icon("download", 14), " الأصلي"]),
          d.fillable
            ? el("button", {
                class: "btn btn-sm btn-primary",
                onclick: (e) => { e.stopPropagation(); go(); },
              }, [icon("pen", 14), " عبّئ"])
            : null,
        ]),
      ]);
      listEl.append(row);
    });
  }

  const chipRow = el("div", { class: "flex-wrap mt-8" });
  function setChips(target) {
    chipRow.querySelectorAll(".chip.active").forEach((c) => c.classList.remove("active"));
    target.classList.add("active");
  }
  chipRow.append(el("button", {
    class: "chip active", text: tr("all"),
    onclick: (e) => { activeCat = ""; setChips(e.currentTarget); renderLibrary(); },
  }));
  cats.slice().sort((a, b) => (b.count || 0) - (a.count || 0)).forEach((c) => {
    chipRow.append(el("button", {
      class: "chip", text: `${c.name} (${c.count})`,
      onclick: (e) => { activeCat = c.slug; setChips(e.currentTarget); renderLibrary(); },
    }));
  });
  searchInput.addEventListener("input", renderLibrary);

  wrap.append(el("div", { class: "section-head mt-24" }, [
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

const NUMERIC_RE = /^[\d\s.,]+$/;

function numericError(raw) {
  const v = String(raw || "").trim();
  if (!v) return "";
  if (!NUMERIC_RE.test(v)) return "أدخل رقماً فقط (بدون حروف أو رموز).";
  return "";
}

function inputFor(field, value) {
  const set = (val) => { value[field.key] = val; };
  if (field.type === "textarea") {
    return el("textarea", { class: "input", rows: 3, placeholder: "اكتب هنا...", oninput: (e) => set(e.target.value) });
  }
  if (field.type === "date") {
    return el("input", { class: "input", type: "date", onchange: (e) => set(e.target.value) });
  }
  if (field.type === "money") {
    return el("input", { class: "input", type: "text", inputmode: "decimal", dir: "ltr",
      placeholder: "مثال: 15000", oninput: (e) => set(e.target.value) });
  }
  if (field.type === "number") {
    return el("input", { class: "input", type: "text", inputmode: "numeric", dir: "ltr",
      placeholder: "مثال: 12345", oninput: (e) => set(e.target.value) });
  }
  return el("input", { class: "input", type: "text", placeholder: "اكتب هنا...", oninput: (e) => set(e.target.value) });
}

async function openTemplate(file, template, editable) {
  const wrap = el("div", { class: "flex-col" });
  wrap.append(skeleton(4, 90));
  let data;
  try {
    const qsParam = template ? `template=${encodeURIComponent(template)}&file=${fileParam(file)}` : `file=${fileParam(file)}`;
    data = await api.get(`/api/generator/fields?${qsParam}`);
  } catch (e) {
    wrap.replaceChildren(el("div", { class: "card empty" }, [
      el("div", { class: "empty-icon" }, [icon("alertTriangle", 40)]),
      el("div", { text: e.message }),
    ]));
    return wrap;
  }

  const fields = data.fields || [];
  const values = {};

  // --- استرجاع المسودة المحفوظة (قيم + خيار المبلغ)
  const draft = loadDraft(file);
  const moneyState = {
    add: draft && draft.money && draft.money.add === false ? false : true,
    lang: draft && draft.money && draft.money.lang === "fr" ? "fr" : "ar",
  };
  const draftValues = (draft && draft.values) || {};

  let saveTimer = null;
  function scheduleSave() {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(() => {
      saveDraft(file, { values: collect(), money: moneyState });
    }, 350);
  }

  const titleRow = el("div", { class: "section-head" }, [
    el("div", {}, [
      el("button", { class: "btn btn-ghost btn-sm", onclick: () => navigate("/generator") }, [icon("arrowLeft", 16), " " + tr("back")]),
      el("h2", { class: "mt-4", text: data.title }),
      el("p", {
        class: "small muted mt-4",
        text: editable
          ? "استخرِجت الحقول تلقائيًا من فراغات القالب الأصلي — عدّل تسمية أي حقل أو نوعه إن لزم، ثم عبِّئ البيانات."
          : "عبِّئ الحقول أدناه (الحقول المعلَّمة بـ * مطلوبة)، ثم عاين المستند واطبعه أو نزّله.",
      }),
    ]),
  ]);
  if (draft) {
    const draftNote = el("p", { class: "small gen-draft-note mt-4" }, [
      icon("clipboard", 14),
      " استُعيدت تعبئتك المحفوظة من جلسة سابقة — راجعها أو امسحها بخيار «محو المسودة».",
    ]);
    titleRow.querySelector(".section-head > div").append(draftNote);
  }

  const form = el("div", { class: "card mt-8 flex-col" });
  const invalid = new Set();
  const moneyLiveRefresh = [];

  let currentGroup = "";
  fields.forEach((f) => {
    if (f.group && f.group !== currentGroup) {
      currentGroup = f.group;
      form.append(el("div", { class: "gen-section mt-16" }, [
        el("span", { class: "gen-section-title", text: f.group }),
      ]));
    }
    const labelRow = editable
      ? el("input", { class: "input", value: f.label || f.key, oninput: (e) => { f.label = e.target.value; } })
      : el("span", {}, [
          el("span", { text: f.label || f.key }),
          ...(isRequired(f) ? [el("span", { class: "gen-required" })] : [el("span", { class: "gen-opt", text: " اختياري" })]),
        ]);
    const typeNode = editable
      ? el("select", { class: "input gen-lang", onchange: (e) => { f.type = e.target.value; } },
          ["text", "textarea", "date", "money", "number"].map((t) =>
            el("option", { value: t, text: t, selected: f.type === t })))
      : null;
    const hint = !editable && TYPE_HINTS[f.type] ? el("span", { class: "field-help", text: TYPE_HINTS[f.type] }) : null;
    const row = el("div", { class: "field mb-8", "data-key": f.key }, [el("label", {}, [labelRow])]);
    if (typeNode) row.append(typeNode);

    const input = inputFor(f, values);
    const initVal = draftValues[f.key];
    if (initVal != null) input.value = String(initVal);
    row.append(input);

    if (initVal != null) values[f.key] = String(initVal);
    const errNode = el("span", { class: "field-error", text: "" });
    row.append(errNode);
    if (hint) row.append(hint);

    // المبلغ كتابةً حي (يُحدَّث مع كل إدخال/تغيير لغة)
    if (f.type === "money" && !editable) {
      const live = el("span", { class: "field-help money-live", text: "" });
      row.append(live);
      moneyLiveRefresh.push(refreshLive);
      function refreshLive() {
        const raw = String(values[f.key] || "").trim();
        if (!raw || !/\d/.test(raw)) { live.textContent = ""; return; }
        clearTimeout(pathTimer);
        pathTimer = setTimeout(async () => {
          try {
            const res = await fetch(
              `/api/generator/amount?value=${encodeURIComponent(raw)}&lang=${moneyState.lang}`);
            const p = await res.json();
            if (!res.ok || p.error) { live.textContent = ""; return; }
            live.textContent = moneyState.lang === "fr" ? p.line_fr : p.line_ar;
          } catch (_err) {
            live.textContent = "";
          }
        }, 300);
      }
      let pathTimer = null;
      input.addEventListener("input", refreshLive);
    }

    // حفظ تلقائي للمسودة مع كل تغيير
    input.addEventListener("input", scheduleSave);
    input.addEventListener("change", scheduleSave);
    input.addEventListener("input", () => {
      errNode.textContent = "";
      row.classList.remove("field-invalid");
    });

    form.append(row);
  });

  // --- بطاقة خيار «المبلغ كتابةً»
  const moneyToggle = el("input", { type: "checkbox", checked: moneyState.add });
  const moneyLangSel = el("select", { class: "input gen-lang" }, [
    el("option", { value: "ar", text: "عربية", selected: moneyState.lang === "ar" }),
    el("option", { value: "fr", text: "Français", selected: moneyState.lang === "fr" }),
  ]);
  moneyToggle.onclick = () => { moneyState.add = moneyToggle.checked; scheduleSave(); };
  moneyLangSel.onchange = () => {
    moneyState.lang = moneyLangSel.value;
    moneyLiveRefresh.forEach((fn) => fn());
    scheduleSave();
  };
  const moneyCard = el("div", { class: "card mt-8 gen-money" }, [
    el("div", { class: "flex-between flex-wrap gap-8" }, [
      el("label", { class: "flex gap-8", style: "align-items:center" }, [
        moneyToggle,
        el("span", { text: "أضف «المبلغ كتابةً» (حروفًا ورقمًا) تلقائيًا بعد كل مبلغ" }),
      ]),
      moneyLangSel,
    ]),
    el("p", { class: "small muted mt-4", text: "مثال: 1500 ← تُدرج «المبلغ كتابةً: ألف وخمسمائة درهم» في الوثيقة والمعاينة." }),
  ]);

  function validate() {
    invalid.clear();
    fields.forEach((f) => {
      const raw = String(values[f.key] || "").trim();
      const row = form.querySelector(`[data-key="${f.key}"]`);
      const errNode = row ? row.querySelector(".field-error") : null;
      let msg = "";
      if (isRequired(f) && !raw) msg = "هذا الحقل مطلوب.";
      else if ((f.type === "money" || f.type === "number") && raw) msg = numericError(raw);
      if (msg) {
        invalid.add(f.key);
        if (errNode) errNode.textContent = msg;
        if (row) row.classList.add("field-invalid");
      } else {
        if (errNode) errNode.textContent = "";
        if (row) row.classList.remove("field-invalid");
      }
    });
    if (invalid.size) {
      const first = fields.find((f) => invalid.has(f.key));
      const firstRow = first ? form.querySelector(`[data-key="${first.key}"]`) : null;
      if (firstRow) firstRow.scrollIntoView({ behavior: "smooth", block: "center" });
    }
    return invalid.size;
  }

  function collect() {
    return fields.reduce((acc, f) => {
      if (String(values[f.key] || "").trim()) acc[f.key] = String(values[f.key]).trim();
      return acc;
    }, {});
  }

  const busy = { on: false };
  function setBusy(btnSet, on) {
    busy.on = on;
    btnSet.forEach(([btn, label]) => {
      btn.disabled = on;
      btn.setAttribute("data-label", label);
      btn.lastChild.textContent = on ? " جارٍ..." : (" " + label);
    });
  }

  // --- المعاينة داخل الصفحة (iframe معزول بدون نوافذ منبثقة)
  const previewBox = el("div", { class: "gen-preview-wrap flex-col", style: "display:none" });
  const previewIframe = el("iframe", {
    class: "gen-preview",
    sandbox: "allow-modals",
    title: "معاينة المستند",
  });
  const previewNote = el("p", {
    class: "small muted",
    text: "هذه معاينة مطابقة للقالب ببياناتك — راجعها جيدًا قبل الطباعة أو التوقيع. لا يوقَّع على نسخة إلا إذا طابقت أصل العقد.",
  });

  function printPreview() {
    try {
      const w = previewIframe.contentWindow;
      if (!w) throw new Error();
      w.focus();
      w.print();
    } catch (_e) {
      toast("الطباعة لم تُنفَّذ تلقائيًا — افتح المعاينة واطبع من المتصفح.", "warn");
    }
  }

  async function doRender(btn, opts) {
    opts = opts || {};
    if (busy.on) return;
    if (!opts.original) {
      const missing = validate();
      if (missing) {
        toast(`أكمل الحقول الناقصة (${missing}) أولًا.`, "error");
        return;
      }
    }
    setBusy([[btns.render, "عاين الآن"]], true);
    toast(opts.original ? "جارٍ عرض القالب الأصلي..." : "جارٍ توليد المستند...", "info");
    try {
      const res = await fetch("/api/generator/render", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          file,
          template: template || null,
          values: opts.original ? {} : collect(),
          money: { add: moneyState.add, lang: moneyState.lang },
          original: !!opts.original,
        }),
      });
      const payload = await res.json();
      if (!res.ok) throw new Error(payload.error || "تعذر توليد المستند");
      previewIframe.setAttribute("srcdoc", payload.preview);
      previewBox.style.display = "";
      previewBox.scrollIntoView({ behavior: "smooth", block: "nearest" });
      toast(opts.original ? "عرض أصل القالب (قبل التعبئة)." : "تم إنشاء المعاينة بنجاح.", "success");
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setBusy([[btns.render, "عاين الآن"]], false);
    }
  }

  async function doDownload(btn) {
    if (busy.on) return;
    const missing = validate();
    if (missing) {
      toast(`أكمل الحقول الناقصة (${missing}) أولًا.`, "error");
      return;
    }
    setBusy([[btns.download, "نزّل Word"]], true);
    toast("جارٍ إنشاء ملف Word...", "info");
    try {
      const res = await fetch("/api/generator/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          file,
          template: template || null,
          values: collect(),
          money: { add: moneyState.add, lang: moneyState.lang },
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || "تعذر إنشاء الملف");
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = (data.title || "document").replace(/[\\/:*?"<>|]+/g, "_") + ".docx";
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 4000);
      toast("تم تنزيل المستند بنجاح.", "success");
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setBusy([[btns.download, "نزّل Word"]], false);
    }
  }

  function clearFields() {
    form.querySelectorAll("input, textarea, select").forEach((inp) => {
      if (inp.type === "date") inp.value = "";
      else if (inp.tagName === "INPUT") inp.value = "";
      else if (inp.tagName === "TEXTAREA") inp.value = "";
    });
    fields.forEach((f) => { delete values[f.key]; });
    form.querySelectorAll(".field-invalid").forEach((r) => r.classList.remove("field-invalid"));
    form.querySelectorAll(".field-error").forEach((n) => { n.textContent = ""; });
    previewBox.style.display = "none";
    clearDraft(file);
    moneyLiveRefresh.forEach((fn) => fn());
    toast("تم مسح الحقول والمسودة.", "info");
  }

  const btns = {};
  btns.render = el("button", { class: "btn btn-primary" }, [icon("eye", 16), " عاين الآن"]);
  btns.download = el("button", { class: "btn" }, [icon("download", 16), " نزّل Word"]);
  const origBtn = el("button", { class: "btn btn-ghost" }, [icon("fileText", 15), " عاين الأصل"]);
  const clearBtn = el("button", { class: "btn btn-ghost" }, [icon("trash", 15), " محو المسودة"]);
  clearBtn.title = "يمسح الحقول والمسودة المحفوظة لهذه الوثيقة";
  btns.render.onclick = () => doRender(btns.render);
  btns.download.onclick = () => doDownload(btns.download);
  origBtn.onclick = () => doRender(btns.render, { original: true });
  clearBtn.onclick = clearFields;

  const actions = el("div", { class: "flex-between mt-16 flex-wrap gap-8" }, [btns.render, btns.download, origBtn, clearBtn]);

  previewBox.append(
    el("div", { class: "section-head" }, [
      el("div", {}, [el("h3", { text: "معاينة المستند" })]),
      el("div", { class: "flex" }, [
        el("button", { class: "btn btn-sm btn-primary", onclick: printPreview }, [icon("send", 14), " اطبع"]),
        el("button", { class: "btn btn-sm", onclick: () => { previewBox.style.display = "none"; } }, [icon("x", 14), " إخفاء"]),
      ]),
    ]),
    previewIframe,
    previewNote,
  );

  wrap.replaceChildren(titleRow);
  wrap.append(form);
  wrap.append(moneyCard);
  wrap.append(actions);
  wrap.append(previewBox);
  wrap.append(el("p", {
    class: "small muted mt-24",
    html: esc("تنبيه قانوني: المحتوى يولّده الخادم من القالب الرسمي الأصلي. تحقق من بياناتك قبل اعتماد أي وثيقة، ولا توقّع إلا على نسخة مطابقة لأصلك. قد تحتاج بعض العقود إلى الختم الرسمي أو التوثيق."),
  }));

  if (draft) toast("استُعيدت مسودتك المحفوظة لهذه الوثيقة.", "info");

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