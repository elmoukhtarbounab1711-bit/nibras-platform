"""
مسارات القانون المقارن المستقل (Blueprint) — دول + قوانين + اجتهادات.

وحدة مستقلة بالكامل عن المكتبة المغربية: مسارات منفصلة (/api/comp/)
مع عزل صارم على مستوى قاعدة البيانات. لا تتداخل مع /api/texts أو
/api/search أبدًا.
"""
from flask import Blueprint, jsonify, request

from .. import services_comp
from ..database import db_session
from ..middleware.auth_middleware import require_role
from ..services_comp import CompError

comp_bp = Blueprint("comp", __name__)

# المسارات الحساسة تحصل على no-store (app/__init__.py يغطي /api/admin/)


def _handle(exc: CompError):
    return jsonify({"error": exc.message}), exc.status_code


def _clamp(value, default, lo, hi):
    try:
        return max(lo, min(int(value), hi))
    except (TypeError, ValueError):
        return default


# ===================================================================
# Public Endpoints
# ===================================================================

@comp_bp.route("/api/comp/countries", methods=["GET"])
def list_countries():
    return jsonify({"countries": services_comp.list_countries()})


@comp_bp.route("/api/comp/countries/<code>", methods=["GET"])
def country_detail(code):
    country = services_comp.get_country(code)
    if not country:
        return jsonify({"error": "الدولة غير موجودة"}), 404
    return jsonify(country)


@comp_bp.route("/api/comp/countries/<code>/categories", methods=["GET"])
def country_categories(code):
    country = services_comp.get_country(code)
    if not country:
        return jsonify({"error": "الدولة غير موجودة"}), 404
    with db_session() as conn:
        rows = conn.execute(
            "SELECT category, COUNT(*) AS count FROM comp_laws "
            "WHERE country_id = ? GROUP BY category ORDER BY count DESC",
            (country["id"],),
        ).fetchall()
    return jsonify({"categories": [dict(r) for r in rows]})


@comp_bp.route("/api/comp/countries/<code>/laws", methods=["GET"])
def country_laws(code):
    country = services_comp.get_country(code)
    if not country:
        return jsonify({"error": "الدولة غير موجودة"}), 404
    category = request.args.get("category")
    laws = services_comp.list_laws(country["id"], category=category)
    return jsonify({"laws": laws, "country": country["code"]})


@comp_bp.route("/api/comp/countries/<code>/courts", methods=["GET"])
def country_courts(code):
    country = services_comp.get_country(code)
    if not country:
        return jsonify({"error": "الدولة غير موجودة"}), 404
    courts = services_comp.list_courts(country["id"])
    return jsonify({"courts": courts, "country": country["code"]})


@comp_bp.route("/api/comp/countries/<code>/jurisprudence",
               methods=["GET"])
def country_jurisprudence(code):
    country = services_comp.get_country(code)
    if not country:
        return jsonify({"error": "الدولة غير موجودة"}), 404
    court_id = request.args.get("court_id", type=int)
    decisions = services_comp.list_jurisprudence(
        country["id"], court_id=court_id,
    )
    return jsonify({
        "decisions": decisions,
        "country": country["code"],
    })


@comp_bp.route("/api/comp/laws/<int:law_id>", methods=["GET"])
def law_detail(law_id):
    law = services_comp.get_law(law_id)
    if not law:
        return jsonify({"error": "القانون غير موجود"}), 404
    return jsonify(law)


@comp_bp.route("/api/comp/laws/<int:law_id>/articles/<int:article_id>",
               methods=["GET"])
def law_article_detail(law_id, article_id):
    article = services_comp.get_law_article(article_id)
    if not article or article["law_id"] != law_id:
        return jsonify({"error": "المادة غير موجودة"}), 404
    return jsonify(article)


@comp_bp.route("/api/comp/jurisprudence/<int:decision_id>",
               methods=["GET"])
def decision_detail(decision_id):
    decision = services_comp.get_decision(decision_id)
    if not decision:
        return jsonify({"error": "القرار غير موجود"}), 404
    return jsonify(decision)


@comp_bp.route("/api/comp/search", methods=["GET"])
def search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "الرجاء إدخال كلمة البحث (q)"}), 400
    country = request.args.get("country")
    doc_type = request.args.get("type")
    limit = _clamp(request.args.get("limit", 50), 50, 1, 200)
    results = services_comp.search_comp(
        q, country_code=country, doc_type=doc_type, limit=limit,
    )
    return jsonify({"query": q, "count": len(results), "results": results})


