// نبراس — تعلم اللغة القانونية (FR/EN/ES)
import { tr, currentLang } from "../i18n.js";
import { api, session } from "../api.js";
import { el, emptyState, toast } from "../ui.js";
import { icon, iconHTML } from "../icons.js";
import { navigate } from "../router.js";

/* ── helpers ─────────────────────────────────────────────────────────── */
const esc = (s) => { const d = document.createElement("div"); d.textContent = s; return d.innerHTML; };

function getLang() {
  const h = location.hash;
  const m = h.match(/lang=(\w+)/);
  return m ? m[1] : "fr";
}

const LANG_META = {
  fr: { flag: "\u{1F1EB}\u{1F1F7}", label: "Fran\u00e7ais juridique", labelAr: "الفرنسية القانونية", color: "#2563eb" },
  en: { flag: "\u{1F1EC}\u{1F1E7}", label: "English legal", labelAr: "الإنجليزية القانونية", color: "#059669" },
  es: { flag: "\u{1F1EA}\u{1F1F8}", label: "Espa\u00f1ol jur\u00eddico", labelAr: "الإسبانية القانونية", color: "#d97706" },
};

/* ── Main Dashboard ──────────────────────────────────────────────────── */
export async function legalFrenchView() {
  const lang = getLang();
  const langInfo = LANG_META[lang] || LANG_META.fr;

  let languages = [];
  try {
    const resp = await api.get("/api/legal-french/languages");
    languages = resp.languages || [];
  } catch { /* fallback */ }

  const section = el("div", {});

  /* Hero */
  section.append(el("section", { class: "lib-hero" }, [
    el("div", { class: "hero-bg" }),
    el("span", { class: "hero-crown" }, [icon("book-open", 30)]),
    el("span", { class: "hero-eyebrow" }, [icon("book-open", 15), "اللغة القانونية"]),
    el("h1", { text: "Droit & Langue \u2014 تعلم اللغة القانونية" }),
    el("p", { class: "hero-sub", text: "من المبتدئ إلى المحترف: دروس تفاعلية في اللغة والقواعد القانونية" }),
  ]));

  /* Language selector — stat-chips */
  const langSection = el("section", { class: "content-section" });
  langSection.append(el("div", { class: "section-head" }, [
    el("div", {}, [
      el("div", { class: "eyebrow", text: tr("libCategoriesTitle") || "اللغات" }),
      el("h2", { text: "اختر اللغة القانونية" }),
    ]),
  ]));

  const langGrid = el("div", { class: "grid grid-3", style: "margin-bottom:1.5rem" });
  for (const lg of languages) {
    const meta = LANG_META[lg.code] || LANG_META.fr;
    const active = lg.code === lang;
    langGrid.append(el("button", {
      class: `tile-card card-hover${active ? " active" : ""}`,
      style: `cursor:pointer;padding:1.5rem;text-align:center;border:2px solid ${active ? meta.color : "var(--line,#e5e7eb)"};transition:border-color .2s`,
      onclick: () => navigate(`/legal-french?lang=${lg.code}`),
    }, [
      el("div", { style: "font-size:2.2rem;margin-bottom:0.3rem", text: lg.flag }),
      el("h3", { class: "t-title", text: lg.title }),
      el("div", { class: "t-sub", text: lg.title_ar }),
      el("div", { class: "t-sub", style: "margin-top:auto" }, [
        el("span", { text: `${lg.level_count} مستويات` }),
        el("span", { text: " · " }),
        el("span", { text: `${lg.lesson_count} دروس` }),
      ]),
    ]));
  }
  langSection.append(langGrid);
  section.append(langSection);

  /* Stats */
  if (session.token) {
    try {
      const stats = await api.get(`/api/legal-french/stats?lang=${lang}`);
      const statsSection = el("section", { class: "content-section" });
      statsSection.append(el("div", { class: "section-head" }, [
        el("div", {}, [
          el("div", { class: "eyebrow", text: "الإحصائيات" }),
          el("h2", { text: "تقدمك في اللغة القانونية" }),
        ]),
      ]));
      statsSection.append(el("div", { class: "stats-row" }, [
        [stats.completed_lessons, "checkCircle", "دروس مكتملة"],
        [stats.total_lessons, "book", "إجمالي الدروس"],
        [`${stats.completion_pct}%`, "trendingUp", "نسبة الإتمام"],
        [stats.total_score, "star", "مجموع النقاط"],
      ].map(([n, ic, lbl]) => el("div", { class: "stat-chip" }, [
        el("div", { class: "sc-icon" }, [icon(ic, 22)]),
        el("div", { style: "line-height:1.25" }, [
          el("div", { class: "sc-num", text: String(n) }),
          el("div", { class: "sc-lbl", text: lbl }),
        ]),
      ]))));
      section.append(statsSection);
    } catch { /* guest */ }
  }

  /* Levels */
  const { levels } = await api.get(`/api/legal-french/levels?lang=${lang}`);
  const levelsSection = el("section", { class: "content-section" });
  levelsSection.append(el("div", { class: "section-head" }, [
    el("div", {}, [
      el("div", { class: "eyebrow", text: "المستويات" }),
      el("h2", { text: "المستويات التعليمية" }),
    ]),
  ]));
  levelsSection.append(el("div", { class: "tile-grid" }, levels.map((lv) => el("article", {
    class: "tile-card card-hover",
    style: "cursor:pointer",
    onclick: () => navigate(`/legal-french/${lv.id}?lang=${lang}`),
  }, [
    el("div", { class: "t-tag" }, [
      el("span", {
        class: "badge-pill",
        style: `background:${lv.color}20;color:${lv.color};font-size:0.75rem;padding:0.2rem 0.6rem`,
        text: `المستوى ${lv.id}`,
      }),
    ]),
    el("h3", { class: "t-title", text: lv.title }),
    el("p", { class: "t-sub", text: lv.description }),
    el("div", { class: "t-sub", style: "margin-top:auto" }, [
      el("span", { text: `${lv.unit_count} وحدات` }),
      el("span", { text: " · " }),
      el("span", { text: `${lv.lesson_count} دروس` }),
    ]),
    el("button", {
      class: "btn btn-primary btn-sm",
      style: "margin-top:0.5rem",
      text: "ابدأ التعلم",
      onclick: (e) => { e.stopPropagation(); navigate(`/legal-french/${lv.id}?lang=${lang}`); },
    }),
  ]))));
  section.append(levelsSection);

  /* Roadmap */
  const roadmapSection = el("section", { class: "content-section" });
  roadmapSection.append(el("div", { class: "section-head" }, [
    el("div", {}, [
      el("div", { class: "eyebrow", text: "خارطة الطريق" }),
      el("h2", { text: "المسار التعليمي" }),
    ]),
  ]));
  const roadRow = el("div", { class: "stats-row" }, [
    ["fr", "\u{1F1EB}\u{1F1F7}", "الفرنسية القانونية", "#2563eb"],
    ["en", "\u{1F1EC}\u{1F1E7}", "الإنجليزية القانونية", "#059669"],
    ["es", "\u{1F1EA}\u{1F1F8}", "الإسبانية القانونية", "#d97706"],
  ].map(([code, flag, label, color]) => el("div", {
    class: "stat-chip",
    style: `cursor:pointer;border:2px solid ${code === lang ? color : "transparent"};background:${code === lang ? color + "10" : "var(--surface)"};border-radius:var(--radius-sm)`,
    onclick: () => navigate(`/legal-french?lang=${code}`),
  }, [
    el("div", { style: "font-size:1.5rem" }, [document.createTextNode(flag)]),
    el("div", { style: "line-height:1.25" }, [
      el("div", { class: "sc-num", text: label }),
    ]),
  ])));
  roadmapSection.append(roadRow);
  section.append(roadmapSection);

  /* Treaties link — card style */
  const treatySection = el("section", { class: "content-section" });
  treatySection.append(el("div", { class: "section-head" }, [
    el("div", {}, [
      el("div", { class: "eyebrow", text: "نصوص واتفاقيات" }),
      el("h2", { text: "النصوص القانونية والاتفاقيات الدولية" }),
    ]),
  ]));
  treatySection.append(el("div", { class: "grid grid-3" }, [
    el("article", {
      class: "law-card card-hover",
      style: "cursor:pointer",
      onclick: () => navigate(`/legal-french/treaties?lang=${lang}`),
    }, [
      el("div", { class: "law-ic" }, [icon("file", 20)]),
      el("div", { class: "law-body" }, [
        el("div", { class: "flex-between mb-8" }, [
          el("span", { class: "badge-pill badge-navy", text: "نصوص" }),
        ]),
        el("h3", { class: "card-title", text: "النصوص والاتفاقيات" }),
        el("p", { class: "small muted", text: "تصفح النصوص القانونية الأصيلة والاتفاقيات الدولية بعدة لغات" }),
        el("div", { class: "flex-between mt-8" }, [
          el("span", { class: "small muted", text: "FR · EN · ES · AR" }),
          el("button", { class: "btn btn-primary btn-sm", text: "تصفح" }),
        ]),
      ]),
    ]),
  ]));
  section.append(treatySection);

  return section;
}

