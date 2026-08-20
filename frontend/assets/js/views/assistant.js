// نبراس — المساعد القانوني (v3): محادثة موثقة بالمصادر + رفع PDF + صور
import { tr, currentLang } from "../i18n.js";
import { api, session } from "../api.js";
import { el, esc, toast } from "../ui.js";
import { icon } from "../icons.js";

const STORE_KEY = "nibras_chats";

function loadChats() {
  try { return JSON.parse(localStorage.getItem(STORE_KEY) || "[]"); } catch { return []; }
}
function saveChats(chats) { localStorage.setItem(STORE_KEY, JSON.stringify(chats)); }

let state = { chats: [], activeId: null };

function newSession() {
  const id = "c" + Date.now();
  state.chats.unshift({ id, title: tr("newChat"), messages: [] });
  saveChats(state.chats);
  state.activeId = id;
  return id;
}
function currentChat() { return state.chats.find((c) => c.id === state.activeId) || null; }

/* ── استخراج نص PDF (محلياً عبر pdf.js كخطة احتياطية) ── */
async function extractPdfText(file) {
  const lib = window.pdfjsLib;
  if (!lib) throw new Error("PDF engine not loaded");
  const url = URL.createObjectURL(file);
  try {
    const doc = await lib.getDocument({ url }).promise;
    let text = "";
    const max = Math.min(doc.numPages, 30);
    for (let i = 1; i <= max; i++) {
      const page = await doc.getPage(i);
      const content = await page.getTextContent();
      text += content.items.map((it) => it.str || "").join(" ") + "\n";
    }
    return text.trim().slice(0, 18000);
  } finally { URL.revokeObjectURL(url); }
}

/* ── إرسال مرفق (PDF/صورة) للخادم ── */
async function sendAttachment(file, question, mode) {
  const fd = new FormData();
  fd.append("file", file);
  if (question) fd.append("question", question);
  return api.uploadFields("/api/ai/explain-attachment", fd);
}

/* ── إرسال رسالة نصية (كما كان) ── */
function sendTextMessage(question, mode) {
  return api.post("/api/ai/explain", { question, mode });
}

function sendMessage(input, modeBtn, attachWrap) {
  const q = input.value.trim();
  const pendingFile = state._pendingFile;
  const pendingPreview = state._pendingPreview;
  if (!q && !pendingFile) return;
  const chat = currentChat();
  if (!chat) return;

  /* ── بناء رسالة المستخدم ── */
  const userMsg = { role: "user", text: q || "" };
  if (pendingPreview) {
    userMsg.attachment = pendingPreview;
  }

  chat.messages.push(userMsg);
  renderMessages();
  input.value = "";
  input.disabled = true;
  modeBtn.disabled = true;

  /* ── تنظيف الحالة المؤقتة ── */
  state._pendingFile = null;
  state._pendingPreview = null;
  attachWrap.querySelector(".attach-name").textContent = "";
  attachWrap.querySelector(".attach-preview")?.remove();

  const mode = modeBtn.dataset.mode || "auto";
  const typing = renderTyping();

  let apiCall;
  if (pendingFile) {
    apiCall = sendAttachment(pendingFile, q, mode);
  } else {
    apiCall = sendTextMessage(q, mode);
  }

  apiCall.then((data) => {
    typing.remove();
    chat.messages.push({
      role: "ai",
      text: data.answer || "",
      cites: Array.isArray(data.cited_article_ids) ? data.cited_article_ids : [],
      decises: Array.isArray(data.cited_decision_ids) ? data.cited_decision_ids : [],
      external: Array.isArray(data.external_sources) ? data.external_sources : [],
      source: data.source || null,
      status: data.status || "ok",
    });
    if (chat.messages.length === 2) chat.title = (q || "مرفق").slice(0, 40);
    saveChats(state.chats);
    renderMessages();
  }).catch((err) => {
    typing.remove();
    toast(err.message || tr("error"), "error");
    chat.messages.push({ role: "ai", text: err.message || tr("error"), cites: [], error: true });
    saveChats(state.chats);
    renderMessages();
  }).finally(() => {
    input.disabled = false;
    modeBtn.disabled = false;
  });
}

