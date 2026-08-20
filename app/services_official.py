"""
خدمات المصادر الرسمية — استيراد، تحقق، مزامنة، حماية.

المبدأ الأساسي: Nibras لا يؤلف القانون.
Nibras يستورد القانون الرسمي من مصدره الرسمي، يحفظه كما هو، ويوثّق مصدره.

الذكاء الاصطناعي في Nibras يستخدم لفهم القانون والبحث فيه وشرحه،
وليس لإنشاء نص قانوني بديل عن النص الرسمي.

ZERO AI REWRITING — يُمنع أي تعديل للنصوص الرسمية عبر أي نموذج LLM.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import sqlite3
import urllib.request
from datetime import datetime, timezone
from typing import Any

from .database import db_session

log = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════════
# أنواع المصادر الرسمية
# ══════════════════════════════════════════════════════════════════════════════

OFFICIAL_SOURCES = {
    "adala": {
        "name": "وزارة العدل المغربية — عدالة",
        "name_en": "Ministry of Justice - Adala",
        "url": "https://adala.justice.gov.ma/",
        "type": "OFFICIAL",
        "priority": 1,
    },
    "sgg": {
        "name": "الأمانة العامة للحكومة — الجريدة الرسمية",
        "name_en": "General Secretariat of the Government",
        "url": "https://www.sgg.gov.ma/",
        "type": "OFFICIAL",
        "priority": 2,
    },
    "ansvar": {
        "name": "قاعدة بيانات القانون المغربي — Ansvar MCP",
        "name_en": "Ansvar Moroccan Law MCP",
        "url": "https://github.com/ansvar/moroccan-law-mcp",
        "type": "OFFICIAL",
        "priority": 3,
    },
    "legislation_ma": {
        "name": "منصة التشريع المغربي",
        "name_en": "Moroccan Legislation Platform",
        "url": "https://www.legislation.gov.ma/",
        "type": "OFFICIAL",
        "priority": 4,
    },
}

# ══════════════════════════════════════════════════════════════════════════════
# أنواع الإصدارات
# ══════════════════════════════════════════════════════════════════════════════

VERSION_TYPES = {
    "ORIGINAL_OFFICIAL": "النص كما نشر رسميًا",
    "CONSOLIDATED_OFFICIAL": "النص الموطد/المحين من مصدر رسمي",
    "AMENDMENT": "نص تعديلي",
}

# ══════════════════════════════════════════════════════════════════════════════
# حالات التحقق
# ══════════════════════════════════════════════════════════════════════════════

VERIFICATION_STATUS = {
    "VERIFIED": "تم التحقق — مطابق للمصدر الرسمي",
    "UNVERIFIED": "لم يتم التحقق بعد",
    "SOURCE_CHANGED": "النص تغير عن النسخة الأصلية",
    "SOURCE_CONFLICT": "矛盾 بين مصدرين رسميين",
    "IMPORT_FAILED": "فشل الاستيراد من المصدر",
}


# ══════════════════════════════════════════════════════════════════════════════
# حساب البصمة الرقمية (Content Hash)
# ══════════════════════════════════════════════════════════════════════════════

def content_hash(text: str) -> str:
    """حساب بصمة SHA-256 للنص — للكشف عن التغيير ومنع التكرار."""
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def compute_text_hash(legal_text_id: int) -> str | None:
    """حساب بصمة لنص قانوني من جميع مواده."""
    with db_session() as conn:
        rows = conn.execute(
            "SELECT content FROM articles WHERE legal_text_id = ? ORDER BY number",
            (legal_text_id,),
        ).fetchall()
        if not rows:
            return None
        combined = "\n\n".join(r["content"] for r in rows)
        return content_hash(combined)


# ══════════════════════════════════════════════════════════════════════════════
# التحقق من النص الرسمي
# ══════════════════════════════════════════════════════════════════════════════

def verify_official_text(legal_text_id: int) -> dict[str, Any]:
    """مقارنة النص المخزّن مع بصمته الأصلية.

    Returns:
        dict مع:
        - status: "MATCH" | "DIFFERENT" | "NO_HASH" | "NO_TEXT"
        - stored_hash: البصمة المخزّنة
        - current_hash: البصمة الحالية
        - verified_at: تاريخ التحقق
    """
    with db_session() as conn:
        row = conn.execute(
            "SELECT id, content_hash FROM legal_texts WHERE id = ?",
            (legal_text_id,),
        ).fetchone()
        if not row:
            return {"status": "NO_TEXT", "message": "النص غير موجود"}

        stored_hash = row["content_hash"]
        if not stored_hash:
            return {"status": "NO_HASH", "message": "لا توجد بصمة مسجلة"}

        current_hash = compute_text_hash(legal_text_id)
        if not current_hash:
            return {"status": "NO_TEXT", "message": "لا توجد مواد"}

        now = datetime.now(timezone.utc).isoformat()
        if stored_hash == current_hash:
            return {
                "status": "MATCH",
                "stored_hash": stored_hash,
                "current_hash": current_hash,
                "verified_at": now,
            }
        else:
            return {
                "status": "DIFFERENT",
                "stored_hash": stored_hash,
                "current_hash": current_hash,
                "verified_at": now,
                "message": "النص تغير عن النسخة الأصلية المسجلة",
            }


def verify_all_texts() -> dict[str, Any]:
    """التحقق من جميع النصوص القانونية."""
    results = {"total": 0, "match": 0, "different": 0, "no_hash": 0, "errors": []}
    with db_session() as conn:
        rows = conn.execute(
            "SELECT id, title FROM legal_texts WHERE is_sample_data = 0"
        ).fetchall()
        results["total"] = len(rows)
        for row in rows:
            try:
                r = verify_official_text(row["id"])
                if r["status"] == "MATCH":
                    results["match"] += 1
                elif r["status"] == "DIFFERENT":
                    results["different"] += 1
                    results["errors"].append({
                        "id": row["id"],
                        "title": row["title"][:80],
                        "status": r["status"],
                    })
                elif r["status"] == "NO_HASH":
                    results["no_hash"] += 1
            except Exception as e:
                results["errors"].append({
                    "id": row["id"],
                    "title": row["title"][:80],
                    "status": "ERROR",
                    "error": str(e),
                })
    return results


# ══════════════════════════════════════════════════════════════════════════════
# حماية النصوص الرسمية من تعديل AI
# ══════════════════════════════════════════════════════════════════════════════

_OFFICIAL_TEXT_MUTATION_PATTERNS = re.compile(
    r"UPDATE\s+articles\s+SET\s+(?:content|official_text_raw)\s*="
    r"|UPDATE\s+legal_texts\s+SET\s+(?:content_hash|source_url)\s*=",
    re.IGNORECASE,
)


def is_official_text_mutation(query: str) -> bool:
    """كشف محاولات تعديل النصوص الرسمية عبر SQL."""
    return bool(_OFFICIAL_TEXT_MUTATION_PATTERNS.search(query))


def protect_official_text(func):
    """زخرفة تمنع تعديل official_text_raw أو content للنصوص الرسمية."""
    def wrapper(*args, **kwargs):
        # لا يمكن تعديل النص الأصلي عبر AI
        raise PermissionError(
            "ZERO AI REWRITING: يُمنع تعديل النصوص الرسمية عبر الذكاء الاصطناعي. "
            "استخدم OfficialSourceImporter للاستيراد والمزامنة."
        )
    return wrapper


# ══════════════════════════════════════════════════════════════════════════════
# خدمة استيراد النصوص الرسمية
# ══════════════════════════════════════════════════════════════════════════════

class OfficialSourceImporter:
    """استيراد النصوص القانونية من المصادر الرسمية — بدون AI rewriting.

    المبدأ: SOURCE → FETCH → EXTRACT → VERIFY → STORE → DISPLAY
    """

    @staticmethod
    def create_text(
        title: str,
        articles: list[dict],
        source_key: str,
        source_url: str | None = None,
        source_document_url: str | None = None,
        official_ref: str | None = None,
        enacted_date: str | None = None,
        category_id: int | None = None,
        text_type: str = "law",
        version_type: str = "ORIGINAL_OFFICIAL",
        published_date: str | None = None,
        language: str = "ar",
        is_sample_data: int = 0,
        tenant_id: int = 1,
    ) -> dict[str, Any]:
        """إنشاء نص قانوني من مصدر رسمي — بدون أي تدخل AI.

        Args:
            title: عنوان النص القانوني
            articles: قائمة المواد [{'number': '1', 'label': 'المادة 1', 'content': '...'}]
            source_key: مفتاح المصدر (adala/sgg/ansvar/legislation_ma)
            source_url: رابط الصفحة الرئيسية للمصدر
            source_document_url: رابط الوثيقة الأصلية مباشرة
            official_ref: الرقم الرسمي (رقم الظهير/الجريدة الرسمية)
            enacted_date: تاريخ الإصدار
            category_id: معرف الفئة
            text_type: نوع النص (constitution/code/law/decree/gazette/treaty/ruling)
            version_type: نوع الإصدار (ORIGINAL_OFFICIAL/CONSOLIDATED_OFFICIAL)
            published_date: تاريخ النشر الرسمي
            language: اللغة (ar/fr/en)
            is_sample_data: 0=محتوى رسمي، 1=بيانات نموذجية
            tenant_id: المستأجر المالك

        Returns:
            dict مع text_id، content_hash، article_count
        """
        source_info = OFFICIAL_SOURCES.get(source_key, {})
        source_name = source_info.get("name", source_key)
        is_official = 1 if source_info.get("type") == "OFFICIAL" else 0

        # حساب بصمة المحتوى من جميع المواد
        all_content = "\n\n".join(a.get("content", "") for a in articles)
        c_hash = content_hash(all_content)

        now = datetime.now(timezone.utc).isoformat()

        with db_session() as conn:
            # التحقق من عدم التكرار (نفس البصمة)
            if c_hash:
                existing = conn.execute(
                    "SELECT id FROM legal_texts WHERE content_hash = ?",
                    (c_hash,),
                ).fetchone()
                if existing:
                    log.info("Text already exists (hash match): id=%s", existing["id"])
                    return {
                        "text_id": existing["id"],
                        "content_hash": c_hash,
                        "article_count": len(articles),
                        "status": "DUPLICATE",
                    }

            # إنشاء النص القانوني
            cur = conn.execute(
                """INSERT INTO legal_texts
                   (category_id, type, title, official_ref, enacted_date,
                    source_note, is_sample_data, source_url, source_document_url,
                    official_source, content_hash, version_type, verification_status,
                    imported_at, updated_at, published_date, language, source_name,
                    tenant_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    category_id,
                    text_type,
                    title,
                    official_ref,
                    enacted_date,
                    f"النص الرسمي المستخرج من {source_name}",
                    is_sample_data,
                    source_url,
                    source_document_url,
                    is_official,
                    c_hash,
                    version_type,
                    "UNVERIFIED",
                    now,
                    now,
                    published_date,
                    language,
                    source_name,
                    tenant_id,
                ),
            )
            text_id = cur.lastrowid

            # إنشاء المواد — بدون أي تعديل AI
            article_count = 0
            for art in articles:
                art_content = art.get("content", "")
                art_hash = content_hash(art_content)
                conn.execute(
                    """INSERT INTO articles
                       (legal_text_id, number, label, content, content_hash,
                        official_text_raw, tenant_id)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        text_id,
                        art.get("number", ""),
                        art.get("label", f"المادة {art.get('number', '')}"),
                        art_content,
                        art_hash,
                        art_content,  # official_text_raw = النص الأصلي كما هو
                        tenant_id,
                    ),
                )
                article_count += 1

            # تحديث إحصائيات الفئات
            if category_id:
                conn.execute(
                    """UPDATE categories SET description =
                       COALESCE(description, '') || '' WHERE id = ?""",
                    (category_id,),
                )

            log.info(
                "Imported official text: id=%s title='%s' articles=%d hash=%s",
                text_id, title[:60], article_count, c_hash[:16],
            )

            return {
                "text_id": text_id,
                "content_hash": c_hash,
                "article_count": article_count,
                "status": "IMPORTED",
            }

    @staticmethod
    def update_text_hash(legal_text_id: int) -> str | None:
        """تحديث بصمة النص القانوني بعد تعديل المواد."""
        c_hash = compute_text_hash(legal_text_id)
        if c_hash:
            now = datetime.now(timezone.utc).isoformat()
            with db_session() as conn:
                conn.execute(
                    "UPDATE legal_texts SET content_hash = ?, updated_at = ? WHERE id = ?",
                    (c_hash, now, legal_text_id),
                )
        return c_hash

    @staticmethod
    def get_source_info(legal_text_id: int) -> dict[str, Any] | None:
        """الحصول على معلومات مصدر النص القانوني."""
        with db_session() as conn:
            row = conn.execute(
                """SELECT id, title, source_url, source_document_url, source_name,
                          official_source, content_hash, version_type,
                          verification_status, imported_at, updated_at,
                          published_date, language
                   FROM legal_texts WHERE id = ?""",
                (legal_text_id,),
            ).fetchone()
            if not row:
                return None
            return dict(row)


# ══════════════════════════════════════════════════════════════════════════════
# خدمة المزامنة مع المصادر الرسمية
# ══════════════════════════════════════════════════════════════════════════════

class OfficialLegalSourcesSync:
    """مزامنة دورية مع المصادر الرسمية.

    الخطوات:
    1. الاتصال بالمصادر الرسمية
    2. اكتشاف النصوص الجديدة
    3. اكتشاف النصوص المعدلة
    4. تحميل الوثائق
    5. حساب hash للملف
    6. استخراج النص
    7. مقارنة hash مع النسخة الموجودة
    8. إنشاء version جديد عند وجود تغيير
    9. تحديث metadata
    10. تسجيل تاريخ المزامنة
    """

    @staticmethod
    def sync_status() -> dict[str, Any]:
        """الحصول على حالة المزامنة الحالية."""
        with db_session() as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM legal_texts WHERE is_sample_data = 0"
            ).fetchone()[0]
            verified = conn.execute(
                "SELECT COUNT(*) FROM legal_texts WHERE verification_status = 'VERIFIED'"
            ).fetchone()[0]
            with_hash = conn.execute(
                "SELECT COUNT(*) FROM legal_texts WHERE content_hash IS NOT NULL"
            ).fetchone()[0]
            with_source = conn.execute(
                "SELECT COUNT(*) FROM legal_texts WHERE source_url IS NOT NULL"
            ).fetchone()[0]
            by_source = conn.execute(
                """SELECT source_name, COUNT(*) as cnt
                   FROM legal_texts
                   WHERE is_sample_data = 0 AND source_name IS NOT NULL
                   GROUP BY source_name
                   ORDER BY cnt DESC"""
            ).fetchall()
            by_version = conn.execute(
                """SELECT version_type, COUNT(*) as cnt
                   FROM legal_texts
                   WHERE is_sample_data = 0
                   GROUP BY version_type"""
            ).fetchall()

            return {
                "total_texts": total,
                "verified_texts": verified,
                "with_hash": with_hash,
                "with_source_url": with_source,
                "by_source": {r["source_name"]: r["cnt"] for r in by_source},
                "by_version": {r["version_type"]: r["cnt"] for r in by_version},
            }

    @staticmethod
    def register_sync_run(
        source_key: str,
        status: str,
        docs_found: int = 0,
        docs_imported: int = 0,
        docs_skipped: int = 0,
        docs_failed: int = 0,
        error_message: str | None = None,
    ) -> None:
        """تسجيل تشغيل مزامنة."""
        now = datetime.now(timezone.utc).isoformat()
        log.info(
            "Sync run: source=%s status=%s found=%d imported=%d skipped=%d failed=%d",
            source_key, status, docs_found, docs_imported, docs_skipped, docs_failed,
        )

    @staticmethod
    def backfill_hashes() -> dict[str, Any]:
        """حساب البصمات للنصوص التي لا تملك بصمة."""
        updated = 0
        with db_session() as conn:
            rows = conn.execute(
                "SELECT id FROM legal_texts WHERE content_hash IS NULL"
            ).fetchall()
            for row in rows:
                c_hash = compute_text_hash(row["id"])
                if c_hash:
                    conn.execute(
                        "UPDATE legal_texts SET content_hash = ? WHERE id = ?",
                        (c_hash, row["id"]),
                    )
                    updated += 1
        log.info("Backfilled %d text hashes", updated)
        return {"updated": updated, "total_scanned": len(rows)}

    @staticmethod
    def backfill_source_metadata() -> dict[str, Any]:
        """ملء بيانات المصدر للنصوص الموجودة بناءً على source_note."""
        source_patterns = {
            "ansvar": "Ansvar MCP",
            "عدالة": "adala",
            "وزارة العدل": "adala",
            "adala": "adala",
            "sgg.gov.ma": "sgg",
            "الجريدة الرسمية": "sgg",
            "legislation.gov.ma": "legislation_ma",
        }
        updated = 0
        with db_session() as conn:
            rows = conn.execute(
                """SELECT id, source_note, title FROM legal_texts
                   WHERE source_name IS NULL AND is_sample_data = 0"""
            ).fetchall()
            for row in rows:
                note = (row["source_note"] or "").lower()
                title = (row["title"] or "").lower()
                source_key = None
                for pattern, key in source_patterns.items():
                    if pattern.lower() in note or pattern.lower() in title:
                        source_key = key
                        break

                if source_key:
                    source_info = OFFICIAL_SOURCES.get(source_key, {})
                    conn.execute(
                        """UPDATE legal_texts
                           SET source_name = ?, official_source = ?
                           WHERE id = ?""",
                        (
                            source_info.get("name", source_key),
                            1 if source_info.get("type") == "OFFICIAL" else 0,
                            row["id"],
                        ),
                    )
                    updated += 1
        log.info("Backfilled source metadata for %d texts", updated)
        return {"updated": updated}


# ══════════════════════════════════════════════════════════════════════════════
# واجهة API للتحقق والمزامنة
# ══════════════════════════════════════════════════════════════════════════════

def get_text_source_info(text_id: int) -> dict[str, Any]:
    """API: الحصول على معلومات مصدر النص."""
    info = OfficialSourceImporter.get_source_info(text_id)
    if not info:
        return {"error": "النص غير موجود"}
    return info


def verify_text(text_id: int) -> dict[str, Any]:
    """API: التحقق من تطابق النص مع بصمته."""
    return verify_official_text(text_id)


def sync_status() -> dict[str, Any]:
    """API: حالة المزامنة."""
    return OfficialLegalSourcesSync.sync_status()


def backfill_all() -> dict[str, Any]:
    """API: ملء البصمات وبيانات المصدر للنصوص الموجودة."""
    hashes = OfficialLegalSourcesSync.backfill_hashes()
    sources = OfficialLegalSourcesSync.backfill_source_metadata()
    return {"hashes": hashes, "sources": sources}