/* ── Level View ──────────────────────────────────────────────────────── */
export async function legalFrenchLevelView(params) {
  const levelId = parseInt(params.id, 10);
  const lang = getLang();

  let level;
  try {
    level = await api.get(`/api/legal-french/levels/${levelId}?lang=${lang}`);
  } catch {
    return el("div", {}, [
      el("section", { class: "content-section" }, [emptyState("المستوى غير موجود", "book")]),
    ]);
  }

  const section = el("div", {});

  /* Hero */
  section.append(el("section", { class: "lib-hero" }, [
    el("div", { class: "hero-bg" }),
    el("span", { class: "hero-crown" }, [icon("book-open", 30)]),
    el("span", { class: "hero-eyebrow" }, [icon("book-open", 15), LANG_META[lang]?.labelAr || "اللغة القانونية"]),
    el("h1", { text: level.title }),
    el("p", { class: "hero-sub", text: level.description }),
  ]));

  /* Back button */
  const contentSection = el("section", { class: "content-section" });
  contentSection.append(el("button", {
    class: "btn btn-ghost btn-sm mb-16",
    text: `\u2190 ${tr("back") || "رجوع"}`,
    onclick: () => navigate(`/legal-french?lang=${lang}`),
  }));

  let progressMap = {};
  if (session.token) {
    try {
      const { progress } = await api.get(`/api/legal-french/progress?lang=${lang}`);
      for (const p of progress) progressMap[p.lesson_id] = p;
    } catch { /* guest */ }
  }

  for (const unit of level.units) {
    contentSection.append(el("div", { class: "section-head", style: "margin-top:1rem" }, [
      el("div", {}, [
        el("div", { class: "eyebrow", text: unit.title }),
        el("p", { class: "sub", text: unit.title_ar }),
      ]),
    ]));

    const lessonsGrid = el("div", { class: "grid grid-3" });
    for (const ls of unit.lessons) {
      const prog = progressMap[ls.id];
      const completed = prog && prog.completed_at;

      lessonsGrid.append(el("article", {
        class: "law-card card-hover",
        style: "cursor:pointer",
        onclick: () => navigate(`/legal-french/lesson/${ls.id}?lang=${lang}`),
      }, [
        el("div", { class: "law-ic", style: `background:${completed ? "var(--success-bg,#e7f6f0)" : "var(--surface-2,#eef1f8)"};color:${completed ? "var(--success)" : level.color}` }, [
          completed ? icon("checkCircle", 20) : document.createTextNode(ls.id.split("_").pop().toUpperCase()),
        ]),
        el("div", { class: "law-body" }, [
          el("div", { class: "flex-between mb-8" }, [
            el("span", { class: "badge-pill badge-navy", text: completed ? "مكتمل" : ls.id.split("_").pop().toUpperCase() }),
          ]),
          el("h3", { class: "card-title", text: ls.title }),
          el("p", { class: "small muted", text: ls.subtitle }),
          el("p", { class: "small muted", text: ls.title_ar }),
          el("div", { class: "flex-between mt-8" }, [
            el("button", {
              class: "btn btn-ghost btn-sm",
              text: "الدرس",
              onclick: (e) => { e.stopPropagation(); navigate(`/legal-french/lesson/${ls.id}?lang=${lang}`); },
            }),
            el("button", {
              class: "btn btn-primary btn-sm",
              text: "اختبار",
              onclick: (e) => { e.stopPropagation(); navigate(`/legal-french/quiz/${ls.id}?lang=${lang}`); },
            }),
          ]),
        ]),
      ]));
    }
    contentSection.append(lessonsGrid);
  }

  section.append(contentSection);
  return section;
}

