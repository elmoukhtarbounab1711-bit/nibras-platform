"""
خدمات القانون المقارن المستقل — دول + قوانين + اجتهادات + استيراد.

وحدة منفصلة بالكامل عن المكتبة المغربية: جداول مستقلة (comp_*),
بحث FTS5 مستقل (comp_*_fts)، وعزل صارم على مستوى قاعدة البيانات.
"""
import hashlib

from . import tenant_scope
from .database import db_session

# بيانات بذور الدول — معلومة رسمية فقط (لا قوانين مولدة)
COUNTRY_SEED = (
    ("france", "فرنسا", "فرنسا", "🇫🇷", "fr"),
    ("egypt", "مصر", "مصر", "🇪🇬", "ar"),
)

# فئات القوانين المسبقة (مُعادل أسماء الأكواد الفرنسية والمصرية)
LAW_CATEGORIES = (
    "civil",
    "criminal",
    "commercial",
    "administrative",
    "labor",
    "constitutional",
    "family",
    "other",
)

# مصادر الاستيراد الأولية (public government sources)
IMPORT_SOURCES_SEED = (
    ("Légifrance (PISTE API)", "france", "api",
     "https://api.piste.gouv.fr/dila/legifrance/lf-engine-app", True),
    ("Légifrance XML Open Data", "france", "xml_bulk",
     "https://echanges.dila.gouv.fr/OPENDATA/", True),
    ("Cour de cassation (Judilibre)", "france", "api",
     "https://api.piste.gouv.fr/cassation/judilibre/v1.0", True),
    ("Conseil d'État Open Data", "france", "xml_bulk",
     "https://opendata.justice-administrative.fr", True),
    ("الجريدة الرسمية المصرية", "egypt", "manual",
     "http://www.alamiria.com/", True),
    ("البوابة القانونية (IDSC)", "egypt", "manual",
     "https://elpai.idsc.gov.eg", True),
)


class CompError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


# ---------------------------------------------------------------------------
# ensure_defaults — بذور الدول والمصادر (idempotent)
# ---------------------------------------------------------------------------

def ensure_defaults():
    """بذر الدول والمصادر إن كانت فارغة (idempotent)."""
    with db_session() as conn:
        count = conn.execute(
            "SELECT COUNT(*) AS c FROM comp_countries"
        ).fetchone()["c"]
        if count == 0:
            for code, name, name_ar, flag, lang in COUNTRY_SEED:
                conn.execute(
                    "INSERT INTO comp_countries "
                    "(code, name, name_ar, flag_emoji, language, tenant_id) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (code, name, name_ar, flag, lang,
                     tenant_scope.insert_tenant_id()),
                )
        src_count = conn.execute(
            "SELECT COUNT(*) AS c FROM comp_import_sources"
        ).fetchone()["c"]
        if src_count == 0:
            for name, country, stype, url, official in IMPORT_SOURCES_SEED:
                conn.execute(
                    "INSERT INTO comp_import_sources "
                    "(name, country_code, source_type, url, official, "
                    " access_method, tenant_id) "
                    "VALUES (?, ?, ?, ?, ?, 'api', ?)",
                    (name, country, stype, url, int(official),
                     tenant_scope.insert_tenant_id()),
                )


# ---------------------------------------------------------------------------
# Countries
# ---------------------------------------------------------------------------

def list_countries():
    with db_session() as conn:
        q = "SELECT * FROM comp_countries ORDER BY name"
        params = []
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            q = q.replace("ORDER BY", "WHERE " + cond + " ORDER BY")
            params.extend(vals)
        return [dict(r) for r in conn.execute(q, params).fetchall()]


def get_country(code: str):
    with db_session() as conn:
        q = "SELECT * FROM comp_countries WHERE code = ?"
        params = [code]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            q += " AND " + cond
            params.extend(vals)
        row = conn.execute(q, params).fetchone()
        if not row:
            return None
        country = dict(row)
        country["law_count"] = conn.execute(
            "SELECT COUNT(*) AS c FROM comp_laws WHERE country_id = ?",
            (country["id"],),
        ).fetchone()["c"]
        country["court_count"] = conn.execute(
            "SELECT COUNT(*) AS c FROM comp_courts WHERE country_id = ?",
            (country["id"],),
        ).fetchone()["c"]
        country["decision_count"] = conn.execute(
            "SELECT COUNT(*) AS c FROM comp_jurisprudence "
            "WHERE country_id = ?",
            (country["id"],),
        ).fetchone()["c"]
        return country


