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
from functools import lru_cache
from html import escape
from pathlib import Path

from . import config

DOCS_ROOT = Path(config.LEGAL_DOCS_DIR)
INDEX_PATH = DOCS_ROOT / "index.json"
TEMPLATES_PATH = DOCS_ROOT / "templates.json"

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
    p = (base / file).resolve()
    if str(p) != str(base) and not str(p).startswith(str(base) + os.sep):
        raise GeneratorError("مسار وثيقة غير صالح.", 400)
    if not p.is_file():
        raise GeneratorError("الوثيقة غير موجودة في المكتبة.", 404)
    suffix = Path(file).suffix.lower()
    if suffix not in _SUPPORTED_EXTS:
        raise GeneratorError("صيغة الوثيقة غير مدعومة.", 400)
    return p


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
    _field_cache[file] = fields
    return fields


# ---------------------------------------------------------------------------
# التعبئة: وضع القيم داخل الفراغ مع الحفاظ على التنسيق
# ---------------------------------------------------------------------------

def _apply_values_to_texts(texts, spans, values):
    """يعيد نصوص Runs معدَّلة بعد وضع القيم في الفراغات (بنفس الترتيب)."""
    if not spans:
        return list(texts)
    result = list(texts)
    offsets = []
    pos = 0
    for t in texts:
        offsets.append(pos)
        pos += len(t)
    run_idx = 0
    for idx, (s, e) in enumerate(spans):
        value = str(values[idx]).strip() if idx < len(values) else ""
        if not value:
            continue
        while run_idx < len(texts) and offsets[run_idx] + len(result[run_idx]) < s:
            run_idx += 1
        # نبحث من run_idx عن الجزء الذي يحتوي الفراغ كاملًا
        for i in range(run_idx, len(texts)):
            if offsets[i] <= s and e <= offsets[i] + len(result[i]):
                t = result[i]
                start = s - offsets[i]
                end = e - offsets[i]
                result[i] = t[:start] + value + t[end:]
                break
    return result


def generate_docx_bytes(file: str, fields: list, answers: dict) -> tuple:
    """يبني DOCX معبّأً (في الذاكرة) انطلاقًا من القالب الأصلي. يعيد (بايتات، اسم)."""
    doc, name = _open_doc(file)
    values = [answers.get(f.get("key")) for f in fields]
    filled = 0
    for paragraph in _iter_paragraphs(doc):
        runs, texts, spans = _analyze_paragraph(paragraph)
        if not spans:
            continue
        chunk = values[filled:filled + len(spans)]
        filled += len(spans)
        new_texts = _apply_values_to_texts(texts, spans, chunk)
        for run, text in zip(runs, new_texts):
            run.text = text
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue(), name


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


def preview_html(file: str, fields: list, answers: dict) -> tuple:
    """يعيد معاينة HTML للمستند المعبّأ (فقرات + اتجاه RTL للطباعة)."""
    doc, name = _open_doc(file)
    values = [answers.get(f.get("key")) for f in fields]
    filled = 0
    lines = []
    for paragraph in _iter_paragraphs(doc):
        _runs, texts, spans = _analyze_paragraph(paragraph)
        new_texts = list(texts)
        if spans:
            chunk = values[filled:filled + len(spans)]
            filled += len(spans)
            new_texts = _apply_values_to_texts(texts, spans, chunk)
        parts = _render_paragraph_html(paragraph, new_texts)
        text = "".join(parts)
        if text.strip():
            lines.append(f'<p class="{_alignment_class(paragraph)}">{text}</p>')
    body = "\n".join(lines)
    return _html_shell(escape(name), body), name


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
    """حقول للعرض/التوليد: من القالب الموصى به إن حُدد وإلا اكتشاف تلقائي."""
    if template:
        t = get_recommended(template)
        if t and t.get("fields"):
            return t["fields"]
    return extract_fields(file)
