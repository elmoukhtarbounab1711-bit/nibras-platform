"""
خدمات الإشعارات داخل التطبيق (المرحلة 12).

جدول notifications (D-030): إشعار دوري لكل مستخدم مع نوع ونص ورابط داخلي
ومُحفِّز اختياري، يُنشأ ضمن معاملة الفعل نفسه (transactional) عبر
`notify(conn, ...)` — لا يُرسَل إشعار لفعل الذات (يُحسم في المُحفِّز).
القراءة خاصة بصاحبها: قائمة مع عدد غير المقروء، تعليم المقروء منفردًا
أو كلها. لا توجد نقاط دفع (push/email) — الإشعارات داخل التطبيق فقط.
"""
from .database import db_session

# أنواع الإشعارات المدعومة (تُرجع 400 لأي نوع آخر عند الإدراج المباشر)
NOTIFICATION_TYPES = (
    "verification.approved",
    "verification.rejected",
    "community.comment",
    "community.reaction",
    "moderation.content_hidden",
    "moderation.content_removed",
)

DEFAULT_LIST_LIMIT = 20
MAX_LIST_LIMIT = 100


class NotificationError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def notify(conn, user_id: int, type_: str, title: str, body=None, link=None,
           actor_id=None) -> int:
    """ينشئ إشعارًا داخل معاملة conn المفتوحة (transactional مع الفعل).

    يُستدعى من خدمات المُحفِّزات بعد التأكد من عدم كون الفعل من المستلم.
    """
    if type_ not in NOTIFICATION_TYPES:
        raise NotificationError("نوع إشعار غير معروف.", 400)
    cur = conn.execute(
        "INSERT INTO notifications (user_id, type, title, body, link, "
        "actor_id, is_read, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, 0, datetime('now'))",
        (user_id, type_, title, body, link, actor_id),
    )
    return cur.lastrowid


def _notification_item(row) -> dict:
    return {
        "id": row["id"],
        "type": row["type"],
        "title": row["title"],
        "body": row["body"],
        "link": row["link"],
        "actor_id": row["actor_id"],
        "actor_name": row["actor_name"],
        "is_read": bool(row["is_read"]),
        "created_at": row["created_at"],
    }


def _list_columns():
    return (
        "SELECT n.id, n.type, n.title, n.body, n.link, n.actor_id, n.is_read, "
        "n.created_at, "
        "COALESCE(u.full_name, '') AS actor_name "
        "FROM notifications n LEFT JOIN users u ON u.id = n.actor_id"
    )


def list_notifications(user_id: int, limit: int = DEFAULT_LIST_LIMIT,
                       offset: int = 0, unread_only: bool = False) -> dict:
    limit = max(1, min(int(limit or DEFAULT_LIST_LIMIT), MAX_LIST_LIMIT))
    offset = max(0, int(offset or 0))
    where = "n.user_id = ?"
    params = [user_id]
    if unread_only:
        where += " AND n.is_read = 0"
    with db_session() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) AS c FROM notifications n WHERE {where}", params
        ).fetchone()["c"]
        unread_count = conn.execute(
            "SELECT COUNT(*) AS c FROM notifications "
            "WHERE user_id = ? AND is_read = 0", (user_id,)
        ).fetchone()["c"]
        rows = conn.execute(
            _list_columns() + f" WHERE {where}"
            " ORDER BY n.created_at DESC, n.id DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
    return {
        "notifications": [_notification_item(dict(r)) for r in rows],
        "total": total,
        "unread_count": unread_count,
    }


def unread_count(user_id: int) -> int:
    with db_session() as conn:
        return conn.execute(
            "SELECT COUNT(*) AS c FROM notifications "
            "WHERE user_id = ? AND is_read = 0", (user_id,)
        ).fetchone()["c"]


def _notification_owner(conn, user_id, notification_id):
    row = conn.execute(
        "SELECT id, is_read FROM notifications "
        "WHERE id = ? AND user_id = ?", (notification_id, user_id),
    ).fetchone()
    if row is None:
        raise NotificationError("الإشعار غير موجود.", 404)
    return row


def mark_read(user_id: int, notification_id: int) -> dict:
    with db_session() as conn:
        row = _notification_owner(conn, user_id, notification_id)
        if not row["is_read"]:
            conn.execute(
                "UPDATE notifications SET is_read = 1 WHERE id = ?",
                (notification_id,),
            )
        item = conn.execute(
            _list_columns() + " WHERE n.id = ?", (notification_id,)
        ).fetchone()
    return _notification_item(dict(item))


def mark_all_read(user_id: int) -> int:
    with db_session() as conn:
        cur = conn.execute(
            "UPDATE notifications SET is_read = 1 "
            "WHERE user_id = ? AND is_read = 0", (user_id,)
        )
        return cur.rowcount
