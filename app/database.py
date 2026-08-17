"""
طبقة قاعدة البيانات لمنصة نبراس — المكتبة القانونية والبحث والهوية.

تستخدم SQLite مع محرك FTS5 للبحث النصي الكامل في المواد القانونية العربية،
وجداول الهوية (المستخدمون، الأدوار، الجلسات، استعادة كلمة المرور) وفق وثيقة
المصادقة والتفويض. SQLite مناسبة لمرحلة البداية والتطوير؛ يمكن استبدالها
بـ PostgreSQL لاحقًا دون تغيير طبقة الخدمة (services*.py) لأن الاستعلامات
معزولة هنا.
"""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

# مسار قاعدة بيانات SQLite — يَتعيّن عبر NIBRAS_DB_PATH في الإنتاج ليوضع على
# قرص مُثبَّت (persistent disk) لأن أنظمة PaaS (Render/Railway/Fly) لها
# نظام ملفات عابر (ephemeral) يُمسح عند كل إعادة نشر. الافتراضي محلي.
DB_PATH = Path(os.environ.get(
    "NIBRAS_DB_PATH", str(Path(__file__).parent.parent / "nibras.db")
))

# فهرس بحث نصي كامل (FTS5) على المواد — يخزّن نسخة مطبَّعة من النص
# (nbr_normalize: بلا تشكيل، ألف موحدة، ة→ه، ى→ي ...) ليتلاقى مع تطبيع
# الاستعلام (المرحلة 14). فهرس قائم بذاته (غير مرتبط بجدول خارجي) تُبقي
# المشغّلات نسخته متزامنة تلقائيًا مع أي تعديل على articles.
FTS_DDL = """
CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
    label, content, keywords
);

-- مزامنة الفهرس تلقائيًا مع أي تعديل على جدول المواد (نسخة مطبَّعة)
CREATE TRIGGER IF NOT EXISTS articles_ai AFTER INSERT ON articles BEGIN
    INSERT INTO articles_fts(rowid, label, content, keywords)
    VALUES (new.id, nbr_normalize(new.label), nbr_normalize(new.content),
            nbr_normalize(new.keywords));
END;

CREATE TRIGGER IF NOT EXISTS articles_ad AFTER DELETE ON articles BEGIN
    DELETE FROM articles_fts WHERE rowid = old.id;
END;

CREATE TRIGGER IF NOT EXISTS articles_au AFTER UPDATE ON articles BEGIN
    DELETE FROM articles_fts WHERE rowid = old.id;
    INSERT INTO articles_fts(rowid, label, content, keywords)
    VALUES (new.id, nbr_normalize(new.label), nbr_normalize(new.content),
            nbr_normalize(new.keywords));
END;
"""

JURISPRUDENCE_FTS_DDL = """
CREATE VIRTUAL TABLE IF NOT EXISTS jurisprudence_fts USING fts5(
    title, content, keywords
);

CREATE TRIGGER IF NOT EXISTS jurisprudence_ai AFTER INSERT ON jurisprudence BEGIN
    INSERT INTO jurisprudence_fts(rowid, title, content, keywords)
    VALUES (new.id, nbr_normalize(new.title), nbr_normalize(new.content),
            nbr_normalize(new.court || ' ' || COALESCE(new.source_note, '')));
END;

CREATE TRIGGER IF NOT EXISTS jurisprudence_ad AFTER DELETE ON jurisprudence BEGIN
    DELETE FROM jurisprudence_fts WHERE rowid = old.id;
END;

CREATE TRIGGER IF NOT EXISTS jurisprudence_au AFTER UPDATE ON jurisprudence BEGIN
    DELETE FROM jurisprudence_fts WHERE rowid = old.id;
    INSERT INTO jurisprudence_fts(rowid, title, content, keywords)
    VALUES (new.id, nbr_normalize(new.title), nbr_normalize(new.content),
            nbr_normalize(new.court || ' ' || COALESCE(new.source_note, '')));
END;
"""

