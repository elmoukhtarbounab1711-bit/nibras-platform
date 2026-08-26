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
    services_ads,
    services_analytics,
    services_blog,
    services_comparative,
    services_ingestion,
    services_marketplace,
    services_notifications,
    services_tenants,
)
from ..middleware.auth_middleware import require_role
from ..services_admin import AdminError
from ..services_ads import AdError
from ..services_blog import BlogError
from ..services_comparative import ComparativeError
from ..services_ingestion import IngestionError
from ..services_marketplace import MarketplaceError
from ..services_procedures import ProcedureError
from ..services_tenants import TenantError

admin_bp = Blueprint("admin", __name__)


def _handle_admin_error(exc: AdminError):
    return jsonify({"error": exc.message}), exc.status_code


def _handle_ad_error(exc: AdError):
    return jsonify({"error": exc.message}), exc.status_code


def _handle_marketplace_error(exc: MarketplaceError):
    return jsonify({"error": exc.message}), exc.status_code


def _handle_ingestion_error(exc: IngestionError):
    return jsonify({"error": exc.message}), exc.status_code


def _handle_blog_error(exc: BlogError):
    return jsonify({"error": exc.message}), exc.status_code


def _handle_procedure_error(exc: ProcedureError):
    return jsonify({"error": exc.message}), exc.status_code


def _handle_comparative_error(exc: ComparativeError):
    return jsonify({"error": exc.message}), exc.status_code


def _handle_jurisprudence_error(exc):
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


@admin_bp.route("/api/admin/texts/bulk-delete", methods=["POST"])
@require_role("admin")
def delete_texts_bulk():
    """حذف جماعي لنصوص قانونية — المرحلة 15 (D-033). الحمولة: {ids: [...]}."""
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = services_admin.bulk_delete_texts(_admin_id(), data.get("ids"))
    except AdminError as exc:
        return _handle_admin_error(exc)
    return jsonify(result), 200


@admin_bp.route("/api/admin/texts/bulk-update", methods=["POST"])
@require_role("admin")
def update_texts_bulk():
    """تحديث جماعي بحقول مشتركة — المرحلة 15 (D-033).

    الحمولة: {ids: [...], ...الحقول} — تُطبَّق نفس الحقول على كل النصوص."""
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = services_admin.bulk_update_texts(
            _admin_id(), data.get("ids"), {k: v for k, v in data.items() if k != "ids"}
        )
    except AdminError as exc:
        return _handle_admin_error(exc)
    return jsonify(result), 200


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


@admin_bp.route("/api/admin/articles/bulk-delete", methods=["POST"])
@require_role("admin")
def delete_articles_bulk():
    """حذف جماعي لمواد قانونية — المرحلة 15 (D-033). الحمولة: {ids: [...]}."""
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = services_admin.bulk_delete_articles(_admin_id(), data.get("ids"))
    except AdminError as exc:
        return _handle_admin_error(exc)
    return jsonify(result), 200


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


@admin_bp.route("/api/admin/verification/bulk", methods=["POST"])
@require_role("admin")
def verification_bulk():
    """قبول/رفض جماعي لطلبات التحقق — المرحلة 15 (D-033).

    الحمولة: {action: approve|reject, user_ids: [...], reason?: str}.
    يُعالَج كل عنصر في معاملة واحدة؛ النجاح الجزئي مع تقرير لكل معرّف."""
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = services_admin.bulk_verification(
            _admin_id(),
            data.get("action"),
            data.get("user_ids"),
            data.get("reason"),
        )
    except AdminError as exc:
        return _handle_admin_error(exc)
    return jsonify(result), 200


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


