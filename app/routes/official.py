"""
مسارات المصادر الرسمية — API endpoints للتحقق والمزامنة.

المبدأ: Nibras لا يؤلف القانون.
"""
from flask import Blueprint, jsonify, request

from ..database import db_session
from ..services_official import (
    get_text_source_info,
    verify_text,
    sync_status,
    backfill_all,
    verify_all_texts,
    OfficialSourceImporter,
    OfficialLegalSourcesSync,
)

bp = Blueprint("official", __name__)


@bp.route("/api/official/status")
def official_status():
    """حالة نظام المصادر الرسمية."""
    return jsonify(sync_status())


@bp.route("/api/official/verify/<int:text_id>")
def official_verify(text_id: int):
    """التحقق من تطابق النص مع بصمته الأصلية."""
    return jsonify(verify_text(text_id))


@bp.route("/api/official/verify-all", methods=["POST"])
def official_verify_all():
    """التحقق من جميع النصوص."""
    return jsonify(verify_all_texts())


@bp.route("/api/official/source/<int:text_id>")
def official_source(text_id: int):
    """معلومات مصدر النص القانوني."""
    info = get_text_source_info(text_id)
    if "error" in info:
        return jsonify(info), 404
    return jsonify(info)


@bp.route("/api/official/backfill", methods=["POST"])
def official_backfill():
    """ملء البصمات وبيانات المصدر للنصوص الموجودة."""
    return jsonify(backfill_all())


@bp.route("/api/official/sync-status")
def official_sync_status():
    """حالة المزامنة التفصيلية."""
    return jsonify(OfficialLegalSourcesSync.sync_status())
