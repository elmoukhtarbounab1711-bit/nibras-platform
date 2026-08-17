// نبراس — القانون المقارن (المرحلة 20 — D-038): قائمة ولايات قضائية
// + صفحة كل ولاية بتبويبات (القوانين / الاجتهادات / الدراسات المقارنة).
import { tr, currentLang } from "../i18n.js";
import { api, session } from "../api.js";
import { el, esc, truncate, emptyState, fmtDate, pagination, toast, initials } from "../ui.js";
import { icon, iconHTML } from "../icons.js";
import { navigate } from "../router.js";
import { openAuth } from "./auth.js";

const PER_PAGE = 9;

// لون تمييز لكل ولاية (حسب slug) لتغطيات البطاقات
function jurisdictionColor(slug) {
  const palette = ["#1f3a93", "#0f766e", "#9a3412", "#4f46e5", "#0e7490", "#b45309", "#8a5a00", "#7c3aed"];
  let h = 0;
  for (const ch of String(slug || "x")) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return palette[h % palette.length];
}

/* ---------- بطاقة ولاية قضائية ---------- */
function jurisdictionCard(j) {
  const color = jurisdictionColor(j.slug);
  const name = el("a", { class: "t-title", href: `#/comparative/jurisdiction/${j.slug}`, text: j.name });
  const card = el("article", { class: "tile-card", onclick: () => navigate(`/comparative/jurisdiction/${j.slug}`) });
  card.appendChild(el("div", { class: "tile-cover", style: `background:linear-gradient(135deg,${color},#0f1e4f);border-radius:var(--radius-md);height:74px;display:grid;place-items:center;color:#fff;font-size:30px;font-weight:800` },
    esc((j.name || "و")[0])));
  card.appendChild(el("span", { class: "t-tag badge-pill badge-navy", text: j.slug }));
  card.appendChild(name);
  card.appendChild(el("div", { class: "t-sub" }, [
    iconHTML("book", 13), ` ${j.text_count ?? 0} ${tr("lawsCount")}`,
  ]));
  card.appendChild(el("div", { class: "t-sub" }, [
    iconHTML("scale", 13), ` ${j.decision_count ?? 0} ${tr("jurisCount")}`,
  ]));
  card.appendChild(el("div", { class: "t-sub" }, [
    iconHTML("globe", 13), ` ${j.study_count ?? 0} ${tr("comparativeStudies")}`,
  ]));
  return card;
}

/* ---------- بطاقة نص قانوني ---------- */
function textCard(t) {
  const card = el("article", { class: "card card-hover" });
  card.innerHTML = `
    <div class="blog-meta">
      <span class="badge-pill badge-gold">${esc(t.category_name || tr("laws"))}</span>
      <span class="small muted">${esc(t.type || "")}</span>
    </div>
    <h3 class="card-title"><a href="#/text/${t.id}">${esc(t.title)}</a></h3>
    <p class="small muted">${esc(t.official_ref || "")}${t.article_count != null ? ` · ${t.article_count} ${tr("comparativeEntries")}` : ""}</p>
    <div class="blog-meta">
      <span style="margin-inline-start:auto">${iconHTML("book", 14)} ${tr("lawsCount")}</span>
    </div>`;
  return card;
}

/* ---------- بطاقة اجتهاد ---------- */
function decisionCard(d) {
  const card = el("article", { class: "card card-hover" });
  card.innerHTML = `
    <div class="blog-meta">
      <span class="badge-pill badge-navy">${esc(d.category_name || tr("jurisprudence"))}</span>
      <span>${esc(d.court || "")}</span>
    </div>
    <h3 class="card-title"><a href="#/jurisprudence/${d.id}">${esc(d.title)}</a></h3>
    <p class="small muted">${esc(truncate(d.principles || d.content || "", 130))}</p>
    <div class="blog-meta">
      <span>${esc(fmtDate(d.decision_date || d.created_at, currentLang()))}</span>
      <span style="margin-inline-start:auto">${iconHTML("eye", 14)} ${d.views ?? 0}</span>
    </div>`;
  return card;
}

