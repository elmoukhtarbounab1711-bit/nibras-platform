import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, r"C:\Users\Bounab\Documents\Default Project\nibras-backend")

from app import tenant_scope
from app.database import db_session

ADALA_BASE = "https://adala.justice.gov.ma/api"
UA = {"User-Agent": "Mozilla/5.0", "accept-language": "AR"}
TMP_DIR = r"C:\Users\Bounab\AppData\Local\Temp\opencode"
STATE_FILE = r"C:\Users\Bounab\AppData\Local\Temp\opencode\adala_bulk_state.json"
FAIL_FILE = r"C:\Users\Bounab\AppData\Local\Temp\opencode\adala_bulk_fail.json"

# أنواع الوثائق المعيارية (دون النسخ/الفرنسية/الملكية/المناشير/الاتفاقيات)
LEGISLATIVE_TYPES = {1, 2, 5, 7, 8, 9, 13, 15, 16, 17}

# خريطة نص نوع الوثيقة -> (type, label) عند غياب theme
TYPE_FALLBACK = {
    1: ("organic_law", "قانون تنظيمي"),
    2: ("law", "قانون"),
    5: ("decree", "مرسوم"),
    7: ("decision", "قرار"),
    8: ("decision", "قرار"),
    9: ("code", "مدونة"),
    13: ("dahir", "ظهير"),
    15: ("decision", "قرار"),
    16: ("royal_decree", "مرسوم ملكي"),
    17: ("dahir_law", "ظهير بمثابة قانون"),
}

# تصنيف ذكي مطابق لبوابة عدالة: اسم الموضوع -> (category_slug, category_name)
# يدمج الموضوعات المتقاربة في فئات قانونية واضحة.
THEME_MAP = {
    "المادة المدنية": ("madani", "القانون المدني"),
    "المادة العقارية": ("aqari", "القانون العقاري"),
    "المادة الكرائية": ("aqari", "القانون العقاري"),
    "المادة الأسرية": ("usra", "قانون الأسرة"),
    "المادة الاجتماعية": ("ijtimai", "القانون الاجتماعي"),
    "مؤسسات الأعمال الإجتماعية للقطاعات الحكومية": ("ijtimai", "القانون الاجتماعي"),
    "المادة الجنائية": ("jinai", "القانون الجنائي"),
    "المادة الأمنية": ("jinai", "القانون الجنائي"),
    "المادة التجارية": ("tijari", "القانون التجاري"),
    "مادة الصناعة التقليدية": ("tijari", "القانون التجاري"),
    "مادة التأمين و التقاعد": ("tijari", "القانون التجاري"),
    "مادة الصناعة والاقتصاد والاستثمار": ("iqtisadi", "القانون الاقتصادي"),
    "مادة المعاملات الالكترونية": ("raqami", "قانون المعاملات الإلكترونية"),
    "مادة المهن": ("mihan", "قانون المهن"),
    "مهنة المحاماة": ("mihan", "قانون المهن"),
    "مهنة التوثيق": ("mihan", "قانون المهن"),
    "مهنة المفوضون القضائيون": ("mihan", "قانون المهن"),
    "مهنة النساخة": ("mihan", "قانون المهن"),
    "مهنة التراجمة": ("mihan", "قانون المهن"),
    "الخبراء القضائيين": ("mihan", "قانون المهن"),
    "مادة الوظيفة العمومية": ("idari", "القانون الإداري"),
    "المادة الإدارية": ("idari", "القانون الإداري"),
    "مادة اختصاصات وتنظيم القطاعات الحكومية والمؤسساتية": ("idari", "القانون الإداري"),
    "مادة الجماعات الترابية": ("idari", "القانون الإداري"),
    "السلطة التنفيدية": ("idari", "القانون الإداري"),
    "التنظيم الهيكلي للوزارة": ("idari", "القانون الإداري"),
    "خطة العدالة": ("idari", "القانون الإداري"),
    "المادة المالية": ("mali", "القانون المالي والجبائي"),
    "المادة الجبائية": ("mali", "القانون المالي والجبائي"),
    "مادة التربية والتعليم": ("tarbiya", "قانون التربية والتعليم"),
    "مادة الثقافة والسياحة والتراث": ("thaqafa", "قانون الثقافة والإعلام"),
    "مادة الصحافة": ("thaqafa", "قانون الثقافة والإعلام"),
    "مادة السمعية البصرية": ("thaqafa", "قانون الثقافة والإعلام"),
    "مادة الشؤون الدينية والإسلامية": ("diniya", "قانون الشؤون الدينية"),
    "مادة المنظومة الصحية والحماية الاجتماعية": ("sihha", "قانون الصحة والحماية الاجتماعية"),
    "مادة السلامة الصحية والغدائية": ("sihha", "قانون الصحة والحماية الاجتماعية"),
    "حالة الطوارئ الصحية": ("sihha", "قانون الصحة والحماية الاجتماعية"),
    "المادة البيئية": ("biaa", "قانون البيئة"),
    "مادة الفلاحة": ("filaha", "قانون الفلاحة"),
    "مادة الصيد البحري": ("filaha", "قانون الفلاحة"),
    "مادة الطاقة": ("taqa", "قانون الطاقة"),
    "النقل عبر الطرق": ("naql", "قانون النقل"),
    "مادة النقل الجوي و البحري": ("naql", "قانون النقل"),
    "المادة الإنتخابية": ("intikhab", "القانون الانتخابي"),
    "مادة الحقوق والحريات": ("huquq", "قانون الحقوق والحريات"),
    "مؤسسات وهيئات حماية حقوق الإنسان والنهوض بها": ("huquq", "قانون الحقوق والحريات"),
    "مؤسسات وهيئات النهوض بالتنمية البشرية والمستدامة والديمقراطية التشاركية": ("huquq", "قانون الحقوق والحريات"),
    "مؤسسة الوسيط": ("huquq", "قانون الحقوق والحريات"),
    "الهيئة الوطنية للنزاهة والوقاية من الرشوة ومحاربتها": ("huquq", "قانون الحقوق والحريات"),
    "الدستور": ("dostouri", "القانون الدستوري"),
    "السلطة التشريعية": ("dostouri", "القانون الدستوري"),
    "السلطة القضائية": ("qadhai", "القضاء والمحاكم"),
    "المحكمة الدستورية": ("qadhai", "القضاء والمحاكم"),
    "المجلس الأعلى للحسابات": ("qadhai", "القضاء والمحاكم"),
    "مادة التنظيم القضائي": ("qadhai", "القضاء والمحاكم"),
    "المجلس الاقتصادي والاجتماعي والبيئي": ("muassasat", "المؤسسات الدستورية"),
    "مجلس المنافسة": ("muassasat", "المؤسسات الدستورية"),
    "مجلة القضاء والقانون": ("qadhai", "القضاء والمحاكم"),
}

