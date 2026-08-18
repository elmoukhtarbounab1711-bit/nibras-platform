// نبراس — صفحات قانونية: سياسة الخصوصية + شروط الاستخدام + سياسة ملفات الارتباط
import { tr, currentLang } from "../i18n.js";
import { api } from "../api.js";
import { el, emptyState } from "../ui.js";
import { icon } from "../icons.js";
import { navigate } from "../router.js";

/* ─────────────── مكوّن مشترك ─────────────── */

function legalPage(title, subtitle, sections, lastUpdated) {
  const hero = el("section", { class: "lib-hero" }, [
    el("div", { class: "hero-bg" }),
    el("span", { class: "hero-crown" }, [icon("shield", 30)]),
    el("span", { class: "hero-eyebrow" }, [
      icon("shield", 15),
      tr("legalNav"),
    ]),
    el("h1", { text: title }),
    el("p", { class: "hero-sub", text: subtitle }),
  ]);

  const tocItems = sections.map((s, i) =>
    el("li", {}, [
      el("a", {
        href: `#section-${i}`,
        text: s.title,
        onclick: (e) => {
          e.preventDefault();
          document.getElementById(`section-${i}`)?.scrollIntoView({ behavior: "smooth" });
        },
      }),
    ])
  );

  const sectionEls = sections.map((s, i) => {
    const children = [];
    if (s.lead) children.push(el("p", { class: "legal-lead", text: s.lead }));
    if (s.items) {
      children.push(el("ol", { class: "legal-list" },
        s.items.map(item => el("li", { html: item }))
      ));
    }
    if (s.content) children.push(el("p", { class: "legal-text", text: s.content }));
    if (s.subsections) {
      for (const sub of s.subsections) {
        children.push(el("h4", { text: sub.title }));
        if (sub.content) children.push(el("p", { class: "legal-text", text: sub.content }));
        if (sub.items) {
          children.push(el("ul", { class: "legal-list" },
            sub.items.map(item => el("li", { html: item }))
          ));
        }
      }
    }
    if (s.table) {
      const rows = s.table.rows.map(r =>
        el("tr", {}, r.map(c => el("td", { html: c })))
      );
      const headerRow = el("tr", {}, s.table.headers.map(h => el("th", { text: h })));
      children.push(el("div", { class: "legal-table-wrap" }, [
        el("table", { class: "legal-table" }, [el("thead", {}, [headerRow]), el("tbody", {}, rows)]),
      ]));
    }
    return el("section", { id: `section-${i}`, class: "legal-section" }, [
      el("h2", { text: s.title }),
      ...children,
    ]);
  });

  return el("div", {}, [
    hero,
    el("section", { class: "content-section" }, [
      el("button", {
        class: "btn btn-ghost btn-sm mb-16",
        text: `← ${tr("back")}`,
        onclick: () => history.back(),
      }),
      el("div", { class: "card", style: "padding:2rem" }, [
        el("div", { class: "legal-meta" }, [
          el("span", { class: "badge-pill badge-navy", text: `${tr("lastUpdated")}: ${lastUpdated}` }),
          el("span", { class: "badge-pill", style: "margin-inline-start:8px", text: `${tr("legalVersion")}: 1.0` }),
        ]),
        el("nav", { class: "legal-toc" }, [
          el("h3", { text: tr("toc") }),
          el("ol", {}, tocItems),
        ]),
        ...sectionEls,
      ]),
    ]),
  ]);
}


/* ═══════════════════════════════════════════════════════════════════
   سياسة الخصوصية — القانون 09-08
   ═══════════════════════════════════════════════════════════════════ */

