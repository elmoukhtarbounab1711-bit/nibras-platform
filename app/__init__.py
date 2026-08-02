"""
تطبيق Flask الرئيسي لمنصة نبراس.

ينشئ التطبيق ويسجّل Blueprints الوحدات ويضيف بنية تحتية عامة
(health/ready, CORS, أمن الرؤوس, سجلات مهيكلة, error handlers).
يُعدَّل المحتوى لكل وحدة في routes/<module>.
"""
import logging
import sqlite3

from flask import Flask, jsonify, request

from . import config
from . import logging_utils as nibras_logging
from .database import db_session


def _add_cors_headers(response):
    """تقييد CORS بالنطاقات المهيأة بدل wildcard (Security Architecture §1)."""
    origin = request.headers.get("Origin")
    if origin:
        if origin in config.CORS_ALLOWED_ORIGINS or "*" in config.CORS_ALLOWED_ORIGINS:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Headers"] = (
            "Content-Type, Authorization"
        )
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Max-Age"] = "3600"
    return response


def _add_security_headers(response):
    """رؤوس أمن عامة على كل الاستجابات (المرحلة 11).

    API يخدم JSON فقط (الواجهة خادم منفصل)، لذلك لا تُضاف CSP هنا — يُوصى
    بضبطها في خادم الواجهة الأمامية عند تقديم HTML. الرؤوس هنا تمنع Sniffing
    أنواع المحتوى والتضمين في frames (وثيقة 12 Security Architecture §7).
    """
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=()"
    )
    return response


def create_app():
    app = Flask(__name__)
    app.json.ensure_ascii = False  # لعرض النصوص العربية كما هي بدل ترميز \u

    # السجلات المهيكلة + سجل الطلبات (يُهيَّأ قبل أي معالجة طلب)
    nibras_logging.configure_logging(app)

    # ضمان وجود المخطط وجداول الهوية والأدوار عند الإقلاع (ترحيل خفيف)
    from .database import init_db

    init_db()

    app.before_request(nibras_logging.log_request_start)
    app.after_request(nibras_logging.log_request_end)
    app.after_request(_add_security_headers)
    app.after_request(_add_cors_headers)

    @app.route("/api/health", methods=["GET"])
    def health():
        # حيوية (liveness): استجابتها ثابتة — نقطة منفصلة /api/ready للجاهزية
        return jsonify({"status": "ok", "service": "nibras-backend"})

    @app.route("/api/ready", methods=["GET"])
    def ready():
        """جاهزية (readiness): يتحقق من قابلية الوصول لقاعدة البيانات.

        يتضمن فحص المستأجر الافتراضي (المرحلة 17 — D-035) لضمان جاهزية
        البنية متعددة المستأجرين عند الإقلاع.
        """
        checks = {}
        try:
            with db_session() as conn:
                conn.execute("SELECT 1").fetchone()
            checks["database"] = "up"
        except sqlite3.Error as exc:
            logging.getLogger("nibras.ready").warning(
                "readiness_failed", extra={"check": "database", "reason": str(exc)}
            )
            checks["database"] = "down"
        if checks["database"] == "up":
            from .services_tenants import default_tenant_id

            try:
                default_tenant_id()
                checks["tenants"] = "up"
            except sqlite3.Error as exc:
                logging.getLogger("nibras.ready").warning(
                    "readiness_failed", extra={"check": "tenants", "reason": str(exc)}
                )
                checks["tenants"] = "down"
        if all(status == "up" for status in checks.values()):
            return jsonify({
                "status": "ready",
                "version": config.APP_VERSION,
                "checks": checks,
            }), 200
        return jsonify({
            "status": "not_ready",
            "version": config.APP_VERSION,
            "checks": checks,
        }), 503

    # تسجيل Blueprints الوحدات — تُضاف وحدات جديدة بملف blueprint في routes/
    from .routes.admin import admin_bp
    from .routes.ads import ads_bp
    from .routes.ai import ai_bp
    from .routes.auth import auth_bp
    from .routes.calculators import calculators_bp
    from .routes.community import community_bp
    from .routes.documents import documents_bp
    from .routes.library import library_bp
    from .routes.marketplace import marketplace_bp
    from .routes.notifications import notifications_bp
    from .routes.procedures import procedures_bp
    from .routes.professionals import professionals_bp

    app.register_blueprint(ads_bp)
    app.register_blueprint(library_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(calculators_bp)
    app.register_blueprint(procedures_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(professionals_bp)
    app.register_blueprint(community_bp)
    app.register_blueprint(marketplace_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(ai_bp)

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "المسار غير موجود"}), 404

    @app.errorhandler(500)
    def server_error(e):
        # تسجيل الاستثناء كاملاً (traceback) بدون كشف التفاصيل للمستجيب
        logging.getLogger("nibras.app").exception(
            "unhandled_error", extra={"path": request.path}
        )
        return jsonify({"error": "خطأ داخلي في الخادم"}), 500

    return app
