"""
استيراد القوانين المغربية الرسمية من بوابة "عدالة" (وزارة العدل) إلى مكتبة نبراس.

المصدر: https://adala.justice.gov.ma — النصوص الرسمية المنشورة كما هي دون أي تغيير.
يعمل على ثلاث مراحل لكل نص:
  1) البحث في عدالة (API رسمي) واختيار أفضل وثيقة (تفضيل "صيغة محينة"/الأحدث).
  2) تحميل PDF واستخراج نصه (pdfplumber) مع إصلاح الاتجاه المعكوس للأرقام.
  3) تقسيم النص إلى مواد/فصول (segment_articles) وإدخالها في بنية
     categories → legal_texts → articles مع إعادة فهرسة FTS تلقائية.

البيانات مُعلَّمة is_sample_data=0 (محتوى رسمي موثّق) مع source_note يذكر المصدر.
إعادة التشغيل آمنة: تُتخطى النصوص الموجود عنوانها مسبقًا.

الاستخدام: python -m scripts.import_adala
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, r"C:\Users\Bounab\Documents\Default Project\nibras-backend")

from app import tenant_scope
from app.database import db_session

ADALA_BASE = "https://adala.justice.gov.ma/api"
UA = {"User-Agent": "Mozilla/5.0", "accept-language": "AR"}

# قائمة القوانين الكبرى: (عنوان في نبراس، كلمة بحث في عدالة، slug القسم، type)
# title_search يختار أفضل مطابقة من نتائج عدالة.
LAWS = [
    ("الدستور المغربي", "دستور 2011", "dostouri", "constitution"),
    ("قانون الالتزامات والعقود", "ظهير بمثابة قانون الالتزامات والعقود", "madani", "code"),
    ("مدونة الأسرة", "قانون بمثابة مدونة الأسرة", "usra", "code"),
    ("القانون الجنائي", "مجموعة القانون الجنائي", "jinai", "code"),
    ("مدونة الشغل", "مدونة الشغل", "shughl", "code"),
    ("مدونة التجارة", "مدونة التجارة", "tijari", "code"),
    ("قانون المسطرة المدنية", "قانون المسطرة المدنية صيغة محينة", "jinai", "code"),
    ("قانون المسطرة الجنائية", "قانون المسطرة الجنائية", "jinai", "code"),
    ("مدونة الحقوق العينية", "مدونة الحقوق العينية", "madani", "code"),
    ("مدونة التأمينات", "مدونة التأمينات", "tijari", "code"),
    ("قانون الجنسية المغربية", "قانون الجنسية المغربية", "dostouri", "law"),
    ("قانون الشركات", "ظهير شريف رقم 1.08.102", "tijari", "law"),
]


def _http(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read()


def _search(term: str, take: int = 30) -> list:
    url = f"{ADALA_BASE}/files/search?name={urllib.parse.quote(term)}&take={take}"
    data = json.loads(_http(url).decode("utf-8"))
    return data["items"]["results"]


def _score(item: dict) -> tuple:
    name = (item.get("name") or "")
    fm = item.get("fileMeta") or {}
    s = 0
    if "محينة" in name or "محين" in name:
        s += 4
    if "المستجدات" in name:
        s -= 3
    for bad in ("رأي", "دراسة", "تقرير", "إحصائيات", "مسودة", "مشروع", "ندوات", "المستجدات"):
        if bad in name:
            s -= 5
    date = fm.get("gregorianDate") or ""
    if date:
        s += 0.5
    return (s, date)


def _pick_best(term: str) -> dict | None:
    items = _search(term)
    if not items:
        return None
    items.sort(key=_score, reverse=True)
    return items[0]


def _fix_text(pdf_path: str) -> str:
    """يستخرج نص PDF ويصلح الاتجاه المعكوس للأسطر العربية والأرقام."""
    import pdfplumber

    with pdfplumber.open(pdf_path) as pdf:
        raw = "\n".join((p.extract_text() or "") for p in pdf.pages)

    def fix_line(line: str) -> str:
        s = line[::-1]
        return re.sub(r"\d+", lambda m: m.group(0)[::-1], s)

    return "\n".join(fix_line(l) for l in raw.splitlines())


def _store_original_pdf(text_id: int, pdf_data: bytes) -> str:
    """يحفظ النسخة الرسمية الأصلية من عدالة في uploads/laws ويُعيد مفتاح التخزين.

    يتبع نفس نمط تخزين uploads/laws (services_admin.update_text_pdf) بحيث
    يعرضها مسار /api/texts/<id>/pdf مباشرة (يُفضَّل على الملف المولَّد)."""
    from pathlib import Path

    from app import config

    base = Path(config.UPLOAD_DIR) if config.UPLOAD_DIR else (
        Path(__file__).resolve().parent.parent / "uploads"
    )
    uploads = base / "laws"
    uploads.mkdir(parents=True, exist_ok=True)
    key = f"law-{text_id}-adala.pdf"
    path = uploads / key
    path.write_bytes(pdf_data)
    return key


def _category_id(conn, slug: str) -> int | None:
    row = conn.execute("SELECT id FROM categories WHERE slug = ?", (slug,)).fetchone()
    return row[0] if row else None


def _text_exists(conn, title: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM legal_texts WHERE title = ? LIMIT 1", (title,)
    ).fetchone() is not None


def _replace_sample(conn, title: str) -> bool:
    """يحذف نصًا نموذجيًا (is_sample_data=1) بنفس العنوان لإحلاله بالنص الرسمي.
    يعيد True إذا حُذف (يجب متابعة الاستيراد)، وFalse إن لم يوجد نص."""
    row = conn.execute(
        "SELECT id, is_sample_data FROM legal_texts WHERE title = ? LIMIT 1",
        (title,),
    ).fetchone()
    if row is None:
        return False
    if row["is_sample_data"] == 1:
        conn.execute("DELETE FROM legal_texts WHERE id = ?", (row["id"],))
        return True
    return False


def import_law(title: str, term: str, cat_slug: str, text_type: str) -> dict:
    with db_session() as conn:
        cat_id = _category_id(conn, cat_slug)
    if cat_id is None:
        return {"title": title, "status": "skip", "reason": f"no category {cat_slug}"}

    item = _pick_best(term)
    if item is None:
        return {"title": title, "status": "error", "reason": "not found on adala"}

    fm = item.get("fileMeta") or {}
    path = (item.get("path") or "").replace("uploads/", "", 1)
    pdf_url = f"{ADALA_BASE}/uploads/{urllib.parse.quote(path)}"
    pdf_data = _http(pdf_url)
    tmp = r"C:\Users\Bounab\AppData\Local\Temp\opencode\_law.pdf"
    with open(tmp, "wb") as f:
        f.write(pdf_data)

    fixed = _fix_text(tmp)

    with db_session() as conn:
        row = conn.execute(
            "SELECT id, uploaded_pdf_key FROM legal_texts WHERE title = ? LIMIT 1",
            (title,),
        ).fetchone()
        if row is not None:
            # النص موجود سابقًا: نرفق/نحدّث النسخة الرسمية الأصلية فقط.
            key = _store_original_pdf(row["id"], pdf_data)
            if row["uploaded_pdf_key"] != key:
                conn.execute(
                    "UPDATE legal_texts SET uploaded_pdf_key = ? WHERE id = ?",
                    (key, row["id"]),
                )
            return {
                "title": title, "status": "ok", "id": row["id"],
                "pdf": key, "source_name": item.get("name", ""),
            }

        _replace_sample(conn, title)

    from app.services_ingestion import _warn_duplicates, segment_articles

    _pre, articles, warnings = segment_articles(fixed)
    _warn_duplicates(articles, warnings)
    if not articles:
        return {"title": title, "status": "error", "reason": "no articles extracted"}

    official_ref = fm.get("lawNumber") or ""
    enacted = (fm.get("gregorianDate") or "")[:10] or None
    source_note = (
        "النص الرسمي المنشور ببوابة «عدالة» لوزارة العدل المغربية "
        "(adala.justice.gov.ma) — منقول كما هو دون أي تغيير."
    )

    with db_session() as conn:
        cur = conn.execute(
            """INSERT INTO legal_texts
               (category_id, type, title, official_ref, enacted_date,
                last_amended, source_note, is_sample_data, tenant_id)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                cat_id, text_type, title, official_ref or None, enacted,
                None, source_note, 0, tenant_scope.insert_tenant_id(),
            ),
        )
        text_id = cur.lastrowid
        for a in articles:
            conn.execute(
                "INSERT INTO articles (legal_text_id, number, label, content, "
                "plain_explanation, keywords, tenant_id) VALUES (?,?,?,?,?,?,?)",
                (text_id, a["number"], a["label"], a["content"], None, None,
                 tenant_scope.insert_tenant_id()),
            )
        key = _store_original_pdf(text_id, pdf_data)
        conn.execute(
            "UPDATE legal_texts SET uploaded_pdf_key = ? WHERE id = ?",
            (key, text_id),
        )

    return {
        "title": title, "status": "ok", "id": text_id,
        "articles": len(articles), "pdf": key,
        "source_name": item.get("name", ""),
        "warnings": warnings[:3],
    }


def main() -> None:
    print(f"استيراد {len(LAWS)} قانونًا من عدالة...")
    results = []
    for title, term, cat, ttype in LAWS:
        start = time.monotonic()
        r = import_law(title, term, cat, ttype)
        r["sec"] = round(time.monotonic() - start, 1)
        results.append(r)
        print(json.dumps(r, ensure_ascii=False))
    ok = [r for r in results if r["status"] == "ok"]
    print(f"\nتم بنجاح: {len(ok)} / {len(results)}")


if __name__ == "__main__":
    main()
