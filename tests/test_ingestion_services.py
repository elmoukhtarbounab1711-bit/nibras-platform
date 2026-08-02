"""
اختبارات محرك رفع المستندات (services_ingestion) — المرحلة 10 (قرار D-028).

تقسيم النصوص إلى مواد (المادة/الفصل بأرقام لاتينية/هندية/ترتيبية)، استخراج
PDF/DOCX، والاستيعاب في المكتبة (dry_run بلا كتابة، سجل تدقيق، تحقق المدخلات).
"""
import io
import os

import pytest

from app import config, services
from app import services_ingestion as ing
from app.database import db_session
from app.services_auth import create_user_with_role
from app.services_ingestion import IngestionError

PASSWORD = "test-password-123"

_FONT_CANDIDATES = [
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",
]


class _FakeFile:
    def __init__(self, filename, content=b""):
        self.filename = filename
        self._content = content

    def read(self):
        return self._content


def _docx_bytes(paragraphs):
    from docx import Document

    doc = Document()
    for p in paragraphs:
        doc.add_paragraph(p)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _pdf_latin_bytes(lines):
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    y = 750
    for line in lines:
        c.drawString(72, y, line)
        y -= 18
    c.save()
    return buf.getvalue()


def _pdf_arabic_bytes(lines):
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas

    font = next((p for p in _FONT_CANDIDATES if os.path.exists(p)), None)
    if font is None:
        pytest.skip("لا يوجد خط عربي قابل للتضمين على هذا النظام")
    pdfmetrics.registerFont(TTFont("ArTestFont", font))
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.setFont("ArTestFont", 14)
    y = 750
    for line in lines:
        c.drawString(72, y, line)
        y -= 18
    c.save()
    return buf.getvalue()


def _admin():
    return create_user_with_role(
        "admin-ingest@nibras.test", PASSWORD, "مدير استيعاب", "admin",
    )


# ---------------------------------------------------------------------------
# المقسّم (دوال نقية بلا قاعدة بيانات)
# ---------------------------------------------------------------------------

def test_segment_simple_digits():
    preamble, articles, warnings = ing.segment_articles(
        "المادة 1 النص الأول\nالمادة 2 النص الثاني"
    )
    assert [(a["number"], a["label"]) for a in articles] == [
        ("1", "المادة 1"), ("2", "المادة 2"),
    ]
    assert articles[0]["content"] == "النص الأول"
    assert not preamble and not warnings


def test_segment_arabic_indic_digits():
    _p, articles, _w = ing.segment_articles(
        "المادة ١ الأول\nالمادة ٢ الثاني\nالمادة ٣ الثالث"
    )
    assert [a["number"] for a in articles] == ["1", "2", "3"]


def test_segment_ordinal_and_teen():
    _p, articles, _w = ing.segment_articles(
        "الفصل الأول أحكام عامة\nالفصل الثاني عشر أحكام خاصة"
    )
    assert [(a["number"], a["label"]) for a in articles] == [
        ("1", "الفصل الأول"), ("12", "الفصل الثاني عشر"),
    ]


def test_segment_suffix_kept_in_label():
    _p, articles, _w = ing.segment_articles(
        "المادة 1 مكرر نص\nالمادة 2 نص"
    )
    assert articles[0]["label"] == "المادة 1 مكرر"
    assert articles[0]["content"] == "نص"
    assert articles[1]["number"] == "2"


def test_segment_parens_and_punctuation():
    _p, articles, _w = ing.segment_articles(
        "المادة (12): النص الأول\nالمادة 13. النص الثاني"
    )
    assert articles[0]["number"] == "12"
    assert articles[1]["number"] == "13"
    assert articles[1]["content"] == "النص الثاني"


def test_segment_compound_number_kept():
    _p, articles, _w = ing.segment_articles(
        "المادة 230/1 نص\nالمادة 230/2 نص"
    )
    assert [a["number"] for a in articles] == ["230/1", "230/2"]


def test_segment_mid_sentence_marker_not_header():
    _p, articles, _w = ing.segment_articles(
        "تنص المادة 5 على أحكام\nالمادة 6 النص"
    )
    assert [a["number"] for a in articles] == ["6"]
    assert articles[0]["content"] == "النص"
    assert _w and "نص تمهيدي" in _w[0]


def test_segment_empty_content_articles_skipped():
    _p, articles, warnings = ing.segment_articles(
        "المادة 1\nالمادة 2 نص"
    )
    assert [a["number"] for a in articles] == ["2"]
    assert any("فارغة" in w for w in warnings)


def test_segment_orphan_article_word_not_header():
    _p, articles, _w = ing.segment_articles(
        "المادة أحكام عامة تبدأ هنا"
    )
    assert articles == []
    assert _p == ["المادة أحكام عامة تبدأ هنا"]


