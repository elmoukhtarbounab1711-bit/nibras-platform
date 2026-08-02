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
│   ├── services_documents.py   # مولّد الوثائق (قوالب + تحقق + توليد + تصدير PDF/DOCX)
│   ├── services_professionals.py # النظام البيئي المهني: دليل + ملفات + وثائق تحقق + تقييمات
│   ├── services_community.py     # المجتمع: منشورات + تعليقات + تفاعلات + بلاغات + إشراف
│   ├── services_marketplace.py   # سوق القوالب: كتالوج + إدارة قوالب/فئات + رفع/تنزيل الملف
│   ├── services_analytics.py     # لوحة التحليلات الإدارية: ملخص قراءة-فقط من جداول الوحدات القائمة
│   ├── services_ads.py           # نظام الإعلانات: خدمة فتحات + حملات (3 أنواع) + تتبع انطباع/نقرة
│   ├── services_ingestion.py     # محرك رفع المستندات: استخراج PDF/DOCX + تقسيم إلى مواد + فهرسة
│   ├── services_notifications.py # إشعارات داخل التطبيق: قائمة + تعليم مقروء + محفِّزات تلقائية
│   ├── create_admin.py     # CLI إنشاء أول حساب مسؤول (python -m app.create_admin)
│   ├── middleware/
│   │   └── auth_middleware.py  # require_auth و require_role(*roles)
│   └── routes/
│       ├── library.py      # نقاط نهاية المكتبة العامة (Blueprint)
│       ├── admin.py        # نقاط نهاية الإدارة — محمية بـ require_role("admin")
│       ├── auth.py         # نقاط نهاية المصادقة (Blueprint)
│       ├── calculators.py  # نقاط نهاية الحاسبات القانونية (Blueprint)
│       ├── procedures.py   # نقاط نهاية المساطر وتقدمها (Blueprint)
│       ├── ai.py           # نقاط نهاية واجهة الذكاء الاصطناعي (Blueprint)
│       ├── documents.py    # نقاط نهاية مولّد الوثائق (Blueprint)
│       ├── professionals.py # نقاط نهاية النظام البيئي المهني (Blueprint)
│       ├── community.py    # نقاط نهاية المجتمع والإشراف (Blueprint)
│       ├── marketplace.py  # نقاط نهاية سوق القوالب العامة (Blueprint)
│       ├── ads.py          # نقاط نهاية نظام الإعلانات العامة (Blueprint)
│       └── notifications.py # نقاط نهاية الإشعارات (Blueprint — خاصة بالمستخدم)
├── uploads/              # وثائق التحقق المهنية + ملفات قوالب السوق (مجلد محلي — يُنقل لمخزن كائنات لاحقًا)
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
| `NIBRAS_PDF_FONT` | (تلقائي) | مسار خط عربي لتصدير PDF — فارغ = حل تلقائي من مسارات شائعة (ويندوز Arial، لينكس Noto Naskh/Amiri). |
| `NIBRAS_DOC_RATE_LIMIT_MAX_REQUESTS` | `10` | حد توليد الوثائق لكل مستخدم لكل نافذة. |
| `NIBRAS_DOC_RATE_LIMIT_WINDOW_SECONDS` | `3600` | نافذة حد توليد الوثائق بالثواني. |
| `NIBRAS_UPLOAD_DIR` | (فارغ = `repo/uploads/`) | مجلد رفع وثائق التحقق المهنية (تخزين محلي ريثما يُنقل لمخزن كائنات). |
| `NIBRAS_MAX_UPLOAD_BYTES` | `5242880` (5MB) | الحد الأقصى لحجم وثيقة التحقق بالبايت. |
| `NIBRAS_COMMUNITY_RATE_LIMIT_MAX_REQUESTS` | `30` | حد إنشاء المنشورات/التعليقات لكل مستخدم لكل نافذة (مكافحة الإساءة). |
| `NIBRAS_COMMUNITY_RATE_LIMIT_WINDOW_SECONDS` | `3600` | نافذة حد كتابة المجتمع بالثواني. |
| `NIBRAS_AD_RATE_LIMIT_MAX_REQUESTS` | `100` | حد أحداث تتبع الإعلانات (انطباع/نقرة) لكل مفتاح (مستخدم نشط أو عنوان IP) لكل نافذة — منع تضخيم الإحصائيات. |
| `NIBRAS_AD_RATE_LIMIT_WINDOW_SECONDS` | `3600` | نافذة حد تتبع الإعلانات بالثواني. |
| `NIBRAS_INGESTION_MAX_BYTES` | `20971520` (20MB) | الحد الأقصى لحجم ملف المستند المستورد (نصوص قانونية أطول من وثائق التحقق). |
| `NIBRAS_INGESTION_MAX_ARTICLES` | `1000` | سقف المواد المستخرجة لكل استيعاب (حماية من ملف هائل). |
| `NIBRAS_INGESTION_SINGLE_ARTICLE_MAX_CHARS` | `4000` | سقف حروف "المادة الواحدة" الاحتياطية عند غياب عناوين مواد. |
| `NIBRAS_LOG_LEVEL` | `INFO` | مستوى سجل الجذر (DEBUG/INFO/WARNING/ERROR). |
| `NIBRAS_LOG_FORMAT` | `json` | صيغة السجل: `json` (سطر JSON مهيكل) أو `text` (key=value). |
| `NIBRAS_LOG_ACCESS` | `1` | تسجيل كل طلب HTTP (سجل `nibras.request`) — `0` يوقفه. |
| `NIBRAS_APP_VERSION` | `1.0.0` | إصدار التطبيق المعروض في `/api/ready` والسجلات. |