/* ── Single Lesson View ──────────────────────────────────────────────── */
export async function legalFrenchLessonView(params) {
  const lessonId = params.id;
  const lang = getLang();

  let lesson;
  try {
    lesson = await api.get(`/api/legal-french/lessons/${lessonId}`);
  } catch {
    return el("div", {}, [
      el("section", { class: "content-section" }, [emptyState("الدرس غير موجود", "book")]),
    ]);
  }

  const section = el("div", {});

  /* Hero */
  section.append(el("section", { class: "lib-hero" }, [
    el("div", { class: "hero-bg" }),
    el("span", { class: "hero-crown" }, [icon("book-open", 30)]),
    el("span", { class: "hero-eyebrow" }, [icon("book-open", 15), lesson.level_title]),
    el("h1", { text: lesson.title }),
    el("p", { class: "hero-sub", text: `${lesson.subtitle} \u2014 ${lesson.title_ar}` }),
  ]));

  const contentSection = el("section", { class: "content-section" });
  contentSection.append(el("button", {
    class: "btn btn-ghost btn-sm mb-16",
    text: `\u2190 ${tr("back") || "رجوع"}`,
    onclick: () => navigate(`/legal-french/${lesson.level_id}?lang=${lang}`),
  }));

  /* Tabs */
  const tabsContainer = el("div", {});
  let activeTab = "theory";

  const tabTheory = el("button", { class: "tab active", text: "الشرح النظري" });
  const tabVocab = el("button", { class: "tab", text: "المفردات" });
  const tabEx = el("button", { class: "tab", text: "التمارين" });
  const tabsEl = el("div", { class: "tabs tabs-row", style: "margin-bottom:1.5rem" }, [tabTheory, tabVocab, tabEx]);
  tabsContainer.append(tabsEl);

  const theoryPanel = el("div", {});
  const vocabPanel = el("div", { style: "display:none" });
  const exPanel = el("div", { style: "display:none" });

  /* Theory */
  theoryPanel.append(el("div", { class: "card", style: "padding:1.5rem" }, [
    el("h3", { style: "margin-bottom:1rem", text: "الشرح النظري \u2014 Th\u00e9orie" }),
    el("div", { style: "line-height:1.8;color:var(--ink-2);font-size:0.92rem;white-space:pre-wrap", html: esc(lesson.theory) }),
    el("div", { style: "margin-top:1.5rem;padding-top:1rem;border-top:1px solid var(--line)" }, [
      el("h4", { style: "color:var(--navy);margin-bottom:0.5rem", text: "الشرح بالعربية" }),
      el("div", { style: "line-height:1.8;color:var(--ink-2);font-size:0.92rem;white-space:pre-wrap", html: esc(lesson.theory_ar) }),
    ]),
  ]));

  /* Vocab */
  vocabPanel.append(el("h3", { style: "margin-bottom:1rem", text: "المفردات \u2014 Vocabulaire" }));
  const vocabGrid = el("div", { class: "grid grid-3" });
  lesson.vocab.forEach((v, i) => {
    vocabGrid.append(el("div", { class: "law-card", style: "padding:1rem" }, [
      el("div", { class: "flex-between mb-8" }, [
        el("span", { class: "badge-pill badge-navy", text: `${i + 1}` }),
        el("span", { class: "small muted", text: v.fr }),
      ]),
      el("div", { style: "font-weight:600;margin-bottom:0.3rem", text: v.fr }),
      el("div", { class: "small muted", text: v.ar }),
      el("p", { class: "small", style: "margin-top:0.5rem;color:var(--ink-3);font-style:italic", text: v.example }),
    ]));
  });
  vocabPanel.append(vocabGrid);

  /* Exercises */
  exPanel.append(el("h3", { style: "margin-bottom:0.5rem", text: "تمارين سريعة" }));
  exPanel.append(el("p", { class: "small muted", style: "margin-bottom:1rem", text: "اختر المعنى الصحيح لكل مصطلح" }));
  const exerciseForm = el("div", {});
  lesson.vocab.forEach((v, i) => {
    const wrong = lesson.vocab.filter((_, j) => j !== i).slice(0, 3);
    const opts = [v.ar, ...wrong.map((w) => w.ar)].sort(() => Math.random() - 0.5);
    const fieldset = el("div", { class: "law-card", style: "padding:1rem;margin-bottom:0.75rem" }, [
      el("p", { style: "font-weight:600;margin-bottom:0.5rem" }, [
        el("span", { class: "badge-pill badge-navy", text: `${i + 1}`, style: "margin-inline-end:0.5rem" }),
        document.createTextNode(v.fr),
      ]),
    ]);
    for (const opt of opts) {
      fieldset.append(el("label", { style: "display:flex;align-items:center;gap:0.5rem;padding:0.4rem 0;cursor:pointer" }, [
        el("input", { type: "radio", name: `ex_${i}`, value: opt }),
        document.createTextNode(" " + opt),
      ]));
    }
    exerciseForm.append(fieldset);
  });
  const checkBtn = el("button", { class: "btn btn-primary", text: "تحقق من الإجابات" });
  const resultDiv = el("div", { style: "margin-top:1rem" });
  checkBtn.addEventListener("click", () => {
    let correct = 0;
    lesson.vocab.forEach((v, i) => {
      const selected = exerciseForm.querySelector(`input[name="ex_${i}"]:checked`);
      const cards = exerciseForm.querySelectorAll(".law-card");
      const card = cards[i];
      if (selected && selected.value === v.ar) { correct++; card.style.borderColor = "var(--success)"; }
      else { card.style.borderColor = "var(--danger)"; }
    });
    resultDiv.innerHTML = "";
    const pct = Math.round(correct / lesson.vocab.length * 100);
    resultDiv.append(el("div", {
      class: `stat-chip`,
      style: `border:2px solid ${pct >= 60 ? "var(--success)" : "var(--danger)"};background:${pct >= 60 ? "var(--success-bg)" : "var(--danger-bg)"};border-radius:var(--radius-sm)`,
    }, [
      el("div", { class: "sc-icon" }, [icon(pct >= 60 ? "checkCircle" : "alertTriangle", 22)]),
      el("div", { style: "line-height:1.25" }, [
        el("div", { class: "sc-num", text: `${correct}/${lesson.vocab.length} \u2014 ${pct}%` }),
        el("div", { class: "sc-lbl", text: pct >= 60 ? "أحسنت!" : "حاول مرة أخرى" }),
      ]),
    ]));
  });
  exerciseForm.append(checkBtn, resultDiv);
  exPanel.append(exerciseForm);

  /* Tab switching */
  const panels = [theoryPanel, vocabPanel, exPanel];
  const tabs = [tabTheory, tabVocab, tabEx];
  tabs.forEach((tab, idx) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      panels.forEach((p) => p.style.display = "none");
      tab.classList.add("active");
      panels[idx].style.display = "";
    });
  });

  tabsContainer.append(theoryPanel, vocabPanel, exPanel);
  contentSection.append(tabsContainer);

  /* Footer CTA */
  contentSection.append(el("div", { style: "margin-top:2rem;text-align:center" }, [
    el("button", {
      class: "btn btn-gold",
      style: "width:100%;max-width:400px",
      text: "ابدأ الاختبار النهائي",
      onclick: () => navigate(`/legal-french/quiz/${lessonId}?lang=${lang}`),
    }),
  ]));

  section.append(contentSection);
  return section;
}

