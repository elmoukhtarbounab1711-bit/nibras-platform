"""
خدمات التجارة والفوترة (دخل نبراس).

باقات (payment_plans) من نوعين:
  * credits       — نقاط تُضاف للحساب عند تأكيد الطلب إداريًا، وتُصرف على
                    المكالمات المتقدمة للذكاء الاصطناعي وتصدير الوثائق.
  * premium_listing — ظهر مميز لملف مهني محقَّق لمدة duration_days.

الطلبات (orders) تبدأ pending وتُؤكَّد يدويًا من الإدارة عند إثبات الدفع
(تحويل بنكي/CMI أولًا)، ثم تُضاف النقاط للحساب (wallet_balances) مع سجل
حركة في credit_ledger، أو يُفعَّل الظهور المميز (premium_until). النموذج
عمدًا بلا بوابة دفع بعد، لكن payment_method جاهز لمرحلة لاحقة.
"""
from datetime import date, datetime, timedelta, timezone

from . import tenant_scope
from .database import db_session

PLAN_KINDS = ("credits", "premium_listing")
ORDER_STATUSES = ("pending", "paid", "cancelled")


def _today():
    """تاريخ اليوم (UTC) — مقارنة نصوص %Y-%m-%d تُبنى على التاريخ فقط."""
    return datetime.now(timezone.utc).date()


class BillingError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


# ---------------------------------------------------------------------------
# بذر أدنى للباقات (idempotent) — تُدار لاحقًا من لوحة التحكم
# ---------------------------------------------------------------------------

DEFAULT_PLANS = (
    {"slug": "credits-50", "name": "50 نقطة", "kind": "credits",
     "price_cents": 1000, "credits": 50, "duration_days": None,
     "description": "50 نقطة للاستخدامات المتقدمة (AI + تصدير وثائق)."},
    {"slug": "credits-150", "name": "150 نقطة", "kind": "credits",
     "price_cents": 2500, "credits": 150, "duration_days": None,
     "description": "150 نقطة — خصم تراكمي لغير المبتدئين."},
    {"slug": "credits-400", "name": "400 نقطة", "kind": "credits",
     "price_cents": 6000, "credits": 400, "duration_days": None,
     "description": "400 نقطة — الأكثر اقتصادية للاستخدام الكثيف."},
    {"slug": "premium-30", "name": "ظهور مميز — 30 يومًا", "kind": "premium_listing",
     "price_cents": 14900, "credits": 0, "duration_days": 30,
     "description": "أولوية الظهور وشارة مميزة في دليل المهنيين."},
)


