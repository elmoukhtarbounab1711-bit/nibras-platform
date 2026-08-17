"""
نبراس — مستورد مصر (المرحلة التجريبية) من أرشيف "الذاكرة والمعرفة" المفتوح
(mksegypt.org — رخصة المشاع الإبداعي CC BY 4.0، يتطلب الإسناد).

يستورد:
  1) قوانين مصرية كاملة (نصوص حرفية) — قائمة /ar/laws + صفحة القانون
  2) اجتهادات محكمة النقض + المحكمة الإدارية العليا + الدستورية العليا
     — نصوص أحكام كاملة

إلى قاعدة نبراس عبر واجهة الإدارة المحلية (localhost:8000) بفئة ولاية مستقلة
لدولة مصر (law_jurisdictions.id = 2). لا يمسّ المغرب أو بقية الولايات.

الاستخدام:
  python scripts/import_egypt_pilot.py [--laws N] [--rulings N] [--pages P]
        [--dry-run] [--checkpoint PATH] [--categories-slug slug...]
  افتراضيًا: dry-run يعرض ما سيُستورد بدون كتابة.
"""
import argparse
import datetime as dt
import gzip
import json
import os
import re
import sqlite3
import sys
import urllib.request
import urllib.error

from bs4 import BeautifulSoup

BASE = "http://127.0.0.1:8000"  # ليس localhost — دقة IPv6 تكلّف ~2 ثانية لكل طلب
JID = 2  # مصر
COLLECTIONS = {
    "cassation": {
        "list": "https://mksegypt.org/ar/court-of-cassation-rulings",
        "court": "محكمة النقض المصرية",
        "default_cat": "madani",
    },
    "administrative": {
        "list": "https://mksegypt.org/ar/judgments-of-the-supreme-administrative-court",
        "court": "المحكمة الإدارية العليا المصرية",
        "default_cat": "idari",
    },
    "constitutional": {
        "list": "https://mksegypt.org/ar/supreme-constitutional-court-rulings",
        "court": "المحكمة الدستورية العليا المصرية",
        "default_cat": "dostouri",
    },
}

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) nibras-importer/1.0 (CC-BY-4.0 attribution)"}

CATEGORIES_LAW = [
    (1, "dostouri"), (2, "madani"), (3, "usra"), (4, "jinai"),
    (5, "shughl"), (6, "tijari"), (1878, "idari"), (1874, "iqtisadi"),
    (1868, "mali"), (1870, "huquq"), (1852, "qawanin"), (1866, "madan_k"),
    (1869, "sihha"), (1872, "aqari"), (1877, "qadhai"),
]

RULING_CATS = {
    "madani": "القانون المدني",
    "jinai": "القانون الجنائي",
    "usra": "قانون الأسرة",
    "shughl": "قانون العمل",
    "tijari": "القانون التجاري",
    "idari": "القانون الإداري",
    "dostouri": "القانون الدستوري",
}

CAT_RULES = [
    (re.compile(r"جنائ|عقوب|جناية|النيابة العامة|الدائرة الجنائية|اتهام"), "jinai"),
    (re.compile(r"أحوال شخصية|أسرة|طلاق|نفقة|زواج|ولاية|ميراث|حضانة|مواريث"), "usra"),
    (re.compile(r"عمل|أجور|عامل|تشغيل|تأمينات"), "shughl"),
    (re.compile(r"تجار|شركة|شركات|بنوك|كمبيالة|شيك|إفلاس|بورصة|صناعى"), "tijari"),
    (re.compile(r"إداري|قرار إدارى|تأديب|موظف عام|جهة إدارية|الولاية على المال"), "idari"),
    (re.compile(r"دستور|دستورية|حقوق وحريات|انتخاب"), "dostouri"),
    (re.compile(r"مدني|التعويض|عقد|إيجار|ملكية|حجز|تنفيذ|دين|قرض|ضمان|وكالة|بيع|إيجار"), "madani"),
]