/* ---------- الصفحة الرئيسية: شبكة الولايات ---------- */
export async function comparativeView() {
  const [jurData] = await Promise.all([
    api.get("/api/comparative/jurisdictions"),
  ]);
  const jurisdictions = jurData.jurisdictions || [];

  const hero = el("section", { class: "lib-hero" }, [
    el("div", { class: "hero-bg" }),
    el("span", { class: "hero-crown" }, [icon("globe", 30)]),
    el("span", { class: "hero-eyebrow" }, [icon("globe", 15), tr("comparativeEyebrow")]),
    el("h1", { text: tr("comparativeTitle") }),
    el("p", { class: "hero-sub", text: tr("comparativeSub") }),
  ]);

  const grid = jurisdictions.length
    ? el("div", { class: "tile-grid" }, jurisdictions.map(jurisdictionCard))
    : emptyState(tr("noResults"), "globe");

  const section = el("div", {}, [
    hero,
    el("section", { class: "content-section" }, [
      el("div", { class: "section-head" }, [
        el("div", {}, [
          el("div", { class: "eyebrow", text: tr("comparativeJurisdictions") }),
          el("h2", { text: tr("comparativeChooseJurisdiction") }),
          el("div", { class: "sub", text: tr("comparativeChooseSub") }),
        ]),
      ]),
      grid,
    ]),
  ]);
  return section;
}

/* ---------- تبويبات صفحة الولاية ---------- */
function jurTabs(active, onSelect) {
  const items = [
    ["laws", tr("jurTabsLaws")],
    ["decisions", tr("jurTabsDecisions")],
    ["studies", tr("jurTabsStudies")],
  ];
  return el("div", { class: "tabs tabs-row" }, items.map(([key, label]) =>
    el("button", { class: "tab" + (key === active ? " active" : ""), text: label, onclick: () => onSelect(key) })));
}

function jurPanel(kind, jur) {
  const box = el("div", {});
  const titleTxt = kind === "laws" ? tr("jurTabsLaws") : tr("jurTabsDecisions");
  const emptyTxt = kind === "laws" ? tr("jurNoLaws") : tr("jurNoDecisions");
  const iconName = kind === "laws" ? "book" : "scale";
  const seg = kind === "laws" ? "texts" : "decisions";
  const grid = el("div", { class: "grid grid-3" });
  const pills = el("div", { class: "chips", style: "margin:0 0 14px;flex-wrap:wrap" });
  const pager = el("div", { class: "adm-pager" });
  let page = 1;
  let catSlug = null;

  function url() {
    const p = new URLSearchParams({ limit: PER_PAGE, offset: (page - 1) * PER_PAGE });
    if (catSlug) p.set("category", catSlug);
    return `/api/comparative/jurisdictions/${jur.slug}/${seg}?${p.toString()}`;
  }

  async function loadPills() {
    try {
      const cats = kind === "laws"
        ? (await api.get(`/api/comparative/jurisdictions/${jur.slug}/categories`)).categories || []
        : await api.get(`/api/jurisprudence/categories?jurisdiction_id=${jur.id}`);
      const btn = (slug, label, active) => el("button",
        { class: "chip" + (active ? " chip-active" : ""), text: label, onclick: () => { catSlug = slug; page = 1; draw(); } });
      pills.replaceChildren(
        btn(null, kind === "laws" ? tr("jurTabsLaws") : tr("jurTabsDecisions"), catSlug === null),
        ...cats.map((x) => btn(x.slug, `${x.name} (${x.count ?? x.decision_count ?? 0})`, catSlug === x.slug)),
      );
    } catch (_) { pills.replaceChildren(); }
  }

  async function draw() {
    grid.replaceChildren(el("div", { class: "skeleton", style: "height:120px" }));
    try {
      const data = await api.get(url());
      const items = kind === "laws" ? (data.texts || []) : (data.decisions || []);
      const total = data.count ?? items.length;
      if (items.length) {
        grid.replaceChildren(...items.map(kind === "laws" ? textCard : decisionCard));
      } else {
        grid.replaceChildren(emptyState(emptyTxt, iconName));
      }
      pager.replaceChildren(total > PER_PAGE
        ? pagination(total, page, PER_PAGE, (p) => { page = p; draw(); })
        : null);
    } catch (e) {
      grid.replaceChildren(el("div", { class: "adm-404", text: String(e?.message || e) }));
    }
  }
  box.append(
    el("div", { class: "lib-section-title" }, [el("span", { class: "lst-rule" }), `${titleTxt} — ${jur.name}`]),
    pills,
    grid,
    pager,
  );
  loadPills();
  draw();
  return box;
}

function jurisdictionLawsPanel(jur) {
  return jurPanel("laws", jur);
}

function jurisdictionDecisionsPanel(jur) {
  return jurPanel("decisions", jur);
}