# فئات إضافية (للوثائق التي لا تحمل موضوعًا أو كنطاق احتياطي)
EXTRA_CATEGORIES = {
    "moustara": ("قانون المسطرة", "قوانين المساطر القضائية وقواعد الإجراء"),
    "dawli": ("القانون الدولي والاتفاقيات", "الاتفاقيات الدولية والثنائية"),
    "shughl": ("قانون الشغل", "تشريعات العمل والعلاقات الشغلية"),
    "qawanin": ("القوانين", "قوانين عامة"),
    "qawanin-tanthim": ("القوانين التنظيمية", "قوانين تنظيمية"),
    "madan_k": ("المدونات", "مدونات قانونية"),
    "dhawahir-kanun": ("ظهائر بمثابة قانون", "ظهائر شريفة بمثابة قانون"),
    "marasim-malakiya": ("المراسيم الملكية", "مراسيم ملكية"),
    "dhawahir": ("الظهائر", "ظهائر شريفة"),
    "marasim": ("المراسيم", "مراسيم"),
    "qararat": ("القرارات", "قرارات تنظيمية"),
}


def _http(url: str, retries: int = 4) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    for i in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return r.read()
        except Exception:
            if i == retries - 1:
                raise
            time.sleep(1 + i * 2)


def _search(params: dict) -> dict:
    url = f"{ADALA_BASE}/files/search?" + urllib.parse.urlencode(params)
    return json.loads(_http(url).decode("utf-8"))


def _load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def _save_state(state: set):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(state), f, ensure_ascii=False)


