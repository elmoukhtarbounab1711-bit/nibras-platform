"""
مسارات الهوية (Blueprint) — منصة عامة بلا حسابات مستخدمين (تحوّل أمني).

نُزيل نقاط المصادقة العامة: التسجيل والدخول وتسجيل الخروج وملف المستخدم
واستعادة كلمة المرور للجمهور. لا حسابات زوار. الوصول الإداري (admin) لا
يمر عبر هذه النقاط العامة — يُدار حصريًا عبر السكربت الداخلي
app.create_admin وتوقيع التوكنات الداخلي للوحة الإدارة. (وثيقة 12.)
"""
import time

from flask import Blueprint, jsonify, request

from .. import config
from ..middleware.auth_middleware import require_auth

auth_bp = Blueprint("auth", __name__)

# حد معدل في الذاكرة لكل عنوان IP — يحمي النقاط الحساسة عند إعادة التفعيل
_attempts = {}


def _rate_limited(key: str) -> bool:
    now = time.time()
    window = config.RATE_LIMIT_WINDOW_SECONDS
    bucket = _attempts.setdefault(key, [])
    bucket[:] = [t for t in bucket if now - t < window]
    if len(bucket) >= config.RATE_LIMIT_MAX_ATTEMPTS:
        return True
    bucket.append(now)
    return False


@auth_bp.route("/api/auth/register", methods=["POST"])
def register():
    client = request.remote_addr or "unknown"
    if _rate_limited(f"auth:{client}"):
        return jsonify({"error": "طلبات كثيرة جدًا. حاول لاحقًا."}), 429
    return jsonify({"error": "التسجيل متاح فقط عبر إدارة النظام."}), 403


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    client = request.remote_addr or "unknown"
    if _rate_limited(f"auth:{client}"):
        return jsonify({"error": "طلبات كثيرة جدًا. حاول لاحقًا."}), 429
    return jsonify({"error": "الدخول متاح فقط عبر لوحة الإدارة الداخلية."}), 403


@auth_bp.route("/api/auth/refresh", methods=["POST"])
def refresh():
    client = request.remote_addr or "unknown"
    if _rate_limited(f"auth:{client}"):
        return jsonify({"error": "طلبات كثيرة جدًا. حاول لاحقًا."}), 429
    return jsonify({"error": "تحديث التوكن غير متاح للجمهور."}), 403


@auth_bp.route("/api/auth/logout", methods=["POST"])
def logout():
    return jsonify({"message": "تم تسجيل الخروج"}), 200


@auth_bp.route("/api/auth/me", methods=["GET"])
@require_auth
def me():
    return jsonify({"user": request.user.to_dict()}), 200


@auth_bp.route("/api/auth/password-reset/request", methods=["POST"])
def password_reset_request():
    client = request.remote_addr or "unknown"
    if _rate_limited(f"auth:{client}"):
        return jsonify({"error": "طلبات كثيرة جدًا. حاول لاحقًا."}), 429
    return jsonify({"error": "استعادة كلمة المرور للجمهور غير متاحة."}), 403


@auth_bp.route("/api/auth/password-reset/confirm", methods=["POST"])
def password_reset_confirm():
    client = request.remote_addr or "unknown"
    if _rate_limited(f"auth:{client}"):
        return jsonify({"error": "طلبات كثيرة جدًا. حاول لاحقًا."}), 429
    return jsonify({"error": "استعادة كلمة المرور للجمهور غير متاحة."}), 403
