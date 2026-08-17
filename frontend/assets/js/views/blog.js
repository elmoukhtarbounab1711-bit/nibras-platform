// نبراس — بوابة المقالات القانونية
import { tr, currentLang } from "../i18n.js";
import { api, session } from "../api.js";
import { el, esc, emptyState, fmtDate, pagination, toast, showConfirm, closeModal, openModal, initials } from "../ui.js";
import { icon, iconHTML } from "../icons.js";
import { navigate } from "../router.js";
import { authForm, openAuth } from "./auth.js";
import { isFav, toggleFav } from "../favs.js";

const PER_PAGE = 9;
const COVER_COLORS = ["#1f3a93", "#0f766e", "#9a3412", "#4f46e5", "#0e7490", "#b45309", "#8a5a00", "#7c3aed"];

function coverColor(id) { return COVER_COLORS[Number(id) % COVER_COLORS.length]; }

function blogCard(a) {
  const card = el("article", { class: "card card-hover blog-card" });
  const cover = a.cover_url
    ? `<img src="${esc(a.cover_url)}" alt="" style="width:100%;height:150px;object-fit:cover;border-radius:8px;margin-bottom:12px">`
    : `<div class="cover" style="background:linear-gradient(135deg,${coverColor(a.id)},#0f1e4f)">${esc((a.title || "ن")[0])}</div>`;
  card.innerHTML = `
    ${cover}
    <div class="blog-meta">
      <span class="badge-pill badge-gold">${esc(a.category_name || "")}</span>
      <span>${esc(fmtDate(a.published_at || a.created_at, currentLang()))}</span>
    </div>
    <h3 class="card-title"><a href="#/blog/${a.id}">${esc(a.title)}</a></h3>
    <p class="small muted">${esc((a.summary || a.body || "").slice(0, 120))}…</p>
    <div class="blog-meta">
      <span class="avatar-sm" style="background:${esc((a.author && a.author.id) ? "" : "var(--navy)")}">${esc((a.author?.full_name || "م")[0])}</span>
      <span>${esc(a.author?.full_name || "")}</span>
      ${a.author?.verified ? `<span class="verified-badge">${iconHTML("check", 12)} ${tr("verified")}</span>` : ""}
      <span style="margin-inline-start:auto">${iconHTML("eye", 14)} ${a.views ?? 0} · ${iconHTML("messageCircle", 14)} ${a.comment_count ?? 0}</span>
    </div>`;
  return card;
}

export async function blogView(params) {
  const page = Math.max(1, parseInt(params.page || "1", 10) || 1);
  const category = params.category || "";
  const q = params.q || "";

  const [catsData, data] = await Promise.all([
    api.get("/api/blog/categories"),
    api.get(`/api/blog/articles?limit=${PER_PAGE}&offset=${(page - 1) * PER_PAGE}${category ? `&category=${category}` : ""}${q ? `&q=${encodeURIComponent(q)}` : ""}`),
  ]);
  const articles = data.articles || [];
  const total = data.count || 0;

  const catBar = el("div", { class: "flex mb-16", style: "flex-wrap:gap:8px" }, [
    el("button", { class: `chip${!category ? " active" : ""}`, text: tr("all"), onclick: () => navigate("/blog") }),
    ...(catsData || []).map((c) =>
      el("button", { class: `chip${category === c.slug ? " active" : ""}`, text: c.name,
        onclick: () => navigate(`/blog/cat/${c.slug}`) })),
  ]);

  const searchBox = el("div", { class: "search-bar" }, [
    el("input", { type: "search", placeholder: tr("search"), value: q,
      onkeydown: (e) => { if (e.key === "Enter") navigate(`/blog/q/${encodeURIComponent(e.target.value)}`); } }),
    el("button", { class: "btn btn-primary", text: tr("search"), onclick: () => navigate(`/blog/q/${encodeURIComponent(searchBox.querySelector("input").value)}`) }),
  ]);

  return el("div", {}, [
    el("div", { class: "section-head" }, [
      el("div", {}, [el("h2", { text: tr("homeBlogTitle") }), el("div", { class: "sub", text: tr("homeBlogSub") })]),
      session.token ? el("button", { class: "btn btn-primary btn-sm", onclick: () => navigate("/blog/new") }, [icon("pen", 14), " " + tr("writeArticle")]) : null,
    ]),
    searchBox,
    catBar,
    articles.length ? el("div", { class: "grid grid-3" }, articles.map(blogCard))
      : emptyState(tr("noResults"), "newspaper"),
    pagination(total, page, PER_PAGE, (p) =>
      navigate(`/blog${category ? `/cat/${category}` : ""}${q ? `/q/${encodeURIComponent(q)}` : ""}${p > 1 ? `/page/${p}` : ""}`)),
  ]);
}