export async function privacyView() {
  const isFr = currentLang() === "fr";

  if (isFr) {
    return legalPage(
      "Politique de Confidentialité",
      "Conformément à la Loi 09-08 relative à la protection des personnes physiques",
      [
        {
          title: "1. Responsable du traitement",
          content: "La plateforme Nibras (ci-après « la Plateforme ») est responsable du traitement des données personnelles collectées. Pour toute question relative à la protection de vos données, vous pouvez nous contacter via l'adresse e-mail indiquée sur la Plateforme.",
        },
        {
          title: "2. Données collectées",
          lead: "Nous collectons uniquement les données strictement nécessaires au fonctionnement de la Plateforme :",
          items: [
            "<strong>Données d'inscription</strong> : adresse e-mail, nom complet, mot de passe (haché par argon2id).",
            "<strong>Rôle sélectionné</strong> : citoyen, étudiant, avocat, notaire, etc.",
            "<strong>Données de connexion</strong> : journal d'authentification (adresses IP, agents utilisateur, horodatages).",
            "<strong>Consentements</strong> : acceptation de la politique de confidentialité et des conditions d'utilisation.",
          ],
        },
        {
          title: "3. Finalité du traitement",
          lead: "Vos données sont traitées uniquement pour les finalités suivantes :",
          items: [
            "Authentification et gestion de votre compte utilisateur.",
            "Fourniture des services juridiques de la Plateforme (bibliothèque, jurisprudence, calculatrices, documents).",
            "Protection contre les tentatives de connexion non autorisées (limitation du débit, verrouillage de compte).",
            "Amélioration de la qualité du service et maintenance technique.",
          ],
        },
        {
          title: "4. Base légale du traitement",
          content: "Le traitement de vos données repose sur votre consentement explicite (article 6 de la Loi 09-08) et sur l'exécution du contrat de service que vous acceptez lors de votre inscription.",
        },
        {
          title: "5. Durée de conservation",
          content: "Vos données personnelles sont conservées pendant toute la durée d'activité de votre compte. En cas de suppression de compte, toutes les données sont effacées de manière permanente dans un délai de 30 jours.",
        },
        {
          title: "6. Sécurité des données",
          items: [
            "Mots de passe hachés avec argon2id (algorithme résistant aux attaques matérielles).",
            "Tokens JWT à durée courte (15 minutes) avec rotation des tokens de rafraîchissement.",
            "Authentification à deux facteurs (TOTP) obligatoire pour les administrateurs.",
            "Protection contre les attaques par timing lors de la vérification des e-mails.",
            "Journalisation complète de tous les événements d'authentification.",
          ],
        },
        {
          title: "7. Vos droits (Loi 09-08)",
          lead: "Conformément à la Loi 09-08, vous disposez des droits suivants :",
          table: {
            headers: ["Droit", "Description", "Comment l'exercer"],
            rows: [
              ["Droit d'accès", "Obtenir une copie de toutes vos données personnelles.", "GET /api/auth/data-export"],
              ["Droit de rectification", "Modifier vos informations de profil.", "Page Profil de la Plateforme"],
              ["Droit à l'effacement", "Supprimer définitivement votre compte et toutes vos données.", "POST /api/auth/data-delete"],
              ["Droit à la portabilité", "Exporter vos données dans un format structuré.", "GET /api/auth/data-export"],
              ["Droit de retrait du consentement", "Retirer votre consentement à tout moment.", "Suppression du compte"],
            ],
          },
        },
        {
          title: "8. Transfert international de données",
          content: "Vos données ne sont pas transférées en dehors du Maroc. Tout transfert international, le cas échéant, sera soumis aux garanties prévues par la Loi 09-08.",
        },
        {
          title: "9. Cookies",
          content: "Voir notre Politique de Cookies dédiée pour plus d'informations sur l'utilisation des cookies et traceurs.",
        },
        {
          title: "10. Réclamation",
          content: "Si vous estimez que le traitement de vos données n'est pas conforme à la réglementation, vous pouvez adresser une réclamation à l'Autorité Nationale de Protection des Données à Caractère Personnel (ANPDP).",
        },
        {
          title: "11. Contact",
          content: "Pour toute question relative à cette politique de confidentialité, contactez-nous via les canaux indiqués sur la Plateforme.",
        },
      ],
      "01 janvier 2025"
    );
  }

  return legalPage(
    "سياسة الخصوصية",
    "وفقاً للقانون 09-08 المتعلق بحماية الأشخاص الطبيعيين في المعالجة الآلية للمعطيات الشخصية",
    [
      {
        title: "١. مسؤول المعالجة",
        content: "منصة نبراس (يُشار إليها بـ « المنصة ») هي مسؤولة عن معالجة المعطيات الشخصية التي تُجمَع. لأي سؤال يتعلق بحماية بياناتك، يمكنك التواصل عبر البريد الإلكتروني المُشار إليه في المنصة.",
      },
      {
        title: "٢. المعطيات المُجمَعة",
        lead: "نجمع فقط المعطيات الضرورية لتشغيل المنصة:",
        items: [
          "<strong>معطيات التسجيل</strong>: البريد الإلكتروني، الاسم الكامل، كلمة المرور (مُجزَّأة بـ argon2id).",
          "<strong>الدور المُختار</strong>: مواطن، طالب، محامٍ، موثق، عدل، إلخ.",
          "<strong>معطيات الاتصال</strong>: سجل المصادقة (عناوين IP، وكلاء المستخدم، والتوقيتات).",
          "<strong>الموافقات</strong>: قبول سياسة الخصوصية وشروط الاستخدام.",
        ],
      },
      {
        title: "٣. غاية المعالجة",
        lead: "تُعالَج معطياتك فقط للأغراض التالية:",
        items: [
          "المصادقة وإدارة حسابك كمستخدم.",
          "توفير الخدمات القانونية في المنصة (المكتبة، الاجتهادات، الحاسبات، الوثائق).",
          "الحماية من محاولات الاتصال غير المصرح بها (تحديد المعدل، قفل الحساب).",
          "تحسين جودة الخدمة والصيانة التقنية.",
        ],
      },
      {
        title: "٤. الأساس القانوني للمعالجة",
        content: "يقوم معالجة معطياتك على موافقتك الصريحة (المادة 6 من القانون 09-08) وتنفيذ عقد الخدمة الذي تقبله عند التسجيل.",
      },
      {
        title: "٥. مدة الاحتفاظ بالمعطيات",
        content: "تُحتفظ بمعطياتك الشخصية طوال مدة نشاط حسابك. في حالة حذف الحساب، تُمحو جميع المعطيات بشكل نهائي خلال 30 يوماً.",
      },
      {
        title: "٦. أمان المعطيات",
        items: [
          "كلمات المرور مُجزَّأة بـ argon2id (خوارزمية مقاومة للهجمات المادية).",
          "توكنات JWT قصيرة العمر (15 دقيقة) مع تدوير توكنات التحديث.",
          "التحقق بخطوتين (TOTP) إلزامي للمشرفين.",
          "الحماية من هجمات التوقيت عند التحقق من عناوين البريد.",
          "تسجيل كامل لكل أحداث المصادقة.",
        ],
      },
      {
        title: "٧. حقوقك (القانون 09-08)",
        lead: "وفقاً للقانون 09-08، لديك الحقوق التالية:",
        table: {
          headers: ["الحق", "الوصف", "كيفية ممارسته"],
          rows: [
            ["حق الوصول", "الحصول على نسخة من جميع معطياتك الشخصية.", "GET /api/auth/data-export"],
            ["حق التصحيح", "تعديل معلومات ملفك الشخصي.", "صفحة الملف الشخصي في المنصة"],
            ["حق المحو", "حذف حسابك وجميع معطياتك نهائياً.", "POST /api/auth/data-delete"],
            ["حق النقل", "تصدير معطياتك بصيغة منظمة.", "GET /api/auth/data-export"],
            ["حق سحب الموافقة", "سحب موافقتك في أي وقت.", "حذف الحساب"],
          ],
        },
      },
      {
        title: "٨. النقل الدولي للمعطيات",
        content: "لا تُنقل معطياتك خارج المغرب. أي نقل دولي، إن وُجد، будетخضع للضمانات المنصوص عليها في القانون 09-08.",
      },
      {
        title: "٩. ملفات تعريف الارتباط (Cookies)",
        content: "راجع سياسة ملفات تعريف الارتباط الخاصة بنا لمزيد من المعلومات حول استخدام ملفات تعريف الارتباط.",
      },
      {
        title: "١٠. الشكوى",
        content: "إذا كنت تعتقد أن معالجة معطياتك غير متوافقة مع التنظيمات المعمول بها، يمكنك تقديم شكوى لدى الهيئة الوطنية لحماية المعطيات الشخصية.",
      },
      {
        title: "١١. الاتصال",
        content: "لأي سؤال يتعلق بسياسة الخصوصية هذه، يرجى التواصل معنا عبر القنوات المُشار إليها في المنصة.",
      },
    ],
    "01 يناير 2025"
  );
}


