// نبراس — الإشعارات (قائمة حديثة + إعدادات التسليم الخارجي)
import { tr, currentLang } from "../i18n.js";
import { api } from "../api.js";
import { el, emptyState, fmtDate, toast } from "../ui.js";
import { icon } from "../icons.js";

const TYPE_ICONS = {
  "verification.approved": "shield",
  "verification.rejected": "shield",
  "community.comment": "messageCircle",
  "community.reaction": "heart",
  "moderation.content_hidden": "ban",
  "moderation.content_removed": "trash",
};

const CHANNELS = ["email", "push"];
const TYPE_LABELS = {
  "verification.approved": ["قبول التحقق", "Vérification approuvée"],
  "verification.rejected": ["رفض التحقق", "Vérification rejetée"],
  "community.comment": ["تعليق جديد", "Nouveau commentaire"],
  "community.reaction": ["تفاعل جديد", "Nouvelle réaction"],
  "moderation.content_hidden": ["إخفاء محتوى", "Contenu masqué"],
  "moderation.content_removed": ["حذف محتوى", "Contenu supprimé"],
};
const fr = () => currentLang() === "fr";
const typeLabel = (t) => (TYPE_LABELS[t] ? TYPE_LABELS[t][fr() ? 1 : 0] : t || "");

function notifItem(n) {
  const row = el("article", { class: `notif-item${n.is_read ? " read" : ""}` }, [
    el("div", { class: "notif-icon" }, [icon(TYPE_ICONS[n.type] || "bell", 20)]),
    el("div", { class: "notif-body" }, [
      el("div", { class: "notif-title" }, [
        el("strong", { text: n.title }),
        !n.is_read ? el("span", { class: "notif-dot" }) : null,
      ]),
      n.body ? el("div", { class: "notif-text", text: n.body }) : null,
      el("div", { class: "notif-time" }, [
        typeLabel(n.type) ? el("span", { class: "spec-tag", text: typeLabel(n.type) }) : null,
        el("span", { text: fmtDate(n.created_at, currentLang()) }),
      ]),
    ]),
    !n.is_read ? el("button", { class: "btn btn-ghost btn-sm", text: tr("markRead"), onclick: async (e) => {
      try {
        await api.post(`/api/notifications/${n.id}/read`);
        n.is_read = true;
        e.currentTarget.remove();
        row.classList.add("read");
        toast(tr("saved"), "success");
      } catch (err) { toast(err.message, "error"); }
    } }) : null,
  ]);
  return row;
}