/* ── Quiz View ───────────────────────────────────────────────────────── */
export async function legalFrenchQuizView(params) {
  const lessonId = params.lessonId;
  const lang = getLang();

  let quiz;
  try {
    quiz = await api.get(`/api/legal-french/quiz/${lessonId}`);
  } catch {
    return el("div", {}, [
      el("section", { class: "content-section" }, [emptyState("الاختبار غير متوفر", "book")]),
    ]);
  }

  const section = el("div", {});

  section.append(el("section", { class: "lib-hero" }, [
    el("div", { class: "hero-bg" }),
    el("span", { class: "hero-crown" }, [icon("checkCircle", 30)]),
    el("span", { class: "hero-eyebrow" }, [icon("checkCircle", 15), "اختبار"]),
    el("h1", { text: `اختبار: ${quiz.lesson_title}` }),
    el("p", { class: "hero-sub", text: `عدد الأسئلة: ${quiz.questions.length} \u2014 النجاح: 60% على الأقل` }),
  ]));

  const contentSection = el("section", { class: "content-section" });
  contentSection.append(el("button", {
    class: "btn btn-ghost btn-sm mb-16",
    text: `\u2190 ${tr("back") || "رجوع"}`,
    onclick: () => navigate(`/legal-french/lesson/${lessonId}?lang=${lang}`),
  }));

  const form = el("div", {});

  quiz.questions.forEach((q) => {
    const qEl = el("div", { class: "law-card", style: "padding:1.25rem;margin-bottom:0.75rem" }, [
      el("p", { style: "font-weight:600;margin-bottom:0.5rem" }, [
        el("span", { class: "badge-pill badge-navy", text: `${q.id}`, style: "margin-inline-end:0.5rem" }),
        document.createTextNode(q.question),
      ]),
      q.example ? el("p", { class: "small muted", text: q.example }) : null,
    ]);
    for (const opt of q.options) {
      qEl.append(el("label", { style: "display:flex;align-items:center;gap:0.5rem;padding:0.4rem 0;cursor:pointer" }, [
        el("input", { type: "radio", name: `q_${q.id}`, value: opt }),
        document.createTextNode(" " + opt),
      ]));
    }
    form.append(qEl);
  });

  const submitBtn = el("button", { class: "btn btn-gold", style: "width:100%;margin-top:1rem", text: "أجب عن كل الأسئلة" });
  const resultDiv = el("div", { style: "margin-top:1rem" });

  submitBtn.addEventListener("click", async () => {
    let correct = 0;
    quiz.questions.forEach((q) => {
      const selected = form.querySelector(`input[name="q_${q.id}"]:checked`);
      const cards = form.querySelectorAll(".law-card");
      const qEl = cards[q.id - 1];
      if (selected && selected.value === q.correct) { correct++; qEl.style.borderColor = "var(--success)"; }
      else { qEl.style.borderColor = "var(--danger)"; }
    });

    const total = quiz.questions.length;
    const pct = Math.round(correct / total * 100);
    resultDiv.innerHTML = "";
    resultDiv.append(el("div", {
      class: "stat-chip",
      style: `border:2px solid ${pct >= 60 ? "var(--success)" : "var(--danger)"};background:${pct >= 60 ? "var(--success-bg)" : "var(--danger-bg)"};border-radius:var(--radius-sm);margin-top:1rem`,
    }, [
      el("div", { class: "sc-icon" }, [icon(pct >= 60 ? "checkCircle" : "alertTriangle", 22)]),
      el("div", { style: "line-height:1.25" }, [
        el("div", { class: "sc-num", text: pct >= 60 ? "أحسنت! نجحت في الاختبار" : "حاول مرة أخرى" }),
        el("div", { class: "sc-lbl", text: `${correct}/${total} \u2014 ${pct}%` }),
      ]),
    ]));

    if (session.token) {
      try {
        await api.post("/api/legal-french/progress", { lesson_id: lessonId, score: correct, total });
        resultDiv.append(el("p", { class: "small muted", style: "margin-top:0.5rem", text: "تم حفظ تقدمك" }));
      } catch { /* silent */ }
    }

    submitBtn.disabled = true;
    submitBtn.textContent = "تم الانتهاء";
  });

  form.append(submitBtn, resultDiv);
  contentSection.append(form);
  section.append(contentSection);
  return section;
}

