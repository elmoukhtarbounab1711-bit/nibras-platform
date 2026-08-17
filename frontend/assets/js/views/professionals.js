// نبراس — دليل المهنيين (v2): بحث متقدم، ملفات مهنية، ملفي الشخصي والتحقق
import { tr, currentLang } from "../i18n.js";
import { api, session } from "../api.js";
import { el, esc, initials, avatarColor, toast, emptyState, openModal, closeModal } from "../ui.js";
import { addMyReview } from "../favs.js";
import { icon, iconHTML } from "../icons.js";
import { buyPlan } from "./billing.js";

const PROF_TYPES = [
  "lawyer", "notary", "adoul", "judicial_commissioner", "sworn_translator", "judicial_expert",
];
const PROF_LABELS = {
  lawyer: ["محامٍ", "Avocat"], notary: ["موثق", "Notaire"], adoul: ["عدل", "Adoul"],
  judicial_commissioner: ["مفوض قضائي", "Commissaire judiciaire"],
  sworn_translator: ["مترجم محلف", "Traducteur assermenté"],
  judicial_expert: ["خبير قضائي", "Expert judiciaire"],
};
const langIsFr = () => currentLang() === "fr";
export const profTypeLabel = (t) => (PROF_LABELS[t] ? PROF_LABELS[t][langIsFr() ? 1 : 0] : t || "—");

async function premiumBySlug(slug) {
  try { const p = await api.get(`/api/plans/${slug}`); if (p && p.kind === "premium_listing") return p; }
  catch { /* fallback */ }
  try {
    const d = await api.get("/api/plans?kind=premium_listing");
    const list = d.plans || [];
    return list.find((x) => x.slug === slug) || list[0] || null;
  } catch { return null; }
}

function premiumCta(slug = "premium-30") {
  return el("button", {
    class: "btn btn-gold btn-block",
    text: tr("premiumCta"),
    onclick: async () => {
      const plan = await premiumBySlug(slug);
      if (!plan) { toast(tr("premiumSoon"), "info"); return; }
      buyPlan(plan);
    },
  });
}

function stars(n) {
  const v = Math.round(Number(n || 0) * 2) / 2;
  return [1, 2, 3, 4, 5].map((i) => i <= v ? icon("star", 14, { filled: true }) : icon("star", 14, { filled: false }));
}

function verifiedBadge() {
  return el("span", { class: "badge-pill badge-green" }, [icon("check", 12), " " + tr("verifiedPro")]);
}

function proCard(p, onOpen) {
  return el("article", { class: "card card-hover pro-card" }, [
    p.photo_url
      ? el("div", { class: "pro-avatar" }, [el("img", { src: p.photo_url, alt: p.full_name })])
      : el("div", { class: "pro-avatar", style: `background:${avatarColor(p.full_name)}`, text: initials(p.full_name) }),
    el("div", { class: "pro-meta", style: "flex:1;min-width:0" }, [
      el("div", { class: "pro-name" }, [
        el("span", { text: p.full_name }),
        verifiedBadge(),
      ]),
      el("div", { class: "pro-spec", text: profTypeLabel(p.profession_type) }),
      el("div", { class: "flex", style: "flex-wrap:gap:5px" },
        (p.specialties || []).map((s) => el("span", { class: "spec-tag", text: s }))),
      el("div", { class: "flex", style: "flex-wrap:wrap;gap:12px" }, [
        p.city ? el("span", { class: "small muted" }, [icon("mapPin", 14), " " + p.city]) : null,
        p.years_of_experience != null ? el("span", { class: "small muted", text: `${p.years_of_experience} ${tr("yearsExp")}` }) : null,
        p.address ? el("span", { class: "small muted" }, [icon("building", 14), " " + p.address]) : null,
      ]),
      el("div", { class: "flex", style: "flex-wrap:wrap;gap:8px;align-items:center" }, [
        el("span", { class: "stars" }, stars(p.rating)),
        el("span", { class: "small", style: "font-weight:700;color:var(--gold)", text: `${p.rating ?? "0.0"} (${p.review_count ?? 0} ${tr("reviews")})` }),
      ]),
      el("div", { class: "flex mt-8", style: "flex-wrap:wrap;gap:8px" }, [
        el("button", { class: "btn btn-primary btn-sm", text: tr("viewProfile"), onclick: onOpen }),
        p.phone ? el("a", { class: "btn btn-ghost btn-sm", href: `tel:${p.phone.replace(/\s+/g, "")}`, text: tr("callNow") }) : null,
        p.email ? el("a", { class: "btn btn-ghost btn-sm", href: `mailto:${p.email}`, text: tr("emailNow") }) : null,
      ]),
    ]),
  ]);
}

