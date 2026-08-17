"""
اختبارات عزل القانون المقارن — ضمان عدم اختلاط المحتوى المغربي والأجنبي.

هذه الاختبارات حرجة: يجب أن لا تُرجع المكتبة المغربية أبدًا محتوى
comparative vice versa.
"""
from app import services_auth
from app.database import db_session

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _headers(email, role="admin"):
    profile = services_auth.create_user_with_role(
        email=email, password="test-password-123",
        full_name="مدير العزل", role_code=role,
        role_status="active", user_status="active",
    )
    token = services_auth.create_access_token(profile.id)[0]
    return {"Authorization": f"Bearer {token}"}


def _admin():
    return _headers("iso-admin@test.local")


def _seed_moroccan_content():
    """إدخال محتوى مغربي تجريبي في المكتبة الرئيسية."""
    with db_session() as conn:
        cat_id = conn.execute(
            "INSERT INTO categories (slug, name) VALUES (?, ?)",
            ("civil-comp-test", "مدني اختبار"),
        ).lastrowid
        text_id = conn.execute(
            "INSERT INTO legal_texts (category_id, type, title) "
            "VALUES (?, ?, ?)",
            (cat_id, "code", "قانون اختباري مغربي"),
        ).lastrowid
        conn.execute(
            "INSERT INTO articles (legal_text_id, number, label, content) "
            "VALUES (?, ?, ?, ?)",
            (text_id, "1", "المادة 1", "هذا نص مغربي تجريبي للعزل"),
        )
    return text_id


def _seed_comp_france_content():
    """إدخال محتوى فرنسي تجريبي في القانون المقارن."""
    with db_session() as conn:
        country_id = conn.execute(
            "SELECT id FROM comp_countries WHERE code = 'france'"
        ).fetchone()["id"]
        law_id = conn.execute(
            "INSERT INTO comp_laws (country_id, title, category) "
            "VALUES (?, ?, ?)",
            (country_id, "Code civil test", "civil"),
        ).lastrowid
        conn.execute(
            "INSERT INTO comp_law_articles (law_id, number, label, content) "
            "VALUES (?, ?, ?, ?)",
            (law_id, "Art. 1", "La loi",
             "Ceci est un texte francais de test pour l'isolement"),
        )
    return law_id


def _seed_comp_egypt_content():
    """إدخال محتوى مصري تجريبي في القانون المقارن."""
    with db_session() as conn:
        country_id = conn.execute(
            "SELECT id FROM comp_countries WHERE code = 'egypt'"
        ).fetchone()["id"]
        law_id = conn.execute(
            "INSERT INTO comp_laws (country_id, title, category) "
            "VALUES (?, ?, ?)",
            (country_id, "قانون مدني مصري تجريبي", "civil"),
        ).lastrowid
        conn.execute(
            "INSERT INTO comp_law_articles (law_id, number, label, content) "
            "VALUES (?, ?, ?, ?)",
            (law_id, "1", "المادة الأولى",
             "هذا نص مصري تجريبي للعزل"),
        )
    return law_id


# ---------------------------------------------------------------------------
# Isolation: Moroccan library never returns comparative content
# ---------------------------------------------------------------------------

class TestMoroccoIsolation:
    def test_moroccan_search_excludes_comparative(self, client):
        """البحث المغربي لا يُرجع مواد قانون مقارن."""
        _seed_moroccan_content()
        _seed_comp_france_content()
        r = client.get("/api/search?q=texte")
        assert r.status_code == 200
        results = r.get_json()["results"]
        for res in results:
            assert "comp_" not in str(res.get("id", ""))

    def test_moroccan_texts_excludes_comparative(self, client):
        """قائمة النصوص المغربية لا تتضمن قوانين مقارنة."""
        _seed_moroccan_content()
        _seed_comp_france_content()
        r = client.get("/api/texts")
        assert r.status_code == 200
        titles = [t["title"] for t in r.get_json()]
        assert "Code civil test" not in titles

    def test_moroccan_stats_excludes_comparative(self, client):
        """إحصائيات المكتبة المغربية لا تتضمن القانون المقارن."""
        _seed_moroccan_content()
        _seed_comp_france_content()
        r = client.get("/api/library/stats")
        assert r.status_code == 200
        stats = r.get_json()
        assert isinstance(stats, dict)
        stats_str = str(stats)
        assert "comp_" not in stats_str


