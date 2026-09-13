# تطبيق أندرويد (Trusted Web Activity)

تطبيق **نبراس** على Google Play مبني كـ **Trusted Web Activity (TWA)**: غلاف أندرويد أصلي يعرض الموقع الحالي
بملء الشاشة وبدون شريط المتصفح، عبر تحقق `Digital Asset Links` ثنائي الاتجاه بين التطبيق والموقع.

الموقع نفسه **لا يتغير إطلاقاً**: التطبيق يفتح `https://nibraslaw.com/` بنفس الـ SPA والـ SSR، وكل ما أُضيف
للموقع هو ملف تحقق واحد فقط: `frontend/.well-known/assetlinks.json`.

## البنية

```
android-app/
  settings.gradle / build.gradle / gradle.properties
  gradlew, gradlew.bat, gradle/wrapper/gradle-wrapper.jar  (Gradle 8.7)
  app/
    build.gradle                     # applicationId com.nibraslaw.app، توقيع release من keystore.properties
    src/main/AndroidManifest.xml     # LauncherActivity + asset_statements + النطاق
    src/main/res/                    # اسم التطبيق، الألوان، splash، أيقونة adaptive
  keystore/nibras-release.p12        # مفتاح التوقيع (مضمّن مؤقتاً في repo — انظر ملاحظة الأمان)
  keystore.properties                # كلمة السر والاسم (مضمّن مؤقتاً)
frontend/.well-known/assetlinks.json # رابط التطبيق بالموقع (يُنشر مع الموقع)
.github/workflows/android-build.yml  # يبني AAB موقّع تلقائياً
```

## كيف يعمل TWA

1. `asset_statements` داخل الـ Manifest يصرّح: هذا التطبيق تابع للموقع `https://nibraslaw.com`.
2. `assetlinks.json` على الموقع يصرّح: هذا الموقع يخوّل التطبيق `com.nibraslaw.app` الموقّع
   بالشهادة ذات الـ SHA-256 المدرجة.
3. عند فتح التطبيق يتحقق Chrome من التطابق، فيعرض الموقع بملء الشاشة (بدون شريط عنوان).
   عند عدم تطابق البصمات يفتح التطبيق الموقع داخل Custom Tab (لا يزال يعمل، لكن بحدود المتصفح).

## الإعداد

مفتاح التوقيع (`android-app/keystore/nibras-release.p12`) ومعلوماته (`android-app/keystore.properties`)
مضمّنان حالياً في repo كي يعمل البناء تلقائياً من GitHub Actions دون أسرار.

> **⚠️ ملاحظة أمان مهمة**: المستودع **عام**. مفتاح مضمّن في repo عام يعني أن أياً كان قادراً على
> بناء وتوقيع نسخ بنفس `applicationId`. قبل أي إطلاق أو توزيع على نطاق واسع:
> 1. اجعل repo **خاصاً** (GitHub → Settings، مجاني).
> 2. انقل المفتاح من repo إلى **GitHub Secrets** (احذف الملف بعد النقل) وعدّل workflow
>    لينقرأ الجمل من الأسرار، أو بدّل **Upload Key** في Play Console (Setup → App signing →
>    Replace upload key) بعد أول رفع.
> يمكن توليد مفتاح جديد بالكامل عبر:
> `python scripts/gen_release_keystore.py --out android-app/keystore/nibras-release.p12`
> ثم تحديث البصمة الجديدة في `frontend/.well-known/assetlinks.json`.

## البناء

- **تلقائياً**: عند رفع `android-app/**` إلى `master` يشغّل workflow البناء ويرفع `nibras-release-bundle.aab`
  في Artifacts (Actions ← آخر تشغيل ← App signing المعلومات + تنزيل الـ AAB).
- **محلياً (اختياري)**: افتح المجلد `android-app` في Android Studio ثم Build → Generate Signed Bundle.
  (يتطلب JDK 17 + Android SDK؛ لوضع المفتاح المحلي: انسخ `keystore/nibras-release.p12` وحدد مساره مع
  كلمة السر والاسم `nibras` في إعدادات التوقيع).

## النشر على Google Play

1. حساب مطوّر (رسوم تسجيل لمرة واحدة) → Create app.
2. ارفع `*.aab` (من CI Artifacts) في Internal testing أولاً.
3. عادة تفعّل **Play App Signing**: به يوقّع Google التطبيق بمفتاحه الخاص في متجر Play.
   في هذه الحالة: انسخ **بصمة SHA-256 لشهادة App signing** من Play Console
   (Setup → App signing) وضعها في `frontend/.well-known/assetlinks.json` (بدل بصمة مفتاح الرفع)
   ثم أعد النشر. بصمة مفتاح الرفع الحالية صالحة للاختبارات المحلية.
4. أكمل استمارة المحتوى (نظرة عامة) حسب `docs/PLAY_STORE.md`.
5. تقدّم للـ review — التطبيق معلومات/قانون تعليمي بنطاق مملوك وموثوق فتمر مراجعة عادة بسرعة.

## اختبار محلي (بدون متجر)

- اشحن `debug` APK على جهاز: `./gradlew assembleDebug` ثم
  `adb install app/build/outputs/apk/debug/app-debug.apk`.
- TWA لا يختفي شريط المتصفح إلا عند تحقق كامل؛ للاختبار المحلي أضف بصمة شهادة الـ debug
  إلى `assetlinks.json` (تجدها عبر `keytool -list -v -keystore ~/.android/debug.keystore`) أو
  فعّل `--disable-digital-asset-link-verification` في Chrome للأجهزة الجذرية.

## ملاحظات أداء ومتجر

- `minSdk 24`, `targetSdk 35`, `compileSdk 35` (متطلب سياسة Play للتطبيقات الجديدة)، أيقونات adaptive + splash من ألوان وهوية الموقع.
- لا توجد أذونات طلبها (لا `INTERNET` — يقدمه الخروج عبر Custom Tabs/TWA ضمني).
- الإشعارات (`enableNotifications`) جاهزة دون Firebase؛ لتفعيل الإشعارات الفعلية يُضاف لاحقاً
  FCM service وملف `google-services.json`.