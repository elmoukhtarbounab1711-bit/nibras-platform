"""
سكربت تفريغ صندوق الإشعارات الخارجية (CLI) — المرحلة 16 (قرار D-034).

الاستخدام:
    python -m app.flush_notifications            # تفريغ بالسقف الافتراضي
    python -m app.flush_notifications 100        # تفريغ حتى 100 صف

يُستدعى يدويًا أو من جدولة (cron/CI) في الإنتاج — لا توجد بنية خلفية
مسبقة. المزوّدان الافترضيان noop/console يسجّلان الإرسال بلا شبكة
(NIBRAS_EMAIL_PROVIDER / NIBRAS_PUSH_PROVIDER).
"""
import sys


def _print(text: str) -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(text)


def main() -> int:
    from .services_notifications import deliver_pending

    limit = None
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            _print(f"خطأ: وسيط غير رقمي: {sys.argv[1]}")
            return 1
    result = deliver_pending(limit=limit)
    _print(
        "تم تفريغ الصندوق: "
        f"معالجة={result['processed']} مرسلة={result['sent']} فاشلة={result['failed']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