# ---------------------------------------------------------------------------
# Laws
# ---------------------------------------------------------------------------

def _content_hash(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def list_laws(country_id: int, category: str | None = None):
    with db_session() as conn:
        q = ("SELECT l.*, c.name AS country_name, c.code AS country_code "
             "FROM comp_laws l JOIN comp_countries c ON c.id = l.country_id "
             "WHERE l.country_id = ?")
        params = [country_id]
        if category:
            q += " AND l.category = ?"
            params.append(category)
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            q += " AND " + cond
            params.extend(vals)
        q += " ORDER BY l.title"
        return [dict(r) for r in conn.execute(q, params).fetchall()]


def get_law(law_id: int):
    with db_session() as conn:
        q = ("SELECT l.*, c.name AS country_name, c.code AS country_code "
             "FROM comp_laws l JOIN comp_countries c ON c.id = l.country_id "
             "WHERE l.id = ?")
        params = [law_id]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            q += " AND " + cond
            params.extend(vals)
        row = conn.execute(q, params).fetchone()
        if not row:
            return None
        law = dict(row)
        law["articles"] = [dict(r) for r in conn.execute(
            "SELECT * FROM comp_law_articles WHERE law_id = ? ORDER BY number",
            (law_id,),
        ).fetchall()]
        return law


def create_law(country_id: int, title: str, category: str = "general",
               **kwargs):
    content = kwargs.get("content", "")
    with db_session() as conn:
        cur = conn.execute(
            "INSERT INTO comp_laws "
            "(country_id, category, title, title_original, official_ref, "
            " language, enacted_date, published_date, source_name, source_url, "
            " official_source, content_hash, content, tenant_id) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                country_id, category, title,
                kwargs.get("title_original"),
                kwargs.get("official_ref"),
                kwargs.get("language", "fr"),
                kwargs.get("enacted_date"),
                kwargs.get("published_date"),
                kwargs.get("source_name"),
                kwargs.get("source_url"),
                int(kwargs.get("official_source", 0)),
                _content_hash(content) if content else None,
                content,
                tenant_scope.insert_tenant_id(),
            ),
        )
        return cur.lastrowid


def update_law(law_id: int, **kwargs):
    fields, vals = [], []
    allowed = (
        "title", "title_original", "category", "official_ref", "language",
        "enacted_date", "published_date", "source_name", "source_url",
        "official_source", "content",
    )
    for key in allowed:
        if key in kwargs:
            fields.append(f"{key} = ?")
            vals.append(kwargs[key])
    if "content" in kwargs:
        fields.append("content_hash = ?")
        vals.append(_content_hash(kwargs["content"] or ""))
    fields.append("updated_at = datetime('now')")
    vals.append(law_id)
    if not fields:
        return
    with db_session() as conn:
        conn.execute(
            f"UPDATE comp_laws SET {', '.join(fields)} WHERE id = ?",
            vals,
        )


def delete_law(law_id: int):
    with db_session() as conn:
        conn.execute("DELETE FROM comp_laws WHERE id = ?", (law_id,))


# ---------------------------------------------------------------------------
# Law Articles
# ---------------------------------------------------------------------------

def list_law_articles(law_id: int):
    with db_session() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM comp_law_articles WHERE law_id = ? ORDER BY number",
            (law_id,),
        ).fetchall()]


def get_law_article(article_id: int):
    with db_session() as conn:
        row = conn.execute(
            "SELECT a.*, l.title AS law_title, l.country_id, "
            "c.code AS country_code "
            "FROM comp_law_articles a "
            "JOIN comp_laws l ON l.id = a.law_id "
            "JOIN comp_countries c ON c.id = l.country_id "
            "WHERE a.id = ?",
            (article_id,),
        ).fetchone()
        return dict(row) if row else None