def test_segment_blank_lines_ignored():
    _p, articles, _w = ing.segment_articles(
        "المادة 1 نص\n\nالمادة 2 نص\n"
    )
    assert len(articles) == 2


# ---------------------------------------------------------------------------
# الاستخراج
# ---------------------------------------------------------------------------

def test_docx_extraction():
    content = _docx_bytes(["المادة 1 نص أول", "", "المادة 2 نص ثانٍ"])
    filename, text = ing._read_document(_FakeFile("law.docx", content))
    assert filename == "law.docx"
    assert "المادة 1 نص أول" in text and "المادة 2 نص ثانٍ" in text


def test_pdf_latin_extraction():
    content = _pdf_latin_bytes(["Article 1 - This is content"])
    _name, text = ing._read_document(_FakeFile("law.pdf", content))
    assert "This is content" in text


def test_pdf_arabic_extraction():
    content = _pdf_arabic_bytes(["المادة 1 نص عربي", "المادة 2 نص عربي ثانٍ"])
    _name, text = ing._read_document(_FakeFile("law.pdf", content))
    assert "المادة 1" in text and "المادة 2" in text


# ---------------------------------------------------------------------------
# الاستيعاب
# ---------------------------------------------------------------------------

def test_docx_import_indexes_articles(fresh_db):
    admin = _admin()
    content = _docx_bytes(["المادة 1 الزواج عقد.", "المادة 2 يقع الزواج عند."])
    result = ing.import_document(
        admin.id,
        {"category_id": 2, "type": "code", "title": "مدونة الأسرة المستوردة"},
        _FakeFile("code.docx", content),
    )
    assert result["article_count"] == 2
    assert result["id"] > 0
    with db_session() as conn:
        text = conn.execute(
            "SELECT * FROM legal_texts WHERE id = ?", (result["id"],)
        ).fetchone()
        assert text["title"] == "مدونة الأسرة المستوردة"
        assert text["source_note"] == "مُستورد عبر محرك رفع المستندات."
        assert text["is_sample_data"] == 1
        count = conn.execute(
            "SELECT COUNT(*) AS c FROM articles WHERE legal_text_id = ?",
            (result["id"],),
        ).fetchone()["c"]
        assert count == 2
        audit = conn.execute(
            "SELECT * FROM admin_audit_log WHERE target_id = ? "
            "AND action = 'ingestion.import'",
            (result["id"],),
        ).fetchone()
        assert audit is not None
    # بحث FTS يجد المحتوى المفهرس تلقائيًا
    hits = services.search_articles("الزواج عقد")
    assert any(h["legal_text_title"] == "مدونة الأسرة المستوردة" for h in hits)


def test_dry_run_writes_nothing(fresh_db):
    admin = _admin()
    content = _docx_bytes(["المادة 1 نص."])
    with db_session() as conn:
        before = conn.execute("SELECT COUNT(*) AS c FROM legal_texts").fetchone()["c"]
    result = ing.import_document(
        admin.id,
        {"category_id": 1, "type": "law", "title": "معاينة"},
        _FakeFile("x.docx", content),
        dry_run=True,
    )
    assert result["dry_run"] is True
    assert result["article_count"] == 1
    assert result["articles"][0]["content"] == "نص."
    with db_session() as conn:
        after = conn.execute("SELECT COUNT(*) AS c FROM legal_texts").fetchone()["c"]
        audit = conn.execute(
            "SELECT COUNT(*) AS c FROM admin_audit_log "
            "WHERE action = 'ingestion.import'"
        ).fetchone()["c"]
    assert after == before
    assert audit == 0


def test_import_requires_fields(fresh_db):
    admin = _admin()
    content = _docx_bytes(["المادة 1 نص."])
    with pytest.raises(IngestionError):
        ing.import_document(admin.id, {}, _FakeFile("x.docx", content))
    with pytest.raises(IngestionError):
        ing.import_document(
            admin.id,
            {"category_id": 1, "type": "code"},
            _FakeFile("x.docx", content),
        )
    with pytest.raises(IngestionError):
        ing.import_document(
            admin.id,
            {"category_id": 999, "type": "code", "title": "عنوان"},
            _FakeFile("x.docx", content),
        )
    with pytest.raises(IngestionError):
        ing.import_document(
            admin.id,
            {"category_id": 1, "type": "bogus", "title": "عنوان"},
            _FakeFile("x.docx", content),
        )


def test_document_validation(fresh_db):
    admin = _admin()
    data = {"category_id": 1, "type": "code", "title": "عنوان"}
    with pytest.raises(IngestionError):
        ing.import_document(admin.id, data, None)
    with pytest.raises(IngestionError):
        ing.import_document(admin.id, data, _FakeFile("doc.txt", b"x"))
    with pytest.raises(IngestionError):
        ing.import_document(admin.id, data, _FakeFile("doc.pdf", b""))


