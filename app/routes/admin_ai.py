"""
المسارات الإدارية لمزوّدي الذكاء الاصطناعي (Blueprint) — D-021 المحسَّن.

إدارة المزوّدات من لوحة التحكم: عرض/إنشاء/تحديث/حذف، تعيين الافتراضي،
واختبار اتصال حقيقي. كلها محمية بدور admin. المفتاح لا يُعاد كشفه عبر API.
"""
from flask import Blueprint, jsonify, request

from .. import services_ai
from ..middleware.auth_middleware import require_role
from ..services_ai import AIProviderError

admin_ai_bp = Blueprint("admin_ai", __name__)


@admin_ai_bp.route("/api/admin/ai/providers", methods=["GET"])
@require_role("admin")
def list_providers():
    try:
        return jsonify({"providers": services_ai.list_providers()}), 200
    except AIProviderError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@admin_ai_bp.route("/api/admin/ai/providers/catalog", methods=["GET"])
@require_role("admin")
def catalog():
    try:
        return jsonify({"catalog": services_ai.FREE_CATALOG}), 200
    except AIProviderError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@admin_ai_bp.route("/api/admin/ai/providers", methods=["POST"])
@require_role("admin")
def create_provider():
    try:
        res = services_ai.create_provider(request.get_json(silent=True) or {})
    except AIProviderError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify(res), 201


@admin_ai_bp.route("/api/admin/ai/providers/<int:pid>", methods=["PUT"])
@require_role("admin")
def update_provider(pid: int):
    try:
        res = services_ai.update_provider(pid, request.get_json(silent=True) or {})
    except AIProviderError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify(res), 200


@admin_ai_bp.route("/api/admin/ai/providers/<int:pid>", methods=["DELETE"])
@require_role("admin")
def delete_provider(pid: int):
    try:
        res = services_ai.delete_provider(pid)
    except AIProviderError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify(res), 200


@admin_ai_bp.route("/api/admin/ai/providers/<int:pid>/default", methods=["POST"])
@require_role("admin")
def set_default(pid: int):
    try:
        res = services_ai.set_default_provider(pid)
    except AIProviderError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify(res), 200


@admin_ai_bp.route("/api/admin/ai/providers/test", methods=["POST"])
@require_role("admin")
def test_provider():
    try:
        res = services_ai.test_provider(request.get_json(silent=True) or {})
    except AIProviderError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify(res), 200
