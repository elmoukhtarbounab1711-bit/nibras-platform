"""
مسارات القانون المقارن (Blueprint) — المرحلة 20 (قرار D-038).

تصفح عام للولايات القضائية والدراسات المنشورة فقط؛ الإنشاء لأي مستخدم
مسجَّل (يبدأ draft) وإدارة مقارناته؛ النشر/الإخفاء إداري حصري (في
routes/admin.py مع إدارة الولايات القضائية).
"""
from flask import Blueprint, jsonify, request

from .. import services, services_blog, services_comparative, services_jurisprudence
from ..middleware.auth_middleware import optional_auth, require_auth
from ..services_comparative import ComparativeError

comparative_bp = Blueprint("comparative", __name__)


def _handle_error(exc: ComparativeError):
    return jsonify({"error": exc.message}), exc.status_code


def _clamp(value, default, lo, hi):
    try:
        return max(lo, min(int(value), hi))
    except (TypeError, ValueError):
        return default


@comparative_bp.route("/api/comparative/jurisdictions", methods=["GET"])
def list_jurisdictions():
    include_all = request.args.get("all") == "1"
    return jsonify({
        "jurisdictions": services_comparative.list_jurisdictions(
            include_all=include_all
        )
    })


@comparative_bp.route("/api/comparative/jurisdictions/<slug>",
                      methods=["GET"])
def jurisdiction_detail(slug):
    """صفحة الولاية: بياناتها مع عدّادات (نصوص/اجتهادات/دراسات)."""
    include_all = request.args.get("all") == "1"
    juris = services_comparative.get_jurisdiction_by_slug(slug,
                                                          include_all=include_all)
    if not juris:
        return jsonify({"error": "الولاية القضائية غير موجودة."}), 404
    counts = next(
        (j for j in services_comparative.list_jurisdictions(include_all=True)
         if j["id"] == juris["id"]), {})
    juris["text_count"] = counts.get("text_count", 0)
    juris["decision_count"] = counts.get("decision_count", 0)
    juris["study_count"] = counts.get("study_count", 0)
    return jsonify({"jurisdiction": juris})


@comparative_bp.route("/api/comparative/jurisdictions/<slug>/categories",
                      methods=["GET"])
def jurisdiction_categories(slug):
    """فئات نصوص الولاية (خاصة بصفحتها — من نصوصها فقط)."""
    juris = services_comparative.get_jurisdiction_by_slug(slug)
    if not juris:
        return jsonify({"error": "الولاية القضائية غير موجودة."}), 404
    return jsonify({
        "categories": services_comparative.list_jurisdiction_text_categories(
            juris["id"]
        )
    })


@comparative_bp.route("/api/comparative/jurisdictions/<slug>/texts",
                      methods=["GET"])
def jurisdiction_texts(slug):
    """قوانين الولاية (نصوص المكتبة المرتبطة بها) قابلة للترشيح بالفئة."""
    juris = services_comparative.get_jurisdiction_by_slug(slug)
    if not juris:
        return jsonify({"error": "الولاية القضائية غير موجودة."}), 404
    limit = _clamp(request.args.get("limit"), 12, 1, 100)
    offset = _clamp(request.args.get("offset"), 0, 0, 10_000)
    result = services.list_texts(
        jurisdiction_id=juris["id"], limit=limit, offset=offset,
        category_slug=request.args.get("category") or None,
    )
    return jsonify(result)


@comparative_bp.route("/api/comparative/jurisdictions/<slug>/decisions",
                      methods=["GET"])
def jurisdiction_decisions(slug):
    """اجتهادات الولاية (القرارات المنشورة المرتبطة بها) قابلة للترشيح بالفئة."""
    juris = services_comparative.get_jurisdiction_by_slug(slug)
    if not juris:
        return jsonify({"error": "الولاية القضائية غير موجودة."}), 404
    limit = _clamp(request.args.get("limit"), 12, 1, 100)
    offset = _clamp(request.args.get("offset"), 0, 0, 10_000)
    result = services_jurisprudence.list_decisions(
        jurisdiction_id=juris["id"], limit=limit, offset=offset,
        category_slug=request.args.get("category") or None,
    )
    return jsonify(result)


