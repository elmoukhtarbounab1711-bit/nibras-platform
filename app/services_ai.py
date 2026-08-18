"""
خدمات الذكاء الاصطناعي (المرحلة 3) — قرار D-021 (المحسَّن: مزوّدات متعددة).

واجهة مزوّد موحَّدة generate() قابلة للاستبدال (وثيقة 13 §5). تُدار المزوّدات
من لوحة التحكم (جدول ai_providers) وتشمل:
  * noop              — تطوير/اختبار حتمي بلا شبكة (احتياطي دائم العمل).
  * gemini            — Google Gemini (حصة مجانية سخية بلا بطاقة بنكي).
  * openai_compatible — Groq / OpenRouter / NVIDIA / Mistral / Cerebras ...
  * ollama            — تشغيل محلي بلا مفتاح (إن ثُبّت).
  * anthropic         — للمدفوع لاحقًا.

كل المكالمات عبر urllib القياسي (لا اعتماد pip إضافي). تبقى خطوط الأنابيب
الموجَّهة (grounded) والعامة (general) واستخراج الاستشهادات كما هي، وتُضاف
خطوط المقارنة (research): استرجاع مواد نبراس + بحث ويب خارجي، ومقارنة
الاثنين في إجابة احترافية توضح ما يطابق نبراس وما يخالفها.
"""
import base64
import json
import re
import time
import urllib.error
import urllib.request

from . import config, services
from .database import db_session
from .legal_knowledge import (
    classify_query,
    expand_query,
    topic_context,
)
from .services_jurisprudence import search_decisions
from .services_websearch import search_web


class AIProviderError(Exception):
    def __init__(self, message: str, status_code: int = 503):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


# ---------------------------------------------------------------------------
# استخراج نص PDF + تحليل الصور (رفع المرفقات)
# ---------------------------------------------------------------------------
AI_ATTACHMENT_MAX_BYTES = 10 * 1024 * 1024  # 10MB
AI_IMAGE_MAX_BYTES = 5 * 1024 * 1024  # 5MB
AI_PDF_MAX_PAGES = 30
AI_PDF_TEXT_MAX_CHARS = 18000
AI_ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/jpg"}
AI_ALLOWED_PDF_TYPES = {"application/pdf"}


def extract_pdf_text(file_bytes: bytes) -> str:
    """يستخرج نص PDF عبر pdfminer.six (موجود بالفعل في المشروع)."""
    try:
        from io import BytesIO

        from pdfminer.high_level import extract_text as pdf_extract
        text = pdf_extract(BytesIO(file_bytes), maxpages=AI_PDF_MAX_PAGES)
        return (text or "").strip()[:AI_PDF_TEXT_MAX_CHARS]
    except ImportError:
        raise AIProviderError("مكتبة pdfminer غير متوفرة.", 503)
    except (ValueError, TypeError, OSError) as exc:
        raise AIProviderError(f"تعذر استخراج نص PDF: {exc}", 400)


def encode_image_base64(file_bytes: bytes, mime_type: str) -> str:
    """يحوّل بايتات الصورة إلى base64 لإرسالها للمزوّد."""
    if len(file_bytes) > AI_IMAGE_MAX_BYTES:
        raise AIProviderError("حجم الصورة يتجاوز 5MB.", 400)
    return base64.b64encode(file_bytes).decode("ascii")


def _build_prompt_with_attachment(question: str, extracted_text: str = "",
                                  image_data_url: str = "",
                                  context_articles: list | None = None,
                                  mode: str = "general"):
    """يبني system/user_prompt مع مرفق PDF أو صورة."""
    if extracted_text:
        truncated_notice = ""
        if len(extracted_text) >= AI_PDF_TEXT_MAX_CHARS - 10:
            truncated_notice = (
                "\n\n⚠ تنبيه: تم اقتطاع بعض من النص بسبب حجم الملف الكبير. "
                " Grove قد لا يحتوي النص على كامل المستند."
            )
        system = (
            "قواعد صارمة يجب اتباعها:\n"
            "1. أنت تحلّل مستندًا قانونيًا مغربيًا حقيقيًا مرفقًا أدناه.\n"
            "2. استخرج التحليل حصريًا من النص المُرفَق فقط — لا تختلق أو تخمّن أو "
            "تستخدم معلومات خارج هذا النص.\n"
            "3. ابدأ ردك بتحديد عنوان المستند والجهة الصادرة عنه إن وُجد في النص.\n"
            "4. إذا لم تجد معلومة في النص، قل \"لا تتوفر هذه المعلومة في المستند المُرفَق\" "
            "بدلاً من التخمين.\n"
            "5. اذكر المواد والأرقام كما هي في النص.\n"
            "6. لا تذكر \"قانون المحاماة\" أو أي قانون آخر إن لم يكن موجودًا في النص.\n\n"
            "أجب بالعربية الفصحى الواضحة. إذا كان السؤال بالدارجة المغربية، "
            "افهمه وأجب بالفصحى.\n"
            "أمثلة على الدارجة: واش (هل)، شحال (كم)، كيفاش (كيف)، علاش (لماذا)."
            f"{truncated_notice}"
        )
        user_prompt = (
            f"سؤال المستخدم:\n{question}\n\n"
            f"--- النص المستخرج من ملف PDF ---\n"
            f"{extracted_text}\n"
            f"--- نهاية النص ---\n\n"
            f"حلّل هذا المستند وأجب على السؤال أعلاه بناءً على النص فقط."
        )
    elif image_data_url:
        system = (
            "أنت مساعد قانوني مغربي خبير. المستخدم أرفق صورة قد تحتوي على "
            "مستند قانوني أو صورة ذات علاقة بالقانون.حلل الصورة وأجب على "
            "سؤال المستخدم بناءً عليها.\n\n"
            "أجب بالعربية الفصحى الواضحة. إذا كان السؤال بالدارجة المغربية، "
            "افهمه وأجب بالفصحى."
        )
        user_prompt = question or "حلّل هذه الصورة وأخبرني بها:"
    else:
        return _build_prompt(question, context_articles or [], mode)
    return system, user_prompt