function reportModal(articleId) {
  openModal(el("div", {}, [
    el("h2", { text: tr("report") }),
    el("div", { class: "field" }, [
      el("label", { text: tr("reportReason") }),
      el("textarea", { id: "report-reason", placeholder: tr("reportReason") }),
    ]),
    el("div", { class: "modal-actions" }, [
      el("button", { class: "btn btn-ghost", text: tr("cancel"), onclick: closeModal }),
      el("button", { class: "btn btn-danger", text: tr("send"), onclick: async () => {
        const reason = document.getElementById("report-reason").value.trim();
        if (!reason) return toast(tr("reportReason"), "warn");
        try {
          await api.post(`/api/blog/articles/${articleId}/report`, { reason });
          toast(tr("sent"), "success");
          closeModal();
        } catch (err) { toast(err.message, "error"); }
      } }),
    ]),
  ]));
}

export async function blogDetailView(params) {
  const article = await api.get(`/api/blog/articles/${params.id}`);
  const me = session.user;
  const isOwner = me && me.id === article.user_id;
  const isAdmin = session.isAdmin;

  const view = el("div", { class: "post-body" });

  const commentsBox = el("div", { class: "mt-24" }, [el("div", { class: "skeleton", style: "height:60px" })]);

  async function loadComments() {
    try {
      const list = await api.get(`/api/blog/articles/${params.id}/comments`);
      commentsBox.replaceChildren(
        el("h3", { text: `${tr("commentsCount")} (${list.length})` }),
        ...(list.length ? list.map((c) => el("div", { class: "comment" }, [
          el("span", { class: "avatar-sm", text: initials(c.user_name) }),
          el("div", {}, [
            el("strong", { class: "small", text: c.user_name }),
            el("div", { class: "small muted", text: fmtDate(c.created_at, currentLang()) }),
            el("p", { style: "margin:4px 0 0", text: c.body }),
          ]),
        ])) : [emptyState(tr("noResults"), "messageCircle")]),
      );
    } catch (err) { commentsBox.replaceChildren(emptyState(err.message)); }
  }

  const likeBtn = el("button", { class: `reaction-btn${article.liked ? " active" : ""}` },
    [icon("heart", 14, { filled: article.liked }), " " + tr("like") + ` (${article.like_count ?? 0})`]);
  likeBtn.onclick = async () => {
    if (!session.token) return openAuth("login");
    try {
      const r = await api.post(`/api/blog/articles/${params.id}/like`);
      likeBtn.replaceChildren(icon("heart", 14, { filled: r.liked }), " " + tr("like") + ` (${r.likes})`);
      likeBtn.classList.toggle("active", r.liked);
    } catch (err) { toast(err.message, "error"); }
  };

  const commentForm = el("form", { class: "flex mt-8" }, [
    el("input", { placeholder: tr("commentPlaceholder"), style: "flex:1;padding:10px 12px;border:1px solid var(--line);border-radius:8px;background:var(--surface);color:var(--ink)" }),
    el("button", { class: "btn btn-primary", type: "submit", text: tr("send") }),
  ]);
  commentForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!session.token) return openAuth("login");
    const body = commentForm.querySelector("input").value.trim();
    if (!body) return;
    try {
      await api.post(`/api/blog/articles/${params.id}/comments`, { body });
      commentForm.querySelector("input").value = "";
      await loadComments();
      toast(tr("sent"), "success");
    } catch (err) { toast(err.message, "error"); }
  });

  view.append(
    el("button", { class: "btn btn-ghost btn-sm mb-16", text: `← ${tr("back")}`, onclick: () => navigate("/blog") }),
    el("div", { class: "blog-meta" }, [
      el("span", { class: "badge-pill badge-gold", text: article.category_name || "" }),
      el("span", { class: "small", text: fmtDate(article.published_at || article.created_at, currentLang()) }),
      el("span", { class: "small muted" }, [icon("eye", 14), ` ${article.views ?? 0} ${tr("viewsCount")}`]),
      article.status !== "published"
        ? el("span", { class: "badge-pill badge-warn", text: article.status === "pending" ? tr("articleDraft") : tr("articleHidden") })
        : null,
    ]),
    el("h1", { style: "font-size:26px", text: article.title }),
    el("div", { class: "blog-meta" }, [
      el("span", { class: "avatar-sm", text: initials(article.author?.full_name) }),
      el("span", { text: article.author?.full_name }),
      article.author?.verified ? el("span", { class: "verified-badge" }, [icon("check", 12), " " + tr("verified")]) : null,
    ]),
    el("p", { class: "lead", text: article.summary }),
    el("hr", { class: "divider" }),
    ...String(article.body || "").split("\n").filter(Boolean).map((para) => el("p", { text: para })),
    article.keywords ? el("div", { class: "flex mt-16", style: "flex-wrap:gap:6px" }, article.keywords.split(",").filter(Boolean).map((k) =>
      el("span", { class: "chip", text: k.trim() }))) : null,

    el("div", { class: "post-toolbar" }, [
      likeBtn,
      el("button", { class: "reaction-btn", onclick: () => commentsBox.scrollIntoView({ behavior: "smooth" }) }, [icon("messageCircle", 14), ` ${article.comment_count ?? 0} ${tr("commentsCount")}`]),
      el("button", { class: "reaction-btn", onclick: () => reportModal(params.id) }, [icon("flag", 14), " " + tr("report")]),
      (() => {
        const favBtn = el("button", { class: "reaction-btn" }, [icon("star", 14, { filled: isFav("blog", params.id) }), " " + tr("addFav")]);
        favBtn.onclick = () => {
          if (!session.token) return openAuth("login");
          const added = toggleFav("blog", params.id, article.title, `#/blog/${params.id}`);
          favBtn.replaceChildren(icon("star", 14, { filled: added }), " " + (added ? tr("inFav") : tr("addFav")));
          toast(added ? tr("inFav") : tr("saved"), "success");
        };
        return favBtn;
      })(),
      ...(isOwner || isAdmin ? [
        el("button", { class: "reaction-btn", onclick: () => navigate(`/blog/edit/${params.id}`) }, [icon("pen", 14), " " + tr("edit")]),
        el("button", { class: "reaction-btn", style: "color:var(--danger)", onclick: () => showConfirm({ title: tr("delete"), text: article.title,
            onOk: async () => {
              try {
                await api.del(`/api/blog/articles/${params.id}`);
                toast(tr("sent"), "success");
                navigate("/blog/my");
              } catch (err) { toast(err.message, "error"); }
            } }) }, [icon("trash", 14), " " + tr("delete")]),
      ] : []),
    ]),

    el("div", { class: "mt-24" }, [
      el("h3", { text: tr("comment") }),
      commentForm,
      commentsBox,
    ]),
  );

  loadComments();
  return view;
}

