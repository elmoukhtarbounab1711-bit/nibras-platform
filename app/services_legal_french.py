"""
خدمات تعلم اللغة القانونية — من المبتدئ إلى المحترف.

المنهج مقسم إلى 4 مستويات لكل لغة (Débutant → Avancé) مع دروس نظرية
وتمارين تفاعلية واختبارات تقييمية. يُسجَّل تقدم المستخدم (نسبة الإتقان،
عدد المحاولات، النقاط) في جدول `legal_language_progress`.

اللغات المدعومة: fr (فرنسية) / en (إنجليزية) / es (إسبانية)
"""

from .database import db_session

# ─── المنهج الدراسي ───────────────────────────────────────────────────────
# كل مستوى يحتوي على وحدات، كل وحدة تحتوي على دروس، كل درس يحتوي على:
#   title, subtitle, theory (نص شرح)، vocab (مفردات)، exercises (تمارين)

# ──────────────────────────────────────────────────────────────────────────
# 🇫🇷 الفرنسية القانونية
# ──────────────────────────────────────────────────────────────────────────

LEVELS_FR = [

    {
        "id": 1,
        "title": "Débutant — المبتدئ",
        "description": "المفردات والتعبيرات الأساسية في اللغة القانونية الفرنسية",
        "color": "#2563eb",
        "units": [
            {
                "id": "fr_l1_u1",
                "title": "Les bases du droit",
                "title_ar": "أساسيات القانون",
                "lessons": [
                    {
                        "id": "fr_l1_u1_l1",
                        "title": "Introduction au vocabulaire juridique",
                        "title_ar": "مقدمة في المفردات القانونية",
                        "subtitle": "Les termes fondamentaux du droit français",
                        "theory": (
                            "Le vocabulaire juridique constitue le fondement de toute compréhension du système juridique français. Contrairement au langage courant, le français juridique emploie des termes techniques dont le sens précis est déterminé par la loi et la jurisprudence. Maîtriser ces termes est indispensable pour tout étudiant en droit ou tout professionnel en contact avec le monde judiciaire.\n"
                            "\n"
                            "Les principaux termes fondamentaux du droit français sont les suivants. La loi, au sens strict, désigne une règle de droit écrite, édictée par le pouvoir législatif et votée par le Parlement. Le Code, quant à lui, est une compilation méthodique et ordonnée de lois relatives à une matière déterminée. Le Code civil, codifié en 1804 sous Napoléon, régit les relations entre les particuliers. Le Code pénal définit les infractions et les peines applicables. Le Code de procédure civile établit les règles de fonctionnement des tribunaux civils.\n"
                            "\n"
                            "La jurisprudence désigne l'ensemble des décisions rendues par les juridictions. Elle constitue une source de droit complémentaire aux textes législatifs. La doctrine regroupe les travaux des professeurs d'université et des praticiens du droit. Le jugement est la décision rendue par un tribunal de première instance, tandis que l'arrêt est la décision d'une cour d'appel ou de la Cour de cassation. Le décret est un acte réglementaire pris par le pouvoir exécutif, et la circulaire est une instruction interprétative adressée aux services administratifs. Le règlement est un acte à portée générale et impersonnelle."
                        ),
                        "theory_ar": (
                            "يشكل المفردات القانونية الأساس لأي فهم للنظام القانوني الفرنسي. على عكس اللغة اليومية، يستخدم القانون الفرنسي مصطلحات تقنية معناها الدقيق محدد بالقانون والاجتهاد القضائي. إتقان هذه المصطلحات ضروري لكل طالب قانون أو متخصص في المجال القضائي.\n"
                            "\n"
                            "المصطلحات الأساسية الرئيسية هي: القانون (Loi) بمعناه الدقيق، وهو قاعدة قانونية مكتوبة تصدر عن السلطة التشريعية. القانون (Code) هو تجميع منهجي للقوانين الخاصة بموضوع محدد. القانون المدني الذي صدر عام 1804 يُنظم العلاقات بين الأفراد. قانون العقوبات يُحدد الجرائم والعقوبات. قانون الإجراءات المدنية يضع قواعد عمل المحاكم المدنية.\n"
                            "\n"
                            "الاجتهاد القضائي (Jurisprudence) يشمل القرارات الصادرة عن المحاكم المختلفة ويُشكّل مصدر تكميلي. الفقه القانوني (Doctrine) يجمع أعمال الفقهاء والباحثين. الحكم (Jugement) هو قرار محكمة أول درجة، بينما القرار (Arrêt) هو قرار محكمة استئناف أو النقض. المرسوم (Décret) عمل تنظيمي يتخذه السلطة التنفيذية. التعميم (Circulaire) تعليم تفسيري موجه للإدارات الحكومية. اللائحة (Règlement) عمل ذي صلاحية عامة وغير شخصية."
                        ),
                        "vocab": [
                            {"fr": "la loi", "ar": "القانون", "example": "La loi a été votée par le Parlement."},
                            {"fr": "le code", "ar": "القانون المدني", "example": "Le Code civil a été rédigé en 1804."},
                            {"fr": "la jurisprudence", "ar": "الاجتهاد القضائي", "example": "La jurisprudence évolue constamment."},
                            {"fr": "la doctrine", "ar": "الفقه القانوني", "example": "La doctrine critique cette réforme."},
                            {"fr": "le jugement", "ar": "الحكم", "example": "Le jugement a été rendu en première instance."},
                            {"fr": "l'arrêt", "ar": "القرار (استئناف/نقض)", "example": "La cour a prononcé un arrêt confirmatif."},
                            {"fr": "le décret", "ar": "المرسوم", "example": "Le décret est paru au Journal officiel."},
                            {"fr": "la circulaire", "ar": "التعميم", "example": "La circulaire précise l'application de la loi."},
                            {"fr": "le règlement", "ar": "اللائحة", "example": "Le règlement intérieur prévoit ces cas."},
                            {"fr": "l'infraction", "ar": "الجريمة", "example": "L'infraction est caractérisée par trois éléments."}
                        ],
                    },

                    {
                        "id": "fr_l1_u1_l2",
                        "title": "Les acteurs du droit",
                        "title_ar": "المتدخلون في النظام القانوني",
                        "subtitle": "Les professionnels et institutions juridiques",
                        "theory": (
                            "Le système judiciaire français repose sur un ensemble d'institutions et de professionnels qui concourent au fonctionnement de la justice. Les juridictions judiciaires sont organisées hiérarchiquement. Le Tribunal judiciaire est la juridiction de droit commun en matière civile. Le Tribunal de commerce traite les litiges entre commerçants. Le Tribunal correctionnel juge les délits pénaux, tandis que la Cour d'assises, composée de trois magistrats et de six jurés, connaît des crimes. La Cour d'appel examine les recours contre les décisions des tribunaux de première instance.\n"
                            "\n"
                            "La Cour de cassation, juridiction suprême de l'ordre judiciaire, vérifie le respect de la loi par les juges du fond. En matière administrative, le Conseil d'État est la juridiction suprême. Les professionnels du droit jouent des rôles complémentaires. L'avocat assiste et représente les justiciables devant les juridictions. Le magistrat exerce la fonction de juge ou du ministère public. Le notaire est un officier public chargé de dresser des actes authentiques. Le greffier tient les procès-verbaux d'audience. L'huissier de justice signifie les actes et procède aux exécutions forcées. L'expert judiciaire apporte son expertise technique au tribunal dans des domaines spécialisés. Le procureur représente le ministère public et requiert l'application de la loi."
                        ),
                        "theory_ar": (
                            "يعتمد النظام القضائي الفرنسي على مجموعة من المؤسسات والمحترفين الذين يساهمون في سير العدالة. المحاكم القضائية منظمة هرمياً. محكمة القضاء العام هي المحكمة المختصة في الأمور المدنية. محكمة التجارة تنظر في النزاعات التجارية. المحكمة الجنائية تحاكم الجنايات البسيطة، بينما تنظر محكمة الجنايات الكبرى في الجنايات. محكمة الاستئناف تنظر الطعون ضد قرارات المحاكم الابتدائية.\n"
                            "\n"
                            "محكمة النقض هي المحكمة العليا للنظام القضائي وتتحقق من احترام القضاة للقانون. في الشؤون الإدارية، مجلس الدولة هو المحكمة العليا. المحترفون القانونيون يلعبون أدواراً متكاملة. المحامي يساعد ويمثل المتقاضين. القاضي يُباشر وظيفة الحكم أو النيابة العامة. الموثق موظف عام مكلف بتحرير عقود رسمية. كاتب المحكمة يُسجّل محاضر الجلسات. المحضر يُبلغ الأحكام وينفذ التنفيذ القسري. الخبير القضائي يقدم خبرته التقنية. النائب العام يمثل النيابة العامة ويطلب تطبيق القانون."
                        ),
                        "vocab": [
                            {"fr": "l'avocat", "ar": "المحامي", "example": "L'avocat plaide devant le tribunal."},
                            {"fr": "le magistrat", "ar": "القاضي", "example": "Le magistrat rend son jugement."},
                            {"fr": "le notaire", "ar": "الموثق", "example": "Le notaire authentifie le contrat."},
                            {"fr": "le greffier", "ar": "كاتب المحكمة", "example": "Le greffier rédige le procès-verbal."},
                            {"fr": "l'huissier", "ar": "المحضر", "example": "L'huissier signifie l'assignation."},
                            {"fr": "le tribunal", "ar": "المحكمة", "example": "Le tribunal est composé de trois juges."},
                            {"fr": "la cour", "ar": "المحكمة الاستئنافية", "example": "La cour d'appel examine l'affaire."},
                            {"fr": "le procureur", "ar": "النائب العام", "example": "Le procureur requiert l'application de la loi."},
                            {"fr": "la partie", "ar": "الطرف في النزاع", "example": "La partie demanderesse saisit le tribunal."},
                            {"fr": "le litige", "ar": "النزاع", "example": "Le litige est soumis au tribunal compétent."}
                        ],
                    },

                    {
                        "id": "fr_l1_u1_l3",
                        "title": "Les expressions juridiques courantes",
                        "title_ar": "التعبيرات القانونية الشائعة",
                        "subtitle": "Formulations essentielles du langage juridique",
                        "theory": (
                            "Le langage juridique français utilise des formules stéréotypées qui constituent le vocabulaire de base de tout texte ou plaidoirie. Ces expressions ont un sens juridique précis et leur utilisation correcte est indispensable pour communiquer efficacement dans le domaine du droit.\n"
                            "\n"
                            "Les expressions d'introduction servent à fonder juridiquement un raisonnement. « En vertu de » signifie conformément à un texte. « Conformément à » indique l'accord avec une norme. « Aux termes de » renvoie aux dispositions d'un texte précis. « Il ressort de » exprime une déduction tirée d'un élément probatoire. « Il est établi que » constate un fait avéré.\n"
                            "\n"
                            "Les expressions de conclusion permettent de clore un raisonnement juridique. « Par ces motifs » est la formule finale du jugement. « Il y a lieu de » exprime la nécessité d'une mesure. « Il convient de » indique ce qui est approprié. « Il sera fait droit à » signifie que le juge accueille la demande. « La demande est rejetée » exprime le rejet. Les expressions temporelles sont essentielles en procédure. « Dans le délai de » fixe une échéance. « À compter de » marque le point de départ. « Sous réserve de » exprime une condition. « Faute de » signifie en l'absence de."
                        ),
                        "theory_ar": (
                            "يستخدم القانون الفرنسي صيغًا ثابتة تُشكّل المفردات الأساسية لأي نص أو مرافعة. لهذه التعبيرات معنى قانوني دقيق وصحتها ضرورية للتواصل الفعال في مجال القانون.\n"
                            "\n"
                            "تعبيرات المقدمة تُستخدم لتأسيس التحليل القانوني. « En vertu de » تعني وفقًا لنص. « Conformément à » تُشير إلى التوافق مع معيار. « Aux terms de » تُحيل إلى أحكام نص محدد. « Il ressort de » تُعبّر عن استنتاج مُستخلص من عنصر إثباتي. « Il est établi que » تُثبت حقيقة مؤكدة.\n"
                            "\n"
                            "تعبيرات الختام تُستخدم لإنهاء التحليل القانوني. « Par ces motifs » الصيغة النهائية للحكم. « Il y a lieu de » تُعبّر عن ضرورة إجراء. « Il convient de » تُحدد ما هو مناسب. « Il sera fait droit à » تعني أن القاضي يُجيز الطلب. التعبيرات الزمنية أساسية في الإجراءات. « Dans le délai de » تُحدد موعداً نهائياً. « À compter de » تُحدد نقطة انطلاق المدة. « Sous réserve de » تُعبّر عن شرط. « Faute de » تعني في غياب."
                        ),
                        "vocab": [
                            {"fr": "en vertu de", "ar": "بناءً على / بموجب", "example": "En vertu de l'article 544 du Code civil."},
                            {"fr": "conformément à", "ar": "وفقاً لـ", "example": "Conformément à la loi n° 12-00."},
                            {"fr": "il ressort de", "ar": "يُستنتج من", "example": "Il ressort des débats que..."},
                            {"fr": "il est établi que", "ar": "ثابت أن", "example": "Il est établi que le défendeur..."},
                            {"fr": "par ces motifs", "ar": "بناءً على هذه الدوافع", "example": "Par ces motifs, le tribunal juge."},
                            {"fr": "il y a lieu de", "ar": "يجب / من الضروري", "example": "Il y a lieu d'ordonner une expertise."},
                            {"fr": "il convient de", "ar": "من المناسب", "example": "Il convient de rappeler que..."},
                            {"fr": "sous réserve de", "ar": "شريطة / مع مراعاة", "example": "Sous réserve de l'approbation."},
                            {"fr": "faute de", "ar": "في غياب / لعدم", "example": "Faute de preuve, la demande est rejetée."},
                            {"fr": "à compter de", "ar": "ابتداءً من", "example": "Le délai court à compter de la notification."}
                        ],
                    },

                    {
                        "id": "fr_l1_u1_l4",
                        "title": "Les sources du droit",
                        "title_ar": "مصادر القانون",
                        "subtitle": "Hiérarchie et origines des normes juridiques",
                        "theory": (
                            "Les sources du droit désignent l'ensemble des origines et des fondements des règles de droit applicables en France. La hiérarchie des normes organise ces sources selon un ordre de prééminence.\n"
                            "\n"
                            "Au sommet de la hiérarchie se trouve la Constitution du 4 octobre 1958. Le bloc de constitutionnalité comprend la Déclaration des droits de l'homme et du citoyen de 1789, le Préambule de la Constitution de 1946 et la Charte de l'environnement de 2004. Les traités internationaux ratifiés par la France ont une autorité supérieure à celle des lois, mais inférieure à celle de la Constitution.\n"
                            "\n"
                            "Les lois constituent la source principale du droit. On distingue les lois constitutionnelles, les lois organiques, les lois ordinaires votées par le Parlement, et les lois dérogatoires. Les règlements, pris par le pouvoir exécutif, comprennent les décrets en Conseil d'État, les décrets simples et les arrêtés. Les usages, coutumes et conventions collectives complètent ces sources écrites. La jurisprudence, bien que non formellement une source de droit, joue un rôle majeur dans l'interprétation des règles juridiques. La doctrine constitue une source d'inspiration pour les législateurs et les juges."
                        ),
                        "theory_ar": (
                            "مصادر القانون تشمل مجموعة الأصول والأساسات للقواعد القانونية المطبقة في فرنسا. تُنظّم التراتبية القانونية هذه المصادر حسب ترتيب الأسبقية.\n"
                            "\n"
                            "في قمة التراتبية يقع الدستور الصادر في 4 أكتوبر 1958. تشمل الكتلة الدستورية إعلان droits de l'homme لعام 1789 وديباجة الدستور لعام 1946 وميثاق البيئة لعام 2004. المعاهدات الدولية لها سلطة أعلى من القوانين لكنها أقل من الدستور.\n"
                            "\n"
                            "القوانين تُشكّل المصدر الرئيسي للقانون. وتُميّز بين القوانين الدستورية والعضوية والعادية والاستثنائية. اللوائح التنظيمية الصادرة عن السلطة التنفيذية تشمل مراسيم مجلس الدولة والمرسوم البسيط والأوامر. العرف والاتفاقيات الجماعية تُكمل هذه المصادر المكتوبة. الاجتهاد القضائي رغم أنه ليس مصدرًا رسميًا للقانون يلعب دورًا رئيسيًا في تفسير القواعد القانونية. الفقه القانوني يُشكّل مصدر إلهام للتشريعين والقضاة."
                        ),
                        "vocab": [
                            {"fr": "la Constitution", "ar": "الدستور", "example": "La Constitution est la norme suprême."},
                            {"fr": "la loi", "ar": "القانون", "example": "La loi ordinaire est votée par le Parlement."},
                            {"fr": "le règlement", "ar": "اللائحة التنظيمية", "example": "Le règlement précise l'application de la loi."},
                            {"fr": "le décret", "ar": "المرسوم", "example": "Le décret est pris en Conseil des ministres."},
                            {"fr": "l'arrêté", "ar": "الأمر", "example": "L'arrêté municipal réglemente la circulation."},
                            {"fr": "le traité", "ar": "المعاهدة", "example": "Le traité a été ratifié par le Parlement."},
                            {"fr": "l'usage", "ar": "العرف", "example": "L'usage complète les dispositions légales."},
                            {"fr": "la coutume", "ar": "العادة", "example": "La coutume s'impose aux parties."},
                            {"fr": "la convention collective", "ar": "الاتفاقية الجماعية", "example": "La convention collective fixe les salaires minimums."},
                            {"fr": "la hiérarchie des normes", "ar": "تراتبية القواعد", "example": "La hiérarchie des normes garantit la cohérence du droit."}
                        ],
                    },

                ],
            },

            {
                "id": "fr_l1_u2",
                "title": "Les branches fondamentales",
                "title_ar": "فروع القانون الأساسية",
                "lessons": [
                    {
                        "id": "fr_l1_u2_l1",
                        "title": "La Constitution et les lois",
                        "title_ar": "الدستور والقوانين",
                        "subtitle": "Architecture constitutionnelle et processus législatif",
                        "theory": (
                            "La Constitution du 4 octobre 1958 organise les pouvoirs publics français. Elle instaure un régime semi-présidentiel avec une assemblée bicamérale composée de l'Assemblée nationale et du Sénat. Le Président de la République est élu au suffrage universel direct et nomme le Premier ministre.\n"
                            "\n"
                            "Le processus législatif suit plusieurs étapes strictement encadrées. Un projet de loi émane du gouvernement, tandis qu'une proposition de loi émane d'un membre du Parlement. Le texte est examiné successivement par les deux chambres dans le cadre de la procédure de navette. En cas de désaccord, le Premier ministre peut convoquer une commission mixte paritaire.\n"
                            "\n"
                            "Le contrôle de constitutionnalité est exercé par le Conseil constitutionnel, composé de neuf membres nommés pour neuf ans. Depuis la réforme de 2010, la question prioritaire de constitutionnalité permet aux justiciables de contester la conformité d'une disposition législative à la Constitution. Le Conseil constitutionnel vérifie également la régularité des élections présidentielles et législatives."
                        ),
                        "theory_ar": (
                            "الدستور الصادر في 4 أكتوبر 1958 يُنظّم السلط العامة في فرنسا. وهو يُنشئ نظامًا نصف رئاسيًا مع برلمان مؤلف من مجلسين: الجمعية الوطنية ومجلس الشيوخ. رئيس الجمهورية يُنتخب بالاقتراع العام المباشر ويعين رئيس الوزراء.\n"
                            "\n"
                            "المسار التشريعي يتبع عدة مراحل منضبطة بصرامة. مشروع القانون يصدر عن الحكومة، بينما 제안 القانون يصدر عن عضو في البرلمان. يُفحص النص من قبل المجلسين بالتناوب في إطار إجراء التنقل. في حالة عدم الاتفاق، يمكن لرئيس الوزراء تشكيل لجنة مشتركة.\n"
                            "\n"
                            "رقابة الدستورية يمارسها مجلس الدستور المكون من تسعة أعضاء معينين لمدة تسع سنوات. منذ إصلاح عام 2010، تتيح المسألة الأولية الدستورية للمتقاضين الطعن في مطابقة حكم تشريعي للدستور."
                        ),
                        "vocab": [
                            {"fr": "la Constitution", "ar": "الدستور", "example": "La Constitution fixe l'organisation des pouvoirs publics."},
                            {"fr": "le Parlement", "ar": "البرلمان", "example": "Le Parlement vote les lois."},
                            {"fr": "l'Assemblée nationale", "ar": "الجمعية الوطنية", "example": "L'Assemblée nationale examine le texte en première lecture."},
                            {"fr": "le Sénat", "ar": "مجلس الشيوخ", "example": "Le Sénat délibère sur les propositions de loi."},
                            {"fr": "le projet de loi", "ar": "مشروع القانون", "example": "Le projet de loi a été présenté en Conseil des ministres."},
                            {"fr": "la proposition de loi", "ar": "مشروع قانون برلماني", "example": "La proposition de loi est signée par cinquante députés."},
                            {"fr": "le Conseil constitutionnel", "ar": "مجلس الدستور", "example": "Le Conseil constitutionnel a déclaré la loi conforme."},
                            {"fr": "le référendum", "ar": "الاستفتاء", "example": "Le référendum a été organisé pour approuver le traité."},
                            {"fr": "la commission mixte paritaire", "ar": "اللجنة المشتركة", "example": "La commission mixte paritaire a proposé un texte unique."},
                            {"fr": "la publication au Journal officiel", "ar": "النشر في الجريدة الرسمية", "example": "La loi entre en vigueur après sa publication au JORF."}
                        ],
                    },

                    {
                        "id": "fr_l1_u2_l2",
                        "title": "Le droit civil fondamental",
                        "title_ar": "القانون المدني الأساسي",
                        "subtitle": "Principes et règles du droit civil français",
                        "theory": (
                            "Le droit civil est la branche du droit qui régit les relations entre les particuliers. Constituant le socle du système juridique français, il touche tous les aspects de la vie quotidienne.\n"
                            "\n"
                            "Le Code civil, entré en vigueur en 1804, repose sur plusieurs principes fondamentaux. Le principe de liberté contractuelle permet aux parties de conclure les contrats de leur choix. Le principe de l'autonomie de la volonté reconnaît la capacité des personnes à déterminer le contenu de leurs engagements. Le principe de l'effet relatif des contrats dispose qu'un contrat ne crée d'obligations qu'entre les parties.\n"
                            "\n"
                            "Les obligations constituent le cœur du droit civil. Une obligation est un lien de droit en vertu duquel une personne, le débiteur, est tenue envers une autre, le créancier, d'exécuter une prestation. Les sources principales des obligations sont le contrat, le quasi-contrat, le délit et le quasi-délit. Le droit de la propriété, défini par l'article 544 du Code civil, constitue un droit absolu et exclusif. La responsabilité civile vise à réparer le préjudice causé par le fait d'autrui."
                        ),
                        "theory_ar": (
                            "القانون المدني هو الفرع من القانون الذي يُنظم العلاقات بين الأفراد. وهو يُشكّل أساس النظام القانوني الفرنسي.\n"
                            "\n"
                            "القانون المدني الذي دخل حيز التنفيذ عام 1804 يقوم على مبادئ أساسية. مبدأ حرية التعاقد يتيح للأطراف إبرام العقود التي يختارونها. مبدأ سيادة الإرادة يُعترف بقدرة الأشخاص على تحديد مضمون التزاماتهم. مبدأ المفعول النسبي للعقود يُنص على أن العقد لا يُنشئ التزامات إلا بين أطرافه.\n"
                            "\n"
                            "الالتزامات تُشكّل جوهر القانون المدني. الالتزام هو رابطة قانونية يُصبح بموجبها المدين مُلزَمًا تجاه الدائن بتنفيذ التزام. المصادر الرئيسية للالتزامات هي العقد وشبه العقد والجريمة وشبه الجريمة. حق الملكية المحدد بالمادة 544 يُشكّل حقًا مطلقًا وحصريًا. المسؤولية المدنية تهدف إلى تعويض الضرر الذي سببه فعل الغير."
                        ),
                        "vocab": [
                            {"fr": "le contrat", "ar": "العقد", "example": "Le contrat a été conclu entre les deux parties."},
                            {"fr": "l'obligation", "ar": "الالتزام", "example": "Le débiteur est tenu d'exécuter son obligation."},
                            {"fr": "le créancier", "ar": "الدائن", "example": "Le créancier peut poursuivre le débiteur."},
                            {"fr": "le débiteur", "ar": "المدين", "example": "Le débiteur est en retard d'exécution."},
                            {"fr": "la propriété", "ar": "الملكية", "example": "La propriété est le droit de jouir et disposer."},
                            {"fr": "le quasi-contrat", "ar": "شبه العقد", "example": "La gestion d'affaires est un quasi-contrat."},
                            {"fr": "le délit civil", "ar": "الجريمة المدنية", "example": "Le délit civil engage la responsabilité de son auteur."},
                            {"fr": "la responsabilité civile", "ar": "المسؤولية المدنية", "example": "La responsabilité civile répare le préjudice causé."},
                            {"fr": "la succession", "ar": "الإرث", "example": "La succession est réglée conformément à la loi."},
                            {"fr": "l'autonomie de la volonté", "ar": "سيادة الإرادة", "example": "L'autonomie de la volonté est un principe fondamental."}
                        ],
                    },

                    {
                        "id": "fr_l1_u2_l3",
                        "title": "Le droit pénal de base",
                        "title_ar": "قانون العقوبات الأساسي",
                        "subtitle": "Infractions, peines et principes du droit pénal",
                        "theory": (
                            "Le droit pénal définit les infractions et établit les peines applicables. Il obéit au principe de légalité des délits et des peines, selon lequel nul ne peut être puni pour un fait que la loi n'a pas prévu et qualifié d'infraction.\n"
                            "\n"
                            "Le Code pénal distingue trois catégories d'infractions. Le crime est l'infraction la plus grave, punie de la réclusion criminelle allant de quinze ans à la perpétuité. Le délit est une infraction intermédiaire, punie d'amendes ou d'emprisonnement jusqu'à dix ans. La contravention est l'infraction la moins grave, punie uniquement d'amendes.\n"
                            "\n"
                            "Toute infraction est constituée de trois éléments cumulatifs. L'élément légal consiste en l'existence d'un texte incriminant le fait. L'élément matériel désigne le comportement prohibé. L'élément moral, ou mens rea, est l'intention criminelle de l'auteur. La présomption d'innocence est un principe fondamental selon lequel toute personne est présumée innocente jusqu'à ce que sa culpabilité ait été établie par une décision définitive. Les circonstances atténuantes et aggravantes peuvent modifier la peine encourue."
                        ),
                        "theory_ar": (
                            "قانون العقوبات يُحدد الجرائم ويضع العقوبات المطبقة. ويخضع لمبدأ مشروعية الجرائم والعقوبات.\n"
                            "\n"
                            "يُميّز قانون العقوبات بين ثلاث فئات من الجرائم. الجناية هي الجريمة الأسوأ يُعاقب عليها بالسجن من خمسة عشر سنة إلى المؤبد. الجنحة جريمة متوسطة يُعاقب عليها بالغرامات أو السجن حتى عشر سنوات. المخالفة الجريمة الأقل خطورة يُعاقب عليها بالغرامات فقط.\n"
                            "\n"
                            "تتألف كل جريمة من ثلاثة عناصر تتراكم. العنصر القانوني يتمثل في وجود نص يجرّم الفعل. العنصر المادي يُشير إلى السلوك المحظور. العنصر المعنوي (mens rea) هو نية الجريمة من الفاعل. البراءة الأصلية مبدأ أساسي ينص على أن كل شخص يُفترض بريئاً حتى تثبت إدانته. ظروف التخفيف والتشديد يمكنها تعديل العقوبة."
                        ),
                        "vocab": [
                            {"fr": "l'infraction", "ar": "الجريمة", "example": "L'infraction est caractérisée par trois éléments."},
                            {"fr": "le crime", "ar": "الجناية", "example": "Le crime est puni de la réclusion criminelle."},
                            {"fr": "le délit", "ar": "الجنحة", "example": "Le délit est puni d'emprisonnement ou d'amende."},
                            {"fr": "la contravention", "ar": "المخالفة", "example": "La contravention est punie d'une amende."},
                            {"fr": "l'élément matériel", "ar": "العنصر المادي", "example": "L'élément matériel est l'acte prohibé."},
                            {"fr": "l'élément moral", "ar": "العنصر المعنوي", "example": "L'élément moral est l'intention de l'auteur."},
                            {"fr": "la peine", "ar": "العقوبة", "example": "La peine est proportionnée à la gravité de l'infraction."},
                            {"fr": "la présomption d'innocence", "ar": "البراءة الأصلية", "example": "La présomption d'innocence est un droit fondamental."},
                            {"fr": "la circonstance aggravante", "ar": "ظرف التشديد", "example": "La préméditation est une circonstance aggravante."},
                            {"fr": "la circonstance atténuante", "ar": "ظرف التخفيف", "example": "Les aveux constituent une circonstance atténuante."}
                        ],
                    },

                ],
            },

            {
                "id": "fr_l1_u3",
                "title": "La pratique juridique",
                "title_ar": "الممارسة القانونية",
                "lessons": [
                    {
                        "id": "fr_l1_u3_l1",
                        "title": "La procédure civile",
                        "title_ar": "الإجراءات المدنية",
                        "subtitle": "Déroulement d'un procès civil en France",
                        "theory": (
                            "La procédure civile régit le déroulement des instances devant les juridictions civiles. Elle assure le respect du contradictoire et le droit de la défense.\n"
                            "\n"
                            "Un litige civil débute par une assignation délivrée par un huissier de justice au défendeur. Le demandeur expose ses prétentions dans un exposé sommaire. Le défendeur dispose d'un délai pour constituer avocat et produire ses conclusions. L'échange des écritures constitue la phase préalable au jugement.\n"
                            "\n"
                            "L'audience de mise en état permet au juge de contrôler l'instruction de l'affaire et de fixer un calendrier procédural. Les parties peuvent être convoquées à une audience de plaidoirie où leurs avocats présentent oralement leurs arguments.\n"
                            "\n"
                            "Le jugement est rendu après délibéré, en public, et motivé. Il est signifié aux parties et peut faire l'objet d'un appel dans un délai d'un mois. L'appel est un recours suspensif, sauf en matière d'urgence ou d'exécution provisoire."
                        ),
                        "theory_ar": (
                            "الإجراءات المدنية تُنظم سير القضايا أمام المحاكم المدنية. وتكفل احترام المواجهة وحقوق الدفاع.\n"
                            "\n"
                            "يبدأ النزاع المدني بإعلان يتولاه المحضر للمدعى عليه. يُقدّم المدعي مطالباته في عرض موجز. يتمتع المدعى عليه بمدة لتعيين محامي وإعداد مذكراته. تبادل المذكرات يُشكّل المرحلة السابقة للحكم.\n"
                            "\n"
                            "جلسات التحضير تتيح للقاضي التحقق من تجهيز القضية. يمكن استدعاء الأطراف إلى جلسة مرافعة يُقدّم فيها المحامون حججهم شفهياً.\n"
                            "\n"
                            "يُصدر الحكم بعد التشاور، في جلسة علنية، ومُبرر. يُبلغ للأطراف ويمكن الطعن بالاستئناف خلال شهر. الاستئناف تظلم مُعلّق يُوقف تنفيذ الحكم إلا في حالة الاستعجال."
                        ),
                        "vocab": [
                            {"fr": "l'assignation", "ar": "الاستدعاء", "example": "L'assignation est délivrée par un huissier."},
                            {"fr": "les conclusions", "ar": "المذكرات", "example": "Les conclusions sont échangées entre les parties."},
                            {"fr": "la plaidoirie", "ar": "المرافعة", "example": "La plaidoirie a duré deux heures."},
                            {"fr": "le jugement", "ar": "الحكم", "example": "Le jugement a été rendu en audience publique."},
                            {"fr": "l'appel", "ar": "الاستئناف", "example": "L'appel doit être formé dans le délai d'un mois."},
                            {"fr": "la mise en état", "ar": "التحضير", "example": "Le juge de la mise en état organise l'instruction."},
                            {"fr": "la médiation", "ar": "الوساطة", "example": "Le juge ordonne la médiation avant de statuer."},
                            {"fr": "la signification", "ar": "التبليغ", "example": "La signification fait courir les délais de recours."},
                            {"fr": "l'huissier de justice", "ar": "المحضر", "example": "L'huissier signifie l'acte au défendeur."},
                            {"fr": "le délibéré", "ar": "التشاور", "example": "Le délibéré est secret et ne peut être révélé."}
                        ],
                    },

                    {
                        "id": "fr_l1_u3_l2",
                        "title": "Le droit du travail",
                        "title_ar": "قانون العمل",
                        "subtitle": "Relations individuelles et collectives du travail",
                        "theory": (
                            "Le droit du travail encadre les relations entre les salariés et les employeurs. Il vise à protéger le travailleur tout en garantissant le bon fonctionnement de l'économie.\n"
                            "\n"
                            "Le contrat de travail peut être à durée indéterminée ou à durée déterminée. Il doit comporter les mentions obligatoires, notamment la nature de l'emploi, la rémunération, le lieu et la durée du travail. La période d'essai permet à chaque partie d'évaluer l'adéquation entre le salarié et le poste.\n"
                            "\n"
                            "Le Code du travail prévoit des dispositions protectrices. Le SMIC garantit un revenu minimal. La durée légale du travail est fixée à trente-cinq heures par semaine. Le salarié bénéficie d'un droit aux congés payés d'au moins cinq semaines par an. Le licenciement obéit à des règles strictes concernant la justification de la cause réelle et sérieuse.\n"
                            "\n"
                            "Le dialogue social est assuré par les représentants du personnel, les comités sociaux et économiques, et les syndicats. Les conventions collectives de branche complètent les dispositions légales minimales."
                        ),
                        "theory_ar": (
                            "قانون العمل يُنظم العلاقات بين العمال وأصحاب العمل. ويهدف إلى حماية العامل مع ضمان سير الاقتصاد.\n"
                            "\n"
                            "عقد العمل يمكن أن يكون محدد المدة أو غير محدد. ويجب أن يتضمن عناصر إلزامية تشمل طبيعة الوظيفة والأجر ومكان العمل ومدة العمل. فترة التجربة تتيح لكل طرف تقييم التوافق.\n"
                            "\n"
                            "قانون العمل ينص على حماية للعامل. الحد الأدنى للأجر يُضمن دخلاً أدنى. المدة القانونية للعمل محددة بخمس وثلاثين ساعة أسبوعياً. يستفيد العامل من إجازة مدفوعة الأجر لا تقل عن خمس أسابيع. الفصل يخضع لقواعد صارمة تتعلق بمبرر السبب الحقيقي والجدري.\n"
                            "\n"
                            "الحوار الاجتماعي يضمنه ممثلو الموظفين واللجان الاجتماعية والنقابات. الاتفاقيات الجماعية للفرع تُكمل الأدنى القانوني."
                        ),
                        "vocab": [
                            {"fr": "le contrat de travail", "ar": "عقد العمل", "example": "Le contrat à durée indéterminée est la règle."},
                            {"fr": "le salarié", "ar": "العامل", "example": "Le salarié bénéficie de la protection du Code du travail."},
                            {"fr": "l'employeur", "ar": "صاحب العمل", "example": "L'employeur doit assurer la sécurité du salarié."},
                            {"fr": "le salaire", "ar": "الأجر", "example": "Le salaire est payé mensuellement."},
                            {"fr": "le licenciement", "ar": "الفصل", "example": "Le licenciement nécessite une cause réelle et sérieuse."},
                            {"fr": "la période d'essai", "ar": "فترة التجربة", "example": "La période d'essai ne peut excéder six mois."},
                            {"fr": "les congés payés", "ar": "الإجازة المدفوعة", "example": "Le salarié a droit à cinq semaines de congés payés."},
                            {"fr": "la convention collective", "ar": "الاتفاقية الجماعية", "example": "La convention collective améliore les conditions de travail."},
                            {"fr": "le comité social", "ar": "اللجنة الاجتماعية", "example": "Le comité social est consulté avant tout licenciement collectif."},
                            {"fr": "le SMIC", "ar": "الحد الأدنى للأجر", "example": "Le SMIC est revalorisé chaque année."}
                        ],
                    },

                    {
                        "id": "fr_l1_u3_l3",
                        "title": "Le droit de la famille",
                        "title_ar": "قانون الأسرة",
                        "subtitle": "Mariage, filiation et autorité parentale",
                        "theory": (
                            "Le droit de la famille régit les relations juridiques entre les membres d'une même famille. Il a connu des évolutions majeures ces dernières décennies.\n"
                            "\n"
                            "Le mariage est l'union de deux personnes depuis la loi du 17 mai 2013. Il est célébré devant l'officier d'état civil et constitue un contrat soumettant les époux à des obligations réciproques. Le régime matrimonial détermine les droits et devoirs patrimoniaux des époux.\n"
                            "\n"
                            "La filiation, biologique ou adoptive, établit le lien de droit entre un parent et son enfant. L'autorité parentale est l'ensemble des droits et devoirs parentaux visant l'intérêt de l'enfant. Elle est exercée conjointement par les deux parents.\n"
                            "\n"
                            "Le divorce peut être prononcé pour acceptation du principe de la rupture, pour altération définitive du lien conjugal, ou pour faute. La pension alimentaire et le droit de visite sont réglés dans l'intérêt supérieur de l'enfant. Le PACS et le concubinage font l'objet de dispositions spécifiques."
                        ),
                        "theory_ar": (
                            "قانون الأسرة يُنظم العلاقات القانونية بين أفراد الأسرة واحدة. وقد شهد تطورات رئيسية.\n"
                            "\n"
                            "الزواج هو اتحاد شخصين منذ القانون الصادر في 17 مايو 2013. ويُحتفل بهم أمام الموظف المدني ويُشكّل عقداً يخضع له الأزواج بالتزامات متبادلة. النظام الزوجي يُحدد الحقوق والواجبات المالية للأزواج.\n"
                            "\n"
                            "النسب البيولوجي أو التبني يُنشئ الرابطة القانونية بين الوالد وطفله. السلطة الأصلية هي مجموعة الحقوق والواجبات الأبوية في مصلحة الطفل. تُمارَّس بشكل مشترك من قبل الوالدين.\n"
                            "\n"
                            "يمكن الحكم بالطلاق بسبب قبول مبدأ الانفصال أو انتهاك الرابطة الزوجية أو بسبب خطأ. المبلغ الإعانة وحق الزيارة يُنتظمان في المصلحة الفوقية للطفل. اتفاقية الشراكة المدنية والعيش المشترك لها أحكام خاصة."
                        ),
                        "vocab": [
                            {"fr": "le mariage", "ar": "الزواج", "example": "Le mariage est célébré devant l'officier d'état civil."},
                            {"fr": "le divorce", "ar": "الطلاق", "example": "Le divorce peut être accepté par les deux époux."},
                            {"fr": "la filiation", "ar": "النسب", "example": "La filiation établit le lien juridique parent-enfant."},
                            {"fr": "l'autorité parentale", "ar": "السلطة الأصلية", "example": "L'autorité parentale est exercée conjointement."},
                            {"fr": "la pension alimentaire", "ar": "النفقة", "example": "La pension alimentaire est fixée selon les besoins."},
                            {"fr": "le droit de visite", "ar": "حق الزيارة", "example": "Le droit de visite est accordé au parent non gardien."},
                            {"fr": "la communauté réduite aux acquêts", "ar": "مجتمع المكتسبات", "example": "Le régime légal est la communauté réduite aux acquêts."},
                            {"fr": "le PACS", "ar": "اتفاقية الشراكة المدنية", "example": "Le PACS est conclu devant le greffier du tribunal."},
                            {"fr": "le concubinage", "ar": "العيش المشترك", "example": "Le concubinage est une union de fait stable."},
                            {"fr": "l'intérêt supérieur de l'enfant", "ar": "المصلحة الفوقية للطفل", "example": "L'intérêt supérieur de l'enfant guide toute décision."}
                        ],
                    },

                ],
            },

        ],
    },

    {
        "id": 2,
        "title": "Intermédiaire — المتوسط",
        "description": "قواعد نحوية متقدمة وصيغ قانونية معقدة",
        "color": "#059669",
        "units": [
            {
                "id": "fr_l2_u1",
                "title": "Le langage juridique avancé",
                "title_ar": "اللغة القانونية المتقدمة",
                "lessons": [
                    {
                        "id": "fr_l2_u1_l1",
                        "title": "La phrase juridique complexe",
                        "title_ar": "الجملة القانونية المعقدة",
                        "subtitle": "Subordination, coordination et complexité syntaxique",
                        "theory": (
                            "Le style juridique se caractérise par l'utilisation de phrases complexes, souvent longues et riches en propositions subordonnées. Cette complexité vise à exprimer avec précision les conditions, les exceptions et les réserves qui encadrent l'application d'une règle de droit.\n"
                            "\n"
                            "La subordination conditionnelle est fréquente dans les textes législatifs. Les connecteurs « si », « à moins que », « dans l'hypothèse où », « pourvu que » introduisent des conditions. La subordination causale, introduite par « puisque », « dès lors que », « attendu que », justifie la décision. La subordination de but, avec « afin que », « de manière à ce que », indique l'objectif poursuivi par la règle.\n"
                            "\n"
                            "La coordination permet de lier plusieurs idées avec « et », « ou », « mais ». Le style juridique emploie des couples synonymiques tels que « droits et obligations », « nullité et inopposabilité ». Les incises explicatives apportent des précisions sans rompre la cohérence de la phrase. La maîtrise de ces structures syntaxiques est indispensable pour lire et rédiger des textes juridiques avec exactitude."
                        ),
                        "theory_ar": (
                            "يتميز الأسلوب القانوني باستخدام الجمل المعقدة التي غالباً ما تكون طويلة وغنية بالجمل التابعة. تهدف هذه التعقيدية إلى التعبير بدقة عن الشروط والاستثناءات التي تُحدد نطاق تطبيق قاعدة قانونية.\n"
                            "\n"
                            "التبعية الشرطية شائعة في النصوص التشريعية. روابط مثل « إذا » و « إلا إذا » تُدخل شروطاً تُقيّد أو توسع نطاق القاعدة. التبعية السببية تُبرر القرار بالاستناد إلى وقائع مؤكدة. التبعية الغائية تُحدد المتبوع من القاعدة.\n"
                            "\n"
                            "التنسيق يربط عدة أفكار من نفس الأهمية. الأسلوب القانوني يستخدم أزواج مرادفة مثل « حقوق وواجبات » لتقوية نطاق العبارة. الفواصل التوضيحية تُقدّم تفاصيل دون إخلال بالتماسك النحوي. إتقان هذه التراكيب النحوية ضروري لقراءة وكتابة النصوص القانونية بدقة."
                        ),
                        "vocab": [
                            {"fr": "à moins que", "ar": "إلا إذا", "example": "À moins que le débiteur ne prouve le contraire."},
                            {"fr": "dès lors que", "ar": "حالما / بمجرد أن", "example": "Dès lors que le contrat est valable."},
                            {"fr": "attendu que", "ar": "بما أن", "example": "Attendu que les conditions sont réunies."},
                            {"fr": "pourvu que", "ar": "شريطة أن", "example": "Pourvu que la condition soit remplie."},
                            {"fr": "afin que", "ar": "حتى / لكي", "example": "Afin que le droit soit respecté."},
                            {"fr": "de manière à ce que", "ar": "بطريقة تجعل", "example": "De manière à ce que l'intérêt soit protégé."},
                            {"fr": "en vertu de", "ar": "بناءً على / بموجب", "example": "En vertu de la loi n° 12-00."},
                            {"fr": "sous réserve de", "ar": "شريطة / مع مراعاة", "example": "Sous réserve de l'approbation du Conseil."},
                            {"fr": "nonobstant", "ar": "رغم / على الرغم من", "example": "Nonobstant les dispositions légales."},
                            {"fr": "sans préjudice de", "ar": "دون الإخلال بـ", "example": "Sans préjudice du droit de recours."}
                        ],
                    },

                    {
                        "id": "fr_l2_u1_l2",
                        "title": "La voix passive juridique",
                        "title_ar": "المبني للمجهول القانوني",
                        "subtitle": "Formules impersonnelles et passives en droit",
                        "theory": (
                            "Le style juridique privilégie systématiquement la voix passive et les tournures impersonnelles. Ce choix stylistique permet de mettre en avant l'action de la norme plutôt que l'auteur, renforçant ainsi l'autorité et l'objectivité du discours.\n"
                            "\n"
                            "Les formules impersonnelles les plus courantes sont « il a été jugé que », « il a été décidé que », « il convient de rappeler que », « il y a lieu de constater que ». Ces tournures créent une distance entre l'auteur et le contenu, conférant un caractère plus objectif à la décision.\n"
                            "\n"
                            "L'utilisation du passif se justifie par la nécessité de maintenir la neutralité du juge. Le conditionnel passé, utilisé dans les arrêts de la Cour de cassation (« il aurait dû être jugé que »), exprime le reproche fait au juge du fond d'avoir mal appliqué la loi.\n"
                            "\n"
                            "Cependant, l'abus de formules impersonnelles peut rendre le texte lourd. Le bon usage consiste à alterner entre voix active et voix passive selon le contexte."
                        ),
                        "theory_ar": (
                            "يُفضّل الأسلوب القانوني بشكل منهجي المبني للمجهول والصيغ غير الشخصية. هذا الاختيار يُتيح تسليط الضوء على عمل القاعدة بدلاً من فاعلها، مما يعزز سلطة الخطاب.\n"
                            "\n"
                            "الصيغ غير الشخصية الأكثر شيوعاً هي « أُحكِم بأن » و « قُرِّر بأن » و « يجب تذكير بأن ». هذه الصيغ تخلق مسافة بين الكاتب والمحتوى، مما يمنح طابعاً أكثر موضوعية.\n"
                            "\n"
                            "استخدام المبني للمجهول يبرر بالحاجة إلى الحفاظ على حيادية القاضي. الشرط الماضي المستخدم في قرارات محكمة النقض يُعبّر عن اللوم الموجه للقاضي لسوء تطبيقه للقانون.\n"
                            "\n"
                            "ومع ذلك، الإفراط في الصيغ غير الشخصية قد يجعل النص ثقيلاً. الاستخدام الصحيح يكمن في التبديل بين المبني للمعلوم والمبني للمجهول حسب السياق."
                        ),
                        "vocab": [
                            {"fr": "il a été jugé que", "ar": "أُحكِم بأن", "example": "Il a été jugé que le contrat est nul."},
                            {"fr": "il convient de", "ar": "يجب / من المناسب", "example": "Il convient d'examiner cette question."},
                            {"fr": "il y a lieu de", "ar": "يُتعيّن", "example": "Il y a lieu de prononcer la nullité."},
                            {"fr": "il est constant que", "ar": "ثابت أن", "example": "Il est constant que les faits sont établis."},
                            {"fr": "il ressort de", "ar": "يُستنتج من", "example": "Il ressort du procès-verbal que..."},
                            {"fr": "il est soutenu que", "ar": "يحتج بأن", "example": "Il est soutenu que la preuve est rapportée."},
                            {"fr": "il sera fait droit", "ar": "يُجيز", "example": "Il sera fait droit à la demande."},
                            {"fr": "il a été décidé que", "ar": "قُرِّر بأن", "example": "Il a été décidé de surseoir à statuer."},
                            {"fr": "il est ordonné que", "ar": "يُؤمَر بأن", "example": "Il est ordonné une expertise."},
                            {"fr": "il est fait droit", "ar": "يُجيز", "example": "Il est fait droit à la demande principale."}
                        ],
                    },

                    {
                        "id": "fr_l2_u1_l3",
                        "title": "Le vocabulaire des obligations",
                        "title_ar": "مفردات حق الالتزامات",
                        "subtitle": "Sources, exécution et extinction des obligations",
                        "theory": (
                            "Le droit des obligations constitue le socle du droit civil. Les obligations naissent de sources variées et obéissent à des règles communes d'exécution et d'extinction.\n"
                            "\n"
                            "Les sources principales sont le contrat (accord de volontés créateur de droits), le quasi-contrat (acte volontaire licite comme la gestion d'affaires), le délit civil (fait intentionnel illicite causant un dommage) et le quasi-délit (fait non intentionnel mais fautif). La loi peut également créer des obligations directement.\n"
                            "\n"
                            "L'exécution peut être naturelle (spontanée) ou forcée (imposée par justice). La mise en demeure somme le débiteur d'exécuter et fait courir les intérêts moratoires. L'exécution doit être conforme à la bonne foi.\n"
                            "\n"
                            "Les obligations s'éteignent par l'exécution, la confusion des qualités, la novation, la remise de dette, l'impossibilité d'exécution et la prescription extinctive."
                        ),
                        "theory_ar": (
                            "حق الالتزامات يُشكّل أساس القانون المدني. تنشأ الالتزامات من مصادر متعددة وتخضع لقواعد مشتركة.\n"
                            "\n"
                            "المصادر الرئيسية هي العقد (توافق إرادات) وشبه العقد (فعل طوعي مشروع كإدارة شؤون الغير) والجريمة المدنية (فعل مقصود غير مشروع يُسبب ضرراً) وشبه الجريمة (فعل غير مقصود لكنه خطأ). يمكن للقانون أيضًا إنشاء التزامات مباشرة.\n"
                            "\n"
                            "التنفيذ يمكن أن يكون طبيعيًا (طوعي) أو بالقوة الجبرية. الإنذار يُذكّر المدين بالوفاء ويجري الفوائد التأخيرية. يجب أن يكون التنفيذ وفق حسن النية.\n"
                            "\n"
                            "تنطفئ الالتزامات بالتنفيذ والالتباس والتجديد وإبراء الدين والاستحالة والتقادم."
                        ),
                        "vocab": [
                            {"fr": "l'offre", "ar": "العرض", "example": "L'offre doit être précise et définitive."},
                            {"fr": "l'acceptation", "ar": "القبول", "example": "L'acceptation doit être pure et simple."},
                            {"fr": "le consentement", "ar": "الرضا", "example": "Le consentement doit être libre et éclairé."},
                            {"fr": "la cause", "ar": "السبب", "example": "La cause illicite entraîne la nullité."},
                            {"fr": "l'objet", "ar": "الموضوع", "example": "L'objet doit être déterminé ou déterminable."},
                            {"fr": "la capacité", "ar": "الأهلية", "example": "Le mineur est frappé d'incapacité."},
                            {"fr": "le dol", "ar": "التدليس", "example": "Le dol vicie le consentement."},
                            {"fr": "la violence", "ar": "الإكراه", "example": "La violence rend le contrat nul."},
                            {"fr": "la mise en demeure", "ar": "الإنذار", "example": "La mise en demeure fait courir les intérêts."},
                            {"fr": "la résolution", "ar": "الفسخ", "example": "La résolution est prononcée par le juge."}
                        ],
                    },

                    {
                        "id": "fr_l2_u1_l4",
                        "title": "Le droit des contrats",
                        "title_ar": "قانون العقود",
                        "subtitle": "Formation, exécution et rupture du contrat",
                        "theory": (
                            "Le droit des contrats est au cœur des activités juridiques. La réforme du 10 février 2016 a modernisé les règles applicables, codifiées aux articles 1101 à 1233 du Code civil.\n"
                            "\n"
                            "La formation suppose le consentement libre et éclairé, la capacité de contracter, un objet certain et une cause licite. Les vices du consentement (erreur, dol, violence) entraînent la nullité. L'erreur sur la substance vicie également le consentement.\n"
                            "\n"
                            "L'exécution obéit au principe de bonne foi. En cas de manquement, le créancier peut demander l'exécution forcée en nature, la réduction du prix ou la résolution du contrat assortie de dommages-intérêts.\n"
                            "\n"
                            "La révision pour imprévision permet au juge d'adapter les clauses lorsque l'exécution est devenue excessivement onéreuse en raison d'un changement de circonstances imprévisible. Cette faculté tempère le principe de l'autonomie de la volonté."
                        ),
                        "theory_ar": (
                            "قانون العقود يُشكّل جوهر النشاط القانوني اليومي. إصلاح 10 فبراير 2016 حدّث القواعد المطبقة على العقود.\n"
                            "\n"
                            "التكوين يُشترط فيه رضا الأطراف الحر والأهلية وموضوع محدد وسبب مشروع. عيوب الرضا (الخطأ والتدليس والإكراه) تُبطل العقد. الخطأ في الجوهر يُبطل الرضا.\n"
                            "\n"
                            "التنفيذ يخضع لمبدأ حسن النية. في حالة الإخلال، يمكن للدائن طلب التنفيذ الجبري أو تخفيض السعر أو فسخ العقد مع تعويض.\n"
                            "\n"
                            "التصحيح للحالة غير المتوقعة يُتيح للقاضي تعديل البنود عندما يصبح التنفيذ مكلفًا بسبب تغير ظروف غير متوقعة. هذه الصلاحية تُخفّف من مبدأ سيادة الإرادة."
                        ),
                        "vocab": [
                            {"fr": "la bonne foi", "ar": "حسن النية", "example": "L'exécution du contrat obéit au principe de bonne foi."},
                            {"fr": "la nullité", "ar": "البطلان", "example": "La nullité du contrat entraîne la restitution."},
                            {"fr": "l'exécution forcée", "ar": "التنفيذ الجبري", "example": "L'exécution en nature est la règle."},
                            {"fr": "la résolution", "ar": "الفسخ", "example": "La résolution est prononcée par le juge."},
                            {"fr": "la réduction du prix", "ar": "تخفيض السعر", "example": "La réduction du prix est demandée en cas d'exécution imparfaite."},
                            {"fr": "l'imprévision", "ar": "الحالة غير المتوقعة", "example": "La révision pour imprévision permet d'adapter le contrat."},
                            {"fr": "le dommage-intérêt", "ar": "تعويض الأضرار", "example": "Le dommage-intérêt répare le préjudice subi."},
                            {"fr": "la clause", "ar": "البند", "example": "La clause pénale fixe les indemnités d'astreinte."},
                            {"fr": "le consentement vicié", "ar": "الرضا المعيوب", "example": "Le consentement vicié entraîne la nullité relative."},
                            {"fr": "la substance", "ar": "الجوهر", "example": "L'erreur sur la substance vicie le consentement."}
                        ],
                    },

                ],
            },

            {
                "id": "fr_l2_u2",
                "title": "Les branches du droit privé",
                "title_ar": "فروع القانون الخاص",
                "lessons": [
                    {
                        "id": "fr_l2_u2_l1",
                        "title": "La responsabilité civile",
                        "title_ar": "المسؤولية المدنية",
                        "subtitle": "Responsabilité du fait personnel et du fait d'autrui",
                        "theory": (
                            "La responsabilité civile vise la réparation des dommages causés à autrui. Elle obéit au principe de l'article 1240 du Code civil : tout fait quelconque de l'homme qui cause à autrui un dommage oblige celui par la faute duquel il est arrivé à le réparer.\n"
                            "\n"
                            "La responsabilité du fait personnel suppose une faute, un dommage certain et un lien de causalité. La faute peut être intentionnelle ou non, civile sans être pénalement punissable.\n"
                            "\n"
                            "La responsabilité du fait d'autrui engage le commettant pour les actes de ses préposés, les parents pour les actes de leurs enfants mineurs, le gardien d'un animal ou d'une chose.\n"
                            "\n"
                            "La responsabilité sans faute, ou objective, est engagée indépendamment de toute faute, notamment en matière de produits défectueux et de risques technologiques. La loi Badinter du 5 juillet 1985 organise la réparation des dommages causés par les accidents de la circulation."
                        ),
                        "theory_ar": (
                            "المسؤولية المدنية تهدف إلى تعويض الأضرار التي سببها الإنسان للغير. المادة 1240 من القانون المدني: كل فعل يُسبب ضرراً للغير يُلزم فاعله بالتعويض.\n"
                            "\n"
                            "المسؤولية عن الفعل الشخصي تشترط خطأ وضرراً مباشراً ورابطة سببية. الخطأ يمكن أن يكون عمدياً أو غير عمدي.\n"
                            "\n"
                            "المسؤولية عن فعل الغير تُحمّل صاحب العمل مسؤولية أفعال موظفيه، والآباء عن أطفالهم القاصرين، وحارس الحيوان أو الشيء.\n"
                            "\n"
                            "المسؤولية بدون خطأ تُحمّل بغض النظر عن أي خطأ، خاصة في مسؤولية التفريغ والمخاطر التقنية. قانون بدنتير يُنظّم تعويض حوادث المرور."
                        ),
                        "vocab": [
                            {"fr": "la faute", "ar": "الخطأ", "example": "La faute est la première condition de la responsabilité."},
                            {"fr": "le préjudice", "ar": "الضرر", "example": "Le préjudice doit être certain, direct et personnel."},
                            {"fr": "le lien de causalité", "ar": "الرابط السببي", "example": "Le lien de causalité unit la faute et le dommage."},
                            {"fr": "la responsabilité du fait d'autrui", "ar": "المسؤولية عن فعل الغير", "example": "Le commettant est responsable du fait de son préposé."},
                            {"fr": "le commettant", "ar": "صاحب العمل", "example": "Le commettant répond des actes de ses préposés."},
                            {"fr": "le préposé", "ar": "الموظف", "example": "Le préposé agit dans le cadre de ses fonctions."},
                            {"fr": "la responsabilité sans faute", "ar": "المسؤولية بدون خطأ", "example": "La responsabilité sans faute est objective."},
                            {"fr": "la garantie des vices cachés", "ar": "ضمان العيوب الخفية", "example": "Le vendeur est tenu de la garantie des vices cachés."},
                            {"fr": "la réparation intégrale", "ar": "التعويض الكامل", "example": "Le principe de réparation intégrale vise à replacer la victime."},
                            {"fr": "la cause étrangère", "ar": "القوة القاهرة", "example": "La force majeure exclut la responsabilité."}
                        ],
                    },

                    {
                        "id": "fr_l2_u2_l2",
                        "title": "Le droit commercial",
                        "title_ar": "القانون التجاري",
                        "subtitle": "Actes de commerce, sociétés et procédure collective",
                        "theory": (
                            "Le droit commercial encadre les activités des commerçants et les actes de commerce. Il se distingue du droit civil par des règles plus rapides et plus souples.\n"
                            "\n"
                            "Le commerçant exerce des actes de commerce à titre professionnel et habituel. Les actes de commerce comprennent les opérations d'achat-revente, le courtage, les transports et les opérations de banque. Le fonds de commerce est l'ensemble des éléments servant à l'exploitation de l'activité commerciale.\n"
                            "\n"
                            "Les sociétés commerciales les plus courantes sont la SARL (responsabilité limitée aux apports) et la SA (permet la cotation en bourse). La société par actions simplifiée (SAS) offre une grande liberté statutaire.\n"
                            "\n"
                            "La procédure collective comprend le redressement judiciaire (poursuite de l'activité sous contrôle), la liquidation judiciaire (cession des actifs) et les mesures préventives (mandat ad hoc, conciliation)."
                        ),
                        "theory_ar": (
                            "القانون التجاري يُنظم نشاط التجار والأعمال التجارية. يتميز عن القانون المدني بقواعد أسرع وأكثر مرونة.\n"
                            "\n"
                            "التاجر يمارس أعمالاً تجارية بشكل مهني واعتيادي. تشمل الأعمال التجارية عمليات الشراء والبيع والوساطة والنقل والعمليات المصرفية.\n"
                            "\n"
                            "الشركات التجارية الأكثر شيوعاً هي الشركة ذات المسؤولية المحدودة (مسؤولية المشاركين بحصصهم) والشركة المساهمة (تتيح التداول في البورصة). SAS تقدم حرية كبيرة في النظام الأساسي.\n"
                            "\n"
                            "الإجراءات الجماعية تشمل الإعادة القضائية (متابعة النشاط تحت الرقابة) والتصفية القضائية (بيع الأصول) والإجراءات الوقائية (المندوب الخاص والتسوية)."
                        ),
                        "vocab": [
                            {"fr": "le commerçant", "ar": "التاجر", "example": "Le commerçant est soumis aux obligations du Code de commerce."},
                            {"fr": "le fonds de commerce", "ar": "النشاط التجاري", "example": "La vente du fonds de commerce est soumise à des formalités."},
                            {"fr": "la SARL", "ar": "شركة ذات مسؤولية محدودة", "example": "La SARL est la forme sociétaire la plus répandue."},
                            {"fr": "la SA", "ar": "الشركة المساهمة", "example": "La SA permet la cotation en bourse."},
                            {"fr": "le redressement judiciaire", "ar": "الإعادة القضائية", "example": "Le redressement judiciaire permet la poursuite de l'activité."},
                            {"fr": "la liquidation judiciaire", "ar": "التصفية القضائية", "example": "La liquidation judiciaire entraîne la vente des actifs."},
                            {"fr": "le bilan", "ar": "الميزانية العمومية", "example": "Le bilan reflète la situation financière de l'entreprise."},
                            {"fr": "l'actif", "ar": "الأصول", "example": "L'actif comprend les biens meubles et immeubles."},
                            {"fr": "le passif", "ar": "الخصوم", "example": "Le passif comprend les dettes de l'entreprise."},
                            {"fr": "le mandataire ad hoc", "ar": "المندوب الخاص", "example": "Le mandataire ad hoc facilite la négociation avec les créanciers."}
                        ],
                    },

                    {
                        "id": "fr_l2_u2_l3",
                        "title": "Le droit administratif",
                        "title_ar": "القانون الإداري",
                        "subtitle": "Fonctionnement de l'administration et voies de recours",
                        "theory": (
                            "Le droit administratif régit les rapports entre l'administration et les administrés. Il organise le fonctionnement des services publics et garantit les droits des citoyens.\n"
                            "\n"
                            "Les actes administratifs se divisent en actes unilatéraux (décrets, arrêtés, décisions individuelles) et contrats administratifs. L'acte administratif crée des droits et des obligations. Le décret est pris par le Premier ministre ou un ministre. L'arrêté est pris par un maire ou un préfet.\n"
                            "\n"
                            "Le contrat administratif se distingue du contrat de droit commun par les clauses exorbitantes qu'il contient, notamment la modification unilatérale par l'administration.\n"
                            "\n"
                            "Les voies de recours sont le recours pour excès de pouvoir (contrôle de légalité) et le référé (mesures d'urgence). Le Conseil d'État est la juridiction suprême administrative."
                        ),
                        "theory_ar": (
                            "القانون الإداري يُنظم العلاقات بين الإدارة والمواطنين. يُنظّم عمل الخدمات العامة ويُكفل حقوق المواطنين.\n"
                            "\n"
                            "العمل الإداري ينقسم إلى أعمال أحادية (مراسيم وأوامر وقرارات فردية) وعقود إدارية. العمل الإداري يُنشئ حقوقاً والتزامات.\n"
                            "\n"
                            "العقد الإداري يتميز عن عقد القانون العام بالبنود الاستثنائية خاصة التعديل الأحادي من الإدارة.\n"
                            "\n"
                            "طرق الطعن هي الطعن في تجاوز السلطة (رقابة الشرعية) والتدبير المستعجل. مجلس الدولة هو المحكمة العليا للنظام الإداري."
                        ),
                        "vocab": [
                            {"fr": "l'acte administratif", "ar": "العمل الإداري", "example": "L'acte administratif unilatéral crée des obligations."},
                            {"fr": "le décret", "ar": "المرسوم", "example": "Le décret est publié au Journal officiel."},
                            {"fr": "l'arrêté", "ar": "الأمر", "example": "L'arrêté municipal réglemente la circulation."},
                            {"fr": "le service public", "ar": "الخدمة العامة", "example": "Le service public doit assurer l'égalité des usagers."},
                            {"fr": "le recours pour excès de poder", "ar": "الطعن في تجاوز السلطة", "example": "Le recours pour excès de pouvoir conteste la légalité."},
                            {"fr": "le Conseil d'État", "ar": "مجلس الدولة", "example": "Le Conseil d'État est juge en dernier ressort administratif."},
                            {"fr": "l'autorité de chose jugée", "ar": "قوة الشيء المحكوم به", "example": "L'autorité de chose jugée s'impose aux parties."},
                            {"fr": "le contrat administratif", "ar": "العقد الإداري", "example": "Le contrat administratif contient des clauses exorbitantes."},
                            {"fr": "l'usager du service public", "ar": "مستخدم الخدمة العامة", "example": "L'usager a droit à une égalité de traitement."},
                            {"fr": "la légalité", "ar": "الشرعيّة", "example": "Le contrôle de légalité est exercé par le juge administratif."}
                        ],
                    },

                ],
            },

            {
                "id": "fr_l2_u3",
                "title": "Les domaines spécialisés",
                "title_ar": "المجالات المتخصصة",
                "lessons": [
                    {
                        "id": "fr_l2_u3_l1",
                        "title": "Le droit de la propriété",
                        "title_ar": "قانون الملكية",
                        "subtitle": "Droits réels, immobiliers et mobiliers",
                        "theory": (
                            "Le droit de la propriété est un droit fondamental garanti par la Constitution. L'article 544 du Code civil la définit comme « le droit de jouir et disposer des choses de la manière la plus absolue ».\n"
                            "\n"
                            "La propriété se compose du droit d'usage, du droit de percevoir les fruits et du droit de disposer. Ces prérogatives sont limitées par les règles de voisinage, le droit de l'urbanisme et l'expropriation pour utilité publique.\n"
                            "\n"
                            "Les démembrements sont l'usufruit (jouissance de la chose d'autrui), l'usage et l'habitation. L'usufruitier jouit de la chose à charge d'en conserver la substance. Le nu-propriétaire conserve le droit de disposer.\n"
                            "\n"
                            "Les sûretés réelles comprennent l'hypothèque (bien immobilier) et le gage (bien meuble). La privation de propriété ne peut intervenir qu'en cas d'utilité publique moyennant une indemnisation préalable et juste."
                        ),
                        "theory_ar": (
                            "حق الملكية حق أساسي مُكفّل بالدستور. المادة 544 تُعرّفها بأنها « حق التمتع والتصرف بالأشياء بأعلى درجة ». يتكون من حق الاستمتاع وحق تحصيل الثمار وحق التصرف.\n"
                            "\n"
                            "هذه الصلحيات مُقيّدة بقواعد الجوار والتخطيط الحضري والاستملاك للمصلحة العامة.\n"
                            "\n"
                            "تقاسيم الملكية هي الاستثناء والاستعمال والسكنى. المستفيد بالاستثناء يتمتع بشيء يملكه غيره شريطة الحفاظ على جوهره. مالك析分权利 يحتفظ بحق التصرف.\n"
                            "\n"
                            "الضمانات العينية تشمل الرهن العقاري (مال عقاري) والرهن النقدي (مال منقول). سلب الملكية لا يتم إلا في حالة المصلحة العامة ومقابل تعويض سابق وعادل."
                        ),
                        "vocab": [
                            {"fr": "la propriété", "ar": "الملكية", "example": "La propriété est le droit de jouir et disposer."},
                            {"fr": "l'usufruit", "ar": "الاستثناء", "example": "L'usufruitier a le droit de jouir de la chose."},
                            {"fr": "la nue-propriété", "ar": "حق التملك", "example": "Le nu-propriétaire conserve le droit de disposer."},
                            {"fr": "l'hypothèque", "ar": "الرهن العقاري", "example": "L'hypothèque garantit le remboursement du prêt."},
                            {"fr": "le gage", "ar": "الرهن النقدي", "example": "Le gage porte sur des biens meubles."},
                            {"fr": "l'expropriation", "ar": "الاستملاك", "example": "L'expropriation pour utilité publique est indemnisée."},
                            {"fr": "les servitudes", "ar": "حقوق الارتفاق", "example": "Les servitudes limitent l'exercice du droit de propriété."},
                            {"fr": "la mitoyenneté", "ar": "المشترك في الجدار", "example": "La mitoyenneté suppose un mur partagé entre voisins."},
                            {"fr": "le droit de superficie", "ar": "حق التشييد", "example": "Le droit de superficie permet de construire sur le terrain d'autrui."},
                            {"fr": "leDomaine public", "ar": "الممتلكات العامة", "example": "LeDomaine public est inaliénable et imprescriptible."}
                        ],
                    },

                    {
                        "id": "fr_l2_u3_l2",
                        "title": "Le droit international privé",
                        "title_ar": "القانون الدولي الخاص",
                        "subtitle": "Conflits de lois et conflits de juridictions",
                        "theory": (
                            "Le droit international privé règle les situations juridiques impliquant un élément d'extranéité.\n"
                            "\n"
                            "Les conflits de lois surgissent lorsque plusieurs législations revendiquent l'application à une même situation. La règle de conflit désigne la loi applicable. En matière contractuelle, le règlement Rome I permet aux parties de choisir la loi applicable. En l'absence de choix, la loi applicable est celle du pays avec lequel le contrat présente le lien le plus étroit.\n"
                            "\n"
                            "Les conflits de juridictions déterminent la juridiction compétente. Le règlement Bruxelles I bis prévoit des règles de compétence entre États membres. Le for convenu permet aux parties de choisir la juridiction.\n"
                            "\n"
                            "La reconnaissance des jugements étrangers obéit à des conditions spécifiques. Un jugement étranger peut être reconnu s'il réunit les conditions de compétence internationale et s'il ne viole pas l'ordre public international."
                        ),
                        "theory_ar": (
                            "القانون الدولي الخاص يُحل الوضعيات القانونية التي تتضمن عنصرًا أجنبيًا.\n"
                            "\n"
                            "تعارض القوانين ينشأ عندما تدّعي عدة تشريعات تطبيقها على نفس الوضعية. قاعدة التعارض تُحدّد القانون المطبق. في الأمور العقدية، يُتيح نظام روما الأول اختيار القانون المطبق. في غياب الاختيار يكون القانون المطبق هو قانون الدولة بأوثق رابطة.\n"
                            "\n"
                            "تعارض الاختصاصات يُحدّد المحكمة المختصة. نظام بروكسل الأول يضع قواعد الاختصاص بين دول الاتحاد الأوروبي. الاتفاق على الاختصاص يُتيح اختيار المحكمة.\n"
                            "\n"
                            "الاعتراف بالأحكام الأجنبية يخضع لشروط. يمكن الاعتراف بحكم أجنبي إذا تحققت شروط الاختصاص الدولي وإذا لم ينتهك النظام العام الدولي."
                        ),
                        "vocab": [
                            {"fr": "l'élément d'extranéité", "ar": "العنصر الأجنبي", "example": "L'élément d'extranéité déclenche l'application du droit international privé."},
                            {"fr": "la règle de conflit", "ar": "قاعدة التعارض", "example": "La règle de conflit désigne la loi applicable."},
                            {"fr": "la loi applicable", "ar": "القانون المطبق", "example": "La loi applicable est déterminée par le règlement Rome I."},
                            {"fr": "la compétence internationale", "ar": "الاختصاص الدولي", "example": "La compétence internationale détermine le juge compétent."},
                            {"fr": "le for", "ar": "المحكمة المختصة", "example": "Le for convenu est choisi par les parties."},
                            {"fr": "l'exequatur", "ar": "التنفيذ", "example": "L'exequatur est nécessaire pour exécuter un jugement étranger."},
                            {"fr": "l'ordre public international", "ar": "النظام العام الدولي", "example": "La reconnaissance est refusée en cas de violation de l'ordre public."},
                            {"fr": "le règlement Rome I", "ar": "نظام روما الأول", "example": "Le règlement Rome I régit la loi applicable aux contrats."},
                            {"fr": "le règlement Bruxelles I bis", "ar": "نظام بروكسل الأول", "example": "Le règlement Bruxelles I bis organise la compétence judiciaire."},
                            {"fr": "la convention d'arbitrage", "ar": "اتفاقية التحكيم", "example": "La convention d'arbitrage exclut la compétence des tribunaux étatiques."}
                        ],
                    },

                    {
                        "id": "fr_l2_u3_l3",
                        "title": "Les voies de recours",
                        "title_ar": "طرق الطعن",
                        "subtitle": "Appel, cassation, tierce opposition et opposition",
                        "theory": (
                            "Les voies de recours permettent de contester les décisions de justice. Elles se divisent en voies ordinaires (opposition, appel) et voies extraordinaires (cassation, tierce opposition, révision).\n"
                            "\n"
                            "L'opposition est le recours contre un jugement par défaut. L'appel est le recours principal contre les jugements de première instance. Il a un effet dévolutif : le juge d'appel réexamine l'affaire en fait et en droit. Le délai est d'un mois à compter de la signification.\n"
                            "\n"
                            "Le pourvoi en cassation n'est pas un troisième degré de juridiction. Il vise uniquement à vérifier la correcte application de la loi. La Cour de cassation contrôle la régularité de la procédure sans réexaminer les faits.\n"
                            "\n"
                            "La tierce opposition permet à un tiers non partie au procès de contester un jugement qui lui porte préjudice. La révision est un recours extraordinaire ouvert en cas de découverte de faits nouveaux. L'opposition à exécution forcée permet au tiers saisi de contester la saisie."
                        ),
                        "theory_ar": (
                            "طرق الطعن تُتيح الطعن في قرارات المحاكم. تنقسم إلى طرق عادية (الاستدعاء والاستئناف) وطرق استثنائية (النقض والاعتراض والتحقيق).\n"
                            "\n"
                            "الاستدعاء هو الطعن ضد حكم غيابي. الاستئناف هو الطعن الرئيسي ضد أحكام أول درجة. له أثر إضافي: القاضي يعيد نظر القضية في الوقائع والقانون. المدة شهر من التبليغ.\n"
                            "\n"
                            "النقض ليس درجة ثالثة في المحاكمات. يهدف فقط إلى التحقق من صحة تطبيق القانون.محكمة النقض تتحقق من نظامية الإجراءات دون إعادة النظر في الوقائع.\n"
                            "\n"
                            "الاعتراض يُتيح لشخص غير طرف الطعن في حكم يُلحق بضرراً. التحقيق طريق استثنائي يُفتح في حالة اكتشاف وقائع جديدة."
                        ),
                        "vocab": [
                            {"fr": "l'appel", "ar": "الاستئناف", "example": "L'appel doit être formé dans le délai d'un mois."},
                            {"fr": "l'opposition", "ar": "الاستدعاء", "example": "L'opposition est formée contre un jugement par défaut."},
                            {"fr": "le pourvoi en cassation", "ar": "الطعن بالنقض", "example": "Le pourvoi en cassation viole la correcte application de la loi."},
                            {"fr": "la tierce opposition", "ar": "الاعتراض", "example": "La tierce opposition est ouverte au tiers lésé."},
                            {"fr": "l'effet dévolutif", "ar": "الأثر الإضافي", "example": "L'effet dévolutif soumet l'affaire entière à la cour d'appel."},
                            {"fr": "l'autorité de la chose jugée", "ar": "قوة الشيء المحكوم به", "example": "L'autorité de la chose jugée s'oppose à la rejugure."},
                            {"fr": "la cassation", "ar": "النقض", "example": "La cassation annule le jugement pour violation de la loi."},
                            {"fr": "la révision", "ar": "التحقيق", "example": "La révision est un recours extraordinaire."},
                            {"fr": "le délai", "ar": "المدة", "example": "Le délai de recours est de un mois."},
                            {"fr": "la signification", "ar": "التبليغ", "example": "La signification fait courir les délais de recours."}
                        ],
                    },

                ],
            },

        ],
    },

    {
        "id": 3,
        "title": "Supérieur — المتقدم",
        "description": "النصوص التشريعية والتحليل النقدي والكتابة القانونية",
        "color": "#d97706",
        "units": [
            {
                "id": "fr_l3_u1",
                "title": "L'analyse législative",
                "title_ar": "التحليل التشريعي",
                "lessons": [
                    {
                        "id": "fr_l3_u1_l1",
                        "title": "La lecture des textes législatifs",
                        "title_ar": "قراءة النصوص التشريعية",
                        "subtitle": "Anatomie d'un texte législatif",
                        "theory": (
                            "Un article de loi suit une structure codifiée. Il comprend l'amendement (modification proposée), l'article (disposition principale), l'alinéa (paragraphe) et la rubrique (titre de section). Les articles peuvent être définissants, prescrivant, autorisant, interdisant ou sanctionnant.\n"
                            "\n"
                            "L'interprétation littérale recherche le sens grammatical des mots utilisés par le législateur. L'interprétation téléologique recherche le but poursuivi par la loi. L'interprétation historique s'appuie sur les travaux préparatoires. L'interprétation systématique vérifie la cohérence avec l'ensemble du texte.\n"
                            "\n"
                            "La maxime « Le législateur n'omet pas ce qu'il connaît » signifie qu'un silence du législateur est volontaire. L'interprétation a contrario tire argument de l'omission. L'interprétation extensive s'applique aux droits fondamentaux, tandis que l'interprétation stricte s'applique aux lois pénales et fiscales."
                        ),
                        "theory_ar": (
                            "تتبع المادة القانونية بنية معيارية. تشمل التعديل والمادة والفقرة والعنوان. قد تكون المواد تحديدية أو إلزامية أو تخليصية أو تحريمية أو عقابية.\n"
                            "\n"
                            "التفسير الحرفية يبحث عن المعنى النحوي للكلمات. التفسير الغائي يبحث عن هدف القانون. التفسير التاريخية تعتمد على الأعمال التحضيرية. التفسير المنهجية تتحقق من التناسق مع النص الكامل.\n"
                            "\n"
                            "المبدأ « لا يُغفل المشرّع ما يعرفه » يعني أن صمت المشرّع إرادي. التفسير بالمفاسد يحتج بالإغفال. التفسير الواسع ينطبق على الحقوق الأساسية، بينما التفسير الضيق ينطبق على القوانين الجنائية والضريبية."
                        ),
                        "vocab": [
                            {"fr": "l'article", "ar": "المادة", "example": "L'article 544 du Code civil définit la propriété."},
                            {"fr": "l'alinéa", "ar": "الفقرة", "example": "Le premier alinéa prévoit une exception."},
                            {"fr": "l'amendement", "ar": "التعديل", "example": "L'amendement a été adopté à la majorité."},
                            {"fr": "la rubrique", "ar": "العنوان للقسم", "example": "La rubrique du chapitre précise le sujet."},
                            {"fr": "l'interprétation", "ar": "التفسير", "example": "L'interprétation de la loi est délicate."},
                            {"fr": "les travaux préparatoires", "ar": "الأعمال التحضيرية", "example": "Les travaux préparatoires éclairent la loi."},
                            {"fr": "l'interprétation stricte", "ar": "التفسير الضيق", "example": "Les peines sont d'interprétation stricte."},
                            {"fr": "l'interprétation extensive", "ar": "التفسير الموسع", "example": "Les droits fondamentaux reçoivent une interprétation extensive."},
                            {"fr": "le sens littéral", "ar": "المعنى الحرفية", "example": "On privilégie le sens littéral des termes."},
                            {"fr": "le but de la loi", "ar": "غاية القانون", "example": "L'interprétation téléologique recherche le but."}
                        ],
                    },

                    {
                        "id": "fr_l3_u1_l2",
                        "title": "L'interprétation des lois",
                        "title_ar": "تفسير القوانين",
                        "subtitle": "Méthodes et techniques d'interprétation juridique",
                        "theory": (
                            "L'interprétation des lois est l'art de déterminer le sens exact d'une disposition législative. Plusieurs méthodes coexistent en doctrine.\n"
                            "\n"
                            "L'interprétation authentique est celle donnée par le législateur lui-même à travers une loi d'interprétation. L'interprétation judiciaire est celle dégagée par les juges à travers leur jurisprudence. L'interprétation doctrinale émane des professeurs et praticiens.\n"
                            "\n"
                            "La règle d'interprétation « derogatio generalibus non praesumitur » signifie que la dérogation à une règle générale n'est pas présumée. Le specialia derogant generalibus veut que la disposition spéciale l'emporte sur la disposition générale.\n"
                            "\n"
                            "En cas de doute, le juge recherche la solution la plus favorable aux droits fondamentaux. L'interprétation constitutionnelle impose de privilégier le sens conforme à la Constitution. Le contrôle de conventionalité vérifie la conformité des lois aux traités internationaux."
                        ),
                        "theory_ar": (
                            "تفسير القوانين هو فن تحديد المعنى الدقيق لحكم تشريعي. تتعدد مناهج الفقه في هذا المجال.\n"
                            "\n"
                            "التفسير التفويضي هو الذي يُعطيه المشرّع نفسه من خلال قانون تفسيري. التفسير القضائي هو الذي تتبعه المحاكم من خلال اجتهاداتها. التفسير الفقهي يصدر عن الأساتذة والباحثين.\n"
                            "\n"
                            "قاعدة « لا يُفترض الاستثناء من القاعدة العامة » تعني أن التخلي عن قاعدة عامة لا يُفترض. القاعدة الخاصة تتفوق على العامة.\n"
                            "\n"
                            "في حالة الشك، يبحث القاضي عن الحل الأ favoriser للحقوق الأساسية. التفسير الدستوري يفرض أولوية المعنى المتفق مع الدستور. رقابة المطابقة تتحقق من توافق القوانين مع المعاهدات الدولية."
                        ),
                        "vocab": [
                            {"fr": "l'interprétation authentique", "ar": "التفسير التفويضي", "example": "L'interprétation authentique émane du législateur."},
                            {"fr": "l'interprétation judiciaire", "ar": "التفسير القضائي", "example": "L'interprétation judiciaire se dégage de la jurisprudence."},
                            {"fr": "l'interprétation restrictive", "ar": "التفسير الضيق", "example": "L'interprétation restrictive s'applique aux sanctions."},
                            {"fr": "l'interprétation extensive", "ar": "التفسير الموسع", "example": "L'interprétation extensive s'applique aux droits fondamentaux."},
                            {"fr": "le contrôle de conventionality", "ar": "رقابة المطابقة", "example": "Le contrôle de conventionality vérifie la conformité aux traités."},
                            {"fr": "la dérogation", "ar": "الاستثناء", "example": "La dérogation à une règle générale doit être express."},
                            {"fr": "le doute interprétatif", "ar": "الشك التفسيري", "example": "En cas de doute, on privilégie l'interprétation favorable."},
                            {"fr": "la hiérarchie des interprétations", "ar": "تراتبية التفسيرات", "example": "L'interprétation constitutionnelle prime sur les autres."},
                            {"fr": "le sens commun", "ar": "المعنى السائغ", "example": "On recherche d'abord le sens commun des termes."},
                            {"fr": "la portée de la loi", "ar": "نطاق القانون", "example": "La portée de la loi se détermine par son texte et son esprit."}
                        ],
                    },

                    {
                        "id": "fr_l3_u1_l3",
                        "title": "La rédaction juridique",
                        "title_ar": "الكتابة القانونية",
                        "subtitle": "Structure et style des écrits juridiques",
                        "theory": (
                            "La rédaction juridique exige rigueur et clarté. La structure d'un mémoire comprend l'en-tête (identité des parties), l'exposé des faits (narration chronologique), la discussion (argumentation juridique), le dispositif (demandes précises) et les conclusions.\n"
                            "\n"
                            "Le style de la rédaction requiert des phrases courtes et claires, l'usage de connecteurs logiques : « toutefois » (néanmoins), « en outre » (de plus), « en revanche » (au contraire), « en conséquence » (donc), « dès lors » (par conséquent).\n"
                            "\n"
                            "Il faut éviter les pléonasmes juridiques (« annuler et réformer ») et les anglicismes (« le data » → « la donnée »). Le vocabulaire doit être précis et constant tout au long du document. Les références aux articles de loi et à la jurisprudence renforcent la crédibilité de l'écrit."
                        ),
                        "theory_ar": (
                            "تتطلب الكتابة القانونية الدقة والوضوح. بنية المذكرة تتضمن الترويسة وعرض الوقائع والنقاش والمطلب والخلاصة.\n"
                            "\n"
                            "أسلوب الكتابة يتطلب جمل قصيرة وواضحة واستخدام روابط منطقية: « toutefois » (ومع ذلك) و « en outre » (بالإضافة إلى) و « en revanche » (عكس ذلك) و « en conséquence » (نتيجة لذلك) و « dès lors » (إذن).\n"
                            "\n"
                            "يجب تجنب التكرارات القانونية والنعومات الإنجليزية. المصطلحات يجب أن تكون دقيقة ومتينة طوال المستند. الإشارات إلى المواد القانونية والاجتهادات تعزز مصداقية الكتابة."
                        ),
                        "vocab": [
                            {"fr": "le mémoire", "ar": "المذكرة", "example": "Le mémoire en appel est déposé dans le délai."},
                            {"fr": "l'exposé des faits", "ar": "عرض الوقائع", "example": "L'exposé des faits doit être chronologique."},
                            {"fr": "la discussion", "ar": "النقاش", "example": "La discussion comprend l'argumentation juridique."},
                            {"fr": "le dispositif", "ar": "المطلب", "example": "Le dispositif contient les demandes précises."},
                            {"fr": "les conclusions", "ar": "الخلاصة", "example": "Les conclusions résument l'argumentation."},
                            {"fr": "toutefois", "ar": "ومع ذلك", "example": "Toutefois, cette solution est contestée."},
                            {"fr": "en outre", "ar": "بالإضافة إلى ذلك", "example": "En outre, le demandeur invoque..."},
                            {"fr": "en revanche", "ar": "في المقابل", "example": "En revanche, le défendeur soutient que..."},
                            {"fr": "en conséquence", "ar": "نتيجة لذلك", "example": "En conséquence, le contrat est nul."},
                            {"fr": "dès lors", "ar": "إذن", "example": "Dès lors, le juge doit statuer."}
                        ],
                    },

                    {
                        "id": "fr_l3_u1_l4",
                        "title": "Le style des codes",
                        "title_ar": "أسلوب المدونات القانونية",
                        "subtitle": "Technique de codification et rédaction législative",
                        "theory": (
                            "La codification est l'art d'organiser méthodiquement un ensemble de règles de droit dans un texte unique appelé code. Le Code civil français, entré en vigueur en 1804, reste le modèle de référence.\n"
                            "\n"
                            "Un code suit une architecture codifiée : des livres divisés en titres, des titres en chapitres, des chapitres en sections, et des sections en articles. Chaque article est numéroté et doit être autonome dans son énoncé.\n"
                            "\n"
                            "Le style du code se caractérise par des énoncés généraux et abstraits. Le législateur emploie le présent de vérité générale (« la propriété est le droit de... »). Les définitions sont placées en tête des matières. Les conditions sont énumérées de manière limitative.\n"
                            "\n"
                            "Le pouvoir réglementaire complète les codes par des décrets d'application. Les lois spéciales dérogent aux codes dans des matières particulières. La cohérence du code est un objectif constant du législateur."
                        ),
                        "theory_ar": (
                            "التنظيم هو فن ترتيب مجموعة القواعد القانونية في نص وحيد يُسمّى مدونة. القانون المدني الفرنسي النموذج.\n"
                            "\n"
                            "تتبع المدونة بنية معيارية: كُتب مقسمة إلى أقسام وأقسام إلى فصول وفصول إلى أقسام وSections إلى مواد. كل مادة مُرقمة ويجب أن تكون مستقلة في صياغتها.\n"
                            "\n"
                            "يتميز أسلوب المدونة بالبيانات العامة والمجردة. يستخدم المشرّع المضار للحقيقة العامة. التعريفات تُوضع في بداية المواضيع. الشروط تُسرد على سبيل الحصر.\n"
                            "\n"
                            "السلطة التنظيمية تُكمل المدونات بمراسيم التطبيق. القوانين الخاصة تستثنى من المدونات في مواضيع محددة. التناسق هو هدف دائم للمشرّع."
                        ),
                        "vocab": [
                            {"fr": "la codification", "ar": "التنظيم", "example": "La codification organise les règles de droit dans un code."},
                            {"fr": "le code", "ar": "المدونة", "example": "Le Code civil est la référence du droit français."},
                            {"fr": "le livre", "ar": "الكتاب", "example": "Le livre divise le code en grandes parties."},
                            {"fr": "le titre", "ar": "القسم", "example": "Le titre regroupe les matières proches."},
                            {"fr": "l'article", "ar": "المادة", "example": "Chaque article du code est numéroté."},
                            {"fr": "le décret d'application", "ar": "مرسوم التطبيق", "example": "Le décret d'application précise les modalités."},
                            {"fr": "la loi spéciale", "ar": "القانون الخاص", "example": "La loi spéciale déroge au code dans sa matière."},
                            {"fr": "l'énumération limitative", "ar": "السرد على سبيل الحصر", "example": "Les conditions sont énumérées de manière limitative."},
                            {"fr": "le présent de vérité générale", "ar": "المضار للحقيقة العامة", "example": "Le législateur emploie le présent de vérité générale."},
                            {"fr": "la cohérence", "ar": "التناسق", "example": "La cohérence du code est un objectif constant."}
                        ],
                    },

                ],
            },

            {
                "id": "fr_l3_u2",
                "title": "Les actes juridiques",
                "title_ar": "الالتحريات القانونية",
                "lessons": [
                    {
                        "id": "fr_l3_u2_l1",
                        "title": "Les actes juridiques",
                        "title_ar": "الالتحريات القانونية",
                        "subtitle": "Classification, forme et validityé des actes juridiques",
                        "theory": (
                            "Les actes juridiques sont les manifestations de volonté destinées à produire des effets juridiques. On les distingue des actes juridiques unilatéraux (une seule volonté) et des actes bilatéraux ou multilatéraux (contrats).\n"
                            "\n"
                            "La forme des actes peut être solennelle (requérant des formalités spéciales, comme l'acte notarié) ou libre (sans forme imposée, comme les contrats consensuels). L'acte authentique, reçu par un officier public, fait foi de son contenu jusqu'à inscription de faux.\n"
                            "\n"
                            "Les conditions de validité d'un acte sont : la capacité de l'auteur, la licéité de l'objet, la réalité du consentement. Les vices (erreur, dol, violence, lésion) entraînent la nullité relative ou absolue.\n"
                            "\n"
                            "L'interprétation des actes juridiques obéit au principe de bonne foi. Le juge recherche la commune intention des parties plutôt que le sens littéral des termes. Les clauses ambigues s'interprètent contre le rédacteur (contra proferentem)."
                        ),
                        "theory_ar": (
                            "الالتحريات القانونية هي تظاهرات الإرادة المُنشئة لتأثيرات قانونية. تُميّز بين الالتحريات الأحادية (إرادة واحدة) والثنائية أو متعددة (العقود).\n"
                            "\n"
                            "يمكن أن تكون الشكلية رسمية (تتطلب إجراءات خاصة كالعقد الموثق) أو حرة (دون شكل مفروض كالعقود التراضية). العمل الرسمي الذي يتولاه موظف عام يُثبت مضمونه حتى الإثبات بالتزوير.\n"
                            "\n"
                            "شروط صحة العمل هي أهلية المُحرّر ومشروعية الموضوع ورضا حقيقية. العيوب (الخطأ والتدليس والإكراه والغبن) تُبطل العمل نسبياً أو مطلقاً.\n"
                            "\n"
                            "تفسير الالتحريات يخضع لمبدأ حسن النية. يبحث القاضي عن النية المشتركة للأطراف بدلاً من المعنى الحرفية. البنود الغامضة تُفسّر ضد صاحبها."
                        ),
                        "vocab": [
                            {"fr": "l'acte juridique", "ar": "الالتحري القانوني", "example": "L'acte juridique est une manifestation de volonté."},
                            {"fr": "l'acte authentique", "ar": "العمل الرسمي", "example": "L'acte authentique fait foi jusqu'à inscription de faux."},
                            {"fr": "l'acte sous seing privé", "ar": "العمل الخاص", "example": "L'acte sous seing privé a force probante entre les parties."},
                            {"fr": "la forme solennelle", "ar": "الشكلية الرسمية", "example": "La forme solennelle requiert des formalités spéciales."},
                            {"fr": "la forme consensuelle", "ar": "الشكلية التراضية", "example": "La forme consensuelle n'exige aucune formalité."},
                            {"fr": "la nullité relative", "ar": "البطلان النسبي", "example": "La nullité relative ne peut être invoquée que par la partie lésée."},
                            {"fr": "la nullité absolue", "ar": "البطلان المطلق", "example": "La nullité absolue peut être invoquée par tous."},
                            {"fr": "l'inscription de faux", "ar": "الإثبات بالتزوير", "example": "L'inscription de faux remet en cause l'authenticité d'un acte."},
                            {"fr": "le contra proferentem", "ar": "التفسير ضد الصياغ", "example": "Les clauses ambiguës s'interprètent contre le rédacteur."},
                            {"fr": "la commune intention des parties", "ar": "النية المشتركة للأطراف", "example": "Le juge recherche la commune intention des parties."}
                        ],
                    },

                    {
                        "id": "fr_l3_u2_l2",
                        "title": "La preuve en droit",
                        "title_ar": "الإثبات في القانون",
                        "subtitle": "Modes de preuve et charge de la preuve",
                        "theory": (
                            "La preuve en droit civil se définit par tout moyen permettant de convaincre le juge de la véracité d'un fait allégué. La charge de la preuve repose en principe sur celui qui invoque un droit (actori incumbit probatio).\n"
                            "\n"
                            "Les modes de preuve comprennent la preuve littérale (écrits, contrats, actes authentiques), la preuve testimoniale (témoignages), la preuve par présomptions (indices graves, précis et concordants), l'aveu (reconnaissance d'un fait par la partie contre laquelle il est invoqué) et le serment.\n"
                            "\n"
                            "La preuve littérale peut être authentique (acte notarié) ou sous seing privé (accord entre les parties). L'écrit électronique a la même valeur que l'écrit papier depuis la loi de 2000.\n"
                            "\n"
                            "Certaines matières sont soumises à un régime de preuve spécifique : la preuve du contrat doit être écrite si la valeur excède un certain seuil, conformément à l'article 1341 du Code civil."
                        ),
                        "theory_ar": (
                            "الإثبات في القانون المدني يشمل كل وسيلة تُقنع القاضي بصحة حقيقة مزعومة. عبء الإثبات يقع في الأصل على من يدّعي حقاً.\n"
                            "\n"
                            "تشمل وسائل الإثبات الإثبات المكتوب (عقود ومذكرات ورسائل) والإثبات بالشهادة والإثبات بالقرائن (دلائل جدية ودقيقة ومتوافقة) والإقرار (اعتراف طرف بحقيقة ضد نفسه) والقسم.\n"
                            "\n"
                            "يمكن أن يكون الإثبات المكتوب رسميأً (عقد موثق) أو خاصاً (اتفاق بين الأطراف). الكتابة الإلكترونية لها نفس قيمة الورقي.\n"
                            "\n"
                            "بعض المواضيع تخضع لنظام إثبات خاص: إثبات العقد يجب أن يكون مكتوباً إذا تجاوزت القيمة عتبة معينة."
                        ),
                        "vocab": [
                            {"fr": "la charge de la preuve", "ar": "عبء الإثبات", "example": "La charge de la preuve incombe à celui qui allègue."},
                            {"fr": "la preuve littérale", "ar": "الإثبات المكتوب", "example": "La preuve littérale est constituée par les écrits."},
                            {"fr": "la preuve testimoniale", "ar": "الإثبات بالشهادة", "example": "La preuve testimoniale consiste en témoignages."},
                            {"fr": "l'aveu", "ar": "الإقرار", "example": "L'aveu est la reconnaissance d'un fait par une partie."},
                            {"fr": "le serment", "ar": "القسم", "example": "Le serment est une affirmation solennelle devant le juge."},
                            {"fr": "les présomptions", "ar": "القرائن", "example": "Les présomptions sont des indices graves et concordants."},
                            {"fr": "l'acte authentique", "ar": "العمل الرسمي", "example": "L'acte authentique fait pleine foi jusqu'à faux."},
                            {"fr": "l'écrit électronique", "ar": "الكتابة الإلكترونية", "example": "L'écrit électronique a la même valeur que l'écrit papier."},
                            {"fr": "le seuil de preuve", "ar": "عتبة الإثبات", "example": "Au-delà d'un certain seuil, la preuve doit être écrite."},
                            {"fr": "l'inscription de faux", "ar": "الإثبات بالتزوير", "example": "L'inscription de faux est la contestation de l'authenticité."}
                        ],
                    },

                    {
                        "id": "fr_l3_u2_l3",
                        "title": "L'arbitrage",
                        "title_ar": "التحكيم",
                        "subtitle": "Règlement alternatif des différends et arbitrage commercial",
                        "theory": (
                            "L'arbitrage est un mode de règlement des différends par lequel les parties conviennent de soumettre leur litige à des arbitres de leur choix plutôt qu'à la juridiction étatique.\n"
                            "\n"
                            "L'arbitrage peut être institutional (sous l'égide d'une institution comme la Cour internationale d'arbitrage de Paris) ou ad hoc (sans intervention d'une institution). La convention d'arbitrage est la clause par laquelle les parties s'engagent à soumettre à l'arbitrage tous les différends nés ou à naître du contrat.\n"
                            "\n"
                            "La sentence arbitrale a l'autorité de la chose jugée et est exécutoire sans exequatur. Elle ne peut être attaquée que devant la cour d'appel pour des motifs limitativement énumérés (inexistence ou irrégularité de la convention d'arbitrage, composition irrégulière du tribunal, méconnaissance du droit de la défense).\n"
                            "\n"
                            "L'arbitrage international est régi par la partie IV du Nouveau Code de procédure civile. Il offre des avantages en matière de confidentialité, de rapidité et de neutralité du for."
                        ),
                        "theory_ar": (
                            "التحكيم هو وسيلة لتسوية النزاعات يتفق بموجبها الأطراف على إحالة نزاعهم إلى محكمين يختارونهم بدلاً من المحكمة الوطنية.\n"
                            "\n"
                            "يمكن أن يكون تحكيماً مؤسسياً (تحت إشراف مؤسسة) أو تحكيماً خاصاً (بدون تدخل مؤسسي). اتفاقية التحكيم هي البند الذي يُلتزم فيه الأطراف بتحكيم كل النزاعات.\n"
                            "\n"
                            "الحكم التحكيمي له قوة الشيء المحكوم به وقابل للتنفيذ دون تفويض. لا يمكن الطعن فيه إلا أمام محكمة الاستئناف لأسباب محددة.\n"
                            "\n"
                            "التحكيم الدولي يخضع للجزء الرابع من قانون الإجراءات المدنية الجديد. يقدم مزايا في السرية والسرعة وحيادية المحكمة."
                        ),
                        "vocab": [
                            {"fr": "l'arbitrage", "ar": "التحكيم", "example": "L'arbitrage est un mode alternatif de règlement des différends."},
                            {"fr": "la convention d'arbitrage", "ar": "اتفاقية التحكيم", "example": "La convention d'arbitrage est la base de la compétence arbitrale."},
                            {"fr": "la sentence arbitrale", "ar": "الحكم التحكيمي", "example": "La sentence arbitrale a l'autorité de la chose jugée."},
                            {"fr": "l'arbitre", "ar": "المحكم", "example": "L'arbitre est désigné par les parties ou par une institution."},
                            {"fr": "l'arbitrage institutionnel", "ar": "التحكيم المؤسسي", "example": "L'arbitrage institutionnel est administré par une institution."},
                            {"fr": "l'arbitrage ad hoc", "ar": "التحكيم الخاص", "example": "L'arbitrage ad hoc se déroule sans intervention institutionnelle."},
                            {"fr": "la confidentialité", "ar": "السرية", "example": "L'arbitrage offre la confidentialité des débats."},
                            {"fr": "l'exequatur", "ar": "التفويض", "example": "L'exequatur rend la sentence arbitrale exécutoire."},
                            {"fr": "le for arbitral", "ar": "المحكمة التحكيمية", "example": "Le for arbitral est le lieu où se déroule l'arbitrage."},
                            {"fr": "la clause compromissoire", "ar": "بند التحكيم", "example": "La clause compromissoire soumet les litiges futurs à l'arbitrage."}
                        ],
                    },

                ],
            },

            {
                "id": "fr_l3_u3",
                "title": "Le droit international et européen",
                "title_ar": "القانون الدولي والأوروبي",
                "lessons": [
                    {
                        "id": "fr_l3_u3_l1",
                        "title": "Le droit européen",
                        "title_ar": "القانون الأوروبي",
                        "subtitle": "Droit de l'Union européenne et Convention européenne des droits de l'homme",
                        "theory": (
                            "Le droit européen se compose du droit de l'Union européenne (UE) et de la Convention européenne des droits de l'homme (CEDH). Ces deux systèmes se superposent au droit interne.\n"
                            "\n"
                            "Le droit de l'UE se décline en règlements (directement applicables), directives (nécessitant une transposition) et décisions (individuelles). Le principe de primauté du droit de l'UE sur le droit interne a été consacré par la Cour de justice de l'UE. Le principe d'effet direct permet aux particuliers d'invoquer devant leur juge national les dispositions du droit de l'UE.\n"
                            "\n"
                            "La CEDH, signée en 1950, garantit un catalogue de droits fondamentaux. La Cour européenne des droits de l'homme siégeant à Strasbourg contrôle le respect de ces droits par les États parties. Un individu peut saisir la Cour après l'épuisement des voies de recours internes.\n"
                            "\n"
                            "Les principes généraux du droit de l'UE comprennent la proportionnalité, le légitime attente, la sécurité juridique et le droit de la défense."
                        ),
                        "theory_ar": (
                            "القانون الأوروبي يتكون من قانون الاتحاد الأوروبي واتفاقية حقوق الإنسان الأوروبية. هذان النظامان يتراكبان على القانون الداخلي.\n"
                            "\n"
                            "قانون الاتحاد الأوروبي ينقسم إلى تنظيمات (مطبقة مباشرة) وتأشيرات (تتطلب توطيناً) وقرارات (فردية). مبدأ تفوق قانون الاتحاد على القانون الداخلي أقره محكمة العدل. مبدأ الأثر المباشر يُتيح للأفراد النزاع أمام محكمتهم الوطنية بأحكام قانون الاتحاد.\n"
                            "\n"
                            "اتفاقية حقوق الإنسان وقعت عام 1950 وتكفل قائمة بالحقوق الأساسية. المحكمة الأوروبية تقع في ستراسبورغ وتراقب احترام هذه الحقوق. يمكن للأفراد رفع الدعوى أمامها بعد استنفاد وسائل الطعن الداخلية.\n"
                            "\n"
                            "المبادئ العامة لقانون الاتحاد تشمل التناسب والتوقع مشروع والأمان القانوني وحقوق الدفاع."
                        ),
                        "vocab": [
                            {"fr": "le droit de l'UE", "ar": "قانون الاتحاد الأوروبي", "example": "Le droit de l'UE prime sur le droit interne."},
                            {"fr": "le règlement", "ar": "التنظيم", "example": "Le règlement est directement applicable dans tous les États membres."},
                            {"fr": "la directive", "ar": "التأشير", "example": "La directive doit être transposée dans le droit interne."},
                            {"fr": "la primauté", "ar": "التفوق", "example": "Le principe de primauté assure la suprématie du droit de l'UE."},
                            {"fr": "l'effet direct", "ar": "الأثر المباشر", "example": "L'effet direct permet l'invoque devant les juridictions nationales."},
                            {"fr": "la CEDH", "ar": "اتفاقية حقوق الإنسان الأوروبية", "example": "La CEDH garantit les droits fondamentaux en Europe."},
                            {"fr": "la Cour EDH", "ar": "المحكمة الأوروبية", "example": "La Cour EDH siège à Strasbourg."},
                            {"fr": "la proportionnality", "ar": "التناسب", "example": "Le principe de proportionnalité contrôle l'adéquation des mesures."},
                            {"fr": "le légitime attente", "ar": "التوقع المشروع", "example": "Le légitime attente protège les attentes raisonnables."},
                            {"fr": "la sécurité juridique", "ar": "الأمان القانوني", "example": "La sécurité juridique assure la prévisibilité des situations."}
                        ],
                    },

                    {
                        "id": "fr_l3_u3_l2",
                        "title": "Les droits fondamentaux",
                        "title_ar": "الحقوق الأساسية",
                        "subtitle": "Catégories et protection des droits fondamentaux",
                        "theory": (
                            "Les droits fondamentaux sont les droits imprescriptibles et inaliénables reconnus à toute personne. Ils se divisent en trois catégories.\n"
                            "\n"
                            "Les droits civils et politiques garantissent la liberté individuelle : droit à la vie, interdiction de la torture, liberté d'aller et venir, liberté d'expression, droit au procès équitable, présomption d'innocence.\n"
                            "\n"
                            "Les droits économiques, sociaux et culturels incluent le droit au travail, le droit à l'éducation, le droit à la protection de la santé, le droit à un niveau de vie décent.\n"
                            "\n"
                            "Les droits de troisième génération, plus récents, comprennent le droit à l'environnement, le droit au développement et le droit à la paix.\n"
                            "\n"
                            "La hiérarchie des droits varie selon les systèmes juridiques. Certains droits sont d'application immédiate, d'autres requièrent des mesures d'application. La marge d'appréciation des États permet un équilibre entre l'universalité des droits et les spécificités nationales."
                        ),
                        "theory_ar": (
                            "الحقوق الأساسية هي حقوق غير قابلة للتقادم والانتزاع المعترف لكل شخص. تنقسم إلى ثلاث فئات.\n"
                            "\n"
                            "الحقوق المدنية والسياسية تكفل الحرية الفردية: الحق في الحياة وحظر التعذيب وحرية التنقل وحرية التعبير وحقوق المحاكمة العادلة والبراءة الأصلية.\n"
                            "\n"
                            "الحقوق الاقتصادية والاجتماعية والثقافية تشمل الحق في العمل والتعليم والحماية الصحية ومستوى معيشي لائق.\n"
                            "\n"
                            "حقوق الجيل الثالث الأحدث تشمل الحق في البيئة والحق في التنمية والحق في السلام.\n"
                            "\n"
                            "تراتبية الحقوق تختلف حسب الأنظمة القانونية. بعضها قابل للتطبيق المباشر والبعض الآخر يتطلب إجراءات تطبيقية. هامش تقدير الدول يُتيح التوازن بين عالمية الحقوق والخصوصيات الوطنية."
                        ),
                        "vocab": [
                            {"fr": "les droits civils", "ar": "الحقوق المدنية", "example": "Les droits civils protègent la liberté individuelle."},
                            {"fr": "les droits politiques", "ar": "الحقوق السياسية", "example": "Les droits politiques garantissent la participation à la vie publique."},
                            {"fr": "les droits sociaux", "ar": "الحقوق الاجتماعية", "example": "Les droits sociaux incluent le droit au travail et à la santé."},
                            {"fr": "les droits de l'homme", "ar": "حقوق الإنسان", "example": "Les droits de l'homme sont universels et inaliénables."},
                            {"fr": "la liberté d'expression", "ar": "حرية التExpression", "example": "La liberté d'expression est un droit fondamental."},
                            {"fr": "le droit à un procès éque", "ar": "حقوق المحاكمة العادلة", "example": "Le droit à un procès équitable est garanti par la CEDH."},
                            {"fr": "l'interdiction de la torture", "ar": "حظر التعذيب", "example": "L'interdiction de la torture est absolue et non dérogeable."},
                            {"fr": "la dignité humaine", "ar": "الكرامةHumanité", "example": "La dignité humaine est le fondement de tous les droits."},
                            {"fr": "la marge d'appréciation", "ar": "هامش التقدير", "example": "La marge d'appréciation permet l'adaptation nationale."},
                            {"fr": "les droits inviolables", "ar": "الحقوق الطبيعية", "example": "Les droits inviolables ne peuvent être supprimés."}
                        ],
                    },

                    {
                        "id": "fr_l3_u3_l3",
                        "title": "La médecine légale",
                        "title_ar": "الطب الشرعي",
                        "subtitle": "Expertise médicale, certificats et preuves médicales",
                        "theory": (
                            "La médecine légale est la branche de la médecine qui applique les connaissances médicales au droit. Elle intervient dans les domaines civil et pénal.\n"
                            "\n"
                            "En matière pénale, l'expertise médicale permet de déterminer le lien entre une infraction et les blessures subies par la victime. Le certificat médical constitue une pièce essentielle de la procédure. Il doit décrire les lésions, leur ancienneté et leur rapport avec les faits dénoncés.\n"
                            "\n"
                            "L'expert médico-légal est désigné par le juge d'instruction. Il établit un rapport qui peut être contesté par les parties. Le contre-expertise est de droit.\n"
                            "\n"
                            "En matière civile, la médecine légale intervient pour évaluer le taux d'incapacité permanente, établir un lien de causalité entre un acte médical et un préjudice, ou évaluer les conséquences d'un accident de travail.\n"
                            "\n"
                            "La déontologie médicale impose des règles strictes à l'expert. Le secret médical doit être respecté, sauf dérogation légale. L'indépendance de l'expert est garantie par la loi."
                        ),
                        "theory_ar": (
                            "الطب الشرعي هو فرع من الطب يُطبّق المعرفة الطبية على القانون. يتدخل في المجالين المدني والجنائي.\n"
                            "\n"
                            "في Matters الجنائية، تُتيح الخبرة الطبية تحديد الصلة بين الجريمة والجروح التي لحقت بالضحية. تُشكّل الشهادة الطبية لائحة أساسية في الإجراءات.\n"
                            "\n"
                            "الخبير الطبي الشرعي يُعيّنه قاضي التحقيق. يُحرّر تقريراً يمكن الطعن فيه من الأطراف. المقابلة حق.\n"
                            "\n"
                            "في Matters المدنية، يتدخل الطب الشرعي لتقييم نسب الإعاقة الدائمة وتحديد رابطة سببية بين فعل طبي وضرر وتقييم نتائج حادث عمل.\n"
                            "\n"
                            "الضوابط الطبية تضع قواعد صارمة للخبير. السرية الطبية يجب احترامها إلا في حالة استثناء قانوني. استقلالية الخPERT مضمونة بالقانون."
                        ),
                        "vocab": [
                            {"fr": "la médecine légale", "ar": "الطب الشرعي", "example": "La médecine légale applique la médecine au droit."},
                            {"fr": "l'expertise médicale", "ar": "الخبرة الطبية", "example": "L'expertise médicale établit le lien entre infraction et blessures."},
                            {"fr": "le certificat médical", "ar": "الشهادة الطبية", "example": "Le certificat médical décrit les lésions subies."},
                            {"fr": "l'expert", "ar": "الخبير", "example": "L'expert établit un rapport sous serment."},
                            {"fr": "le rapport d'expertise", "ar": "تقرير الخبرة", "example": "Le rapport d'expertise est soumis au juge."},
                            {"fr": "le taux d'incapacité", "ar": "نسبة الإعاقة", "example": "Le taux d'incapacité évalue la perte de capacités."},
                            {"fr": "le lien de causalité", "ar": "الرابط السببي", "example": "Le lien de causalité unit le fait et le dommage."},
                            {"fr": "le secret médical", "ar": "السرية الطبية", "example": "Le secret médical est une obligation déontologique."},
                            {"fr": "la déontologie", "ar": "الضوابط المهنية", "example": "La déontologie impose des règles à l'expert."},
                            {"fr": "la contre-expertise", "ar": "المقابلة", "example": "La contre-expertise est un droit des parties."}
                        ],
                    },

                ],
            },

        ],
    },

    {
        "id": 4,
        "title": "Avancé — المحترف",
        "description": "التقاضي والكتابة الاستشارية والمحاكاة",
        "color": "#dc2626",
        "units": [
            {
                "id": "fr_l4_u1",
                "title": "La pratique professionnelle",
                "title_ar": "الممارسة المهنية",
                "lessons": [
                    {
                        "id": "fr_l4_u1_l1",
                        "title": "La plaidoirie",
                        "title_ar": "المرافعة",
                        "subtitle": "Art de la plaidoirie et techniques d'argumentation",
                        "theory": (
                            "La plaidoirie est l'art de convaincre le juge par la parole. Elle comprend une accroche pour capter l'attention, un exposé des faits chronologique, une argumentation juridique structurée et une péroraison percutante.\n"
                            "\n"
                            "Le syllogisme juridique est la structure de base : la majeure (la règle de droit applicable), la mineure (les faits établis) et la conclusion (l'application au cas d'espèce). La hiérarchie des normes guide l'argumentation : Constitution supérieure aux traités, qui l'emportent sur les lois.\n"
                            "\n"
                            "Les principes généraux du droit fournissent des arguments subsidiaires : principe d'égalité, principe de liberté, principe de sécurité juridique.\n"
                            "\n"
                            "Le style oral de la plaidoirie se distingue de l'écrit par des phrases courtes, la répétition thématique, le ton affirmatif et l'absence de jargon excessif. L'avocat doit maîtriser les questions du juge et concéder les points perdus."
                        ),
                        "theory_ar": (
                            "المرافعة هي فن إقناع القاضي بالكلام. تتضمن افتتاحاً لجذب الانتباه وعرضًا وقاعيًا تسلسلياً وحججاً قانونية منظمة وخاتمة مؤثرة.\n"
                            "\n"
                            "القياس القانوني هو البنية الأساسية: الكبرى (القاعدة القانونية المطبقة) والصغرى (الوقائع المثبتة) والنتيجة (التطبيق على الحالة). ترتيب القواعد يوجه الحجج.\n"
                            "\n"
                            "المبادئ العامة للقانون توفر حججاً احتياطية: مبدأ المساواة ومبدأ الحرية ومبدأ الأمان القانوني.\n"
                            "\n"
                            "يتميز الأسلوب الشفهي بالجمل القصيرة والتكرار الموضوعي والنبرة الحازمة وغياب الجامعات المفرطة. يجب على المحامي إجابة أسئلة القاضي والتنازل عن النقاط الضائعة."
                        ),
                        "vocab": [
                            {"fr": "la plaidoirie", "ar": "المرافعة", "example": "La plaidoirie a duré deux heures."},
                            {"fr": "le syllogisme", "ar": "القياس", "example": "Le syllogisme juridique est la base de l'argumentation."},
                            {"fr": "la majeure", "ar": "الكبرى", "example": "La majeure est la règle de droit applicable."},
                            {"fr": "la mineure", "ar": "الصغرى", "example": "La mineure est l'ensemble des faits établis."},
                            {"fr": "la péroraison", "ar": "الخاتمة", "example": "La péroraison doit être percutante."},
                            {"fr": "l'accroche", "ar": "الافتتاح", "example": "L'accroche capte l'attention du juge."},
                            {"fr": "la hiérarchie des normes", "ar": "ترتيب القوانين", "example": "La hiérarchie des normes est respectée."},
                            {"fr": "le principe d'égalité", "ar": "مبدأ المساواة", "example": "Le principe d'égalité s'impose au législateur."},
                            {"fr": "la sécurité juridique", "ar": "الأمان القانوني", "example": "La sécurité juridique est un principe général."},
                            {"fr": "la demande claire", "ar": "الطلب الواضح", "example": "La demande claire et précise est requise."}
                        ],
                    },

                    {
                        "id": "fr_l4_u1_l2",
                        "title": "La négociation juridique",
                        "title_ar": "المفاوضة القانونية",
                        "subtitle": "Techniques de négociation et conventions extrajudiciaires",
                        "theory": (
                            "La négociation juridique est un mode de règlement amiable des différends qui permet aux parties de trouver une solution mutuellement acceptable sans recourir au juge.\n"
                            "\n"
                            "Les techniques de négociation comprennent la négociation distributive (marchandage sur le prix), la négociation intégrative (création de valeur) et la négociation de principe (fondée sur des critères objectifs).\n"
                            "\n"
                            "L'accord transactionnel est le résultat de la négociation. Il a l'autorité de la chose jugée entre les parties. La transaction est un contrat par lequel les parties font des concessions réciproques pour mettre fin à un litige existant ou à naître.\n"
                            "\n"
                            "Le médiateur est un tiers neutre qui facilite la négociation sans imposer de solution. La conciliation est un processus similaire dans lequel le conciliateur peut proposer une solution. L'avocat joue un rôle clé en conseillant son client et en protégeant ses intérêts lors de la négociation."
                        ),
                        "theory_ar": (
                            "المفاوضة القانونية هي وسيلة لتسوية ودية للنزاعات تُتيح للأطراف إيجاد حل مقبول دون اللجوء للقاضي.\n"
                            "\n"
                            "تتضمن تقنيات المفاوضة المفاوضة التوزيعية (المساومة على السعر) والمفاوضة التكاملية (خلق القيمة) والمفاوضة المبدأية (المبنية على معايير موضوعية).\n"
                            "\n"
                            "الاتفاق التوفيقي هو نتجة المفاوضة. له قوة الشيء المحكوم به بين الأطراف. التوفيق عقد يُقدم فيه الأطراف تنازلات متبادلة لإنهاء نزاع.\n"
                            "\n"
                            "الوساط第三者 neutral يسهل المفاوضة دون فرض حل. التسوية عملية مشابهة يقترح فيها المسوّط حلاً. يلعب المحامي دوراً مهماً في إرشاد عميله وحماية مصالحه أثناء المفاوضة."
                        ),
                        "vocab": [
                            {"fr": "la négociation", "ar": "المفاوضة", "example": "La négociation est un mode amiable de règlement des différends."},
                            {"fr": "la transaction", "ar": "التسوية", "example": "La transaction a l'autorité de la chose jugée."},
                            {"fr": "la médiation", "ar": "الوساطة", "example": "La médiation fait intervenir un tiers neutre."},
                            {"fr": "la conciliation", "ar": "التسوية الودية", "example": "La conciliation permet au conciliateur de proposer un accord."},
                            {"fr": "l'accord", "ar": "الاتفاق", "example": "L'accord met fin au litige entre les parties."},
                            {"fr": "le compromis", "ar": "التنازل", "example": "Le compromis suppose des concessions réciproques."},
                            {"fr": "le médiateur", "ar": "الوسيط", "example": "Le médiateur facilite le dialogue entre les parties."},
                            {"fr": "le conciliateur", "ar": "المسوّط", "example": "Le conciliateur peut proposer une solution."},
                            {"fr": "l'intérêt commun", "ar": "المصلحة المشتركة", "example": "La recherche de l'intérêt commun facilite la négociation."},
                            {"fr": "le désaccord", "ar": "الخلاف", "example": "Le désaccord conduit au recours au juge."}
                        ],
                    },

                    {
                        "id": "fr_l4_u1_l3",
                        "title": "Le droit des affaires",
                        "title_ar": "قانون الأعمال",
                        "subtitle": "Droit commercial, droit des sociétés et opérations de financement",
                        "theory": (
                            "Le droit des affaires englobe l'ensemble des règles juridiques applicables aux activités économiques et commerciales.\n"
                            "\n"
                            "Le droit des sociétés régit la création, le fonctionnement et la dissolution des sociétés commerciales. Les principales formes sont la SARL, la SA, la SAS et la société en nom collectif. Chaque forme présente des avantages en matière de responsabilité, de fiscalité et de gouvernance.\n"
                            "\n"
                            "Le droit des contrats commerciaux encadre les relations d'affaires : contrats de distribution, franchise, concession commerciale, transport de marchandises.\n"
                            "\n"
                            "Le droit des procédures collectives traite les difficultés financières des entreprises. Le plan de redressement permet la poursuite de l'activité. La liquidation entraîne la vente des actifs et la clôture pour insuffisance d'actif.\n"
                            "\n"
                            "Le droit de la concurrence prohibe les pratiques anticoncurrentielles (ententes, abus de position dominante) et contrôle les opérations de concentration."
                        ),
                        "theory_ar": (
                            "قانون الأعمال يشمل القواعد القانونية المطبقة على الأنشطة الاقتصادية والتجارية.\n"
                            "\n"
                            "قانون الشركات يُنظم إنشاء وتشغيل وتصفية الشركات التجارية. الأشكال الرئيسية هي SARL وSA وSAS والشركة بالاسم الجماعي.\n"
                            "\n"
                            "قانون العقود التجارية يُنظم العلاقات التجارية: عقود التوزيع والامتياز والمناولة ونقل البضائع.\n"
                            "\n"
                            "قانون الإجراءات الجماعية يعالج الصعوبات المالية للمؤسسات. خطة الإنقاذ تُتيح متابعة النشاط. التصفية تؤدي إلى بيع الأصول.\n"
                            "\n"
                            "قانون المنافسة يحظر الممارسات المنافسة (الاتفاقيات وإساءة الاستخدام للموقع المهيمن) ويُراقب عمليات التركيز."
                        ),
                        "vocab": [
                            {"fr": "la SARL", "ar": "شركة ذات مسؤولية محدودة", "example": "La SARL limite la responsabilité aux apports."},
                            {"fr": "la SA", "ar": "الشركة المساهمة", "example": "La SA permet la cotation en bourse."},
                            {"fr": "la SAS", "ar": "شركة بالأسهم المبسطة", "example": "La SAS offre une grande liberté statutaire."},
                            {"fr": "la franchise", "ar": "الامتياز التجاري", "example": "La franchise est un contrat de diffusion de savoir-faire."},
                            {"fr": "la concession", "ar": "المناولة", "example": "La concession est un contrat de distribution exclusive."},
                            {"fr": "le plan de redressement", "ar": "خطة الإنقاذ", "example": "Le plan de redressement prévoit la reprise d'activité."},
                            {"fr": "l'entente", "ar": "الاتفاقية المنافسة", "example": "L'entente entre concurrents est prohibée."},
                            {"fr": "l'abus de position dominante", "ar": "إساءة الاستخدام للموقع المهيمن", "example": "L'abus de position dominante est sanctionné par l'Autorité de la concurrence."},
                            {"fr": "la concentration", "ar": "التركيز", "example": "Les concentrations sont soumises à contrôle préalable."},
                            {"fr": "le greffe du tribunal de commerce", "ar": "مكتب محكمة التجارة", "example": "Le greffe du tribunal de commerce tient le registre du commerce."}
                        ],
                    },

                    {
                        "id": "fr_l4_u1_l4",
                        "title": "La fiscalité",
                        "title_ar": "الضرائب",
                        "subtitle": "Principes du droit fiscal et obligation déclarative",
                        "theory": (
                            "Le droit fiscal régit l'ensemble des prélèvements effectués par l'État et les collectivités territoriales. Les principes directeurs sont la légalité, l'égale répartition de la charge fiscale et l'équité.\n"
                            "\n"
                            "L'impôt sur le revenu (IR) frappe les revenus des personnes physiques. L'impôt sur les sociétés (IS) frappe les bénéfices des personnes morales. La taxe sur la valeur ajoutée (TVA) est un impôt indirect sur la consommation.\n"
                            "\n"
                            "L'obligation déclarative impose aux contribuables de déclarer leurs revenus et leur patrimoine. Le non-respect de cette obligation entraîne des pénalités (majorations, amendes, poursuites pénales).\n"
                            "\n"
                            "Le contentieux fiscal se déroule devant le tribunal administratif, puis la cour administrative d'appel et le Conseil d'État. La procédure de rectification contradictoire offre au contribuable la possibilité de répondre aux observations de l'administration avant toute mise en recouvrement."
                        ),
                        "theory_ar": (
                            "القانون الضريبي يُنظم جميع الاقتطاعات التي تقوم بها الدولة والسلطات المحلية. المبادئ التوجيهية هي المشروعية والعدالة في توزيع العبء الضريبي.\n"
                            "\n"
                            "ضريبة الدخل تضرب دخل الأشخاص الطبيعية. ضريبة الشركات تضرب أرباح الأشخاص المعنوية. ضريبة القيمة المضافة ضريبة غير مباشرة على الاستهلاك.\n"
                            "\n"
                            "الالتزام الإعلاني يفرض على دافعي الضرائب الإعلاء عن دخلهم وأرصدتهم. عدم الالتزام يُنتج عقوبات (زيادات وغرامات وملاحقة جنائية).\n"
                            "\n"
                            "التخاصم الضريبي يجري أمام المحكمة الإدارية ثم محكمة الاستئناف الإدارية ومجلس الدولة. إجراء التصحيح المواجه يُتيح لدافع الضرائب الرد على ملاحظات الإدارة قبل أي تحصيل."
                        ),
                        "vocab": [
                            {"fr": "l'impôt sur le revenu", "ar": "ضريبة الدخل", "example": "L'IR frappe les revenus des personnes physiques."},
                            {"fr": "l'impôt sur les sociétés", "ar": "ضريبة الشركات", "example": "L'IS frappe les bénéfices des personnes morales."},
                            {"fr": "la TVA", "ar": "ضريبة القيمة المضافة", "example": "La TVA est un impôt indirect sur la consommation."},
                            {"fr": "l'obligation déclarative", "ar": "الالتزام الإ declaratif", "example": "L'obligation déclarative impose la déclaration des revenus."},
                            {"fr": "le contribuable", "ar": "دافع الضرائب", "example": "Le contribuable est tenu de déclarer ses revenus."},
                            {"fr": "la mise en recouvrement", "ar": "التحصيل", "example": "La mise en recouvrement intervient après la mise en demeure."},
                            {"fr": "le contentieux fiscal", "ar": "التخاصم الضريبي", "example": "Le contentieux fiscal se déroule devant le juge administratif."},
                            {"fr": "la pénalité", "ar": "العقوبة", "example": "La pénalité est due en cas de retard ou d'inexactitude."},
                            {"fr": "le taux marginal d'imposition", "ar": "النسبة الضريبية الهامشية", "example": "Le taux marginal s'applique à la tranche supérieure de revenus."},
                            {"fr": "l'exonération", "ar": "الإعفاء", "example": "L'exonération dispense le contribuable du paiement de l'impôt."}
                        ],
                    },

                ],
            },

            {
                "id": "fr_l4_u2",
                "title": "Les domaines spécialisés",
                "title_ar": "المجالات المتخصصة",
                "lessons": [
                    {
                        "id": "fr_l4_u2_l1",
                        "title": "Le droit immobilier",
                        "title_ar": "قانون العقارات",
                        "subtitle": "Transactions immobilières, hypothèques et copropriété",
                        "theory": (
                            "Le droit immobilier régit les transactions portant sur les biens immeubles. Il comprend le droit de la propriété immobilière, le droit de l'urbanisme et le droit de la copropriété.\n"
                            "\n"
                            "La vente immobilière obéit à un formalisme strict. Le contrat de vente est généralement conclu devant notaire. La promesse de vente engage le vendeur à vendre et l'acheteur à acheter sous conditions suspensives (obtention du prêt, absence d' servitudes). La clause de substitution permet à l'acquéreur de céder ses droits à un tiers.\n"
                            "\n"
                            "Le statut de la copropriété, issu de la loi du 10 juillet 1965, organise la vie collective des immeubles en lots. L'assemblée générale vote les décisions relatives à l'administration et aux travaux. Le syndic est le mandataire de la copropriété.\n"
                            "\n"
                            "Le droit de l'urbanisme réglemente l'utilisation des sols. Le permis de construire est requis pour les constructions nouvelles. Les plans locaux d'urbanisme (PLU) déterminent les règles applicables dans chaque commune."
                        ),
                        "theory_ar": (
                            "قانون العقارات يُنظم المعاملات المتعلقة بالعقارات. يشمل حق الملكية العقارية وقانون التخطيط الحضري وقانون المُلكية المشتركة.\n"
                            "\n"
                            "بيع العقارات يخضع لشكلية صارمة. عقد البيع يُبرم غالباً أمام الموثق. عقد البيع المبدئي يُلزم البائع بالبيع والمشتري بالشراء مشروطاً بتحقيق شروط (الحصول على القرض وغياب الارتفاقات). بند الاستبدال يُتيح للمشتري التنازل عن حقوقه لطرف ثالث.\n"
                            "\n"
                            "قانون المُلكية المشتركة الذي صدر بقانون 10 يوليو 1965 يُنظم الحياة الجماعية للعقارات المنقسمة إلى حصص. الجمعية العامة تُصوت على القرارات الإدارية والإصلاحية. المُدير هو مندوب المُلكية المشتركة.\n"
                            "\n"
                            "قانون التخطيط الحضري يُنظم استعمال الأراضي. التصريح بالبناء مطلوب للمباني الجديدة. خطط التخطيط المحلية تُحدد القواعد المطبقة في كل بلدية."
                        ),
                        "vocab": [
                            {"fr": "la vente immobilière", "ar": "بيع العقارات", "example": "La vente immobilière obéit à un formalisme strict."},
                            {"fr": "la promesse de vente", "ar": "عقد البيع المبدئي", "example": "La promesse de vente engage les parties sous conditions."},
                            {"fr": "la condition suspensive", "ar": "الشرط التعليقي", "example": "La condition suspensive doit être réalisée pour la vente."},
                            {"fr": "le notaire", "ar": "الموثق", "example": "Le notaire authentifie le contrat de vente."},
                            {"fr": "la copropriété", "ar": "المُلكية المشتركة", "example": "Le statut de la copropriété organise la vie collective."},
                            {"fr": "l'assemblée générale", "ar": "الجمعية العامة", "example": "L'assemblée générale vote les décisions importantes."},
                            {"fr": "le syndic", "ar": "المُدير", "example": "Le syndic administre la copropriété."},
                            {"fr": "le permis de construire", "ar": "تصريح البناء", "example": "Le permis de construire est requis pour les nouvelles constructions."},
                            {"fr": "le PLU", "ar": "خطط التخطيط المحلية", "example": "Le PLU détermine les règles d'urbanisme applicables."},
                            {"fr": "les servitudes", "ar": "حقوق الارتفاق", "example": "Les servitudes pèsent sur la valeur du bien immobilier."}
                        ],
                    },

                    {
                        "id": "fr_l4_u2_l2",
                        "title": "Le droit de la santé",
                        "title_ar": "قانون الصحة",
                        "subtitle": "Droit médical, responsabilité sanitaire et protection des patients",
                        "theory": (
                            "Le droit de la santé encadre les relations entre les professionnels de santé, les patients et les organismes de sécurité sociale.\n"
                            "\n"
                            "Le consentement éclairé du patient est un principe fondamental. Tout acte médical doit faire l'objet d'une information préalable permettant au patient de donner son consentement libre et éclairé. Le droit au refus de traitement est reconnu à toute personne capable.\n"
                            "\n"
                            "Le secret médical protège les informations relatives à la santé du patient. Sa divulgation est punie pénalement, sauf dérogations légales (obligation de signalement, danger pour des tiers).\n"
                            "\n"
                            "La responsabilité médicale peut être engagée sur le fondement de la faute prouvée ou du fait des produits défectueux. La loi du 4 mars 2002 a instauré une réparation automatique des aléas thérapeutiques par l'Office national d'indemnisation des accidents médicaux.\n"
                            "\n"
                            "Le droit à la santé est garanti par le Préambule de la Constitution de 1946. Il impose à l'État de fournir un accès aux soins pour tous."
                        ),
                        "theory_ar": (
                            "قانون الصحة يُنظم العلاقات بين مقدمي الرعاية الصحية والمريض والتأمين الصحي.\n"
                            "\n"
                            "الرضا المُسبَق والمُ informed للمريض مبدأ أساسي. كل فعل طبي يجب أن يتضمن معلومات مسبقة تُتيح للمريض إعطاء رضا حر ومُ informed. الحق في رفض العلاج معترف به لكل شخص أهل.\n"
                            "\n"
                            "السرية الطبية تحمي المعلومات المتعلقة بصحة المريض. إفشاءها يُعاقب عليها جزائياً إلا في حالات استثنائية.\n"
                            "\n"
                            "المسؤولية الطبية يمكن أن تُحمّل على أساس الخطأ المُثبت أو التفريغ. قانون 4 مارس 2002 أنشأ تعويضاً تلقائياً عن المخاطر العلاجية.\n"
                            "\n"
                            "الحق في الصحة مكفول بديباجة الدستور 1946. يُلزم الدولة بتوفير الوصول إلى الرعاية للجميع."
                        ),
                        "vocab": [
                            {"fr": "le consentement éclairé", "ar": "الرضا المُسبَق والمُ informed", "example": "Le consentement éclairé est un droit du patient."},
                            {"fr": "le secret médical", "ar": "السرية الطبية", "example": "Le secret médical protège les informations de santé."},
                            {"fr": "la responsabilité médicale", "ar": "المسؤولية الطبية", "example": "La responsabilité médicale est engagée en cas de faute."},
                            {"fr": "le droit au refus", "ar": "حق الرفض", "example": "Le droit au refus de traitement est reconnu à toute personne."},
                            {"fr": "l'information préalable", "ar": "المعلومات المسبقة", "example": "L'information préalable est une obligation du médecin."},
                            {"fr": "l'accident médical", "ar": "الحادث الطبي", "example": "L'indemnisation des accidents médicaux est automatique."},
                            {"fr": "l'OMNITHES", "ar": "المكتب الوطني للمصادم الطبية", "example": "L'ONIAM indemnise les aléas thérapeutiques."},
                            {"fr": "le secret professionnel", "ar": "السرية المهنية", "example": "Le secret professionnel s'impose à tout membre de l'équipe soignante."},
                            {"fr": "l'accès aux soins", "ar": "الوصول إلى الرعاية", "example": "L'accès aux soins est un droit à caractère général."},
                            {"fr": "la déclaration de naissance", "ar": "شهادة الميلاد", "example": "La déclaration de naissance est un acte d'état civil."}
                        ],
                    },

                    {
                        "id": "fr_l4_u2_l3",
                        "title": "Le droit numérique",
                        "title_ar": "القانون الرقمي",
                        "subtitle": "Protection des données, commerce électronique et droit d'auteur numérique",
                        "theory": (
                            "Le droit numérique encadre les activités liées aux technologies de l'information et de la communication. Il comprend la protection des données personnelles, le commerce électronique et la propriété intellectuelle numérique.\n"
                            "\n"
                            "Le Règlement Général sur la Protection des Données (RGPD) est le texte de référence européen. Il impose aux responsables de traitement le respect de principes tels que la minimisation des données, la limitation de la finalité et la sécurité. Les droits des personnes comprennent l'accès, la rectification, l'effacement et la portabilité des données.\n"
                            "\n"
                            "Le commerce électronique est régi par la directive 2000/31/CE et le droit français. Les obligations d'information du professionnel en ligne, le consentement préalable pour les cookies et la protection des consommateurs sont des exigences essentielles.\n"
                            "\n"
                            "Le droit d'auteur numérique protège les œuvres diffusées en ligne. La copie privée est limitée, la protection techniques (DRM) est encouragée, et la responsabilité des hébergeurs est encadrée par la loi sur la confiance dans l'économie numérique (LCEN)."
                        ),
                        "theory_ar": (
                            "القانون الرقمي يُنظم الأنشطة المتعلقة بتقنيات المعلومات والتواصل. يشمل حماية البيانات الشخصية والتجارة الإلكترونية والملكية الفكرية الرقمية.\n"
                            "\n"
                            "اللائحة العامة لحماية البيانات (RGPD) هي النص المرجعي الأوروبي. تفرض على مسؤولي المعالجة احترام مبادئ كالحد الأدنى من البيانات وتحديد الغرض والأمان. حقوق الأشخاص تشمل الوصول والتصحيح والحذف وقابلية النقل.\n"
                            "\n"
                            "التجارة الإلكترونية يُنظمها التأشيرة 2000/31/CE والقانون الفرنسي. التزامات المعلومات والموافقة المسبقة لملفات تعريف الارتباط وحماية المستهلكين.\n"
                            "\n"
                            "حقوق المؤلف الرقمية تحمي المنشورات عبر الإنترنت. النسخ الخاص محدودة، الحماية التقنية مشجعة، مسؤولية المضيفين منظمة بالقانون على الثقة في الاقتصاد الرقمي."
                        ),
                        "vocab": [
                            {"fr": "le RGPD", "ar": "اللائحة العامة لحماية البيانات", "example": "Le RGPD impose le respect de principes de protection des données."},
                            {"fr": "la donnée personnelle", "ar": "البيانات الشخصية", "example": "La donnée personnelle est soumise à protection."},
                            {"fr": "le consentement", "ar": "الموافقة", "example": "Le consentement préalable est requis pour le traitement des données."},
                            {"fr": "le droit d'accès", "ar": "حق الوصول", "example": "Le droit d'accès permet de consulter ses données."},
                            {"fr": "le droit à l'effacement", "ar": "حق الحذف", "example": "Le droit à l'effacement est le droit à l'oubli numérique."},
                            {"fr": "le commerce électronique", "ar": "التجارة الإلكترونية", "example": "Le commerce électronique obéit à des obligations d'information."},
                            {"fr": "le cookie", "ar": "ملف تعريف الارتباط", "example": "L'utilisation de cookies nécessite un consentement préalable."},
                            {"fr": "le droit d'auteur numérique", "ar": "حقوق المؤلف الرقمية", "example": "Le droit d'auteur protège les œuvres diffusées en ligne."},
                            {"fr": "l'hébergeur", "ar": "المضيف", "example": "L'hébergeur a une obligation de réactivité en cas de signalement."},
                            {"fr": "la LCEN", "ar": "قانون الثقة في الاقتصاد الرقمي", "example": "La LCEN encadre les activités numériques."}
                        ],
                    },

                ],
            },

            {
                "id": "fr_l4_u3",
                "title": "Le droit contemporain",
                "title_ar": "القانون المعاصر",
                "lessons": [
                    {
                        "id": "fr_l4_u3_l1",
                        "title": "Le droit de l'environnement",
                        "title_ar": "قانون البيئة",
                        "subtitle": "Protection de l'environnement et responsabilité écologique",
                        "theory": (
                            "Le droit de l'environnement est un ensemble de règles visant à protéger la nature, prévenir les pollutions et réparer les dommages écologiques.\n"
                            "\n"
                            "La Charte constitutionnelle de l'environnement de 2004 a élevé les principes écologiques au rang de principes à valeur constitutionnelle. Le principe de prévention impose de prendre des mesures pour éviter les dommages environnementaux. Le principe pollueur-payeur fait peser le coût de la dépollution sur l'auteur de la pollution.\n"
                            "\n"
                            "Les autorisations environnementales (ICPE) sont soumises à une étude d'impact et une enquête publique. L'évaluation environnementale est obligatoire pour les projets susceptibles d'avoir un impact significatif.\n"
                            "\n"
                            "La responsabilité environnementale est engagée sans faute pour les dommages à la biodiversité et aux ressources naturelles. Le droit à un environnement sain est reconnu comme un droit fondamental. Les associations environnementales disposent d'un droit d'agir en justice pour défendre l'environnement."
                        ),
                        "theory_ar": (
                            "قانون البيئة هو مجموعة القواعد التي تهدف إلى حماية الطبيعة ومنع التلوث وإصلاح الأضرار البيئية.\n"
                            "\n"
                            "ميثاق البيئة الدستوري لعام 2004 رفع المبادئ البيئية إلى مبادئ ذات قيمة دستورية. مبدأ الوقاية يفرض اتخاذ إجراءات لتجنب الأضرار البيئية. مبدأ الملوث يدفع يتحمل تكلفة إزالة التلوث.\n"
                            "\n"
                            "التصاريح البيئية تخضع لدراسة للتأثير واستطلاع عام. التقييم البيئي إلزامي للمشاريع التي قد تُسبب تأثيراً ملحوظاً.\n"
                            "\n"
                            "المسؤولية البيئية تُحمّل دون خطأ عن الأضرار بالتنوع البيولوجي والموارد الطبيعية. الحق في بيئة سليمة معترف به كحق أساسي. جمعيات البيئة تتمتع بصلاحية الرفع أمام المحاكم."
                        ),
                        "vocab": [
                            {"fr": "la pollution", "ar": "التلوث", "example": "La pollution est sanctionnée par le droit de l'environnement."},
                            {"fr": "le principe pollueur-payeur", "ar": "مبدأ الملوث يدفع", "example": "Le principe pollueur-payeur fait peser le coût sur l'auteur."},
                            {"fr": "le principe de prévention", "ar": "مبدأ الوقاية", "example": "Le principe de prévention impose des mesures anticipées."},
                            {"fr": "l'étude d'impact", "ar": "دراسة التأثير", "example": "L'étude d'impact évalue les conséquences du projet."},
                            {"fr": "l'enquête publique", "ar": "الاستطلاع العام", "example": "L'enquête publique permet au public de formuler ses observations."},
                            {"fr": "l'ICPE", "ar": "المؤسسة المُثيرة للقلق البيئي", "example": "L'ICPE est soumise à autorisation environnementale."},
                            {"fr": "la biodiversité", "ar": "التنوع البيولوجي", "example": "La biodiversité est protégée par le droit de l'environnement."},
                            {"fr": "l'évaluation environnementale", "ar": "التقييم البيئي", "example": "L'évaluation environnementale est obligatoire pour les grands projets."},
                            {"fr": "l'association environnementale", "ar": "جمعية البيئة", "example": "L'association environnementale peut agir en justice."},
                            {"fr": "l'environnement sain", "ar": "البيئة السليمة", "example": "Le droit à un environnement sain est un droit fondamental."}
                        ],
                    },

                    {
                        "id": "fr_l4_u3_l2",
                        "title": "Les conventions internationales",
                        "title_ar": "الاتفاقيات الدولية",
                        "subtitle": "Droit des traités, ratification et applicabilité en droit interne",
                        "theory": (
                            "Les conventions internationales sont des accords conclus entre États ou organisations internationales. Elles constituent une source importante de droit international.\n"
                            "\n"
                            "La convention de Vienne de 1969 sur le droit des traités régit la négociation, l'adoption, la signature et la ratification des traités. Un traité ne lie que les parties et ne crée d'obligations qu'à leur égard.\n"
                            "\n"
                            "En droit français, la ratification suit une procédure constitutionnelle : le Président négocie et signe les traités, après autorisation du Parlement pour les traités les plus importants. Les traités ratifiés ont une autorité supérieure à celle des lois, mais inférieure à la Constitution.\n"
                            "\n"
                            "Le droit de l'Union européenne reconnaît aux traités internationaux une primauté sur le droit interne des États membres. La Cour de justice de l'UE veille à l'application uniforme du droit conventionnel.\n"
                            "\n"
                            "La dénonciation d'un traité est soumise aux procédures prévues par la convention de Vienne. Elle prend effet un an après la notification."
                        ),
                        "theory_ar": (
                            "الاتفاقيات الدولية هي اتفاقيات تُبرم بين دول أو منظمات دولية. تُشكّل مصدرًا مهماً للقانون الدولي.\n"
                            "\n"
                            "اتفاقية فيينا 1969 على قانون المعاهدات تُنظم التفاوض واتخاذ والتوقيع والتصديق على المعاهدات. المعاهدة لا تُلزم إلا الأطراف.\n"
                            "\n"
                            "في القانون الفرنسي، يتبع التصديق مساراً دستورياً: يتفاوض الرئيس ووقّع المعاهدات بعد تفويض من البرلمان للمعاهدات الأهم. المعاهدات المصدّق عليها لها سلطة أعلى من القوانين لكنها أقل من الدستور.\n"
                            "\n"
                            "يُقر قانون الاتحاد الأوروبي بتفوق المعاهدات الدولية على القانون الداخلي لدول الأعضاء. محكمة العدل تراقب التطبيق الموحد.\n"
                            "\n"
                            "إلغاء معاهدة يخضع للإجراءات المنصوص عليها في اتفاقية فيينا. يأخذ حيز التنفيذ بعد سنة من التبليغ."
                        ),
                        "vocab": [
                            {"fr": "la convention", "ar": "الاتفاقية", "example": "La convention internationale lie les parties signataires."},
                            {"fr": "le traité", "ar": "المعاهدة", "example": "Le traité a force obligatoire pour les États parties."},
                            {"fr": "la ratification", "ar": "التصديق", "example": "La ratification exprime le consentement de l'État à être lié."},
                            {"fr": "la signature", "ar": "التوقيع", "example": "La signature ouvre la voie à la ratification."},
                            {"fr": "la dénonciation", "ar": "الإلغاء", "example": "La dénonciation met fin aux obligations du traité."},
                            {"fr": "la convention de Vienne", "ar": "اتفاقية فيينا", "example": "La convention de Vienne régit le droit des traités."},
                            {"fr": "l'autorité supérieure", "ar": "السلطة العليا", "example": "Les traités ont une autorité supérieure aux lois."},
                            {"fr": "l'a réserves", "ar": "الاحتياطات", "example": "Les réserves permettent de modifer la portée du traité."},
                            {"fr": "la succession d'États", "ar": "خلافة الدول", "example": "La succession d'États affecte les traités en vigueur."},
                            {"fr": "l'interprétation des traités", "ar": "تفسير المعاهدations", "example": "L'interprétation des traités obéit aux règles de la convention de Vienne."}
                        ],
                    },

                    {
                        "id": "fr_l4_u3_l3",
                        "title": "Le droit comparé",
                        "title_ar": "المقارنة القانونية",
                        "subtitle": "Méthodologie et enjeux de la comparaison des systèmes juridiques",
                        "theory": (
                            "Le droit comparé est la discipline qui étudie les différences et les similitudes entre les systèmes juridiques de différents pays. Il constitue un outil essentiel pour la réforme du droit et la compréhension internationale.\n"
                            "\n"
                            "Les grandes familles juridiques sont le système civil law (droit continental, inspiré du Code civil français), le common law (droit anglo-saxon, basé sur la jurisprudence), le système socialiste et le droit islamique.\n"
                            "\n"
                            "La méthode comparative ne se limite pas à la description des droits étrangers. Elle cherche les raisons des différences (facteurs historiques, culturels, économiques) et en tire des enseignements pour le droit national.\n"
                            "\n"
                            "Le droit comparé joue un rôle croissant dans la construction européenne. Les juges nationaux et européens s'inspirent mutuellement de leurs jurisprudences respectives. La constitutionnalisation progressive des droits sociaux dans plusieurs pays témoigne de cette influence croisée.\n"
                            "\n"
                            "Les défis contemporains du droit comparé incluent la mondialisation du droit, l'harmonisation des normes internationales et la protection des diversités juridiques."
                        ),
                        "theory_ar": (
                            "المقارنة القانونية هي Discipline التي تدرس الفروق والتشابهات بين الأنظمة القانونية لبلدان مختلفة. تُشكّل أداةً أساسية للإصلاح القانوني.\n"
                            "\n"
                            "المجموعات القانونية الكبرى هي النظام المدني (القانون القارة، مستوحى من القانون المدني الفرنسي) والقانون العام (القانون الأنجلوساكسوني، المبني على الاجتهاد) والنظام الاشتراكي والقانون الإسلامي.\n"
                            "\n"
                            "منهج المقارنة لا يقتصر على وصف القوانين الأجنبية. يبحث عن أسباب الفروق (العوامل التاريخية والثقافية والاقتصادية) ويستخلص منها دروساً للقانون الوطني.\n"
                            "\n"
                            "يلعب المقارنة القانونية دوراً متنامياً في البناء الأوروبي. القضاة الأوروبيون يستلهمون من اجتهادات بعضهم البعض.\n"
                            "\n"
                            "التحديات المعاصرة تشمل العولمة القانونية وتوحيد المعايير الدولية وحماية التنوعات القانونية."
                        ),
                        "vocab": [
                            {"fr": "le droit comparé", "ar": "المقارنة القانونية", "example": "Le droit comparé étudie les systèmes juridiques étrangers."},
                            {"fr": "le civil law", "ar": "القانون المدني", "example": "Le civil law est le système juridique continental."},
                            {"fr": "le common law", "ar": "القانون العام", "example": "Le common law est basé sur la jurisprudence."},
                            {"fr": "la méthode comparative", "ar": "المنهج المقارن", "example": "La méthode comparative recherche les causes des différences."},
                            {"fr": "la famille juridique", "ar": "المجموعة القانونية", "example": "Les familles juridiques regroupent les systèmes similaires."},
                            {"fr": "l'harmonisation", "ar": "التوحيد", "example": "L'harmonisation des normes facilite les échanges internationaux."},
                            {"fr": "la diversité juridique", "ar": "التنوع القانوني", "example": "La diversité juridique est un patrimoine à préserver."},
                            {"fr": "l'influence mutuelle", "ar": "التأثير المتبادل", "example": "Les systèmes juridiques s'influencent mutuellement."},
                            {"fr": "le juge comparatiste", "ar": "القاضي المقارن", "example": "Le juge comparatiste s'inspire du droit étranger."},
                            {"fr": "la réforme du droit", "ar": "إصلاح القانون", "example": "Le droit comparé est un outil essentiel pour la réforme."}
                        ],
                    },

                ],
            },

        ],
    },

]


# ──────────────────────────────────────────────────────────────────────────
# 🇬🇧 الإنجليزية القانونية
# ──────────────────────────────────────────────────────────────────────────

LEVELS_EN = [
    {
        "id": 1,
        "title": "Beginner — المبتدئ",
        "description": "Essential legal vocabulary and expressions in English law",
        "color": "#2563eb",
        "units": [
            {
                "id": "en_l1_u1",
                "title": "Fundamental Legal Terms",
                "title_ar": "المصطلحات القانونية الأساسية",
                "lessons": [
                    {
                        "id": "en_l1_u1_l1",
                        "title": "Introduction to Legal Vocabulary",
                        "title_ar": "مقدمة في المفردات القانونية الإنجليزية",
                        "subtitle": "Core terminology of the common law system",
                        "theory": (
                            "Legal vocabulary is the foundation of understanding any legal system. The"
                            "English common law tradition uses specific terms that differ significantly from"
                            "those used in civil law jurisdictions. Understanding these terms is essential"
                            "for anyone seeking to work with or understand the English legal system.\n\nThe"
                            "common law system originated in England and has influenced legal systems across"
                            "the world, including those of the United States, Canada, Australia, and India."
                            "Unlike civil law systems which rely on comprehensive codes, common law systems"
                            "depend heavily on judicial precedent and case law.\n\nKey fundamental terms"
                            "include: The law refers to the entire body of rules enforced by the state"
                            "through its institutions. A statute is an Act of Parliament, representing"
                            "written law enacted by the legislature. Case law, also known as common law, is"
                            "law developed by judges through their decisions in individual cases. A"
                            "precedent is a previous court decision that courts must follow when deciding"
                            "similar cases.\n\nThe court system includes several levels: the Magistrates'"
                            "Court handles minor criminal cases; the Crown Court deals with serious criminal"
                            "offences; the County Court handles civil cases of lower value; the High Court"
                            "is the senior court of first instance; the Court of Appeal reviews decisions of"
                            "lower courts; and the Supreme Court is the highest court of appeal.\n\nLegal"
                            "professionals include judges who preside over courts, barristers who are"
                            "specialist advocates in England and Wales, and solicitors who handle day-to-day"
                            "legal matters. The decision of a jury or judge is the verdict, and the court's"
                            "formal decision is the judgment. Damages refer to monetary compensation for"
                            "loss or injury awarded by the court."
                        ),
                        "theory_ar": (
                            "المفردات القانونية هي أساس فهم أي نظام قانوني. يستخدم التقليد القانوني"
                            "الإنجليزي (القانون العام) مصطلحات محددة تختلف جذرياً عن تلك المستخدمة في"
                            "الأنظمة المدنية. فهم هذه المصطلحات أمر ضروري لأي شخص يسعى للعمل مع النظام"
                            "القانوني الإنجليزي.\n\nنشأ نظام القانون العام في إنجلترا وأثر على الأنظمة"
                            "القانونية في جميع أنحاء العالم. يعتمد بشكل كبير على سابقة قضائية وقانون"
                            "القضايا.\n\nمن المصطلحات الأساسية: القانون يشير إلى مجموعة القواعد التي يفرضها"
                            "الدولة. القانون الموضوعي (Statute) هو قانون صادر عن البرلمان. القانون القضائي"
                            "(Case law) هو قانون طوره القضاة. سابقة قضائية (Precedent) هي قرار محكمة سابق"
                            "يجب اتباعه.\n\nيشمل نظام المحاكم عدة مستويات: المحكمة الجزئية للجرائم البسيطة،"
                            "والمحكمة الجنائية للجرائم الخطيرة، ومحكمة المقاطعية للقضايا المدنية الأقل قيمة،"
                            "والمحكمة العليا للمسائل المدنية المعقدة.\n\nيشمل المهنيون القانونيون القضاة"
                            "والمحامون المُحترفون (Barristers) والمحامون العامون (Solicitors). الحكم"
                            "(Verdict) هو قرار هيئة المحلفين، والحكم القضائي (Judgment) هو القرار الرسمي"
                            "للمحكمة. التعويض (Damages) هو تعويض مالي عن الضرر."
                        ),
                        "vocab": [
                            {"fr": "the law", "ar": "القانون", "example": "The law provides for equal rights for all citizens."},
                            {"fr": "statute", "ar": "قانون موضوعي", "example": "The statute was enacted by Parliament in 2020."},
                            {"fr": "precedent", "ar": "سابقة قضائية", "example": "The court followed the precedent set in Donoghue v Stevenson."},
                            {"fr": "the court", "ar": "المحكمة", "example": "The court will hear the case next Monday morning."},
                            {"fr": "the judge", "ar": "القاضي", "example": "The judge ruled in favour of the claimant on all counts."},
                            {"fr": "the barrister", "ar": "المحامي المُحترف", "example": "The barrister presented compelling arguments to the jury."},
                            {"fr": "the solicitor", "ar": "المحامي العام", "example": "She instructed her solicitor to file the claim immediately."},
                            {"fr": "the plaintiff", "ar": "المدعي", "example": "The plaintiff seeks damages for breach of contract."},
                            {"fr": "the defendant", "ar": "المدعى عليه", "example": "The defendant denied all allegations in the statement of claim."},
                            {"fr": "the verdict", "ar": "الحكم", "example": "The jury returned a verdict of not guilty after deliberation."},
                            {"fr": "the judgment", "ar": "الحكم القضائي", "example": "The judgment was handed down by the High Court yesterday."},
                            {"fr": "damages", "ar": "التعويض", "example": "The court awarded fifty thousand pounds in damages."},
                            {"fr": "the remedy", "ar": "العلاج القانوني", "example": "The only available remedy in this case is damages."},
                            {"fr": "the litigant", "ar": "الخصم في الدعوى", "example": "Each litigant must disclose all relevant documents."},
                        ],
                    },
                    {
                        "id": "en_l1_u1_l2",
                        "title": "Legal Professionals and Institutions",
                        "title_ar": "المهن والمؤسسات القانونية",
                        "subtitle": "Who works in the legal system and where",
                        "theory": (
                            "The English legal system has a split legal profession, which is unique compared"
                            "to most civil law countries. There are two distinct branches of legal practice"
                            "that have developed over centuries, each with its own regulatory body and"
                            "professional standards.\n\nSolicitors are legal practitioners who handle the"
                            "majority of day-to-day legal work. They meet with clients, prepare legal"
                            "documents, conduct negotiations, and may appear in the lower courts. Solicitors"
                            "are regulated by the Solicitors Regulation Authority (SRA) and are members of"
                            "the Law Society.\n\nBarristers are specialist advocates who appear in court on"
                            "behalf of clients. They are instructed by solicitors rather than directly by"
                            "clients, and they must follow the cab-rank rule, which requires them to accept"
                            "any case in their area of expertise. Barristers are regulated by the Bar"
                            "Standards Board and are members of one of the four Inns of Court.\n\nKey legal"
                            "institutions include: the Supreme Court, which has been the highest court of"
                            "appeal since 2009; the High Court with its three divisions of Queen's Bench,"
                            "Chancery, and Family; the Crown Court which handles serious criminal offences;"
                            "the County Court for civil cases of lower value; and the Magistrates' Court for"
                            "minor criminal and civil matters. The Crown Prosecution Service (CPS) is"
                            "responsible for prosecuting crimes in England and Wales."
                        ),
                        "theory_ar": (
                            "يتميز النظام القانوني الإنجليزي بانفصال المهنة القانونية، وهو ما يميزه عن معظم"
                            "الأنظمة المدنية. هناك فرعان متميزان من الممارسة القانونية.\n\nالمحامون العامون"
                            "(Solicitors) يتعاملون مع معظم العمل القانوني اليومية. يلتقيون بالعملاء ويحضرون"
                            "المستندات القانونية.\n\nالمحامون المُحترفون (Barristers) هم خبراء في المحاكم"
                            "يُوكل إليهم المحامون العامون.\n\nتشمل المؤسسات القانونية الرئيسية: المحكمة"
                            "العليا (Supreme Court) و المحكمة العليا (High Court) و المحكمة الجنائية (Crown"
                            "Court) و محكمة المقاطعية (County Court) و المحكمة الجزئية (Magistrates' Court)."
                            "تتحمل خدمة الادعاء (CPS) مسؤولية متابعة الجرائم."
                        ),
                        "vocab": [
                            {"fr": "solicitor", "ar": "المحامي العام", "example": "I need to see my solicitor about the property contract."},
                            {"fr": "barrister", "ar": "المحامي المُحترف", "example": "The barrister will represent you in the Crown Court."},
                            {"fr": "the High Court", "ar": "المحكمة العليا", "example": "The case is being heard in the High Court next term."},
                            {"fr": "the Crown Court", "ar": "المحكمة الجنائية", "example": "The trial will take place at the Crown Court in London."},
                            {"fr": "the Magistrates' Court", "ar": "المحكمة الجزئية", "example": "Minor offences are heard at the local Magistrates' Court."},
                            {"fr": "the Supreme Court", "ar": "المحكمة العليا (النقض)", "example": "The Supreme Court will hear the appeal in November."},
                            {"fr": "the tribunal", "ar": "المحكمة المتخصصة", "example": "Employment disputes go to the employment tribunal."},
                            {"fr": "legal aid", "ar": "المساعدة القانونية", "example": "She qualified for legal aid to cover her court costs."},
                            {"fr": "the prosecution", "ar": "الادعاء / النيابة", "example": "The prosecution must prove the case beyond reasonable doubt."},
                            {"fr": "the defence", "ar": "الدفاع", "example": "The defence argued that the evidence was insufficient."},
                            {"fr": "the jury", "ar": "هيئة المحلفين", "example": "The jury deliberated for three days before reaching a verdict."},
                            {"fr": "the witness", "ar": "الشاهد", "example": "The witness gave evidence under oath in open court."},
                        ],
                    },
                    {
                        "id": "en_l1_u1_l3",
                        "title": "Essential Legal Expressions",
                        "title_ar": "التعبيرات القانونية الأساسية",
                        "subtitle": "Phrases every legal professional must know",
                        "theory": (
                            "Legal English uses specific fixed expressions that differ from everyday"
                            "English. These expressions are used in legal documents, court proceedings, and"
                            "professional correspondence. Mastering them is crucial for anyone working in an"
                            "English-speaking legal environment.\n\nExpressions of obligation include:"
                            "'shall' which imposes a legal duty and is mandatory; 'must' which indicates a"
                            "strong obligation similar to shall; and 'may' which grants discretion or"
                            "permission. Related expressions include 'is entitled to' meaning has a right"
                            "to, 'is liable for' meaning legally responsible for, and 'is obliged to'"
                            "meaning under a duty to.\n\nExpressions of prohibition include: 'shall not'"
                            "expressing an absolute prohibition; 'must not' for strong prohibition; 'is"
                            "prohibited from' meaning formally forbidden; and 'it is an offence to' which"
                            "indicates a criminal prohibition.\n\nProcedural expressions are commonly used"
                            "in litigation: 'the burden of proof lies with' identifies the party who must"
                            "prove their case; 'on the balance of probabilities' is the civil standard of"
                            "proof; 'beyond reasonable doubt' is the criminal standard of proof; 'subject"
                            "to' means conditional upon; 'notwithstanding' means despite or in spite of; and"
                            "'in accordance with' means following or complying with.\n\nFurthermore,"
                            "understanding these expressions is essential for drafting legal documents. For"
                            "instance, the word 'shall' is used in legislation to impose a mandatory"
                            "obligation, whereas 'may' confers a discretion upon the decision-maker. In"
                            "practice, the distinction between 'shall' and 'may' can have significant legal"
                            "consequences. A statute that says a public authority 'shall' grant a permit"
                            "creates a duty to do so, while one that says it 'may' grant a permit gives the"
                            "authority a choice. Legal professionals must also understand the difference"
                            "between 'must' and 'should', where 'must' indicates a binding requirement and"
                            "'should' indicates a recommendation that is not legally enforceable. The"
                            "expressions 'in accordance with' and 'subject to' are frequently encountered in"
                            "commercial contracts and statutory provisions. These fixed expressions form the"
                            "backbone of legal communication and must be mastered by anyone seeking to work"
                            "in an English-speaking legal environment."
                        ),
                        "theory_ar": (
                            "يستخدم القانون الإنجليزي عبارات ثابتة محددة تختلف عن الإنجليزية اليومية."
                            "تُستخدم هذه العبارات في المستندات القانونية والإجراءات المحكمة.\n\nتعبيرات"
                            "الإلزام تشمل: shall يفرض التزاماً قانونياً وهو إلزامي؛ must يدل على إلزام قوي؛"
                            "و may يمنح صلاحية أو إذن.\n\nتعبيرات التحريم تشمل: shall not للتحريم المطلق؛"
                            "must not للتحريم القوي؛ is prohibited from للممنوع رسمياً؛ و it is an offence"
                            "to للجريمة الجنائية.\n\nالتعبيرات الإجرائية شائعة في التقاضي: عبء الإثبات على"
                            "الطرف الذي يجب أن يثبت؛ على الاحتمالات الأرجح هو معيار الإثبات المدنية؛ فوق"
                            "الشك المعقول هو معيار الإثبات الجنائي؛ subject to مشروط بـ؛ notwithstanding"
                            "رغم؛ in accordance with وفقاً لـ."
                        ),
                        "vocab": [
                            {"fr": "shall", "ar": "يجب (إلزامي)", "example": "The employer shall provide a safe workplace for all employees."},
                            {"fr": "may", "ar": "يمكن / يحق", "example": "The court may order an injunction in appropriate cases."},
                            {"fr": "liable for", "ar": "مسؤول عن", "example": "The company is liable for the employee's negligence."},
                            {"fr": "entitled to", "ar": "له الحق في", "example": "The tenant is entitled to quiet enjoyment of the property."},
                            {"fr": "the burden of proof", "ar": "عبء الإثبات", "example": "The burden of proof lies with the claimant in civil cases."},
                            {"fr": "beyond reasonable doubt", "ar": "فوق الشك المعقول", "example": "The prosecution must prove the case beyond reasonable doubt."},
                            {"fr": "on the balance of probabilities", "ar": "على الاحتمالات الأرجح", "example": "Civil cases are decided on the balance of probabilities."},
                            {"fr": "in accordance with", "ar": "وفقاً لـ", "example": "This must be done in accordance with the regulations."},
                            {"fr": "subject to", "ar": "مشروط بـ", "example": "Subject to court approval, the settlement is final."},
                            {"fr": "notwithstanding", "ar": "رغم / على الرغم من", "example": "Notwithstanding any other provision, this clause applies."},
                            {"fr": "it is an offence to", "ar": "يُعتبر جريمة", "example": "It is an offence to drive without valid insurance."},
                            {"fr": "in the interests of justice", "ar": "في مصلحة العدالة", "example": "The case was transferred in the interests of justice."},
                        ],
                    },
                    {
                        "id": "en_l1_u1_l4",
                        "title": "Sources of Law in Common Law Systems",
                        "title_ar": "مصادر القانون في أنظمة القانون العام",
                        "subtitle": "How law is created and developed",
                        "theory": (
                            "The common law system derives its authority from multiple sources of law that"
                            "work together to form a coherent legal framework. Understanding these sources"
                            "is fundamental to studying any common law jurisdiction.\n\nPrimary sources of"
                            "law include: legislation (also called statutes or Acts of Parliament), which is"
                            "law made by the legislature; case law (also called judge-made law or common"
                            "law), which develops through judicial decisions; and delegated legislation,"
                            "which is law made by ministers or other bodies under authority granted by"
                            "Parliament.\n\nThe hierarchy of legislation is important: Acts of Parliament"
                            "are supreme and cannot be overridden by any other legislation. Delegated"
                            "legislation must be consistent with the enabling Act and can be challenged if"
                            "it exceeds the authority granted.\n\nCase law develops through the doctrine of"
                            "precedent. When a higher court decides a point of law, that decision becomes"
                            "binding on lower courts in the same hierarchy. A ratio decidendi is the legal"
                            "reasoning that supports the decision and is binding. Obiter dicta are remarks"
                            "made by the judge that are not essential to the decision and are persuasive"
                            "rather than binding. Distinguishing a case means finding material differences"
                            "that allow a court to depart from a previous decision. Overruling occurs when a"
                            "higher court expressly rejects a previous decision."
                        ),
                        "theory_ar": (
                            "يُشتق نظام القانون العام سلطته من مصادر قانونية متعددة تعمل معاً لتشكيل إطار"
                            "قانوني متماسك. فهم هذه المصادر أساسي لدراسة أي ولاية قضائية تتبع قانون"
                            "العام.\n\nتشمل المصادر الأولية للقانون: التشريعات (Acts of Parliament)؛ وقانون"
                            "القضايا (Case law)؛ والتشريعات المن delegated legislation.\n\nتسلسل التشريعات"
                            "مهم: قوانين البرلمان مطلقة ولا يمكن لأي تشريع آخر تجاوزها.\n\nيتطور قانون"
                            "القضايا عبر مبدأ سابقة قضائية. Ratio decidendi هو التبرير القانوني الملزم."
                            "Obiter dicta هي ملاحظات القاضي غير الأساسية. التمييز (Distinguishing) يعني"
                            "إيجاد فروقات جوهرية. الإلغاء (Overruling) يحدث عندما ترفض محكمة أعلى قرار محكمة"
                            "أدنى."
                        ),
                        "vocab": [
                            {"fr": "legislation", "ar": "التشريعات", "example": "New legislation was introduced to protect consumer rights."},
                            {"fr": "statute", "ar": "قانون موضوعي", "example": "The statute came into force on the first of January."},
                            {"fr": "case law", "ar": "قانون القضايا", "example": "Case law has developed significantly in this area."},
                            {"fr": "precedent", "ar": "سابقة قضائية", "example": "The court considered the binding precedent from the House of Lords."},
                            {"fr": "ratio decidendi", "ar": "التبرير القضائي", "example": "The ratio decidendi of the judgment is clear and persuasive."},
                            {"fr": "obiter dicta", "ar": "ملاحظات عرضية", "example": "The obiter dicta in this case are highly instructive."},
                            {"fr": "delegated legislation", "ar": "التشريعات المنوابة", "example": "The statutory instrument is a form of delegated legislation."},
                            {"fr": "enabling Act", "ar": "القانون التمكيني", "example": "The enabling Act grants powers to make regulations."},
                            {"fr": "to distinguish", "ar": "تمييز / تفريق", "example": "Counsel sought to distinguish the earlier authority."},
                            {"fr": "to overrule", "ar": "إلغاء / رفض", "example": "The Supreme Court declined to overrule the established principle."},
                            {"fr": "binding authority", "ar": "سلطة ملزمة", "example": "This decision is a binding authority on all county courts."},
                            {"fr": "persuasive authority", "ar": "سلطة إقناعية", "example": "The Scottish decision is only a persuasive authority in England."},
                        ],
                    },
                    {
                        "id": "en_l1_u1_l5",
                        "title": "Constitutional Law Basics",
                        "title_ar": "أسس القانون الدستوري",
                        "subtitle": "The foundation of the legal system",
                        "theory": (
                            "Constitutional law governs the relationship between the state and its citizens,"
                            "and between the different branches of government. Unlike many countries, the"
                            "United Kingdom does not have a single codified constitution. Instead, its"
                            "constitution is uncodified and derived from multiple sources.\n\nThe main"
                            "sources of the UK constitution include: Acts of Parliament such as the Magna"
                            "Carta 1215, the Bill of Rights 1689, and the Human Rights Act 1998;"
                            "constitutional conventions which are unwritten rules of political practice;"
                            "common law decisions of the courts; works of authoritative legal writers; and"
                            "treaties and international obligations.\n\nParliamentary sovereignty is the"
                            "cornerstone of the UK constitution. This means that Parliament is the supreme"
                            "legal authority and can create or repeal any law. No body, including the"
                            "courts, can override or set aside legislation enacted by Parliament.\n\nThe"
                            "separation of powers divides government into three branches: the legislature"
                            "(Parliament), the executive (the Government), and the judiciary (the courts)."
                            "The rule of law requires that all persons and institutions are accountable to"
                            "laws that are publicly promulgated, equally enforced, and independently"
                            "adjudicated. Judicial review allows courts to examine the legality of"
                            "government actions.\n\nThe UK constitution also includes the devolution"
                            "settlements, which grant legislative and executive powers to the Scottish"
                            "Parliament, the Welsh Senedd, and the Northern Ireland Assembly. These devolved"
                            "institutions can legislate on matters within their competence, but the UK"
                            "Parliament retains the sovereignty to legislate on any matter. The relationship"
                            "between Westminster and the devolved institutions is governed by conventions"
                            "and statute. Judicial review of government action is a vital mechanism for"
                            "ensuring that the rule of law is maintained and that public bodies act within"
                            "their legal powers."
                        ),
                        "theory_ar": (
                            "يُنظّم القانون الدستوري العلاقة بين الدولة ومواطنيها وبين الفروع المختلفة"
                            "للحكومة. لا تملك المملكة المتحدة دستوراً مكتوباً واحداً.\n\nتشمل المصادر"
                            "الرئيسية للدستور: Acts of Parliament مثل الماجنا كارتا 1215 وقانون الحقوق 1689"
                            "وقانون حقوق الإنسان 1998؛ والاتفاقيات الدستورية غير المكتوبة.\n\nسيادة البرلمان"
                            "هي حجر الأساس في الدستور البريطاني. هذا يعني أن البرلمان هو السلطة القانونية"
                            "العليا.\n\nيُقسم فصل السلطات الحكومة إلى ثلاثة فروع: السلطة التشريعية والسلطة"
                            "التنفيذية والسلطة القضائية. يطلب حكم القانون أن جميع الأشخاص والمؤسسات مسؤولة"
                            "أمام القوانين. تُمكّن الرقابة القضائية المحاكم من فحص شرعيات أفعال الحكومة."
                        ),
                        "vocab": [
                            {"fr": "the constitution", "ar": "الدستور", "example": "The UK has an uncodified constitution drawn from multiple sources."},
                            {"fr": "Parliamentary sovereignty", "ar": "سيادة البرلمان", "example": "Parliamentary sovereignty is the cornerstone of the UK constitution."},
                            {"fr": "the rule of law", "ar": "حكم القانون", "example": "The rule of law ensures equality before the law for all citizens."},
                            {"fr": "separation of powers", "ar": "فصل السلطات", "example": "The separation of powers prevents concentration of authority."},
                            {"fr": "the executive", "ar": "السلطة التنفيذية", "example": "The executive is responsible for implementing legislation."},
                            {"fr": "the legislature", "ar": "السلطة التشريعية", "example": "The legislature has the power to enact new statutes."},
                            {"fr": "the judiciary", "ar": "السلطة القضائية", "example": "The judiciary interprets and applies the law independently."},
                            {"fr": "judicial review", "ar": "الرقابة القضائية", "example": "Judicial review allows courts to quash unlawful government decisions."},
                            {"fr": "constitutional convention", "ar": "اتفاقية دستورية", "example": "Constitutional conventions are unwritten but politically binding."},
                            {"fr": "declaration of incompatibility", "ar": "إعلان عدم التوافق", "example": "The court issued a declaration of incompatibility under the Human Rights Act."},
                            {"fr": "human rights", "ar": "حقوق الإنسان", "example": "The Human Rights Act incorporates the European Convention on Human Rights."},
                            {"fr": "Magna Carta", "ar": "الماغنا كارتا", "example": "The Magna Carta is considered a foundational constitutional document."},
                        ],
                    },
                    {
                        "id": "en_l1_u1_l6",
                        "title": "Fundamentals of Civil Law",
                        "title_ar": "أسس القانون المدني",
                        "subtitle": "Rights, obligations and civil disputes",
                        "theory": (
                            "Civil law governs disputes between private individuals and organizations, as"
                            "opposed to criminal law which deals with offences against the state. In England"
                            "and Wales, civil law encompasses contract, tort, property, family, and"
                            "employment law.\n\nThe Civil Procedure Rules (CPR) were introduced in 1999 to"
                            "reform civil litigation. The overriding objective is to enable courts to deal"
                            "with cases justly and at proportionate cost. Key principles include ensuring"
                            "parties are on an equal footing and cases are dealt with proportionately.\n\nA"
                            "civil claim begins with the claimant filing a claim form and particulars of"
                            "claim. The defendant then files a defence. Disclosure of documents is a crucial"
                            "stage where both parties must reveal all relevant documents. Cases may be"
                            "resolved through negotiation, mediation, or other forms of alternative dispute"
                            "resolution before reaching trial.\n\nThe standard of proof in civil cases is on"
                            "the balance of probabilities, meaning the claimant must show that their version"
                            "of events is more likely than not to be true. Remedies include damages,"
                            "injunctions, specific performance, and declarations of rights.\n\nCivil cases"
                            "in England and Wales are governed by the Civil Procedure Rules, which were"
                            "introduced to streamline the litigation process and reduce costs. Pre-action"
                            "protocols encourage parties to resolve disputes before proceedings are issued."
                            "The court has wide case management powers to ensure that cases progress"
                            "efficiently. Proportionate case management means that the court will tailor its"
                            "approach to the value and complexity of the dispute. Costs management orders"
                            "require parties to provide estimated costs budgets at an early stage. These"
                            "reforms have made civil litigation more accessible and efficient."
                        ),
                        "theory_ar": (
                            "يُنظّم القانون المدني النزاعات بين الأفراد والمؤسسات الخاصة، على خلاف القانون"
                            "الجنائي الذي ي dealt مع الجرائم ضد الدولة.\n\nأُدخلت قواعد الإجراءات المدنية"
                            "(CPR) عام 1999 لإصلاح التقاضي المدني. الهدف الأساسي هو التعامل مع القضايا بعدل"
                            "وبتكلفة متناسبة.\n\nتبدأ الدعوى المدنية بتقديم المدعي استمارة دعوى وتفاصيل"
                            "الدعوى. ثم يقدم المدعى عليه دفاعه. الإفصاح عن المستندات هو مرحلة"
                            "حاسمة.\n\nمعيار الإثبات في القضايا المدنية هو على الاحتمالات الأرجح. تشمل"
                            "العلاجات التعويض والأوامر القضائية والتنفيذ الجبري والإعلانات الرسمية."
                        ),
                        "vocab": [
                            {"fr": "civil law", "ar": "القانون المدني", "example": "Civil law governs disputes between private parties."},
                            {"fr": "the claimant", "ar": "المدعي", "example": "The claimant filed a claim form in the county court."},
                            {"fr": "the defendant", "ar": "المدعى عليه", "example": "The defendant has twenty-eight days to file a defence."},
                            {"fr": "particulars of claim", "ar": "تفاصيل الدعوى", "example": "The particulars of claim set out the basis of the claim."},
                            {"fr": "disclosure", "ar": "الإفصاح عن المستندات", "example": "Both parties must complete disclosure of all relevant documents."},
                            {"fr": "balance of probabilities", "ar": "الاحتمالات الأرجح", "example": "The civil standard of proof is the balance of probabilities."},
                            {"fr": "injunction", "ar": "أمر قضائي", "example": "She obtained an interim injunction to prevent eviction."},
                            {"fr": "specific performance", "ar": "التنفيذ الجبري", "example": "The court ordered specific performance of the land sale contract."},
                            {"fr": "mediation", "ar": "الوساطة", "example": "The parties were ordered to attempt mediation before trial."},
                            {"fr": "the CPR", "ar": "قواعد الإجراءات المدنية", "example": "The CPR governs the conduct of civil litigation in England and Wales."},
                            {"fr": "the overriding objective", "ar": "الهدف الأساسي", "example": "The overriding objective is to deal with cases justly."},
                            {"fr": "a declaration", "ar": "إعلان قضائي", "example": "The court granted a declaration of the parties' respective rights."},
                        ],
                    },
                    {
                        "id": "en_l1_u1_l7",
                        "title": "Introduction to Criminal Law",
                        "title_ar": "مقدمة في القانون الجنائي",
                        "subtitle": "Offences, defences and criminal procedure",
                        "theory": (
                            "Criminal law defines conduct that is considered harmful to society and provides"
                            "for the prosecution and punishment of those who commit criminal offences. In"
                            "England and Wales, criminal law is derived primarily from statute and case"
                            "law.\n\nThe key elements of a criminal offence are: the actus reus (the"
                            "physical element or guilty act) and the mens rea (the mental element or guilty"
                            "mind). Both elements must generally be present for a person to be found"
                            "guilty.\n\nTypes of criminal offences include summary offences (minor offences"
                            "tried in the Magistrates' Court), either-way offences (which can be tried in"
                            "either the Magistrates' Court or the Crown Court), and indictable offences"
                            "(serious offences that can only be tried in the Crown Court).\n\nAvailable"
                            "defences include: self-defence, duress, necessity, intoxication, automatism,"
                            "insanity, and diminished responsibility. The prosecution must prove all"
                            "elements of the offence beyond reasonable doubt.\n\nThe criminal justice"
                            "process in England and Wales follows a structured sequence. After an arrest,"
                            "the suspect is interviewed by the police. The Crown Prosecution Service then"
                            "decides whether to charge the suspect based on the realistic prospect of"
                            "conviction test. If charged, the case proceeds to a preliminary hearing before"
                            "the Magistrates' Court or the Crown Court. The defendant has the right to a"
                            "fair trial, including the right to legal representation, the right to silence,"
                            "and the presumption of innocence. Sentencing follows established guidelines"
                            "published by the Sentencing Council. Appeals against conviction or sentence can"
                            "be made to the Court of Appeal Criminal Division."
                        ),
                        "theory_ar": (
                            "يُعرّف القانون الجنائي السلوك الذي يُعتبر ضاراً بالمجتمع ويوفر مقاضاة ومعاقبة"
                            "مرتكبي الجرائم.\n\nتشمل العناصر الأساسية للجريمة: الفعل المادي (actus reus)"
                            "والنية الإجرامية (mens rea). يجب وجود كلا العنصرين عموماً لإدانة الشخص.\n\nتشمل"
                            "أنواع الجرائم: الجرائم الجزئية والجرائم المتوسطة والجرائم الجسيمة.\n\nتشمل"
                            "الدفاعات المتاحة: الدفاع عن النفس والإكراه والضرورة والسلوكي الآلي والجنون"
                            "والمسؤولية المخففة. يجب على الادعاء إثبات جميع عناصر الجريمة فوق الشك المعقول."
                        ),
                        "vocab": [
                            {"fr": "criminal law", "ar": "القانون الجنائي", "example": "Criminal law defines offences against the state."},
                            {"fr": "actus reus", "ar": "الفعل المادي الإجرامي", "example": "The actus reus of theft is the appropriation of property."},
                            {"fr": "mens rea", "ar": "النية الإجرامية", "example": "The prosecution must prove the defendant had the requisite mens rea."},
                            {"fr": "the offence", "ar": "الجريمة", "example": "The offence was committed in the early hours of the morning."},
                            {"fr": "the verdict", "ar": "الحكم", "example": "The jury returned a unanimous verdict of not guilty."},
                            {"fr": "self-defence", "ar": "الدفاع عن النفس", "example": "The accused claimed self-defence as the basis for his actions."},
                            {"fr": "reasonable doubt", "ar": "شك معقول", "example": "The prosecution must prove guilt beyond reasonable doubt."},
                            {"fr": "acquitted", "ar": "بريء / مبرأ", "example": "The defendant was acquitted of all charges by the jury."},
                            {"fr": "sentencing", "ar": "التكييف الجنائي / الحكم", "example": "Sentencing will take place next month after a pre-sentence report."},
                            {"fr": "the indictment", "ar": "الإدعاء الرسمي", "example": "The indictment charges the defendant with three counts of fraud."},
                            {"fr": "summary offence", "ar": "جريمة جزئية", "example": "Common assault is a summary offence heard in the Magistrates' Court."},
                            {"fr": "diminished responsibility", "ar": "المسؤولية المخففة", "example": "Diminished responsibility is a partial defence to murder."},
                        ],
                    },
                    {
                        "id": "en_l1_u1_l8",
                        "title": "Civil Procedure Basics",
                        "title_ar": "أسس الإجراءات المدنية",
                        "subtitle": "How civil cases move through the courts",
                        "theory": (
                            "Civil procedure refers to the rules and practices that govern how civil cases"
                            "are conducted in court. The Civil Procedure Rules (CPR) were introduced in"
                            "England and Wales in 1999 following Lord Woolf's report on access to"
                            "justice.\n\nThe stages of a typical civil case include: pre-action protocols"
                            "which require parties to exchange information before starting proceedings;"
                            "issuing a claim; service of the claim; filing a defence; case management"
                            "conferences; disclosure of documents; exchange of witness statements; pre-trial"
                            "review; and the trial itself.\n\nCase management is a key feature of modern"
                            "civil procedure. The court actively manages cases to ensure they proceed"
                            "efficiently and proportionately. The court may impose sanctions for"
                            "non-compliance with rules or orders.\n\nCosts in civil litigation follow the"
                            "general rule that the unsuccessful party pays the costs of the successful"
                            "party. However, the court has discretion to make different costs orders. Costs"
                            "can be assessed on the standard basis or the indemnity basis.\n\nThe CPR"
                            "introduced a culture shift in civil litigation, moving away from the"
                            "adversarial approach towards a more cooperative process. Parties are required"
                            "to help the court further the overriding objective. This includes dealing with"
                            "cases proportionately and ensuring that the parties are on an equal footing."
                            "The court can impose adverse costs orders against parties who fail to comply"
                            "with rules, directions, or court orders. Part 36 offers are a powerful tactical"
                            "tool that encourage early settlement by imposing costs consequences on parties"
                            "who fail to accept reasonable offers."
                        ),
                        "theory_ar": (
                            "تشير الإجراءات المدنية إلى القواعد والممارسات التي تُنظّم كيفية نظر القضايا"
                            "المدنية في المحاكم. أُدخلت قواعد الإجراءات المدنية (CPR) عام 1999.\n\nتتضمن"
                            "مراحل القضية المدنية: بروتوكولات ما قبل الدعوى ودعوى الخدمة والدفاع واجتماعات"
                            "إدارة القضية والإفصاح عن المستندات وتبادل شهادات الشهود والمحاكمة.\n\nإدارة"
                            "القضية هي سمة رئيسية في الإجراءات المدنية الحديثة.\n\nتتبع تكاليف التقاضي"
                            "المدني القاعدة العامة القائلة بأن الطرف الخاسر يدفع تكاليف الطرف الناجح."
                        ),
                        "vocab": [
                            {"fr": "civil procedure", "ar": "الإجراءات المدنية", "example": "Civil procedure governs how disputes are resolved in court."},
                            {"fr": "pre-action protocol", "ar": "بروتوكول ما قبل الدعوى", "example": "Parties must comply with the pre-action protocol before issuing a claim."},
                            {"fr": "claim form", "ar": "استمارة الدعوى", "example": "The claim form was issued at the county court on Monday."},
                            {"fr": "service", "ar": "خدمة / تبليغ", "example": "Service of the claim must be effected within four months."},
                            {"fr": "defence", "ar": "الدفاع", "example": "The defendant filed a defence denying all allegations."},
                            {"fr": "disclosure", "ar": "الإفصاح", "example": "Standard disclosure requires each party to reveal relevant documents."},
                            {"fr": "case management", "ar": "إدارة القضية", "example": "The case management conference will determine the trial timetable."},
                            {"fr": "witness statement", "ar": "شهادة الشاهد", "example": "The witness statement must be verified by a statement of truth."},
                            {"fr": "trial", "ar": "المحاكمة", "example": "The trial is listed for three days in the High Court."},
                            {"fr": "costs", "ar": "التكاليف", "example": "The unsuccessful party was ordered to pay the costs of the action."},
                            {"fr": "striking out", "ar": "حذف / إسقاط", "example": "The court may strike out a statement of case for non-compliance."},
                            {"fr": "sanctions", "ar": "العقوبات الإجرائية", "example": "The court imposed sanctions for failure to comply with the order."},
                        ],
                    },
                    {
                        "id": "en_l1_u1_l9",
                        "title": "Employment and Labor Law",
                        "title_ar": "قانون العمل والتوظيف",
                        "subtitle": "Rights and obligations in the workplace",
                        "theory": (
                            "Employment law regulates the relationship between employers and employees in"
                            "the workplace. In England and Wales, employment rights are derived from both"
                            "statute and common law. The Employment Rights Act 1996 is the primary statute"
                            "governing individual employment rights.\n\nKey employment rights include: the"
                            "right not to be unfairly dismissed after two years of continuous employment;"
                            "the right to a written statement of employment particulars; the right to"
                            "receive the national minimum wage; the right to paid annual leave; and"
                            "protection against discrimination under the Equality Act 2010.\n\nThe Equality"
                            "Act 2010 consolidates previous anti-discrimination legislation and protects"
                            "workers from discrimination on the basis of nine protected characteristics:"
                            "age, disability, gender reassignment, marriage and civil partnership, pregnancy"
                            "and maternity, race, religion or belief, sex, and sexual"
                            "orientation.\n\nEmployment disputes are primarily resolved through the"
                            "employment tribunal. Before making a claim, employees must generally notify"
                            "ACAS through the early conciliation process.\n\nEmployment tribunal claims must"
                            "generally be brought within three months of the effective date of termination."
                            "The tribunal has the power to extend this time limit in certain exceptional"
                            "circumstances. Remedies available in the employment tribunal include"
                            "reinstatement, re-engagement, and compensation. The basic award is calculated"
                            "in a similar way to a statutory redundancy payment. The compensatory award is"
                            "designed to compensate the employee for actual financial loss resulting from"
                            "the dismissal. The tribunal can also make a recommendation that the employer"
                            "take specified steps to reduce the adverse effect of the discrimination on the"
                            "claimant."
                        ),
                        "theory_ar": (
                            "يُنظّم قانون العمل علاقة أصحاب العمل بالعمال. في إنجلترا وويلز، تُشتق حقوق"
                            "العمل من التشريع والقانون المشترك.\n\nتشمل حقوق العمل الرئيسية: الحق في عدم"
                            "الفصل بشكل غير عادل بعد سنتين من التوظيف المتواصل؛ والحق في بيان خطي لشروط"
                            "العمل؛ والحق في الحد الأدنى للأجور الوطنية؛ والحق في إجازة سنوية"
                            "مدفوعة.\n\nيقضي قانون المساواة 2010 بحماية العمال من التمييز على أساس تسع صفات"
                            "محمية.\n\nتُحل نزاعات العمل أساساً من خلال محكمة العمل. يجب على العمال عموماً"
                            "إخطار ACAS عبر عملية التوفيق المبكر."
                        ),
                        "vocab": [
                            {"fr": "employment law", "ar": "قانون العمل", "example": "Employment law protects the rights of workers in the UK."},
                            {"fr": "unfair dismissal", "ar": "الفصل غير العادل", "example": "She brought a claim for unfair dismissal after losing her job."},
                            {"fr": "the national minimum wage", "ar": "الحد الأدنى للأجور", "example": "All workers are entitled to receive the national minimum wage."},
                            {"fr": "annual leave", "ar": "الإجازة السنوية", "example": "Workers are entitled to a minimum of 5.6 weeks of annual leave."},
                            {"fr": "discrimination", "ar": "التمييز", "example": "Discrimination on the basis of race is unlawful under the Equality Act."},
                            {"fr": "the Equality Act", "ar": "قانون المساواة", "example": "The Equality Act 2010 protects against workplace discrimination."},
                            {"fr": "ACAS", "ar": "هيئة الإصلاح والتوسط", "example": "You must contact ACAS before lodging a tribunal claim."},
                            {"fr": "the employment tribunal", "ar": "محكمة العمل", "example": "The employment tribunal hearing is scheduled for next month."},
                            {"fr": "constructive dismissal", "ar": "الاستقالة القسرية", "example": "The employee resigned and claimed constructive dismissal."},
                            {"fr": "the employer", "ar": "صاحب العمل", "example": "The employer must provide a safe working environment."},
                            {"fr": "continuous employment", "ar": "التوظيف المتواصل", "example": "Two years of continuous employment is required for unfair dismissal rights."},
                            {"fr": "maternity leave", "ar": "إجازة الأمومة", "example": "She is currently on maternity leave and expects to return in September."},
                        ],
                    },
                    {
                        "id": "en_l1_u1_l10",
                        "title": "Family Law Fundamentals",
                        "title_ar": "أسس قانون الأسرة",
                        "subtitle": "Marriage, divorce, children and domestic relations",
                        "theory": (
                            "Family law deals with legal issues related to family relationships, including"
                            "marriage, civil partnerships, divorce, children, and domestic violence. In"
                            "England and Wales, family law has undergone significant reform in recent"
                            "decades.\n\nThe Matrimonial Causes Act 1973 governs divorce proceedings. Since"
                            "the Divorce, Dissolution and Separation Act 2020, couples can seek a divorce on"
                            "the basis of irretrievable breakdown of the marriage without having to prove"
                            "fault.\n\nThe welfare of the child is the paramount consideration in all"
                            "decisions concerning children under the Children Act 1989. The court may make"
                            "orders regarding with whom a child is to live, with whom a child is to spend"
                            "time, and other matters relating to the child's upbringing.\n\nDomestic"
                            "violence is addressed through both criminal law and family law. The court can"
                            "issue non-molestation orders and occupation orders to protect victims of"
                            "domestic abuse.\n\nFinancial remedies in family proceedings are governed by the"
                            "Matrimonial Causes Act 1973. The court considers a range of factors including"
                            "the income, earning capacity, property, and financial needs of each party. The"
                            "starting point is equal sharing of the matrimonial assets, subject to any"
                            "statutory departure factors. In children cases, the welfare checklist in"
                            "section 1(3) of the Children Act 1989 guides the court's decision-making. The"
                            "no order principle means that the court will not make an order unless it"
                            "considers that doing so would be better for the child than making no order."
                        ),
                        "theory_ar": (
                            "يُ dealt قانون الأسرة مع المسائل القانونية المتعلقة بالعلاقات الأسرية، بما في"
                            "ذلك الزواج والشراكات المدنية والطلاق والأطفال والعنف المنزلي.\n\nيُنظّم قانون"
                            "أسباب الزواج 1973 إجراءات الطلاق. منذ قانون الطلاق والإلغاء والفصل 2020، يمكن"
                            "للأزواج البحث عن الطلاق على أساس الانهيار غير القابل للإصلاح.\n\nرفاهية الطفل"
                            "هي الاعتبار الأسمى في جميع القرارات تتعلق بالأطفال بموجب قانون الأطفال"
                            "1989.\n\nيتم معالجة العنف المنزلي من خلال القانون الجنائي وقانون الأسرة. يمكن"
                            "للمحكمة إصدار أوامر عدم التحرش وأمر السكن لحماية ضحايا العنف المنزلي."
                        ),
                        "vocab": [
                            {"fr": "family law", "ar": "قانون الأسرة", "example": "Family law deals with marriage, divorce and children matters."},
                            {"fr": "divorce", "ar": "الطلاق", "example": "The divorce petition was filed in the Family Court."},
                            {"fr": "child arrangements order", "ar": "ترتيب arrangements للأطفال", "example": "The court made a child arrangements order specifying contact."},
                            {"fr": "parental responsibility", "ar": "المسؤولية الأبوية", "example": "Both parents have parental responsibility for the child."},
                            {"fr": "the welfare principle", "ar": "مبدأ الرفاهية", "example": "The welfare of the child is the paramount consideration."},
                            {"fr": "non-molestation order", "ar": "أمر عدم التحرش", "example": "She obtained a non-molestation order against her former partner."},
                            {"fr": "occupation order", "ar": "أمر السكن", "example": "The occupation order excluded the respondent from the family home."},
                            {"fr": "matrimonial assets", "ar": "الأصول الزوجية", "example": "The matrimonial assets were divided equally between the parties."},
                            {"fr": "civil partnership", "ar": "شراكة مدنية", "example": "Civil partners have similar rights to married couples."},
                            {"fr": "the Family Court", "ar": "محكمة الأسرة", "example": "The application will be heard in the Family Court."},
                            {"fr": "contact order", "ar": "أمر الاتصال", "example": "The father was granted a contact order for alternate weekends."},
                            {"fr": "residence order", "ar": "أمر الإقامة", "example": "The residence order specified that the child would live with the mother."},
                        ],
                    },
                ],
            },
        ],
    },
    {
        "id": 2,
        "title": "Intermediate — المتوسط",
        "description": "Complex legal structures, obligations and contract law",
        "color": "#059669",
        "units": [
            {
                "id": "en_l2_u1",
                "title": "Advanced Legal Language",
                "title_ar": "اللغة القانونية المتقدمة",
                "lessons": [
                    {
                        "id": "en_l2_u1_l1",
                        "title": "Complex Legal Sentences",
                        "title_ar": "الجمل القانونية المعقدة",
                        "subtitle": "Understanding and constructing complex legal language",
                        "theory": (
                            "Legal English frequently employs complex sentence structures that can be"
                            "challenging for non-native speakers to understand. These structures are"
                            "designed to express precise legal relationships and conditions with minimal"
                            "ambiguity. Understanding them is essential for reading and drafting legal"
                            "documents accurately.\n\nConditional sentences are fundamental in legal"
                            "drafting. For example, 'If the vendor fails to complete on the completion date,"
                            "the purchaser may rescind the contract and recover the deposit.' Multiple"
                            "conditions can be nested within a single sentence: 'Subject to the approval of"
                            "the board, and provided that the relevant regulatory consent has been obtained,"
                            "the company shall proceed with the transaction.'\n\nRelative clauses add detail"
                            "and specification to legal documents. For instance, 'The person who has"
                            "occupied the property as his only or principal home for a period of at least"
                            "twelve months immediately preceding the date of application.' Participial"
                            "clauses condense information: 'Having considered all the evidence submitted by"
                            "both parties, the tribunal finds in favour of the claimant.'\n\nNegative"
                            "conditionals express consequences of non-compliance: 'Unless the tenant pays"
                            "the rent within fourteen days of the due date, the landlord may serve a notice"
                            "seeking possession.' These complex structures allow the expression of multiple"
                            "legal relationships within a single sentence, which is essential for precise"
                            "legal drafting."
                        ),
                        "theory_ar": (
                            "يستخدم القانون الإنجليزي بنيات جمل معقدة يمكن أن تشكل تحدياً لغير الناطقين"
                            "بالإنجليزية. هذه البنيات مصممة للتعبير عن علاقات قانونية دقيقة.\n\nالجمل"
                            "الشرطية أساسية في التصيغة القانونية. يمكن تداخل شروط متعددة. تضيف الجمل النسبية"
                            "التفاصيل. الجمل participial تلخص المعلومات.\n\nالجمل الشرطية السلبية تعبر عن"
                            "عواقب عدم الامتثال. تُمكّن الجمل المنسقة والمُرتبطة من التعبير عن علاقات"
                            "قانونية متعددة داخل جملة واحدة."
                        ),
                        "vocab": [
                            {"fr": "subject to", "ar": "مشروط بـ", "example": "Subject to the terms of this agreement, the seller shall transfer title."},
                            {"fr": "provided that", "ar": "شريطة أن", "example": "The licence is granted provided that the applicant meets all conditions."},
                            {"fr": "in the event that", "ar": "في حالة", "example": "In the event that the buyer defaults, the seller may retain the deposit."},
                            {"fr": "unless", "ar": "ما لم", "example": "Unless otherwise agreed, payment is due within thirty days."},
                            {"fr": "notwithstanding", "ar": "رغم / على الرغم من", "example": "Notwithstanding the above, the supplier shall not be liable for indirect loss."},
                            {"fr": "hereby", "ar": "بعناية هذا", "example": "The parties hereby agree to the terms set out below."},
                            {"fr": "herein", "ar": "في هذا العقد", "example": "The obligations herein shall survive termination of this agreement."},
                            {"fr": "thereof", "ar": "لهذا / لذلك", "example": "The seller shall transfer all rights and interest therein to the buyer."},
                            {"fr": "whereas", "ar": "فيما يخص / نظراً لأن", "example": "Whereas the parties wish to enter into this agreement, they hereby agree."},
                            {"fr": "therein", "ar": "في ذلك", "example": "The property referred to therein shall be valued by an independent surveyor."},
                            {"fr": "notwithstanding any other provision", "ar": "دون الإخلال بأي حكم آخر", "example": "Notwithstanding any other provision, this clause shall survive termination."},
                        ],
                    },
                    {
                        "id": "en_l2_u1_l2",
                        "title": "Legal Passive Voice and Impersonal Constructions",
                        "title_ar": "المبني للمجهول والصيغ غير الشخصية في القانون",
                        "subtitle": "How legal English avoids identifying actors",
                        "theory": (
                            "Legal English frequently employs the passive voice and impersonal"
                            "constructions. This is not merely a stylistic choice but serves important legal"
                            "functions: it shifts focus from who performs an action to the action itself, it"
                            "creates formality and objectivity, and it allows the law to apply universally"
                            "regardless of the specific actor.\n\nPassive constructions are extremely common"
                            "in legislation. For example, 'A person who commits an offence under this"
                            "section shall be liable to a fine not exceeding level five on the standard"
                            "scale.' The agent is identified but the focus is on the consequence. In many"
                            "cases, the agent is omitted entirely: 'The sum shall be paid within fourteen"
                            "days.'\n\nImpersonal constructions using 'it' are widely used in legal texts."
                            "'It is an offence to fail to comply with a notice served under this section.'"
                            "'It shall be the duty of the court to ensure that the welfare of the child is"
                            "safeguarded.' The expression 'there is' creates existence statements: 'There is"
                            "a rebuttable presumption that the child's welfare is served by contact with"
                            "both parents.'\n\nNominalisation is another hallmark of legal English, where"
                            "verbs are turned into nouns: 'consideration' from 'consider', 'determination'"
                            "from 'determine', 'notification' from 'notify'. This makes the language more"
                            "formal and abstract."
                        ),
                        "theory_ar": (
                            "يستخدم القانون الإنجليزي المبني للمجهول والصيغ غير الشخصية بشكل متكرر. هذا ليس"
                            "مجرد خيار أسلوبي بل يؤدي وظائف قانونية مهمة: ينقل التركيز من من يؤدي الفعل إلى"
                            "الفعل نفسه.\n\nتُستخدم البنى passive بشكل متكرر في التشريعات. الصيغ غير الشخصية"
                            "تُستخدم بشكل واسع مع it. التسمية (nominalisation) هي سمة أخرى للغة القانونية"
                            "الإنجليزية حيث تتحول الأفعال إلى أسماء."
                        ),
                        "vocab": [
                            {"fr": "shall be liable to", "ar": "يكون مسؤولاً عن", "example": "A person who commits an offence shall be liable to a fine."},
                            {"fr": "it is an offence to", "ar": "يُعتبر جريمة", "example": "It is an offence to fail to disclose relevant information."},
                            {"fr": "it shall be the duty of", "ar": "تكون واجباً على", "example": "It shall be the duty of every employer to ensure workplace safety."},
                            {"fr": "there is a presumption", "ar": "هناك فرضية", "example": "There is a presumption in favour of contact with both parents."},
                            {"fr": "shall be deemed to", "ar": "يعتبر", "example": "A document served by post shall be deemed to have been received."},
                            {"fr": "shall be taken to mean", "ar": "يعني", "example": "Property in this section shall be taken to mean any real estate."},
                            {"fr": "the sum shall be paid", "ar": "تُدفع المبلغ", "example": "The sum shall be paid within fourteen days of the judgment."},
                            {"fr": "shall apply notwithstanding", "ar": "تسري رغم", "example": "This provision shall apply notwithstanding any other provision herein."},
                            {"fr": "an offence is committed where", "ar": "تُرتكب جريمة حيث", "example": "An offence is committed where a person fails to register."},
                            {"fr": "notification shall be given", "ar": "تُ给出 إشعار", "example": "Notification shall be given in writing to the relevant authority."},
                        ],
                    },
                    {
                        "id": "en_l2_u1_l3",
                        "title": "Contract Law Vocabulary",
                        "title_ar": "مفردات قانون العقود",
                        "subtitle": "Essential terms for understanding contracts",
                        "theory": (
                            "Contract law is a fundamental area of English law that governs the creation and"
                            "enforcement of agreements between parties. A valid contract requires four"
                            "essential elements: offer, acceptance, consideration, and intention to create"
                            "legal relations.\n\nAn offer is a clear and definite proposal made by one party"
                            "to another. Acceptance is the unconditional agreement to all the terms of the"
                            "offer. Consideration is something of value exchanged between the parties,"
                            "meaning each party must give something or promise something in return.\n\nTerms"
                            "of a contract may be express (explicitly agreed) or implied (inferred by law,"
                            "custom, or the courts). Conditions are fundamental terms whose breach entitles"
                            "the innocent party to terminate the contract and claim damages. Warranties are"
                            "minor terms whose breach gives rise to damages only.\n\nRemedies for breach of"
                            "contract include damages (monetary compensation), specific performance (a court"
                            "order to perform the contract), injunctions, and rescission (setting aside the"
                            "contract). The duty of mitigation requires the innocent party to take"
                            "reasonable steps to minimise their loss.\n\nThe doctrine of privity means that"
                            "only parties to a contract can enforce its terms. This means that a third party"
                            "cannot sue on a contract to which they are not a party, even if the contract"
                            "was made for their benefit. However, the Contracts (Rights of Third Parties)"
                            "Act 1999 reformed this doctrine by allowing third parties to enforce terms that"
                            "expressly confer a benefit on them. Duress and undue influence are vitiating"
                            "factors that can render a contract voidable. Misrepresentation, whether"
                            "fraudulent, negligent, or innocent, provides the innocent party with a remedy"
                            "in damages or rescission. The implied terms incorporated by statute, such as"
                            "the Sale of Goods Act terms as to quality and fitness, provide additional"
                            "protection for contracting parties."
                        ),
                        "theory_ar": (
                            "قانون العقود هو مجال أساسي في القانون الإنجليزي يُنظّم تكوين وتنفيذ الاتفاقيات"
                            "بين الأطراف. يتطلب العقد الصالح أربعة عناصر أساسية: العرض والقبول والاعتبار"
                            "المادي ونية إنشاء علاقات قانونية.\n\nالعرض هو اقتراح واضح ودقيق. القبول هو"
                            "الموافقة غير المشروطة على جميع شروط العرض. الاعتبار المادي هو شيء ذي قيمة"
                            "يتبادل بين الأطراف.\n\nيمكن أن تكون شروط العقد صريحة أو ضمنية. الشروط الجوهرية"
                            "خللها يخول الطرف البريء إنهاء العقد والمطالبة بالتعويض.\n\nتشمل العلاجات"
                            "للإخلال بالعقد: التعويض والتنفيذ الجبري والأوامر القضائية والإبطال."
                        ),
                        "vocab": [
                            {"fr": "offer", "ar": "العرض", "example": "The offer must be clear, definite, and communicated to the offeree."},
                            {"fr": "acceptance", "ar": "القبول", "example": "Acceptance must be absolute and unqualified."},
                            {"fr": "consideration", "ar": "الاعتبار المادي", "example": "There must be valuable consideration for a contract to be enforceable."},
                            {"fr": "breach of contract", "ar": "الإخلال بالعقد", "example": "The breach of contract entitled the claimant to terminate the agreement."},
                            {"fr": "specific performance", "ar": "التنفيذ الجبري", "example": "The court ordered specific performance of the land sale agreement."},
                            {"fr": "injunction", "ar": "أمر قضائي", "example": "She sought an injunction to prevent the demolition of her property."},
                            {"fr": "damages", "ar": "التعويض", "example": "The measure of damages is the loss directly caused by the breach."},
                            {"fr": "rescission", "ar": "الإبطال", "example": "Rescission is available where there has been a misrepresentation."},
                            {"fr": "misrepresentation", "ar": "التمثيل الكاذب", "example": "The claimant alleged misrepresentation as a ground for rescission."},
                            {"fr": "frustration", "ar": "الإحباط", "example": "The doctrine of frustration discharged the contract when performance became impossible."},
                            {"fr": "mitigation", "ar": "خفض الأضرار", "example": "The claimant failed to take reasonable steps to mitigate their loss."},
                            {"fr": "terms and conditions", "ar": "الأحكام والشروط", "example": "The terms and conditions of the sale are set out in the schedule."},
                        ],
                    },
                    {
                        "id": "en_l2_u1_l4",
                        "title": "Tort Law and Negligence",
                        "title_ar": "قانون المسؤولية التقصيرية والإهمال",
                        "subtitle": "Civil wrongs and the duty of care",
                        "theory": (
                            "Tort law provides remedies for civil wrongs that cause harm or loss to"
                            "individuals. Unlike contract law, tort liability does not depend on any"
                            "agreement between the parties. The most common tort is negligence, which"
                            "requires the claimant to establish four elements.\n\nThe four elements of"
                            "negligence are: duty of care, breach of that duty, causation, and damage. The"
                            "duty of care was established in Donoghue v Stevenson [1932], where the House of"
                            "Lords held that a manufacturer owes a duty of care to the ultimate consumer."
                            "The test is the neighbour principle.\n\nBreach of duty is assessed by the"
                            "reasonable person test. The court considers the likelihood of harm, the"
                            "severity of harm, the cost of precautions, and the social utility of the"
                            "activity. Causation requires proof that the defendant's breach caused the"
                            "claimant's loss.\n\nOther important torts include: defamation (protecting"
                            "reputation), nuisance (unreasonable interference with the use of land),"
                            "trespass (unauthorized entry onto land), and occupiers' liability for injuries"
                            "to visitors.\n\nVicarious liability is an important aspect of tort law whereby"
                            "an employer is held liable for the torts of its employees committed in the"
                            "course of employment. This is a strict liability doctrine based on the policy"
                            "that the employer who profits from the employee's activities should bear the"
                            "risk of negligent conduct. The key test is whether there is a sufficient"
                            "connection between the employment and the wrongful act. Product liability under"
                            "the Consumer Protection Act 1987 makes manufacturers strictly liable for damage"
                            "caused by defective products. Defamation law protects reputation through the"
                            "torts of libel (permanent form) and slander (temporary form)."
                        ),
                        "theory_ar": (
                            "يوفّر قانون المسؤولية التقصيرية علاجات للإساءات المدنية التي تسبب ضرراً أو"
                            "خسارة للأفراد. أكثر التوصيلات شيوعاً هو الإهمال الذي يتطلب إثبات أربعة"
                            "عناصر.\n\nتشمل عناصر الإهمال: واجب العناية وخرق هذا الواجب والسببية والضرر. نشأ"
                            "واجب العناية في قضية Donoghue v Stevenson.\n\nيُقيّم خرق الواجب باختبار الشخص"
                            "المعقول. تشمل التوصيلات المدنية الأخرى: السمعة والأذى والتعدي ومسؤوليةoccupier."
                        ),
                        "vocab": [
                            {"fr": "tort", "ar": "المسؤولية التقصيرية", "example": "Tort law provides remedies for civil wrongs causing loss or damage."},
                            {"fr": "negligence", "ar": "الإهمال", "example": "The claimant alleged negligence in the design of the product."},
                            {"fr": "duty of care", "ar": "واجب العناية", "example": "The defendant owed a duty of care to the claimant."},
                            {"fr": "breach of duty", "ar": "خرق الواجب", "example": "The defendant was found to have breached the duty of care."},
                            {"fr": "causation", "ar": "السببية", "example": "The claimant must establish causation between the breach and the loss."},
                            {"fr": "remoteness of damage", "ar": "البعيد عن الضرر", "example": "The damage was too remote to be recoverable in law."},
                            {"fr": "reasonable foreseeability", "ar": "القابلية المعقولة للتنبؤ", "example": "The test of reasonable foreseeability determines whether a duty of care exists."},
                            {"fr": "defamation", "ar": "التشهير", "example": "The claimant brought an action in defamation against the newspaper."},
                            {"fr": "nuisance", "ar": "الأذى", "example": "The factory emissions constituted a private nuisance to neighbouring residents."},
                            {"fr": "trespass", "ar": "التعدي", "example": "Entering the property without permission constitutes trespass to land."},
                            {"fr": "occupiers' liability", "ar": "مسؤولية occupier", "example": "The occupiers liability act imposes a duty of care towards visitors."},
                            {"fr": "the reasonable person", "ar": "الشخص المعقول", "example": "The standard of care is that of the reasonable person in the circumstances."},
                        ],
                    },
                    {
                        "id": "en_l2_u1_l5",
                        "title": "Commercial Law Essentials",
                        "title_ar": "أسس القانون التجاري",
                        "subtitle": "Sales, agency and commercial transactions",
                        "theory": (
                            "Commercial law governs the rights, relations, and conduct of persons engaged in"
                            "commerce, trade, and sales. Key areas include the sale of goods, agency,"
                            "partnership, and company law.\n\nThe Sale of Goods Act 1979 implies certain"
                            "terms into contracts for the sale of goods: that the goods will be of"
                            "satisfactory quality, fit for their purpose, and match any sample or"
                            "description. The Consumer Rights Act 2015 provides additional protections for"
                            "consumers.\n\nAgency law governs the relationship between a principal and an"
                            "agent. An agent can bind the principal to contracts with third parties. The"
                            "authority of an agent can be express (specifically granted), implied, or"
                            "apparent (ostensible authority arising when a principal leads a third party to"
                            "believe that the agent has authority).\n\nPartnership is governed by the"
                            "Partnership Act 1890. A partnership is defined as the relation which subsists"
                            "between persons carrying on a business in common with a view to profit."
                            "Partners have joint and several liability for the debts of the"
                            "partnership.\n\nThe Sale of Goods Act 1979 implies that goods sold must conform"
                            "to any description and match any sample shown to the buyer. The buyer has the"
                            "right to reject goods that do not conform and to claim damages for any loss"
                            "suffered. The Consumer Rights Act 2015 strengthened consumer protection by"
                            "providing a thirty-day right to reject faulty goods and a right to a repair or"
                            "replacement. In agency law, the agent's authority can be actual (expressly or"
                            "impliedly granted by the principal) or apparent (created by the principal's"
                            "representations to a third party). The distinction between a partnership and a"
                            "limited company is significant for liability purposes, as partners have"
                            "unlimited personal liability while shareholders of limited companies enjoy"
                            "limited liability."
                        ),
                        "theory_ar": (
                            "يُنظّم القانون التجاري حقوق وعلاقات وسلوك الأشخاص العاملين في التجارة والبيع."
                            "تشمل المجالات الرئيسية بيع البضائع والوكالة والشراكة وقانون الشركات.\n\nيُلزم"
                            "قانون بيع البضائع 1979 بضمانات معينة. يوفر قانون حقوق المستهلك 2015 حماية"
                            "إضافية.\n\nيُنظّم قانون الوكالة العلاقة بين الموكل والوكيل. يمكن أن تكون صلاحية"
                            "الوكيل صريحة أو ضمنية أو ظاهرية.\n\nتُنظّم الشراكة قانون الشراكة 1890. يكون"
                            "الشركاء مسؤولين تضامنياً عن ديون الشراكة."
                        ),
                        "vocab": [
                            {"fr": "commercial law", "ar": "القانون التجاري", "example": "Commercial law governs trade and business transactions."},
                            {"fr": "sale of goods", "ar": "بيع البضائع", "example": "The Sale of Goods Act implies terms as to quality and fitness."},
                            {"fr": "satisfactory quality", "ar": "جودة مرضية", "example": "The goods must be of satisfactory quality under the Act."},
                            {"fr": "agency", "ar": "الوكالة", "example": "The law of agency governs the relationship between principal and agent."},
                            {"fr": "the principal", "ar": "الموكل", "example": "The principal is bound by contracts made by the agent."},
                            {"fr": "ostensible authority", "ar": "الصلاحية الظاهرية", "example": "The company was bound by the agent's apparent authority."},
                            {"fr": "partnership", "ar": "الشراكة", "example": "Partners have joint and several liability for partnership debts."},
                            {"fr": "joint and several liability", "ar": "المسؤولية التضامنية", "example": "Each partner has joint and several liability for the debts."},
                            {"fr": "consumer rights", "ar": "حقوق المستهلك", "example": "The Consumer Rights Act provides remedies for faulty goods."},
                            {"fr": "good faith", "ar": "الحسن النية", "example": "Commercial parties are expected to act in good faith."},
                            {"fr": "capacity to contract", "ar": "أهلية التعاقد", "example": "A person under eighteen lacks full capacity to contract."},
                            {"fr": "the bill of lading", "ar": "بوليصة الشحن", "example": "The bill of lading serves as evidence of the contract of carriage."},
                        ],
                    },
                    {
                        "id": "en_l2_u1_l6",
                        "title": "Administrative Law",
                        "title_ar": "القانون الإداري",
                        "subtitle": "Judicial review and the powers of government",
                        "theory": (
                            "Administrative law controls the exercise of power by government bodies and"
                            "public authorities. It ensures that decisions are made lawfully, fairly, and"
                            "within the scope of the authority granted by Parliament. Judicial review is the"
                            "primary mechanism for enforcing these principles.\n\nThe grounds for judicial"
                            "review are: illegality (the decision-maker acted without legal authority);"
                            "procedural impropriety (the decision-maker failed to follow fair procedures);"
                            "and irrationality or Wednesbury unreasonableness. A fourth ground,"
                            "proportionality, is increasingly used.\n\nThe ultra vires doctrine provides"
                            "that a public body can only act within the powers given to it by Parliament."
                            "Any action beyond those powers is void.\n\nThe remedies available include:"
                            "quashing orders (certiorari) to set aside unlawful decisions; mandatory orders"
                            "(mandamus) to compel a body to perform its duty; and prohibiting orders"
                            "(prohibition) to prevent a body from acting beyond its powers.\n\nThe grounds"
                            "of judicial review have been developed through case law, most notably in the"
                            "GCHQ case (1985) and Council of Civil Service Unions v Minister for the Civil"
                            "Service (1985). Proportionality has become an increasingly important ground,"
                            "particularly in human rights cases. The court will assess whether the decision"
                            "was a proportionate means of achieving a legitimate aim. The Equality Act 2010"
                            "also provides grounds for challenge where public bodies act in a discriminatory"
                            "manner. Standing to apply for judicial review has been liberalised and any"
                            "person with a sufficient interest may apply."
                        ),
                        "theory_ar": (
                            "يُنظّم القانون الإداري ممارسة السلطة من قبل الجهات الحكومية والسلطات العامة."
                            "يضمن أن القرارات تُتخذ بشكل قانوني ومنصف.\n\nتشمل أسباب الرقابة القضائية: عدم"
                            "الشرعية والخلل الإجرائي وعدم المعقولية.\n\nمبدأ ultra vires يوفر أن الجهة"
                            "العامة يمكنها فقط العمل ضمن الصلاحية الممنوحة لها.\n\nتشمل العلاجات المتاحة:"
                            "أوامر الإلغاء والأوامر الإلزامية وأوامر الحظر."
                        ),
                        "vocab": [
                            {"fr": "administrative law", "ar": "القانون الإداري", "example": "Administrative law controls the exercise of power by government bodies."},
                            {"fr": "judicial review", "ar": "الرقابة القضائية", "example": "Judicial review ensures that public bodies act within their legal powers."},
                            {"fr": "illegality", "ar": "العدم الشرعية", "example": "The decision was quashed on the ground of illegality."},
                            {"fr": "irrationality", "ar": "العبثية", "example": "The decision was found to be irrational and Wednesbury unreasonable."},
                            {"fr": "procedural impropriety", "ar": "الخلل الإجرائي", "example": "The decision was challenged on the basis of procedural impropriety."},
                            {"fr": "ultra vires", "ar": "تجاوز الصلاحية", "example": "The regulation was declared ultra vires as it exceeded statutory powers."},
                            {"fr": "quashing order", "ar": "أمر الإلغاء", "example": "The court granted a quashing order to set aside the unlawful decision."},
                            {"fr": "mandatory order", "ar": "أمر إلزامي", "example": "A mandatory order was issued to compel the authority to process the application."},
                            {"fr": "prohibiting order", "ar": "أمر حظري", "example": "The court issued a prohibiting order to prevent the authority from acting unlawfully."},
                            {"fr": "standing", "ar": "الصفة", "example": "The applicant must demonstrate sufficient standing to apply for judicial review."},
                            {"fr": "Wednesbury unreasonableness", "ar": "عدم معقولية Wednesbury", "example": "The decision was so unreasonable that no reasonable authority could have made it."},
                            {"fr": "public authority", "ar": "جهة عامة", "example": "The public authority must act in accordance with the enabling legislation."},
                        ],
                    },
                    {
                        "id": "en_l2_u1_l7",
                        "title": "Property Law",
                        "title_ar": "قانون الملكية",
                        "subtitle": "Real and personal property rights",
                        "theory": (
                            "Property law governs the ownership and use of land and other assets. English"
                            "property law distinguishes between real property (land and buildings) and"
                            "personal property (all other forms of property, including tangible and"
                            "intangible assets).\n\nThe key legislation governing land law is the Law of"
                            "Property Act 1925. Interests in land can be legal or equitable. Legal interests"
                            "include the fee simple absolute and the leasehold. Equitable interests include"
                            "beneficial interests under a trust.\n\nThe registration of title to land is"
                            "governed by the Land Registration Act 2002. Most land in England and Wales is"
                            "now registered at HM Land Registry. A charge (mortgage) over land must be"
                            "registered to take effect as a legal interest.\n\nEasements are rights over the"
                            "land of another, such as a right of way or a right of light. Covenants are"
                            "obligations that run with the land, binding future owners. A restrictive"
                            "covenant prevents the landowner from doing something on the land.\n\nBeneficial"
                            "interests under a trust arise where the legal title to property is held by"
                            "trustees for the benefit of beneficiaries. A resulting trust arises where the"
                            "beneficial interest returns to the settlor. A constructive trust is imposed by"
                            "the court to prevent unjust enrichment. The Landlord and Tenant Act 1954 gives"
                            "business tenants a statutory right to renew their lease. The Land Compensation"
                            "Act 1973 provides for compensation when land is compulsorily acquired by the"
                            "state. The planning system controls the development and use of land through the"
                            "grant of planning permission by local planning authorities."
                        ),
                        "theory_ar": (
                            "يُنظّم قانون الملكية ملكية واستخدام الأرض والأصول الأخرى. يُميّز قانون الملكية"
                            "البريطاني بين الملكية العقارية والملكية المنقولة.\n\nتشمل المصالح في الأرض"
                            "المصلحة القانونية وال equity. المصالح القانونية تشمل الملكية المطلقة"
                            "والإيجار.\n\nتُنظّم تسجيل ملكية الأرض قانون تسجيل الأرض 2002. يجب تسجيل الرهن"
                            "لأخذ الأثر القانوني.\n\nالservitudes هي حقوق فوق أرض الغير. العهود هي"
                            "الالتزامات تنتقل مع الأرض."
                        ),
                        "vocab": [
                            {"fr": "real property", "ar": "الملكية العقارية", "example": "Real property includes land and anything permanently attached to it."},
                            {"fr": "personal property", "ar": "الملكية المنقولة", "example": "Personal property includes all property other than land."},
                            {"fr": "fee simple", "ar": "الملكية المطلقة", "example": "The fee simple is the most complete form of ownership of land."},
                            {"fr": "leasehold", "ar": "حق الإيجار", "example": "The leasehold grants exclusive possession for a fixed term."},
                            {"fr": "freehold", "ar": "الملكية الحرة", "example": "The freehold interest in the property has been sold to the buyer."},
                            {"fr": "easement", "ar": "حق ارتفاق", "example": "The property benefits from an easement of way over the neighbouring land."},
                            {"fr": "covenant", "ar": "عهد / التزام عقاري", "example": "The restrictive covenant prevents the building of any commercial premises."},
                            {"fr": "conveyancing", "ar": "نقل الملكية", "example": "The conveyancing process typically takes between eight and twelve weeks."},
                            {"fr": "land registration", "ar": "تسجيل الأرض", "example": "Land registration provides certainty of title to the owner."},
                            {"fr": "mortgage", "ar": "رهن عقاري", "example": "The mortgage must be registered at the Land Registry to take effect."},
                            {"fr": "charge", "ar": "رهن", "example": "The bank registered a charge over the property as security for the loan."},
                            {"fr": "beneficial interest", "ar": "المصلحة النفعية", "example": "The beneficiary has a beneficial interest under the trust."},
                        ],
                    },
                    {
                        "id": "en_l2_u1_l8",
                        "title": "International Private Law",
                        "title_ar": "القانون الدولي الخاص",
                        "subtitle": "Cross-border disputes and choice of law",
                        "theory": (
                            "Private international law (also called conflict of laws) deals with disputes"
                            "that have a foreign element. It determines which country's law applies to a"
                            "dispute, which court has jurisdiction, and whether a foreign judgment will be"
                            "recognized and enforced.\n\nJurisdiction in civil and commercial matters was"
                            "previously governed by the Brussels I Regulation. After Brexit, the UK revived"
                            "the common law rules on jurisdiction.\n\nChoice of law rules determine which"
                            "law governs the substance of the dispute. For contracts, the Rome I Regulation"
                            "applies the law chosen by the parties. In the absence of a choice, the law of"
                            "the country most closely connected to the contract applies.\n\nRecognition and"
                            "enforcement of foreign judgments is governed by both domestic legislation and"
                            "international treaties. The common law rule requires the foreign judgment to be"
                            "for a definite sum, rendered by a court of competent jurisdiction, and final"
                            "and conclusive.\n\nService of court documents abroad is governed by"
                            "international conventions such as the Hague Service Convention. The recognition"
                            "of foreign court judgments at common law requires the judgment to be final, for"
                            "a definite sum, and rendered by a court of competent jurisdiction. The"
                            "Enforcement of Foreign Judgments Act 1933 provides a statutory framework for"
                            "the registration of judgments from countries that have reciprocal enforcement"
                            "arrangements with the UK. Anti-suit injunctions may be granted to prevent a"
                            "party from commencing or continuing proceedings in a foreign court where there"
                            "is an adequate alternative forum available."
                        ),
                        "theory_ar": (
                            "ي dealt القانون الدولي الخاص مع النزاعات التي لها عنصر أجنبي. يُحدد أي قانون"
                            "بلد ينطبق على النزاع وأي محكمة لها الاختصاص.\n\nتُنظّم الاختصاص اللائحة بروكسل"
                            "I previously. بعد Brexit، أعادت UK قواعد القانون المشترك.\n\nتُحدد قواعد اختيار"
                            "القانون أي قانون يحكم موضوع النزاع. للعقد، تُطبق اللائحة Rome I القانون الذي"
                            "يختاره الأطراف.\n\nيُنظّم الاعتراف بأحكام الأجانب والتنفيذ التشريعات الوطنية"
                            "والمعاهدات الدولية."
                        ),
                        "vocab": [
                            {"fr": "private international law", "ar": "القانون الدولي الخاص", "example": "Private international law determines which law applies to cross-border disputes."},
                            {"fr": "choice of law", "ar": "اختيار القانون", "example": "The parties may agree on the choice of law governing the contract."},
                            {"fr": "jurisdiction", "ar": "الاختصاص", "example": "The English courts have jurisdiction to hear this dispute."},
                            {"fr": "foreign judgment", "ar": "حكم أجنبي", "example": "The foreign judgment was recognized and enforced by the English court."},
                            {"fr": "conflict of laws", "ar": "تعارض القوانين", "example": "Conflict of laws rules determine the applicable law in cross-border cases."},
                            {"fr": "domicile", "ar": "الإقامة الدائمة", "example": "The defendant's domicile determines which court has jurisdiction."},
                            {"fr": "service abroad", "ar": "الخدمة خارج البلاد", "example": "Service abroad must comply with the requirements of the Hague Convention."},
                            {"fr": "the Rome I Regulation", "ar": "اللائحة روما الأولى", "example": "The Rome I Regulation governs the choice of law in contractual obligations."},
                            {"fr": "enforcement", "ar": "التنفيذ", "example": "The enforcement of the foreign arbitral award was granted by the court."},
                            {"fr": "public policy exception", "ar": "استثناء النظام العام", "example": "Recognition may be refused on grounds of public policy."},
                            {"fr": "reciprocity", "ar": "التبادلية", "example": "Enforcement may depend on reciprocity between the two states."},
                        ],
                    },
                    {
                        "id": "en_l2_u1_l9",
                        "title": "Remedies and Damages",
                        "title_ar": "العلاجات والتعويضات",
                        "subtitle": "Types of relief available in civil law",
                        "theory": (
                            "Remedies are the means by which a right is enforced or the violation of a right"
                            "is prevented, redressed, or compensated. Understanding the different types of"
                            "remedies available is essential for effective legal practice.\n\nDamages are"
                            "the most common remedy in civil law. They aim to put the claimant in the"
                            "position they would have been in had the contract been performed. Compensatory"
                            "damages compensate for actual loss. Expectation damages aim to put the claimant"
                            "in the position they expected to be in.\n\nConsequential damages compensate for"
                            "losses that flow naturally from the breach. Liquidated damages are a pre-agreed"
                            "sum specified in the contract. Punitive or exemplary damages go beyond"
                            "compensation to punish the defendant.\n\nEquitable remedies include: specific"
                            "performance, injunctions, and rescission. Equitable remedies are granted at the"
                            "discretion of the court and are subject to principles such as clean hands and"
                            "laches.\n\nThe court has discretion in awarding damages and may take into"
                            "account the conduct of the parties, including whether the claimant has failed"
                            "to mitigate their loss. The measure of damages depends on the type of claim. In"
                            "contract, damages are designed to put the innocent party in the position they"
                            "would have been in had the contract been performed. In tort, damages are"
                            "designed to put the claimant in the position they would have been in had the"
                            "tort not been committed. Interest on damages may be awarded under the Supreme"
                            "Court Act 1981 from the date of loss to the date of judgment."
                        ),
                        "theory_ar": (
                            "العلاجات هي الوسيلة التي تُفرض بها права أو تُمنع أو تُعوّض إساءة"
                            "حقوق.\n\nالتعويض هو العلاج الأكثر شيوعاً. يهدف إلى إعادة المدعي إلى المكان الذي"
                            "كان سيكون فيه لو نُفّذ العقد. تشمل التعويضات التصحيحية والتوقعية.\n\nتشمل"
                            "العلاجات equity: التنفيذ الجبري والأوامر القضائية والإبطال. تُمنح بموجب صلاحية"
                            "المحكمة.\n\nتُنقذ الأضرار غير المباشرة الخسائر الناتجة عن الإخلال. الأضرار"
                            "المتفق عليها مسبقاً هي مبلغ محدد في العقد."
                        ),
                        "vocab": [
                            {"fr": "damages", "ar": "التعويض", "example": "The court awarded compensatory damages for the loss suffered."},
                            {"fr": "compensatory damages", "ar": "التعويضات التصحيحية", "example": "Compensatory damages aim to put the claimant in the position before the breach."},
                            {"fr": "expectation damages", "ar": "تعويضات التوقع", "example": "Expectation damages reflect what the claimant expected to receive."},
                            {"fr": "consequential damages", "ar": "الأضرار غير المباشرة", "example": "The defendant argued that the consequential damages were too remote."},
                            {"fr": "liquidated damages", "ar": "التعويضات المتفق عليها", "example": "The contract specifies liquidated damages of five hundred pounds per day."},
                            {"fr": "punitive damages", "ar": "التعويضات التأديبية", "example": "Punitive damages may be awarded in cases of egregious conduct."},
                            {"fr": "specific performance", "ar": "التنفيذ الجبري", "example": "Specific performance was ordered as damages were an inadequate remedy."},
                            {"fr": "injunction", "ar": "أمر قضائي", "example": "An interim injunction was granted to prevent further publication."},
                            {"fr": "rescission", "ar": "الإبطال", "example": "The contract was rescinded on the ground of misrepresentation."},
                            {"fr": "equitable remedy", "ar": "علاج equity", "example": "Specific performance is an equitable remedy granted at the court's discretion."},
                            {"fr": "loss of bargain", "ar": "خسارة العقد", "example": "The measure of damages is the loss of bargain suffered by the claimant."},
                            {"fr": "mitigation of loss", "ar": "خفض الخسارة", "example": "The claimant has a duty to mitigate their loss after the breach."},
                        ],
                    },
                    {
                        "id": "en_l2_u1_l10",
                        "title": "Evidence and Burden of Proof",
                        "title_ar": "الدليل وعبء الإثبات",
                        "subtitle": "How facts are proved in legal proceedings",
                        "theory": (
                            "The law of evidence governs what facts may be proved in legal proceedings and"
                            "how they must be proved. It is fundamental to both criminal and civil"
                            "litigation.\n\nThe burden of proof refers to the obligation on a party to prove"
                            "their case. In criminal cases, the burden lies with the prosecution, who must"
                            "prove guilt beyond reasonable doubt. In civil cases, the burden lies with the"
                            "claimant, who must prove on the balance of probabilities.\n\nEvidence may be"
                            "oral (witness testimony), documentary (documents produced for inspection), or"
                            "real (physical objects). Hearsay evidence, which is an out-of-court statement"
                            "offered to prove the truth of its contents, is generally inadmissible in"
                            "criminal proceedings.\n\nCharacter evidence is generally inadmissible to prove"
                            "that a person acted in conformity with that character. Privilege protects"
                            "certain communications from being disclosed, such as legal professional"
                            "privilege (communications between a lawyer and client).\n\nThe rules on"
                            "admissibility of evidence are designed to ensure that only reliable and"
                            "relevant evidence is placed before the court. The bad character provisions of"
                            "the Criminal Justice Act 2003 allow evidence of a defendant's previous"
                            "convictions to be admitted in certain circumstances. The hearsay provisions in"
                            "the Criminal Justice Act 2003 and the Civil Evidence Act 1995 have liberalised"
                            "the rules on hearsay evidence. Expert evidence is governed by Part 35 of the"
                            "CPR and requires the court's permission. The expert owes a duty to the court"
                            "that overrides any duty to the party instructing them."
                        ),
                        "theory_ar": (
                            "يُنظّم قانون الدليل أي الحقائق يمكن إثباتها في الإجراءات القانونية وكيف يجب"
                            "إثباتها.\n\nعبء الإثبات هو الواجب على طرف لإثبات قضيته. في القضايا الجنائية،"
                            "العبء على الادعاء الذي يجب أن يثبت إدانة المدعى عليه فوق الشك المعقول.\n\nيمكن"
                            "أن يكون الدليل شفوياً أو وثائقياً أو حقيقياً. الدليل غير المباشر (Hearsay) هو"
                            "عادةً غير مقبول.\n\nال Privilege يحمي اتصالات معينة من الإفصاح مثل Privilege"
                            "المهني القانوني."
                        ),
                        "vocab": [
                            {"fr": "evidence", "ar": "الدليل", "example": "The evidence must be relevant to be admissible in court."},
                            {"fr": "burden of proof", "ar": "عبء الإثبات", "example": "The burden of proof lies with the party making the assertion."},
                            {"fr": "standard of proof", "ar": "معيار الإثبات", "example": "The standard of proof in criminal cases is beyond reasonable doubt."},
                            {"fr": "beyond reasonable doubt", "ar": "فوق الشك المعقول", "example": "The prosecution must prove the case beyond reasonable doubt."},
                            {"fr": "balance of probabilities", "ar": "الاحتمالات الأرجح", "example": "The civil standard of proof is the balance of probabilities."},
                            {"fr": "hearsay", "ar": "السمعة / الدليل غير المباشر", "example": "Hearsay evidence is generally inadmissible in criminal proceedings."},
                            {"fr": "witness testimony", "ar": "شهادة الشاهد", "example": "The witness testimony was the key piece of evidence in the trial."},
                            {"fr": "privileged communication", "ar": "اتصال محظور الإفصاح", "example": "Communications between a lawyer and client are privileged."},
                            {"fr": "admissibility", "ar": "القبولية", "example": "The admissibility of the evidence was challenged by the defence."},
                            {"fr": "corroboration", "ar": "التأييد / التوثيق", "example": "Scottish law requires corroboration of the essential facts."},
                            {"fr": "documentary evidence", "ar": "الدليل الوثائقي", "example": "Documentary evidence was produced to support the claim."},
                            {"fr": "character evidence", "ar": "دليل الشخصية", "example": "Character evidence is generally inadmissible to prove propensity."},
                        ],
                    },
                ],
            },
        ],
    },
    {
        "id": 3,
        "title": "Advanced — المتقدم",
        "description": "Legal drafting, research and specialized areas of law",
        "color": "#d97706",
        "units": [
            {
                "id": "en_l3_u1",
                "title": "Legal Practice and Specialized Law",
                "title_ar": "الممارسة القانونية والقانون المتخصص",
                "lessons": [
                    {
                        "id": "en_l3_u1_l1",
                        "title": "Reading Legislation",
                        "title_ar": "قراءة التشريعات",
                        "subtitle": "Interpreting and understanding Acts of Parliament",
                        "theory": (
                            "Reading and understanding legislation is a core skill for any legal"
                            "professional. Acts of Parliament are structured documents with specific"
                            "conventions that must be understood to apply the law correctly.\n\nThe"
                            "structure of an Act typically includes: long title (describing the purpose),"
                            "enacting formula, parts and sections (the main provisions), schedules (detailed"
                            "provisions appended to the Act), and commencement provisions (when the Act"
                            "comes into force).\n\nSections are the primary building blocks of legislation."
                            "Each section deals with a specific topic and is numbered sequentially."
                            "Subsections, paragraphs, and sub-paragraphs provide further detail."
                            "Cross-references between sections are common and must be followed.\n\nKey words"
                            "in legislation have specific legal meanings: 'shall' imposes an obligation;"
                            "'may' grants discretion; 'must' indicates a requirement; 'includes' is an"
                            "inclusive definition; 'means' is an exhaustive definition. 'Notwithstanding'"
                            "prevails over inconsistent provisions.\n\nThe interpretation of legislation is"
                            "guided by the presumption that Parliament does not intend to override"
                            "fundamental rights. Where legislation is capable of two meanings, the court"
                            "will prefer the interpretation that is compatible with Convention rights under"
                            "the Human Rights Act 1998. EU-derived legislation that remained in UK law after"
                            "Brexit continues to be interpreted in accordance with the principles of EU law"
                            "where consistent with the text. The court will also have regard to explanatory"
                            "notes published by the government alongside the Act, although these are not"
                            "legally binding."
                        ),
                        "theory_ar": (
                            "قراءة التشريعات وفهمها هو مهارة أساسية لأي محامٍ. Acts of Parliament هي مستندات"
                            "منظمة باتفاقيات محددة.\n\nيحتوي القانون عادةً على: العنوان الطويل وصيغة السن"
                            "والأقسام والمواد والجداول.\n\nتُعد المواد اللبنات الأساسية للتشريعات. تشمل"
                            "المصطلحات الرئيسية: shall يفرض التزاماً؛ may يمنح صلاحية؛ must يشترط شرطاً؛"
                            "includes تعريف شامل؛ means تعريف حصرية."
                        ),
                        "vocab": [
                            {"fr": "section", "ar": "مادة / فقرة", "example": "Section 1 of the Act defines the key terms used throughout."},
                            {"fr": "subsection", "ar": "البند الفرعي", "example": "Subsection 2 provides an exception to the general rule."},
                            {"fr": "schedule", "ar": "الجدول", "example": "The details are set out in Schedule 1 to the Act."},
                            {"fr": "commencement", "ar": "الEntry into force", "example": "The Act came into force on the first of October 2023."},
                            {"fr": "repeal", "ar": "الإلغاء", "example": "The 1985 Act was repealed by the new legislation."},
                            {"fr": "amendment", "ar": "التعديل", "example": "The Act was amended to include new provisions on data protection."},
                            {"fr": "enacting formula", "ar": "صيغة التشريع", "example": "The enacting formula states that the Act is enacted by the Crown."},
                            {"fr": "long title", "ar": "العنوان الطويل", "example": "The long title describes the purpose and scope of the Act."},
                            {"fr": "interpretation section", "ar": "مادة التفسير", "example": "The interpretation section defines terms used in the Act."},
                            {"fr": "subordinate legislation", "ar": "التشريعات الفرعية", "example": "Subordinate legislation is made under powers granted by the Act."},
                            {"fr": "in force", "ar": "نافذ / ساري المفعول", "example": "The provisions of the Act are not yet in force."},
                        ],
                    },
                    {
                        "id": "en_l3_u1_l2",
                        "title": "Statutory Interpretation",
                        "title_ar": "التفسير التشريعي",
                        "subtitle": "How courts interpret and apply legislation",
                        "theory": (
                            "Statutory interpretation is the process by which courts interpret and apply"
                            "legislation. When the meaning of a statute is unclear or ambiguous, courts must"
                            "determine the intended meaning using established principles.\n\nThe three main"
                            "approaches to statutory interpretation are: the literal rule (the words are"
                            "given their ordinary meaning); the golden rule (the ordinary meaning is applied"
                            "unless it leads to an absurdity); and the mischief rule (the court considers"
                            "the problem the statute was intended to remedy).\n\nThe purposive approach,"
                            "increasingly favoured by courts, looks at the purpose behind the legislation"
                            "rather than merely the literal meaning of the words.\n\nRules of interpretation"
                            "include: the expressio unius rule (the expression of one thing implies the"
                            "exclusion of others); the eiusdem generis rule (general words following"
                            "specific words are limited to the same class); and the contemporanea exposito"
                            "rule (words should be interpreted according to their meaning at the time the"
                            "statute was enacted).\n\nThe European Court of Human Rights has adopted a"
                            "purposive approach to the interpretation of the Convention. The domestic courts"
                            "increasingly follow this approach, particularly when interpreting the Human"
                            "Rights Act 1998. The Supreme Court in R (on the application of SK) v Secretary"
                            "of State for Work and Pensions [2015] endorsed a holistic, Article 14-compliant"
                            "approach to statutory interpretation. Reference materials such as Hansard"
                            "(parliamentary debates) may be considered by the court when determining the"
                            "background to the legislation, following Pepper v Hart [1993]."
                        ),
                        "theory_ar": (
                            "التفسير التشريعي هو العملية التي تُفسّر بها المحاكم التشريعات"
                            "وتُطبّقها.\n\nتشمل المقاربات الثلاث الرئيسية: القاعدة الحرفية والقاعدة الذهبية"
                            "والقاعدة الهادفة.\n\nالمنهج الت purposeي ينظر إلى الغرض من التشريع بدلاً من"
                            "المعنى الحرفي للكلمات فقط.\n\nتشمل قواعد التفسير: expressio unius وeiusdem"
                            "generis وcontemporanea exposito."
                        ),
                        "vocab": [
                            {"fr": "statutory interpretation", "ar": "التفسير التشريعي", "example": "Statutory interpretation is the process by which courts construe legislation."},
                            {"fr": "the literal rule", "ar": "القاعدة الحرفية", "example": "Under the literal rule, words are given their ordinary meaning."},
                            {"fr": "the golden rule", "ar": "القاعدة الذهبية", "example": "The golden rule allows a departure from the ordinary meaning to avoid absurdity."},
                            {"fr": "the mischief rule", "ar": "القاعدة الهادفة", "example": "The mischief rule considers the problem the statute was intended to remedy."},
                            {"fr": "purposive approach", "ar": "المنهج الت purposeي", "example": "The purposive approach looks at the purpose behind the legislation."},
                            {"fr": "expressio unius", "ar": "التعبير عن واحد", "example": "The expressio unius rule implies that the enumeration of one thing excludes others."},
                            {"fr": "eiusdem generis", "ar": "من نفس النوع", "example": "Under the eiusdem generis rule, general words are limited by the specific words."},
                            {"fr": "ambiguity", "ar": "الغموض", "example": "Where there is ambiguity, the court must determine the true meaning."},
                            {"fr": "parliamentary intent", "ar": "نية البرلمان", "example": "The court sought to ascertain the parliamentary intent behind the provision."},
                            {"fr": "plain meaning", "ar": "المعنى الواضح", "example": "The words should be given their plain and ordinary meaning."},
                        ],
                    },
                    {
                        "id": "en_l3_u1_l3",
                        "title": "Legal Drafting",
                        "title_ar": "التصياغة القانونية",
                        "subtitle": "Writing clear and effective legal documents",
                        "theory": (
                            "Legal drafting is the art of producing legal documents that are clear, precise,"
                            "and effective. Good drafting requires a thorough understanding of the law and"
                            "the ability to express complex legal concepts in accessible language.\n\nThe"
                            "structure of a legal document typically includes: a preamble identifying the"
                            "parties and the date; recitals setting out the background and purpose;"
                            "definitions of key terms; operative clauses setting out the main obligations"
                            "and rights; schedules; and execution clauses.\n\nPrinciples of good legal"
                            "drafting include: use plain English where possible; define key terms at the"
                            "beginning; use consistent terminology; avoid archaic words such as hereinafter,"
                            "whereas, and aforesaid; use short sentences and the active voice;"
                            "cross-reference rather than repeat.\n\nCommon drafting patterns include: 'The"
                            "Party shall...' (imposing an obligation); 'The Party may...' (granting a"
                            "discretion); 'The Party shall not...' (imposing a prohibition); 'In the event"
                            "that...' (creating a condition); 'For the avoidance of doubt...'; and 'Without"
                            "prejudice to...' (preserving rights).\n\nModern legal drafting favours plain"
                            "English over traditional legal jargon. The Law Commission has recommended the"
                            "use of plain language in legislation. Drafters should avoid unnecessary"
                            "complexity, use active voice where possible, and structure documents logically."
                            "The use of defined terms improves clarity and reduces the risk of ambiguity."
                            "Schedules and annexes can be used to supplement the main body of the document"
                            "without cluttering it with detail. Each clause should deal with a single topic"
                            "and be expressed as clearly and concisely as possible."
                        ),
                        "theory_ar": (
                            "التصياغة القانونية هي فن إنتاج مستندات قانونية واضحة ودقيقة وفعالة. تتطلب"
                            "الكتابة الجيدة فهماً عميقاً للقانون.\n\nتتضمن بنية المستند القانوني: ترويسة"
                            "وسرد الخلفية والتعريفات والمادات التشغيلة والجداول.\n\nتشمل مبادئ الكتابة"
                            "القانونية الجيدة: استخدام الإنجليزية البسيطة وتعريف المصطلحات الرئيسية واستخدام"
                            "مصطلحات متسقة وتجنب الكلمات القديمة.\n\nتشمل أنماط التصيغة الشائعة: The Party"
                            "shall (التزام) و The Party may (صلاة) و The Party shall not (تحريم) و In the"
                            "event that (شرط) و For the avoidance of doubt (توضيح) و Without prejudice to"
                            "(حفظ الحقوق)."
                        ),
                        "vocab": [
                            {"fr": "the preamble", "ar": "الترويسة", "example": "The preamble identifies the parties to the agreement."},
                            {"fr": "the operative clause", "ar": "المادة التشغيلة", "example": "The operative clause sets out the main obligations of each party."},
                            {"fr": "the definition clause", "ar": "المادة التعريفية", "example": "In this agreement, Property is defined in the definition clause."},
                            {"fr": "for the avoidance of doubt", "ar": "لتجنب أي شك", "example": "For the avoidance of doubt, this clause survives termination."},
                            {"fr": "without prejudice to", "ar": "دون الإخلال بـ", "example": "Without prejudice to any other rights, the seller may terminate."},
                            {"fr": "in the event that", "ar": "في حالة", "example": "In the event that the buyer defaults, the seller may rescind."},
                            {"fr": "hereunder", "ar": "في هذا العقد", "example": "The obligations hereunder are binding on both parties."},
                            {"fr": "indemnify", "ar": "يُعوّض", "example": "The seller shall indemnify the buyer against all losses and claims."},
                            {"fr": "warrant and represent", "ar": "يُؤكد ويُصرّح", "example": "The seller warrants and represents that it has full title to the property."},
                            {"fr": "force majeure", "ar": "القوة القاهرة", "example": "Neither party shall be liable for delay caused by force majeure."},
                            {"fr": "severability", "ar": "الانفصال", "example": "If any clause is found invalid, the severability clause preserves the rest."},
                            {"fr": "governing law", "ar": "القانون الحاكم", "example": "The governing law of this agreement shall be the law of England and Wales."},
                        ],
                    },
                    {
                        "id": "en_l3_u1_l4",
                        "title": "Conveyancing and Documentation",
                        "title_ar": "نقل الملكية والتوثيق",
                        "subtitle": "Transferring property ownership legally",
                        "theory": (
                            "Conveyancing is the legal process of transferring property ownership from one"
                            "person to another. It involves a series of steps that must be carefully managed"
                            "to ensure a valid and effective transfer.\n\nThe conveyancing process begins"
                            "with pre-contract enquiries, where the buyer's solicitor raises questions about"
                            "the property. Searches are conducted, including local authority searches,"
                            "environmental searches, and water and drainage searches.\n\nThe contract for"
                            "sale is then exchanged, at which point both parties become legally committed. A"
                            "completion date is agreed, usually between one and three weeks after exchange."
                            "On completion, the balance of the purchase price is paid and the transfer"
                            "document is executed.\n\nAfter completion, the buyer's solicitor arranges"
                            "registration at HM Land Registry. Stamp duty land tax must be paid within"
                            "fourteen days of completion.\n\nAfter completion, the buyer becomes the legal"
                            "owner of the property and assumes responsibility for all outgoings including"
                            "council tax, utility bills, and ground rent where applicable. The seller's"
                            "solicitor must ensure that all encumbrances on the title are discharged prior"
                            "to or at completion. Leasehold conveyancing involves additional considerations"
                            "such as the terms of the lease, service charges, and the need for consent from"
                            "the freeholder or management company. The electronic communications network and"
                            "sewerage agreements may affect the property and should be investigated during"
                            "the conveyancing process."
                        ),
                        "theory_ar": (
                            "نقل الملكية هو العملية القانونية لنقل ملكية العقار من شخص إلى آخر. تتضمن سلسلة"
                            "من الخطوات.\n\nتبدأ العملية بأسئلة ما قبل العقد. تُجرى بحثات تشمل بحثات السلطة"
                            "المحلية والبيئية.\n\nيُتبادل عقد البيع ثم يتفق على تاريخ التسليم. عند التسليم،"
                            "يُدفع رصيد ثمن الشراء ويُنفّذ مستند النقل.\n\nبعد التسليم، يُرتب المحامي"
                            "التسجيل في سجل الأراضي ويُدفع ضريبة الأراضي."
                        ),
                        "vocab": [
                            {"fr": "conveyancing", "ar": "نقل الملكية", "example": "Conveyancing is the legal process of transferring property ownership."},
                            {"fr": "exchange of contracts", "ar": "تبادل العقود", "example": "Exchange of contracts commits both parties to the transaction."},
                            {"fr": "completion", "ar": "التسليم", "example": "Completion is scheduled for the fifteenth of next month."},
                            {"fr": "title deeds", "ar": "وثائق الملكية", "example": "The title deeds must be provided to the buyer's solicitor."},
                            {"fr": "land registry", "ar": "سجل الأراضي", "example": "The transfer must be registered at HM Land Registry."},
                            {"fr": "stamp duty", "ar": "ضريبة الطوابع", "example": "Stamp duty land tax must be paid within fourteen days of completion."},
                            {"fr": "pre-contract enquiries", "ar": "أسئلة ما قبل العقد", "example": "The buyer's solicitor raised pre-contract enquiries about the property."},
                            {"fr": "searches", "ar": "البحثات", "example": "Local authority searches revealed no outstanding planning issues."},
                            {"fr": "transfer document", "ar": "مستند النقل", "example": "The transfer document must be executed by both parties."},
                            {"fr": "completion statement", "ar": "بيان التسليم", "example": "The completion statement sets out the final amounts payable."},
                            {"fr": "fixed charge", "ar": "رهن ثابت", "example": "The bank holds a fixed charge over the property."},
                            {"fr": "caveat emptor", "ar": "ليحذر المشتري", "example": "Under caveat emptor, the buyer must satisfy themselves as to the condition of the property."},
                        ],
                    },
                    {
                        "id": "en_l3_u1_l5",
                        "title": "Legal Research Methods",
                        "title_ar": "مناهج البحث القانوني",
                        "subtitle": "Finding and using legal authorities effectively",
                        "theory": (
                            "Legal research is the process of identifying and retrieving legal information"
                            "relevant to a particular issue or question. Effective legal research requires"
                            "both knowledge of the sources available and the methodology to use them"
                            "efficiently.\n\nPrimary sources of law include: Acts of Parliament (available"
                            "on legislation.gov.uk); statutory instruments; case law reports; and EU law"
                            "sources.\n\nSecondary sources include: legal textbooks and commentaries; legal"
                            "journals such as the Law Quarterly Review; Halsbury's Laws of England; and"
                            "looseleaf services providing current awareness.\n\nElectronic legal research"
                            "has transformed the way lawyers find information. Key databases include:"
                            "Westlaw UK, LexisNexis, BAILII, and the official legislation website. Effective"
                            "research requires formulating a clear research question, identifying relevant"
                            "keywords, selecting appropriate sources, evaluating the results, and"
                            "synthesising the findings into a coherent legal analysis.\n\nEffective legal"
                            "research requires an understanding of the hierarchy of sources and the weight"
                            "to be given to each. Primary legislation is the highest authority, followed by"
                            "secondary legislation and then case law. Academic commentary and textbooks are"
                            "persuasive rather than binding. The researcher must evaluate the currency and"
                            "relevance of each source. Research should be systematic and well-documented,"
                            "with clear records of the sources consulted and the conclusions reached. Time"
                            "management is essential in legal research, as deadlines must be met and"
                            "resources allocated efficiently."
                        ),
                        "theory_ar": (
                            "البحث القانوني هو عملية تحديد واسترجاع المعلومات القانونية ذات الصلة بمسألة"
                            "محددة.\n\nتشمل المصادر الأولية: Acts of Parliament وstatutory instruments وcase"
                            "law reports.\n\nتشمل المصادر الثانوية: الكتب القانونية والمجلات القانونية"
                            "وHalsbury's Laws of England.\n\nالبحث القانوني الإلكتروني غيّر طريقة العثور"
                            "المحامين على المعلومات. تشمل قواعد البيانات الرئيسية: Westlaw UK وLexisNexis"
                            "وBAILII."
                        ),
                        "vocab": [
                            {"fr": "legal research", "ar": "البحث القانوني", "example": "Effective legal research is essential for building a strong case."},
                            {"fr": "primary sources", "ar": "المصادر الأولية", "example": "Acts of Parliament and case law are primary sources of law."},
                            {"fr": "secondary sources", "ar": "المصادر الثانوية", "example": "Textbooks and legal journals are secondary sources of law."},
                            {"fr": "law reports", "ar": "تقارير القضايا", "example": "The decision is reported in the All England Law Reports."},
                            {"fr": "statutory instruments", "ar": "الأدوات التشريعية", "example": "Statutory instruments are a form of delegated legislation."},
                            {"fr": "case law", "ar": "قانون القضايا", "example": "Case law provides authoritative statements of legal principles."},
                            {"fr": "legal database", "ar": "قاعدة البيانات القانونية", "example": "Westlaw UK is a comprehensive legal database for case law research."},
                            {"fr": "keyword search", "ar": "بحث بالكلمات المفتاحية", "example": "A keyword search of the legislation revealed the relevant provision."},
                            {"fr": "authority", "ar": "سلطة قضائية", "example": "This case is the leading authority on the issue of misrepresentation."},
                            {"fr": "digest", "ar": "ملخص", "example": "The law digest provides a convenient summary of the relevant principles."},
                            {"fr": "current awareness", "ar": "الوعي بالمستجدات", "example": "Regular current awareness updates are essential for legal practice."},
                        ],
                    },
                    {
                        "id": "en_l3_u1_l6",
                        "title": "Alternative Dispute Resolution",
                        "title_ar": "وسائل تسوية النزاعات البديلة",
                        "subtitle": "Resolving disputes outside the courtroom",
                        "theory": (
                            "Alternative dispute resolution (ADR) refers to methods of resolving disputes"
                            "without going to trial. ADR has become increasingly important in English law,"
                            "and courts now actively encourage parties to consider ADR.\n\nMediation is the"
                            "most common form of ADR. It involves a neutral third party who helps the"
                            "parties reach a mutually acceptable settlement. Mediation is confidential and"
                            "without prejudice.\n\nArbitration is a more formal process where an independent"
                            "arbitrator makes a binding decision. The Arbitration Act 1996 governs"
                            "arbitration in England and Wales. Arbitration awards are enforceable in the"
                            "same way as court judgments.\n\nExpert determination involves the appointment"
                            "of an independent expert to resolve a technical dispute. Conciliation is"
                            "similar to mediation but the conciliator may put forward proposals for"
                            "settlement. Early neutral evaluation involves an independent third party"
                            "providing an assessment of the strengths and weaknesses of each party's"
                            "case.\n\nThe courts have indicated that unreasonable refusal to engage in ADR"
                            "may result in costs sanctions. In Halsey v Milton Keynes General NHS Trust"
                            "[2011], the Court of Appeal held that while courts cannot compel parties to"
                            "mediate, unreasonable refusal to do so may be taken into account when awarding"
                            "costs. Mediation agreements are enforceable as contracts. Arbitration"
                            "agreements must comply with the requirements of section 5 of the Arbitration"
                            "Act 1996. The court has limited supervisory jurisdiction over arbitration"
                            "proceedings, including the power to remove an arbitrator for serious"
                            "irregularity and to challenge an award on a point of law."
                        ),
                        "theory_ar": (
                            "تشير وسائل تسوية النزاعات البديلة (ADR) إلى طرق تسوية النزاعات دون محاكمة."
                            "أصبحت ADR أهمية متزايدة في القانون الإنجليزي.\n\nالوساطة هي الشكل الأكثر شيوعاً"
                            "لـ ADR. تتضمن طرفياً محايداً يساعد الأطراف على التوصل إلى تسوية.\n\nالتحكيم هو"
                            "عملية أكثر رسمية حيث يتخذ arbitrator قراراً ملزماً. أحكام التحكيم قابلة للتنفيذ"
                            "بنفس الطريقة مثل أحكام المحاكم.\n\nيشمل التحديد الخبير تعيين خبير مستقل لحل"
                            "نزاع فني."
                        ),
                        "vocab": [
                            {"fr": "alternative dispute resolution", "ar": "وسائل تسوية النزاعات البديلة", "example": "ADR provides a faster and more cost-effective way to resolve disputes."},
                            {"fr": "mediation", "ar": "الوساطة", "example": "The court ordered the parties to attempt mediation before trial."},
                            {"fr": "arbitration", "ar": "التحكيم", "example": "The dispute was referred to arbitration under the Arbitration Act."},
                            {"fr": "arbitrator", "ar": "المحكم", "example": "The arbitrator issued a binding award on all issues."},
                            {"fr": "mediator", "ar": "الوسّاط", "example": "The mediator helped the parties reach a settlement agreement."},
                            {"fr": "settlement", "ar": "تسوية", "example": "The parties reached a settlement before the trial commenced."},
                            {"fr": "without prejudice", "ar": "دون ضرر", "example": "The mediation discussions were conducted on a without prejudice basis."},
                            {"fr": "arbitration award", "ar": "حكم التحكيم", "example": "The arbitration award is final and binding on both parties."},
                            {"fr": "expert determination", "ar": "التحديد الخبير", "example": "The technical dispute was referred to expert determination."},
                            {"fr": "conciliation", "ar": "التوسط", "example": "The conciliator put forward proposals for settlement to both parties."},
                            {"fr": "early neutral evaluation", "ar": "التقييم المحايد المبكر", "example": "Early neutral evaluation helped the parties assess the strength of their cases."},
                        ],
                    },
                    {
                        "id": "en_l3_u1_l7",
                        "title": "Human Rights Law",
                        "title_ar": "قانون حقوق الإنسان",
                        "subtitle": "Fundamental rights and freedoms",
                        "theory": (
                            "Human rights law protects the fundamental rights and freedoms of individuals"
                            "against abuse by the state. In the United Kingdom, the principal human rights"
                            "legislation is the Human Rights Act 1998, which incorporated the European"
                            "Convention on Human Rights (ECHR) into domestic law.\n\nKey rights protected"
                            "under the ECHR include: the right to life (Article 2); the prohibition of"
                            "torture and inhuman treatment (Article 3); the right to liberty and security"
                            "(Article 5); the right to a fair trial (Article 6); the right to respect for"
                            "private and family life (Article 8); freedom of expression (Article 10); and"
                            "freedom of assembly and association (Article 11).\n\nThe Human Rights Act"
                            "requires all public authorities to act compatibly with Convention rights."
                            "Courts must, so far as it is possible, interpret legislation compatibly with"
                            "Convention rights. If legislation cannot be read compatibly, courts may issue a"
                            "declaration of incompatibility.\n\nThe rights under the ECHR are not absolute."
                            "They may be subject to limitations that are prescribed by law and necessary in"
                            "a democratic society.\n\nThe ECHR rights are qualified, meaning they can be"
                            "limited where such limitation is prescribed by law, necessary in a democratic"
                            "society, and proportionate to the legitimate aim pursued. The courts apply a"
                            "balancing exercise under Article 10(2) when assessing whether a restriction on"
                            "freedom of expression is justified. The Equality Act 2010, while not part of"
                            "the ECHR framework, works alongside it to provide comprehensive protection"
                            "against discrimination. The UK's membership of the Council of Europe created"
                            "obligations under the ECHR, and the Human Rights Act 1998 gave domestic effect"
                            "to these obligations."
                        ),
                        "theory_ar": (
                            "يحمي قانون حقوق الإنسان الحقوق والحريات الأساسية للأفراد ضد إساءة استخدام"
                            "الدولة. التشريع الرئيسي هو قانون حقوق الإنسان 1998 الذي دمج الاتفاقية الأوروبية"
                            "لحقوق الإنسان في القانون المحلي.\n\nتشمل الحقوق الرئيسية: الحق في الحياة"
                            "(المادة 2) والحظر التعذيب (المادة 3) والمحاكمة العادلة (المادة 6) والحق في"
                            "الخصوصية (المادة 8) وحرية التعبير (المادة 10).\n\nيتطلب قانون حقوق الإنسان 1998"
                            "من جميع السلطات العامة العمل بشكل متوافق مع حقوق الاتفاقية.\n\nليست الحقوق تحت"
                            "الاتفاقية مطلقة. يمكن خضوعها لقيد مشروط بالقانون وضروري في مجتمع ديمقراطي."
                        ),
                        "vocab": [
                            {"fr": "human rights", "ar": "حقوق الإنسان", "example": "The Human Rights Act protects fundamental rights and freedoms."},
                            {"fr": "the European Convention on Human Rights", "ar": "الاتفاقية الأوروبية لحقوق الإنسان", "example": "The ECHR sets out the fundamental rights that must be protected."},
                            {"fr": "Convention rights", "ar": "حقوق الاتفاقية", "example": "Public authorities must act compatibly with Convention rights."},
                            {"fr": "right to life", "ar": "الحق في الحياة", "example": "Article 2 of the Convention protects the right to life."},
                            {"fr": "right to a fair trial", "ar": "الحق في محاكمة عادلة", "example": "The right to a fair trial is protected under Article 6."},
                            {"fr": "right to privacy", "ar": "الحق في الخصوصية", "example": "Article 8 protects the right to respect for private and family life."},
                            {"fr": "freedom of expression", "ar": "حرية التعبير", "example": "Freedom of expression is protected under Article 10 of the Convention."},
                            {"fr": "declaration of incompatibility", "ar": "إعلان عدم التوافق", "example": "The court issued a declaration of incompatibility with the Human Rights Act."},
                            {"fr": "proportionality", "ar": "التناسب", "example": "Any restriction on a right must satisfy the test of proportionality."},
                            {"fr": "limitation", "ar": "تقييد", "example": "Rights may be subject to limitations prescribed by law."},
                            {"fr": "public authority", "ar": "جهة عامة", "example": "A public authority must not act in a way incompatible with Convention rights."},
                        ],
                    },
                    {
                        "id": "en_l3_u1_l8",
                        "title": "Corporate Law",
                        "title_ar": "قانون الشركات",
                        "subtitle": "Company formation, governance and liability",
                        "theory": (
                            "Corporate law governs the formation, management, and dissolution of companies."
                            "In England and Wales, the principal legislation is the Companies Act 2006.\n\nA"
                            "company is a separate legal entity from its members, established in Salomon v A"
                            "Salomon & Co Ltd [1897]. This means the company can own property, enter"
                            "contracts, sue and be sued in its own name. Shareholder liability is generally"
                            "limited to the amount unpaid on their shares.\n\nCompanies may be private (Ltd)"
                            "or public (plc). Private companies cannot offer shares to the public and have a"
                            "minimum of one member. Public companies can offer shares to the public and must"
                            "have at least two shareholders.\n\nDirectors owe duties under sections 171 to"
                            "177 of the Companies Act 2006, including the duty to act within powers, promote"
                            "the success of the company, exercise independent judgment, and avoid conflicts"
                            "of interest.\n\nThe Companies Act 2006 introduced a statutory code of"
                            "directors' duties in sections 171 to 177, which codified the common law and"
                            "equitable duties. Directors must declare any interest in a proposed"
                            "transaction. Related party transactions must be approved by the shareholders."
                            "The court may grant relief to a director who has acted honestly and reasonably"
                            "under section 1157 of the Act. Insolvency law intersects with company law when"
                            "a company is unable to pay its debts, triggering potentially wrongful or"
                            "fraudulent trading provisions."
                        ),
                        "theory_ar": (
                            "يُنظّم قانون الشركات تكوين وإدارة وتصفية الشركات. القانون الرئيسي هو قانون"
                            "الشركات 2006.\n\nالشركة كيان قانوني منفصل عن أعضائها، وهو مبدأ ترسّخ في قضية"
                            "Salomon v A Salomon & Co Ltd.\n\nيمكن أن تكون الشركات خاصة أو عامة. الشركات"
                            "الخاصة لا يمكنها عرض أسهمها للعامة.\n\nيُلزم المديرون بالواجبات بموجب أقسام 171"
                            "إلى 177 من قانون الشركات 2006."
                        ),
                        "vocab": [
                            {"fr": "company", "ar": "شركة", "example": "A company is a separate legal entity from its members."},
                            {"fr": "Articles of Association", "ar": "عقد التأسيس", "example": "The Articles of Association govern the internal management of the company."},
                            {"fr": "shareholder", "ar": "مساهم", "example": "The shareholders voted to approve the annual accounts."},
                            {"fr": "director", "ar": "مدير", "example": "Directors owe fiduciary duties to the company."},
                            {"fr": "board of directors", "ar": "مجلس الإدارة", "example": "The board of directors met to consider the proposed acquisition."},
                            {"fr": "limited liability", "ar": "المسؤولية المحدودة", "example": "The shareholders enjoy limited liability for the company's debts."},
                            {"fr": "memorandum of association", "ar": "عقد التأسيس", "example": "The memorandum of association is filed with the Registrar of Companies."},
                            {"fr": "annual return", "ar": "الإقرار السنوي", "example": "The company must file an annual return with Companies House."},
                            {"fr": "winding up", "ar": "تصفية الشركة", "example": "The company was wound up due to insolvency."},
                            {"fr": "fiduciary duty", "ar": "الواجب الائتماني", "example": "Directors must act in accordance with their fiduciary duties."},
                            {"fr": "ultra vires", "ar": "تجاوز الصلاحية", "example": "An act beyond the company's Objects Clause is ultra vires."},
                            {"fr": "share capital", "ar": "رأس المال المدفوع", "example": "The public company must have an issued share capital of at least fifty thousand pounds."},
                        ],
                    },
                    {
                        "id": "en_l3_u1_l9",
                        "title": "Intellectual Property Law",
                        "title_ar": "قانون الملكية الفكرية",
                        "subtitle": "Protecting creations of the mind",
                        "theory": (
                            "Intellectual property (IP) law protects creations of the mind, including"
                            "inventions, literary and artistic works, designs, symbols, and names used in"
                            "commerce. IP rights are generally territorial.\n\nPatents protect inventions"
                            "for a limited period (usually twenty years). The invention must be new, involve"
                            "an inventive step, and be capable of industrial application. The Patents Act"
                            "1977 governs patent law in the UK.\n\nCopyright protects original literary,"
                            "dramatic, musical, and artistic works, as well as sound recordings, films,"
                            "broadcasts, and typographical arrangements. Copyright arises automatically upon"
                            "creation and does not require registration. The Copyright, Designs and Patents"
                            "Act 1988 is the principal legislation.\n\nTrade marks protect signs, logos, and"
                            "words that distinguish goods and services of one business from another. Trade"
                            "marks must be registered to receive full protection under the Trade Marks Act"
                            "1994.\n\nConfidential information and trade secrets are protected through the"
                            "law of confidence, which requires the information to have the necessary quality"
                            "of confidence and to have been imparted in circumstances importing an"
                            "obligation of confidence.\n\nThe duration of copyright varies depending on the"
                            "type of work. For literary, dramatic, musical, and artistic works, copyright"
                            "lasts for the life of the author plus seventy years. For sound recordings and"
                            "films, it lasts for seventy years from the date of publication. For broadcasts,"
                            "it lasts for fifty years. Moral rights, which include the right of paternity"
                            "and the right of integrity, protect the personal interests of the author. These"
                            "rights cannot be assigned but can be waived. The Digital Economy Act 2010"
                            "addresses copyright infringement in the digital environment."
                        ),
                        "theory_ar": (
                            "يحمي قانون الملكية الفكرية إبداعات العقول، بما في ذلك الاختراعات والأعمال"
                            "الأدبية والفنية والأ designs والعلامات التجارية.\n\nتحمي براءات الاختراع"
                            "الاختراعات لفترة محدودة (عادةً عشرون عاماً). يجب أن يكون الاختراع جديداً ويحتوي"
                            "على خطوة ابتكارية.\n\nتحمي حقوق النشر الأعمال الأدبية والدرامية والموسيقية"
                            "والفنية الأصلية. تنشأ تلقائياً عند الإنشاء ولا تتطلب تسجيلاً.\n\nتحمي العلامات"
                            "التجارية العلامات والشعارات والكلمات التي تميز بضائع وخدمات عمل من"
                            "آخر.\n\nتُحمى المعلومات السرية وسر المهنة من خلال قانون الثقة."
                        ),
                        "vocab": [
                            {"fr": "patent", "ar": "براءة اختراع", "example": "The patent protects the invention for a period of twenty years."},
                            {"fr": "copyright", "ar": "حقوق النشر", "example": "Copyright arises automatically upon creation of the work."},
                            {"fr": "trade mark", "ar": "علامة تجارية", "example": "The trade mark must be registered to receive full protection."},
                            {"fr": "intellectual property", "ar": "الملكية الفكرية", "example": "Intellectual property law protects creations of the mind."},
                            {"fr": "inventive step", "ar": "خطوة ابتكارية", "example": "The invention must involve an inventive step to be patentable."},
                            {"fr": "industrial application", "ar": "تطبيق صناعي", "example": "The invention must be capable of industrial application."},
                            {"fr": "infringement", "ar": "انتهاك", "example": "The defendant was found to have infringed the claimant's patent."},
                            {"fr": "confidential information", "ar": "معلومات سرية", "example": "Confidential information is protected through the law of confidence."},
                            {"fr": "trade secrets", "ar": "أسرار تجارية", "example": "The former employee was restrained from using trade secrets."},
                            {"fr": "registered design", "ar": "تصميم مسجل", "example": "The registered design protects the appearance of the product."},
                            {"fr": "passing off", "ar": "التظاهر الزائف", "example": "The claimant brought an action for passing off against the defendant."},
                            {"fr": "licensing", "ar": "التخويل", "example": "The IP owner may grant a licence to third parties to use the protected work."},
                        ],
                    },
                    {
                        "id": "en_l3_u1_l10",
                        "title": "Environmental Law",
                        "title_ar": "قانون البيئة",
                        "subtitle": "Protecting the natural environment through law",
                        "theory": (
                            "Environmental law encompasses the body of law that governs the interaction"
                            "between human activities and the natural environment. It addresses issues such"
                            "as pollution, conservation, waste management, and climate change.\n\nIn the"
                            "United Kingdom, environmental law is derived from both domestic legislation and"
                            "international obligations. Key domestic statutes include the Environmental"
                            "Protection Act 1990, the Environment Act 2021, and the Climate Change Act"
                            "2008.\n\nThe Environmental Protection Act 1990 established the framework for"
                            "controlling pollution. It introduced the concept of best available techniques"
                            "for controlling emissions. The Environment Act 2021 created the Office for"
                            "Environmental Protection to hold government to account.\n\nEnvironmental impact"
                            "assessment is a process that requires certain projects to be assessed for their"
                            "likely environmental effects before they are approved. Habitats and species"
                            "protection is provided through the Conservation of Habitats and Species"
                            "Regulations.\n\nClimate change law includes the Climate Change Act 2008, which"
                            "set legally binding targets for reducing greenhouse gas emissions. The Paris"
                            "Agreement established the international framework for addressing climate"
                            "change.\n\nThe Environment Act 2021 introduced new duties on public authorities"
                            "to have regard to biodiversity enhancement. Biodiversity gain is now required"
                            "for most development projects in England. Water resources management is"
                            "regulated through abstraction licences and water company obligations."
                            "Environmental standards are enforced through environmental permits and"
                            "prosecutions for breach. The concept of the precautionary principle plays an"
                            "important role in environmental regulation, requiring preventive action even"
                            "where scientific certainty is lacking."
                        ),
                        "theory_ar": (
                            "يشمل قانون البيئة مجموعة القواعد القانونية التي تُنظّم التفاعل بين الأنشطة"
                            "البشرية والبيئة الطبيعية. يتناول قضايا مثل التلوث والحفاظ على الطبيعة وإدارة"
                            "النفايات وتغير المناخ.\n\nفي المملكة المتحدة، يُشتق قانون البيئة من التشريعات"
                            "المحلية والالتزامات الدولية. تشمل القوانين الرئيسية قانون الحماية البيئية 1990"
                            "وقانون البيئة 2021 وقانون تغير المناخ 2008.\n\nأنشأ قانون الحماية البيئية"
                            "إطاراً للتحكم في التلوث. أنشأ قانون البيئة 2021 مكتب الحماية البيئية.\n\nتقييم"
                            "الأثر البيئي هو عملية تتطلب تقييم مشاريع معينة لتأثيراتها البيئية المحتملة قبل"
                            "اعتمادها.\n\nيشمل قانون تغير المناخ قانون تغير المناخ 2008 الذي وضع أهدافاً"
                            "ملزمة قانونياً لخفض انبعاثات غازات الاحتباس الحراري."
                        ),
                        "vocab": [
                            {"fr": "environmental law", "ar": "قانون البيئة", "example": "Environmental law governs the interaction between human activities and the environment."},
                            {"fr": "pollution", "ar": "التلوث", "example": "The factory was prosecuted for causing pollution of the river."},
                            {"fr": "environmental impact assessment", "ar": "تقييم الأثر البيئي", "example": "An environmental impact assessment must be carried out before the project is approved."},
                            {"fr": "conservation", "ar": "ال conserve", "example": "The conservation regulations protect certain habitats and species."},
                            {"fr": "waste management", "ar": "إدارة النفايات", "example": "The waste management regulations impose duties on producers of waste."},
                            {"fr": "climate change", "ar": "تغير المناخ", "example": "The Climate Change Act sets legally binding targets for reducing emissions."},
                            {"fr": "emissions", "ar": "الانبعاثات", "example": "The company must reduce its greenhouse gas emissions in accordance with the Act."},
                            {"fr": "sustainability", "ar": "الاستدامة", "example": "The Act promotes sustainability in the use of natural resources."},
                            {"fr": "contaminated land", "ar": "الأراضي الملوثة", "example": "The regulations impose liability for the remediation of contaminated land."},
                            {"fr": "biodiversity", "ar": "التنوع البيولوجي", "example": "The Environment Act places a duty on public authorities to have regard to biodiversity."},
                            {"fr": "environmental protection", "ar": "الحماية البيئية", "example": "The Environmental Protection Act established the framework for controlling pollution."},
                            {"fr": "renewable energy", "ar": "الطاقة المتجددة", "example": "The government is promoting renewable energy to meet its climate change targets."},
                        ],
                    },
                ],
            },
        ],
    },
    {
        "id": 4,
        "title": "Professional — المحترف",
        "description": "Professional legal practice and specialized topics",
        "color": "#dc2626",
        "units": [
            {
                "id": "en_l4_u1",
                "title": "Professional Legal Topics",
                "title_ar": "المواضيع القانونية المهنية",
                "lessons": [
                    {
                        "id": "en_l4_u1_l1",
                        "title": "Court Advocacy Techniques",
                        "title_ar": "تقنيات المرافعة أمام المحكمة",
                        "subtitle": "The art of persuading the judge",
                        "theory": (
                            "Advocacy is the art of persuading the court. It is one of the most important"
                            "skills for a barrister and requires careful preparation, clear presentation,"
                            "and the ability to think on one's feet.\n\nThe structure of submissions"
                            "includes: opening (stating the case and key issues), skeleton argument (written"
                            "summary of legal points), oral submissions (developing arguments verbally),"
                            "dealing with questions (handling judicial interruptions), and closing"
                            "(summarising and asking for relief).\n\nTechniques of effective advocacy"
                            "include: knowing your case inside out, addressing the judge directly and"
                            "politely, using the judge's title (My Lord/Lady or Your Honour), structuring"
                            "arguments logically, anticipating the other side's arguments, using authorities"
                            "to support points, handling difficult questions with composure, never arguing"
                            "with the judge, conceding points that are lost, and always addressing the court"
                            "rather than opposing counsel.\n\nKey phrases include: 'May it please the"
                            "court...', 'If I may take your Lordship to...', 'With great respect, I"
                            "disagree...', 'I am obliged to concede that...', and 'In all the circumstances,"
                            "I invite the court to...'\n\nEffective advocacy requires mastery of both the"
                            "substantive law and the procedural rules governing the case. Counsel must be"
                            "able to identify and distil the key issues from a mass of evidence and present"
                            "them concisely. The ability to respond to judicial questions with composure and"
                            "accuracy is critical. Cross-examination of witnesses requires skill in"
                            "eliciting evidence that supports the client's case while exposing weaknesses in"
                            "the opposing case. The Advocate's duty is to the court, and this duty overrides"
                            "any duty to the client."
                        ),
                        "theory_ar": (
                            "المرافعة هي فن إقناع المحكمة. وهي واحدة من أهم المهارات للمحامي المُحترف وتتطلب"
                            "تجهيزاً دقيقاً وعرضاً واضحاً والقدرة على التفكير السريع.\n\nتتضمن بنية"
                            "الإبداهات: الافتتاح والمذكرة الإيضاحية والإبداهات الشفهية والتعامل مع الأسئلة"
                            "والخاتمة.\n\nتشمل تقنيات المرافعة الفعالة: معرفة القضية جيداً وخاطب القاضي"
                            "مباشرة بلباقة واستخدام لقب القاضي وإنشاء الحجج منطقياً والتوقع لحجج الطرف"
                            "الآخر.\n\nتشمل العبارات الأساسية: May it please the court و With great respect"
                            "I disagree و I am obliged to concede that و I invite the court to."
                        ),
                        "vocab": [
                            {"fr": "my Lord / my Lady", "ar": "سيدي القاضي / سيدتي القاضية", "example": "May it please the court, my Lord."},
                            {"fr": "your Honour", "ar": "سيادة القاضي", "example": "Your Honour, the evidence shows that the claimant acted reasonably."},
                            {"fr": "may it please the court", "ar": "تتشرف المحكمة", "example": "May it please the court, I appear for the claimant."},
                            {"fr": "with great respect", "ar": "بكل احترام", "example": "With great respect, I submit that the judge erred in his assessment."},
                            {"fr": "I am obliged to concede", "ar": "أنا مُلزَم بالاعتراف", "example": "I am obliged to concede that point, my Lady."},
                            {"fr": "I invite the court to", "ar": "أطلب من المحكمة", "example": "I invite the court to find for the claimant on all heads of claim."},
                            {"fr": "the skeleton argument", "ar": "المذكرة الإيضاحية", "example": "My skeleton argument is before the court at page twelve."},
                            {"fr": "oral submissions", "ar": "الإبداهات الشفهية", "example": "I now turn to my oral submissions on the second issue."},
                            {"fr": "to submit that", "ar": "أحتج بأن", "example": "I submit that the claimant has not proved his case to the required standard."},
                            {"fr": "in the alternative", "ar": "بدلاً من ذلك", "example": "In the alternative, the claimant relies on the doctrine of estoppel."},
                        ],
                    },
                    {
                        "id": "en_l4_u1_l2",
                        "title": "Legal Negotiation",
                        "title_ar": "المفاوضة القانونية",
                        "subtitle": "Reaching agreements and settlements",
                        "theory": (
                            "Legal negotiation is the process by which lawyers resolve disputes and reach"
                            "agreements on behalf of their clients. Effective negotiation requires"
                            "preparation, strategy, communication skills, and the ability to find creative"
                            "solutions that satisfy both parties.\n\nPreparation for negotiation includes:"
                            "understanding the facts and law, identifying the client's interests and"
                            "objectives, assessing the strengths and weaknesses of both sides, determining"
                            "the best alternative to a negotiated agreement (BATNA), and setting realistic"
                            "parameters for settlement.\n\nNegotiation strategies include: positional"
                            "bargaining (starting from an extreme position and making concessions),"
                            "interest-based negotiation (focusing on underlying interests rather than stated"
                            "positions), and principled negotiation (separating the people from the problem,"
                            "focusing on interests, generating options, and insisting on objective"
                            "criteria).\n\nKey skills in legal negotiation include: active listening, asking"
                            "open-ended questions, reframing issues, making credible commitments, managing"
                            "emotions, and knowing when to walk away. Written settlement agreements must be"
                            "clear, comprehensive, and enforceable.\n\nThe success of a negotiation often"
                            "depends on thorough preparation and the ability to read the other party's"
                            "position. Understanding cultural differences is important in international"
                            "negotiations. The use of frameworks such as the Harvard Negotiation Project's"
                            "principled negotiation method can help structure the process. Maintaining a"
                            "professional relationship while protecting the client's interests requires"
                            "diplomacy and strategic thinking. Written follow-up to confirm the terms agreed"
                            "is essential to avoid subsequent disputes about the negotiation outcome."
                        ),
                        "theory_ar": (
                            "المفاوضة القانونية هي العملية التي يحل بها المحامون النزاعات ويتوصلون إلى"
                            "اتفاقيات نيابةً عن عملائهم. تتطلب المفاوضة الفعالة تجهيزاً واستراتيجيةومهارات"
                            "تواصل والقدرة على إيجاد حلول إبداعية.\n\nيشمل التحضير للمفاوضة: فهم الوقائع"
                            "والقانون وتحديد مصالح العميل وأهدافه وتقييم نقاط القوة والضعف.\n\nتشمل"
                            "استراتيجيات المفاوضة: التفاوض الموقفي والتفاوض القائم على المصالح والتفاوض"
                            "المبدئي.\n\nتشمل المهارات الرئيسية: الاستماع النشط وطرح أسئلة مفتوحة وإعادة"
                            "صياغة المسائل والتحكم بالمشاعر."
                        ),
                        "vocab": [
                            {"fr": "negotiation", "ar": "المفاوضة", "example": "The parties entered into good faith negotiations to resolve the dispute."},
                            {"fr": "settlement", "ar": "تسوية", "example": "The case was settled out of court for an undisclosed sum."},
                            {"fr": "BATNA", "ar": "أفضل بديل لاتفاق متفاوض", "example": "Understanding your BATNA is essential before entering into negotiations."},
                            {"fr": "positional bargaining", "ar": "التفاوض الموقفي", "example": "Positional bargaining involves making extreme opening offers."},
                            {"fr": "interest-based negotiation", "ar": "التفاوض القائم على المصالح", "example": "Interest-based negotiation focuses on underlying needs rather than stated positions."},
                            {"fr": "concessions", "ar": "تنازلات", "example": "Both parties made significant concessions to reach an agreement."},
                            {"fr": "written agreement", "ar": "اتفاق مكتوب", "example": "The terms of the settlement were set out in a written agreement."},
                            {"fr": "without prejudice", "ar": "دون ضرر", "example": "The negotiations were conducted on a without prejudice basis."},
                            {"fr": "mediation", "ar": "الوساطة", "example": "The court encouraged the parties to attempt mediation before trial."},
                            {"fr": "good faith", "ar": "الحسن النية", "example": "Both parties are required to negotiate in good faith."},
                        ],
                    },
                    {
                        "id": "en_l4_u1_l3",
                        "title": "Banking and Finance Law",
                        "title_ar": "قانون البنوك والمالية",
                        "subtitle": "Regulating financial services and transactions",
                        "theory": (
                            "Banking and finance law governs the regulation of financial services, the"
                            "relationship between banks and their customers, and the legal framework for"
                            "financial transactions. It is one of the most heavily regulated areas of"
                            "law.\n\nThe Financial Services and Markets Act 2000 established the regulatory"
                            "framework for financial services in the UK. The Financial Conduct Authority"
                            "(FCA) is responsible for regulating the conduct of financial firms and"
                            "protecting consumers. The Prudential Regulation Authority (PRA) regulates the"
                            "safety and soundness of financial firms.\n\nBanking law covers the relationship"
                            "between banks and their customers, including the duty of confidentiality, the"
                            "bank's duty of care, money laundering regulations, and the banker's right of"
                            "set-off. The relationship between a bank and its customer is fundamentally a"
                            "debtor-creditor relationship.\n\nFinancial transactions include lending and"
                            "borrowing, securities and collateral, derivatives, project finance, and"
                            "syndicated loans. Key concepts include: due diligence, know your customer (KYC)"
                            "requirements, anti-money laundering (AML) obligations, and capital adequacy"
                            "requirements.\n\nThe Financial Services and Markets Act 2000 also established"
                            "the Financial Services Compensation Scheme, which provides protection for"
                            "customers of failed financial firms. The Payment Services Regulations 2017"
                            "govern the regulation of payment service providers. Consumer credit is"
                            "regulated under the Consumer Credit Act 1974. The regulation of financial"
                            "products and services continues to evolve in response to new technologies and"
                            "market developments, including fintech, cryptocurrencies, and digital banking."
                        ),
                        "theory_ar": (
                            "يُنظّم قانون البنوك والمالية تنظيم الخدمات المالية والعلاقة بين البنوك وعملائها"
                            "والإطار القانوني للمعاملات المالية.\n\nأنشأ قانون الخدمات والأسواق المالية 2000"
                            "الإطار التنظيمي للخدمات المالية في المملكة المتحدة. تتولى هيئة سلوك التمويل"
                            "(FCA) تنظيم سلوك الشركات المالية.\n\nيشمل قانون البنوك العلاقة بين البنوك"
                            "وعملائها وشمل واجب السرية وواجب العناية وقواعد غسيل الأموال.\n\nتشمل المعاملات"
                            "المالية الإقراض والاقتراض والأوراق المالية والرهون والمشتقات المالية."
                        ),
                        "vocab": [
                            {"fr": "banking law", "ar": "قانون البنوك", "example": "Banking law governs the relationship between banks and their customers."},
                            {"fr": "the FCA", "ar": "هيئة سلوك التمويل", "example": "The FCA regulates the conduct of financial firms in the UK."},
                            {"fr": "due diligence", "ar": "العناية الواجبة", "example": "The bank must carry out due diligence before opening a new account."},
                            {"fr": "money laundering", "ar": "غسيل الأموال", "example": "The bank reported the suspicious transaction under the money laundering regulations."},
                            {"fr": "know your customer", "ar": "اعرف عميلك", "example": "KYC requirements require banks to verify the identity of their customers."},
                            {"fr": "set-off", "ar": "المقاصة", "example": "The bank exercised its right of set-off against the customer's account."},
                            {"fr": "securities", "ar": "الأوراق المالية", "example": "The loan was secured against a portfolio of securities."},
                            {"fr": "collateral", "ar": "ضمان", "example": "The borrower provided real property as collateral for the loan."},
                            {"fr": "syndicated loan", "ar": "قرض متعدد الأطراف", "example": "The project was financed through a syndicated loan facility."},
                            {"fr": "capital adequacy", "ar": " كفاية رأس المال", "example": "The bank must maintain capital adequacy ratios in accordance with Basel III."},
                            {"fr": "anti-money laundering", "ar": "مكافحة غسيل الأموال", "example": "The firm must have robust anti-money laundering policies in place."},
                        ],
                    },
                    {
                        "id": "en_l4_u1_l4",
                        "title": "Tax Law",
                        "title_ar": "القانون الضريبي",
                        "subtitle": "Principles of taxation and fiscal obligations",
                        "theory": (
                            "Tax law governs the levying and collection of taxes by the state. It is a"
                            "complex area that affects individuals, businesses, and other organisations. In"
                            "the UK, the main taxes include income tax, corporation tax, value added tax"
                            "(VAT), capital gains tax, and inheritance tax.\n\nThe principle of statutory"
                            "construction in tax law is that taxes can only be imposed by statute. The court"
                            "will not imply obligations to pay tax. Any ambiguity in tax legislation is"
                            "interpreted in favour of the taxpayer.\n\nIncome tax is charged on income from"
                            "employment, self-employment, property, savings, and investments. Corporation"
                            "tax is charged on the taxable profits of companies. VAT is a consumption tax"
                            "charged on the supply of goods and services. Capital gains tax is charged on"
                            "the disposal of assets. Inheritance tax is charged on the transfer of wealth on"
                            "death or during lifetime.\n\nTax avoidance is the legal minimisation of tax"
                            "liability, while tax evasion is the illegal non-payment or underpayment of tax."
                            "The General Anti-Abuse Rule (GAAR) targets artificial and abusive tax"
                            "arrangements.\n\nThe General Anti-Abuse Rule (GAAR) was introduced in 2013 to"
                            "counter aggressive tax avoidance schemes. HMRC has the power to issue"
                            "accelerated payment notices requiring payment of disputed tax before the"
                            "outcome of an appeal is determined. Transfer pricing rules ensure that"
                            "transactions between connected persons reflect arm's length values. Tax"
                            "residency is determined by the Statutory Residence Test. Double taxation"
                            "treaties prevent the same income from being taxed in more than one jurisdiction."
                        ),
                        "theory_ar": (
                            "يُنظّم القانون الضريبي فرض وتحصيل الضرائب من الدولة. وهو مجال معقد يؤثر على"
                            "الأفراد والشركات. في المملكة المتحدة، تشمل الضرائب الرئيسية ضريبة الدخل وضريبة"
                            "الشركات وضريبة القيمة المضافة وضريبة أرباح رأس المال وضريبة الإرث.\n\nمبدأ"
                            "التفسير في القانون الضريبي هو أن الضرائب لا يمكن فرضها إلا بموجب قانون."
                            "interpreter أي غموض في التشريعات الضريبية يُفسّر لصالح دافع الضريبة.\n\nتشمل"
                            "الضرائب الرئيسية: ضريبة الدخل وضريبة الشركات وضريبة القيمة المضافة وضريبة أرباح"
                            "رأس المال وضريبة الإرث.\n\nالتهرب الضريبي هو تقليل الالتزام الضريبي بشكل"
                            "قانوني، بينما التهرب من الضريبة هو عدم الدفع أو الدفع الناقص بشكل غير قانوني."
                        ),
                        "vocab": [
                            {"fr": "tax law", "ar": "القانون الضريبي", "example": "Tax law governs the levying and collection of taxes by the state."},
                            {"fr": "income tax", "ar": "ضريبة الدخل", "example": "Income tax is charged on income from employment and investments."},
                            {"fr": "corporation tax", "ar": "ضريبة الشركات", "example": "Corporation tax is charged on the taxable profits of companies."},
                            {"fr": "VAT", "ar": "ضريبة القيمة المضافة", "example": "VAT is charged at the standard rate of twenty percent on most goods and services."},
                            {"fr": "capital gains tax", "ar": "ضريبة أرباح رأس المال", "example": "Capital gains tax is payable on the disposal of shares and property."},
                            {"fr": "inheritance tax", "ar": "ضريبة الإرث", "example": "Inheritance tax is charged on the transfer of wealth on death."},
                            {"fr": "tax avoidance", "ar": "التهرّب الضريبي", "example": "Tax avoidance is the legal minimisation of tax liability."},
                            {"fr": "tax evasion", "ar": "التهرب من الضرائب", "example": "Tax evasion is a criminal offence punishable by imprisonment."},
                            {"fr": "HMRC", "ar": "إدارة جمارك وضرائب הודّي Majesty", "example": "HMRC is responsible for the collection of taxes in the UK."},
                            {"fr": "the GAAR", "ar": "القاعدة العامة لمناهضة سوء الاستخدام", "example": "The GAAR targets artificial and abusive tax avoidance arrangements."},
                            {"fr": "taxable profit", "ar": "الربح الخاضع للضريبة", "example": "Corporation tax is charged on the company's taxable profit for the accounting period."},
                        ],
                    },
                    {
                        "id": "en_l4_u1_l5",
                        "title": "Immigration Law",
                        "title_ar": "قانون الهجرة",
                        "subtitle": "Visas, asylum and nationality",
                        "theory": (
                            "Immigration law governs the entry, stay, and removal of foreign nationals from"
                            "the United Kingdom. It is a rapidly changing area of law that is heavily"
                            "influenced by government policy.\n\nThe Immigration Act 1971 is the principal"
                            "legislation governing immigration in the UK. The Immigration Rules are a"
                            "detailed set of administrative directions that set out the requirements for"
                            "entry and stay.\n\nKey areas of immigration law include: visa applications"
                            "(visitor visas, student visas, work visas, family visas), the points-based"
                            "immigration system, asylum and human rights claims, detention and removal, and"
                            "nationality and citizenship.\n\nAsylum seekers must prove that they have a"
                            "well-founded fear of persecution in their country of origin. Claims are"
                            "assessed under the Refugee Convention and the Human Rights Act. The principle"
                            "of non-refoulement prevents the return of a person to a country where they face"
                            "serious risks to their life or freedom.\n\nImmigration decisions can be"
                            "challenged through judicial review and the First-tier Tribunal (Immigration and"
                            "Asylum Chamber).\n\nThe Immigration Act 2014 and 2016 introduced measures to"
                            "deter illegal working and overstaying. Employers have a duty to check the"
                            "immigration status of workers and face civil penalties for employing those"
                            "without the right to work. Sponsorship of skilled workers is governed by the"
                            "points-based system, which assigns points based on salary, skills, and"
                            "qualifications. Family reunion provisions allow certain family members of"
                            "refugees to join them in the UK. Judicial review of immigration decisions is"
                            "subject to specific procedural requirements."
                        ),
                        "theory_ar": (
                            "يُنظّم قانون الهجرة دخول وبقاء وإبعاد الأجانب من المملكة المتحدة. وهو مجال"
                            "يتغير بسرعة ويتأثر بشكل كبير بالسياسة الحكومية.\n\nقانون الهجرة 1971 هو القانون"
                            "الرئيسي. قواعد الهجرة هي مجموعة مفصلة من التوجيهات الإدارية.\n\nتشمل المجالات"
                            "الرئيسية: طلبات التأشيرة ونظام الهجرة القائم على النقاط وطلبات اللجوء وحقوق"
                            "الإنسان.\n\nيجب على طالبي اللجوء إثبات خوفهم المبرر من الاضطهاد. تُقيّم الطلبات"
                            "بموجب اتفاقية اللاجئين وقانون حقوق الإنسان.\n\nيمكن الطعن في قرارات الهجرة من"
                            "خلال الرقابة القضائية ومحكمة الدرجة الأولى."
                        ),
                        "vocab": [
                            {"fr": "immigration law", "ar": "قانون الهجرة", "example": "Immigration law governs the entry and stay of foreign nationals."},
                            {"fr": "visa", "ar": "تأشيرة", "example": "The applicant applied for a student visa to study at a UK university."},
                            {"fr": "asylum", "ar": "لجوء", "example": "The asylum seeker claimed protection under the Refugee Convention."},
                            {"fr": "deportation", "ar": "ترحيل", "example": "The respondent faced deportation following the criminal conviction."},
                            {"fr": "right to work", "ar": "الحق في العمل", "example": "The visa conditions do not grant the holder the right to work."},
                            {"fr": "indefinite leave to remain", "ar": "إقامة دائمة", "example": "She was granted indefinite leave to remain after five years."},
                            {"fr": "the Refugee Convention", "ar": "اتفاقية اللاجئين", "example": "The Refugee Convention provides protection to persons with a well-founded fear of persecution."},
                            {"fr": "non-refoulement", "ar": "عدم الإعادة القسرية", "example": "The principle of non-refoulement prevents the return of a person to face persecution."},
                            {"fr": "immigration tribunal", "ar": "محكمة الهجرة", "example": "The appeal was heard by the First-tier Tribunal Immigration and Asylum Chamber."},
                            {"fr": "points-based system", "ar": "النظام القائم على النقاط", "example": "The points-based system assesses applicants based on their skills and qualifications."},
                        ],
                    },
                    {
                        "id": "en_l4_u1_l6",
                        "title": "Health Law",
                        "title_ar": "قانون الصحة",
                        "subtitle": "Medical negligence, patient rights and regulation",
                        "theory": (
                            "Health law encompasses the legal framework governing healthcare, medical"
                            "practice, and public health. It addresses issues such as medical negligence,"
                            "patient consent, confidentiality, and the regulation of healthcare"
                            "professionals.\n\nMedical negligence (also called clinical negligence) occurs"
                            "when a healthcare professional breaches their duty of care, causing harm to a"
                            "patient. To establish medical negligence, the claimant must prove: a duty of"
                            "care existed, the duty was breached, the breach caused harm, and damage"
                            "resulted.\n\nPatient autonomy is protected through the doctrine of informed"
                            "consent. Patients must be given sufficient information about the risks and"
                            "benefits of treatment to make an informed decision. The Bolam test, modified by"
                            "the Bolitho case, determines the standard of care: a doctor is not negligent if"
                            "they acted in accordance with a practice accepted as proper by a responsible"
                            "body of medical professionals.\n\nConfidentiality is a fundamental principle of"
                            "medical ethics and law. Patient information must not be disclosed without"
                            "consent, except in limited circumstances such as to protect public health or"
                            "prevent crime.\n\nThe Care Quality Commission regulates health and social care"
                            "services in England. The Mental Health Act 1983 provides the framework for"
                            "compulsory detention and treatment of persons with mental disorders. The Mental"
                            "Capacity Act 2005 protects persons who lack capacity to make their own"
                            "decisions. Advance decisions (living wills) allow individuals to refuse"
                            "treatment in advance. The Human Fertilisation and Embryology Act regulates"
                            "fertility treatment and embryo research. Coroners investigate deaths that are"
                            "unnatural, violent, or of unknown cause."
                        ),
                        "theory_ar": (
                            "يشمل قانون الصحة الإطار القانوني الذي يُنظّم الرعاية الصحية والممارسة الطبية"
                            "والصحة العامة.\n\nيحدث الإهمال الطبي عندما يخرق مقدم الرعاية الصحية واجب"
                            "العناية، مسبباً ضرراً للمريض.\n\nيُحمي استقلالية المريض من خلال مبدأ الموافقة"
                            "المستنيرة. يجب تقديم معلومات كافية للمريض عن المخاطر والفوائد.\n\nالسرية هي"
                            "مبدأ أساسي في الأخلاقيات والقانون الطبي. لا يجب الكشف عن معلومات المريض دون"
                            "موافقة."
                        ),
                        "vocab": [
                            {"fr": "medical negligence", "ar": "الإهمال الطبي", "example": "The claimant brought a claim for medical negligence against the hospital."},
                            {"fr": "clinical negligence", "ar": "الإهمال السريري", "example": "Clinical negligence claims require expert medical evidence."},
                            {"fr": "duty of care", "ar": "واجب العناية", "example": "The doctor owed a duty of care to the patient from the moment of consultation."},
                            {"fr": "informed consent", "ar": "الموافقة المستنيرة", "example": "The patient must give informed consent before any medical procedure."},
                            {"fr": "the Bolam test", "ar": "اختبار Bolam", "example": "The Bolam test determines the standard of care expected of a medical professional."},
                            {"fr": "confidentiality", "ar": "السرية", "example": "Patient confidentiality is a fundamental principle of medical law."},
                            {"fr": "clinical trial", "ar": "التجربة السريرية", "example": "The clinical trial was conducted in accordance with ethical guidelines."},
                            {"fr": "medical records", "ar": "السجلات الطبية", "example": "The patient is entitled to access their medical records."},
                            {"fr": "public health", "ar": "الصحة العامة", "example": "The local authority has powers to take action to protect public health."},
                            {"fr": "NHS", "ar": "خدمة الصحة الوطنية", "example": "The NHS is responsible for providing healthcare to all UK residents."},
                        ],
                    },
                    {
                        "id": "en_l4_u1_l7",
                        "title": "Digital and Cyber Law",
                        "title_ar": "القانون الرقمي والسيبراني",
                        "subtitle": "Data protection, cybercrime and digital rights",
                        "theory": (
                            "Digital and cyber law addresses the legal issues arising from the use of"
                            "digital technology, the internet, and electronic communications. It includes"
                            "data protection, cybercrime, electronic commerce, and digital rights.\n\nThe UK"
                            "General Data Protection Regulation (UK GDPR) and the Data Protection Act 2018"
                            "regulate the processing of personal data. Key principles include: lawfulness,"
                            "fairness, and transparency; purpose limitation; data minimisation; accuracy;"
                            "storage limitation; integrity and confidentiality; and accountability.\n\nThe"
                            "Data Protection Act 2018 provides data subjects with rights including: the"
                            "right to be informed, the right of access, the right to rectification, the"
                            "right to erasure (the right to be forgotten), the right to restrict processing,"
                            "the right to data portability, and the right to object to"
                            "processing.\n\nCybercrime encompasses offences committed using computer"
                            "systems, including unauthorized access (hacking), distribution of malware,"
                            "identity theft, and online fraud. The Computer Misuse Act 1990 is the principal"
                            "legislation addressing cybercrime in the UK.\n\nThe Information Commissioner's"
                            "Office (ICO) is independent authority responsible for enforcing data protection"
                            "law in the UK. Fines for data protection breaches can be up to 17.5 million"
                            "pounds or four percent of annual global turnover. Privacy by design requires"
                            "organisations to consider data protection from the outset of any project. Data"
                            "protection impact assessments are required for high-risk processing activities."
                            "The Privacy and Electronic Communications Regulations 2003 govern electronic"
                            "marketing and the use of cookies."
                        ),
                        "theory_ar": (
                            "ي dealt القانون الرقمي والسيبراني مع المسائل القانونية الناتجة عن استخدام"
                            "التكنولوجيا الرقمية والإنترنت.\n\nتُنظّم اللائحة العامة لحماية البيانات (UK"
                            "GDPR) وقانون حماية البيانات 2018 معالجة البيانات الشخصية. تشمل المبادئ"
                            "الرئيسية: المشروعية والإنصاف والشفافية.\n\nيوفر قانون حماية البيانات 2018"
                            "حقوقاً لholders البيانات تشمل: الحق في الإبلاغ والحق في الوصول والحق في التصحيح"
                            "والحق في المحو.\n\nيشمل الجرائم السيبرانية جرائم ارتكابها باستخدام أنظمة"
                            "الكمبيوتر بما في ذلك الوصول غير المصرح به والتلاعب بالهوية والاحتيال عبر"
                            "الإنترنت."
                        ),
                        "vocab": [
                            {"fr": "data protection", "ar": "حماية البيانات", "example": "The UK GDPR regulates the processing of personal data."},
                            {"fr": "personal data", "ar": "البيانات الشخصية", "example": "Personal data includes any information relating to an identifiable person."},
                            {"fr": "data controller", "ar": "المتحكّم بالبيانات", "example": "The data controller is responsible for complying with data protection principles."},
                            {"fr": "data processor", "ar": "معالج البيانات", "example": "The data processor must act only on the instructions of the data controller."},
                            {"fr": "right to be forgotten", "ar": "الحق في النسيان", "example": "The data subject exercised the right to be forgotten to have their data erased."},
                            {"fr": "cybercrime", "ar": "الجريمة السيبرانية", "example": "Cybercrime encompasses offences committed using computer systems."},
                            {"fr": "hacking", "ar": "التسلل الإلكتروني", "example": "Unauthorised access to a computer system constitutes hacking under the Computer Misuse Act."},
                            {"fr": "data breach", "ar": "خرق البيانات", "example": "The organisation reported the data breach to the Information Commissioner within seventy-two hours."},
                            {"fr": "privacy policy", "ar": "سياسة الخصوصية", "example": "The organisation's privacy policy explains how personal data is processed."},
                            {"fr": "consent", "ar": "الموافقة", "example": "The data controller must obtain consent before processing personal data."},
                        ],
                    },
                    {
                        "id": "en_l4_u1_l8",
                        "title": "International Arbitration",
                        "title_ar": "التحكيم الدولي",
                        "subtitle": "Resolving cross-border disputes through arbitration",
                        "theory": (
                            "International arbitration is a method of resolving disputes between parties"
                            "from different countries through a binding decision made by an independent"
                            "arbitrator or tribunal. It is increasingly preferred over litigation for"
                            "international commercial disputes.\n\nThe Arbitration Act 1996 is the principal"
                            "legislation governing arbitration in England and Wales. It is based on the"
                            "UNCITRAL Model Law, which provides a harmonised framework for international"
                            "arbitration.\n\nKey features of international arbitration include: party"
                            "autonomy (the parties choose the arbitrator, the seat of arbitration, and the"
                            "applicable law); confidentiality (arbitration proceedings are private);"
                            "flexibility (the parties can agree on the procedure); and finality (arbitral"
                            "awards are binding and difficult to challenge).\n\nThe New York Convention on"
                            "the Recognition and Enforcement of Foreign Arbitral Awards (1958) provides a"
                            "framework for the enforcement of arbitral awards in over 170 countries. This"
                            "makes arbitration particularly attractive for international"
                            "disputes.\n\nInternational arbitration institutions include the International"
                            "Chamber of Commerce (ICC), the London Court of International Arbitration"
                            "(LCIA), and the Singapore International Arbitration Centre (SIAC).\n\nThe"
                            "tribunal in an international arbitration has the power to order interim"
                            "measures, including the appointment of an emergency arbitrator before the"
                            "tribunal is constituted. challenges to an arbitral award are limited to the"
                            "grounds set out in section 67 (lack of substantive jurisdiction) and section 68"
                            "(serious irregularity) of the Arbitration Act 1996. The court's power to"
                            "intervene is deliberately circumscribed to preserve the finality of"
                            "arbitration. Investor-state arbitration under bilateral investment treaties is"
                            "a growing area of international arbitration."
                        ),
                        "theory_ar": (
                            "التحكيم الدولي هو طريقة لحل النزاعات بين أطراف من بلدان مختلفة عبر قرار ملزم"
                            "يتخذه محك تحكيم مستقلة. يُفضل بشكل متزايد على التقاضي للنزاعات التجارية"
                            "الدولية.\n\nقانون التحكيم 1996 هو القانون الرئيسي الذي يُنظّم التحكيم في"
                            "إنجلترا وويلز.\n\nتشمل الميزات الرئيسية: استقلالية الأطراف (يختار الأطراف"
                            "المحكم ومقر التحكيم والقانون القابل للتطبيق) والسرية والمرونة"
                            "والنهائية.\n\nتوفر اتفاقية نيويورك框架اً لتنفيذ أحكام التحكيم في أكثر من 170"
                            "دولة.\n\nتشمل مؤسسات التحكيم الدولي: الغرفة التجارية الدولية (ICC) ومحكمة لندن"
                            "للتحكيم الدولي (LCIA)."
                        ),
                        "vocab": [
                            {"fr": "international arbitration", "ar": "التحكيم الدولي", "example": "International arbitration is the preferred method for resolving cross-border commercial disputes."},
                            {"fr": "the Arbitration Act", "ar": "قانون التحكيم", "example": "The Arbitration Act 1996 governs arbitration in England and Wales."},
                            {"fr": "arbitral award", "ar": "حكم التحكيم", "example": "The arbitral award is final and binding on both parties."},
                            {"fr": "the New York Convention", "ar": "اتفاقية نيويورك", "example": "The New York Convention facilitates the enforcement of foreign arbitral awards."},
                            {"fr": "seat of arbitration", "ar": "مقر التحكيم", "example": "The seat of arbitration determines the procedural law applicable to the proceedings."},
                            {"fr": "party autonomy", "ar": "استقلالية الأطراف", "example": "Party autonomy allows the parties to choose the arbitrator and the applicable law."},
                            {"fr": "ICC", "ar": "الغرفة التجارية الدولية", "example": "The ICC is one of the leading international arbitration institutions."},
                            {"fr": "LCIA", "ar": "محكمة لندن للتحكيم الدولي", "example": "The LCIA administers international arbitrations under its own rules."},
                            {"fr": "confidentiality", "ar": "السرية", "example": "Arbitration proceedings are conducted on a confidential basis."},
                            {"fr": "enforcement", "ar": "التنفيذ", "example": "The award was enforced in the courts of the United Kingdom under the New York Convention."},
                        ],
                    },
                    {
                        "id": "en_l4_u1_l9",
                        "title": "International Treaties and Conventions",
                        "title_ar": "الاتفاقيات والمعاهدات الدولية",
                        "subtitle": "The framework of international law",
                        "theory": (
                            "International treaties and conventions are agreements between states that"
                            "create legally binding obligations. They are a primary source of international"
                            "law and govern a wide range of issues including human rights, trade, the"
                            "environment, and armed conflict.\n\nThe Vienna Convention on the Law of"
                            "Treaties (1969) provides the framework for the creation, interpretation, and"
                            "termination of treaties. A treaty becomes binding on a state when it has been"
                            "duly ratified.\n\nKey international conventions include: the European"
                            "Convention on Human Rights (ECHR), the United Nations Convention on the Law of"
                            "the Sea (UNCLOS), the Geneva Conventions on the conduct of armed conflict, the"
                            "Paris Agreement on climate change, and the Convention on Contracts for the"
                            "International Sale of Goods (CISG).\n\nIn the UK, the relationship between"
                            "international law and domestic law is governed by the doctrine of dualism."
                            "International treaties do not form part of UK domestic law unless they have"
                            "been incorporated by an Act of Parliament. The Human Rights Act 1998"
                            "incorporated the ECHR into UK law.\n\nTreaties can be bilateral (between two"
                            "states) or multilateral (between three or more states). The process of"
                            "treaty-making involves negotiation, authentication, signature, ratification,"
                            "and entry into force. A state may express its consent to be bound by a treaty"
                            "through ratification, acceptance, approval, or accession. Reservations are"
                            "unilateral statements made by a state when signing or ratifying a treaty,"
                            "modifying the legal effects of certain provisions. The International Court of"
                            "Justice provides judicial settlement of disputes between states arising from"
                            "treaties."
                        ),
                        "theory_ar": (
                            "الاتفاقيات والمعاهدات الدولية هي اتفاقيات بين الدول تُنشئ التزامات قانونية"
                            "ملزمة. وهي مصدر رئيسي للقانون الدولي.\n\nتوفر اتفاقية فيينا بشأن قوانين"
                            "المعاهدات (1969) الإطار لإنشاء وتفسير وإنهاء المعاهدات.\n\nتشمل الاتفاقيات"
                            "الدولية الرئيسية: الاتفاقية الأوروبية لحقوق الإنسان واتفاقية الأمم المتحدة 关于"
                            "law of the sea واتفاقيات جنيف واتفاقية باريس وتغير المناخ.\n\nفي المملكة"
                            "المتحدة، يُنظّم مبدأ dualism العلاقة بين القانون الدولي والقانون المحلي."
                            "المعاهدات الدولية لا تشكل جزءاً من القانون المحلي إلا إذا دُمجت بموجب Act of"
                            "Parliament."
                        ),
                        "vocab": [
                            {"fr": "treaty", "ar": "معاهدة", "example": "The treaty was signed by representatives of both states."},
                            {"fr": "convention", "ar": "اتفاقية", "example": "The convention sets out the rights and obligations of the parties."},
                            {"fr": "ratification", "ar": "التصديق", "example": "The treaty entered into force following ratification by the required number of states."},
                            {"fr": "the Vienna Convention", "ar": "اتفاقية فيينا", "example": "The Vienna Convention on the Law of Treaties provides the framework for treaty law."},
                            {"fr": "the ECHR", "ar": "الاتفاقية الأوروبية لحقوق الإنسان", "example": "The ECHR was incorporated into UK law by the Human Rights Act 1998."},
                            {"fr": "the Geneva Conventions", "ar": "اتفاقيات جنيف", "example": "The Geneva Conventions govern the conduct of armed conflict."},
                            {"fr": "the Paris Agreement", "ar": "اتفاقية باريس", "example": "The Paris Agreement establishes the international framework for addressing climate change."},
                            {"fr": "dualism", "ar": "المثنوية", "example": "Under the doctrine of dualism, international treaties do not form part of UK domestic law without incorporation."},
                            {"fr": "monism", "ar": "الوحيدة", "example": "Under the doctrine of monism, international law forms part of the domestic legal system automatically."},
                            {"fr": "incorporation", "ar": "دمج", "example": "The Human Rights Act achieved the incorporation of the ECHR into UK law."},
                            {"fr": "reservations", "ar": "تحفظات", "example": "The state entered a reservation to Article 1 of the convention."},
                        ],
                    },
                    {
                        "id": "en_l4_u1_l10",
                        "title": "Comparative Legal Systems",
                        "title_ar": "الأنظمة القانونية المقارنة",
                        "subtitle": "Understanding different legal traditions around the world",
                        "theory": (
                            "Comparative legal systems studies the similarities and differences between the"
                            "legal systems of different countries. Understanding comparative law is"
                            "increasingly important in a globalised world.\n\nThe major legal traditions"
                            "include: common law (originating in England, based on judicial precedent and"
                            "case law, used in the UK, US, Australia, Canada, and India); civil law"
                            "(originating in Roman law, based on comprehensive codes, used in France,"
                            "Germany, Japan, and most of Latin America); and mixed systems (combining"
                            "elements of both, such as South Africa, Scotland, and Louisiana).\n\nKey"
                            "differences between common law and civil law systems include: the role of"
                            "judicial precedent (binding in common law, persuasive in civil law); the"
                            "codification of law (comprehensive codes in civil law, scattered legislation"
                            "and case law in common law); the role of the judge (passive umpire in common"
                            "law, active investigator in civil law); and the legal profession (split"
                            "profession in common law, unified profession in civil law).\n\nOther legal"
                            "traditions include Islamic law (Sharia), which is based on the Quran and the"
                            "teachings of the Prophet Muhammad, and Chinese law, which has its own"
                            "distinctive tradition influenced by Confucianism and socialist legal"
                            "theory.\n\nThe European Convention on Human Rights has influenced legal systems"
                            "across Europe, requiring them to incorporate fundamental rights protections."
                            "International trade law is governed by the World Trade Organization (WTO)"
                            "framework, which sets rules for international commerce. The principle of comity"
                            "requires courts of different jurisdictions to respect each other's laws and"
                            "decisions. Transnational litigation raises complex issues of jurisdiction,"
                            "applicable law, and enforcement of judgments. The development of international"
                            "commercial law has been influenced by the work of UNCITRAL in producing model"
                            "laws and conventions."
                        ),
                        "theory_ar": (
                            "دراسة الأنظمة القانونية المقارنة تدرس أوجه التشابه والاختلاف بين الأنظمة"
                            "القانونية للدول المختلفة. فهم القانون المقارن مهم بشكل متزايد في عالم"
                            "العولمة.\n\nتشمل التقاليد القانونية الرئيسية: القانون العام (المنشأ في إنجلترا،"
                            "مبني على سابقة قضائية وقانون القضايا) والقانون المدني (المنشأ في القانون"
                            "الروماني، مبني على أكواد شاملة) والأنظمة المختلطة (تجمع عناصر من"
                            "كليهما).\n\nتشمل الاختلافات الرئيسية: دور سابقة قضائية (ملزمة في القانون العام،"
                            "مقنعة في القانون المدني) وتوحيد القانون والأدوار القضائية ومهنة"
                            "المحاماة.\n\nتشمل التقاليد القانونية الأخرى: القانون الإسلامي (الشريعة)"
                            "والقانون الصيني."
                        ),
                        "vocab": [
                            {"fr": "common law", "ar": "القانون العام", "example": "Common law systems rely heavily on judicial precedent."},
                            {"fr": "civil law", "ar": "القانون المدني", "example": "Civil law systems are based on comprehensive written codes."},
                            {"fr": "mixed system", "ar": "نظام مختلط", "example": "South Africa has a mixed legal system combining common and civil law traditions."},
                            {"fr": "judicial precedent", "ar": "سابقة قضائية", "example": "Judicial precedent is a binding source of law in common law systems."},
                            {"fr": "codification", "ar": "توحيد القانون", "example": "Codification is a defining feature of civil law systems."},
                            {"fr": "comparative law", "ar": "القانون المقارن", "example": "Comparative law examines the differences between legal systems."},
                            {"fr": "Sharia law", "ar": "القانون الإسلامي", "example": "Sharia law is based on the Quran and the teachings of the Prophet."},
                            {"fr": "Roman law", "ar": "القانون الروماني", "example": "Roman law is the historical foundation of civil law systems."},
                            {"fr": "dualism", "ar": "المثنوية", "example": "In dualist systems, international treaties require domestic legislation to take effect."},
                            {"fr": "unified profession", "ar": "مهنة موحدة", "example": "Civil law countries typically have a unified legal profession."},
                            {"fr": "legal tradition", "ar": "تقليد قانوني", "example": "Each legal tradition has its own distinctive features and historical development."},
                            {"fr": "the jury system", "ar": "نظام هيئة المحلفين", "example": "The jury system is a feature of common law but not civil law systems."},
                        ],
                    },
                ],
            },
        ],
    },
]


# ──────────────────────────────────────────────────────────────────────────
# 🇪🇸 الإسبانية القانونية
# ──────────────────────────────────────────────────────────────────────────

LEVELS_ES = [
    # ─── Nivel 1 — Principiante ──────────────────────────────────────────
    {
        "id": 1,
        "title": "Principiante — المبتدئ",
        "description": "Vocabulario jurídico esencial en español",
        "color": "#2563eb",
        "units": [
            {
                "id": "es_l1_u1",
                "title": "Introducción al vocabulario jurídico",
                "title_ar": "مقدمة في المفردات القانونية",
                "lessons": [
                    {
                        "id": "es_l1_u1_l1",
                        "title": "Introducción al vocabulario jurídico",
                        "title_ar": "مقدمة في المفردات القانونية الإسبانية",
                        "subtitle": "Términos básicos del sistema jurídico español",
                        "theory": (
                            "El vocabulario jurídico constituye la base indispensable para comprender cualquier sistema legal. "
                            "En España, el sistema jurídico se fundamenta en la tradición del derecho continental, heredero del derecho romano "
                            "y fuertemente influido por el código civil napoleónico. Dominar los términos técnicos del derecho español es "
                            "requisito previo para cualquier estudiante de derecho o profesional que necesite interactuar con el sistema judicial español.\n\n"
                            "Los términos fundamentales del derecho español incluyen: la ley, que es la norma jurídica dictada por las Cortes Generales "
                            "y sancionada por el Rey; la Constitución Española de 1978, que es la norma suprema del ordenamiento jurídico y articula "
                            "el Estado de las Autonomías; el Código Civil, que regula las relaciones privadas entre personas; y el Código Penal, "
                            "que define los delitos y establece las penas correspondientes.\n\n"
                            "La jurisprudencia, entendida como la interpretación reiterada de los tribunales superiores, complementa las fuentes "
                            "legislativas y actúa como fuente auxiliar del derecho. El Tribunal Supremo, como órgano jurisdiccional supremo, "
                            "establece doctrina vinculante a través de sus sentencias. Los tribunales ordinarios se organizan en un sistema jerárquico "
                            "que comprende los juzgados de primera instancia, las audiencias provinciales y las salas de lo civil y lo penal "
                            "de los Tribunales Superiores de Justicia.\n\n"
                            "Los profesionales del derecho desempeñan funciones esenciales: el abogado asiste y representa a las partes; "
                            "el juez administra justicia imparcialmente; el fiscal defiende la legalidad y el interés público; "
                            "y el procurador representa a las partes ante los tribunales."
                        ),
                        "theory_ar": (
                            "يشكل المفردات القانونية الأساس الضروري لفهم أي نظام قانوني. في إسبانيا، يرتكز النظام القانوني على تقاليد القانون القار، "
                            "الوريث للقانون الروماني وتأثر بشكل كبير بالقانون المدني النابليوني. إتقان المصطلحات التقنية للقانون الإسباني "
                            "هو شرط مسبق لأي طالب قانون أو متخصص يحتاج للتفاعل مع النظام القضائي الإسباني.\n\n"
                            "تشمل المصطلحات الأساسية: القانون وهو القاعدة القانونية الصادرة عن البرلمان الإسباني؛ "
                            "والدستور الإسباني لعام 1978 وهو القاعدة العليا للنظام القانوني؛ والقانون المدني الذي يُنظم العلاقات الخاصة؛ "
                            "وقانون العقوبات الذي يُحدد الجرائم والعقوبات.\n\n"
                            "الاجتهاد القضائي يُكمل المصادر التشريعية ويعمل كمصدر مساعد للقانون. يُنظّم النظام القضائي بشكل هرمي.\n\n"
                            "يلعب المحترفون القانونيون أدواراً أساسية: المحامي يُمثل الأطراف؛ القاضي يُadminister العدالة بحياد؛ "
                            "والمدعي العام يُدافع عن المشروعية والمصلحة العامة."
                        ),
                        "vocab": [
                            {"fr": "la ley", "ar": "القانون", "example": "La ley fue aprobada por las Cortes Generales."},
                            {"fr": "la Constitución", "ar": "الدستور", "example": "La Constitución Española de 1978 es la norma suprema."},
                            {"fr": "el Código Civil", "ar": "القانون المدني", "example": "El Código Civil regula las relaciones privadas."},
                            {"fr": "el Código Penal", "ar": "قانون العقوبات", "example": "El Código Penal define los delitos y las penas."},
                            {"fr": "la jurisprudencia", "ar": "الاجتهاد القضائي", "example": "La jurisprudencia del Tribunal Supremo es vinculante."},
                            {"fr": "el Tribunal Supremo", "ar": "المحكمة العليا", "example": "El Tribunal Supremo fija doctrina jurisprudencial."},
                            {"fr": "el juez / la jueza", "ar": "القاضي / القاضية", "example": "El juez dictó sentencia condenatoria."},
                            {"fr": "el abogado / la abogada", "ar": "المحامي / المحامية", "example": "La abogada presentó el recurso de apelación."},
                            {"fr": "el fiscal", "ar": "المدعي العام", "example": "El fiscal solicitó la apertura del juicio oral."},
                            {"fr": "el procurador", "ar": "الممثل القانوني", "example": "El procurador representa a la parte ante el tribunal."},
                            {"fr": "la sentencia", "ar": "الحكم", "example": "La sentencia fue notificada a las partes."},
                            {"fr": "el tribunal", "ar": "المحكمة", "example": "El tribunal está compuesto por tres magistrados."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l1_u2",
                "title": "Los profesionales del derecho",
                "title_ar": "محترفو القانون",
                "lessons": [
                    {
                        "id": "es_l1_u2_l1",
                        "title": "Los profesionales del derecho",
                        "title_ar": "محترفو القانون الإسباني",
                        "subtitle": "Abogados, jueces, fiscales y otros profesionales",
                        "theory": (
                            "El ejercicio del derecho en España requiere una formación específica y el cumplimiento de requisitos profesionales rigurosos. "
                            "Cada profesional del derecho desempeña un papel fundamental dentro del sistema de administración de justicia, y es "
                            "imprescindible conocer sus funciones, atribuciones y responsabilidades.\n\n"
                            "El abogado es el profesional titulado que asiste jurídicamente a personas físicas o jurídicas, defendiéndolas ante "
                            "los tribunales o asesorándolas en sus relaciones jurídicas. Para ejercer la abogacía es necesaria la habilitación "
                            "profesional que otorga el Colegio de Abogados correspondiente. El abogado tiene el deber de sigilo profesional, "
                            "la obligación de actuar con diligencia y el deber de informar adecuadamente a su cliente.\n\n"
                            "El juez es el funcionario público investido de autoridad para administrar justicia en nombre del Rey. Los jueces "
                            "y magistrados son inamovibles, irresponsables e independientes. El Consejo General del Poder Judicial es el órgano "
                            "de gobierno de los jueces y garantiza la independencia del poder judicial.\n\n"
                            "El fiscal, integrante del Ministerio Público, tiene como función principal la defensa de la legalidad y la "
                            "perseguición de los delitos. El procurador es el profesional que representa a las partes ante los tribunales. "
                            "El notario es el funcionario público autorizado para dar fe de los actos y contratos. El registrador de la propiedad "
                            "custodia los libros de registro y publica los hechos jurídicos relativos a los bienes inmuebles."
                        ),
                        "theory_ar": (
                            "يتطلب ممارسة القانون في إسبانيا تكويناً محدداً والتزاماً بمتطلبات مهنية صارمة. يُلعب كل متخصص في القانون دوراً "
                            "أساسياً في نظام إدارة العدالة.\n\n"
                            "المحامي هو المتخصص الحاصل على شهادة يُقدم المساعدة القانونية للأشخاص الطبيعيين أو الاعتبارية.\n\n"
                            "القاضي هو الموظف العام المُustadh بالسلطة لإدارة العدالة باسم الملك. يخضع للضوابط القانونية ويتمتع بالاستقلالية.\n\n"
                            "المدعي العام عضو في النيابة العامة مهمته الدفاع عن المشروعية وملاحقة الجرائم.\n\n"
                            "الممثل القانوني يُمثل الأطراف أمام المحاكم. الموثق هو الموظف العام المُustadh لإعطاء الثقة للأفعال.\n\n"
                            "مسجّل العقارات يحفظ سجلات التسجيل وينشر الأفعال القانونية المتعلقة بالعقارات."
                        ),
                        "vocab": [
                            {"fr": "el abogado / la abogada", "ar": "المحامي / المحامية", "example": "El abogado debe actuar con diligencia y lealtad."},
                            {"fr": "el juez / la jueza", "ar": "القاضي / القاضية", "example": "El juez es independiente e inamovible."},
                            {"fr": "el magistrado / la magistrada", "ar": "القاضي (درجة عليا)", "example": "La magistrada presidió la sala de lo penal."},
                            {"fr": "el fiscal", "ar": "المدعي العام", "example": "El fiscal ejerce la acción penal pública."},
                            {"fr": "el procurador / la procuradora", "ar": "الممثل القانوني", "example": "El procurador presenta los escritos ante el juzgado."},
                            {"fr": "el notario / la notaria", "ar": "الموثق", "example": "El notario dio fe del otorgamiento de la escritura."},
                            {"fr": "el registrador de la propiedad", "ar": "مسجّل العقارات", "example": "El registrador inscribió la transmisión de la propiedad."},
                            {"fr": "el secretario judicial", "ar": "كاتب المحكمة", "example": "El secretario judicial levanta acta de la vista oral."},
                            {"fr": "el Colegio de Abogados", "ar": "نقابة المحامين", "example": "El Colegio de Abogados expide la cédula profesional."},
                            {"fr": "el Consejo General del Poder Judicial", "ar": "المجلس العام للسلطة القضائية", "example": "El Consejo garantiza la independencia judicial."},
                            {"fr": "la habilitación profesional", "ar": "التصريح المهني", "example": "La habilitación profesional es requisito para ejercer."},
                            {"fr": "el deber de sigilo", "ar": "واجب السرية", "example": "El deber de sigilo protege la confidencialidad del cliente."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l1_u3",
                "title": "Expresiones jurídicas comunes",
                "title_ar": "التعبيرات القانونية الشائعة",
                "lessons": [
                    {
                        "id": "es_l1_u3_l1",
                        "title": "Expresiones jurídicas comunes",
                        "title_ar": "التعبيرات القانونية الإسبانية الشائعة",
                        "subtitle": "Fórmulas habituales del lenguaje jurídico",
                        "theory": (
                            "El lenguaje jurídico español emplea un repertorio de fórmulas estereotipadas que forman el vocabulario de base "
                            "de todo escrito, demanda o alegato. El conocimiento y dominio de estas expresiones es indispensable para "
                            "comunicar eficazmente argumentos jurídicos y redactar documentos con precisión técnica.\n\n"
                            "Las expresiones de introducción sirven para fundamentar jurídicamente un razonamiento: «En virtud de» indica "
                            "con fundamento en una norma; «Conforme a» expresa acuerdo con un precepto; «Según resulta de» se refiere a lo "
                            "que emerge de una prueba o documento; «Resulta acreditado que» constata un hecho probado; «De lo expuesto» "
                            "resume lo argumentado anteriormente.\n\n"
                            "Las expresiones de conclusión permiten cerrar un razonamiento jurídico: «En méritos de lo expuesto» recapitula "
                            "los argumentos presentados; «Por todo lo expuesto» sintetiza los fundamentos; «Procede estimatoriamente» indica "
                            "que la pretensión debe ser acogida; «Se declara» formula una declaración judicial; «Se condena» impone una "
                            "condena concreta.\n\n"
                            "Las expresiones temporales son esenciales en el ámbito procesal: «En el plazo de» fija un plazo perentorio; "
                            "«A partir de» señala el punto de partida; «Sin perjuicio de» reserva derechos; «No obstante» introduce una matización. "
                            "Dominar estas fórmulas permite al operador jurídico desenvolverse con soltura en el entorno judicial español."
                        ),
                        "theory_ar": (
                            "يستخدم القانون الإسباني مجموعة من الصيغ الثابتة التي تُشكّل المفردات الأساسية لكل مذكرة أو دعوى. "
                            "معرفة هذه التعبيرات واستخدامها صحيح ضروري لتقديم الحجج القانونية بدقة.\n\n"
                            "تعبيرات المقدمة تُستخدم لتأسيس التحليل القانوني: «En virtud de» تعني بناءً على نص قانوني؛ "
                            "«Conforme a» تُعبّر عن التوافق مع حكم؛ «Resulta acreditado que» تُثبت حقيقة مؤكدة.\n\n"
                            "تعبيرات الختام تُستخدم لإنهاء التحليل: «En méritos de lo expuesto» تُلخص الحجج المقدمة؛ "
                            "«Procede estimatoriamente» تعني أن المطالبة يجب قبولها؛ «Se declara» تُصدر حكماً قضائياً.\n\n"
                            "التعبيرات الزمنية أساسية في الإجراءات: «En el plazo de» تُحدد ميعاداً نهائياً؛ "
                            "«A partir de» تُحدد نقطة انطلاق المدة؛ «Sin perjuicio de» تحتفظ بالحقوق."
                        ),
                        "vocab": [
                            {"fr": "en virtud de", "ar": "بناءً على / بموجب", "example": "En virtud del artículo 24 de la Constitución."},
                            {"fr": "conforme a", "ar": "وفقاً لـ", "example": "Conforme a la Ley de Enjuiciamiento Civil."},
                            {"fr": "según resulta de", "ar": "وفقاً لما يظهر من", "example": "Según resulta de la documental aportada."},
                            {"fr": "resulta acreditado que", "ar": "ثابت أن", "example": "Resulta acreditado que el demandado incumplió."},
                            {"fr": "de lo expuesto", "ar": "مما سبق عرضه", "example": "De lo expuesto se desprende la responsabilidad."},
                            {"fr": "en méritos de lo expuesto", "ar": "بناءً على ما تم عرضه", "example": "En méritos de lo expuesto, solicito la estimación."},
                            {"fr": "por todo lo expuesto", "ar": "بناءً على كل ما سبق", "example": "Por todo lo expuesto, solicito que se estime la demanda."},
                            {"fr": "procede estimatoriamente", "ar": "يجب قبول الدعوى", "example": "Procede estimatoriamente la pretensión del demandante."},
                            {"fr": "se declara", "ar": "يُعلن", "example": "Se declara la nulidad del contrato impugnado."},
                            {"fr": "se condena", "ar": "يُحكم", "example": "Se condena al demandado al pago de la cantidad reclamada."},
                            {"fr": "sin perjuicio de", "ar": "دون الإخلال بـ", "example": "Sin perjuicio de lo anterior, la parte puede recurrir."},
                            {"fr": "no obstante", "ar": "رغم / على الرغم من", "example": "No obstante la falta de prueba, el juez estimó la demanda."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l1_u4",
                "title": "Las fuentes del derecho",
                "title_ar": "مصادر القانون",
                "lessons": [
                    {
                        "id": "es_l1_u4_l1",
                        "title": "Las fuentes del derecho",
                        "title_ar": "مصادر القانون الإسباني",
                        "subtitle": "Jerarquía normativa y origen del derecho",
                        "theory": (
                            "Las fuentes del derecho son el conjunto de orígenes y fundamentos de las normas jurídicas aplicables en España. "
                            "El artículo 1.1 del Código Civil enumera las fuentes del ordenamiento jurídico español: la ley, la costumbre "
                            "y los principios generales del derecho.\n\n"
                            "La jerarquía normativa organiza las fuentes según un orden de preeminencia. En la cúspide se encuentra la "
                            "Constitución Española de 1978, que es la norma de mayor rango y fuente de todo el ordenamiento jurídico. "
                            "Los tratados internacionales ratificados por España forman parte del ordenamiento interno y prevalecen sobre "
                            "la legislación ordinaria en caso de contradicción, conforme al artículo 96 de la Constitución.\n\n"
                            "Las leyes se clasifican en leyes orgánicas, que regulan materias fundamentales como los derechos fundamentales "
                            "y la libertad de enseñanza, y leyes ordinarias, que son dictadas por las Cortes Generales en ejercicio de la "
                            "potestad legislativa ordinaria.\n\n"
                            "La costumbre, entendida como la práctica reiterada y voluntaria de un comportamiento con convicción de "
                            "obligatoriedad, es fuente del derecho cuando no existe ley aplicable o cuando no se contrapone a ella. "
                            "Los principios generales del derecho, como la buena fe, la justicia y la equidad, actúan como criterios "
                            "interpretativos y supletorios. La jurisprudencia complementa el ordenamiento a través de la interpretación "
                            "reiterada y consolidada de las normas por parte de los tribunales."
                        ),
                        "theory_ar": (
                            "مصادر القانون هي مجموعة أصول القواعد القانونية المطبقة في إسبانيا. تُحدد المادة 1.1 من القانون المدني "
                            "مصادر النظام القانوني الإسباني: القانون والعرف والمبادئ العامة للقانون.\n\n"
                            "تراتبية القواعد تُنظّم المصادر حسب ترتيب الأسبقية. في قمتها الدستور الإسباني لعام 1978 وهو الأعلى رتبة. "
                            "المعاهدات الدولية المصادق عليها تُشكّل جزءاً من النظام القانوني الداخلي.\n\n"
                            "تُصنّف القوانين إلى قوانين تنظيمية تُنظم المواضيع الجوهرية وقوانين عادية تصدر عن البرلمان الإسباني.\n\n"
                            "العرف هو الممارسة المتكررة والطوعية التي تُعتبر ملزمة. المبادئ العامة للقانون مثل حسن النية والعدل تعمل "
                            "كمعايير تفسيرية وتكميلية. الاجتهاد القضائي يُكمل النظام القانوني."
                        ),
                        "vocab": [
                            {"fr": "la ley", "ar": "القانون", "example": "La ley es la fuente principal del derecho."},
                            {"fr": "la costumbre", "ar": "العرف", "example": "La costumbre suple la falta de ley aplicable."},
                            {"fr": "los principios generales del derecho", "ar": "المبادئ العامة للقانون", "example": "Los principios generales del derecho son criterios interpretativos."},
                            {"fr": "la Constitución", "ar": "الدستور", "example": "La Constitución es la norma suprema del ordenamiento."},
                            {"fr": "la ley orgánica", "ar": "القانون التنظيمي", "example": "La ley orgánica regula los derechos fundamentales."},
                            {"fr": "la ley ordinaria", "ar": "القانون العادي", "example": "La ley ordinaria es aprobada por las Cortes Generales."},
                            {"fr": "el tratado internacional", "ar": "المعاهدة الدولية", "example": "El tratado internacional prevalece sobre la legislación interna."},
                            {"fr": "la jurisprudencia", "ar": "الاجتهاد القضائي", "example": "La jurisprudencia complementa las fuentes escritas."},
                            {"fr": "el Código Civil", "ar": "القانون المدني", "example": "El Código Civil enumera las fuentes del derecho."},
                            {"fr": "la jerarquía normativa", "ar": "تراتبية القواعد", "example": "La jerarquía normativa garantiza la coherencia del sistema."},
                            {"fr": "la potestad legislativa", "ar": "السلطة التشريعية", "example": "La potestad legislativa corresponde a las Cortes Generales."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l1_u5",
                "title": "La Constitución y las leyes",
                "title_ar": "الدستور والقوانين",
                "lessons": [
                    {
                        "id": "es_l1_u5_l1",
                        "title": "La Constitución y las leyes",
                        "title_ar": "الدستور الإسباني والتشريعات",
                        "subtitle": "Arquitectura constitucional y proceso legislativo",
                        "theory": (
                            "La Constitución Española de 1978, aprobada mediante referéndum el 6 de diciembre de ese año, es la norma "
                            "suprema del ordenamiento jurídico español. Establece la forma de gobierno parlamentario, organiza el Estado "
                            "de las Autonomías y reconoce un catálogo extenso de derechos y libertades fundamentales.\n\n"
                            "El proceso legislativo en España se desarrolla conforme a los artículos 66 y siguientes de la Constitución. "
                            "Las Cortes Generales, compuestas por el Congreso de los Diputados y el Senado, ejercen la potestad legislativa "
                            "del Estado. Un proyecto de ley puede ser presentado por el Gobierno, mientras que una proposición de ley "
                            "puede ser iniciada por el Congreso, el Senado, las Asambleas de las Comunidades Autónomas o por iniciativa ciudadana.\n\n"
                            "El procedimiento de aprobación comprende: la presentación del texto, la discusión en comisión, la votación "
                            "en el pleno de cada cámara, y la sanción y promulgación por parte del Rey.\n\n"
                            "Las leyes orgánicas requieren mayoría absoluta del Congreso y regulan materias como los derechos fundamentales. "
                            "Las leyes ordinarias se aprueban con mayoría simple y cubren el resto del ámbito legislativo. Los Reales "
                            "Decretos-leyes permiten al Gobierno legislar en casos de extraordinaria y urgente necesidad."
                        ),
                        "theory_ar": (
                            "الدستور الإسباني لعام 1978 الذي صدر بالاستفتاء في 6 ديسمبر يُشكّل القاعدة العليا للنظام القانوني الإسباني. "
                            "يُؤسس للنظام البرلماني وينظم دولة الحكم الذاتي.\n\n"
                            "يتبع المسار التشريعي أحكام الدستور. تتألف البرلمان الإسباني من مجلسي النواب والشيوخ.\n\n"
                            "تتضمن إجراءات الموافقة: تقديم النص والمناقشة والتصويت والتوقيع والتصديق من قبل الملك.\n\n"
                            "القوانين التنظيمية تتطلب أغلبية مطلقة وتنظم المواضيع الجوهرية. القوانين العادية تُعتمد بأغلبية بسيطة. "
                            "المراسيم التشريعية تسمح للحكومة بالتشريع في حالات الضرورة."
                        ),
                        "vocab": [
                            {"fr": "la Constitución Española", "ar": "الدستور الإسباني", "example": "La Constitución Española de 1978 es la norma suprema."},
                            {"fr": "las Cortes Generales", "ar": "البرلمان الإسباني", "example": "Las Cortes Generales ejercen la potestad legislativa."},
                            {"fr": "el Congreso de los Diputados", "ar": "مجلس النواب", "example": "El Congreso aprueba las leyes por mayoría absoluta."},
                            {"fr": "el Senado", "ar": "مجلس الشيوخ", "example": "El Senado examina los proyectos de ley."},
                            {"fr": "la ley orgánica", "ar": "القانون التنظيمي", "example": "La ley orgánica regula los derechos fundamentales."},
                            {"fr": "la ley ordinaria", "ar": "القانون العادي", "example": "La ley ordinaria se aprueba por mayoría simple."},
                            {"fr": "el proyecto de ley", "ar": "مشروع القانون الحكومي", "example": "El proyecto de ley fue presentado por el Gobierno."},
                            {"fr": "la proposición de ley", "ar": "المبادرة التشريعية", "example": "La proposición de ley fue registrada en el Congreso."},
                            {"fr": "la sanción y promulgación", "ar": "التوقيع والتصديق", "example": "La sanción real es requisito para la entrada en vigor."},
                            {"fr": "el Real Decreto-ley", "ar": "المرسوم التشريعي", "example": "El Real Decreto-ley se aprueba en casos de urgencia."},
                            {"fr": "la iniciativa ciudadana", "ar": "المبادرة الشعبية", "example": "La iniciativa ciudadana permite proponer leyes."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l1_u6",
                "title": "Derecho civil fundamental",
                "title_ar": "القانون المدني الأساسي",
                "lessons": [
                    {
                        "id": "es_l1_u6_l1",
                        "title": "Derecho civil fundamental",
                        "title_ar": "القانون المدني الإسباني الأساسي",
                        "subtitle": "Principios y reglas del derecho civil",
                        "theory": (
                            "El derecho civil es la rama del derecho que regula las relaciones entre los particulares. Constituye el tronco "
                            "común del sistema jurídico español y abarca todos los aspectos de la vida cotidiana de las personas, desde "
                            "su capacidad jurídica hasta la transmisión de bienes por sucesión mortis causa.\n\n"
                            "El Código Civil español, promulgado en 1889 con reformas posteriores, descansa sobre varios principios fundamentales. "
                            "El principio de libertad contractual permite a las partes celebrar los contratos que estimen conveniente. "
                            "El principio de autonomía de la voluntad reconoce la capacidad de las personas para determinar el contenido de "
                            "sus obligaciones. El principio de relatividad de los contratos dispone que un contrato solo produce efectos entre "
                            "las partes que lo celebraron.\n\n"
                            "Las obligaciones constituyen el núcleo del derecho civil. Una obligación es un vínculo jurídico en virtud del cual "
                            "un sujeto pasivo, el deudor, queda sujeto a realizar una prestación en favor de un sujeto activo, el acreedor. "
                            "Las principales fuentes de las obligaciones son el contrato, el cuasicontrato, el delito civil y el cuasidelito civil.\n\n"
                            "El derecho de propiedad, definido en el artículo 1.532 del Código Civil, comprende el derecho de dominio y los "
                            "demás derechos reales sobre bienes. La responsabilidad civil, regulada en los artículos 1.902 y siguientes, "
                            "tiene como finalidad reparar el daño causado por la acción u omisión antijurídica."
                        ),
                        "theory_ar": (
                            "القانون المدني هو الفرع الذي يُنظم العلاقات بين الأفراد. يُشكّل جذع النظام القانوني الإسباني ويشمل جميع "
                            "جوانب حياة الأشخاص اليومية.\n\n"
                            "القانون المدني الإسباني الذي صدر عام 1889 يقوم على مبادئ أساسية. مبدأ حرية التعاقد يتيح للأطراف إبرام العقود. "
                            "مبدأ سيادة الإرادة يعترف بقدرة الأشخاص على تحديد مضمون التزاماتهم. مبدأ النسبية ينص على أن العقد لا يُنشئ "
                            "التزامات إلا بين أطرافه.\n\n"
                            "الالتزامات تُشكّل جوهر القانون المدني. الالتزام هو رابطة قانونية يصبح بموجبها المدين ملزماً بتنفيذ التزام. "
                            "المصادر الرئيسية هي العقد وشبه العقد والجريمة المدنية وشبه الجريمة.\n\n"
                            "حق الملكية المحدد بالمادة 1532 يشمل حق التصرف والاستعمال والانتفاع. المسؤولية المدنية تهدف إلى تعويض "
                            "الضرر الناتج عن الفعل غير القانوني."
                        ),
                        "vocab": [
                            {"fr": "el contrato", "ar": "العقد", "example": "El contrato fue otorgado ante notario."},
                            {"fr": "la obligación", "ar": "الالتزام", "example": "El deudor está obligado a cumplir la prestación."},
                            {"fr": "el acreedor", "ar": "الدائن", "example": "El acreedor puede reclamar el pago de la deuda."},
                            {"fr": "el deudor", "ar": "المدين", "example": "El deudor incumplió el plazo de pago."},
                            {"fr": "la propiedad", "ar": "الملكية", "example": "La propiedad se adquiere por la ley, sucesión o contrato."},
                            {"fr": "el cuasicontrato", "ar": "شبه العقد", "example": "La gestión de negocios ajenos es un cuasicontrato."},
                            {"fr": "el delito civil", "ar": "الجريمة المدنية", "example": "El delito civil engendra obligación de indemnizar."},
                            {"fr": "la responsabilidad civil", "ar": "المسؤولية المدنية", "example": "La responsabilidad civil se funda en el artículo 1902."},
                            {"fr": "la sucesión mortis causa", "ar": "الإرث الميت", "example": "La sucesión mortis causa se rige por la voluntad del causante."},
                            {"fr": "la capacidad jurídica", "ar": "الأهلية القانونية", "example": "La capacidad jurídica se adquiere a los dieciocho años."},
                            {"fr": "el derecho real", "ar": "الحق العيني", "example": "La hipoteca es un derecho real sobre bienes inmuebles."},
                            {"fr": "la buena fe", "ar": "حسن النية", "example": "La buena fe protege al adquirente de buena fe."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l1_u7",
                "title": "Derecho penal básico",
                "title_ar": "قانون العقوبات الأساسي",
                "lessons": [
                    {
                        "id": "es_l1_u7_l1",
                        "title": "Derecho penal básico",
                        "title_ar": "قانون العقوبات الإسباني الأساسي",
                        "subtitle": "Delitos, penas y principios del derecho penal",
                        "theory": (
                            "El derecho penal define las conductas que constituyen delitos y establece las penas correspondientes. "
                            "Se rige por el principio de legalidad penal, según el cual nadie puede ser condenado por una acción que no "
                            "esté previamente definida como delito por la ley. Este principio, consagrado en el artículo 25 de la Constitución "
                            "Española, es una garantía fundamental del ciudadano frente al poder punitivo del Estado.\n\n"
                            "El Código Penal español distingue entre delitos graves, delitos menos graves y faltas, según la gravedad de la pena "
                            "aplicable. Los delitos graves llevan aparejada una pena de prisión superior a tres años o de otras penas "
                            "más graves; los delitos menos graves conllevan penas de prisión de tres meses a tres años.\n\n"
                            "Todo delito requiere la concurrencia de tres elementos: el tipo penal, el elemento objetivo y el elemento subjetivo "
                            "o dolo. Las circunstancias que modifican la responsabilidad criminal, como la alevosía, la premeditación conocida, "
                            "y las atenuantes como la confesión voluntaria, pueden agravar o atenuar la pena.\n\n"
                            "La presunción de inocencia, reconocida en el artículo 24 de la Constitución, garantiza que toda persona "
                            "es considerada inocente hasta que se demuestre lo contrario mediante sentencia firme."
                        ),
                        "theory_ar": (
                            "يُحدد قانون العقوبات السلوكيات التي تُشكّل جرائم ويضع العقوبات المقابلة. يخضع لمبدأ مشروعية العقوبات "
                            "الذي ينص على أنه لا يجوز محاسبة أي شخص على فعل غير محدد مسبقاً كجريمة.\n\n"
                            "يُميّز قانون العقوبات الإسباني بين الجرائم الخطيرة والجرائم الأقل خطورة والمخالفات.\n\n"
                            "تتطلب كل جريمة ثلاثة عناصر: النوع الجنائي والعنصر المادي والعنصر الذاتي. ظروف تعديل المسؤولية الجنائية "
                            "مثل القتل العمد يمكنها تشديد أو تخفيف العقوبة.\n\n"
                            "البراءة الأصلية المُكرَّسة في المادة 24 من الدستور تضمن اعتبار كل شخص بريئاً حتى تثبت إدانته بحكم نهائي."
                        ),
                        "vocab": [
                            {"fr": "el delito", "ar": "الجريمة", "example": "El delito requiere tipo, elemento objetivo y subjetivo."},
                            {"fr": "la falta", "ar": "المخالفة", "example": "Las faltas son infracciones leves del ordenamiento penal."},
                            {"fr": "la pena de prisión", "ar": "عقوبة السجن", "example": "La pena de prisión puede oscilar entre tres meses y veinte años."},
                            {"fr": "el dolo", "ar": "النية الإجرامية", "example": "El dolo directo es la intención de cometer el delito."},
                            {"fr": "la culpa", "ar": "الإهمال", "example": "La culpa genera responsabilidad penal a título de negligencia."},
                            {"fr": "la alevosía", "ar": "القتل العمد", "example": "La alevosía es circunstancia agravante de la responsabilidad criminal."},
                            {"fr": "la premeditación", "ar": "التخطيط المسبق", "example": "La premeditación conocida agrava la pena del autor."},
                            {"fr": "la atenuante", "ar": "ظرف التخفيف", "example": "La confesión voluntaria es circunstancia atenuante."},
                            {"fr": "la presunción de inocencia", "ar": "البراءة الأصلية", "example": "La presunción de inocencia es un derecho fundamental."},
                            {"fr": "el Ministerio Fiscal", "ar": "النيابة العامة", "example": "El Ministerio Fiscal ejerce la acción penal pública."},
                            {"fr": "la sentencia condenatoria", "ar": "الحكم الإدانة", "example": "La sentencia condenatoria declara la culpabilidad."},
                            {"fr": "el indulto", "ar": "العفو الرئاسي", "example": "El indulto total o parcial remite la pena impuesta."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l1_u8",
                "title": "Procedimiento civil",
                "title_ar": "الإجراءات المدنية",
                "lessons": [
                    {
                        "id": "es_l1_u8_l1",
                        "title": "Procedimiento civil",
                        "title_ar": "إجراءات التقاضي المدنية في إسبانيا",
                        "subtitle": "Desarrollo de un proceso civil",
                        "theory": (
                            "El procedimiento civil regula el desarrollo de los litigios ante los tribunales civiles españoles. "
                            "La Ley de Enjuiciamiento Civil de 2000 establece las normas fundamentales que rigen el proceso civil, "
                            "garantizando el principio de contradicción, el derecho de defensa y la igualdad de armas entre las partes.\n\n"
                            "Un litigo civil se inicia mediante la presentación de una demanda ante el juzgado de primera instancia "
                            "correspondiente. La demanda debe cumplir los requisitos formales establecidos en los artículos 399 y siguientes "
                            "de la Ley de Enjuiciamiento Civil: identificación de las partes, hechos relevantes, fundamentos jurídicos "
                            "y concreción de las pretensiones. El demandado es emplazado y dispone de un plazo para contestar la demanda.\n\n"
                            "La fase de alegaciones se desarrolla mediante el intercambio de escritos: la contestación a la demanda, "
                            "los escritos de réplica y duplica, y los escritos de conclusiones. El juez puede acordar la práctica de "
                            "medios de prueba propuestos por las partes, como interrogatorios de partes, documentos, periciales y testifical.\n\n"
                            "El acto del juicio oral comprende la lectura de la demanda y contestación, la proposición y admisión de prueba, "
                            "la práctica de la prueba admitida, y las conclusiones orales de las partes. Finalmente, el juez dicta sentencia."
                        ),
                        "theory_ar": (
                            "إجراءات التقاضي المدنية تُنظم سير النزاعات أمام المحاكم المدنية الإسبانية. قانون الإجراءات المدنية لعام 2000 "
                            "يضع القواعد الأساسية التي تحكم الإجراءات المدنية.\n\n"
                            "يبدأ النزاع المدني بتقديم دعوى أمام محكمة الدرجة الأولى المختصة.\n\n"
                            "مرحلة العروض تتضمن تبادل المذكرات.\n\n"
                            "الجلسة الصوتية تُعقد أمام محكمة الدرجة الأولى وتتضمن قراءة الدعوى والرد وتقديم الإثبات والخلاصة الشفهية. "
                            "يُصدر القاضي حكماً مبرراً ومطابقاً للقانون."
                        ),
                        "vocab": [
                            {"fr": "la demanda", "ar": "الدعوى المدنية", "example": "La demanda fue presentada en el juzgado de primera instancia."},
                            {"fr": "la contestación a la demanda", "ar": "الرد على الدعوى", "example": "El demandado formuló contestación a la demanda."},
                            {"fr": "la reconvención", "ar": "الدعوى المتقابلة", "example": "El demandado planteó reconvención en su escrito."},
                            {"fr": "el juicio oral", "ar": "الجلسة الصوتية", "example": "El juicio oral se celebró en la fecha señalada."},
                            {"fr": "la sentencia", "ar": "الحكم", "example": "La sentencia fue notificada a las partes."},
                            {"fr": "el plazo", "ar": "المدة", "example": "El demandado dispone de un plazo de veinte días."},
                            {"fr": "la prueba testifical", "ar": "الإثبات بالشهادات", "example": "La prueba testifical fue propuesta por ambas partes."},
                            {"fr": "la prueba documental", "ar": "الإثبات المستندي", "example": "La prueba documental acredita la titularidad del demandante."},
                            {"fr": "la prueba pericial", "ar": "الخبرة", "example": "La prueba pericial determina el valor del inmueble."},
                            {"fr": "la audiencia previa", "ar": "الجلسة التحضيرية", "example": "En la audiencia previa se intentó la conciliación."},
                            {"fr": "la conciliación", "ar": "التوافق", "example": "El juzgado ordenó el acto de conciliación."},
                            {"fr": "el recurso de apelación", "ar": "الاستئناف", "example": "El recurso de apelación fue interpuesto dentro del plazo legal."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l1_u9",
                "title": "Derecho laboral",
                "title_ar": "قانون العمل",
                "lessons": [
                    {
                        "id": "es_l1_u9_l1",
                        "title": "Derecho laboral",
                        "title_ar": "قانون العمل الإسباني",
                        "subtitle": "Relaciones laborales y derechos de los trabajadores",
                        "theory": (
                            "El derecho laboral en España regula las relaciones entre los trabajadores por cuenta ajena y sus empleadores. "
                            "Su norma fundamental es el Estatuto de los Trabajadores, que establece los derechos y obligaciones de ambas partes "
                            "en la relación laboral.\n\n"
                            "El contrato de trabajo es el acuerdo entre trabajador y empresario por el cual aquél se obliga a prestar sus "
                            "servicios profesionales por cuenta y bajo la dirección de éste, a cambio de una retribución. Los contratos "
                            "pueden ser indefinidos o temporales, a tiempo completo o parcial.\n\n"
                            "El Estatuto de los Trabajadores reconoce derechos fundamentales como la libertad sindical, la negociación "
                            "colectiva, la huelga, y la limitación de la jornada diaria a un máximo de nueve horas, con un descanso "
                            "mínimo de doce horas entre jornadas. El salario mínimo interprofesional, fijado anualmente por el Gobierno, "
                            "garantiza un ingreso mínimo para todos los trabajadores.\n\n"
                            "El despido puede ser objetivo por causas económicas, técnicas, organizativas o de producción, o disciplinario "
                            "por incumplimiento grave y culpable del trabajador. En caso de despido improcedente, el trabajador tiene derecho "
                            "a una indemnización o a la readmisión en su puesto de trabajo."
                        ),
                        "theory_ar": (
                            "يُنظم قانون العمل في إسبانيا العلاقات بين العاملين لحساب الغير وأصحاب عملهم. الميثاق الأساسي للعاملين "
                            "يُحدد الحقوق والواجبات لكلا الطرفين.\n\n"
                            "عقد العمل هو اتفاق بين العامل وصاحب العمل.\n\n"
                            "يُقرّ الميثاق الأساسي بحقوق أساسية مثل الحرية النقابية والتفاوض الجماعي وإضراب وتحديد يوم العمل. "
                            "الحد الأدنى للأجر يُضمن دخلاً أدنى لجميع العاملين.\n\n"
                            "يمكن أن يكون الفصل هدفياً أو تأديبياً. في حالة الفصل غير المشروع يحق للعامل تعويضاً أو إعادة التعيين."
                        ),
                        "vocab": [
                            {"fr": "el contrato de trabajo", "ar": "عقد العمل", "example": "El contrato de trabajo fue firmado por ambas partes."},
                            {"fr": "el trabajador / la trabajadora", "ar": "العامل / العاملة", "example": "El trabajador tiene derecho a un salario digno."},
                            {"fr": "el empresario", "ar": "صاحب العمل", "example": "El empresario debe respetar la jornada laboral máxima."},
                            {"fr": "el salario", "ar": "الأجر", "example": "El salario mínimo interprofesional se fija cada año."},
                            {"fr": "el despido", "ar": "الفصل من العمل", "example": "El despido debe ser comunicado por escrito."},
                            {"fr": "el despido improcedente", "ar": "الفصل غير المشروع", "example": "El despido improcedente genera derecho a indemnización."},
                            {"fr": "la indemnización", "ar": "التعويض", "example": "La indemnización por despido improcedente es de 33 días por año."},
                            {"fr": "la negociación colectiva", "ar": "التفاوض الجماعي", "example": "La negociación colectiva se realiza entre sindicatos y empresarios."},
                            {"fr": "el convenio colectivo", "ar": "الاتفاقية الجماعية", "example": "El convenio colectivo mejora las condiciones laborales mínimas."},
                            {"fr": "el derecho de huelga", "ar": "حق الإضراب", "example": "El derecho de huelga es un derecho fundamental."},
                            {"fr": "el SMI", "ar": "الحد الأدنى للأجر", "example": "El SMI garantiza un ingreso mínimo para todos los trabajadores."},
                            {"fr": "la incapacidad temporal", "ar": "العجز المؤقت", "example": "La incapacidad temporal genera prestaciones por enfermedad."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l1_u10",
                "title": "Derecho de familia",
                "title_ar": "قانون الأسرة",
                "lessons": [
                    {
                        "id": "es_l1_u10_l1",
                        "title": "Derecho de familia",
                        "title_ar": "قانون الأسرة الإسباني",
                        "subtitle": "Matrimonio, filiación y patria potestad",
                        "theory": (
                            "El derecho de familia regula las relaciones jurídicas entre los miembros de una familia. En España, "
                            "está regulado principalmente por el Código Civil, con importantes modificaciones derivadas de la Constitución "
                            "y de la legislación sobre igualdad y derechos de las mujeres.\n\n"
                            "El matrimonio es la unión de dos personas que se constituye mediante la celebración ante el encargado del "
                            "Registro Civil. Los cónyuges tienen obligaciones recíprocas de asistencia mutua, fidelidad y socorro. "
                            "El régimen económico matrimonial se establece en capitulaciones matrimoniales antes o durante el matrimonio.\n\n"
                            "La filiación, biológica o adoptiva, establece el vínculo jurídico entre padres e hijos. La patria potestad "
                            "es el conjunto de derechos y deberes que tienen los progenitores sobre sus hijos menores de edad, ejercida "
                            "conjuntamente por ambos progenitores siempre que sea posible.\n\n"
                            "El divorcio puede ser de mutuo acuerdo o contencioso. La ley de divorcio exprés permite tramitaciones "
                            "más ágiles cuando no hay hijos menores o incapacitados. La patria potestad, la guarda y custodia "
                            "y el régimen de visitas se determinan en interés superior del menor."
                        ),
                        "theory_ar": (
                            "يُنظم قانون الأسرة العلاقات القانونية بين أفراد الأسرة. في إسبانيا يُحكم بشكل أساسي بالقانون المدني "
                            "مع تعديلات ناتجة عن الدستور.\n\n"
                            "الزواج هو اتحاد شخصين يُحتفل بهما أمام مسجّل الحالة المدنية.\n\n"
                            "النسب البيولوجي أو التبني يُنشئ الرابطة القانونية بين الوالدين والأبناء. السلطة الأبوية هي مجموعة "
                            "الحقوق والواجبات على الأقل سن القصر.\n\n"
                            "الطلاق يمكن أن يكون بالتوافق أو خلافاً. قانون الطلاق السريع يُسرّع الإجراءات في غياب أطفال قاصرين. "
                            "تُحدد السلطة الأبوية وحقوق الزيارة والمتابعة في المصلحة الفوقية للطفل."
                        ),
                        "vocab": [
                            {"fr": "el matrimonio", "ar": "الزواج", "example": "El matrimonio se celebra ante el encargado del Registro Civil."},
                            {"fr": "el divorcio", "ar": "الطلاق", "example": "El divorcio puede ser de mutuo acuerdo o contencioso."},
                            {"fr": "la filiación", "ar": "النسب", "example": "La filiación biológica o adoptiva establece el vínculo jurídico."},
                            {"fr": "la patria potestad", "ar": "السلطة الأبوية", "example": "La patria potestad se ejerce conjuntamente por ambos progenitores."},
                            {"fr": "los alimentos", "ar": "النفقة", "example": "La obligación de alimentos se extiende a los ascendientes."},
                            {"fr": "la guarda y custodia", "ar": "الحراسة والحضانة", "example": "La guarda y custodia puede ser compartida o unilateral."},
                            {"fr": "el régimen de visitas", "ar": "نظام الزيارة", "example": "El régimen de visitas se fija en interés del menor."},
                            {"fr": "las capitulaciones matrimoniales", "ar": "اتفاقيات الزواج", "example": "Las capitulaciones se otorgan ante notario."},
                            {"fr": "el régimen de gananciales", "ar": "نظام المكاسب المشتركة", "example": "El régimen de gananciales es el legal supletorio."},
                            {"fr": "la separación de bienes", "ar": "الفصل بين الأموال", "example": "La separación de bienes puede pactarse en capitulaciones."},
                            {"fr": "la adopción", "ar": "التبني", "example": "La adopción confiere al adoptado la condición de hijo propio."},
                            {"fr": "el interés superior del menor", "ar": "المصلحة الفوقية للطفل", "example": "El interés superior del menor guía toda decisión judicial."},
                        ],
                    },
                ],
            },
        ],
    },
    # ─── Nivel 2 — Intermedio ──────────────────────────────────────────
    {
        "id": 2,
        "title": "Intermedio — المتوسط",
        "description": "Estructuras jurídicas complejas y derecho de obligaciones",
        "color": "#059669",
        "units": [
            {
                "id": "es_l2_u1",
                "title": "Estructuras jurídicas complejas",
                "title_ar": "البنيات القانونية المعقدة",
                "lessons": [
                    {
                        "id": "es_l2_u1_l1",
                        "title": "Estructuras jurídicas complejas",
                        "title_ar": "البنيات القانونية المعقدة",
                        "subtitle": "Organización del sistema jurídico y sus ramas",
                        "theory": (
                            "El sistema jurídico español se organiza en múltiples ramas del derecho, cada una con su propio objeto normativo "
                            "y su cuerpo de principios y reglas. Comprender la estructura del sistema es esencial para localizar la norma "
                            "aplicable a un caso concreto y para argumentar correctamente ante los tribunales.\n\n"
                            "El derecho se divide en derecho público y derecho privado. El derecho público regula las relaciones en las que "
                            "una de las partes es un poder público: incluye el derecho constitucional, el derecho administrativo, el derecho "
                            "penal y el derecho procesal. El derecho privado regula las relaciones entre particulares: abarca el derecho "
                            "civil, el derecho mercantil y el derecho laboral.\n\n"
                            "Dentro del derecho administrativo, se distingue el derecho administrativo general, que regula la organización "
                            "y funcionamiento de la Administración; el derecho urbanístico, que regula la edificación y la ordenación del "
                            "territorio; y el derecho tributario, que regula las obligaciones fiscales.\n\n"
                            "El derecho mercantil regula las actividades de comercio y los actos de comercio objetivos, incluyendo el derecho "
                            "de sociedades, el derecho cambiario y el derecho de la competencia. Estas ramas interactúan entre sí y "
                            "requieren una comprensión interdisciplinaria para su correcta aplicación."
                        ),
                        "theory_ar": (
                            "ينظم النظام القانوني الإسباني عدة فروع للقانون، لكل منها موضوعه ومبادئه وقواعد. فهم بنيته "
                            "ضروري لتحديد القانون المطبق على حالة معينة.\n\n"
                            "ينقسم القانون إلى قانون عام وقانون خاص. القانون العام يُنظم العلاقات التي يكون فيها أحد الأطراف جهة حكومية.\n\n"
                            "في مجال القانون الإداري يُميّز بين القانون الإداري العام والقانون الحضري والقانون الضريبي.\n\n"
                            "القانون التجاري يُنظم أنشطة التجارة ويشمل قانون الشركات وقانون المنافسة. هذه الفروع "
                            "تتفاعل وتتطلب فهماً متعدد التخصصات."
                        ),
                        "vocab": [
                            {"fr": "el derecho público", "ar": "القانون العام", "example": "El derecho público regula las relaciones con poderes públicos."},
                            {"fr": "el derecho privado", "ar": "القانون الخاص", "example": "El derecho privado regula las relaciones entre particulares."},
                            {"fr": "el derecho administrativo", "ar": "القانون الإداري", "example": "El derecho administrativo regula la actuación de la Administración."},
                            {"fr": "el derecho constitucional", "ar": "القانون الدستوري", "example": "El derecho constitucional protege los derechos fundamentales."},
                            {"fr": "el derecho mercantil", "ar": "القانون التجاري", "example": "El derecho mercantil regula las sociedades y el comercio."},
                            {"fr": "el derecho laboral", "ar": "قانون العمل", "example": "El derecho laboral protege a los trabajadores."},
                            {"fr": "el derecho tributario", "ar": "القانون الضريبي", "example": "El derecho tributario regula las obligaciones fiscales."},
                            {"fr": "el derecho urbanístico", "ar": "القانون الحضري", "example": "El derecho urbanístico regula la edificación."},
                            {"fr": "la jurisdicción contencioso-administrativa", "ar": "المنازعات الإدارية", "example": "La jurisdicción contencioso-administrativa conoce reclamaciones contra la Administración."},
                            {"fr": "el derecho de sociedades", "ar": "قانون الشركات", "example": "El derecho de sociedades regula la creación de empresas."},
                            {"fr": "el derecho de la competencia", "ar": "قانون المنافسة", "example": "El derecho de la competencia sanciona abusos de posición dominante."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l2_u2",
                "title": "La voz pasiva en derecho",
                "title_ar": "المبني للمجهول في اللغة القانونية",
                "lessons": [
                    {
                        "id": "es_l2_u2_l1",
                        "title": "La voz pasiva en derecho",
                        "title_ar": "المبني للمجهول في النصوص القانونية",
                        "subtitle": "Uso de la voz pasiva en textos legales",
                        "theory": (
                            "La voz pasiva es un recurso gramatical ampliamente utilizado en la redacción jurídica española. "
                            "Permite despersonalizar la acción y centrar la atención en el objeto de la misma, lo cual resulta "
                            "particularmente útil en textos legales donde la impersonalidad y la objetividad son valores esenciales.\n\n"
                            "En el ámbito jurídico, la voz pasiva se emplea en múltiples contextos: en la legislación (\"Se prohíbe...\", "
                            "\"Se entenderá por...\", \"Se procederá a...\"), en las resoluciones judiciales (\"Se declara probado...\", "
                            "\"Se condena al acusado...\") y en los escritos procesales. El uso de la pasiva refuerza la autoridad "
                            "de la norma y la imparcialidad del juzgador.\n\n"
                            "Las formas más comunes de la voz pasiva en el lenguaje jurídico incluyen: la pasiva con \"ser\" (\"La ley fue aprobada "
                            "por las Cortes\"), la pasiva con participio (\"Dictada la sentencia, se procederá a su notificación\"), "
                            "y la construcción impersonal pasiva (\"Se requiere la autorización previa\").\n\n"
                            "El uso correcto de la voz pasiva permite al operador jurídico redactar textos con precisión técnica, "
                            "evitando ambigüedades y centrándose en la acción o el resultado más que en el sujeto que la realiza."
                        ),
                        "theory_ar": (
                            "المبني للمجهول هو أسلوب نحوي يُستخدم بكثرة في الكتابة القانونية الإسبانية. يسمح بتخليص الفاعل "
                            "والتركيز على مفعول الفعل.\n\n"
                            "في المجال القانوني يُستخدم المبني للمجهول في سياقات متعددة: التشريعات والقرارات القضائية "
                            "والمذكرات الإجرائية. استخدام المبني للمجهول يعزز سلطة القاعدة وحياد القاضي.\n\n"
                            "الأشكال الأكثر شيوعاً تشمل: المبني للمجهول مع \"ser\" والمبني للمجهول مع التصريف الماضي والصيغة المبتدأية.\n\n"
                            "الاستخدام الصحيح للمبني للمجهول يُتيح للمoperator القانوني كتابة نصوص بدقة تقنية."
                        ),
                        "vocab": [
                            {"fr": "se prohíbe", "ar": "يُحظر", "example": "Se prohíbe el acceso a menores de edad."},
                            {"fr": "se entenderá por", "ar": "يُ understood by", "example": "Se entenderá por fraude la acción engañosa deliberada."},
                            {"fr": "se procederá a", "ar": "يُ procede to", "example": "Se procederá a la ejecución forzosa del bien."},
                            {"fr": "se declara probado", "ar": "يُثبت أن", "example": "Se declara probado que el demandado incumplió."},
                            {"fr": "se condena al acusado", "ar": "يُحكم على المتهَم", "example": "Se condena al acusado a la pena de prisión."},
                            {"fr": "se requiere la autorización previa", "ar": "تتطلب إذناً مسبقاً", "example": "Se requiere la autorización previa de la Administración."},
                            {"fr": "fue aprobada por", "ar": "تُ approve by", "example": "La ley fue aprobada por las Cortes Generales."},
                            {"fr": "fue dictada por", "ar": "تُ issued by", "example": "La sentencia fue dictada por el juez de primera instancia."},
                            {"fr": "está previsto en", "ar": "is foreseen in", "example": "Está previsto en el artículo 24 de la Constitución."},
                            {"fr": "queda acreditado que", "ar": "ثابت أن", "example": "Queda acreditado que el contrato fue incumplido."},
                            {"fr": "se encuentra regulado por", "ar": "is regulated by", "example": "Se encuentra regulado por el Código Civil."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l2_u3",
                "title": "Obligaciones y contratos",
                "title_ar": "الالتزامات والعقود",
                "lessons": [
                    {
                        "id": "es_l2_u3_l1",
                        "title": "Obligaciones y contratos",
                        "title_ar": "حق الالتزامات والعقود",
                        "subtitle": "Formación, cumplimiento y extinción de obligaciones",
                        "theory": (
                            "El derecho de obligaciones es una de las ramas más fundamentales del derecho civil español. "
                            "Una obligación es un vínculo jurídico por el que una o varias personas quedan "
                            "constreñidas a realizar una prestación determinada en favor de otra u otras personas.\n\n"
                            "Las fuentes de las obligaciones, recogidas en los artículos 1.089 y siguientes del Código Civil, son la ley, "
                            "los contratos y cuasicontratos, los actos y omisiones ilícitos y los cuasidelitos. El contrato es la fuente "
                            "más relevante. Para que un contrato sea válido requiere consentimiento, objeto cierto y causa.\n\n"
                            "La extinción de las obligaciones se produce por: pago, pérdida de la cosa debida, confusión "
                            "de los derechos de acreedor y deudor, compensación y novación.\n\n"
                            "Los modos de garantía incluyen la fianza, la hipoteca, el embargo y los privilegios. "
                            "La fianza es un contrato por el cual una persona se compromete a cumplir la obligación "
                            "principal si el deudor no lo hace."
                        ),
                        "theory_ar": (
                            "حق الالتزامات هو أحد الفروع الأكثر أساسية في القانون المدني الإسباني. الالتزام هو رابطة قانونية "
                            "يصبح بموجبها المدين ملزماً بتنفيذ التزام محدد.\n\n"
                            "مصادر الالتزامات المُكرَّسة في المواد 1089 وما بعدها هي: القانون والعقود وشبه العقود "
                            "والأفعال غير المشروعة وشبه الجرائم.\n\n"
                            "تنقطع الالتزامات بالتنفيذ أو تعذر الشيء أو بالالتباس أو بالتجديد.\n\n"
                            "تشمل ضمانات الالتزامات الكفالة والرهن العقاري والحجز والامتيازات."
                        ),
                        "vocab": [
                            {"fr": "la obligación", "ar": "الالتزام", "example": "La obligación es un vínculo jurídico entre acreedor y deudor."},
                            {"fr": "el contrato", "ar": "العقد", "example": "El contrato requiere consentimiento, objeto y causa."},
                            {"fr": "el consentimiento", "ar": "الرضا", "example": "El consentimiento debe ser libre y viciado de error o dolo."},
                            {"fr": "la novación", "ar": "التجديد", "example": "La novación extintiva sustituye la obligación anterior por una nueva."},
                            {"fr": "la fianza", "ar": "الكفالة", "example": "La fianza es un contrato accesorio que garantiza la obligación principal."},
                            {"fr": "la hipoteca", "ar": "الرهن العقاري", "example": "La hipoteca grava un inmueble en garantía de un préstamo."},
                            {"fr": "el pago", "ar": "التنفيذ", "example": "El pago extingue la obligación de manera natural."},
                            {"fr": "la compensación", "ar": "التعويض", "example": "La compensación se produce cuando dos personas son deudoras y acreedoras recíprocamente."},
                            {"fr": "la confusión de derechos", "ar": "الالتباس في الحقوق", "example": "La confusión se produce cuando acreedor y deudor se confunden."},
                            {"fr": "la responsabilidad civil contractual", "ar": "المسؤولية العقدية", "example": "La responsabilidad contractual nace del incumplimiento."},
                            {"fr": "la responsabilidad civil extracontractual", "ar": "المسؤولية ما بعد العقدية", "example": "La responsabilidad extracontractual se fundamenta en el artículo 1902."},
                            {"fr": "el embargo", "ar": "الحجز", "example": "El embargo garantiza la efectividad de la condena dineraria."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l2_u4",
                "title": "Responsabilidad civil",
                "title_ar": "المسؤولية المدنية",
                "lessons": [
                    {
                        "id": "es_l2_u4_l1",
                        "title": "Responsabilidad civil",
                        "title_ar": "المسؤولية المدنية في القانون الإسباني",
                        "subtitle": "Reparación del daño por hecho propio, ajeno o de las cosas",
                        "theory": (
                            "La responsabilidad civil es la obligación de reparar el daño causado a un tercero. En el derecho español, "
                            "se distingue entre responsabilidad civil contractual, que nace del incumplimiento de una obligación "
                            "contratual, y responsabilidad civil extracontractual, que se deriva de un hecho dañoso no "
                            "basado en un contrato previo.\n\n"
                            "La responsabilidad civil objetiva, regulada en los artículos 1.902 y siguientes del Código Civil, se fundamenta "
                            "en la culpa o negligencia del causante del daño. También existe responsabilidad objetiva sin culpa en "
                            "determinados supuestos: riesgo creado, daños causados por animales y por cosas inanimadas.\n\n"
                            "Los requisitos de la responsabilidad civil son: la antijuridicidad de la conducta, la existencia de un daño "
                            "efectivo y cuantificable, y el nexo causal entre la conducta y el daño. La indemnización debe reparar "
                            "integralmente el perjuicio, incluyendo daños materiales y morales.\n\n"
                            "La responsabilidad civil de los menores de edad se rige por el artículo 1.903 del Código Civil, que establece "
                            "una responsabilidad objetiva de los progenitores por los daños causados por sus hijos."
                        ),
                        "theory_ar": (
                            "المسؤولية المدنية هي الالتزام بتعويض الضرر الذي لحق بطرف ثالث. يُميّز القانون الإسباني بين المسؤولية "
                            "العقدية والمسؤولية غير العقدية.\n\n"
                            "المسؤولية الموضوعية تقوم على خطأ أو إهمال مسبب الضرر. توجد أيضاً مسؤولية موضوعية دون خطأ.\n\n"
                            "تشمل شروط المسؤولية المدنية: مخالفة السلوك للقانون ووجود فعل ضار فعلي ورابط سببي.\n\n"
                            "مسؤولية القاصرين تخضع للمادة 1903 التي تُقر مسؤولية الوالدين."
                        ),
                        "vocab": [
                            {"fr": "la responsabilidad civil", "ar": "المسؤولية المدنية", "example": "La responsabilidad civil contractual nace del contrato."},
                            {"fr": "la indemnización", "ar": "التعويض", "example": "La indemnización debe reparar integralmente el daño."},
                            {"fr": "el daño material", "ar": "الضرر المادي", "example": "El daño material incluye la pérdida patrimonial."},
                            {"fr": "el daño moral", "ar": "الضرر المعنوي", "example": "El daño moral se repara con una cantidad fijada por el juez."},
                            {"fr": "la culpa o negligencia", "ar": "الخطأ أو الإهمال", "example": "La culpa o negligencia es el fundamento de la responsabilidad civil."},
                            {"fr": "el nexo causal", "ar": "الرابط السببي", "example": "El nexo causal conecta la conducta con el daño causado."},
                            {"fr": "la responsabilidad objetiva", "ar": "المسؤولية الموضوعية", "example": "La responsabilidad objetiva prescinde de la culpa."},
                            {"fr": "el hecho propio", "ar": "الفعل الشخصي", "example": "La responsabilidad por hecho propio se basa en la culpa propia."},
                            {"fr": "el hecho ajeno", "ar": "فعل الغير", "example": "La responsabilidad por hecho ajeno se predica de los progenitores."},
                            {"fr": "el artículo 1902 del Código Civil", "ar": "المادة 1902 من القانون المدني", "example": "El artículo 1902 es la base de la responsabilidad extracontractual."},
                            {"fr": "la responsabilidad por vicios del producto", "ar": "المسؤولية عن عيوب المنتج", "example": "La responsabilidad por vicios protege al consumidor."},
                            {"fr": "la reparación integral", "ar": "التعويض الكامل", "example": "La reparación integral comprende todos los perjuicios sufridos."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l2_u5",
                "title": "Derecho mercantil",
                "title_ar": "القانون التجاري",
                "lessons": [
                    {
                        "id": "es_l2_u5_l1",
                        "title": "Derecho mercantil",
                        "title_ar": "القانون التجاري الإسباني",
                        "subtitle": "Comercio, sociedades y actos de comercio",
                        "theory": (
                            "El derecho mercantil regula las relaciones jurídicas derivadas del ejercicio del comercio. "
                            "El Código de Comercio español, aprobado en 1885, y la Ley de Sociedades de Capital de 2014 son "
                            "las normas fundamentales de esta materia.\n\n"
                            "Los actos de comercio se clasifican en actos objetivos y actos subjetivos. El comerciante es todo aquel que "
                            "ejerce actos de comercio y hace de ello su profesión habitual.\n\n"
                            "Las sociedades mercantiles se regulan por la Ley de Sociedades de Capital. Las formas más habituales "
                            "son la sociedad limitada (SL) y la sociedad anónima (SA). La SL tiene un capital social "
                            "dividido en participaciones sociales, mientras que la SA lo tiene dividido en acciones. "
                            "Ambas requieren inscripción en el Registro Mercantil.\n\n"
                            "El Derecho de Quiebras y suspensiones de pagos regula la situación del comerciante en estado "
                            "de insolvencia. El concurso de acreedores puede ser voluntario o necesario."
                        ),
                        "theory_ar": (
                            "القانون التجاري يُنظم العلاقات القانونية الناتجة عن ممارسة التجارة. "
                            "القانون التجاري الإسباني وقانون رأس المال الاجتماعي هما النصان الأساسيان.\n\n"
                            "تُصنّف الأفعال التجارية إلى أفعال موضوعية وأفعال ذاتية.\n\n"
                            "تُنظم الشركات التجارية بقانون رأس المال الاجتماعي. الأشكال الأكثر شيوعاً هي شركة المحدودة والشركة المساهمة.\n\n"
                            "قانون الإفلاس يُنظم حالة التاجر غير المعسر."
                        ),
                        "vocab": [
                            {"fr": "el acto de comercio", "ar": "العمل التجاري", "example": "Los actos de comercio se regulan por el Código de Comercio."},
                            {"fr": "el comerciante", "ar": "التاجر", "example": "El comerciante debe inscribirse en el Registro Mercantil."},
                            {"fr": "la sociedad limitada (SL)", "ar": "شركة المحدودة", "example": "La sociedad limitada tiene un capital mínimo de 3.000 euros."},
                            {"fr": "la sociedad anónima (SA)", "ar": "الشركة المساهمة", "example": "La sociedad anónima tiene un capital mínimo de 60.000 euros."},
                            {"fr": "el Registro Mercantil", "ar": "السجل التجاري", "example": "La inscripción en el Registro Mercantil es obligatoria."},
                            {"fr": "el concurso de acreedores", "ar": "إفلاس الدائنين", "example": "El concurso de acreedores puede ser voluntario o necesario."},
                            {"fr": "la letra de cambio", "ar": "الكمبيالة", "example": "La letra de cambio es un documento mercantil de pago."},
                            {"fr": "el pagaré", "ar": "السند الإذني", "example": "El pagaré es un documento de pago a la orden del beneficiario."},
                            {"fr": "el derecho concursal", "ar": "قانون الإفلاس", "example": "El derecho concursal regula la insolvencia del deudor."},
                            {"fr": "las participaciones sociales", "ar": "الحصص الاجتماعية", "example": "Las participaciones sociales son libremente transmisibles."},
                            {"fr": "los administradores", "ar": "الإدارة", "example": "Los administradores responden ante la sociedad por su gestión."},
                            {"fr": "el capital social", "ar": "رأس المال الاجتماعي", "example": "El capital social se integra por las aportaciones de los socios."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l2_u6",
                "title": "Derecho administrativo",
                "title_ar": "القانون الإداري",
                "lessons": [
                    {
                        "id": "es_l2_u6_l1",
                        "title": "Derecho administrativo",
                        "title_ar": "القانون الإداري الإسباني",
                        "subtitle": "Actos administrativos, procedimiento y contencioso",
                        "theory": (
                            "El derecho administrativo regula la organización, funcionamiento y potestades de la Administración Pública. "
                            "En España, el marco normativo fundamental es la Ley 39/2015 del Procedimiento Administrativo Común "
                            "y la Ley 40/2015 de Régimen Jurídico del Sector Público.\n\n"
                            "Los actos administrativos son las declaraciones de voluntad, juicio, conocimiento o deseo realizadas por un "
                            "órgano administrativo en el ejercicio de una potestad pública. Los requisitos de validez son: competencia, "
                            "finalidad, forma, motivo y causa.\n\n"
                            "El procedimiento administrativo se desarrolla en varias fases: iniciación, instrucción y terminación. "
                            "El silencio administrativo puede ser positivo o negativo según la naturaleza de la petición.\n\n"
                            "La jurisdicción contencioso-administrativa conoce de las reclamaciones contra los actos de la Administración. "
                            "El plazo general para interponer recurso contencioso-administrativo es de dos meses."
                        ),
                        "theory_ar": (
                            "القانون الإداري يُنظّم تنظيم وعمل وسلطات الإدارة العامة. في إسبانيا الإطار الأساسي هو قانون الإجراءات "
                            "الإدارية المشتركة وقانون النظام القانوني للقطاع العام.\n\n"
                            "القرارات الإدارية هي إرادات أو أحكام صادرة عن جهة إدارية.\n\n"
                            "يتضمن الإجراء الإداري عدة مراحل: البداية والتحقيق والانتهاء.\n\n"
                            "المنازعات الإدارية تنظر في الطعون ضد إجراءات الإدارة العامة."
                        ),
                        "vocab": [
                            {"fr": "el acto administrativo", "ar": "القرار الإداري", "example": "El acto administrativo requiere competencia, finalidad y causa."},
                            {"fr": "el procedimiento administrativo", "ar": "الإجراء الإداري", "example": "El procedimiento administrativo se inicia de oficio o a solicitud."},
                            {"fr": "el silencio administrativo", "ar": "صمت الإدارة", "example": "El silencio administrativo puede ser positivo o negativo."},
                            {"fr": "la potestad administrativa", "ar": "السلطة الإدارية", "example": "La potestad administrativa se ejerce conforme a la ley."},
                            {"fr": "el recurso contencioso-administrativo", "ar": "الطعن الإداري", "example": "El recurso se interpone ante la jurisdicción contencioso-administrativa."},
                            {"fr": "la nulidad de pleno derecho", "ar": "الإلغاء من الأول", "example": "El acto contrario a Derecho es nulo de pleno derecho."},
                            {"fr": "la anulabilidad", "ar": "القابلية للإلغاء", "example": "El acto viciado de anulabilidad puede ser convalidado."},
                            {"fr": "el interesado", "ar": "المعني", "example": "El interesado puede solicitar la revisión del acto."},
                            {"fr": "la Administración Pública", "ar": "الإدارة العامة", "example": "La Administración Pública actúa conforme a los principios de legalidad."},
                            {"fr": "el recurso de alzada", "ar": "الاستئناف الإداري", "example": "El recurso de alzada se interpone ante el superior jerárquico."},
                            {"fr": "la revisión de oficio", "ar": "المراجعة التلقائية", "example": "La revisión de oficio permite corregir actos ilegales."},
                            {"fr": "el plazo de dos meses", "ar": "المدة المحددة شهرين", "example": "El plazo para recurrir es de dos meses desde la notificación."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l2_u7",
                "title": "Derecho de propiedad",
                "title_ar": "حق الملكية",
                "lessons": [
                    {
                        "id": "es_l2_u7_l1",
                        "title": "Derecho de propiedad",
                        "title_ar": "حقوق الملكية في القانون الإسباني",
                        "subtitle": "Derechos reales y propiedad inmobiliaria",
                        "theory": (
                            "El derecho de propiedad es uno de los derechos más fundamentales del ordenamiento jurídico español. "
                            "El artículo 33 de la Constitución Española reconoce el derecho a la propiedad privada y a la herencia, "
                            "pero establece que su contenido se determinará por las leyes.\n\n"
                            "El Código Civil regula los derechos reales en los artículos 348 y siguientes. El derecho de propiedad "
                            "se define como el derecho de usar, disfrutar y disponer de un bien de manera exclusiva y excluyente. "
                            "Los derechos reales sobre bienes ajenos incluyen la hipoteca, el usufructo, la servidumbre y el derecho de superficie.\n\n"
                            "La transmisión de la propiedad inmobiliaria requiere la formalización de una escritura pública ante notario "
                            "y su inscripción en el Registro de la Propiedad.\n\n"
                            "El deslinde y amojonamiento son procedimientos para determinar los linderos de una finca. La servidumbre "
                            "es un gravamen impuesto sobre un bien en beneficio de otro. El tanto de retracto es el derecho del propietario "
                            "de una finca colindante a subrogarse en lugar del comprador."
                        ),
                        "theory_ar": (
                            "حق الملكية هو أحد أبسط الحقوق في النظام القانوني الإسباني. المادة 33 من الدستور تعترف بالملكية الخاصة.\n\n"
                            "يُنظم القانون المدني Rights العينية في المواد 348 وما بعدها.\n\n"
                            "تتطلب نقل ملكية العقارات توثيقاً رسمياً أمام موثق وتسجيلاً في سجل العقارات.\n\n"
                            "التدبير هو إجراء لتحديد حدود الأرض. الخدمة العينية هي تغرير يُفرض على شيء لفائدة شيء آخر."
                        ),
                        "vocab": [
                            {"fr": "la propiedad privada", "ar": "الملكية الخاصة", "example": "La propiedad privada es un derecho fundamental."},
                            {"fr": "el derecho real", "ar": "الحق العيني", "example": "Los derechos reales se ejercen sobre bienes inmuebles."},
                            {"fr": "el usufructo", "ar": "حق الانتفاع", "example": "El usufructuario puede usar y disfrutar del bien."},
                            {"fr": "la servidumbre", "ar": "الخدمة العينية", "example": "La servidumbre de paso permite el tránsito por finca ajena."},
                            {"fr": "la hipoteca", "ar": "الرهن العقاري", "example": "La hipoteca garantiza el pago de un préstamo hipotecario."},
                            {"fr": "el Registro de la Propiedad", "ar": "سجل العقارات", "example": "La inscripción en el Registro protege al adquirente."},
                            {"fr": "la escritura pública", "ar": "الوثيقة الرسمية", "example": "La escritura pública es requisito para transmitir la propiedad."},
                            {"fr": "el deslinde", "ar": "التدبير", "example": "El deslinde determina los linderos de una finca."},
                            {"fr": "el retracto", "ar": "حق الأولوية", "example": "El tanto de retracto permite al colindante subrogarse en la venta."},
                            {"fr": "la expropiación forzosa", "ar": "المصادرة القسرية", "example": "La expropiación forzosa se realiza por causa de utilidad pública."},
                            {"fr": "la usucapión", "ar": "التقادم المكتسب", "example": "La usucapión permite adquirir la propiedad por posesión prolongada."},
                            {"fr": "la ocupación", "ar": "الاستيلاء", "example": "La ocupación es un modo de adquirir la propiedad."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l2_u8",
                "title": "Derecho internacional privado",
                "title_ar": "القانون الدولي الخاص",
                "lessons": [
                    {
                        "id": "es_l2_u8_l1",
                        "title": "Derecho internacional privado",
                        "title_ar": "القانون الدولي الخاص الإسباني",
                        "subtitle": "Conflictos de leyes y de jurisdicción",
                        "theory": (
                            "El derecho internacional privado regula las relaciones jurídicas con un elemento extranjero. "
                            "Su objetivo principal es determinar la jurisdicción competente y la ley aplicable al caso concreto.\n\n"
                            "Los criterios de conexión permiten vincular una relación jurídica con un ordenamiento determinado. "
                            "Los más habituales son: la nacionalidad, el domicilio, la residencia habitual, el lugar de celebración del "
                            "contrato, el lugar de situación del bien inmueble, y la voluntad de las partes.\n\n"
                            "La ley aplicable se determina mediante normas de conflicto. Los Tratados Internacionales y los Reglamentos "
                            "Europeos proporcionan un marco normativo supranacional.\n\n"
                            "La lex fori es la ley del tribunal que conoce del asunto. La lex loci es la ley del lugar donde se celebró el "
                            "acto. La autocomposición de la ley a través de la cláusula de elección de ley es un principio reconocido."
                        ),
                        "theory_ar": (
                            "القانون الدولي الخاص يُنظم العلاقات القانونية ذات العنصر الأجنبي. هدفه الأساسي هو تحديد Jurisdicción "
                            "المختصة والقانون المطبق.\n\n"
                            "معايير الربط هي العناصر التي تربط العلاقة القانونية بنظام قانوني محدد.\n\n"
                            "يُحدد القانون المطبق بقواعد تعارض القوانين التي تحيل إلى نظام قانوني أجنبي.\n\n"
                            "Lex fori هي قانون المحكمة. Lex loci هي قانون مكان وقوع الفعل."
                        ),
                        "vocab": [
                            {"fr": "el derecho internacional privado", "ar": "القانون الدولي الخاص", "example": "El derecho internacional privado regula relaciones con elemento extranjero."},
                            {"fr": "el conflicto de leyes", "ar": "تعارض القوانين", "example": "El conflicto de leyes se resuelve mediante normas de conflicto."},
                            {"fr": "el conflicto de jurisdicciones", "ar": "تعارض الاختصاصات", "example": "El conflicto de jurisdicciones se resuelve por reglas de competencia."},
                            {"fr": "el criterio de conexión", "ar": "معيار الربط", "example": "El criterio de conexión más habitual es la residencia habitual."},
                            {"fr": "la lex fori", "ar": "قانون المحكمة", "example": "La lex fori se aplica cuando no hay conflicto de leyes."},
                            {"fr": "la lex loci", "ar": "قانون مكان الواقعة", "example": "La lex loci regula la forma del acto jurídico."},
                            {"fr": "la elección de ley", "ar": "اختيار القانون", "example": "Las partes pueden elegir la ley aplicable al contrato."},
                            {"fr": "el domicilio", "ar": "الإقامة", "example": "El domicilio determina la competencia general del juez."},
                            {"fr": "la residencia habitual", "ar": "الإقامة المعتادة", "example": "La residencia habitual es criterio de conexión contractual."},
                            {"fr": "el Reglamento Roma I", "ar": "اللائحة روما الأولى", "example": "El Reglamento Roma I regula la ley contractual entre Estados miembros."},
                            {"fr": "la exequátur", "ar": "التنفيذ الأجنبي", "example": "La exequátur es el procedimiento para reconocer una sentencia extranjera."},
                            {"fr": "el Tratado Internacional", "ar": "المعاهدة الدولية", "example": "El Tratado Internacional prevalece sobre la legislación interna."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l2_u9",
                "title": "Medios de impugnación",
                "title_ar": "وسائل الطعن",
                "lessons": [
                    {
                        "id": "es_l2_u9_l1",
                        "title": "Medios de impugnación",
                        "title_ar": "وسائل الطعن في القانون الإسباني",
                        "subtitle": "Apelación, casación y recursos extraordinarios",
                        "theory": (
                            "Los medios de impugnación son los mecanismos procesales que permiten a las partes solicitar la revisión "
                            "de una resolución judicial. El sistema procesal español reconoce diversos tipos de recursos.\n\n"
                            "El recurso de apelación es el recurso ordinario contra las sentencias dictadas en primera instancia. "
                            "El plazo para interponerlo es de veinte días desde la notificación de la sentencia. La apelación tiene "
                            "efecto devolutivo.\n\n"
                            "El recurso de casación es un recurso extraordinario ante el Tribunal Supremo. Solo procede cuando existe "
                            "un interés casacional objetivo, entendido como la existencia de doctrina jurisprudencial contradictoria "
                            "o la necesidad de fijar criterio sobre una cuestión novedosa.\n\n"
                            "El recurso de amparo se interpone ante el Tribunal Constitucional y protege los derechos fundamentales. "
                            "El recurso de queja se utiliza contra el auto de inadmisión de un recurso."
                        ),
                        "theory_ar": (
                            "وسائل الطعن هي الآليات الإجرائية التي تتيح للأطراف طلب مراجعة قرار قضائي. "
                            "يتعرف النظام الإسباني على أنواع متعددة.\n\n"
                            "الاستئناف هو الطعن العادي ضد الأحكام الصادرة في درجة أولى. الميعاد عشرون يوماً.\n\n"
                            "الطعن بالنقض هو طعن استثنائي أمام المحكمة العليا. لا يُقبل إلا إذا وُجد مصلحة في النقض.\n\n"
                            "الطعن الدستوري يُقدم أمام المحكمة الدستورية ويحمي الحقوق الأساسية."
                        ),
                        "vocab": [
                            {"fr": "el recurso de apelación", "ar": "الاستئناف", "example": "El recurso de apelación se interpone en veinte días."},
                            {"fr": "el recurso de casación", "ar": "الطعن بالنقض", "example": "El recurso de casación se interpone ante el Tribunal Supremo."},
                            {"fr": "el recurso de amparo", "ar": "الطعن الدستوري", "example": "El recurso de amparo protege los derechos fundamentales."},
                            {"fr": "el recurso de queja", "ar": "طعن الشكوى", "example": "El recurso de queja se interpone contra el auto de inadmisión."},
                            {"fr": "la Audiencia Provincial", "ar": "المحكمة الإقليمية", "example": "La Audiencia Provincial conoce de los recursos de apelación civil."},
                            {"fr": "el Tribunal Constitucional", "ar": "المحكمة الدستورية", "example": "El Tribunal Constitucional conoce de los recursos de amparo."},
                            {"fr": "el interés casacional", "ar": "المصلحة في النقض", "example": "El interés casacional es requisito para la admisión del recurso."},
                            {"fr": "el efecto devolutivo", "ar": "التأثير الإجرائي", "example": "El efecto devolutivo transfiere el conocimiento al tribunal superior."},
                            {"fr": "el plazo de veinte días", "ar": "المدة المحددة عشرين يوماً", "example": "El plazo para apelar es de veinte días desde la notificación."},
                            {"fr": "la unificación de doctrina", "ar": "توحيد الاجتهاد", "example": "El recurso de casación busca la unificación de doctrina."},
                            {"fr": "la sentencia firme", "ar": "الحكم النهائي", "example": "La sentencia firme no admite recurso ordinario."},
                            {"fr": "el recurso extraordinario", "ar": "الاستئناف الاستثنائي", "example": "Los recursos extraordinarios tienen requisitos más estrictos."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l2_u10",
                "title": "La prueba en el proceso",
                "title_ar": "الإثبات في الإجراءات",
                "lessons": [
                    {
                        "id": "es_l2_u10_l1",
                        "title": "La prueba en el proceso",
                        "title_ar": "نظام الإثبات في القانون الإسباني",
                        "subtitle": "Medios de prueba, carga y valoración",
                        "theory": (
                            "La prueba es el conjunto de medios procesales mediante los cuales las partes acreditan la certeza de los "
                            "hechos que constituyen el objeto del litigio. En el derecho español, la carga de la prueba recae sobre "
                            "quien afirma un hecho favorable a su pretensión, conforme al artículo 217 de la Ley de Enjuiciamiento Civil.\n\n"
                            "Los medios de prueba admisibles son: el interrogatorio de las partes, la prueba documental, la prueba pericial, "
                            "la prueba testifical, el reconocimiento judicial y la prueba de absolución en rubrica.\n\n"
                            "La prueba documental comprende documentos públicos y privados. Los documentos públicos gozan de plena prueba. "
                            "Los documentos privados solo tienen valor probatorio entre las partes que los otorgaron.\n\n"
                            "La prueba pericial es aquella en la que un experto emite un dictamen sobre cuestiones que requieren "
                            "conocimientos especializados. El juez valorará la prueba según las reglas de la sana crítica."
                        ),
                        "theory_ar": (
                            "الإثبات هو مجموعة الوسائل الإجرائية التي تُستخدمها الأطراف لإثبات صدق الوقائع. "
                            "في القانون الإسباني تقع عبء الإثبات على من يدّعي وقائع مواتية.\n\n"
                            "تشمل أدلة الإثبات: استجواب الأطراف والإثبات المستندي والخبري والشهادات والمعاينة القضائية.\n\n"
                            "يشمل الإثبات المستندي المستندات العامة والخاصة.\n\n"
                            "الإثبات الخبري هو الذي يُقدم فيه خبير رأيه. يُقيّم القاضي الإثبات حسب قواعد النقد السليم."
                        ),
                        "vocab": [
                            {"fr": "la carga de la prueba", "ar": "عبء الإثبات", "example": "La carga de la prueba corresponde a quien afirma el hecho."},
                            {"fr": "la prueba testifical", "ar": "الإثبات بالشهادات", "example": "La prueba testifical se practica mediante interrogatorio de testigos."},
                            {"fr": "la prueba documental", "ar": "الإثبات المستندي", "example": "La prueba documental comprende documentos públicos y privados."},
                            {"fr": "la prueba pericial", "ar": "الخبرة", "example": "El dictamen pericial explica las cuestiones técnicas del caso."},
                            {"fr": "el interrogatorio", "ar": "الاستجواب", "example": "El interrogatorio de las partes puede ser decisivo."},
                            {"fr": "el reconocimiento judicial", "ar": "المعاينة القضائية", "example": "El juez realiza el reconocimiento judicial en el lugar de los hechos."},
                            {"fr": "el documento público", "ar": "المستند العام", "example": "El documento público otorgado por notario tiene plena prueba."},
                            {"fr": "el documento privado", "ar": "المستند الخاص", "example": "El documento privado solo tiene eficacia entre las partes."},
                            {"fr": "el dictamen pericial", "ar": "تقرير الخبرة", "example": "El dictamen pericial es un elemento clave para la valoración judicial."},
                            {"fr": "la valoración judicial de la prueba", "ar": "تقييم الإثبات القضائي", "example": "El juez valora la prueba según las reglas de la sana crítica."},
                            {"fr": "la presunción", "ar": "الاستنتاج", "example": "Las presunciones son consecuencias deducidas de un hecho conocido."},
                            {"fr": "la prueba ilícita", "ar": "الإثبات غير القانوني", "example": "La prueba ilícita es inadmisible por vulnerar derechos fundamentales."},
                        ],
                    },
                ],
            },
        ],
    },
    # ─── Nivel 3 — Avanzado ──────────────────────────────────────────
    {
        "id": 3,
        "title": "Avanzado — المتقدم",
        "description": "Redacción jurídica y técnica de litigación",
        "color": "#d97706",
        "units": [
            {
                "id": "es_l3_u1",
                "title": "Redacción de escritos judiciales",
                "title_ar": "كتابة المذكرات القضائية",
                "lessons": [
                    {
                        "id": "es_l3_u1_l1",
                        "title": "Redacción de escritos judiciales",
                        "title_ar": "كتابة المذكرات القضائية الإسبانية",
                        "subtitle": "Técnicas de redacción jurídica y estilo forense",
                        "theory": (
                            "La redacción de escritos judiciales es una de las competencias fundamentales del abogado español. "
                            "Un escrito bien redactado no solo comunica los argumentos jurídicos con claridad, sino que también "
                            "refleja la profesionalidad y la rigurosidad del letrado que lo suscribe.\n\n"
                            "Los escritos judiciales deben cumplir requisitos formales y sustantivos. Entre los primeros se encuentran "
                            "la identificación de las partes, la designación del procurador, la enumeración de hechos y fundamentos "
                            "jurídicos, y la firma del abogado y procurador. Entre los segundos destaca la claridad expositiva, "
                            "la precisión terminológica y la coherencia argumentativa.\n\n"
                            "El lenguaje jurídico utilizado debe ser formal, preciso y técnico. Se emplean fórmulas sacramentales como "
                            "\"DIGO que\" para los hechos, \"FUNDAMENTO DE DERECHO\" para las normas, y \"SOLICITO que\" para las peticiones.\n\n"
                            "La estructura lógica del escrito debe seguir un orden cronológico de los hechos, una fundamentación jurídica "
                            "precisa que cite la norma aplicable y la jurisprudencia relevante, y unas peticiones concretas y medibles."
                        ),
                        "theory_ar": (
                            "كتابة المذكرات القضائية هي واحدة من الكفاءات الأساسية للمحامي الإسباني. المذكرة المكتوبة جيداً لا تُunicamente "
                            "تُواصل الحجج القانونية بوضوح بل تعكس احترافية المحامي.\n\n"
                            "تتطلب المذكرات القضائية متطلبات شكلية وموضوعية.\n\n"
                            "يجب أن يكون اللغة القانونية المستخدمة رسمياً ودقيقة وتقنية. تُستخدم صيغ ثابتة.\n\n"
                            "يجب أن تتبع البنية المنطقية تسلسلاً زمنياً للأحداث وأسساً قانونية دقيقة."
                        ),
                        "vocab": [
                            {"fr": "DIGO que", "ar": "أقول أن", "example": "DIGO que, conforme al artículo 1902 del Código Civil."},
                            {"fr": "FUNDAMENTO DE DERECHO", "ar": "الأساس القانوني", "example": "FUNDAMENTO DE DERECHO: Primero.- Conforme al artículo..."},
                            {"fr": "SOLICITO que", "ar": "أطلب أن", "example": "SOLICITO que se condene al demandado al pago."},
                            {"fr": "TERMINO suplicando", "ar": "أنهي بال RequestContext أن", "example": "TERMINO suplicando que se dicte sentencia estimatoria."},
                            {"fr": "Otrosí digo", "ar": "أقول أيضاً", "example": "Otrosí digo que, con independencia de lo anterior..."},
                            {"fr": "la demanda", "ar": "الدعوى", "example": "La demanda debe cumplir los requisitos del artículo 399 LEC."},
                            {"fr": "el escrito de conclusiones", "ar": "مذكرة النتائج", "example": "El escrito de conclusiones resume los argumentos de cada parte."},
                            {"fr": "el procurador", "ar": "الممثل القانوني", "example": "El procurador representa legalmente al demandante."},
                            {"fr": "la firme y ruego", "ar": "أوقع وأطلب", "example": "Firme y ruego que se tenga por presentado el escrito."},
                            {"fr": "la notificación", "ar": "التبليغ", "example": "La notificación es el acto procesal por el que se da conocimiento."},
                            {"fr": "el expediente", "ar": "الملف", "example": "El expediente contiene todos los escritos del proceso."},
                            {"fr": "la copia para la parte contraria", "ar": "النسخة للطرف المقابل", "example": "Se acompaña copia simple para la parte contraria."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l3_u2",
                "title": "Interpretación de leyes",
                "title_ar": "تفسير القوانين",
                "lessons": [
                    {
                        "id": "es_l3_u2_l1",
                        "title": "Interpretación de leyes",
                        "title_ar": "تفسير القوانين في القانون الإسباني",
                        "subtitle": "Métodos y criterios hermenéuticos",
                        "theory": (
                            "La interpretación de las normas jurídicas es una actividad fundamental del operador jurídico. "
                            "En el sistema español, el Código Civil contiene una norma sobre interpretación en sus artículos 3.1 y 3.2.\n\n"
                            "Los métodos clásicos de interpretación incluyen: el método literal, que se atiene al significado gramatical; "
                            "el método teleológico, que busca la finalidad de la norma; el método sistemático, que sitúa la norma en "
                            "el contexto del ordenamiento completo; y el método histórico, que atiende a la intención del legislador.\n\n"
                            "El artículo 3.1 del Código Civil establece que las normas se interpretarán \"según el sentido propio de sus "
                            "palabras, en relación con el contexto, los antecedentes históricos y legislativos, y la realidad social del "
                            "tiempo en que han de ser aplicadas\".\n\n"
                            "La interpretación auténtica, realizada por el propio legislador, prevalece sobre cualquier otra. "
                            "La interpretación judicial adquiere especial relevancia a través de la jurisprudencia del Tribunal Supremo."
                        ),
                        "theory_ar": (
                            "تفسير القواعد القانونية هو نشاط أساسي للمoperator القانوني. في النظام الإسباني يحتوي القانون المدني "
                            "على قاعدة تفسيرية في مادتيه 3.1 و3.2.\n\n"
                            "تشمل الأساليب الكلاسيكية: الأسلوب الحرفي والأسلوب الهادف والأسلوب المنهجي والأسلوب التاريخي.\n\n"
                            "تنص المادة 3.1 على أن القواعد تُفسر حسب معناها الحرفي وفي سياقها وتاريخها وواقعها الاجتماعي.\n\n"
                            "التفسير الأصلي الذي يُمارسه المشرع نفسه يتفوق على أي تفسير آخر."
                        ),
                        "vocab": [
                            {"fr": "la interpretación literal", "ar": "التفسير الحرفي", "example": "La interpretación literal atiende al significado de las palabras."},
                            {"fr": "la interpretación teleológica", "ar": "التفسير الهادف", "example": "La interpretación teleológica busca la finalidad de la norma."},
                            {"fr": "la interpretación sistemática", "ar": "التفسير المنهجي", "example": "La interpretación sistemática sitúa la norma en su contexto."},
                            {"fr": "la interpretación histórica", "ar": "التفسير التاريخي", "example": "La interpretación histórica atiende a la intención del legislador."},
                            {"fr": "la interpretación auténtica", "ar": "التفسير الأصلي", "example": "La interpretación auténtica prevalece sobre otras interpretaciones."},
                            {"fr": "la jurisprudencia", "ar": "الاجتهاد القضائي", "example": "La jurisprudencia del Tribunal Supremo fija criterios interpretativos."},
                            {"fr": "el contexto normativo", "ar": "السياق القانوني", "example": "El contexto normativo es esencial para la interpretación."},
                            {"fr": "la realidad social", "ar": "الواقع الاجتماعي", "example": "La interpretación debe ajustarse a la realidad social del momento."},
                            {"fr": "la ratio legis", "ar": "سبب القانون", "example": "La ratio legis es el fundamento racional de la norma."},
                            {"fr": "la duda interpretativa", "ar": "الشك التفسيري", "example": "En caso de duda, se adopta la interpretación más favorable al derecho."},
                            {"fr": "la integración de lagunas", "ar": "سد الفراغات", "example": "La integración de lagunas se realiza por analogía."},
                            {"fr": "el uso y la costumbre", "ar": "العرف والاستعمال", "example": "El uso y la costumbre completan la interpretación de la norma."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l3_u3",
                "title": "La demanda y la contestación",
                "title_ar": "الدعوى والرد عليها",
                "lessons": [
                    {
                        "id": "es_l3_u3_l1",
                        "title": "La demanda y la contestación",
                        "title_ar": "الدعوى المدنية والرد عليها",
                        "subtitle": "Técnicas de redacción de demandas y contestaciones",
                        "theory": (
                            "La demanda y la contestación son los escritos fundamentales del proceso civil. La demanda es el escrito "
                            "por el que el demandante ejercita una o varias acciones frente a una o varias personas.\n\n"
                            "La demanda debe cumplir los requisitos del artículo 399 de la LEC: designación del juzgado competente, "
                            "identificación del demandante y demandado, una narración de los hechos, fundamentos jurídicos, "
                            "y una petición concreta.\n\n"
                            "La contestación a la demanda debe ser igualmente rigurosa. El demandado puede: confessar los hechos, "
                            "negarlos, oponer excepciones procesales, proponer reconvención, o alegar hechos nuevos.\n\n"
                            "La réplica y la duplica son escritos complementarios que permiten a las partes concretar sus posiciones "
                            "después de la contestación. Estos escritos no son obligatorios, pero pueden ser convenientes."
                        ),
                        "theory_ar": (
                            "الدعوى والرد عليها هي المذكرات الأساسية في الإجراءات المدنية.\n\n"
                            "يجب أن تُلبي الدعوى المتطلبات الشكلية للمادة 399 من قانون الإجراءات المدنية.\n\n"
                            "الرد على الدعوى يجب أن يكون صارماً أيضاً.\n\n"
                            "الرد المضاد والمضاد للرد هما مذكرات تكميلية تتيح للأطراف تحديد مواقفهم."
                        ),
                        "vocab": [
                            {"fr": "la demanda", "ar": "الدعوى المدنية", "example": "La demanda fue admitida a trámite por el juzgado."},
                            {"fr": "la contestación a la demanda", "ar": "الرد على الدعوى", "example": "La contestación debe presentarse en el plazo de veinte días."},
                            {"fr": "la reconvención", "ar": "الدعوى المتقابلة", "example": "La reconvención se formula en la contestación a la demanda."},
                            {"fr": "la réplica", "ar": "الرد المضاد", "example": "El demandante formuló réplica para matizar sus pretensiones."},
                            {"fr": "la duplica", "ar": "الرد على الرد المضاد", "example": "El demandado presentó duplica para defender sus argumentos."},
                            {"fr": "la excepción procesal", "ar": "الاستثناء الإجرائي", "example": "Se opuso excepción de incompetencia del juzgado."},
                            {"fr": "la cosa juzgada", "ar": "الحكم القضائي القطعي", "example": "La cosa juzgada impide la reiteración de la misma pretensión."},
                            {"fr": "la prescripción", "ar": "التقادم", "example": "La prescripción extingue la acción después de un plazo legal."},
                            {"fr": "el fundamento jurídico", "ar": "الأساس القانوني", "example": "El fundamento jurídico debe citar la norma aplicable."},
                            {"fr": "la narración de hechos", "ar": "سرد الوقائع", "example": "La narración de hechos debe ser cronológica y precisa."},
                            {"fr": "la petición concreta", "ar": "المطلب المحدد", "example": "La petición concreta permite al juez pronunciarse."},
                            {"fr": "el documento justificativo", "ar": "المستند التأسيسي", "example": "Los documentos justificativos acreditan los hechos alegados."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l3_u4",
                "title": "El recurso de apelación",
                "title_ar": "استئناف الحكم",
                "lessons": [
                    {
                        "id": "es_l3_u4_l1",
                        "title": "El recurso de apelación",
                        "title_ar": "استئناف الأحكام في القانون الإسباني",
                        "subtitle": "Procedimiento y requisitos del recurso de apelación",
                        "theory": (
                            "El recurso de apelación es el medio procesal mediante el cual una parte solicita al tribunal superior "
                            "que revoque o modifique una sentencia dictada en primera instancia.\n\n"
                            "No son apelables los autos que no pongan fin al procedimiento, salvo que contengan un pronunciamiento "
                            "sobre el fondo. El escrito de apelación debe expresar las causas que motivan la impugnación.\n\n"
                            "El plazo para interponer el recurso es de veinte días desde la notificación de la resolución, y se interpone "
                            "ante el juzgado que dictó la resolución impugnada.\n\n"
                            "La Audiencia Provincial examina el recurso de apelación. En esta segunda instancia, la prueba solo puede "
                            "proponerse si existe causa justificada. El tribunal puede confirmar, revocar o modificar la sentencia apelada."
                        ),
                        "theory_ar": (
                            "الاستئناف هو الآلية الإجرائية التي يطلب بموجبها طرف من المحكمة العليا إلغاء أو تعديل حكم.\n\n"
                            "لا يُستأنف الأوامر التي لا تنهي الإجراءات إلا إذا تضمّنت حكماً في الموضوع.\n\n"
                            "الميعاد عشرون يوماً من تبليغ القرار.\n\n"
                            "المحكمة الإقليمية كمحكمة استئناف تفحص الطعن. يمكن للمحكمة تأكيد أو إلغاء أو تعديل الحكم المستأنف."
                        ),
                        "vocab": [
                            {"fr": "el recurso de apelación", "ar": "الاستئناف", "example": "El recurso de apelación se interpone en veinte días."},
                            {"fr": "la sentencia apelada", "ar": "الحكم المستأنف", "example": "La sentencia apelada fue modificada por la Audiencia."},
                            {"fr": "la Audiencia Provincial", "ar": "المحكمة الإقليمية", "example": "La Audiencia Provincial conoce en segunda instancia."},
                            {"fr": "las causas de impugnación", "ar": "أسباب الطعن", "example": "Las causas de impugnación deben expresarse en el escrito."},
                            {"fr": "el plazo de veinte días", "ar": "المدة المحددة عشرين يوماً", "example": "El plazo para apelar es de veinte días hábiles."},
                            {"fr": "la revocación", "ar": "الإلغاء", "example": "El tribunal puede revocar total o parcialmente la sentencia."},
                            {"fr": "la confirmación", "ar": "التأكيد", "example": "La confirmación de la sentencia mantiene sus pronunciamientos."},
                            {"fr": "la modificación", "ar": "التعديل", "example": "La modificación ajusta determinados pronunciamientos."},
                            {"fr": "la segunda instancia", "ar": "الدرجة الثانية", "example": "La segunda instancia permite revisar la resolución impugnada."},
                            {"fr": "la prueba en segunda instancia", "ar": "الإثبات في الدرجة الثانية", "example": "La prueba solo puede proponerse si existe causa justificada."},
                            {"fr": "el recurso contra autos", "ar": "الطعن ضد الأوامر", "example": "No todos los autos son susceptibles de recurso de apelación."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l3_u5",
                "title": "Derecho probatorio",
                "title_ar": "قانون الإثبات",
                "lessons": [
                    {
                        "id": "es_l3_u5_l1",
                        "title": "Derecho probatorio",
                        "title_ar": "قانون الإثبات في القانون الإسباني",
                        "subtitle": "Reglas de admisión, práctica y valoración de la prueba",
                        "theory": (
                            "El derecho probatorio constituye uno de los pilares del proceso judicial. En España, las reglas de "
                            "admisión, práctica y valoración de la prueba están reguladas en la LEC de 2000, arts. 265 a 432.\n\n"
                            "La admisión de la prueba se realiza en la audiencia previa al juicio oral. El juez examina la pertinencia "
                            "y la utilidad de los medios de prueba propuestos.\n\n"
                            "La carga de la prueba sigue el principio de que \"affirmanti non neganti incumbit probatio\". "
                            "El artículo 217 de la LEC establece las reglas especiales de distribución de la carga de la prueba.\n\n"
                            "La valoración de la prueba es libre, pero racional. El juez valora la prueba personal según las reglas "
                            "de la sana crítica, y la prueba documental y pericial con apreciación razonada."
                        ),
                        "theory_ar": (
                            "قانون الإثبات يُشكّل أحد ركائز الإجراءات القضائية.\n\n"
                            "يتم قبول الإثبات في الجلسة التحضيرية قبل الجلسة الصوتية.\n\n"
                            "عبء الإثبات يقع على من يدّعي.\n\n"
                            "تقييم الإثبات حر لكنه منطقي."
                        ),
                        "vocab": [
                            {"fr": "la carga de la prueba", "ar": "عبء الإثبات", "example": "La carga de la prueba corresponde a quien afirma el hecho."},
                            {"fr": "la prueba testifical", "ar": "الإثبات بالشهادات", "example": "La prueba testifical se practica mediante interrogatorio."},
                            {"fr": "la prueba documental", "ar": "الإثبات المستندي", "example": "La prueba documental comprende documentos públicos y privados."},
                            {"fr": "la prueba pericial", "ar": "الخبرة", "example": "El dictamen pericial explica las cuestiones técnicas."},
                            {"fr": "el interrogatorio", "ar": "الاستجواب", "example": "El interrogatorio de las partes puede ser decisivo."},
                            {"fr": "el reconocimiento judicial", "ar": "المعاينة القضائية", "example": "El juez realiza el reconocimiento judicial en el lugar de los hechos."},
                            {"fr": "el documento público", "ar": "المستند العام", "example": "El documento público tiene plena prueba."},
                            {"fr": "el documento privado", "ar": "المستند الخاص", "example": "El documento privado solo tiene eficacia entre las partes."},
                            {"fr": "el dictamen pericial", "ar": "تقرير الخبرة", "example": "El dictamen pericial es un elemento clave."},
                            {"fr": "la valoración judicial", "ar": "التقييم القضائي", "example": "El juez valora la prueba según la sana crítica."},
                            {"fr": "la presunción", "ar": "الاستنتاج", "example": "Las presunciones se deducen de un hecho conocido."},
                            {"fr": "la prueba ilícita", "ar": "الإثبات غير القانوني", "example": "La prueba ilícita es inadmisible."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l3_u6",
                "title": "Arbitraje",
                "title_ar": "التحكيم",
                "lessons": [
                    {
                        "id": "es_l3_u6_l1",
                        "title": "Arbitraje",
                        "title_ar": "التحكيم في القانون الإسباني",
                        "subtitle": "Resolución alternativa de conflictos",
                        "theory": (
                            "El arbitraje es un mecanismo de resolución alternativa de conflictos por el que las partes someten "
                            "sus controversias a la decisión de uno o más árbitros. En España, la Ley 60/2003, de 23 de diciembre, "
                            "de Arbitraje regula este procedimiento.\n\n"
                            "El convenio arbitral es el acuerdo por el que las partes deciden someter a arbitraje todas o algunas "
                            "de las controversias. Puede adoptar la forma de cláusula compromisoria o de compromiso arbitral.\n\n"
                            "El procedimiento arbitral puede ser de derecho o de equidad. En el arbitraje de derecho, el árbitro "
                            "decide conforme a las normas jurídicas aplicables. En el arbitraje de equidad, el árbitro decide "
                            "conforme a criterios de equidad y justicia.\n\n"
                            "El laudo arbitral es la resolución que pone fin al procedimiento arbitral. Tiene efectos de cosa juzgada "
                            "y puede ser objeto de anulación ante los tribunales ordinarios por causas tasadas."
                        ),
                        "theory_ar": (
                            "التحكيم هو آليّة لحل النزاعات البديلة التي يُقدم فيها الأطراف خلافاتهم لقرار من حكم أو أكثر.\n\n"
                            "اتفاق التحكيم هو اتفاق تتخضع بموجبه الأطراف للتحكيم.\n\n"
                            "يمكن أن يكون الإجراء التحكيمي قانونياً أو عادلاً.\n\n"
                            "الحكم التحكيمي هو القرار الذي ينهي الإجراء ويملك قوة الحكم القضائي القطعي."
                        ),
                        "vocab": [
                            {"fr": "el arbitraje", "ar": "التحكيم", "example": "El arbitraje es un mecanismo de resolución alternativa de conflictos."},
                            {"fr": "el convenio arbitral", "ar": "اتفاق التحكيم", "example": "El convenio arbitral somete las controversias a decisión del árbitro."},
                            {"fr": "la cláusula compromisoria", "ar": "بند التحكيم", "example": "La cláusula compromisoria se incluye en un contrato principal."},
                            {"fr": "el compromiso arbitral", "ar": "عقد التحكيم", "example": "El compromiso arbitral se celebra después de surgir la controversia."},
                            {"fr": "el árbitro / la árbitro", "ar": "الحكيم", "example": "El árbitro debe ser independiente e imparcial."},
                            {"fr": "el laudo arbitral", "ar": "الحكم التحكيمي", "example": "El laudo arbitral tiene efectos de cosa juzgada."},
                            {"fr": "el arbitraje de derecho", "ar": "التحكيم القانوني", "example": "En el arbitraje de derecho, el árbitro decide conforme a las normas."},
                            {"fr": "el arbitraje de equidad", "ar": "التحكيم العادل", "example": "En el arbitraje de equidad, el árbitro decide por criterios de justicia."},
                            {"fr": "la anulación del laudo", "ar": "إلغاء الحكم التحكيمي", "example": "El laudo puede ser anulado ante los tribunales ordinarios."},
                            {"fr": "el Centro de Arbitraje", "ar": "مركز التحكيم", "example": "El Centro de Arbitraje administra los procedimientos arbitrales."},
                            {"fr": "la impugnación del laudo", "ar": "طعن الحكم التحكيمي", "example": "La impugnación del laudo solo procede por causas tasadas."},
                            {"fr": "el derecho aplicable", "ar": "القانون المطبق", "example": "El árbitro determina el derecho aplicable a la controversia."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l3_u7",
                "title": "Derecho europeo",
                "title_ar": "القانون الأوروبي",
                "lessons": [
                    {
                        "id": "es_l3_u7_l1",
                        "title": "Derecho europeo",
                        "title_ar": "القانون الأوروبي والمكاسب الأوروبية",
                        "subtitle": "Derecho de la Unión Europea y su impacto en España",
                        "theory": (
                            "El derecho europeo comprende el conjunto de normas jurídicas emanadas de las instituciones de la Unión Europea "
                            "que son directamente aplicables o indirectamente integradas en los ordenamientos de los Estados miembros. "
                            "España, como Estado miembro de la Unión Europea, está vinculada por el derecho comunitario.\n\n"
                            "Las fuentes del derecho europeo incluyen los Tratados constitutivos (Tratado de la UE y Tratado de funcionamiento), "
                            "las Directivas, los Reglamentos, las Decisiones y las Recomendaciones. Los Reglamentos son directamente "
                            "aplicables en todos los Estados miembros. Las Directivas requieren una transposición al derecho interno.\n\n"
                            "El principio de primacía del derecho europeo implica que en caso de conflicto entre una norma europea "
                            "y una norma nacional, prevalece la primera. El principio de efecto directo permite a los ciudadanos "
                            "invocar directamente el derecho europeo ante sus tribunales nacionales.\n\n"
                            "El Tribunal de Justicia de la Unión Europea, con sede en Luxemburgo, es el órgano jurisdiccional que "
                            "garantiza la interpretación y aplicación uniforme del derecho europeo. Las cuestiones prejudiciales "
                            "permiten a los tribunales nacionales consultar al Tribunal de Luxemburgo sobre la interpretación del derecho europeo."
                        ),
                        "theory_ar": (
                            "القانون الأوروبي يشمل مجموعة القواعد القانونية الصادرة عن مؤسسات الاتحاد الأوروبي. إسبانيا كعضو في الاتحاد "
                            "مرتبطة بالقانون الأوروبي.\n\n"
                            "تشمل مصادر القانون الأوروبي المعاهدات والتعليمات واللائحيات والقرارات والتوصيات.\n\n"
                            "مبدأ سبق القانون الأوروبي يعني أن القاعدة الأوروبية تتفوق على القاعدة الوطنية في حالة التعارض.\n\n"
                            "محكمة العدل للاتحاد الأوروبي تضمن التفسير الموحد للقانون الأوروبي."
                        ),
                        "vocab": [
                            {"fr": "el derecho europeo", "ar": "القانون الأوروبي", "example": "El derecho europeo es directamente aplicable en los Estados miembros."},
                            {"fr": "el Reglamento europeo", "ar": "اللائحة الأوروبية", "example": "El Reglamento europeo es directamente aplicable."},
                            {"fr": "la Directiva europea", "ar": "التعليمية الأوروبية", "example": "La Directiva debe ser transpuesta al derecho interno."},
                            {"fr": "la primacía del derecho europeo", "ar": "سبق القانون الأوروبي", "example": "La primacía del derecho europeo prevalece sobre el derecho nacional."},
                            {"fr": "el efecto directo", "ar": "المفعول المباشر", "example": "El efecto directo permite invocar el derecho europeo ante los tribunales."},
                            {"fr": "el Tribunal de Justicia de la UE", "ar": "محكمة العدل للاتحاد الأوروبي", "example": "El Tribunal de Justicia garantiza la interpretación uniforme."},
                            {"fr": "la cuestión prejudicial", "ar": "المسألة التمهيدية", "example": "Las cuestiones prejudiciales permiten consultar al Tribunal de Luxemburgo."},
                            {"fr": "la transposición", "ar": "النقل", "example": "La transposición de Directivas adapta el derecho interno."},
                            {"fr": "el Tratado de la UE", "ar": "معاهدة الاتحاد الأوروبي", "example": "El Tratado de la UE es la norma fundacional."},
                            {"fr": "el Estado miembro", "ar": "الدولة العضو", "example": "Cada Estado miembro debe aplicar el derecho europeo."},
                            {"fr": "la Directiva de transposición", "ar": "تعليمية النقل", "example": "La Directiva de transposición debe incorporarse al derecho nacional."},
                            {"fr": "el derecho derivado", "ar": "القانون المشتق", "example": "El derecho derivado incluye Reglamentos y Directivas."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l3_u8",
                "title": "Derechos fundamentales",
                "title_ar": "الحقوق الأساسية",
                "lessons": [
                    {
                        "id": "es_l3_u8_l1",
                        "title": "Derechos fundamentales",
                        "title_ar": "الحقوق الأساسية في القانون الإسباني",
                        "subtitle": "Catálogo constitucional y garantías",
                        "theory": (
                            "Los derechos fundamentales son aquellos derechos inherentes a todas las personas por el simple hecho de "
                            "serlo, reconocidos y protegidos por la Constitución y los tratados internacionales. En España, "
                            "el Título Preliminar de la Constitución de 1978 contiene un catálogo extenso de derechos fundamentales.\n\n"
                            "Los derechos fundamentales reconocidos incluyen: el derecho a la vida (art. 15), la dignidad de la persona "
                            "(art. 10), la igualdad ante la ley (art. 14), la libertad ideológica y religiosa (art. 16), la libertad "
                            "de expresión (art. 20), el derecho de reunión (art. 21), el derecho de asociación (art. 22), el derecho a "
                            "la educación (art. 27), el derecho a la intimidad (art. 18), y el derecho a la tutela judicial efectiva (art. 24).\n\n"
                            "Las garantías de los derechos fundamentales incluyen: el recurso de amparo ante el Tribunal Constitucional, "
                            "la inexistencia de censura previa, la reserva de ley para su regulación, y el principio de que los poderes "
                            "públicos están obligados a respetarlos y protegerlos.\n\n"
                            "La doctrina del Tribunal Constitucional ha desarrollado una jurisprudencia rica sobre el contenido y los "
                            "límites de los derechos fundamentales, estableciendo la proporcionalidad como criterio de control."
                        ),
                        "theory_ar": (
                            "الحقوق الأساسية هي الحقوق الكامنة في كل شخص بصفته إنساناً، المعترف بها ومحمية بالدستور والمعاهدات الدولية.\n\n"
                            "تشمل الحقوق الأساسية: الحق في الحياة والكرامة والمساواة والحرية والتعبير والتجمع والتجمع والتربية والخصوصية "
                            "والحماية القضائية.\n\n"
                            "تشمل الضمانات: الطعن الدستوري وعدم وجود رقابة مسبقة واحتياط القانون.\n\n"
                            "القضاء الدستوري طور اجتهادات غنية حول محتوى الحقوق الأساسية."
                        ),
                        "vocab": [
                            {"fr": "el derecho a la vida", "ar": "الحق في الحياة", "example": "El derecho a la vida está reconocido en el artículo 15."},
                            {"fr": "la dignidad de la persona", "ar": "كرامة الإنسان", "example": "La dignidad de la persona es fundamento del orden político y social."},
                            {"fr": "la igualdad ante la ley", "ar": "المساواة أمام القانون", "example": "La igualdad ante la ley es un derecho fundamental."},
                            {"fr": "la libertad de expresión", "ar": "حرية التعبير", "example": "La libertad de expresión protege la comunicación de ideas."},
                            {"fr": "el derecho a la intimidad", "ar": "الحق في الخصوصية", "example": "El derecho a la intimidad protege la vida privada."},
                            {"fr": "el derecho a la tutela judicial efectiva", "ar": "الحق في الحماية القضائية الفعالة", "example": "El derecho a la tutela judicial garantiza la protección de los derechos."},
                            {"fr": "el recurso de amparo", "ar": "الطعن الدستوري", "example": "El recurso de amparo protege los derechos fundamentales."},
                            {"fr": "el Tribunal Constitucional", "ar": "المحكمة الدستورية", "example": "El Tribunal Constitucional controla la constitucionalidad."},
                            {"fr": "el principio de proporcionalidad", "ar": "مبدأ التناسب", "example": "El principio de proporcionalidad limita la restricción de derechos."},
                            {"fr": "la reserva de ley", "ar": "احتياط القانون", "example": "La reserva de ley exige que los derechos se regulen por ley."},
                            {"fr": "la limitación de derechos", "ar": "تقييد الحقوق", "example": "La limitación de derechos debe ser proporcionada y necesaria."},
                            {"fr": "la declaración de derechos", "ar": "إعلان الحقوق", "example": "La declaración de derechos es la base del Estado democrático."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l3_u9",
                "title": "Medicina legal",
                "title_ar": "الطب الشرعي",
                "lessons": [
                    {
                        "id": "es_l3_u9_l1",
                        "title": "Medicina legal",
                        "title_ar": "الطب الشرعي في القانون الإسباني",
                        "subtitle": "Ciencias forenses y su aplicación jurídica",
                        "theory": (
                            "La medicina legal es la rama de la medicina que aplica sus conocimientos para dar respuesta a cuestiones "
                            "de naturaleza jurídica. En España, los peritos médicos forenses son funcionarios del Ministerio de Justicia "
                            "que asisten a los tribunales en la investigación de los hechos delictivos.\n\n"
                            "Las principales materias de la medicina legal incluyen: la determinación de la causa y mecanismo de la muerte, "
                            "la identificación de personas vivas y muertas, la valoración de lesiones, la determinación de la edad, "
                            "y los análisis toxicológicos.\n\n"
                            "La valoración de las lesiones se realiza conforme al Baremo Médico que establece el Real Decreto 1976/1999. "
                            "Las lesiones se clasifican en muy graves, graves y leves, atendiendo a su permanencia en el tiempo y "
                            "sus consecuencias para la salud de la víctima.\n\n"
                            "El informe pericial médico es un medio de prueba fundamental en los procesos penales y civiles. "
                            "El perito médico debe ser imparcial y objetivo, y su informe debe ajustarse a los principios "
                            "de la ciencia médica y la experiencia forense."
                        ),
                        "theory_ar": (
                            "الطب الشرعي هو فرع من الطب يُطبّق معرفته للإجابة على أسئلة ذات طبيعة قانونية.\n\n"
                            "تشمل المواد الرئيسية: تحديد سبب وآلية الوفاة وتحديد الهوية وتقييم الإصابات وتحديد العمر "
                            "والتحاليل السمية.\n\n"
                            "تقييم الإصابات يتم وفقاً للمقياس الطبي.\n\n"
                            "التقرير الطبي الخبير هو وسيلة إثبات أساسية في الإجراءات الجنائية والمدنية."
                        ),
                        "vocab": [
                            {"fr": "la medicina legal", "ar": "الطب الشرعي", "example": "La medicina legal aplica la medicina a cuestiones jurídicas."},
                            {"fr": "el perito médico forense", "ar": "الطبيب الشرعي الخبير", "example": "El perito médico forense asiste a los tribunales."},
                            {"fr": "la causa de muerte", "ar": "سبب الوفاة", "example": "La causa de muerte se determina mediante autopsia."},
                            {"fr": "la autopsia", "ar": "التشريح", "example": "La autopsia revela la causa y mecanismo de la muerte."},
                            {"fr": "la valoración de lesiones", "ar": "تقييم الإصابات", "example": "La valoración de lesiones se realiza conforme al Baremo Médico."},
                            {"fr": "las lesiones graves", "ar": "الإصابات الخطيرة", "example": "Las lesiones graves implican una incapacidad superior a un mes."},
                            {"fr": "la determinación de la edad", "ar": "تحديد العمر", "example": "La determinación de la edad es relevante en menores."},
                            {"fr": "el análisis toxicológico", "ar": "التحليل السمي", "example": "El análisis toxicológico detecta sustancias en el organismo."},
                            {"fr": "el informe pericial", "ar": "التقرير الخبير", "example": "El informe pericial es un medio de prueba fundamental."},
                            {"fr": "la identificación", "ar": "التعريف", "example": "La identificación forense utiliza huellas dactilares y ADN."},
                            {"fr": "la imparcialidad del perito", "ar": "حياد الخبير", "example": "El perito debe ser imparcial y objetivo en su informe."},
                            {"fr": "el Baremo Médico", "ar": "المقياس الطبي", "example": "El Baremo Médico clasifica las lesiones según su gravedad."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l3_u10",
                "title": "Derecho procesal avanzado",
                "title_ar": "الإجراءات المتقدمة",
                "lessons": [
                    {
                        "id": "es_l3_u10_l1",
                        "title": "Derecho procesal avanzado",
                        "title_ar": "إجراءات التقاضي المتقدمة في القانون الإسباني",
                        "subtitle": "Procesos especiales y ejecución de sentencias",
                        "theory": (
                            "El derecho procesal avanzado comprende los aspectos más complejos de la legislación procesal española. "
                            "Incluye los procesos especiales, la ejecución de sentencias, las medidas cautelares y la cooperación "
                            "judicial internacional.\n\n"
                            "Los procesos especiales incluyen: el proceso monitorio (para reclamaciones dinerarias líquidas), "
                            "el juicio verbal (para pretensiones de menor cuantía), el juicio ordinario (para pretensiones de mayor cuantía), "
                            "y los procesos de jurisdicción voluntaria (adopciones, incapacitaciones, declaraciones de ausencia).\n\n"
                            "Las medidas cautelares son disposiciones judiciales adoptadas para asegurar la eficacia de la sentencia "
                            "que eventualmente se dicte. Incluyen el embargo, la anotación de demanda en el Registro de la Propiedad, "
                            "y la intervención y depósito de ingresos.\n\n"
                            "La ejecución de sentencias es el procedimiento por el que se hace efectiva la decisión judicial. "
                            "La ejecución forzosa puede ser dineraria (pago de cantidad líquida) o no dineraria (entrega de bien, "
                            "hacer o no hacer). El ejecutado puede oponerse a la ejecución invocando excepciones."
                        ),
                        "theory_ar": (
                            "إجراءات التقاضي المتقدمة تشمل الجوانب الأكثر تعقيداً في التشريع الإجرائي الإسباني.\n\n"
                            "تشمل الإجراءات الخاصة: الإجراء للتحصيل (لمطالبات الأموال Liquida) والجلسات البسيطة والجلسات العادية "
                            "والإجراءات الإدارية.\n\n"
                            "التدابير الاحتيازية هي تدابير قضائية تُتخذ لضمان فعالية الحكم.\n\n"
                            "تنفيذ الأحكام هو الإجراء الذي يجعل القرار القضائي فعالاً."
                        ),
                        "vocab": [
                            {"fr": "el proceso monitorio", "ar": "إجراءات التحصيل", "example": "El proceso monitorio se tramita para reclamaciones dinerarias líquidas."},
                            {"fr": "el juicio verbal", "ar": "الجلسات البسيطة", "example": "El juicio verbal se celebra para pretensiones de menor cuantía."},
                            {"fr": "el juicio ordinario", "ar": "الجلسات العادية", "example": "El juicio ordinario se tramita para pretensiones de mayor cuantía."},
                            {"fr": "las medidas cautelares", "ar": "التدابير الاحتيازية", "example": "Las medidas cautelares aseguran la eficacia de la sentencia."},
                            {"fr": "el embargo", "ar": "الحجز", "example": "El embargo puede ser dinerario o no dinerario."},
                            {"fr": "la ejecución de sentencias", "ar": "تنفيذ الأحكام", "example": "La ejecución de sentencias es el procedimiento para hacer efectiva la decisión."},
                            {"fr": "la ejecución forzosa", "ar": "التنفيذ القسري", "example": "La ejecución forzosa puede ser dineraria o no dineraria."},
                            {"fr": "la oposición a la ejecución", "ar": "الاعتراض على التنفيذ", "example": "El ejecutado puede oponerse a la ejecución invocando excepciones."},
                            {"fr": "la anotación de demanda", "ar": "تسجيل الدعوى", "example": "La anotación de demanda se practica en el Registro de la Propiedad."},
                            {"fr": "la jurisdicción voluntaria", "ar": "الاختيار الإداري", "example": "La jurisdicción voluntaria comprende adoptions e incapacitaciones."},
                            {"fr": "el depósito de ingresos", "ar": "إيداع المداخيل", "example": "El depósito de ingresos asegura la satisfacción del crédito."},
                            {"fr": "el execute de sentencia", "ar": "تنفيذ الحكم", "example": "El execute de sentencia es un título ejecutivo."},
                        ],
                    },
                ],
            },
        ],
    },
    # ─── Nivel 4 — Profesional ──────────────────────────────────────
    {
        "id": 4,
        "title": "Profesional — المحترف",
        "description": "Litigación oral, negociación y práctica profesional",
        "color": "#dc2626",
        "units": [
            {
                "id": "es_l4_u1",
                "title": "La vista oral y litigación",
                "title_ar": "الجلسة الصوتية والتقاضي",
                "lessons": [
                    {
                        "id": "es_l4_u1_l1",
                        "title": "La vista oral y litigación",
                        "title_ar": "الجلسة الصوتية وفن التقاضي",
                        "subtitle": "Técnicas de litigación oral ante los tribunales",
                        "theory": (
                            "La vista oral es el momento procesal donde se debaten las pretensiones ante el juez. "
                            "Es la fase principal del juicio donde los abogados exponen oralmente sus argumentos, practican la prueba "
                            "y formulan sus conclusiones finales.\n\n"
                            "La estructura de la vista oral comprende: la comparecencia de las partes, el acto de conciliación, "
                            "las alegaciones del demandante, las alegaciones del demandado, la práctica de prueba propuesta y admitida, "
                            "y las conclusiones orales de cada parte.\n\n"
                            "Las técnicas de litigación oral incluyen: conocer el expediente a fondo, dirigirse al juez con respeto "
                            "(\"Ilustrísimo Señor\"), estructurar los argumentos lógicamente, dominar la prueba documental y pericial, "
                            "preparar el interrogatorio de testigos, conceder puntos secundarios, y cerrar con una síntesis poderosa.\n\n"
                            "La preparación previa de la vista oral es fundamental: el abogado debe dominar los hechos, las pruebas, "
                            "la jurisprudencia aplicable y los argumentos de la parte contraria. La improvisación es el mayor enemigo "
                            "del litigante. Un buen abogado anticipa las objeciones y prepara respuestas para cada escenario."
                        ),
                        "theory_ar": (
                            "الجلسة الصوتية هي اللحظة الإجرائية التي تُنقش فيها المطالبات أمام القاضي. وهي المرحلة الرئيسية من المحاكمة.\n\n"
                            "تتضمن الجلسة الصوتية: الحضور والمصالحة ومطالبات المدعي ومطالبات المدعى عليه وممارسة الإثبات والخلاصة الشفهية.\n\n"
                            "تتضمن تقنيات التقاضي: معرفة الملف بعمق ومخاطبة القاضي باحترام وهيكلة الحجج منطقياً وإتقان الإثبات.\n\n"
                            "التحضير المسبق للجلسة الصوتية أساسي. الإرتجال هو العدو الأكبر للمحامي."
                        ),
                        "vocab": [
                            {"fr": "Ilustrísimo Señor", "ar": "سيادة القاضي المحترم", "example": "Ilustrísimo Señor, el demandante ha acreditado los hechos."},
                            {"fr": "la vista oral", "ar": "الجلسة الصوتية", "example": "La vista oral se celebrará el próximo lunes."},
                            {"fr": "la audiencia", "ar": "السماع", "example": "En la audiencia se practicarán las pruebas propuestas."},
                            {"fr": "el interrogatorio", "ar": "الاستجواب", "example": "Procederemos al interrogatorio del demandado."},
                            {"fr": "la prueba pericial", "ar": "الخبرة", "example": "La prueba pericial acredita el valor del inmueble."},
                            {"fr": "las conclusiones", "ar": "الخلاصة", "example": "Pasamos a formular nuestras conclusiones."},
                            {"fr": "en méritos de lo expuesto", "ar": "بناءً على ما تم عرضه", "example": "En méritos de lo expuesto, solicitamos la estimación."},
                            {"fr": "dictar sentencia", "ar": "إصدار الحكم", "example": "El juez dictará sentencia en el plazo de veinte días."},
                            {"fr": "la valoración probatoria", "ar": "تقييم الإثبات", "example": "Discrepamos de la valoración probatoria del juzgado."},
                            {"fr": "estimatoria / desestimatoria", "ar": "قبولية / رفضية", "example": "Solicitamos sentencia estimatoria de nuestra demanda."},
                            {"fr": "el alegato", "ar": "المرافعة", "example": "El alegato del abogado fue convincente y fundamentado."},
                            {"fr": "la réplica oral", "ar": "الرد الشفهي", "example": "La réplica oral desmontó los argumentos de la parte contraria."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l4_u2",
                "title": "Negociación jurídica",
                "title_ar": "التفاوض القانوني",
                "lessons": [
                    {
                        "id": "es_l4_u2_l1",
                        "title": "Negociación jurídica",
                        "title_ar": "التفاوض القانوني والتسويات",
                        "subtitle": "Técnicas de negociación y mediación en conflictos legales",
                        "theory": (
                            "La negociación jurídica es una habilidad esencial para el profesional del derecho moderno. "
                            "Permite resolver conflictos sin recurrir a la vía judicial, ahorrando tiempo, dinero y preservando "
                            "las relaciones entre las partes.\n\n"
                            "Los principios de la negociación jurídica incluyen: la preparación exhaustiva del caso, "
                            "el conocimiento de los intereses reales de las partes (más allá de las posiciones), "
                            "la búsqueda de soluciones creativas que generen valor para ambas partes, y la alternativa mejor a un "
                            "acuerdo negociado (BATNA, por sus siglas en inglés).\n\n"
                            "La mediación es un proceso de resolución de conflictos en el que un tercero imparcial, el mediador, "
                            "facilita la comunicación entre las partes para que lleguen a un acuerdo satisfactorio. "
                            "En España, la Ley 5/2012 de mediación en asuntos civiles y mercantiles regula este proceso.\n\n"
                            "Los acuerdos alcanzados en mediación pueden ser elevados a escritura pública ante notario, "
                            "otorgándoles la misma eficacia que una sentencia judicial firme."
                        ),
                        "theory_ar": (
                            "التفاوض القانوني هو مهارة أساسية للمحامي الحديث. يسمح بحل النزاعات دون اللجوء للقضاء.\n\n"
                            "مبادئ التفاوض تشمل: التحضير الشامل ومعرفة مصالح الأطراف الحقيقية والبحث عن حلول إبداعية.\n\n"
                            "الوساطة هي عملية لحل النزاعات يُسرّع فيها وسيط محايد التواصل بين الأطراف للوصول لاتفاق.\n\n"
                            "يمكن رفع الاتفاقيات إلى عقد رسمي أمام موثق."
                        ),
                        "vocab": [
                            {"fr": "la negociación", "ar": "التفاوض", "example": "La negociación jurídica permite resolver conflictos extrajudicialmente."},
                            {"fr": "la mediación", "ar": "الوساطة", "example": "La mediación facilita la comunicación entre las partes."},
                            {"fr": "el mediador / la mediadora", "ar": "الوساطة", "example": "El mediador es un tercero imparcial que facilita el acuerdo."},
                            {"fr": "el acuerdo", "ar": "الاتفاق", "example": "El acuerdo alcanzado pone fin a la controversia."},
                            {"fr": "el conflicto", "ar": "النزاع", "example": "El conflicto puede resolverse por negociación o judicialmente."},
                            {"fr": "la conciliación", "ar": "التوافق", "example": "La conciliación es un acto previo al juicio oral."},
                            {"fr": "el convenio", "ar": "الاتفاقية", "example": "El convenio recoge los derechos y obligaciones de las partes."},
                            {"fr": "el acuerdo extrajudicial", "ar": "الاتفاق خارج القضاء", "example": "El acuerdo extrajudicial evita los costes del litigio."},
                            {"fr": "el interés legítimo", "ar": "المصلحة المشروعة", "example": "El interés legítimo fundamenta la pretensión del demandante."},
                            {"fr": "la estrategia de negociación", "ar": "استراتيجية التفاوض", "example": "La estrategia de negociación se prepara antes de la reunión."},
                            {"fr": "el BATNA", "ar": "البديل الأفضل لاتفاق متفاوض", "example": "El BATNA es la alternativa que tiene cada parte si fracasa la negociación."},
                            {"fr": "la cláusula de confidencialidad", "ar": "بند السرية", "example": "La cláusula de confidencialidad protege la información sensible."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l4_u3",
                "title": "Derecho de empresas",
                "title_ar": "قانون الشركات",
                "lessons": [
                    {
                        "id": "es_l4_u3_l1",
                        "title": "Derecho de empresas",
                        "title_ar": "قانون الشركات الإسباني",
                        "subtitle": "Gobierno corporativo, fusiones y operaciones societarias",
                        "theory": (
                            "El derecho de empresas o derecho societario regula la creación, funcionamiento y disolución de las sociedades "
                            "mercantiles. En España, la norma fundamental es la Ley de Sociedades de Capital (Real Decreto Legislativo 1/2010).\n\n"
                            "El gobierno corporativo se refiere al conjunto de reglas y procedimientos que rigen la relación entre "
                            "los socios, los administradores y los demás grupos de interés de la sociedad. Los principios del gobierno "
                            "corporativo incluyen la transparencia, la rendición de cuentas, la igualdad de trato a los accionistas "
                            "y la protección de los acreedores sociales.\n\n"
                            "Las operaciones societarias más relevantes incluyen: las fusiones (escisión de una o varias sociedades para "
                            "constituir una nueva), las escisiones (división del patrimonio de una sociedad entre varias sociedades), "
                            "y las transformaciones (cambio de forma jurídica sin disolución).\n\n"
                            "Los socios gozan de derechos políticos (voto en junta) y económicos (derecho al dividendo y a la cuota "
                            "de liquidación). Los administradores están sujetos a deberes de lealtad y diligencia hacia la sociedad."
                        ),
                        "theory_ar": (
                            "قانون الشركات يُنظم إنشاء وعمل وتصفية الشركات التجارية.\n\n"
                            "الحكومةorporativa تشمل مجموعة القواعد والإجراءات التي تحكم العلاقة بين المساهمين والإدارة.\n\n"
                            "تشمل العمليات الرئيسية: الاندماج والانقسام والتحول.\n\n"
                            "يتمتع المساهمون بحقوق سياسية واقتصادية. الإدارة خاضعة لواجبات الولاء والعناية."
                        ),
                        "vocab": [
                            {"fr": "la sociedad limitada", "ar": "شركة المحدودة", "example": "La sociedad limitada tiene un capital mínimo de 3.000 euros."},
                            {"fr": "la sociedad anónima", "ar": "الشركة المساهمة", "example": "La sociedad anónima tiene un capital mínimo de 60.000 euros."},
                            {"fr": "el gobierno corporativo", "ar": "الحكومةorporativa", "example": "El gobierno corporativo regula las relaciones entre socios y administradores."},
                            {"fr": "la fusión", "ar": "الاندماج", "example": "La fusión puede ser por absorción o por creación de nueva sociedad."},
                            {"fr": "la escisión", "ar": "الانقسام", "example": "La escisión divide el patrimonio de una sociedad entre varias."},
                            {"fr": "la transformación", "ar": "التحول", "example": "La transformación cambia la forma jurídica sin disolución."},
                            {"fr": "el administrador", "ar": "الإدارة", "example": "El administrador debe actuar con lealtad y diligencia."},
                            {"fr": "la junta general", "ar": "الجمعية العامة", "example": "La junta general aprueba las cuentas y nombra a los administradores."},
                            {"fr": "el dividendo", "ar": "التوزيعات", "example": "El dividendo se reparte entre los socios según su participación."},
                            {"fr": "la cuota de liquidación", "ar": "حصة التصفية", "example": "La cuota de liquidación corresponde al patrimonio neto residual."},
                            {"fr": "el socio", "ar": "المُساهم", "example": "El socio tiene derecho al voto en la junta general."},
                            {"fr": "el Registro Mercantil", "ar": "السجل التجاري", "example": "La inscripción en el Registro Mercantil es obligatoria."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l4_u4",
                "title": "Fiscalidad",
                "title_ar": "الضرائب",
                "lessons": [
                    {
                        "id": "es_l4_u4_l1",
                        "title": "Fiscalidad",
                        "title_ar": "النظام الضريبي الإسباني",
                        "subtitle": "Impuestos directos, indirectos y obligaciones fiscales",
                        "theory": (
                            "El derecho tributario o fiscalidad regula las relaciones entre los obligados tributarios y la Administración "
                            "Pública en materia de impuestos. En España, el sistema tributario se articula en tres niveles: Estatal, "
                            "autonómico y local.\n\n"
                            "Los impuestos directos gravan la renta o el patrimonio de los contribuyentes. Los más importantes son: "
                            "el Impuesto sobre la Renta de las Personas Físicas (IRPF), que grava la renta global del contribuyente; "
                            "el Impuesto sobre Sociedades (IS), que grava los beneficios de las entidades jurídicas; "
                            "y el Impuesto sobre el Patrimonio, que grava la riqueza neta superior a 700.000 euros.\n\n"
                            "Los impuestos indirectos gravan el consumo y las transmisiones. El principal es el Impuesto sobre el Valor "
                            "Añadido (IVA), que grava las entregas de bienes y prestaciones de servicios. Los tipos impositivos son "
                            "general (21%), reducido (10%) y superreducido (4%).\n\n"
                            "Las obligaciones formales del contribuyente incluyen: declarar las rentas, llevar contabilidad, "
                            "conservar documentación, y facilitar información a la Administración Tributaria. "
                            "El incumplimiento de estas obligaciones puede dar lugar a sanciones administrativas."
                        ),
                        "theory_ar": (
                            "القانون الضريبي يُنظم العلاقات بين المكلفين والإدارة العامة في مجال الضرائب.\n\n"
                            "تشمل الضرائب المباشرة: ضريبة الدخل الشخصي وضريبة الشركات وضريبة الثروة.\n\n"
                            "تشمل الضرائب غير المباشرة: ضريبة القيمة المضافة التي تُفرض على الاستهلاك.\n\n"
                            "تشمل الالتزامات الشكلية: الإقرار بالدخل ومسايرة الحسابات وحفظ الوثائق.\n\n"
                            "يُمكن أن يترتب على الإخلال بالالتزامات عقوبات إدارية."
                        ),
                        "vocab": [
                            {"fr": "el IRPF", "ar": "ضريبة الدخل الشخصي", "example": "El IRPF grava la renta global del contribuyente."},
                            {"fr": "el Impuesto sobre Sociedades", "ar": "ضريبة الشركات", "example": "El Impuesto sobre Sociedades grava los beneficios de las empresas."},
                            {"fr": "el IVA", "ar": "ضريبة القيمة المضافة", "example": "El IVA grava las entregas de bienes y prestaciones de servicios."},
                            {"fr": "el tipo impositivo", "ar": "نسبة الضريبة", "example": "El tipo impositivo general del IVA es el 21%."},
                            {"fr": "la base imponible", "ar": "القاعدة الضريبية", "example": "La base imponible es la cuantía sobre la que se calcula la cuota tributaria."},
                            {"fr": "la cuota tributaria", "ar": "الratea الضريبية", "example": "La cuota tributaria es el importe a pagar por el contribuyente."},
                            {"fr": "el contribuyente", "ar": "المكلف", "example": "El contribuyente está obligado a declarar sus rentas."},
                            {"fr": "la Administración Tributaria", "ar": "الإدارة الضريبية", "example": "La Administración Tributaria verifica el cumplimiento de obligaciones."},
                            {"fr": "la declaración de la renta", "ar": "إقرار الدخل", "example": "La declaración de la renta debe presentarse antes del 30 de junio."},
                            {"fr": "la sanción tributaria", "ar": "العقوبة الضريبية", "example": "El incumplimiento de obligaciones formales puede acarrear sanciones."},
                            {"fr": "la retención en源en源源", "ar": "الاقتطاع", "example": "Las retenciones se practican sobre determinados rendimientos."},
                            {"fr": "el fraude fiscal", "ar": "الاحتيال الضريبي", "example": "El fraude fiscal es un delito que persigue el Ministerio Fiscal."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l4_u5",
                "title": "Derecho inmobiliario",
                "title_ar": "قانون العقارات",
                "lessons": [
                    {
                        "id": "es_l4_u5_l1",
                        "title": "Derecho inmobiliario",
                        "title_ar": "قانون العقارات الإسباني",
                        "subtitle": "Transmisión, arrendamiento y urbanismo",
                        "theory": (
                            "El derecho inmobiliario regula las relaciones jurídicas relativas a los bienes inmuebles, incluyendo "
                            "su transmisión, arrendamiento, garantías reales y régimen urbanístico. Es una materia compleja que "
                            "entrecruza el derecho civil, el derecho administrativo y el derecho mercantil.\n\n"
                            "La transmisión de la propiedad inmobiliaria puede realizarse a título oneroso (compraventa) o gratuito "
                            "(donación). La compraventa inmobiliaria requiere escritura pública ante notario e inscripción en el "
                            "Registro de la Propiedad para su oponibilidad frente a terceros.\n\n"
                            "El arrendamiento urbano se rige por la Ley de Arrendamientos Urbanos de 1994. Los arrendamientos de "
                            "vivienda tienen una duración mínima de cinco años, y los de uso distinto del de vivienda de una año. "
                            "El traspaso o subarriendo requiere consentimiento del arrendador.\n\n"
                            "El derecho urbanístico regula la edificación, la disciplina urbanística y la expropiación forzosa. "
                            "Los Planes Generales de Ordenación Urbana establecen el planeamiento municipal."
                        ),
                        "theory_ar": (
                            "قانون العقارات يُنظم العلاقات القانونية المتعلقة بالعقارات.\n\n"
                            "تتم نقل ملكية العقارات بمقابل أو بلا مقابل. تتطلب البيع عقداً رسمياً أمام موثق وتسجيلاً في سجل العقارات.\n\n"
                            "يُحكم الإيجار الحضري بقانون الإيجارات الحضرية لعام 1994.\n\n"
                            "قانون التخطيط الحضري يُنظم البناء وال disciplinary urbanístico والمصادرة القسرية."
                        ),
                        "vocab": [
                            {"fr": "la compraventa", "ar": "البيع", "example": "La compraventa inmobiliaria requiere escritura pública."},
                            {"fr": "el arrendamiento", "ar": "الإيجار", "example": "El arrendamiento de vivienda tiene una duración mínima de cinco años."},
                            {"fr": "el arrendador", "ar": "المؤجر", "example": "El arrendador tiene derecho al cobro de la renta."},
                            {"fr": "el arrendatario", "ar": "المستأجر", "example": "El arrendatario debe destinar la vivienda a uso residencial."},
                            {"fr": "la hipoteca", "ar": "الرهن العقاري", "example": "La hipoteca garantiza el pago de un préstamo hipotecario."},
                            {"fr": "el Registro de la Propiedad", "ar": "سجل العقارات", "example": "La inscripción en el Registro protege al adquirente."},
                            {"fr": "la escritura pública", "ar": "الوثيقة الرسمية", "example": "La escritura pública es requisito para transmitir la propiedad."},
                            {"fr": "el traspaso", "ar": "الانتقال", "example": "El traspaso de local comercial requiere autorización del arrendador."},
                            {"fr": "la fianza", "ar": "الضمان", "example": "La fianza del arrendamiento es de un mes para vivienda."},
                            {"fr": "el Plan General de Ordenación Urbana", "ar": "الخطة العامة للتنظيم الحضري", "example": "El PGOU establece el planeamiento municipal."},
                            {"fr": "la expropiación forzosa", "ar": "المصادرة القسرية", "example": "La expropiación forzosa se realiza por causa de utilidad pública."},
                            {"fr": "la disciplina urbanística", "ar": "الdisciplinario الحضري", "example": "La disciplina urbanística sanciona las infracciones urbanísticas."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l4_u6",
                "title": "Derecho sanitario",
                "title_ar": "القانون الصحي",
                "lessons": [
                    {
                        "id": "es_l4_u6_l1",
                        "title": "Derecho sanitario",
                        "title_ar": "القانون الصحي الإسباني",
                        "subtitle": "Derechos de los pacientes, responsabilidad médica y bioética",
                        "theory": (
                            "El derecho sanitario regula las relaciones entre los profesionales sanitarios, los pacientes y los "
                            "sistemas de salud. En España, la Ley 41/2002 de autonomía del paciente y la Ley 29/2006 de garantías "
                            "y uso racional de los medicamentos son las normas fundamentales.\n\n"
                            "Los derechos de los pacientes reconocidos incluyen: el derecho a la información sanitaria, "
                            "el derecho al consentimiento informado, el derecho a la confidencialidad de la información clínica, "
                            "el derecho a la dignidad en el proceso asistencial, y el derecho a la documentación clínica.\n\n"
                            "La responsabilidad médica puede ser contractual (relación médico-paciente) o extracontractual (acto médico "
                            "sin relación contractual previa). Los requisitos son los mismos que en la responsabilidad civil general: "
                            "daño, nexo causal y antijuridicidad.\n\n"
                            "La bioética es la disciplina que estudia las cuestiones éticas derivadas de los avances científicos "
                            "y tecnológicos en el ámbito de la salud, incluyendo el aborto, la eutanasia, la reproducción asistida "
                            "y la experimentación con seres humanos."
                        ),
                        "theory_ar": (
                            "القانون الصحي يُنظم العلاقات بين المتخصصين في الصحة والمرضى وأنظمة الصحة.\n\n"
                            "تشمل حقوق المرضى: الحق في المعلومات الصحية والموافقة المستنيرة والسرية والكرامة.\n\n"
                            "يمكن أن تكون المسؤولية الطبية عقدية أو غير عقدية.\n\n"
                            "الأخلاقيات الطبية تدرس القضايا الأخلاقية الناتجة عن التطورات العلمية في مجال الصحة."
                        ),
                        "vocab": [
                            {"fr": "el derecho sanitario", "ar": "القانون الصحي", "example": "El derecho sanitario regula la relación médico-paciente."},
                            {"fr": "el consentimiento informado", "ar": "الموافقة المستنيرة", "example": "El consentimiento informado es un derecho fundamental del paciente."},
                            {"fr": "el paciente", "ar": "المرضى", "example": "El paciente tiene derecho a recibir información completa."},
                            {"fr": "la información sanitaria", "ar": "المعلومات الصحية", "example": "La información sanitaria debe ser clara y comprensible."},
                            {"fr": "la confidencialidad", "ar": "السرية", "example": "La confidencialidad protege la información del paciente."},
                            {"fr": "la responsabilidad médica", "ar": "المسؤولية الطبية", "example": "La responsabilidad médica puede ser contractual o extracontractual."},
                            {"fr": "la historia clínica", "ar": "السجل الطبي", "example": "La historia clínica es un documento público de acceso del paciente."},
                            {"fr": "el bioética", "ar": "الأخلاقيات الطبية", "example": "El bioética estudia las cuestiones éticas de la medicina moderna."},
                            {"fr": "la eutanasia", "ar": "ال協助 الموت", "example": "La eutanasia está regulada en España desde 2021."},
                            {"fr": "la reproducción asistida", "ar": "الإنجاب بمساعدة طبية", "example": "La reproducción asistida se regula por la Ley 14/2006."},
                            {"fr": "el profesional sanitario", "ar": "المتخصص الصحي", "example": "El profesional sanitario debe actuar con diligencia y prudencia."},
                            {"fr": "el derecho a la dignidad", "ar": "الحق في الكرامة", "example": "El derecho a la dignidad guía toda la asistencia sanitaria."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l4_u7",
                "title": "Derecho digital",
                "title_ar": "القانون الرقمي",
                "lessons": [
                    {
                        "id": "es_l4_u7_l1",
                        "title": "Derecho digital",
                        "title_ar": "القانون الرقمي والتقنيات الحديثة",
                        "subtitle": "Protección de datos, comercio electrónico y delitos informáticos",
                        "theory": (
                            "El derecho digital es una rama emergente del derecho que regula las relaciones jurídicas derivadas "
                            "del uso de las tecnologías de la información y la comunicación. En España, las normas fundamentales "
                            "son la Ley Orgánica 3/2018 de Protección de Datos Personales y la Ley 34/2002 de Servicios de la "
                            "Sociedad de la Información y Comercio Electrónico.\n\n"
                            "La protección de datos personales es un derecho fundamental reconocido en el artículo 18.4 de la "
                            "Constitución Española. El Reglamento General de Protección de Datos (RGPD) de la UE y la LOPDGDD "
                            "española establecen los principios de tratamiento: licitud, lealtad, transparencia, limitación de la "
                            "finalidad, minimización de datos, exactitud, limitación del plazo de conservación, integridad y "
                            "confidencialidad, y responsabilidad proactiva.\n\n"
                            "El comercio electrónico se regula por la LSSI, que establece obligaciones de información, transparencia "
                            "y consentimiento para los prestadores de servicios de la sociedad de la información.\n\n"
                            "Los delitos informáticos, regulados en los artículos 197 bis y siguientes del Código Penal, incluyen "
                            "el acceso ilícito a sistemas informáticos, la interceptación ilícita de comunicaciones, la alteración "
                            "de datos y la falsificación de documentos electrónicos."
                        ),
                        "theory_ar": (
                            "القانون الرقمي هو فرع ناشئ يُنظم العلاقات القانونية الناتجة عن استخدام تكنولوجيا المعلومات والاتصالات.\n\n"
                            "حماية البيانات الشخصية حق أساسي مُكرَّس في المادة 18.4 من الدستور الإسباني.\n\n"
                            "يُنظم تجارة إلكترونية قانون الخدمات بمسؤوليات المعلومات والشفافية.\n\n"
                            "تشمل الجرائم الإلكترونية: الوصول غير المشروع لأنظمة المعلومات واعتراض الاتصالات غير المشروع وتعديل البيانات."
                        ),
                        "vocab": [
                            {"fr": "el derecho digital", "ar": "القانون الرقمي", "example": "El derecho digital regula las relaciones jurídicas en el ámbito digital."},
                            {"fr": "la protección de datos personales", "ar": "حماية البيانات الشخصية", "example": "La protección de datos es un derecho fundamental."},
                            {"fr": "el RGPD", "ar": " اللائحة العامة لحماية البيانات", "example": "El RGPD establece los principios de tratamiento de datos."},
                            {"fr": "el consentimiento", "ar": "الموافقة", "example": "El consentimiento debe ser libre, informado e inequívoco."},
                            {"fr": "el responsable del tratamiento", "ar": "مسؤول المعالجة", "example": "El responsable del tratamiento debe garantizar la seguridad de los datos."},
                            {"fr": "el derecho de supresión", "ar": "حق الحذف", "example": "El derecho de supresión permite solicitar la eliminación de datos personales."},
                            {"fr": "el comercio electrónico", "ar": "التجارة الإلكترونية", "example": "El comercio electrónico se regula por la LSSI."},
                            {"fr": "los delitos informáticos", "ar": "الجرائم الإلكترونية", "example": "Los delitos informáticos se tipifican en el Código Penal."},
                            {"fr": "el acceso ilícito", "ar": "الوصول غير المشروع", "example": "El acceso ilícito a sistemas informáticos es un delito."},
                            {"fr": "la ciberseguridad", "ar": "الأمن السيبراني", "example": "La ciberseguridad protege los sistemas de información."},
                            {"fr": "la huella digital", "ar": "البصمة الرقمية", "example": "La huella digital permite la identificación del usuario."},
                            {"fr": "la firma electrónica", "ar": "التوقيع الإلكتروني", "example": "La firma electrónica tiene la misma validez que la firma manuscrita."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l4_u8",
                "title": "Derecho ambiental",
                "title_ar": "القانون البيئي",
                "lessons": [
                    {
                        "id": "es_l4_u8_l1",
                        "title": "Derecho ambiental",
                        "title_ar": "القانون البيئي الإسباني",
                        "subtitle": "Protección del medio ambiente y responsabilidad ambiental",
                        "theory": (
                            "El derecho ambiental regula las normas destinadas a la protección y conservación del medio ambiente. "
                            "En España, el artículo 45 de la Constitución establece que todos tienen el derecho a disfrutar de un "
                            "medio ambiente adecuado para el desarrollo de la persona y el deber de conservarlo.\n\n"
                            "Las normas fundamentales incluyen: la Ley 21/2013 de Evaluación Ambiental, la Ley 26/2007 de Responsabilidad "
                            "Medioambiental, y la Ley 33/2011 General de Salud Pública. A nivel europeo, destaca la Directiva "
                            "Marco del Agua y la Directiva sobre Evaluación de Efectos de Determinados Planes y Programas.\n\n"
                            "La responsabilidad medioambiental tiene un régimen objetivo: el operador responde por los daños "
                            "medioambientales independientemente de su culpabilidad. Los daños medioambientales incluyen la "
            "contaminación del suelo, del agua y del aire, la degradación de hábitats naturales y la pérdida de biodiversidad.\n\n"
                            "Los instrumentos de política ambiental incluyen: la evaluación de impacto ambiental, la auditoría "
                            "ambiental, los sistemas de gestión ambiental (ISO 14001), y los impuestos medioambientales "
                            "(como el Impuesto Especial sobre Determinados Medios de Transporte)."
                        ),
                        "theory_ar": (
                            "القانون البيئي يُنظم القواعد الموجهة لحماية وحفظ البيئة. المادة 45 من الدستور تنص على الحق في البيئة.\n\n"
                            "تشمل القواعد الرئيسية: قانون تقييم الأثر البيئي وقانون المسؤولية البيئية وقانون الصحة العامة.\n\n"
                            "المسؤولية البيئية نظام موضوعي: المشغل يتحمل المسؤولية عن الأضرار البيئية بغض النظر عن اللوم.\n\n"
                            "تشمل الأدوات البيئية: تقييم الأثر البيئي والتدقيق البيئي وأنظمة الإدارة البيئية والضرائب البيئية."
                        ),
                        "vocab": [
                            {"fr": "el derecho ambiental", "ar": "القانون البيئي", "example": "El derecho ambiental regula la protección del medio ambiente."},
                            {"fr": "la contaminación", "ar": "التلوث", "example": "La contaminación del agua es un daño medioambiental."},
                            {"fr": "la biodiversidad", "ar": "التنوع البيولوجي", "example": "La protección de la biodiversidad es un objetivo del derecho ambiental."},
                            {"fr": "el impacto ambiental", "ar": "الأثر البيئي", "example": "La evaluación de impacto ambiental es obligatoria para grandes proyectos."},
                            {"fr": "la evaluación ambiental", "ar": "التقييم البيئي", "example": "La evaluación ambiental previene daños al medio ambiente."},
                            {"fr": "la responsabilidad medioambiental", "ar": "المسؤولية البيئية", "example": "La responsabilidad medioambiental es un régimen objetivo."},
                            {"fr": "el operador", "ar": "المشغّل", "example": "El operador responde por los daños medioambientales que cause."},
                            {"fr": "el residuo", "ar": "النفايات", "example": "La gestión de residuos se rige por la normativa ambiental."},
                            {"fr": "el desarrollo sostenible", "ar": "التنمية المستدامة", "example": "El desarrollo sostenible equilibra crecimiento económico y protección ambiental."},
                            {"fr": "el cambio climático", "ar": "التغير المناخي", "example": "El cambio climático es un desafío prioritario del derecho ambiental."},
                            {"fr": "la auditoría ambiental", "ar": "التدقيق البيئي", "example": "La auditoría ambiental verifica el cumplimiento de la normativa."},
                            {"fr": "el impuesto medioambiental", "ar": "الضريبة البيئية", "example": "Los impuestos medioambientales incentivan la reducción de emisiones."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l4_u9",
                "title": "Convenciones internacionales",
                "title_ar": "الاتفاقيات الدولية",
                "lessons": [
                    {
                        "id": "es_l4_u9_l1",
                        "title": "Convenciones internacionales",
                        "title_ar": "الاتفاقيات والمعاهدات الدولية",
                        "subtitle": "Derecho internacional público y tratados",
                        "theory": (
                            "Las convenciones internacionales o tratados internacionales son acuerdos celebrados entre Estados o "
                            "entre Estados y organizaciones internacionales que crean obligaciones jurídicas. En España, los tratados "
                            "internacionales ratificados forman parte del ordenamiento interno conforme al artículo 96 de la Constitución.\n\n"
                            "Los requisitos de validez de un tratado internacional son: capacidad de los sujetos, libre manifestación "
                            "de voluntad, objeto lícito y causa lícita. La Convención de Viena de 1969 sobre el Derecho de los Tratados "
                            "establece las normas de interpretación y las causas de nulidad.\n\n"
                            "Las convenciones internacionales más relevantes en el ámbito jurídico incluyen: la Convención de Viena "
                            "sobre Compraventa Internacional de Mercancías, los Convenios de Ginebra sobre Derecho Humanitario, "
                            "el Convenio Europeo de Derechos Humanos, y la Convención de Naciones Unidas sobre el Derecho del Mar.\n\n"
                            "El proceso de ratificación de un tratado internacional en España comprende: la negociación, la firma "
                            "del tratado, la autorización parlamentaria (cuando proceda), la ratificación por parte del Estado, "
                            "y el depósito o canje de instrumentos de ratificación."
                        ),
                        "theory_ar": (
                            "الاتفاقيات الدولية هي اتفاقيات تُبرم بين دول أو بين دول ومنظمات دولية وتخلق التزامات قانونية. في إسبانيا "
                            "تُشكّل المعاهدات الدولية المُصادق عليها جزءاً من النظام القانوني الداخلي.\n\n"
                            "تشمل شروط صحة المعاهدة: أهلية الأطراف وإرادة حرة وموضوع مشروع وسبب مشروع.\n\n"
                            "تشمل الاتفاقيات الدولية الأكثر أهمية: اتفاقية فيينا لبيع البضائع الدولية واتفاقيات جنيف والاتفاقية الأوروبية "
                            "لحقوق الإنسان.\n\n"
                            "يتضمن عملية التصديق: التفاوض والتوقيع والتفويض البرلماني والتصديق."
                        ),
                        "vocab": [
                            {"fr": "la convención internacional", "ar": "الاتفاقية الدولية", "example": "Las convenciones internacionales crean obligaciones jurídicas."},
                            {"fr": "el tratado internacional", "ar": "المعاهدة الدولية", "example": "El tratado internacional prevalece sobre la legislación interna."},
                            {"fr": "la ratificación", "ar": "التصديق", "example": "La ratificación del tratado es requisito para su entrada en vigor."},
                            {"fr": "la firma", "ar": "التوقيع", "example": "La firma del tratado expresa la voluntad de vincularse."},
                            {"fr": "la negociación", "ar": "التفاوض", "example": "La negociación es la primera fase de la celebración de tratados."},
                            {"fr": "el depósito", "ar": "الإيداع", "example": "El depósito de instrumentos formaliza la ratificación."},
                            {"fr": "la Convención de Viena", "ar": "اتفاقية فيينا", "example": "La Convención de Viena regula el derecho de los tratados."},
                            {"fr": "el Convenio Europeo de Derechos Humanos", "ar": "الاتفاقية الأوروبية لحقوق الإنسان", "example": "El CEDH protege los derechos humanos en Europa."},
                            {"fr": "el objeto lícito", "ar": "الموضوع المشروع", "example": "El objeto del tratado debe ser lícito y posible."},
                            {"fr": "la causa lícita", "ar": "السبب المشروع", "example": "La causa del tratado debe ser conforme al derecho internacional."},
                            {"fr": "el Estado parte", "ar": "الدولة الطرف", "example": "El Estado parte está vinculado por las obligaciones del tratado."},
                            {"fr": "la reserva", "ar": "التحفظ", "example": "La reserva permite a un Estado excluir o modificar ciertas disposiciones."},
                        ],
                    },
                ],
            },
            {
                "id": "es_l4_u10",
                "title": "Derecho comparado",
                "title_ar": "القانون المقارن",
                "lessons": [
                    {
                        "id": "es_l4_u10_l1",
                        "title": "Derecho comparado",
                        "title_ar": "القانون المقارن والأنظمة القانونية",
                        "subtitle": "Análisis comparativo de sistemas jurídicos contemporáneos",
                        "theory": (
                            "El derecho comparado es la disciplina que estudia y compara las diferentes soluciones jurídicas adoptadas "
                            "por los distintos ordenamientos jurídicos para resolver problemas jurídicos similares. Su estudio permite "
                            "comprender mejor el propio sistema jurídico y descubrir alternativas legislativas.\n\n"
                            "Los principales sistemas jurídicos del mundo son: el sistema romano-germánico (o derecho continental), "
                            "que se basa en la codificación y la tradición del derecho romano; el sistema common law (o derecho anglosajón), "
                            "que se basa en la jurisprudencia judicial y el precedente vinculante; y el sistema de derecho mixto, que "
                            "combina elementos de ambos sistemas.\n\n"
                            "España pertenece al sistema romano-germánico, pero presenta peculiaridades propias derivadas de su "
                            "organización en comunidades autónomas y su pertenencia a la Unión Europea. El sistema jurídico español "
                            "se caracteriza por la existencia de códigos, la separación de poderes y la protección constitucional "
                            "de los derechos fundamentales.\n\n"
                            "Los métodos de estudio del derecho comparado incluyen: el método funcional (comparar soluciones a problemas "
                            "similares), el método estructural (comparar instituciones con funciones análogas) y el método histórico "
                            "(comparar la evolución de instituciones similares en distintos sistemas)."
                        ),
                        "theory_ar": (
                            "القانون المقارن هو التخصص الذي يدرس ويقارن الحلول القانونية المتبناة من مختلف الأنظمة القانونية.\n\n"
                            "تشمل الأنظمة الرئيسية: النظام الروماني الجرماني (القانون القار) ونظام القانون العام (القانون الأنغلوساكسوني) "
                            "ونظام القانون المختلط.\n\n"
                            "تنتمي إسبانيا إلى النظام الروماني الجermاني لكن لها خصوصياتها.\n\n"
                            "تشمل أساليب الدراسة: الأسلوب الوظيفي والأسلوب الهيكلي والأسلوب التاريخي."
                        ),
                        "vocab": [
                            {"fr": "el derecho comparado", "ar": "القانون المقارن", "example": "El derecho comparado estudia y compara los sistemas jurídicos."},
                            {"fr": "el sistema romano-germánico", "ar": "النظام الروماني الجرماني", "example": "España pertenece al sistema romano-germánico."},
                            {"fr": "el common law", "ar": "القانون العام الأنغلوساكسوني", "example": "El common law se basa en la jurisprudencia judicial."},
                            {"fr": "el precedente vinculante", "ar": "ال суд_previo الملزم", "example": "El precedente vinculante es la base del sistema anglosajón."},
                            {"fr": "el código", "ar": "القانون", "example": "El código es la fuente principal del derecho continental."},
                            {"fr": "la codificación", "ar": "التقييد", "example": "La codificación sistematiza las normas jurídicas en un cuerpo único."},
                            {"fr": "la función comparada", "ar": "الوظيفة المقارنة", "example": "La función comparada identifica soluciones a problemas similares."},
                            {"fr": "el método funcional", "ar": "الأسلوب الوظيفي", "example": "El método funcional compara soluciones a problemas similares."},
                            {"fr": "el sistema de derecho mixto", "ar": "نظام القانون المختلط", "example": "El sistema de derecho mixto combina elementos de ambos sistemas."},
                            {"fr": "la familia jurídica", "ar": "العائلة القانونية", "example": "Las familias jurídicas agrupan sistemas con características comunes."},
                            {"fr": "la transposición normativa", "ar": "النقل التشريعي", "example": "La transposición normativa permite adoptar soluciones jurídicas extranjeras."},
                            {"fr": "el análisis comparativo", "ar": "التحليل المقارن", "example": "El análisis comparativo enriquece la comprensión del propio sistema."},
                        ],
                    },
                ],
            },
        ],
    },
]


# ─── دليل اللغة ─────────────────────────────────────────────────────────
LANGUAGES = {
    "fr": {"levels": LEVELS_FR, "title": "Français juridique", "title_ar": "الفرنسية القانونية", "flag": "🇫🇷"},
    "en": {"levels": LEVELS_EN, "title": "English legal", "title_ar": "الإنجليزية القانونية", "flag": "🇬🇧"},
    "es": {"levels": LEVELS_ES, "title": "Español jurídico", "title_ar": "الإسبانية القانونية", "flag": "🇪🇸"},
}


def _all_levels():
    """إعادة كل المستويات من كل اللغات."""
    result = []
    for lang, info in LANGUAGES.items():
        for lv in info["levels"]:
            result.append({**lv, "lang": lang, "lang_title": info["title_ar"]})
    return result


_DDL = """
CREATE TABLE IF NOT EXISTS legal_language_progress (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL,
    lesson_id     TEXT NOT NULL,
    lang          TEXT NOT NULL DEFAULT 'fr',
    score         INTEGER NOT NULL DEFAULT 0,
    total         INTEGER NOT NULL DEFAULT 0,
    attempts      INTEGER NOT NULL DEFAULT 1,
    completed_at  TEXT,
    created_at    TEXT DEFAULT (datetime('now')),
    UNIQUE(user_id, lesson_id)
);
"""


def ensure_table():
    """إنشاء جدول التقدم (idempotent)."""
    with db_session() as conn:
        conn.execute(_DDL)


def _row_to_dict(row):
    """تحويل SQLite Row إلى dict."""
    return dict(row) if row else None


def _get_levels(lang: str):
    """إعادة قائمة مستويات لغة معينة."""
    info = LANGUAGES.get(lang)
    return info["levels"] if info else LANGUAGES["fr"]["levels"]


def _find_lesson(lesson_id: str, lang: str | None = None):
    """بحث عن درس في كل اللغات أو لغة محددة."""
    langs = [lang] if lang else list(LANGUAGES.keys())
    for lg in langs:
        for lv in LANGUAGES[lg]["levels"]:
            for u in lv["units"]:
                for ls in u["lessons"]:
                    if ls["id"] == lesson_id:
                        return ls, lv, u, lg
    return None, None, None, None


def list_languages():
    """إعادة قائمة اللغات المتاحة."""
    return [
        {"code": code, "title": info["title"], "title_ar": info["title_ar"],
         "flag": info["flag"],
         "level_count": len(info["levels"]),
         "lesson_count": sum(len(u["lessons"]) for lv in info["levels"] for u in lv["units"])}
        for code, info in LANGUAGES.items()
    ]


def list_levels(lang: str = "fr"):
    """إعادة قائمة المستويات مع معلومات عامة."""
    ensure_table()
    levels = _get_levels(lang)
    return [
        {
            "id": lv["id"],
            "title": lv["title"],
            "title_ar": lv["title"],
            "description": lv["description"],
            "color": lv["color"],
            "unit_count": len(lv["units"]),
            "lesson_count": sum(len(u["lessons"]) for u in lv["units"]),
        }
        for lv in levels
    ]


def get_level(level_id: int, lang: str = "fr"):
    """إعادة مستوى مع كل وحداته ودروسه (بدون التمارين)."""
    levels = _get_levels(lang)
    for lv in levels:
        if lv["id"] == level_id:
            return {
                "id": lv["id"],
                "title": lv["title"],
                "description": lv["description"],
                "color": lv["color"],
                "lang": lang,
                "units": [
                    {
                        "id": u["id"],
                        "title": u["title"],
                        "title_ar": u["title_ar"],
                        "lessons": [
                            {
                                "id": ls["id"],
                                "title": ls["title"],
                                "title_ar": ls["title_ar"],
                                "subtitle": ls["subtitle"],
                            }
                            for ls in u["lessons"]
                        ],
                    }
                    for u in lv["units"]
                ],
            }
    return None


def get_lesson(lesson_id: str):
    """إعادة درس كامل مع المحتوى والمفردات."""
    ls, lv, u, lang = _find_lesson(lesson_id)
    if not ls:
        return None
    return {
        "id": ls["id"],
        "title": ls["title"],
        "title_ar": ls["title_ar"],
        "subtitle": ls["subtitle"],
        "theory": ls["theory"],
        "theory_ar": ls["theory_ar"],
        "vocab": ls["vocab"],
        "level_id": lv["id"],
        "level_title": lv["title"],
        "unit_id": u["id"],
        "unit_title": u["title"],
        "lang": lang,
    }


def get_quiz(lesson_id: str):
    """إعادة اختبار لدرس معين — أسئلة اختيار من متعدد."""
    lesson = get_lesson(lesson_id)
    if not lesson:
        return None
    vocab = lesson["vocab"]
    if len(vocab) < 4:
        return None
    questions = []
    for i, v in enumerate(vocab):
        wrong = [x["ar"] for j, x in enumerate(vocab) if j != i]
        options = [v["ar"]] + wrong[:3]
        import random
        random.shuffle(options)
        questions.append({
            "id": i + 1,
            "question": f"ما معنى '{v['fr']}' بالعربية؟",
            "options": options,
            "correct": v["ar"],
            "example": v["example"],
            "hint": v["ar"],
        })
    return {"lesson_id": lesson_id, "lesson_title": lesson["title"],
            "lang": lesson["lang"], "questions": questions}


def save_progress(user_id: int, lesson_id: str, score: int, total: int):
    """حفظ أو تحديث تقدم المستخدم في درس."""
    ensure_table()
    _, _, _, lang = _find_lesson(lesson_id)
    lang = lang or "fr"
    completed = score >= total * 0.6
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    with db_session() as conn:
        existing = conn.execute(
            "SELECT id, score, attempts FROM legal_language_progress "
            "WHERE user_id = ? AND lesson_id = ?",
            (user_id, lesson_id),
        ).fetchone()
        if existing:
            new_attempts = existing["attempts"] + 1
            new_score = max(existing["score"], score)
            conn.execute(
                "UPDATE legal_language_progress SET score = ?, total = ?, "
                "attempts = ?, completed_at = ? WHERE user_id = ? AND lesson_id = ?",
                (new_score, total, new_attempts,
                 now if completed else existing["completed_at"],
                 user_id, lesson_id),
            )
        else:
            conn.execute(
                "INSERT INTO legal_language_progress "
                "(user_id, lesson_id, lang, score, total, attempts, completed_at) "
                "VALUES (?, ?, ?, ?, ?, 1, ?)",
                (user_id, lesson_id, lang, score, total, now if completed else None),
            )


def get_user_progress(user_id: int, lang: str | None = None):
    """إعادة تقدم المستخدم (كل اللغات أو لغة محددة)."""
    ensure_table()
    with db_session() as conn:
        if lang:
            rows = conn.execute(
                "SELECT lesson_id, score, total, attempts, completed_at, lang "
                "FROM legal_language_progress WHERE user_id = ? AND lang = ?",
                (user_id, lang),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT lesson_id, score, total, attempts, completed_at, lang "
                "FROM legal_language_progress WHERE user_id = ?",
                (user_id,),
            ).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_user_stats(user_id: int, lang: str | None = None):
    """إحصائيات المستخدم الإجمالية (كل اللغات أو لغة محددة)."""
    ensure_table()
    where = "WHERE user_id = ? AND completed_at IS NOT NULL"
    params = [user_id]
    if lang:
        where += " AND lang = ?"
        params.append(lang)
    with db_session() as conn:
        row = conn.execute(
            f"SELECT COUNT(*) as completed, "
            f"COALESCE(SUM(score), 0) as total_score, "
            f"COALESCE(AVG(CASE WHEN total > 0 THEN score * 100.0 / total END), 0) as avg_pct "
            f"FROM legal_language_progress {where}",
            params,
        ).fetchone()
    if lang:
        levels = _get_levels(lang)
        total_lessons = sum(len(u["lessons"]) for lv in levels for u in lv["units"])
    else:
        total_lessons = sum(
            len(u["lessons"])
            for info in LANGUAGES.values()
            for lv in info["levels"]
            for u in lv["units"]
        )
    completed = row["completed"] if row else 0
    return {
        "completed_lessons": completed,
        "total_lessons": total_lessons,
        "completion_pct": round(completed / total_lessons * 100, 1) if total_lessons else 0,
        "total_score": row["total_score"] if row else 0,
        "avg_pct": round(row["avg_pct"], 1) if row else 0,
    }
