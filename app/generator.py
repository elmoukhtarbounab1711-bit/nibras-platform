"""
مولّد الوثائق والعقود من مكتبة القوالب (مرحلة مكتبة الوثائق).

يبني وثائق قابلة للتعبئة انطلاقًا من قوالب Word حقيقية (مكتبة أُرسِبت عبر
scripts/ingest_legal_docs.py): يكتشف الفراغات (.........) داخل كل مستند،
يحوّلها إلى حقول نموذج، وعند التعبئة يضع القيمة داخل نفس الجزء Runs مع
الحفاظ التام على التنسيق الأصلي، ويولّد معاينة HTML للطباعة تحاكي بنية
المستند (فقرات وجداول واتجاه RTL).

القوالب الموصى بها (مُنتقاة من المكتبة) في data/legal_docs/templates.json —
بيانات قابلة للتحرير؛ التوليد يعتمد على ترتيب الفراغات في المستند الأصلي
لا على القيم، فيبقى التنسيق موثوقًا مهما غُيّرت تسميات الحقول.
"""
import io
import json
import os
import re
import unicodedata
from copy import deepcopy
from functools import lru_cache
from html import escape
from pathlib import Path

from . import amount_words, config

DOCS_ROOT = Path(config.LEGAL_DOCS_DIR)
INDEX_PATH = DOCS_ROOT / "index.json"
TEMPLATES_PATH = DOCS_ROOT / "templates.json"
PROFILES_PATH = DOCS_ROOT / "field_profiles.json"

_BLANK_RE = re.compile(r"(?:\.{3,}|…+|_{3,})")
_FILLABLE_EXTS = {".docx"}
_SUPPORTED_EXTS = {".doc", ".docx", ".pdf", ".pptx"}

_field_cache: dict = {}


class GeneratorError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


# ---------------------------------------------------------------------------
# الفهرس والقوالب الموصى بها
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def read_index() -> dict:
    """يقرأ فهرس المكتبة (categories → docs). فارغ إن غابت الملفات."""
    if not INDEX_PATH.exists():
        return {"categories": [], "total_files": 0}
    try:
        with open(INDEX_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"categories": [], "total_files": 0}


def categories() -> list:
    index = read_index()
    return [
        {"name": c.get("name"), "slug": c.get("slug"),
         "count": len(c.get("docs") or [])}
        for c in index.get("categories") or []
    ]


def list_docs(category: str | None = None) -> list:
    """يفهرس كل مستندات المكتبة مع قابلية التعبئة (fillable=True للـ docx)."""
    out = []
    for c in read_index().get("categories") or []:
        if category and c.get("slug") != category and c.get("name") != category:
            continue
        for d in c.get("docs") or []:
            path = d.get("file") or ""
            out.append({
                "file": path,
                "title": d.get("title") or Path(path).stem,
                "size": d.get("size", 0),
                "ext": d.get("ext", ""),
                "category": c.get("name"),
                "category_slug": c.get("slug"),
                "fillable": Path(path).suffix.lower() in _FILLABLE_EXTS,
            })
    return out


def get_doc(file: str):
    for d in list_docs():
        if d["file"] == file:
            return d
    return None


def _resolve_file(file: str) -> Path:
    """يحل مسارًا آمنًا داخل مجلد المكتبة (يمنع الخروج عبر ../)."""
    if not file or not isinstance(file, str):
        raise GeneratorError("ملف الوثيقة غير محدد.", 400)
    base = DOCS_ROOT.resolve()
    p = _locate_in_docs(base, file)
    if p is None:
        # يضمن أمان الحاوية حتى مع الاختلافات في صيغة يونيكود (NFC/NFD)
        real = _norm_nfc(file)
        if real.startswith("../") or real.startswith("..\\") or "/.." in real:
            raise GeneratorError("مسار وثيقة غير صالح.", 400)
        raise GeneratorError("الوثيقة غير موجودة في المكتبة.", 404)
    suffix = Path(file).suffix.lower()
    if suffix not in _SUPPORTED_EXTS:
        raise GeneratorError("صيغة الوثيقة غير مدعومة.", 400)
    return p


