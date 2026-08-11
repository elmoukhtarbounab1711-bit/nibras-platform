"""
تعبئة قاعدة البيانات ببيانات نموذجية للعرض التوضيحي.

تنبيه مهم: النصوص أدناه مبسّطة/نموذجية لأغراض العرض التقني فقط،
وقد لا تعكس آخر التعديلات الرسمية. في نسخة الإنتاج، يجب أن تُغذّى
المكتبة القانونية حصرًا من مصادر رسمية موثّقة (الجريدة الرسمية،
الأمانة العامة للحكومة...)، مع تسجيل is_sample_data=0 بعد التحقق.
"""
from . import config, tenant_scope
from .database import db_session, init_db

CATEGORIES = [
    ("dostouri", "القانون الدستوري", "النصوص المؤسِّسة والحقوق والحريات الأساسية"),
    ("madani", "القانون المدني", "الالتزامات، العقود، الملكية"),
    ("usra", "قانون الأسرة", "الزواج، الطلاق، النفقة، الإرث"),
    ("jinai", "القانون الجنائي", "الجرائم والعقوبات والمسطرة الجنائية"),
    ("shughl", "قانون الشغل", "علاقات العمل وحقوق الأجراء"),
    ("tijari", "القانون التجاري", "الشركات والمعاملات التجارية"),
]

TEXTS = [
    # (category_slug, type, title, official_ref, enacted_date, source_note, description, issuing_body)
    ("dostouri", "constitution", "الدستور المغربي", "ظهير 1.11.91", "2011-07-29",
     "دستور المملكة المغربية الصادر بتنفيذه الظهير الشريف رقم 1.11.91",
     "النص التأسيسي الذي يحدد نظام الحكم بالمملكة وطبيعة المؤسسات وحقوق المواطنين والحريات الأساسية.",
     "المجلس الدستوري / الجريدة الرسمية"),
    ("madani", "code", "قانون الالتزامات والعقود", "ظهير 12 غشت 1913", "1913-08-12",
     "أحد أقدم النصوص المنظِّمة للمعاملات المدنية في المغرب",
     "يُنظّم الالتزامات والعقود والملكية بكل صورها، وهو الإطار المرجعي للمعاملات المدنية والتجارية.",
     "الجريدة الرسمية"),
    ("usra", "code", "مدونة الأسرة", "ظهير 1.04.22", "2004-02-03",
     "المدونة المنظِّمة لأحكام الأسرة والزواج والطلاق والإرث",
     "تُنظّم أحكام الأسرة من زواج وطلاق ونفقة وحضانة وإرث، وفق مقتضيات حديثة تراعي التوازن بين الطرفين.",
     "الجريدة الرسمية"),
    ("jinai", "code", "القانون الجنائي", "ظهير 1.59.413", "1962-11-26",
     "مجموعة النصوص الزجرية الأساسية في المغرب",
     "يحدد الجرائم والعقوبات المطبقة عليها وفق مبدأ الشرعية الجنائية.",
     "الجريدة الرسمية"),
    ("shughl", "code", "مدونة الشغل", "ظهير 1.03.194", "2004-05-11",
     "المدونة المنظِّمة لعلاقات الشغل بين الأجراء والمشغّلين",
     "تُنظّم عقد الشغل وشروطه وواجبات الأجراء والمشغلين وإنهاء العلاقة الشغلية.",
     "الجريدة الرسمية"),
]

