"""
مسارات تعلم اللغة القانونية (Blueprint).

GET  /api/legal-french/languages     قائمة اللغات المتاحة
GET  /api/legal-french/levels?lang=  قائمة المستويات
GET  /api/legal-french/levels/<id>   مستوى مع الدروس
GET  /api/legal-french/lessons/<id>  محتوى درس كامل
GET  /api/legal-french/quiz/<id>     اختبار درس
POST /api/legal-french/progress      حفظ نتيجة اختبار (مصادق)
GET  /api/legal-french/progress      تقدم المستخدم (مصادق)
GET  /api/legal-french/stats         إحصائيات المستخدم (مصادق)
"""
from flask import Blueprint, jsonify, request

from .. import services_legal_french as svc
from ..middleware.auth_middleware import require_auth

legal_french_bp = Blueprint("legal_french", __name__)


@legal_french_bp.route("/api/legal-french/languages", methods=["GET"])
def list_languages():
    return jsonify({"languages": svc.list_languages()})


@legal_french_bp.route("/api/legal-french/levels", methods=["GET"])
def list_levels():
    lang = request.args.get("lang", "fr")
    return jsonify({"levels": svc.list_levels(lang), "lang": lang})


@legal_french_bp.route("/api/legal-french/levels/<int:level_id>", methods=["GET"])
def get_level(level_id):
    lang = request.args.get("lang", "fr")
    level = svc.get_level(level_id, lang)
    if not level:
        return jsonify({"error": "المستوى غير موجود"}), 404
    return jsonify(level)


@legal_french_bp.route("/api/legal-french/lessons/<lesson_id>", methods=["GET"])
def get_lesson(lesson_id):
    lesson = svc.get_lesson(lesson_id)
    if not lesson:
        return jsonify({"error": "الدرس غير موجود"}), 404
    return jsonify(lesson)


@legal_french_bp.route("/api/legal-french/quiz/<lesson_id>", methods=["GET"])
def get_quiz(lesson_id):
    quiz = svc.get_quiz(lesson_id)
    if not quiz:
        return jsonify({"error": "الاختبار غير متوفر لهذا الدرس"}), 404
    return jsonify(quiz)


@legal_french_bp.route("/api/legal-french/progress", methods=["POST"])
@require_auth
def save_progress():
    data = request.get_json(force=True, silent=True) or {}
    lesson_id = data.get("lesson_id")
    score = data.get("score", 0)
    total = data.get("total", 0)
    if not lesson_id:
        return jsonify({"error": "lesson_id مطلوب"}), 400
    svc.save_progress(request.user.id, lesson_id, score, total)
    return jsonify({"status": "ok"}), 201


@legal_french_bp.route("/api/legal-french/progress", methods=["GET"])
@require_auth
def get_progress():
    lang = request.args.get("lang")
    progress = svc.get_user_progress(request.user.id, lang)
    return jsonify({"progress": progress})


@legal_french_bp.route("/api/legal-french/stats", methods=["GET"])
@require_auth
def get_stats():
    lang = request.args.get("lang")
    stats = svc.get_user_stats(request.user.id, lang)
    return jsonify(stats)
