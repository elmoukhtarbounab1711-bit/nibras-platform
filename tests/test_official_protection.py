"""
اختبارات حماية النصوص الرسمية — ZERO AI REWRITING.

تمنع مستقبلًا إدخال نص مولد عبر AI على أنه رسمي.
"""
import hashlib
import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))

from app.database import db_session
from app.services_official import (
    content_hash,
    compute_text_hash,
    verify_official_text,
    OfficialSourceImporter,
    is_official_text_mutation,
)


def test_content_hash_deterministic():
    """بصمة المحتوى ثابتة للنص نفسه."""
    text = "تلتزم البائع بتسليم المبيع للمشتري في الآجل المتفق عليه."
    h1 = content_hash(text)
    h2 = content_hash(text)
    assert h1 == h2, "Content hash must be deterministic"
    assert len(h1) == 64, "SHA-256 hash must be 64 chars"


def test_content_hash_differs_for_different_text():
    """نصوص مختلفة → بصمات مختلفة."""
    h1 = content_hash("نص أول")
    h2 = content_hash("نص ثاني")
    assert h1 != h2, "Different texts must have different hashes"


def test_content_hash_empty():
    """نص فارغ → بصمة ثابتة."""
    h = content_hash("")
    assert len(h) == 64, "Empty text should still produce a valid hash"


def test_verify_official_text_match():
    """التحقق يعيد MATCH عندما لا يتغير النص."""
    with db_session() as conn:
        # إنشاء نص تجريبي
        conn.execute(
            """INSERT INTO legal_texts
               (category_id, type, title, is_sample_data, tenant_id)
               VALUES (1, 'law', 'قانون تجريبي للاختبار', 0, 1)"""
        )
        text_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute(
            """INSERT INTO articles
               (legal_text_id, number, label, content, tenant_id)
               VALUES (?, '1', 'المادة 1', 'تلتزم البائع بتسليم المبيع.', 1)""",
            (text_id,),
        )

    # حساب البصمة في اتصال منفصل (يقرأ البيانات المُلتزمة)
    h = compute_text_hash(text_id)
    with db_session() as conn:
        conn.execute(
            "UPDATE legal_texts SET content_hash = ? WHERE id = ?",
            (h, text_id),
        )

    result = verify_official_text(text_id)
    assert result["status"] == "MATCH", f"Expected MATCH, got {result['status']}"
    assert result["stored_hash"] == result["current_hash"]


def test_official_text_mutation_detection():
    """كشف محاولات تعديل النص الأصلي عبر SQL."""
    # محاولات تعديل content
    assert is_official_text_mutation(
        "UPDATE articles SET content = 'نص مولد' WHERE id = 1"
    ), "Should detect content mutation"

    # محاولات تعديل official_text_raw
    assert is_official_text_mutation(
        "UPDATE articles SET official_text_raw = 'نص مولد' WHERE id = 1"
    ), "Should detect official_text_raw mutation"

    # استعلامات قراءة عادية — لا يجب كشفها
    assert not is_official_text_mutation(
        "SELECT * FROM articles WHERE id = 1"
    ), "Should not flag SELECT queries"

    assert not is_official_text_mutation(
        "UPDATE articles SET views = views + 1 WHERE id = 1"
    ), "Should not flag views increment"