## التشغيل

```bash
pip install -r requirements.txt
python3 -m app.seed        # تعبئة قاعدة البيانات (مرة واحدة، أو عند الحاجة لإعادة التصفير)
python3 run.py              # يشتغل على http://localhost:8000
```

## الصلابة التشغيلية (المرحلة 11)

```bash
# النسخ الاحتياطي والاستعادة (قاعدة SQLite — نسخة متسقة عبر sqlite3 backup API)
python scripts/backup.py backup [--keep 7]        # ينشئ نسخة في backups/ مع دوران
python scripts/backup.py list                     # عرض النسخ (الحجم/التاريخ)
python scripts/backup.py restore --backup backups/nibras-*.sqlite

# اختبار الحمل/الإجهاد (يُشغّل الخادم على نسخة مؤقتة من قاعدة البيانات)
python scripts/load_test.py --concurrency 32 --requests 1000
```

- **السجلات المهيكلة:** سطر JSON لكل طلب (`nibras.request`) مع
  `request_id/method/path/status/duration_ms/remote_addr/user_id`، ورأس
  `X-Request-ID` في كل استجابة للتعقّب. الحقول الحساسة (كلمات المرور،
  الرموز، الأسرار، البريد…) تُعمَّى `[REDACTED]` عند التسجيل. رؤوس أمن
  عامة على كل الاستجابة (nosniff / X-Frame-Options DENY / Referrer-Policy /
  Permissions-Policy).
- **المراجعة الأمنية:** النتائج والأدلة والبنود المؤجلة في
  `docs/SECURITY_REVIEW.md`.

## نقاط النهاية (API Endpoints)