def _load_fails():
    if os.path.exists(FAIL_FILE):
        with open(FAIL_FILE, "r", encoding="utf-8") as f:
            return dict(json.load(f))
    return {}


def _save_fails(fails: dict):
    with open(FAIL_FILE, "w", encoding="utf-8") as f:
        json.dump(fails, f, ensure_ascii=False, indent=1)


def _fix_text(pdf_path: str) -> str:
    import pdfplumber

    with pdfplumber.open(pdf_path) as pdf:
        raw = "\n".join((p.extract_text() or "") for p in pdf.pages)

    def fix_line(line: str) -> str:
        s = line[::-1]
        return re.sub(r"\d+", lambda m: m.group(0)[::-1], s)

    return "\n".join(fix_line(l) for l in raw.splitlines())


def _ensure_categories(conn):
    slugs = {v[0] for v in THEME_MAP.values()}
    slugs.update(EXTRA_CATEGORIES)
    for slug in slugs:
        name = next((v[1] for v in THEME_MAP.values() if v[0] == slug), None)
        desc = "وثائق مواضيعية من بوابة عدالة الرسمية"
        if slug in EXTRA_CATEGORIES:
            name, desc = EXTRA_CATEGORIES[slug]
        conn.execute(
            "INSERT OR IGNORE INTO categories (slug, name, description, tenant_id) "
            "VALUES (?, ?, ?, 1)",
            (slug, name or slug, desc),
        )


def _store_original_pdf(text_id: int, pdf_data: bytes) -> str:
    from pathlib import Path

    from app import config

    base = Path(config.UPLOAD_DIR) if config.UPLOAD_DIR else (
        Path(__file__).resolve().parent.parent / "uploads"
    )
    uploads = base / "laws"
    uploads.mkdir(parents=True, exist_ok=True)
    key = f"law-{text_id}-adala.pdf"
    (uploads / key).write_bytes(pdf_data)
    return key


def _title_exists(conn, title: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM legal_texts WHERE title = ? LIMIT 1", (title,)
    ).fetchone() is not None


def _resolve_category(item: dict):
    """يحدد (category_slug, text_type) من موضوع عدالة ثم نوع الوثيقة."""
    fm = item.get("fileMeta") or {}
    theme = (fm.get("theme") or {}).get("name") or ""
    tid = (fm.get("LawType") or {}).get("id")
    if theme in THEME_MAP:
        slug, _name = THEME_MAP[theme]
        # نوع النص: من نوع الوثيقة إن كان قانونيًا وإلا عام
        ttype = TYPE_FALLBACK.get(tid, ("law", "قانون"))[0]
        return slug, ttype
    # لا موضوع: نصنّف حسب نوع الوثيقة
    ttype, _label = TYPE_FALLBACK.get(tid, ("law", "قانون"))
    if tid == 9:
        return "madan_k", ttype  # مدونات
    if tid == 17:
        return "dhawahir-kanun", ttype
    if tid == 16:
        return "marasim-malakiya", ttype
    if tid == 13:
        return "dhawahir", ttype
    if tid == 5:
        return "marasim", ttype
    if tid in (7, 8, 15):
        return "qararat", ttype
    if tid == 1:
        return "qawanin-tanthim", ttype
    if tid == 2:
        return "qawanin", ttype
    return "qawanin", ttype


def _process(item: dict) -> dict:
    import hashlib

    path = (item.get("path") or "").replace("uploads/", "", 1)
    if not path:
        return {"path": path, "ok": False, "error": "no path"}
    pdf_url = f"{ADALA_BASE}/uploads/{urllib.parse.quote(path)}"
    pdf_data = _http(pdf_url)
    digest = hashlib.sha1(path.encode("utf-8")).hexdigest()[:12]
    tmp = os.path.join(TMP_DIR, f"_bulk_{digest}.pdf")
    with open(tmp, "wb") as f:
        f.write(pdf_data)
    try:
        text = _fix_text(tmp)
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass
    return {"path": path, "ok": True, "text": text, "pdf": pdf_data}