def create_law_article(law_id: int, number: str, label: str,
                       content: str, keywords: str | None = None):
    with db_session() as conn:
        cur = conn.execute(
            "INSERT INTO comp_law_articles "
            "(law_id, number, label, content, keywords, tenant_id) "
            "VALUES (?,?,?,?,?,?)",
            (law_id, number, label, content, keywords,
             tenant_scope.insert_tenant_id()),
        )
        return cur.lastrowid


def update_law_article(article_id: int, **kwargs):
    fields, vals = [], []
    for key in ("number", "label", "content", "keywords"):
        if key in kwargs:
            fields.append(f"{key} = ?")
            vals.append(kwargs[key])
    vals.append(article_id)
    if not fields:
        return
    with db_session() as conn:
        conn.execute(
            f"UPDATE comp_law_articles SET {', '.join(fields)} WHERE id = ?",
            vals,
        )


def delete_law_article(article_id: int):
    with db_session() as conn:
        conn.execute(
            "DELETE FROM comp_law_articles WHERE id = ?", (article_id,),
        )


# ---------------------------------------------------------------------------
# Courts
# ---------------------------------------------------------------------------

def list_courts(country_id: int):
    with db_session() as conn:
        q = ("SELECT * FROM comp_courts WHERE country_id = ? "
             "ORDER BY name")
        params = [country_id]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            q = q.replace("ORDER BY", "WHERE country_id = ? AND " + cond +
                          " ORDER BY")
            params = [country_id] + vals
        return [dict(r) for r in conn.execute(q, params).fetchall()]


def get_court(court_id: int):
    with db_session() as conn:
        q = "SELECT * FROM comp_courts WHERE id = ?"
        params = [court_id]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            q += " AND " + cond
            params.extend(vals)
        row = conn.execute(q, params).fetchone()
        return dict(row) if row else None


def get_court_by_slug(country_id: int, slug: str):
    with db_session() as conn:
        q = "SELECT * FROM comp_courts WHERE country_id = ? AND slug = ?"
        params = [country_id, slug]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            q += " AND " + cond
            params.extend(vals)
        row = conn.execute(q, params).fetchone()
        return dict(row) if row else None


def create_court(country_id: int, name: str, slug: str,
                 name_ar: str | None = None, description: str | None = None):
    with db_session() as conn:
        cur = conn.execute(
            "INSERT INTO comp_courts "
            "(country_id, name, slug, name_ar, description, tenant_id) "
            "VALUES (?,?,?,?,?,?)",
            (country_id, name, slug, name_ar, description,
             tenant_scope.insert_tenant_id()),
        )
        return cur.lastrowid


def update_court(court_id: int, **kwargs):
    fields, vals = [], []
    for key in ("name", "slug", "name_ar", "description"):
        if key in kwargs:
            fields.append(f"{key} = ?")
            vals.append(kwargs[key])
    vals.append(court_id)
    if not fields:
        return
    with db_session() as conn:
        conn.execute(
            f"UPDATE comp_courts SET {', '.join(fields)} WHERE id = ?",
            vals,
        )


def delete_court(court_id: int):
    with db_session() as conn:
        conn.execute("DELETE FROM comp_courts WHERE id = ?", (court_id,))


# ---------------------------------------------------------------------------
# Jurisprudence (Foreign Court Decisions)
# ---------------------------------------------------------------------------

def list_jurisprudence(country_id: int, court_id: int | None = None):
    with db_session() as conn:
        q = ("SELECT j.*, c.name AS court_name "
             "FROM comp_jurisprudence j "
             "LEFT JOIN comp_courts c ON c.id = j.court_id "
             "WHERE j.country_id = ? AND j.published = 1")
        params = [country_id]
        if court_id:
            q += " AND j.court_id = ?"
            params.append(court_id)
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            q += " AND " + cond
            params.extend(vals)
        q += " ORDER BY j.decision_date DESC"
        return [dict(r) for r in conn.execute(q, params).fetchall()]


def get_decision(decision_id: int):
    with db_session() as conn:
        q = ("SELECT j.*, c.name AS court_name, co.name AS country_name, "
             "co.code AS country_code "
             "FROM comp_jurisprudence j "
             "LEFT JOIN comp_courts c ON c.id = j.court_id "
             "JOIN comp_countries co ON co.id = j.country_id "
             "WHERE j.id = ?")
        params = [decision_id]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            q += " AND " + cond
            params.extend(vals)
        row = conn.execute(q, params).fetchone()
        return dict(row) if row else None