/* ---------- صفحة القائمة مع البحث المتقدم ---------- */
export async function professionalsView() {
  const filter = { type: "", specialty: "", city: "" };

  const typeSel = el("select", {},
    [el("option", { value: "", text: tr("allProfessions") })]
      .concat(PROF_TYPES.map((t) => el("option", { value: t, text: profTypeLabel(t) }))));
  const citySel = el("select", {}, [el("option", { value: "", text: tr("allCities") })]);
  const specInput = el("input", { type: "text", placeholder: tr("filterSpecialty") });
  const count = el("span", { class: "small muted" });

  const grid = el("div", { class: "grid grid-2" });
  const load = async () => {
    grid.replaceChildren(el("div", { class: "sk-card" }, [el("div", { class: "sk-cover" }), el("div", { class: "sk-line w70" }), el("div", { class: "sk-line w45" })]),
      el("div", { class: "sk-card" }, [el("div", { class: "sk-cover" }), el("div", { class: "sk-line w70" }), el("div", { class: "sk-line w45" })]));
    const qs = new URLSearchParams();
    if (filter.type) qs.set("type", filter.type);
    if (filter.specialty) qs.set("specialty", filter.specialty);
    if (filter.city) qs.set("city", filter.city);
    qs.set("limit", "50");
    try {
      const data = await api.get(`/api/professionals?${qs.toString()}`);
      const list = Array.isArray(data) ? data : data.professionals || [];
      if (citySel.options.length <= 1) {
        for (const c of [...new Set(list.map((p) => p.city).filter(Boolean))].sort())
          citySel.append(el("option", { value: c, text: c }));
      }
      count.textContent = `${list.length} ${tr("resultsCount")}`;
      if (list.length) {
        grid.replaceChildren(...list.map((p) => proCard(p, () => { location.hash = `#/professionals/${p.id}`; })));
      } else {
        grid.replaceChildren(emptyState(tr("noResults"), "users"));
      }
    } catch (e) { grid.replaceChildren(emptyState(e.message || tr("error"))); }
  };

  const apply = () => { filter.type = typeSel.value; filter.city = citySel.value; filter.specialty = specInput.value.trim(); load(); };
  typeSel.addEventListener("change", apply);
  citySel.addEventListener("change", apply);
  specInput.addEventListener("keydown", (e) => { if (e.key === "Enter") apply(); });

  return el("div", {}, [
    el("div", { class: "section-head" }, [
      el("div", {}, [
        el("div", { class: "eyebrow", text: tr("professionalsSub") }),
        el("h2", { text: tr("professionalsTitle") }),
      ]),
      session.token ? el("button", { class: "btn btn-gold btn-sm", text: tr("myProfile"), onclick: () => { location.hash = "#/professionals/me"; } }) : null,
    ]),
    el("div", { class: "card", style: "margin-bottom:18px" }, [
      el("div", { class: "filter-grid" }, [
        el("div", { class: "field" }, [el("label", { text: tr("filterProfession") }), typeSel]),
        el("div", { class: "field" }, [el("label", { text: tr("filterSpecialty") }), specInput]),
        el("div", { class: "field" }, [el("label", { text: tr("filterCity") }), citySel]),
      ]),
      el("div", { class: "flex mt-16", style: "justify-content:space-between" }, [
        count,
        el("button", { class: "btn btn-primary btn-sm", text: tr("homeSearchBtn"), onclick: apply }),
      ]),
    ]),
    grid,
  ]);
}

