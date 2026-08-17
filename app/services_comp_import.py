"""
خدمات استيراد القانون المقارن — فرنسا (DILA XML) + رفع يدوي (مصر).

يستورد القرارات القضائية الفرنسية من أرشيفات DILA الرسمية XML
إلى جداول comp_* مع تتبع جلسة الاستيراد واستبعاد التكرار.
"""
import html
import os
import re
import tarfile
import urllib.request
from pathlib import Path

from . import services_comp, tenant_scope
from .database import db_session

CACHE_DIR = Path(__file__).resolve().parent.parent / "scripts" / "_dila_cache"

FRANCE_DATASETS = {
    "constitu": {
        "url": ("https://echanges.dila.gouv.fr/OPENDATA/CONSTIT/"
                "CONSTIT_20260804-220219.tar.gz"),
        "court_name": "Conseil constitutionnel",
        "court_slug": "conseil-constitutionnel",
    },
    "cass": {
        "url": ("https://echanges.dila.gouv.fr/OPENDATA/CASS/"
                "CASS_20251103-213357.tar.gz"),
        "court_name": "Cour de cassation",
        "court_slug": "cour-de-cassation",
    },
}


# ---------------------------------------------------------------------------
# XML Parsing Helpers
# ---------------------------------------------------------------------------

def _xml_text(tag, content):
    m = re.search(r"<" + tag + r">(.*?)</" + tag + r">", content, re.DOTALL)
    return html.unescape(m.group(1)).strip() if m else None


def _xml_body(content):
    m = re.search(r"<CONTENU>(.*?)</CONTENU>", content, re.DOTALL)
    if not m:
        return ""
    raw = m.group(1)
    raw = re.sub(r"<br\s*/?>", "\n", raw)
    raw = re.sub(r"<[^>]+>", "", raw)
    return html.unescape(raw).strip()


# ---------------------------------------------------------------------------
# Download / Extract
# ---------------------------------------------------------------------------

def _download_archive(url):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    name = url.rsplit("/", 1)[-1]
    dest = CACHE_DIR / name
    if not dest.exists():
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=180).read()
        dest.write_bytes(data)
    return dest


def _load_xmls(archive_path):
    out = []
    with tarfile.open(str(archive_path), mode="r:gz") as tf:
        for member in tf.getmembers():
            if member.name.endswith(".xml"):
                data = tf.extractfile(member).read().decode("utf-8")
                out.append((os.path.basename(member.name), data))
    return out


# ---------------------------------------------------------------------------
# Court Lookup
# ---------------------------------------------------------------------------

def _ensure_court(country_id, name, slug):
    with db_session() as conn:
        row = conn.execute(
            "SELECT id FROM comp_courts "
            "WHERE country_id = ? AND slug = ?",
            (country_id, slug),
        ).fetchone()
        if row:
            return row["id"]
        cur = conn.execute(
            "INSERT INTO comp_courts "
            "(country_id, name, slug, tenant_id) VALUES (?,?,?,?)",
            (country_id, name, slug,
             tenant_scope.insert_tenant_id()),
        )
        return cur.lastrowid


# ---------------------------------------------------------------------------
# Import France Decisions → comp_jurisprudence
# ---------------------------------------------------------------------------

def import_france_decisions(dataset="constitu", run_id=None):
    """استيراد قرارات فرنسية من أرشيف DILA إلى comp_jurisprudence."""
    cfg = FRANCE_DATASETS.get(dataset)
    if not cfg:
        return {"error": f"dataset '{dataset}' unknown"}

    country = services_comp.get_country("france")
    if not country:
        return {"error": "france not found"}

    court_id = _ensure_court(
        country["id"], cfg["court_name"], cfg["court_slug"])

    if not run_id:
        run_id = services_comp.create_import_run(
            "france", source_id=None)

    archive = _download_archive(cfg["url"])
    xmls = _load_xmls(archive)

    imported = 0
    skipped = 0
    failed = 0
    found = len(xmls)

    services_comp.update_import_run(
        run_id, docs_found=found, status="running")

    for fname, text in xmls:
        titre = _xml_text("TITRE", text) or fname
        date_dec = _xml_text("DATE_DEC", text)
        solution = _xml_text("SOLUTION", text) or ""
        ecli = _xml_text("ECLI", text) or ""
        numero = (_xml_text("NUMERO_AFFAIRE", text)
                  if dataset == "cass"
                  else _xml_text("NUMERO", text)) or ""
        url_ref = _xml_text("URL_CC", text) or ""
        body = _xml_body(text)

        if not body:
            skipped += 1
            continue

        content_hash = services_comp._content_hash(body)

        existing = services_comp.find_existing_by_hash(
            content_hash, table="comp_jurisprudence")
        if existing:
            skipped += 1
            continue

        title = f"{cfg['court_name']} — {titre}"
        if numero:
            title += f" (n° {numero})"

        try:
            services_comp.create_decision(
                country["id"], title, body,
                court_id=court_id,
                decision_number=numero,
                decision_date=date_dec,
                decision_type=solution,
                keywords=ecli,
                source_name=cfg["court_name"],
                source_url=url_ref or None,
                official_source=1,
            )
            imported += 1
        except (ValueError, OSError):
            failed += 1

    services_comp.update_import_run(
        run_id,
        status="completed",
        docs_imported=imported,
        docs_skipped=skipped,
        docs_failed=failed,
    )

    return {
        "run_id": run_id,
        "found": found,
        "imported": imported,
        "skipped": skipped,
        "failed": failed,
    }


def import_france_cassation(run_id=None):
    """استيراد قرارات محكمة النقض الفرنسية."""
    return import_france_decisions("cass", run_id=run_id)


def import_france_constitutional(run_id=None):
    """استيراد قرارات المجلس الدستوري الفرنسي."""
    return import_france_decisions("constitu", run_id=run_id)
