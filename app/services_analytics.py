"""
خدمات لوحة التحليلات الإدارية (المرحلة 8 — إتمام Roadmap Phase 6، قرار D-026).

تجميع قراءة-فقط (Admin Panel 20 §3.6 + Functional Spec 04 §12) من جداول
الوحدات القائمة: الاستخدام (المستخدمون، AI، الحاسبات، الوثائق، المجتمع،
الملفات المهنية، السوق) + الطابوران (التحقق والإشراف) + اتجاه 7 أيام.
التحويل (free→premium) والإيرادات (اشتراكات/سوق/إعلانات) صفرية ومؤجَّلة
مع وحدة الفوترة (BRD §5) — تُعاد قيمها 0 مع ملاحظة. بُعد "البحث" غير متاح
لأن البحث لا يُسجَّل في جدول (لا search_log). يُستدعى من نقطة إدارية واحدة
GET /api/admin/analytics/summary (دور admin) في routes/admin.py.
"""
from .database import db_session
from .services_auth import PROFESSIONAL_ROLES


def _count(conn, table: str, where: str = "", params=()) -> int:
    return conn.execute(
        f"SELECT COUNT(*) AS c FROM {table} {where}", params
    ).fetchone()["c"]


def _count_where(conn, table: str, column: str, value) -> int:
    return _count(conn, table, f"WHERE {column} = ?", (value,))


def _role_placeholders() -> str:
    return ", ".join("?" for _ in sorted(PROFESSIONAL_ROLES))


def _count_role(conn, code: str, role_status: str | None = None) -> int:
    """عدد المستخدمين بدور محدد (اختياري مع حالة دور)."""
    where = ["r.code = ?"]
    params = [code]
    if role_status:
        where.append("ur.role_status = ?")
        params.append(role_status)
    return conn.execute(
        f"""SELECT COUNT(DISTINCT u.id) AS c
            FROM users u
            JOIN user_roles ur ON ur.user_id = u.id
            JOIN roles r ON r.id = ur.role_id
            WHERE {" AND ".join(where)}""",
        params,
    ).fetchone()["c"]


def _count_professional_role(conn, role_status: str) -> int:
    """عدد الحسابات المهنية حسب حالة دورها (بند الطابور/المجالات)."""
    return conn.execute(
        f"""SELECT COUNT(DISTINCT u.id) AS c
            FROM users u
            JOIN user_roles ur ON ur.user_id = u.id
            JOIN roles r ON r.id = ur.role_id
            WHERE r.code IN ({_role_placeholders()})
              AND ur.role_status = ?""",
        (*sorted(PROFESSIONAL_ROLES), role_status),
    ).fetchone()["c"]


def _users(conn) -> dict:
    return {
        "total": _count(conn, "users"),
        "active": _count_where(conn, "users", "status", "active"),
        "suspended": _count_where(conn, "users", "status", "suspended"),
        "admins": _count_role(conn, "admin"),
        "professionals_pending": _count_professional_role(conn,
                                                          "pending_verification"),
        "professionals_active": _count_professional_role(conn, "active"),
        "new_today": _count(conn, "users",
                            "WHERE date(created_at) = date('now')"),
    }


def _ai(conn) -> dict:
    return {
        "total": _count(conn, "ai_queries"),
        "today": _count(conn, "ai_queries",
                        "WHERE date(created_at) = date('now')"),
        "by_mode": {
            r["mode"]: r["c"]
            for r in conn.execute(
                "SELECT mode, COUNT(*) AS c FROM ai_queries "
                "GROUP BY mode ORDER BY mode"
            )
        },
    }


def _calculators(conn) -> dict:
    return {
        "total_runs": _count(conn, "calculator_runs"),
        "today": _count(conn, "calculator_runs",
                        "WHERE date(created_at) = date('now')"),
        "distinct_calculators": conn.execute(
            "SELECT COUNT(DISTINCT calculator_id) AS c FROM calculator_runs"
        ).fetchone()["c"],
        "by_calculator": {
            r["slug"]: r["c"]
            for r in conn.execute(
                """SELECT c.slug, COUNT(*) AS c
                   FROM calculator_runs cr
                   JOIN calculators c ON c.id = cr.calculator_id
                   GROUP BY c.slug ORDER BY c.slug"""
            )
        },
    }