| الطريقة | المسار | الوصف |
|---|---|---|
| GET | `/api/health` | فحص حالة الخادم (حيوية — استجابة ثابتة) |
| GET | `/api/ready` | جاهزية الخادم: فحص اتصال قاعدة البيانات (`200` جاهز / `503` غير جاهز) |
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
| GET | `/api/documents/templates?category=` | قائمة قوالب الوثائق (عام) |
| GET | `/api/documents/templates/<slug>` | تفاصيل قالب: الحقول (field_schema) + هيكل الوثيقة (عام) |
| POST | `/api/documents/generate` | توليد وثيقة `{template_id, answers}` (يتطلب JWT + حد معدل) |
| GET | `/api/documents/my` | وثائق المستخدم المولَّدة (يتطلب JWT) |
| POST | `/api/documents/<id>/regenerate` | إعادة توليد بنسخة +1 عند التعديل (يتطلب JWT + مالك) |
| GET | `/api/documents/<id>/export?format=pdf\|docx` | تنزيل الوثيقة PDF/DOCX (يتطلب JWT + مالك) |
| GET | `/api/professionals?type=&specialty=&city=&limit=&offset=` | دليل مهني عام — **المحقَّقون فقط** (تفرضه طبقة الاستعلام) |
| GET | `/api/professionals/<id>` | تفاصيل ملف محترف + تقييماته (المحقَّقون فقط) |
| POST | `/api/professionals/profile` | إنشاء/تحديث الملف المهني الذاتي `{profession_type, bio, city, phone, contact_preference, specialties}` (يتطلب دورًا مهنيًا) |
| POST | `/api/professionals/verify-document` | رفع وثيقة التحقق multipart (حقل `document` — pdf/jpg/png حتى 5MB) |
| POST | `/api/professionals/<id>/reviews` | تقييم محترف `{rating: 1-5, comment}` — upsert بلا تقييم ذاتي (يتطلب JWT) |
| GET | `/api/admin/verification/<user_id>/document` | تنزيل وثيقة التحقق لمستخدم (يتطلب دور `admin`) |
| GET | `/api/community/categories` | فئات المجتمع (عدد المنشورات المرئية لكل فئة) |
| GET | `/api/community/posts?category=&limit=&offset=` | منشورات مرئية (ترقيم) |
| GET | `/api/community/posts/<id>` | تفاصيل منشور + تعليقات + تفاعلات (+ `my_reactions` للمُصادَق) |
| POST | `/api/community/posts` | إنشاء منشور `{category_id, title, body}` (يتطلب JWT + حد معدل) |
| PUT/DELETE | `/api/community/posts/<id>` | تعديل/حذف (removed) منشوراتك فقط (يتطلب JWT) |
| POST | `/api/community/posts/<id>/comments` | إضافة تعليق (يتطلب JWT + حد معدل) |
| PUT/DELETE | `/api/community/posts/<id>/comments/<comment_id>` | تعديل/حذف تعليقاتك فقط (يتطلب JWT) |
| POST | `/api/community/posts/<id>/react` | تبديل تفاعل `{type: like\|helpful}` (يتطلب JWT) |
| POST | `/api/community/report` | بلاغ `{target_type: post\|comment\|professional_profile, target_id, reason}` (يتطلب JWT) |
| GET | `/api/notifications?unread=&limit=&offset=` | إشعاراتي مرتَّبة (الأحدث أولًا) + عدد غير المقروء (يتطلب JWT) |
| GET | `/api/notifications/unread-count` | عداد الإشعارات غير المقروءة (يتطلب JWT) |
| POST | `/api/notifications/<id>/read` | تعليم إشعار مقروءًا (يتطلب JWT) |
| POST | `/api/notifications/read-all` | تعليم كل الإشعارات مقروءة (يتطلب JWT) |
| GET | `/api/admin/moderation-queue` | بلاغات الإشراف المفتوحة مع لمحة عن المحتوى (يتطلب دور `admin`) |
| POST | `/api/admin/moderation/<report_id>/action` | `{action: dismiss\|hide\|remove}` على بلاغ مفتوح — مُسجَّل تدقيقًا (يتطلب دور `admin`) |
| GET | `/api/marketplace/categories` | فئات السوق (عدد القوالب لكل فئة) |
| GET | `/api/marketplace/templates?category=&q=&limit=&offset=` | تصفح القوالب (تصفية بالتصنيف + بحث نصي + ترقيم) |
| GET | `/api/marketplace/templates/<id>` | تفاصيل قالب (بلا `storage_key`) |
| POST | `/api/admin/marketplace/categories` | إنشاء فئة سوق `{slug, name}` (يتطلب دور `admin`) |
| PUT/DELETE | `/api/admin/marketplace/categories/<id>` | تعديل/حذف فئة (حذف ممنوع لفئة فيها قوالب — يتطلب دور `admin`) |
| GET | `/api/admin/marketplace/templates` | قائمة إدارية بالقوالب (معلومات الملف — يتطلب دور `admin`) |
| POST | `/api/admin/marketplace/templates` | إنشاء قالب multipart `{category_id, title, description, price_cents, file}` (pdf/docx — يتطلب دور `admin`) |
| PUT | `/api/admin/marketplace/templates/<id>` | تعديل قالب (JSON أو multipart، `file` اختياري — يتطلب دور `admin`) |
| DELETE | `/api/admin/marketplace/templates/<id>` | حذف قالب + ملفه (حذف ممنوع لقالب له شراءات — يتطلب دور `admin`) |
| GET | `/api/admin/marketplace/templates/<id>/file` | تنزيل ملف القالب (يتطلب دور `admin`) — بلا تنزيل عام حتى الشراء |
| GET | `/api/admin/analytics/summary` | ملخص التحليلات الإدارية: استخدام + طابورا التحقق/الإشراف + إيرادات صفرية مؤجَّلة (يتطلب دور `admin`) |
| GET | `/api/ads/serve?slot=<slug>` | خدمة إعلانية عامة: تعيد الحملة النشطة للفتحة (`library_sidebar`/`search_results_top`/`directory_listing_top`) أو `null` |
| POST | `/api/ads/<campaign_id>/impression` | تسجيل انطباع إعلان (مصادقة اختيارية + حد معدل) |
| POST | `/api/ads/<campaign_id>/click` | تسجيل نقرة إعلان (مصادقة اختيارية + حد معدل) |
| GET | `/api/admin/ads/slots` | فتحات الإعلانات مع عدد الحملات النشطة (يتطلب دور `admin`) |
| GET | `/api/admin/ads/campaigns` | حملات الإعلانات مع إحصائيات (انطباعات/نقرات/CTR + اسم الفتحة) (يتطلب دور `admin`) |
| POST | `/api/admin/ads/campaigns` | إنشاء حملة `{slot_id, campaign_type, advertiser_name, creative_url, target_url, starts_at?, ends_at?, status?, profile_id?}` (يتطلب دور `admin`) |
| PUT/DELETE | `/api/admin/ads/campaigns/<id>` | تعديل/حذف حملة (حذف بحذف أحداثها تسلسليًا — يتطلب دور `admin`) |
| POST | `/api/admin/ingestion/import` | استيعاب PDF/DOCX في المكتبة: multipart `{file, category_id, type, title, official_ref?, enacted_date?, last_amended?, source_note?, is_sample_data?, dry_run?}` — `dry_run=1` يعاين التقسيم بلا كتابة؛ بدونه يُنشئ النص ومواده مفهرسة (يتطلب دور `admin`) |

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