@comp_bp.route("/api/comp/stats", methods=["GET"])
def stats():
    return jsonify(services_comp.comp_stats())


# ===================================================================
# Admin Endpoints
# ===================================================================

@comp_bp.route("/api/admin/comp/laws", methods=["POST"])
@require_role("admin")
def admin_create_law():
    data = request.get_json(force=True, silent=True) or {}
    country_code = data.get("country_code", "").strip()
    title = (data.get("title") or "").strip()
    if not country_code or not title:
        return jsonify({"error": "country_code و title مطلوبان"}), 400
    country = services_comp.get_country(country_code)
    if not country:
        return jsonify({"error": "الدولة غير موجودة"}), 404
    law_id = services_comp.create_law(
        country["id"], title,
        category=data.get("category", "general"),
        title_original=data.get("title_original"),
        official_ref=data.get("official_ref"),
        language=data.get("language", country.get("language", "fr")),
        enacted_date=data.get("enacted_date"),
        published_date=data.get("published_date"),
        source_name=data.get("source_name"),
        source_url=data.get("source_url"),
        official_source=data.get("official_source", 0),
        content=data.get("content", ""),
    )
    return jsonify({"id": law_id}), 201


@comp_bp.route("/api/admin/comp/laws/<int:law_id>", methods=["PUT"])
@require_role("admin")
def admin_update_law(law_id):
    law = services_comp.get_law(law_id)
    if not law:
        return jsonify({"error": "القانون غير موجود"}), 404
    data = request.get_json(force=True, silent=True) or {}
    services_comp.update_law(law_id, **data)
    return jsonify({"ok": True})


@comp_bp.route("/api/admin/comp/laws/<int:law_id>", methods=["DELETE"])
@require_role("admin")
def admin_delete_law(law_id):
    law = services_comp.get_law(law_id)
    if not law:
        return jsonify({"error": "القانون غير موجود"}), 404
    services_comp.delete_law(law_id)
    return jsonify({"ok": True})


@comp_bp.route("/api/admin/comp/laws/<int:law_id>/articles",
               methods=["POST"])
@require_role("admin")
def admin_create_article(law_id):
    law = services_comp.get_law(law_id)
    if not law:
        return jsonify({"error": "القانون غير موجود"}), 404
    data = request.get_json(force=True, silent=True) or {}
    number = (data.get("number") or "").strip()
    label = (data.get("label") or "").strip()
    content = data.get("content", "")
    if not number or not label or not content:
        return jsonify({"error": "number و label و content مطلوبة"}), 400
    article_id = services_comp.create_law_article(
        law_id, number, label, content, keywords=data.get("keywords"),
    )
    return jsonify({"id": article_id}), 201


@comp_bp.route("/api/admin/comp/articles/<int:article_id>", methods=["PUT"])
@require_role("admin")
def admin_update_article(article_id):
    article = services_comp.get_law_article(article_id)
    if not article:
        return jsonify({"error": "المادة غير موجودة"}), 404
    data = request.get_json(force=True, silent=True) or {}
    services_comp.update_law_article(article_id, **data)
    return jsonify({"ok": True})


@comp_bp.route("/api/admin/comp/articles/<int:article_id>",
               methods=["DELETE"])
@require_role("admin")
def admin_delete_article(article_id):
    article = services_comp.get_law_article(article_id)
    if not article:
        return jsonify({"error": "المادة غير موجودة"}), 404
    services_comp.delete_law_article(article_id)
    return jsonify({"ok": True})


@comp_bp.route("/api/admin/comp/courts", methods=["POST"])
@require_role("admin")
def admin_create_court():
    data = request.get_json(force=True, silent=True) or {}
    country_code = data.get("country_code", "").strip()
    name = (data.get("name") or "").strip()
    slug = (data.get("slug") or "").strip()
    if not country_code or not name or not slug:
        return jsonify({"error": "country_code و name و slug مطلوبة"}), 400
    country = services_comp.get_country(country_code)
    if not country:
        return jsonify({"error": "الدولة غير موجودة"}), 404
    court_id = services_comp.create_court(
        country["id"], name, slug,
        name_ar=data.get("name_ar"),
        description=data.get("description"),
    )
    return jsonify({"id": court_id}), 201


@comp_bp.route("/api/admin/comp/courts/<int:court_id>", methods=["PUT"])
@require_role("admin")
def admin_update_court(court_id):
    court = services_comp.get_court(court_id)
    if not court:
        return jsonify({"error": "المحكمة غير موجودة"}), 404
    data = request.get_json(force=True, silent=True) or {}
    services_comp.update_court(court_id, **data)
    return jsonify({"ok": True})


