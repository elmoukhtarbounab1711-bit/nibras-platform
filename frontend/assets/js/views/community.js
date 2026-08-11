// نبراس — مجتمع (أسئلة ونقاشات)
import { tr, currentLang } from "../i18n.js";
import { api, session } from "../api.js";
import { el, esc, emptyState, fmtDate, toast, openModal, closeModal, initials, avatarColor } from "../ui.js";
import { openAuth } from "./auth.js";
import { navigate } from "../router.js";
import { icon, iconHTML } from "../icons.js";

export async function communityView(params) {
  const page = Math.max(1, parseInt(params.page || "1", 10) || 1);
  const data = await api.get(`/api/community/posts?limit=15&offset=${(page - 1) * 15}`);
  const posts = Array.isArray(data) ? data : data.posts || [];

  const list = posts.length ? el("div", { class: "flex-col" }, posts.map((p) =>
    el("article", { class: "card post-card" }, [
      el("div", { class: "post-head" }, [
        el("span", { class: "avatar-sm", style: `background:${avatarColor(p.author_name)}`, text: initials(p.author_name) }),
        el("div", { style: "flex:1" }, [
          el("strong", { class: "small", text: p.author_name }),
          p.author_is_verified ? el("span", { class: "verified-badge" }, [icon("check", 12), " " + tr("verified")]) : null,
          el("div", { class: "small muted", text: fmtDate(p.created_at, currentLang()) }),
        ]),
      ]),
      el("h3", { class: "card-title" }, el("a", { href: `#/community/${p.id}`, text: p.title })),
      el("p", { class: "small muted", text: esc(truncate(p.body, 200)) }),
      el("div", { class: "post-actions" }, [
        el("span", { class: "counter" }, [icon("heart", 14), " " + (p.reaction_count ?? 0)]),
        el("span", { class: "counter" }, [icon("messageCircle", 14), " " + (p.comment_count ?? 0)]),
      ]),
    ]))) : emptyState(tr("noResults"), "messageCircle");

  return el("div", {}, [
    el("div", { class: "section-head" }, [
      el("div", {}, [el("h2", { text: tr("communityTitle") }), el("div", { class: "sub", text: tr("communitySub") })]),
      session.token
        ? el("button", { class: "btn btn-primary btn-sm", onclick: () => navigate("/community/new") }, [icon("pen", 14), " " + tr("newPost")])
        : null,
    ]),
    list,
  ]);
}