# (text_title, number, label, content, plain_explanation, keywords)
ARTICLES = [
    ("قانون الالتزامات والعقود", "230", "المادة 230",
     "الالتزامات التعاقدية المنشأة على وجه صحيح تقوم مقام القانون بالنسبة لمنشئيها، ولا يجوز إلغاؤها إلا برضاهما معا أو في الحالات المنصوص عليها في القانون.",
     "هذه المادة تُرسي مبدأ 'العقد شريعة المتعاقدين': ما يتفق عليه الطرفان في عقد صحيح يصبح ملزِمًا لهما كأنه نص قانوني، ولا يمكن لأحدهما التراجع عنه منفردًا إلا في حالات استثنائية يحددها القانون.",
     "عقد,التزام,رضائية,فسخ"),
    ("قانون الالتزامات والعقود", "231", "المادة 231",
     "كل التزام يجب تنفيذه بحسن نية، ويلزم بما وقع التصريح به، وبجميع ملحقاته التي يقررها القانون أو العرف أو الإنصاف طبقا لنوع الالتزام.",
     "تفرض هذه المادة على أطراف العقد الالتزام بمبدأ حسن النية أثناء التنفيذ، ولا يقتصر الالتزام على الحرف المكتوب فقط بل يمتد إلى ما يقتضيه العرف والإنصاف.",
     "حسن نية,تنفيذ العقد,عرف"),
    ("مدونة الأسرة", "49", "المادة 49",
     "لكل واحد من الزوجين ذمة مالية مستقلة عن ذمة الزوج الآخر. غير أنه يجوز للزوجين في إطار تدبير الأموال المكتسبة أثناء قيام الزوجية، الاتفاق على استثمار الأموال التي ستكتسب أثناء الزوجية وتوزيعها.",
     "تحافظ هذه المادة على استقلال الذمة المالية لكل من الزوجين، لكنها تتيح لهما الاتفاق مسبقًا في وثيقة مستقلة عن عقد الزواج على طريقة تدبير الأموال التي يكتسبانها معًا خلال الحياة الزوجية.",
     "ذمة مالية,زواج,أموال مكتسبة"),
    ("مدونة الأسرة", "4", "المادة 4",
     "الزواج ميثاق تراض وترابط شرعي بين رجل وامرأة على وجه الدوام، غايته الإحصان والعفاف وإنشاء أسرة مستقرة برعاية الزوجين.",
     "تُعرّف هذه المادة الزواج بوصفه ميثاقًا رضائيًا بين طرفين، هدفه بناء أسرة مستقرة، وتُبرز الطابع التعاقدي إلى جانب البعد الاجتماعي للزواج في المنظومة القانونية المغربية.",
     "زواج,ميثاق,أسرة"),
    ("الدستور المغربي", "24", "الفصل 24",
     "لكل شخص الحق في حماية حياته الخاصة. لا يمكن انتهاك حرمة المنزل. لا تفتيش أو تحر إلا وفق الشروط والإجراءات التي ينص عليها القانون. تكون سرية الاتصالات الشخصية، أيا كان شكلها، مضمونة.",
     "يكفل هذا الفصل الحق في الحياة الخاصة وحرمة المسكن وسرية المراسلات والاتصالات، ولا يجوز المساس بها إلا وفق مسطرة قانونية محددة، ما يجعله ركيزة أساسية لحماية الحريات الفردية.",
     "حياة خاصة,حرمة المسكن,اتصالات"),
    ("الدستور المغربي", "1", "الفصل 1",
     "نظام الحكم بالمغرب نظام ملكية دستورية، ديمقراطية، برلمانية واجتماعية. يقوم النظام الدستوري للمملكة على أساس فصل السلط وتوازنها والتعاون فيما بينها، والديمقراطية المواطنة والتشاركية...",
     "يحدد هذا الفصل الطبيعة العامة للدولة المغربية ونظام حكمها القائم على فصل السلط وتوازنها، ويُعد من أهم الفصول التأسيسية في الدستور.",
     "نظام الحكم,فصل السلط,ملكية دستورية"),
    ("القانون الجنائي", "1", "المادة 1",
     "لا جريمة ولا عقوبة أو تدبير وقائي بغير قانون.",
     "تُرسي هذه المادة مبدأ الشرعية الجنائية: لا يُعاقَب أي شخص على فعل لم يُجرّمه القانون صراحة قبل ارتكابه، وهو أحد أهم الضمانات الدستورية للحرية الفردية.",
     "شرعية جنائية,عقوبة,جريمة"),
    ("مدونة الشغل", "9", "المادة 9",
     "يمنع كل تمييز بين الأجراء في الأجر أو التكوين أو الترقية أو الفصل من الشغل يقوم على أساس الجنس أو السن أو الوضعية الاجتماعية أو العرق أو اللون أو الأصل...",
     "تحظر هذه المادة أي تمييز بين الأجراء لأسباب غير موضوعية، وتشمل الحماية جوانب الأجر والترقية والتكوين والفصل من العمل.",
     "تمييز,أجراء,مساواة"),
]

