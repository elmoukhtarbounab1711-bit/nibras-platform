"""
السجلات المهيكلة (المرحلة 11 — الصلابة التشغيلية).

تُوحَّد السجلات عبر logging وحدة Python: مُنسِّق JSON (سطر واحد لكل سجل)
أو key=value للنصوص، مع سجل لكل طلب HTTP (method/path/status/duration_ms/
request_id/remote_addr/user_id) يُكتب بعد كل استجابة. تُحمى الحقول الحساسة
من التسرّب دفاعًا متعدد الطبقات (تُحوَّل قيمها إلى [REDACTED] في المُنسِّق
إن وُجدت في extra). تفعيل التهيئة: configure_logging(app) في create_app.
"""
import json
import logging
import time
import uuid

from flask import g, request

from . import config

# مسار معالج الطلبات والتهيئة
_REQUEST_LOGGER = "nibras.request"
_CONFIG_LOGGER = "nibras.config"

# مفاتيح حساسة تُحوَّل قيمها إلى [REDACTED] في المُنسِّق (طبقة حماية إضافية:
# الأساس هو عدم تمرير القيم الحساسة إلى السجلات أصلًا)
_SENSITIVE_KEYS = frozenset({
    "password", "password_hash", "old_password", "new_password",
    "token", "refresh_token", "access_token", "authorization", "secret",
    "api_key", "email",
})

# أزواج انعطاف قيمة الحقول في صيغة النص (تحسين قابلية قراءة المحطة)
_TEXT_FORMAT = "{ts} {level:<7} {logger} {message}{extra}"


# حقول LogRecord القياسية المستبعَدة من الحقول المهيكلة (الباقي = extra)
_STANDARD_FIELDS = frozenset({
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "message", "taskName",
})


def _structured_fields(record: logging.LogRecord) -> dict:
    """حقول extra المندمجة في السجل (تستبعد القياسية وما يبدأ بـ _)."""
    return {
        key: _redact(key, value)
        for key, value in record.__dict__.items()
        if not key.startswith("_") and key not in _STANDARD_FIELDS
    }


class _JsonFormatter(logging.Formatter):
    """مُنسِّق يكتب كل سجل كسطر JSON واحد مع حقول extra مهيكلة."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        payload.update(_structured_fields(record))
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


class _TextFormatter(logging.Formatter):
    """مُنسِّق key=value للمراجعة المحلية (NIBRAS_LOG_FORMAT=text)."""

    def format(self, record: logging.LogRecord) -> str:
        tail = " ".join(
            f"{k}={v}" for k, v in _structured_fields(record).items()
        )
        suffix = f" {tail}" if tail else ""
        return _TEXT_FORMAT.format(
            ts=self.formatTime(record, "%Y-%m-%d %H:%M:%S"),
            level=record.levelname,
            logger=record.name,
            message=record.getMessage(),
            extra=suffix,
        )


def _redact(key: str, value):
    if key.lower() in _SENSITIVE_KEYS and value is not None:
        return "[REDACTED]"
    return value


class _SafeStreamHandler(logging.StreamHandler):
    """معالج مخرجات لا ينهار على وحدات تحكم لا تدعم العربية (مثل cp1252):
    عند فشل الترميز يُعيد الكتابة بترميز ASCII آمن (backslashreplace)."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            super().emit(record)
        except UnicodeEncodeError:
            try:
                msg = self.format(record)
                self.stream.write(
                    msg.encode("ascii", "backslashreplace").decode("ascii")
                    + self.terminator
                )
                self.flush()
            except (OSError, ValueError, UnicodeError):
                self.handleError(record)


def _handler() -> logging.Handler:
    handler = _SafeStreamHandler()
    handler.setFormatter(
        _JsonFormatter() if config.LOG_FORMAT.lower() == "json"
        else _TextFormatter()
    )
    return handler


def configure_logging(app=None):
    """يضبط سجل الجذر ومعالج الطلبات (idempotent — يزيل المعالجات المكررة).

    يُستدعى في create_app قبل تسجيل Blueprints. `app` اختياري لعزل السجلات
    في الاختبارات (اختبار التطبيق يكوِّن root طالما لم يُضبط سجل مخصص).
    """
    level = getattr(logging, str(config.LOG_LEVEL).upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(level)
    for existing in list(root.handlers):
        if getattr(existing, "_nibras", False):
            root.removeHandler(existing)
    handler = _handler()
    handler._nibras = True
    root.addHandler(handler)


def get_request_logger():
    return logging.getLogger(_REQUEST_LOGGER)


def get_config_logger():
    return logging.getLogger(_CONFIG_LOGGER)


def log_request_start():
    """يُخزِّن بداية الطلب ومعرّفه في سياق الطلب (قبل المعالجة)."""
    g.request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    g.request_start = time.perf_counter()


def log_request_end(response):
    """يُسجّل الطلب بعد الاستجابة ويضيف رأس X-Request-ID (معالجة الطلب)."""
    duration_ms = (time.perf_counter() - g.request_start) * 1000
    response.headers["X-Request-ID"] = g.request_id
    if config.LOG_ACCESS:
        user = getattr(request, "user", None)
        get_request_logger().info(
            "http_request",
            extra={
                "request_id": g.request_id,
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "remote_addr": request.remote_addr or "",
                "user_id": getattr(user, "id", None),
            },
        )
    return response
