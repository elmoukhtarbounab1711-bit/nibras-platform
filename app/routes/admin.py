"""
المسارات الإدارية (Blueprint) — المرحلة 2 (لوحة الإدارة).

محمية بالكامل بمصادقة JWT + دور admin (وثيقة المصادقة §2.4/§2.5).
نقاط النهاية رفيعة: تُفوَّض المنطق والتحقق وتدقيق كل إجراء إلى طبقة
الخدمة services_admin (وثيقة الأمان §3/§5/§8). شكل الاستجابة للعمليات
المعدِّلة: {id, message} وفق اصطلاحات وثيقة API.
"""
from flask import Blueprint, jsonify, request, send_file

from .. import (
    services_admin,
    services_analytics,
    services_marketplace,
)
from ..middleware.auth_middleware import require_role
from ..services_admin import AdminError
from ..services_marketplace import MarketplaceError

admin_bp = Blueprint("admin", __name__)


def _handle_admin_error(exc: AdminError):
    return jsonify({"error": exc.message}), exc.status_code


def _handle_marketplace_error(exc: MarketplaceError):
    return jsonify({"error": exc.message}), exc.status_code


def _admin_form_or_json() -> dict:
    """حقول نصية من multipart (إنشاء/تحديث قوالب) أو من JSON — نمط موحَّد."""
    if request.form:
        return request.form
    return request.get_json(force=True, silent=True) or {}


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


@admin_bp.route("/api/admin/verification/<int:user_id>/document", methods=["GET"])
@require_role("admin")
def verification_document(user_id):
    """تنزيل وثيقة التحقق المخزنة — دور admin فقط (قرار D-023)."""
    try:
        path, name, content_type = services_admin.get_verification_document(user_id)
    except AdminError as exc:
        return _handle_admin_error(exc)
    return send_file(
        path, mimetype=content_type, as_attachment=True, download_name=name
    )


@admin_bp.route("/api/admin/moderation-queue", methods=["GET"])
@require_role("admin")
def moderation_queue():
    """بلاغات الإشراف المفتوحة (مجتمع + ملفات مهنية) — قرار D-024."""
    return jsonify({"reports": services_admin.list_moderation_queue()}), 200


@admin_bp.route("/api/admin/moderation/<int:report_id>/action", methods=["POST"])
@require_role("admin")
def moderation_action(report_id):
    """dismiss|hide|remove على بلاغ مفتوح، مع تسجيل تدقيقي (وثيقة 16 §3)."""
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = services_admin.moderate_report(
            _admin_id(), report_id, data.get("action")
        )
    except AdminError as exc:
        return _handle_admin_error(exc)
    return jsonify(result), 200


# ---------------------------------------------------------------------------
# سوق القوالب (المرحلة 7 — قرار D-025، وثيقة 19 §6 / Admin Panel §3):
# إدارة فئات وقوالب الكتالوج مع رفع/تنزيل الملف. الشراء مؤجَّل لحسم بوابة
# الدفع (BRD §5). كل إجراء يُسجَّل في admin_audit_log (Security §8).
# ---------------------------------------------------------------------------

@admin_bp.route("/api/admin/marketplace/categories", methods=["POST"])
@require_role("admin")
def marketplace_create_category():
    data = request.get_json(force=True, silent=True) or {}
    try:
        new_id = services_marketplace.create_category(_admin_id(), data)
    except MarketplaceError as exc:
        return _handle_marketplace_error(exc)
    return jsonify({"id": new_id, "message": "تم إنشاء فئة السوق."}), 201


@admin_bp.route("/api/admin/marketplace/categories/<int:category_id>",
                methods=["PUT"])
@require_role("admin")
def marketplace_update_category(category_id):
    data = request.get_json(force=True, silent=True) or {}
    try:
        services_marketplace.update_category(_admin_id(), category_id, data)
    except MarketplaceError as exc:
        return _handle_marketplace_error(exc)
    return jsonify({"id": category_id, "message": "تم تحديث فئة السوق."}), 200


@admin_bp.route("/api/admin/marketplace/categories/<int:category_id>",
                methods=["DELETE"])
@require_role("admin")
def marketplace_delete_category(category_id):
    try:
        services_marketplace.delete_category(_admin_id(), category_id)
    except MarketplaceError as exc:
        return _handle_marketplace_error(exc)
    return jsonify({"id": category_id, "message": "تم حذف فئة السوق."}), 200


@admin_bp.route("/api/admin/marketplace/templates", methods=["GET"])
@require_role("admin")
def marketplace_list_templates():
    return jsonify({
        "templates": services_marketplace.list_templates_admin(),
    }), 200


@admin_bp.route("/api/admin/marketplace/templates", methods=["POST"])
@require_role("admin")
def marketplace_create_template():
    file = request.files.get("file")
    if file is None or not (file.filename or "").strip():
        return jsonify({"error": "الرجاء رفع ملف القالب باسم file."}), 400
    try:
        result = services_marketplace.create_template(
            _admin_id(), _admin_form_or_json(), file
        )
    except MarketplaceError as exc:
        return _handle_marketplace_error(exc)
    return jsonify(result), 201


@admin_bp.route("/api/admin/marketplace/templates/<int:template_id>",
                methods=["PUT"])
@require_role("admin")
def marketplace_update_template(template_id):
    file = request.files.get("file")
    try:
        result = services_marketplace.update_template(
            _admin_id(), template_id, _admin_form_or_json(), file
        )
    except MarketplaceError as exc:
        return _handle_marketplace_error(exc)
    return jsonify(result), 200


@admin_bp.route("/api/admin/marketplace/templates/<int:template_id>",
                methods=["DELETE"])
@require_role("admin")
def marketplace_delete_template(template_id):
    try:
        result = services_marketplace.delete_template(_admin_id(), template_id)
    except MarketplaceError as exc:
        return _handle_marketplace_error(exc)
    return jsonify(result), 200


@admin_bp.route("/api/admin/marketplace/templates/<int:template_id>/file",
                methods=["GET"])
@require_role("admin")
def marketplace_template_file(template_id):
    """تنزيل ملف القالب — دور admin فقط (بلا تنزيل عام حتى الشراء)."""
    try:
        path, name, content_type = services_marketplace.get_template_file(
            template_id
        )
    except MarketplaceError as exc:
        return _handle_marketplace_error(exc)
    return send_file(
        path, mimetype=content_type, as_attachment=True, download_name=name
    )


# ---------------------------------------------------------------------------
# لوحة التحليلات الإدارية (المرحلة 8 — قرار D-026، Admin Panel §3.6 /
# Functional Spec §12): ملخص قراءة-فقط من جداول الوحدات القائمة. التحويل
# والإيرادات صفرية مؤجَّلة مع الفوترة (BRD §5).
# ---------------------------------------------------------------------------

@admin_bp.route("/api/admin/analytics/summary", methods=["GET"])
@require_role("admin")
def analytics_summary():
    return jsonify(services_analytics.summary()), 200
