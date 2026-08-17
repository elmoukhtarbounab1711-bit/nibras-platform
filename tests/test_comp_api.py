"""
اختبارات API القانون المقارن المستقل — دول + قوانين + اجتهادات + بحث.

تختبر جميع نقاط النهاية العامة والإدارية مع ضمان العزل الكامل
عن المكتبة المغربية.
"""
from app import services_auth

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _headers(email, role="admin"):
    profile = services_auth.create_user_with_role(
        email=email, password="test-password-123",
        full_name="مدير المقارن", role_code=role,
        role_status="active", user_status="active",
    )
    token = services_auth.create_access_token(profile.id)[0]
    return {"Authorization": f"Bearer {token}"}


def _admin():
    return _headers("comp-admin@test.local")


# ---------------------------------------------------------------------------
# Countries
# ---------------------------------------------------------------------------

class TestCountries:
    def test_list_countries(self, client):
        r = client.get("/api/comp/countries")
        assert r.status_code == 200
        data = r.get_json()
        assert "countries" in data
        codes = [c["code"] for c in data["countries"]]
        assert "france" in codes
        assert "egypt" in codes

    def test_country_detail_france(self, client):
        r = client.get("/api/comp/countries/france")
        assert r.status_code == 200
        data = r.get_json()
        assert data["code"] == "france"
        assert data["flag_emoji"] == "\U0001f1eb\U0001f1f7"
        assert "law_count" in data
        assert "court_count" in data

    def test_country_not_found(self, client):
        r = client.get("/api/comp/countries/nonexistent")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Laws (Admin CRUD)
# ---------------------------------------------------------------------------

class TestLawsCRUD:
    def test_admin_create_law(self, client):
        ah = _admin()
        r = client.post("/api/admin/comp/laws", json={
            "country_code": "france",
            "title": "Code civil",
            "category": "civil",
            "official_source": 1,
        }, headers=ah)
        assert r.status_code == 201
        assert "id" in r.get_json()

    def test_admin_create_law_missing_fields(self, client):
        ah = _admin()
        r = client.post("/api/admin/comp/laws", json={
            "country_code": "france",
        }, headers=ah)
        assert r.status_code == 400

    def test_admin_create_law_unknown_country(self, client):
        ah = _admin()
        r = client.post("/api/admin/comp/laws", json={
            "country_code": "nonexistent", "title": "Test",
        }, headers=ah)
        assert r.status_code == 404

    def test_public_cannot_create_law(self, client):
        r = client.post("/api/admin/comp/laws", json={
            "country_code": "france", "title": "Test",
        })
        assert r.status_code in (401, 403)

    def test_list_laws_for_country(self, client):
        ah = _admin()
        client.post("/api/admin/comp/laws", json={
            "country_code": "france",
            "title": "Code civil",
            "category": "civil",
        }, headers=ah)
        r = client.get("/api/comp/countries/france/laws")
        assert r.status_code == 200
        laws = r.get_json()["laws"]
        assert len(laws) >= 1
        assert laws[0]["country_code"] == "france"

    def test_list_laws_filter_by_category(self, client):
        ah = _admin()
        client.post("/api/admin/comp/laws", json={
            "country_code": "france", "title": "Code civil",
            "category": "civil",
        }, headers=ah)
        client.post("/api/admin/comp/laws", json={
            "country_code": "france", "title": "Code penal",
            "category": "criminal",
        }, headers=ah)
        r = client.get("/api/comp/countries/france/laws?category=civil")
        assert r.status_code == 200
        laws = r.get_json()["laws"]
        assert all(l["category"] == "civil" for l in laws)

    def test_law_detail(self, client):
        ah = _admin()
        cid = client.post("/api/admin/comp/laws", json={
            "country_code": "france", "title": "Code civil",
        }, headers=ah).get_json()["id"]
        r = client.get(f"/api/comp/laws/{cid}")
        assert r.status_code == 200
        assert r.get_json()["title"] == "Code civil"

    def test_law_not_found(self, client):
        r = client.get("/api/comp/laws/99999")
        assert r.status_code == 404

    def test_admin_update_law(self, client):
        ah = _admin()
        cid = client.post("/api/admin/comp/laws", json={
            "country_code": "france", "title": "Old Title",
        }, headers=ah).get_json()["id"]
        r = client.put(f"/api/admin/comp/laws/{cid}", json={
            "title": "New Title",
        }, headers=ah)
        assert r.status_code == 200
        detail = client.get(f"/api/comp/laws/{cid}").get_json()
        assert detail["title"] == "New Title"

    def test_admin_delete_law(self, client):
        ah = _admin()
        cid = client.post("/api/admin/comp/laws", json={
            "country_code": "france", "title": "To Delete",
        }, headers=ah).get_json()["id"]
        r = client.delete(f"/api/admin/comp/laws/{cid}", headers=ah)
        assert r.status_code == 200
        assert client.get(f"/api/comp/laws/{cid}").status_code == 404


