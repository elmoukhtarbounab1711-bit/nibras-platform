// نبراس — إدارة القانون المقارن المستقل (لوحة الإدارة): دول + قوانين + اجتهادات + استيراد
import {
  el, api, t, badge, confirmDialog, toast,
  emptyState, skeleton, input, select, tabs,
} from "../ui.js";

export function compLibAdminView() {
  let active = "laws";
  const container = el("div", { class: "flex-col", style: "gap:16px" });

  function render() {
    container.replaceChildren(tabs([
      { key: "laws", label: "القوانين" },
      { key: "jurisprudence", label: "الاجتهادات" },
      { key: "courts", label: "المحاكم" },
      { key: "import", label: "الاستيراد" },
      { key: "stats", label: "الإحصائيات" },
    ], active, (k) => { active = k; render(); }));

    const panels = {
      laws: lawsPanel,
      jurisprudence: jurisprudencePanel,
      courts: courtsPanel,
      import: importPanel,
      stats: statsPanel,
    };
    const p = panels[active]();
    if (p && typeof p.then === "function") {
      p.then((node) => container.replaceChildren(
        container.children[0], node));
    } else {
      container.append(p);
    }
  }

  render();
  return container;
}

// ── Laws Panel ──────────────────────────────────────────────────
async function lawsPanel() {
  const box = el("div", { class: "flex-col", style: "gap:12px" });
  const countryS = select({}, [el("option", { value: "", text: "كل الدول" })]);
  try {
    const cData = await api.get("/api/comp/countries");
    for (const c of cData.countries || []) {
      countryS.append(el("option", { value: c.code, text: c.name }));
    }
  } catch { /* تجاهل */ }

  const tbody = el("tbody", {});

  async function draw() {
    tbody.replaceChildren(el("tr", {}, el("td", { colspan: 5 }, skeleton(2, 60))));
    const cc = countryS.value;
    let laws = [];
    if (cc) {
      const d = await api.get(`/api/comp/countries/${cc}/laws`);
      laws = d.laws || [];
    }
    tbody.replaceChildren(laws.length
      ? laws.map((l) => el("tr", {}, [
          el("td", { text: `#${l.id}` }),
          el("td", {}, [el("strong", { text: l.title })]),
          el("td", { text: l.country_code || "—" }),
          el("td", { text: l.category || "—" }),
          el("td", {}, [
            el("button", {
              class: "btn btn-danger btn-sm", text: "حذف",
              onclick: async () => {
                if (!(await confirmDialog({ title: "تأكيد الحذف", text: l.title }))) return;
                try {
                  await api.del(`/api/admin/comp/laws/${l.id}`);
                  toast("تم الحذف", "success");
                  draw();
                } catch (e) { toast(String(e?.message || e), "error"); }
              },
            }),
          ]),
        ]))
      : el("tr", {}, el("td", { colspan: 5 }, emptyState("لا قوانين"))));
  }

  countryS.onchange = draw;
  await draw();
  box.append(
    el("div", { class: "flex", style: "gap:8px;align-items:center" }, [
      el("label", { text: "الدولة:" }),
      countryS,
    ]),
    el("div", { class: "table-wrap" }, [
      el("table", { class: "adm-table" }, [
        el("thead", {}, el("tr", {}, [
          el("th", { text: "#" }),
          el("th", { text: "العنوان" }),
          el("th", { text: "الدولة" }),
          el("th", { text: "الفئة" }),
          el("th", { text: "إجراء" }),
        ])),
        tbody,
      ]),
    ]),
  );
  return box;
}

// ── Jurisprudence Panel ─────────────────────────────────────────
async function jurisprudencePanel() {
  const box = el("div", { class: "flex-col", style: "gap:12px" });
  const tbody = el("tbody", {});

  async function draw() {
    tbody.replaceChildren(el("tr", {}, el("td", { colspan: 4 }, skeleton(2, 60))));
    let decisions = [];
    for (const cc of ["france", "egypt"]) {
      try {
        const d = await api.get(`/api/comp/countries/${cc}/jurisprudence`);
        decisions = decisions.concat(d.decisions || []);
      } catch { /* تجاهل */ }
    }
    tbody.replaceChildren(decisions.length
      ? decisions.map((d) => el("tr", {}, [
          el("td", { text: `#${d.id}` }),
          el("td", {}, [el("strong", { text: d.title })]),
          el("td", { text: d.country_code || "—" }),
          el("td", {}, [
            el("button", {
              class: "btn btn-danger btn-sm", text: "حذف",
              onclick: async () => {
                if (!(await confirmDialog({ title: "تأكيد الحذف", text: d.title }))) return;
                try {
                  await api.del(`/api/admin/comp/jurisprudence/${d.id}`);
                  toast("تم الحذف", "success");
                  draw();
                } catch (e) { toast(String(e?.message || e), "error"); }
              },
            }),
          ]),
        ]))
      : el("tr", {}, el("td", { colspan: 4 }, emptyState("لا اجتهادات"))));
  }

  await draw();
  box.append(el("div", { class: "table-wrap" }, [
    el("table", { class: "adm-table" }, [
      el("thead", {}, el("tr", {}, [
        el("th", { text: "#" }),
        el("th", { text: "العنوان" }),
        el("th", { text: "الدولة" }),
        el("th", { text: "إجراء" }),
      ])),
      tbody,
    ]),
  ]));
  return box;
}