class AIProvider:
    """generate(question, context_articles, mode) -> نص الرد. name معرف النوع.

    الوسائط الاختيارية system/user_prompt تسمح بالتحكم الكامل بالبرومبت من
    خارج (يستخدمها وضع المقارنة research حيث يتطلب البرومبت بنية مزدوجة
    نبراس + ويب). عند غيابها يُبنى البرومبت داخليًا.

    images: قائمة dicts بتنسيق {"mime": "image/jpeg", "data": "<base64>"} اختيارية.
    """
    name = "noop"

    def generate(self, question: str, context_articles: list, mode: str,
                 system: str | None = None, user_prompt: str | None = None,
                 images: list | None = None) -> str:
        raise NotImplementedError

    def ping(self) -> str:
        return self.generate("اختبار", [], "general")


def _build_prompt(question: str, context_articles: list, mode: str,
                  system: str | None = None, user_prompt: str | None = None,
                  context_decisions: list | None = None):
    """يبني (system, user_prompt) — منطق موحَّد لكل المزوّدات.

    إن مُرِّرت system/user_prompt صراحةً (وضع المقارنة) تُستخدم كما هي.

    context_decisions: اجتهادات قضائية مسترجعة تُرفق بالمواد كمرجع ثانٍ
    (فقه قضائي) في الإجابة الموجَّهة (grounded/research). تُنسَّق بترويسة
    «اجتهاد قضائي — المحكمة — رقم القرار».
    """
    if system is not None and user_prompt is not None:
        return system, user_prompt

    topics = classify_query(question)
    topic_ctx = topic_context(topics)

    if mode == "general":
        system = (
            "أنت مساعد قانوني تعليمي مغربي خبير. أجب بلغة عربية واضحة ومبسطة "
            "مناسبة لمواطن عادي. بيّن في بداية الرد أن الجواب تعليمي عام وغير "
            "موجَّه بمكتبة نبراس وأنه ليس استشارة قانونية.\n\n"
            "مجالات خبرتك الرئيسية (القانون المغربي اليومي):\n"
            "1) قانون الأسرة: الزواج (النكا��، العقد، المهر)، الطلاق (تطليق، خلع، شقاق)، "
            "النفقة، الحضانة، الولاية الأبوية، الميراث والوصية.\n"
            "2) قانون الشغل: عقد العمل، الأجر، الإجازات، التسريح، التقاعد، "
            "حوادث العمل، الضمان الاجتماعي (CNSS).\n"
            "3) الإيجار والسكنى: عقد الإيجار، رفع الكرية، الإخلاء، الضمان، "
            "التوطين، الملكية المشتركة.\n"
            "4) القانون الجنائي: السرقة، النصب، التشهير، القذف، التهديد، "
            "الحبس، الغرامات، التقادم.\n"
            "5) حماية المستهلك: الضمان، استرجاع البضاعة، الغش التجاري.\n"
            "6) قانون السير: رخصة السياقة، المخالفات، التأمين، حوادث السير.\n"
            "7) الصحة والحماية الاجتماعية: التأمين الصحي (AMO)، CNSS، التقاعد.\n"
            "8) الضرائب: التصريح الجبائي، ضريبة الدخل، القيمة المضافة.\n"
            "9) حماية البيانات: القانون 09-08، الخصوصية الرقمية.\n\n"
            "إذا كتب المستخدم بالدارجة المغربية، فافهم سؤاله وحوّل المعنى إلى "
            "فصحى وأجب بالعربية الفصحى الواضحة.\n"
            "أمثلة: واش (هل)، شحال (كم)، كيفاش (كيف)، علاش (لماذا)، "
            "هاد (هذا)، اللّي (الذي)، ديال (خاص بـ)، بزاف (كثير)، ماشي (ليس)، "
            "غادي (سوف)، شكون (من)، وين (أين)، الخدمة (العمل)، الكرا (الإيجار)."
        )
        user_prompt = question
    else:
        system = (
            "أنت مساعد قانوني مغربي خبير وموثَّق يعتمد حصريًا على مكتبة نبراس "
            "القانونية — أكثر من 1600 نص قانوني مغربي (24000+ مادة) واجتهادات "
            "قضائية لمحكمة النقض. تغطي المكتبة مجالات القانون اليومي:\n"
            "• مدونة الأسرة (الزواج، الطلاق، النفقة، الحضانة، الميراث)\n"
            "• مدونة الشغل (العمل، الأجر، الإجازات، التسريح، حوادث العمل)\n"
            "• قانون الإيجار (عقد الإيجار، رفع الكرية، الإخلاء)\n"
            "• القانون الجنائي (السرقة، النصب، التشهير، الحبس)\n"
            "• مدونة الالتزامات والعقود (البيع، الضمان، العيوب الخفية)\n"
            "• القانون التجاري، قانون السير، الضرائب، حماية البيانات\n\n"
            "النصوص المرجعية المرفقة مستخرجة من مكتبة نبراس. أجِب بناءً عليها "
            "واستشهد برقم المادة بين قوسين (مثل «المادة 344»). عند الاستناد إلى "
            "اجتهاد قضائي استشهد بمحكمته ورقم القرار.\n\n"
            "إذا لم تغطِّ المواد المرفقة السؤال فعلًا، فأجِب إجابة تعليمية عامة "
            "وبيّن في بدايتها أنها عامة غير موجَّهة بمكتبة نبراس.\n\n"
            "إذا كتب المستخدم بالدارجة المغربية، فافهم سؤاله واحوّله ذهنيًا إلى "
            "فصحى وأجب بالعربية الفصحى الواضحة.\n"
            "أمثلة على الدارجة: واش (هل)، شحال (كم)، كيفاش (كيف)، علاش (لماذا)، "
            "هاد (هذا)، اللّي (الذي)، ديال (خاص بـ)، بزاف (كثير)، ماشي (ليس)، "
            "غادي (سوف)، الخدمة (العمل)، الكرا (الإيجار)، الفلوس (المال)."
        )
        parts = []
        if context_articles:
            parts.append("\n".join(
                f"{a['label']} ({a.get('legal_text_title', '')}):\n{a['content']}"
                for a in context_articles
            ))
        if context_decisions:
            dec_rows = []
            for d in context_decisions:
                principles = d.get("principles") or ""
                body = d.get("content") or ""
                if len(body) > config.AI_JURISPRUDENCE_MAX_CHARS:
                    body = body[: config.AI_JURISPRUDENCE_MAX_CHARS] + " …"
                if not body and principles:
                    body = principles
                court = d.get("court") or "محكمة النقض"
                num = d.get("decision_number") or ""
                label = f"اجتهاد قضائي — {court}"
                if num:
                    label += f" — رقم {num}"
                cat = d.get("category_name") or ""
                if cat:
                    label += f" ({cat})"
                dec_rows.append(f"{label}:\n{body}")
            if dec_rows:
                parts.append("اجتهادات قضائية مسترجعة:\n" + "\n\n".join(dec_rows))
        context = "\n\n".join(parts)

        topic_hint = ""
        if topic_ctx and not context_articles:
            from .legal_knowledge import DAILY_LIFE_TOPICS as _TOPICS
            topic_hint = (
                "\n\nملاحظة: السؤال يتعلق بـ"
                + "، ".join(
                    _TOPICS[k]["title"] for k in topics[:2]
                    if k in _TOPICS
                )
                + ". النصوص المرجعية في المكتبة قد لا تظهر بالبحث المباشر — "
                "استخدم معرفتك العامة في هذا المجال مع التوضيح بأنها من معرفتك "
                "العامة وليست من مكتبة نبراس."
            )

        user_prompt = (
            f"سؤال المستخدم:\n{question}\n\n"
            f"النصوص المرجعية:\n{context}"
            f"{topic_hint}"
        )
    return system, user_prompt


