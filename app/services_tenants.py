"""
خدمات المستأجرين — جاهزية multi-tenant (المرحلة 17 — قرار D-035).

عزل الهوية فقط: جدول tenants مع مستأجر افتراضي مبذور (slug من
config.DEFAULT_TENANT_SLUG) وربط كل مستخدم بمستأجره عبر users.tenant_id
(ترحيل آمن للموجودين). دقة المستأجر عبر رأس X-Tenant-Id تُنفَّذ في
auth_middleware (رفض 403 عند غياب/تعطل/تعارض المستأجر) ولا تُفعَّل إلا
عند NIBRAS_MULTI_TENANT=1 — وإلا يُتجاهل الرأس ويبقى سلوك المستأجر
الواحد الحالي تمامًا. عزل بيانات الوحدات (مكتبة/مجتمع/سوق/إعلانات)
مؤجَّل لمرحلة multi-tenancy الفعلية — هنا البنية والهوية فقط.
"""
import re

from . import config
from .database import db_session
from .services_admin import _log_admin_action

# معرّف مستأجر صالح: أحرف لاتينية صغيرة وأرقام وشرطات (1-63)، بلا شرطة
# في البداية/النهاية (نمط أسماء الأكواد الفريدة)
_TENANT_SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


class TenantError(Exception):
    """خطأ تجاري في المستأجرين يُترجم إلى استجابة HTTP في routes."""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def get_tenant(tenant_id: int) -> dict | None:
    with db_session() as conn:
        row = conn.execute(
            "SELECT id, slug, name, status, created_at FROM tenants WHERE id = ?",
            (tenant_id,),
        ).fetchone()
    return dict(row) if row else None


def get_tenant_by_slug(slug: str) -> dict | None:
    with db_session() as conn:
        row = conn.execute(
            "SELECT id, slug, name, status, created_at FROM tenants WHERE slug = ?",
            ((slug or "").strip().lower(),),
        ).fetchone()
    return dict(row) if row else None


def resolve_tenant(identifier) -> dict | None:
    """يحل معرّف المستأجر من الرأس (رقم id أو slug) إلى صفه أو None."""
    if identifier is None or str(identifier).strip() == "":
        return None
    if str(identifier).strip().isdigit():
        return get_tenant(int(identifier))
    return get_tenant_by_slug(str(identifier))


def list_tenants() -> list:
    """قائمة المستأجرين مع عدد مستخدمي كل واحد (لللوحة الإدارية)."""
    with db_session() as conn:
        rows = conn.execute(
            """SELECT t.id, t.slug, t.name, t.status, t.created_at,
                      (SELECT COUNT(*) FROM users u WHERE u.tenant_id = t.id)
                       AS user_count
               FROM tenants t ORDER BY t.id ASC"""
        ).fetchall()
    return [dict(r) for r in rows]


def create_tenant(admin_id: int, name: str, slug: str) -> dict:
    """ينشئ مستأجرًا بتدقيق إداري (يُسجَّل في admin_audit_log — Security §8)."""
    name = (name or "").strip()
    slug = (slug or "").strip().lower()
    if not name:
        raise TenantError("اسم المستأجر مطلوب.", 400)
    if not _TENANT_SLUG_RE.match(slug):
        raise TenantError(
            "معرّف المستأجر: أحرف لاتينية صغيرة وأرقام وشرطات فقط (1-63) "
            "بلا شرطة في البداية/النهاية.",
            400,
        )
    with db_session() as conn:
        exists = conn.execute(
            "SELECT id FROM tenants WHERE slug = ?", (slug,)
        ).fetchone()
        if exists:
            raise TenantError("معرّف المستأجر مستخدم مسبقًا.", 409)
        cur = conn.execute(
            "INSERT INTO tenants (slug, name) VALUES (?,?)", (slug, name)
        )
        tenant_id = cur.lastrowid
        _log_admin_action(
            conn, admin_id, "tenant.create", "tenant", tenant_id,
            f"slug={slug}",
        )
    return get_tenant(tenant_id)


def ensure_defaults() -> int:
    """يبذر المستأجر الافتراضي إن لم يوجد (idempotent) ويعيد معرفه."""
    with db_session() as conn:
        row = conn.execute(
            "SELECT id FROM tenants WHERE slug = ?", (config.DEFAULT_TENANT_SLUG,)
        ).fetchone()
        if row is not None:
            return row["id"]
        return conn.execute(
            "INSERT INTO tenants (slug, name) VALUES (?,?)",
            (config.DEFAULT_TENANT_SLUG, "المستأجر الرئيسي"),
        ).lastrowid


def default_tenant_id() -> int:
    return ensure_defaults()


def get_user_tenant_id(user_id: int) -> int | None:
    with db_session() as conn:
        row = conn.execute(
            "SELECT tenant_id FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    return row["tenant_id"] if row else None


def backfill_default_tenant() -> int:
    """يلحق المستخدمين بلا مستأجر بالمستأجر الافتراضي (ترحيل قديم idempotent)."""
    default_id = ensure_defaults()
    with db_session() as conn:
        conn.execute(
            "UPDATE users SET tenant_id = ? WHERE tenant_id IS NULL", (default_id,)
        )
    return default_id


# جداول عزل بيانات الوحدات (قرار D-036) — تُملأ tenant_id في الترحيل القديم
_ISOLATED_TABLES = (
    "categories",
    "legal_texts",
    "articles",
    "professional_profiles",
    "professional_specialties",
    "professional_reviews",
    "posts",
    "comments",
    "reactions",
    "reports",
    "marketplace_categories",
    "marketplace_templates",
    "purchases",
    "ad_campaigns",
    "ad_events",
    "jurisprudence_categories",
    "jurisprudence",
)


def backfill_isolated_tables() -> int:
    """يلحق صفوف الجداول الـ 15 المعزولة بلا مستأجر بالمستأجر الافتراضي.

    ترحيل قديم (قواعد أُنشئت قبل المرحلة 18): عند تفعيل multi-tenancy
    لاحقًا يجب ألا يفلت أي صف من الفلترة. idempotent — يلمس صفوف NULL فقط.
    """
    default_id = ensure_defaults()
    with db_session() as conn:
        for table in _ISOLATED_TABLES:
            conn.execute(
                f"UPDATE {table} SET tenant_id = ? WHERE tenant_id IS NULL",
                (default_id,),
            )
    return default_id
