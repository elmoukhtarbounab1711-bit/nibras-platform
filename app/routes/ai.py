"""
مسارات واجهة الذكاء الاصطناعي (Blueprint) — المرحلة 3.

POST /api/ai/explain — {question, mode} → {answer, cited_article_ids[], mode}
وفق وثيقة API. يتطلب مصادقة + حد معدل لكل مستخدم (وثيقة 13 §7 / Security
12 §6). فشل المزوّد يعيد خطأ واضحًا (503) لا ردًّا صامتًا غير موجَّه
(المواصفة الوظيفية §3).
"""
import time

from flask import Blueprint, jsonify, request

from .. import config, services_ai
from ..middleware.auth_middleware import require_auth
from ..services_ai import AIProviderError

ai_bp = Blueprint("ai", __name__)

# حد معدل في الذاكرة لكل مستخدم (+ عنوان IP) — نمط routes/auth.py
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
@require_auth
def explain():
    key = f"ai:{request.user.id}:{request.remote_addr or 'unknown'}"
    if _rate_limited(key):
        return jsonify({"error": "طلبات كثيرة جدًا. حاول لاحقًا."}), 429
    data = request.get_json(force=True, silent=True) or {}
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify({"error": "الرجاء إدخال سؤال (question)"}), 400
    mode = data.get("mode", "grounded")
    if mode not in ("grounded", "general"):
        return jsonify({"error": "mode يجب أن يكون grounded أو general"}), 400
    try:
        if mode == "grounded":
            result = services_ai.grounded_explanation(question, user_id=request.user.id)
        else:
            result = services_ai.general_explanation(question, user_id=request.user.id)
    except AIProviderError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify(result), 200