# ---------------------------------------------------------------------------
# Articles (Admin CRUD)
# ---------------------------------------------------------------------------

class TestArticlesCRUD:
    def _create_law(self, client, ah):
        return client.post("/api/admin/comp/laws", json={
            "country_code": "france", "title": "Code civil",
        }, headers=ah).get_json()["id"]

    def test_admin_create_article(self, client):
        ah = _admin()
        law_id = self._create_law(client, ah)
        r = client.post(f"/api/admin/comp/laws/{law_id}/articles", json={
            "number": "Art. 1",
            "label": "La loi",
            "content": "Les lois et les actes administratifs entrent en "
                       "vigueur a la date qu'ils fixent.",
        }, headers=ah)
        assert r.status_code == 201

    def test_article_missing_fields(self, client):
        ah = _admin()
        law_id = self._create_law(client, ah)
        r = client.post(f"/api/admin/comp/laws/{law_id}/articles", json={
            "number": "Art. 1",
        }, headers=ah)
        assert r.status_code == 400

    def test_article_detail(self, client):
        ah = _admin()
        law_id = self._create_law(client, ah)
        art_id = client.post(f"/api/admin/comp/laws/{law_id}/articles", json={
            "number": "Art. 1", "label": "La loi",
            "content": "Les lois entrent en vigueur a la date qu'elles fixent.",
        }, headers=ah).get_json()["id"]
        r = client.get(f"/api/comp/laws/{law_id}/articles/{art_id}")
        assert r.status_code == 200
        assert r.get_json()["content"].startswith("Les lois")

    def test_article_not_found(self, client):
        r = client.get("/api/comp/laws/1/articles/99999")
        assert r.status_code == 404

    def test_admin_update_article(self, client):
        ah = _admin()
        law_id = self._create_law(client, ah)
        art_id = client.post(f"/api/admin/comp/laws/{law_id}/articles", json={
            "number": "Art. 1", "label": "La loi",
            "content": "Old content",
        }, headers=ah).get_json()["id"]
        client.put(f"/api/admin/comp/articles/{art_id}", json={
            "content": "New content",
        }, headers=ah)
        r = client.get(f"/api/comp/laws/{law_id}/articles/{art_id}")
        assert r.get_json()["content"] == "New content"

    def test_admin_delete_article(self, client):
        ah = _admin()
        law_id = self._create_law(client, ah)
        art_id = client.post(f"/api/admin/comp/laws/{law_id}/articles", json={
            "number": "Art. 1", "label": "La loi",
            "content": "To delete",
        }, headers=ah).get_json()["id"]
        client.delete(f"/api/admin/comp/articles/{art_id}", headers=ah)
        r = client.get(f"/api/comp/laws/{law_id}/articles/{art_id}")
        assert r.status_code == 404

    def test_admin_list_law_articles(self, client):
        ah = _admin()
        law_id = self._create_law(client, ah)
        client.post(f"/api/admin/comp/laws/{law_id}/articles", json={
            "number": "Art. 1", "label": "La loi",
            "content": "Content 1",
        }, headers=ah)
        client.post(f"/api/admin/comp/laws/{law_id}/articles", json={
            "number": "Art. 2", "label": "La coutume",
            "content": "Content 2",
        }, headers=ah)
        r = client.get(f"/api/admin/comp/laws/{law_id}/articles",
                       headers=ah)
        assert r.status_code == 200
        assert len(r.get_json()["articles"]) == 2


# ---------------------------------------------------------------------------
# Courts (Admin CRUD)
# ---------------------------------------------------------------------------

