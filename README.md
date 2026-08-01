# نبراس — Backend (المكتبة القانونية والبحث)

خادم API مبني بـ **Flask + SQLite (FTS5)** يخدم المكتبة القانونية ومحرك البحث النصي الكامل
للواجهة الأمامية لمنصة نبراس. تم اختيار Flask + SQLite لأنهما جاهزان فورًا بدون تبعيات خارجية
(SQLite ملف واحد، لا حاجة لخادم قاعدة بيانات منفصل)، مع بنية معزولة (database / services / routes)
تسمح بالانتقال لاحقًا إلى PostgreSQL أو FastAPI دون إعادة كتابة منطق العمل.

> ⚠️ **تنبيه مهم**: البيانات القانونية المضمّنة في `app/seed.py` نموذجية ومبسّطة لأغراض
> العرض التقني فقط (`is_sample_data=1`)، وقد لا تعكس آخر التعديلات الرسمية. في نسخة
> الإنتاج، يجب تغذية المكتبة حصرًا من مصادر رسمية موثّقة (الجريدة الرسمية، الأمانة العامة
> للحكومة...) قبل تصنيفها كمحتوى موثّق (`is_sample_data=0`).

## البنية

```
nibras-backend/
├── app/
│   ├── __init__.py         # create_app(): مصنع التطبيق (health, CORS, Blueprints, init_db)
│   ├── config.py           # إعدادات البيئة (DEBUG, CORS, JWT, معدل الطلبات)
│   ├── database.py         # مخطط SQLite + FTS5 + جداول الهوية والأدوار
│   ├── seed.py             # بيانات نموذجية (دستور، مدونات، قوانين + مواد فعلية)
│   ├── services.py         # منطق المكتبة (معزول عن HTTP)
│   ├── services_auth.py    # منطق المصادقة: argon2id, JWT, refresh, استعادة كلمة المرور
│   ├── services_admin.py   # منطق لوحة الإدارة: إدارة المحتوى + طابور التحقق + التدقيق
│   ├── services_calculators.py # الحاسبات القانونية (حاسبة الإرث — الفرائض)
│   ├── services_procedures.py  # مساعد المساطر + تتبع تقدم المستخدم
│   ├── services_ai.py          # واجهة الذكاء الاصطناعي (موجَّه + تعليم عام)
│   ├── create_admin.py     # CLI إنشاء أول حساب مسؤول (python -m app.create_admin)
│   ├── middleware/
│   │   └── auth_middleware.py  # require_auth و require_role(*roles)
│   └── routes/
│       ├── library.py      # نقاط نهاية المكتبة العامة (Blueprint)
│       ├── admin.py        # نقاط نهاية الإدارة — محمية بـ require_role("admin")
│       ├── auth.py         # نقاط نهاية المصادقة (Blueprint)
│       ├── calculators.py  # نقاط نهاية الحاسبات القانونية (Blueprint)
│       ├── procedures.py   # نقاط نهاية المساطر وتقدمها (Blueprint)
│       └── ai.py           # نقاط نهاية واجهة الذكاء الاصطناعي (Blueprint)
├── admin.html           # لوحة إدارة داخلية مستقلة (دخول + محتوى + طابور التحقق)
├── tests/               # اختبارات الوحدة والتكامل (pytest)
├── scripts/run_checks.py # بوابة الفحص المحلية (ruff + pytest)
├── run.py              # نقطة تشغيل الخادم
├── requirements.txt
└── requirements-dev.txt # تبعيات التطوير (pytest, ruff)
```

## الاختبارات والفحص

```bash
pip install -r requirements-dev.txt   # تبعيات التطوير
python scripts/run_checks.py          # بوابة الفحص: lint + كامل الاختبارات
python -m pytest -q                    # الاختبارات مباشرة
```

## إعدادات البيئة (كلها اختيارية للتطوير المحلي)

