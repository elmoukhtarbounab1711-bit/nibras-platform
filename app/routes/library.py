"""
نقاط نهاية المكتبة القانونية (Blueprint).

محتوى هذا الملف منقول حرفيًا من routes.py القائم مع الحفاظ على المسارات
دون أي بادئة وحدة (قرار تقني D-002 في docs/DECISIONS.md) لضمان عدم كسر
الواجهة الحالية أو الواجهة الأمامية nibras.html.
"""
from flask import Blueprint, Response, jsonify, request

from .. import services

library_bp = Blueprint("library", __name__)


@library_bp.route("/api/categories", methods=["GET"])
def get_categories():
    return jsonify(services.list_categories())


@library_bp.route("/api/texts", methods=["GET"])
def get_texts():
    category = request.args.get("category")
    text_type = request.args.get("type")
    jurisdiction_id = request.args.get("jurisdiction_id")
    limit = request.args.get("limit")
    offset = request.args.get("offset", 0)
    if limit is not None:
        limit = max(1, min(int(limit), 100))
    return jsonify(services.list_texts(
        category_slug=category, text_type=text_type,
        jurisdiction_id=jurisdiction_id,
        limit=limit, offset=int(offset or 0),
    ))


@library_bp.route("/api/texts/<int:text_id>", methods=["GET"])
def get_text(text_id):
    text = services.get_text(text_id)
    if not text:
        return jsonify({"error": "النص القانوني غير موجود"}), 404
    return jsonify(text)


@library_bp.route("/api/articles", methods=["GET"])
def list_articles():
    """قائمة أحدث المواد عبر المكتبة — تُغذي قسم المقالات في الواجهة."""
    limit = min(max(int(request.args.get("limit", 12)), 1), 100)
    offset = max(int(request.args.get("offset", 0)), 0)
    articles = services.list_articles(limit=limit, offset=offset)
    total = services.count_articles()
    return jsonify({"count": total, "articles": articles})


@library_bp.route("/api/articles/<int:article_id>", methods=["GET"])
def get_article(article_id):
    services.increment_article_views(article_id)
    article = services.get_article(article_id)
    if not article:
        return jsonify({"error": "المادة غير موجودة"}), 404
    return jsonify(article)


@library_bp.route("/api/texts/<int:text_id>/pdf", methods=["GET"])
def text_pdf(text_id):
    """عرض/تحميل النص القانوني PDF — يفضَّل الملف المرفوع إداريًا (إن وُجد)
    ثم الرابط الخارجي (source_url)، وإلا يُولَّد تلقائيًا."""
    from flask import send_file

    from .. import services

    uploaded = services.get_uploaded_pdf(text_id)
    if uploaded is not None:
        path, _key, content_type = uploaded
        text = services.get_text(text_id)
        name = f"{text['title'] if text else f'law-{text_id}'}.pdf"
        return send_file(
            path,
            mimetype=content_type,
            as_attachment=bool(request.args.get("download")),
            download_name=name,
        )

    text = services.get_text(text_id)
    if text and text.get("source_url"):
        src = text["source_url"]
        if "r2.dev" in src or "r2.cloudflarestorage.com" in src:
            try:
                import requests as _req
                r = _req.get(src, timeout=15)
                if r.status_code == 200 and "pdf" in r.headers.get("Content-Type", ""):
                    disposition = "attachment" if request.args.get("download") else "inline"
                    safe_name = f"law-{text_id}.pdf"
                    out = Response(r.content, content_type="application/pdf")
                    out.headers["Content-Disposition"] = f'{disposition}; filename="{safe_name}"'
                    out.headers["Cache-Control"] = "public, max-age=86400"
                    return out
            except Exception:
                pass

    from .. import services_pdf

    result = services_pdf.render_text_pdf(text_id)
    if result is None:
        return jsonify({"error": "النص القانوني غير موجود"}), 404
    data, filename = result
    disposition = "attachment" if request.args.get("download") else "inline"
    resp = Response(data, mimetype="application/pdf")
    resp.headers["Content-Disposition"] = f"{disposition}; filename={filename}"
    return resp


@library_bp.route("/api/library/stats", methods=["GET"])
def library_stats():
    return jsonify(services.library_stats())


@library_bp.route("/api/domains", methods=["GET"])
def get_domains():
    """إرجاع جميع النطاقات القانونية مع عدد النصوص."""
    return jsonify(services.get_legal_domains(with_counts=True))


@library_bp.route("/api/domains/<int:domain_id>/categories", methods=["GET"])
def get_domain_categories(domain_id):
    """إرجاع الفئات التابعة لنطاق قانوني معين."""
    return jsonify(services.get_domain_categories(domain_id))


@library_bp.route("/api/domains/<int:domain_id>/texts", methods=["GET"])
def get_domain_texts(domain_id):
    """جلب النصوص القانونية ضمن نطاق معين مع ترقيم."""
    limit = min(int(request.args.get("limit", 20)), 100)
    offset = max(int(request.args.get("offset", 0)), 0)
    text_type = request.args.get("type")
    texts = services.get_legal_texts_by_domain(domain_id, limit, offset, text_type)
    total = services.count_legal_texts_by_domain(domain_id, text_type)
    return jsonify({"total": total, "texts": texts})


@library_bp.route("/api/search", methods=["GET"])
def search():
    q = request.args.get("q", "")
    limit = min(int(request.args.get("limit", 20)), 50)
    domain_id = request.args.get("domain_id", type=int)
    category_id = request.args.get("category_id", type=int)
    text_type = request.args.get("type")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    highlight = request.args.get("highlight", "true").lower() != "false"
    facets = request.args.get("facets", "true").lower() != "false"

    if not q.strip():
        return jsonify({"error": "الرجاء إدخال نص للبحث عبر المعامل q"}), 400

    result = services.search_legal(
        q, limit=limit, domain_id=domain_id, category_id=category_id,
        text_type=text_type, date_from=date_from, date_to=date_to,
        highlight=highlight, facets=facets
    )
    return jsonify(result)


@library_bp.route("/api/search/suggestions", methods=["GET"])
def search_suggestions():
    q = request.args.get("q", "")
    limit = min(int(request.args.get("limit", 8)), 20)
    suggestions = services.get_search_suggestions(q, limit=limit)
    return jsonify({"query": q, "suggestions": suggestions})


@library_bp.route("/api/ads/slot/<slot_slug>", methods=["GET"])
def ads_serve_slot(slot_slug):
    """API عام لجلب مزوّدين فتحة — يستخدمه الواجهة لتحميل السكريبتات.

    لا يتطلب مصادقة. يعيد إعدادات الإعلانات ومزوّدين الفتحة.
    لا يُعيد أي بيانات المستخدم أو رموز المصادقة.
    يتحقق من حالة الاشتراك المميز من جانب الخادم فقط.
    """
    from ..middleware.auth_middleware import _bearer_token
    from .. import services_ads, services_billing, services_auth

    is_premium = False
    token = _bearer_token()
    if token is not None:
        user_id = services_auth.decode_access_token(token)
        if user_id is not None:
            profile = services_auth.get_user_profile(user_id)
            if profile is not None and profile.status == "active":
                status = services_billing.premium_status_for_user(user_id)
                is_premium = status.get("is_premium", False)

    show = services_ads.should_show_ads(is_premium=is_premium)
    if not show:
        return jsonify({"enabled": False, "providers": []}), 200

    providers = services_ads.serve_slot(slot_slug)
    return jsonify({
        "enabled": True,
        "providers": providers,
    }), 200