SCHEMA = """
-- الفروع القانونية (مدني، أسرة، جنائي، دستوري ...)
CREATE TABLE IF NOT EXISTS categories (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    slug        TEXT UNIQUE NOT NULL,
    name        TEXT NOT NULL,
    description TEXT,
    tenant_id   INTEGER REFERENCES tenants(id)  -- المستأجر المالك (عزل D-036)
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
    is_sample_data  INTEGER NOT NULL DEFAULT 1,  -- 1 = بيانات نموذجية للعرض، 0 = محتوى موثّق كليًا
    jurisdiction_id INTEGER REFERENCES law_jurisdictions(id),  -- الولاية القضائية (القانون المقارن)
    tenant_id       INTEGER REFERENCES tenants(id)  -- المستأجر المالك (عزل D-036)
);

-- المواد/الفصول داخل كل نص قانوني
CREATE TABLE IF NOT EXISTS articles (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    legal_text_id   INTEGER NOT NULL REFERENCES legal_texts(id) ON DELETE CASCADE,
    number          TEXT NOT NULL,      -- "230" أو "24" ...
    label           TEXT NOT NULL,      -- "المادة 230" أو "الفصل 24"
    content         TEXT NOT NULL,      -- النص القانوني الأصلي
    plain_explanation TEXT,             -- شرح مبسّط (يُعبَّأ لاحقًا بمحرك الذكاء الاصطناعي)
    keywords        TEXT,               -- كلمات مفتاحية مفصولة بفواصل
    tenant_id       INTEGER REFERENCES tenants(id)  -- المستأجر المالك (عزل D-036)
);

-- روابط "مواد ذات صلة"
CREATE TABLE IF NOT EXISTS related_articles (
    article_id          INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    related_article_id  INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    PRIMARY KEY (article_id, related_article_id)
);

""" + FTS_DDL + """

-- =====================================================================
-- جدول الهوية (المرحلة 1 — المصادقة والتفويض):
-- المستخدمون والأدوار وجلسات التحديث واستعادة كلمة المرور، وفق
-- وثيقة المصادقة والتفويض (§1، §2.1، §2.4، §2.6) وقاعدة البيانات (§2).
-- =====================================================================

-- المستأجرون (المرحلة 17 — قرار D-035): جاهزية multi-tenant. يُبذر
-- مستأجر افتراضي واحد (slug من الإعداد، افتراضيًا nibras) ويرتبط به كل
-- مستخدم عبر users.tenant_id (عمود يُضاف بترحيل آمن للموجودين). عزل
-- بيانات الوحدات نفسه مؤجَّل لمرحلة multi-tenancy الفعلية.
CREATE TABLE IF NOT EXISTS tenants (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    slug        TEXT UNIQUE NOT NULL COLLATE NOCASE,
    name        TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'active',  -- active | suspended
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- المستخدمون
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    email           TEXT NOT NULL UNIQUE COLLATE NOCASE,
    full_name       TEXT NOT NULL,
    password_hash   TEXT NOT NULL,              -- argon2id
    status          TEXT NOT NULL DEFAULT 'active',  -- active | suspended | deleted
    tenant_id       INTEGER REFERENCES tenants(id),  -- المستأجر (افتراضيًا الرئيسي)
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
-- مزوّدو الذكاء الاصطناعي (تكوين متعدد المزوّدات — D-021 المحسَّن)
-- جداول إدارة المزوّدين (مجاني/مدفوع/محمّل محليًا) من لوحة التحكم.
-- type: noop | gemini | openai | ollama | anthropic
-- base_url حقل اختياري (OpenAI-compatible / Ollama); model معرف النموذج.
-- is_default: واحد فقط بتفعَّل في كل لحظة؛ enable يخبر التوفر.
-- =====================================================================
CREATE TABLE IF NOT EXISTS ai_providers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    type        TEXT NOT NULL,          -- noop | gemini | openai_compatible | anthropic | ollama
    base_url    TEXT NOT NULL DEFAULT '',
    api_key     TEXT NOT NULL DEFAULT '',
    model       TEXT NOT NULL DEFAULT '',
    enabled     INTEGER NOT NULL DEFAULT 0,
    is_default  INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
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
    typical_timeframe    TEXT,
    fees                 TEXT,               -- وصف الرسوم (نص حر)
    faq                  TEXT                -- نص JSON [{"q":..,"a":..}] — أسئلة شائعة
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
    description   TEXT NOT NULL DEFAULT '',
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
    photo_url           TEXT,           -- رابط صورة الملف (إضافي — قرار الواجهة)
    registration_number TEXT,           -- رقم التسجيل المهني
    address             TEXT,
    website             TEXT,
    years_of_experience INTEGER,
    work_hours          TEXT,           -- ساعات العمل (نص حر)
    social_links        TEXT,           -- نص JSON {facebook:.., linkedin:.., twitter:.., instagram:..}
    map_embed           TEXT,           -- خريطة الموقع (رابط/بيانات خريطة)
    tenant_id           INTEGER REFERENCES tenants(id),  -- المستأجر المالك (عزل D-036)
    created_at          TEXT,
    updated_at          TEXT
);

CREATE TABLE IF NOT EXISTS professional_specialties (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL REFERENCES professional_profiles(id) ON DELETE CASCADE,
    specialty  TEXT NOT NULL,
    tenant_id  INTEGER REFERENCES tenants(id)  -- المستأجر المالك (عزل D-036)
);

CREATE TABLE IF NOT EXISTS professional_reviews (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id  INTEGER NOT NULL REFERENCES professional_profiles(id) ON DELETE CASCADE,
    reviewer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rating      INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment     TEXT,
    tenant_id   INTEGER REFERENCES tenants(id),  -- المستأجر المالك (عزل D-036)
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
    tenant_id   INTEGER REFERENCES tenants(id),  -- المستأجر المالك (عزل D-036)
    created_at  TEXT,
    updated_at  TEXT
);

CREATE TABLE IF NOT EXISTS comments (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id    INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    body       TEXT NOT NULL,
    status     TEXT NOT NULL DEFAULT 'visible',  -- visible|hidden|removed
    tenant_id  INTEGER REFERENCES tenants(id),  -- المستأجر المالك (عزل D-036)
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS reactions (
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    post_id    INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    type       TEXT NOT NULL,   -- like|helpful
    created_at TEXT,
    tenant_id  INTEGER REFERENCES tenants(id),  -- المستأجر المالك (عزل D-036)
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
    tenant_id   INTEGER REFERENCES tenants(id),  -- المستأجر المالك (عزل D-036)
    UNIQUE (reporter_id, target_type, target_id, status)
);

-- =====================================================================
-- المقالات القانونية المنشورة (بوابة المقالات — مرحلة الواجهة):
-- فئات مستقلة عن مكتبة النصوص (مثل المجتمع D-024)، مقالات كاملة بغلاف
-- وتصنيف وكلمات مفتاحية وحالة نشر (pending|published|hidden) وعدّادات
-- مشاهدات/إعجابات/تعليقات، مع تفاعلات (إعجاب/تعليق/بلاغ) بنمط موحّد.
-- الدور: يمكن للمشرف وللمستخدم المسجَّل كتابة مقالات؛ نشرها إداري فقط.
-- =====================================================================
CREATE TABLE IF NOT EXISTS blog_categories (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    slug      TEXT UNIQUE NOT NULL,
    name      TEXT NOT NULL,
    tenant_id INTEGER REFERENCES tenants(id)  -- المستأجر المالك (عزل D-036)
);

CREATE TABLE IF NOT EXISTS blog_articles (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id  INTEGER REFERENCES blog_categories(id),
    title        TEXT NOT NULL,
    cover_url    TEXT,
    summary      TEXT,
    body         TEXT NOT NULL,
    keywords     TEXT,                  -- كلمات مفتاحية مفصولة بفواصل
    status       TEXT NOT NULL DEFAULT 'pending',  -- pending|published|hidden
    views        INTEGER NOT NULL DEFAULT 0,
    published_at TEXT,
    jurisdiction_id INTEGER REFERENCES law_jurisdictions(id),  -- الدولة لفئة الدراسات المقارنة
    tenant_id    INTEGER REFERENCES tenants(id),  -- المستأجر المالك (عزل D-036)
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS blog_comments (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL REFERENCES blog_articles(id) ON DELETE CASCADE,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    body       TEXT NOT NULL,
    status     TEXT NOT NULL DEFAULT 'visible',  -- visible|hidden|removed
    tenant_id  INTEGER REFERENCES tenants(id),  -- المستأجر المالك (عزل D-036)
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS blog_likes (
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    article_id INTEGER NOT NULL REFERENCES blog_articles(id) ON DELETE CASCADE,
    tenant_id  INTEGER REFERENCES tenants(id),  -- المستأجر المالك (عزل D-036)
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (user_id, article_id)
);

CREATE TABLE IF NOT EXISTS blog_reports (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    reporter_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    article_id  INTEGER NOT NULL REFERENCES blog_articles(id) ON DELETE CASCADE,
    reason      TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'open',  -- open|actioned|dismissed
    created_at  TEXT,
    resolved_at TEXT,
    resolved_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    tenant_id   INTEGER REFERENCES tenants(id),  -- المستأجر المالك (عزل D-036)
    UNIQUE (reporter_id, article_id, status)
);

-- =====================================================================
-- الإشعارات داخل التطبيق (المرحلة 12): إشعارات دورية لكل مستخدم
-- (نتائج التحقق المهني، تفاعلات المجتمع، قرارات الإشراف). تُنشأ
-- تلقائيًا ضمن معاملة الفعل المُحفِّز (لا يُرسَل إشعار لفعل الذات).
-- =====================================================================
CREATE TABLE IF NOT EXISTS notifications (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type        TEXT NOT NULL,    -- verification.approved | verification.rejected |
                                  -- community.comment | community.reaction |
                                  -- moderation.content_hidden | moderation.content_removed
    title       TEXT NOT NULL,
    body        TEXT,
    link        TEXT,             -- رابط داخلي (مثل /posts/123)
    actor_id    INTEGER REFERENCES users(id) ON DELETE SET NULL,  -- مَن فعَّل الإشعار
    is_read     INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- فهارس مفاتيح أجنبية: حذف تسلسلي فعّال وبحث عن جلسات مستخدم/توكنات استعادته
CREATE INDEX IF NOT EXISTS idx_user_roles_role_id ON user_roles(role_id);
CREATE INDEX IF NOT EXISTS idx_users_tenant ON users(tenant_id);
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
CREATE INDEX IF NOT EXISTS idx_notifications_user_created ON notifications(user_id, created_at, id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, is_read);

-- =====================================================================
-- تسليم الإشعارات الخارجية (المرحلة 16 — قرار D-034): بريد + دفع.
-- ---------------------------------------------------------------------
-- notification_preferences: تفضيل تسليم خارجي لكل (قناة، نوع) — غياب الصف
--   يعني مُفعَّل افتراضيًا (الاشتراك الخفي). القناة in_app أساسية دائمًا
--   (داخل التطبيق) وغير قابلة للتعطيل — التفضيلات للقنوات الخارجية فقط.
-- notification_devices: أجهزة المستخدم لإرسال الدفع (توكن فريد عالميًا،
--   يُحدَّث مالكه عند إعادة التسجيل). جاهزة لربط مزوّد دفع لاحقًا.
-- notification_outbox: صندوق تسليم يُملأ ضمن معاملة notify() (transactional)
--   ويُفرَّغ عبر deliver_pending() يدويًا/مجدولًا — لا بنية خلفية مسبقة.
-- =====================================================================
CREATE TABLE IF NOT EXISTS notification_preferences (
    user_id           INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    channel           TEXT NOT NULL,          -- email | push
    notification_type TEXT NOT NULL,
    enabled           INTEGER NOT NULL DEFAULT 1,
    updated_at        TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (user_id, channel, notification_type)
);

CREATE TABLE IF NOT EXISTS notification_devices (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform      TEXT NOT NULL,              -- android | ios | web
    token         TEXT NOT NULL UNIQUE,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    last_seen_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_notification_devices_user
    ON notification_devices(user_id);

CREATE TABLE IF NOT EXISTS notification_outbox (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    notification_id INTEGER NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
    channel         TEXT NOT NULL,            -- email | push
    recipient       TEXT NOT NULL,            -- بريد المستلم أو توكن جهاز
    status          TEXT NOT NULL DEFAULT 'pending',  -- pending | sent | failed
    attempts        INTEGER NOT NULL DEFAULT 0,
    last_error      TEXT,
    sent_at         TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_notification_outbox_status
    ON notification_outbox(status, id);

-- =====================================================================
-- سوق القوالب (المرحلة 7 — قرار D-025، وثيقة 06 §8): فئات مستقلة (تُبذر
-- بنفس تصنيف المكتبة — نمط المجتمع D-024)، قوالب بملف قابل للتنزيل يُخزَّن
-- محليًا في uploads/marketplace، وجدول purchases مبكّر بلا نقطة نهاية
-- (payment_id فارغ ريثما تُحسم بوابة الدفع — BRD §5).
-- =====================================================================
CREATE TABLE IF NOT EXISTS marketplace_categories (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    tenant_id INTEGER REFERENCES tenants(id)  -- المستأجر المالك (عزل D-036)
);

CREATE TABLE IF NOT EXISTS marketplace_templates (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES marketplace_categories(id),
    title       TEXT NOT NULL,
    description TEXT,
    price_cents INTEGER NOT NULL CHECK (price_cents >= 0),
    storage_key TEXT NOT NULL,
    download_count INTEGER NOT NULL DEFAULT 0,  -- عدّاد مرات التنزيل (عرض في الكتالوج)
    rating      REAL NOT NULL DEFAULT 0,         -- التقييم (0-5، يُضبط إداريًا ريثما تفتح التقييمات)
    image_url   TEXT,                            -- صورة غلاف النموذج (رابط اختياري)
    tenant_id   INTEGER REFERENCES tenants(id),  -- المستأجر المالك (عزل D-036)
    created_at  TEXT,
    updated_at  TEXT
);

CREATE TABLE IF NOT EXISTS purchases (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER REFERENCES users(id) ON DELETE CASCADE,
    template_id INTEGER REFERENCES marketplace_templates(id),
    payment_id  INTEGER,            -- مرجع payments (الفوترة مؤجَّلة — D-025)
    tenant_id   INTEGER REFERENCES tenants(id),  -- المستأجر المالك (عزل D-036)
    purchased_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_marketplace_templates_category
    ON marketplace_templates(category_id);
CREATE INDEX IF NOT EXISTS idx_blog_articles_status
    ON blog_articles(status, published_at);
CREATE INDEX IF NOT EXISTS idx_blog_articles_author
    ON blog_articles(user_id);
CREATE INDEX IF NOT EXISTS idx_blog_articles_category
    ON blog_articles(category_id);
CREATE INDEX IF NOT EXISTS idx_blog_comments_article
    ON blog_comments(article_id);
CREATE INDEX IF NOT EXISTS idx_blog_reports_status
    ON blog_reports(status);

-- =====================================================================
-- التجارة والفوترة (دخل نبراس): باقات (plans) قابلة للشراء، طلبات بحالة
-- pending|paid|cancelled بمصدر تحقق يدوي أولًا (تحويل بنكي/CMI) قابلة
-- للربط ببوابة دفع لاحقًا عبر payment_method (manual أولًا)، حوافظ نقاط
-- (wallet_balances) تُضاف عند التأكيد الإداري للطلب وتُصرف على مكالمات
-- الذكاء الاصطناعي المتقدمة وتصدير الوثائق، مع سجل حركة (credit_ledger)
-- للمساءلة. قرار: إيراد نبراس (محسَّن D-021/B5 سابق).
-- =====================================================================
CREATE TABLE IF NOT EXISTS payment_plans (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    slug        TEXT UNIQUE NOT NULL,
    name        TEXT NOT NULL,
    kind        TEXT NOT NULL,            -- credits | premium_listing
    price_cents INTEGER NOT NULL CHECK (price_cents >= 0),
    credits     INTEGER NOT NULL DEFAULT 0,   -- نقاط عند kind=credits
    duration_days INTEGER,                -- أيام الظهور عند kind=premium
    description TEXT NOT NULL DEFAULT '',
    enabled     INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS orders (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_id      INTEGER NOT NULL REFERENCES payment_plans(id),
    amount_cents INTEGER NOT NULL,
    status       TEXT NOT NULL DEFAULT 'pending',  -- pending | paid | cancelled
    payment_method TEXT NOT NULL DEFAULT 'manual', -- manual أولًا (بوابة لاحقًا)
    note         TEXT,                -- ملاحظة المستخدم/إثبات الدفع
    processed_by INTEGER REFERENCES users(id),       -- من أكّد الطلب (إدارة)
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    processed_at TEXT,
    tenant_id    INTEGER REFERENCES tenants(id)      -- عزل المستأجر (D-036)
);

CREATE TABLE IF NOT EXISTS wallet_balances (
    user_id      INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    credits      INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS credit_ledger (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    delta         INTEGER NOT NULL,              -- +عند الشراء/الإهداء، -عند الإنفاق
    reason        TEXT NOT NULL,                 -- order|ai_research|doc_export|adjust
    reference     TEXT,                          -- مرجع (رقم طلب/معرف وثيقة)
    balance_after INTEGER NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    tenant_id     INTEGER REFERENCES tenants(id) -- عزل المستأجر (D-036)
);

CREATE INDEX IF NOT EXISTS idx_orders_user_created ON orders(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_credit_ledger_user ON credit_ledger(user_id, created_at);

-- =====================================================================
-- نظام الإعلانات (المرحلة 9 — Roadmap Phase 6) — وفق وثيقة 15 وقرار D-027
-- =====================================================================
CREATE TABLE IF NOT EXISTS ad_slots (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ad_campaigns (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_id         INTEGER NOT NULL REFERENCES ad_slots(id),
    campaign_type   TEXT NOT NULL DEFAULT 'general',
                    -- general | sponsored | professional_promotion
    advertiser_name TEXT NOT NULL,
    creative_url    TEXT NOT NULL,
    target_url      TEXT NOT NULL,
    profile_id      INTEGER REFERENCES professional_profiles(id),
                    -- نوع الترويج المهني فقط (وثيقة 15 §4)
    starts_at       TEXT,
    ends_at         TEXT,
    status          TEXT NOT NULL DEFAULT 'active',  -- active|paused|ended
    -- الاستهداف الفئوي (المرحلة 19 — قرار D-037): نوع الفئة (library|
    -- marketplace|jurisprudence) ومعرّفها؛ NULL = حملة عامة بلا استهداف.
    target_category_type  TEXT,
    target_category_id    INTEGER,
    tenant_id       INTEGER REFERENCES tenants(id),  -- المستأجر المالك (عزل D-036)
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS ad_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER NOT NULL REFERENCES ad_campaigns(id) ON DELETE CASCADE,
    user_id     INTEGER REFERENCES users(id) ON DELETE SET NULL,
    event_type  TEXT NOT NULL,   -- impression | click
    tenant_id   INTEGER REFERENCES tenants(id),  -- المستأجر المالك (عزل D-036)
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_ad_events_campaign_created
    ON ad_events(campaign_id, created_at);

-- =====================================================================
-- الاجتهادات القضائية (مرحلة الفقه القضائي): فئات الاجتهاد (مدني، جنائي،
-- إداري، عقاري، ...) وقرارات المحاكم (title + مبدأ + نص). تُنشأ فئات
-- افتراضية في bots kwargs ولا تُلزم النصوص بالتصنيف القديم.
-- =====================================================================
CREATE TABLE IF NOT EXISTS jurisprudence_categories (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    slug            TEXT NOT NULL,
    name            TEXT NOT NULL,
    description     TEXT,
    jurisdiction_id INTEGER REFERENCES law_jurisdictions(id),
                -- NULL = فئة عامة (تراث المغرب)؛ رقم = فئة خاصة بولاية (قرار D-042)
    tenant_id       INTEGER REFERENCES tenants(id)   -- عزل المستأجر (قرار D-036)
);

CREATE TABLE IF NOT EXISTS jurisprudence (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id     INTEGER NOT NULL REFERENCES jurisprudence_categories(id),
    title           TEXT NOT NULL,
    principles      TEXT,               -- مبدأ القرار (خلاصة للحكم)
    content         TEXT NOT NULL,       -- نص الاجتهاد / أسباب الحكم
    court           TEXT,                -- المحكمة المصدرة
    decision_number TEXT,                -- رقم القرار
    decision_date   TEXT,                -- تاريخ القرار (YYYY-MM-DD)
    source_note     TEXT,                -- مصدر الاجتهاد (مرجع النشر)
    pdf_url         TEXT,                -- رابط التحميل الأصلي للقرار (PDF)
    published       INTEGER NOT NULL DEFAULT 1,
    views           INTEGER NOT NULL DEFAULT 0,
    jurisdiction_id INTEGER REFERENCES law_jurisdictions(id),  -- الولاية القضائية (القانون المقارن)
    tenant_id       INTEGER REFERENCES tenants(id),  -- عزل عاجر (D-036)
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_jurisprudence_category
    ON jurisprudence(category_id);
CREATE INDEX IF NOT EXISTS idx_jurisprudence_published
    ON jurisprudence(published);
CREATE INDEX IF NOT EXISTS idx_jurisprudence_categories_tenant
    ON jurisprudence_categories(tenant_id);
CREATE INDEX IF NOT EXISTS idx_jurisprudence_tenant
    ON jurisprudence(tenant_id);

-- =====================================================================
-- القانون المقارن (المرحلة 20 — قرار D-038): مقارنة نصوص من ولايات
-- قضائية متعددة حول موضوع واحد. دراسة مقارنة (comparative_studies)
-- تجمع مقارنات (comparative_entries) كلٌّ منها يرجع إلى ولاية قضائية
-- (law_jurisdictions) ونصٍّ ومادة في مكتبة النصوص.
-- =====================================================================
CREATE TABLE IF NOT EXISTS law_jurisdictions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    slug            TEXT UNIQUE NOT NULL COLLATE NOCASE,
    name            TEXT NOT NULL,
    is_comparative  INTEGER NOT NULL DEFAULT 1,
                -- المغرب = 0: مستقل وغير وارد في القانون المقارن (قرار D-042)
    tenant_id       INTEGER REFERENCES tenants(id),  -- المستأجر المالك (عزل D-036)
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS comparative_studies (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER REFERENCES users(id) ON DELETE SET NULL,
                -- منشئ الدراسة (أي مستخدم مسجَّل)
    title       TEXT NOT NULL,
    description TEXT,
    status      TEXT NOT NULL DEFAULT 'draft',
                -- draft | published | hidden (نشر إداري حصري)
    tenant_id   INTEGER REFERENCES tenants(id),  -- المستأجر المالك (عزل D-036)
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS comparative_entries (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    study_id        INTEGER NOT NULL REFERENCES comparative_studies(id)
                            ON DELETE CASCADE,
    jurisdiction_id INTEGER NOT NULL REFERENCES law_jurisdictions(id),
    legal_text_id   INTEGER REFERENCES legal_texts(id) ON DELETE CASCADE,
                    -- النص المقارن (اختياري مع المادة)
    article_id      INTEGER REFERENCES articles(id) ON DELETE CASCADE,
                    -- المادة المقارنة داخل النص
    note            TEXT,             -- ملاحظة الباحث حول الجانب المقارن
    position        INTEGER NOT NULL DEFAULT 0,
    tenant_id       INTEGER REFERENCES tenants(id),  -- المستأجر المالك (عزل D-036)
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_law_jurisdictions_tenant
    ON law_jurisdictions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_comparative_studies_tenant
    ON comparative_studies(tenant_id);
CREATE INDEX IF NOT EXISTS idx_comparative_entries_tenant
    ON comparative_entries(tenant_id);
CREATE INDEX IF NOT EXISTS idx_comparative_entries_study
    ON comparative_entries(study_id);

-- فهارس عزل المستأجر (D-036): تسريع كل بحث مُقيَّد بـ tenant_id
-- (تُنشأ بعد كل الجداول لأن marketplace/ads تُعرَّف لاحقًا في المخطط)
CREATE INDEX IF NOT EXISTS idx_categories_tenant ON categories(tenant_id);
CREATE INDEX IF NOT EXISTS idx_legal_texts_tenant ON legal_texts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_articles_tenant ON articles(tenant_id);
CREATE INDEX IF NOT EXISTS idx_posts_tenant ON posts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_comments_tenant ON comments(tenant_id);
CREATE INDEX IF NOT EXISTS idx_reactions_tenant ON reactions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_reports_tenant ON reports(tenant_id);
CREATE INDEX IF NOT EXISTS idx_professional_profiles_tenant ON professional_profiles(tenant_id);
CREATE INDEX IF NOT EXISTS idx_professional_specialties_tenant ON professional_specialties(tenant_id);
CREATE INDEX IF NOT EXISTS idx_professional_reviews_tenant ON professional_reviews(tenant_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_categories_tenant ON marketplace_categories(tenant_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_templates_tenant ON marketplace_templates(tenant_id);
CREATE INDEX IF NOT EXISTS idx_purchases_tenant ON purchases(tenant_id);
CREATE INDEX IF NOT EXISTS idx_ad_campaigns_tenant ON ad_campaigns(tenant_id);
CREATE INDEX IF NOT EXISTS idx_ad_events_tenant ON ad_events(tenant_id);
CREATE INDEX IF NOT EXISTS idx_blog_categories_tenant ON blog_categories(tenant_id);
CREATE INDEX IF NOT EXISTS idx_blog_articles_tenant ON blog_articles(tenant_id);
CREATE INDEX IF NOT EXISTS idx_blog_comments_tenant ON blog_comments(tenant_id);
CREATE INDEX IF NOT EXISTS idx_blog_likes_tenant ON blog_likes(tenant_id);
CREATE INDEX IF NOT EXISTS idx_blog_reports_tenant ON blog_reports(tenant_id);
"""


