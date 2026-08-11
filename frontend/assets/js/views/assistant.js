// نبراس — المساعد القانوني (v2): محادثة موثقة بالمصادر + رفع PDF
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

/* ---------- استخراج نص PDF (عبر pdf.js من داخل المتصفح) ---------- */
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

function sendMessage(input, modeBtn, attachWrap) {
  const q = input.value.trim();
  if (!q && !state._pendingPdf) return;
  const chat = currentChat();
  if (!chat) return;

  let question = q;
  if (state._pendingPdf) {
    question = q
      ? `${q}\n\n--- ${tr("extractedFromPdf")} ---\n${state._pendingPdf}`
      : `حلّل المستند التالي واشرحه:\n${state._pendingPdf}`;
    state._pendingPdf = null;
    attachWrap.querySelector(".attach-name").textContent = "";
  }

  chat.messages.push({ role: "user", text: question });
  renderMessages();
  input.value = "";
  input.disabled = true;
  modeBtn.disabled = true;

  const typing = renderTyping();
  api.post("/api/ai/explain", {
    question,
    mode: modeBtn.dataset.mode || "grounded",
  }).then((data) => {
    typing.remove();
    chat.messages.push({
      role: "ai",
      text: data.answer || "",
      cites: Array.isArray(data.cited_article_ids) ? data.cited_article_ids : [],
      decises: Array.isArray(data.cited_decision_ids) ? data.cited_decision_ids : [],
      external: Array.isArray(data.external_sources) ? data.external_sources : [],
      status: data.status || "ok",
    });
    if (chat.messages.length === 2) chat.title = q.slice(0, 40);
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
    const bubble = el("div", { class: "bubble", text: msg.text });
    const row = el("div", { class: `chat-msg ${msg.role}` }, [bubble]);
    if (msg.role === "ai") {
      if (msg.error) bubble.style.background = "var(--danger-bg)";
      else {
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
        // أرسل مباشرة
        const fake = { value: p, disabled: false };
        sendMessage(fake, modeBtn, attachWrap);
      },
    }));
  }
}

function attachLogic(attachWrap, input) {
  const fileInput = attachWrap.querySelector("input[type=file]");
  const nameEl = attachWrap.querySelector(".attach-name");
  fileInput.addEventListener("change", async () => {
    const file = fileInput.files[0];
    if (!file) return;
    try {
      if (file.type === "application/pdf" || /\.pdf$/i.test(file.name)) {
        toast(tr("loading"));
        const text = await extractPdfText(file);
        if (!text) { toast(tr("noResults"), "warn"); return; }
        state._pendingPdf = text;
        nameEl.replaceChildren(icon("paperclip", 14), " " + file.name);
        toast("PDF OK", "success");
      } else {
        nameEl.replaceChildren(icon("paperclip", 14), " " + file.name + " " + tr("docxNote"));
        state._pendingPdf = null;
        toast(tr("docxNote"), "warn");
      }
    } catch { toast(tr("error"), "error"); }
    fileInput.value = "";
  });
}

export function assistantView() {
  const MODES = ["grounded", "research", "general"];
  const MODE_META = {
    grounded: { icon: "target", labelKey: "groundedMode" },
    research: { icon: "globe", labelKey: "researchMode" },
    general: { icon: "messageCircle", labelKey: "generalMode" },
  };
  const paintMode = (btn, mode) => {
    const meta = MODE_META[mode];
    btn.replaceChildren(icon(meta.icon, 14), " " + tr(meta.labelKey));
    btn.title = tr(mode + "Hint");
  };
  const modeBtn = el("button", { class: "chat-mode on", dataset: { mode: "grounded" } });
  paintMode(modeBtn, "grounded");
  modeBtn.addEventListener("click", () => {
    const next = MODES[(MODES.indexOf(modeBtn.dataset.mode) + 1) % MODES.length];
    modeBtn.dataset.mode = next;
    modeBtn.classList.toggle("on", next === "grounded");
    paintMode(modeBtn, next);
  });

  const input = el("input", { placeholder: tr("chatPlaceholder"), "aria-label": tr("chatPlaceholder") });
  const attachWrap = el("div", { class: "chat-attach" }, [
    el("button", { class: "btn btn-ghost btn-sm", type: "button" }, [icon("paperclip", 14)]),
    el("input", { type: "file", accept: ".pdf,.docx", "aria-label": tr("uploadPdf") }),
  ]);
  const attachName = el("span", { class: "attach-name small muted" });
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
        el("div", { class: "small muted", style: "padding:0 18px 12px", text: attachName }),
      ]),
    ]),
  ]);

  // بعد الإدراج في DOM
  requestAnimationFrame(() => { renderSessions(); renderMessages(); renderSuggestions(attachWrap, modeBtn); });

  return view;
}