function compArticleCard(a) {
  const card = el("article", { class: "card card-hover" });
  card.innerHTML = `
    <div class="blog-meta">
      <span class="badge-pill badge-gold">${esc(a.category_name || tr("comparativeStudy"))}</span>
      <span>${esc(fmtDate(a.published_at || a.created_at, currentLang()))}</span>
    </div>
    <h3 class="card-title"><a href="#/blog/${a.id}">${esc(a.title)}</a></h3>
    <p class="small muted">${esc((a.summary || a.body || "").slice(0, 110))}${(a.summary || a.body || "").length > 110 ? "…" : ""}</p>
    <div class="blog-meta">
      <span>${esc(a.author?.full_name || "")}</span>
      <span style="margin-inline-start:auto">${iconHTML("eye", 14)} ${a.views ?? 0}</span>
    </div>`;
  return card;
}

async function jurisdictionStudiesPanel(jur) {
  const box = el("div", {});
  const [data, artsData] = await Promise.all([
    api.get(`/api/comparative/studies?limit=${PER_PAGE}&jurisdiction_id=${jur.id}`),
    api.get(`/api/comparative/jurisdictions/${jur.slug}/articles`),
  ]);
  const studies = data.studies || [];
  const articles = artsData.articles || [];
  box.append(
    el("div", { class: "lib-section-title" }, [el("span", { class: "lst-rule" }), `${tr("jurTabsStudies")} — ${jur.name}`]),
    articles.length
      ? el("div", { class: "grid grid-3" }, articles.map(compArticleCard))
      : null,
    studies.length
      ? el("div", { class: "grid grid-3" }, studies.map(studyCard))
      : (articles.length ? null : emptyState(tr("jurNoStudies"), "globe")),
  );
  return box;
}

function studyCard(s) {
  const color = jurisdictionColor(s.id);
  const card = el("article", { class: "card card-hover" });
  card.innerHTML = `
    <div class="blog-meta">
      <span class="badge-pill badge-gold">${tr("comparativeStudy")}</span>
      <span>${esc(fmtDate(s.updated_at, currentLang()))}</span>
    </div>
    <h3 class="card-title"><a href="#/comparative/study/${s.id}">${esc(s.title)}</a></h3>
    <p class="small muted">${esc((s.description || "").slice(0, 110))}${(s.description || "").length > 110 ? "…" : ""}</p>
    <div class="blog-meta">
      <span class="avatar-sm" style="background:var(--navy)">${esc((s.creator_name || "ب")[0])}</span>
      <span>${esc(s.creator_name || "")}</span>
      <span style="margin-inline-start:auto">${iconHTML("globe", 14)} ${s.entry_count ?? 0} ${tr("comparativeEntries")}</span>
    </div>`;
  return card;
}

/* ---------- صفحة الولاية القضائية (تبويبات 3) ---------- */
export async function jurisdictionView(params) {
  const slug = params.slug;
  const data = await api.get(`/api/comparative/jurisdictions/${slug}`);
  const jur = data.jurisdiction;
  if (!jur) return emptyState(tr("comparativeNotFound"), "globe");

  let active = params.tab || "laws";
  const container = el("div", {});

  async function render() {
    container.replaceChildren(
      el("button", { class: "btn btn-ghost btn-sm mb-16", text: `← ${tr("back")}`, onclick: () => navigate("/comparative") }),
      el("section", { class: "lib-hero" }, [
        el("div", { class: "hero-bg" }),
        el("span", { class: "hero-crown" }, [icon("globe", 30)]),
        el("span", { class: "hero-eyebrow" }, [icon("globe", 15), tr("comparativeEyebrow")]),
        el("h1", { text: jur.name }),
        el("p", { class: "hero-sub", text: `${jur.text_count ?? 0} ${tr("lawsCount")} · ${jur.decision_count ?? 0} ${tr("jurisCount")} · ${jur.study_count ?? 0} ${tr("comparativeStudies")}` }),
      ]),
      el("div", { class: "content-section" }, [
        jurTabs(active, (k) => { active = k; render(); }),
        el("div", { class: "tab-panel" }),
      ]),
    );
    const panelEl = container.querySelector(".tab-panel");
    panelEl.replaceChildren(el("div", { class: "skeleton", style: "height:120px" }));
    try {
      const p = active === "laws" ? jurisdictionLawsPanel(jur)
        : active === "decisions" ? jurisdictionDecisionsPanel(jur)
        : jurisdictionStudiesPanel(jur);
      const node = await p;
      panelEl.replaceChildren(node);
    } catch (e) {
      panelEl.replaceChildren(el("div", { class: "adm-404", text: String(e?.message || e) }));
    }
  }
  render();
  return container;
}