def _documents(conn) -> dict:
    return {
        "generated_total": _count(conn, "generated_documents"),
        "generated_today": _count(conn, "generated_documents",
                                  "WHERE date(created_at) = date('now')"),
        "templates": _count(conn, "document_templates"),
    }


def _community(conn) -> dict:
    return {
        "posts": _count(conn, "posts"),
        "comments": _count(conn, "comments"),
        "reactions": _count(conn, "reactions"),
        "reports_open": _count_where(conn, "reports", "status", "open"),
        "reports_resolved": _count(
            conn, "reports", "WHERE status IN ('actioned', 'dismissed')"
        ),
    }


def _professionals(conn) -> dict:
    by_status = {
        r["verification_status"]: r["c"]
        for r in conn.execute(
            "SELECT verification_status, COUNT(*) AS c "
            "FROM professional_profiles GROUP BY verification_status"
        )
    }
    avg_rating = conn.execute(
        "SELECT AVG(rating) AS avg FROM professional_reviews"
    ).fetchone()["avg"]
    return {
        "profiles_total": _count(conn, "professional_profiles"),
        "by_status": by_status,
        "reviews": _count(conn, "professional_reviews"),
        "avg_rating": round(avg_rating, 1) if avg_rating is not None else None,
    }


def _marketplace(conn) -> dict:
    value = conn.execute(
        "SELECT COALESCE(SUM(price_cents), 0) AS total "
        "FROM marketplace_templates"
    ).fetchone()["total"]
    return {
        "templates": _count(conn, "marketplace_templates"),
        "catalog_value_cents": value,
        "purchases": _count(conn, "purchases"),
    }


def _verification(conn) -> dict:
    """طابور التحقق المعلّق — نفس تعريف طابور التحقق في الإدارة."""
    return {"pending_requests": _count_professional_role(
        conn, "pending_verification"
    )}


def _moderation(conn) -> dict:
    return {"open_reports": _count_where(conn, "reports", "status", "open")}


def _revenue() -> dict:
    return {
        "subscriptions_cents": 0,
        "marketplace_cents": 0,
        "ads_cents": 0,
        "note": "الفوترة مؤجَّلة (BRD §5): الإيرادات صفرية حتى بناء وحدة الفوترة.",
    }


def _daily_series(conn, table: str, column: str = "created_at") -> dict:
    return {
        r["d"]: r["c"]
        for r in conn.execute(
            f"""SELECT date({column}) AS d, COUNT(*) AS c FROM {table}
                WHERE date({column}) >= date('now', '-6 days')
                GROUP BY d"""
        )
    }


def _trends(conn) -> list:
    series = [
        ("ai_queries", "ai_queries", "created_at"),
        ("calculator_runs", "calculator_runs", "created_at"),
        ("documents", "generated_documents", "created_at"),
        ("new_users", "users", "created_at"),
    ]
    series_data = [
        (name, _daily_series(conn, table, column))
        for name, table, column in series
    ]
    days = []
    for i in range(6, -1, -1):
        date = conn.execute(
            f"SELECT date('now', '-{i} days') AS d"
        ).fetchone()["d"]
        entry = {"date": date}
        for name, data in series_data:
            entry[name] = data.get(date, 0)
        days.append(entry)
    return days


def summary() -> dict:
    """ملخص التحليلات الإداري — قراءة-فقط من الجداول القائمة (قرار D-026)."""
    with db_session() as conn:
        return {
            "generated_at": conn.execute(
                "SELECT datetime('now') AS t"
            ).fetchone()["t"],
            "users": _users(conn),
            "ai": _ai(conn),
            "calculators": _calculators(conn),
            "documents": _documents(conn),
            "community": _community(conn),
            "professionals": _professionals(conn),
            "marketplace": _marketplace(conn),
            "verification": _verification(conn),
            "moderation": _moderation(conn),
            "revenue": _revenue(),
            "trends": _trends(conn),
        }
