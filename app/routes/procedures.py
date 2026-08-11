"""
مسارات مساعد المساطر (Blueprint) — المرحلة 3 (منصة عامة).

التصفح والتفصيل عامان (FR-6.1). تتبع التقدم كان مخصصًا للحسابات؛ بعد
التحول إلى منصة بلا حسابات لا يُخزَّن تقدم شخصي (الخصوصية بالتصميم):
GET progress يعيد تعريف المسطرة فقط، و POST progress يعيد اعترافًا
بدون كتابة سجل شخصي. (وثيقة API: GET /api/procedures،
GET /api/procedures/<slug>.)"""
from flask import Blueprint, jsonify, request

from .. import services_procedures

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


@procedures_bp.route("/api/procedures/<slug>/progress", methods=["GET"])
def get_progress(slug):
    return jsonify({
        "procedure_slug": slug,
        "progress": [],
        "message": "منصة عامة — لا تتبع تقدم شخصي",
    })


@procedures_bp.route("/api/procedures/<slug>/progress", methods=["POST"])
def set_progress(slug):
    return jsonify({
        "message": "منصة عامة — لا يُحفظ تقدم شخصي",
        "progress": [],
    }), 200