class TestCourtsCRUD:
    def test_admin_create_court(self, client):
        ah = _admin()
        r = client.post("/api/admin/comp/courts", json={
            "country_code": "france",
            "name": "Cour de cassation",
            "slug": "cour-de-cassation",
            "name_ar": "\u0645\u062d\u0643\u0645\u0629 \u0627\u0644\u0646\u0642\u0636",
        }, headers=ah)
        assert r.status_code == 201

    def test_court_missing_fields(self, client):
        ah = _admin()
        r = client.post("/api/admin/comp/courts", json={
            "country_code": "france",
        }, headers=ah)
        assert r.status_code == 400

    def test_list_courts(self, client):
        ah = _admin()
        client.post("/api/admin/comp/courts", json={
            "country_code": "france",
            "name": "Cour de cassation",
            "slug": "cour-de-cassation",
        }, headers=ah)
        r = client.get("/api/comp/countries/france/courts")
        assert r.status_code == 200
        courts = r.get_json()["courts"]
        assert len(courts) >= 1

    def test_admin_update_court(self, client):
        ah = _admin()
        cid = client.post("/api/admin/comp/courts", json={
            "country_code": "france",
            "name": "Old Name", "slug": "old-slug",
        }, headers=ah).get_json()["id"]
        client.put(f"/api/admin/comp/courts/{cid}", json={
            "name": "New Name",
        }, headers=ah)
        r = client.get("/api/comp/countries/france/courts")
        names = [c["name"] for c in r.get_json()["courts"]]
        assert "New Name" in names

    def test_admin_delete_court(self, client):
        ah = _admin()
        cid = client.post("/api/admin/comp/courts", json={
            "country_code": "france",
            "name": "To Delete", "slug": "to-delete",
        }, headers=ah).get_json()["id"]
        client.delete(f"/api/admin/comp/courts/{cid}", headers=ah)
        r = client.get("/api/comp/countries/france/courts")
        slugs = [c["slug"] for c in r.get_json()["courts"]]
        assert "to-delete" not in slugs


# ---------------------------------------------------------------------------
# Jurisprudence (Admin CRUD)
# ---------------------------------------------------------------------------

class TestJurisprudenceCRUD:
    def test_admin_create_decision(self, client):
        ah = _admin()
        r = client.post("/api/admin/comp/jurisprudence", json={
            "country_code": "france",
            "title": "Cass. civ. 1ere, 2024-01-15, n 23-12.345",
            "content": "La cour casse l'arret attaque.",
            "decision_number": "23-12.345",
            "decision_date": "2024-01-15",
        }, headers=ah)
        assert r.status_code == 201

    def test_decision_missing_fields(self, client):
        ah = _admin()
        r = client.post("/api/admin/comp/jurisprudence", json={
            "country_code": "france",
        }, headers=ah)
        assert r.status_code == 400

    def test_decision_detail(self, client):
        ah = _admin()
        did = client.post("/api/admin/comp/jurisprudence", json={
            "country_code": "france",
            "title": "Test Decision",
            "content": "Content of decision",
        }, headers=ah).get_json()["id"]
        r = client.get(f"/api/comp/jurisprudence/{did}")
        assert r.status_code == 200
        assert r.get_json()["country_code"] == "france"

    def test_list_jurisprudence(self, client):
        ah = _admin()
        client.post("/api/admin/comp/jurisprudence", json={
            "country_code": "france",
            "title": "Decision 1", "content": "Content 1",
        }, headers=ah)
        r = client.get("/api/comp/countries/france/jurisprudence")
        assert r.status_code == 200
        assert len(r.get_json()["decisions"]) >= 1

    def test_admin_update_decision(self, client):
        ah = _admin()
        did = client.post("/api/admin/comp/jurisprudence", json={
            "country_code": "france",
            "title": "Old Title", "content": "Old",
        }, headers=ah).get_json()["id"]
        client.put(f"/api/admin/comp/jurisprudence/{did}", json={
            "title": "New Title",
        }, headers=ah)
        r = client.get(f"/api/comp/jurisprudence/{did}")
        assert r.get_json()["title"] == "New Title"

    def test_admin_delete_decision(self, client):
        ah = _admin()
        did = client.post("/api/admin/comp/jurisprudence", json={
            "country_code": "france",
            "title": "To Delete", "content": "Del",
        }, headers=ah).get_json()["id"]
        client.delete(f"/api/admin/comp/jurisprudence/{did}", headers=ah)
        r = client.get(f"/api/comp/jurisprudence/{did}")
        assert r.status_code == 404

    def test_decision_not_found(self, client):
        r = client.get("/api/comp/jurisprudence/99999")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

