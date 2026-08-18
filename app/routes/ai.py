"""
مسارات واجهة الذكاء الاصطناعي (Blueprint) — المرحلة 3 (منصة عامة).

POST /api/ai/explain — {question, mode} → {answer, cited_article_ids[], mode}
POST /api/ai/explain-attachment — multipart file → {answer, mode}
وفق وثيقة API. عام بلا حساب (public_auth): الزائر يرسل سؤاله دون تسجيل؛
حد معدل لكل عنوان IP (٤٣ — منع سوء الاستخدام) وتمنع السجلات تخزين
المحادثات الشخصية كاملة. فشل المزوّد يعيد خطأ واضحًا (503).
"""
import time

from flask import Blueprint, jsonify, request

from .. import config, services_ai
from ..middleware.auth_middleware import public_auth
from ..services_ai import AI_ALLOWED_IMAGE_TYPES, AI_ALLOWED_PDF_TYPES, AIProviderError

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
    if len(question) > config.AI_QUESTION_MAX_LENGTH:
        return jsonify({"error": "السؤال طويل جدًا. الحد الأقصى 2000 حرف."}), 400
    mode = data.get("mode", "auto")
    if mode not in ("auto", "grounded", "general", "research"):
        return jsonify({"error": "mode يجب أن يكون auto أو grounded أو general أو research"}), 400
    try:
        if mode == "auto":
            result = services_ai.auto_explanation(question, user_id=None)
        elif mode == "grounded":
            result = services_ai.grounded_explanation(question, user_id=None)
        elif mode == "research":
            result = services_ai.research_explanation(question, user_id=None)
        else:
            result = services_ai.general_explanation(question, user_id=None)
    except AIProviderError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify(result), 200


@ai_bp.route("/api/ai/explain-attachment", methods=["POST"])
@public_auth
def explain_attachment():
    """تحليل مرفق PDF أو صورة (JPEG/PNG).

    يتطلب multipart/form-data مع:
      - file: ملف PDF أو صورة
      - question: سؤال المستخدم (اختياري — افتراضي: "حلّل المستند")
    """
    client = request.remote_addr or "unknown"
    if _rate_limited(f"ai:{client}"):
        return jsonify({"error": "طلبات كثيرة جدًا. حاول لاحقًا."}), 429

    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "الرجاء إرفاق ملف (PDF أو صورة)"}), 400

    question = (request.form.get("question") or "").strip()
    if not question:
        question = "حلّل المستند المرفق وأجب على أي سؤال يتعلق به"

    filename = file.filename.lower()
    mime = file.content_type or ""

    try:
        if filename.endswith(".pdf") or mime in AI_ALLOWED_PDF_TYPES:
            file_bytes = file.read()
            if len(file_bytes) > services_ai.AI_ATTACHMENT_MAX_BYTES:
                return jsonify({"error": "حجم الملف يتجاوز 10MB"}), 400
            extracted_text = services_ai.extract_pdf_text(file_bytes)
            if not extracted_text:
                return jsonify({"error": "تعذر استخراج نص من ملف PDF — تأكد أن الملف يحتوي على نص"}), 400
            import logging as _log
            _log.getLogger("nibras.ai").info(
                "PDF extracted: file=%s bytes=%d text_len=%d preview=%s",
                filename, len(file_bytes), len(extracted_text),
                extracted_text[:200],
            )
            result = services_ai.document_analysis(
                extracted_text=extracted_text, question=question
            )

        elif mime in AI_ALLOWED_IMAGE_TYPES or filename.endswith((".jpg", ".jpeg", ".png")):
            file_bytes = file.read()
            if len(file_bytes) > services_ai.AI_IMAGE_MAX_BYTES:
                return jsonify({"error": "حجم الصورة يتجاوز 5MB"}), 400
            if not mime or mime == "application/octet-stream":
                if filename.endswith(".png"):
                    mime = "image/png"
                else:
                    mime = "image/jpeg"
            img_b64 = services_ai.encode_image_base64(file_bytes, mime)
            result = services_ai.document_analysis(
                images=[{"mime": mime, "data": img_b64}],
                question=question,
            )
        else:
            return jsonify({"error": "نوع الملف غير مدعوم. الرجاء إرفاق PDF أو صورة (JPEG/PNG)"}), 400

    except AIProviderError as exc:
        return jsonify({"error": exc.message}), exc.status_code

    return jsonify(result), 200