def ensure_defaults():
    """بذر الباقات الافتراضية إن كانت فارغة (idempotent — نمط ensure_defaults)."""
    with db_session() as conn:
        count = conn.execute("SELECT COUNT(*) AS c FROM payment_plans").fetchone()["c"]
        if count == 0:
            for plan in DEFAULT_PLANS:
                conn.execute(
                    """INSERT INTO payment_plans
                       (slug, name, kind, price_cents, credits, duration_days,
                        description, enabled)
                       VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
                    (plan["slug"], plan["name"], plan["kind"], plan["price_cents"],
                     plan["credits"], plan["duration_days"], plan["description"]),
                )


# ---------------------------------------------------------------------------
# الباقات (عامة)
# ---------------------------------------------------------------------------

def _plan_dict(row) -> dict:
    return {
        "id": row["id"],
        "slug": row["slug"],
        "name": row["name"],
        "kind": row["kind"],
        "price_cents": row["price_cents"],
        "price": round(row["price_cents"] / 100, 2),
        "credits": row["credits"],
        "duration_days": row["duration_days"],
        "description": row["description"],
        "enabled": bool(row["enabled"]),
    }


def list_plans(kind: str | None = None) -> list:
    query = "SELECT * FROM payment_plans WHERE enabled = 1"
    params = []
    if kind:
        if kind not in PLAN_KINDS:
            raise BillingError("kind يجب أن يكون credits أو premium_listing.", 400)
        query += " AND kind = ?"
        params.append(kind)
    query += " ORDER BY price_cents"
    with db_session() as conn:
        rows = conn.execute(query, params).fetchall()
    return [_plan_dict(r) for r in rows]


def get_plan(plan_id: int):
    with db_session() as conn:
        row = conn.execute(
            "SELECT * FROM payment_plans WHERE id = ? AND enabled = 1", (plan_id,)
        ).fetchone()
    return _plan_dict(row) if row else None


def get_plan_by_slug(slug: str):
    with db_session() as conn:
        row = conn.execute(
            "SELECT * FROM payment_plans WHERE slug = ? AND enabled = 1", (slug,)
        ).fetchone()
    return _plan_dict(row) if row else None


def _required_plan(conn, ident) -> dict:
    """يستوفي الباقة المطلوبة (بالـ id أو الـ slug) أو يرفع 404."""
    if isinstance(ident, int) or (isinstance(ident, str) and ident.isdigit()):
        row = conn.execute(
            "SELECT * FROM payment_plans WHERE id = ? AND enabled = 1", (int(ident),)
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT * FROM payment_plans WHERE slug = ? AND enabled = 1", (ident,)
        ).fetchone()
    if row is None:
        raise BillingError("الباقة غير موجودة.", 404)
    return _plan_dict(row)


# ---------------------------------------------------------------------------
# الحساب / المحفظة
# ---------------------------------------------------------------------------

def _get_balance_row(conn, user_id: int):
    return conn.execute(
        "SELECT credits FROM wallet_balances WHERE user_id = ?", (user_id,)
    ).fetchone()


def get_balance(user_id: int) -> int:
    """رصيد النقاط الحالي للمستخدم (0 إن لم تُنشأ المحفظة بعد)."""
    with db_session() as conn:
        row = _get_balance_row(conn, user_id)
        return row["credits"] if row else 0


def _set_balance(conn, user_id: int, delta: int, reason: str, reference=None) -> int:
    """يحدّث الرصيد ويسجّل الحركة في credit_ledger ضمن معاملة واحدة.

    balance_after يُخزَّن للمساءلة؛ أي رصيد سالب يرفع 402 (لا دين) وتُتراجع
    المعاملة بأكملها.
    """
    row = _get_balance_row(conn, user_id)
    current = row["credits"] if row else 0
    new_balance = current + delta
    if new_balance < 0:
        raise BillingError("رصيد النقاط غير كافٍ.", 402)
    if row:
        conn.execute(
            "UPDATE wallet_balances SET credits = ? WHERE user_id = ?",
            (new_balance, user_id),
        )
    else:
        conn.execute(
            "INSERT INTO wallet_balances (user_id, credits) VALUES (?, ?)",
            (user_id, new_balance),
        )
    conn.execute(
        """INSERT INTO credit_ledger
           (user_id, delta, reason, reference, balance_after, tenant_id)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, delta, reason, reference, new_balance,
         tenant_scope.insert_tenant_id()),
    )
    return new_balance


def add_credits(user_id: int, amount: int, reason: str = "order",
                reference: str | None = None) -> int:
    """إضافة نقاط (شراء/إهداء/تسوية) — موجبة فقط."""
    if amount <= 0:
        raise BillingError("كمية النقاط يجب أن تكون موجبة.", 400)
    with db_session() as conn:
        return _set_balance(conn, user_id, amount, reason, reference)


def spend_credits(user_id: int, amount: int, reason: str,
                  reference: str | None = None) -> int:
    """تسوية نقاط (إنفاق) — ترفع 402 عند رصيد غير كافٍ."""
    if amount <= 0:
        raise BillingError("كمية النقاط يجب أن تكون موجبة.", 400)
    with db_session() as conn:
        return _set_balance(conn, user_id, -amount, reason, reference)


def has_sufficient_credits(user_id: int, amount: int) -> bool:
    return get_balance(user_id) >= amount