/* ---------- صفحة الملف المهني ---------- */
export async function professionalDetailView({ id }) {
  const p = await api.get(`/api/professionals/${id}`);

  const reviews = el("div", { class: "flex-col" });
  for (const rv of p.reviews || []) {
    reviews.append(el("div", { class: "review-item" }, [
      el("div", { class: "rv-head" }, [
        el("span", { class: "avatar-sm", style: `background:${avatarColor(rv.reviewer_name || "x")}`, text: initials(rv.reviewer_name || "؟") }),
        el("span", { style: "font-weight:700", text: rv.reviewer_name }),
        el("span", { class: "stars" }, stars(rv.rating)),
      ]),
      rv.comment ? el("div", { class: "rv-body", text: rv.comment }) : null,
    ]));
  }

  const reviewForm = el("form", { class: "card", style: "margin-top:14px" }, [
    el("h3", { text: tr("reviews") }),
    el("div", { class: "flex", style: "gap:6px;margin-bottom:10px" },
      [1, 2, 3, 4, 5].map((n) => {
        const b = el("button", { type: "button", class: "stars", style: "font-size:22px;border:0;background:none;cursor:pointer;color:var(--gold)" }, [icon("star", 20, { filled: false })]);
        b.onclick = () => {
          b.parentElement.querySelectorAll("button").forEach((bt, i) => { bt.replaceChildren(icon("star", 20, { filled: i < n })); });
          b.dataset.val = n;
        };
        return b;
      })),
    el("div", { class: "field" }, [el("textarea", { placeholder: tr("commentPlaceholder"), rows: 3 })]),
    el("button", {
      class: "btn btn-primary btn-sm", text: tr("send"),
      onclick: async (e) => {
        e.preventDefault();
        const rating = reviewForm.querySelector(".stars[data-val]")?.dataset.val;
        const comment = reviewForm.querySelector("textarea").value.trim();
        if (!rating) { toast(tr("requiredFields"), "warn"); return; }
        try {
          await api.post(`/api/professionals/${id}/reviews`, { rating: Number(rating), comment });
          addMyReview({ profId: id, profName: p.full_name, rating: Number(rating), comment });
          toast(tr("sent"), "success");
          setTimeout(() => { location.reload(); }, 700);
        } catch (err) { toast(err.message, "error"); }
      },
    }),
  ]);

  const mapBlock = p.map_embed
    ? el("a", { class: "map-embed", href: p.map_embed, target: "_blank", rel: "noopener" }, [
      el("div", { class: "ta-center" }, [el("div", {}, [icon("map", 30)]), el("div", { class: "small", text: tr("openMap") })]),
    ])
    : null;

  return el("div", {}, [
    el("button", { class: "btn btn-ghost btn-sm mb-16", text: `→ ${tr("professionalsTitle")}`, onclick: () => { location.hash = "#/professionals"; } }),
    el("div", { class: "card", style: "margin-bottom:18px" }, [
      el("div", { class: "profile-hero-card" }, [
        p.photo_url
          ? el("div", { class: "ph-avatar" }, [el("img", { src: p.photo_url, alt: p.full_name })])
          : el("div", { class: "ph-avatar", style: `background:${avatarColor(p.full_name)}`, text: initials(p.full_name) }),
        el("div", { class: "ph-info" }, [
          el("div", { class: "pro-name", style: "font-size:22px" }, [
            el("span", { text: p.full_name }),
            verifiedBadge(),
          ]),
          el("div", { class: "flex", style: "gap:6px;flex-wrap:wrap;margin:6px 0" }, [
            el("span", { class: "badge-pill badge-gold", text: profTypeLabel(p.profession_type) }),
            (p.specialties || []).map((s) => el("span", { class: "spec-tag", text: s })),
          ]),
          el("div", { class: "flex", style: "gap:10px;flex-wrap:wrap" }, [
            el("span", { class: "stars" }, stars(p.rating)),
            el("span", { class: "small", text: `${p.rating ?? "0.0"} · ${p.review_count ?? 0} ${tr("reviews")}` }),
          ]),
          el("div", { class: "ph-actions mt-16" }, [
            p.phone ? el("a", { class: "btn btn-gold btn-sm", href: `tel:${p.phone.replace(/\s+/g, "")}` }, [icon("phone", 14), " " + tr("callNow")]) : null,
            p.email ? el("a", { class: "btn btn-primary btn-sm", href: `mailto:${p.email}` }, [icon("mail", 14), " " + tr("emailNow")]) : null,
            p.website ? el("a", { class: "btn btn-ghost btn-sm", href: p.website, target: "_blank", rel: "noopener" }, [icon("globe", 14)]) : null,
          ]),
        ]),
      ]),
    ]),

    el("div", { class: "grid", style: "grid-template-columns:1.4fr 1fr;gap:18px" }, [
      el("div", {}, [
        el("div", { class: "card", style: "margin-bottom:18px" }, [
          el("h3", { text: tr("profileTitle") }),
          p.bio ? el("p", { class: "muted", text: p.bio }) : null,
          el("div", { class: "info-grid mt-16" }, [
            p.address ? el("div", { class: "info-item" }, [el("span", { class: "ii-icon" }, [icon("building", 16)]), el("div", {}, [el("div", { class: "ii-label", text: tr("officeAddress") }), el("div", { class: "ii-val", text: p.address })])]) : null,
            p.years_of_experience != null ? el("div", { class: "info-item" }, [el("span", { class: "ii-icon" }, [icon("graduationCap", 16)]), el("div", {}, [el("div", { class: "ii-label", text: tr("yearsExp") }), el("div", { class: "ii-val", text: `${p.years_of_experience}` })])]) : null,
            p.work_hours ? el("div", { class: "info-item" }, [el("span", { class: "ii-icon" }, [icon("clock", 16)]), el("div", {}, [el("div", { class: "ii-label", text: tr("workHours") }), el("div", { class: "ii-val", text: p.work_hours })])]) : null,
            p.registration_number ? el("div", { class: "info-item" }, [el("span", { class: "ii-icon" }, [icon("idCard", 16)]), el("div", {}, [el("div", { class: "ii-label", text: tr("registration_number") || "رقم الاعتماد" }), el("div", { class: "ii-val", text: p.registration_number })])]) : null,
          ]),
          p.social_links && Object.keys(p.social_links).length
            ? el("div", { class: "flex mt-16", style: "flex-wrap:wrap;gap:8px" }, Object.entries(p.social_links).map(([k, v]) => el("a", { class: "btn btn-ghost btn-sm", href: v, target: "_blank", rel: "noopener" }, [icon("link", 14), " " + k])))
            : null,
        ]),
        el("div", { class: "card" }, [
          el("h3", { text: `${tr("reviews")} (${p.review_count ?? 0})` }),
          p.reviews?.length ? reviews : el("div", { class: "small muted", text: tr("reviewsEmpty") }),
          session.token && session.user?.id !== p.user_id ? reviewForm : null,
        ]),
      ]),
      el("div", {}, [
        el("div", { class: "card", style: "margin-bottom:18px" }, [
          el("h3", { text: tr("contact") }),
          el("div", { class: "flex-col" }, [
            p.phone ? el("a", { class: "btn btn-outline btn-block", href: `tel:${p.phone.replace(/\s+/g, "")}` }, [icon("phone", 14), " " + p.phone]) : null,
            p.email ? el("a", { class: "btn btn-outline btn-block", href: `mailto:${p.email}` }, [icon("mail", 14), " " + p.email]) : null,
            p.website ? el("a", { class: "btn btn-ghost btn-block", href: p.website, target: "_blank", rel: "noopener" }, [icon("globe", 14), " " + p.website]) : null,
          ]),
        ]),
        mapBlock ? el("div", { class: "card", style: "margin-bottom:18px" }, [el("h3", { text: tr("mapLocation") }), mapBlock]) : null,
        el("div", { class: "pricing-card" }, [
          el("span", { class: "pc-badge" }, [icon("star", 18, { filled: true })]),
          el("h3", {}, [icon("star", 16, { filled: true }), " " + tr("premiumTitle")]),
          el("div", { class: "pc-price", text: "MAD 149" }),
          el("ul", [
            el("li", {}, [icon("check", 12), " " + tr("premiumDesc")]),
            el("li", {}, [icon("check", 12), " شارة مميزة في نتائج البحث"]),
            el("li", {}, [icon("check", 12), " أولوية الظهور في الدليل"]),
          ]),
          premiumCta(),
        ]),
      ]),
    ]),
  ]);
}