/* ═══════════════════════════════════════════════════════════════════
   شروط الاستخدام
   ═══════════════════════════════════════════════════════════════════ */

export async function termsView() {
  const isFr = currentLang() === "fr";

  if (isFr) {
    return legalPage(
      "Conditions d'Utilisation",
      "En vigueur depuis le 01 janvier 2025",
      [
        {
          title: "1. Acceptation des conditions",
          content: "En créant un compte ou en utilisant la plateforme Nibras, vous acceptez sans réserve les présentes conditions d'utilisation. Si vous n'acceptez pas ces conditions, veuillez ne pas utiliser la Plateforme.",
        },
        {
          title: "2. Description du service",
          content: "Nibras est une plateforme d'information juridique mettant à disposition : une bibliothèque de textes juridiques marocains, une base de données de jurisprudence, des calculatrices juridiques, des modèles de documents, un assistant juridique par intelligence artificielle et une communauté d'utilisateurs.",
        },
        {
          title: "3. Inscription et compte",
          items: [
            "Vous devez fournir des informations exactes et complètes lors de votre inscription.",
            "Vous êtes responsable de la sécurité de votre mot de passe.",
            "Un seul compte par personne est autorisé.",
            "L'inscription est soumise à l'acceptation de notre Politique de Confidentialité.",
            "Les rôles professionnels (avocat, notaire, etc.) sont soumis à vérification.",
          ],
        },
        {
          title: "4. Règles d'utilisation",
          lead: "Vous vous engagez à :",
          items: [
            "Utiliser la Plateforme uniquement à des fins légales et licites.",
            "Ne pas reproduire, distribuer ou modifier le contenu sans autorisation.",
            "Ne pas tenter d'accéder aux zones protégées de la Plateforme.",
            "Ne pas utiliser de robots ou de scripts automatisés pour extraire des données.",
            "Signaler tout contenu illégal ou contrevenant aux conditions d'utilisation.",
          ],
        },
        {
          title: "5. Propriété intellectuelle",
          content: "Le contenu de la Plateforme (textes, lois, jurisprudence, code source) est protégé par les droits de propriété intellectuelle. Les textes officiels sont dans le domaine public. Le code source de la Plateforme est sous licence open source.",
        },
        {
          title: "6. Limitation de responsabilité",
          content: "Les informations fournies par la Plateforme sont à titre informatif uniquement et ne constituent pas un avis juridique. La Plateforme ne saurait être tenue responsable des décisions prises sur la base de ses informations.",
        },
        {
          title: "7. Intelligence artificielle",
          content: "L'assistant juridique utilise l'intelligence artificielle pour fournir des explications. Ces explications sont générées automatiquement et doivent être vérifiées par un professionnel du droit.",
        },
        {
          title: "8. Modifications",
          content: "Nibras se réserve le droit de modifier les présentes conditions à tout moment. Les utilisateurs seront notifiés de toute modification substantielle.",
        },
        {
          title: "9. Résiliation",
          content: "Vous pouvez demander la suppression de votre compte à tout moment. Nibras se réserve le droit de suspendre un compte en cas de violation des présentes conditions.",
        },
        {
          title: "10. Droit applicable",
          content: "Les présentes conditions sont régies par le droit marocain. Tout litige sera soumis aux tribunaux compétents du Royaume du Maroc.",
        },
      ],
      "01 janvier 2025"
    );
  }

  return legalPage(
    "شروط الاستخدام",
    "سارية المفعول منذ 01 يناير 2025",
    [
      {
        title: "١. قبول الشروط",
        content: "بإنشاء حساب أو استخدام منصة نبراس، أنت توافق دون تحفظ على شروط الاستخدام هذه. إذا لم تكن توافق على هذه الشروط، يرجى عدم استخدام المنصة.",
      },
      {
        title: "٢. وصف الخدمة",
        content: "نبراس هي منصة معلوماتية قانونية تقدم: مكتبة للنصوص القانونية المغربية، قاعدة بيانات للاجتهادات القضائية، حاسبات قانونية، نماذج وثائق، مساعد قانوني بالذكاء الاصطناعي، ومجتمع للمستخدمين.",
      },
      {
        title: "٣. التسجيل والحساب",
        items: [
          "يجب عليك تقديم معلومات دقيقة وكاملة أثناء التسجيل.",
          "أنت مسؤول عن أمان كلمة المرور الخاصة بك.",
          "يُسمح بحساب واحد فقط لكل شخص.",
          "التسجيل مُقيد بقبول سياسة الخصوصية الخاصة بنا.",
          "الأدوار المهنية (محامٍ، موثق، إلخ) تخضع للتحقق.",
        ],
      },
      {
        title: "٤. قواعد الاستخدام",
        lead: "أنت تتعهد بما يلي:",
        items: [
          "استخدام المنصة لأغراض قانونية مشروعة فقط.",
          "عدم نسخ أو توزيع أو تعديل المحتوى دون تفويض.",
          "عدم محاولة الوصول إلى المناطق المحمية في المنصة.",
          "عدم استخدام روبوتات أو سكريبتات أتمتة لاستخراج البيانات.",
          "الإبلاغ عن أي محتوى غير قانوني أو مخالف لشروط الاستخدام.",
        ],
      },
      {
        title: "٥. حقوق الملكية الفكرية",
        content: "المحتوى المنشور في المنصة (نصوص، قوانين، اجتهادات، كود مصدري) محمي بحقوق الملكية الفكرية. النصوص الرسمية في النطاق العام. الكود المصدري للمنصة بترخيص مفتوح المصدر.",
      },
      {
        title: "٦. تحديد المسؤولية",
        content: "المعلومات المقدمة من المنصة هي لأغراض إعلامية فقط ولا تُشكّل رأياً قانونياً. لا يمكن أن تُتحمل المنصة مسؤولية القرارات المتخذة بناءً على معلوماتها.",
      },
      {
        title: "٧. الذكاء الاصطناعي",
        content: "المساعد القانوني يستخدم الذكاء الاصطناعي لتوفير شروحات. هذه الشروحات مولّدة تلقائياً ويجب التحقق منها من قِبَل متخصص في القانون.",
      },
      {
        title: "٨. التعديلات",
        content: "تحتفظ نبراس بالحق في تعديل هذه الشروط في أي وقت. ستتم إخطار المستخدمين بأي تعديل جوهري.",
      },
      {
        title: "٩. الإنهاء",
        content: "يمكنك طلب حذف حسابك في أي وقت. تحتفظ نبراس بحق تعليق حساب في حالة انتهاك هذه الشروط.",
      },
      {
        title: "١٠. القانون الحاكم",
        content: "تخضع هذه الشروط للقانون المغربي. أي نزاع يخضع للمحاكم المختصة في المملكة المغربية.",
      },
    ],
    "01 يناير 2025"
  );
}


