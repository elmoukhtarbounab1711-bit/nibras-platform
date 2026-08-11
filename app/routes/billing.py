"""
مسارات الفوترة والتجارة (Blueprint) — سير عمل الطلبات اليدوية.

نقاط نهاية عامة (بمصادقة) للباقات/الشراء/المحفظة، ونقاط نهاية إدارية
(décorateur require_auth + role admin) للتأكيد/الإلغاء وإدارة الباقات.
كل منطق العمل والتحقق في services_billing؛ المسارات رفيعة.
"""
from flask import Blueprint, jsonify, request

from .. import services_billing
from ..middleware.auth_middleware import require_auth, require_role
from ..services_billing import BillingError

billing_bp = Blueprint("billing", __name__)


def _handle_error(exc: BillingError):
    return jsonify({"error": exc.message}), exc.status_code


def _clamp_limit(value, default=20, maximum=100):
    try:
        return max(1, min(int(value), maximum))
    except (TypeError, ValueError):
        return default


def _clamp_offset(value):
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


# ---------------------------------------------------------------------------
# باقات (عامة)
# ---------------------------------------------------------------------------

@billing_bp.route("/api/plans", methods=["GET"])
def list_plans():
    try:
        plans = services_billing.list_plans(kind=request.args.get("kind"))
    except BillingError as exc:
        return _handle_error(exc)
    return jsonify({"plans": plans}), 200


@billing_bp.route("/api/plans/<plan_ident>", methods=["GET"])
def get_plan(plan_ident):
    plan = services_billing.get_plan_by_slug(plan_ident)
    if plan is None:
        return jsonify({"error": "الباقة غير موجودة."}), 404
    return jsonify(plan), 200


# ---------------------------------------------------------------------------
# المحفظة / النقاط
# ---------------------------------------------------------------------------

@billing_bp.route("/api/wallet", methods=["GET"])
@require_auth
def get_wallet():
    balance = services_billing.get_balance(request.user.id)
    premium = services_billing.premium_status_for_user(request.user.id)
    return jsonify({
        "balance": balance,
        "premium_until": premium["until"],
        "is_premium": premium["is_premium"],
    }), 200


@billing_bp.route("/api/wallet/ledger", methods=["GET"])
@require_auth
def get_ledger():
    limit = _clamp_limit(request.args.get("limit"), 20, 100)
    offset = _clamp_offset(request.args.get("offset"))
    return jsonify({
        "entries": services_billing.list_ledger(request.user.id, limit, offset),
    }), 200


# ---------------------------------------------------------------------------
# الطلبات (سير عمل يدوي)
# ---------------------------------------------------------------------------

@billing_bp.route("/api/orders", methods=["POST"])
@require_auth
def create_order():
    payload = request.get_json(silent=True) or {}
    plan_ident = payload.get("plan")
    if not plan_ident:
        return jsonify({"error": "يُشترط تحديد الباقة (id أو slug)."}), 400
    try:
        order = services_billing.create_order(request.user.id, plan_ident)
    except BillingError as exc:
        return _handle_error(exc)
    return jsonify(order), 201


@billing_bp.route("/api/orders/mine", methods=["GET"])
@require_auth
def my_orders():
    limit = _clamp_limit(request.args.get("limit"), 20, 100)
    offset = _clamp_offset(request.args.get("offset"))
    return jsonify({
        "orders": services_billing.list_orders_for_user(request.user.id, limit, offset),
    }), 200


@billing_bp.route("/api/orders/<int:order_id>/cancel", methods=["POST"])
@require_auth
def cancel_my_order(order_id):
    try:
        order = services_billing.user_cancel_order(request.user.id, order_id)
    except BillingError as exc:
        return _handle_error(exc)
    return jsonify(order), 200


# ---------------------------------------------------------------------------
# الإدارة: الطلبات والجرد
# ---------------------------------------------------------------------------

@billing_bp.route("/api/admin/orders", methods=["GET"])
@require_role("admin")
def admin_list_orders():
    try:
        orders = services_billing.list_orders_admin(
            status=request.args.get("status"),
            limit=_clamp_limit(request.args.get("limit"), 100, 200),
            offset=_clamp_offset(request.args.get("offset")),
        )
    except BillingError as exc:
        return _handle_error(exc)
    return jsonify({"orders": orders}), 200


@billing_bp.route("/api/admin/orders/<int:order_id>/confirm", methods=["POST"])
@require_role("admin")
def admin_confirm_order(order_id):
    try:
        order = services_billing.confirm_order(request.user.id, order_id)
    except BillingError as exc:
        return _handle_error(exc)
    return jsonify(order), 200


@billing_bp.route("/api/admin/orders/<int:order_id>/cancel", methods=["POST"])
@require_role("admin")
def admin_cancel_order(order_id):
    payload = request.get_json(silent=True) or {}
    try:
        order = services_billing.cancel_order(
            request.user.id, order_id, payload.get("note"))
    except BillingError as exc:
        return _handle_error(exc)
    return jsonify(order), 200


@billing_bp.route("/api/admin/billing/summary", methods=["GET"])
@require_role("admin")
def admin_billing_summary():
    return jsonify(services_billing.billing_summary()), 200


# ---------------------------------------------------------------------------
# الإدارة: الباقات (CRUD)
# ---------------------------------------------------------------------------

@billing_bp.route("/api/admin/plans", methods=["GET"])
@require_role("admin")
def admin_list_plans():
    return jsonify({"plans": services_billing.list_plans_admin()}), 200


@billing_bp.route("/api/admin/plans", methods=["POST"])
@require_role("admin")
def admin_create_plan():
    payload = request.get_json(silent=True) or {}
    try:
        plan_id = services_billing.create_plan(request.user.id, payload)
    except BillingError as exc:
        return _handle_error(exc)
    return jsonify({"id": plan_id}), 201


@billing_bp.route("/api/admin/plans/<int:plan_id>", methods=["PUT"])
@require_role("admin")
def admin_update_plan(plan_id):
    payload = request.get_json(silent=True) or {}
    try:
        services_billing.update_plan(request.user.id, plan_id, payload)
    except BillingError as exc:
        return _handle_error(exc)
    return jsonify({"ok": True}), 200


@billing_bp.route("/api/admin/plans/<int:plan_id>", methods=["DELETE"])
@require_role("admin")
def admin_delete_plan(plan_id):
    try:
        services_billing.delete_plan(request.user.id, plan_id)
    except BillingError as exc:
        return _handle_error(exc)
    return jsonify({"ok": True}), 200