"""
مسارات الهوية (Blueprint) — منصة عامة بلا حسابات مستخدمين (تحوّل أمني).

نُزيل نقاط المصادقة العامة: التسجيل والدخول وتسجيل الخروج وملف المستخدم
واستعادة كلمة المرور للجمهور. لا حسابات زوار. الوصول الإداري (admin) لا
يمر عبر هذه النقاط العامة — يُدار حصريًا عبر السكربت الداخلي
app.create_admin وتوقيع التوكنات الداخلي للوحة الإدارة. (وثيقة 12.)
"""
from flask import Blueprint, jsonify, request

from ..middleware.auth_middleware import require_auth

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/auth/register", methods=["POST"])
def register():
    return jsonify({"error": "التسجيل متاح فقط عبر إدارة النظام."}), 403


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    return jsonify({"error": "الدخول متاح فقط عبر لوحة الإدارة الداخلية."}), 403


@auth_bp.route("/api/auth/refresh", methods=["POST"])
def refresh():
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
    return jsonify({"error": "استعادة كلمة المرور للجمهور غير متاحة."}), 403


@auth_bp.route("/api/auth/password-reset/confirm", methods=["POST"])
def password_reset_confirm():
    return jsonify({"error": "استعادة كلمة المرور للجمهور غير متاحة."}), 403