def _insert(item: dict, result: dict) -> dict:
    from app.services_ingestion import _warn_duplicates, segment_articles

    title = (item.get("name") or "").strip()
    text = result["text"]
    _pre, articles, warnings = segment_articles(text)
    _warn_duplicates(articles, warnings)

    cat_slug, text_type = _resolve_category(item)
    fm = item.get("fileMeta") or {}
    official_ref = fm.get("lawNumber") or ""
    enacted = (fm.get("gregorianDate") or "")[:10] or None
    source_note = (
        "النص الرسمي المنشور ببوابة «عدالة» لوزارة العدل المغربية "
        "(adala.justice.gov.ma) — منقول كما هو دون أي تغيير."
    )

    with db_session() as conn:
        _ensure_categories(conn)
        cat = conn.execute(
            "SELECT id FROM categories WHERE slug = ?", (cat_slug,)
        ).fetchone()
        if cat is None:
            return {"ok": False, "error": f"category {cat_slug} missing"}
        if _title_exists(conn, title):
            return {"ok": False, "error": "title exists"}
        cur = conn.execute(
            """INSERT INTO legal_texts
               (category_id, type, title, official_ref, enacted_date,
                last_amended, source_note, is_sample_data, tenant_id)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (cat["id"], text_type, title, official_ref or None, enacted,
             None, source_note, 0, tenant_scope.insert_tenant_id()),
        )
        text_id = cur.lastrowid
        for a in articles:
            conn.execute(
                "INSERT INTO articles (legal_text_id, number, label, content, "
                "plain_explanation, keywords, tenant_id) VALUES (?,?,?,?,?,?,?)",
                (text_id, a["number"], a["label"], a["content"], None, None,
                 tenant_scope.insert_tenant_id()),
            )
        key = _store_original_pdf(text_id, result["pdf"])
        conn.execute(
            "UPDATE legal_texts SET uploaded_pdf_key = ? WHERE id = ?",
            (key, text_id),
        )
    return {"ok": True, "id": text_id, "articles": len(articles),
            "cat": cat_slug, "warnings": warnings[:2]}


def build_manifest() -> list:
    items = []
    seen = set()
    for tid in LEGISLATIVE_TYPES:
        d = _search({"name": "", "lawTypeId": tid, "take": 5000})
        total = d["meta"]["totalItems"]
        results = d["items"]["results"]
        got = 0
        for it in results:
            p = it.get("path") or ""
            if p in seen:
                continue
            seen.add(p)
            items.append(it)
            got += 1
        print(f"  type {tid}: {got}/{total}", flush=True)
    return items


def main():
    done = _load_state()
    fails = _load_fails()
    print(f"محاولات مكتملة سابقًا: {len(done)}، أخطاء: {len(fails)}", flush=True)

    with db_session() as conn:
        _ensure_categories(conn)

    print("بناء كشف الوثائق من عدالة...", flush=True)
    manifest = build_manifest()
    print(f"كشف جاهز: {len(manifest)} وثيقة", flush=True)

    todo = [it for it in manifest if (it.get("path") or "") not in done]
    print(f"متبقٍ للاستيراد: {len(todo)}", flush=True)

    t0 = time.monotonic()
    ok_count = 0
    err_count = 0
    with ThreadPoolExecutor(max_workers=6) as pool:
        futs = {}
        for it in todo:
            f = pool.submit(_process, it)
            futs[f] = it
        for i, fut in enumerate(as_completed(futs), 1):
            it = futs[fut]
            path = it.get("path") or ""
            try:
                res = fut.result()
                if not res.get("ok"):
                    fails[path] = res.get("error")
                    err_count += 1
                else:
                    ins = _insert(it, res)
                    if ins.get("ok"):
                        ok_count += 1
                    else:
                        fails[path] = ins.get("error")
                        err_count += 1
            except Exception as e:  # noqa: BLE001 — سكربت استيراد: يلتقط ويواصل
                fails[path] = str(e)[:200]
                err_count += 1
            done.add(path)
            if i % 25 == 0 or i == len(todo):
                _save_state(done)
                _save_fails(fails)
                el = time.monotonic() - t0
                print(
                    f"[{i}/{len(todo)}] ok={ok_count} err={err_count} "
                    f"elapsed={el/60:.1f}m",
                    flush=True,
                )
    _save_state(done)
    _save_fails(fails)
    print(f"\nتم بنجاح: {ok_count} / {len(todo)}، أخطاء: {err_count}", flush=True)


if __name__ == "__main__":
    main()