def _ensure_column(conn, table: str, column: str, definition: str) -> None:
    """ترحيل خفيف: يضيف عمودًا للجداول القائمة إن لم يكن موجودًا (idempotent)."""
    cols = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})")}
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _table_exists(conn, table: str) -> bool:
    """هل الجدول موجود في قاعدة البيانات (لترحيل آمن للقواعد القديمة)؟"""
    return conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)
    ).fetchone() is not None


def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    # وضع WAL: قراءة متزامنة مع كتابة واحدة بين العُمّال المتعددين (gunicorn)
    # + مهلة انتظار القفل للنجاة من التزاحم العابر بدل خطأ locked فوري.
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 30000")
    # دالة التطبيع العربي — تستخدمها مشغّلات FTS عند فهرسة المواد
    from . import arabic_text

    conn.create_function(
        "nbr_normalize", 1, arabic_text.normalize_arabic, deterministic=True
    )
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


def _migrate_articles_fts(conn) -> None:
    """يعيد بناء فهرس FTS عند وجود نسخة قديمة (مرتبطة بجدول خارجي).

    قواعد البيانات المنشأة قبل المرحلة 14 تستخدم articles_fts كفهرس خارجي
    (content='articles') يخزّن النص الخام. يُكتشف ذلك من تعريف الجدول
    المخزَّن في sqlite_master، فيُهدم الفهرس والمشغّلات ويُعاد إنشاؤها
    بالصيغة الجديدة ثم يُعاد تعبئتها بنصوص مطبَّعة (idempotent).
    """
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='articles_fts'"
    ).fetchone()
    needs_rebuild = row is None or "content='articles'" in (row["sql"] or "")
    if not needs_rebuild:
        return
    for trigger in ("articles_ai", "articles_ad", "articles_au"):
        conn.execute(f"DROP TRIGGER IF EXISTS {trigger}")
    conn.execute("DROP TABLE IF EXISTS articles_fts")
    conn.executescript(FTS_DDL)
    conn.execute(
        """INSERT INTO articles_fts(rowid, label, content, keywords)
           SELECT id, nbr_normalize(label), nbr_normalize(content),
                  nbr_normalize(keywords) FROM articles"""
    )