def test_create_text_with_source():
    """إنشاء نص قانوني من مصدر رسمي."""
    result = OfficialSourceImporter.create_text(
        title="قانون تجريبي — اختبار المصدر",
        articles=[
            {"number": "1", "label": "المادة 1", "content": "تلتزم البائع بتسليم المبيع."},
            {"number": "2", "label": "المادة 2", "content": "يحق للمشتري فسخ العقد."},
        ],
        source_key="adala",
        source_url="https://adala.justice.gov.ma/",
        source_document_url="https://adala.justice.gov.ma/api/test",
        official_ref="TEST-001",
        category_id=1,
    )
    assert result["status"] == "IMPORTED", f"Expected IMPORTED, got {result['status']}"
    assert result["article_count"] == 2
    assert result["content_hash"] is not None

    # التحقق من وجود البصمة في القاعدة
    with db_session() as conn:
        row = conn.execute(
            "SELECT content_hash, source_name, official_source, version_type "
            "FROM legal_texts WHERE id = ?",
            (result["text_id"],),
        ).fetchone()
        assert row is not None, "Text should exist in database"
        assert row["content_hash"] is not None, "Content hash should be set"
        assert row["source_name"] == "وزارة العدل المغربية — عدالة"
        assert row["official_source"] == 1
        assert row["version_type"] == "ORIGINAL_OFFICIAL"

        # التحقق من أن official_text_raw محفوظ في المواد
        articles = conn.execute(
            "SELECT content, official_text_raw, content_hash FROM articles "
            "WHERE legal_text_id = ?",
            (result["text_id"],),
        ).fetchall()
        assert len(articles) == 2
        for art in articles:
            assert art["official_text_raw"] == art["content"], \
                "official_text_raw should equal content on import"
            assert art["content_hash"] is not None, \
                "Article content_hash should be set"

    # تنظيف
    with db_session() as conn:
        conn.execute("DELETE FROM articles WHERE legal_text_id = ?", (result["text_id"],))
        conn.execute("DELETE FROM legal_texts WHERE id = ?", (result["text_id"],))


def test_duplicate_detection():
    """منع تكرار النصوص بنفس البصمة."""
    result1 = OfficialSourceImporter.create_text(
        title="قانون التكرار — الجزء 1",
        articles=[{"number": "1", "label": "المادة 1", "content": "نص موحد للتكرار."}],
        source_key="ansvar",
        category_id=1,
    )
    assert result1["status"] == "IMPORTED"

    # محاولة إدخال نفس النص مرة أخرى
    result2 = OfficialSourceImporter.create_text(
        title="قانون التكرار — الجزء 2",
        articles=[{"number": "1", "label": "المادة 1", "content": "نص موحد للتكرار."}],
        source_key="ansvar",
        category_id=1,
    )
    assert result2["status"] == "DUPLICATE", f"Expected DUPLICATE, got {result2['status']}"
    assert result2["text_id"] == result1["text_id"]

    # تنظيف
    with db_session() as conn:
        conn.execute("DELETE FROM articles WHERE legal_text_id = ?", (result1["text_id"],))
        conn.execute("DELETE FROM legal_texts WHERE id = ?", (result1["text_id"],))


def test_no_ai_source_in_official_texts():
    """التأكد من أن لا يوجد مصدر AI في النصوص الرسمية."""
    with db_session() as conn:
        # البحث عن أي نص يحتوي على علامات AI generation
        ai_patterns = ["generated by", "ai-generated", "ollama", "gemini", "claude", "gpt"]
        for pattern in ai_patterns:
            rows = conn.execute(
                "SELECT id, title FROM legal_texts WHERE "
                "LOWER(source_note) LIKE ? OR LOWER(title) LIKE ?",
                (f"%{pattern}%", f"%{pattern}%"),
            ).fetchall()
            # يجب ألا يوجد نص رسمي مولَّد عبر AI
            for row in rows:
                assert row is not None, f"Found AI-generated text: {row['title']}"


def run_all_tests():
    """تشغيل جميع الاختبارات."""
    tests = [
        test_content_hash_deterministic,
        test_content_hash_differs_for_different_text,
        test_content_hash_empty,
        test_verify_official_text_match,
        test_official_text_mutation_detection,
        test_create_text_with_source,
        test_duplicate_detection,
        test_no_ai_source_in_official_texts,
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  ✓ {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ✗ {test.__name__}: {e}")
            failed += 1
    print(f"\nالنتائج: {passed} نجح / {failed} فشل / {len(tests)} إجمالي")
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