LAW_CAT_RULES = [
    (re.compile(r"دستور"), 1),
    (re.compile(r"أحوال شخصية|أسرة|زواج|طلاق|ميراث|ولاية|نفقة"), 3),
    (re.compile(r"جنائى|عقوبات|إجراءات جنائية|أمن الدولة|مخدرات|أسلحة"), 4),
    (re.compile(r"عمل\b|عامل\b|عمال\b|خدمة مدنية"), 5),
    (re.compile(r"تجارى|شركات|بنوك|بورصة|استثمار|منافسة|حماية المستهلك"), 6),
    (re.compile(r"إدارى|تنظيمى|محليات|مجالس محلية"), 1878),
    (re.compile(r"اقتصاد|ضريبة|ضرائب|مالى|جمارك|نقدى|استثمار"), 1868),
    (re.compile(r"صحة|دواء|تأمين صحى|بيئة"), 1869),
    (re.compile(r"ثقافة|إعلام|مخطوط|آثار|فن|آداب|سياحة"), 1848),
    (re.compile(r"قضائى|محاكم|نقض|إجراءات مدنية|مرافعات|إثبات"), 1877),
    (re.compile(r"مدنى"), 2),
]
LAW_CAT_DEFAULT = 1852  # qawanin (عام)

TRAILER_RE = re.compile(
    r"^(نشر هذا|يُنشر هذا|ينشر هذا|يعمل بهذا|يُعمل|صدر|يبصم|بمقتضى|حُرر|بخلاف ذلك|ثالثًا|رابعًا)",
)


DELAY = 0.15  # مهلة مهذبة بين الطلبات (احترامًا للمصدر المفتوح)
_last_req = {"t": 0.0}


def _polite():
    import time
    wait = DELAY - (time.monotonic() - _last_req["t"])
    if wait > 0:
        time.sleep(wait)
    _last_req["t"] = time.monotonic()


def fetch(url, timeout=45, retries=3):
    import time
    last = None
    for attempt in range(retries):
        _polite()
        req = urllib.request.Request(url, headers=UA)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
                return raw.decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise last


def main_blocks(soup):
    col = soup.select_one(".single-blogs .container .row .col-md-8")
    if col is None:
        return []
    out = []
    for el in col.find_all(["p", "h1", "h2", "h3", "h4", "li"]):
        t = el.get_text(" ", strip=True)
        t = re.sub(r"\s+", " ", t).strip()
        if t and (not out or out[-1] != t):
            out.append(t)
    return out


# --------------------------------------------------------------------------
# تحليل صفحة قانون
# --------------------------------------------------------------------------

def parse_law_card(html):
    """يعيد قائمة (url, title_card) للعمال من صفحة قائمة القوانين."""
    soup = BeautifulSoup(html, "lxml")
    rows = []
    for a in soup.find_all("a", href=re.compile(r"/ar/laws/\d+")):
        h = a.get_text(" ", strip=True)
        h = re.sub(r"\s+", " ", h).strip()
        rows.append((a["href"], h))
    unique = dict()
    for url, text in rows:
        unique.setdefault(url, text)
    return list(unique.items())


ART_RE = re.compile(r"^\(?\s*(المادة\s+[^)]*?)\s*\)?\s*[:：]?\s*$")


def parse_law(url):
    """يستخرج النص الكامل حرفيًا من صفحة المصدر.

    القاعدة: لا يُقص ولا يُرقّم ولا يُعاد صياغة أي شيء.
      - العنوان: سطر المصدر الأول.
      - التمهيد: كل كتلة قبل أول مادة مرقمة (نص حرفي).
      - المواد: كتل تُفتتح بسطر عنوان «المادة X» فقط بنصفها حرفيًا
        (الرقم كما ورد في المصدر؛ لا ترقيم ترتيبي مخترع أبدًا).
      - الذيل: كل ما بعد آخر مادة (صدر/نشر/خاتم...) محفوظ داخل نص المادة
        الأخيرة أو في التمهيد عند غياب مواد — النص الكامل لا يُفقَد أبدًا.
    """
    html = fetch(url)
    soup = BeautifulSoup(html, "lxml")
    blocks = main_blocks(soup)
    if not blocks:
        return None
    title = blocks[0]
    m = re.search(r"بتاريخ (\d{2}-\d{2}-\d{4})", title)
    date_s = m.group(1) if m else None
    # العنوان حرفي؛ نحذف فقط ذيل التاريخ من عنوان الشاشة إن وُجد.
    title_short = re.sub(r"\s*بتاريخ\s+\d{2}-\d{2}-\d{4}\s*$", "", title).strip() or title

    materials = []
    preamble = []
    cur = None
    for b in blocks[1:]:
        hm = ART_RE.match(b)
        if hm:
            if cur and cur["content"]:
                materials.append(cur)
            cur = {"number": hm.group(1).strip(), "content": ""}
            continue
        if cur is None:
            preamble.append(b)
        else:
            cur["content"] += ("\n" if cur["content"] else "") + b
    if cur and cur["content"].strip():
        materials.append(cur)
    if materials:
        description = "\n".join(x for x in preamble if x).strip()
    else:
        # لا سطور «المادة» في الصفحة: النص متصل — يُحفظ كله في التمهيد حرفيًا.
        description = "\n".join(x for x in blocks[1:] if x).strip()
        preamble = blocks[1:]
    return {
        "url": url,
        "title": title_short,
        "title_card": title,
        "date": date_s,
        "materials": materials,
        "description": description,
        "full": "\n".join(x for x in blocks[1:] if x),
    }


