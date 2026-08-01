"""
خدمات مولّد الوثائق (المرحلة 4) — قرار D-022.

توليد وثائق قانونية من قوالب بيانات (field_schema + body_template بنمط
Jinja2) عبر سؤال موجَّه: تحقق صارم من الإجابات ثم استبدال في هيكل ثابت
وحفظ لكل مستخدم متدرج (version) وتصدير PDF/DOCX في الذاكرة بلا ملفات
على القرص. القوالب بيانات لا كود (المواصفة التقنية §6) — تُضاف أنواع
وثائق جديدة عبر السجل لا إعادة نشر. التصدير: DOCX بـ python-docx
(ضبط RTL)، PDF بـ reportlab + arabic-reshaper + python-bidi مع خط عربي
يُحلَّل من مسارات شائعة (D-022 — استُبعد WeasyPrint لتعذره على ويندوز).
"""
import io
import json
import os
from datetime import date

from jinja2 import Environment, StrictUndefined
from jinja2.exceptions import UndefinedError

from . import config
from .database import db_session

_FIELD_TYPES = {"text", "textarea", "number", "date", "select", "boolean"}

# قوالب نموذجية عربية (بيانات لا كود) — محتوى إرشادي تعليمي؛ أي وثيقة
# تنتهي بتنبيه صريح بأنها لا تغني عن مراجعة قانونية/توثيق. إدارة المحتوى
# (FR-12.1) مؤجَّلة كوحدة أدمن — النمط ذاته في D-021.
_SEED_TEMPLATES = [
    {
        "slug": "rental-contract",
        "name": "عقد كراء سكني",
        "category": "العقود",
        "field_schema": [
            {"name": "landlord_name", "label": "اسم المؤجّر (المالك)", "type": "text", "required": True},
            {"name": "tenant_name", "label": "اسم المكتري", "type": "text", "required": True},
            {"name": "property_address", "label": "عنوان العقار", "type": "textarea", "required": True},
            {"name": "monthly_rent", "label": "الكراء الشهري (درهم)", "type": "number", "required": True, "min": 0},
            {"name": "start_date", "label": "تاريخ بداية العقد", "type": "date", "required": True},
            {"name": "duration_months", "label": "المدة (بالأشهر)", "type": "number", "required": True, "min": 1},
            {"name": "deposit_amount", "label": "وديعة التأمين (درهم)", "type": "number", "required": True, "min": 0},
            {"name": "payment_date", "label": "يوم أداء الكراء", "type": "text", "required": False},
        ],
        "body_template": """عقد كراء سكني

حُرر هذا العقد بين:

السيد/السيدة {{ landlord_name }}، بصفته مالكًا للعقار الكائن بـ {{ property_address }}، من جهة أولى،
والسيد/السيدة {{ tenant_name }}، من جهة ثانية،

واتفق الطرفان على ما يلي:

1. يؤجِّر الطرف الأول للطرف الثاني العقار الكائن بـ {{ property_address }} قصد السكنى.
2. تُحسب مدة الكراء ابتداءً من {{ start_date }} لمدة {{ duration_months }} شهرًا.
3. يستحق كراء شهري قدره {{ monthly_rent }} درهم{% if payment_date %}، يُؤدى في {{ payment_date }} من كل شهر{% endif %}.
4. أودع المكتري لدى المؤجِّر وديعة تأمين قدرها {{ deposit_amount }} درهم تُرَد عند انتهاء العقد بعد استيفاء كل الالتزامات.

حُرر هذا العقد ليكون حجة على الطرفين وتحريرًا منهما.

تنبيه: هذا العقد نموذج تعليمي يُعدّه نظام نبراس بلا مراجعة قانونية؛ يلزم عرضه على مفوض قضائي أو عدل للتوثيق قبل الاعتماد عليه.""",
    },
    {
        "slug": "power-of-attorney",
        "name": "وكالة خاصة",
        "category": "التوثيق",
        "field_schema": [
            {"name": "principal_name", "label": "اسم الموكل", "type": "text", "required": True},
            {"name": "agent_name", "label": "اسم الوكيل", "type": "text", "required": True},
            {"name": "scope", "label": "نطاق الوكالة", "type": "textarea", "required": True},
            {"name": "city", "label": "مدينة التحرير", "type": "text", "required": True},
            {"name": "date", "label": "تاريخ الوكالة", "type": "date", "required": True},
            {"name": "valid_until", "label": "مدة الصلاحية (تاريخ)", "type": "date", "required": False},
        ],
        "body_template": """وكالة خاصة

أنا الموقّع أسفله السيد/السيدة {{ principal_name }}، أصيلًا عن نفسي، أُنيب السيد/السيدة {{ agent_name }} في القيام بالأعمال التالية:

{{ scope }}

وتكون هذه الوكالة سارية المفعول من {{ date }}{% if valid_until %} إلى غاية {{ valid_until }}{% endif %} أو عند إلغائها.

حُررت بمدينة {{ city }} ليكون لها أثرها القانوني.

تنبيه: نموذج تعليمي من إعداد نظام نبراس؛ لا يُعتمد في التصرفات العقارية أو التوثيقية إلا بعد تحريرها لدى عدل/موثّق.""",
    },
    {
        "slug": "debt-acknowledgment",
        "name": "إقرار بدين",
        "category": "العقود",
        "field_schema": [
            {"name": "debtor_name", "label": "اسم المدين (المُقر)", "type": "text", "required": True},
            {"name": "creditor_name", "label": "اسم الدائن", "type": "text", "required": True},
            {"name": "amount", "label": "مبلغ الدين (درهم)", "type": "number", "required": True, "min": 0},
            {"name": "reason", "label": "سبب الدين", "type": "textarea", "required": False},
            {"name": "repayment_date", "label": "أجل الأداء", "type": "date", "required": False},
            {"name": "city", "label": "مكان التحرير", "type": "text", "required": False},
        ],
        "body_template": """إقرار بدين

أقرّ أنا الموقّع أسفله السيد/السيدة {{ debtor_name }} بأن في ذمتي للسيد/السيدة {{ creditor_name }} مبلغًا قدره {{ amount }} درهم{% if reason %} ({{ reason }}){% endif %}.

ألتزم بأداء هذا المبلغ كاملًا في أجل أقصاه {{ repayment_date or "حسب الاتفاق بين الطرفين" }}.

حُرر هذا الإقرار{% if city %} بمدينة {{ city }}{% endif %} ليكون حجة على من يهمه الأمر.

تنبيه: نموذج تعليمي من إعداد نظام نبراس؛ يلزم عرضه على عدل أو مفوض قضائي لتوثيقه والتحقق من صحته القانونية.""",
    },
]

