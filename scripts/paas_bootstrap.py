"""
بوتستراب النشر (PaaS) — يهيِّئ القرص المُثبَّت عند أول إقلاع.

لأن أنظمة PaaS (Render/Railway/Fly) لديها نظام ملفات عابر، يُطلب ربط قرص
مُثبَّت يُشار إليه بـ NIBRAS_DB_PATH و NIBRAS_UPLOAD_DIR. على قرص فارغ
ينشئ هذا السكربت قاعدة بيانات سليمة (المخطط كاملًا + فئات/أدوار/قوالب
الافتراضية) و/أو يستنسخ قاعدة موجودة من مكان آخر.

الاستخدام:
    # على قرص فارغ — بذر مخطط نظيف + بيانات افتراضية
    NIBRAS_DB_PATH=/data/nibras.db python scripts/paas_bootstrap.py seed

    # استنساخ قاعدة قائمة (مثل ملف مرشَّح من النسخ الاحتياطي) إلى القرص
    NIBRAS_DB_PATH=/data/nibras.db \
      NIBRAS_BOOTSTRAP_SOURCE=/tmp/nibras-prod.sqlite \
      python scripts/paas_bootstrap.py copy

    # المرور اللاحق يكون no-op آمن — تُنشأ القاعدة إن غابت فقط
    python scripts/paas_bootstrap.py ensure
"""
import os
import shutil
import sys
from pathlib import Path

# إضافة جذر المستودع إلى sys.path ليعمل السكربت كملف مباشر (python scripts/...)
_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from app import database


def _path_from_env() -> Path:
    db = database.DB_PATH
    db.parent.mkdir(parents=True, exist_ok=True)
    return db


def _check_db(db: Path) -> bool:
    """هل القاعدة سليمة (مخطط كامل)؟ أي خطأ مخطط/جدول ناقص = تحتاج بذرًا."""
    try:
        conn = database.get_connection()
        try:
            conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'").fetchone()
            conn.execute("SELECT COUNT(*) FROM jurisprudence_categories").fetchone()
        finally:
            conn.close()
    except Exception:  # noqa: BLE001 — قاعدة غير جاهزة/غير متصلة بعد: تعتبر غير مبنية
        return False
    return True


def seed():
    db = _path_from_env()
    if db.exists() and db.stat().st_size > 0 and _check_db(db):
        print(f"[bootstrap] قاعدة موجودة سليمة: {db} — تخطّي البذر.")
        return
    if db.exists():
        db.unlink()
    print(f"[bootstrap] إنشاء قاعدة + بيانات تجريبية: {db}")
    from app.seed import seed as seed_demo
    seed_demo(reset=True)
    print("[bootstrap] البذر اكتمل — قاعدة السرد جاهزة.")


def copy():
    source = os.environ.get("NIBRAS_BOOTSTRAP_SOURCE", "")
    if not source:
        print("[bootstrap] حدّد NIBRAS_BOOTSTRAP_SOURCE لاستنساخ قاعدة قائمة.")
        sys.exit(2)
    src = Path(source)
    if not src.exists():
        print(f"[bootstrap] المصدر غير موجود: {src}")
        sys.exit(2)
    db = _path_from_env()
    if db.exists() and db.stat().st_size > 0:
        print(f"[bootstrap] وجهة موجودة: {db} — تخطّي الاستنساخ (لا تُستبدل قاعدة حيّة).")
        return
    parent = db.parent
    parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, db)
    for suffix in ("-wal", "-shm"):
        cand = Path(str(src) + suffix)
        if cand.exists():
            shutil.copyfile(cand, Path(str(db) + suffix))
    print(f"[bootstrap] استُنسخت القاعدة من {src} إلى {db}.")
    # إعادة بناء أي فهرس نسخة زمنية (idempotent)
    from app import create_app

    create_app()
    print("[bootstrap] المخطط/FTS متزامنان.")


def ensure():
    db = _path_from_env()
    if db.exists() and db.stat().st_size > 0 and _check_db(db):
        print(f"[bootstrap] جاهز: {db}")
        return
    seed()


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "ensure"
    {"seed": seed, "copy": copy, "ensure": ensure}.get(action, ensure)()