export async function myArticlesView() {
  const data = await api.get("/api/blog/my");
  const articles = data.articles || [];
  return el("div", {}, [
    el("div", { class: "section-head" }, [
      el("div", {}, [el("h2", { text: tr("myBlogTitle") }), el("div", { class: "sub", text: tr("articlesSub") })]),
      el("button", { class: "btn btn-primary btn-sm", onclick: () => navigate("/blog/new") }, [icon("pen", 14), " " + tr("writeArticle")]),
    ]),
    articles.length ? el("div", { class: "grid grid-2" }, articles.map((a) => {
      const card = blogCard(a);
      const statusBadge = a.status === "published"
        ? `<span class="badge-pill badge-green">${tr("articlePublished")}</span>`
        : a.status === "hidden"
          ? `<span class="badge-pill badge-gray">${tr("articleHidden")}</span>`
          : `<span class="badge-pill badge-warn">${tr("articleDraft")}</span>`;
      card.insertAdjacentHTML("afterbegin", `<div class="flex-between mb-8">${statusBadge}
        <button class="btn btn-ghost btn-sm" onclick="location.hash='#/blog/edit/${a.id}'">${iconHTML("pen", 14)} ${tr("edit")}</button></div>`);
      return card;
    })) : emptyState(tr("noResults"), "pen"),
  ]);
}