def _build_research_prompt(question: str, context_articles: list, web_results: list,
                           context_decisions: list | None = None):
    """يبني (system, user_prompt) لوضع المقارنة (research).

    الإجابة الاحترافية تُعتمد على مواد نبراس كمرجع قانوني ملزم، وتقارنها
    بالمقالات الخارجية المسترجعة من الويب: تُبيّن أوجه الاتفاق والاختلاف،
    وتنبّه إلى أن المقالات الخارجية إعلامية غير ملزمة وقد تكون قديمة أو
    تعتمد نصوصًا معدَّلة، وأن النص النافذ هو ما في نبراس.
    """
    system = (
        "أنت مستشار قانوني مغربي احترافي ومحايد. تُعطي إجابة مقارِنة موثقة "
        "تعتمد مادة مادة من مكتبة نبراس القانونية (أكثر من 1600 نص قانوني مغربي "
        "محدث) واجتهاداتها القضائية باعتبارها المرجع الملزم، وتقابلها بالمقالات "
        "الخارجية المسترجعة من الويب. التزم بالآتي:\n"
        "1) ابدأ بخلاصة مباشرة من نبراس مع الاستشهاد برقم المادة بين قوسين "
        "(مثل «المادة 344»)، وعند الاستناد إلى اجتهاد قضائي استشهد بمحكمته "
        "ورقم القرار بين قوسين (مثل «اجتهاد محكمة النقض 2021/158»).\n"
        "2) اعرض ما تقوله المقالات الخارجية (بعنوان مصدرها بين قوسين) ثم قارنها "
        "بمواد نبراس واجتهاداتها: حدّد أوجه الاتفاق، وأوجه الاختلاف/التناقض بوضوح.\n"
        "3) عندما يختلف مصدر خارجي عن نبراس، بيّن أن نبراس تعكس النصوص النافذة "
        "والمحدثة وأن المقالة الخارجية إعلامية غير ملزمة وقد تعتمد نصوصًا "
        "معدَّلة أو قديمة.\n"
        "4) إن كان السؤال لا تغطيه مواد نبراس المسترجعة، قل ذلك صراحةً وأجب "
        "إجابة عامة واضحة بأنها غير ملزمة وليست استشارة قانونية.\n"
        "5) اجعل الرد بالعربية الفصحى، منظّمًا بعناوين قصيرة، دون إطالة.\n"
        "6) إذا كتب المستخدم بالدارجة المغربية، فافهم سؤاله واحوّله ذهنيًا إلى "
        "فصحى وأجب بالعربية الفصحى الواضحة."
    )
    nibras = "\n\n".join(
        f"{a['label']} ({a.get('legal_text_title', '')}):\n{a['content']}"
        for a in context_articles
    )
    if context_decisions:
        dec_rows = []
        for d in context_decisions:
            body = d.get("content") or d.get("principles") or ""
            if len(body) > config.AI_JURISPRUDENCE_MAX_CHARS:
                body = body[: config.AI_JURISPRUDENCE_MAX_CHARS] + " …"
            court = d.get("court") or "محكمة النقض"
            num = d.get("decision_number") or ""
            label = f"اجتهاد قضائي — {court}"
            if num:
                label += f" — رقم {num}"
            cat = d.get("category_name") or ""
            if cat:
                label += f" ({cat})"
            dec_rows.append(f"{label}:\n{body}")
        nibras += "\n\nاجتهادات قضائية مسترجعة:\n" + "\n\n".join(dec_rows)
    if web_results:
        web = "\n\n".join(
            f"{i + 1}. «{w['title']}» — {w['url']}\n   {w.get('snippet', '')}"
            for i, w in enumerate(web_results)
        )
        web_block = f"المقالات الخارجية المسترجعة من الويب (إعلامية غير ملزمة):\n{web}"
    else:
        web_block = "لم تُسترجَع مقالات خارجية من الويب — اكتفِ بمواد نبراس."
    user_prompt = (
        f"سؤال المستخدم:\n{question}\n\n"
        f"مواد نبراس المرجعية (ملزمة):\n{nibras}\n\n{web_block}"
    )
    return system, user_prompt