| المتغير | الافتراضي | المعنى |
|---|---|---|
| `NIBRAS_DEBUG` | `0` | تفعيل وضع تصحيح Werkzeug محليًا (`1`). **مُعطَّل افتراضيًا**. |
| `NIBRAS_CORS_ORIGINS` | نطاقات محلية + `null` | النطاقات المسموح لها قراءة الـ API (قائمة مفصولة بفواصل). في الإنتاج: النطاقات الفعلية فقط. |
| `NIBRAS_JWT_SECRET` | (سر عشوائي لكل إقلاع) | سر توقيع JWT. **إلزامي ثابت في الإنتاج** — بدونه تنتهي الجلسات عند كل إعادة تشغيل. |
| `NIBRAS_ACCESS_TOKEN_TTL_MINUTES` | `15` | عمر توكن الوصول (JWT) بالدقائق. |
| `NIBRAS_REFRESH_TOKEN_TTL_DAYS` | `30` | عمر توكن التحديث بالأيام. |
| `NIBRAS_PASSWORD_RESET_TOKEN_TTL_HOURS` | `1` | عمر رابط استعادة كلمة المرور بالساعات. |
| `NIBRAS_RATE_LIMIT_MAX_ATTEMPTS` | `5` | حد المحاولات على نقاط المصادقة والاستعادة. |
| `NIBRAS_RATE_LIMIT_WINDOW_SECONDS` | `900` | نافذة حد المحاولات بالثواني. |
| `NIBRAS_FRONTEND_BASE_URL` | `http://localhost:3000` | أساس رابط استعادة كلمة المرور في البريد. |
| `NIBRAS_AI_PROVIDER` | `noop` | مزوّد الذكاء الاصطناعي: `noop` (تطوير حتمي بلا شبكة) أو `anthropic`. |
| `ANTHROPIC_API_KEY` | (فارغ) | مفتاح Anthropic API — إلزامي عند ضبط `NIBRAS_AI_PROVIDER=anthropic`. |
| `NIBRAS_AI_MODEL` | `claude-sonnet-4-5` | نموذج Anthropic المستخدم. |
| `NIBRAS_AI_MAX_TOKENS` | `1024` | الحد الأقصى لرموز الرد. |
| `NIBRAS_AI_RETRIEVAL_LIMIT` | `5` | عدد المواد المسترجعة لبناء سياق الرد الموجَّه. |
| `NIBRAS_AI_RATE_LIMIT_MAX_REQUESTS` | `20` | حد طلبات `/api/ai/explain` لكل مستخدم لكل نافذة. |
| `NIBRAS_AI_RATE_LIMIT_WINDOW_SECONDS` | `3600` | نافذة حد طلبات الذكاء الاصطناعي بالثواني. |

## التشغيل

```bash
pip install -r requirements.txt
python3 -m app.seed        # تعبئة قاعدة البيانات (مرة واحدة، أو عند الحاجة لإعادة التصفير)
python3 run.py              # يشتغل على http://localhost:8000
```

## نقاط النهاية (API Endpoints)

| الطريقة | المسار | الوصف |
|---|---|---|
| GET | `/api/health` | فحص حالة الخادم |
| GET | `/api/categories` | قائمة الفروع القانونية |
| GET | `/api/texts?category=&type=` | قائمة النصوص القانونية (قابلة للتصفية) |
| GET | `/api/texts/<id>` | تفاصيل نص قانوني + قائمة مواده |
| GET | `/api/articles/<id>` | تفاصيل مادة + المواد ذات الصلة |
| GET | `/api/search?q=...&limit=20` | بحث نصي كامل (FTS5) في المواد |
| POST | `/api/auth/register` | تسجيل مستخدم (role اختياري، افتراضي citizen) — يرفض admin |
| POST | `/api/auth/login` | دخول (بريد + كلمة مرور) → JWT + refresh |
| POST | `/api/auth/refresh` | تدوير توكن التحديث → زوج جديد |
| POST | `/api/auth/logout` | إبطال توكن التحديث (يتطلب JWT) |
| GET | `/api/auth/me` | ملف المستخدم الحالي (يتطلب JWT) |
| POST | `/api/auth/password-reset/request` | طلب رابط استعادة (رسالة موحدة لا تكشف البريد) |
| POST | `/api/auth/password-reset/confirm` | تطبيق كلمة مرور جديدة بالتوكن |
| POST | `/api/admin/texts` | إنشاء نص قانوني جديد (يتطلب دور `admin`) |
| PUT | `/api/admin/texts/<id>` | تعديل نص قانوني (يتطلب دور `admin`) |
| DELETE | `/api/admin/texts/<id>` | حذف نص قانوني مع مواده تسلسليًا (يتطلب دور `admin`) |
| POST | `/api/admin/texts/<id>/articles` | إضافة مادة لنص قانوني (يتطلب دور `admin`) |
| PUT | `/api/admin/articles/<id>` | تعديل مادة (يتطلب دور `admin`) |
| DELETE | `/api/admin/articles/<id>` | حذف مادة (يتطلب دور `admin`) |
| GET | `/api/admin/verification-queue` | طلبات التحقق المهنية في الانتظار (يتطلب دور `admin`) |
| POST | `/api/admin/verification/<user_id>/approve` | قبول طلب تحقق وتفعيل الدور (يتطلب دور `admin`) |
| POST | `/api/admin/verification/<user_id>/reject` | رفض طلب تحقق مع سبب مطلوب (يتطلب دور `admin`) |
| GET | `/api/calculators` | قائمة الحاسبات القانونية المتاحة |
| POST | `/api/calculators/<slug>/run` | تنفيذ حاسبة (مثلًا `inheritance`) — المدخلات/المخرجات JSON |
| GET | `/api/procedures?category=` | قائمة مساطر الحياة (تصفية اختيارية حسب الفئة) |
| GET | `/api/procedures/<slug>` | تفاصيل مسطرة + خطواتها مرتبة |
| POST | `/api/procedures/<slug>/progress` | تحديث تقدم خطوة (يتطلب JWT) |
| POST | `/api/ai/explain` | شرح موجَّه من المواد المسترجعة أو تعليم عام (يتطلب JWT + حد معدل) |

مثال تنفيذ حاسبة الإرث (زوجة + ابن، تركة 120000):
```bash
curl -X POST http://localhost:8000/api/calculators/inheritance/run \
  -H "Content-Type: application/json" \
  -d '{"estate_value": 120000, "spouse": "wife", "sons": 1}'
```