def law_category(title, subtitle="", full=""):
    low = title + " " + subtitle
    for rx, cat_id in LAW_CAT_RULES:
        if rx.search(low):
            return cat_id
    return LAW_CAT_DEFAULT


# --------------------------------------------------------------------------
# تحليل صفحة/قائمة اجتهاد
# --------------------------------------------------------------------------

def parse_ruling_card(html, collection):
    soup = BeautifulSoup(html, "lxml")
    rows = []
    pattern = re.compile(r"/ar/(court-of-cassation-rulings|judgments-of-the-supreme-administrative-court|supreme-constitutional-court-rulings)/\d+")
    for a in soup.find_all("a", href=pattern):
        h = a.get_text(" ", strip=True)
        h = re.sub(r"\s+", " ", h).strip()
        card = {}
        for cls in ("naqd-number", "naqd-type", "naqd-release-date", "naqd-issuer"):
            p = a.find(class_=cls)
            if p:
                card[cls] = p.get_text(" ", strip=True)
        rows.append((a["href"], h, card))
    seen = set()
    out = []
    for url, text, card in rows:
        if url in seen:
            continue
        seen.add(url)
        out.append((url, text, card))
    return out


def parse_ruling(url, collection):
    html = fetch(url)
    soup = BeautifulSoup(html, "lxml")
    blocks = main_blocks(soup)
    if not blocks:
        return None
    title = blocks[0]
    m = re.search(r"بتاريخ (\d{2}-\d{2}-\d{4})", title)
    date_s = m.group(1) if m else None
    mnum = re.search(r"رقم (\d+) لسنة (\d+)", title)
    decision_number = None
    decision_year = None
    if mnum:
        decision_number = mnum.group(1)
        decision_year = mnum.group(2)
    # slug: للتعقيب (النقض) نُصنّف حسب محتوى الدائرة/الجريمة؛ أما الإدارية
    # والدستورية فتُبقي على فئتهما العامة المختصة.
    body = "\n".join(blocks)
    cat = COLLECTIONS[collection]["default_cat"]
    if collection == "cassation":
        for rx, slug in CAT_RULES:
            if rx.search(body):
                cat = slug
                break
    content = "\n".join(blocks[1:])  # نبدأ بعد العنوان مباشرة (النص الكامل)
    return {
        "url": url,
        "title": title,
        "date": date_s,
        "number": (f"طعن رقم {decision_number} لسنة {decision_year}" if decision_number else None),
        "court": COLLECTIONS[collection]["court"],
        "category_slug": cat,
        "content": content,
    }


# --------------------------------------------------------------------------
# API + سجل التقدم (checkpoint عبر sqlite) + استيراد
# --------------------------------------------------------------------------