/* ═══════════════════════════════════════════════════════════════════
   سياسة ملفات تعريف الارتباط (Cookies)
   ═══════════════════════════════════════════════════════════════════ */

export async function cookiePolicyView() {
  const isFr = currentLang() === "fr";

  if (isFr) {
    return legalPage(
      "Politique de Cookies",
      "Comment nous utilisons les cookies et traceurs",
      [
        {
          title: "1. Qu'est-ce qu'un cookie ?",
          content: "Un cookie est un petit fichier texte stocké sur votre appareil (ordinateur, tablette, téléphone) lorsque vous visitez un site web. Il permet au site de mémoriser vos actions et préférences sur une certaine période.",
        },
        {
          title: "2. Types de cookies utilisés",
          table: {
            headers: ["Type", "Finalité", "Durée"],
            rows: [
              ["Cookies strictement nécessaires", "Authentification, session utilisateur, préférences linguistiques, thème.", "Session / 30 jours"],
              ["Cookies de fonctionnalité", "Mémorisation des préférences d'affichage et de navigation.", "30 jours"],
              ["Cookies analytiques (non utilisés actuellement)", "Mesure d'audience et amélioration du service.", "—"],
              ["Cookies publicitaires (non utilisés actuellement)", "Personnalisation des publicités.", "—"],
            ],
          },
        },
        {
          title: "3. Cookies que nous utilisons",
          subsections: [
            {
              title: "3.1. Cookies strictement nécessaires",
              items: [
                "<strong>nibras_access</strong> : Token d'authentification JWT (localStorage). Supprimé à la déconnexion.",
                "<strong>nibras_refresh</strong> : Token de rafraîchissement (localStorage). Durée : 30 jours.",
                "<strong>nibras_user</strong> : Données du profil utilisateur (localStorage). Supprimé à la déconnexion.",
                "<strong>nibras_lang</strong> : Préférence linguistique (localStorage). Durée : permanente.",
                "<strong>nibras_theme</strong> : Préférence de thème (clair/sombre, localStorage). Durée : permanente.",
              ],
            },
            {
              title: "3.2. Cookies de session",
              content: "La session utilisateur est gérée via des tokens JWT stockés dans localStorage. Ces tokens sont essentiels au fonctionnement de l'authentification et ne contiennent aucune donnée sensible (le mot de passe n'est jamais stocké).",
            },
          ],
        },
        {
          title: "4. Gestion des cookies",
          content: "Vous pouvez gérer vos préférences de cookies à tout moment via le bouton « Gérer les cookies » en bas de la page. Vous pouvez également configurer votre navigateur pour refuser les cookies.",
        },
        {
          title: "5. Cookies tiers",
          content: "La Plateforme n'utilise actuellement aucun cookie tiers (Google Analytics, Facebook Pixel, etc.). Si des cookies tiers sont ajoutés dans le futur, cette politique sera mise à jour en conséquence et votre consentement sera sollicité.",
        },
        {
          title: "6. Droit applicable",
          content: "Cette politique de cookies est régie par la Loi 09-08 relative à la protection des données personnelles et la réglementation marocaine applicable.",
        },
      ],
      "01 janvier 2025"
    );
  }

  return legalPage(
    "سياسة ملفات تعريف الارتباط (Cookies)",
    "كيفية استخدامنا لملفات تعريف الارتباط والتعقب",
    [
      {
        title: "١. ما هو ملف تعريف الارتباط؟",
        content: "ملف تعريف الارتباط هو ملف نصي صغير يُخزَّن على جهازك (الكمبيوتر، اللوحي، الهاتف) عند زيارة موقع ويب. يُتيح للموقع تذكر إجراءاتك وتفضيلاتك لفترة معينة.",
      },
      {
        title: "٢. أنواع ملفات تعريف الارتباط المُستخدمة",
        table: {
          headers: ["النوع", "الغرض", "المدة"],
          rows: [
            ["ملفات ضرورية", "المصادقة، جلسة المستخدم، التفضيلات اللغوية، السمة.", "الجلسة / 30 يوماً"],
            ["ملفات وظيفية", "تذكّر تفضيلات العرض والتنقل.", "30 يوماً"],
            ["ملفات تحليلية (غير مُستخدمة حالياً)", "قياس الجمهور وتحسين الخدمة.", "—"],
            ["ملفات إعلانية (غير مُستخدمة حالياً)", "تخصيص الإعلانات.", "—"],
          ],
        },
      },
      {
        title: "٣. ملفات تعريف الارتباط المُستخدمة",
        subsections: [
          {
            title: "٣.١. الملفات الضرورية",
            items: [
              "<strong>nibras_access</strong>: توكن مصادقة JWT (localStorage). يُحذف عند تسجيل الخروج.",
              "<strong>nibras_refresh</strong>: توكن التحديث (localStorage). المدة: 30 يوماً.",
              "<strong>nibras_user</strong>: بيانات الملف الشخصي للمستخدم (localStorage). يُحذف عند تسجيل الخروج.",
              "<strong>nibras_lang</strong>: التفضيل اللغوي (localStorage). المدة: دائمة.",
              "<strong>nibras_theme</strong>: تفضيل السمة (فاتح/داكن، localStorage). المدة: دائمة.",
            ],
          },
          {
            title: "٣.٢. ملفات الجلسة",
            content: "تُدار جلسة المستخدم عبر توكنات JWT المخزنة في localStorage. هذه التوكنات ضرورية لعمل المصادقة ولا تحتوي على أي بيانات حساسة (كلمة المرور لا تُخزَّن أبداً).",
          },
        ],
      },
      {
        title: "٤. إدارة ملفات تعريف الارتباط",
        content: "يمكنك إدارة تفضيلات ملفات تعريف الارتباط في أي وقت عبر زر « إدارة ملفات تعريف الارتباط » في أسفل الصفحة. يمكنك أيضاً تكوين متصفحك لرفض ملفات تعريف الارتباط.",
      },
      {
        title: "٥. ملفات تعريف الارتباط التابعة",
        content: "لا تُستخدم المنصة حالياً أي ملفات تعريف ارتباط تابعة (Google Analytics، Facebook Pixel، إلخ). إذا أُضيفت ملفات تعريف ارتباط تابعة في المستقبل، ستُحدَّث هذه السياسة وستُطلَب موافقتك.",
      },
      {
        title: "٦. القانون الحاكم",
        content: "تخضع سياسة ملفات تعريف الارتباط هذه للقانون 09-08 المتعلق بحماية المعطيات الشخصية والتنظيمات المغربية المعمول بها.",
      },
    ],
    "01 يناير 2025"
  );
}