def list_ledger(user_id: int, limit: int = 20, offset: int = 0) -> list:
    """سجل حركة النقاط (الأحدث أولًا)."""
    limit = max(1, min(int(limit or 20), 100))
    offset = max(0, int(offset or 0))
    with db_session() as conn:
        rows = conn.execute(
            """SELECT id, delta, reason, reference, balance_after, tenant_id,
                      created_at
               FROM credit_ledger WHERE user_id = ?
               ORDER BY id DESC LIMIT ? OFFSET ?""",
            (user_id, limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# الظهور المميز
# ---------------------------------------------------------------------------

def get_premium_until(profile_id: int):
    with db_session() as conn:
        row = conn.execute(
            "SELECT premium_until FROM professional_profiles WHERE id = ?",
            (profile_id,),
        ).fetchone()
    return row["premium_until"] if row and row["premium_until"] else None


def is_profile_premium(profile_id: int) -> bool:
    """هل الملف مميز فعلًا الآن (انتهاء مستقبلي أو يساوي اليوم)؟"""
    until = get_premium_until(profile_id)
    if not until:
        return False
    try:
        return date.fromisoformat(until) >= _today()
    except ValueError:
        return False


def premium_status_for_user(user_id: int) -> dict:
    """حالة الظهور المميز بناءً على مستخدم (يُبحَث ملفه المحقَّق)."""
    with db_session() as conn:
        rows = conn.execute(
            "SELECT premium_until FROM professional_profiles "
            "WHERE user_id = ? AND verification_status = 'verified' "
            "ORDER BY id DESC LIMIT 1",
            (user_id,),
        ).fetchone()
    until = rows["premium_until"] if rows and rows["premium_until"] else None
    is_premium = False
    if until:
        try:
            is_premium = date.fromisoformat(until) >= _today()
        except ValueError:
            pass
    return {"until": until, "is_premium": is_premium}


def activate_premium(user_id: int, duration_days: int) -> dict:
    """يفعّل الظهور المميز لملف المستخدم المهني المحقَّق لمدة إضافية.

    يُمدَّد من تاريخ انتهاء الاشتراك القائم إن كان حاضرًا، وإلا من اليوم.
    """
    with db_session() as conn:
        sel_q = (
            "SELECT id, premium_until FROM professional_profiles "
            "WHERE user_id = ? AND verification_status = 'verified'"
        )
        sel_params = [user_id]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            sel_q += " AND " + cond
            sel_params.extend(vals)
        row = conn.execute(sel_q, sel_params).fetchone()
        if not row:
            raise BillingError(
                "الظهور المميز يتطلب ملفًا مهنيًا محقَّقًا (verified).", 400
            )
        base = _today()
        if row["premium_until"]:
            try:
                parsed = date.fromisoformat(row["premium_until"])
                base = max(base, parsed)
            except ValueError:
                pass
        new_until = (base + timedelta(days=duration_days)).strftime("%Y-%m-%d")
        upd_q = (
            "UPDATE professional_profiles SET premium_until = ?, "
            "updated_at = datetime('now') WHERE id = ?"
        )
        upd_params = [new_until, row["id"]]
        if cond:
            upd_q += " AND " + cond
            upd_params.extend(vals)
        conn.execute(upd_q, upd_params)
        return new_until


def set_premium_until_admin(profile_id: int, until: str | None):
    """إدارة فورية للظهور المميز (تسوية يدوية من لوحة التحكم)."""
    with db_session() as conn:
        sel_q = "SELECT id FROM professional_profiles WHERE id = ?"
        sel_params = [profile_id]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            sel_q += " AND " + cond
            sel_params.extend(vals)
        if conn.execute(sel_q, sel_params).fetchone() is None:
            raise BillingError("الملف المهني غير موجود.", 404)
        upd_q = (
            "UPDATE professional_profiles SET premium_until = ?, "
            "updated_at = datetime('now') WHERE id = ?"
        )
        upd_params = [until, profile_id]
        if cond:
            upd_q += " AND " + cond
            upd_params.extend(vals)
        conn.execute(upd_q, upd_params)


# ---------------------------------------------------------------------------
# الطلبات
# ---------------------------------------------------------------------------

def list_plans_admin() -> list:
    with db_session() as conn:
        rows = conn.execute(
            """SELECT p.*, (SELECT COUNT(*) FROM orders o WHERE o.plan_id = p.id)
               AS order_count FROM payment_plans p ORDER BY p.id""",
        ).fetchall()
        return [dict(r) | {"enabled": bool(r["enabled"])} for r in rows]


def create_plan(admin_id: int, data: dict) -> int:
    slug = (data.get("slug") or "").strip()
    name = (data.get("name") or "").strip()
    kind = (data.get("kind") or "").strip()
    if not slug or not name:
        raise BillingError("slug و name مطلوبان.", 400)
    if kind not in PLAN_KINDS:
        raise BillingError("kind يجب أن يكون credits أو premium_listing.", 400)
    try:
        price_cents = int(data.get("price_cents"))
        credits = int(data.get("credits") or 0)
    except (TypeError, ValueError):
        raise BillingError("price_cents و credits يجب أن يكونا رقمين.", 400)
    if price_cents < 0:
        raise BillingError("price_cents لا يمكن أن يكون سالبًا.", 400)
    duration_days = None
    if kind == "premium_listing":
        try:
            duration_days = int(data.get("duration_days"))
        except (TypeError, ValueError):
            raise BillingError("duration_days مطلوب لنوع premium_listing.", 400)
        if duration_days <= 0:
            raise BillingError("duration_days يجب أن يكون موجبًا.", 400)
    with db_session() as conn:
        if conn.execute(
            "SELECT 1 FROM payment_plans WHERE slug = ?", (slug,)
        ).fetchone():
            raise BillingError("يوجد طلب بنفس الـ slug.", 400)
        cur = conn.execute(
            """INSERT INTO payment_plans
               (slug, name, kind, price_cents, credits, duration_days,
                description, enabled)
               VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
            (slug, name, kind, price_cents,
             credits if kind == "credits" else 0, duration_days,
             (data.get("description") or "")),
        )
        plan_id = cur.lastrowid
    return plan_id


def update_plan(admin_id: int, plan_id: int, data: dict) -> int:
    with db_session() as conn:
        sel = conn.execute(
            "SELECT id FROM payment_plans WHERE id = ?", (plan_id,)
        ).fetchone()
        if not sel:
            raise BillingError("الباقة غير موجودة.", 404)
        updates = {}
        for col, cast in (("name", str), ("price_cents", int),
                          ("credits", int), ("duration_days", int),
                          ("description", str)):
            if col in data:
                updates[col] = cast(data[col])
        if "enabled" in data:
            updates["enabled"] = 1 if data["enabled"] else 0
        if not updates:
            raise BillingError("لا توجد حقول للتحديث.", 400)
        sets = ", ".join(f"{k} = ?" for k in updates)
        conn.execute(
            f"UPDATE payment_plans SET {sets} WHERE id = ?",
            list(updates.values()) + [plan_id],
        )
    return plan_id


def delete_plan(admin_id: int, plan_id: int) -> int:
    with db_session() as conn:
        if conn.execute(
            "SELECT 1 FROM payment_plans WHERE id = ?", (plan_id,)
        ).fetchone() is None:
            raise BillingError("الباقة غير موجودة.", 404)
        conn.execute("DELETE FROM payment_plans WHERE id = ?", (plan_id,))
    return plan_id


# ---------------------------------------------------------------------------
# الطلبات (سير عمل يدوي)
# ---------------------------------------------------------------------------

def create_order(user_id: int, plan_ident) -> dict:
    """ينشئ طلبًا pending (دفع يدوي). يُجمَّد السعر في الطلب نفسه."""
    with db_session() as conn:
        plan = _required_plan(conn, plan_ident)
        cur = conn.execute(
            """INSERT INTO orders
               (user_id, plan_id, amount_cents, status, payment_method,
                note, tenant_id)
               VALUES (?, ?, ?, 'pending', 'manual', ?, ?)""",
            (user_id, plan["id"], plan["price_cents"], "",
             tenant_scope.insert_tenant_id()),
        )
        order_id = cur.lastrowid
        order = get_order(conn, order_id)
    return order


def get_order(conn, order_id: int):
    row = conn.execute(
        """SELECT o.*, p.name AS plan_name, p.kind AS plan_kind,
                  p.credits AS plan_credits, p.duration_days AS plan_duration_days
           FROM orders o JOIN payment_plans p ON p.id = o.plan_id
           WHERE o.id = ?""",
        (order_id,),
    ).fetchone()
    if not row:
        return None
    return dict(row) | {"amount": round(row["amount_cents"] / 100, 2)}


def get_order_for_user(user_id: int, order_id: int):
    with db_session() as conn:
        row = conn.execute(
            "SELECT id FROM orders WHERE id = ?", (order_id,)
        ).fetchone()
        if not row:
            return None
        return get_order(conn, order_id)


def list_orders_for_user(user_id: int, limit: int = 50, offset: int = 0) -> list:
    limit = max(1, min(int(limit or 50), 100))
    offset = max(0, int(offset or 0))
    with db_session() as conn:
        rows = conn.execute(
            """SELECT o.*, p.name AS plan_name, p.kind AS plan_kind,
                      p.credits AS plan_credits
               FROM orders o JOIN payment_plans p ON p.id = o.plan_id
               WHERE o.user_id = ?
               ORDER BY o.id DESC LIMIT ? OFFSET ?""",
            (user_id, limit, offset),
        ).fetchall()
        return [
            dict(r) | {"amount": round(r["amount_cents"] / 100, 2)}
            for r in rows
        ]


def _apply_order_effect(conn, order, plan_kind: str, plan_credits: int,
                        plan_duration_days: int) -> None:
    """يطبّق أثر الطلب المدفوع على حساب/ملف المستخدم (نقاط أو ظهور مميز)."""
    user_id = order["user_id"]
    if plan_kind == "credits":
        _set_balance(
            conn, user_id, plan_credits, "order",
            f"order-{order['id']}",
        )
    elif plan_kind == "premium_listing":
        if plan_duration_days is None:
            raise BillingError("باقة الظهور المميز بلا مدة (duration_days).", 400)
        # التحقق من الملف المحقَّق + تفعيل المدة — داخل المعاملة نفسها
        sel_q = (
            "SELECT id, premium_until FROM professional_profiles "
            "WHERE user_id = ? AND verification_status = 'verified'"
        )
        sel_params = [user_id]
        cond, vals = tenant_scope.tenant_eq()
        if cond:
            sel_q += " AND " + cond
            sel_params.extend(vals)
        row = conn.execute(sel_q, sel_params).fetchone()
        if row is None:
            raise BillingError(
                "الظهور المميز يتطلب ملفًا مهنيًا محقَّقًا (verified).", 400
            )
        base = _today()
        if row["premium_until"]:
            try:
                parsed = date.fromisoformat(row["premium_until"])
                base = max(base, parsed)
            except ValueError:
                pass
        new_until = (base + timedelta(days=plan_duration_days)).strftime("%Y-%m-%d")
        upd_q = (
            "UPDATE professional_profiles SET premium_until = ?, "
            "updated_at = datetime('now') WHERE id = ?"
        )
        upd_params = [new_until, row["id"]]
        if cond:
            upd_q += " AND " + cond
            upd_params.extend(vals)
        conn.execute(upd_q, upd_params)


def confirm_order(admin_id: int, order_id: int) -> dict:
    """تأكيد أدمن لإثبات دفع يدوي — يفعِّل الأثر في معاملة ذرّية.

    يُقصى الطلب على paid أولًا (منع التكرار) ثم يُطبَّق الأثر؛ إن فشل
    الأثر (مثلاً ملف غير محقق) تُتراجع المعاملة كاملة وتبقى الحالة pending.
    """
    with db_session() as conn:
        row = conn.execute(
            "SELECT o.*, p.kind AS plan_kind, p.credits AS plan_credits, "
            "p.duration_days AS plan_duration_days "
            "FROM orders o JOIN payment_plans p ON p.id = o.plan_id "
            "WHERE o.id = ?",
            (order_id,),
        ).fetchone()
        if row is None:
            raise BillingError("الطلب غير موجود.", 404)
        if row["status"] != "pending":
            raise BillingError("الطلب ليس قيد الانتظار (paid/cancelled).", 400)
        conn.execute(
            "UPDATE orders SET status = 'paid', processed_by = ?, "
            "processed_at = datetime('now') WHERE id = ?",
            (admin_id, order_id),
        )
        _apply_order_effect(conn, row, row["plan_kind"],
                            row["plan_credits"], row["plan_duration_days"])
        return get_order(conn, order_id)


def cancel_order(admin_id: int, order_id: int, note: str | None = None) -> dict:
    """إلغاء طلب pending من الإدارة (لم يُحصَّل) — بلا أثر."""
    with db_session() as conn:
        row = conn.execute(
            "SELECT status FROM orders WHERE id = ?", (order_id,)
        ).fetchone()
        if row is None:
            raise BillingError("الطلب غير موجود.", 404)
        if row["status"] != "pending":
            raise BillingError("لا يمكن إلغاء طلب غير معلَّق.", 400)
        conn.execute(
            "UPDATE orders SET status = 'cancelled', processed_by = ?, "
            "processed_at = datetime('now'), note = ? WHERE id = ?",
            (admin_id, note or "", order_id),
        )
        return get_order(conn, order_id)


def user_cancel_order(user_id: int, order_id: int) -> dict:
    """إلغاء طلب معلَّق من قبل صاحبه (لم يُحصَّل بعد)."""
    with db_session() as conn:
        row = conn.execute(
            "SELECT status FROM orders WHERE id = ? AND user_id = ?",
            (order_id, user_id),
        ).fetchone()
        if row is None:
            raise BillingError("الطلب غير موجود.", 404)
        if row["status"] != "pending":
            raise BillingError("لا يمكن إلغاء الطلب المعالَج.", 400)
        conn.execute(
            "UPDATE orders SET status = 'cancelled', "
            "processed_at = datetime('now') WHERE id = ?",
            (order_id,),
        )
        return get_order(conn, order_id)


def list_orders_admin(status: str | None = None, limit: int = 100,
                      offset: int = 0) -> list:
    limit = max(1, min(int(limit or 100), 200))
    offset = max(0, int(offset or 0))
    query = (
        "SELECT o.*, p.name AS plan_name, p.kind AS plan_kind, "
        "u.full_name AS user_name, u.email AS user_email "
        "FROM orders o JOIN payment_plans p ON p.id = o.plan_id "
        "JOIN users u ON u.id = o.user_id"
    )
    params = []
    if status:
        status = status.strip()
        if status not in ORDER_STATUSES:
            raise BillingError("status غير صالح.", 400)
        query += " WHERE o.status = ?"
        params.append(status)
    query += " ORDER BY o.id DESC LIMIT ? OFFSET ?"
    params += [limit, offset]
    with db_session() as conn:
        rows = conn.execute(query, params).fetchall()
        return [
            dict(r) | {"amount": round(r["amount_cents"] / 100, 2)}
            for r in rows
        ]


def billing_summary() -> dict:
    """ملخص مالي للوحة التحكم (إيرادات مدفوعة، طلبات بانتظار، نقاط مصروفة)."""

    def _scalar(sql) -> int:
        with db_session() as conn:
            return conn.execute(sql).fetchone()[0] or 0

    paid = _scalar(
        "SELECT COALESCE(SUM(amount_cents),0) FROM orders WHERE status='paid'"
    )
    pending = _scalar(
        "SELECT COALESCE(SUM(amount_cents),0) FROM orders WHERE status='pending'"
    )
    paid_count = _scalar("SELECT COUNT(*) FROM orders WHERE status='paid'")
    pending_count = _scalar("SELECT COUNT(*) FROM orders WHERE status='pending'")
    credits_issued = _scalar(
        "SELECT COALESCE(SUM(delta),0) FROM credit_ledger WHERE delta > 0"
    )
    credits_spent = _scalar(
        "SELECT COALESCE(-SUM(delta),0) FROM credit_ledger WHERE delta < 0"
    )
    return {
        "revenue_cents": round(paid, 0),
        "revenue": round(paid / 100, 2),
        "pending_cents": round(pending, 0),
        "pending": round(pending / 100, 2),
        "paid_orders": paid_count,
        "pending_orders": pending_count,
        "credits_issued": credits_issued,
        "credits_spent": credits_spent,
    }
