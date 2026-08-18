"""استيراد كتب مكتبة الباحث من مصادر مفتوحة — أطروحتان ورسائل وأبحاث."""
import hashlib
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db_session

BOOKS = [
    # أطروحة دكتوراه — مصر
    {
        "title": "Rebalancing the Scales: Egyptian Contract Law and Unconscionability",
        "author": "Yousef Samir Elnemr",
        "book_type": "dissertation",
        "legal_category": "civil",
        "description": "دراسة مقارنة بين قواعد القانون المدني المصري بشأن العقود غير المتكافئة ومبدأ الغير معقول في القانون الأمريكي. أطروحة ماجستير، الجامعة الأمريكية بالقاهرة 2024.",
        "year": 2024,
        "language": "en",
        "source_name": "AUC Knowledge Fountain",
        "source_url": "https://fount.aucegypt.edu/cgi/viewcontent.cgi?article=3337&context=etds",
        "official_source": 1,
    },
    # رسالة ماجستير — مصر
    {
        "title": "حقوق والضمانات المقررة للمتهمين في جرائم الإرهاب: دراسة مقارنة",
        "title_ar": "حقوق والضمانات المقررة للمتهمين في جرائم الإرهاب: دراسة مقارنة",
        "author": "عبدالله عاصم رمضان مرسى",
        "book_type": "thesis",
        "legal_category": "criminal",
        "description": "أطروحة دكتوراه من كلية الحقوق جامعة القاهرة 2025، تتناول الضمانات الإجرائية للمتهمين في جرائم الإرهاب مع مقارنة بالأنظمة الدولية.",
        "year": 2025,
        "language": "ar",
        "source_name": "جامعة القاهرة - كلية الحقوق",
        "source_url": "https://fll.law.cu.edu.eg/cgi-bin/koha/opac-detail.pl?biblionumber=43194",
        "official_source": 1,
    },
    # رسالة ماجستير — مصر
    {
        "title": "الحماية الجنائية للمبلغين في جرائم الفساد: دراسة مقارنة",
        "title_ar": "الحماية الجنائية للمبلغين في جرائم الفساد: دراسة مقارنة",
        "author": "سمير حافظ السيد حافظ",
        "book_type": "thesis",
        "legal_category": "criminal",
        "description": "رسالة ماجستير من كلية الحقوق جامعة القاهرة 2024، تتناول الحماية الجنائية للمبلغين (الوسيط السري) في جرائم الفساد بمختلف أنواعها.",
        "year": 2024,
        "language": "ar",
        "source_name": "جامعة القاهرة - كلية الحقوق",
        "source_url": "https://fll.law.cu.edu.eg/cgi-bin/koha/opac-detail.pl?biblionumber=5331",
        "official_source": 1,
    },
    # أطروحة دكتوراه — مصر/جنوب أفريقيا
    {
        "title": "المᎾرة الإلزامية في الدول الإسلامية مع التركيز على القانون المصري",
        "title_ar": "المᎾرة الإلزامية في الدول الإسلامية مع التركيز على القانون المصري",
        "author": "Dahbali",
        "book_type": "thesis",
        "legal_category": "personal_status",
        "description": "دراسة مقارنة للوية الإلزامية (وصية الجد المتوفى) في مصر والأردن ومالزيا مع التركيز على تطبيق القانون المصري رقم 71 لسنة 1946.",
        "year": 2025,
        "language": "ar",
        "source_name": "University of the Western Cape",
        "source_url": "https://hdl.handle.net/10566/24938",
        "official_source": 1,
    },
    # كتاب مرجعي — قانون مدني
    {
        "title": "الوسيط في شرح القانون المدني الجديد",
        "title_ar": "الوسيط في شرح القانون المدني الجديد",
        "author": "عبد الرزاق أحمد السنهوري",
        "book_type": "book",
        "legal_category": "civil",
        "description": "المرجع الأساسي في القانون المدني العربي — يتناول الملكية والالتزامات والعقود المدنية. منشور على Internet Archive.",
        "year": 1970,
        "language": "ar",
        "source_name": "Internet Archive (Alexandrina Collection)",
        "source_url": "https://archive.org/details/AAlexandrina-051220",
        "official_source": 1,
    },
    # كتاب مرجعي — أحكام الالتزام
    {
        "title": "أحكام الالتزام - آثار الحق في القانون المدني",
        "title_ar": "أحكام الالتزام - آثار الحق في القانون المدني",
        "author": "عبد القادر س미ح الفار",
        "book_type": "book",
        "legal_category": "civil",
        "description": "كتاب أكاديمي يتناول دراسة آثار الالتزام وأوصافه وانتقاله وانقضائه في القانون المدني — الطبعة السادسة والعشرين 2024.",
        "year": 2024,
        "language": "ar",
        "source_name": "دار الثقافة",
        "source_url": "https://daralthaqafa.com",
        "official_source": 1,
    },
    # قانون أصول المحاكمات الجزائية
    {
        "title": "قانون أصول المحاكمات الجزائية",
        "title_ar": "قانون أصول المحاكمات الجزائية 2025",
        "author": "الجمهورية الجزائرية",
        "book_type": "article",
        "legal_category": "criminal",
        "description": "نص قانون أصول المحاكمات الجزائية الجزائري وفق آخر تعديل 2025 مع شروح تفصيلية.",
        "year": 2025,
        "language": "ar",
        "source_name": "العبادي للمحاماة",
        "source_url": "https://www.alabbadilawfirm.com",
        "official_source": 1,
    },
    # كتاب قانون الأسرة الجزائري
    {
        "title": "كتاب قانون الأسرة الجزائري — دليل القاضي والمحامي",
        "title_ar": "كتاب قانون الأسرة الجزائري — دليل القاضي والمحامي مادة بمادة",
        "author": "مجموعة من المؤلفين",
        "book_type": "book",
        "legal_category": "personal_status",
        "description": "كتاب مرجعي في قانون الأسرة الجزائري مادة بمادة على ضوء أحكام الشريعة الإسلامية والاجتهاد القضائي.",
        "year": 2024,
        "language": "ar",
        "source_name": "Internet Archive",
        "source_url": "https://archive.org/details/20240412_20240412_1611",
        "official_source": 1,
    },
    # التشريع الجنائي
    {
        "title": "التشريع الجنائي — الجزء الأول",
        "title_ar": "التشريع الجنائي — الجزء الأول",
        "author": "مجموعة من المؤلفين",
        "book_type": "book",
        "legal_category": "criminal",
        "description": "كتاب في التشريع الجنائي الجزء الأول — المبادئ العامة للتجريم والعقاب. منشور على دار الكتاب العربي.",
        "year": 2022,
        "language": "ar",
        "source_name": "المكتبة القانونية",
        "source_url": "https://www.aljawadain.org/library/books/single?book_id=923",
        "official_source": 1,
    },
    # الواضح في شرح القانون المدني
    {
        "title": "الواضح في شرح القانون المدني — مصادر الالتزام",
        "title_ar": "الواضح في شرح القانون maduras",
        "author": "محمد صبري السعدي",
        "book_type": "book",
        "legal_category": "civil",
        "description": "كتاب أكاديمي شامل في شرح النظرية العامة للالتزامات — مصادر الالتزام والعقد والإرادة المنفردة مع دراسة مقارنة.",
        "year": 2025,
        "language": "ar",
        "source_name": "milaff.com",
        "source_url": "https://milaff.com/6685/",
        "official_source": 1,
    },
    # الدليل الإلكتروني ووسائل إثباته
    {
        "title": "الدليل الإلكتروني ووسائل إثباته — مذكرة ماستر",
        "title_ar": "الدليل الإلكتروني ووسائل إثباته — رسالة ماستر في القانون القضائي الجزائري",
        "author": "مناد مصطفى لعيمش غزالة",
        "book_type": "thesis",
        "legal_category": "administrative",
        "description": "رسالة ماستر في القانون القضائي الجزائري تتناول الدليل الإلكتروني وأحكام الإثبات الإلكترونية وفق القانون 04-15 لسنة 2015.",
        "year": 2024,
        "language": "ar",
        "source_name": "جامعة مولود م.memories Mostaganem",
        "source_url": "https://e-biblio.univ-mosta.dz",
        "official_source": 1,
    },
    # أحكام القانون الجنائي في الفقه الإباضي
    {
        "title": "أحكام القانون الجنائي في الفقه الإباضي",
        "title_ar": "أحكام القانون الجنائي في الفقه الإباضي",
        "author": "مجموعة من المؤلفين",
        "book_type": "book",
        "legal_category": "criminal",
        "description": "كتاب شامل في المبادئ العامة للتجريم والعقاب والجريمة والعقوبة في الفقه الإباضي — يتضمن المسؤولية الجنائية والمشاركة والجنايات الدولية.",
        "year": 2020,
        "language": "ar",
        "source_name": "المكتبة السعيدية",
        "source_url": "https://alsaidia.com/node/573",
        "official_source": 1,
    },
    # Copyright and Metaverse
    {
        "title": "Copyright Law and Metaverse: Egyptian Copyright Law in the Virtual Era",
        "author": "Ayat Khalaf",
        "book_type": "dissertation",
        "legal_category": "commercial",
        "description": "دراسة مقارنة لتحديات وفرص قانون حقوق النشر المصري في عصر الميتافيرس — أطروحة ماجستير، الجامعة الأمريكية بالقاهرة 2025.",
        "year": 2025,
        "language": "en",
        "source_name": "AUC Knowledge Fountain",
        "source_url": "https://fount.aucegypt.edu/cgi/viewcontent.cgi?article=3406&context=etds",
        "official_source": 1,
    },
    # Domestic Violence Egypt
    {
        "title": "Criminalizing Domestic Violence in Egypt: Legal Gaps and Reform",
        "author": "Ahmed Hussein",
        "book_type": "dissertation",
        "legal_category": "personal_status",
        "description": "دراسة تحليلية للثغرات القانونية في تجريم العنف الأسري في مصر — أطروحة ماجستير، الجامعة الأمريكية بالقاهرة 2025.",
        "year": 2025,
        "language": "en",
        "source_name": "AUC Knowledge Fountain",
        "source_url": "https://fount.aucegypt.edu/cgi/viewcontent.cgi?article=3506&context=etds",
        "official_source": 1,
    },
    # Constitutional Law Egypt
    {
        "title": "Egyptian Public Economic Policies Between the Supreme Constitutional Court and the State",
        "author": "Dina Sherif Abdelrahman",
        "book_type": "dissertation",
        "legal_category": "constitutional",
        "description": "دراسة عن العلاقة بين المحكمة الدستورية العليا والسلطة التنفيذية في السياسات الاقتصادية العامة المصرية منذ 1952 — أطروحة ماجستير 2025.",
        "year": 2025,
        "language": "en",
        "source_name": "AUC Knowledge Fountain",
        "source_url": "https://fount.aucegypt.edu/cgi/viewcontent.cgi?article=3598&context=etds",
        "official_source": 1,
    },
    # Legal Modernism Egypt
    {
        "title": "Egypt's Legal Modernism: Challenging the National Discourse",
        "author": "Mohamed A. El-Deeb",
        "book_type": "dissertation",
        "legal_category": "constitutional",
        "description": "بحث يتناول التاريخ القانوني الحديث لمصر من إصلاحات judiciary في القرن التاسع عشر一直到 قضايا الهوية — أطروحة ماجستير 2024.",
        "year": 2024,
        "language": "en",
        "source_name": "AUC Knowledge Fountain",
        "source_url": "https://fount.aucegypt.edu/cgi/viewcontent.cgi?article=3403&context=etds",
        "official_source": 1,
    },
]


