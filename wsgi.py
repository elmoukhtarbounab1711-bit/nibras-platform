"""Vercel serverless entry — downloads DB to /tmp on cold start, returns Flask app."""
import gzip
import os
import shutil
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

os.environ.setdefault("NIBRAS_DB_PATH", "/tmp/nibras.db")


def _ensure_db():
    from app.database import DB_PATH, load_bundled_db

    if DB_PATH.exists() and DB_PATH.stat().st_size > 1000:
        return

    url = os.environ.get("NIBRAS_DB_URL", "").strip()
    if url:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = Path(str(DB_PATH) + ".gz.tmp")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "nibras/1.0"})
            with urllib.request.urlopen(req, timeout=300) as resp, open(tmp, "wb") as f:
                shutil.copyfileobj(resp, f)
            with gzip.open(tmp, "rb") as f_in, open(DB_PATH, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
            tmp.unlink(missing_ok=True)
            return
        except Exception:  # noqa: BLE001 — نكمل بالنسخة المضمّنة عند فشل التحميل
            tmp.unlink(missing_ok=True)

    # بلا NIBRAS_DB_URL: نستخدم نسخة الـ DB المضمّنة في المستودع إن وُجدت
    load_bundled_db()


_ensure_db()

from app import create_app  # noqa: E402

app = create_app()
