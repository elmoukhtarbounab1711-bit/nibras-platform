"""
خدمات الحاسبات القانونية (المرحلة 3) — قرار D-021.

كل حاسبة زوج مستقل (schema مدخلات + دالة حساب) وفق المواصفة الوظيفية §4،
لا امتداد لتجريد عام قبل أوانه. أولى الحاسبات: حاسبة الإرث وفق المواد
334-356 من مدونة الأسرة. نطاقها: الزوج/الزوجة، الأبناء والبنات، الأب
والأم، الإخوة والأخوات الأشقاء ومن الأم. أي ورثة خارج النطاق (جد، جدة،
أعمام، أحفاد، وصية واجبة) تُرفض بتحقق الـ schema برسالة واضحة بدل حساب
خاطئ. الحساب بـ Fraction (دقة تامة) ثم تُعمَّم المبالغ.
"""
import json
from fractions import Fraction

from .database import db_session

# أرقام مواد مدونة الأسرة المعتمدة للفروض (تحقق خارجي — قرار D-021):
# 342 النصف، 343 الربع، 344 الثمن، 345 الثلثان، 346 الثلث، 347 السدس،
# 339/340 الأب والبنت، 348/349 العصبة والترتيب والرد، 350 الأب مع البنت،
# 351 العصبة بالغير (2:1)، 352 العصبة مع الغير (الأخوات مع البنات)،
# 355/356 الحجب.

_INT_FIELDS = (
    "sons",
    "daughters",
    "full_brothers",
    "full_sisters",
    "maternal_brothers",
    "maternal_sisters",
)
_BOOL_FIELDS = ("father", "mother")
_ALLOWED_FIELDS = {"estate_value", "spouse", *_INT_FIELDS, *_BOOL_FIELDS}
_SPOUSE_VALUES = {"none", "husband", "wife"}

_DISCLAIMER = (
    "نتيجة تقديرية تعليمية وفق المواد 334-356 من مدونة الأسرة، لا تغني عن "
    "تحقق قضائي؛ الحالات المعقدة (الجد، الأعمام، الأحفاد، الوصية الواجبة، "
    "تخارج/مخالصة) خارج نطاق الحاسبة."
)


class CalculatorError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def list_calculators():
    with db_session() as conn:
        rows = conn.execute(
            "SELECT id, slug, name, legal_basis FROM calculators ORDER BY id"
        ).fetchall()
        return [dict(r) for r in rows]


def get_calculator_by_slug(slug: str):
    with db_session() as conn:
        row = conn.execute(
            "SELECT id, slug, name, legal_basis FROM calculators WHERE slug = ?",
            (slug,),
        ).fetchone()
        return dict(row) if row else None


def ensure_defaults():
    """بيانات إسناد (idempotent) — تُستدعى من init_db بنمط ensure_roles."""
    with db_session() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO calculators (slug, name, legal_basis) VALUES (?, ?, ?)",
            ("inheritance", "حاسبة الإرث", "المواد 334-356 من مدونة الأسرة"),
        )


def run_calculator(slug: str, data, user_id=None):
    """يوزّع على دالة الحساب ويُسجّل التنفيذ في calculator_runs."""
    calc = get_calculator_by_slug(slug)
    if not calc:
        raise CalculatorError("الحاسبة غير موجودة", 404)
    if slug == "inheritance":
        result = _compute_inheritance(data)
    else:
        raise CalculatorError("دالة الحساب غير معرّفة لهذه الحاسبة", 500)
    with db_session() as conn:
        conn.execute(
            "INSERT INTO calculator_runs (calculator_id, user_id, input_json, result_json) "
            "VALUES (?, ?, ?, ?)",
            (
                calc["id"],
                user_id,
                json.dumps(data, ensure_ascii=False),
                json.dumps(result["result"], ensure_ascii=False),
            ),
        )
    return {"result": result["result"], "legal_basis": result["legal_basis"]}


# ---------------------------------------------------------------------------
# حاسبة الإرث — محرك الفرائض (نطاق D-021)
# ---------------------------------------------------------------------------

def _validate_inheritance_input(data):
    if not isinstance(data, dict):
        raise CalculatorError("يجب إرسال جسم JSON")
    unknown = set(data) - _ALLOWED_FIELDS
    if unknown:
        raise CalculatorError(
            f"حقول غير مدعومة (خارج نطاق الحاسبة): {', '.join(sorted(unknown))}"
        )
    estate = data.get("estate_value")
    if not isinstance(estate, (int, float)) or isinstance(estate, bool) or estate <= 0:
        raise CalculatorError("قيمة التركة (estate_value) يجب أن تكون رقمًا موجبًا")
    spouse = data.get("spouse", "none")
    if spouse not in _SPOUSE_VALUES:
        raise CalculatorError("spouse يجب أن يكون none أو husband أو wife")
    for field in _INT_FIELDS:
        value = data.get(field, 0)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise CalculatorError(f"{field} يجب أن يكون عددًا صحيحًا غير سالب")
    for field in _BOOL_FIELDS:
        value = data.get(field, False)
        if not isinstance(value, bool):
            raise CalculatorError(f"{field} يجب أن يكون قيمة منطقية")
    return {
        "estate_value": estate,
        "spouse": spouse,
        "sons": data.get("sons", 0),
        "daughters": data.get("daughters", 0),
        "father": data.get("father", False),
        "mother": data.get("mother", False),
        "full_brothers": data.get("full_brothers", 0),
        "full_sisters": data.get("full_sisters", 0),
        "maternal_brothers": data.get("maternal_brothers", 0),
        "maternal_sisters": data.get("maternal_sisters", 0),
    }