def _norm_nfc(path) -> str:
    return unicodedata.normalize("NFC", str(path))


@lru_cache(maxsize=2048)
def _locate_in_docs(base: Path, file: str):
    """يبحث عن الملف داخل المكتبة حاميًا من الخروج، مع التسامح مع NFD/NFC."""
    if not file or not isinstance(file, str):
        return None
    if _norm_nfc(file).startswith("../") or "\\.." in file or "/.." in file:
        return None
    candidate = (base / file).resolve()
    nfc_file = _norm_nfc(file)
    nfc_base = _norm_nfc(base)
    nfc_candidate = _norm_nfc(candidate)
    if (nfc_candidate == nfc_base or not nfc_candidate.startswith(nfc_base + os.sep)):
        return None
    if candidate.is_file():
        return candidate
    # مسار الفهرس غالبًا به صيغة NFC والمستودع على القرص NFD (أنظمة يونيكس)
    for dirpath, _dirs, names in os.walk(base):
        for resolved in names:
            rel = _norm_nfc(os.path.join(dirpath, resolved))
            want = _norm_nfc(os.path.join(base, file))
            if rel == want:
                return Path(dirpath, resolved)
    return None


def _open_doc(file: str):
    try:
        from docx import Document
    except ImportError:
        raise GeneratorError("مكتبة معالجة DOCX غير مثبتة.", 500)
    p = _resolve_file(file)
    if p.suffix.lower() not in _FILLABLE_EXTS:
        raise GeneratorError(
            "هذا المستند بصيغة غير قابلة للتعبئة (تنزيل فقط).", 400
        )
    return Document(str(p)), p.name


# ---------------------------------------------------------------------------
# استعراض الفقرات بترتيب المستند (الجسم ثم الجداول)
# ---------------------------------------------------------------------------

def _iter_paragraphs(doc):
    """يستعرض الفقرات بترتيب المستند (الجسم ثم جداوله بالأعمدة/الأسطر)."""
    from docx.oxml.table import CT_Tbl
    from docx.oxml.text.paragraph import CT_P
    from docx.table import _Cell
    from docx.text.paragraph import Paragraph

    def _walk(elements):
        for el in elements:
            if isinstance(el, CT_P):
                yield Paragraph(el, doc)
            elif isinstance(el, CT_Tbl):
                for tr in el.tr_lst:
                    for tc in tr.tc_lst:
                        cell = _Cell(tc, doc)
                        yield from _walk(list(cell._element.iterchildren()))

    yield from _walk(list(doc.element.body))


def _analyze_paragraph(paragraph):
    """يعيد (runs, texts, spans) لفقرات تحتوي فراغات."""
    runs = [r for r in paragraph.runs if r.text is not None]
    if not runs:
        return [], [], []
    texts = [r.text for r in runs]
    full = "".join(texts)
    spans = [(m.start(), m.end()) for m in _BLANK_RE.finditer(full)]
    return runs, texts, spans


# ---------------------------------------------------------------------------
# استخراج الحقول من الفراغات
# ---------------------------------------------------------------------------

_TYPE_KEYWORDS = {
    "date": ("تاريخ", "بتاريخ", "حرر", "يوم", "سنة"),
    "money": ("مبلغ", "أجرة", "ثمن", "تعويض", "مصاريف", "penalite",
              "somme", "montant"),
    "number": ("رقم", "عدد", "هاتف"),
}


def _infer_field_type(label: str) -> str:
    for ftype, kws in _TYPE_KEYWORDS.items():
        if any(kw in label for kw in kws):
            return ftype
    return "text"