RELATED = [
    # (رقم المادة، عنوان النص) -> (رقم المادة المرتبطة، عنوان النص المرتبط)
    (("230", "قانون الالتزامات والعقود"), ("231", "قانون الالتزامات والعقود")),
    (("230", "قانون الالتزامات والعقود"), ("1", "القانون الجنائي")),
    (("49", "مدونة الأسرة"), ("4", "مدونة الأسرة")),
    (("24", "الدستور المغربي"), ("1", "الدستور المغربي")),
]

# ---------------------------------------------------------------------------
# بيانات العرض التوضيحي لبوابة المقالات والنظام المهني (مرحلة الواجهة)
# ---------------------------------------------------------------------------

# (email, full_name, role, password) — تُنشأ أدوار مهنية بحالة pending ثم تُصدَّق
DEMO_USERS = [
    ("elmoukhtar.bounab1711@gmail.com", "إدارة منصة نبراس", "admin", "@#Nibras@#$"),
    ("lawyer@nibras.local", "ذ. سلمى الإدريسي", "lawyer", "NibrasDemo!2026"),
    ("citizen@nibras.local", "يوسف بنعلي", "citizen", "NibrasDemo!2026"),
]

# (slug, عنوان، مؤلِّف البريد، ملخص، جسم، كلمات مفتاحية، تصنيف slug، cover_hint)
BLOG_ARTICLES = [
    (
        "explanations",
        "شرح المادة 230 من قانون الالتزامات والعقود: العقد شريعة المتعاقدين",
        "lawyer@nibras.local",
        "كيف نفهم مبدأ قوة العقد الملزمة في القانون المغربي؟ شرح مبسط مع أمثلة عملية.",
        (
            "قاعدة العقد شريعة المتعاقدين هي حجر الزاوية في القانون المدني المغربي، "
            "وتتجلى في المادة 230 من قانون الالتزامات والعقود التي تجعل الالتزامات "
            "المنشأة على وجه صحيح تقوم مقام القانون بالنسبة لمنشئيها.\n\n"
            "عمليًا، هذا يعني أن ما يتفق عليه الطرفان في عقد صحيح يصبح ملزمًا لهما "
            "كأنه نص قانوني. لا يجوز لأي طرف التراجع عن التزامه منفردًا، ولا يمكن "
            "للعدالة التراجع عن التعهد إلا بموافقة الطرفين أو في الحالات التي "
            "يحددها القانون صراحة.\n\n"
            "يستثنى من ذلك عقود الإذعان والعقود التي قد يترتب عنها إخلال بالنظام "
            "العام، حيث تسهر المحاكم على حماية الطرف الضعيف. كما أن مبدأ حسن النية "
            "المنصوص عليه في المادة 231 يكمل هذه القاعدة ويوجب تنفيذ الالتزام "
            "بأمانة ووفق ما تقتضيه طبيعة التعامل.\n\n"
            "نصيحة عملية: عند تحرير أي عقد، احرص على صياغة شروط واضحة لا لبس فيها، "
            "وتوثيق الالتزامات المتبادلة، والاحتفاظ بنسخة موقعة. فالوضوح يمنع "
            "النزاعات ويجعل التنفيذ القضائي أسرع عند الحاجة."
        ),
        "عقد,التزامات,رضائية,تنفيذ",
        "#c9a227",
    ),
    (
        "guides",
        "دليل خطوات طلب النفقة أمام قاضي الأسرة بالمغرب",
        "citizen@nibras.local",
        "خطوات عملية لرفع دعوى النفقة: الوثائق المطلوبة، الجهة المختصة، والمسطرة أمام قاضي الأسرة.",
        (
            "طلب النفقة من الإجراءات التي تهم شريحة واسعة من الأسر المغربية. "
            "تبدأ المسطرة بجمع الوثائق الأساسية (عقد الزواج، دفتر الحالة العائلية، "
            "ووثائق قياس الحاجة)، ثم تحرير مقال الطلب وتوجيهه إلى قسم قضاء الأسرة "
            "بالمحكمة الابتدائية المختصة.\n\n"
            "تعقد المحكمة جلسة صلح يحدد خلالها القاضي نفقة مؤقتة عند الحاجة، "
            "قبل صدور الحكم النهائي بتحديد مبلغ النفقة الدوري وتواريخ الأداء. "
            "وتُحسب النفقة وفق قاعدة 'قدرة المنفق عليه وحاجة المستفيد'.\n\n"
            "في حال عدم الأداء، يمكن للمستفيد اللجوء إلى مسطرة التنفيذ، بما فيها "
            "الحجز على أموال المنفذ عليه، عملاً بقانون التنفيذ الجاري به العمل.\n\n"
            "ملاحظة: البيانات في هذا الدليل إرشادية عامة ولا تغني عن استشارة "
            "مهني قانوني مختص بحسب الحالة الخاصة."
        ),
        "نفقة,قاضي الأسرة,مسطرة,تنفيذ",
        "#1f3a93",
    ),
    (
        "opinions",
        "قوة الملزمية التنفيذية للشهادة العدلية في الممارسة القضائية",
        "lawyer@nibras.local",
        "تحليل للممارسة القضائية حول القيمة التنفيذية للشهادات العدلية ودور العدول في توثيق الحقوق.",
        (
            "الشهادة العدلية من أقدم وأهم أدوات التوثيق في المنظومة القانونية المغربية، "
            "وتُعد في كثير من الأحوال وثيقة تنفيذية لا تحتاج إلى حكم قضائي سابق "
            "لتصحيح حق من الحقوق.\n\n"
            "غير أن الممارسة القضائية أفرزت ضوابط هامة: فالشهادة العدلية لا تكتسب "
            "قوة تنفيذية كاملة إلا متى توفرت شروط موضوعية (سلامة التراضي، أهلية "
            "التصرف، وعدم مخالفة النظام العام) وشكلية (إجراءات التوثيق أمام عدلين).\n\n"
            "ينبغي على الموثقين والعدول التحقق من هوية الأطراف وملكية الحق موضوع "
            "التوثيق، لما لذلك من أثر مباشر على صحة الوثيقة وقابليتها للتنفيذ.\n\n"
            "نخلص إلى أن التوثيق العدلي يظل ركيزة الثقة في المعاملات المدنية، "
            "ويُستحسن للمواطنين تعزيز الوثائق العدلية بالشهود والقرائن المكملة "
            "كلما اقتضت الحالة ذلك."
        ),
        "شهادة عدلية,توثيق,تنفيذ,عدول",
        "#0f766e",
    ),
]