def test_empty_text_rejected(fresh_db):
    admin = _admin()
    # مستند DOCX فارغ (بلا فقرات نصية) يُستخرج بنص فارغ
    content = _docx_bytes([])
    with pytest.raises(IngestionError):
        ing.import_document(
            admin.id,
            {"category_id": 1, "type": "code", "title": "عنوان"},
            _FakeFile("empty.docx", content),
        )


def test_corrupt_pdf_rejected(fresh_db):
    admin = _admin()
    with pytest.raises(IngestionError):
        ing.import_document(
            admin.id,
            {"category_id": 1, "type": "code", "title": "عنوان"},
            _FakeFile("bad.pdf", b"%PDF-1.4 garbage garbage not a pdf"),
        )


def test_latin_pdf_fallback_single_article(fresh_db):
    admin = _admin()
    content = _pdf_latin_bytes(["Short single article text here"])
    result = ing.import_document(
        admin.id,
        {"category_id": 1, "type": "law", "title": "وثيقة صغيرة"},
        _FakeFile("small.pdf", content),
    )
    assert result["article_count"] == 1
    assert any("لم تُعثر على عناوين" in w for w in result["warnings"])


def test_long_unstructured_text_rejected(fresh_db, monkeypatch):
    admin = _admin()
    monkeypatch.setattr(config, "INGESTION_SINGLE_ARTICLE_MAX_CHARS", 20)
    long_text = "\n".join(f"فقرة طويلة رقم {i} " * 10 for i in range(50))
    content = _docx_bytes([long_text])
    with pytest.raises(IngestionError):
        ing.import_document(
            admin.id,
            {"category_id": 1, "type": "code", "title": "بلا مواد"},
            _FakeFile("long.docx", content),
        )


def test_max_articles_cap(fresh_db, monkeypatch):
    admin = _admin()
    monkeypatch.setattr(config, "INGESTION_MAX_ARTICLES", 2)
    content = _docx_bytes(
        ["المادة 1 نص", "المادة 2 نص", "المادة 3 نص", "المادة 4 نص"]
    )
    with pytest.raises(IngestionError):
        ing.import_document(
            admin.id,
            {"category_id": 1, "type": "code", "title": "كبير"},
            _FakeFile("big.docx", content),
        )


def test_size_limit(fresh_db, monkeypatch):
    admin = _admin()
    monkeypatch.setattr(config, "INGESTION_MAX_BYTES", 10)
    content = _docx_bytes(["المادة 1 نص."])
    assert len(content) > 10
    with pytest.raises(IngestionError):
        ing.import_document(
            admin.id,
            {"category_id": 1, "type": "code", "title": "كبير"},
            _FakeFile("big.docx", content),
        )


def test_duplicate_numbers_warn_only(fresh_db):
    admin = _admin()
    content = _docx_bytes(["المادة 1 نص أ.", "المادة 1 نص ب.", "المادة 2 نص ج."])
    result = ing.import_document(
        admin.id,
        {"category_id": 1, "type": "code", "title": "بأرقام مكررة"},
        _FakeFile("dup.docx", content),
    )
    assert result["article_count"] == 3
    assert any("أرقام مواد مكررة" in w for w in result["warnings"])


def test_custom_fields_and_sample_flag(fresh_db):
    admin = _admin()
    content = _docx_bytes(["المادة 1 نص."])
    result = ing.import_document(
        admin.id,
        {
            "category_id": 1, "type": "decree", "title": "ظهير مستورد",
            "official_ref": "ظهير 1.05.12", "enacted_date": "2005-01-01",
            "source_note": "مصدر رسمي خاص", "is_sample_data": 0,
        },
        _FakeFile("dah.docx", content),
    )
    with db_session() as conn:
        text = conn.execute(
            "SELECT * FROM legal_texts WHERE id = ?", (result["id"],)
        ).fetchone()
    assert text["official_ref"] == "ظهير 1.05.12"
    assert text["enacted_date"] == "2005-01-01"
    assert text["source_note"] == "مصدر رسمي خاص"
    assert text["is_sample_data"] == 0


def test_pdf_arabic_import(fresh_db):
    admin = _admin()
    content = _pdf_arabic_bytes(
        ["المادة 1 الزواج عقد رضائي.", "المادة 2 يتطلب سن الرشد."]
    )
    result = ing.import_document(
        admin.id,
        {"category_id": 2, "type": "code", "title": "مدونة PDF"},
        _FakeFile("family.pdf", content),
    )
    assert result["article_count"] == 2
    hits = services.search_articles("سن الرشد")
    assert any(h["legal_text_title"] == "مدونة PDF" for h in hits)
