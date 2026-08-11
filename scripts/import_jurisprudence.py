"""
استيراد الاجتهادات القضائية المغربية (محكمة النقض) إلى وحدة الاجتهادات في نبراس.

المصدر: https://www.huquqai.ma/api/juriscassation — واجهة عامة تعرض القرارات
الصادرة عن محكمة النقض المغربية (مشتقة من منشورات المجلس الأعلى للسلطة
القضائية؛ ~40 ألف قرار). يستورد القرارات الأحدث أولًا (ترتيب الواجهة)، ويحاول
جلب النص الكامل من ملف PDF المرفق (عبر pdfplumber) متى أمكن، وإلا يعتمد على
الخلاصة/المبدأ المحفوظة في الواجهة.

الخصائص:
  - خريطة التصنيف (case_type + وسوم domain) → 11 فئة nibras الموجودة.
  - إزالة التكرار بمفتاح stable (decision_number+date أو العنوان) عبر قاعدة
    البيانات نفسها ⇐ إعادة التشغيل آمنة (idempotent).
  - source_note يوثق المصدر + رابط PDF.
  - إعادة الفهرسة FTS تلقائية عبر مشغّلات الجدول.

الاستخدام:
    python -m scripts.import_jurisprudence [limit] [--no-pdf]

مثال:
    python -m scripts.import_jurisprudence 300
"""
import io
import json
import re
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, r"C:\Users\Bounab\Documents\Default Project\nibras-backend")

from app import tenant_scope
from app.database import db_session

try:  # PDF اختياريًا
    import pdfplumber
except Exception:  # noqa: BLE001 — pragma: no cover
    pdfplumber = None

API_BASE = "https://www.huquqai.ma/api/juriscassation"
UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "Chrome/120.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "ar,en;q=0.8",
}

CASE_TYPE_MAP = {
    "civil": "madani",
    "criminal": "jinai",
    "commercial": "tijari",
    "administrative": "idari",
    "social": "shari3a",  # في المصدر = قانون الشغل (وسوم domaine تؤكد)
}

# تحسين category من وسوم الدوائر: (قائمة كلمات دلالية، slug)
DOMAIN_KEYWORDS = [
    (("مدونة الأسرة", "الأسرة", "الأحوال الشخصية", "طلاق", "تطليق", "النفقة",
      "الحضانة", "الميراث", "النسب", "الزواج", "الموارث"), "usra"),
    (("عقار", "التعقير", "التحفيظ", "الملكية", "الاكتساب", "الحيازة",
      "مطلب تحفيظ", "شهر عقار", "التقادم المكسب"), "aqari"),
    (("الشغل", "العمل", "الأجير", "فصل تعسفي", "المهني", "مياونة", "الأجرة"), "shari3a"),
    (("تجاري", "الشركات", "سند", "السندات", "الإفلاس", "المقاولة", "امحصولات"), "tijari"),
    (("إداري", "الصفقات", "الملك العام", "المرافق", "شطط", "السلطة التقديرية"), "idari"),
    (("جنائي", "جنائية", "جريمة", "عقوبة", "فساد", "المخدرات", "القتل", "سرقة"), "jinai"),
    (("اجتماعي", "تعاضدية", "صندوق المقاصة"), "shari3a"),
    (("دستوري", "الدستور", "حريات", "حقوق الإنسان"), "mnawaa"),
    (("ضريب", "الضريبة", "جباية", "عؤدج", "الرسوم"), "dariba"),
]