def _field_label(before: str) -> str:
    """يشتق تسمية الحقل من المقاطع قبل الفراغ (قابل للتحرير لاحقًا)."""
    seg = before.rstrip(" ()/؛،:-")
    parts = [p.strip(" ()/") for p in re.split(r"[؛:،\n]", seg) if p.strip()]
    last = parts[-1] if parts else ""
    if not last:
        toks = re.findall(r"[\u0600-\u06FF][\u0600-\u06FF\s]*", before)
        last = toks[-1] if toks else "نص"
    words = last.split()
    if len(words) > 3:
        last = " ".join(words[-3:])
    last = last.lstrip(" ._…–\u00a0-")
    if len(last) > 30:
        last = last[:30]
    if "السيد" in last or "السيدة" in last or "الاسم" in last:
        return "الاسم الكامل"
    return last or "نص"


# ---------------------------------------------------------------------------
# تهذيب التسميات المكتشفة تلقائيًا (تطبق على جميع الحقول عند العرض)
# ---------------------------------------------------------------------------

_LABEL_FIXES = (
    ("التعريف الوطنية", "رقم بطاقة التعريف الوطنية"),
    ("الساكن(ة", "الساكنة"),
    ("والساكن(ة", "الساكنة"),
    ("حرر   بـ", "مكان التحرير"),
    ("حسن نية بتاريخ", "تاريخ الإدلاء"),
    ("المزداد(ة) بتاريخ", "تاريخ الازدياد"),
    ("الإمضاء", "اسم الموثق / الإمضاء"),
)

_AR_NUMS = "٠١٢٣٤٥٦٧٨٩"


def _ar_ordinal(n: int) -> str:
    if n < 10:
        return _AR_NUMS[n]
    return "".join(_AR_NUMS[int(c)] for c in str(n))


def _clean_label(label: str) -> str:
    """ينظف التسمية من بقايا الفراغات والأقواس المعلقة دون المساس بأزواجها."""
    if not label:
        return "نص"
    label = re.sub(r"[\.…]{2,}|_{3,}", " ", label)
    label = re.sub(r"\s+", " ", label).strip(" /؛،:-–")
    for bad, good in _LABEL_FIXES:
        if bad in label and good not in label:
            label = label.replace(bad, good)
    if label.count("(") != label.count(")"):
        label = re.sub(r"[\(（].{0,10}$", "", label).strip()
    label = re.sub(r"\s+", " ", label).strip()
    if len(label) > 45:
        label = label[:45].rsplit(" ", 1)[0]
    return label or "نص"


def _dedupe_labels(fields: list) -> list:
    """يضيف ترقيمًا للأسماء المتكررة (الاسم الكامل، الاسم الكامل ٢...)."""
    counts: dict = {}
    for f in fields:
        counts[f.get("label") or ""] = counts.get(f.get("label") or "", 0) + 1
    seen: dict = {}
    out = []
    for f in fields:
        label = f.get("label") or ""
        if counts[label] > 1:
            seen[label] = seen.get(label, 0) + 1
            if seen[label] > 1:
                label = f"{label} {_ar_ordinal(seen[label])}"
        out.append({**f, "label": label})
    return out


def _finalize_fields(fields: list) -> list:
    """تطبق التهذيب وإزالة التكرار على أي قائمة حقول قبل عرضها."""
    return _dedupe_labels([
        {**f, "label": _clean_label(f.get("label") or "")}
        for f in fields
    ])


# ---------------------------------------------------------------------------
# المبالغ كتابةً (تحقن في DOCX والمعاينة عند تفعيل الخيار)
# ---------------------------------------------------------------------------

_MONEY_PREFIX = {"ar": "المبلغ كتابةً: ", "fr": "Le montant en lettres : "}


def _money_line(value, lang: str) -> str | None:
    data = amount_words.amount_words(value, lang)
    if not data:
        return None
    if lang == "fr":
        line = data["line_fr"]
    else:
        line = data["line_ar"]
    prefix = _MONEY_PREFIX.get(lang, _MONEY_PREFIX["ar"])
    return f"{prefix}{line}"