function renderTyping() {
  const t = el("div", { class: "chat-msg ai" }, [el("div", { class: "chat-typing" }, [
    el("span"), el("span"), el("span")])]);
  document.getElementById("chat-messages").append(t);
  scrollBottom();
  return t;
}

function scrollBottom() {
  const m = document.getElementById("chat-messages");
  if (m) m.scrollTop = m.scrollHeight;
}

function citeLinks(cites) {
  if (!cites.length) return el("div", { class: "small muted", text: tr("noCitations") });
  return el("div", { class: "cite" }, [
    el("span", { class: "small muted", text: `${tr("citations")}:` }),
    ...cites.map((id) => el("a", { class: "cite-link", href: `#/text/${id}`, text: `§ ${id}` })),
  ]);
}

function decisionCiteLinks(decises) {
  if (!decises.length) return null;
  return el("div", { class: "cite" }, [
    el("span", { class: "small muted", text: `${tr("decisionCitations")}:` }),
    ...decises.map((id) => el("a", { class: "cite-link cite-decision", href: `#/jurisprudence/${id}`, text: `⚖ ${id}` })),
  ]);
}

function externalLinks(external) {
  if (!external || !external.length) return null;
  const items = external.map((s, i) => el("a", {
    class: "ext-link", href: s.url, target: "_blank", rel: "noopener",
    text: `[${i + 1}] ${s.title || s.source || s.url}`,
  }));
  return el("div", { class: "ext-src" }, [
    el("span", { class: "small muted", text: `${tr("externalSources")}:` }),
    ...items,
  ]);
}

function sourceBadge(source) {
  const MAP = {
    nibras: { label: tr("sourceNibras"), cls: "source-nibras", official: true },
    web: { label: tr("sourceWeb"), cls: "source-web", official: false },
    general: { label: tr("sourceGeneral"), cls: "source-general", official: false },
    attachment: { label: "مرفق", cls: "source-web", official: false },
  };
  const m = MAP[source] || MAP.general;
  const badge = el("div", { class: `source-badge ${m.cls}`, text: m.label });
  if (m.official) {
    const note = el("div", {
      class: "small",
      style: "margin-top:4px;color:#2d3748;font-size:11px;",
      text: "المواد المرفقة مستخرجة من مصادرها الرسمية — لا تمر عبر AI لإعادة الصياغة",
    });
    return el("div", {}, [badge, note]);
  }
  return badge;
}

function renderMessages() {
  const wrap = document.getElementById("chat-messages");
  const chat = currentChat();
  if (!chat) return;
  wrap.replaceChildren();
  if (!chat.messages.length) {
    wrap.append(el("div", { class: "ta-center muted", style: "margin:auto;max-width:440px" }, [
      el("div", { style: "display:flex;justify-content:center;margin-bottom:6px" }, [icon("scale", 38)]),
      el("div", { class: "fw-800", style: "font-size:17px;color:var(--ink)", text: tr("assistantStart") }),
      el("div", { class: "small", style: "margin-top:6px", text: tr("assistantStartText") }),
    ]));
    return;
  }
  for (const msg of chat.messages) {
    const bubble = el("div", { class: "bubble" });
    if (msg.text) bubble.append(document.createTextNode(msg.text));

    /* ── عرض صورة مرفقة ── */
    if (msg.attachment && msg.attachment.type === "image") {
      const imgWrap = el("div", { style: "margin-top:8px" }, [
        el("img", {
          src: msg.attachment.dataUrl,
          style: "max-width:260px;max-height:200px;border-radius:8px;border:1px solid var(--line);object-fit:cover",
          alt: msg.attachment.name || "مرفق",
        }),
      ]);
      if (msg.attachment.name) {
        imgWrap.append(el("div", { class: "small muted", style: "margin-top:2px", text: msg.attachment.name }));
      }
      bubble.append(imgWrap);
    }

    /* ── عرض اسم ملف PDF ── */
    if (msg.attachment && msg.attachment.type === "pdf") {
      const fileTag = el("div", {
        style: "display:inline-flex;align-items:center;gap:6px;padding:6px 12px;"
          + "background:var(--info-bg);border-radius:8px;margin-top:6px;font-size:0.82rem",
      }, [
        icon("file", 14),
        document.createTextNode(msg.attachment.name || "PDF"),
      ]);
      bubble.append(fileTag);
    }

    const row = el("div", { class: `chat-msg ${msg.role}` }, [bubble]);
    if (msg.role === "ai") {
      if (msg.error) bubble.style.background = "var(--danger-bg)";
      else {
        if (msg.source) row.append(sourceBadge(msg.source));
        const decLinks = decisionCiteLinks(msg.decises || []);
        if (decLinks) row.append(decLinks);
        row.append(citeLinks(msg.cites));
      }
      if (!msg.error && msg.external && msg.external.length) row.append(externalLinks(msg.external));
    }
    wrap.append(row);
  }
  scrollBottom();
}