/* ── Treaties List View ──────────────────────────────────────────────── */
export async function legalFrenchTreatiesView() {
  const lang = getLang();
  let currentLang = lang;

  const section = el("div", {});

  /* Hero */
  section.append(el("section", { class: "lib-hero" }, [
    el("div", { class: "hero-bg" }),
    el("span", { class: "hero-crown" }, [icon("globe", 30)]),
    el("span", { class: "hero-eyebrow" }, [icon("globe", 15), "النصوص والاتفاقيات"]),
    el("h1", { text: "النصوص القانونية والاتفاقيات الدولية" }),
    el("p", { class: "hero-sub", text: "نصوص قانونية أصيلة واتفاقيات دولية بعدة لغات" }),
  ]));

  const contentSection = el("section", { class: "content-section" });
  contentSection.append(el("button", {
    class: "btn btn-ghost btn-sm mb-16",
    text: `\u2190 ${tr("back") || "رجوع"}`,
    onclick: () => navigate(`/legal-french?lang=${lang}`),
  }));

  /* Language filter tabs */
  const langTabs = el("div", { class: "tabs tabs-row", style: "margin-bottom:1.5rem" }, [
    { code: "fr", label: "\u{1F1EB}\u{1F1F7} فرنسية" },
    { code: "en", label: "\u{1F1EC}\u{1F1E7} إنجليزية" },
    { code: "es", label: "\u{1F1EA}\u{1F1F8} إسبانية" },
    { code: "ar", label: "\u{1F1F8}\u{1F1EC}\u{1F1FE}\u{1F1EA} عربية" },
  ].map((l) => el("button", {
    class: `tab${l.code === currentLang ? " active" : ""}`,
    text: l.label,
    onclick: () => { currentLang = l.code; loadContent(); },
  })));
  contentSection.append(langTabs);

  const grid = el("div", { class: "tile-grid" });
  contentSection.append(grid);
  section.append(contentSection);

  async function loadContent() {
    /* Update active tab */
    langTabs.querySelectorAll(".tab").forEach((t, i) => {
      const codes = ["fr", "en", "es", "ar"];
      t.classList.toggle("active", codes[i] === currentLang);
    });

    grid.innerHTML = "";
    try {
      const data = await api.get(`/api/treaties?language=${currentLang}`);
      const items = data.treaties || [];

      if (items.length === 0) {
        grid.append(emptyState("لا توجد نصوص متوفرة بهذه اللغة", "book"));
        return;
      }

      for (const t of items) {
        grid.append(el("article", {
          class: "tile-card card-hover",
          style: "cursor:pointer",
          onclick: () => navigate(`/legal-french/treaty/${t.id}?lang=${currentLang}`),
        }, [
          el("div", { class: "t-tag" }, [
            el("span", {
              class: "badge-pill",
              style: "background:var(--info-bg);color:var(--info);font-size:0.75rem;padding:0.2rem 0.6rem",
              text: t.category,
            }),
          ]),
          el("h3", { class: "t-title", text: t.title }),
          t.title_ar ? el("div", { class: "t-sub", text: t.title_ar }) : null,
          el("p", { class: "t-sub", text: (t.description || "").slice(0, 120) }),
          el("div", { class: "t-sub", style: "margin-top:auto" }, [
            t.ratification_date ? el("span", { text: t.ratification_date }) : null,
            t.source_name ? el("span", { text: ` \u00b7 ${t.source_name}` }) : null,
          ]),
        ]));
      }
    } catch {
      grid.append(emptyState("خطأ في تحميل البيانات", "alert"));
    }
  }

  await loadContent();
  return section;
}