# مسارات خطوط عربية شائعة (ويندوز ثم لينكس) — تُحلَّل عند أول تصدير PDF
# ويُتجاوز المسار عبر NIBRAS_PDF_FONT (config.PDF_FONT_PATH)
_CANDIDATE_FONTS = [
    ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"),
    ("/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",
     "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Bold.ttf"),
    ("/usr/share/fonts/opentype/noto/NotoNaskhArabic-Regular.ttf", None),
    ("/usr/share/fonts/truetype/amiri/Amiri-Regular.ttf", None),
]

_FONT_REGISTERED = {"regular": None, "bold": None}


class DocumentError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def ensure_defaults():
    """بذر القوالب النموذجية (idempotent) — تُستدعى من init_db."""
    with db_session() as conn:
        for tmpl in _SEED_TEMPLATES:
            existing = conn.execute(
                "SELECT id FROM document_templates WHERE slug = ?", (tmpl["slug"],)
            ).fetchone()
            if existing:
                continue
            conn.execute(
                "INSERT INTO document_templates "
                "(slug, name, category, field_schema, body_template, created_at) "
                "VALUES (?, ?, ?, ?, ?, datetime('now'))",
                (
                    tmpl["slug"],
                    tmpl["name"],
                    tmpl["category"],
                    json.dumps(tmpl["field_schema"], ensure_ascii=False),
                    tmpl["body_template"],
                ),
            )