@comparative_bp.route("/api/comparative/jurisdictions/<slug>/articles",
                      methods=["GET"])
def jurisdiction_articles(slug):
    """مقالات «الدراسات المقارنة» المنشورة لدولة الولاية (صفحة الدراسات)."""
    juris = services_comparative.get_jurisdiction_by_slug(slug)
    if not juris:
        return jsonify({"error": "الولاية القضائية غير موجودة."}), 404
    result = services_blog.list_comparative_articles(juris["id"])
    return jsonify(result)


@comparative_bp.route("/api/comparative/studies", methods=["GET"])
def list_studies():
    try:
        result = services_comparative.list_studies(
            q=request.args.get("q"),
            jurisdiction_id=request.args.get("jurisdiction_id"),
            limit=_clamp(request.args.get("limit"), 12, 1, 100),
            offset=_clamp(request.args.get("offset"), 0, 0, 10_000),
        )
    except ComparativeError as exc:
        return _handle_error(exc)
    return jsonify(result)


@comparative_bp.route("/api/comparative/studies/<int:study_id>", methods=["GET"])
@optional_auth
def study_detail(study_id):
    viewer = getattr(request, "user", None)
    is_admin = bool(viewer and viewer.roles and "admin" in viewer.roles)
    data = services_comparative.get_study(
        study_id,
        viewer_id=viewer.id if viewer else None,
        include_internal=is_admin,
    )
    if not data:
        return jsonify({"error": "الدراسة غير موجودة."}), 404
    return jsonify(data)


@comparative_bp.route("/api/comparative/studies", methods=["POST"])
@require_auth
def create_study():
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = services_comparative.create_study(request.user.id, data)
    except ComparativeError as exc:
        return _handle_error(exc)
    return jsonify(result), 201


@comparative_bp.route("/api/comparative/studies/<int:study_id>", methods=["PUT"])
@require_auth
def update_study(study_id):
    data = request.get_json(force=True, silent=True) or {}
    is_admin = request.user.roles and "admin" in request.user.roles
    try:
        result = services_comparative.update_study(
            request.user.id, study_id, data, is_admin=is_admin
        )
    except ComparativeError as exc:
        return _handle_error(exc)
    return jsonify(result)


@comparative_bp.route("/api/comparative/studies/<int:study_id>", methods=["DELETE"])
@require_auth
def delete_study(study_id):
    is_admin = request.user.roles and "admin" in request.user.roles
    try:
        result = services_comparative.delete_study(
            request.user.id, study_id, is_admin=is_admin
        )
    except ComparativeError as exc:
        return _handle_error(exc)
    return jsonify(result)


@comparative_bp.route("/api/comparative/my", methods=["GET"])
@require_auth
def my_studies():
    return jsonify({
        "studies": services_comparative.list_studies_for_user(request.user.id)
    })


@comparative_bp.route("/api/comparative/studies/<int:study_id>/entries",
                      methods=["POST"])
@require_auth
def add_entry(study_id):
    data = request.get_json(force=True, silent=True) or {}
    is_admin = request.user.roles and "admin" in request.user.roles
    try:
        result = services_comparative.add_entry(
            request.user.id, study_id, data, is_admin=is_admin
        )
    except ComparativeError as exc:
        return _handle_error(exc)
    return jsonify(result), 201


@comparative_bp.route("/api/comparative/entries/<int:entry_id>",
                      methods=["PUT"])
@require_auth
def update_entry(entry_id):
    data = request.get_json(force=True, silent=True) or {}
    is_admin = request.user.roles and "admin" in request.user.roles
    try:
        result = services_comparative.update_entry(
            request.user.id, entry_id, data, is_admin=is_admin
        )
    except ComparativeError as exc:
        return _handle_error(exc)
    return jsonify(result)


@comparative_bp.route("/api/comparative/entries/<int:entry_id>",
                      methods=["DELETE"])
@require_auth
def delete_entry(entry_id):
    is_admin = request.user.roles and "admin" in request.user.roles
    try:
        result = services_comparative.delete_entry(
            request.user.id, entry_id, is_admin=is_admin
        )
    except ComparativeError as exc:
        return _handle_error(exc)
    return jsonify(result)