/* ── Treaty Detail View ──────────────────────────────────────────────── */
export async function legalFrenchTreatyDetailView(params) {
  const id = parseInt(params.id, 10);
  const lang = getLang();

  let treaty;
  try {
    treaty = await api.get(`/api/treaties/${id}`);
  } catch {
    return el("div", {}, [
      el("section", { class: "content-section" }, [emptyState("النص غير موجود", "file")]),
    ]);
  }

  const section = el("div", {});

  /* Hero */
  section.append(el("section", { class: "lib-hero" }, [
    el("div", { class: "hero-bg" }),
    el("span", { class: "hero-crown" }, [icon("globe", 30)]),
    el("span", { class: "hero-eyebrow" }, [icon("globe", 15), treaty.category]),
    el("h1", { text: treaty.title }),
    el("p", { class: "hero-sub", text: treaty.title_ar || "" }),
  ]));

  const contentSection = el("section", { class: "content-section" });
  contentSection.append(el("button", {
    class: "btn btn-ghost btn-sm mb-16",
    text: `\u2190 ${tr("back") || "رجوع"}`,
    onclick: () => navigate(`/legal-french/treaties?lang=${lang}`),
  }));

  /* Meta stats */
  const metaItems = [];
  metaItems.push([treaty.category, "folder", "التصنيف"]);
  if (treaty.ratification_date) metaItems.push([treaty.ratification_date, "calendar", "تاريخ التصديق"]);
  if (treaty.source_name) metaItems.push([treaty.source_name, "externalLink", "المصدر"]);
  if (metaItems.length > 0) {
    contentSection.append(el("div", { class: "stats-row", style: "margin-bottom:1.5rem" }, metaItems.map(([val, ic, lbl]) =>
      el("div", { class: "stat-chip" }, [
        el("div", { class: "sc-icon" }, [icon(ic, 22)]),
        el("div", { style: "line-height:1.25" }, [
          el("div", { class: "sc-num", text: val }),
          el("div", { class: "sc-lbl", text: lbl }),
        ]),
      ])
    )));
  }

  /* Description */
  if (treaty.description) {
    contentSection.append(el("div", { class: "card", style: "padding:1.5rem;margin-bottom:1.5rem" }, [
      el("h3", { style: "margin-bottom:0.5rem", text: "الوصف" }),
      el("p", { style: "line-height:1.8;color:var(--ink-2);font-size:0.92rem", text: treaty.description }),
    ]));
  }

  /* Source link */
  if (treaty.source_url) {
    contentSection.append(el("a", {
      class: "btn btn-primary btn-sm mb-16",
      href: treaty.source_url,
      target: "_blank",
      rel: "noopener noreferrer",
    }, [icon("externalLink", 14), " الاطلاع على النص الأصلي في المصدر"]));
  }

  /* Full text */
  if (treaty.full_text) {
    const formatted = treaty.full_text.split("\n").map((line) => {
      const t = line.trim();
      if (t.match(/^(Article|PR\u00c9AMBULE|PREAMBLE|\u0627\u0644\u0645\u0627\u062f\u0629|\u062a\u0645\u0647\u064a\u062f|PREMIER|DEUXI\u00c8ME|Livre|Titre|Source:|\u0627\u0644\u0645\u0635\u062f\u0631)/i)) {
        return `<h4 style="color:var(--navy);font-weight:700;border-bottom:1px solid var(--line);padding-bottom:4px;margin:18px 0 6px;font-size:0.95rem">${esc(t)}</h4>`;
      }
      if (t === "") return "<br>";
      return `<p style="margin:0 0 8px;color:var(--ink-2)">${esc(t)}</p>`;
    }).join("\n");

    contentSection.append(el("div", { class: "card", style: "padding:1.5rem;margin-top:1rem" }, [
      el("h2", { style: "margin-bottom:1rem;font-size:1.15rem", text: "النص الكامل" }),
      el("div", {
        html: formatted,
        style: "line-height:1.8;font-size:0.88rem;font-family:'Georgia','Times New Roman',serif",
      }),
    ]));
  }

  section.append(contentSection);
  return section;
}
