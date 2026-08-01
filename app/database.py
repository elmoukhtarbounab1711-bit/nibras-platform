"""
طبقة قاعدة البيانات لمنصة نبراس — المكتبة القانونية والبحث والهوية.

تستخدم SQLite مع محرك FTS5 للبحث النصي الكامل في المواد القانونية العربية،
وجداول الهوية (المستخدمون، الأدوار، الجلسات، استعادة كلمة المرور) وفق وثيقة
المصادقة والتفويض. SQLite مناسبة لمرحلة البداية والتطوير؛ يمكن استبدالها
بـ PostgreSQL لاحقًا دون تغيير طبقة الخدمة (services*.py) لأن الاستعلامات
معزولة هنا.
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "nibras.db"

SCHEMA = """
-- الفروع القانونية (مدني، أسرة، جنائي، دستوري ...)
CREATE TABLE IF NOT EXISTS categories (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    slug        TEXT UNIQUE NOT NULL,
    name        TEXT NOT NULL,
    description TEXT
);

-- النصوص القانونية (دستور، مدونة، قانون، مرسوم، جريدة رسمية ...)
CREATE TABLE IF NOT EXISTS legal_texts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id     INTEGER NOT NULL REFERENCES categories(id),
    type            TEXT NOT NULL,      -- constitution | code | law | decree | gazette | treaty | ruling
    title           TEXT NOT NULL,
    official_ref    TEXT,               -- رقم الظهير/الجريدة الرسمية
    enacted_date    TEXT,               -- YYYY-MM-DD أو نص وصفي
    last_amended    TEXT,
    source_note     TEXT,               -- ملاحظة حول المصدر (للشفافية)
    is_sample_data  INTEGER NOT NULL DEFAULT 1  -- 1 = بيانات نموذجية للعرض، 0 = محتوى موثّق كليًا
);

-- المواد/الفصول داخل كل نص قانوني
CREATE TABLE IF NOT EXISTS articles (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    legal_text_id   INTEGER NOT NULL REFERENCES legal_texts(id) ON DELETE CASCADE,
    number          TEXT NOT NULL,      -- "230" أو "24" ...
    label           TEXT NOT NULL,      -- "المادة 230" أو "الفصل 24"
    content         TEXT NOT NULL,      -- النص القانوني الأصلي
    plain_explanation TEXT,             -- شرح مبسّط (يُعبَّأ لاحقًا بمحرك الذكاء الاصطناعي)
    keywords        TEXT                -- كلمات مفتاحية مفصولة بفواصل
);

-- روابط "مواد ذات صلة"
CREATE TABLE IF NOT EXISTS related_articles (
    article_id          INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    related_article_id  INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    PRIMARY KEY (article_id, related_article_id)
);

-- فهرس بحث نصي كامل (FTS5) على المواد، يدعم العربية بدون تشكيل
CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
    label, content, keywords, content='articles', content_rowid='id'
);

-- مزامنة الفهرس تلقائيًا مع أي تعديل على جدول المواد
CREATE TRIGGER IF NOT EXISTS articles_ai AFTER INSERT ON articles BEGIN
    INSERT INTO articles_fts(rowid, label, content, keywords)
    VALUES (new.id, new.label, new.content, new.keywords);
END;

CREATE TRIGGER IF NOT EXISTS articles_ad AFTER DELETE ON articles BEGIN
    INSERT INTO articles_fts(articles_fts, rowid, label, content, keywords)
    VALUES ('delete', old.id, old.label, old.content, old.keywords);
END;

CREATE TRIGGER IF NOT EXISTS articles_au AFTER UPDATE ON articles BEGIN
    INSERT INTO articles_fts(articles_fts, rowid, label, content, keywords)
    VALUES ('delete', old.id, old.label, old.content, old.keywords);
    INSERT INTO articles_fts(rowid, label, content, keywords)
    VALUES (new.id, new.label, new.content, new.keywords);
END;

-- =====================================================================
-- جدول الهوية (المرحلة 1 — المصادقة والتفويض):
-- المستخدمون والأدوار وجلسات التحديث واستعادة كلمة المرور، وفق
-- وثيقة المصادقة والتفويض (§1، §2.1، §2.4، §2.6) وقاعدة البيانات (§2).
-- =====================================================================

-- المستخدمون
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    email           TEXT NOT NULL UNIQUE COLLATE NOCASE,
    full_name       TEXT NOT NULL,
    password_hash   TEXT NOT NULL,              -- argon2id
    status          TEXT NOT NULL DEFAULT 'active',  -- active | suspended | deleted
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- الأدوار الثابتة (قائمة مغلقة حسب وثيقة المصادقة والتفويض §1)
CREATE TABLE IF NOT EXISTS roles (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT UNIQUE NOT NULL,
    name        TEXT NOT NULL
);

-- علاقة المستخدم بأدواره (يمكن أن يملك أكثر من دور مستقبلًا)
CREATE TABLE IF NOT EXISTS user_roles (
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id     INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    role_status TEXT NOT NULL DEFAULT 'active', -- active | pending_verification | rejected
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (user_id, role_id)
);

-- جلسات تحديث (refresh tokens) — تُخزَّن مجزَّأةً بـ SHA-256 وفق
-- المواصفة التقنية §4 (لا يُخزَّن التوكن الصريح أبدًا)
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    token_hash  TEXT UNIQUE NOT NULL,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at  TEXT NOT NULL
);

-- طلبات استعادة كلمة المرور — تُخزَّن مجزَّأةً بـ SHA-256
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    token_hash  TEXT UNIQUE NOT NULL,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at  TEXT NOT NULL,
    used_at     TEXT
);

-- فهارس مفاتيح أجنبية: حذف تسلسلي فعّال وبحث عن جلسات مستخدم/توكنات استعادته
CREATE INDEX IF NOT EXISTS idx_user_roles_role_id ON user_roles(role_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user_id ON password_reset_tokens(user_id);
"""


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_session():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(reset: bool = False):
    if reset and DB_PATH.exists():
        DB_PATH.unlink()
    with db_session() as conn:
        conn.executescript(SCHEMA)
    # بذر الأدوار الثابتة بعد إنشاء المخطط (من services_auth لتجنب الاستيراد الدائري)
    from . import services_auth

    services_auth.ensure_roles()