def create_decision(country_id: int, title: str, content: str,
                    court_id: int | None = None, **kwargs):
    content_hash = _content_hash(content)
    with db_session() as conn:
        cur = conn.execute(
            "INSERT INTO comp_jurisprudence "
            "(country_id, court_id, title, content, decision_number, "
            " decision_date, decision_type, keywords, source_name, "
            " source_url, official_source, content_hash, tenant_id) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                country_id, court_id, title, content,
                kwargs.get("decision_number"),
                kwargs.get("decision_date"),
                kwargs.get("decision_type"),
                kwargs.get("keywords"),
                kwargs.get("source_name"),
                kwargs.get("source_url"),
                int(kwargs.get("official_source", 0)),
                content_hash,
                tenant_scope.insert_tenant_id(),
            ),
        )
        return cur.lastrowid


def update_decision(decision_id: int, **kwargs):
    fields, vals = [], []
    allowed = (
        "title", "content", "court_id", "decision_number", "decision_date",
        "decision_type", "keywords", "source_name", "source_url",
        "official_source", "published",
    )
    for key in allowed:
        if key in kwargs:
            fields.append(f"{key} = ?")
            vals.append(kwargs[key])
    if "content" in kwargs:
        fields.append("content_hash = ?")
        vals.append(_content_hash(kwargs["content"] or ""))
    fields.append("updated_at = datetime('now')")
    vals.append(decision_id)
    if not fields:
        return
    with db_session() as conn:
        conn.execute(
            "UPDATE comp_jurisprudence SET " + ", ".join(fields) +
            " WHERE id = ?",
            vals,
        )


def delete_decision(decision_id: int):
    with db_session() as conn:
        conn.execute(
            "DELETE FROM comp_jurisprudence WHERE id = ?", (decision_id,),
        )


# ---------------------------------------------------------------------------
# Search (FTS5)
# ---------------------------------------------------------------------------

def search_comp(query: str, country_code: str | None = None,
                doc_type: str | None = None, limit: int = 50):
    """بحث في القانون المقارن (مواد + اجتهادات) عبر FTS5."""
    from .arabic_text import (
        build_fts_query,
        build_search_terms,
        normalize_arabic,
    )
    norm = normalize_arabic(query)
    terms = build_search_terms(norm)
    if not terms:
        return []
    fts_query = build_fts_query(terms)
    results = []
    with db_session() as conn:
        # بحث في مواد القوانين
        if doc_type in (None, "law"):
            law_q = (
                "SELECT a.id, a.label, a.content, a.keywords, "
                "       l.title AS law_title, l.category, "
                "       c.code AS country_code, c.name AS country_name, "
                "       'law' AS result_type "
                "FROM comp_law_articles_fts fts "
                "JOIN comp_law_articles a ON a.id = fts.rowid "
                "JOIN comp_laws l ON l.id = a.law_id "
                "JOIN comp_countries c ON c.id = l.country_id "
                "WHERE comp_law_articles_fts MATCH ? "
            )
            law_params = [fts_query]
            if country_code:
                law_q += "AND c.code = ? "
                law_params.append(country_code)
            law_q += " ORDER BY bm25(comp_law_articles_fts) LIMIT ?"
            law_params.append(limit)
            for r in conn.execute(law_q, law_params).fetchall():
                d = dict(r)
                d["snippet"] = _snippet(d["content"], norm)
                results.append(d)

        # بحث في الاجتهادات
        if doc_type in (None, "jurisprudence"):
            jur_q = (
                "SELECT j.id, j.title, j.content, j.keywords, "
                "       j.decision_number, j.decision_date, "
                "       ct.name AS court_name, "
                "       c.code AS country_code, c.name AS country_name, "
                "       'jurisprudence' AS result_type "
                "FROM comp_jurisprudence_fts fts "
                "JOIN comp_jurisprudence j ON j.id = fts.rowid "
                "JOIN comp_countries c ON c.id = j.country_id "
                "LEFT JOIN comp_courts ct ON ct.id = j.court_id "
                "WHERE comp_jurisprudence_fts MATCH ? "
                "AND j.published = 1 "
            )
            jur_params = [fts_query]
            if country_code:
                jur_q += "AND c.code = ? "
                jur_params.append(country_code)
            jur_q += " ORDER BY bm25(comp_jurisprudence_fts) LIMIT ?"
            jur_params.append(limit)
            for r in conn.execute(jur_q, jur_params).fetchall():
                d = dict(r)
                d["snippet"] = _snippet(d["content"], norm)
                results.append(d)

    results.sort(key=lambda x: x.get("snippet", ""), reverse=True)
    return results[:limit]


