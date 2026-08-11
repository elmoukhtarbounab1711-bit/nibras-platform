"""
توليد PDF للنصوص القانونية (reportlab + تشكيل عربي).

يُشكِّل النص العربي عبر arabic-reshaper/python-bidi ثم يبنيه reportlab
بخط عربي من نظام التشغيل (Tahoma وأخواتها)، فيُنتج ملف PDF يُعرض داخل
الواجهة (عارض PDF.js) ويُحمَّل عند الطلب — مع احترام عزل المستأجر عبر
طبقة الخدمة (services.get_text / list_text_articles_full).
"""
import os

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    PageTemplate,
    Paragraph,
    Spacer,
)

from . import services

_FONT_REGULAR = None
_FONT_BOLD = None

_BRAND = "نبراس"
_FOOTER = "منارة المعرفة القانونية المغربية"


def _find_arabic_fonts():
    fonts_dir = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
    for name, bold_name in (
        ("tahoma.ttf", "tahomabd.ttf"),
        ("segoeui.ttf", "segoeuib.ttf"),
        ("arial.ttf", "arialbd.ttf"),
        ("simpo.ttf", "simpbdo.ttf"),
    ):
        regular = os.path.join(fonts_dir, name)
        if os.path.exists(regular):
            bold = os.path.join(fonts_dir, bold_name)
            return regular, (bold if os.path.exists(bold) else regular)
    raise RuntimeError("لا يوجد خط عربي متاح لتوليد PDF على هذا النظام.")


def _ensure_fonts():
    global _FONT_REGULAR, _FONT_BOLD
    if _FONT_REGULAR:
        return
    regular, bold = _find_arabic_fonts()
    pdfmetrics.registerFont(TTFont("Nibras", regular))
    try:
        pdfmetrics.registerFont(TTFont("Nibras-Bold", bold))
    except Exception:  # noqa: BLE001 — الخط الغليظ قد لا يوجد: يُستعمل العادي
        pdfmetrics.registerFont(TTFont("Nibras-Bold", regular))
    _FONT_REGULAR = "Nibras"
    _FONT_BOLD = "Nibras-Bold"


def _ar(text):
    """تشكيل + إعادة ترتيب للنص العربي للعرض داخل PDF."""
    try:
        return get_display(arabic_reshaper.reshape(str(text or "")))
    except Exception:  # noqa: BLE001 — فشل التشكيل (مثل حرف غير مدعوم): يُرجع النص كما هو
        return str(text or "")


def _xml(text):
    return (
        str(text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _par(text, style):
    """فقرة عربية جاهزة (تشكيل + أسطر متعددة)."""
    lines = _ar(text).replace("\r\n", "\n").split("\n")
    body = "<br/>".join(_xml(line) for line in lines)
    return Paragraph(body, style)


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont(_FONT_REGULAR, 8)
    canvas.setFillColor(colors.HexColor("#8C6A32"))
    canvas.drawString(20 * mm, 14 * mm, _BRAND)
    canvas.drawRightString(A4[0] - 20 * mm, 14 * mm, _FOOTER)
    canvas.drawCentredString(A4[0] / 2, 14 * mm, f"صفحة {doc.page}")
    canvas.restoreState()


def render_text_pdf(text_id):
    """يولّد PDF كاملًا للنص القانوني؛ يرجع (bytes, filename) أو None إن غاب."""
    _ensure_fonts()
    text = services.get_text(text_id)
    if not text:
        return None
    articles = services.list_text_articles_full(text_id)

    base = {
        "fontName": _FONT_REGULAR,
        "fontSize": 10.5,
        "leading": 19,
        "textColor": colors.HexColor("#1C2D42"),
        "alignment": TA_JUSTIFY,
        "wordWrap": "CJK",
        "spaceAfter": 8,
    }
    st_title = ParagraphStyle(
        "t", fontName=_FONT_BOLD, fontSize=22, leading=32,
        alignment=TA_CENTER, textColor=colors.HexColor("#0F1B2B"),
    )
    st_meta = ParagraphStyle(
        "m", **{**base, "fontSize": 10, "leading": 17, "alignment": TA_CENTER,
                "textColor": colors.HexColor("#8C6A32")},
    )
    st_label = ParagraphStyle(
        "l", fontName=_FONT_BOLD, fontSize=13, leading=22, alignment=TA_RIGHT,
        textColor=colors.HexColor("#8C6A32"), spaceBefore=14, spaceAfter=4,
    )
    st_body = ParagraphStyle("b", **base)
    st_explain = ParagraphStyle(
        "e", **{**base, "fontName": _FONT_BOLD, "fontSize": 10, "leading": 18,
                "textColor": colors.HexColor("#3B6B4F")},
    )
    st_note = ParagraphStyle(
        "n", **{**base, "fontSize": 9.5, "leading": 16,
                "textColor": colors.HexColor("#7A7368"),
                "borderColor": colors.HexColor("#E4D9C0"),
                "borderWidth": 0.8, "borderPadding": 8, "spaceBefore": 6},
    )

    story = []
    story.append(Paragraph(
        _ar(f"{_BRAND} — المكتبة القانونية"),
        ParagraphStyle("brand", fontName=_FONT_REGULAR, fontSize=11,
                       alignment=TA_CENTER, textColor=colors.HexColor("#B8863F"),
                       spaceAfter=6),
    ))
    story.append(Paragraph(_ar(text.get("title") or "نص قانوني"), st_title))
    meta = " · ".join(
        x for x in (
            _ar(text.get("category_name") or ""),
            _ar(text.get("official_ref") or ""),
            _ar(text.get("type") or ""),
        ) if x
    )
    if meta:
        story.append(Paragraph(meta, st_meta))
    if text.get("enacted_date"):
        story.append(Paragraph(
            _ar(f"سُنّ {text['enacted_date']}") + f" — {len(articles)} مادة", st_meta,
        ))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(
        width="100%", thickness=1, color=colors.HexColor("#B8863F"), spaceAfter=10,
    ))
    if text.get("source_note"):
        story.append(_par(f"مصدر النص: {text['source_note']}", st_note))
        story.append(Spacer(1, 4))

    if not articles:
        story.append(_par("لا توجد مواد مسجّلة لهذا النص بعد.", st_body))

    for a in articles:
        story.append(Paragraph(_ar(a.get("label") or f"المادة {a.get('number')}"), st_label))
        if a.get("content"):
            story.append(_par(a["content"], st_body))
        if a.get("plain_explanation"):
            story.append(_par(f"شرح مبسّط: {a['plain_explanation']}", st_explain))
        if a.get("keywords"):
            story.append(_par("كلمات مفتاحية: " + a["keywords"], st_note))

    class _Buffer:
        def __init__(self):
            self._data = bytearray()

        def write(self, data):
            self._data.extend(data)

        def getvalue(self):
            return bytes(self._data)

    buf = _Buffer()
    margins = 20 * mm
    doc = BaseDocTemplate(
        buf, pagesize=A4, leftMargin=margins, rightMargin=margins,
        topMargin=margins, bottomMargin=22 * mm,
        title=f"{_BRAND} — {text.get('title')}", author=_BRAND,
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")
    doc.addPageTemplates([PageTemplate(id="page", frames=[frame], onPage=_footer)])
    doc.build(story)

    return buf.getvalue(), f"text-{text_id}.pdf"