def _migrate_jurisprudence_fts(conn) -> None:
    """يُنشئ فهرس FTS للاجتهادات ويعيد تعبئته من الجداول (idempotent)."""
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='jurisprudence_fts'"
    ).fetchone()
    if row is None:
        conn.executescript(JURISPRUDENCE_FTS_DDL)
    elif "content='jurisprudence'" in (row["sql"] or ""):
        for trigger in ("jurisprudence_ai", "jurisprudence_ad", "jurisprudence_au"):
            conn.execute(f"DROP TRIGGER IF EXISTS {trigger}")
        conn.execute("DROP TABLE IF EXISTS jurisprudence_fts")
        conn.executescript(JURISPRUDENCE_FTS_DDL)
    else:
        return
    conn.execute(
        """INSERT INTO jurisprudence_fts(rowid, title, content, keywords)
           SELECT id, nbr_normalize(title), nbr_normalize(content),
                  nbr_normalize(COALESCE(court, '') || ' ' ||
                                COALESCE(source_note, '')) FROM jurisprudence"""
    )


def _migrate_jurisdiction_scoped_categories() -> None:
    """فئات اجتهاد مستقلة لكل ولاية + مغرب خارج القانون المقارن (قرار D-042).

    تُنفَّذ على اتصال مستقل بعد اكتمال الصفقة الرئيسية لأنها تعيد بناء جدول
    (إزالة قيد UNIQUE(slug)) ولا يمكن تغيير PRAGMA foreign_keys وسط صفقة.
    ثلاث عمليات idempotent:
      1. عمود jurisdiction_id في jurisprudence_categories (NULL = فئة عامة/
         تراث المغرب؛ رقم = فئة خاصة بولاية).
      2. إعادة بناء الجدول لإزالة UNIQUE(slug) واستبدالها بفهارس فريدة جزئية.
      3. عزل المغرب: is_comparative=0 (لا يُمس أي من محتواه).
    ثم إعادة ربط الاجتهادات القائمة (الولايات) بفئات خاصة بكل ولاية
    (المغرب بلا jurisdiction_id يبقى على فئاته العامة دون تغيير).
    """
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("PRAGMA busy_timeout = 30000")
    from . import arabic_text

    conn.create_function(
        "nbr_normalize", 1, arabic_text.normalize_arabic, deterministic=True
    )
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(jurisprudence_categories)")]
        if "jurisdiction_id" not in cols:
            conn.execute(
                "ALTER TABLE jurisprudence_categories ADD COLUMN jurisdiction_id "
                "INTEGER REFERENCES law_jurisdictions(id)"
            )
        auto = conn.execute("PRAGMA index_list('jurisprudence_categories')").fetchall()
        needs_rebuild = any((r[1] or "").startswith("sqlite_autoindex")
                            for r in auto)
        if needs_rebuild:
            conn.execute(
                "ALTER TABLE jurisprudence_categories "
                "RENAME TO jurisprudence_categories_old"
            )
            conn.execute(
                """CREATE TABLE jurisprudence_categories (
                       id              INTEGER PRIMARY KEY AUTOINCREMENT,
                       slug            TEXT NOT NULL,
                       name            TEXT NOT NULL,
                       description     TEXT,
                       jurisdiction_id INTEGER REFERENCES law_jurisdictions(id),
                       tenant_id       INTEGER REFERENCES tenants(id)
                   )"""
            )
            conn.execute(
                "INSERT INTO jurisprudence_categories "
                "(id, slug, name, description, jurisdiction_id, tenant_id) "
                "SELECT id, slug, name, description, jurisdiction_id, tenant_id "
                "FROM jurisprudence_categories_old"
            )
            conn.execute(
                "UPDATE sqlite_sequence SET seq = (SELECT MAX(id) FROM "
                "jurisprudence_categories) WHERE name = 'jurisprudence_categories'"
            )
            conn.execute("DROP TABLE jurisprudence_categories_old")
        # الفهارس الفريدة الجزئية (سواء أُعيد البناء أم لا — idempotent):
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_jc_slug_legacy "
            "ON jurisprudence_categories(slug) WHERE jurisdiction_id IS NULL"
        )
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_jc_slug_jurisdiction "
            "ON jurisprudence_categories(slug, jurisdiction_id) "
            "WHERE jurisdiction_id IS NOT NULL"
        )
        # عزل المغرب خارج القانون المقارن (بدون لمس أي من بياناته)
        jcols = [r[1] for r in conn.execute("PRAGMA table_info(law_jurisdictions)")]
        if "is_comparative" not in jcols:
            conn.execute(
                "ALTER TABLE law_jurisdictions ADD COLUMN is_comparative "
                "INTEGER NOT NULL DEFAULT 1"
            )
        conn.execute("UPDATE law_jurisdictions SET is_comparative = 0 "
                     "WHERE slug = 'morocco'")
        conn.execute("UPDATE law_jurisdictions SET is_comparative = 1 "
                     "WHERE is_comparative IS NULL")
        # إعادة ربط اجتهادات الولايات بالفئات الخاصة بكل ولاية (المغرب مستثنى)
        pairs = conn.execute(
            """SELECT DISTINCT j.jurisdiction_id AS jid, c.slug AS slug,
                               c.name AS name
               FROM jurisprudence j
               JOIN jurisprudence_categories c ON c.id = j.category_id
               WHERE j.jurisdiction_id IS NOT NULL"""
        ).fetchall()
        for pid in pairs:
            src = conn.execute(
                "SELECT id, tenant_id FROM jurisprudence_categories "
                "WHERE slug = ? AND jurisdiction_id IS NULL",
                (pid["slug"],),
            ).fetchone()
            row = conn.execute(
                "SELECT id FROM jurisprudence_categories WHERE slug = ? "
                "AND jurisdiction_id = ?",
                (pid["slug"], pid["jid"]),
            ).fetchone()
            if row is not None:
                new_id = row[0]
            else:
                cur = conn.execute(
                    "INSERT INTO jurisprudence_categories "
                    "(slug, name, description, jurisdiction_id, tenant_id) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (pid["slug"], pid["name"], "",
                     pid["jid"], (None if src is None else src["tenant_id"])),
                )
                new_id = cur.lastrowid
            conn.execute(
                "UPDATE jurisprudence SET category_id = ? WHERE jurisdiction_id = ? "
                "AND category_id IN (SELECT id FROM jurisprudence_categories "
                "WHERE slug = ? AND jurisdiction_id IS NULL)",
                (new_id, pid["jid"], pid["slug"]),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _migrate_jurisprudence_category_fk() -> None:
    """يُصلح قيد FK لجدول الاجتهادات (بعد قرار D-042).

    عند إعادة بناء jurisprudence_categories (إزالة UNIQUE(slug)) بقيت
    jurisprudence.category_id تُشير إلى الجدول القديم jurisprudence_categories_old
    (فئات مرقمة 1..11 فقط). النتيجة: أي اجتهاد جديد لفئة ولاية (مصر وغيرها —
    ids تبدأ من 12) يفشل بقيد FOREIGN KEY. هنا يُعاد بناء الجدول بحيث يشير
    category_id إلى jurisprudence_categories ويعاد إنشاء الفهارس والمشغّلات ثم
    يُحذف الجدول القديم. Idempotent: الكشف عبر PRAGMA foreign_key_list.
    """
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("PRAGMA busy_timeout = 60000")
    from . import arabic_text

    conn.create_function(
        "nbr_normalize", 1, arabic_text.normalize_arabic, deterministic=True
    )
    try:
        fks = conn.execute("PRAGMA foreign_key_list('jurisprudence')").fetchall()
        needs = any(
            r["from"] == "category_id" and r["table"] == "jurisprudence_categories_old"
            for r in fks
        )
        if not needs:
            return
        triggers = [
            dict(r)
            for r in conn.execute(
                "SELECT name, sql FROM sqlite_master "
                "WHERE type='trigger' AND tbl_name='jurisprudence'"
            )
        ]
        indexes = [
            dict(r)
            for r in conn.execute(
                "SELECT name, sql FROM sqlite_master "
                "WHERE type='index' AND tbl_name='jurisprudence' AND sql IS NOT NULL"
            )
        ]
        for trig in triggers:
            conn.execute(f"DROP TRIGGER IF EXISTS {trig['name']}")
        conn.execute(
            """CREATE TABLE jurisprudence_new (
                   id              INTEGER PRIMARY KEY AUTOINCREMENT,
                   category_id     INTEGER NOT NULL
                                   REFERENCES jurisprudence_categories(id),
                   title           TEXT NOT NULL,
                   principles      TEXT,
                   content         TEXT NOT NULL,
                   court           TEXT,
                   decision_number TEXT,
                   decision_date   TEXT,
                   source_note     TEXT,
                   published       INTEGER NOT NULL DEFAULT 1,
                   views           INTEGER NOT NULL DEFAULT 0,
                   tenant_id       INTEGER REFERENCES tenants(id),
                   created_at      TEXT NOT NULL DEFAULT (datetime('now')),
                   updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
                   pdf_url         TEXT,
                   jurisdiction_id INTEGER REFERENCES law_jurisdictions(id)
               )"""
        )
        conn.execute(
            """INSERT INTO jurisprudence_new
               (id, category_id, title, principles, content, court,
                decision_number, decision_date, source_note, published, views,
                tenant_id, created_at, updated_at, pdf_url, jurisdiction_id)
               SELECT id, category_id, title, principles, content, court,
                      decision_number, decision_date, source_note, published, views,
                      tenant_id, created_at, updated_at, pdf_url, jurisdiction_id
               FROM jurisprudence"""
        )
        conn.execute("DROP TABLE jurisprudence")
        conn.execute("ALTER TABLE jurisprudence_new RENAME TO jurisprudence")
        for idx in indexes:
            conn.execute(idx["sql"])
        for trig in triggers:
            conn.execute(trig["sql"])
        conn.execute("DROP TABLE IF EXISTS jurisprudence_categories_old")
        conn.commit()
        print("[migrate] repaired jurisprudence.category_id FK -> "
              "jurisprudence_categories (dropped stale *_old)")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(reset: bool = False):
    if reset and DB_PATH.exists():
        DB_PATH.unlink()
    with db_session() as conn:
        # ترحيل مسبق للقواعد القائمة (أُنشئت قبل المرحلة 17): يجب وجود جدول
        # tenants وعمود users.tenant_id قبل تنفيذ SCHEMA لأن فهارسه تشير إليهما.
        # للقواعد الجديدة يُنشئ SCHEMA نفسه الجدولين — نتخطى العمود هنا فقط.
        conn.execute(
            """CREATE TABLE IF NOT EXISTS tenants (
                   id          INTEGER PRIMARY KEY AUTOINCREMENT,
                   slug        TEXT UNIQUE NOT NULL COLLATE NOCASE,
                   name        TEXT NOT NULL,
                   status      TEXT NOT NULL DEFAULT 'active',
                   created_at  TEXT NOT NULL DEFAULT (datetime('now'))
               )"""
        )
        if _table_exists(conn, "users"):
            _ensure_column(conn, "users", "tenant_id", "INTEGER REFERENCES tenants(id)")
        # ترحيل عزل المستأجر (D-036): يضيف عمود tenant_id للجداول الـ 15
        # المعزولة في القواعد القائمة (أُنشئت قبل المرحلة 18) قبل تنفيذ
        # SCHEMA حتى تطبَّق فهارس العزل. للقواعد الجديدة يُنشئ SCHEMA
        # العمود والفهارس مباشرة — نتخطى الإضافة هنا فقط.
        for _t in (
            "categories",
            "legal_texts",
            "articles",
            "professional_profiles",
            "professional_specialties",
            "professional_reviews",
            "posts",
            "comments",
            "reactions",
            "reports",
            "marketplace_categories",
            "marketplace_templates",
            "purchases",
            "ad_campaigns",
            "ad_events",
            "jurisprudence_categories",
            "jurisprudence",
            "law_jurisdictions",
            "comparative_studies",
            "comparative_entries",
        ):
            if _table_exists(conn, _t):
                _ensure_column(conn, _t, "tenant_id", "INTEGER REFERENCES tenants(id)")
        conn.executescript(SCHEMA)
        # ترحيل خفيف للجداول القائمة (قواعد بيانات أُنشئت قبل المرحلة 2):
        _ensure_column(conn, "user_roles", "rejection_reason", "TEXT")
        # ترحيل الفهرس للصيغة المطبَّعة (المرحلة 14):
        _migrate_articles_fts(conn)
        # فهرس FTS للاجتهادات القضائية (فقه قضائي):
        _migrate_jurisprudence_fts(conn)
        # عدّاد مشاهدات المواد (قسم المقالات في الواجهة + توليد PDF):
        _ensure_column(conn, "articles", "views", "INTEGER NOT NULL DEFAULT 0")
        # حقول القوانين الإضافية (الوصف/الجهة الناشرة + ملف PDF مرفوع إداريًا):
        _ensure_column(conn, "legal_texts", "description", "TEXT")
        _ensure_column(conn, "legal_texts", "issuing_body", "TEXT")
        _ensure_column(conn, "legal_texts", "uploaded_pdf_key", "TEXT")
        # حقول الملف المهني الإضافية (صفحة الملف في الواجهة):
        for _col, _def in (
            ("photo_url", "TEXT"),
            ("registration_number", "TEXT"),
            ("address", "TEXT"),
            ("website", "TEXT"),
            ("years_of_experience", "INTEGER"),
            ("work_hours", "TEXT"),
            ("social_links", "TEXT"),
            ("map_embed", "TEXT"),
        ):
            _ensure_column(conn, "professional_profiles", _col, _def)
        # رسوم وأسئلة المساطر الشائعة:
        _ensure_column(conn, "procedures", "fees", "TEXT")
        _ensure_column(conn, "procedures", "faq", "TEXT")
        # عدّاد تحميل القوالب والتقييم والغلاف:
        _ensure_column(conn, "marketplace_templates", "download_count",
                       "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(conn, "marketplace_templates", "rating", "REAL NOT NULL DEFAULT 0")
        _ensure_column(conn, "marketplace_templates", "image_url", "TEXT")
        # الظهور المميز للملفات المهنية (المرحلة 19 — دخل نبراس): تاريخ
        # انتهاء الاشتراك المميز (NULL = غير مميز). يُفعَّل عند تأكيد طلب
        # premium_listing إداريًا، ويُقرأ في ترتيب الدليل وأولوية الظهور.
        _ensure_column(conn, "professional_profiles", "premium_until",
                       "TEXT")
        # الاستهداف الفئوي للحملات الإعلانية (المرحلة 19 — قرار D-037):
        _ensure_column(conn, "ad_campaigns", "target_category_type", "TEXT")
        _ensure_column(conn, "ad_campaigns", "target_category_id", "INTEGER")
        # ربط النصوص والاجتهادات بالولايات القضائية (صفحات القانون المقارن — D-038):
        _ensure_column(conn, "legal_texts", "jurisdiction_id", "INTEGER")
        _ensure_column(conn, "jurisprudence", "jurisdiction_id", "INTEGER")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_legal_texts_jurisdiction "
            "ON legal_texts(jurisdiction_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_jurisprudence_jurisdiction "
            "ON jurisprudence(jurisdiction_id)"
        )
        # رابط التحميل الأصلي للقرار القضائي (الاجتهاد يبقى PDF قابلاً للتحميل):
        _ensure_column(conn, "jurisprudence", "pdf_url", "TEXT")
    # بذر الأدوار الثابتة وبيانات الإسناد بعد إنشاء المخطط (استيراد مؤجَّل
    # لكسر الدورة الظاهرية — نمط ensure_roles القائم في D-021)
    from . import (
        services_ads,
        services_auth,
        services_billing,
        services_blog,
        services_calculators,
        services_community,
        services_comparative,
        services_documents,
        services_jurisprudence,
        services_marketplace,
        services_procedures,
        services_tenants,
    )

    services_auth.ensure_roles()
    services_billing.ensure_defaults()
    services_calculators.ensure_defaults()
    services_procedures.ensure_defaults()
    services_documents.ensure_defaults()
    services_community.ensure_defaults()
    services_marketplace.ensure_defaults()
    services_ads.ensure_defaults()
    services_blog.ensure_defaults()
    services_jurisprudence.ensure_defaults()
    services_comparative.ensure_defaults()
    # فئات اجتهاد مستقلة لكل ولاية + المغرب خارج القانون المقارن (D-042):
    # تُنفَّذ بعد بذر الولايات (حتى تُعزل المغرب في القواعد الجديدة أيضًا)
    # وبعد انتهاء الصفقة الرئيسية (إعادة البناء تتطلب PRAGMA خارج الصفقة).
    _migrate_jurisdiction_scoped_categories()
    # إصلاح FK الاجتهادات (بقايا قرار D-042): category_id إلى الجدول الفعلي
    # (كان يُشير إلى *_old). idempotent — يعمل بلا قيدَ إن كان سليمًا.
    _migrate_jurisprudence_category_fk()
    # المستأجر الافتراضي ثم إلحاق المستخدمين الموجودين به (idempotent)
    services_tenants.ensure_defaults()
    services_tenants.backfill_default_tenant()
    # إلحاق صفوف العزل القائمة (بلا مستأجر) بالمستأجر الافتراضي (idempotent)
    services_tenants.backfill_isolated_tables()
