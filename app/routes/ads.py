"""
مسارات نظام الإعلانات (Blueprint) — المرحلة 9 (قرار D-027).

خدمة عامة GET /api/ads/serve?slot= تعيد الحملة النشطة للفتحة (أو null) بلا
أي كتابة — الترويستة لا تلمس منطق الصفحة (وثيقة 15 §2)، والتتبع بنقطتين
منفصلتين (انطباع/نقرة — §6) بمصادقة اختيارية وحد معدل خفيف لمنع تضخيم
الإحصائيات. إدارة الحملات (دور admin) في routes/admin.py.
"""
import time

from flask import Blueprint, jsonify, request

from .. import config, services_ads
from ..middleware.auth_middleware import optional_auth
from ..services_ads import AdError

ads_bp = Blueprint("ads", __name__)

# حد معدل أحداث التتبع في الذاكرة لكل مفتاح (مستخدم نشط أو عنوان IP)
_attempts = {}


def _rate_limited(key: str) -> bool:
    now = time.time()
    window = config.AD_RATE_LIMIT_WINDOW_SECONDS
    bucket = _attempts.setdefault(key, [])
    bucket[:] = [t for t in bucket if now - t < window]
    if len(bucket) >= config.AD_RATE_LIMIT_MAX_REQUESTS:
        return True
    bucket.append(now)
    return False


def _client_key(prefix: str) -> str:
    user = getattr(request, "user", None)
    ident = user.id if user else (request.remote_addr or "unknown")
    return f"{prefix}:{ident}"


def _viewer_id():
    user = getattr(request, "user", None)
    return user.id if user else None


def _handle_ad_error(exc: AdError):
    return jsonify({"error": exc.message}), exc.status_code


@ads_bp.route("/api/ads/serve", methods=["GET"])
def serve():
    slot = request.args.get("slot", "").strip()
    if not slot:
        return jsonify({"error": "معامل slot مطلوب."}), 400
    try:
        campaign = services_ads.serve(slot)
    except AdError as exc:
        return _handle_ad_error(exc)
    return jsonify({"campaign": campaign}), 200


@ads_bp.route("/api/ads/<int:campaign_id>/impression", methods=["POST"])
@optional_auth
def impression(campaign_id):
    return _track(campaign_id, "impression")


@ads_bp.route("/api/ads/<int:campaign_id>/click", methods=["POST"])
@optional_auth
def click(campaign_id):
    return _track(campaign_id, "click")


def _track(campaign_id: int, event_type: str):
    if _rate_limited(_client_key(f"ads:{event_type}")):
        return jsonify({"error": "طلبات كثيرة جدًا. حاول لاحقًا."}), 429
    try:
        services_ads.log_event(campaign_id, event_type, _viewer_id())
    except AdError as exc:
        return _handle_ad_error(exc)
    return jsonify({"ok": True}), 201