مثال شرح موجَّه (يتطلب التوكن):
```bash
curl -X POST http://localhost:8000/api/ai/explain \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <JWT>" \
  -d '{"question": "ماذا يقع للزوجة عند وجود أبناء؟", "mode": "grounded"}'
```

كل إجراء إداري (إنشاء/تعديل/حذف محتوى، قبول/رفض تحقق) يُسجَّل في `admin_audit_log`
(المسؤول، الفعل، الهدف، التوقيت) وفق Security Architecture §8.

مثال بحث:
```bash
curl "http://localhost:8000/api/search?q=عقد"
```

المسارات الإدارية محمية بدور `admin` عبر `Authorization: Bearer <JWT>`. لإنشاء أول
حساب مسؤول (دور admin لا يُمنح عبر التسجيل العام):
```bash
export NIBRAS_ADMIN_EMAIL="admin@nibras.ma"
export NIBRAS_ADMIN_PASSWORD="كلمة-مرور-قوية-طويلة"
python -m app.create_admin
```

مثال إضافة محتوى بعد الحصول على التوكن:
```bash
curl -X POST http://localhost:8000/api/admin/texts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <JWT>" \
  -d '{"category_id": 2, "type": "law", "title": "قانون جديد"}'
```

## ربط الواجهة الأمامية

ملف `nibras.html` (الواجهة الأمامية) يتصل تلقائيًا بـ `http://localhost:8000/api`
عند فتحه في المتصفح. لتفعيل البيانات الحية بدل النص التوضيحي الاحتياطي:

1. شغّل الـ backend حسب التعليمات أعلاه (`python3 run.py`).
2. افتح `nibras.html` مباشرة في المتصفح (بالنقر المزدوج، أو بسحبه إليه).
3. سيظهر شريط أخضر أعلى قسم "المستكشف الذكي" يؤكد الاتصال، وستتحمّل
   المكتبة القانونية وصندوق البحث بيانات حقيقية من قاعدة البيانات.

إن كان الخادم متوقفًا، تعرض الواجهة تلقائيًا نصًا احتياطيًا مع شريط أحمر
يوضّح أن البيانات توضيحية فقط — الموقع لا يتعطّل، بل يتدهور بأمان (graceful degradation).

> عند النشر الفعلي على الإنترنت، يجب استبدال `http://localhost:8000/api`
> في `nibras.html` برابط الخادم المنشور فعليًا (مثلًا `https://api.nibras.ma/api`).

### لوحة الإدارة (`admin.html`)

أداة داخلية مستقلة (Admin Panel Spec §5) تتصل بالـ API نفسه وتحمل عنوانه في
`API_BASE`. تتيح تسجيل الدخول بحساب مسؤول ثم:

- **إدارة المحتوى**: عرض/إنشاء/تعديل/حذف النصوص القانونية وموادها.
- **طابور التحقق**: عرض طلبات الأدوار المهنية في الانتظار وقبولها أو رفضها
  مع سبب إلزامي يُحفظ.

تُفتح مباشرة في المتصفح بجانب الخادم المشغّل (`python3 run.py`) بنفس طريقة
`nibras.html`. تُستبدل قيمة `API_BASE` بالرابط المنشور عند النشر الفعلي.

## لماذا Flask بدل FastAPI؟

طُلب اختيار الأنسب. اعتمدنا Flask لأن تبعياته (أساسية/مكتبة/JWT) خفيفة ومتوافقة
مع بيئة التشغيل، ولأنه كان أساس خط الأساس المراجع (Extend, don't rewrite)، وقد
جُرِّبت كل نقاط النهاية وتعمل فعليًا. الكود منظم بشكل يسهّل الانتقال إلى FastAPI
لاحقًا إن رغبت (خاصة عند إضافة توثيق تلقائي للـ API أو معالجة غير متزامنة لمحرك
الذكاء الاصطناعي).

## الخطوات التالية المقترحة (بحسب رؤية نبراس)

1. **تفعيل الاستشعار الفعلي**: واجهة الذكاء الاصطناعي جاهزة (استرجاع ثم توليد موجَّه
   مع استشهاد حصري بالمسترجَع)، وتبقى خطوة ربطها بمزوّد Anthropic حقيقي
   (`NIBRAS_AI_PROVIDER=anthropic` + `ANTHROPIC_API_KEY`) وضبط prompts حسب النتائج.
2. **محرك رفع المستندات**: نقطة نهاية لرفع PDF/DOCX وتحويلها تلقائيًا لمواد مفهرَسة
   (يتطلب مكتبة استخراج نصوص + معالجة غير متزامنة).
3. **الترقية لقاعدة بيانات إنتاجية**: PostgreSQL مع امتداد بحث نصي عربي (pg_trgm أو
   Elasticsearch) عند نمو الحجم.
4. **مزيد من الحاسبات القانونية**: حاسبة الإرث شغّالة (الفروض، العول، الرد، التعصيب،
   الحجب)، وتُضاف حاسبات أخرى (الطلاق، التعويض...) بنفس نمط الحاسبة المفردة.
