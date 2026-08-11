"""
مسارات مولّد الوثائق (Blueprint) — المرحلة 4 (منصة عامة بلا حسابات).

التصفح عام (GET /api/documents/templates و /<slug>) والتوليد عام أيضًا:
الزائر يختار قالبًا ويُدخِل بياناته دون تسجيل (public_auth) ويتلقى
الوثيقة والتصدير PDF/DOCX فورًا. لا تُخزَّن أي وثيقة على الخادم —
المولِّد يعمل عديم الحالة (stateless) حفاظًا على الخصوصية: لا ملفات
ولا سجلّ وثائق شخصي دائم. حد معدل لكل عنوان IP. (قرار D-022 — محسَّن
للنشر العام.)
"""
import time
from io import BytesIO

from flask import Blueprint, jsonify, request, send_file

from .. import config, services_documents
from ..middleware.auth_middleware import public_auth
from ..services_documents import DocumentError

documents_bp = Blueprint("documents", __name__)

# حد معدل في الذاكرة لكل عنوان IP — نمط routes/ai.py
_attempts = {}

_DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _rate_limited(key: str) -> bool:
    now = time.time()
    window = config.DOC_RATE_LIMIT_WINDOW_SECONDS
    bucket = _attempts.setdefault(key, [])
    bucket[:] = [t for t in bucket if now - t < window]
    if len(bucket) >= config.DOC_RATE_LIMIT_MAX_REQUESTS:
        return True
    bucket.append(now)
    return False


@documents_bp.route("/api/documents/templates", methods=["GET"])
def list_templates():
    category = request.args.get("category")
    return jsonify(services_documents.list_templates(category))


@documents_bp.route("/api/documents/templates/<slug>", methods=["GET"])
def template_detail(slug):
    tmpl = services_documents.get_template(slug)
    if not tmpl:
        return jsonify({"error": "القالب غير موجود."}), 404
    return jsonify(tmpl)


@documents_bp.route("/api/documents/generate", methods=["POST"])
@public_auth
def generate():
    client = request.remote_addr or "unknown"
    if _rate_limited(f"doc:{client}"):
        return jsonify({"error": "طلبات كثيرة جدًا. حاول لاحقًا."}), 429
    data = request.get_json(force=True, silent=True) or {}
    template_id = data.get("template_id")
    template_slug = data.get("template_slug")
    if template_id is None and not template_slug:
        return jsonify({"error": "الرجاء تحديد القالب (template_id)."}), 400
    ident = template_id if template_id is not None else template_slug
    fmt = (data.get("format") or "text").lower()
    try:
        result = services_documents.generate_document(
            None, ident, data.get("answers") or {}, format_=fmt
        )
    except DocumentError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    if fmt in ("pdf", "docx"):
        mime = _DOCX_MIME if fmt == "docx" else "application/pdf"
        ext = fmt
        fname = f"{result['template_slug']}.{ext}"
        return send_file(
            BytesIO(result["data"]), mimetype=mime, as_attachment=True,
            download_name=fname,
        )
    return jsonify(result), 201