مثال توليد وثيقة (عقد كراء سكني — يتطلب التوكن):
```bash
curl -X POST http://localhost:8000/api/documents/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <JWT>" \
  -d '{"template_id": 1, "answers": {"landlord_name": "علي", "tenant_name": "فاطمة",
       "property_address": "الدار البيضاء", "monthly_rent": 2500,
       "start_date": "2026-09-01", "duration_months": 12, "deposit_amount": 5000}}'
```

مثال النظام البيئي المهني (التسجيل بدور مهني ثم إنشاء الملف ورفع وثيقة التحقق):
```bash
# 1) التسجيل بدور "محامٍ" — يُنشأ بانتظار التحقق
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "lawyer@nibras.ma", "password": "قوية-طويلة", "full_name": "محامٍ", "role": "lawyer"}'

# 2) إنشاء الملف المهني (يظهر في الدليل فقط بعد قبول الأدمن للتحقق)
curl -X POST http://localhost:8000/api/professionals/profile \
  -H "Content-Type: application/json" -H "Authorization: Bearer <JWT>" \
  -d '{"profession_type": "lawyer", "city": "الدار البيضاء",
       "bio": "محامٍ معتمد", "specialties": ["مدني", "أسر"],
       "contact_preference": "visible", "phone": "0612345678"}'

# 3) رفع وثيقة التحقق (multipart)
curl -X POST http://localhost:8000/api/professionals/verify-document \
  -H "Authorization: Bearer <JWT>" -F "document=@carton.pdf"

# 4) تصفح الدليل العام (المحقَّقون فقط)
curl "http://localhost:8000/api/professionals?type=lawyer&city=الدار البيضاء"
```

مثال سوق القوالب (رفع قالب من الأدمن ثم التصفح العام — الشراء مؤجَّل لحسم بوابة الدفع):
```bash
# 1) رفع قالب (يتطلب توكن admin) — multipart
curl -X POST http://localhost:8000/api/admin/marketplace/templates \
  -H "Authorization: Bearer <JWT>" \
  -F "category_id=1" -F "title=نموذج عقد إيجار" -F "price_cents=1500" \
  -F "file=@contract.pdf"

# 2) تصفح عام
curl "http://localhost:8000/api/marketplace/templates?category=1"
```

مثال نظام الإعلانات (خدمة عامة + تتبع — الفصل البصري عن المحتوى القانوني مسؤولية
الواجهة، وتكشف الاستجابة `sponsored` للوسم):
```bash
# 1) طلب إعلان لفتحة المكتبة الجانبية
curl "http://localhost:8000/api/ads/serve?slot=library_sidebar"

# 2) تسجيل انطباع ثم نقرة (تستدعيها الواجهة عند العرض والنقر)
curl -X POST http://localhost:8000/api/ads/1/impression
curl -X POST http://localhost:8000/api/ads/1/click
```

