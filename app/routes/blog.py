"""
مسارات بوابة المقالات القانونية (Blueprint) — مرحلة الواجهة (وحدة إضافية).

التصفح العام يعرض المقالات المنشورة فقط (فرض عند مستوى الاستعلام). إنشاء
المقال لأي مستخدم مسجَّل (يبدأ pending)؛ النشر/الإخفاء إداري حصري في
routes/admin.py. التفاعلات (إعجاب/تعليق/بلاغ) بمصادقة؛ تفصيل المقال بمصادقة
اختيارية ليُظهر حالة إعجاب المستخدم الحالي.
"""
from flask import Blueprint, jsonify, request

from .. import services_blog
from ..middleware.auth_middleware import optional_auth, require_auth
from ..services_blog import BlogError

blog_bp = Blueprint("blog", __name__)


def _handle_blog_error(exc: BlogError):
    return jsonify({"error": exc.message}), exc.status_code


def _clamp(value, default, lo, hi):
    try:
        return max(lo, min(int(value), hi))
    except (TypeError, ValueError):
        return default


@blog_bp.route("/api/blog/categories", methods=["GET"])
def list_categories():
    return jsonify(services_blog.list_categories())


@blog_bp.route("/api/blog/articles", methods=["GET"])
def list_articles():
    try:
        result = services_blog.list_articles(
            category=request.args.get("category"),
            q=request.args.get("q"),
            jurisdiction_id=request.args.get("jurisdiction_id"),
            limit=_clamp(request.args.get("limit"), 12, 1, 100),
            offset=_clamp(request.args.get("offset"), 0, 0, 10_000),
        )
    except BlogError as exc:
        return _handle_blog_error(exc)
    return jsonify(result)


@blog_bp.route("/api/blog/articles/<int:article_id>", methods=["GET"])
@optional_auth
def article_detail(article_id):
    viewer = getattr(request, "user", None)
    is_admin = bool(viewer and viewer.roles and "admin" in viewer.roles)
    data = services_blog.get_article(
        article_id,
        viewer_id=viewer.id if viewer else None,
        include_internal=is_admin,
    )
    if not data:
        return jsonify({"error": "المقال غير موجود."}), 404
    return jsonify(data)


@blog_bp.route("/api/blog/articles", methods=["POST"])
@require_auth
def create_article():
    data = request.get_json(force=True, silent=True) or {}
    is_admin = request.user.roles and "admin" in request.user.roles
    try:
        result = services_blog.create_article(request.user.id, data, is_admin=is_admin)
    except BlogError as exc:
        return _handle_blog_error(exc)
    return jsonify(result), 201


@blog_bp.route("/api/blog/articles/<int:article_id>", methods=["PUT"])
@require_auth
def update_article(article_id):
    data = request.get_json(force=True, silent=True) or {}
    is_admin = request.user.roles and "admin" in request.user.roles
    try:
        result = services_blog.update_article(
            request.user.id, article_id, data, is_admin=is_admin
        )
    except BlogError as exc:
        return _handle_blog_error(exc)
    return jsonify(result)


@blog_bp.route("/api/blog/articles/<int:article_id>", methods=["DELETE"])
@require_auth
def delete_article(article_id):
    is_admin = request.user.roles and "admin" in request.user.roles
    try:
        result = services_blog.delete_article(
            request.user.id, article_id, is_admin=is_admin
        )
    except BlogError as exc:
        return _handle_blog_error(exc)
    return jsonify(result)


@blog_bp.route("/api/blog/articles/<int:article_id>/like", methods=["POST"])
@require_auth
def like_article(article_id):
    try:
        result = services_blog.toggle_like(request.user.id, article_id)
    except BlogError as exc:
        return _handle_blog_error(exc)
    return jsonify(result)


@blog_bp.route("/api/blog/articles/<int:article_id>/comments", methods=["GET"])
def article_comments(article_id):
    try:
        return jsonify(services_blog.list_comments(article_id))
    except BlogError as exc:
        return _handle_blog_error(exc)


@blog_bp.route("/api/blog/articles/<int:article_id>/comments", methods=["POST"])
@require_auth
def add_comment(article_id):
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = services_blog.add_comment(
            request.user.id, article_id, data.get("body")
        )
    except BlogError as exc:
        return _handle_blog_error(exc)
    return jsonify(result), 201


@blog_bp.route("/api/blog/articles/<int:article_id>/report", methods=["POST"])
@require_auth
def report_article(article_id):
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = services_blog.add_report(
            request.user.id, article_id, data.get("reason")
        )
    except BlogError as exc:
        return _handle_blog_error(exc)
    return jsonify(result), 201


@blog_bp.route("/api/blog/my", methods=["GET"])
@require_auth
def my_articles():
    return jsonify({
        "articles": services_blog.list_articles_for_user(request.user.id)
    })
