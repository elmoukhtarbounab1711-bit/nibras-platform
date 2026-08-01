"""
اختبارات وحدة لطبقة الخدمة (services.py) للمكتبة القانونية.

تُختبر دوال الخدمة مباشرة دون مسار HTTP، حسب Testing Strategy (§2):
مجموعة اختبار لكل ملف services_* بحدود دواله.
"""
from app import services


def _text_id_by_title(title):
    for t in services.list_texts():
        if t["title"] == title:
            return t["id"]
    raise AssertionError(f"النص '{title}' غير موجود في بيانات الاختبار")


def test_list_categories_sorted_by_name(fresh_db):
    cats = services.list_categories()
    names = [c["name"] for c in cats]
    assert names == sorted(names)


def test_list_texts_returns_metadata_with_counts(fresh_db):
    texts = services.list_texts()
    by_title = {t["title"]: t for t in texts}
    assert set(by_title) == {"قانون الالتزامات والعقود", "مدونة الأسرة"}
    for t in texts:
        assert t["article_count"] >= 1
        assert t["category_name"]


def test_list_texts_filter_by_category_slug(fresh_db):
    texts = services.list_texts(category_slug="usra")
    assert len(texts) == 1
    assert texts[0]["category_slug"] == "usra"
    assert texts[0]["title"] == "مدونة الأسرة"


def test_list_texts_filter_by_type(fresh_db):
    texts = services.list_texts(text_type="constitution")
    assert texts == []

    texts = services.list_texts(text_type="code")
    assert len(texts) == 2


def test_get_text_returns_article_summaries_only(fresh_db):
    tid = _text_id_by_title("قانون الالتزامات والعقود")
    text = services.get_text(tid)
    assert text["title"] == "قانون الالتزامات والعقود"
    assert len(text["articles"]) == 1
    assert set(text["articles"][0].keys()) == {"id", "number", "label"}


def test_get_text_missing_returns_none(fresh_db):
    assert services.get_text(99999) is None


def test_get_article_with_related(fresh_db):
    tid = _text_id_by_title("قانون الالتزامات والعقود")
    aid = services.get_text(tid)["articles"][0]["id"]
    article = services.get_article(aid)
    assert article["label"] == "المادة 230"
    assert article["plain_explanation"] == "مبدأ العقد شريعة المتعاقدين."
    assert len(article["related_articles"]) == 1
    assert article["related_articles"][0]["label"] == "المادة 49"


def test_get_article_missing_returns_none(fresh_db):
    assert services.get_article(99999) is None


def test_search_articles_empty_query_returns_empty(fresh_db):
    assert services.search_articles("") == []
    assert services.search_articles("   ") == []


def test_search_articles_matches_content_and_keywords(fresh_db):
    results = services.search_articles("عقد")
    assert len(results) >= 1
    assert results[0]["label"] == "المادة 230"
    assert results[0]["legal_text_title"] == "قانون الالتزامات والعقود"


def test_search_articles_respects_limit(fresh_db):
    results = services.search_articles("عقد", limit=1)
    assert len(results) == 1


def test_search_articles_fts_failure_falls_back_gracefully(fresh_db):
    # استعلام يكسر صياغة FTS5 (اقتباس غير مغلق) فيُستخدم البحث LIKE دون خطأ
    results = services.search_articles('"عقد')
    assert isinstance(results, list)


def test_production_seed_loads_and_searches(fresh_db):
    from app import seed

    seed.seed(reset=True)
    assert len(services.list_categories()) == 6
    texts = services.list_texts()
    assert len(texts) == 5
    assert all(t["is_sample_data"] == 1 for t in texts)
    assert len(services.search_articles("تمييز")) >= 1