def _snippet(content: str, query_norm: str, ctx: int = 200) -> str:
    """استخراج مقتطف من المحتوى حول أول ظهور لكلمة من الاستعلام."""
    if not content:
        return ""
    words = [w for w in query_norm.split() if len(w) > 1]
    best_pos = -1
    for w in words:
        pos = content.lower().find(w.lower())
        if pos >= 0 and (best_pos < 0 or pos < best_pos):
            best_pos = pos
    if best_pos < 0:
        return content[:ctx]
    start = max(0, best_pos - ctx // 4)
    return content[start:start + ctx]


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def comp_stats():
    with db_session() as conn:
        countries = conn.execute(
            "SELECT COUNT(*) AS c FROM comp_countries"
        ).fetchone()["c"]
        laws = conn.execute(
            "SELECT COUNT(*) AS c FROM comp_laws"
        ).fetchone()["c"]
        articles = conn.execute(
            "SELECT COUNT(*) AS c FROM comp_law_articles"
        ).fetchone()["c"]
        courts = conn.execute(
            "SELECT COUNT(*) AS c FROM comp_courts"
        ).fetchone()["c"]
        decisions = conn.execute(
            "SELECT COUNT(*) AS c FROM comp_jurisprudence WHERE published=1"
        ).fetchone()["c"]
        return {
            "countries": countries,
            "laws": laws,
            "articles": articles,
            "courts": courts,
            "decisions": decisions,
        }


# ---------------------------------------------------------------------------
# Import Runs
# ---------------------------------------------------------------------------

def create_import_run(country_code: str, source_id: int | None = None):
    with db_session() as conn:
        cur = conn.execute(
            "INSERT INTO comp_import_runs "
            "(country_code, source_id, tenant_id) VALUES (?,?,?)",
            (country_code, source_id, tenant_scope.insert_tenant_id()),
        )
        return cur.lastrowid


def update_import_run(run_id: int, **kwargs):
    fields, vals = [], []
    for key in ("status", "finished_at", "docs_found", "docs_imported",
                "docs_skipped", "docs_failed", "error_message"):
        if key in kwargs:
            fields.append(f"{key} = ?")
            vals.append(kwargs[key])
    vals.append(run_id)
    if not fields:
        return
    with db_session() as conn:
        conn.execute(
            "UPDATE comp_import_runs SET " + ", ".join(fields) +
            " WHERE id = ?",
            vals,
        )


def list_import_runs(country_code: str | None = None, limit: int = 50):
    with db_session() as conn:
        q = "SELECT * FROM comp_import_runs"
        params = []
        if country_code:
            q += " WHERE country_code = ?"
            params.append(country_code)
        q += " ORDER BY started_at DESC LIMIT ?"
        params.append(limit)
        return [dict(r) for r in conn.execute(q, params).fetchall()]


def get_import_run(run_id: int):
    with db_session() as conn:
        row = conn.execute(
            "SELECT * FROM comp_import_runs WHERE id = ?", (run_id,),
        ).fetchone()
        return dict(row) if row else None


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def find_existing_by_hash(content_hash: str, table: str = "comp_laws"):
    """التحقق من وجود وثيقة بنفس content_hash (منع التكرار)."""
    if table not in ("comp_laws", "comp_jurisprudence"):
        return None
    with db_session() as conn:
        row = conn.execute(
            f"SELECT id FROM {table} WHERE content_hash = ?",
            (content_hash,),
        ).fetchone()
        return row["id"] if row else None
