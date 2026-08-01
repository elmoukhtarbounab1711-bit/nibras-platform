"""
مسارات الحاسبات القانونية (Blueprint) — المرحلة 3.

GET /api/calculators يعرض قائمة الحاسبات، و POST /api/calculators/<slug>/run
يستقبل مدخلات منظمة ويعيد {result, legal_basis} وفق وثيقة API. عامة بلا
مصادقة (المحتوى التعليمي مجاني — فلسفة "المعرفة القانونية مجانية")؛
calculator_runs تُسجَّل بـ user_id null للمجهولين (قرار D-021).
"""
from flask import Blueprint, jsonify, request

from .. import services_calculators
from ..services_calculators import CalculatorError

calculators_bp = Blueprint("calculators", __name__)


@calculators_bp.route("/api/calculators", methods=["GET"])
def list_calculators():
    return jsonify(services_calculators.list_calculators())


@calculators_bp.route("/api/calculators/<slug>/run", methods=["POST"])
def run_calculator(slug):
    data = request.get_json(force=True, silent=True) or {}
    try:
        result = services_calculators.run_calculator(slug, data)
    except CalculatorError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    return jsonify(result), 200
