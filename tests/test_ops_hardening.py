"""
اختبارات الصلابة التشغيلية (المرحلة 11): السجلات المهيكلة، رؤوس الأمن،
نقاط الحيوية/الجاهزية، ومعرّف الطلب.
"""
import logging
import sqlite3

from app import logging_utils
from app.logging_utils import _JsonFormatter

# ---------------------------------------------------------------------------
# نقاط الحيوية والجاهزية
# ---------------------------------------------------------------------------

def test_health_liveness_unchanged(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok", "service": "nibras-backend"}


def test_ready_reports_database_up(client):
    r = client.get("/api/ready")
    assert r.status_code == 200
    body = r.get_json()
    assert body["status"] == "ready"
    # المرحلة 17 (D-035): يُضاف فحص المستأجر الافتراضي إلى تقرير الجاهزية
    assert body["checks"] == {"database": "up", "tenants": "up"}
    assert "version" in body


def test_ready_returns_503_when_db_down(client, monkeypatch):
    from app import database

    def _boom():
        raise sqlite3.OperationalError("connection refused")

    monkeypatch.setattr(database, "get_connection", _boom)
    r = client.get("/api/ready")
    assert r.status_code == 503
    assert r.get_json()["checks"] == {"database": "down"}


# ---------------------------------------------------------------------------
# رؤوس الأمن
# ---------------------------------------------------------------------------

def test_security_headers_present(client):
    r = client.get("/api/health")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "geolocation=()" in r.headers["Permissions-Policy"]


# ---------------------------------------------------------------------------
# معرّف الطلب
# ---------------------------------------------------------------------------

def test_request_id_generated(client):
    r = client.get("/api/health")
    request_id = r.headers.get("X-Request-ID")
    assert request_id and len(request_id) >= 8


def test_request_id_echoes_client_value(client):
    r = client.get("/api/health", headers={"X-Request-ID": "trace-abc-123"})
    assert r.headers.get("X-Request-ID") == "trace-abc-123"


# ---------------------------------------------------------------------------
# السجلات المهيكلة
# ---------------------------------------------------------------------------

def test_request_log_emits_structured_fields(client, caplog):
    caplog.set_level(logging.INFO)
    client.get("/api/health")
    records = [
        rec for rec in caplog.records
        if rec.name == "nibras.request" and rec.getMessage() == "http_request"
    ]
    assert records, "لم يُصدر سجل الطلب"
    record = records[-1]
    assert record.method == "GET"
    assert record.path == "/api/health"
    assert record.status == 200
    assert record.request_id
    assert "duration_ms" in record.__dict__


def test_json_formatter_includes_extra_and_redacts_secrets():
    formatter = _JsonFormatter()
    logger = logging.getLogger("nibras.test")
    record = logger.makeRecord(
        logger.name, logging.INFO, __file__, 1,
        "operation", (), None,
        extra={"user_id": 7, "password": "supersecret", "request_id": "abc"},
    )
    line = formatter.format(record)
    assert '"user_id": 7' in line
    assert '"request_id": "abc"' in line
    assert "supersecret" not in line
    assert '"password": "[REDACTED]"' in line


def test_json_formatter_output_is_valid_json():
    import json

    formatter = _JsonFormatter()
    logger = logging.getLogger("nibras.test2")
    record = logger.makeRecord(
        logger.name, logging.WARNING, __file__, 1, "رسالة عربية", (),
        None, extra={"status": 200},
    )
    parsed = json.loads(formatter.format(record))
    assert parsed["message"] == "رسالة عربية"
    assert parsed["status"] == 200


def test_configure_logging_is_idempotent(app):
    root = logging.getLogger()
    before = sum(1 for h in root.handlers if getattr(h, "_nibras", False))
    logging_utils.configure_logging(app)
    after = sum(1 for h in root.handlers if getattr(h, "_nibras", False))
    assert after == before == 1
