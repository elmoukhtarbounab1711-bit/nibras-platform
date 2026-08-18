"""
تطبيق Flask الرئيسي لمنصة نبراس.

ينشئ التطبيق ويسجّل Blueprints الوحدات ويضيف بنية تحتية عامة
(health/ready, CORS, أمن الرؤوس, سجلات مهيكلة, error handlers).
يُعدَّل المحتوى لكل وحدة في routes/<module>.
"""
import logging
import os
import sqlite3
from pathlib import Path

from flask import Flask, jsonify, request

from . import config, tenant_scope
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
            "Content-Type, Authorization, X-Tenant-Id"
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
    # HSTS (P1-2): يُفعَّل فقط عبر NIBRAS_HSTS_ENABLED=1 (خلف HTTPS proxy).
    # لا يُضاف على HTTP المحلي لتجنب حظر المتصفح للموقع.
    if config.HSTS_ENABLED:
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
    return response


# مسارات حساسة تتطلب Cache-Control: no-store (P1-3)
_SENSITIVE_PATHS = (
    "/api/auth/",
    "/api/notifications",
    "/api/admin/",
)


def _add_cache_control(response):
    """يمنع التخزين المؤقت للمحتوى الحساس (حسابات، إشعارات، إدارة)."""
    path = request.path
    if any(path.startswith(p) for p in _SENSITIVE_PATHS):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return response


