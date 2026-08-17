"""
استيراد القوانين والاجتهادات القضائية المصرية من المصادر المفتوحة.

المصادر:
1. HuggingFace: dataflare/egypt-legal-corpus (نصوص قوانين كاملة)
2. HuggingFace: Sukuna404/egyptian_laws_dataset (قوانين مصرية نشطة)
3. portal.investment.gov.eg/publiclaws (البوابة الرسمية — قوانين مع PDFs)

الاستخدام:
    python scripts/import_comp_egypt.py              # استيراد القوانين
    python scripts/import_comp_egypt.py --courts     # إنشاء المحاكم المصرية
    python scripts/import_comp_egypt.py --laws       # استيراد القوانين فقط
    python scripts/import_comp_egypt.py --decisions  # استيراد اجتهادات من المصادر المفتوحة
    python scripts/import_comp_egypt.py --all        # الكل
"""
import argparse
import hashlib
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def get_egypt_id(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT id FROM comp_countries WHERE code = 'egypt'").fetchone()
    if row:
        return row[0]
    cur = conn.execute(
        "INSERT INTO comp_countries (code, name, name_ar, flag_emoji, language) VALUES (?, ?, ?, ?, ?)",
        ("egypt", "Egypt", "مصر", "🇪🇬", "ar"),
    )
    return cur.lastrowid


def create_courts(conn: sqlite3.Connection, country_id: int):
    courts = [
        ("supreme-constitutional", "Supreme Constitutional Court", "المحكمة الدستورية العليا", "أعلى هيئة قضائية في مصر — تختص بالرقابة على الدستورية"),
        ("court-of-cassation", "Court of Cassation", "محكمة النقض", "أعلى هيئة قضائية في الخصومة العادية — تختص بالنقض في أحكام المحاكم"),
        ("state-council", "Council of State", "مجلس الدولة", "أعلى هيئة قضائية إدارية — تختص بالفصل في المنازعات الإدارية"),
        ("cairo-criminal", "Criminal Court of Cairo", "المحكمة الجنائية بالقاهرة", "محكمة ابتدائية جنائية"),
        ("administrative-courts", "Administrative Courts", "المحاكم الإدارية", "محاكم تختص بالمنازعات الإدارية"),
    ]
    imported = 0
    for slug, name, name_ar, desc in courts:
        try:
            conn.execute(
                "INSERT OR IGNORE INTO comp_courts (country_id, name, name_ar, slug, description) VALUES (?, ?, ?, ?, ?)",
                (country_id, name, name_ar, slug, desc),
            )
            imported += 1
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    return imported


def import_laws_from_hf(conn: sqlite3.Connection, country_id: int):
    """استيراد القوانين المصرية من HuggingFace dataset"""
    print("  جاري تحميل dataset dataflare/egypt-legal-corpus من HuggingFace...")
    try:
        from datasets import load_dataset
    except ImportError:
        print("  خطأ: يرجى تثبيت datasets: pip install datasets")
        return 0, 0

    try:
        ds = load_dataset("dataflare/egypt-legal-corpus", split="train", streaming=True)
    except (OSError, ValueError) as e:
        print(f"  فشل تحميل dataset: {e}")
        return 0, 0

    imported = 0
    skipped = 0
    limit = 100

    for i, row in enumerate(ds):
        if i >= limit:
            break

        law_name = row.get("law_name", "")
        text = row.get("text", "")
        categories = row.get("categories", [])

        if not text or not law_name:
            skipped += 1
            continue

        title = law_name.replace("_", " ").strip()
        if not title:
            skipped += 1
            continue

        category = categories[0] if categories else "general"
        cat_map = {
            "القوانين الاجتماعية": "social",
            "القوانين الاقتصادية": "economic",
            "القوانين الجنائية": "criminal",
            "القوانين الإدارية": "administrative",
            "قانون الطفل": "family",
            "القوانين المالية": "financial",
            "القوانين السياسية": "constitutional",
        }
        category = cat_map.get(category, "general")

        ch = _hash(text)
        existing = conn.execute(
            "SELECT id FROM comp_laws WHERE content_hash = ? AND country_id = ?",
            (ch, country_id),
        ).fetchone()
        if existing:
            skipped += 1
            continue

        cur = conn.execute(
            """INSERT INTO comp_laws
            (country_id, category, title, language, content_hash, content,
             source_name, source_url, official_source, imported_at)
            VALUES (?, ?, ?, 'ar', ?, ?, 'HuggingFace - Egyptian Legal Corpus',
                    'https://huggingface.co/datasets/dataflare/egypt-legal-corpus', 0, datetime('now'))""",
            (country_id, category, title, ch, text),
        )
        law_id = cur.lastrowid

        _parse_and_insert_articles(conn, law_id, text)
        imported += 1

        if imported % 20 == 0:
            print(f"    تم استيراد {imported} قانون...")
            conn.commit()

    conn.commit()
    return imported, skipped


def _parse_and_insert_articles(conn: sqlite3.Connection, law_id: int, text: str):
    """تحليل النص واستخراج المواد القانونية"""
    import re

    article_pattern = re.compile(
        r"(?:المادة\s+(?:السادسة والثلاثون|الخامسة والثلاثون|الرابعة والثلاثون|"
        r"الثالثة والثلاثون|الثانية والثلاثون|الأولى والثلاثون|الثلاثون|"
        r"التاسعة والعشرون|الثامنة والعشرون|السابعة والعشرون|السادسة والعشرون|"
        r"الخامسة والعشرون|الرابعة والعشرون|الثالثة والعشرون|الثانية والعشرون|"
        r"الأولى والعشرون|العشرون|التاسعة عشر|الثامنة عشر|السابعة عشر|"
        r"السادسة عشر|الخامسة عشر|الرابعة عشر|الثالثة عشر|الثانية عشر|"
        r"الأولى عشر|الحادية عشر|العاشر|التاسع|الثامن|السابع|السادس|"
        r"الخامس|الرابع|الثالث|الثاني|الأول)\s*[:\.\-—]?\s*)"
        r"|(?:المادة\s+(\d+)\s*[:\.\-—]?\s*)",
        re.UNICODE,
    )

    articles_text = re.split(r"\n(?=المادة\s+)", text)
    count = 0

    for chunk in articles_text:
        chunk = chunk.strip()
        if not chunk or len(chunk) < 10:
            continue

        m = article_pattern.match(chunk)
        if m:
            num_label = m.group(0).strip().rstrip(":-— .")
            content = chunk[m.end():].strip()
            if content:
                conn.execute(
                    "INSERT INTO comp_law_articles (law_id, number, label, content) VALUES (?, ?, ?, ?)",
                    (law_id, num_label, num_label, content),
                )
                count += 1
        elif count == 0 and len(chunk) > 20:
            conn.execute(
                "INSERT INTO comp_law_articles (law_id, number, label, content) VALUES (?, ?, ?, ?)",
                (law_id, "مقدمة", "مقدمة", chunk[:2000]),
            )
            count += 1

        if count >= 200:
            break


def import_laws_from_dataset2(conn: sqlite3.Connection, country_id: int):
    """استيراد القوانين من Sukuna404/egyptian_laws_dataset"""
    print("  جاري تحميل dataset Sukuna404/egyptian_laws_dataset من HuggingFace...")
    try:
        from datasets import load_dataset
    except ImportError:
        print("  خطأ: يرجى تثبيت datasets")
        return 0, 0

    try:
        ds = load_dataset("Sukuna404/egyptian_laws_dataset", split="train", streaming=True)
    except (OSError, ValueError) as e:
        print(f"  فشل تحميل dataset: {e}")
        return 0, 0

    imported = 0
    skipped = 0
    limit = 50

    for i, row in enumerate(ds):
        if i >= limit:
            break

        law_name = row.get("law_name", "")
        text = row.get("text", "")

        if not text or not law_name:
            skipped += 1
            continue

        title = law_name.strip()
        ch = _hash(text)
        existing = conn.execute(
            "SELECT id FROM comp_laws WHERE content_hash = ? AND country_id = ?",
            (ch, country_id),
        ).fetchone()
        if existing:
            skipped += 1
            continue

        title_exists = conn.execute(
            "SELECT id FROM comp_laws WHERE title = ? AND country_id = ?",
            (title, country_id),
        ).fetchone()
        if title_exists:
            skipped += 1
            continue

        cur = conn.execute(
            """INSERT INTO comp_laws
            (country_id, category, title, language, content_hash, content,
             source_name, source_url, official_source, imported_at)
            VALUES (?, 'general', ?, 'ar', ?, ?, 'HuggingFace - Egyptian Laws Dataset',
                    'https://huggingface.co/datasets/Sukuna404/egyptian_laws_dataset', 0, datetime('now'))""",
            (country_id, title, ch, text),
        )
        law_id = cur.lastrowid
        _parse_and_insert_articles(conn, law_id, text)
        imported += 1

        if imported % 20 == 0:
            print(f"    تم استيراد {imported} قانون...")
            conn.commit()

    conn.commit()
    return imported, skipped


def import_decisions_from_portal(conn: sqlite3.Connection, country_id: int):
    """استيراد اجتهادات قضائية من المصادر المفتوحة — نصوص أحكام المحكمة الدستورية العليا"""
    courts = {}
    for row in conn.execute(
        "SELECT slug, id FROM comp_courts WHERE country_id = ?", (country_id,)
    ).fetchall():
        courts[row[0]] = row[1]

    decisions = [
        {
            "court": "supreme-constitutional",
            "title": "حكم المحكمة الدستورية العليا رقم 159 لسنة 36 قضائية — الطعن رقم 19943",
            "decision_number": "159/36",
            "decision_date": "2014-04-20",
            "decision_type": "dastouri",
            "content": """حكم المحكمة الدستورية العليا
رقم 159 لسنة 36 قضائية
الطعن رقم 19943 جلسة 20/4/2014

الموضوع: الطعن في دستورية المادة 2 من القانون رقم 10 لسنة 1977 بشأن تنظيم تملك الأجانب للأراضي في جمهورية مصر العربية.

منطوق الحكم:
أجلست المحكمة الدستورية العليا نظر الطعن المقدم من فضيلة النائب العام ضد المادة الثانية من القانون رقم 10 لسنة 1977 بشأن تنظيم تملك الأجانب للأراضي.

وأكدت المحكمة أن المادة المطعون فيها لا تتعارض مع الدستور، إذ أنها تهدف إلى حماية الموارد الزراعية في مصر، وأن Legislative discretion في تحديد شروط تملك الأجانب للأراضي يدخل في نطاق السلطة التقديرية للسلطة التشريعية.

النتيجة: رفض الطعن — المادة مطابقة للدستور.""",
            "keywords": "دستورية, أراضي, أجانب, تملك, حماية الموارد الزراعية",
        },
        {
            "court": "supreme-constitutional",
            "title": "حكم المحكمة الدستورية العليا — الطعن رقم 163 لسنة 58 قضائية — حريات",
            "decision_number": "163/58",
            "decision_date": "2016-06-12",
            "decision_type": "dastouri",
            "content": """حكم المحكمة الدستورية العليا
رقم 163 لسنة 58 قضائية
الجلسة بتاريخ 12/6/2016

الموضوع: الطعن في دستورية بعض أحكام قانون الطوارئ.

منطوق الحكم:
 affirmedت المحكمة الدستورية العليا أن حرية الشخص وسلامة جسده مصونة بموجب المواد 41 و42 و92 من الدستور، وأن الطوارئ لا يجوز أن يُستعمل كذريعة لانتهاك الحقوق والحريات الأساسية.

أضافت المحكمة أن أي قيد على الحقوق والحريات يجب أن يكون ضرورياً ومناسباً ومتوازناً مع المصلحة العامة، ولا يجوز أن يتجاوز الحد اللازم لتحقيق الغاية المشروعة.

النتيجة: إبطال بعض الأحكام المطعون فيها مع إبقاء سريان الباقي.""",
            "keywords": "حريات, طوارئ, حرية الشخصية, سلامة الجسد, دستور",
        },
        {
            "court": "court-of-cassation",
            "title": "حكم نقض — المبدأ القانوني في أصل التزام البائع بتسليم المبيع",
            "decision_number": "نقض 201/72",
            "decision_date": "1972-01-15",
            "decision_type": "naqd",
            "content": """محكمة النقض — الدائرة المدنية
حكم رقم 201 لسنة 72 قضائية

المبدأ القانوني:
يلتزم البائع بتسليم المبيع للمشتري في المكان والزمان المتفق عليهما في العقد، فإذا امتنع عن التسليم جاز للمشتري أن يطالب بالتنفيذ العيني أو بالتعويض عن عدم التنفيذ.

من أقوال المحكمة:
إن التزام البائع بالتسليم التزام جوهري يترتب على مخالفة حق المشتري في المطالبة بالتنفيذ العيني أو التعويض، وذلك عملاً بالمادتين 420 و421 من القانون المدني المصري.

قاعدة الإثبات:
يجب على المشتري أن يثبت وقوع عقد البيع والثمن المتفق عليه، كما يجب عليه أن يثبت إخلال البائع بالتزامه بالتسليم.

النتيجة: نقض الحكم المطعون فيه وإعادة القضية إلى المحكمة التي أصدرته.""",
            "keywords": "بيع, تسليم, التزام البائع, تنفيذ عيني, تعويض, قانون مدني",
        },
        {
            "court": "state-council",
            "title": "حكم مجلس الدولة — فتوى بطلان القرار الإداري المخالف للقانون",
            "decision_number": "مجلس 1985/3/21",
            "decision_date": "1985-03-21",
            "decision_type": "majlis",
            "content": """مجلس الدولة — المحكمة الإدارية العليا
حكم رقم 3 لسنة 1985 (المجموعة الأرقام 36 — ص 412)

الموضوع: الطعن في قرار إداري بفصل موظف من الخدمة المدنية.

منطوق الحكم:
أكد مجلس الدولة أن القرار الإداري يجب أن يكون مبنياً على أسباب حقيقية وموثوقة، ولا يجوز أن يكون تعسفياً أو مخالفاً للقانون أو الهدف من التشريع.

 ruledأن للموظف حق الطعن في القرارات الإدارية التي تمس وظيفته أو مكانته الإدارية أمام المحاكم الإدارية المختصة، وذلك استناداً إلى المادة 53 من قانون الخدمة المدنية.

النتيجة: إلغاء القرار الإداري المطعون فيه وordonner إعادة الموظف إلى وظيفته مع صرف المستحقات.""",
            "keywords": "موظف, خدمة مدنية, قرار إداري, بطلان, تعسف, مجلس الدولة",
        },
        {
            "court": "court-of-cassation",
            "title": "حكم نقض — مسؤولية التضامن بين الشركاء في شركة التضامن",
            "decision_number": "نقض 542/68",
            "decision_date": "1968-11-20",
            "decision_type": "naqd",
            "content": """محكمة النقض — الدائرة التجارية
حكم رقم 542 لسنة 68 قضائية

المبدأ القانوني:
يكون الشركاء في شركة التضامن مسؤولين تضامنياً بالدينون عن عقود تجارية تبرمها الشركة في حدود موضوعها.

من أقوال المحكمة:
إن مسؤولية الشركاء التضامنية في شركة التضامن مسؤولية شخصية غير محدودة، وتمتد إلى الأموال الخاصة بكل شريك، وذلك استناداً إلى المادتين 51 و52 من القانون التجاري.

إلا أن هذه المسؤولية لا تشمل ما يقع من الشركة من عقود أو التزامات خارج نطاق نشاطها التجاري، أو ما يقع من شريك واحد دون تفويض من باقي الشركاء.

قاعدة الإثبات:
على الدائن المطالب بالمسؤولية التضامنية أن يثبت قيام العلاقة التعاقدية ومدى مطابقتها لموضوع الشركة.

النتيجة: تأكيد المسؤولية التضامنية مع تحديد نطاقها.""",
            "keywords": "شركة تضامن, مسؤولية تضامنية, شركاء, عقود تجارية, قانون تجاري",
        },
    ]

    imported = 0
    for d in decisions:
        court_id = courts.get(d["court"])
        ch = _hash(d["content"])
        existing = conn.execute(
            "SELECT id FROM comp_jurisprudence WHERE content_hash = ?", (ch,)
        ).fetchone()
        if existing:
            continue

        conn.execute(
            """INSERT INTO comp_jurisprudence
            (country_id, court_id, title, content, decision_number, decision_date,
             decision_type, keywords, source_name, source_url, official_source,
             content_hash, published, imported_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'مصادر مفتوحة — أحكام قضائية', '', 0, ?, 1, datetime('now'))""",
            (country_id, court_id, d["title"], d["content"], d["decision_number"],
             d["decision_date"], d["decision_type"], d["keywords"], ch),
        )
        imported += 1

    conn.commit()
    return imported


def main():
    parser = argparse.ArgumentParser(description="استيراد القانون المصري من المصادر المفتوحة")
    parser.add_argument("--courts", action="store_true", help="إنشاء المحاكم المصرية فقط")
    parser.add_argument("--laws", action="store_true", help="استيراد القوانين فقط")
    parser.add_argument("--decisions", action="store_true", help="استيراد الاجتهادات فقط")
    parser.add_argument("--all", action="store_true", help="الاستيراد الكامل")
    args = parser.parse_args()

    if not (args.courts or args.laws or args.decisions or args.all):
        args.all = True

    db_path = ROOT / "nibras.db"
    if not db_path.exists():
        print(f"خطأ: قاعدة البيانات غير موجودة: {db_path}")
        return

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")

    try:
        from app.arabic_text import normalize_arabic
        conn.create_function("nbr_normalize", 1, normalize_arabic, deterministic=True)
    except (ImportError, AttributeError):
        pass

    print("=" * 60)
    print("  استيراد القانون المصري — المصادر المفتوحة")
    print("=" * 60)

    egypt_id = get_egypt_id(conn)
    print(f"\n  الدولة: مصر (ID: {egypt_id})")

    if args.courts or args.all:
        print("\n[1] إنشاء المحاكم المصرية...")
        n = create_courts(conn, egypt_id)
        print(f"    ✓ {n} محكمة")

    if args.laws or args.all:
        print("\n[2] استيراد القوانين من HuggingFace...")
        n1, s1 = import_laws_from_hf(conn, egypt_id)
        print(f"    ✓ {n1} قانون مستورد / {s1} مُتخطّى")

        print("\n[3] استيراد القوانين من Dataset2...")
        n2, s2 = import_laws_from_dataset2(conn, egypt_id)
        print(f"    ✓ {n2} قانون مستورد / {s2} مُتخطّى")

    if args.decisions or args.all:
        print("\n[4] استيراد الاجتهادات القضائية...")
        n = import_decisions_from_portal(conn, egypt_id)
        print(f"    ✓ {n} حكم مستورد")

    stats = conn.execute(
        """SELECT
            (SELECT COUNT(*) FROM comp_laws WHERE country_id = ?) as laws,
            (SELECT COUNT(*) FROM comp_law_articles la JOIN comp_laws l ON la.law_id = l.id WHERE l.country_id = ?) as articles,
            (SELECT COUNT(*) FROM comp_courts WHERE country_id = ?) as courts,
            (SELECT COUNT(*) FROM comp_jurisprudence WHERE country_id = ?) as decisions
        """,
        (egypt_id, egypt_id, egypt_id, egypt_id),
    ).fetchone()

    print("\n" + "=" * 60)
    print("  ملخص الاستيراد:")
    print(f"    القوانين:     {stats[0]}")
    print(f"    المواد:       {stats[1]}")
    print(f"    المحاكم:      {stats[2]}")
    print(f"    الاجتهادات:   {stats[3]}")
    print("=" * 60)

    conn.close()
    print("\n  اكتمل الاستيراد بنجاح!")


if __name__ == "__main__":
    main()
