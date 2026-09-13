"""تحويل الأرقام والمبالغ المالية إلى كلمات بالعربية أو الفرنسية.

يُستعمل في مولد الوثائق لإضافة «المبلغ كتابةً» (حروفًا ورقمًا) كما هو
معمول به في الوثائق الرسمية المغربية. الواجهة الأساسية: amount_words().
"""
from __future__ import annotations

import re
from typing import Optional

# ---------------------------------------------------------------------------
# العربية (الضمّ الكلاسيكي المستعمل في الوثائق الرسمية)
# ---------------------------------------------------------------------------

_UNITS = ["", "واحد", "اثنان", "ثلاثة", "أربعة", "خمسة",
          "ستة", "سبعة", "ثمانية", "تسعة"]
_TEENS = ["عشرة", "أحد عشر", "اثنا عشر", "ثلاثة عشر", "أربعة عشر",
          "خمسة عشر", "ستة عشر", "سبعة عشر", "ثمانية عشر", "تسعة عشر"]
_TENS = ["", "", "عشرون", "ثلاثون", "أربعون", "خمسون",
         "ستون", "سبعون", "ثمانون", "تسعون"]
_HUNDREDS = {1: "مائة", 2: "مائتان", 3: "ثلاثمائة", 4: "أربعمائة",
             5: "خمسمائة", 6: "ستمائة", 7: "سبعمائة",
             8: "ثمانمائة", 9: "تسعمائة"}


def _under_hundred(n: int) -> str:
    """أرقام 0–99 بشكل نصّي."""
    if n == 0:
        return ""
    if n < 10:
        return _UNITS[n]
    if n == 10:
        return "عشرة"
    if n < 20:
        return _TEENS[n - 10]
    tens, unit = divmod(n, 10)
    if unit == 0:
        return _TENS[tens]
    return _UNITS[unit] + " و" + _TENS[tens]


def _under_thousand(n: int) -> str:
    """أرقام 0–999 بشكل نصّي."""
    if n == 0:
        return ""
    hundreds, rest = divmod(n, 100)
    out = ""
    if hundreds:
        out = _HUNDREDS[hundreds]
    rest_w = _under_hundred(rest)
    if rest_w:
        out = (out + " و" + rest_w) if out else rest_w
    return out


def _thousands_word(t: int) -> str:
    """أرقام الآلاف (1000–999999) بشكل نصّي."""
    if t == 0:
        return ""
    if t == 1:
        return "ألف"
    if t == 2:
        return "ألفان"
    if t < 11:
        return _UNITS[t] + " آلاف"
    if t < 100:
        return _under_hundred(t) + " ألفًا"
    return _under_thousand(t) + " ألف"


def _millions_word(m: int) -> str:
    """أرقام الملايين (1e6–999e6) بشكل نصّي."""
    if m == 0:
        return ""
    if m == 1:
        return "مليون"
    if m == 2:
        return "مليونان"
    if m < 11:
        return _UNITS[m] + " ملايين"
    if m < 100:
        return _under_hundred(m) + " مليونًا"
    return _under_thousand(m) + " مليون"


def number_to_arabic(value: int) -> str:
    """يحوّل عددًا صحيحًا غير سالب إلى كلمات عربية."""
    if value == 0:
        return "صفر"
    millions, rem = divmod(value, 1_000_000)
    thousands, rest = divmod(rem, 1000)
    parts = []
    if millions:
        parts.append(_millions_word(millions))
    if thousands:
        parts.append(_thousands_word(thousands))
    if rest:
        parts.append(_under_thousand(rest))
    return " و".join(parts)


# ---------------------------------------------------------------------------
# الفرنسية
# ---------------------------------------------------------------------------

_FR_UNITS = ["", "un", "deux", "trois", "quatre", "cinq", "six",
             "sept", "huit", "neuf"]
_FR_TEENS = ["dix", "onze", "douze", "treize", "quatorze", "quinze",
             "seize", "dix-sept", "dix-huit", "dix-neuf"]
_FR_TENS = ["", "", "vingt", "trente", "quarante", "cinquante",
            "soixante", "soixante-dix", "quatre-vingt", "quatre-vingt-dix"]


def _fr_under_hundred(n: int) -> str:
    if n == 0:
        return ""
    if n < 10:
        return _FR_UNITS[n]
    if n < 20:
        return _FR_TEENS[n - 10]
    tens, unit = divmod(n, 10)
    if tens == 7:
        if unit == 1:
            return "soixante et onze"
        return "soixante-" + _FR_TEENS[unit]
    if tens == 9:
        return "quatre-vingt-" + _FR_TEENS[unit]
    out = _FR_TENS[tens] + ("s" if n == 80 else "")
    if unit == 1:
        out += " et un"
    elif unit:
        out += "-" + _FR_UNITS[unit]
    return out


