"""
خدمات الإشعارات (المرحلة 12 + المرحلة 16 للتسليم الخارجي).

جدول notifications (D-030): إشعار دوري لكل مستخدم مع نوع ونص ورابط داخلي
ومُحفِّز اختياري، يُنشأ ضمن معاملة الفعل نفسه (transactional) عبر
`notify(conn, ...)` — لا يُرسَل إشعار لفعل الذات (يُحسم في المُحفِّز).
القراءة خاصة بصاحبها: قائمة مع عدد غير المقروء، تعليم المقروء منفردًا
أو كلها.

التسليم الخارجي (D-034 — المرحلة 16): إلى جانب الإشعار داخل التطبيق،
تُصطف صفوف تسليم في notification_outbox (بريد/دفع) ضمن معاملة notify()
وفق تفضيلات المستخدم (notification_preferences — غياب الصف = مُفعَّل).
لا يحدث أي إرسال شبكي داخل الطلب: يُفرَّغ الصندوق عبر `deliver_pending()`
يدويًا (نقطة إدارية) أو مجدولًا (سكربت flush_notifications) — بلا بنية
خلفية مسبقة. المزوّدان الافترضيان noop/console (تسجيل بلا شبكة).
"""
import logging

from . import config
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

# القنوات الخارجية الخاضعة للتفضيلات (in_app أساسية دائمًا وغير قابلة للتعطيل)
NOTIFICATION_CHANNELS = ("email", "push")

# منصات أجهزة الدفع المقبولة عند تسجيل جهاز
DEVICE_PLATFORMS = ("android", "ios", "web")

DEFAULT_LIST_LIMIT = 20
MAX_LIST_LIMIT = 100