def extract_fields(file: str) -> list:
    """يكتشف حقول المستند من فراغاته بترتيب التصدير الفعلي.

    النتيجة قابلة للتعديل (label/type) في data/legal_docs/templates.json —
    لا يؤثر تعديل التسمية على ترتيب التوليد.
    """
    if file in _field_cache:
        return _field_cache[file]
    doc, _ = _open_doc(file)
    fields = []
    for paragraph in _iter_paragraphs(doc):
        const_txt = "".join(r.text or "" for r in paragraph.runs)
        for m in _BLANK_RE.finditer(const_txt):
            before = const_txt[max(0, m.start() - 45):m.start()]
            label = _field_label(before) or "نص"
            fields.append({
                "key": f"f{len(fields) + 1:03d}",
                "label": label,
                "type": _infer_field_type(label),
            })
            if len(fields) >= config.GENERATOR_MAX_FIELDS:
                break
        if len(fields) >= config.GENERATOR_MAX_FIELDS:
            break
    if not fields:
        raise GeneratorError(
            "لم يُعثر على فراغات قابلة للتعبئة في هذا المستند.", 400
        )
    if len(_field_cache) > 500:
        _field_cache.clear()
    fields = _finalize_fields(fields)
    _field_cache[file] = fields
    return fields


# ---------------------------------------------------------------------------
# التعبئة: وضع القيم داخل الفراغ مع الحفاظ على التنسيق
# ---------------------------------------------------------------------------

def _apply_values_to_texts(texts, spans, values):
    """يعيد نصوص Runs معدَّلة بعد وضع القيم في الفراغات (بنفس الترتيب).

    يتعامل مع الفراغات الممتدة عبر أكثر من Run (نص منقسم): يحقن القيمة
    في أول مقطع ويعيد أطراف بقية المقاطع للحفاظ على التنسيق المحيط.
    """
    if not spans:
        return list(texts)
    result = list(texts)
    offsets = []
    pos = 0
    for t in texts:
        offsets.append(pos)
        pos += len(t)
    total = pos
    for idx, (s, e) in enumerate(spans):
        value = str(values[idx]).strip() if idx < len(values) else ""
        if not value:
            continue
        s = min(s, total - 1)
        e = min(e, total)
        if e <= s:
            continue
        start_run = end_run = None
        for k in range(len(texts)):
            o = offsets[k]
            if o <= s < o + len(texts[k]):
                start_run = k
            if o < e <= o + len(texts[k]):
                end_run = k
        if start_run is None or end_run is None:
            continue
        start = s - offsets[start_run]
        if start_run == end_run:
            result[start_run] = (
                texts[start_run][:start] + value + texts[start_run][e - offsets[start_run]:])
        else:
            result[start_run] = texts[start_run][:start] + value
            for k in range(start_run + 1, end_run):
                result[k] = ""
            result[end_run] = texts[end_run][e - offsets[end_run]:]
    return result


def generate_docx_bytes(file: str, fields: list, answers: dict,
                        money: dict | None = None) -> tuple:
    """يبني DOCX معبّأً (في الذاكرة) انطلاقًا من القالب الأصلي. يعيد (بايتات، اسم).

    money={"add": True, "lang": "ar"|"fr"} يُدرج سطر «المبلغ كتابةً» تحت كل
    حقل مالي معبأ، مع الحفاظ على موضعه وتنسيقه الأصلي.
    """
    doc, name = _open_doc(file)
    values = [answers.get(f.get("key")) for f in fields]
    paras = list(_iter_paragraphs(doc))  # لقطة قبل أي إدراج لاحق
    filled = 0
    money_inserts: dict = {}  # id(_p) → [سطور]
    for paragraph in paras:
        runs, texts, spans = _analyze_paragraph(paragraph)
        if not spans:
            continue
        chunk = values[filled:filled + len(spans)]
        filled += len(spans)
        new_texts = _apply_values_to_texts(texts, spans, chunk)
        for run, text in zip(runs, new_texts):
            run.text = text
        if not (money and money.get("add")):
            continue
        for i, span in enumerate(spans):
            if i >= len(chunk):
                break
            fld = fields[filled - len(spans) + i] if 0 <= filled - len(spans) + i < len(fields) else None
            if not fld or fld.get("type") != "money" or not chunk[i]:
                continue
            line = _money_line(chunk[i], money.get("lang") or "ar")
            if line:
                money_inserts.setdefault(id(paragraph._p), []).append(line)
    if money_inserts:
        for paragraph in paras:
            lines = money_inserts.get(id(paragraph._p))
            if not lines:
                continue
            for line in lines:
                _insert_money_paragraph(doc, paragraph, line)
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue(), name