def main():
    count = 0
    with db_session() as conn:
        for book in BOOKS:
            ch = hashlib.sha256(
                (book.get("title", "") + book.get("author", "")).encode("utf-8")
            ).hexdigest()
            existing = conn.execute(
                "SELECT id FROM research_books WHERE content_hash = ?", (ch,)
            ).fetchone()
            if existing:
                print(f"  [موجود] #{existing['id']}: {book['title'][:60]}")
                continue
            cur = conn.execute(
                """INSERT INTO research_books
                (title, title_ar, author, book_type, legal_category, description,
                 file_path, file_name, file_size, pages, year, language,
                 source_name, source_url, official_source, content_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    book["title"], book.get("title_ar"), book.get("author"),
                    book.get("book_type", "book"), book.get("legal_category", "general"),
                    book.get("description"), book.get("file_path"), book.get("file_name"),
                    book.get("file_size"), book.get("pages"), book.get("year"),
                    book.get("language", "ar"), book.get("source_name"), book.get("source_url"),
                    book.get("official_source", 0), ch,
                ),
            )
            count += 1
            print(f"  [جديد] #{cur.lastrowid}: {book['title'][:60]}")

    total = count
    print(f"\n✅ تم إضافة {count} كتاب | الإجمالي: {total}")


if __name__ == "__main__":
    main()