class Api:
    def __init__(self, token, mint=None, retries=3):
        self.token = token
        self.mint = mint
        self.retries = retries

    def call(self, method, path, payload=None):
        attempt = 0
        while True:
            attempt += 1
            body = json.dumps(payload).encode("utf-8") if payload is not None else None
            req = urllib.request.Request(BASE + path, data=body, method=method)
            req.add_header("Authorization", "Bearer " + self.token)
            if body is not None:
                req.add_header("Content-Type", "application/json")
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    raw = resp.read().decode("utf-8")
                    return resp.status, (json.loads(raw) if raw else {})
            except urllib.error.HTTPError as e:
                code = e.code
                raw = e.read().decode("utf-8")
                data = json.loads(raw) if raw else {"error": str(e)}
                if code == 401 and self.mint and attempt <= self.retries:
                    # الخادم قد أُعيد تشغيله (سر JWT جديد) — أعِد سكّ التوكن وأعد المحاولة.
                    try:
                        self.token, _ = self.mint()
                    except Exception:  # noqa: BLE001
                        pass
                    continue
                return code, data
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                if attempt <= self.retries:
                    import time
                    time.sleep(1.5 * attempt)
                    continue
                return 0, {"error": f"net: {e}"}


def mint_token():
    """يسكّ توكن إداري عبر استيراد التطبيق مباشرة."""
    backend = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, backend)
    os.chdir(backend)
    try:
        from app import services_auth
        token, _exp = services_auth.create_access_token(1)
        return token
    except Exception as e:  # noqa: BLE001
        raise SystemExit(f"تعذّر سكّ التوكن إداريًا: {e}")


def ensure_category(api, slug, name):
    code, data = api.call("POST", "/api/admin/jurisprudence/categories", {
        "slug": slug, "name": name, "jurisdiction_id": JID,
    })
    if code in (200, 201):
        return True
    msg = (data or {}).get("error", "")
    if "موجود" in msg or "يوجد" in msg or "already exists" in msg.lower() or "duplicate" in msg.lower():
        return False
    print(f"  ! category FAIL {slug}: {code} {msg}")
    return False


def purge_egypt(checkpoint_path):
    """يمسح نصوص واجتهادات مصر الحالية ويعفّر checkpoint القوانين/الاجتهادات
    ليعاد الاستيراد حرفيًا كاملًا من المصدر (دون لمس باقي الولايات)."""
    backend = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, backend)
    os.chdir(backend)
    from app import database
    con = sqlite3.connect(database.DB_PATH)
    con.execute("PRAGMA foreign_keys=ON")
    n_txt = con.execute(
        "SELECT COUNT(*) FROM legal_texts WHERE jurisdiction_id=?", (JID,)
    ).fetchone()[0]
    n_art = con.execute(
        "SELECT COUNT(*) FROM articles a JOIN legal_texts t ON t.id=a.legal_text_id "
        "WHERE t.jurisdiction_id=?", (JID,)
    ).fetchone()[0]
    n_dec = con.execute(
        "SELECT COUNT(*) FROM jurisprudence WHERE jurisdiction_id=?", (JID,)
    ).fetchone()[0]
    con.execute("DELETE FROM legal_texts WHERE jurisdiction_id=?", (JID,))
    con.execute("DELETE FROM jurisprudence WHERE jurisdiction_id=?", (JID,))
    con.commit()
    con.close()
    # checkpoint (egyp_checkpoint.sqlite) — مسح مفاتيح القانون والاجتهاد فقط
    ck = sqlite3.connect(checkpoint_path)
    ck.execute("DELETE FROM imported WHERE kind IN ('law','ruling')")
    ck.commit()
    ck.close()
    print(f"== purge مصر: {n_txt} نصًا ({n_art} مادة) + {n_dec} اجتهادًا — أُزيلت، وأُفرغ checkpoint (law/ruling).")


def export_full_law(api, tid):
    """(اختياري) يعيد نص القانون الكامل حرفيًا عبر الـ API للتدقيق."""
    code, data = api.call("GET", f"/api/texts/{tid}")
    if code != 200:
        return None
    parts = list(data.get("articles") or [])
    return {
        "title": data.get("title"),
        "description": data.get("description"),
        "articles": len(parts),
    }


