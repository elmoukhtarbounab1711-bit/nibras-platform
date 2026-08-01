"""
المسارات الإدارية (Blueprint).

محمية بمصادقة JWT + دور admin (المرحلة 1) وفق وثيقة المصادقة والتفويض
(§2.2/§2.5) — حُلّ محل مفتاح X-Admin-Key القديم.
"""
from flask import Blueprint, jsonify, request

from ..database import db_session
from ..middleware.auth_middleware import require_role

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/api/admin/texts", methods=["POST"])
@require_role("admin")
def create_text():
    data = request.get_json(force=True, silent=True) or {}
    required = ["category_id", "type", "title"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"حقول ناقصة: {', '.join(missing)}"}), 400
    with db_session() as conn:
        cur = conn.execute(
            """INSERT INTO legal_texts
               (category_id, type, title, official_ref, enacted_date, source_note, is_sample_data)
               VALUES (?,?,?,?,?,?,?)""",
            (
                data["category_id"], data["type"], data["title"],
                data.get("official_ref"), data.get("enacted_date"),
                data.get("source_note"), int(data.get("is_sample_data", 1)),
            ),
        )
        new_id = cur.lastrowid
    return jsonify({"id": new_id, "message": "تم إنشاء النص القانوني"}), 201


@admin_bp.route("/api/admin/texts/<int:text_id>/articles", methods=["POST"])
@require_role("admin")
def create_article(text_id):
    data = request.get_json(force=True, silent=True) or {}
    required = ["number", "label", "content"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"حقول ناقصة: {', '.join(missing)}"}), 400
    with db_session() as conn:
        text_exists = conn.execute(
            "SELECT id FROM legal_texts WHERE id = ?", (text_id,)
        ).fetchone()
        if not text_exists:
            return jsonify({"error": "النص القانوني غير موجود"}), 404
        cur = conn.execute(
            """INSERT INTO articles
               (legal_text_id, number, label, content, plain_explanation, keywords)
               VALUES (?,?,?,?,?,?)""",
            (
                text_id, data["number"], data["label"], data["content"],
                data.get("plain_explanation"), data.get("keywords", ""),
            ),
        )
        new_id = cur.lastrowid
    return jsonify({"id": new_id, "message": "تمت إضافة المادة"}), 201