async function settingsCard() {
  const [prefsData, devData] = await Promise.all([
    api.get("/api/notifications/preferences").catch(() => null),
    api.get("/api/notifications/devices").catch(() => null),
  ]);
  const prefs = (prefsData && prefsData.preferences) || {};
  const devices = (devData && devData.devices) || [];

  const grid = el("div", { class: "flex-col" });
  for (const ch of CHANNELS) {
    grid.append(el("div", { class: "card", style: "margin-bottom:14px" }, [
      el("h3", { style: "font-size:16px" }, [icon(ch === "email" ? "mail" : "bell", 18), ` ${ch === "email" ? tr("channelEmail") : tr("channelPush")}`]),
      el("div", { class: "flex-col" },
        Object.keys(TYPE_LABELS).map((t) => {
          const sw = el("label", { class: "switch", "data-t": t }, [
            el("input", { type: "checkbox", "data-channel": ch, "data-t": t, checked: !!(prefs[ch] && prefs[ch][t]) }),
            el("span", { class: "slider" }),
          ]);
          return el("div", { class: "flex-between", style: "padding:8px 0;border-bottom:1px solid var(--line)" }, [
            el("span", { class: "small", text: typeLabel(t) }),
            sw,
          ]);
        })),
      el("div", { class: "flex mt-8", style: "gap:8px" }, [
        el("button", { class: "btn btn-ghost btn-sm", text: tr("prefOffAll"), onclick: (e) => e.target.closest(".card").querySelectorAll('.switch input').forEach((i) => { i.checked = false; }) }),
        el("button", { class: "btn btn-ghost btn-sm", text: tr("prefOnAll"), onclick: (e) => e.target.closest(".card").querySelectorAll('.switch input').forEach((i) => { i.checked = true; }) }),
      ]),
    ]));
  }

  const saveBtn = el("button", { class: "btn btn-primary", text: tr("save"), onclick: async () => {
    const list = [];
    grid.querySelectorAll('.switch input').forEach((i) => {
      list.push({ channel: i.dataset.channel, notification_type: i.dataset.t, enabled: i.checked });
    });
    try {
      await api.put("/api/notifications/preferences", { preferences: list });
      toast(tr("prefSaved"), "success");
    } catch (err) { toast(err.message, "error"); }
  } });

  const devicesCard = el("div", { class: "card", style: "margin-top:14px" }, [
    el("h3", { style: "font-size:16px" }, [icon("smartphone", 18), " " + tr("channelPush")]),
    devices.length
      ? el("div", { class: "flex-col" }, devices.map((d) =>
          el("div", { class: "flex-between", style: "padding:8px 0;border-bottom:1px solid var(--line)" }, [
            el("span", { class: "small", text: `${d.platform || "web"} · ${d.token ? d.token.slice(0, 18) + "…" : "—"}` }),
            el("button", { class: "btn btn-ghost btn-sm", onclick: async () => {
              try { await api.del(`/api/notifications/devices/${d.id}`); location.hash = "#/notifications/settings"; toast(tr("saved"), "success"); }
              catch (err) { toast(err.message, "error"); }
            } }, [icon("x", 14)]),
          ])))
      : el("div", { class: "small muted", text: tr("noNotifications") }),
  ]);

  return el("div", { class: "card" }, [
    el("h2", { text: tr("deliverySettings") }),
    el("p", { class: "small muted", style: "margin-bottom:12px", text: tr("prefInAppNote") }),
    grid,
    saveBtn,
    devicesCard,
  ]);
}

export async function notificationsSettingsView() {
  return el("div", {}, [
    el("button", { class: "btn btn-ghost btn-sm mb-16", text: `→ ${tr("notificationsTitle")}`, onclick: () => { location.hash = "#/notifications"; } }),
    await settingsCard(),
  ]);
}

export async function notificationsView() {
  const data = await api.get("/api/notifications");
  const items = Array.isArray(data) ? data : data.notifications || [];
  const unread = items.filter((n) => !n.is_read).length;

  const tabBtn = (label, active, onclick) => el("button", { class: `chip${active ? " active" : ""}`, text: label, onclick });
  const notifTab = tabBtn(tr("notificationsTitle"), true, () => { location.hash = "#/notifications"; });
  const settingsTab = tabBtn(tr("deliverySettings"), false, () => { location.hash = "#/notifications/settings"; });

  return el("div", {}, [
    el("div", { class: "section-head" }, [
      el("div", {}, [el("h2", { text: tr("notificationsTitle") }), el("div", { class: "sub", text: tr("notificationsSub") })]),
      unread > 0 ? el("span", { class: "badge-pill badge-gold", text: `${unread}` }) : null,
    ]),
    el("div", { class: "flex mb-16", style: "gap:8px" }, [notifTab, settingsTab]),
    el("div", {}, [
      unread > 0
        ? el("button", { class: "btn btn-outline btn-sm mb-16", text: tr("markAllRead"), onclick: async () => {
            try {
              await api.post("/api/notifications/read-all");
              toast(tr("saved"), "success");
              location.hash = "#/notifications";
            } catch (err) { toast(err.message, "error"); }
          } })
        : null,
      items.length ? el("div", { class: "flex-col" }, items.map(notifItem)) : emptyState(tr("noNotifications"), "bell"),
    ]),
  ]);
}