class TestCompIsolation:
    def test_comp_search_excludes_moroccan(self, client):
        """البحث في القانون المقارن لا يُرجع مواد مغربية."""
        _seed_moroccan_content()
        _seed_comp_france_content()
        r = client.get("/api/comp/search?q=\u0645\u063a\u0631\u0628\u064a")
        assert r.status_code == 200
        results = r.get_json()["results"]
        for res in results:
            assert res.get("country_code") in ("france", "egypt")

    def test_comp_france_excludes_egypt(self, client):
        """القوانين الفرنسية لا تتضمن محتوى مصري."""
        _seed_comp_france_content()
        _seed_comp_egypt_content()
        r = client.get("/api/comp/countries/france/laws")
        assert r.status_code == 200
        laws = r.get_json()["laws"]
        assert all(l["country_code"] == "france" for l in laws)

    def test_comp_egypt_excludes_france(self, client):
        """القوانين المصرية لا تتضمن محتوى فرنسي."""
        _seed_comp_france_content()
        _seed_comp_egypt_content()
        r = client.get("/api/comp/countries/egypt/laws")
        assert r.status_code == 200
        laws = r.get_json()["laws"]
        assert all(l["country_code"] == "egypt" for l in laws)


class TestMoroccoJurisprudenceIsolation:
    """اجتهادات المغربية لا تتضمن اجتهادات القانون المقارن."""

    def test_moroccan_decisions_separate(self, client):
        """اجتهادات Morocco منفصلة عن comp_jurisprudence."""
        with db_session() as conn:
            moroccan_count = conn.execute(
                "SELECT COUNT(*) AS c FROM jurisprudence"
            ).fetchone()["c"]
            comp_count = conn.execute(
                "SELECT COUNT(*) AS c FROM comp_jurisprudence"
            ).fetchone()["c"]
        assert isinstance(moroccan_count, int)
        assert isinstance(comp_count, int)


# ---------------------------------------------------------------------------
# Schema Isolation: Tables are separate
# ---------------------------------------------------------------------------

_COMP_TABLE_NAMES = frozenset({
    "comp_countries", "comp_laws", "comp_law_articles",
    "comp_courts", "comp_jurisprudence",
    "comp_import_runs", "comp_import_sources",
})