class TestCompSearch:
    def _seed_france_law(self, client):
        ah = _admin()
        law_id = client.post("/api/admin/comp/laws", json={
            "country_code": "france", "title": "Code civil",
            "category": "civil",
        }, headers=ah).get_json()["id"]
        client.post(f"/api/admin/comp/laws/{law_id}/articles", json={
            "number": "Art. 1", "label": "La loi",
            "content": "Les lois et les actes administratifs entrent en "
                       "vigueur a la date qu'ils fixent.",
            "keywords": "loi, vigueur, entree",
        }, headers=ah)
        return law_id

    def test_search_missing_q(self, client):
        r = client.get("/api/comp/search")
        assert r.status_code == 400

    def test_search_finds_french_law(self, client):
        self._seed_france_law(client)
        r = client.get("/api/comp/search?q=vigueur")
        assert r.status_code == 200
        data = r.get_json()
        assert data["count"] >= 1
        assert data["results"][0]["result_type"] == "law"

    def test_search_country_filter(self, client):
        self._seed_france_law(client)
        r = client.get("/api/comp/search?q=vigueur&country=egypt")
        assert r.status_code == 200
        assert r.get_json()["count"] == 0

    def test_search_type_filter(self, client):
        self._seed_france_law(client)
        r = client.get("/api/comp/search?q=vigueur&type=jurisprudence")
        assert r.status_code == 200
        assert r.get_json()["count"] == 0


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

class TestCompStats:
    def test_stats(self, client):
        r = client.get("/api/comp/stats")
        assert r.status_code == 200
        data = r.get_json()
        assert "countries" in data
        assert "laws" in data
        assert "articles" in data
        assert "courts" in data
        assert "decisions" in data


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

class TestCountryCategories:
    def test_country_categories(self, client):
        ah = _admin()
        client.post("/api/admin/comp/laws", json={
            "country_code": "france", "title": "Code civil",
            "category": "civil",
        }, headers=ah)
        r = client.get("/api/comp/countries/france/categories")
        assert r.status_code == 200
        cats = r.get_json()["categories"]
        assert any(c["category"] == "civil" for c in cats)

    def test_country_categories_unknown(self, client):
        r = client.get("/api/comp/countries/nonexistent/categories")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Import Runs
# ---------------------------------------------------------------------------

class TestImportRuns:
    def test_trigger_import(self, client):
        ah = _admin()
        r = client.post("/api/admin/comp/import/run", json={
            "country_code": "france",
        }, headers=ah)
        assert r.status_code == 201
        assert r.get_json()["status"] == "running"

    def test_import_missing_country(self, client):
        ah = _admin()
        r = client.post("/api/admin/comp/import/run", json={}, headers=ah)
        assert r.status_code == 400

    def test_import_unknown_country(self, client):
        ah = _admin()
        r = client.post("/api/admin/comp/import/run", json={
            "country_code": "nonexistent",
        }, headers=ah)
        assert r.status_code == 404

    def test_list_import_runs(self, client):
        ah = _admin()
        client.post("/api/admin/comp/import/run", json={
            "country_code": "france",
        }, headers=ah)
        r = client.get("/api/admin/comp/import/runs", headers=ah)
        assert r.status_code == 200
        assert len(r.get_json()["runs"]) >= 1

    def test_import_run_detail(self, client):
        ah = _admin()
        rid = client.post("/api/admin/comp/import/run", json={
            "country_code": "france",
        }, headers=ah).get_json()["id"]
        r = client.get(f"/api/admin/comp/import/runs/{rid}", headers=ah)
        assert r.status_code == 200
        assert r.get_json()["country_code"] == "france"

    def test_import_run_not_found(self, client):
        ah = _admin()
        r = client.get("/api/admin/comp/import/runs/99999", headers=ah)
        assert r.status_code == 404

    def test_public_cannot_trigger_import(self, client):
        r = client.post("/api/admin/comp/import/run", json={
            "country_code": "france",
        })
        assert r.status_code in (401, 403)
