"""
مسارات الاتفاقيات والنصوص القانونية الدولية بالفرنسية (Blueprint).

GET  /api/treaties           قائمة الاتفاقيات (?category= و ?q=)
GET  /api/treaties/<id>      تفاصيل اتفاقية
"""
from flask import Blueprint, jsonify, request

from .. import services_treaties as svc

treaties_bp = Blueprint("treaties", __name__)


@treaties_bp.route("/api/treaties", methods=["GET"])
def list_treaties():
    category = request.args.get("category")
    q = request.args.get("q")
    language = request.args.get("language")
    items = svc.list_treaties(category=category, query=q, language=language)
    categories = svc.list_categories(language=language)
    return jsonify({"treaties": items, "categories": categories})


@treaties_bp.route("/api/treaties/<int:treaty_id>", methods=["GET"])
def get_treaty(treaty_id):
    treaty = svc.get_treaty(treaty_id)
    if not treaty:
        return jsonify({"error": "الاتفاقية غير موجودة"}), 404
    return jsonify(treaty)