def _http_json(url: str, headers: dict, payload: dict, timeout: int = 90):
    """طلب HTTP JSON عام عبر urllib — يرفع AIProviderError على كل فشل."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("User-Agent",
                   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
    for k, v in headers.items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise AIProviderError(
            f"المزوّد أعاد HTTP {exc.code}: {exc.read().decode('utf-8', 'replace')[:300]}",
            503,
        ) from exc
    except urllib.error.URLError as exc:
        raise AIProviderError(
            f"تعذر الاتصال بمزوّد الذكاء الاصطناعي: {getattr(exc, 'reason', exc)}", 503
        ) from exc
    except (TimeoutError, OSError, ValueError) as exc:
        raise AIProviderError("تعذر الاتصال بمزوّد الذكاء الاصطناعي. حاول لاحقًا.", 503) from exc


class NoopProvider(AIProvider):
    name = "noop"
    free = True

    def generate(self, question, context_articles, mode,
                 system=None, user_prompt=None, images=None):
        if mode == "general":
            return (
                f"رد تعليمي عام (غير موجَّه بمكتبة نبراس) حول: {question} — "
                "هذه إجابة إعلامية عامة وليست استشارة قانونية."
            )
        if not context_articles:
            return "إجابة عامة (غير موجَّهة بمكتبة نبراس): لم تُستَرجع مواد تغطي سؤالك، إليك رد تعليمي عام وليس استشارة قانونية."
        labels = "، ".join(a["label"] for a in context_articles)
        return f"بناءً على المواد المسترجعة من مكتبة نبراس ({labels})، إليك الجواب الموجَّه. وإن لم تغطِّ المواد سؤالك، فهو رد تعليمي عام غير موجَّه بمكتبة نبراس."

    def ping(self) -> str:
        return "noop"


class GeminiProvider(AIProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: str, base_url: str = "https://generativelanguage.googleapis.com"):
        self.api_key = api_key
        self.model = model or "gemini-flash-latest"
        self.base_url = (base_url or "https://generativelanguage.googleapis.com").rstrip("/")

    def generate(self, question, context_articles, mode,
                 system=None, user_prompt=None, images=None):
        if not self.api_key:
            raise AIProviderError("مفتاح Gemini مفقود. أضفه من لوحة التحكم.", 503)
        system, user_prompt = _build_prompt(
            question, context_articles, mode, system, user_prompt
        )
        url = f"{self.base_url}/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        user_parts = [{"text": user_prompt}]
        if images:
            for img in images:
                user_parts.append({
                    "inline_data": {
                        "mime_type": img.get("mime", "image/jpeg"),
                        "data": img.get("data", ""),
                    }
                })

        payload = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"parts": user_parts}],
        }
        body = _http_json(url, {"Content-Type": "application/json"}, payload)
        try:
            parts = body["candidates"][0]["content"]["parts"]
            text = "".join(p.get("text", "") for p in parts)
        except (KeyError, IndexError, TypeError):
            raise AIProviderError("Gemini أعاد استجابة غير متوقعة.", 503)
        text = text.strip()
        if not text:
            raise AIProviderError("Gemini أعاد ردًا فارغًا.", 503)
        return text


class OpenAICompatProvider(AIProvider):
    name = "openai"

    def __init__(self, api_key: str, model: str, base_url: str):
        self.api_key = api_key
        self.model = model or "gpt-4o-mini"
        self.base_url = (base_url or "https://api.openai.com/v1").rstrip("/")

    def generate(self, question, context_articles, mode,
                 system=None, user_prompt=None, images=None):
        if not self.api_key:
            raise AIProviderError("مفتاح API غير موجود. أضفه من لوحة التحكم.", 503)
        system, user_prompt = _build_prompt(
            question, context_articles, mode, system, user_prompt
        )
        url = f"{self.base_url}/chat/completions"

        user_content = [{"type": "text", "text": user_prompt}]
        if images:
            for img in images:
                mime = img.get("mime", "image/jpeg")
                data = img.get("data", "")
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{data}"},
                })

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_content},
            ],
            "max_tokens": config.AI_MAX_TOKENS,
        }
        body = _http_json(
            url,
            {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
            payload,
        )
        try:
            text = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise AIProviderError("المزوّد أعاد استجابة غير متوقعة.", 503)
        if not text or not str(text).strip():
            raise AIProviderError("المزوّd أعاد ردًا فارغًا.", 503)
        return str(text)


class OllamaProvider(AIProvider):
    name = "ollama"

    def __init__(self, model: str, base_url: str = "http://localhost:11434"):
        self.model = model or "llama3"
        self.base_url = (base_url or "http://localhost:11434").rstrip("/")

    def generate(self, question, context_articles, mode,
                 system=None, user_prompt=None, images=None):
        system, user_prompt = _build_prompt(
            question, context_articles, mode, system, user_prompt
        )
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt},
            ],
        }
        body = _http_json(url, {"Content-Type": "application/json"}, payload)
        text = (body.get("message") or {}).get("content") or ""
        if not str(text).strip():
            raise AIProviderError("Ollama أعاد ردًا فارغًا.", 503)
        return str(text)


class AnthropicProvider(AIProvider):
    name = "anthropic"

    def __init__(self, api_key: str, model: str, base_url: str = "https://api.anthropic.com"):
        self.api_key = api_key
        self.model = model or config.AI_MODEL
        self.base_url = (base_url or "https://api.anthropic.com").rstrip("/")

    def generate(self, question, context_articles, mode,
                 system=None, user_prompt=None, images=None):
        if not self.api_key:
            raise AIProviderError("مفتاح Anthropic مفقود. أضفه من لوحة التحكم.", 503)
        system, user_prompt = _build_prompt(
            question, context_articles, mode, system, user_prompt
        )
        url = f"{self.base_url}/v1/messages"
        payload = {
            "model": self.model,
            "max_tokens": config.AI_MAX_TOKENS,
            "system": system,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        body = _http_json(
            url,
            {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            payload,
        )
        parts = [b.get("text", "") for b in body.get("content", []) if b.get("type") == "text"]
        text = "".join(parts).strip()
        if not text:
            raise AIProviderError("Anthropic أعاد ردًا فارغًا.", 503)
        return text


PROVIDER_CLASSES = {
    "noop": None,
    "gemini": GeminiProvider,
    "openai_compatible": OpenAICompatProvider,
    "ollama": OllamaProvider,
    "anthropic": AnthropicProvider,
}


def provider_instance(row: dict) -> AIProvider:
    typ = row.get("type")
    if typ == "gemini":
        return GeminiProvider(row.get("api_key", ""), row.get("model", ""), row.get("base_url", ""))
    if typ == "openai_compatible":
        return OpenAICompatProvider(row.get("api_key", ""), row.get("model", ""), row.get("base_url", ""))
    if typ == "ollama":
        return OllamaProvider(row.get("model", ""), row.get("base_url", ""))
    if typ == "anthropic":
        return AnthropicProvider(row.get("api_key", ""), row.get("model", ""), row.get("base_url", ""))
    return NoopProvider()


# ---------------------------------------------------------------------------
# كتالوج النماذج المجانية الجاهزة (تظهر في لوحة التحكم كقوالب)
# ---------------------------------------------------------------------------
FREE_CATALOG = [
    {"type": "gemini", "name": "Gemini Flash (الأحدث — مجاني)", "model": "gemini-flash-latest",
     "base_url": "https://generativelanguage.googleapis.com", "free": True},
    {"type": "gemini", "name": "Gemini 3.5 Flash (مجاني)", "model": "gemini-3.5-flash",
     "base_url": "https://generativelanguage.googleapis.com", "free": True},
    {"type": "gemini", "name": "Gemini 3.1 Flash-Lite (مجاني)", "model": "gemini-3.1-flash-lite",
     "base_url": "https://generativelanguage.googleapis.com", "free": True},
    {"type": "openai_compatible", "name": "Groq · Llama 3.3 70B", "model": "llama-3.3-70b-versatile",
     "base_url": "https://api.groq.com/openai/v1", "free": True},
    {"type": "openai_compatible", "name": "Groq · Llama 3.1 8B", "model": "llama-3.1-8b-instant",
     "base_url": "https://api.groq.com/openai/v1", "free": True},
    {"type": "openai_compatible", "name": "OpenRouter · Llama 3.3 70B (:free)", "model": "meta-llama/llama-3.3-70b-instruct:free",
     "base_url": "https://openrouter.ai/api/v1", "free": True},
    {"type": "openai_compatible", "name": "NVIDIA NIM · Llama 3.3 70B", "model": "meta/llama-3.3-70b-instruct",
     "base_url": "https://integrate.api.nvidia.com/v1", "free": True},
    {"type": "openai_compatible", "name": "Mistral · Small", "model": "mistral-small-latest",
     "base_url": "https://api.mistral.ai/v1", "free": True},
    {"type": "ollama", "name": "Ollama محلي (بلا مفتاح)", "model": "llama3",
     "base_url": "http://localhost:11434", "free": True},
    {"type": "anthropic", "name": "Anthropic · Claude Sonnet 4.5", "model": "claude-sonnet-4-5",
     "base_url": "https://api.anthropic.com", "free": False},
    {"type": "openai_compatible", "name": "OpenAI · GPT-4o mini", "model": "gpt-4o-mini",
     "base_url": "https://api.openai.com/v1", "free": False},
]

_PROVIDER_COLUMNS = (
    "id", "name", "type", "base_url", "api_key", "model", "enabled", "is_default"
)


def _row_to_dict(row) -> dict:
    return {
        "id": row[0], "name": row[1], "type": row[2], "base_url": row[3],
        "api_key": row[4], "model": row[5], "enabled": bool(row[6]),
        "is_default": bool(row[7]),
    }


def _active_row(conn):
    return conn.execute(
        "SELECT id, name, type, base_url, api_key, model, enabled, is_default "
        "FROM ai_providers WHERE enabled = 1 ORDER BY is_default DESC, id ASC LIMIT 1"
    ).fetchone()


def list_providers() -> list:
    """يعيد كل المزوّدين مع إخفاء المفتاح (لا يُكشف عبر API)."""
    with db_session() as conn:
        rows = conn.execute(
            "SELECT id, name, type, base_url, api_key, model, enabled, is_default "
            "FROM ai_providers ORDER BY id ASC"
        ).fetchall()
    out = []
    for r in rows:
        d = _row_to_dict(r)
        d.pop("api_key", None)
        out.append(d)
    return out


def get_provider() -> AIProvider:
    """يعيد المزوّd النشيط (الافتراضي إن وُجد) أو احتياطيًا: anthropic إن ضُبط
    عبر البيئة، وإلا noop."""
    row = None
    try:
        with db_session() as conn:
            row = _active_row(conn)
    except Exception:  # noqa: BLE001 — أي فشل في قراءة القاعدة يُسقط للاحتياطي
        row = None
    if row is not None:
        return provider_instance(_row_to_dict(row))
    if config.AI_PROVIDER == "anthropic" and config.ANTHROPIC_API_KEY:
        return AnthropicProvider(config.ANTHROPIC_API_KEY, config.AI_MODEL)
    return NoopProvider()


def _enabled_providers() -> list:
    """قائمة المزوّدين المفعّلين بالترتيب (الافتراضي أولًا).

    آخر احتياطي: NoopProvider (استجابة حتمية بلا شبكة) إن لم يُفعَّل أي
    مزوّد — يحافظ على سلوك «يعمل دائمًا» الأصلي (قرار D-021).
    """
    try:
        with db_session() as conn:
            rows = conn.execute(
                "SELECT id, name, type, base_url, api_key, model, enabled, is_default "
                "FROM ai_providers WHERE enabled = 1 "
                "ORDER BY is_default DESC, id ASC"
            ).fetchall()
    except Exception:  # noqa: BLE001 — قاعدة غير جاهزة: قائمة فارغة تُسقط للاحتياطي
        rows = []
    if rows:
        return [provider_instance(_row_to_dict(r)) for r in rows]
    if config.AI_PROVIDER == "anthropic" and config.ANTHROPIC_API_KEY:
        return [AnthropicProvider(config.ANTHROPIC_API_KEY, config.AI_MODEL)]
    return [NoopProvider()]


QUOTA_HINTS = (
    "quota", "rate limit", "rate_limit", "resource_exhausted", "429",
    "too many requests", "exceeded your current",
    "high demand", "temporarily", "try again later", "unavailable",
)

TEMPORARY_OVERLOAD_HINTS = (
    "high demand", "temporarily", "try again later", "unavailable",
    "overloaded", "capacity",
)


def _is_quota_error(exc: Exception) -> bool:
    """هل الخطأ استنفاد حصة/تجاوز حد المعدل (429) وليس خللًا تقنيًا؟"""
    if not isinstance(exc, AIProviderError):
        return False
    code = getattr(exc, "status_code", 0)
    if code == 429:
        return True
    msg = (exc.message or "").lower()
    return any(hint in msg for hint in QUOTA_HINTS)


def _is_temporary_overload(exc: Exception) -> bool:
    """هل الخطأ حمل مؤقت على المزوّد (503 + رسالة طلب عالي) أو خطأ تكوين
    مؤقت (404 — موديل غير موجود/متوقف)؟

    مزوّدات Gemini و OpenAI تُعيد 503 عند الذروة — خطأ عابر مثل 429
    يجب أن يُجرب عبر المزوّد الاحتياطي ولا يُسقط الطلب فورًا.
    يشمل أيضًا 404 (model not found) لأن بعض المزوّدين يُوقفون موديلات
    مجانية دون إشعار مسبق."""
    if not isinstance(exc, AIProviderError):
        return False
    code = getattr(exc, "status_code", 0)
    if code == 503:
        msg = (exc.message or "").lower()
        if any(hint in msg for hint in TEMPORARY_OVERLOAD_HINTS):
            return True
    if code == 404:
        msg = (exc.message or "").lower()
        if any(hint in msg for hint in ("model", "not found", "does not exist", "deprecated")):
            return True
    return False


NETWORK_ERROR_HINTS = (
    "getaddrinfo", "errno", "gaierror", "dns", "resolve", "connection",
    "timed out", "timeout", "network", "unreachable",
)


def _is_network_error(exc: Exception) -> bool:
    """هل الخطأ تقني (شبكة/DNS/مهلة) وليس منطق قانوني أو استنفاد حصة؟

    أخطاء مثل [Errno 11001] getaddrinfo failed عابرة عادة: معالجة شبكة مفصولة
    أو حاجز DNS مؤقت. مثل الأخطاء تعامل كما تعامل مَحاولات الاستنفاد: لا
    يُسقَط الطلب فورًا بل يُجرب المزوّد الاحتياطي التالي."""
    if not isinstance(exc, AIProviderError):
        return False
    code = getattr(exc, "status_code", 0)
    if code == 429:
        return False
    msg = (exc.message or "").lower()
    return any(hint in msg for hint in NETWORK_ERROR_HINTS)


def generate_with_fallback(question: str, context_articles: list, mode: str,
                           system: str | None = None,
                           user_prompt: str | None = None,
                           images: list | None = None):
    """يستدعي المزوّد المفعل؛ على استنفاد الحصة (429) أو حمل مؤقت (503) أو
    فشل شبكة/DNS عابر يجرب بقية المزوّدين المفعّلين تباعًا."""
    providers = _enabled_providers()
    if not providers:
        raise AIProviderError(
            "لا يوجد مزوّد ذكاء اصطناعي مفعّل. أضف مزوّدًا من لوحة التحكم.", 503
        )
    quota_errors = []
    network_errors = []
    overload_errors = []
    for provider in providers:
        try:
            return provider.generate(
                question, context_articles, mode,
                system=system, user_prompt=user_prompt, images=images
            ), provider
        except AIProviderError as exc:
            if _is_quota_error(exc):
                quota_errors.append((provider.name, exc))
                continue
            if _is_temporary_overload(exc):
                overload_errors.append((provider.name, exc))
                continue
            if _is_network_error(exc):
                network_errors.append((provider.name, exc))
                continue
            raise
        except (TimeoutError, OSError, ValueError, TypeError, KeyError) as exc:
            raise AIProviderError(
                "تعذر الاتصال بمزوّد الذكاء الاصطناعي. حاول لاحقًا.", 503
            ) from exc
    # كل المزوّدين فشلوا — أيُّ فئة سادت؟
    all_errors = quota_errors + overload_errors + network_errors
    if all_errors:
        last = all_errors[-1][1]
        detail = getattr(last, "message", "") if last else ""
        failed_names = ", ".join(name for name, _ in all_errors)
        if overload_errors and not quota_errors:
            raise AIProviderError(
                "مزوّدي الذكاء الاصطناعي محمّلون حاليًا. "
                f"({failed_names}) — أعد المحاولة بعد قليل أو أضف مزوّدًا آخر."
                + (f" — {detail[:200]}" if detail else ""),
                503,
            )
        if quota_errors:
            raise AIProviderError(
                "حصة الذكاء الاصطناعي المجانية مستنفدة حاليًا (429). "
                "أضف مفتاح مزوّد آخر من لوحة التحكم (مثل Groq المجاني) أو أعد "
                "المحاولة لاحقًا."
                + (f" — {detail[:200]}" if detail else ""),
                429,
            )
        raise AIProviderError(
            f"تعذر الاتصال بمزوّدي الذكاء الاصطناعي ({failed_names}). "
            "حدث خطأ شبكة/اتصال مؤقت"
            + (f": {detail[:200]}" if detail else "")
            + ". أعد المحاولة أو تحقق من الاتصال بالإنترنت.",
            503,
        )
    raise AIProviderError(
        "تعذر الحصول على رد من مزوّد الذكاء الاصطناعي. حاول لاحقًا.", 503
    )


def document_analysis(extracted_text: str = "", images: list | None = None,
                      question: str = "", user_id: int | None = None):
    """تحليل مرفق (PDF أو صورة): يستخرج النص/الصورة ويُرسله للمزوّد.

    images: قائمة dicts [{"mime": "image/jpeg", "data": "<base64>"}].
    """
    if not extracted_text and not images:
        raise AIProviderError("لا يوجد محتوى للتحليل (نص أو صورة).", 400)

    started = time.monotonic()

    if images:
        images_list = images
    else:
        images_list = None

    system, user_prompt = _build_prompt_with_attachment(
        question, extracted_text=extracted_text,
        image_data_url="data:{};base64,...".format(images[0]["mime"]) if images else "",
    )

    answer, provider = generate_with_fallback(
        question, [], "general",
        system=system, user_prompt=user_prompt, images=images_list
    )

    latency_ms = int((time.monotonic() - started) * 1000)
    _log_query(user_id, question, [], answer, "attachment", provider.name, latency_ms)

    return {
        "answer": answer,
        "cited_article_ids": [],
        "mode": "attachment",
        "source": "attachment",
        "status": "ok",
    }


def _require(data, keys):
    for k in keys:
        if not data.get(k):
            raise AIProviderError(f"الحقل «{k}» مطلوب.", 400)
    if data.get("type") not in PROVIDER_CLASSES:
        raise AIProviderError("نوع المزوّد غير معروف.", 400)


def create_provider(data: dict) -> dict:
    _require(data, ("name", "type"))
    name = str(data["name"])[:120]
    base_url = str(data.get("base_url") or "").strip()
    api_key = str(data.get("api_key") or "").strip()
    model = str(data.get("model") or "").strip()
    enabled = 1 if data.get("enabled") else 0
    with db_session() as conn:
        has_enabled = conn.execute(
            "SELECT COUNT(*) FROM ai_providers WHERE enabled = 1"
        ).fetchone()[0]
        cur = conn.execute(
            "INSERT INTO ai_providers (name, type, base_url, api_key, model, enabled, is_default) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, data["type"], base_url, api_key, model, enabled, int(enabled and not has_enabled)),
        )
        pid = cur.lastrowid
    return {"id": pid, "message": "أضِيف المزوّد."}


def update_provider(pid: int, data: dict) -> dict:
    with db_session() as conn:
        if conn.execute("SELECT id FROM ai_providers WHERE id = ?", (pid,)).fetchone() is None:
            raise AIProviderError("المزوّد غير موجود.", 404)
        fields, vals = [], []
        for col in ("name", "type", "base_url", "api_key", "model"):
            if col in data:
                fields.append(f"{col} = ?")
                vals.append(str(data[col] or "").strip())
        if "enabled" in data:
            fields.append("enabled = ?")
            vals.append(1 if data["enabled"] else 0)
        if fields:
            vals.append(pid)
            conn.execute(
                f"UPDATE ai_providers SET {', '.join(fields)},"
                f" updated_at = datetime('now') WHERE id = ?",
                vals,
            )
    return {"id": pid, "message": "حُدّث المزوّد."}


def delete_provider(pid: int) -> dict:
    with db_session() as conn:
        conn.execute("DELETE FROM ai_providers WHERE id = ?", (pid,))
    return {"id": pid, "message": "حُذف المزوّd."}


def set_default_provider(pid: int) -> dict:
    with db_session() as conn:
        if conn.execute("SELECT id FROM ai_providers WHERE id = ?", (pid,)).fetchone() is None:
            raise AIProviderError("المزوّd غير موجود.", 404)
        conn.execute("UPDATE ai_providers SET is_default = 0")
        conn.execute(
            "UPDATE ai_providers SET is_default = 1, enabled = 1,"
            " updated_at = datetime('now') WHERE id = ?",
            (pid,),
        )
    return {"id": pid, "message": "أصبح المزوّd الافتراضي."}


def test_provider(data: dict) -> dict:
    """ينشئ مزوّدًا مؤقتًا من البيانات المقدَّمة ويختبر اتصالًا حقيقيًا."""
    _require(data, ("type",))
    row = {
        "type": data["type"],
        "api_key": data.get("api_key") or "",
        "model": data.get("model") or "",
        "base_url": data.get("base_url") or "",
    }
    prov = provider_instance(row)
    started = time.monotonic()
    try:
        reply = prov.ping()
    except AIProviderError as exc:
        return {"ok": False, "error": exc.message}
    latency_ms = int((time.monotonic() - started) * 1000)
    return {"ok": True, "provider": prov.name, "latency_ms": latency_ms, "preview": reply[:200]}


# ---------------------------------------------------------------------------
# الأرقام المساعدة: استخراج الاستشهادات + التسجيل
# ---------------------------------------------------------------------------
def _article_number_from_label(label: str) -> str | None:
    if not label:
        return None
    m = re.search(r"(\d+)\s*/\s*(\d+)", label)
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    m = re.search(r"\d+", label)
    return m.group(0) if m else None


def _extract_cited_article_ids(answer: str, retrieved: list) -> list:
    cited_numbers = set(
        re.findall(r"المادة\s*[\[\(（]?\s*(\d+(?:/\d+)?)\s*[\]\)）]?", answer)
    )
    id_by_number = {}
    for article in retrieved:
        number = _article_number_from_label(article.get("label"))
        if number:
            id_by_number.setdefault(number, article["id"])
    return [id_by_number[n] for n in cited_numbers if n in id_by_number]


def _retrieve_decisions(question: str) -> list:
    """استرجاع اجتهادات قضائية متصلة بالسؤال (بلا أخطاء تُسقط الإجابة).

    يجرّب البحث FTS عبر search_decisions، وإن فشل (فهرس/بنية) يعود بقائمة
    فارغة — الاجتهاد مؤيِّد اختياري لا يُفشل الإجابة الموجَّهة.
    """
    limit = max(0, int(config.AI_JURISPRUDENCE_LIMIT or 0))
    if limit <= 0:
        return []
    try:
        return search_decisions(question, limit=limit)
    except Exception:  # noqa: BLE001 — الاجتهاد مؤيِّد اختياري: فشله لا يُفشل الإجابة
        return []


def _extract_cited_decision_ids(answer: str, retrieved: list) -> list:
    """يعيد معرفات الاجتهادات المسترجعة التي استُشهد بها فعلًا في الرد.

    الاجتهاد المذكور يُتعرَّف عليه برقم قراره (مثل «2021/158») — كما
    جرت عليه ترويسة السياق «— رقم 2021/158». حصرية للمسترجَع فقط.
    """
    if not answer or not retrieved:
        return []
    cited = []
    for d in retrieved:
        num = (d.get("decision_number") or "").strip()
        if not num:
            continue
        if num in answer:
            cited.append(d["id"])
    return cited


def _log_query(user_id, question, retrieved_ids, response, mode, provider, latency_ms):
    """سجل الحد الأدنى — لا تُخزَّن محادثات المستخدمين (خصوصية المنصة العامة).

    لا يحفظ سؤال الزائر ولا إجابة المزوّد (قد يحملان بيانات شخصية — وثيقة
    الخصوصية §٦). يُخزَّن فقط عدد استرجاع الاستشهادات + الوضع + المزوّد
    + زمن الاستجابة لأغراض المراقبة الصارمة. مسار analytics يقرأ هذه
    الصفوف للعدّ فقط (لا محتوى).
    """
    with db_session() as conn:
        conn.execute(
            "INSERT INTO ai_queries "
            "(user_id, question, retrieved_article_ids, response, mode, provider, latency_ms) "
            "VALUES (?, '', ?, '', ?, ?, ?)",
            (user_id, json.dumps(retrieved_ids) if retrieved_ids else None,
             mode, provider, latency_ms),
        )


def grounded_explanation(question: str, user_id: int | None = None):
    expanded = expand_query(question)
    retrieved = services.search_articles(
        expanded, limit=config.AI_RETRIEVAL_LIMIT, min_terms=2
    )
    decisions = _retrieve_decisions(question)
    started = time.monotonic()
    if not retrieved and not decisions:
        provider = get_provider()
        answer = (
            "لم نعثر في مكتبة نبراس على مواد قانونية تنطبق على سؤالك. "
            "أعد صياغة السؤال بألفاظ قانونية أدق، أو استخدم الوضع العام."
        )
        latency_ms = int((time.monotonic() - started) * 1000)
        _log_query(user_id, question, [], answer, "grounded", provider.name, latency_ms)
        return {
            "answer": answer,
            "cited_article_ids": [],
            "cited_decision_ids": [],
            "mode": "general",
            "status": "no_source",
        }
    system, user_prompt = _build_prompt(
        question, retrieved, "grounded", context_decisions=decisions
    )
    answer, provider = generate_with_fallback(
        question, retrieved, "grounded", system=system, user_prompt=user_prompt
    )
    latency_ms = int((time.monotonic() - started) * 1000)
    cited_ids = _extract_cited_article_ids(answer, retrieved)
    cited_dec = _extract_cited_decision_ids(answer, decisions)
    _log_query(user_id, question, cited_ids, answer, "grounded", provider.name, latency_ms)
    return {
        "answer": answer,
        "cited_article_ids": cited_ids,
        "cited_decision_ids": cited_dec,
        "mode": "grounded",
        "status": "ok",
    }


def research_explanation(question: str, user_id: int | None = None):
    """وضع المقارنة: استرجاع مواد نبراس + بحث ويب خارجي + إجابة مقارنة.

    إن أخفق البحث الخارجي أو وُجد صفر نتائج، تُعاد الإجابة من نبراس فقط
    (لا يفشل الوضع بسبب المصادر الخارجية). الاستشهادات تبقى حصريةً لمواد
    نبراس المسترجعة.
    """
    retrieved = services.search_articles(
        expand_query(question), limit=config.AI_RETRIEVAL_LIMIT, min_terms=2
    )
    decisions = _retrieve_decisions(question)
    web_results = []
    if config.AI_WEBSEARCH_LIMIT > 0:
        try:
            web_results = search_web(question, limit=config.AI_WEBSEARCH_LIMIT)
        except Exception:  # noqa: BLE001 — الويب اختياري: فشله لا يُفشل الإجابة
            web_results = []
        web_results = web_results[: config.AI_WEBSEARCH_LIMIT]

    provider = get_provider()
    started = time.monotonic()
    if not retrieved and not web_results:
        answer = (
            "لم نعثر في مكتبة نبراس على مواد قانونية تنطبق على سؤالك، ولا على "
            "مقالات خارجية موثوقة. أعد صياغة السؤال بألفاظ قانونية أدق، أو "
            "استخدم الوضع العام."
        )
        latency_ms = int((time.monotonic() - started) * 1000)
        _log_query(user_id, question, [], answer, "research", provider.name, latency_ms)
        return {
            "answer": answer,
            "cited_article_ids": [],
            "cited_decision_ids": [],
            "external_sources": [],
            "mode": "research",
            "status": "no_source",
        }

    system, user_prompt = _build_research_prompt(
        question, retrieved, web_results, context_decisions=decisions
    )
    answer, provider = generate_with_fallback(
        question, retrieved, "research", system=system, user_prompt=user_prompt
    )
    latency_ms = int((time.monotonic() - started) * 1000)
    cited_ids = _extract_cited_article_ids(answer, retrieved)
    cited_dec = _extract_cited_decision_ids(answer, decisions)
    _log_query(user_id, question, cited_ids, answer, "research", provider.name, latency_ms)
    return {
        "answer": answer,
        "cited_article_ids": cited_ids,
        "cited_decision_ids": cited_dec,
        "external_sources": web_results,
        "mode": "research",
        "status": "ok",
    }


def general_explanation(question: str, user_id: int | None = None):
    started = time.monotonic()
    answer, provider = generate_with_fallback(question, [], "general")
    latency_ms = int((time.monotonic() - started) * 1000)
    _log_query(user_id, question, [], answer, "general", provider.name, latency_ms)
    return {"answer": answer, "cited_article_ids": [], "mode": "general", "status": "ok"}


def auto_explanation(question: str, user_id: int | None = None):
    """الوضع التلقائي: تتابع ذكي — نبراس أولاً → بحث ويب إن لم يُغطِ → إجابة عامة.

    الخطوات:
    1. بحث في مكتبة نبراس (FTS + اجتهادات).
    2. إن وُجدت نتائج → إجابة موثقة (grounded) مع مصدر: nibras.
    3. إن لم تُعثر نتائج → بحث ويب خارجي.
    4. إن وُجدت نتائج ويب → إجابة مقارنة (research) مع مصدر: web.
    5. إن لم يُعثر على شيء → إجابة عامة مع مصدر: general + توضيح.
    """
    started = time.monotonic()

    # الخطوة 1: بحث في مكتبة نبراس (بتوسعة الاستعلام)
    expanded = expand_query(question)
    retrieved = services.search_articles(
        expanded, limit=config.AI_RETRIEVAL_LIMIT, min_terms=2
    )
    decisions = _retrieve_decisions(question)

    # الخطوة 2: إن وُجدت نتائج نبراس → إجابة موثقة
    if retrieved or decisions:
        system, user_prompt = _build_prompt(
            question, retrieved, "grounded", context_decisions=decisions
        )
        answer, provider = generate_with_fallback(
            question, retrieved, "grounded", system=system, user_prompt=user_prompt
        )
        latency_ms = int((time.monotonic() - started) * 1000)
        cited_ids = _extract_cited_article_ids(answer, retrieved)
        cited_dec = _extract_cited_decision_ids(answer, decisions)
        _log_query(user_id, question, cited_ids, answer, "auto", provider.name, latency_ms)
        return {
            "answer": answer,
            "cited_article_ids": cited_ids,
            "cited_decision_ids": cited_dec,
            "mode": "auto",
            "source": "nibras",
            "status": "ok",
        }

    # الخطوة 3: بحث ويب خارجي
    web_results = []
    if config.AI_WEBSEARCH_LIMIT > 0:
        try:
            web_results = search_web(question, limit=config.AI_WEBSEARCH_LIMIT)
        except Exception:  # noqa: BLE001 — الويب اختياري
            web_results = []
        web_results = web_results[: config.AI_WEBSEARCH_LIMIT]

    # الخطوة 4: إن وُجدت نتائج ويب → إجابة مقارنة
    if web_results:
        system, user_prompt = _build_research_prompt(
            question, [], web_results, context_decisions=None
        )
        answer, provider = generate_with_fallback(
            question, [], "research", system=system, user_prompt=user_prompt
        )
        latency_ms = int((time.monotonic() - started) * 1000)
        _log_query(user_id, question, [], answer, "auto", provider.name, latency_ms)
        return {
            "answer": answer,
            "cited_article_ids": [],
            "cited_decision_ids": [],
            "external_sources": web_results,
            "mode": "auto",
            "source": "web",
            "status": "ok",
        }

    # الخطوة 5: إجابة عامة مع توضيح
    answer, provider = generate_with_fallback(question, [], "general")
    latency_ms = int((time.monotonic() - started) * 1000)
    _log_query(user_id, question, [], answer, "auto", provider.name, latency_ms)
    return {
        "answer": answer,
        "cited_article_ids": [],
        "cited_decision_ids": [],
        "mode": "auto",
        "source": "general",
        "status": "ok",
    }
