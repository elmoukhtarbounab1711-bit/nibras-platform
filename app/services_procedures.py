"""
خدمات مساعد المساطر (المرحلة 3) — قرار D-021.

وحدة محتوى منظم على شكل وحدة المكتبة (FR-6.1: خطوات مرتبة، وثائق مطلوبة،
جهة مسؤولة، مدة نموذجية) + طبقة اختيارية لتتبع تقدم المستخدم المسجَّل
(FR-6.2). الجداول مطابقة لقاعدة البيانات 06 §6 حرفيًا (بلا is_sample_data).
"""
from .database import db_session

# مساطر نموذجية تُبذَر كبيانات إرشادية (idempotent) — محتوى إداري لاحقًا
# عبر FR-12.1 (مؤجل مثل D-017). نصوص وثائق رسمية عامة مبسطة.
_SEED_PROCEDURES = [
    {
        "slug": "succession-liquidation",
        "title": "تصفية التركة وتقسيم الميراث",
        "category": "الميراث",
        "responsible_authority": "عدول المحكمة الابتدائية — قسم قضاء الأسرة",
        "typical_timeframe": "من أسابيع إلى أشهر حسب تعقيد التركة",
        "steps": [
            {
                "number": 1,
                "title": "الحصول على شهادة الوفاة",
                "description": "استخراج شهادة الوفاة الرسمية من مكتب الحالة المدنية التابع لمكان الوفاة.",
                "documents": "بطاقة التعريف الوطنية للمتوفى\nشهادة الوفاة الطبية",
            },
            {
                "number": 2,
                "title": "تحديد الورثة الشرعيين",
                "description": "جرد الورثة (الزوج/الزوجة، الأبناء، الأبوين، الإخوة...) ووضعياتهم.",
                "documents": "دفاتر الحالة العائلية\nعقود الزواج\nعقود الوفاة",
            },
            {
                "number": 3,
                "title": "تحرير شهادة الإرث (الشهادة العدلية)",
                "description": "لجوء الورثة إلى عدلين لتحرير الشهادة العدلية المحددة للأنصبة طبقًا للفرائض.",
                "documents": "شهادة الوفاة\nبطائق تعريف الورثة\nشهادة عدلية سابقة إن وجدت",
            },
            {
                "number": 4,
                "title": "إثبات التصرف في الأموال العقارية",
                "description": "إن شملت التركة عقارًا، تُحرَّر وثيقة محررة من قبل العدول وتُؤشَّر لدى المحكمة.",
                "documents": "الشهادة العدلية\nرسوم الملكية\nعقود الحيازة",
            },
            {
                "number": 5,
                "title": "توزيع التركة أو الحسم أمام القضاء",
                "description": "إن تعذر الاتفاق تُرفع دعوى قسمة أمام قاضي الأسرة للقسمة المالية أو العينية.",
                "documents": "الشهادة العدلية\nطلبات الورثة\nمقرر القسمة",
            },
        ],
    },
    {
        "slug": "amicable-divorce",
        "title": "الطلاق الاتفاقي",
        "category": "الأسرة",
        "responsible_authority": "قاضي الأسرة بالمحكمة الابتدائية",
        "typical_timeframe": "حوالي شهر إلى شهرين",
        "steps": [
            {
                "number": 1,
                "title": "الاتفاق بين الزوجين على الطلاق",
                "description": "اتفاق الطرفين على الطلاق وتحديد الالتزامات المالية والحضانة والزيارة.",
                "documents": "عقد الزواج\nبطائق التعريف\nوثائق الأبناء",
            },
            {
                "number": 2,
                "title": "التوجه للمحكمة الابتدائية",
                "description": "إيداع طلب التوثيق لدى قاضي الأسرة بالمحكمة الابتدائية المختصة.",
                "documents": "طلب التوثيق\nعقد الزواج\nشهادة تعذر الصلح",
            },
            {
                "number": 3,
                "title": "جلسة الصلح أمام القاضي",
                "description": "محاولة الصلح بين الزوجين قبل توثيق الطلاق، ومحضر الجلسة يسجل الاتفاق.",
                "documents": "محضر الجلسة\nالاستمارة المعدة لذلك",
            },
            {
                "number": 4,
                "title": "توثيق الطلاق من قبل عدلين",
                "description": "توثيق الطلاق الاتفاقي بمقتضى محضر يحرره عدلان يوقعه الطرفان.",
                "documents": "المحضر العدلي\nعقد الزواج",
            },
            {
                "number": 5,
                "title": "تسجيل الطلاق بالحالة المدنية",
                "description": "الإدلاء بمحضر التوثيق لمكتب الحالة المدنية لتسجيل الطلاق.",
                "documents": "محضر التوثيق\nدفتر الحالة العائلية",
            },
        ],
    },
    {
        "slug": "alimony-claim",
        "title": "طلب النفقة",
        "category": "الأسرة",
        "responsible_authority": "قاضي الأسرة بالمحكمة الابتدائية",
        "typical_timeframe": "جلسة إلى عدة جلسات",
        "steps": [
            {
                "number": 1,
                "title": "جمع الوثائق الأساسية",
                "description": "تجميع وثائق إثبات العلاقة الزوجية/القرابة ووضعية المستفيد.",
                "documents": "عقد الزواج\nدفاتر الحالة العائلية\nوثائق قياس الحاجة",
            },
            {
                "number": 2,
                "title": "إيداع مقال الطلب",
                "description": "تقديم مقال إلى قسم قضاء الأسرة يبين طلب النفقة ومقدارها.",
                "documents": "مقال الطلب\nعقد الزواج\nشهادة عدم تحقق الصلح",
            },
            {
                "number": 3,
                "title": "جلسة الصلح",
                "description": "محاولة الصلح وتحديد نفقة مؤقتة عند الحاجة.",
                "documents": "محضر الجلسة",
            },
            {
                "number": 4,
                "title": "صدور الحكم بالنفقة",
                "description": "حكم قضائي يحدد النفقة ومقدارها الدوري وتواريخ الأداء.",
                "documents": "نسخة من الحكم",
            },
        ],
    },
]