مثال محرك رفع المستندات (رفع نص قانوني PDF/DOCX من الأدمن وفهرسة مواده تلقائيًا
— المعالجة متزامنة مع سقف حجم/مواد، قرار D-028):
```bash
# 1) معاينة التقسيم قبل الالتزام (dry_run=1 — بلا كتابة)
curl -X POST http://localhost:8000/api/admin/ingestion/import \
  -H "Authorization: Bearer <JWT>" \
  -F "file=@madouna.docx" -F "category_id=3" -F "type=code" \
  -F "title=مدونة الأسرة" -F "dry_run=1"

# 2) الالتزام (ينشئ النص + مواده مفهرسة في FTS)
curl -X POST http://localhost:8000/api/admin/ingestion/import \
  -H "Authorization: Bearer <JWT>" \
  -F "file=@madouna.docx" -F "category_id=3" -F "type=code" \
  -F "title=مدونة الأسرة" -F "official_ref=ظهير 1.04.22"
```

كل إجراء إداري (إنشاء/تعديل/حذف محتوى، قبول/رفض تحقق، إجراءات إشراف
hide/remove/dismiss، عمليات سوق marketplace.*، حملات إعلانية ads.*) يُسجَّل في
`admin_audit_log` (المسؤول، الفعل، الهدف، التوقيت) وفق Security Architecture §8.

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
2. **محرك رفع المستندات (المرحلة 10 — اكتمل)**: مكتمل (قرار D-028):
   `POST /api/admin/ingestion/import` يستوعب PDF/DOCX (استخراج بـ
   pdfminer.six/python-docx) ويقسّم تلقائيًا إلى مواد (`المادة`/`الفصل`
   بأرقام لاتينية/هندية/ترتيبية) ويُفهرسها في المكتبة (FTS) بمعاملة واحدة
   وسجل تدقيق، مع `dry_run=1` لمعاينة التقسيم بلا كتابة. المعالجة متزامنة
   مع سقف حجم/مواد؛ **المعالجة غير المتزامنة (queue/worker) مؤجَّلة** كباقي
   بنية تحتية (مثل هجرة PostgreSQL — لا تُبرمج مسبقًا).
3. **الترقية لقاعدة بيانات إنتاجية**: PostgreSQL مع امتداد بحث نصي عربي (pg_trgm أو
   Elasticsearch) عند نمو الحجم.
4. **مزيد من الحاسبات القانونية**: حاسبة الإرث شغّالة (الفروض، العول، الرد، التعصيب،
   الحجب)، وتُضاف حاسبات أخرى (الطلاق، التعويض...) بنفس نمط الحاسبة المفردة.
5. **الاشتراكات/الفواتير والفتح المتميز لمولّد الوثائق**: المولّد شغّال بلا قيود؛
   فتح الميزة المتميزة (gating عبر `has_premium_access`) يُربط بقرار بوابة الدفع
   (BRD §5) — إضافة دالة واحدة عند بناء وحدة الفوترة.
6. **النظام البيئي المهني**: الدليل (المحقَّقون فقط) والملفات الذاتية ووثائق التحقق
   والتقييمات مكتملة (قرار D-023). المؤجَّل لحسم بوابة الدفع: تدرجات الاشتراك المهنية
   (FR-7.2) والميزات المدفوعة للدليل؛ وللمرحلة المجتمعية: الإشراف والبلاغات
   (التحقق من التفاعلات مرحلة لاحقة — v2).
7. **المجتمع**: الفئات والمنشورات والتعليقات والتفاعلات (like/helpful) وبلاغات
   الإشراف مع إجراءات hide/remove/dismiss مُسجَّلة والشارة الخضراء للمحترفين
   مكتملة (قرار D-024). المؤجَّل لحسم منتج: المتابعة (follows) والنقاط (reputation —
   الصيغة قرار عمل غير محسوم، وثيقة 16 §2)؛ وقيد عمر الحساب كمكافحة إساءة يبقى
   معايرة منتج.
8. **سوق القوالب (Roadmap Phase 5)**: الكتالوج مكتمل (قرار D-025): فئات، قوالب
   بسعر/وصف/ملف (pdf/docx)، إدارة إدارية كاملة (رفع/تسعير/تصنيف/حذف + تنزيل
   إداري)، وتصفح/تصفية/بحث/تفصيل عام بلا كشف للملف. **المؤجَّل لحسم بوابة الدفع
   (BRD §5)**: الشراء الأحادي (POST /templates/<id>/purchase + /my-purchases)
   ومراجعات القوالب (ما بعد الشراء — وثيقة 19 §5)؛ جدول `purchases` مُنشأ
   بلا نقاط نهاية.
