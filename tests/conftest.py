"""
إعداد الاختبارات المشترك لمنصة نبراس.

عزل قاعدة البيانات: تُوجَّه DB_PATH إلى ملف مؤقت لكل اختبار، فتُبنى
المكتبة النموذجية بأمان دون المساس بـ nibras.db الحقيقية، وفق Testing
Strategy (§2) واستخدام علامة is_sample_data للبيانات النموذجية (§3).
"""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app import database
from app.database import db_session
from app.routes.auth import _attempts as _auth_attempts


@pytest.fixture(autouse=True)
def _clear_auth_rate_limits():
    """ينظف حدود المعدل قبل كل اختبار لمنع التراكم بين الاختبارات."""
    _auth_attempts.clear()
    yield
    _auth_attempts.clear()


def _seed_test_data():
    """بيانات تحكم صغيرة تُغطي سلوك المكتبة (كلها is_sample_data=1)."""
    with db_session() as conn:
        cat_madani = conn.execute(
            "INSERT INTO categories (slug, name, description) VALUES (?,?,?)",
            ("madani", "القانون المدني", "الالتزامات والعقود"),
        ).lastrowid
        cat_usra = conn.execute(
            "INSERT INTO categories (slug, name, description) VALUES (?,?,?)",
            ("usra", "قانون الأسرة", "الزواج والطلاق"),
        ).lastrowid

        doc_cod = conn.execute(
            """INSERT INTO legal_texts
               (category_id, type, title, official_ref, enacted_date, source_note, is_sample_data)
               VALUES (?,?,?,?,?,?,1)""",
            (cat_madani, "code", "قانون الالتزامات والعقود", "ظهير 12 غشت 1913",
             "1913-08-12", "مصدر نموذجي"),
        ).lastrowid
        doc_usra = conn.execute(
            """INSERT INTO legal_texts
               (category_id, type, title, official_ref, enacted_date, source_note, is_sample_data)
               VALUES (?,?,?,?,?,?,1)""",
            (cat_usra, "code", "مدونة الأسرة", "ظهير 1.04.22",
             "2004-02-03", "مصدر نموذجي"),
        ).lastrowid

        art_230 = conn.execute(
            """INSERT INTO articles
               (legal_text_id, number, label, content, plain_explanation, keywords)
               VALUES (?,?,?,?,?,?)""",
            (doc_cod, "230", "المادة 230",
             "الالتزامات التعاقدية المنشأة على وجه صحيح تقوم مقام القانون بالنسبة لمنشئيها.",
             "مبدأ العقد شريعة المتعاقدين.",
             "عقد,التزام,رضائية"),
        ).lastrowid
        art_49 = conn.execute(
            """INSERT INTO articles
               (legal_text_id, number, label, content, plain_explanation, keywords)
               VALUES (?,?,?,?,?,?)""",
            (doc_usra, "49", "المادة 49",
             "لكل واحد من الزوجين ذمة مالية مستقلة عن ذمة الزوج الآخر.",
             "استقلال الذمة المالية للزوجين.",
             "ذمة مالية,زواج"),
        ).lastrowid

        conn.execute(
            "INSERT INTO related_articles (article_id, related_article_id) VALUES (?,?)",
            (art_230, art_49),
        )
        conn.execute(
            "INSERT INTO related_articles (article_id, related_article_id) VALUES (?,?)",
            (art_49, art_230),
        )

        # اجتهادات قضائية نموذجية — مستخدمة في اختبارات المساعد (فقه قضائي)
        jcat = conn.execute(
            "INSERT INTO jurisprudence_categories (slug, name) VALUES (?,?)",
            ("test-jinaiya", "قانون المسطرة الجنائية (اختبار)"),
        ).lastrowid
        conn.execute(
            """INSERT INTO jurisprudence
               (category_id, title, principles, content, court, decision_number,
                decision_date, source_note, published, views, tenant_id)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (jcat, "طلب النقض من حكم غيابي - تعذر عشرية الاستئناف",
             "القرار المطعون فيه الصادر غيابيا يقبل التعرض",
             (
                 "بمقتضى المادة 521 من قانون المسطرة الجنائية، فإنه لا يصح أن يطعن "
                 "بطريق المطالبة بالنقض إلا في الأحكام الصادرة بصفة نهائية، ولما كان "
                 "الحكم المطعون فيه صدر غيابيا فهو قابل للطعن بطريق التعرض."
             ),
             "محكمة النقض", "2021/158", "2021-01-19",
             "قرار محكمة النقض", 1, 0, None),
        )
        conn.execute(
            """INSERT INTO jurisprudence
               (category_id, title, principles, content, court, decision_number,
                decision_date, source_note, published, views, tenant_id)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (jcat, "طلب النقض - أجل الطعن",
             "الطعن بالنقض يخضع لأجل محدد",
             (
                 "يجب تقديم طلب النقض داخل الأجل القانوني، وأن مخالفة الأجل تجعل الطعن "
                 "غير مقبول."
             ),
             "محكمة النقض", "2021/119", "2021-01-19",
             "قرار محكمة النقض", 1, 0, None),
        )
        conn.execute(
            """INSERT INTO jurisprudence
               (category_id, title, principles, content, court, decision_number,
                decision_date, source_note, published, views, tenant_id)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (jcat, "مبدأ التعرض أمام المحكمة الابتدائية",
             "التعرض وسيلة طعن عادية",
             "التعرض هو وسيلة عادية للطعن، ويُقبل من المحكوم عليه غيابيا.",
             "محكمة النقض", "2021/173", "2021-01-19",
             "قرار محكمة النقض", 1, 0, None),
        )


@pytest.fixture()
def fresh_db(tmp_path):
    """قاعدة بيانات مؤقتة معزولة مع البيانات النموذجية أعلاه."""
    db_path = tmp_path / "test_nibras.db"
    old = database.DB_PATH
    database.DB_PATH = db_path
    database.init_db(reset=True)
    _seed_test_data()
    yield db_path
    database.DB_PATH = old


@pytest.fixture()
def app(fresh_db):
    from app import create_app

    application = create_app()
    application.config["TESTING"] = True
    return application


@pytest.fixture()
def client(app):
    return app.test_client()
