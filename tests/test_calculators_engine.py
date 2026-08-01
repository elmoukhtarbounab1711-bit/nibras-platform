"""
اختبارات محرك الفرائض لحاسبة الإرث (المرحلة 3) — قرار D-021.

حالات رقمية معروفة محسوبة يدويًا من مواد مدونة الأسرة (342-352):
الفرض والعول والرد والتعصيب بالبنوة وبالغير ومع الغير. كل حالة تنتهي
بتوزيع يساوي التركة (بهامش تقريب السنتيم).
"""
from fractions import Fraction

import pytest

from app.services_calculators import (
    CalculatorError,
    _compute_inheritance,
)


def _share_of(result, label):
    for h in result["result"]["heirs"]:
        if h["heir"] == label:
            return Fraction(h["share"])
    return None


def _assert_case(data, expected):
    """expected: {label: Fraction}. يتحقق من النصيب ومطابقة المجموع للتركة."""
    result = _compute_inheritance(data)
    heirs = {h["heir"]: h for h in result["result"]["heirs"]}
    assert set(heirs) == set(expected), f"الورثة غير مطابقين: {set(heirs)}"
    for label, share in expected.items():
        assert _share_of(result, label) == share, f"نصيب {label} غير صحيح"
    total = round(sum(h["amount"] for h in heirs.values()), 2)
    assert abs(total - data["estate_value"]) <= 0.02, f"المجموع لا يطابق التركة: {total}"
    for h in heirs.values():
        if h["count"] > 1:
            # تقريب السنتيم المستقل يجعل per_capita × count يختلف عنها بمقدار
            # سنت واحد أحيانًا — نسمح بهامش السنت.
            assert abs(h["amount_per_capita"] * h["count"] - h["amount"]) <= 0.02


@pytest.mark.parametrize(
    "label,data,expected",
    [
        (
            "زوجة + ابن",
            {"estate_value": 1000, "spouse": "wife", "sons": 1},
            {"الزوجة": Fraction(1, 8), "الابن": Fraction(7, 8)},
        ),
        (
            "زوجة + بنتان (رد)",
            {"estate_value": 1000, "spouse": "wife", "daughters": 2},
            {"الزوجة": Fraction(3, 19), "البنت": Fraction(16, 19)},
        ),
        (
            "زوج + أخت شقيقة",
            {"estate_value": 1000, "spouse": "husband", "full_sisters": 1},
            {"الزوج": Fraction(1, 2), "الأخت الشقيقة": Fraction(1, 2)},
        ),
        (
            "زوج + أختان (عول)",
            {"estate_value": 1000, "spouse": "husband", "full_sisters": 2},
            {"الزوج": Fraction(3, 7), "الأخت الشقيقة": Fraction(4, 7)},
        ),
        (
            "زوجة + أم + ابن",
            {"estate_value": 1000, "spouse": "wife", "mother": True, "sons": 1},
            {"الزوجة": Fraction(1, 8), "الأم": Fraction(1, 6), "الابن": Fraction(17, 24)},
        ),
        (
            "أب + أم + ابن",
            {"estate_value": 1000, "father": True, "mother": True, "sons": 1},
            {"الأم": Fraction(1, 6), "الأب": Fraction(1, 6), "الابن": Fraction(2, 3)},
        ),
        (
            "أب + أم + بنت (الأب سدس + تعصيب)",
            {"estate_value": 1000, "father": True, "mother": True, "daughters": 1},
            {"الأم": Fraction(1, 6), "الأب": Fraction(1, 3), "البنت": Fraction(1, 2)},
        ),
        (
            "أم + زوج + أخت شقيقة (عول)",
            {"estate_value": 1000, "spouse": "husband", "mother": True, "full_sisters": 1},
            {"الزوج": Fraction(3, 8), "الأم": Fraction(1, 4), "الأخت الشقيقة": Fraction(3, 8)},
        ),
        (
            "زوجة + بنتان + أم (رد)",
            {"estate_value": 1000, "spouse": "wife", "mother": True, "daughters": 2},
            {"الزوجة": Fraction(3, 23), "الأم": Fraction(4, 23), "البنت": Fraction(16, 23)},
        ),
        (
            "أم + أخ شقيق + أخ من الأم",
            {"estate_value": 1000, "mother": True, "full_brothers": 1, "maternal_brothers": 1},
            {"الأم": Fraction(1, 6), "الأخ/الأخت من الأم": Fraction(1, 6),
             "الأخ الشقيق": Fraction(2, 3)},
        ),
        (
            "زوجة + أم + أخ من الأم (رد)",
            {"estate_value": 1000, "spouse": "wife", "mother": True, "maternal_brothers": 1},
            {"الزوجة": Fraction(1, 3), "الأم": Fraction(4, 9), "الأخ/الأخت من الأم": Fraction(2, 9)},
        ),
        (
            "زوجة + بنتان + أخ شقيق",
            {"estate_value": 1000, "spouse": "wife", "daughters": 2, "full_brothers": 1},
            {"الزوجة": Fraction(1, 8), "البنت": Fraction(2, 3), "الأخ الشقيق": Fraction(5, 24)},
        ),
        (
            "بنتان + أختان شقيقتان (عصبة مع الغير)",
            {"estate_value": 1000, "daughters": 2, "full_sisters": 2},
            {"البنت": Fraction(2, 3), "الأخت الشقيقة": Fraction(1, 3)},
        ),
        (
            "زوجة + بنت + أخت شقيقة (عصبة مع الغير)",
            {"estate_value": 1000, "spouse": "wife", "daughters": 1, "full_sisters": 1},
            {"الزوجة": Fraction(1, 8), "البنت": Fraction(1, 2), "الأخت الشقيقة": Fraction(3, 8)},
        ),
        (
            "زوج + أم + أب (الأب عاصب)",
            {"estate_value": 1000, "spouse": "husband", "mother": True, "father": True},
            {"الزوج": Fraction(1, 2), "الأم": Fraction(1, 3), "الأب": Fraction(1, 6)},
        ),
        (
            "زوجة + أم + أب + بنت (الأب سدس + تعصيب)",
            {"estate_value": 1000, "spouse": "wife", "mother": True, "father": True, "daughters": 1},
            {"الزوجة": Fraction(1, 8), "الأم": Fraction(1, 6),
             "الأب": Fraction(5, 24), "البنت": Fraction(1, 2)},
        ),
        (
            "أخ شقيق + أختان (للذكر مثل حظ الأنثيين)",
            {"estate_value": 1000, "full_brothers": 1, "full_sisters": 2},
            {"الأخ الشقيق": Fraction(1, 2), "الأخت الشقيقة": Fraction(1, 2)},
        ),
        (
            "زوجة + ابنان + بنتان",
            {"estate_value": 1000, "spouse": "wife", "sons": 2, "daughters": 2},
            {"الزوجة": Fraction(1, 8), "الابن": Fraction(7, 12), "البنت": Fraction(7, 24)},
        ),
        (
            "ابن وحيد (عصبة كاملة)",
            {"estate_value": 1000, "sons": 1},
            {"الابن": Fraction(1, 1)},
        ),
        (
            "لا ورثة (بيت المال)",
            {"estate_value": 1000},
            {},
        ),
    ],
)
def test_inheritance_cases(label, data, expected):
    result = _compute_inheritance(data)
    if not expected:
        assert result["result"]["heirs"] == []
        assert "بيت المال" in result["result"]["method"]
        return
    _assert_case(data, expected)


