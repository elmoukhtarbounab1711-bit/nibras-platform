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
    rejection_reason TEXT,                      -- سبب الرفض (وثيقة المصادقة §3: رفض مع سبب)
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

-- =====================================================================
-- سجل تدقيق الإجراءات الإدارية (المرحلة 2 — لوحة الإدارة):
-- يُسجَّل كل إجراء إداري (إنشاء/تعديل/حذف محتوى، قبول/رفض تحقق)
-- بالمسؤول والفعل والهدف والتوقيت، وفق وثيقة الأمان §8 (المساءلة
-- وتسوية النزاعات). لم تُحدَّد الوثيقة شكل الجدول — هذا أدنى تنفيذ
-- يفي بالمتطلب (يُوثَّق في D-018).
-- =====================================================================
CREATE TABLE IF NOT EXISTS admin_audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id    INTEGER REFERENCES users(id) ON DELETE SET NULL,  -- يُبقى السجل حتى لو حُذف المسؤول
    action      TEXT NOT NULL,          -- text.create | text.update | text.delete | article.create | article.update | article.delete | verification.approve | verification.reject
    target_type TEXT NOT NULL,          -- legal_text | article | user
    target_id   INTEGER,
    details     TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_admin_audit_log_admin_id ON admin_audit_log(admin_id);
CREATE INDEX IF NOT EXISTS idx_admin_audit_log_created_at ON admin_audit_log(created_at);

