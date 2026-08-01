"""
المسارات الإدارية (Blueprint) — المرحلة 2 (لوحة الإدارة).

محمية بالكامل بمصادقة JWT + دور admin (وثيقة المصادقة §2.4/§2.5).
نقاط النهاية رفيعة: تُفوَّض المنطق والتحقق وتدقيق كل إجراء إلى طبقة
الخدمة services_admin (وثيقة الأمان §3/§5/§8). شكل الاستجابة للعمليات
المعدِّلة: {id, message} وفق اصطلاحات وثيقة API.
"""
from flask import Blueprint, jsonify, request

from .. import services_admin
from ..middleware.auth_middleware import require_role
from ..services_admin import AdminError

admin_bp = Blueprint("admin", __name__)


def _handle_admin_error(exc: AdminError):
    return jsonify({"error": exc.message}), exc.status_code


def _admin_id() -> int:
    return request.user.id


@admin_bp.route("/api/admin/texts", methods=["POST"])
@require_role("admin")
def create_text():
    data = request.get_json(force=True, silent=True) or {}
    try:
        new_id = services_admin.create_text(_admin_id(), data)
    except AdminError as exc:
        return _handle_admin_error(exc)
    return jsonify({"id": new_id, "message": "تم إنشاء النص القانوني"}), 201


@admin_bp.route("/api/admin/texts/<int:text_id>", methods=["PUT"])
@require_role("admin")
def update_text(text_id):
    data = request.get_json(force=True, silent=True) or {}
    try:
        services_admin.update_text(_admin_id(), text_id, data)
    except AdminError as exc:
        return _handle_admin_error(exc)
    return jsonify({"id": text_id, "message": "تم تحديث النص القانوني"}), 200


@admin_bp.route("/api/admin/texts/<int:text_id>", methods=["DELETE"])
@require_role("admin")
def delete_text(text_id):
    try:
        services_admin.delete_text(_admin_id(), text_id)
    except AdminError as exc:
        return _handle_admin_error(exc)
    return jsonify({"id": text_id, "message": "تم حذف النص القانوني"}), 200


@admin_bp.route("/api/admin/texts/<int:text_id>/articles", methods=["POST"])
@require_role("admin")
def create_article(text_id):
    data = request.get_json(force=True, silent=True) or {}
    try:
        new_id = services_admin.create_article(_admin_id(), text_id, data)
    except AdminError as exc:
        return _handle_admin_error(exc)
    return jsonify({"id": new_id, "message": "تمت إضافة المادة"}), 201


@admin_bp.route("/api/admin/articles/<int:article_id>", methods=["PUT"])
@require_role("admin")
def update_article(article_id):
    data = request.get_json(force=True, silent=True) or {}
    try:
        services_admin.update_article(_admin_id(), article_id, data)
    except AdminError as exc:
        return _handle_admin_error(exc)
    return jsonify({"id": article_id, "message": "تم تحديث المادة"}), 200


@admin_bp.route("/api/admin/articles/<int:article_id>", methods=["DELETE"])
@require_role("admin")
def delete_article(article_id):
    try:
        services_admin.delete_article(_admin_id(), article_id)
    except AdminError as exc:
        return _handle_admin_error(exc)
    return jsonify({"id": article_id, "message": "تم حذف المادة"}), 200


@admin_bp.route("/api/admin/verification-queue", methods=["GET"])
@require_role("admin")
def verification_queue():
    return jsonify({"requests": services_admin.list_verification_queue()}), 200


@admin_bp.route("/api/admin/verification/<int:user_id>/approve", methods=["POST"])
@require_role("admin")
def verification_approve(user_id):
    try:
        services_admin.approve_verification(_admin_id(), user_id)
    except AdminError as exc:
        return _handle_admin_error(exc)
    return jsonify({"id": user_id, "message": "تم قبول طلب التحقق"}), 200


@admin_bp.route("/api/admin/verification/<int:user_id>/reject", methods=["POST"])
@require_role("admin")
def verification_reject(user_id):
    data = request.get_json(force=True, silent=True) or {}
    try:
        services_admin.reject_verification(_admin_id(), user_id, data.get("reason"))
    except AdminError as exc:
        return _handle_admin_error(exc)
    return jsonify({"id": user_id, "message": "تم رفض طلب التحقق"}), 200