def _fmt(share: Fraction) -> str:
    if share.denominator == 1:
        return "1"
    return f"{share.numerator}/{share.denominator}"


def _compute_inheritance(data):
    v = _validate_inheritance_input(data)
    estate = v["estate_value"]

    has_descendant = v["sons"] > 0 or v["daughters"] > 0
    sibling_count = (
        v["full_brothers"] + v["full_sisters"]
        + v["maternal_brothers"] + v["maternal_sisters"]
    )

    notes = [_DISCLAIMER]
    fards = []      # (index, share) في entries
    entries = []    # {label, count, share, articles}

    def add(label, count, share, articles):
        entries.append(
            {"label": label, "count": count, "share": share, "articles": articles}
        )
        return len(entries) - 1

    # --- الزوج/الزوجة (342/343/344)
    if v["spouse"] == "wife":
        if has_descendant:
            share, arts = Fraction(1, 8), ["344"]
        else:
            share, arts = Fraction(1, 4), ["343"]
        fards.append((add("الزوجة", 1, share, arts), share))
    elif v["spouse"] == "husband":
        if has_descendant:
            share, arts = Fraction(1, 4), ["343"]
        else:
            share, arts = Fraction(1, 2), ["342"]
        fards.append((add("الزوج", 1, share, arts), share))

    # --- الأم (346/347)
    if v["mother"]:
        if has_descendant or sibling_count >= 2:
            share, arts = Fraction(1, 6), ["347"]
        else:
            share, arts = Fraction(1, 3), ["346"]
        fards.append((add("الأم", 1, share, arts), share))

    # --- الأب: فرض السدس مع الفرع الوارث + تعصيب الباقي (347/350)،
    #     أو عاصب فقط بلا فرع وارث (339/350)
    father_index = None
    father_taasib = False
    if v["father"]:
        father_taasib = True
        if has_descendant:
            father_index = add("الأب", 1, Fraction(1, 6), ["347", "350"])
            fards.append((father_index, Fraction(1, 6)))
        else:
            father_index = add("الأب", 1, Fraction(0, 1), ["339", "350"])

    # --- البنات بلا ابن: فرض النصف/الثلثان (342/345)
    daughters_fard = None
    if v["daughters"] > 0 and v["sons"] == 0:
        if v["daughters"] == 1:
            share, arts = Fraction(1, 2), ["342"]
        else:
            share, arts = Fraction(2, 3), ["345"]
        daughters_fard = add("البنت", v["daughters"], share, arts)
        fards.append((daughters_fard, share))

    # --- الإخوة من الأم: فرض السدس/الثلث (346) — محجوبون بفرع وارث أو بالأب
    maternal_present = (v["maternal_brothers"] + v["maternal_sisters"]) > 0
    if maternal_present and not (has_descendant or v["father"]):
        count = v["maternal_brothers"] + v["maternal_sisters"]
        share = Fraction(1, 6) if count == 1 else Fraction(1, 3)
        fards.append((add("الأخ/الأخت من الأم", count, share, ["346"]), share))
    elif maternal_present:
        notes.append("الإخوة من الأم محجوبون بفرع وارث أو بالأب (المواد 346، 355/356)")

    # --- الإخوة الأشقاء: محجوبون بابن أو بالأب (349/355)؛ مع وجودهم:
    #     أشقاء → عصبة بالغير 2:1 (351)؛ شقيقات فقط مع بنات → عصبة مع الغير
    #     بالسوية (352)؛ شقيقات فقط بلا بنات → فرض النصف/الثلثان (342/345)
    full_brothers_taasib = None
    sisters_taasib_idx = None
    full_sisters_fard = None
    siblings_present = (v["full_brothers"] + v["full_sisters"]) > 0
    if siblings_present:
        if v["sons"] > 0 or v["father"]:
            notes.append("الإخوة والأخوات الأشقاء محجوبون بابن أو بالأب (المواد 349، 355/356)")
        elif v["full_brothers"] > 0:
            bro_idx = add("الأخ الشقيق", v["full_brothers"], Fraction(0, 1), ["351"])
            sis_idx = None
            if v["full_sisters"] > 0:
                sis_idx = add("الأخت الشقيقة", v["full_sisters"], Fraction(0, 1), ["351"])
            full_brothers_taasib = (bro_idx, sis_idx)
        elif v["daughters"] > 0:
            sisters_taasib_idx = add(
                "الأخت الشقيقة", v["full_sisters"], Fraction(0, 1), ["352"]
            )
        else:
            share = Fraction(1, 2) if v["full_sisters"] == 1 else Fraction(2, 3)
            arts = ["342"] if v["full_sisters"] == 1 else ["345"]
            full_sisters_fard = add("الأخت الشقيقة", v["full_sisters"], share, arts)
            fards.append((full_sisters_fard, share))

    # --- لا ورثة في النطاق → بيت المال (349/6).
    # الأبناء يُضافون لاحقًا في مرحلة التوزيع (تعصيب بالبنوة)، لذا مع وجود
    # أبناء تُتجاوز العودة المبكرة حتى لو لم تُسجَّل فروض بعد.
    if not entries and v["sons"] == 0:
        return {
            "result": {
                "heirs": [],
                "method": "لا وارث في النطاق المدخل — التركة لبيت المال (المادة 349/6)",
                "total_estate": estate,
                "notes": notes,
            },
            "legal_basis": ["المادة 349/6 من مدونة الأسرة"],
        }

    # --- التوزيع: فرض / عول / تعصيب / رد
    fard_total = sum(share for _, share in fards)
    method = ""

    if fard_total > 1:
        # العول: تُقاس السهام على المجموع (قاعدة فرائضية مطبقة — المواد 341)
        for idx, _ in fards:
            entries[idx]["share"] = entries[idx]["share"] / fard_total
        method = (
            f"عول — مجموع الفروض ({_fmt(fard_total)}) تجاوز التركة، "
            f"فعُولت المسألة إلى {fard_total.numerator} (المواد 341، 342-347)"
        )
        notes.append("العول قاعدة فرائضية مطبقة (لا مادة مستقلة مرقمة) — لا عاصب هنا.")
    elif fard_total < 1:
        remainder = Fraction(1) - fard_total
        if v["sons"] > 0:
            # الأبناء (والبنات معهم 2:1) عصبة بالبنوة — يأخذون الباقي كاملًا
            units = v["sons"] * 2 + v["daughters"]
            per_unit = remainder / units
            add("الابن", v["sons"], per_unit * 2 * v["sons"], ["349", "351"])
            if v["daughters"] > 0:
                add("البنت", v["daughters"], per_unit * v["daughters"], ["349", "351"])
            method = "تعصيب — الأبناء (للذكر مثل حظ الأنثيين) أخذوا الباقي (المواد 349/351)"
        elif father_taasib:
            # الأب عاصب بالنفس يأخذ الباقي (350: مع الفرع أنثى بعد فرض السدس)
            entries[father_index]["share"] += remainder
            method = "تعصيب — الأب أخذ الباقي بعد أصحاب الفروض (المواد 349/350)"
        elif full_brothers_taasib is not None:
            bro_idx, sis_idx = full_brothers_taasib
            units = v["full_brothers"] * 2 + v["full_sisters"]
            per_unit = remainder / units
            entries[bro_idx]["share"] = per_unit * 2 * v["full_brothers"]
            if sis_idx is not None:
                entries[sis_idx]["share"] = per_unit * v["full_sisters"]
            method = "تعصيب — الإخوة (للذكر مثل حظ الأنثيين) أخذوا الباقي (المادة 351)"
        elif sisters_taasib_idx is not None:
            # عصبة مع الغير: الأخوات مع البنات يتقاسمن الباقي بالسوية
            entries[sisters_taasib_idx]["share"] = remainder
            method = "تعصيب مع الغير — الأخوات أخذن الباقي مع البنات بالتساوي (المادة 352)"
        else:
            # رد: لا عصبة — يُردّ الباقي على أصحاب الفروض بنسبة فروضهم (349/6)
            for idx, share in fards:
                entries[idx]["share"] += remainder * (share / fard_total)
            method = (
                "رد — لا عصبة، فَرُدّ الباقي على أصحاب الفروض بنسبة فروضهم "
                "(المادة 349/6)"
            )
    else:
        method = "الفروض استغرقت التركة بالكامل"

    # --- المبالغ (Fraction دقيق ثم تقريب)
    heirs_result = []
    for e in entries:
        amount = round(float(estate) * float(e["share"]), 2)
        per_capita = round(amount / e["count"], 2) if e["count"] > 1 else amount
        heirs_result.append(
            {
                "heir": e["label"],
                "count": e["count"],
                "share": _fmt(e["share"]),
                "amount": amount,
                "amount_per_capita": per_capita,
                "articles": e["articles"],
            }
        )

    all_articles = []
    for e in entries:
        for a in e["articles"]:
            if a not in all_articles:
                all_articles.append(a)
    legal_basis = [f"المادة {a} من مدونة الأسرة" for a in all_articles]

    return {
        "result": {
            "heirs": heirs_result,
            "method": method,
            "total_estate": estate,
            "notes": notes,
        },
        "legal_basis": legal_basis,
    }
