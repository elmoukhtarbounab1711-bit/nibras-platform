// نبراس — الملف الشخصي (تبويبات: المعلومات، الأمان، محتواي، التفضيلات)
import { tr, currentLang, setLang } from "../i18n.js";
import { api, session } from "../api.js";
import { el, initials, avatarColor, toast, emptyState, fmtDate, showConfirm } from "../ui.js";
import { logout } from "./auth.js";
import { navigate, render } from "../router.js";
import { getFavs, removeFav, getMyReviews } from "../favs.js";
import { icon, iconHTML } from "../icons.js";

const DATA_KEY = "nibras_profile_data";
const PW_KEY = "nibras_pw";
const BUYS_KEY = "nibras_purchases";

const localData = () => { try { return JSON.parse(localStorage.getItem(DATA_KEY) || "{}"); } catch { return {}; } };
const localPw = () => localStorage.getItem(PW_KEY) || "";

function profileHero(u) {
  return el("div", { class: "profile-hero-card card" }, [
    el("div", { class: "ph-avatar", style: `background:${avatarColor(u.full_name || u.email)}`, text: initials(u.full_name || u.email) }),
    el("div", { class: "ph-info" }, [
      el("div", { class: "pro-name", style: "font-size:22px" }, [el("span", { text: u.full_name || "—" })]),
      el("div", { class: "flex", style: "gap:6px;flex-wrap:wrap;margin:6px 0" }, [
        el("span", { class: "badge-pill badge-navy", text: u.email }),
        ...(u.roles || []).map((r) => el("span", { class: `badge-pill ${r === "admin" ? "badge-gold" : "badge-green"}`, text: r })),
      ]),
      u.created_at ? el("div", { class: "small muted", text: `${tr("memberSince")}: ${fmtDate(u.created_at, currentLang())}` }) : null,
    ]),
  ]);
}

function infoTab(u) {
  const d = localData();
  const f = (v) => v ?? "";
  const nameInput = el("input", { value: f(d.full_name || u.full_name) });
  const phoneInput = el("input", { dir: "ltr", value: f(d.phone) });
  const cityInput = el("input", { value: f(d.city) });
  const bioInput = el("textarea", { rows: 3, value: f(d.bio) });

  const form = el("form", { class: "card" }, [
    el("h3", { text: tr("accountInfo") }),
    el("p", { class: "small muted", style: "margin-bottom:12px", text: tr("localNotice") }),
    el("div", { class: "form-row" }, [
      el("div", { class: "field" }, [el("label", { text: tr("fullName") }), nameInput]),
      el("div", { class: "field" }, [el("label", { text: tr("phone") }), phoneInput]),
    ]),
    el("div", { class: "form-row" }, [
      el("div", { class: "field" }, [el("label", { text: tr("city") }), cityInput]),
      el("div", { class: "field" }, [el("label", { text: tr("bio") }), bioInput]),
    ]),
    el("button", { class: "btn btn-gold", type: "submit", text: tr("save") }),
  ]);
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const next = { ...d, full_name: nameInput.value.trim(), phone: phoneInput.value.trim(), city: cityInput.value.trim(), bio: bioInput.value.trim() };
    localStorage.setItem(DATA_KEY, JSON.stringify(next));
    toast(tr("saved"), "success");
  });
  return form;
}

