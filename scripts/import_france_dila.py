# -*- coding: utf-8 -*-
"""مستورد النصوص الرسمية الفرنسية (Légifrance/DILA open data).

يحمّل أرشيف CONSTIT الرسمي (قرارات المجلس الدستوري الفرنسي) من
echanges.dila.gouv.fr ويستورد القرارات حرفيًا كما وردت في XML الرسمي:
عنوان، محكمة، رقم القرار، تاريخه، نص القرار، ومصدر موثّق (URL + ECLI).
يُخزَّن تحت ولاية فرنسا (jurisdiction_id=3) فقط — معزولًا عن أسطح المغرب.

الاستخدام:
    python scripts/import_france_dila.py [--skip-download] [--purge]
"""
import argparse
import glob
import html
import json
import os
import re
import sqlite3
import sys
import tarfile
import io
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.database import db_session
from app import tenant_scope  # noqa: E402

DATASETS = {
    "constitu": {
        "url": ("https://echanges.dila.gouv.fr/OPENDATA/CONSTIT/"
                "CONSTIT_20260804-220219.tar.gz"),
        "cat_slug": "dostouri",
        "cat_name": "القانون الدستوري",
        "source": "Conseil constitutionnel (Légifrance/DILA)",
    },
    "cass": {
        "url": ("https://echanges.dila.gouv.fr/OPENDATA/CASS/"
                "CASS_20251103-213357.tar.gz"),
        "cat_slug": "cassation",
        "cat_name": "قرارات محكمة النقض",
        "source": "Cour de cassation (Légifrance/DILA)",
    },
}
CACHE_DIR = Path(__file__).resolve().parent / "_dila_cache"
CHECKPOINT = Path(__file__).resolve().parent / "france_checkpoint.sqlite"

FRANCE_ID = 3          # ولاية فرنسا في law_jurisdictions


def _checkpoint_conn():
    conn = sqlite3.connect(str(CHECKPOINT))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS imported (key TEXT PRIMARY KEY)"
    )
    return conn


def _ensure_category(cat_slug, cat_name):
    with db_session() as conn:
        row = conn.execute(
            "SELECT id FROM jurisprudence_categories "
            "WHERE slug = ? AND jurisdiction_id = ?",
            (cat_slug, FRANCE_ID),
        ).fetchone()
        if row:
            return row["id"]
        cur = conn.execute(
            "INSERT INTO jurisprudence_categories "
            "(slug, name, jurisdiction_id, tenant_id) VALUES (?, ?, ?, ?)",
            (cat_slug, cat_name, FRANCE_ID,
             tenant_scope.insert_tenant_id()),
        )
        return cur.lastrowid


def _text(tag, content):
    m = re.search(r"<" + tag + r">(.*?)</" + tag + r">", content, re.S)
    return html.unescape(m.group(1)).strip() if m else None


def _body(content):
    m = re.search(r"<CONTENU>(.*?)</CONTENU>", content, re.S)
    if not m:
        return ""
    raw = m.group(1)
    raw = re.sub(r"<br\s*/?>", "\n", raw)
    raw = re.sub(r"<[^>]+>", "", raw)
    return html.unescape(raw).strip()


def _download_archive(url):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    name = url.rsplit("/", 1)[-1]
    dest = CACHE_DIR / name
    if not dest.exists():
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=180).read()
        dest.write_bytes(data)
        print(f"downloaded {name} ({len(data)} bytes)")
    else:
        print(f"cached {name}")
    return dest


def _load_xmls(archive_path):
    tf = tarfile.open(str(archive_path), mode="r:gz")
    out = []
    for member in tf.getmembers():
        if member.name.endswith(".xml"):
            data = tf.extractfile(member).read().decode("utf-8")
            out.append((os.path.basename(member.name), data))
    tf.close()
    return out


def import_decisions(dataset="constitu", purge=False):
    cfg = DATASETS[dataset]
    ck = _checkpoint_conn()
    if purge:
        ck.execute("DELETE FROM imported")
        with db_session() as conn:
            conn.execute(
                "DELETE FROM jurisprudence WHERE jurisdiction_id = ?",
                (FRANCE_ID,),
            )
        print("purged France decisions + checkpoint")
    category_id = _ensure_category(cfg["cat_slug"], cfg["cat_name"])
    archive = _download_archive(cfg["url"])
    xmls = _load_xmls(archive)
    seen = {r[0] for r in ck.execute("SELECT key FROM imported").fetchall()}
    ok = 0
    with db_session() as conn:
        for fname, text in xmls:
            ident = _text("ID", text)
            if not ident or ident in seen:
                continue
            titre = _text("TITRE", text) or fname
            date_dec = _text("DATE_DEC", text) or None
            solution = _text("SOLUTION", text) or ""
            ecli = _text("ECLI", text) or ""
            court = _text("JURIDICTION", text) or cfg["source"]
            if dataset == "cass":
                numero = _text("NUMERO_AFFAIRE", text) or ""
            else:
                numero = _text("NUMERO", text) or ""
            url_ref = _text("URL_CC", text) or ""
            body = _body(text)
            if not body:
                print(f"  ! {ident}: نص فارغ — تجاوز")
                continue
            source_note = (
                f"{cfg['source']}. "
                f"{url_ref} | ECLI: {ecli} | Archive: {cfg['url']}"
            ).strip(" |")
            conn.execute(
                """INSERT INTO jurisprudence
                   (category_id, title, principles, content, court,
                    decision_number, decision_date, source_note, pdf_url,
                    published, views, jurisdiction_id, tenant_id,
                    created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, '', 1, 0, ?, ?,
                           datetime('now'), datetime('now'))""",
                (category_id, titre, solution, body, court, numero, date_dec,
                 source_note, FRANCE_ID, tenant_scope.insert_tenant_id()),
            )
            ck.execute("INSERT OR IGNORE INTO imported (key) VALUES (?)",
                       (ident,))
            ok += 1
            print(f"  + {ident} — {titre[:60]}")
    ck.commit()
    ck.close()
    print(f"imported {ok} decision(s) from {dataset}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", choices=list(DATASETS), default="constitu")
    ap.add_argument("--skip-download", action="store_true")
    ap.add_argument("--purge", action="store_true")
    args = ap.parse_args()
    import_decisions(dataset=args.dataset, purge=args.purge)


if __name__ == "__main__":
    main()