def _insert_money_paragraph(doc, anchor, text: str) -> None:
    """يُدرج فقرة بعد فقرة المصدر (بعد نقلها من نهاية المستند)."""
    try:
        new_p = doc.add_paragraph()
        try:
            new_p.alignment = anchor.alignment
        except (AttributeError, TypeError, ValueError):
            pass
        new_p.add_run(text)
        anchor._p.addnext(new_p._p)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# معاينة HTML للطباعة (تحاكي بنية المستند)
# ---------------------------------------------------------------------------

def _is_bold(run) -> bool:
    try:
        return bool(run.bold)
    except (TypeError, ValueError):
        return False


def _is_underline(run) -> bool:
    try:
        return bool(run.underline)
    except (TypeError, ValueError):
        return False


def _alignment_class(paragraph) -> str:
    try:
        if paragraph.alignment == 1:  # CENTER
            return "center"
    except (AttributeError, TypeError, ValueError):
        pass
    return "right"


def _render_paragraph_html(paragraph, new_texts):
    parts = []
    for run, text in zip(paragraph.runs, new_texts):
        if text:
            t = escape(text)
            if _is_bold(run):
                t = f"<b>{t}</b>"
            if _is_underline(run):
                t = f"<u>{t}</u>"
            parts.append(t)
    return parts


def preview_html(file: str, fields: list, answers: dict,
                 money: dict | None = None, original: bool = False) -> tuple:
    """يعيد معاينة HTML للمستند المعبّأ (جداول + فقرات + اتجاه RTL للطباعة).

    original=True يعرض القالب قبل التعبئة (للتبديل بين شكل الأصلي والمعبأ).
    """
    doc, name = _open_doc(file)
    if original:
        answers = {}
    values = [answers.get(f.get("key")) for f in fields]
    filled = 0
    body_parts: list = []

    def _render_para(paragraph) -> list:
        """يعيد شرائح HTML لحقول محددة (لا يعدّل filled)."""
        nonlocal filled
        _runs, texts, spans = _analyze_paragraph(paragraph)
        new_texts = list(texts)
        chunk = []
        if spans:
            chunk = values[filled:filled + len(spans)]
            filled += len(spans)
            new_texts = _apply_values_to_texts(texts, spans, chunk)
        parts = _render_paragraph_html(paragraph, new_texts)
        text = "".join(parts)
        frags = []
        if text.strip():
            frags.append(f'<p class="{_alignment_class(paragraph)}">{text}</p>')
        if money and money.get("add"):
            for i, _span in enumerate(spans):
                if i >= len(chunk):
                    break
                fld = fields[filled - len(spans) + i] if 0 <= filled - len(spans) + i < len(fields) else None
                if not fld or fld.get("type") != "money" or not chunk[i]:
                    continue
                line = _money_line(chunk[i], money.get("lang") or "ar")
                if line:
                    frags.append(f'<p class="money-words">{escape(line)}</p>')
        return frags

    def _render_table(tbl) -> str:
        """يعيد جدول HTML كاملاً مع تعبئة خلاياه بالترتيب الصحيح."""
        rows = []
        for row in tbl.rows:
            cells = []
            for cell in row.cells:
                cell_parts: list = []
                for kind, paragraph, _t in _iter_blocks(cell._element):
                    if kind == "p":
                        cell_parts.extend(_render_para(paragraph))
                cells.append("<td>" + "\n".join(cell_parts) + "</td>")
            if cells:
                rows.append("<tr>" + "".join(cells) + "</tr>")
        return "<table>" + "\n".join(rows) + "</table>"

    for kind, paragraph, tbl in _iter_blocks(doc.element.body):
        if kind == "tbl":
            body_parts.append(_render_table(tbl))
        else:
            body_parts.extend(_render_para(paragraph))

    if original:
        body_parts.insert(
            0, ('<p class="note">أصل القالب قبل التعبئة — '
                'الفراغات ظاهرة بنقاط.</p>'))
    body = "\n".join(body_parts)
    return _html_shell(escape(name), body), name