# قوالب سوق تجريبية (ملف PDF مبسط يُولَّد محليًا للتجربة فقط)
DEMO_TEMPLATES = [
    ("usra", "عقد زواج تفصيلي", "نموذج كامل لعقد الزواج وفق مدونة الأسرة مع بنود اختيارية.", 12000),
    ("madani", "عقد إيجار سكني", "عقد إيجار مبني للسكن مع شروط عامة وخصوصية وفاتورة مرافق.", 8000),
    ("shughl", "عقد عمل محدد المدة", "عقد شغل محدد المدة وفق أحكام مدونة الشغل مع لائحة المهام.", 10000),
]


def seed(reset: bool = True):
    init_db(reset=reset)
    # بيانات العرض تُنسب للمستأجر الافتراضي في الوضع المفعّل (D-036)
    if config.MULTI_TENANT:
        from .services_tenants import default_tenant_id

        seed_tenant_id = default_tenant_id()
    else:
        seed_tenant_id = tenant_scope.insert_tenant_id()
    with db_session() as conn:
        cat_ids = {}
        for slug, name, desc in CATEGORIES:
            cur = conn.execute(
                "INSERT INTO categories (slug, name, description, tenant_id) "
                "VALUES (?,?,?,?)",
                (slug, name, desc, seed_tenant_id),
            )
            cat_ids[slug] = cur.lastrowid

        text_ids = {}
        for cat_slug, ttype, title, ref, date, note, desc, issuer in TEXTS:
            cur = conn.execute(
                """INSERT INTO legal_texts
                   (category_id, type, title, official_ref, enacted_date, source_note,
                    description, issuing_body, is_sample_data, tenant_id)
                   VALUES (?,?,?,?,?,?,?,?,1,?)""",
                (cat_ids[cat_slug], ttype, title, ref, date, note, desc, issuer,
                 seed_tenant_id),
            )
            text_ids[title] = cur.lastrowid

        article_ids = {}
        for text_title, number, label, content, explanation, keywords in ARTICLES:
            cur = conn.execute(
                """INSERT INTO articles
                   (legal_text_id, number, label, content, plain_explanation, keywords, tenant_id)
                   VALUES (?,?,?,?,?,?,?)""",
                (text_ids[text_title], number, label, content, explanation, keywords,
                 seed_tenant_id),
            )
            article_ids[(number, text_title)] = cur.lastrowid

        for (a_num, a_text), (b_num, b_text) in RELATED:
            a_id = article_ids[(a_num, a_text)]
            b_id = article_ids[(b_num, b_text)]
            conn.execute(
                "INSERT OR IGNORE INTO related_articles (article_id, related_article_id) VALUES (?,?)",
                (a_id, b_id),
            )
            conn.execute(
                "INSERT OR IGNORE INTO related_articles (article_id, related_article_id) VALUES (?,?)",
                (b_id, a_id),
            )

        _seed_demo_users_and_content(conn, seed_tenant_id)

    print("✓ تمت تعبئة قاعدة البيانات ببيانات نموذجية بنجاح.")


