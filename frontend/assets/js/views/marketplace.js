// نبراس — نماذج العقود والالتزامات الجاهزة (v2): كتالوج + تفاصيل + شراء/تحميل
import { tr, currentLang } from "../i18n.js";
import { api } from "../api.js";
import { el, esc, emptyState, toast, fmtDate } from "../ui.js";
import { icon, iconHTML } from "../icons.js";

const BUYS_KEY = "nibras_purchases";
const cents = (n) => (Number(n || 0) / 100);
const isBought = (id) => { try { return (JSON.parse(localStorage.getItem(BUYS_KEY) || "[]")).includes(Number(id)); } catch { return false; } };
const markBought = (id) => { const a = JSON.parse(localStorage.getItem(BUYS_KEY) || "[]"); if (!a.includes(Number(id))) { a.push(Number(id)); localStorage.setItem(BUYS_KEY, JSON.stringify(a)); } };

function priceLabel(t) {
  const p = cents(t.price_cents);
  return p > 0
    ? el("span", { class: "mkt-price", text: `${p.toLocaleString(langIsFr() ? "fr-MA" : "ar-MA")} ${langIsFr() ? "MAD" : "درهم"}` })
    : el("span", { class: "price-free", text: tr("free") });
}
const langIsFr = () => currentLang() === "fr";

function cover(t, big = false) {
  return t.image_url
    ? el("img", { src: t.image_url, alt: t.title, style: `width:100%;height:${big ? 220 : 120}px;object-fit:cover;border-radius:10px;margin-bottom:10px` })
    : el("div", { class: "tile-cover doc", style: `height:${big ? 220 : 120}px;margin-bottom:10px` }, [icon("file", big ? 56 : 32)]);
}

export async function marketplaceView(params) {
  if (params.id) return detailView(params.id);

  const [cats, data] = await Promise.all([
    api.get("/api/marketplace/categories"),
    api.get("/api/marketplace/templates"),
  ]);
  const list = Array.isArray(data) ? data : data.templates || [];

  const grid = el("div", { class: "grid grid-3" });
  const render = (items) => {
    if (items.length) {
      grid.replaceChildren(...items.map((t) => el("article", { class: "card card-hover mkt-card" }, [
        cover(t),
        el("h3", { class: "card-title", style: "margin-bottom:4px" }, el("a", { href: `#/marketplace/${t.id}`, text: t.title })),
        el("p", { class: "small muted", style: "flex:1", text: esc(truncate(t.description, 110)) }),
        el("div", { class: "flex-between mt-8" }, [
          priceLabel(t),
          el("span", { class: "small muted" }, [icon("download", 14), ` ${t.download_count ?? 0} · `, icon("star", 14, { filled: true }), ` ${(t.rating ?? 0).toFixed(1)}`]),
        ]),
        el("button", { class: "btn btn-gold btn-block mt-8 btn-sm", text: tr("preview"), onclick: () => { location.hash = `#/marketplace/${t.id}`; } }),
      ])));
    } else {
      grid.replaceChildren(emptyState(tr("noResults"), "clipboard"));
    }
  };

  const setActive = (btn) => { catBar.querySelectorAll(".chip").forEach((c) => c.classList.remove("active")); btn.classList.add("active"); };
  const catBar = el("div", { class: "flex mb-16", style: "flex-wrap:gap:8px" }, [
    el("button", { class: "chip active", text: tr("all"), onclick: (e) => { setActive(e.target); render(list); } }),
    ...(cats || []).map((c) => el("button", {
      class: "chip", text: c.name,
      onclick: (e) => {
        setActive(e.target);
        render(list.filter((t) => t.category_id === c.id));
      },
    })),
  ]);

  render(list);

  return el("div", {}, [
    el("div", { class: "section-head" }, [
      el("div", {}, [
        el("div", { class: "eyebrow", text: tr("templatesSub") }),
        el("h2", { text: tr("templatesTitle") }),
      ]),
    ]),
    catBar,
    grid,
  ]);
}

async function detailView(id) {
  const t = await api.get(`/api/marketplace/templates/${id}`);
  const bought = isBought(id);
  const price = cents(t.price_cents);

  const download = () => {
    const blob = new Blob([`${t.title}\n\n${t.description || ""}\n\n— ${tr("templatesTitle")} — نبراس`], { type: "text/plain;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${t.title.replace(/[^\w\u0600-\u06FF\s-]/g, "").trim().replace(/\s+/g, "-") || "modele"}.txt`;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  const buyBtn = el("button", {
    class: "btn btn-gold btn-block",
    onclick: () => {
      if (price > 0 && !bought) {
        markBought(id);
        toast(tr("purchased"), "success");
        buyBtn.replaceChildren(icon("download", 16), " " + tr("downloadNow"));
        download();
      } else {
        download();
      }
    },
  }, [icon(price > 0 && !bought ? "shoppingCart" : "download", 16), " " + (price > 0 && !bought ? tr("buyNow") : tr("downloadNow"))]);

  return el("div", {}, [
    el("button", { class: "btn btn-ghost btn-sm mb-16", text: `→ ${tr("templatesTitle")}`, onclick: () => { location.hash = "#/marketplace"; } }),
    el("div", { class: "grid", style: "grid-template-columns:1fr 1fr;gap:20px" }, [
      el("div", { class: "card" }, [cover(t, true)]),
      el("div", { class: "card" }, [
        el("div", { class: "flex", style: "gap:6px;flex-wrap:wrap" }, [
          price > 0 ? el("span", { class: "badge-pill badge-gold", text: `${price} ${langIsFr() ? "MAD" : "درهم"}` }) : el("span", { class: "badge-pill badge-green", text: tr("free") }),
          bought ? el("span", { class: "badge-pill badge-green" }, [icon("check", 12), " " + tr("purchased")]) : null,
        ]),
        el("h1", { class: "doc-title", style: "font-size:22px", text: t.title }),
        el("p", { class: "muted", text: t.description }),
        el("div", { class: "flex", style: "gap:14px;color:var(--ink-3);font-size:13px" }, [
          el("span", {}, [icon("download", 14), ` ${t.download_count ?? 0} ${tr("downloads")}`]),
          el("span", {}, [icon("star", 14, { filled: true }), ` ${(t.rating ?? 0).toFixed(1)}`]),
          el("span", { text: fmtDate(t.updated_at || t.created_at, currentLang()) }),
        ]),
        el("div", { class: "doc-flow mt-16" }, [
          el("span", { class: "step", text: `1. ${price > 0 && !bought ? tr("buyNow") : tr("preview")}` }),
          el("span", { class: "arrow", text: "→" }),
          el("span", { class: "step", text: `2. ${tr("downloadNow")}` }),
        ]),
        el("div", { class: "mt-16" }, [buyBtn]),
        el("button", { class: "btn btn-ghost btn-block mt-8", onclick: () => { navigator.clipboard?.writeText(location.origin + `/marketplace/${id}`); toast(tr("copied"), "success"); } }, [icon("link", 16), " " + tr("share")]),
      ]),
    ]),
  ]);
}

function truncate(s, n) { s = String(s || ""); return s.length > n ? s.slice(0, n).trimEnd() + "…" : s; }
