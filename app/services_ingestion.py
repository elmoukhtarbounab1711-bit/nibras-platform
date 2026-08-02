"""
محرك رفع المستندات (المرحلة 10 — قرار D-028).

نقطة إدارية واحدة لاستيعاب نصوص قانونية PDF/DOCX في المكتبة القائمة:
يُستخرج النص (pdfminer.six للـ PDF و python-docx للـ DOCX)، ثم يُقسَّم
تلقائيًا إلى مواد وفق عناوين `المادة`/`الفصل` (في أول السطر فقط)، وتُفهرَس
في بنية categories → legal_texts → articles (مشغّلات FTS موجودة مسبقًا)
داخل معاملة واحدة مع تسجيل تدقيقي (Security §8). يدعم `dry_run` لمراجعة
التقسيم قبل الالتزام. الملف لا يُخزَّن على القرص إطلاقًا — يُستخرج نصه فقط.
"""
import io
import os
import re

from . import config
from .database import db_session
from .services_admin import LEGAL_TEXT_TYPES, _log_admin_action

# امتدادات المستندات المقبولة (قرار D-028)
SUPPORTED_EXTENSIONS = {".pdf", ".docx"}

# تحويل الأرقام العربية-الهندية (٠-٩) إلى اللاتينية لرقم المادة القابل للترتيب
_AR_INDIC = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

# الأعداد الترتيبية الفردية (1-9) — تُقرأ من رأس المادة عند غياب الأرقام
_UNIT_ORDINALS = {
    "الأول": 1, "الأولى": 1, "الاول": 1, "الاولى": 1,
    "الثاني": 2, "الثانية": 2,
    "الثالث": 3, "الثالثة": 3,
    "الرابع": 4, "الرابعة": 4,
    "الخامس": 5, "الخامسة": 5,
    "السادس": 6, "السادسة": 6,
    "السابع": 7, "السابعة": 7,
    "الثامن": 8, "الثامنة": 8,
    "التاسع": 9, "التاسعة": 9,
}

# الأعداد الترتيبية المركّبة (11-19) — تُكملها كلمة "عشر/عشرة" التالية
_TEEN_ORDINALS = {
    "الحادي": 11, "الحادية": 11,
    "الثاني": 12, "الثانية": 12,
    "الثالث": 13, "الثالثة": 13,
    "الرابع": 14, "الرابعة": 14,
    "الخامس": 15, "الخامسة": 15,
    "السادس": 16, "السادسة": 16,
    "السابع": 17, "السابعة": 17,
    "الثامن": 18, "الثامنة": 18,
    "التاسع": 19, "التاسعة": 19,
}

_TEEN_WORDS = {"عشر", "عشرة"}

# لواحق تسمية شائعة تُلحق برقم المادة بدل بدء المحتوى (المادة 1 مكرر)
_LABEL_SUFFIXES = {
    "مكرر", "مكررة", "متكرر", "متكررة",
    "معدل", "معدلة", "ملغى", "ملغاة",
}

# أرقام مركّبة مقبولة كما هي (مثل 230/1 أو 12bis) — بلا حروف عربية ملحقة
_RAW_NUMBER_RE = re.compile(r"^[0-9٠-٩]+[0-9٠-٩/.\-]*[a-zA-Z]*$")

# رأس المادة: يبدأ السطر بـ المادة أو الفصل (أول السطر فقط — لا يلتقط
# الإشارات داخل النص مثل "تنص المادة 5")
_ARTICLE_HEADER_RE = re.compile(r"^\s*(?P<marker>المادة|الفصل)")


