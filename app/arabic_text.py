"""
تطبيع النص العربي للبحث النصي الكامل (المرحلة 14 — تحسينات البحث العربي).

يوفّر تطبيعًا موحَّدًا يُطبَّق على كلٍّ من محتوى الفهرس (عبر دالة SQL
nbr_normalize المسجَّلة عند فتح كل اتصال) وعلى الاستعلام، بحيث يتلاقى
الطرفان على صيغة موحدة:
- إزالة التشكيل (الحركات والشدة) والتطويل،
- توحيد ألف (أ/إ/آ) إلى (ا)، والهاء مع التاء المربوطة (ة→ه)،
  والألف المقصورة إلى ياء (ى→ي)، والهمزة المضمومة/المكسورة (ؤ→و، ئ→ي).

كما يوفّر قائمة كلمات وظيفية عربية (stopwords) تُستبعد من شروط البحث،
وتوليد متغيّرات "ال" التعريفية لكل كلمة (الكلمة، وبدون ال، ومع إضافة ال)
لتوسيع نطاق التقاط المطابقات رغم اختلاف التعريف بين الاستعلام والمحتوى.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# التطبيع
# ---------------------------------------------------------------------------

_DIACRITICS = dict.fromkeys(
    [ord(c) for c in "\u0640\u064B\u064C\u064D\u064E\u064F\u0650\u0651\u0652\u0670"]
    , ""
)

_TRANSLIT = {
    "أ": "ا",
    "إ": "ا",
    "آ": "ا",
    "ٱ": "ا",
    "ة": "ه",
    "ى": "ي",
    "ؤ": "و",
    "ئ": "ي",
}


def normalize_arabic(text):
    """يطبّع نصًا عربيًا (أو أي نص) لصيغة البحث الموحدة."""
    if text is None:
        return ""
    text = str(text)
    text = text.translate(_DIACRITICS)
    text = "".join(_TRANSLIT.get(c, c) for c in text)
    return text


# ---------------------------------------------------------------------------
# كلمات وظيفية تُستبعد من شروط البحث (لا تحمل معنى دلاليًا في النص القانوني)
# ---------------------------------------------------------------------------

ARABIC_STOPWORDS = frozenset(normalize_arabic(w) for w in (
    "في", "من", "على", "الى", "إلى", "عن", "أن", "ان", "إن", "قد", "لن",
    "لم", "ما", "لا", "كل", "بعض", "هذا", "هذه", "ذلك", "التي", "الذي",
    "الذين", "الذى", "وهو", "وهي", "كما", "كذلك", "هناك", "هنا", "ثم",
    "أو", "او", "بين", "مع", "عند", "دون", "غير", "فقط", "بعد", "قبل",
    "خلال", "حول", "أمام", "خلف", "كان", "كانت", "يكون", "أصبح", "إذا",
    "اذا", "حيث", "عبر", "نحو", "ضد", "أي", "اي", "أيضا", "ايضا", "لكن",
    "أم", "ام", "هل", "بل", "منذ", "لذا", "له", "لها", "لهم", "بها", "به",
    "منه", "منها", "فيه", "فيها", "اليه", "إليه", "عليه", "عليها", "لدى",
    "بما", "مما", "فما", "وما", "هو", "هي", "هم", "هن", "و", "ف", "ب",
    "ل", "ك", "ال",
))

# بادئات "ال" التعريفية مع أدوات الجر/العطف الملتصقة بها
_ARTICLE_PREFIXES = ("ال", "وال", "فال", "بال", "كال", "لل")

# حروف العطف/الجر الملتصقة: تطبَّق على الصيغ المجرّدة والمعرّفة
_CONJUNCTIONS = ("و", "ف", "ب", "ك")


def article_variants(term: str) -> list:
    """متغيّرات الكلمة لالتقاط مطابقات رغم اختلاف التعريف وحروف العطف.

    خطوات: (1) نزع متتالٍ لبادئات التعريف (ال/وال/فال/بال/كال/لل) لتوليد
    صيغ مجرّدة، (2) إضافة الصيغة المعرّفة بـ"ال" لكل صيغة مجرّدة،
    (3) إلصاق حروف العطف (و/ف/ب/ك) بالصيغ المجرّدة والمعرّفة («وعمل»،
    «والعمل» ...) وحرف الجر ل بالمجردة فقط («لعمل» و«للعمل») لتطابق كلمات
    المحتوى الملتصقة مثل «والمشغل» و«بالعقد».
    """
    final = [term]
    seen = {term}

    stripped = [term]
    index = 0
    while index < len(stripped):
        current = stripped[index]
        index += 1
        for prefix in _ARTICLE_PREFIXES:
            if current.startswith(prefix) and len(current) > len(prefix) + 1:
                next_term = current[len(prefix):]
                if len(next_term) >= 2 and next_term not in stripped:
                    stripped.append(next_term)
        for conj in _CONJUNCTIONS + ("ل",):
            if current.startswith(conj) and len(current) > len(conj) + 2:
                next_term = current[len(conj):]
                if len(next_term) >= 3 and next_term not in stripped:
                    stripped.append(next_term)

    bare_forms = []
    defined_forms = []
    for form in stripped:
        if form not in seen:
            seen.add(form)
            final.append(form)
        if form.startswith("ال"):
            if len(form) >= 3:
                defined_forms.append(form)
            continue
        bare_forms.append(form)
        if len(form) >= 3:
            if form == term and any(
                term.startswith(p) for p in _ARTICLE_PREFIXES
            ):
                continue
            defined = "ال" + form
            if defined not in seen:
                seen.add(defined)
                final.append(defined)
                defined_forms.append(defined)

    for conj in _CONJUNCTIONS:
        for form in bare_forms + defined_forms:
            attached = conj + form
            if len(attached) >= 3 and attached not in seen:
                seen.add(attached)
                final.append(attached)

    for form in bare_forms:
        if len(form) >= 2:
            for attached in ("ل" + form, "لل" + form):
                if len(attached) >= 3 and attached not in seen:
                    seen.add(attached)
                    final.append(attached)
    return final


def build_search_terms(query_text: str) -> list:
    """يطبّع ويقسّم الاستعلام ويعيد متغيّرات كل كلمة (بدون كلمات وظيفية)."""
    normalized = normalize_arabic(query_text)
    raw_terms = (
        t for t in normalized.split()
        if len(t) >= 2 and t not in ARABIC_STOPWORDS
    )
    return [article_variants(t) for t in raw_terms]


def build_fts_query(term_groups: list) -> str:
    """يبني تعبير FTS5: AND بين الكلمات، و OR بين متغيّرات كل كلمة.

    مثال: ("الموظف"* OR "موظف"*) AND ("العقد"* OR "عقد"*)
    """
    groups = []
    for candidates in term_groups:
        groups.append("(" + " OR ".join(f'"{c}"*' for c in candidates) + ")")
    return " AND ".join(groups)
