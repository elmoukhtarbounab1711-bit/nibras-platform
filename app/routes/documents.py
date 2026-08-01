"""
مسارات مولّد الوثائق (Blueprint) — المرحلة 4 (قرار D-022).

التصفح عام (GET /api/documents/templates و /<slug>) والمحتوى التعليمي مجاني؛
التوليد والملكية والتصدير بمصادقة ومالك فقط (Security 12). POST generate
يستقبل {template_id|template_slug, answers} ويعيد الوثيقة المولَّدة؛
regenerate يحقق FR-5.3 (نسخة +1 عند التعديل)؛ export يعيد ملفًا PDF/DOCX
يُنشأ في الذاكرة (لا ملفات على القرص). حد معدل لكل مستخدم على التوليد.
"""
import time
from io import BytesIO

from flask import Blueprint, jsonify, request, send_file

from .. import config, services_documents
from ..middleware.auth_middleware import require_auth
from ..services_documents import DocumentError

documents_bp = Blueprint("documents", __name__)

# حد معدل في الذاكرة لكل مستخدم (+ عنوان IP) — نمط routes/ai.py
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
@require_auth
def generate():
    key = f"doc:{request.user.id}:{request.remote_addr or 'unknown'}"
    if _rate_limited(key):
        return jsonify({"error": "طلبات كثيرة جدًا. حاول لاحقًا."}), 429
    data = request.get_json(force=True, silent=True) or {}
    template_id = data.get("template_id")
    template_slug = data.get("template_slug")
    if template_id is None and not template_slug:
        return jsonify({"error": "الرجاء تحديد القالب (template_id)."}), 400
    ident = template_id if template_id is not None else template_slug
    try:
        result = services_documents.generate_document(
            request.user.id, ident, data.get("answers") or {}
        )
    except DocumentError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify(result), 201


@documents_bp.route("/api/documents/my", methods=["GET"])
@require_auth
def my_documents():
    return jsonify(services_documents.get_user_documents(request.user.id))


@documents_bp.route("/api/documents/<int:doc_id>/regenerate", methods=["POST"])
@require_auth
def regenerate(doc_id):
    key = f"doc:{request.user.id}:{request.remote_addr or 'unknown'}"
    if _rate_limited(key):
        return jsonify({"error": "طلبات كثيرة جدًا. حاول لاحقًا."}), 429
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = services_documents.regenerate_document(
            request.user.id, doc_id, data.get("answers") or {}
        )
    except DocumentError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify(result), 200


@documents_bp.route("/api/documents/<int:doc_id>/export", methods=["GET"])
@require_auth
def export(doc_id):
    fmt = (request.args.get("format") or "pdf").lower()
    if fmt not in ("pdf", "docx"):
        return jsonify({"error": "format يجب أن يكون pdf أو docx."}), 400
    try:
        doc = services_documents.get_document(request.user.id, doc_id)
    except DocumentError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    if fmt == "docx":
        try:
            data = services_documents.export_docx(doc)
        except DocumentError as exc:
            return jsonify({"error": exc.message}), exc.status_code
        mime, ext = _DOCX_MIME, "docx"
    else:
        try:
            data = services_documents.export_pdf(doc)
        except DocumentError as exc:
            return jsonify({"error": exc.message}), exc.status_code
        mime, ext = "application/pdf", "pdf"
    fname = f"{doc['template_slug']}-v{doc['version']}.{ext}"
    return send_file(
        BytesIO(data), mimetype=mime, as_attachment=True, download_name=fname
    )
