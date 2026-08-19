"""خدمات مكتبة الباحث — كتب PDF مقسمة حسب التصنيف القانوني ونوع الكتاب."""
import hashlib
from pathlib import Path

from .database import db_session

BOOK_TYPES = ["thesis", "dissertation", "book", "article", "research"]
LEGAL_CATEGORIES = [
    "civil", "criminal", "labor", "personal_status",
    "administrative", "constitutional", "commercial", "general",
]

BOOK_TYPE_LABELS = {
    "thesis": "أطروحة دكتوراه",
    "dissertation": "رسالة ماستر",
    "book": "كتاب",
    "article": "بحث علمي",
    "research": "بحث",
}

LEGAL_CATEGORY_LABELS = {
    "civil": "قانون مدني",
    "criminal": "قانون جنائي",
    "labor": "قانون العمل",
    "personal_status": "أحوال شخصية",
    "administrative": "قانون إداري",
    "constitutional": "قانون دستوري",
    "commercial": "قانون تجاري",
    "general": "عام",
}


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def list_books(category=None, book_type=None, q=None, limit=50, offset=0):
    with db_session() as conn:
        where = []
        params = []

        if category:
            where.append("legal_category = ?")
            params.append(category)
        if book_type:
            where.append("book_type = ?")
            params.append(book_type)
        if q:
            where.append(
                "id IN (SELECT rowid FROM research_books_fts WHERE research_books_fts MATCH ?)"
            )
            params.append(q)

        where_sql = " AND ".join(where) if where else "1=1"

        rows = conn.execute(
            f"SELECT * FROM research_books WHERE {where_sql} ORDER BY year DESC, title ASC LIMIT ? OFFSET ?",
            [*params, limit, offset],
        ).fetchall()

        total = conn.execute(
            f"SELECT COUNT(*) FROM research_books WHERE {where_sql}",
            params,
        ).fetchone()[0]

        return {"books": [dict(r) for r in rows], "total": total}


def get_book(book_id: int):
    with db_session() as conn:
        row = conn.execute(
            "SELECT * FROM research_books WHERE id = ?", (book_id,)
        ).fetchone()
        if not row:
            return None
        return dict(row)


def create_book(data: dict) -> int:
    with db_session() as conn:
        ch = _hash(data.get("title", "") + data.get("author", ""))
        cur = conn.execute(
            """INSERT INTO research_books
            (title, title_ar, author, book_type, legal_category, description,
             cover_image, file_path, file_name, file_size, pages, year, language,
             source_name, source_url, official_source, content_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data["title"], data.get("title_ar"), data.get("author"),
                data.get("book_type", "book"), data.get("legal_category", "general"),
                data.get("description"), data.get("cover_image"),
                data.get("file_path"), data.get("file_name"),
                data.get("file_size"), data.get("pages"), data.get("year"),
                data.get("language", "ar"), data.get("source_name"), data.get("source_url"),
                data.get("official_source", 0), ch,
            ),
        )
        return cur.lastrowid


def update_book(book_id: int, data: dict) -> bool:
    with db_session() as conn:
        fields = []
        values = []
        for key in ("title", "title_ar", "author", "book_type", "legal_category",
                    "description", "cover_image", "file_path", "file_name", "file_size",
                    "pages", "year", "language", "source_name", "source_url", "official_source"):
            if key in data:
                fields.append(f"{key} = ?")
                values.append(data[key])

        if not fields:
            return False

        values.append(book_id)
        conn.execute(
            f"UPDATE research_books SET {', '.join(fields)} WHERE id = ?",
            values,
        )
        return True


def delete_book(book_id: int) -> bool:
    with db_session() as conn:
        conn.execute("DELETE FROM research_books WHERE id = ?", (book_id,))
        return True


def get_stats():
    with db_session() as conn:
        stats = {}
        for row in conn.execute(
            "SELECT legal_category, COUNT(*) as cnt FROM research_books GROUP BY legal_category"
        ).fetchall():
            stats[row["legal_category"]] = row["cnt"]

        type_stats = {}
        for row in conn.execute(
            "SELECT book_type, COUNT(*) as cnt FROM research_books GROUP BY book_type"
        ).fetchall():
            type_stats[row["book_type"]] = row["cnt"]

        total = conn.execute("SELECT COUNT(*) FROM research_books").fetchone()[0]
        return {"total": total, "by_category": stats, "by_type": type_stats}


def ensure_dirs():
    base = Path(__file__).resolve().parent.parent / "storage" / "research_books"
    try:
        for cat in LEGAL_CATEGORIES:
            (base / cat).mkdir(parents=True, exist_ok=True)
    except OSError:
        base = Path("/tmp/storage/research_books")
        for cat in LEGAL_CATEGORIES:
            (base / cat).mkdir(parents=True, exist_ok=True)
    return base