@admin_bp.route("/api/admin/moderation/bulk", methods=["POST"])
@require_role("admin")
def moderation_bulk():
    """معالجة جماعية لبلاغات الإشراف — المرحلة 15 (D-033).

    الحمولة: {action: dismiss|hide|remove, report_ids: [...]}.
    يُعالَج كل بلاغ في معاملة واحدة مع تقرير لكل معرّف."""
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = services_admin.bulk_moderation(
            _admin_id(), data.get("action"), data.get("report_ids")
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


@admin_bp.route("/api/admin/marketplace/templates/bulk-delete", methods=["POST"])
@require_role("admin")
def marketplace_delete_templates_bulk():
    """حذف جماعي للقوالب (مع إزالة الملفات) — المرحلة 15 (D-033).

    الحمولة: {ids: [...]} — قالب له سجل شراءات يُسجَّل فشلًا جزئيًا."""
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = services_marketplace.delete_templates_bulk(
            _admin_id(), data.get("ids")
        )
    except MarketplaceError as exc:
        return _handle_marketplace_error(exc)
    return jsonify(result), 200


# ---------------------------------------------------------------------------
# لوحة التحليلات الإدارية (المرحلة 8 — قرار D-026، Admin Panel §3.6 /
# Functional Spec §12): ملخص قراءة-فقط من جداول الوحدات القائمة. التحويل
# والإيرادات صفرية مؤجَّلة مع الفوترة (BRD §5).
# ---------------------------------------------------------------------------

@admin_bp.route("/api/admin/analytics/summary", methods=["GET"])
@require_role("admin")
def analytics_summary():
    return jsonify(services_analytics.summary()), 200


# ---------------------------------------------------------------------------
# نظام الإعلانات (المرحلة 9 — قرار D-027، وثيقة 15 §4/§6 + Admin Panel §3.5):
# إدارة الحملات (إنشاء/تعديل/حذف) + فتحات + إحصائيات كل حملة (انطباعات/
# نقرات/CTR). كل إجراء يُسجَّل في admin_audit_log (Security §8).
# ---------------------------------------------------------------------------

@admin_bp.route("/api/admin/ads/slots", methods=["GET"])
@require_role("admin")
def ads_list_slots():
    return jsonify({"slots": services_ads.list_slots()}), 200


@admin_bp.route("/api/admin/ads/campaigns", methods=["GET"])
@require_role("admin")
def ads_list_campaigns():
    return jsonify({"campaigns": services_ads.list_campaigns_admin()}), 200


@admin_bp.route("/api/admin/ads/campaigns", methods=["POST"])
@require_role("admin")
def ads_create_campaign():
    data = request.get_json(force=True, silent=True) or {}
    try:
        new_id = services_ads.create_campaign(_admin_id(), data)
    except AdError as exc:
        return _handle_ad_error(exc)
    return jsonify({"id": new_id, "message": "تم إنشاء الحملة."}), 201


@admin_bp.route("/api/admin/ads/campaigns/<int:campaign_id>", methods=["PUT"])
@require_role("admin")
def ads_update_campaign(campaign_id):
    data = request.get_json(force=True, silent=True) or {}
    try:
        services_ads.update_campaign(_admin_id(), campaign_id, data)
    except AdError as exc:
        return _handle_ad_error(exc)
    return jsonify({"id": campaign_id, "message": "تم تحديث الحملة."}), 200


@admin_bp.route("/api/admin/ads/campaigns/<int:campaign_id>", methods=["DELETE"])
@require_role("admin")
def ads_delete_campaign(campaign_id):
    try:
        services_ads.delete_campaign(_admin_id(), campaign_id)
    except AdError as exc:
        return _handle_ad_error(exc)
    return jsonify({"id": campaign_id, "message": "تم حذف الحملة."}), 200


@admin_bp.route("/api/admin/ads/campaigns/bulk-status", methods=["POST"])
@require_role("admin")
def ads_campaigns_bulk_status():
    """تغيير حالة جماعي للحملات — المرحلة 15 (D-033).

    الحمولة: {ids: [...], status: active|paused|ended}."""
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = services_ads.set_campaign_status_bulk(
            _admin_id(), data.get("ids"), data.get("status")
        )
    except AdError as exc:
        return _handle_ad_error(exc)
    return jsonify(result), 200


# ---------------------------------------------------------------------------
# إدارة المزوّدين الإعلانيين (Security §7)
# ---------------------------------------------------------------------------

@admin_bp.route("/api/admin/ads/providers", methods=["GET"])
@require_role("admin")
def ads_list_providers():
    return jsonify({"providers": services_ads.list_providers()}), 200


@admin_bp.route("/api/admin/ads/providers", methods=["POST"])
@require_role("admin")
def ads_create_provider():
    data = request.get_json(force=True, silent=True) or {}
    try:
        new_id = services_ads.create_provider(_admin_id(), data)
    except AdError as exc:
        return _handle_ad_error(exc)
    return jsonify({"id": new_id, "message": "تم إنشاء المزوّد."}), 201


@admin_bp.route("/api/admin/ads/providers/<int:provider_id>", methods=["PUT"])
@require_role("admin")
def ads_update_provider(provider_id):
    data = request.get_json(force=True, silent=True) or {}
    try:
        services_ads.update_provider(_admin_id(), provider_id, data)
    except AdError as exc:
        return _handle_ad_error(exc)
    return jsonify({"id": provider_id, "message": "تم تحديث المزوّد."}), 200


@admin_bp.route("/api/admin/ads/providers/<int:provider_id>", methods=["DELETE"])
@require_role("admin")
def ads_delete_provider(provider_id):
    try:
        services_ads.delete_provider(_admin_id(), provider_id)
    except AdError as exc:
        return _handle_ad_error(exc)
    return jsonify({"id": provider_id, "message": "تم حذف المزوّد."}), 200


@admin_bp.route("/api/admin/ads/providers/bulk-status", methods=["POST"])
@require_role("admin")
def ads_providers_bulk_status():
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = services_ads.set_provider_status_bulk(
            _admin_id(), data.get("ids"), data.get("enabled", True)
        )
    except AdError as exc:
        return _handle_ad_error(exc)
    return jsonify(result), 200


# ---------------------------------------------------------------------------
# ربط المزوّد بالفتحة
# ---------------------------------------------------------------------------

@admin_bp.route("/api/admin/ads/slots/<int:slot_id>/providers", methods=["GET"])
@require_role("admin")
def ads_slot_providers(slot_id):
    return jsonify({"providers": services_ads.list_slot_providers(slot_id)}), 200


@admin_bp.route("/api/admin/ads/slots/<int:slot_id>/providers", methods=["POST"])
@require_role("admin")
def ads_link_slot_provider(slot_id):
    data = request.get_json(force=True, silent=True) or {}
    try:
        provider_id = int(data.get("provider_id"))
    except (TypeError, ValueError):
        return jsonify({"error": "provider_id مطلوب."}), 400
    try:
        link_id = services_ads.link_provider_to_slot(
            slot_id, provider_id,
            data.get("slot_config", "{}"),
            int(data.get("priority", 0)),
        )
    except AdError as exc:
        return _handle_ad_error(exc)
    return jsonify({"id": link_id, "message": "تم ربط المزوّد بالفتحة."}), 201


@admin_bp.route(
    "/api/admin/ads/slots/<int:slot_id>/providers/<int:provider_id>",
    methods=["DELETE"],
)
@require_role("admin")
def ads_unlink_slot_provider(slot_id, provider_id):
    services_ads.unlink_provider_from_slot(slot_id, provider_id)
    return jsonify({"message": "تم إلغاء الربط."}), 200


# ---------------------------------------------------------------------------
# الإعدادات العامة للإعلانات
# ---------------------------------------------------------------------------

@admin_bp.route("/api/admin/ads/settings", methods=["GET"])
@require_role("admin")
def ads_get_settings():
    return jsonify(services_ads.get_settings()), 200


@admin_bp.route("/api/admin/ads/settings", methods=["PUT"])
@require_role("admin")
def ads_set_setting():
    data = request.get_json(force=True, silent=True) or {}
    key = (data.get("key") or "").strip()
    value = (data.get("value") or "").strip()
    if not key:
        return jsonify({"error": "key مطلوب."}), 400
    try:
        services_ads.set_setting(key, value)
    except AdError as exc:
        return _handle_ad_error(exc)
    return jsonify({"message": "تم حفظ الإعداد."}), 200


# ---------------------------------------------------------------------------
# تسليم الإعلانات للواجهة (API عام)
# ---------------------------------------------------------------------------

@admin_bp.route("/api/ads/slot/<slot_slug>", methods=["GET"])
@require_role("admin")
def ads_serve_slot_api(slot_slug):
    """API عام لجلب مزوّدين فتحة — يستخدمه الواجهة لتحميل السكريبتات."""
    providers = services_ads.serve_slot(slot_slug)
    return jsonify({
        "enabled": services_ads.is_ads_enabled(),
        "providers": providers,
    }), 200


# ---------------------------------------------------------------------------
# محرك رفع المستندات (المرحلة 10 — قرار D-028): استيعاب PDF/DOCX في المكتبة.
# multipart بـ file + حقول النص، مع dry_run=1 لمعاينة التقسيم بلا كتابة.
# الملف لا يُخزَّن؛ يُستخرج نصه ويُفهرس في legal_texts/articles (FTS).
# كل استيعاب مُلتزَم يُسجَّل في admin_audit_log (Security §8).
# ---------------------------------------------------------------------------

@admin_bp.route("/api/admin/ingestion/import", methods=["POST"])
@require_role("admin")
def ingestion_import():
    file = request.files.get("file")
    data = _admin_form_or_json()
    dry_run = str(data.get("dry_run") or "").strip().lower() in (
        "1", "true", "yes", "on"
    )
    try:
        result = services_ingestion.import_document(
            _admin_id(), data, file, dry_run=dry_run
        )
    except IngestionError as exc:
        return _handle_ingestion_error(exc)
    return jsonify(result), (200 if dry_run else 201)


# ---------------------------------------------------------------------------
# تسليم الإشعارات الخارجية (المرحلة 16 — قرار D-034): تفريغ صندوق البريد/الدفع.
# يُستدعى يدويًا (أو عبر سكربت مجدول flush_notifications) — لا شبكة داخل
# طلبات المستخدمين أبدًا. كل تفريغ يُعيد ملخص {processed, sent, failed}.
# ---------------------------------------------------------------------------

@admin_bp.route("/api/admin/notifications/deliver", methods=["POST"])
@require_role("admin")
def notifications_deliver():
    data = request.get_json(force=True, silent=True) or {}
    limit = data.get("limit")
    try:
        result = services_notifications.deliver_pending(
            int(limit) if limit is not None else None
        )
    except ValueError:
        return jsonify({"error": "limit يجب أن يكون رقمًا."}), 400
    return jsonify(result), 200


@admin_bp.route("/api/admin/notifications/delivery-stats", methods=["GET"])
@require_role("admin")
def notifications_delivery_stats():
    return jsonify(services_notifications.delivery_stats()), 200


# ---------------------------------------------------------------------------
# إدارة المستأجرين (المرحلة 17 — قرار D-035): قائمة وإنشاء المستأجرين
# (عزل هوية فقط). كل إنشاء يُسجَّل في admin_audit_log (Security §8).
# ---------------------------------------------------------------------------

@admin_bp.route("/api/admin/tenants", methods=["GET"])
@require_role("admin")
def tenants_list():
    return jsonify({"tenants": services_tenants.list_tenants()}), 200


@admin_bp.route("/api/admin/tenants", methods=["POST"])
@require_role("admin")
def tenants_create():
    data = request.get_json(force=True, silent=True) or {}
    try:
        tenant = services_tenants.create_tenant(
            _admin_id(), data.get("name"), data.get("slug")
        )
    except TenantError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify({"id": tenant["id"], "message": "تم إنشاء المستأجر."}), 201


# ---------------------------------------------------------------------------
# رفع ملف PDF للقوانين (مرحلة الواجهة): يُفضَّل على الملف المولَّد عند العرض
# ---------------------------------------------------------------------------

@admin_bp.route("/api/admin/texts/<int:text_id>/pdf", methods=["POST"])
@require_role("admin")
def text_pdf_upload(text_id):
    file = request.files.get("file")
    if file is None or not (file.filename or "").strip():
        return jsonify({"error": "الرجاء رفع ملف باسم file."}), 400
    try:
        result = services_admin.update_text_pdf(_admin_id(), text_id, file)
    except AdminError as exc:
        return _handle_admin_error(exc)
    return jsonify(result), 200


@admin_bp.route("/api/admin/texts/<int:text_id>/pdf", methods=["DELETE"])
@require_role("admin")
def text_pdf_delete(text_id):
    try:
        result = services_admin.delete_text_pdf(_admin_id(), text_id)
    except AdminError as exc:
        return _handle_admin_error(exc)
    return jsonify(result), 200


# ---------------------------------------------------------------------------
# إدارة المقالات القانونية (بوابة المقالات): قائمة كل الحالات + تغيير الحالة
# ---------------------------------------------------------------------------

@admin_bp.route("/api/admin/blog/articles", methods=["GET"])
@require_role("admin")
def blog_articles_list():
    result = services_blog.list_articles_admin(
        status=request.args.get("status"),
        q=request.args.get("q"),
        limit=int(request.args.get("limit") or 50),
        offset=int(request.args.get("offset") or 0),
    )
    return jsonify({"articles": result})


@admin_bp.route("/api/admin/blog/articles/<int:article_id>/status", methods=["PUT"])
@require_role("admin")
def blog_article_status(article_id):
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = services_blog.set_status(
            _admin_id(), article_id, data.get("status")
        )
    except BlogError as exc:
        return _handle_blog_error(exc)
    return jsonify(result), 200


@admin_bp.route("/api/admin/blog/reports", methods=["GET"])
@require_role("admin")
def blog_reports_list():
    return jsonify({
        "reports": services_blog.list_reports(request.args.get("status"))
    })


@admin_bp.route("/api/admin/blog/reports/<int:report_id>/action", methods=["POST"])
@require_role("admin")
def blog_report_action(report_id):
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = services_blog.action_report(
            _admin_id(), report_id, data.get("decision")
        )
    except BlogError as exc:
        return _handle_blog_error(exc)
    return jsonify(result), 200


# ---------------------------------------------------------------------------
# إدارة المساطر القانونية (مرحلة الواجهة): CRUD بالخطوات والرسوم والأسئلة
# ---------------------------------------------------------------------------

@admin_bp.route("/api/admin/procedures", methods=["GET"])
@require_role("admin")
def procedures_admin_list():
    return jsonify({"procedures": services_admin.list_procedures_admin()})


@admin_bp.route("/api/admin/procedures", methods=["POST"])
@require_role("admin")
def procedures_admin_create():
    data = request.get_json(force=True, silent=True) or {}
    try:
        new_id = services_admin.create_procedure(_admin_id(), data)
    except AdminError as exc:
        return _handle_admin_error(exc)
    return jsonify({"id": new_id, "message": "تم إنشاء المسطرة."}), 201


@admin_bp.route("/api/admin/procedures/<int:procedure_id>", methods=["PUT"])
@require_role("admin")
def procedures_admin_update(procedure_id):
    data = request.get_json(force=True, silent=True) or {}
    try:
        services_admin.update_procedure(_admin_id(), procedure_id, data)
    except AdminError as exc:
        return _handle_admin_error(exc)
    return jsonify({"id": procedure_id, "message": "تم تحديث المسطرة."}), 200


@admin_bp.route("/api/admin/procedures/<int:procedure_id>", methods=["DELETE"])
@require_role("admin")
def procedures_admin_delete(procedure_id):
    try:
        services_admin.delete_procedure(_admin_id(), procedure_id)
    except AdminError as exc:
        return _handle_admin_error(exc)
    return jsonify({"id": procedure_id, "message": "تم حذف المسطرة."}), 200


# ---------------------------------------------------------------------------
# القانون المقارن (المرحلة 20 — D-038): إدارة الولايات القضائية وحالات الدراسات
# ---------------------------------------------------------------------------

@admin_bp.route("/api/admin/comparative/jurisdictions", methods=["GET"])
@require_role("admin")
def comparative_jurisdictions_list():
    return jsonify({
        "jurisdictions": services_comparative.list_jurisdictions()
    }), 200


@admin_bp.route("/api/admin/comparative/jurisdictions", methods=["POST"])
@require_role("admin")
def comparative_jurisdictions_create():
    data = request.get_json(force=True, silent=True) or {}
    try:
        new_id = services_comparative.create_jurisdiction(_admin_id(), data)
    except ComparativeError as exc:
        return _handle_comparative_error(exc)
    return jsonify({"id": new_id, "message": "تم إنشاء النظام القضائي."}), 201


@admin_bp.route("/api/admin/comparative/jurisdictions/<int:jurisdiction_id>",
                methods=["PUT"])
@require_role("admin")
def comparative_jurisdictions_update(jurisdiction_id):
    data = request.get_json(force=True, silent=True) or {}
    try:
        services_comparative.update_jurisdiction(
            _admin_id(), jurisdiction_id, data
        )
    except ComparativeError as exc:
        return _handle_comparative_error(exc)
    return jsonify({
        "id": jurisdiction_id, "message": "تم تحديث النظام القضائي."
    }), 200


@admin_bp.route("/api/admin/comparative/jurisdictions/<int:jurisdiction_id>",
                methods=["DELETE"])
@require_role("admin")
def comparative_jurisdictions_delete(jurisdiction_id):
    try:
        services_comparative.delete_jurisdiction(_admin_id(), jurisdiction_id)
    except ComparativeError as exc:
        return _handle_comparative_error(exc)
    return jsonify({
        "id": jurisdiction_id, "message": "تم حذف النظام القضائي."
    }), 200


@admin_bp.route("/api/admin/comparative/studies", methods=["GET"])
@require_role("admin")
def comparative_studies_list():
    return jsonify({
        "studies": services_comparative.list_studies_admin(
            status=request.args.get("status") or None,
            q=request.args.get("q"),
        ),
    }), 200


@admin_bp.route("/api/admin/comparative/studies/<int:study_id>/status",
                methods=["PUT"])
@require_role("admin")
def comparative_studies_status(study_id):
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = services_comparative.set_study_status(
            _admin_id(), study_id, data.get("status")
        )
    except ComparativeError as exc:
        return _handle_comparative_error(exc)
    return jsonify(result), 200