class IngestionError(Exception):
    """خطأ تجاري في الاستيعاب يُترجم إلى استجابة HTTP في routes."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


# ---------------------------------------------------------------------------
# استخراج النص
# ---------------------------------------------------------------------------

def _extract_pdf(content: bytes) -> str:
    from pdfminer.high_level import extract_text

    try:
        return extract_text(io.BytesIO(content))
    except Exception as exc:
        raise IngestionError("ملف PDF تالف أو غير قابل للقراءة.", 400) from exc


def _extract_docx(content: bytes) -> str:
    from docx import Document

    try:
        doc = Document(io.BytesIO(content))
    except Exception as exc:
        raise IngestionError("ملف DOCX تالف أو غير قابل للقراءة.", 400) from exc
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _read_document(file) -> tuple:
    """يتحقق من ملف المستند ويعيد (filename, text المستخرج) — بلا تخزين."""
    if file is None or not (file.filename or "").strip():
        raise IngestionError("الرجاء رفع ملف مستند باسم file.", 400)
    filename = (file.filename or "").strip()
    ext = os.path.splitext(filename)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise IngestionError("صيغة الملف غير مدعومة (pdf أو docx فقط).", 400)
    content = file.read()
    if not content:
        raise IngestionError("الملف فارغ.", 400)
    if len(content) > config.INGESTION_MAX_BYTES:
        raise IngestionError(
            f"الملف يتجاوز الحد الأقصى "
            f"({config.INGESTION_MAX_BYTES // (1024 * 1024)}MB).",
            400,
        )
    if ext == ".pdf":
        return filename, _extract_pdf(content)
    return filename, _extract_docx(content)


# ---------------------------------------------------------------------------
# تقسيم النص إلى مواد
# ---------------------------------------------------------------------------

def _next_token(text: str) -> str:
    m = re.match(r"(\S+)", text.strip())
    return m.group(1) if m else ""


def _consume_suffix(label_tail: str, after: str) -> tuple:
    """ينزع لاحقة تسمية شائعة (مكرر/معدلة...) من بداية المحتوى ويلحقها بالاسم."""
    token = _next_token(after)
    if token in _LABEL_SUFFIXES:
        return f"{label_tail} {token}", after.strip()[len(token):].strip()
    return label_tail, after


def _header_info(rest: str):
    """يُفسّر بقية سطر رأس المادة ويعيد (number, label_tail, content) أو None.

    لا يعدّ الخط رأسًا صالحًا إلا إذا حوى رقمًا (لاتينيًا أو هنديًا أو
    ترتيبيًا أو مركّبًا قصيرًا) — أي "المادة/الفصل" بلا رقم يُعامل كمحتوى.
    """
    rest = rest.strip().lstrip("([{【（")
    m = re.match(r"(\S+)", rest)
    if not m:
        return None
    token = m.group(1)
    after = rest[m.end():].strip()
    cleaned = token.strip("()]}【】）:.،؛,;-ـ")
    if not cleaned:
        return None

    conv = cleaned.translate(_AR_INDIC)
    if conv.isdigit():
        label_tail, content = _consume_suffix(conv, after)
        return conv, label_tail, content

    if cleaned in _TEEN_ORDINALS:
        t2 = _next_token(after)
        if t2 in _TEEN_WORDS:
            content = after.strip()[len(t2):].strip()
            return str(_TEEN_ORDINALS[cleaned]), f"{cleaned} {t2}", content

    if cleaned in _UNIT_ORDINALS:
        label_tail, content = _consume_suffix(cleaned, after)
        return str(_UNIT_ORDINALS[cleaned]), label_tail, content

    if _RAW_NUMBER_RE.match(cleaned):
        label_tail, content = _consume_suffix(cleaned, after)
        return cleaned, label_tail, content

    return None


def segment_articles(text: str) -> tuple:
    """يُقسّم النص المستخرج إلى مواد ويعيد (preamble, articles, warnings).

    كل سطر يبدأ بـ `المادة`/`الفصل` برقم صالح يفتح مادة جديدة؛ النص قبل أول
    مادة (الديباجة) يُتجاهل مع تحذير، والمواد الفارغة تُتخطى.
    """
    preamble = []
    warnings = []
    articles = []
    current = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        m = _ARTICLE_HEADER_RE.match(line)
        if m:
            info = _header_info(line[m.end():])
            if info is not None:
                number, label_tail, content = info
                if current is not None:
                    articles.append(current)
                current = {
                    "number": number,
                    "label": f"{m.group('marker')} {label_tail}".strip(),
                    "content": content,
                }
                continue
        if current is None:
            preamble.append(line)
        else:
            current["content"] = (
                f"{current['content']}\n{line}" if current["content"] else line
            )

    if current is not None:
        articles.append(current)

    kept = []
    for article in articles:
        article["content"] = article["content"].strip()
        if article["content"]:
            kept.append(article)
    dropped = len(articles) - len(kept)
    if dropped:
        warnings.append(f"تخطّى {dropped} مادة فارغة المحتوى.")

    if preamble:
        warnings.append(
            f"نص تمهيدي قبل أول مادة — يُتجاهل: {' '.join(preamble)[:100]}"
        )
    return preamble, kept, warnings


def _warn_duplicates(articles: list, warnings: list) -> None:
    seen = set()
    duplicates = []
    for article in articles:
        number = article["number"]
        if number in seen:
            duplicates.append(number)
        seen.add(number)
    if duplicates:
        unique = sorted(set(duplicates))
        preview = ", ".join(unique[:5])
        if len(unique) > 5:
            preview += f"... ({len(unique)} مكرر)"
        warnings.append(f"أرقام مواد مكررة (أُدرجت كما هي): {preview}")


# ---------------------------------------------------------------------------
# الاستيعاب
# ---------------------------------------------------------------------------

def _coerce_flag(value, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def import_document(admin_id: int, data: dict, file, dry_run: bool = False) -> dict:
    """يستخرج ويقسّم ملف مستند ويُفهرس مواده في المكتبة (أو يعاين بلا كتابة).

    dry_run=True: يعيد المقالات كاملة للمراجعة دون أي كتابة (ولا تسجيل).
    خلاف ذلك: ينشئ legal_text + المواد + سجل تدقيق في معاملة واحدة.
    """
    title = (data.get("title") or "").strip()
    if not title:
        raise IngestionError("عنوان النص القانوني (title) مطلوب.", 400)
    try:
        category_id = int(data.get("category_id"))
    except (TypeError, ValueError):
        raise IngestionError("category_id يجب أن يكون رقمًا.", 400)
    text_type = (data.get("type") or "").strip()
    if text_type not in LEGAL_TEXT_TYPES:
        raise IngestionError(f"نوع النص غير معروف: {text_type}.", 400)

    filename, text = _read_document(file)
    if not text.strip():
        raise IngestionError(
            "الملف لا يحتوي على نص قابل للاستخراج (قد يكون ممسوحًا ضوئيًا "
            "أو تالفًا).",
            400,
        )

    _preamble, articles, warnings = segment_articles(text)
    _warn_duplicates(articles, warnings)
    if not articles:
        if len(text.strip()) <= config.INGESTION_SINGLE_ARTICLE_MAX_CHARS:
            articles = [
                {"number": "1", "label": "النص الكامل", "content": text.strip()}
            ]
            warnings.append(
                "لم تُعثر على عناوين مواد — أُدرج النص كاملًا كمادة واحدة."
            )
        else:
            raise IngestionError(
                "تعذّر تمييز بنية المواد في المستند — قد يكون ممسوحًا ضوئيًا "
                "أو بتنسيق غير معتاد.",
                400,
            )
    if len(articles) > config.INGESTION_MAX_ARTICLES:
        raise IngestionError(
            f"الملف يحتوي على {len(articles)} مادة — يتجاوز السقف "
            f"({config.INGESTION_MAX_ARTICLES}).",
            400,
        )

    with db_session() as conn:
        category = conn.execute(
            "SELECT id FROM categories WHERE id = ?", (category_id,)
        ).fetchone()
        if category is None:
            raise IngestionError("القسم غير موجود.", 404)

    if dry_run:
        return {
            "dry_run": True,
            "category_id": category_id,
            "type": text_type,
            "title": title,
            "filename": filename,
            "article_count": len(articles),
            "articles": articles,
            "warnings": warnings,
        }

    is_sample_data = int(_coerce_flag(data.get("is_sample_data"), default=True))
    source_note = (data.get("source_note") or "").strip()
    if not source_note:
        source_note = "مُستورد عبر محرك رفع المستندات."

    with db_session() as conn:
        cur = conn.execute(
            """INSERT INTO legal_texts
               (category_id, type, title, official_ref, enacted_date,
                last_amended, source_note, is_sample_data)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                category_id, text_type, title,
                data.get("official_ref"), data.get("enacted_date"),
                data.get("last_amended"), source_note, is_sample_data,
            ),
        )
        text_id = cur.lastrowid
        for article in articles:
            conn.execute(
                "INSERT INTO articles "
                "(legal_text_id, number, label, content, plain_explanation, keywords)"
                " VALUES (?,?,?,?,?,?)",
                (text_id, article["number"], article["label"],
                 article["content"], None, None),
            )
        _log_admin_action(
            conn, admin_id, "ingestion.import", "legal_text", text_id,
            f"filename={filename}; articles={len(articles)}",
        )

    return {
        "id": text_id,
        "title": title,
        "article_count": len(articles),
        "warnings": warnings,
        "message": "تم استيراد المستند وفهرسة مواده تلقائيًا.",
    }
