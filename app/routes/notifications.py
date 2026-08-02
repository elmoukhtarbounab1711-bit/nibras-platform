"""
مسارات الإشعارات (Blueprint) — المرحلة 12 (قرار D-030).

قراءة الإشعارات الخاصة بصاحب الحساب فقط (require_auth): قائمة مرتَّبة
(الأحدث أولًا) مع عدد غير المقروء، عداد سريع للشارة، تعليم مقروء منفردًا
أو كلها. الإشعارات تُنشأ تلقائيًا من محفِّزات خدمات التحقق والمجتمع
والإشراف — لا نقطة إنشاء يدوية هنا.
"""
from flask import Blueprint, jsonify, request

from .. import services_notifications
from ..middleware.auth_middleware import require_auth
from ..services_notifications import NotificationError

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.route("/api/notifications", methods=["GET"])
@require_auth
def list_my_notifications():
    try:
        limit = int(request.args.get("limit") or 0)
        offset = int(request.args.get("offset") or 0)
    except ValueError:
        return jsonify({"error": "limit/offset يجب أن تكون أرقامًا."}), 400
    unread_only = request.args.get("unread", "0") in ("1", "true", "True")
    result = services_notifications.list_notifications(
        request.user.id,
        limit=limit,
        offset=offset,
        unread_only=unread_only,
    )
    return jsonify(result)


@notifications_bp.route("/api/notifications/unread-count", methods=["GET"])
@require_auth
def unread_count():
    return jsonify({
        "unread_count": services_notifications.unread_count(request.user.id)
    })


@notifications_bp.route(
    "/api/notifications/<int:notification_id>/read", methods=["POST"]
)
@require_auth
def mark_read(notification_id):
    try:
        item = services_notifications.mark_read(
            request.user.id, notification_id
        )
    except NotificationError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify(item)


@notifications_bp.route("/api/notifications/read-all", methods=["POST"])
@require_auth
def mark_all_read():
    marked = services_notifications.mark_all_read(request.user.id)
    return jsonify({"marked": marked})