-- =====================================================================
-- الذكاء الاصطناعي (المرحلة 3): سجل طلبات الشرح الموجَّه/العام
-- وفق وثيقة 13 §6 (observability) وقاعدة البيانات 06 §3. أرقام المواد
-- المسترجعة تُخزَّن نصًا JSON (SQLite بلا JSONB — قرار D-021).
-- =====================================================================
CREATE TABLE IF NOT EXISTS ai_queries (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER REFERENCES users(id) ON DELETE SET NULL,
    question    TEXT NOT NULL,
    retrieved_article_ids TEXT,      -- نص JSON [id, ...] أو NULL
    response    TEXT NOT NULL,
    mode        TEXT NOT NULL,       -- grounded | general
    provider    TEXT NOT NULL,
    latency_ms  INTEGER,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- =====================================================================
-- الحاسبات القانونية (المرحلة 3): بيانات إسناد الحاسبات + سجل التنفيذ
-- وفق قاعدة البيانات 06 §4. المنطق في دوال مستقلة في services_calculators
-- (المواصفة الوظيفية §4) والجدولان وصف إداري فقط.
-- =====================================================================
CREATE TABLE IF NOT EXISTS calculators (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    slug        TEXT UNIQUE NOT NULL,   -- 'inheritance' ...
    name        TEXT NOT NULL,
    legal_basis TEXT                    -- مرجع المواد/النصوص
);

CREATE TABLE IF NOT EXISTS calculator_runs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    calculator_id INTEGER REFERENCES calculators(id),
    user_id       INTEGER REFERENCES users(id) ON DELETE SET NULL,  -- null = استخدام مجهول
    input_json    TEXT NOT NULL,
    result_json   TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- =====================================================================
-- مساعد المساطر (المرحلة 3): المساطر وخطواتها وتقدم المستخدم
-- وفق قاعدة البيانات 06 §6 (FR-6.1/6.2). خطوات مرتبة بـ step_number
-- والوثائق المطلوبة نص حر مفصول بأسطر.
-- =====================================================================
CREATE TABLE IF NOT EXISTS procedures (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    slug                 TEXT UNIQUE NOT NULL,
    title                TEXT NOT NULL,
    category             TEXT,
    responsible_authority TEXT,
    typical_timeframe    TEXT
);

CREATE TABLE IF NOT EXISTS procedure_steps (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    procedure_id       INTEGER NOT NULL REFERENCES procedures(id) ON DELETE CASCADE,
    step_number        INTEGER NOT NULL,
    title              TEXT NOT NULL,
    description        TEXT NOT NULL,
    required_documents TEXT
);

CREATE TABLE IF NOT EXISTS procedure_progress (
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    procedure_id INTEGER NOT NULL REFERENCES procedures(id) ON DELETE CASCADE,
    step_id      INTEGER NOT NULL REFERENCES procedure_steps(id) ON DELETE CASCADE,
    completed_at TEXT,
    PRIMARY KEY (user_id, procedure_id, step_id)
);

-- مولّد الوثائق (المرحلة 4 — قرار D-022، وثيقة 06 §5):
-- القوالب بيانات (field_schema + body_template Jinja2) لا كود، والتوليد
-- بحفظ نصه في doc_text (بدل مخزن كائنات غير متوفر محليًا) ثم تصدير PDF/DOCX
-- عند الطلب في الذاكرة.
CREATE TABLE IF NOT EXISTS document_templates (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    slug          TEXT UNIQUE NOT NULL,
    name          TEXT NOT NULL,
    category      TEXT NOT NULL,
    field_schema  TEXT NOT NULL,
    body_template TEXT NOT NULL,
    created_at    TEXT
);

CREATE TABLE IF NOT EXISTS generated_documents (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    template_id INTEGER NOT NULL REFERENCES document_templates(id),
    answers_json TEXT NOT NULL,
    version     INTEGER NOT NULL DEFAULT 1,
    doc_text    TEXT NOT NULL,
    created_at  TEXT,
    updated_at  TEXT
);

-- النظام البيئي المهني (المرحلة 5 — قرار D-023، وثيقة 06 §10):
-- ملف مهني واحد لكل مستخدم؛ verification_status هو مصدر الحقيقة لظهور
-- الدليل فقط (الطابور يبقى بوابة الدور)، والوثيقة مخزَّنة محليًا ريثما
-- يُنقل مخزن الكائنات (Architecture §10).
CREATE TABLE IF NOT EXISTS professional_profiles (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    profession_type     TEXT NOT NULL,   -- lawyer|notary|adoul|judicial_commissioner|sworn_translator|judicial_expert
    bio                 TEXT,
    city                TEXT,
    verification_status TEXT NOT NULL DEFAULT 'pending',  -- pending|verified|rejected
    verification_document_key TEXT,
    verification_document_name TEXT,
    phone               TEXT,
    contact_preference  TEXT NOT NULL DEFAULT 'platform', -- visible|platform
    created_at          TEXT,
    updated_at          TEXT
);

CREATE TABLE IF NOT EXISTS professional_specialties (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL REFERENCES professional_profiles(id) ON DELETE CASCADE,
    specialty  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS professional_reviews (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id  INTEGER NOT NULL REFERENCES professional_profiles(id) ON DELETE CASCADE,
    reviewer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rating      INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment     TEXT,
    created_at  TEXT,
    updated_at  TEXT,
    UNIQUE (profile_id, reviewer_id)
);

-- المجتمع (المرحلة 6 — قرار D-024، وثيقة 06 §9): فئات مستقلة عن مكتبة
-- النصوص (وثيقة 16 §1)، منشورات وتعليقات بحالة (visible|hidden|removed)
-- بلا حذف فعلي (أثر تدقيقي — وثيقة 16 §3)، تفاعلات per (user, post, type)،
-- وبلاغات بنمط موحد (post|comment|professional_profile) لطابور الإشراف.
CREATE TABLE IF NOT EXISTS community_categories (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS posts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL REFERENCES community_categories(id),
    title       TEXT NOT NULL,
    body        TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'visible',  -- visible|hidden|removed
    created_at  TEXT,
    updated_at  TEXT
);

CREATE TABLE IF NOT EXISTS comments (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id    INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    body       TEXT NOT NULL,
    status     TEXT NOT NULL DEFAULT 'visible',  -- visible|hidden|removed
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS reactions (
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    post_id    INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    type       TEXT NOT NULL,   -- like|helpful
    created_at TEXT,
    PRIMARY KEY (user_id, post_id, type)
);

CREATE TABLE IF NOT EXISTS reports (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    reporter_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_type TEXT NOT NULL,   -- post|comment|professional_profile
    target_id   INTEGER NOT NULL,
    reason      TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'open',  -- open|actioned|dismissed
    created_at  TEXT,
    resolved_at TEXT,
    resolved_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE (reporter_id, target_type, target_id, status)
);

-- فهارس مفاتيح أجنبية: حذف تسلسلي فعّال وبحث عن جلسات مستخدم/توكنات استعادته
CREATE INDEX IF NOT EXISTS idx_user_roles_role_id ON user_roles(role_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user_id ON password_reset_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_queries_user_id ON ai_queries(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_queries_created_at ON ai_queries(created_at);
CREATE INDEX IF NOT EXISTS idx_calculator_runs_calculator_id ON calculator_runs(calculator_id);
CREATE INDEX IF NOT EXISTS idx_procedure_steps_procedure_id ON procedure_steps(procedure_id);
CREATE INDEX IF NOT EXISTS idx_procedure_progress_user ON procedure_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_generated_documents_user_id ON generated_documents(user_id);
CREATE INDEX IF NOT EXISTS idx_generated_documents_template_id ON generated_documents(template_id);
CREATE INDEX IF NOT EXISTS idx_profiles_directory ON professional_profiles(verification_status, profession_type, city);
CREATE INDEX IF NOT EXISTS idx_professional_specialties_profile ON professional_specialties(profile_id);
CREATE INDEX IF NOT EXISTS idx_professional_reviews_profile ON professional_reviews(profile_id);
CREATE INDEX IF NOT EXISTS idx_posts_category_status ON posts(category_id, status);
CREATE INDEX IF NOT EXISTS idx_comments_post ON comments(post_id);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);

-- =====================================================================
-- سوق القوالب (المرحلة 7 — قرار D-025، وثيقة 06 §8): فئات مستقلة (تُبذر
-- بنفس تصنيف المكتبة — نمط المجتمع D-024)، قوالب بملف قابل للتنزيل يُخزَّن
-- محليًا في uploads/marketplace، وجدول purchases مبكّر بلا نقطة نهاية
-- (payment_id فارغ ريثما تُحسم بوابة الدفع — BRD §5).
-- =====================================================================
CREATE TABLE IF NOT EXISTS marketplace_categories (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS marketplace_templates (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES marketplace_categories(id),
    title       TEXT NOT NULL,
    description TEXT,
    price_cents INTEGER NOT NULL CHECK (price_cents >= 0),
    storage_key TEXT NOT NULL,
    created_at  TEXT,
    updated_at  TEXT
);

CREATE TABLE IF NOT EXISTS purchases (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER REFERENCES users(id) ON DELETE CASCADE,
    template_id INTEGER REFERENCES marketplace_templates(id),
    payment_id  INTEGER,            -- مرجع payments (الفوترة مؤجَّلة — D-025)
    purchased_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_marketplace_templates_category
    ON marketplace_templates(category_id);
"""


def _ensure_column(conn, table: str, column: str, definition: str) -> None:
    """ترحيل خفيف: يضيف عمودًا للجداول القائمة إن لم يكن موجودًا (idempotent)."""
    cols = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})")}
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


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
        # ترحيل خفيف للجداول القائمة (قواعد بيانات أُنشئت قبل المرحلة 2):
        _ensure_column(conn, "user_roles", "rejection_reason", "TEXT")
    # بذر الأدوار الثابتة وبيانات الإسناد بعد إنشاء المخطط (استيراد مؤجَّل
    # لكسر الدورة الظاهرية — نمط ensure_roles القائم في D-021)
    from . import (
        services_auth,
        services_calculators,
        services_community,
        services_documents,
        services_marketplace,
        services_procedures,
    )

    services_auth.ensure_roles()
    services_calculators.ensure_defaults()
    services_procedures.ensure_defaults()
    services_documents.ensure_defaults()
    services_community.ensure_defaults()
    services_marketplace.ensure_defaults()
