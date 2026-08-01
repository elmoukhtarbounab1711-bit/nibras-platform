"""
مسارات مساعد المساطر (Blueprint) — المرحلة 3.

التصفح والتفصيل عامان (FR-6.1)، وتحديث التقدم يتطلب مصادقة (FR-6.2 —
للمسجّلين فقط) وفق وثيقة API: GET /api/procedures، GET /api/procedures/<slug>،
POST /api/procedures/<slug>/progress.
"""
from flask import Blueprint, jsonify, request

from .. import services_procedures
from ..middleware.auth_middleware import require_auth
from ..services_procedures import ProcedureError

procedures_bp = Blueprint("procedures", __name__)


@procedures_bp.route("/api/procedures", methods=["GET"])
def list_procedures():
    category = request.args.get("category")
    return jsonify(services_procedures.list_procedures(category=category))


@procedures_bp.route("/api/procedures/<slug>", methods=["GET"])
def get_procedure(slug):
    proc = services_procedures.get_procedure(slug)
    if not proc:
        return jsonify({"error": "المسطرة غير موجودة"}), 404
    return jsonify(proc)


@procedures_bp.route("/api/procedures/<slug>/progress", methods=["POST"])
@require_auth
def set_progress(slug):
    data = request.get_json(force=True, silent=True) or {}
    step_number = data.get("step_number")
    if not isinstance(step_number, int) or isinstance(step_number, bool) or step_number < 1:
        return jsonify({"error": "step_number يجب أن يكون رقم خطوة صحيحًا موجبًا"}), 400
    completed = bool(data.get("completed", True))
    try:
        progress = services_procedures.set_step_progress(
            request.user.id, slug, step_number, completed
        )
    except ProcedureError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify({"message": "تم تحديث تقدمك في المسطرة", "progress": progress}), 200
