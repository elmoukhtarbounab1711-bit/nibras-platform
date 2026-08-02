"""
اختبارات النسخ الاحتياطي والاستعادة (المرحلة 11).

تحميل scripts/backup.py كوحدة (importlib) واختبار: إنشاء نسخة متسقة،
التحقق من سلامتها، الاستعادة، الدوران (keep)، والقائمة.
"""
import importlib.util
import sqlite3
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "backup.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("nibras_backup", _SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


backup_mod = _load_module()


def _make_db(path: Path) -> None:
    conn = sqlite3.connect(str(path))
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, value TEXT)")
    conn.execute("INSERT INTO t (value) VALUES ('بيانات')")
    conn.commit()
    conn.close()


def test_create_backup_produces_valid_file(tmp_path):
    db = tmp_path / "app.db"
    bdir = tmp_path / "backups"
    _make_db(db)
    target = backup_mod.create_backup(db, bdir)
    assert target.exists()
    assert backup_mod.verify_backup(target)
    conn = sqlite3.connect(str(target))
    value = conn.execute("SELECT value FROM t").fetchone()[0]
    conn.close()
    assert value == "بيانات"


def test_restore_backup(tmp_path):
    db = tmp_path / "app.db"
    _make_db(db)
    target = backup_mod.create_backup(db, tmp_path / "b")
    # تعديل المصدر ثم استعادة النسخة تُعيد البيانات الأصلية
    conn = sqlite3.connect(str(db))
    conn.execute("UPDATE t SET value = 'معدل'")
    conn.commit()
    conn.close()
    backup_mod.restore_backup(target, db)
    conn = sqlite3.connect(str(db))
    value = conn.execute("SELECT value FROM t").fetchone()[0]
    conn.close()
    assert value == "بيانات"


def test_restore_rejects_corrupt(tmp_path):
    db = tmp_path / "app.db"
    _make_db(db)
    bad = tmp_path / "corrupt.sqlite"
    bad.write_bytes(b"not a sqlite database at all")
    with pytest.raises(backup_mod.BackupError):
        backup_mod.restore_backup(bad, db)


def test_create_backup_missing_db(tmp_path):
    with pytest.raises(backup_mod.BackupError):
        backup_mod.create_backup(tmp_path / "missing.db", tmp_path / "b")


def test_rotation_keeps_newest(tmp_path):
    db = tmp_path / "app.db"
    bdir = tmp_path / "backups"
    _make_db(db)
    for _ in range(5):
        backup_mod.create_backup(db, bdir, keep=3)
    names = [p.name for p in backup_mod._iter_backups(bdir)]
    assert len(names) == 3


def test_list_backups_ordering_and_fields(tmp_path):
    db = tmp_path / "app.db"
    bdir = tmp_path / "backups"
    _make_db(db)
    backup_mod.create_backup(db, bdir, keep=7)
    entries = backup_mod.list_backups(bdir)
    assert len(entries) == 1
    assert entries[0]["name"].startswith("nibras-")
    assert entries[0]["size_bytes"] > 0
    assert "modified" in entries[0]


def test_cli_backup_and_list(tmp_path):
    db = tmp_path / "app.db"
    _make_db(db)
    code = backup_mod.main(["backup", "--db", str(db), "--dir", str(tmp_path / "b")])
    assert code == 0
    code = backup_mod.main(["list", "--dir", str(tmp_path / "b")])
    assert code == 0