def _seed_demo_users_and_content(conn, seed_tenant_id):
    """مستخدمون تجريبيون (مسؤول + محامٍ موثَّق + مواطن) ومقالات وقوالب عرض."""
    from .services_auth import hash_password

    role_ids = {
        row["code"]: row["id"]
        for row in conn.execute("SELECT id, code FROM roles").fetchall()
    }
    user_ids = {}
    for email, full_name, role, password in DEMO_USERS:
        if conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone():
            continue
        role_status = (
            "active"
            if role in ("citizen", "admin")
            else "pending_verification"
        )
        cur = conn.execute(
            "INSERT INTO users (email, full_name, password_hash, status, tenant_id)"
            " VALUES (?,?,?,?,?)",
            (email, full_name, hash_password(password), "active", seed_tenant_id),
        )
        conn.execute(
            "INSERT INTO user_roles (user_id, role_id, role_status) VALUES (?,?,?)",
            (cur.lastrowid, role_ids[role], role_status),
        )
        user_ids[email] = cur.lastrowid

    # ملف مهني موثَّق للمحامية (شارة "مهني موثق")
    lawyer_id = user_ids["lawyer@nibras.local"]
    profile_row = conn.execute(
        "SELECT id FROM professional_profiles WHERE user_id = ?", (lawyer_id,)
    ).fetchone()
    if profile_row is None:
        cur = conn.execute(
            """INSERT INTO professional_profiles
               (user_id, profession_type, bio, city, verification_status, phone,
                contact_preference, photo_url, registration_number, address, website,
                years_of_experience, work_hours, social_links, map_embed,
                tenant_id, created_at, updated_at)
               VALUES (?, ?, ?, ?, 'verified', ?, 'visible', ?, ?, ?, ?, ?, ?, ?, ?,
                       ?, datetime('now'), datetime('now'))""",
            (
                lawyer_id, "lawyer",
                (
                    "محامية بهيئة الدار البيضاء، متخصصة في قانون الأسرة والعقارات، "
                    "أكثر من عشر سنوات من الممارسة القضائية والتحكيم."
                ),
                "الدار البيضاء", "+212661000001",
                "https://ui-avatars.com/api/?name=Salma&background=1f3a93&color=fff",
                "1023", "شارع الزرقطوني، الدار البيضاء", "https://nibras.local/salma",
                12, "الاثنين - الجمعة: 9:00 - 18:00",
                '{"linkedin":"https://linkedin.com/in/salma-idrissi"}',
                "https://maps.google.com/?q=Casablanca", seed_tenant_id,
            ),
        )
        for specialty in ("قانون الأسرة", "العقارات", "التحكيم"):
            conn.execute(
                "INSERT INTO professional_specialties (profile_id, specialty, tenant_id) "
                "VALUES (?, ?, ?)",
                (cur.lastrowid, specialty, seed_tenant_id),
            )

    # مقالات بوابة المقالات (منشورة)
    cat_map = {row["slug"]: row["id"] for row in conn.execute(
        "SELECT id, slug FROM blog_categories"
    ).fetchall()}
    for cat_slug, title, author_email, summary, body, keywords, _cover in BLOG_ARTICLES:
        conn.execute(
            """INSERT INTO blog_articles
               (user_id, category_id, title, summary, body, keywords, status, views,
                published_at, tenant_id, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, 'published', 0, datetime('now', '-3 days'),
                       ?, datetime('now', '-3 days'), datetime('now', '-1 days'))""",
            (user_ids[author_email], cat_map[cat_slug], title, summary, body,
             keywords, seed_tenant_id),
        )

    # قوالب سوق تجريبية بملفات PDF مبسطة (للعرض فقط)
    cat_map = {row["slug"]: row["id"] for row in conn.execute(
        "SELECT id, slug FROM marketplace_categories"
    ).fetchall()}
    _seed_marketplace_templates(conn, seed_tenant_id, cat_map)


