"""
نطاق المستأجر الحالي — عزل بيانات multi-tenant (المرحلة 18 — قرار D-036).

يحمل سياق المستأجر النشط لكل طلب عبر ContextVar تُضبط من خطاف
before_request (فرض شامل: كل نقطة نهاية تطلب X-Tenant-Id عند التفعيل)
وتستعملها طبقة الخدمة لفرز القراءات والكتابات على الجداول المعزولة.

في الوضع أحادي المستأجر (الافتراضي) يبقى السياق None فلا يُطبَّق أي
فرز، وتُكتب القيم NULL وتُعالَج لاحقًا بالترحيل الافتراضي — سلوك
المراحل السابقة تمامًا. الوحدة بلا أي اعتماد على flask لتبقى الخدمات
قابلة للاستخدام من CLI/الاختبارات.
"""
import contextvars

from . import config

_current_tenant = contextvars.ContextVar("nibras_current_tenant", default=None)


def set_current_tenant(tenant_id):
    """يضبط مستأجر الطلب النشط (يُستدعى من before_request عند التفعيل)."""
    _current_tenant.set(tenant_id)


def clear_current_tenant():
    _current_tenant.set(None)


def current_tenant_id():
    """معرّف مستأجر الطلب النشط، أو None في الوضع أحادي المستأجر."""
    if not config.MULTI_TENANT:
        return None
    return _current_tenant.get()


def active() -> bool:
    """هل عزل المستأجر مفعَّل وفي سياق (مستأجر نطاق معيَّن حاليًا)؟"""
    return config.MULTI_TENANT and _current_tenant.get() is not None


def tenant_eq(alias=None):
    """جملة تساوي المستأجر الحالي: (شرط, قيم) أو (None, ()) عند انقطاع النطاق.

    alias: اسم الجدول/الاسم المستعار للجدول المعزول في الاستعلام.
    يُلحِق المتصل الشرط بصيغته (WHERE ... أو AND ...) مع قيمه.
    """
    tenant_id = current_tenant_id()
    if tenant_id is None:
        return None, ()
    col = f"{alias}.tenant_id" if alias else "tenant_id"
    return f"{col} = ?", (tenant_id,)


def insert_tenant_id():
    """قيمة tenant_id عند الإدراج: المستأجر النشط، أو None في الوضع أحادي
    المستأجر (تُعالَج NULL لاحقًا بترحيل backfill عند التفعيل)."""
    return current_tenant_id()
