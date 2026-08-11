"""
مسارات واجهة الذكاء الاصطناعي (Blueprint) — المرحلة 3 (منصة عامة).

POST /api/ai/explain — {question, mode} → {answer, cited_article_ids[], mode}
وفق وثيقة API. عام بلا حساب (public_auth): الزائر يرسل سؤاله دون تسجيل؛
حد معدل لكل عنوان IP (٤٣ — منع سوء الاستخدام) وتمنع السجلات تخزين
المحادثات الشخصية كاملة. فشل المزوّد يعيد خطأ واضحًا (503).
"""
import time

from flask import Blueprint, jsonify, request

from .. import config, services_ai
from ..middleware.auth_middleware import public_auth
from ..services_ai import AIProviderError

ai_bp = Blueprint("ai", __name__)

# حد معدل في الذاكرة لكل عنوان IP — نمط routes/auth.py
_attempts = {}


def _rate_limited(key: str) -> bool:
    now = time.time()
    window = config.AI_RATE_LIMIT_WINDOW_SECONDS
    bucket = _attempts.setdefault(key, [])
    bucket[:] = [t for t in bucket if now - t < window]
    if len(bucket) >= config.AI_RATE_LIMIT_MAX_REQUESTS:
        return True
    bucket.append(now)
    return False


@ai_bp.route("/api/ai/explain", methods=["POST"])
@public_auth
def explain():
    client = request.remote_addr or "unknown"
    if _rate_limited(f"ai:{client}"):
        return jsonify({"error": "طلبات كثيرة جدًا. حاول لاحقًا."}), 429
    data = request.get_json(force=True, silent=True) or {}
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify({"error": "الرجاء إدخال سؤال (question)"}), 400
    mode = data.get("mode", "grounded")
    if mode not in ("grounded", "general", "research"):
        return jsonify({"error": "mode يجب أن يكون grounded أو general أو research"}), 400
    try:
        if mode == "grounded":
            result = services_ai.grounded_explanation(question, user_id=None)
        elif mode == "research":
            result = services_ai.research_explanation(question, user_id=None)
        else:
            result = services_ai.general_explanation(question, user_id=None)
    except AIProviderError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify(result), 200
