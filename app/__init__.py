"""
تطبيق Flask الرئيسي لمنصة نبراس.

ينشئ التطبيق ويسجّل Blueprints الوحدات ويضيف بنية تحتية عامة
(health, CORS, error handlers). يُعدَّل المحتوى لكل وحدة في routes/<module>.
"""
from flask import Flask, jsonify, request

from . import config


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


def create_app():
    app = Flask(__name__)
    app.json.ensure_ascii = False  # لعرض النصوص العربية كما هي بدل ترميز \u

    # ضمان وجود المخطط وجداول الهوية والأدوار عند الإقلاع (ترحيل خفيف)
    from .database import init_db

    init_db()

    app.after_request(_add_cors_headers)

    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "service": "nibras-backend"})

    # تسجيل Blueprints الوحدات — تُضاف وحدات جديدة بملف blueprint في routes/
    from .routes.admin import admin_bp
    from .routes.auth import auth_bp
    from .routes.library import library_bp

    app.register_blueprint(library_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "المسار غير موجود"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "خطأ داخلي في الخادم"}), 500

    return app
