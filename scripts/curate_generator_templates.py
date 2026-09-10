"""يبني data/legal_docs/templates.json (القوالب الموصى بها للمولّد).

يختار ~40 وثيقة مرجعية من مكتبة الوثائق المنزّلة، يستخرج حقولها تلقائيًا
من فراغاتها، ويكتب القائمة الجاهزة (id/title/category/file/fields).
يعمل مرة واحدة ويدويًا بعد التنزيل؛ تعديل التسميات/الأنواع لاحقًا يتم
مباشرة في templates.json.
"""
import json
import os
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import generator

# (category, keywords) — مطابقة جزئية بعد تطبيع Unicode (قياسية)
SELECTED = [
    ("وكالات", ["سياقة وبيع سيارة 1"]),
    ("وكالات", ["التشطيب على السجل التجاري"]),
    ("وكالات", ["توكيل عام"]),
    ("وكالات", ["التصرف الكامل في محل"]),
    ("وكالات", ["بكراء سكنى"]),
    ("وكالات", ["شراء بقعة"]),
    ("وكالات", ["استخلاص حظ ونصيب"]),
    ("وكالات", ["تسلم مبلغ"]),
    ("عقود بيع كراء عمل تسيير", ["عقد كراء سكنى"]),
    ("عقود بيع كراء عمل تسيير", ["كراء محل تجاري نموذج"]),
    ("عقود بيع كراء عمل تسيير", ["عقد بيع دراجة نارية"]),
    ("عقود بيع كراء عمل تسيير", ["بيع آلة حصاد"]),
    ("عقود بيع كراء عمل تسيير", ["وعد بالبيع 2"]),
    ("عقود بيع كراء عمل تسيير", ["عمل محدد المدة 1"]),
    ("عقود بيع كراء عمل تسيير", ["عمل غير محدد المدة"]),
    ("عقود بيع كراء عمل تسيير", ["عقد رهن 2"]),
    ("عقود بيع كراء عمل تسيير", ["شراكة في التجارة"]),
    ("عقود بيع كراء عمل تسيير", ["تسيير محل تجاري"]),
    ("التزامات", ["التزام بالسكن"]),
    ("التزامات", ["بحياة الابناء"]),
    ("التزامات", ["تحمل مسؤولية سيارة"]),
    ("التزامات", ["وتصريح بالشرف للضمان الاجتماعي"]),
    ("التزامات", ["كفالة طفل"]),
    ("التزامات", ["افراغ سكنى من المكتري"]),
    ("اشهادات", ["اشهاد الشهود"]),
    ("اشهادات", ["اشهاد بالعمل"]),
    ("اشهادات", ["بتوصل بمبلغ من مسير محل"]),
    ("اشهادات", ["اشهاد حادثة"]),
    ("اشهادات", ["بتوصل بدفعة مالية أولى"]),
    ("تنازلات", ["تنازل عن شكاية"]),
    ("تنازلات", ["تعويض حادثة سير"]),
    ("تنازلات", ["محل تابع للجماعة"]),
    ("تنازلات", ["عداد الماء"]),
    ("تنازلات", ["بطاقة رمادية"]),
    ("شكايات", ["نموذج شكاية النصب"]),
    ("شكايات", ["شكاية بالضرب والجرح"]),
    ("شكايات", ["السب والشتم والتهجم على المنزل"]),
    ("شكايات", ["الضجيج وإزعاج الساكنة"]),
    ("طلبات ومراسلات واشعارات وتظلمات", ["شهادة عمل"]),
    ("طلبات ومراسلات واشعارات وتظلمات", ["شهادة إدارية"]),
    ("طلبات ومراسلات واشعارات وتظلمات", ["وظيفة نموذج 1"]),
    ("موافقات", ["القاصر بالعمل في محله التجاري"]),
    ("موافقات", ["موافقة سفر قاصر"]),
    ("الجمعيات", ["محضر الجمع العام التأسيسي"]),
    ("الجمعيات", ["أساسي لجمعية رياضية نموذج 1"]),
]


def norm(s):
    s = unicodedata.normalize("NFKC", s or "").lower().strip()
    s = s.replace("\u0640", "")  # إزالة التطويل (ــ)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s


def find_file(category, keywords):
    docs = [d for d in generator.list_docs()
            if d["category"] == category and d["fillable"]]
    for d in docs:
        title = norm(d["title"]).rstrip(".docx")
        if all(norm(kw) in title for kw in keywords):
            return d["file"]
    return None


def main():
    done = 0
    missing = []
    templates = []
    for category, keywords in SELECTED:
        file = find_file(category, keywords)
        if not file:
            missing.append((category, keywords[0]))
            continue
        try:
            fields = generator.extract_fields(file)
        except (generator.GeneratorError, OSError, ValueError) as exc:
            missing.append((category, keywords[0], str(exc)))
            continue
        title = file.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        templates.append({
            "id": f"t{done + 1:03d}",
            "title": title,
            "category": category,
            "file": file,
            "description": f"قالب «{title}» من مكتبة الوثائق المغربية.",
            "fields": fields,
        })
        done += 1
    payload = {"templates": templates, "count": done}
    path = generator.TEMPLATES_PATH
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print("written:", path)
    print("templates:", done)
    for m in missing[:20]:
        print("  MISSING:", m)


if __name__ == "__main__":
    main()