def _seed_marketplace_templates(conn, seed_tenant_id, cat_map):
    """قوالب سوق بملف PDF مبسّط (reportlab) — عينات للتجربة لا للاستخدام."""
    import secrets
    from pathlib import Path

    base = Path(__file__).resolve().parent.parent / "uploads" / "marketplace"
    base.mkdir(parents=True, exist_ok=True)
    for cat_slug, title, description, price in DEMO_TEMPLATES:
        storage_name = f"{secrets.token_urlsafe(12)}.pdf"
        try:
            _render_placeholder_pdf(base / storage_name, title)
        except Exception:  # noqa: BLE001 — فشل التوليد (مثل غياب خط عربي): ملف نصي احتياطي
            (base / storage_name).write_bytes(
                f"%PDF-1.4 placeholder {title}".encode("utf-8", "replace")
            )
        conn.execute(
            """INSERT INTO marketplace_templates
               (category_id, title, description, price_cents, storage_key,
                download_count, rating, image_url, tenant_id, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, 0, 4.6, NULL, ?, datetime('now'), datetime('now'))""",
            (cat_map[cat_slug], title, description, price, storage_name,
             seed_tenant_id),
        )


def _render_placeholder_pdf(path, title):
    """PDF عربي مبسّط (reportlab + reshaper/bidi) لعرض القالب التجريبي."""
    import arabic_reshaper
    from bidi.algorithm import get_display
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas as pdfcanvas

    def shaped(text):
        return get_display(arabic_reshaper.reshape(text))

    c = pdfcanvas.Canvas(str(path), pagesize=A4)
    _width, height = A4
    c.setFont("Helvetica", 12)
    c.drawString(40, height - 60, "NIBRAS - Modèle demo")
    try:
        c.setFont("Helvetica", 16)
        c.drawString(40, height - 100, shaped(title))
    except Exception:  # noqa: BLE001,S110 — فشل تشكيل/رسم العنوان: يُكمل بلا عنوان
        pass
    c.drawString(40, height - 140, shaped("نموذج تجريبي لأغراض العرض فقط"))
    c.drawString(40, height - 165, shaped("غير صالح للاستخدام القانوني الرسمي"))
    c.setFont("Helvetica", 9)
    c.drawString(40, 40, shaped("© منصة نبراس — نموذج تجريبي"))
    c.showPage()
    c.save()


if __name__ == "__main__":
    import sys

    # تجنّب انهيار الطباعة على وحدات تحكم لا تدعم UTF-8 (مثل Windows cp1252)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    seed(reset=True)