function securityTab(u) {
  const curInput = el("input", { type: "password", dir: "ltr", placeholder: tr("currentPassword") });
  const newInput = el("input", { type: "password", dir: "ltr", placeholder: tr("newPassword") });
  const confInput = el("input", { type: "password", dir: "ltr", placeholder: tr("confirmPassword") });

  const pwForm = el("form", { class: "card" }, [
    el("h3", { text: tr("changePassword") }),
    el("p", { class: "small muted", style: "margin-bottom:12px", text: tr("localNotice") }),
    el("div", { class: "field" }, [el("label", { text: tr("currentPassword") }), curInput]),
    el("div", { class: "form-row" }, [
      el("div", { class: "field" }, [el("label", { text: tr("newPassword") }), newInput]),
      el("div", { class: "field" }, [el("label", { text: tr("confirmPassword") }), confInput]),
    ]),
    el("button", { class: "btn btn-gold", type: "submit", text: tr("save") }),
  ]);
  pwForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const cur = localPw();
    if (cur && curInput.value !== cur) { toast(tr("requiredFields"), "warn"); return; }
    if (newInput.value.length < 6) { toast(tr("requiredFields"), "warn"); return; }
    if (newInput.value !== confInput.value) { toast(tr("requiredFields"), "warn"); return; }
    localStorage.setItem(PW_KEY, newInput.value);
    toast(tr("saved"), "success");
    curInput.value = newInput.value = confInput.value = "";
  });

  return el("div", { class: "flex-col" }, [
    pwForm,
    el("div", { class: "card" }, [
      el("h3", {}, [icon("lock", 18)]),
      el("div", { class: "flex mt-8", style: "gap:8px;flex-wrap:wrap" }, [
        el("button", { class: "btn btn-danger", text: tr("logout"), onclick: async () => { await logout(); navigate("/"); } }),
        el("button", { class: "btn btn-ghost", title: tr("delete"), onclick: () => showConfirm({ title: tr("delete"), text: tr("localNotice"),
          onOk: () => { [DATA_KEY, PW_KEY].forEach((k) => localStorage.removeItem(k)); toast(tr("saved"), "success"); } }) }, [icon("trash", 16)]),
      ]),
    ]),
  ]);
}

async function contentTab(u) {
  const wrap = el("div", { class: "flex-col" });

  const [articlesData, docsData, tmplData] = await Promise.all([
    api.get("/api/blog/my").catch(() => null),
    api.get("/api/documents/my").catch(() => null),
    api.get("/api/marketplace/templates").catch(() => null),
  ]);
  const articles = (articlesData && articlesData.articles) || [];
  const docs = Array.isArray(docsData) ? docsData : (docsData && docsData.documents) || [];
  const bought = new Set(((() => { try { return JSON.parse(localStorage.getItem(BUYS_KEY) || "[]"); } catch { return []; } })()).map(Number));
  const templates = ((tmplData && (Array.isArray(tmplData) ? tmplData : tmplData.templates)) || []).filter((t) => bought.has(Number(t.id)));
  const favs = getFavs();
  const reviews = getMyReviews();

  wrap.append(el("h3", { style: "margin:0 0 6px" }, tr("myArticles")));
  wrap.append(articles.length
    ? el("div", { class: "flex-col" }, articles.map((a) => el("div", { class: "card list-row" }, [
        el("span", { class: "small", text: a.title }),
        el("div", { class: "flex", style: "gap:8px;flex-shrink:0" }, [
          el("a", { class: "btn btn-ghost btn-sm", href: `#/blog/${a.id}`, text: tr("view") }),
          el("a", { class: "btn btn-ghost btn-sm", href: `#/blog/edit/${a.id}` }, [icon("pen", 14), " " + tr("edit")]),
        ]),
      ])))
    : emptyState(tr("noResults"), "pen"));

  wrap.append(el("h3", { style: "margin:18px 0 6px" }, tr("myDocuments")));
  wrap.append(docs.length
    ? el("div", { class: "flex-col" }, docs.map((doc) => el("div", { class: "card list-row" }, [
        el("span", { class: "small", text: doc.template_name || doc.document_type || doc.type || doc.title || `#${doc.id}` }),
        el("span", { class: "small muted", text: fmtDate(doc.created_at, currentLang()) }),
      ])))
    : emptyState(tr("noResults"), "file"));

  wrap.append(el("h3", { style: "margin:18px 0 6px" }, tr("favorites")));
  wrap.append(favs.length
    ? el("div", { class: "flex-col" }, favs.map((f) => el("div", { class: "card list-row" }, [
        el("a", { class: "small", href: f.url || "#/home", text: f.title }),
        el("button", { class: "btn btn-ghost btn-sm", onclick: () => { removeFav(f.type, f.id); location.hash = "#/profile"; } }, [icon("x", 14)]),
      ])))
    : emptyState(tr("favoritesEmpty"), "star"));

  wrap.append(el("h3", { style: "margin:18px 0 6px" }, tr("myReviews")));
  wrap.append(reviews.length
    ? el("div", { class: "flex-col" }, reviews.map((r) => el("div", { class: "card" }, [
        el("div", { class: "flex-between" }, [
          el("span", { class: "small" }, [`${r.profName || tr("professionalsTitle")} · `, icon("star", 14, { filled: true }), ` ${r.rating}`]),
          el("span", { class: "small muted", text: fmtDate(r.at, currentLang()) }),
        ]),
        r.comment ? el("div", { class: "small muted", text: r.comment }) : null,
      ])))
    : emptyState(tr("reviewsEmpty"), "star"));

  wrap.append(el("h3", { style: "margin:18px 0 6px" }, tr("templatesTitle")));
  wrap.append(templates.length
    ? el("div", { class: "flex-col" }, templates.map((t) => el("div", { class: "card list-row" }, [
        el("span", { class: "small", text: t.title }),
        el("a", { class: "btn btn-ghost btn-sm", href: `#/marketplace/${t.id}`, text: tr("downloadNow") }),
      ])))
    : emptyState(tr("noResults"), "clipboard"));

  return wrap;
}