def _parse_schema(field_schema: str) -> list:
    try:
        fields = json.loads(field_schema)
    except (TypeError, ValueError):
        raise DocumentError("مخطط قالب الوثيقة غير صالح.", 500)
    if not isinstance(fields, list):
        raise DocumentError("مخطط قالب الوثيقة غير صالح.", 500)
    return fields


def list_templates(category: str | None = None):
    query = """
        SELECT id, slug, name, category
        FROM document_templates
    """
    params = []
    if category:
        query += " WHERE category = ?"
        params.append(category)
    query += " ORDER BY category, name"
    with db_session() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def get_template(slug: str):
    with db_session() as conn:
        row = conn.execute(
            "SELECT id, slug, name, category, field_schema, body_template "
            "FROM document_templates WHERE slug = ?",
            (slug,),
        ).fetchone()
        if not row:
            return None
        tmpl = dict(row)
        tmpl["fields"] = _parse_schema(tmpl.pop("field_schema"))
        return tmpl


def _get_template_by_ident(ident):
    """يحل القالب بالمعرّف الرقمي (template_id) أو بالرابط (template_slug)."""
    with db_session() as conn:
        if isinstance(ident, int):
            row = conn.execute(
                "SELECT id, slug, name, category, field_schema, body_template "
                "FROM document_templates WHERE id = ?",
                (ident,),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT id, slug, name, category, field_schema, body_template "
                "FROM document_templates WHERE slug = ?",
                (str(ident),),
            ).fetchone()
        if not row:
            return None
        tmpl = dict(row)
        tmpl["fields"] = _parse_schema(tmpl.pop("field_schema"))
        return tmpl


def _validate_answers(fields: list, answers: dict) -> dict:
    """تحقق صارم من كل إجابة حسب مخطط الحقل — يرفض بأول خطأ (رسالة عربية)."""
    cleaned = {}
    for field in fields:
        name = field["name"]
        label = field.get("label") or name
        ftype = field.get("type", "text")
        if ftype not in _FIELD_TYPES:
            raise DocumentError(f"نوع حقل غير معروف في القالب: {name}", 500)
        raw = answers.get(name)
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            if field.get("required"):
                raise DocumentError(f"الحقل «{label}» مطلوب.", 400)
            # قيم افتراضية للحقول الاختيارية حتى تمر بـ StrictUndefined داخل
            # {% if %} (فراغ/None → falsy فلا يُطبع شيء) — قيد D-022
            cleaned[name] = None if ftype in ("number", "boolean") else ""
            continue
        if ftype in ("text", "textarea"):
            cleaned[name] = str(raw).strip()
        elif ftype == "number":
            try:
                value = float(str(raw).replace(",", "").strip())
            except (TypeError, ValueError):
                raise DocumentError(f"الحقل «{label}» يجب أن يكون رقمًا.", 400)
            value = int(value) if value.is_integer() else value
            if "min" in field and value < field["min"]:
                raise DocumentError(f"الحقل «{label}» لا يمكن أن يقل عن {field['min']}.", 400)
            if "max" in field and value > field["max"]:
                raise DocumentError(f"الحقل «{label}» لا يمكن أن يزيد عن {field['max']}.", 400)
            cleaned[name] = value
        elif ftype == "date":
            text = str(raw).strip()
            try:
                date.fromisoformat(text)
            except ValueError:
                raise DocumentError(
                    f"الحقل «{label}» يجب أن يكون تاريخًا بصيغة YYYY-MM-DD.", 400
                )
            cleaned[name] = text
        elif ftype == "select":
            options = field.get("options") or []
            if raw not in options:
                raise DocumentError(f"القيمة المقدمة للحقل «{label}» غير مقبولة.", 400)
            cleaned[name] = raw
        elif ftype == "boolean":
            if isinstance(raw, bool):
                cleaned[name] = raw
            elif isinstance(raw, str) and raw.strip().lower() in ("true", "false"):
                cleaned[name] = raw.strip().lower() == "true"
            else:
                raise DocumentError(f"الحقل «{label}» يجب أن يكون قيمة منطقية.", 400)
    return cleaned