// ── Courts Panel ────────────────────────────────────────────────
async function courtsPanel() {
  const box = el("div", { class: "flex-col", style: "gap:12px" });
  const tbody = el("tbody", {});

  async function draw() {
    tbody.replaceChildren(el("tr", {}, el("td", { colspan: 4 }, skeleton(2, 60))));
    let courts = [];
    for (const cc of ["france", "egypt"]) {
      try {
        const d = await api.get(`/api/comp/countries/${cc}/courts`);
        courts = courts.concat(d.courts || []);
      } catch { /* تجاهل */ }
    }
    tbody.replaceChildren(courts.length
      ? courts.map((c) => el("tr", {}, [
          el("td", { text: `#${c.id}` }),
          el("td", {}, [el("strong", { text: c.name })]),
          el("td", { text: c.name_ar || "—" }),
          el("td", {}, [
            el("button", {
              class: "btn btn-danger btn-sm", text: "حذف",
              onclick: async () => {
                if (!(await confirmDialog({ title: "تأكيد الحذف", text: c.name }))) return;
                try {
                  await api.del(`/api/admin/comp/courts/${c.id}`);
                  toast("تم الحذف", "success");
                  draw();
                } catch (e) { toast(String(e?.message || e), "error"); }
              },
            }),
          ]),
        ]))
      : el("tr", {}, el("td", { colspan: 4 }, emptyState("لا محاكم"))));
  }

  await draw();
  box.append(el("div", { class: "table-wrap" }, [
    el("table", { class: "adm-table" }, [
      el("thead", {}, el("tr", {}, [
        el("th", { text: "#" }),
        el("th", { text: "الاسم" }),
        el("th", { text: "الاسم بالعربية" }),
        el("th", { text: "إجراء" }),
      ])),
      tbody,
    ]),
  ]));
  return box;
}

// ── Import Panel ────────────────────────────────────────────────
async function importPanel() {
  const box = el("div", { class: "flex-col", style: "gap:12px" });

  const statusEl = el("div", { class: "card", style: "padding:1rem", text: "جاري التحميل..." });

  async function loadRuns() {
    try {
      const d = await api.get("/api/admin/comp/import/runs");
      const runs = d.runs || [];
      statusEl.replaceChildren(runs.length
        ? el("table", { class: "adm-table" }, [
            el("thead", {}, el("tr", {}, [
              el("th", { text: "#" }), el("th", { text: "الدولة" }),
              el("th", { text: "الحالة" }), el("th", { text: "المستوردة" }),
              el("th", { text: "التاريخ" }),
            ])),
            el("tbody", {}, runs.map((r) => el("tr", {}, [
              el("td", { text: `#${r.id}` }),
              el("td", { text: r.country_code }),
              el("td", {}, [badge(r.status, r.status === "completed" ? "green" : "gray")]),
              el("td", { text: `${r.docs_imported}/${r.docs_found}` }),
              el("td", { text: r.started_at || "—" }),
            ]))),
          ])
        : emptyState("لا جلسات استيراد"));
    } catch (e) {
      statusEl.replaceChildren(el("div", { text: `خطأ: ${e.message}` }));
    }
  }

  const runBtn = el("button", {
    class: "btn btn-primary", text: "استيراد قرارات المجلس الدستوري",
    onclick: async () => {
      runBtn.disabled = true;
      runBtn.textContent = "جاري الاستيراد...";
      try {
        const r = await api.post("/api/admin/comp/import/run", {
          country_code: "france", dataset: "constitu",
        });
        toast(`تم: ${r.imported} قرار مستورد`, "success");
        loadRuns();
      } catch (e) {
        toast(String(e?.message || e), "error");
      }
      runBtn.disabled = false;
      runBtn.textContent = "استيراد قرارات المجلس الدستوري";
    },
  });

  const cassBtn = el("button", {
    class: "btn btn-outline", text: "استيراد قرارات محكمة النقض",
    onclick: async () => {
      cassBtn.disabled = true;
      cassBtn.textContent = "جاري الاستيراد...";
      try {
        const r = await api.post("/api/admin/comp/import/run", {
          country_code: "france", dataset: "cass",
        });
        toast(`تم: ${r.imported} قرار مستورد`, "success");
        loadRuns();
      } catch (e) {
        toast(String(e?.message || e), "error");
      }
      cassBtn.disabled = false;
      cassBtn.textContent = "استيراد قرارات محكمة النقض";
    },
  });

  await loadRuns();
  box.append(
    el("div", { class: "flex", style: "gap:8px" }, [runBtn, cassBtn]),
    statusEl,
  );
  return box;
}

// ── Stats Panel ─────────────────────────────────────────────────
async function statsPanel() {
  const stats = await api.get("/api/comp/stats");
  const items = [
    { label: "الدول", value: stats.countries },
    { label: "القوانين", value: stats.laws },
    { label: "المواد", value: stats.articles },
    { label: "المحاكم", value: stats.courts },
    { label: "الاجتهادات", value: stats.decisions },
  ];
  return el("div", { class: "grid grid-3" }, items.map((item) =>
    el("div", { class: "card", style: "padding:1.5rem;text-align:center" }, [
      el("div", { style: "font-size:2rem;font-weight:700", text: String(item.value) }),
      el("div", { class: "text-muted", text: item.label }),
    ])
  ));
}