/* ═══════════════════════════════════════════════════════════════════
   سياسة الإخلاء من المسؤولية
   ═══════════════════════════════════════════════════════════════════ */

export async function disclaimerView() {
  const isFr = currentLang() === "fr";

  if (isFr) {
    return legalPage(
      "Avertissement Juridique",
      "Information importante sur l'utilisation de la Plateforme",
      [
        {
          title: "1. Nature de l'information",
          content: "Les informations disponibles sur la Plateforme Nibras sont fournies à titre informatif uniquement. Elles ne constituent pas un avis juridique, une consultation juridique ou une représentation légale.",
        },
        {
          title: "2. Pas de relation avocat-client",
          content: "L'utilisation de la Plateforme ne crée aucune relation avocat-client entre vous et Nibras. L'assistant juridique par intelligence artificielle ne remplace pas les conseils d'un avocat qualifié.",
        },
        {
          title: "3. Exactitude des informations",
          content: "Bien que nous nous efforcions de fournir des informations exactes et à jour, nous ne pouvons garantir l'exactitude, l'exhaustivité ou l'actualité du contenu. Les textes de loi sont des reproductions et peuvent contenir des erreurs.",
        },
        {
          title: "4. Recommandation",
          content: "Pour toute question juridique spécifique, nous vous recommandons de consulter un professionnel du droit habilité (avocat, notaire, etc.). La Plateforme ne se substitue pas à un conseil juridique personnalisé.",
        },
      ],
      "01 janvier 2025"
    );
  }

  return legalPage(
    "إخلاء المسؤولية",
    "معلومات مهمة حول استخدام المنصة",
    [
      {
        title: "١. طبيعة المعلومات",
        content: "المعلومات المتاحة في منصة نبراس مقدمة لأغراض إعلامية فقط. لا تُشكّل رأياً قانونياً أو استشارة قانونية أو تمثيلاً قانونياً.",
      },
      {
        title: "٢. لا علاقة محامي/عميل",
        content: "استخدام المنصة لا يُنشئ أي علاقة محامي/عميل بينك وبين نبراس. المساعد القانوني بالذكاء الاصطناعي لا يُحل محل نصيحة محامٍ مؤهل.",
      },
      {
        title: "٣. دقة المعلومات",
        content: "رغم جهدنا لتوفير معلومات دقيقة ومحدّثة، لا يمكننا ضمان دقة أو اكتمال أو تحديث المحتوى. النصوص القانونية مُعاد إنتاجها وقد تحتوي على أخطاء.",
      },
      {
        title: "٤. التوصية",
        content: "لأي سؤال قانوني محدد، نوصي بالاستشارة مع متخصص قانوني معتمد (محامٍ، موثق، إلخ). المنصة لا تُحل محل الاستشارة القانونية الشخصية.",
      },
    ],
    "01 يناير 2025"
  );
}