class State:
    def __init__(self, path):
        self.con = sqlite3.connect(path)
        self.con.execute(
            "CREATE TABLE IF NOT EXISTS imported (kind TEXT, key TEXT PRIMARY KEY, detail TEXT)"
        )

    def has(self, kind, key):
        cur = self.con.execute("SELECT 1 FROM imported WHERE kind=? AND key=?", (kind, key))
        return cur.fetchone() is not None

    def add(self, kind, key, detail=""):
        self.con.execute(
            "INSERT OR IGNORE INTO imported (kind, key, detail) VALUES (?,?,?)",
            (kind, key, detail[:500]),
        )
        self.con.commit()


def import_law(api, st, law, dry):
    if st.has("law", law["url"]):
        return "skip"
    cat_id = law_category(law["title"], law.get("description", ""))
    enacted = None
    if law["date"]:
        try:
            d = dt.datetime.strptime(law["date"], "%d-%m-%Y").date()
            enacted = d.isoformat()
        except ValueError:
            pass
    if dry:
        print(f"  [dry] law: {law['title']} | مقترح cat={cat_id} | مواد={len(law['materials'])}")
        return "dry"
    code, data = api.call("POST", "/api/admin/texts", {
        "category_id": cat_id,
        "type": "law",
        "title": law["title"],
        "official_ref": law["title_card"],
        "description": law["description"] or None,
        "enacted_date": enacted,
        "source_note": f"مصدر: {law['url']} — أرشيف 'الذاكرة والمعرفة' (رخصة CC BY 4.0). نص حرفي كامل.",
        "jurisdiction_id": JID,
        "is_sample_data": 0,
    })
    if code not in (200, 201):
        print(f"  ! law FAIL {code}: {data}")
        return "fail"
    tid = data["id"]
    for ma in law["materials"]:
        num = ma["number"]
        label = num if num.startswith("مادة") else f"المادة {num}"
        api.call("POST", f"/api/admin/texts/{tid}/articles", {
            "number": num,
            "label": label,
            "content": ma["content"],
            "plain_explanation": "",
            "keywords": "",
        })
    st.add("law", law["url"], law["title"])
    print(f"  + law id={tid} — {law['title'][:60]} ({len(law['materials'])} مادة)")
    return "ok"