# كلمات دلالية عالية الدقة لفئتَي المسطرة المدنية والجنائية
# (تُفحص قبل خريطة case_type؛ مصطلحات عامة مثل "الاستئناف/النقض"
# محذوفة لأنها تظهر في أغلب قرارات النقض وتشوّش التصنيف)
PROCEDURE_KEYWORDS = {
    "mcostara-madaniya": (
        "قانون المسطرة المدنية", "ق.م.م", "المسطرة المدنية", "التبليغ",
        "شهادة النفي", "إسقاط الدعوى", "سقوط الحق", "أمر استعجالي",
        "أوامر استعجالية", "قاضي المستعجلات", "المستعجلات", "المواعيد",
        "إجراءات التبليغ", "التنفيذ الجبري", "الحجز التنفيذي",
        "المعارضة في التنفيذ", "الأوامر الاستعجالية",
    ),
    "mcostara-jinaiya": (
        "قانون المسطرة الجنائية", "ق.م.ج", "المسطرة الجنائية", "النيابة العامة",
        "التلبس", "الاعتقال الاحتياطي", "السراح المؤقت", "الدعوى العمومية",
        "التحقيق التمهيدي", "التحقيق القضائي", "الاستجواب", "الأمر بالوضع",
        "المطالبة المدنية", "الغرفة الجنائية",
    ),
}


def _clean(value) -> str:
    if not value:
        return ""
    s = re.sub(r"\s+", " ", str(value)).strip()
    s = re.sub(r"\s*([.,;:!؟\-])\s*", r"\1 ", s)
    return re.sub(r"\s+", " ", s).strip()


def _norm_date(value) -> str | None:
    """تطبيع التواريخ إلى YYYY-MM-DD (يدعم ISO و dd/mm/yyyy), يتجاهل تواريخ غير واقعية."""
    if not value:
        return None
    s = str(value).strip()
    candidates = []
    m = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)
    if m:
        candidates.append((int(m.group(1)), int(m.group(2)), int(m.group(3))))
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if m:
        candidates.append((int(m.group(3)), int(m.group(2)), int(m.group(1))))
    m = re.match(r"(\d{4})/(\d{1,2})/(\d{1,2})", s)
    if m:
        candidates.append((int(m.group(1)), int(m.group(2)), int(m.group(3))))
    for y, mo, d in candidates:
        if not (1980 <= y <= 2035):
            continue
        if not (0 < mo <= 12 and 0 < d <= 31):
            continue
        return f"{y}-{mo:02d}-{d:02d}"
    return None


def _slugify(value: str) -> str:
    s = re.sub(r"[^\w\s-]", "", (value or "").lower())
    return re.sub(r"[\s_]+", "-", s).strip("-") or "mnawaa"


def _category_slug(rec: dict) -> str:
    ct = (rec.get("case_type") or "").strip().lower()
    haystack = " ".join(
        [str(rec.get("title") or ""), str(rec.get("subject") or ""),
         str(rec.get("content_summary") or "")]
    )
    for t in rec.get("tags") or []:
        haystack += " " + str(t.get("label") or "")
    # المساطر أولًا: قرارات المسطرة المدنية/الجنائية تُصنَّف بفئتيهما
    # (نعتمد الدلالة + السياق حتى لا نزاحم الفئات الموضوعية)
    for slug, kws in PROCEDURE_KEYWORDS.items():
        if any(kw and kw in haystack for kw in kws):
            return slug
    slug = CASE_TYPE_MAP.get(ct)
    if slug:
        return slug
    for kws, s in DOMAIN_KEYWORDS:
        for kw in kws:
            if kw and kw in haystack:
                return s
    return "mnawaa"


