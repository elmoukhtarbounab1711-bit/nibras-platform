// نبراس — إدارة SEO ديناميكية: تحديث العنوان/الوصف/البيانات المهيكلة بعد كل تنقّل.
// الواجهة SPA قائمة على hash، لكن جوجل ينفّذ جافاسكربت ويقرأ DOM، لذا نقوم بضبط
// الوسوم ديناميكيًا بعد كل رندر لنمنح كل "صفحة" عنوانًا ووصفًا وبيانات مهيكلة.

const SITE = "https://nibras-law-platforme.vercel.app";
const OG_IMAGE = "/assets/img/og-cover.png";

function ensureMeta(name) {
  let el = document.querySelector(`meta[name="${name}"]`);
  if (!el) {
    el = document.createElement("meta");
    el.setAttribute("name", name);
    document.head.appendChild(el);
  }
  return el;
}
function ensureProp(prop) {
  let el = document.querySelector(`meta[property="${prop}"]`);
  if (!el) {
    el = document.createElement("meta");
    el.setAttribute("property", prop);
    document.head.appendChild(el);
  }
  return el;
}
function setCanonical(href) {
  let el = document.querySelector('link[rel="canonical"]');
  if (!el) {
    el = document.createElement("link");
    el.setAttribute("rel", "canonical");
    document.head.appendChild(el);
  }
  el.setAttribute("href", href);
}
function setJsonLd(scriptId, obj) {
  let el = document.getElementById(scriptId);
  if (!el) {
    el = document.createElement("script");
    el.type = "application/ld+json";
    el.id = scriptId;
    document.head.appendChild(el);
  }
  el.textContent = JSON.stringify(obj);
}

// قاعدة عامة لكل مسار: { base, desc, jsonLd? }
const ROUTE_META = [
  { re: /^\/laws\/(\d+)/, base: "نص قانوني", desc: "نص قانوني مغربي — الاطلاع على المادة القانونية كاملة في مكتبة نبراس القانونية." },
  { re: /^\/text\/(\d+)/, base: "نص قانوني", desc: "نص قانوني مغربي — الاطلاع على المادة القانونية كاملة في مكتبة نبراس القانونية." },
  { re: /^\/pdf\/(\d+)/, base: "ملف PDF", desc: "الملف الرسمي للنص القانوني في مكتبة نبراس." },
  { re: /^\/jurisprudence\/(\d+)/, base: "اجتهاد قضائي", desc: "قرار واجتهاد قضائي من المحاكم المغربية — عرض المبدأ والنص في منصة نبراس." },
  { re: /^\/library\/domain\/(\d+)/, base: "مكتبة نصوص قانونية", desc: "تصفح النصوص القانونية حسب المجال في مكتبة نبراس — قوانين وظهائر ومراسيم مغربية." },
  { re: /^\/procedures\/([^/]+)/, base: "مسطرة إدارية", desc: "خطوات وتفاصيل مسطرة إدارية في المنصة — دليل عملي للإجراءات الإدارية المغربية." },
  { re: /^\/legal-french\/treaty\/(\d+)/, base: "مصطلح قانوني", desc: "مصطلح قانوني فرنسي مع شرح مقارن — أداة اللغة القانونية في نبراس." },
  { re: /^\/legal-french\/lesson\/(\d+)/, base: "درس قانوني", desc: "درس في اللغة القانونية الفرنسية مع تمارين — منصة نبراس التعليمية." },
  { re: /^\/research\/(\d+)/, base: "كتاب باحث", desc: "مرجع من مكتبة الباحث القانونية في نبراس — مراجع ودراسات قانونية." },
  { re: /^\/blog\/(\d+)/, base: "مقال", desc: "مقال قانوني من مدونة نبراس — مستجدات وشروحات قانونية." },
  { re: /^\/community\/(\d+)/, base: "نقاش مجتمع", desc: "نقاش من مجتمع نبراس — أسئلة قانونية ونقاشات بين الأعضاء." },
  { re: /^\/documents\/([^/]+)/, base: "مستند", desc: "نموذج مستند قانوني في منصة نبراس — وثائق قابلة للتخصيص." },
];

// استخراج عنوان الصفحة من DOM بعد الرندر (h1 رئيسي)
function extractH1() {
  const view = document.getElementById("view");
  if (!view) return "";
  const h1 = view.querySelector("h1");
  return (h1 && h1.textContent.trim()) || "";
}