@comp_bp.route("/api/admin/comp/courts/<int:court_id>", methods=["DELETE"])
@require_role("admin")
def admin_delete_court(court_id):
    court = services_comp.get_court(court_id)
    if not court:
        return jsonify({"error": "المحكمة غير موجودة"}), 404
    services_comp.delete_court(court_id)
    return jsonify({"ok": True})


@comp_bp.route("/api/admin/comp/jurisprudence", methods=["POST"])
@require_role("admin")
def admin_create_decision():
    data = request.get_json(force=True, silent=True) or {}
    country_code = data.get("country_code", "").strip()
    title = (data.get("title") or "").strip()
    content = data.get("content", "")
    if not country_code or not title or not content:
        return jsonify({"error": "country_code و title و content مطلوبة"}), 400
    country = services_comp.get_country(country_code)
    if not country:
        return jsonify({"error": "الدولة غير موجودة"}), 404
    court_id = data.get("court_id")
    decision_id = services_comp.create_decision(
        country["id"], title, content, court_id=court_id,
        decision_number=data.get("decision_number"),
        decision_date=data.get("decision_date"),
        decision_type=data.get("decision_type"),
        keywords=data.get("keywords"),
        source_name=data.get("source_name"),
        source_url=data.get("source_url"),
        official_source=data.get("official_source", 0),
    )
    return jsonify({"id": decision_id}), 201


@comp_bp.route("/api/admin/comp/jurisprudence/<int:decision_id>",
               methods=["PUT"])
@require_role("admin")
def admin_update_decision(decision_id):
    decision = services_comp.get_decision(decision_id)
    if not decision:
        return jsonify({"error": "القرار غير موجود"}), 404
    data = request.get_json(force=True, silent=True) or {}
    services_comp.update_decision(decision_id, **data)
    return jsonify({"ok": True})


@comp_bp.route("/api/admin/comp/jurisprudence/<int:decision_id>",
               methods=["DELETE"])
@require_role("admin")
def admin_delete_decision(decision_id):
    decision = services_comp.get_decision(decision_id)
    if not decision:
        return jsonify({"error": "القرار غير موجود"}), 404
    services_comp.delete_decision(decision_id)
    return jsonify({"ok": True})


@comp_bp.route("/api/admin/comp/import/run", methods=["POST"])
@require_role("admin")
def admin_trigger_import():
    data = request.get_json(force=True, silent=True) or {}
    country_code = data.get("country_code", "").strip()
    source_id = data.get("source_id")
    dataset = data.get("dataset", "").strip()
    if not country_code:
        return jsonify({"error": "country_code مطلوب"}), 400
    country = services_comp.get_country(country_code)
    if not country:
        return jsonify({"error": "الدولة غير موجودة"}), 404

    if country_code == "france" and dataset:
        from ..services_comp_import import (
            FRANCE_DATASETS,
            import_france_decisions,
        )
        if dataset not in FRANCE_DATASETS:
            return jsonify({
                "error": f"dataset غير معروف: {dataset}. "
                         f"الخيارات: {', '.join(FRANCE_DATASETS)}",
            }), 400
        result = import_france_decisions(
            dataset, run_id=services_comp.create_import_run(
                country_code, source_id))
        return jsonify(result), 201

    run_id = services_comp.create_import_run(country_code, source_id)
    return jsonify({
        "id": run_id,
        "status": "running",
        "message": "تم بدء جلسة الاستيراد",
    }), 201


@comp_bp.route("/api/admin/comp/import/runs", methods=["GET"])
@require_role("admin")
def admin_list_import_runs():
    country = request.args.get("country")
    limit = _clamp(request.args.get("limit", 50), 50, 1, 200)
    runs = services_comp.list_import_runs(country_code=country, limit=limit)
    return jsonify({"runs": runs})


@comp_bp.route("/api/admin/comp/import/runs/<int:run_id>", methods=["GET"])
@require_role("admin")
def admin_import_run_detail(run_id):
    run = services_comp.get_import_run(run_id)
    if not run:
        return jsonify({"error": "جلسة الاستيراد غير موجودة"}), 404
    return jsonify(run)


@comp_bp.route("/api/admin/comp/laws/<int:law_id>/articles",
               methods=["GET"])
@require_role("admin")
def admin_list_law_articles(law_id):
    law = services_comp.get_law(law_id)
    if not law:
        return jsonify({"error": "القانون غير موجود"}), 404
    articles = services_comp.list_law_articles(law_id)
    return jsonify({"articles": articles})