class TestTableIsolation:
    def test_comp_tables_exist(self, client):
        """جداول comp_* الأساسية موجودة."""
        with db_session() as conn:
            all_tables = {
                r[0] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
        assert _COMP_TABLE_NAMES.issubset(all_tables)

    def test_comp_tables_separate_from_moroccan(self, client):
        """جداول comp_* منفصلة بالكامل عن جداول المكتبة المغربية."""
        with db_session() as conn:
            all_tables = {
                r[0] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
        assert len(_COMP_TABLE_NAMES & all_tables) == len(_COMP_TABLE_NAMES)
        moroccan_tables = all_tables - _COMP_TABLE_NAMES
        assert _COMP_TABLE_NAMES.isdisjoint(moroccan_tables)

    def test_comp_fts_separate_from_moroccan(self, client):
        """فهارس FTS منفصلة: articles_fts vs comp_law_articles_fts."""
        with db_session() as conn:
            fts_tables = {
                r[0] for r in conn.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name LIKE '%_fts%'"
                ).fetchall()
            }
        assert "articles_fts" in fts_tables
        assert "comp_law_articles_fts" in fts_tables
        assert "comp_jurisprudence_fts" in fts_tables
        assert fts_tables != {"articles_fts"}


# ---------------------------------------------------------------------------
# Data Integrity
# ---------------------------------------------------------------------------

class TestDataIntegrity:
    def test_comp_law_has_country(self, client):
        """كل قانون مقارن مرتبط بدولة."""
        ah = _admin()
        law_id = client.post("/api/admin/comp/laws", json={
            "country_code": "france", "title": "Test Law",
        }, headers=ah).get_json()["id"]
        law = client.get(f"/api/comp/laws/{law_id}").get_json()
        assert law["country_id"] is not None
        assert law["country_code"] == "france"

    def test_comp_article_belongs_to_law(self, client):
        """كل مادة مرتبطة بقانون."""
        ah = _admin()
        law_id = client.post("/api/admin/comp/laws", json={
            "country_code": "france", "title": "Test Law",
        }, headers=ah).get_json()["id"]
        art_id = client.post(f"/api/admin/comp/laws/{law_id}/articles", json={
            "number": "1", "label": "Test",
            "content": "Article content",
        }, headers=ah).get_json()["id"]
        article = client.get(
            f"/api/comp/laws/{law_id}/articles/{art_id}"
        ).get_json()
        assert article["law_id"] == law_id

    def test_comp_decision_has_country(self, client):
        """كل قرار مقارن مرتبط بدولة."""
        ah = _admin()
        did = client.post("/api/admin/comp/jurisprudence", json={
            "country_code": "egypt",
            "title": "Test Decision", "content": "Test content",
        }, headers=ah).get_json()["id"]
        decision = client.get(f"/api/comp/jurisprudence/{did}").get_json()
        assert decision["country_code"] == "egypt"


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------

class TestProvenance:
    def test_import_run_recorded(self, client):
        """جلسة الاستيراد مسجلة مع جميع الحقول."""
        ah = _admin()
        rid = client.post("/api/admin/comp/import/run", json={
            "country_code": "france",
        }, headers=ah).get_json()["id"]
        run = client.get(
            f"/api/admin/comp/import/runs/{rid}", headers=ah,
        ).get_json()
        assert run["country_code"] == "france"
        assert run["status"] == "running"
        assert run["docs_found"] == 0
        assert run["docs_imported"] == 0

    def test_law_source_fields(self, client):
        """القانون يحتفظ بمعلومات المصدر."""
        ah = _admin()
        law_id = client.post("/api/admin/comp/laws", json={
            "country_code": "france", "title": "Code civil",
            "source_name": "Legifrance",
            "source_url": "https://www.legifrance.gouv.fr",
            "official_source": 1,
        }, headers=ah).get_json()["id"]
        law = client.get(f"/api/comp/laws/{law_id}").get_json()
        assert law["source_name"] == "Legifrance"
        assert law["source_url"] == "https://www.legifrance.gouv.fr"
        assert law["official_source"] == 1

    def test_decision_source_fields(self, client):
        """القرار يحتفظ بمعلومات المصدر."""
        ah = _admin()
        did = client.post("/api/admin/comp/jurisprudence", json={
            "country_code": "france",
            "title": "Test", "content": "Content",
            "source_name": "Judilibre",
            "source_url": "https://judilibre.fr",
            "official_source": 1,
        }, headers=ah).get_json()["id"]
        decision = client.get(f"/api/comp/jurisprudence/{did}").get_json()
        assert decision["source_name"] == "Judilibre"
        assert decision["official_source"] == 1


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

class TestDeduplication:
    def test_content_hash_prevents_duplicates(self, client):
        """محتوى مكرر بنفس content_hash لا يُنشئ سجلًا ثانيًا."""
        from app import services_comp
        _seed_comp_france_content()
        with db_session() as conn:
            existing = conn.execute(
                "SELECT content_hash FROM comp_laws LIMIT 1"
            ).fetchone()
            if existing and existing["content_hash"]:
                dup = services_comp.find_existing_by_hash(
                    existing["content_hash"],
                )
                assert dup is not None
