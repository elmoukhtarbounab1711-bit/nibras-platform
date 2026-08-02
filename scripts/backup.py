"""
النسخ الاحتياطي والاستعادة لقاعدة بيانات نبراس (المرحلة 11).

SQLite ملف واحد؛ يُنفَّذ النسخ عبر واجهة sqlite3 backup الرسمية (نسخة
متسقة حتى مع قاعدة قيد الاستخدام — تقنية online backup)، مع دوران تلقائي
يُبقي أحدث N نسخة فقط. يُدعى من سطر الأوامر أو كوحدة (دوال قابلة للاختبار).

الاستخدام:
    python scripts/backup.py backup   [--db PATH] [--dir DIR] [--keep N]
    python scripts/backup.py restore  --backup FILE [--db PATH]
    python scripts/backup.py list     [--dir DIR]

خيارات عامة:
    --db PATH   مسار قاعدة البيانات المصدر (الافتراضي: nibras.db في جذر المشروع)
    --dir DIR   مجلد النسخ (الافتراضي: backups/ في جذر المشروع)
"""
import argparse
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = REPO_ROOT / "nibras.db"
DEFAULT_DIR = REPO_ROOT / "backups"
BACKUP_PREFIX = "nibras-"
BACKUP_SUFFIX = ".sqlite"


class BackupError(Exception):
    pass


def _default_db() -> Path:
    return DEFAULT_DB


def _default_dir() -> Path:
    return DEFAULT_DIR


def _backup_name(when: datetime | None = None) -> str:
    when = when or datetime.now(timezone.utc)
    # میکروثانية تضمن تفرد الأسماء حتى داخل نفس الثانية (وقابلية فرز ثابتة)
    return f"{BACKUP_PREFIX}{when.strftime('%Y%m%d-%H%M%S-%f')}{BACKUP_SUFFIX}"


def _iter_backups(backup_dir: Path) -> list:
    if not backup_dir.exists():
        return []
    files = sorted(
        p for p in backup_dir.iterdir()
        if p.is_file() and p.name.startswith(BACKUP_PREFIX)
        and p.name.endswith(BACKUP_SUFFIX)
    )
    return files


def create_backup(db_path: Path, backup_dir: Path, keep: int = 7) -> Path:
    """ينشئ نسخة متسقة من قاعدة البيانات ويعيد مسارها (مع دوران احتفاظ)."""
    db_path = Path(db_path)
    backup_dir = Path(backup_dir)
    if not db_path.exists():
        raise BackupError(f"قاعدة البيانات غير موجودة: {db_path}")
    backup_dir.mkdir(parents=True, exist_ok=True)
    target = backup_dir / _backup_name()
    source = sqlite3.connect(str(db_path))
    try:
        destination = sqlite3.connect(str(target))
        try:
            with destination:
                source.backup(destination)
        finally:
            destination.close()
    finally:
        source.close()

    files = _iter_backups(backup_dir)
    try:
        keep = int(keep)
    except (TypeError, ValueError):
        keep = 7
    if keep > 0:
        for old in files[:-keep]:
            old.unlink(missing_ok=True)
    return target


def verify_backup(backup_path: Path) -> bool:
    """يتحقق أن ملف النسخ قاعدة SQLite سليمة (quick_check)."""
    backup_path = Path(backup_path)
    if not backup_path.exists():
        return False
    try:
        conn = sqlite3.connect(str(backup_path))
        try:
            row = conn.execute("PRAGMA quick_check").fetchone()
            return row is not None and row[0] == "ok"
        finally:
            conn.close()
    except sqlite3.Error:
        return False


def restore_backup(backup_path: Path, db_path: Path) -> None:
    """يستعيد قاعدة البيانات من نسخة موثَّقة (يحل محل db_path)."""
    backup_path = Path(backup_path)
    db_path = Path(db_path)
    if not verify_backup(backup_path):
        raise BackupError(f"ملف النسخ تالف أو غير موجود: {backup_path}")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    source = sqlite3.connect(str(backup_path))
    try:
        destination = sqlite3.connect(str(db_path))
        try:
            with destination:
                source.backup(destination)
        finally:
            destination.close()
    finally:
        source.close()


def list_backups(backup_dir: Path) -> list:
    """قائمة النسخ مع الحجم والتاريخ (الأحدث أولًا)."""
    entries = []
    for path in reversed(_iter_backups(backup_dir)):
        stat = path.stat()
        entries.append({
            "name": path.name,
            "size_bytes": stat.st_size,
            "modified": datetime.fromtimestamp(
                stat.st_mtime, tz=timezone.utc
            ).isoformat(timespec="seconds"),
        })
    return entries


def _cmd_backup(args) -> int:
    db_path = Path(args.db) if args.db else _default_db()
    backup_dir = Path(args.dir) if args.dir else _default_dir()
    target = create_backup(db_path, backup_dir, keep=args.keep)
    print(f"تم إنشاء النسخة: {target}")
    return 0


def _cmd_restore(args) -> int:
    if not args.backup:
        print("restore يتطلب --backup FILE", file=sys.stderr)
        return 2
    db_path = Path(args.db) if args.db else _default_db()
    restore_backup(Path(args.backup), db_path)
    print(f"تمت الاستعادة إلى: {db_path}")
    return 0


def _cmd_list(args) -> int:
    backup_dir = Path(args.dir) if args.dir else _default_dir()
    entries = list_backups(backup_dir)
    if not entries:
        print("لا توجد نسخ احتياطية.")
        return 0
    for entry in entries:
        size_kb = entry["size_bytes"] / 1024
        print(f"{entry['name']}  {size_kb:,.1f} KB  {entry['modified']}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="backup.py", description="نسخ واستعادة قاعدة بيانات نبراس"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_backup = sub.add_parser("backup", help="إنشاء نسخة احتياطية")
    p_backup.add_argument("--db", help="مسار قاعدة البيانات المصدر")
    p_backup.add_argument("--dir", help="مجلد النسخ")
    p_backup.add_argument("--keep", type=int, default=7,
                          help="عدد النسخ المحتفظ بها (0 = بلا دوران)")
    p_backup.set_defaults(func=_cmd_backup)

    p_restore = sub.add_parser("restore", help="استعادة من نسخة")
    p_restore.add_argument("--backup", required=True, help="مسار ملف النسخ")
    p_restore.add_argument("--db", help="مسار قاعدة البيانات الهدف")
    p_restore.set_defaults(func=_cmd_restore)

    p_list = sub.add_parser("list", help="عرض النسخ الاحتياطية")
    p_list.add_argument("--dir", help="مجلد النسخ")
    p_list.set_defaults(func=_cmd_list)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
