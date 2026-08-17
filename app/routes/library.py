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
    وإلا يُولَّد تلقائيًا (reportlab + تشكيل عربي)."""
    from flask import send_file

    from .. import services

    uploaded = services.get_uploaded_pdf(text_id)
    if uploaded is not None:
        path, _key, content_type = uploaded
        disposition = "attachment" if request.args.get("download") else "inline"
        text = services.get_text(text_id)
        name = f"{text['title'] if text else f'law-{text_id}'}.pdf"
        return send_file(
            path,
            mimetype=content_type,
            as_attachment=bool(request.args.get("download")),
            download_name=name,
        )

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


@library_bp.route("/api/search", methods=["GET"])
def search():
    q = request.args.get("q", "")
    limit = min(int(request.args.get("limit", 20)), 50)
    if not q.strip():
        return jsonify({"error": "الرجاء إدخال نص للبحث عبر المعامل q"}), 400
    results = services.search_articles(q, limit=limit)
    return jsonify({"query": q, "count": len(results), "results": results})