export async function communityDetailView(params) {
  const post = await api.get(`/api/community/posts/${params.id}`);
  const myReactions = Array.isArray(post.my_reactions) ? post.my_reactions : [];

  const commentsBox = el("div", { class: "mt-16" });
  function renderComments() {
    const comments = Array.isArray(post.comments) ? post.comments : [];
    commentsBox.replaceChildren(
      el("h4", { text: `${tr("commentsCount")} (${comments.length})` }),
      comments.length ? comments.map((c) => el("div", { class: "comment" }, [
        el("span", { class: "avatar-sm", text: initials(c.author_name) }),
        el("div", {}, [
          el("strong", { class: "small", text: c.author_name }),
          el("div", { class: "small muted", text: fmtDate(c.created_at, currentLang()) }),
          el("p", { style: "margin:4px 0 0", text: c.body }),
        ]),
      ])) : [emptyState(tr("noResults"), "messageCircle")],
    );
  }
  renderComments();

  const likeBtn = el("button", { class: `reaction-btn${myReactions.includes("like") ? " active" : ""}` },
    [icon("heart", 14, { filled: myReactions.includes("like") }), " " + tr("like") + ` (${post.reaction_count ?? 0})`]);
  likeBtn.onclick = async () => {
    if (!session.token) return openAuth("login");
    try {
      const r = await api.post(`/api/community/posts/${params.id}/react`, { reaction: "like" });
      const likes = r.reactions?.like ?? 0;
      const active = !!r.reacted && (r.reactions?.like ?? 0) > 0;
      likeBtn.replaceChildren(icon("heart", 14, { filled: active }), " " + tr("like") + ` (${likes})`);
      likeBtn.classList.toggle("active", active);
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
      const created = await api.post(`/api/community/posts/${params.id}/comments`, { body });
      post.comments = post.comments || [];
      post.comments.push(created);
      post.comment_count = (post.comment_count || 0) + 1;
      commentForm.querySelector("input").value = "";
      renderComments();
      toast(tr("sent"), "success");
    } catch (err) { toast(err.message, "error"); }
  });

  return el("div", { class: "post-body" }, [
    el("button", { class: "btn btn-ghost btn-sm mb-16", text: `← ${tr("back")}`, onclick: () => navigate("/community") }),
    el("div", { class: "post-head" }, [
      el("span", { class: "avatar-sm", text: initials(post.author_name) }),
      el("div", {}, [
        el("strong", { class: "small", text: post.author_name }),
        el("div", { class: "small muted", text: fmtDate(post.created_at, currentLang()) }),
      ]),
    ]),
    el("h1", { style: "font-size:24px", text: post.title }),
    el("p", { text: post.body }),
    el("div", { class: "post-toolbar" }, [
      likeBtn,
      el("button", { class: "reaction-btn", onclick: () => reportModal(params.id) }, [icon("flag", 14), " " + tr("report")]),
    ]),
    el("div", { class: "mt-24" }, [
      el("h3", { text: tr("comment") }),
      commentForm,
      commentsBox,
    ]),
  ]);
}

function reportModal(postId) {
  openModal(el("div", {}, [
    el("h2", { text: tr("report") }),
    el("div", { class: "field" }, [
      el("label", { text: tr("reportReason") }),
      el("textarea", { id: "com-report-reason" }),
    ]),
    el("div", { class: "modal-actions" }, [
      el("button", { class: "btn btn-ghost", text: tr("cancel"), onclick: closeModal }),
      el("button", { class: "btn btn-danger", text: tr("send"), onclick: async () => {
        const reason = document.getElementById("com-report-reason").value.trim();
        if (!reason) return toast(tr("reportReason"), "warn");
        try {
          await api.post("/api/community/report", { target_type: "post", target_id: postId, reason });
          toast(tr("sent"), "success");
          closeModal();
        } catch (err) { toast(err.message, "error"); }
      } }),
    ]),
  ]));
}

export async function communityNewView() {
  const cats = await api.get("/api/community/categories");
  const catSel = el("select", {}, (cats || []).map((c) => el("option", { value: c.id, text: c.name })));
  const title = el("input", { placeholder: tr("postTitle") });
  const body = el("textarea", { rows: 6, placeholder: tr("postBody") });

  const form = el("form", { class: "card article-view" }, [
    el("h2", { text: tr("newPost") }),
    el("div", { class: "field" }, [el("label", { text: tr("postTitle") }), title]),
    el("div", { class: "field" }, [el("label", { text: tr("postCategory") }), catSel]),
    el("div", { class: "field" }, [el("label", { text: tr("postBody") }), body]),
    el("div", { class: "modal-actions" }, [
      el("button", { class: "btn btn-ghost", text: tr("cancel"), onclick: () => navigate("/community") }),
      el("button", { class: "btn btn-primary", type: "submit", text: tr("send") }),
    ]),
  ]);
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!session.token) return openAuth("login");
    try {
      const post = await api.post("/api/community/posts", {
        title: title.value.trim(), body: body.value.trim(),
        category_id: catSel.value ? Number(catSel.value) : undefined,
      });
      toast(tr("sent"), "success");
      navigate(`/community/${post.id}`);
    } catch (err) { toast(err.message, "error"); }
  });
  return form;
}

function truncate(s, n) { s = String(s || ""); return s.length > n ? s.slice(0, n).trimEnd() + "…" : s; }