def _http(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()


def _fetch_page(page: int, limit: int = 50, case_type: str = "") -> dict:
    url = f"{API_BASE}?page={page}&limit={limit}"
    if case_type:
        url += f"&caseType={urllib.parse.quote(case_type)}"
    data = json.loads(_http(url).decode("utf-8"))
    return data


def _fetch_page_with_retry(page: int, limit: int = 50, tries: int = 10,
                           case_type: str = "") -> dict:
    """جلب صفحة مع إعادة المحاولة عند حد الرد (رد فارغ/أخطاء شبكة).

    الواجهة تبدي حدَّا (rate limit) يظهر كاستجابة فارغة بعد عدة طلبات؛
    ننتظر بهدوء، وبفترة راحة أطول بين كل محاولة وبين الصفحات.
    """
    wait = 6
    for attempt in range(1, tries + 1):
        try:
            data = _fetch_page(page, limit, case_type)
            if data.get("data"):
                return data
            total = data.get("totalCount")
            print(f"  [rate] صفحة فارغة (total={total}) — إعادة بعد {wait}ث ({attempt}/{tries})", flush=True)
            time.sleep(wait)
            wait = min(wait * 2 + 3, 150)
        except Exception as e:  # noqa: BLE001 — سكربت استيراد: يلتقط ويعيد المحاولة
            print(f"  [net] {type(e).__name__} — إعادة بعد {wait}ث ({attempt})", flush=True)
            time.sleep(wait)
            wait = min(wait * 2 + 3, 150)
    return {"data": [], "totalCount": 0, "page": page, "limit": limit}


def _fetch_pdf_text(pdf_url: str, max_bytes: int = 6_000_000) -> str | None:
    if not pdf_url or pdfplumber is None:
        return None
    try:
        data = _http(pdf_url)
        if len(data) > max_bytes:
            return None
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            pages = [(p.extract_text() or "") for p in pdf.pages]
        text = "\n".join(pages).strip()
        return text if len(text) > 200 else None
    except Exception:  # noqa: BLE001 — PDF فشل تنزيله/قراءته: يُتجاهل (محتوى اختياري)
        return None


def _build_content(rec: dict) -> str:
    """نص الاجتهاد كما ورد في المصدر (الخلاصة/المبدأ) — دون إعادة صياغة.

    الاجتهاد يُحفظ أصليًّا، والملف الكامل (PDF) يبقى قابلاً للتحميل عبر pdf_url.
    """
    summary = _clean(rec.get("content_summary") or rec.get("subject") or "")
    if summary:
        return summary
    title = _clean(rec.get("title") or "قرار قضائي")
    meta = []
    n = _clean(rec.get("decision_number"))
    if n:
        meta.append(f"رقم القرار: {n}")
    d = _norm_date(rec.get("decision_date"))
    if d:
        meta.append(f"تاريخ القرار: {d}")
    return title + (("\n" + "\n".join(meta)) if meta else "")


def _source_note(rec: dict) -> str:
    parts = []
    if rec.get("case_number"):
        parts.append("رقم الملف: " + str(rec["case_number"]))
    if rec.get("decision_number"):
        parts.append("رقم القرار: " + str(rec["decision_number"]))
    out = "محكمة النقض — منشورات المجلس الأعلى للسلطة القضائية (عبر حقوقي)"
    if parts:
        out += " · " + " — ".join(parts)
    return out


def _get_existing_keys(conn) -> set:
    keys = set()
    for row in conn.execute(
        "SELECT title, decision_number, decision_date FROM jurisprudence"
    ).fetchall():
        if row["title"]:
            keys.add(("t", row["title"]))
        if row["decision_number"]:
            n = row["decision_number"]
            dt = row["decision_date"] or ""
            keys.add(("dn", n, dt))
            keys.add(("dn", n, ""))
    return keys


def _dedupe_key(rec: dict) -> tuple:
    n = _clean(rec.get("decision_number"))
    dt = _norm_date(rec.get("decision_date")) or ""
    if n and dt:
        return ("dn", n, dt)
    if n:
        return ("dn", n, "")
    t = _clean(rec.get("title"))
    if t:
        return ("t", t)
    return ("id", rec.get("id"))


def _category_name(slug: str) -> str:
    return {
        "madani": "القانون المدني",
        "jinai": "القانون الجنائي",
        "idari": "القانون الإداري",
        "aqari": "القانون العقاري",
        "usra": "قانون الأسرة",
        "tijari": "القانون التجاري",
        "mcostara-madaniya": "قانون المسطرة المدنية",
        "mcostara-jinaiya": "قانون المسطرة الجنائية",
        "shari3a": "قانون الشغل",
        "dariba": "الجبايات والضرائب",
        "mnawaa": "مواضيع أخرى",
    }.get(slug, "مواضيع أخرى")


def _ensure_category(conn, slug: str) -> int:
    row = conn.execute(
        "SELECT id FROM jurisprudence_categories WHERE slug = ?", (slug,)
    ).fetchone()
    if row:
        return row["id"]
    cur = conn.execute(
        "INSERT INTO jurisprudence_categories (slug, name, tenant_id) "
        "VALUES (?, ?, ?)",
        (slug, _category_name(slug), tenant_scope.insert_tenant_id()),
    )
    return cur.lastrowid


def _insert_decision(conn, rec: dict):
    title = _clean(rec.get("title"))
    if not title or title.lower().startswith("decisions "):
        head = _clean(rec.get("subject") or rec.get("content_summary") or "")
        title = head[:120] or "قرار قضائي لمحكمة النقض"
    principles = _clean((rec.get("subject") or rec.get("content_summary") or "")[:1500])
    content = _build_content(rec)
    conn.execute(
        """INSERT INTO jurisprudence
           (category_id, title, principles, content, court, decision_number,
            decision_date, source_note, pdf_url, published, views, tenant_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0, ?)""",
        (cat := _ensure_category(conn, _category_slug(rec)),
         title, principles, content, "محكمة النقض",
         _clean(rec.get("decision_number"))[:60],
         _norm_date(rec.get("decision_date")),
         _source_note(rec),
         (rec.get("pdf_url") or ""),
         tenant_scope.insert_tenant_id()),
    )
    return cat


def main(limit: int = 300, use_pdf: bool = True, commit_every: int = 30,
         case_type: str = "", only_proc: bool = False):
    limit = int(limit)
    inserted = skipped = filtered = fetched = 0
    page = 1
    seen = set()
    pending = 0

    with db_session() as conn:
        existing = _get_existing_keys(conn)
        while fetched < limit:
            data = _fetch_page_with_retry(page, case_type=case_type)
            records = data.get("data") or []
            total = data.get("totalCount")
            label = f" [case_type={case_type}]" if case_type else ""
            print(f"[info] صفحة {page}: {len(records)} قرار (المجموع الكلي {total}){label}", flush=True)
            if not records:
                break
            for rec in records:
                if fetched >= limit:
                    break
                fetched += 1
                key = _dedupe_key(rec)
                if key in existing or key in seen:
                    skipped += 1
                    continue
                if only_proc and _category_slug(rec) not in PROCEDURE_KEYWORDS:
                    filtered += 1
                    continue
                seen.add(key)
                _insert_decision(conn, rec)
                inserted += 1
                pending += 1
                if inserted % 20 == 0:
                    print(f"  … {inserted} اجتهاد أُدرج", flush=True)
                if pending >= commit_every:
                    conn.commit()
                    pending = 0
                    print(f"  [commit] {inserted} في الصف (تدريجي)", flush=True)
                time.sleep(0.1)
            page += 1
            if fetched < limit:
                time.sleep(0.1)

        conn.commit()
    print("=" * 60)
    print(f"جُلب {fetched} — أُدرج {inserted}، تخطّى {skipped}، خارج المساطر {filtered}")
    print("استيراد قانوني انتهى.")


if __name__ == "__main__":
    # تحليل وسيطات بسيط: limit، --case-type X، --no-pdf، --only-proc
    args = sys.argv[1:]
    limit = 300
    use_pdf = True
    case_type = ""
    only_proc = False
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--no-pdf":
            use_pdf = False
        elif a == "--only-proc":
            only_proc = True
        elif a in ("--case-type", "--ct") and i + 1 < len(args):
            case_type = args[i + 1]
            i += 1
        else:
            try:
                limit = int(a)
            except (TypeError, ValueError):
                pass
        i += 1
    main(limit=limit, use_pdf=use_pdf, case_type=case_type, only_proc=only_proc)