function renderSessions() {
  const side = document.getElementById("chat-sessions");
  side.replaceChildren();
  for (const c of state.chats) {
    side.append(el("div", { class: `chat-session${c.id === state.activeId ? " active" : ""}` }, [
      el("span", { style: "flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap", text: c.title, onclick: () => { state.activeId = c.id; renderMessages(); renderSessions(); } }),
      el("button", {
        class: "del", title: tr("deleteChat"), onclick: () => {
          state.chats = state.chats.filter((x) => x.id !== c.id);
          if (state.activeId === c.id) state.activeId = state.chats[0]?.id || newSession();
          saveChats(state.chats); renderSessions(); renderMessages();
        },
      }, [icon("x", 14)]),
    ]));
  }
}

function renderSuggestions(attachWrap, modeBtn) {
  const box = document.getElementById("chat-suggestions");
  const prompts = [1, 2, 3, 4].map((n) => tr(`suggest${n}`));
  box.replaceChildren(el("span", { class: "small muted", text: `${tr("suggestedPrompts")}:` }));
  for (const p of prompts) {
    box.append(el("button", {
      class: "chip-suggest", text: p,
      onclick: () => {
        const chat = currentChat() || (state.activeId = newSession(), currentChat());
        chat.messages.push({ role: "user", text: p });
        saveChats(state.chats);
        renderMessages();
        const fake = { value: p, disabled: false };
        sendMessage(fake, modeBtn, attachWrap);
      },
    }));
  }
}

/* ── منطق رفع الملفات (PDF + صور JPEG/PNG) ── */
function attachLogic(attachWrap, input) {
  const fileInput = attachWrap.querySelector("input[type=file]");
  const nameEl = attachWrap.querySelector(".attach-name");

  fileInput.addEventListener("change", () => {
    const file = fileInput.files[0];
    if (!file) return;

    const isPdf = file.type === "application/pdf" || /\.pdf$/i.test(file.name);
    const isImage = /^image\/(jpeg|png|jpe?g)$/i.test(file.type)
      || /\.(jpg|jpeg|png)$/i.test(file.name);

    if (!isPdf && !isImage) {
      toast(tr("docxNote") || "نوع الملف غير مدعوم. الرجاء إرفاق PDF أو صورة (JPEG/PNG)", "warn");
      fileInput.value = "";
      return;
    }

    state._pendingFile = file;

    if (isImage) {
      /* ── معاينة الصورة ── */
      const reader = new FileReader();
      reader.onload = () => {
        state._pendingPreview = { type: "image", dataUrl: reader.result, name: file.name };
        nameEl.replaceChildren(icon("paperclip", 14), " " + file.name);
        /* إضافة معاينة بصرية */
        let preview = attachWrap.querySelector(".attach-preview");
        if (!preview) {
          preview = el("div", { class: "attach-preview", style: "margin-top:6px" });
          attachWrap.append(preview);
        }
        preview.replaceChildren(
          el("img", {
            src: reader.result,
            style: "max-width:120px;max-height:80px;border-radius:6px;border:1px solid var(--line);object-fit:cover",
            alt: file.name,
          }),
          el("button", {
            style: "margin-inline-start:8px;background:none;border:none;color:var(--danger);cursor:pointer;font-size:16px",
            text: "✕",
            title: "إزالة المرفق",
            onclick: () => {
              state._pendingFile = null;
              state._pendingPreview = null;
              nameEl.textContent = "";
              preview.replaceChildren();
              fileInput.value = "";
            },
          })
        );
        toast("تم إرفاق الصورة", "success");
      };
      reader.readAsDataURL(file);
    } else if (isPdf) {
      /* ── PDF: رفع للخادم للاستخراج ── */
      state._pendingPreview = { type: "pdf", name: file.name };
      nameEl.replaceChildren(icon("paperclip", 14), " " + file.name);
      toast("تم إرفاق ملف PDF", "success");
    }

    fileInput.value = "";
  });
}