def _fr_under_thousand(n: int) -> str:
    if n == 0:
        return ""
    hundreds, rest = divmod(n, 100)
    if hundreds == 0:
        return _fr_under_hundred(rest)
    head = "cent"
    if hundreds == 1:
        head = "cent"
    elif hundreds == 2:
        head = "deux cents" if rest == 0 else "deux cent"
    else:
        head = _FR_UNITS[hundreds] + (" cents" if rest == 0 else " cent")
    rest_w = _fr_under_hundred(rest)
    if rest_w:
        return head + " " + rest_w
    return head


def number_to_french(value: int) -> str:
    if value == 0:
        return "zéro"
    if value == 1000:
        return "mille"
    millions, rem = divmod(value, 1_000_000)
    thousands, rest = divmod(rem, 1000)
    parts = []
    if millions:
        parts.append(_fr_under_thousand(millions) + (" millions" if millions > 1 else " million"))
    if thousands:
        if thousands == 1:
            parts.append("mille")
        else:
            parts.append(_fr_under_thousand(thousands) + " mille")
    if rest:
        parts.append(_fr_under_thousand(rest))
    return " ".join(parts)


# ---------------------------------------------------------------------------
# واجهة المبالغ المالية
# ---------------------------------------------------------------------------

_CLEAN_VALUE_RE = re.compile(r"[^\d.,\s]")


def parse_amount(value) -> Optional[tuple[int, int]]:
    """يحلل مدخلات مالية (أرقام/فواصل/نقط) → (دراهم، سنتيمات). يعيد None إن لم يصلح."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if isinstance(value, float):
            return int(value), round((value - int(value)) * 100)
        return int(value), 0
    if isinstance(value, str):
        s = _CLEAN_VALUE_RE.sub("", value).strip()
        if not s:
            return None
        s = s.replace(" ", "")
        # العرف المغربي: النقطة فاصل آلاف والفاصلة فاصل عشري.
        # معه أيضًا الصيغ الشائعة: "1.500", "1.500,50", "1500.50", "1 500".
        if "," in s and "." in s:
            if s.rfind(",") > s.rfind("."):
                # فاصلة عشرية أخيرة → النقاط فواصل آلاف
                s = s.replace(".", "").replace(",", ".")
            else:
                # نقطة عشرية أخيرة → الفواصل ترقيم
                s = s.replace(",", "")
        elif "," in s:
            s = s.replace(".", "").replace(",", ".")
        elif "." in s:
            thousands_pattern = r"^\d{1,3}(\.\d{3})+$"
            if re.match(thousands_pattern, s):
                s = s.replace(".", "")  # نقاط فواصل آلاف ("1.500" → 1500)
            elif s.count(".") == 1:
                whole, frac = s.split(".")
                if len(whole) <= 4 and len(frac) <= 2:
                    pass  # تُعامل كفاصلة عشرية أدناه
                else:
                    s = s.replace(".", "")  # ترقيم آلاف منفرد
            else:
                s = s.replace(".", "")
        if "." in s:
            whole, frac = s.split(".")
            frac = (frac + "00")[:2]
            try:
                return int(whole or 0), int(frac)
            except ValueError:
                return None
        try:
            return int(s), 0
        except ValueError:
            return None
    return None


def amount_words(value, lang: str = "ar") -> Optional[dict]:
    """يعيد تفصيل المبلغ كتابةً (عربي/فرنسي) أو None لمدخل غير صالح.

    النتيجة: {value, dirhams, centimes, arabic, french, line_ar, line_fr}
    """
    parsed = parse_amount(value)
    if parsed is None:
        return None
    dirhams, centimes = parsed
    arabic = number_to_arabic(dirhams)
    french = number_to_french(dirhams)

    if centimes:
        ar_line = f"{arabic} درهم و{number_to_arabic(centimes)} سنتيمًا"
        fr_line = f"{french} dirhams et {number_to_french(centimes)} centimes"
    else:
        ar_line = f"{arabic} درهم"
        fr_line = f"{french} dirhams" if dirhams != 1 else f"{french} dirham"

    return {
        "value": _fmt_value(dirhams, centimes),
        "dirhams": dirhams,
        "centimes": centimes,
        "arabic": arabic,
        "french": french,
        "line_ar": ar_line,
        "line_fr": fr_line,
    }


def _fmt_value(d: int, c: int) -> str:
    if c:
        return f"{d}.{c:02d}"
    return str(d)