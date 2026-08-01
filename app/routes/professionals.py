"""
مسارات النظام البيئي المهني (Blueprint) — المرحلة 5 (قرار D-023).

التصفح العام (GET /api/professionals + /<id>) يعرض الملفات verified فقط
(فرض عند مستوى الاستعلام — لا يمكن تجاوزه عبر API مباشر)؛ إنشاء/تحديث
الملف ورفع وثيقة التحقق بمصادقة ودور مهني غير مرفوض؛ التقييمات لأي مستخدم
نشط مسجَّل (مراجعة واحدة لكل مقيِّم، upsert، بلا تقييم ذاتي). نقاط النهاية
رفيعة: كل المنطق والتحقق في services_professionals.
"""
from flask import Blueprint, jsonify, request

from .. import services_professionals
from ..middleware.auth_middleware import require_auth
from ..services_professionals import ProfessionalError

professionals_bp = Blueprint("professionals", __name__)


def _handle_error(exc: ProfessionalError):
    return jsonify({"error": exc.message}), exc.status_code


def _clamp_limit(value, default=20):
    try:
        return max(1, min(int(value), 100))
    except (TypeError, ValueError):
        return default


def _clamp_offset(value):
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


@professionals_bp.route("/api/professionals", methods=["GET"])
def list_professionals():
    try:
        result = services_professionals.list_professionals(
            profession_type=request.args.get("type"),
            specialty=request.args.get("specialty"),
            city=request.args.get("city"),
            limit=_clamp_limit(request.args.get("limit")),
            offset=_clamp_offset(request.args.get("offset")),
        )
    except ProfessionalError as exc:
        return _handle_error(exc)
    return jsonify(result), 200


@professionals_bp.route("/api/professionals/<int:profile_id>", methods=["GET"])
def professional_detail(profile_id):
    data = services_professionals.get_profile_public(profile_id)
    if not data:
        return jsonify({"error": "الملف المهني غير موجود."}), 404
    return jsonify(data), 200


@professionals_bp.route("/api/professionals/profile", methods=["POST"])
@require_auth
def upsert_profile():
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = services_professionals.upsert_profile(request.user.id, data)
    except ProfessionalError as exc:
        return _handle_error(exc)
    return jsonify(result), 201


@professionals_bp.route("/api/professionals/verify-document", methods=["POST"])
@require_auth
def verify_document():
    file = request.files.get("document")
    if file is None or not (file.filename or "").strip():
        return jsonify({"error": "الرجاء رفع ملف باسم document."}), 400
    try:
        result = services_professionals.upload_verification_document(
            request.user.id, file
        )
    except ProfessionalError as exc:
        return _handle_error(exc)
    return jsonify(result), 200


@professionals_bp.route("/api/professionals/<int:profile_id>/reviews", methods=["POST"])
@require_auth
def add_review(profile_id):
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = services_professionals.add_review(
            request.user.id, profile_id, data.get("rating"), data.get("comment")
        )
    except ProfessionalError as exc:
        return _handle_error(exc)
    return jsonify(result), 201