def _render_body(body_template: str, cleaned_answers: dict) -> str:
    """يستبدل الإجابات في الهيكل الثابت بنمط Jinja2 مع StrictUndefined —
    أي متغير مفقود خطأ صريح لا فراغ صامت (قرار D-022)."""
    try:
        env = Environment(undefined=StrictUndefined)
        return env.from_string(body_template).render(**cleaned_answers)
    except UndefinedError as exc:
        raise DocumentError("تعذر توليد الوثيقة من الإجابات المقدمة.", 400) from exc


def _document_payload(row) -> dict:
    return {
        "id": row["id"],
        "template_id": row["template_id"],
        "template_slug": row["template_slug"],
        "template_name": row["template_name"],
        "version": row["version"],
        "doc_text": row["doc_text"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def generate_document(user_id: int, template_id, answers: dict):
    tmpl = _get_template_by_ident(template_id)
    if not tmpl:
        raise DocumentError("القالب غير موجود.", 404)
    cleaned = _validate_answers(tmpl["fields"], answers or {})
    doc_text = _render_body(tmpl["body_template"], cleaned)
    with db_session() as conn:
        cur = conn.execute(
            "INSERT INTO generated_documents "
            "(user_id, template_id, answers_json, version, doc_text, created_at, updated_at) "
            "VALUES (?, ?, ?, 1, ?, datetime('now'), datetime('now'))",
            (user_id, tmpl["id"], json.dumps(cleaned, ensure_ascii=False), doc_text),
        )
        row = conn.execute(
            "SELECT g.id, g.template_id, t.slug AS template_slug, t.name AS template_name, "
            "       g.version, g.doc_text, g.created_at, g.updated_at "
            "FROM generated_documents g JOIN document_templates t ON t.id = g.template_id "
            "WHERE g.id = ?",
            (cur.lastrowid,),
        ).fetchone()
    return _document_payload(row)


def get_user_documents(user_id: int):
    with db_session() as conn:
        rows = conn.execute(
            "SELECT g.id, g.template_id, t.slug AS template_slug, t.name AS template_name, "
            "       g.version, g.doc_text, g.created_at, g.updated_at "
            "FROM generated_documents g JOIN document_templates t ON t.id = g.template_id "
            "WHERE g.user_id = ? ORDER BY g.created_at DESC, g.id DESC",
            (user_id,),
        ).fetchall()
        return [_document_payload(r) for r in rows]


def get_document(user_id: int, doc_id: int):
    """يعيد وثيقة المستخدم مع تحقق الملكية — الغير يرى 404 (owner-only)."""
    with db_session() as conn:
        row = conn.execute(
            "SELECT g.id, g.template_id, t.slug AS template_slug, t.name AS template_name, "
            "       g.version, g.doc_text, g.created_at, g.updated_at "
            "FROM generated_documents g JOIN document_templates t ON t.id = g.template_id "
            "WHERE g.id = ? AND g.user_id = ?",
            (doc_id, user_id),
        ).fetchone()
        if not row:
            raise DocumentError("الوثيقة غير موجودة.", 404)
        return _document_payload(row)


def regenerate_document(user_id: int, doc_id: int, answers: dict):
    """FR-5.3 متدرج عند التعديل: نسخة +1 مع تحديث doc_text (قرار D-022)."""
    doc = get_document(user_id, doc_id)
    tmpl = _get_template_by_ident(doc["template_id"])
    cleaned = _validate_answers(tmpl["fields"], answers or {})
    doc_text = _render_body(tmpl["body_template"], cleaned)
    with db_session() as conn:
        conn.execute(
            "UPDATE generated_documents SET answers_json = ?, version = version + 1, "
            "doc_text = ?, updated_at = datetime('now') WHERE id = ?",
            (json.dumps(cleaned, ensure_ascii=False), doc_text, doc_id),
        )
        row = conn.execute(
            "SELECT g.id, g.template_id, t.slug AS template_slug, t.name AS template_name, "
            "       g.version, g.doc_text, g.created_at, g.updated_at "
            "FROM generated_documents g JOIN document_templates t ON t.id = g.template_id "
            "WHERE g.id = ?",
            (doc_id,),
        ).fetchone()
    return _document_payload(row)


def export_docx(doc: dict) -> bytes:
    """DOCX عربي بضبط اتجاه الفقرات RTL — توليد في الذاكرة (استيراد مؤجَّل
    فلا اعتماد صلب إن لم تُثبَّت المكتبة، نمط Anthropic في D-021)."""
    try:
        from docx import Document as DocxDocument
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn
    except ImportError:
        raise DocumentError("مكتبة تصدير DOCX غير مثبتة.", 500)
    buffer = io.BytesIO()
    d = DocxDocument()
    d.styles["Normal"].font.name = "Arial"
    lines = (doc["doc_text"] or "").split("\n")
    first = True
    for line in lines:
        text = line.strip()
        if not text:
            continue
        p = d.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p._p.get_or_add_pPr().append(OxmlElement("w:bidi"))
        run = p.add_run(text)
        run.font.name = "Arial"
        if first:
            run.bold = True
        rpr = run._element.get_or_add_rPr()
        rfonts = rpr.rFonts
        if rfonts is None:
            rfonts = OxmlElement("w:rFonts")
            rpr.append(rfonts)
        rfonts.set(qn("w:cs"), "Arial")
        first = False
    d.save(buffer)
    return buffer.getvalue()


def _resolve_pdf_font():
    """يسجّل خطًا عربيًا لدى reportlab مرة واحدة ويعيد (regular, bold)."""
    if _FONT_REGISTERED["regular"] is not None:
        return _FONT_REGISTERED["regular"], _FONT_REGISTERED["bold"]
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError:
        raise DocumentError("مكتبة تصدير PDF غير مثبتة.", 500)
    candidates = []
    if config.PDF_FONT_PATH:
        candidates.append((config.PDF_FONT_PATH, None))
    candidates.extend(_CANDIDATE_FONTS)
    for regular, bold in candidates:
        if not (regular and os.path.exists(regular)):
            continue
        pdfmetrics.registerFont(TTFont("Arabic", regular))
        bold_name = "Arabic"
        if bold and os.path.exists(bold):
            try:
                pdfmetrics.registerFont(TTFont("Arabic-Bold", bold))
                bold_name = "Arabic-Bold"
            except (TimeoutError, OSError, ValueError, TypeError, KeyError):
                bold_name = "Arabic"
        _FONT_REGISTERED["regular"] = "Arabic"
        _FONT_REGISTERED["bold"] = bold_name
        return "Arabic", bold_name
    raise DocumentError("خط عربي للتصدير غير متوفر على هذا النظام.", 500)


def export_pdf(doc: dict) -> bytes:
    """PDF عربي عبر reportlab (بايثون خالص) — إعادة ترتيب النص بـ
    arabic_reshaper + python-bidi ثم بناء المستند في الذاكرة."""
    try:
        from xml.sax.saxutils import escape

        import arabic_reshaper
        from bidi.algorithm import get_display
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    except ImportError:
        raise DocumentError("مكتبات تصدير PDF غير مثبتة.", 500)
    regular, bold = _resolve_pdf_font()
    buffer = io.BytesIO()
    base = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=25 * mm,
        rightMargin=25 * mm,
        topMargin=25 * mm,
        bottomMargin=25 * mm,
        title="نبراس — وثيقة",
    )
    styles = {
        "title": ParagraphStyle(
            "title", fontName=bold, fontSize=16, leading=22, alignment=TA_CENTER, spaceAfter=14
        ),
        "body": ParagraphStyle(
            "body", fontName=regular, fontSize=12, leading=20, alignment=TA_RIGHT
        ),
    }
    story = []
    lines = (doc["doc_text"] or "").split("\n")
    first = True
    for line in lines:
        text = line.strip()
        if not text:
            if not first:
                story.append(Spacer(1, 6))
            continue
        rendered = get_display(arabic_reshaper.reshape(text))
        style = styles["title"] if first and len(text) < 80 else styles["body"]
        story.append(Paragraph(escape(rendered), style))
        first = False
    base.build(story)
    return buffer.getvalue()