9. **لوحة التحليلات الإدارية (Roadmap Phase 6)**: ملخص قراءة-فقط مكتمل (قرار
   D-026): `GET /api/admin/analytics/summary` يجمّع من جداول الوحدات القائمة
   (المستخدمون/الأدوار، AI، الحاسبات، الوثائق، المجتمع، الملفات المهنية،
   السوق) + الطابوران + اتجاه 7 أيام. **الإيرادات والتحويل صفرية مؤجَّلة**
   مع الفوترة (BRD §5)؛ بُعد "البحث" غير مسجَّل في جدول (لا search_log) —
   بند آلات قياس مستقبلي.
10. **نظام الإعلانات (Roadmap Phase 6 — اكتملت)**: مكتمل (قرار D-027): فتحات
    مبذورة، حملات بثلاثة أنواع (عامة/محتوى مرعى/ترويج مهني لملف محقَّق)،
    خدمة `GET /api/ads/serve?slot=` بلا كتابة، تتبع انطباع/نقرة بمصادقة
    اختيارية وحد معدل، وإدارة إدارية مع إحصائيات كل حملة (انطباعات/نقرات/CTR).
    استهداف v1: فتحة + تواريخ فقط (§5)؛ الاستهداف الفئوي (v2) والربط
    بالفوترة (فواتير/ميزانيات) لاحقًا. **بقي من Roadmap Phase 6**: هجرة
    PostgreSQL فقط (مؤقَّتة بالمحفّز، لا تُبرمج مسبقًا — Architecture §9).
11. **محرك رفع المستندات**: مكتمل (قرار D-028، انظر البند 2 أعلاه) — بقيت
    تحسينات لاحقة اختيارية: استيعاب OCR للمسح الضوئي، صفّ معالجة غير متزامن
    للملفات الضخمة، واستخراج كلمات مفتاحية تلقائي من المحتوى.
12. **نظام الإشعارات (المرحلة 12 — اكتمل)**: مكتمل (قرار D-030): جدول
    `notifications` + نقاط `GET /api/notifications` (قائمة مرتَّبة مع عدد
    غير المقروء)، `unread-count` (شارة)، `POST .../<id>/read` و`read-all`،
    ومحفِّزات تلقائية transactional: قبول/رفض التحقق المهني، تعليق/تفاعل
    على منشورك (بلا إشعار لفعل الذات)، وحجب/إزالة بقرار الإشراف.
    **المؤجَّل**: نقاط دفع خارجية (push/email) وإعدادات تفضيلات الإشعارات.
13. **حزمة اختبارات التكامل (المرحلة 13 — اكتمل)**: مكتمل (قرار D-031):
    `tests/test_integration_flows.py` بسيناريوهات نهاية-لنهاية عبر الوحدات
    (5 سيناريوهات): رحلة المحترف الكاملة (تحقق/إشعار/دليل/تحليلات)، إشراف
    المجتمع (تعليق/تفاعل/بلاغ/إزالة)، الاستيعاب → المكتبة → البحث → شرح
    موجَّه بإسناد FTS فعلي، دورة جلسة المصادقة (تسجيل/دخول/تجديد/خروج)،
    وسوق + إعلانات + دليل + ملخص إداري. بعدها البوابة: 373 اختبارًا ناجحًا
    + فحص حي (smoke) على نسخة مؤقتة من القاعدة عبر خادم HTTP فعلي.
14. **تحسينات البحث العربي (المرحلة 14 — اكتمل)**: مكتمل (قرار D-032):
    `app/arabic_text.py` يوفّر تطبيعًا موحَّدًا (إزالة التشكيل، أ/إ/آ→ا،
    ة→ه، ى→ي، ؤ→و، ئ→ي) يُطبَّق على الفهرس عبر دالة SQL `nbr_normalize`
    وعلى الاستعلام، متغيّرات "ال" التعريفية وحروف العطف الملتصقة
    («والمشغل»/«بالعقد»)، واستبعاد كلمات وظيفية؛ فهرس FTS5 أصبح قائمًا
    بذاته مع ترحيل تلقائي (idempotent) للقواعد القديمة في `init_db`.
    البوابة بعدها: 392 اختبارًا ناجحًا + فحص حي على نسخة من nibras.db
    الحقيقية أثبت الترحيل وبحثًا بدون تشكيل وبكلمات ملتصقة والشرح
    الموجَّه. **الباقي**: عمليات إدارية جماعية، إشعارات push/email،
    جاهزية multi-tenant.
