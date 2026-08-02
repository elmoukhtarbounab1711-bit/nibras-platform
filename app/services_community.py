"""
خدمات المجتمع (المرحلة 6 — Roadmap Phase 5، قرار D-024).

منشورات وتعليقات داخل فئات مستقلة (وثيقة 16 §1 و DB §9)، بحالة محتوى
(visible|hidden|removed) بلا حذف فعلي (أثر تدقيقي — وثيقة 16 §3)، تفاعلات
per (user, post, type) مع تبديل، بلاغات موحدة (post|comment|
professional_profile) لطابور الإشراف، وشارة تحقُّق على محتوى المحترفين
verified (وثيقة 16 §5). النقاط (reputation) والمتابعة (follows) مؤجَّلتان
لحسم صيغة النقاط (وثيقة 16 §2) — قرار D-024.
"""
from .database import db_session
from .services_notifications import notify

# أنواع التفاعل (وثيقة API § Community: like|helpful|etc)
REACTION_TYPES = ("like", "helpful")

# أهداف البلاغات الموحدة (جدول reports §9 — المجتمع + الدليل المهني)
REPORT_TARGETS = ("post", "comment", "professional_profile")

# حدود المدخلات (معايير داخلية لمكافحة الإساءة — وثيقة 16 §4)
POST_TITLE_MAX = 300
POST_BODY_MAX = 20000
COMMENT_BODY_MAX = 5000

DEFAULT_LIST_LIMIT = 20
MAX_LIST_LIMIT = 100

# نفس تصنيف مكتبة النصوص (وثيقة 16 §1: إعادة الاستخدام المفهومية مع جدول مستقل)
CATEGORY_SEED = (
    ("dostouri", "القانون الدستوري"),
    ("madani", "القانون المدني"),
    ("usra", "قانون الأسرة"),
    ("jinai", "القانون الجنائي"),
    ("shughl", "قانون الشغل"),
    ("tijari", "القانون التجاري"),
)


class CommunityError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def ensure_defaults():
    """بذر فئات المجتمع إن كانت فارغة (idempotent — نمط ensure_defaults)."""
    with db_session() as conn:
        count = conn.execute(
            "SELECT COUNT(*) AS c FROM community_categories"
        ).fetchone()["c"]
        if count == 0:
            for slug, name in CATEGORY_SEED:
                conn.execute(
                    "INSERT INTO community_categories (slug, name) VALUES (?, ?)",
                    (slug, name),
                )


def _cap(value, max_len):
    return value[:max_len]


def _category_exists(conn, category_id) -> bool:
    return conn.execute(
        "SELECT 1 FROM community_categories WHERE id = ?", (category_id,)
    ).fetchone() is not None


def _author_verified_flag(user_id: int) -> str:
    return (
        "EXISTS (SELECT 1 FROM professional_profiles pp "
        f"WHERE pp.user_id = {user_id} AND pp.verification_status = 'verified')"
    )


_POST_COLUMNS = (
    "SELECT p.id, p.user_id, u.full_name AS author_name, "
    + _author_verified_flag("u.id")
    + " AS author_verified, "
    "p.category_id, p.title, p.body, p.status, p.created_at, p.updated_at, "
    "(SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id "
    " AND c.status = 'visible') AS comment_count "
    "FROM posts p JOIN users u ON u.id = p.user_id"
)


def _reactions_map(conn, post_ids: list) -> dict:
    """{post_id: {type: count}} دفعة واحدة — نمط _specialties_map."""
    if not post_ids:
        return {}
    placeholders = ",".join("?" for _ in post_ids)
    rows = conn.execute(
        f"SELECT post_id, type, COUNT(*) AS c FROM reactions "
        f"WHERE post_id IN ({placeholders}) GROUP BY post_id, type",
        post_ids,
    ).fetchall()
    out = {}
    for row in rows:
        out.setdefault(row["post_id"], {})[row["type"]] = row["c"]
    return out


def _post_item(row, reactions: dict, my_reactions=None) -> dict:
    counts = reactions or {}
    item = {
        "id": row["id"],
        "author_id": row["user_id"],
        "author_name": row["author_name"],
        "author_is_verified": bool(row["author_verified"]),
        "category_id": row["category_id"],
        "title": row["title"],
        "body": row["body"],
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "comment_count": row["comment_count"],
        "reactions": counts,
        "reaction_count": sum(counts.values()),
    }
    if my_reactions is not None:
        item["my_reactions"] = my_reactions
    return item