export function guideView() {
  return legalPage(
    "دليل الاستخدام",
    "دليل شامل لاستخدام منصة نبراس القانونية",
    [
      {
        title: "١. المكتبة القانونية",
        content: "المكتبة تحتوي على أكثر من 24,000 مادة قانونية مغربية منظمة في 35 فئة.",
        items: [
          "من الصفحة الرئيسية، اضغط على المكتبة في شريط التنقل",
          "يمكنك البحث بالكلمات المفتاحية أو تصفح الفئات",
          "افتح أي نص قانوني لقراءة نصه الكامل ومواده",
        ],
      },
      {
        title: "٢. المساعد القانوني بالذكاء الاصطناعي",
        content: "المساعد يجيب على أسئلتك القانونية بناءً على مكتبة نبراس. يمكنك أيضًا رفع ملفات PDF أو صور للتحليل.",
        items: [
          "اكتب سؤالك في مربع المحادثة واضغطإرسال أو Enter",
          "ارفع ملف PDF أو صورة (JPEG/PNG) بزر المرفقات",
          "اختر وضع الإجابة: تلقائي، موجَّه من المكتبة، بحث، عام",
          "المساعد يدعم الدارجة المغربية: اكتب كما تحب وسيفهمك",
        ],
      },
      {
        title: "٣. الاجتهادات القضائية",
        content: "قسم يضم قرارات محكمة النقض المغربية مُنظمة حسب المجال القانوني.",
        items: [
          "تصفح حسب المجال القانوني: جنائي، مدني، أسرة، تجاري",
          "اقرأ ملخص كل قرار والمبدأ القانوني المستفاد منه",
        ],
      },
      {
        title: "٤. تعلّم اللغة القانونية",
        content: "تعلّم المصطلحات القانونية بالفرنسية والإنجليزية والإسبانية مع دروس تدريجية وتمارين تفاعلية.",
        items: [
          "اختر اللغة التي تريد تعلمها",
          "ابدأ من المستوى الأساسي وانتقل تدريجيًا إلى المتقدم",
          "أكمل التمارين والاختبارات لتثبيت المعرفة",
        ],
      },
      {
        title: "٥. مكتبة الباحث",
        content: "حمّل كتبك ووثائقك البحثية ونظّمها في مكتبة شخصية مع إمكانية البحث النصي الكامل.",
        items: [
          "أضف كتابًا جديدًا مع بيانات التصنيف",
          "ارفع ملف PDF المرافق للكتاب",
          "استخدم البحث الفوري للعثور على أي معلومة في كتبك",
        ],
      },
      {
        title: "٦. الحاسبات القانونية",
        content: "أدوات حسابية ذكية لحساب المستحققات المالية والمواعيد القانونية.",
        items: [
          "حاسبة النفقة ومصاريف المعيشة",
          "حاسبة التقادم والمواعيد القانونية",
          "النتائج تقديرية وليست بديلاً عن المحاسبة لدى الجهات الرسمية",
        ],
      },
      {
        title: "٧. حسابك الشخصي",
        content: "سجّل حسابًا مجانًا للوصول إلى الميزات الشخصية مثل مكتبة الباحث والإشعارات.",
        items: [
          "التسجيل بالبريد الإلكتروني وكلمة المرور فقط",
          "غيّر إعدادات الإشعارات من صفحة الملف الشخصي",
          "بياناتك آمنة ونحترم خصوصيتك وفقًا لسياسة الخصوصية",
        ],
      },
      {
        title: "٨. إخلاء المسؤولية",
        content: "نبراس منصة توعوية قانونية. المحتوى المقدم ليس استشارة قانونية ولا يُغني عن استشارة متخصص قانوني معتمد. المعلومات دقيقة قدر الإمكان وقد لا تكون محدّثة في كل الأوقات.",
      },
    ],
    "01 يناير 2025"
  );
}
