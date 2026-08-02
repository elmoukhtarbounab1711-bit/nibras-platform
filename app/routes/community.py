"""
مسارات المجتمع (Blueprint) — المرحلة 6 (قرار D-024).

القراءة عامة (فئات/منشورات/تفصيل) والكتابة بمصادقة مع حد معدل على الإنشاء
(وثيقة 16 §4)، وحذف/تعديل لمالك المحتوى فقط، والبلاغات لأي مستخدم نشط
تدخل طابور الإشراف (القراءة/الإجراء للأدمن في routes/admin.py). التفصيل
العام يُثري بـ my_reactions للمُصادَق عبر optional_auth.
"""
import time

from flask import Blueprint, jsonify, request

from .. import config, services_community
from ..middleware.auth_middleware import optional_auth, require_auth
from ..services_community import CommunityError

community_bp = Blueprint("community", __name__)

# حد معدل في الذاكرة لكل مستخدم (+ عنوان IP) — نمط routes/ai.py
_attempts = {}


def _rate_limited(key: str) -> bool:
    now = time.time()
    window = config.COMMUNITY_RATE_LIMIT_WINDOW_SECONDS
    bucket = _attempts.setdefault(key, [])
    bucket[:] = [t for t in bucket if now - t < window]
    if len(bucket) >= config.COMMUNITY_RATE_LIMIT_MAX_REQUESTS:
        return True
    bucket.append(now)
    return False


def _client_key(prefix: str) -> str:
    return f"{prefix}:{request.user.id}:{request.remote_addr or 'unknown'}"


def _viewer_id():
    return getattr(request, "user", None).id if getattr(request, "user", None) else None


@community_bp.route("/api/community/categories", methods=["GET"])
def list_categories():
    return jsonify(services_community.list_categories())


@community_bp.route("/api/community/posts", methods=["GET"])
def list_posts():
    try:
        category_id = request.args.get("category")
        if category_id:
            category_id = int(category_id)
    except (TypeError, ValueError):
        return jsonify({"error": "category يجب أن يكون رقمًا."}), 400
    try:
        result = services_community.list_posts(
            category_id=category_id,
            limit=int(request.args.get("limit") or 0),
            offset=int(request.args.get("offset") or 0),
        )
    except ValueError:
        return jsonify({"error": "limit/offset يجب أن تكون أرقامًا."}), 400
    return jsonify(result)


@community_bp.route("/api/community/posts/<int:post_id>", methods=["GET"])
@optional_auth
def post_detail(post_id):
    post = services_community.get_post(post_id, viewer_id=_viewer_id())
    if not post:
        return jsonify({"error": "المنشور غير موجود."}), 404
    return jsonify(post)


@community_bp.route("/api/community/posts", methods=["POST"])
@require_auth
def create_post():
    if _rate_limited(_client_key("post")):
        return jsonify({"error": "طلبات كثيرة جدًا. حاول لاحقًا."}), 429
    data = request.get_json(force=True, silent=True) or {}
    try:
        post = services_community.create_post(request.user.id, data)
    except CommunityError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify(post), 201


@community_bp.route("/api/community/posts/<int:post_id>", methods=["PUT"])
@require_auth
def update_post(post_id):
    data = request.get_json(force=True, silent=True) or {}
    try:
        post = services_community.update_post(request.user.id, post_id, data)
    except CommunityError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify(post)


@community_bp.route("/api/community/posts/<int:post_id>", methods=["DELETE"])
@require_auth
def delete_post(post_id):
    try:
        result = services_community.delete_post(request.user.id, post_id)
    except CommunityError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify(result)


@community_bp.route("/api/community/posts/<int:post_id>/comments", methods=["POST"])
@require_auth
def add_comment(post_id):
    if _rate_limited(_client_key("comment")):
        return jsonify({"error": "طلبات كثيرة جدًا. حاول لاحقًا."}), 429
    data = request.get_json(force=True, silent=True) or {}
    try:
        comment = services_community.add_comment(request.user.id, post_id, data)
    except CommunityError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify(comment), 201


@community_bp.route(
    "/api/community/posts/<int:post_id>/comments/<int:comment_id>",
    methods=["PUT"],
)
@require_auth
def update_comment(post_id, comment_id):
    data = request.get_json(force=True, silent=True) or {}
    try:
        comment = services_community.update_comment(
            request.user.id, post_id, comment_id, data
        )
    except CommunityError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify(comment)


@community_bp.route(
    "/api/community/posts/<int:post_id>/comments/<int:comment_id>",
    methods=["DELETE"],
)
@require_auth
def delete_comment(post_id, comment_id):
    try:
        result = services_community.delete_comment(
            request.user.id, post_id, comment_id
        )
    except CommunityError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify(result)


@community_bp.route("/api/community/posts/<int:post_id>/react", methods=["POST"])
@require_auth
def react(post_id):
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = services_community.toggle_reaction(
            request.user.id, post_id, data.get("type", "like")
        )
    except CommunityError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify(result)


@community_bp.route("/api/community/report", methods=["POST"])
@require_auth
def report():
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = services_community.create_report(request.user.id, data)
    except CommunityError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    status_code = 200 if result.get("already_reported") else 201
    return jsonify(result), status_code
