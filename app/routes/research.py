"""مسارات مكتبة الباحث — كتب PDF مقسمة حسب التصنيف القانوني ونوع الكتاب."""
import os
import uuid
from pathlib import Path

from flask import Blueprint, jsonify, request, send_file

from ..database import db_session
from ..middleware.auth_middleware import require_role
from ..services_research import (
    BOOK_TYPE_LABELS,
    BOOK_TYPES,
    LEGAL_CATEGORIES,
    LEGAL_CATEGORY_LABELS,
    create_book,
    delete_book,
    get_book,
    get_stats,
    list_books,
    update_book,
)

research_bp = Blueprint("research", __name__)

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "storage" / "research_books"
COVER_DIR = UPLOAD_DIR / "covers"
BOOK_DIR = UPLOAD_DIR / "files"

ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_BOOK_EXT = {".pdf"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_BOOK_SIZE = 50 * 1024 * 1024  # 50 MB


def _ensure_dirs():
    COVER_DIR.mkdir(parents=True, exist_ok=True)
    BOOK_DIR.mkdir(parents=True, exist_ok=True)


def _save_upload(file_storage, dest_dir: Path, allowed_ext: set, max_size: int):
    """حفظ ملف مرفوع وإرجاع المسار الكامل."""
    filename = file_storage.filename or ""
    ext = Path(filename).suffix.lower()
    if ext not in allowed_ext:
        return None, f"امتداد الملف غير مدعوم: {ext}"
    data = file_storage.read()
    if len(data) > max_size:
        return None, f"حجم الملف يتجاوز الحد الأقصى ({max_size // (1024 * 1024)} MB)"
    unique_name = f"{uuid.uuid4().hex}{ext}"
    dest = dest_dir / unique_name
    dest.write_bytes(data)
    return str(dest), None


@research_bp.route("/api/research/categories", methods=["GET"])
def api_research_categories():
    return jsonify({
        "book_types": [{"key": k, "label": BOOK_TYPE_LABELS.get(k, k)} for k in BOOK_TYPES],
        "legal_categories": [{"key": k, "label": LEGAL_CATEGORY_LABELS.get(k, k)} for k in LEGAL_CATEGORIES],
    })


@research_bp.route("/api/research/books", methods=["GET"])
def api_research_list():
    category = request.args.get("category")
    book_type = request.args.get("type")
    q = request.args.get("q")
    limit = min(int(request.args.get("limit", 50)), 100)
    offset = int(request.args.get("offset", 0))

    data = list_books(category=category, book_type=book_type, q=q, limit=limit, offset=offset)
    return jsonify(data)


@research_bp.route("/api/research/books/<int:book_id>", methods=["GET"])
def api_research_detail(book_id):
    book = get_book(book_id)
    if not book:
        return jsonify({"error": "الكتاب غير موجود"}), 404
    return jsonify(book)


@research_bp.route("/api/research/books/<int:book_id>/download", methods=["GET"])
def api_research_download(book_id):
    book = get_book(book_id)
    if not book:
        return jsonify({"error": "الكتاب غير موجود"}), 404
    fp = book.get("file_path")
    if not fp:
        return jsonify({"error": "الملف غير متاح"}), 404
    if not os.path.exists(fp):
        return jsonify({"error": "الملف غير موجود على الخادم"}), 404
    with db_session() as conn:
        conn.execute(
            "UPDATE research_books SET downloads = downloads + 1 WHERE id = ?", (book_id,)
        )
    return send_file(fp, as_attachment=True, download_name=book.get("file_name", "book.pdf"))


@research_bp.route("/api/research/books/<int:book_id>/cover", methods=["GET"])
def api_research_cover(book_id):
    book = get_book(book_id)
    if not book:
        return jsonify({"error": "الكتاب غير موجود"}), 404
    ci = book.get("cover_image")
    if not ci:
        return jsonify({"error": "لا توجد صورة غلاف"}), 404
    if not os.path.exists(ci):
        return jsonify({"error": "الصورة غير موجودة على الخادم"}), 404
    return send_file(ci)


@research_bp.route("/api/research/stats", methods=["GET"])
def api_research_stats():
    return jsonify(get_stats())


# ── مسارات إدارية ──────────────────────────────────────────────

@research_bp.route("/api/admin/research/upload", methods=["POST"])
@require_role("admin")
def api_admin_research_upload():
    """رفع ملف (صورة غلاف أو كتاب PDF) من الجهاز."""
    _ensure_dirs()
    file = request.files.get("file")
    kind = request.form.get("kind", "book")  # "cover" or "book"

    if not file or not file.filename:
        return jsonify({"error": "لم يتم اختيار ملف"}), 400

    if kind == "cover":
        path, err = _save_upload(file, COVER_DIR, ALLOWED_IMAGE_EXT, MAX_IMAGE_SIZE)
    else:
        path, err = _save_upload(file, BOOK_DIR, ALLOWED_BOOK_EXT, MAX_BOOK_SIZE)

    if err:
        return jsonify({"error": err}), 400

    return jsonify({"path": path, "name": file.filename}), 201


@research_bp.route("/api/admin/research/books", methods=["POST"])
@require_role("admin")
def api_admin_research_create():
    data = request.get_json(silent=True) or {}
    if not data.get("title"):
        return jsonify({"error": "العنوان مطلوب"}), 400
    book_id = create_book(data)
    return jsonify({"id": book_id, "message": "تمت الإضافة"}), 201


@research_bp.route("/api/admin/research/books/<int:book_id>", methods=["PUT"])
@require_role("admin")
def api_admin_research_update(book_id):
    data = request.get_json(silent=True) or {}
    if update_book(book_id, data):
        return jsonify({"message": "تم التحديث"})
    return jsonify({"error": "لم يتم العثور على الكتاب"}), 404


@research_bp.route("/api/admin/research/books/<int:book_id>", methods=["DELETE"])
@require_role("admin")
def api_admin_research_delete(book_id):
    book = get_book(book_id)
    if book:
        for key in ("file_path", "cover_image"):
            fp = book.get(key)
            if fp and os.path.exists(fp):
                os.remove(fp)
    delete_book(book_id)
    return jsonify({"message": "تم الحذف"})


@research_bp.route("/api/admin/research/books", methods=["GET"])
@require_role("admin")
def api_admin_research_list():
    data = list_books(
        category=request.args.get("category"),
        book_type=request.args.get("type"),
        q=request.args.get("q"),
        limit=min(int(request.args.get("limit", 50)), 200),
        offset=int(request.args.get("offset", 0)),
    )
    return jsonify(data)