def test_inheritance_verifies_articles_per_rule():
    """كل ورثة يستشهدون بالمادة المناسبة للقاعدة المطبقة."""
    result = _compute_inheritance(
        {"estate_value": 1000, "spouse": "wife", "mother": True, "sons": 1}
    )
    by_label = {h["heir"]: h for h in result["result"]["heirs"]}
    assert "344" in by_label["الزوجة"]["articles"]      # الثمن للزوجة مع فرع وارث
    assert "347" in by_label["الأم"]["articles"]         # السدس للأم مع الولد
    assert "351" in by_label["الابن"]["articles"]        # تعصيب بالغير
    legal = [b for b in result["legal_basis"]]
    assert any("344" in b for b in legal)


def test_inheritance_validation_errors():
    with pytest.raises(CalculatorError):
        _compute_inheritance({"estate_value": 1000, "grandfather": True})
    with pytest.raises(CalculatorError):
        _compute_inheritance({"estate_value": -5})
    with pytest.raises(CalculatorError):
        _compute_inheritance({"estate_value": "many"})
    with pytest.raises(CalculatorError):
        _compute_inheritance({"estate_value": 1000, "sons": -1})
    with pytest.raises(CalculatorError):
        _compute_inheritance({"estate_value": 1000, "father": "yes"})
    with pytest.raises(CalculatorError):
        _compute_inheritance({"estate_value": 1000, "spouse": "both"})


def test_inheritance_son_blocks_siblings():
    """وجود الابن يحجب الإخوة والأخوات (المواد 355/356)."""
    result = _compute_inheritance(
        {"estate_value": 1000, "sons": 1, "full_brothers": 2, "full_sisters": 1}
    )
    assert [h["heir"] for h in result["result"]["heirs"]] == ["الابن"]
    assert any("محجوب" in n for n in result["result"]["notes"])