class ProcedureError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def ensure_defaults():
    """بذر المساطر النموذجية (idempotent) — تُستدعى من init_db."""
    with db_session() as conn:
        for proc in _SEED_PROCEDURES:
            existing = conn.execute(
                "SELECT id FROM procedures WHERE slug = ?", (proc["slug"],)
            ).fetchone()
            if existing:
                continue
            cur = conn.execute(
                "INSERT INTO procedures "
                "(slug, title, category, responsible_authority, typical_timeframe) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    proc["slug"],
                    proc["title"],
                    proc["category"],
                    proc["responsible_authority"],
                    proc["typical_timeframe"],
                ),
            )
            procedure_id = cur.lastrowid
            for step in proc["steps"]:
                conn.execute(
                    "INSERT INTO procedure_steps "
                    "(procedure_id, step_number, title, description, required_documents) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        procedure_id,
                        step["number"],
                        step["title"],
                        step["description"],
                        step["documents"],
                    ),
                )


def list_procedures(category: str | None = None):
    query = """
        SELECT p.id, p.slug, p.title, p.category, p.responsible_authority,
               p.typical_timeframe,
               (SELECT COUNT(*) FROM procedure_steps s WHERE s.procedure_id = p.id) AS step_count
        FROM procedures p
    """
    params = []
    if category:
        query += " WHERE p.category = ?"
        params.append(category)
    query += " ORDER BY p.title"
    with db_session() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def get_procedure(slug: str):
    with db_session() as conn:
        row = conn.execute(
            "SELECT id, slug, title, category, responsible_authority, typical_timeframe "
            "FROM procedures WHERE slug = ?",
            (slug,),
        ).fetchone()
        if not row:
            return None
        proc = dict(row)
        steps = conn.execute(
            "SELECT id, step_number, title, description, required_documents "
            "FROM procedure_steps WHERE procedure_id = ? ORDER BY step_number",
            (proc["id"],),
        ).fetchall()
        proc["steps"] = [dict(s) for s in steps]
        return proc


def set_step_progress(user_id: int, slug: str, step_number: int, completed: bool):
    """يحدّث تقدم المستخدم في خطوة معينة (FR-6.2) ويعيد ملخص التقدم."""
    with db_session() as conn:
        proc = conn.execute(
            "SELECT id FROM procedures WHERE slug = ?", (slug,)
        ).fetchone()
        if not proc:
            raise ProcedureError("المسطرة غير موجودة", 404)
        step = conn.execute(
            "SELECT id FROM procedure_steps WHERE procedure_id = ? AND step_number = ?",
            (proc["id"], step_number),
        ).fetchone()
        if not step:
            raise ProcedureError("الخطوة غير موجودة في هذه المسطرة", 404)
        if completed:
            conn.execute(
                "INSERT INTO procedure_progress (user_id, procedure_id, step_id, completed_at) "
                "VALUES (?, ?, ?, datetime('now')) "
                "ON CONFLICT(user_id, procedure_id, step_id) "
                "DO UPDATE SET completed_at = datetime('now')",
                (user_id, proc["id"], step["id"]),
            )
        else:
            conn.execute(
                "DELETE FROM procedure_progress WHERE user_id = ? AND procedure_id = ? "
                "AND step_id = ?",
                (user_id, proc["id"], step["id"]),
            )
        total = conn.execute(
            "SELECT COUNT(*) AS n FROM procedure_steps WHERE procedure_id = ?",
            (proc["id"],),
        ).fetchone()["n"]
        done = conn.execute(
            "SELECT COUNT(*) AS n FROM procedure_progress "
            "WHERE user_id = ? AND procedure_id = ?",
            (user_id, proc["id"]),
        ).fetchone()["n"]
        return {"completed": done, "total": total}


def get_user_progress(user_id: int, slug: str):
    """أرقام الخطوات المكتملة للمستخدم في مسطرة معينة."""
    with db_session() as conn:
        proc = conn.execute(
            "SELECT id FROM procedures WHERE slug = ?", (slug,)
        ).fetchone()
        if not proc:
            raise ProcedureError("المسطرة غير موجودة", 404)
        rows = conn.execute(
            """SELECT s.step_number, pp.completed_at
               FROM procedure_progress pp
               JOIN procedure_steps s ON s.id = pp.step_id
               WHERE pp.user_id = ? AND pp.procedure_id = ?""",
            (user_id, proc["id"]),
        ).fetchall()
        return [
            {"step_number": r["step_number"], "completed_at": r["completed_at"]}
            for r in rows
        ]
