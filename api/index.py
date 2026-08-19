"""
نقطة دخول Vercel Serverless — Flask WSGI app.
يُحمّل قاعدة البيانات إلى /tmp عند الإقلاع البارد ثم يُرجع تطبيق Flask.
"""
import gzip
import os
import shutil
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

os.environ.setdefault("NIBRAS_DB_PATH", "/tmp/nibras.db")


def _ensure_db():
    from app.database import DB_PATH

    if DB_PATH.exists() and DB_PATH.stat().st_size > 1000:
        return

    url = os.environ.get("NIBRAS_DB_URL", "").strip()
    if not url:
        return

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(DB_PATH) + ".gz.tmp")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "nibras/1.0"})
        with urllib.request.urlopen(req, timeout=300) as resp:
            with open(tmp, "wb") as f:
                shutil.copyfileobj(resp, f)
        with gzip.open(tmp, "rb") as f_in, open(DB_PATH, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        tmp.unlink(missing_ok=True)
    except Exception:
        tmp.unlink(missing_ok=True)


_ensure_db()

from app import create_app

app = create_app()