/* ---------- ملفي المهني (إنشاء/تعديل + التحقق) ---------- */
export async function myProfessionalView() {
  let existing = null;
  try {
    const data = await api.get("/api/professionals");
    const list = Array.isArray(data) ? data : data.professionals || [];
    existing = list.find((p) => p.email === session.user?.email) || null;
  } catch { existing = null; }

  const f = (val) => val ?? "";
  const makeField = (label, node) => el("div", { class: "field" }, [el("label", { text: label }), node]);

  const form = el("form", {}, [
    el("div", { class: "form-row" }, [
      makeField(tr("profession"), (() => {
        const s = el("select", {}, [el("option", { value: "", text: tr("allProfessions") })].concat(PROF_TYPES.map((t) => el("option", { value: t, text: profTypeLabel(t) }))));
        if (existing) s.value = existing.profession_type;
        return s;
      })()),
      makeField(tr("city"), (() => { const i = el("input", { value: f(existing?.city) }); return i; })()),
    ]),
    makeField(tr("specialty"), (() => { const i = el("input", { value: f((existing?.specialties || []).join("، ")), placeholder: "أسرة، عقار، شركات، جنائي..." }); return i; })()),
    makeField(tr("bio"), (() => { const t = el("textarea", { rows: 4, value: f(existing?.bio) }); return t; })()),
    el("div", { class: "form-row" }, [
      makeField(tr("phone"), (() => { const i = el("input", { dir: "ltr", value: f(existing?.phone) }); return i; })()),
      makeField(tr("email"), (() => { const i = el("input", { dir: "ltr", value: f(existing?.email || session.user?.email), disabled: true }); return i; })()),
    ]),
    el("div", { class: "form-row" }, [
      makeField(tr("officeAddress"), (() => { const i = el("input", { value: f(existing?.address) }); return i; })()),
      makeField(tr("yearsExp"), (() => { const i = el("input", { type: "number", value: f(existing?.years_of_experience) }); return i; })()),
    ]),
    el("div", { class: "form-row" }, [
      makeField(tr("website"), (() => { const i = el("input", { dir: "ltr", value: f(existing?.website), placeholder: "https://" }); return i; })()),
      makeField(tr("workHours"), (() => { const i = el("input", { value: f(existing?.work_hours), placeholder: "9:00 - 17:00" }); return i; })()),
    ]),
    makeField(tr("mapLocation"), (() => { const i = el("input", { dir: "ltr", value: f(existing?.map_embed), placeholder: "https://maps.app.goo.gl/..." }); return i; })()),
    makeField("social_links (JSON)", (() => { const i = el("input", { dir: "ltr", value: existing?.social_links ? JSON.stringify(existing.social_links) : "", placeholder: '{"linkedin":"https://..."}' }); return i; })()),
    el("button", {
      class: "btn btn-gold btn-block mt-8", text: existing ? tr("updateProfile") : tr("createProfile"),
      onclick: async (e) => {
        e.preventDefault();
        const g = (n) => form.querySelector(`[name="${n}"]`) || form.querySelectorAll("input,select,textarea")[0];
        const vals = form.querySelectorAll("input,select,textarea");
        const [profession, city, specialties, bio, phone, , address, yearsExp, website, workHours, mapEmbed, socialRaw] = vals;
        let social = {};
        try { social = JSON.parse(socialRaw.value || "{}"); } catch { social = {}; }
        const payload = {
          profession_type: profession.value,
          city: city.value,
          specialties: specialties.value.split(/[،,]/).map((s) => s.trim()).filter(Boolean).slice(0, 10),
          bio: bio.value,
          phone: phone.value,
          address: address.value,
          years_of_experience: yearsExp.value ? Number(yearsExp.value) : null,
          website: website.value,
          work_hours: workHours.value,
          map_embed: mapEmbed.value,
          social_links: social,
          contact_preference: "visible",
        };
        if (!payload.profession_type) { toast(tr("requiredFields"), "warn"); return; }
        try {
          await api.post("/api/professionals/profile", payload);
          toast(tr("sent"), "success");
        } catch (err) { toast(err.message, "error"); }
      },
    }),
  ]);

  const verifyBtn = el("label", { class: "btn btn-primary btn-block", style: "cursor:pointer" }, [
    icon("paperclip", 16), " " + tr("requestVerification"),
    el("input", { type: "file", accept: ".pdf,.jpg,.jpeg,.png", style: "display:none" }),
  ]);
  verifyBtn.querySelector("input").addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      const fd = new FormData();
      fd.append("document", file);
      await api.uploadFields("/api/professionals/verify-document", fd);
      toast(tr("verificationRequested"), "success");
    } catch (err) { toast(err.message, "error"); }
    e.target.value = "";
  });

  return el("div", {}, [
    el("div", { class: "section-head" }, [
      el("div", {}, [
        el("div", { class: "eyebrow", text: tr("professionalsSub") }),
        el("h2", { text: existing ? tr("updateProfile") : tr("createProfile") }),
      ]),
    ]),
    el("div", { class: "grid", style: "grid-template-columns:1.4fr 1fr;gap:18px" }, [
      el("div", { class: "card" }, [form]),
      el("div", { class: "flex-col" }, [
        el("div", { class: "verify-cta" }, [
          el("h3", {}, [icon("shield", 16), " " + tr("requestVerification")]),
          el("p", { class: "small muted", text: tr("portalProfessionalsD") }),
          verifyBtn,
        ]),
        el("div", { class: "pricing-card" }, [
          el("span", { class: "pc-badge" }, [icon("star", 18, { filled: true })]),
          el("h3", {}, [icon("star", 16, { filled: true }), " " + tr("premiumTitle")]),
          el("ul", [
            el("li", {}, [icon("check", 12), " " + tr("premiumDesc")]),
            el("li", {}, [icon("check", 12), " شارة مميزة في نتائج البحث"]),
          ]),
          premiumCta(),
        ]),
      ]),
    ]),
  ]);
}