export function assistantView() {
  const MODES = ["auto", "grounded", "research", "general"];
  const MODE_META = {
    auto: { icon: "zap", labelKey: "autoMode" },
    grounded: { icon: "target", labelKey: "groundedMode" },
    research: { icon: "globe", labelKey: "researchMode" },
    general: { icon: "messageCircle", labelKey: "generalMode" },
  };
  const paintMode = (btn, mode) => {
    const meta = MODE_META[mode];
    btn.replaceChildren(icon(meta.icon, 14), " " + tr(meta.labelKey));
    btn.title = tr(mode + "Hint");
  };
  const modeBtn = el("button", { class: "chat-mode on", dataset: { mode: "auto" } });
  paintMode(modeBtn, "auto");
  modeBtn.addEventListener("click", () => {
    const next = MODES[(MODES.indexOf(modeBtn.dataset.mode) + 1) % MODES.length];
    modeBtn.dataset.mode = next;
    modeBtn.classList.toggle("on", next === "grounded");
    paintMode(modeBtn, next);
  });

  const input = el("input", { placeholder: tr("chatPlaceholder"), "aria-label": tr("chatPlaceholder") });
  const attachWrap = el("div", { class: "chat-attach" }, [
    el("button", { class: "btn btn-ghost btn-sm", type: "button", title: "إرفاق ملف (PDF أو صورة)" }, [icon("paperclip", 14)]),
    el("input", { type: "file", accept: ".pdf,.jpg,.jpeg,.png", "aria-label": "إرفاق ملف" }),
    el("span", { class: "attach-name small muted" }),
  ]);
  const attachName = attachWrap.querySelector(".attach-name");
  attachLogic(attachWrap, input);

  input.addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(input, modeBtn, attachWrap); } });

  if (!state.chats.length) newSession();
  const active = currentChat();

  const view = el("div", {}, [
    el("div", { class: "section-head" }, [
      el("div", {}, [
        el("div", { class: "eyebrow", text: tr("assistantSub") }),
        el("h2", { text: tr("assistantTitle") }),
      ]),
    ]),

    el("div", { class: "chat-shell" }, [
      /* الشريط الجانبي */
      el("aside", { class: "chat-side" }, [
        el("button", { class: "btn btn-primary btn-sm", text: `+ ${tr("newChat")}`, onclick: () => { newSession(); renderSessions(); renderMessages(); } }),
        el("h3", { text: tr("chatHistory") }),
        el("div", { id: "chat-sessions", class: "flex-col", style: "gap:4px;overflow-y:auto;max-height:48vh" }),
      ]),
      /* المحادثة */
      el("div", { class: "chat-main" }, [
        el("div", { class: "chat-messages", id: "chat-messages" }),
        el("div", { class: "chat-suggestions", id: "chat-suggestions" }),
        el("div", { class: "chat-inputbar" }, [
          attachWrap,
          input,
          modeBtn,
          el("button", { class: "btn btn-primary", text: tr("send"), onclick: () => sendMessage(input, modeBtn, attachWrap) }),
        ]),
      ]),
    ]),
  ]);

  requestAnimationFrame(() => { renderSessions(); renderMessages(); renderSuggestions(attachWrap, modeBtn); });

  return view;
}
