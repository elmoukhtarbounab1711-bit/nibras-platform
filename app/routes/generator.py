"""
مسارات مولّد الوثائق والعقود (Blueprint).

GET  /api/generator/catalog     — فهرس المكتبة كاملة (أصناف + وثائق)
GET  /api/generator/templates   — القوالب الموصى بها (مُنتقاة)
GET  /api/generator/fields      — حقول مستند (?file=... أو ?template=id)
POST /api/generator/render      — معاينة HTML للطباعة بعد التعبئة
POST /api/generator/download    — تنزيل DOCX معبّأ (تحميل مباشر)

عامة بلا مصادقة (قوالب وثائق عامة؛ التوليد عديم الحالة للزوار) — نفس
فلسفة مولّد الوثائق الحالي في services_documents (قرار D-022).
"""
from flask import Blueprint, jsonify, request, send_file

from .. import config, generator
from ..generator import GeneratorError

generator_bp = Blueprint("generator", __name__)


def _ok(payload, status=200):
    return jsonify(payload), status


def _err(exc):
    return jsonify({"error": exc.message}), exc.status_code


@generator_bp.route("/api/generator/catalog", methods=["GET"])
def catalog():
    category = request.args.get("category", "").strip() or None
    return _ok({
        "total": len(generator.read_index().get("categories") or []),
        "categories": generator.categories(),
        "docs": generator.list_docs(category),
    })


@generator_bp.route("/api/generator/templates", methods=["GET"])
def templates():
    return _ok({"templates": generator.recommended_templates()})


@generator_bp.route("/api/generator/fields", methods=["GET"])
def fields():
    file = request.args.get("file", "").strip()
    template = request.args.get("template", "").strip() or None
    if not file:
        return _err(GeneratorError("الوثيقة غير محددة.", 400))
    doc = generator.get_doc(file)
    if not doc:
        return _err(GeneratorError("الوثيقة غير موجودة في المكتبة.", 404))
    try:
        flds = generator.resolve_fields(file, template)
    except GeneratorError as exc:
        return _err(exc)
    return _ok({"file": file, "title": doc["title"], "fillable": doc["fillable"],
                "fields": flds})


@generator_bp.route("/api/generator/render", methods=["POST"])
def render():
    data = request.get_json(force=True, silent=True) or {}
    file = (data.get("file") or "").strip()
    template = (data.get("template") or "").strip() or None
    if not file:
        return _err(GeneratorError("الوثيقة غير محددة.", 400))
    doc = generator.get_doc(file)
    if not doc or not doc["fillable"]:
        return _err(GeneratorError("هذه الوثيقة غير قابلة للتعبئة.", 400))
    try:
        fields = generator.resolve_fields(file, template)
        html, _name = generator.preview_html(file, fields, data.get("values") or {})
    except GeneratorError as exc:
        return _err(exc)
    return _ok({"file": file, "title": doc["title"], "preview": html})


@generator_bp.route("/api/generator/download", methods=["POST"])
def download():
    data = request.get_json(force=True, silent=True) or {}
    file = (data.get("file") or "").strip()
    template = (data.get("template") or "").strip() or None
    if not file:
        return _err(GeneratorError("الوثيقة غير محددة.", 400))
    doc = generator.get_doc(file)
    if not doc or not doc["fillable"]:
        return _err(GeneratorError("هذه الوثيقة غير قابلة للتعبئة.", 400))
    try:
        fields = generator.resolve_fields(file, template)
        data_bytes, name = generator.generate_docx_bytes(
            file, fields, data.get("values") or {})
    except GeneratorError as exc:
        return _err(exc)
    import io

    return send_file(
        io.BytesIO(data_bytes),
        mimetype=("application/vnd.openxmlformats-officedocument."
                  "wordprocessingml.document"),
        as_attachment=True,
        download_name=name,
    )


@generator_bp.route("/api/generator/file", methods=["GET"])
def raw_file():
    """تنزيل الأصل (docx/doc/pdf) من المكتبة مباشرة."""
    file = request.args.get("file", "").strip() or ""
    doc = generator.get_doc(file)
    if not doc:
        return _err(GeneratorError("الوثيقة غير موجودة في المكتبة.", 404))
    try:
        from pathlib import Path
        p = generator._resolve_file(file)
    except GeneratorError as exc:
        return _err(exc)
    return send_file(str(p), as_attachment=True,
                     download_name=Path(file).name)


@generator_bp.route("/api/generator/health", methods=["GET"])
def health():
    """فحص جاهزية المكتبة (يُستخدم في اختبارات ومراقبة النشر)."""
    return _ok({
        "configured": bool(generator.DOCS_ROOT.exists()),
        "indexed_files": generator.read_index().get("total_files", 0),
        "docs_dir": str(generator.DOCS_ROOT),
        "max_fields": config.GENERATOR_MAX_FIELDS,
    })