async function fetchCategories() {
  const cats = await api.get("/api/blog/categories");
  return (cats || []).map((c) => el("option", { value: c.id, text: c.name }));
}

export async function blogEditorView(params) {
  const isEdit = !!params.id;
  let article = null;
  if (isEdit) article = await api.get(`/api/blog/articles/${params.id}`);
  const [cats, jurData] = await Promise.all([
    api.get("/api/blog/categories"),
    api.get("/api/comparative/jurisdictions"),
  ]);
  const jurisdictions = jurData.jurisdictions || [];
  const slugOf = (id) => (cats.find((c) => String(c.id) === String(id)) || {}).slug;

  const titleInput = el("input", { value: article?.title || "", placeholder: "عنوان المقال" });
  const summaryInput = el("textarea", { rows: 2, placeholder: "ملخص قصير" }, article?.summary || "");
  const bodyInput = el("textarea", { rows: 14, placeholder: "نص المقال..." }, article?.body || "");
  const keywordsInput = el("input", { value: article?.keywords || "", placeholder: "كلمات مفتاحية مفصولة بفاصلة" });
  const catSelect = el("select", {}, (cats || []).map((c) => el("option", { value: c.id, text: c.name })));
  if (article?.category_id) catSelect.value = article.category_id;
  const jurSelect = el("select", {}, [
    el("option", { value: "", text: "اختر الدولة" }),
    ...jurisdictions.map((j) => el("option", { value: j.id, text: j.name })),
  ]);
  if (article?.jurisdiction_id) jurSelect.value = String(article.jurisdiction_id);
  const jurField = el("div", { class: "field", style: "display:none" }, [
    el("label", { text: "الدولة (فئة الدراسات المقارنة)" }),
    jurSelect,
  ]);
  const syncJurField = () => {
    jurField.style.display = (slugOf(catSelect.value) === "comparative") ? "" : "none";
  };
  syncJurField();
  catSelect.onchange = syncJurField;

  const form = el("form", { class: "card article-view" }, [
    el("h2", { text: isEdit ? tr("edit") : tr("writeArticle") }),
    el("div", { class: "field" }, [el("label", { text: tr("title") }), titleInput]),
    el("div", { class: "field" }, [el("label", { text: tr("postCategory") }), catSelect]),
    jurField,
    el("div", { class: "field" }, [el("label", { text: "الملخص" }), summaryInput]),
    el("div", { class: "field" }, [el("label", { text: tr("postBody") }), bodyInput]),
    el("div", { class: "field" }, [el("label", { text: "الكلمات المفتاحية" }), keywordsInput]),
    el("div", { class: "modal-actions" }, [
      el("button", { class: "btn btn-ghost", text: tr("cancel"), onclick: () => navigate(isEdit ? `/blog/${params.id}` : "/blog/my") }),
      el("button", { class: "btn btn-primary", type: "submit", text: tr("save") }),
    ]),
  ]);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      title: titleInput.value.trim(),
      body: bodyInput.value.trim(),
      summary: summaryInput.value.trim(),
      keywords: keywordsInput.value.trim(),
      category_id: catSelect.value ? Number(catSelect.value) : undefined,
      jurisdiction_id: jurSelect.value ? Number(jurSelect.value) : undefined,
    };
    try {
      if (isEdit) {
        await api.put(`/api/blog/articles/${params.id}`, payload);
        toast(tr("sent"), "success");
        navigate(`/blog/${params.id}`);
      } else {
        const r = await api.post("/api/blog/articles", payload);
        toast(tr("sent"), "success");
        navigate(`/blog/my`);
      }
    } catch (err) { toast(err.message, "error"); }
  });

  return form;
}