// وصف افتراضي حسب القسم العام
function sectionDesc(base) {
  const map = {
    library: "المكتبة القانونية المغربية: قوانين، ظهائر، مراسيم، مدوّنات مرتبة حسب المجالات والقواعد.",
    jurisprudence: "الاجتهادات القضائية: قرارات ومبادئ المحاكم المغربية مصنفة حسب الموضوع مع البحث بالكلمة.",
    research: "مكتبة الباحث: مراجع ودراسات وكتب قانونية متخصصة للبحث والدراسة.",
    procedures: "المساطر الإدارية: شرح خطوة بخطوة للإجراءات الإدارية والقانونية في المغرب.",
    "legal-french": "اللغة القانونية الفرنسية: مصطلحات ومرادفات لاتينية (FFFF) مع شروحات مقارنة.",
    documents: "مولد الوثائق: نماذج مستندات وعقود قانونية قابلة للتخصيص والتحميل.",
    assistant: "المساعد القانوني الذكي: أجوبة وتحليلات قانونية مبنية على النصوص المغربية.",
    blog: "مدونة نبراس: مقالات ومستجدات وتوعية قانونية.",
    community: "مجتمع نبراس: أسئلة ونقاشات قانونية بين المحامين والعموم.",
    calculators: "الحاسبات القانونية المغربية: حساب التعويضات، الأجور، التقاعد وأكثر.",
    comparative: "الفقه المقارن: مقارنة الأنظمة القانونية عبر القضاء والدراسات.",
    professionals: "دليل المهنيين: محامون وموثّقون وخبراء في المنصة.",
    profile: "الملف الشخصي وحسابي في منصة نبراس.",
    billing: "محفظتي والاشتراكات في منصة نبراس.",
    notifications: "إشعاراتي في منصة نبراس.",
    login: "تسجيل الدخول إلى منصة نبراس القانونية.",
    home: "وتوعية قانونية في مكان واحد — المكتبة، الاجتهادات، المساطر، المساعد الذكي، مولد الوثائق.",
  };
  return map[base] || "منصة نبراس القانونية المغربية — نصوص قانونية واجتهادات قضائية وأدوات قانونية.";
}

export function applySeo(path, params) {
  const cleanPath = (path || "/").split("?")[0];
  const base = cleanPath.split("/").filter(Boolean)[0] || "home";
  const h1 = extractH1();
  const url = SITE + (cleanPath === "/home" ? "/" : cleanPath);

  // العنوان
  let title = "";
  const routeRule = ROUTE_META.find((r) => r.re.test(cleanPath));
  if (routeRule) {
    title = h1 ? `${h1} — ${routeRule.base} | نبراس` : `${routeRule.base} | نبراس`;
  } else if (base === "home") {
    title = h1 ? `${h1} | نبراس` : "نبراس — منصة القانون المغربي";
  } else if (h1) {
    title = `${h1} | نبراس`;
  } else {
    const headMap = { library: "المكتبة القانونية", jurisprudence: "الاجتهادات القضائية", research: "مكتبة الباحث" };
    title = `${headMap[base] || sectionLabel(base)} | نبراس`;
  }
  document.title = title;

  // الوصف
  let desc = routeRule ? routeRule.desc : sectionDesc(base);
  ensureMeta("description").setAttribute("content", desc);

  // Open Graph + Twitter
  setCanonical(url);
  ensureProp("og:title").setAttribute("content", title);
  ensureProp("og:description").setAttribute("content", desc);
  ensureProp("og:url").setAttribute("content", url);
  ensureProp("og:type").setAttribute("content", h1 && /\d/.test(cleanPath) ? "article" : "website");
  ensureProp("og:image").setAttribute("content", SITE + OG_IMAGE);
  ensureProp("og:image:alt").setAttribute("content", "نبراس — منصة القانون المغربي");
  ensureMeta("twitter:card").setAttribute("content", "summary_large_image");
  ensureProp("twitter:title").setAttribute("content", title);
  ensureProp("twitter:description").setAttribute("content", desc);
  ensureProp("twitter:image").setAttribute("content", SITE + OG_IMAGE);

  // بيانات مهيكلة: WebSite ثابتة + Breadcrumb ديناميكي
  setJsonLd("seo-website", {
    "@context": "https://schema.org",
    "@type": "WebSite",
    name: "نبراس",
    alternateName: "Nibras — Plateforme juridique marocaine",
    url: SITE,
    inLanguage: ["ar", "fr"],
    potentialAction: {
      "@type": "SearchAction",
      target: { "@type": "EntryPoint", urlTemplate: SITE + "/#/library/q/{search_term_string}" },
      "query-input": "required name=search_term_string",
    },
  });

  if (cleanPath !== "/" && cleanPath !== "/home") {
    const crumbs = [{ name: "نبراس", path: SITE + "/" }];
    const parts = cleanPath.split("/").filter(Boolean);
    let acc = "";
    parts.forEach((p, i) => {
      acc += "/" + p;
      const label = i === 0 && sectionLabel(p) ? sectionLabel(p) : (p === parts.at(-1) && h1 ? h1 : decodeURIComponent(p));
      crumbs.push({ name: typeof label === "string" ? label : "نبراس", path: SITE + acc });
    });
    setJsonLd("seo-breadcrumb", {
      "@context": "https://schema.org",
      "@type": "BreadcrumbList",
      itemListElement: crumbs.map((c, i) => ({ "@type": "ListItem", position: i + 1, name: c.name, item: c.path })),
    });
  } else {
    document.getElementById("seo-breadcrumb")?.remove();
  }
}

export function sectionLabel(base) {
  const m = {
    library: "المكتبة القانونية",
    laws: "المكتبة القانونية",
    jurisprudence: "الاجتهادات القضائية",
    research: "مكتبة الباحث",
    procedures: "المساطر",
    "legal-french": "اللغة القانونية",
    documents: "الوثائق",
    assistant: "المساعد الذكي",
    blog: "المدونة",
    community: "المجتمع",
    calculators: "الحاسبات",
    comparative: "الفقه المقارن",
    professionals: "المهنيون",
    profile: "حسابي",
    billing: "محفظتي",
    notifications: "الإشعارات",
  };
  return m[base] || "نبراس";
}