def _ensure_database():
    """تحميل قاعدة البيانات من URL إن لم تكن موجودة (النشر المجاني)."""
    import gzip
    import shutil
    import urllib.request as _urlreq
    from .database import DB_PATH

    if DB_PATH.exists() and DB_PATH.stat().st_size > 1000:
        return

    url = os.environ.get("NIBRAS_DB_URL", "").strip()
    if not url:
        return

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(DB_PATH) + ".gz.tmp")
    try:
        logging.getLogger("nibras.startup").info("Downloading DB from %s", url)
        req = _urlreq.Request(url, headers={"User-Agent": "nibras/1.0"})
        with _urlreq.urlopen(req, timeout=300) as resp:
            with open(tmp, "wb") as f:
                shutil.copyfileobj(resp, f)
        with gzip.open(tmp, "rb") as f_in, open(DB_PATH, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        tmp.unlink(missing_ok=True)
        logging.getLogger("nibras.startup").info(
            "DB ready: %.1f MB", DB_PATH.stat().st_size / 1024 / 1024
        )
    except Exception:
        logging.getLogger("nibras.startup").exception("DB download failed")
        tmp.unlink(missing_ok=True)


def create_app():
    app = Flask(__name__)
    app.json.ensure_ascii = False  # لعرض النصوص العربية كما هي بدل ترميز \u

    # السجلات المهيكلة + سجل الطلبات (يُهيَّأ قبل أي معالجة طلب)
    nibras_logging.configure_logging(app)

    # تحميل قاعدة البيانات إن كانت ناقصة (النشر المجاني بدون قرص)
    _ensure_database()

    # ضمان وجود المخطط وجداول الهوية والأدوار عند الإقلاع (ترحيل خفيف)
    from .database import init_db

    init_db()

    # تسخين ذاكرة التخزين المؤقت للصفحات عند الإقلاع: قراءة فهرسة شاملة
    # ليتحمَّل أول طلب بعد الإقلاع دون انتظار قراءة قاعدة البيانات من القرص.
    from . import services

    services.library_stats()
    services.list_categories()
    services.list_texts(limit=8)

    app.before_request(nibras_logging.log_request_start)
    app.after_request(nibras_logging.log_request_end)
    app.after_request(_add_security_headers)
    app.after_request(_add_cors_headers)
    app.after_request(_add_cache_control)

    @app.before_request
    def _tenant_enforcement():
        """فرض شامل لنطاق المستأجر (المرحلة 18 — قرار D-036).

        عند NIBRAS_MULTI_TENANT=1 كل نقطة نهاية تطلب رأس X-Tenant-Id
        (معرّف رقمي أو slug لمستأجر نشط) — غيابه/جهله/تعليقه يرفض الطلب
        403، ويُضبط السياق الحالي لنطاق بيانات الخدمات. يُستثنى فحصا
        الحيوية/الجاهزية (مسابر بنية تحتية بلا نطاق) وطلبات CORS المسبقة.
        في الوضع أحادي المستأجر (الافتراضي) يُصفَّر السياق فلا يُطبَّق
        أي فرز — سلوك المراحل السابقة تمامًا.
        """
        if not config.MULTI_TENANT:
            tenant_scope.clear_current_tenant()
            return None
        if request.method == "OPTIONS" or request.path in ("/api/health", "/api/ready"):
            tenant_scope.clear_current_tenant()
            return None
        from .services_tenants import resolve_tenant

        header = request.headers.get("X-Tenant-Id")
        if not header:
            return jsonify({
                "error": "رأس X-Tenant-Id مطلوب في الوضع متعدد المستأجرين."
            }), 403
        tenant = resolve_tenant(header)
        if tenant is None or tenant["status"] != "active":
            return jsonify({"error": "مستأجر غير معروف أو غير نشط."}), 403
        tenant_scope.set_current_tenant(tenant["id"])
        request.tenant_id = tenant["id"]
        return None

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
    from .routes.admin_ai import admin_ai_bp
    from .routes.ads import ads_bp
    from .routes.ai import ai_bp
    from .routes.auth import auth_bp
    from .routes.billing import billing_bp
    from .routes.blog import blog_bp
    from .routes.calculators import calculators_bp
    from .routes.community import community_bp
    from .routes.comp import comp_bp
    from .routes.comparative import comparative_bp
    from .routes.documents import documents_bp
    from .routes.jurisprudence import jurisprudence_bp
    from .routes.legal_french import legal_french_bp
    from .routes.library import library_bp
    from .routes.marketplace import marketplace_bp
    from .routes.notifications import notifications_bp
    from .routes.procedures import procedures_bp
    from .routes.professionals import professionals_bp
    from .routes.research import research_bp
    from .routes.treaties import treaties_bp

    app.register_blueprint(ads_bp)
    app.register_blueprint(library_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_ai_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(calculators_bp)
    app.register_blueprint(procedures_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(professionals_bp)
    app.register_blueprint(jurisprudence_bp)
    app.register_blueprint(legal_french_bp)
    app.register_blueprint(community_bp)
    app.register_blueprint(comparative_bp)
    app.register_blueprint(comp_bp)
    app.register_blueprint(research_bp)
    app.register_blueprint(marketplace_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(blog_bp)
    app.register_blueprint(treaties_bp)

    # ------------------------------------------------------------------
    # خدمة ملفات الواجهة الأمامية على نفس الخادم (مرحلة الواجهة):
    # frontend/ تُقدم على / (واجهة SPA) و/admin (لوحة الإدارة) و/assets.
    # لا تُغيّر أي نقطة API — الواجهة نفس الأصل فتتحدث إلى /api مباشرة.
    # ------------------------------------------------------------------
    from pathlib import Path as _Path

    from flask import abort, send_from_directory

    frontend_dir = _Path(config.FRONTEND_DIR)
    _assets_dir = frontend_dir / "assets"
    _vendor_dir = frontend_dir / "vendor"

    def _page(name: str):
        def serve_page():
            path = frontend_dir / name
            if not path.exists():
                abort(404)
            return send_from_directory(frontend_dir, name)
        serve_page.__name__ = f"serve_{name.replace('.', '_')}"
        return serve_page

    app.add_url_rule("/", "frontend_index", _page("index.html"))
    app.add_url_rule("/index.html", "frontend_index_alt", _page("index.html"))
    app.add_url_rule("/admin", "frontend_admin", _page("admin.html"))
    app.add_url_rule("/admin/", "frontend_admin_slash", _page("admin.html"))
    app.add_url_rule("/admin.html", "frontend_admin_alt", _page("admin.html"))

    @app.route("/assets/<path:filename>")
    def frontend_assets(filename):
        return send_from_directory(str(_assets_dir), filename)

    @app.route("/vendor/<path:filename>")
    def frontend_vendor(filename):
        return send_from_directory(str(_vendor_dir), filename)

    @app.route("/<path:path>")
    def spa_catch_all(path):
        _api_prefixes = ("api/", "assets/", "vendor/")
        if any(path.startswith(p) for p in _api_prefixes):
            abort(404)
        return send_from_directory(str(frontend_dir), "index.html")

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
