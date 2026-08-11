"""
نقاط نهاية الاجتهادات القضائية (Blueprint).

قراءة عامة للاجتهادات: الفئات (مع عدد الاجتهادات)، قوائم جلرات قابلة للتصفية
بالفئة مع ترقيم، تفاصيل قرار مع جرد المشاهدات، وبحث نصي كامل بالكلمة عبر
FTS5 (يعيد جميع النصوص المحتوية على الكلمة). إدارة الاجتهادات والفئات
(إنشاء/تحديث/نشر/حذف) بدور admin — متوفرة ضمن هذا الـ blueprint نفسه بنمط
billing (المسارات تحت /api/admin/...).
"""
from flask import Blueprint, jsonify, request

from .. import services_jurisprudence
from ..middleware.auth_middleware import require_role
from .admin import _admin_form_or_json, _admin_id, _handle_jurisprudence_error

jurisprudence_bp = Blueprint("jurisprudence", __name__)


def _clamped_args():
    try:
        limit = int(request.args.get("limit") or services_jurisprudence.DEFAULT_LIST_LIMIT)
        offset = int(request.args.get("offset") or 0)
    except (TypeError, ValueError):
        return None
    return limit, offset


@jurisprudence_bp.route("/api/jurisprudence/categories", methods=["GET"])
def list_categories():
    return jsonify(services_jurisprudence.list_categories())


@jurisprudence_bp.route("/api/jurisprudence", methods=["GET"])
def list_decisions():
    args = _clamped_args()
    if args is None:
        return jsonify({"error": "limit/offset يجب أن تكون أرقامًا."}), 400
    limit, offset = args
    return jsonify(services_jurisprudence.list_decisions(
        category_slug=request.args.get("category"),
        limit=limit,
        offset=offset,
    ))


@jurisprudence_bp.route("/api/jurisprudence/search", methods=["GET"])
def search_decisions():
    q = request.args.get("q", "")
    if not q.strip():
        return jsonify({"error": "أدخل كلمة للبحث في الاجتهادات."}), 400
    limit = min(max(int(request.args.get("limit", 20)), 1), 50)
    results = services_jurisprudence.search_decisions(
        q, category_slug=request.args.get("category"), limit=limit
    )
    return jsonify({"query": q, "count": len(results), "results": results})


@jurisprudence_bp.route("/api/jurisprudence/stats", methods=["GET"])
def stats():
    return jsonify(services_jurisprudence.jurisprudence_stats())


@jurisprudence_bp.route("/api/jurisprudence/<int:decision_id>", methods=["GET"])
def get_decision(decision_id):
    decision = services_jurisprudence.get_decision(decision_id)
    if not decision:
        return jsonify({"error": "الاجتهاد غير موجود."}), 404
    return jsonify(decision)


# ---------------------------------------------------------------------------
# إدارة (admin)
# ---------------------------------------------------------------------------

@jurisprudence_bp.route("/api/admin/jurisprudence", methods=["GET"])
@require_role("admin")
def admin_list_decisions():
    try:
        limit = max(1, min(int(request.args.get("limit") or 50), 200))
        offset = max(0, int(request.args.get("offset") or 0))
    except (TypeError, ValueError):
        return jsonify({"error": "limit/offset يجب أن تكون أرقامًا."}), 400
    return jsonify(services_jurisprudence.list_decisions_admin(
        status=request.args.get("status"),
        q=request.args.get("q"),
        limit=limit,
        offset=offset,
    ))


@jurisprudence_bp.route("/api/admin/jurisprudence", methods=["POST"])
@require_role("admin")
def admin_create_decision():
    data = _admin_form_or_json()
    try:
        result = services_jurisprudence.create_decision(_admin_id(), data)
    except services_jurisprudence.JurisprudenceError as exc:
        return _handle_jurisprudence_error(exc)
    return jsonify(result), 201


@jurisprudence_bp.route("/api/admin/jurisprudence/<int:decision_id>", methods=["PUT"])
@require_role("admin")
def admin_update_decision(decision_id):
    data = _admin_form_or_json()
    try:
        result = services_jurisprudence.update_decision(
            _admin_id(), decision_id, data
        )
    except services_jurisprudence.JurisprudenceError as exc:
        return _handle_jurisprudence_error(exc)
    return jsonify(result), 200


@jurisprudence_bp.route("/api/admin/jurisprudence/<int:decision_id>", methods=["DELETE"])
@require_role("admin")
def admin_delete_decision(decision_id):
    try:
        result = services_jurisprudence.delete_decision(_admin_id(), decision_id)
    except services_jurisprudence.JurisprudenceError as exc:
        return _handle_jurisprudence_error(exc)
    return jsonify(result), 200


@jurisprudence_bp.route("/api/admin/jurisprudence/<int:decision_id>/publish", methods=["POST"])
@require_role("admin")
def admin_publish_decision(decision_id):
    data = _admin_form_or_json()
    try:
        result = services_jurisprudence.set_published(
            _admin_id(), decision_id, data.get("published", True)
        )
    except services_jurisprudence.JurisprudenceError as exc:
        return _handle_jurisprudence_error(exc)
    return jsonify(result), 200


@jurisprudence_bp.route("/api/admin/jurisprudence/categories", methods=["GET"])
@require_role("admin")
def admin_list_categories():
    return jsonify(services_jurisprudence.list_categories())


@jurisprudence_bp.route("/api/admin/jurisprudence/categories", methods=["POST"])
@require_role("admin")
def admin_create_category():
    data = _admin_form_or_json()
    try:
        result = services_jurisprudence.create_category(_admin_id(), data)
    except services_jurisprudence.JurisprudenceError as exc:
        return _handle_jurisprudence_error(exc)
    return jsonify(result), 201


@jurisprudence_bp.route("/api/admin/jurisprudence/categories/<int:category_id>", methods=["PUT"])
@require_role("admin")
def admin_update_category(category_id):
    data = _admin_form_or_json()
    try:
        result = services_jurisprudence.update_category(
            _admin_id(), category_id, data
        )
    except services_jurisprudence.JurisprudenceError as exc:
        return _handle_jurisprudence_error(exc)
    return jsonify(result), 200


@jurisprudence_bp.route("/api/admin/jurisprudence/categories/<int:category_id>", methods=["DELETE"])
@require_role("admin")
def admin_delete_category(category_id):
    try:
        result = services_jurisprudence.delete_category(_admin_id(), category_id)
    except services_jurisprudence.JurisprudenceError as exc:
        return _handle_jurisprudence_error(exc)
    return jsonify(result), 200