class NotificationError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class DeliveryError(Exception):
    """فشل تسليم صف صندوق خارجي (تُلتقط في deliver_pending)."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def notify(conn, user_id: int, type_: str, title: str, body=None, link=None,
           actor_id=None) -> int:
    """ينشئ إشعارًا داخل معاملة conn المفتوحة (transactional مع الفعل).

    يُستدعى من خدمات المُحفِّزات بعد التأكد من عدم كون الفعل من المستلم.
    يصطف التسليم الخارجي (بريد/دفع) تلقائيًا وفق تفضيلات المستخدم — داخل
    المعاملة نفسها لضمان عدم فقدان الإشعار مع الفعل.
    """
    if type_ not in NOTIFICATION_TYPES:
        raise NotificationError("نوع إشعار غير معروف.", 400)
    cur = conn.execute(
        "INSERT INTO notifications (user_id, type, title, body, link, "
        "actor_id, is_read, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, 0, datetime('now'))",
        (user_id, type_, title, body, link, actor_id),
    )
    notification_id = cur.lastrowid
    _queue_external_delivery(conn, notification_id, user_id, type_, title, body)
    return notification_id


def _preference_enabled(conn, user_id: int, channel: str, type_: str) -> bool:
    """هل التسليم مفعّل لهذه القناة والنوع؟ غياب الصف = مُفعَّل افتراضيًا."""
    row = conn.execute(
        "SELECT enabled FROM notification_preferences "
        "WHERE user_id = ? AND channel = ? AND notification_type = ?",
        (user_id, channel, type_),
    ).fetchone()
    return True if row is None else bool(row["enabled"])


def _queue_external_delivery(conn, notification_id: int, user_id: int,
                             type_: str, title: str, body) -> None:
    """يصطف صفوف تسليم خارجية (بريد + دفع لكل جهاز) ضمن معاملة conn."""
    user = conn.execute(
        "SELECT email FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    if user is None:
        return
    if _preference_enabled(conn, user_id, "email", type_):
        conn.execute(
            "INSERT INTO notification_outbox (notification_id, channel, recipient) "
            "VALUES (?, 'email', ?)",
            (notification_id, user["email"]),
        )
    if _preference_enabled(conn, user_id, "push", type_):
        devices = conn.execute(
            "SELECT token FROM notification_devices WHERE user_id = ?", (user_id,)
        ).fetchall()
        for device in devices:
            conn.execute(
                "INSERT INTO notification_outbox (notification_id, channel, recipient) "
                "VALUES (?, 'push', ?)",
                (notification_id, device["token"]),
            )


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


# ---------------------------------------------------------------------------
# تفضيلات التسليم الخارجي (المرحلة 16 — قرار D-034)
# ---------------------------------------------------------------------------

def get_preferences(user_id: int) -> dict:
    """الشبكة الفعالة للتفضيلات: كل (قناة، نوع) بقيمتها (الغياب = مفعّل)."""
    effective = {
        channel: {type_: True for type_ in NOTIFICATION_TYPES}
        for channel in NOTIFICATION_CHANNELS
    }
    with db_session() as conn:
        rows = conn.execute(
            "SELECT channel, notification_type, enabled "
            "FROM notification_preferences WHERE user_id = ?",
            (user_id,),
        ).fetchall()
    for row in rows:
        channel = row["channel"]
        if channel in effective and row["notification_type"] in effective[channel]:
            effective[channel][row["notification_type"]] = bool(row["enabled"])
    return {"preferences": effective}


def set_preferences(user_id: int, preferences) -> dict:
    """يطبق قائمة تفضيلات {channel, notification_type, enabled} (تحقق صارم)."""
    if not isinstance(preferences, list) or not preferences:
        raise NotificationError("قائمة التفضيلات مطلوبة.", 400)
    parsed = []
    for item in preferences:
        if not isinstance(item, dict):
            raise NotificationError("كل تفضيل يجب أن يكون كائنًا.", 400)
        channel = (item.get("channel") or "").strip().lower()
        type_ = (item.get("notification_type") or "").strip()
        enabled = item.get("enabled")
        if channel not in NOTIFICATION_CHANNELS:
            raise NotificationError("قناة غير معروفة (email|push).", 400)
        if type_ not in NOTIFICATION_TYPES:
            raise NotificationError("نوع إشعار غير معروف.", 400)
        if not isinstance(enabled, bool):
            raise NotificationError("enabled يجب أن تكون true/false.", 400)
        parsed.append((channel, type_, int(enabled)))
    with db_session() as conn:
        for channel, type_, enabled in parsed:
            existing = conn.execute(
                "SELECT 1 FROM notification_preferences "
                "WHERE user_id = ? AND channel = ? AND notification_type = ?",
                (user_id, channel, type_),
            ).fetchone()
            if existing is not None:
                conn.execute(
                    "UPDATE notification_preferences SET enabled = ?, "
                    "updated_at = datetime('now') "
                    "WHERE user_id = ? AND channel = ? AND notification_type = ?",
                    (enabled, user_id, channel, type_),
                )
            else:
                conn.execute(
                    "INSERT INTO notification_preferences "
                    "(user_id, channel, notification_type, enabled) "
                    "VALUES (?,?,?,?)",
                    (user_id, channel, type_, enabled),
                )
    return get_preferences(user_id)


# ---------------------------------------------------------------------------
# أجهزة الدفع (المرحلة 16 — قرار D-034)
# ---------------------------------------------------------------------------

def register_device(user_id: int, platform: str, token: str) -> dict:
    """يسجّل جهازًا للدفع (إعادة التسجيل بنفس التوكن تُحدِّث المالك والأثر)."""
    platform = (platform or "").strip().lower()
    token = (token or "").strip()
    if platform not in DEVICE_PLATFORMS:
        raise NotificationError(
            "منصة الجهاز غير معروفة (android|ios|web).", 400
        )
    if not token or len(token) > 512:
        raise NotificationError("توكن الجهاز مطلوب (حتى 512 حرفًا).", 400)
    with db_session() as conn:
        existing = conn.execute(
            "SELECT id FROM notification_devices WHERE token = ?", (token,)
        ).fetchone()
        if existing is not None:
            conn.execute(
                "UPDATE notification_devices SET user_id = ?, platform = ?, "
                "last_seen_at = datetime('now') WHERE id = ?",
                (user_id, platform, existing["id"]),
            )
            device_id = existing["id"]
        else:
            device_id = conn.execute(
                "INSERT INTO notification_devices (user_id, platform, token) "
                "VALUES (?,?,?)",
                (user_id, platform, token),
            ).lastrowid
    return {"id": device_id, "platform": platform}


def list_devices(user_id: int) -> list:
    with db_session() as conn:
        rows = conn.execute(
            "SELECT id, platform, token, created_at, last_seen_at "
            "FROM notification_devices WHERE user_id = ? ORDER BY id ASC",
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def delete_device(user_id: int, device_id: int) -> None:
    with db_session() as conn:
        cur = conn.execute(
            "DELETE FROM notification_devices WHERE id = ? AND user_id = ?",
            (device_id, user_id),
        )
        if cur.rowcount == 0:
            raise NotificationError("الجهاز غير موجود.", 404)


# ---------------------------------------------------------------------------
# تسليم الصندوق الخارجي (المرحلة 16 — قرار D-034)
# ---------------------------------------------------------------------------

def _send_email(to_email: str, subject: str, body: str) -> None:
    """يرسل بريدًا عبر مزوّد EMAIL_PROVIDER؛ يرفع DeliveryError عند الفشل."""
    logger = logging.getLogger("nibras.mailer")
    if config.EMAIL_PROVIDER == "noop":
        logger.info(
            "notification_email_noop",
            extra={"to_email": to_email, "subject": subject},
        )
        return
    if config.EMAIL_PROVIDER == "console":
        logger.info(
            "notification_email",
            extra={"to_email": to_email, "subject": subject},
        )
        return
    raise DeliveryError(f"مزوّد بريد غير معروف: {config.EMAIL_PROVIDER}")


def _send_push(token: str, title: str, body: str) -> None:
    """يرسل دفعًا عبر مزوّد PUSH_PROVIDER؛ يرفع DeliveryError عند الفشل.

    لا يُسجَّل التوكن في السجلات (حساس — لا يمر عبر extra أصلًا).
    """
    logger = logging.getLogger("nibras.push")
    if config.PUSH_PROVIDER == "noop":
        logger.info(
            "notification_push_noop",
            extra={"title": title},
        )
        return
    if config.PUSH_PROVIDER == "console":
        logger.info(
            "notification_push",
            extra={"title": title},
        )
        return
    raise DeliveryError(f"مزوّد دفع غير معروف: {config.PUSH_PROVIDER}")


def _deliver_one(row) -> None:
    if row["channel"] == "email":
        _send_email(row["recipient"], row["title"], row["body"] or "")
        return
    if row["channel"] == "push":
        _send_push(row["recipient"], row["title"], row["body"] or "")
        return
    raise DeliveryError("قناة تسليم غير معروفة.")


def deliver_pending(limit: int | None = None) -> dict:
    """يفرّغ صفوف الصندوق المعلقة عبر المزوّدين (يدويًا أو مجدولًا).

    النجاح: sent؛ الفشل: يزيد attempts ويبقى pending حتى الوصول إلى الحد
    الأقصى فيصبح failed مع last_error. لا شبكة داخل طلبات API أبدًا.
    """
    limit = max(1, int(limit or config.NOTIFICATION_OUTBOX_LIMIT))
    processed = sent = failed = 0
    with db_session() as conn:
        rows = conn.execute(
            """SELECT o.id, o.channel, o.recipient, o.attempts, n.title, n.body
               FROM notification_outbox o
               JOIN notifications n ON n.id = o.notification_id
               WHERE o.status = 'pending'
               ORDER BY o.id ASC LIMIT ?""",
            (limit,),
        ).fetchall()
        for row in rows:
            processed += 1
            try:
                _deliver_one(row)
            except DeliveryError as exc:
                failed += 1
                attempts = row["attempts"] + 1
                status = (
                    "failed"
                    if attempts >= config.NOTIFICATION_OUTBOX_MAX_ATTEMPTS
                    else "pending"
                )
                conn.execute(
                    "UPDATE notification_outbox SET attempts = ?, status = ?, "
                    "last_error = ? WHERE id = ?",
                    (attempts, status, exc.message, row["id"]),
                )
            else:
                sent += 1
                conn.execute(
                    "UPDATE notification_outbox SET status = 'sent', "
                    "attempts = attempts + 1, sent_at = datetime('now'), "
                    "last_error = NULL WHERE id = ?",
                    (row["id"],),
                )
    return {"processed": processed, "sent": sent, "failed": failed}


def delivery_stats() -> dict:
    """إحصاء صفوف صندوق التسليم حسب الحالة (لمرصد الإدارة)."""
    with db_session() as conn:
        rows = conn.execute(
            "SELECT status, COUNT(*) AS c FROM notification_outbox "
            "GROUP BY status"
        ).fetchall()
    counts = {row["status"]: row["c"] for row in rows}
    return {
        "pending": counts.get("pending", 0),
        "sent": counts.get("sent", 0),
        "failed": counts.get("failed", 0),
    }