def import_ruling(api, st, ruling, dry):
    if st.has("ruling", ruling["url"]):
        return "skip"
    if dry:
        print(f"  [dry] ruling: {ruling['title'][:70]} | {ruling['court']} | cat={ruling['category_slug']}")
        return "dry"
    code, data = api.call("POST", "/api/admin/jurisprudence", {
        "title": ruling["title"],
        "content": ruling["content"],
        "principles": "",
        "category_slug": ruling["category_slug"],
        "jurisdiction_id": JID,
        "court": ruling["court"],
        "decision_number": ruling["number"] or "",
        "decision_date": ruling["date"],
        "source_note": f"مصدر: {ruling['url']} — أرشيف 'الذاكرة والمعرفة' (رخصة CC BY 4.0). نص حرفي للأسباب والمنطوق.",
        "published": True,
    })
    if code not in (200, 201):
        print(f"  ! ruling FAIL {code}: {data}")
        return "fail"
    st.add("ruling", ruling["url"], ruling["title"])
    print(f"  + ruling id={data.get('id')} — {ruling['title'][:60]}")
    return "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--laws", type=int, default=0, help="عدد القوانين (اختياري)")
    ap.add_argument("--rulings", type=int, default=0, help="عدد الاجتهادات (اختياري)")
    ap.add_argument("--laws-all", action="store_true", help="استيراد كل القوانين حتى نفاد الصفحات")
    ap.add_argument("--rulings-all", action="store_true", help="استيراد كل الاجتهادات حتى نفاد الصفحات لكل مجموعة")
    ap.add_argument("--pages", type=int, default=1, help="عدد صفحات قائمة القوانين لمسحها")
    ap.add_argument("--max-pages", type=int, default=1000, help="سقف صفحات الجلطة безопасности")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--checkpoint", default=os.path.join(os.path.dirname(__file__), "egypt_checkpoint.sqlite"))
    ap.add_argument("--seed-categories", action="store_true", help="إنشاء فئات مصرية للاجتهادات إن لم توجد")
    ap.add_argument("--purge", action="store_true", help="يمسح نصوص/اجتهادات مصر الحالية ويعيد الترقيم قبل الاستيراد")
    args = ap.parse_args()

    token = mint_token()
    api = Api(token, mint=mint_token)
    st = State(args.checkpoint)

    if args.purge:
        purge_egypt(args.checkpoint)

    if args.seed_categories:
        print("== تهيئة الفئات القضائية المصرية (jid=2)")
        for slug, name in RULING_CATS.items():
            ensure_category(api, slug, name)

    stats = {"ok": 0, "skip": 0, "fail": 0, "dry": 0, "laws": 0, "rulings": 0, "unreadable": 0}

    if args.laws > 0 or args.laws_all:
        print("== استيراد القوانين")
        target = args.laws if args.laws > 0 else float("inf")
        pages = args.max_pages if args.laws_all else args.pages
        for page in range(1, pages + 1):
            url = f"https://mksegypt.org/ar/laws?page={page}" if page > 1 else "https://mksegypt.org/ar/laws"
            try:
                cards = parse_law_card(fetch(url))
            except Exception as e:
                print(f"  ! قائمة صفحة {page} فشلت: {e}")
                continue
            if not cards:
                print(f"  -> نفدت صفحات القوانين عند صفحة {page}")
                break
            for card_url, text in cards:
                if stats["laws"] >= target:
                    break
                if st.has("law", card_url):
                    stats["skip"] += 1
                    continue
                try:
                    law = parse_law(card_url)
                except Exception as e:
                    print(f"  ! {card_url} لم تُقرأ: {type(e).__name__} {str(e)[:80]}")
                    stats["unreadable"] += 1
                    continue
                if law is None:
                    stats["unreadable"] += 1
                    continue
                r = import_law(api, st, law, args.dry_run)
                if r in ("ok", "dry"):
                    stats["laws"] += 1
                stats[r] = stats.get(r, 0) + 1
            if stats["laws"] >= target:
                break
        print(f"  -> قوانين مستوردة: {stats['laws']} (تخطّي: {stats['skip']})")

    if args.rulings > 0 or args.rulings_all:
        print("== استيراد الاجتهادات")
        if args.rulings_all:
            per = float("inf")
        else:
            per = max(1, args.rulings // max(1, len(COLLECTIONS)))
        for coll in COLLECTIONS:
            base = COLLECTIONS[coll]["list"]
            got = 0
            consecutive_fail = 0
            collected = 0
            for page in range(1, args.max_pages + 1):
                try:
                    url = base if page == 1 else f"{base}?page={page}"
                    cards = parse_ruling_card(fetch(url), coll)
                except Exception as e:
                    print(f"  ! {coll} صفحة {page} فشلت: {e}")
                    consecutive_fail += 1
                    if consecutive_fail >= 5:
                        break
                    continue
                if not cards:
                    print(f"  -> نفدت صفحات {coll} عند صفحة {page}")
                    break
                consecutive_fail = 0
                for card_url, text, card in cards:
                    if got >= per:
                        break
                    if st.has("ruling", card_url):
                        stats["skip"] += 1
                        continue
                    try:
                        ruling = parse_ruling(card_url, coll)
                    except Exception as e:
                        print(f"  ! {card_url} لم يُقرأ: {type(e).__name__} {str(e)[:80]}")
                        stats["unreadable"] += 1
                        continue
                    if ruling is None:
                        stats["unreadable"] += 1
                        continue
                    r = import_ruling(api, st, ruling, args.dry_run)
                    if r in ("ok", "dry"):
                        got += 1
                        stats["rulings"] += 1
                        consecutive_fail = 0
                    elif r == "fail":
                        consecutive_fail += 1
                    stats[r] = stats.get(r, 0) + 1
                    if consecutive_fail >= 10:
                        print(f"  ! {coll}: توقف بعد {consecutive_fail} إخفاقات متتالية")
                        break
                collected += len(cards)
                if got >= per or consecutive_fail >= 10:
                    break
            print(f"  -> {coll}: {got} مستوردة / صفحة انتهت عند {page}")
        print(f"  -> اجتهادات مستوردة: {stats['rulings']} (تخطّي: {stats['skip']})")

    print("== ملخص:", json.dumps(stats, ensure_ascii=False))


if __name__ == "__main__":
    main()