def _iter_blocks(element):
    """يعيد وعاءين: ('p', paragraph, None) أو ('tbl', None, table)
    لأي عنصر حاوية (body أو خلية جدول) بترتيب المستند الفعلي."""
    from docx.oxml.table import CT_Tbl
    from docx.oxml.text.paragraph import CT_P
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    for el in element.iterchildren():
        if isinstance(el, CT_P):
            yield "p", Paragraph(el, element), None
        elif isinstance(el, CT_Tbl):
            yield "tbl", None, Table(el, element)


def _html_shell(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="robots" content="noindex">
<title>{title}</title>
<style>
  @page {{ size: A4; margin: 2cm; }}
  body {{ font-family: 'Amiri', 'Scheherazade New', 'Times New Roman', Arial, serif;
         direction: rtl; color: #1a1a1a; line-height: 2; margin: 2rem; }}
  p {{ margin: 0.35em 0; text-align: right; }}
  p.center {{ text-align: center; }}
  p.money-words {{ font-weight: 700; margin-top: 0.1em; }}
  p.note {{ color: #8a4b00; background: #fff4e0; border: 1px solid #e8c98a;
           padding: 6px 10px; border-radius: 6px; }}
  table {{ border-collapse: collapse; width: 100%; margin: 0.8em 0; }}
  td, th {{ border: 1px solid #777; padding: 4px 8px; vertical-align: top; text-align: right; }}
  @media print {{ body {{ font-size: 12pt; margin: 0; }} }}
</style>
</head>
<body>
{body}
</body>
</html>"""


# ---------------------------------------------------------------------------
# القوالب الموصى بها
# ---------------------------------------------------------------------------

def _load_templates():
    if not TEMPLATES_PATH.exists():
        return []
    try:
        with open(TEMPLATES_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return []
    if isinstance(data, dict):
        return data.get("templates") or []
    return data


def recommended_templates() -> list:
    return [
        {"id": t.get("id"), "title": t.get("title"), "category": t.get("category"),
         "file": t.get("file"), "description": t.get("description") or "",
         "field_count": len(t.get("fields") or []) or None}
        for t in _load_templates() if t.get("file")
    ]


def get_recommended(template_id: str):
    for t in _load_templates():
        if t.get("id") == template_id:
            return t
    return None


def resolve_fields(file: str, template: str | None = None) -> list:
    """حقول للعرض/التوليد: من النخبة اليدوية إن وُجدت، ثم القالب الموصى به،
    ثم الاستخراج التلقائي. النخبة تُعتبر صالحة فقط إذا طابق عددُ حقولها عددَ
    الفراغات في المستند — وإلا نتراجع للاستخراج التلقائي (حماية من الانحراف)."""
    if template:
        t = get_recommended(template)
        if t and t.get("fields"):
            return _finalize_fields(t["fields"])
    profile = _profile_for(file)
    if profile is not None:
        try:
            if len(profile) == len(extract_fields(file)):
                return _finalize_fields(profile)
        except GeneratorError:
            pass  # المستند غير قابل للتعبئة — يُترك للاستخراج التلقائي للرفع بالخطأ
    return extract_fields(file)


@lru_cache(maxsize=1)
def _profiles() -> list:
    """نخبة الحقول اليدوية لكل عقد (data/legal_docs/field_profiles.json)."""
    if not PROFILES_PATH.exists():
        return []
    try:
        with open(PROFILES_PATH, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return []
    return data.get("profiles") if isinstance(data, dict) else (data or [])


def _profile_for(file: str):
    """يعيد حقول النخبة لهذه الوثيقة (نسخة مطابقة غير مشتركة) أو None."""
    want = _norm_nfc(file)
    for p in _profiles():
        if want == _norm_nfc(p.get("file") or ""):
            return deepcopy(p.get("fields") or [])
    return None
