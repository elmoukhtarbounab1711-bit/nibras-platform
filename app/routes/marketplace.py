"""
مسارات سوق القوالب (Blueprint) — المرحلة 7 (قرار D-025).

القراءة العامة للكتالوج: فئات (مع عدد القوالب)، قوائم قابلة للتصفية بالتصنيف
والبحث النصي مع ترقيم، وتفصيل قالب. التفصيل العام لا يفضح storage_key، ولا
يوجد أي تنزيل عام حتى الشراء (الشراء مؤجَّل لحسم بوابة الدفع — BRD §5).
إدارة القوالب والفئات (دور admin) في routes/admin.py.
"""
from flask import Blueprint, jsonify, request

from .. import services_marketplace

marketplace_bp = Blueprint("marketplace", __name__)


@marketplace_bp.route("/api/marketplace/categories", methods=["GET"])
def list_categories():
    return jsonify(services_marketplace.list_categories())


@marketplace_bp.route("/api/marketplace/templates", methods=["GET"])
def list_templates():
    category_id = request.args.get("category")
    try:
        result = services_marketplace.list_templates(
            category_id=int(category_id) if category_id else None,
            q=request.args.get("q"),
            limit=int(request.args.get("limit") or 0),
            offset=int(request.args.get("offset") or 0),
        )
    except ValueError:
        return jsonify({"error": "category/limit/offset يجب أن تكون أرقامًا."}), 400
    return jsonify(result)


@marketplace_bp.route("/api/marketplace/templates/<int:template_id>", methods=["GET"])
def template_detail(template_id):
    template = services_marketplace.get_template(template_id)
    if not template:
        return jsonify({"error": "القالب غير موجود."}), 404
    return jsonify(template)