def _comment_item(row) -> dict:
    return {
        "id": row["id"],
        "post_id": row["post_id"],
        "author_id": row["user_id"],
        "author_name": row["author_name"],
        "author_is_verified": bool(row["author_verified"]),
        "body": row["body"],
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _my_reactions(conn, user_id, post_id) -> list:
    if user_id is None:
        return []
    rows = conn.execute(
        "SELECT type FROM reactions WHERE user_id = ? AND post_id = ?",
        (user_id, post_id),
    ).fetchall()
    return [r["type"] for r in rows]


# ---------------------------------------------------------------------------
# القراءة العامة
# ---------------------------------------------------------------------------

def list_categories():
    with db_session() as conn:
        rows = conn.execute(
            """SELECT c.id, c.slug, c.name,
                      (SELECT COUNT(*) FROM posts p
                       WHERE p.category_id = c.id AND p.status = 'visible')
                      AS post_count
               FROM community_categories c ORDER BY c.id"""
        ).fetchall()
        return [dict(r) for r in rows]


def list_posts(category_id=None, limit: int = DEFAULT_LIST_LIMIT,
               offset: int = 0):
    limit = max(1, min(int(limit or DEFAULT_LIST_LIMIT), MAX_LIST_LIMIT))
    offset = max(0, int(offset or 0))
    query = _POST_COLUMNS
    conditions = ["p.status = 'visible'"]
    params = []
    if category_id is not None:
        conditions.append("p.category_id = ?")
        params.append(int(category_id))
    query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY p.created_at DESC, p.id DESC LIMIT ? OFFSET ?"
    params += [limit, offset]
    with db_session() as conn:
        rows = conn.execute(query, params).fetchall()
        ids = [r["id"] for r in rows]
        reactions = _reactions_map(conn, ids)
        return [_post_item(dict(r), reactions.get(r["id"])) for r in rows]


def get_post(post_id: int, viewer_id=None):
    with db_session() as conn:
        row = conn.execute(
            _POST_COLUMNS
            + " WHERE p.id = ? AND (p.status = 'visible' OR p.user_id = ?)",
            (post_id, viewer_id or -1),
        ).fetchone()
        if not row:
            return None
        comments = conn.execute(
            """SELECT c.id, c.post_id, c.user_id, u.full_name AS author_name,
                      """ + _author_verified_flag("u.id") + """ AS author_verified,
                      c.body, c.status, c.created_at, c.updated_at
               FROM comments c JOIN users u ON u.id = c.user_id
               WHERE c.post_id = ? AND c.status = 'visible'
               ORDER BY c.created_at, c.id""",
            (post_id,),
        ).fetchall()
        reactions = _reactions_map(conn, [post_id]).get(post_id, {})
        return _post_item(
            dict(row), reactions,
            my_reactions=(
                _my_reactions(conn, viewer_id, post_id)
                if viewer_id is not None else None
            ),
        ) | {"comments": [_comment_item(dict(c)) for c in comments]}


# ---------------------------------------------------------------------------
# الكتابة (المؤلف أو المشرف فقط للحذف/التعديل)
# ---------------------------------------------------------------------------

def _visible_or_owner_post(conn, post_id, user_id):
    row = conn.execute(
        "SELECT id, user_id, status FROM posts WHERE id = ?", (post_id,)
    ).fetchone()
    if not row:
        raise CommunityError("المنشور غير موجود.", 404)
    if row["status"] != "visible" and row["user_id"] != user_id:
        raise CommunityError("المنشور غير موجود.", 404)
    return row


def create_post(user_id: int, data: dict) -> dict:
    title = (data.get("title") or "").strip()
    body = (data.get("body") or "").strip()
    if not title or not body:
        raise CommunityError("العنوان والمحتوى (body) مطلوبان.", 400)
    title = _cap(title, POST_TITLE_MAX)
    body = _cap(body, POST_BODY_MAX)
    category_id = data.get("category_id")
    with db_session() as conn:
        if not _category_exists(conn, category_id):
            raise CommunityError("الفئة غير موجودة.", 400)
        cur = conn.execute(
            "INSERT INTO posts (user_id, category_id, title, body, status, "
            "created_at, updated_at) VALUES (?, ?, ?, ?, 'visible', "
            "datetime('now'), datetime('now'))",
            (user_id, category_id, title, body),
        )
        post_id = cur.lastrowid
    return get_post(post_id, viewer_id=user_id)


def update_post(user_id: int, post_id: int, data: dict) -> dict:
    with db_session() as conn:
        row = _visible_or_owner_post(conn, post_id, user_id)
        if row["user_id"] != user_id:
            raise CommunityError("غير مصرح. يمكنك تعديل منشوراتك فقط.", 403)
        title = (data.get("title") or "").strip()
        body = (data.get("body") or "").strip()
        if not title or not body:
            raise CommunityError("العنوان والمحتوى (body) مطلوبان.", 400)
        conn.execute(
            "UPDATE posts SET title = ?, body = ?, updated_at = datetime('now') "
            "WHERE id = ?",
            (_cap(title, POST_TITLE_MAX), _cap(body, POST_BODY_MAX), post_id),
        )
    return get_post(post_id, viewer_id=user_id)


def delete_post(user_id: int, post_id: int) -> dict:
    with db_session() as conn:
        row = _visible_or_owner_post(conn, post_id, user_id)
        if row["user_id"] != user_id:
            raise CommunityError("غير مصرح. يمكنك حذف منشوراتك فقط.", 403)
        conn.execute(
            "UPDATE posts SET status = 'removed', updated_at = datetime('now') "
            "WHERE id = ?",
            (post_id,),
        )
    return {"id": post_id, "status": "removed", "message": "تم حذف المنشور."}


def _comment_row(conn, post_id, comment_id):
    row = conn.execute(
        "SELECT id, post_id, user_id, status FROM comments "
        "WHERE id = ? AND post_id = ?",
        (comment_id, post_id),
    ).fetchone()
    if not row:
        raise CommunityError("التعليق غير موجود.", 404)
    return row


def add_comment(user_id: int, post_id: int, data: dict) -> dict:
    body = (data.get("body") or "").strip()
    if not body:
        raise CommunityError("محتوى التعليق (body) مطلوب.", 400)
    body = _cap(body, COMMENT_BODY_MAX)
    with db_session() as conn:
        _visible_or_owner_post(conn, post_id, user_id)
        cur = conn.execute(
            "INSERT INTO comments (post_id, user_id, body, status, "
            "created_at, updated_at) VALUES (?, ?, ?, 'visible', "
            "datetime('now'), datetime('now'))",
            (post_id, user_id, body),
        )
        comment_id = cur.lastrowid
        # إشعار صاحب المنشور بتعليق جديد (لا إشعار لفعل الذات)
        owner = conn.execute(
            "SELECT p.user_id, p.title FROM posts p WHERE p.id = ?", (post_id,)
        ).fetchone()
        if owner and owner["user_id"] != user_id:
            notify(
                conn, owner["user_id"], "community.comment",
                "تعليق جديد على منشورك",
                body=f"علَّق أحدهم على منشورك: «{owner['title']}»",
                link=f"/posts/{post_id}",
                actor_id=user_id,
            )
    with db_session() as conn:
        row = conn.execute(
            """SELECT c.id, c.post_id, c.user_id, u.full_name AS author_name,
                      """ + _author_verified_flag("u.id") + """ AS author_verified,
                      c.body, c.status, c.created_at, c.updated_at
               FROM comments c JOIN users u ON u.id = c.user_id
               WHERE c.id = ?""",
            (comment_id,),
        ).fetchone()
    return _comment_item(dict(row))


def update_comment(user_id: int, post_id: int, comment_id: int, data: dict) -> dict:
    body = (data.get("body") or "").strip()
    if not body:
        raise CommunityError("محتوى التعليق (body) مطلوب.", 400)
    with db_session() as conn:
        row = _comment_row(conn, post_id, comment_id)
        if row["user_id"] != user_id:
            raise CommunityError("غير مصرح. يمكنك تعديل تعليقاتك فقط.", 403)
        conn.execute(
            "UPDATE comments SET body = ?, updated_at = datetime('now') "
            "WHERE id = ?",
            (_cap(body, COMMENT_BODY_MAX), comment_id),
        )
        updated = conn.execute(
            """SELECT c.id, c.post_id, c.user_id, u.full_name AS author_name,
                      """ + _author_verified_flag("u.id") + """ AS author_verified,
                      c.body, c.status, c.created_at, c.updated_at
               FROM comments c JOIN users u ON u.id = c.user_id
               WHERE c.id = ?""",
            (comment_id,),
        ).fetchone()
    return _comment_item(dict(updated))


def delete_comment(user_id: int, post_id: int, comment_id: int) -> dict:
    with db_session() as conn:
        row = _comment_row(conn, post_id, comment_id)
        if row["user_id"] != user_id:
            raise CommunityError("غير مصرح. يمكنك حذف تعليقاتك فقط.", 403)
        conn.execute(
            "UPDATE comments SET status = 'removed', updated_at = datetime('now') "
            "WHERE id = ?",
            (comment_id,),
        )
    return {"id": comment_id, "status": "removed", "message": "تم حذف التعليق."}


# ---------------------------------------------------------------------------
# التفاعلات
# ---------------------------------------------------------------------------

def toggle_reaction(user_id: int, post_id: int, reaction_type: str = "like") -> dict:
    if reaction_type not in REACTION_TYPES:
        raise CommunityError("نوع التفاعل يجب أن يكون like أو helpful.", 400)
    with db_session() as conn:
        _visible_or_owner_post(conn, post_id, user_id)
        existing = conn.execute(
            "SELECT 1 FROM reactions WHERE user_id = ? AND post_id = ? AND type = ?",
            (user_id, post_id, reaction_type),
        ).fetchone()
        if existing:
            conn.execute(
                "DELETE FROM reactions WHERE user_id = ? AND post_id = ? AND type = ?",
                (user_id, post_id, reaction_type),
            )
            reacted = False
        else:
            conn.execute(
                "INSERT INTO reactions (user_id, post_id, type, created_at) "
                "VALUES (?, ?, ?, datetime('now'))",
                (user_id, post_id, reaction_type),
            )
            reacted = True
            # إشعار صاحب المنشور بتفاعل جديد (لا إشعار لتفاعل الذات)
            owner = conn.execute(
                "SELECT p.user_id FROM posts p WHERE p.id = ?", (post_id,)
            ).fetchone()
            if owner and owner["user_id"] != user_id:
                notify(
                    conn, owner["user_id"], "community.reaction",
                    "تفاعل مع منشورك",
                    body=f"تفاعل أحدهم بعلامة «{reaction_type}» على منشورك.",
                    link=f"/posts/{post_id}",
                    actor_id=user_id,
                )
        counts = conn.execute(
            "SELECT type, COUNT(*) AS c FROM reactions WHERE post_id = ? "
            "GROUP BY type",
            (post_id,),
        ).fetchall()
    return {
        "reacted": reacted,
        "reactions": {r["type"]: r["c"] for r in counts},
    }


# ---------------------------------------------------------------------------
# البلاغات (طابور الإشراف — يقرؤه الأدمن في services_admin)
# ---------------------------------------------------------------------------

def create_report(reporter_id: int, data: dict) -> dict:
    target_type = data.get("target_type")
    if target_type not in REPORT_TARGETS:
        raise CommunityError("target_type يجب أن يكون post أو comment أو "
                             "professional_profile.", 400)
    reason = (data.get("reason") or "").strip()
    if not reason:
        raise CommunityError("سبب البلاغ (reason) مطلوب.", 400)
    target_id = data.get("target_id")
    try:
        target_id = int(target_id)
    except (TypeError, ValueError):
        raise CommunityError("target_id يجب أن يكون رقمًا.", 400)
    with db_session() as conn:
        _report_target_owner(conn, target_type, target_id, reporter_id)
        existing = conn.execute(
            "SELECT id FROM reports WHERE reporter_id = ? AND target_type = ? "
            "AND target_id = ? AND status = 'open'",
            (reporter_id, target_type, target_id),
        ).fetchone()
        if existing:
            return {"id": existing["id"], "already_reported": True,
                    "message": "سبق أن أبلغت عن هذا المحتوى."}
        cur = conn.execute(
            "INSERT INTO reports (reporter_id, target_type, target_id, reason, "
            "status, created_at) VALUES (?, ?, ?, ?, 'open', datetime('now'))",
            (reporter_id, target_type, target_id, reason),
        )
        report_id = cur.lastrowid
    return {"id": report_id, "message": "تم استلام البلاغ."}


def _report_target_owner(conn, target_type, target_id, reporter_id):
    """يتحقق من وجود الهدف ويرد بصاحبه؛ يرفض الإبلاغ عن محتوى الذات."""
    if target_type == "post":
        row = conn.execute(
            "SELECT user_id, status FROM posts WHERE id = ?", (target_id,)
        ).fetchone()
        if not row:
            raise CommunityError("المنشور غير موجود.", 404)
        if row["status"] != "visible":
            raise CommunityError("المحتوى غير قابل للإبلاغ (تمت معالجته).", 400)
    elif target_type == "comment":
        row = conn.execute(
            "SELECT user_id, status FROM comments WHERE id = ?", (target_id,)
        ).fetchone()
        if not row:
            raise CommunityError("التعليق غير موجود.", 404)
        if row["status"] != "visible":
            raise CommunityError("المحتوى غير قابل للإبلاغ (تمت معالجته).", 400)
    else:
        row = conn.execute(
            "SELECT user_id FROM professional_profiles WHERE id = ?",
            (target_id,),
        ).fetchone()
        if not row:
            raise CommunityError("الملف المهني غير موجود.", 404)
    if row["user_id"] == reporter_id:
        raise CommunityError("لا يمكنك الإبلاغ عن محتوى خاص بك.", 403)
    return row["user_id"]