/* ---------- تفصيل دراسة مقارنة ---------- */
export async function comparativeDetailView(params) {
  const study = await api.get(`/api/comparative/studies/${params.id}`);
  if (!study) return emptyState(tr("comparativeNotFound"), "globe");

  const view = el("div", { class: "post-body" });
  const entries = study.entries || [];

  const byJurisdiction = {};
  for (const e of entries) {
    (byJurisdiction[e.jurisdiction_id] = byJurisdiction[e.jurisdiction_id] || []).push(e);
  }

  const entryBlock = (jurName, list) => el("div", { class: "card mt-16", style: "padding:16px" }, [
    el("div", { class: "flex-between" }, [
      el("h3", { style: "margin:0;font-size:17px;display:flex;align-items:center;gap:8px" }, [
        el("span", { style: `width:10px;height:10px;border-radius:50%;background:${jurisdictionColor(list[0].jurisdiction_slug)};display:inline-block` }),
        esc(jurName),
      ]),
      el("span", { class: "badge-pill badge-navy", text: list[0].jurisdiction_slug }),
    ]),
    ...list.map((e) => el("div", { class: "mt-12", style: "border-inline-start:3px solid var(--line);padding-inline-start:12px" }, [
      e.legal_text_title ? el("div", { class: "small muted" }, [
        iconHTML("book", 13), " ",
        esc(e.legal_text_title),
        e.article_number ? ` — ${tr("article")} ${esc(e.article_number)}` : "",
      ]) : null,
      e.note ? el("p", { style: "margin:4px 0 0", text: e.note }) : null,
    ])),
  ]);

  view.append(
    el("button", { class: "btn btn-ghost btn-sm mb-16", text: `← ${tr("back")}`, onclick: () => navigate("/comparative") }),
    el("div", { class: "blog-meta" }, [
      el("span", { class: "badge-pill badge-gold", text: tr("comparativeStudy") }),
      study.status !== "published"
        ? el("span", { class: "badge-pill badge-warn", text: study.status === "draft" ? tr("articleDraft") : tr("articleHidden") })
        : null,
    ]),
    el("h1", { style: "font-size:26px", text: study.title }),
    el("div", { class: "blog-meta" }, [
      el("span", { class: "avatar-sm", text: initials(study.creator_name) }),
      el("span", { text: study.creator_name }),
      el("span", { class: "small muted", style: "margin-inline-start:auto" }, [iconHTML("globe", 14), ` ${study.entry_count ?? 0} ${tr("comparativeEntries")}`]),
    ]),
    study.description ? el("p", { class: "lead", text: study.description }) : null,
    el("hr", { class: "divider" }),

    entries.length
      ? Object.values(byJurisdiction).map((list) => entryBlock(list[0].jurisdiction_name, list))
      : emptyState(tr("comparativeNoEntries"), "fileText"),
  );
  return view;
}

function fieldInput(label, node, hint) {
  return el("div", { class: "field" }, [
    el("label", { text: label }),
    node,
    hint ? el("div", { class: "small muted", style: "margin-top:3px", text: hint }) : null,
  ]);
}

/* ---------- إنشاء دراسة جديدة ---------- */
export async function comparativeNewView() {
  const jurData = await api.get("/api/comparative/jurisdictions");
  const jurisdictions = jurData.jurisdictions || [];

  const titleInput = el("input", { placeholder: tr("comparativeTitlePh") });
  const descInput = el("textarea", { rows: 3, placeholder: tr("comparativeDescPh") });
  const jurisS = el("select", {}, [
    el("option", { value: "", text: tr("jurSelectPlaceholder") }),
    ...jurisdictions.map((j) => el("option", { value: String(j.id), text: j.name })),
  ]);

  const form = el("form", { class: "card article-view" }, [
    el("h2", { text: tr("comparativeNewStudy") }),
    fieldInput(tr("title") + " *", titleInput),
    fieldInput(tr("description"), descInput),
    fieldInput(tr("comparativePrimaryJurisdiction"), jurisS),
    el("div", { class: "mt-8", style: "color:var(--ink-3);font-size:13px" }, [
      iconHTML("info", 14), " ",
      tr("comparativeNewNote"),
    ]),
    el("div", { class: "modal-actions" }, [
      el("button", { class: "btn btn-ghost", text: tr("cancel"), onclick: () => navigate("/comparative") }),
      el("button", { class: "btn btn-primary", type: "submit", text: tr("save") }),
    ]),
  ]);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = titleInput.value.trim();
    if (!title) return toast(tr("requiredFields"), "warn");
    try {
      const r = await api.post("/api/comparative/studies", {
        title,
        description: descInput.value.trim(),
        jurisdiction_id: jurisS.value ? Number(jurisS.value) : undefined,
      });
      toast(tr("sent"), "success");
      navigate(`/comparative/study/${r.id}`);
    } catch (err) { toast(err.message, "error"); }
  });

  return form;
}