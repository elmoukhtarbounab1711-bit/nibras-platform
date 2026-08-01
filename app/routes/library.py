"""
نقاط نهاية المكتبة القانونية (Blueprint).

محتوى هذا الملف منقول حرفيًا من routes.py القائم مع الحفاظ على المسارات
دون أي بادئة وحدة (قرار تقني D-002 في docs/DECISIONS.md) لضمان عدم كسر
الواجهة الحالية أو الواجهة الأمامية nibras.html.
"""
from flask import Blueprint, jsonify, request

from .. import services

library_bp = Blueprint("library", __name__)


@library_bp.route("/api/categories", methods=["GET"])
def get_categories():
    return jsonify(services.list_categories())


@library_bp.route("/api/texts", methods=["GET"])
def get_texts():
    category = request.args.get("category")
    text_type = request.args.get("type")
    return jsonify(services.list_texts(category_slug=category, text_type=text_type))


@library_bp.route("/api/texts/<int:text_id>", methods=["GET"])
def get_text(text_id):
    text = services.get_text(text_id)
    if not text:
        return jsonify({"error": "النص القانوني غير موجود"}), 404
    return jsonify(text)


@library_bp.route("/api/articles/<int:article_id>", methods=["GET"])
def get_article(article_id):
    article = services.get_article(article_id)
    if not article:
        return jsonify({"error": "المادة غير موجودة"}), 404
    return jsonify(article)


@library_bp.route("/api/search", methods=["GET"])
def search():
    q = request.args.get("q", "")
    limit = min(int(request.args.get("limit", 20)), 50)
    if not q.strip():
        return jsonify({"error": "الرجاء إدخال نص للبحث عبر المعامل q"}), 400
    results = services.search_articles(q, limit=limit)
    return jsonify({"query": q, "count": len(results), "results": results})
