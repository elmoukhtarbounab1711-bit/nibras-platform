"""
مسارات تحليلات الزوار — API endpoints للوحة التحكم الإدارية.

GET /api/admin/visitors/summary   — إحصائيات عامة
GET /api/admin/visitors/trend     — الاتجاه اليومي
GET /api/admin/visitors/hourly    — التوزيع الساعي
GET /api/admin/visitors/pages     — أكثر الصفحات زيارة
GET /api/admin/visitors/referrers — مصادر الزيارات
GET /api/admin/visitors/browsers  — توزيع المتصفحات
GET /api/admin/visitors/devices   — توزيع الأجهزة
GET /api/admin/visitors/live      — الزوار النشطون الآن
GET /api/admin/visitors/all       — كل التحليلات دفعة واحدة
"""
from flask import Blueprint, jsonify, request

from ..middleware.auth_middleware import require_role
from .. import services_visitors

visitors_bp = Blueprint("visitors", __name__)


@visitors_bp.route("/api/admin/visitors/summary", methods=["GET"])
@require_role("admin")
def visitors_summary():
    days = request.args.get("days", 30, type=int)
    return jsonify(services_visitors.summary_stats(days)), 200


@visitors_bp.route("/api/admin/visitors/trend", methods=["GET"])
@require_role("admin")
def visitors_trend():
    days = request.args.get("days", 30, type=int)
    return jsonify(services_visitors.daily_trend(days)), 200


@visitors_bp.route("/api/admin/visitors/hourly", methods=["GET"])
@require_role("admin")
def visitors_hourly():
    days = request.args.get("days", 7, type=int)
    return jsonify(services_visitors.hourly_distribution(days)), 200


@visitors_bp.route("/api/admin/visitors/pages", methods=["GET"])
@require_role("admin")
def visitors_pages():
    days = request.args.get("days", 30, type=int)
    limit = request.args.get("limit", 20, type=int)
    return jsonify(services_visitors.top_pages(limit, days)), 200


@visitors_bp.route("/api/admin/visitors/referrers", methods=["GET"])
@require_role("admin")
def visitors_referrers():
    days = request.args.get("days", 30, type=int)
    return jsonify(services_visitors.referrer_sources(days)), 200


@visitors_bp.route("/api/admin/visitors/browsers", methods=["GET"])
@require_role("admin")
def visitors_browsers():
    days = request.args.get("days", 30, type=int)
    return jsonify(services_visitors.browser_stats(days)), 200


@visitors_bp.route("/api/admin/visitors/devices", methods=["GET"])
@require_role("admin")
def visitors_devices():
    days = request.args.get("days", 30, type=int)
    return jsonify(services_visitors.device_stats(days)), 200


@visitors_bp.route("/api/admin/visitors/os", methods=["GET"])
@require_role("admin")
def visitors_os():
    days = request.args.get("days", 30, type=int)
    return jsonify(services_visitors.os_stats(days)), 200


@visitors_bp.route("/api/admin/visitors/live", methods=["GET"])
@require_role("admin")
def visitors_live():
    return jsonify(services_visitors.live_visitors()), 200


@visitors_bp.route("/api/admin/visitors/all", methods=["GET"])
@require_role("admin")
def visitors_all():
    days = request.args.get("days", 30, type=int)
    return jsonify(services_visitors.full_analytics(days)), 200


@visitors_bp.route("/api/admin/visitors/track", methods=["POST"])
def visitors_track():
    """نقطة تتبع الزوار من الواجهة الأمامية (public)."""
    from flask import request as req
    data = req.get_json(force=True, silent=True) or {}
    services_visitors.track_request(
        path=data.get("path", req.path),
        ip=req.remote_addr or "unknown",
        user_agent=req.headers.get("User-Agent", ""),
        referrer=req.headers.get("Referer", ""),
        user_id=data.get("user_id"),
        method=data.get("method", "GET"),
        status_code=data.get("status_code", 200),
        duration_ms=data.get("duration_ms", 0),
    )
    return jsonify({"ok": True}), 202