function prefsTab(u) {
  const langButtons = el("div", { class: "flex", style: "gap:8px" }, [
    el("button", { class: `chip${currentLang() === "ar" ? " active" : ""}`, text: "العربية", onclick: () => { setLang("ar"); render(); } }),
    el("button", { class: `chip${currentLang() === "fr" ? " active" : ""}`, text: "Français", onclick: () => { setLang("fr"); render(); } }),
  ]);

  return el("div", { class: "flex-col" }, [
    el("div", { class: "card" }, [
      el("h3", { text: tr("languageSettings") }),
      langButtons,
    ]),
    el("div", { class: "card" }, [
      el("h3", { text: tr("notifSettings") }),
      el("p", { class: "small muted", style: "margin-bottom:12px", text: tr("notificationsSub") }),
      el("div", { class: "flex", style: "gap:8px;flex-wrap:wrap" }, [
        el("a", { class: "btn btn-gold btn-sm", href: "#/notifications/settings", text: tr("deliverySettings") }),
        el("a", { class: "btn btn-ghost btn-sm", href: "#/notifications", text: tr("myNotifications") }),
      ]),
    ]),
  ]);
}

export async function profileView() {
  const me = await api.get("/api/auth/me");
  const u = me.user || me;

  const body = el("div", { class: "flex-col" });
  const renderTab = async (name) => {
    body.replaceChildren(
      name === "info" ? infoTab(u)
        : name === "security" ? securityTab(u)
          : name === "content" ? await contentTab(u)
            : prefsTab(u),
    );
  };

  const tabs = el("div", { class: "flex mb-16", style: "flex-wrap:gap:8px" }, [
    ["info", tr("profileTab")], ["security", tr("securityTab")], ["content", tr("contentTab")], ["prefs", tr("prefsTab")],
  ].map(([k, label], i) => {
    const b = el("button", { class: `chip${i === 0 ? " active" : ""}`, text: label });
    b.onclick = () => {
      tabs.querySelectorAll(".chip").forEach((c) => c.classList.remove("active"));
      b.classList.add("active");
      renderTab(k);
    };
    return b;
  }));

  renderTab("info");
  return el("div", {}, [profileHero(u), tabs, body]);
}
