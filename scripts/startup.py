"""
نقطة بداية النشر على PaaS — تحميل القاعدة ثم تشغيل gunicorn.
"""
import gzip
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from app import database


def _check_db(db):
    try:
        from app.database import get_connection
        conn = get_connection()
        try:
            # التحقق من وجود الجداول الأساسية + الجداول الجديدة (legal_domains)
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('users', 'legal_domains')"
            ).fetchall()
            return len(row) == 2
        finally:
            conn.close()
    except Exception:
        return False


def ensure_db():
    db = database.DB_PATH
    db.parent.mkdir(parents=True, exist_ok=True)

    if db.exists() and db.stat().st_size > 1000 and _check_db(db):
        print(f"[startup] DB OK: {db} ({db.stat().st_size / 1024 / 1024:.1f} MB)")
        return

    url = os.environ.get("NIBRAS_DB_URL", "").strip()
    if url:
        print(f"[startup] Downloading DB from: {url}")
        tmp = Path(str(db) + ".gz.tmp")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "nibras/1.0"})
            with urllib.request.urlopen(req, timeout=600) as resp:
                with open(tmp, "wb") as f:
                    shutil.copyfileobj(resp, f)
            print(f"[startup] Downloaded: {tmp.stat().st_size / 1024 / 1024:.1f} MB")
            with gzip.open(tmp, "rb") as f_in, open(db, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
            tmp.unlink(missing_ok=True)
            print(f"[startup] DB ready: {db.stat().st_size / 1024 / 1024:.1f} MB")
            if _check_db(db):
                print("[startup] DB verified OK")
            else:
                print("[startup] WARNING: DB may be incomplete")
            return
        except Exception as e:
            print(f"[startup] Download failed: {e}")
            tmp.unlink(missing_ok=True)

    print("[startup] Seeding demo data")
    from app.seed import seed as seed_demo
    seed_demo(reset=True)


ensure_db()

port = os.environ.get("PORT", "5000")
workers = os.environ.get("WEB_CONCURRENCY", "2")

print(f"[startup] Starting gunicorn on port {port}")
sys.exit(subprocess.call([
    "gunicorn", "app:create_app()",
    "--bind", f"0.0.0.0:{port}",
    "--workers", workers,
    "--threads", "4",
    "--timeout", "120",
    "--access-logfile", "-",
]))
