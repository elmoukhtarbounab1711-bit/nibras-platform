"""
International Treaties, Legal Texts, and Codes — multi-language.
Provides a database table `french_legal_texts` with seed data of real
international treaties Morocco has ratified, French legal codes, plus
list/get/search functions with language filtering.
"""
from .database import db_session

TABLE_DDL = """
CREATE TABLE IF NOT EXISTS french_legal_texts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT NOT NULL,
    title_ar        TEXT NOT NULL,
    category        TEXT NOT NULL,
    description     TEXT,
    full_text       TEXT,
    source_url      TEXT,
    source_name     TEXT,
    ratification_date TEXT,
    language        TEXT NOT NULL DEFAULT 'fr',
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_french_legal_texts_category
    ON french_legal_texts(category);
"""

SEED_DATA = [
    {
        "title": "Déclaration universelle des droits de l'homme",
        "title_ar": "الإعلان العالمي لحقوق الإنسان",
        "category": "حقوق الإنسان",
        "description": "Adoptée par l'Assemblée générale des Nations Unies le 10 décembre 1948. Le Maroc a participé à son élaboration.",
        "full_text": (
            "DÉCLARATION UNIVERSELLE DES DROITS DE L'HOMME\n\n"
            "Adoptée par l'Assemblée générale des Nations Unies dans sa résolution 217 A (III), le 10 décembre 1948\n\n"
            "PRÉAMBULE\n\n"
            "Considérant que la reconnaissance de la dignité inhérente à tous les membres de la famille humaine et "
            "de leurs droits égaux et inaliénables constitue le fondement de la liberté, de la justice et de la paix dans le monde, "
            "Considérant que la méconnaissance et le mépris des droits de l'homme ont conduit à des actes de barbarie "
            "qui révoltent la conscience de l'humanité,\n"
            "Considérant qu'il est essentiel que les droits de l'homme soient protégés par un régime de droit,\n\n"
            "Article 1er.\n"
            "Tous les êtres humains naissent libres et égaux en dignité et en droits. Ils sont dotés de raison et de conscience "
            "et doivent agir les uns envers les autres dans un esprit de fraternité.\n\n"
            "Article 2.\n"
            "Chacun peut se prévaloir de tous les droits et de toutes les libertés proclamés dans la présente Déclaration, "
            "sans distinction aucune, notamment de race, de couleur, de sexe, de langue, de religion, d'opinion politique.\n\n"
            "Article 3.\n"
            "Tout individu a droit à la vie, à la liberté et à la sûreté de sa personne.\n\n"
            "Article 4.\n"
            "Nul ne sera soumis à l'esclavage ni à la servitude; l'esclavage et la traite des esclaves sont interdits sous toutes leurs formes.\n\n"
            "Article 5.\n"
            "Nul ne sera soumis à la torture ni à des peines ou traitements cruels, inhumains ou dégradants.\n\n"
            "Article 6.\n"
            "Chacun a droit à la reconnaissance en tous lieux de sa personnalité juridique.\n\n"
            "Article 7.\n"
            "Tous sont égaux devant la loi et ont droit sans distinction à une égale protection de la loi.\n\n"
            "Article 18.\n"
            "Toute personne a droit à la liberté de pensée, de conscience et de religion.\n\n"
            "Article 19.\n"
            "Tout individu a droit à la liberté d'opinion et d'expression.\n\n"
            "Article 25.\n"
            "Toute personne a droit à un niveau de vie suffisant pour assurer sa santé, son bien-être et ceux de sa famille.\n\n"
            "Article 26.\n"
            "Toute personne a droit à l'éducation."
        ),
        "source_url": "https://www.un.org/fr/about-us/universal-declaration-of-human-rights",
        "source_name": "Nations Unies",
        "ratification_date": "1948-12-10",
    },
    {
        "title": "Convention relative aux droits de l'enfant",
        "title_ar": "اتفاقية حقوق الطفل",
        "category": "حقوق الإنسان",
        "description": "Adoptée par l'Assemblée générale des Nations Unies le 20 novembre 1989. Ratifiée par le Maroc le 21 juin 1993.",
        "full_text": (
            "CONVENTION RELATIVE AUX DROITS DE L'ENFANT\n\n"
            "Adoptée par l'Assemblée générale des Nations Unies le 20 novembre 1989\n\n"
            "Article 1er\n"
            "Aux fins de la présente Convention, un enfant s'entend de tout être humain âgé de moins de dix-huit ans.\n\n"
            "Article 2\n"
            "Les États parties respectent les droits énoncés dans la présente Convention et les garantissent à tout enfant relevant de leur juridiction.\n\n"
            "Article 3\n"
            "Dans toutes les décisions concernant les enfants, l'intérêt de l'enfant sera une considération primordiale.\n\n"
            "Article 6\n"
            "Les États parties reconnaissent à tout enfant le droit intrinsèque à la vie.\n\n"
            "Article 12\n"
            "Les États parties garantissent à l'enfant capable de discernement le droit d'exprimer librement son opinion.\n\n"
            "Article 19\n"
            "Les États parties prennent toutes les mesures pour protéger l'enfant contre toute forme de violence.\n\n"
            "Article 27\n"
            "Les États parties reconnaissent le droit de tout enfant à un niveau de vie suffisant.\n\n"
            "Article 28\n"
            "Les États parties reconnaissent le droit de l'enfant à l'éducation.\n\n"
            "Article 34\n"
            "Les États parties s'engagent à protéger l'enfant contre toutes les formes d'exploitation sexuelle.\n\n"
            "Article 37\n"
            "Les États parties veillent à ce qu'aucun enfant ne soit soumis à la torture."
        ),
        "source_url": "https://www.ohchr.org/fr/instruments-mechanisms/instruments/convention-rights-child",
        "source_name": "Haut-Commissariat aux droits de l'homme",
        "ratification_date": "1993-06-21",
    },
    {
        "title": "Convention sur l'élimination de toutes les formes de discrimination à l'égard des femmes",
        "title_ar": "اتفاقية القضاء على جميع أشكال التمييز ضد المرأة",
        "category": "حقوق الإنسان",
        "description": "Adoptée le 18 décembre 1979. Ratifiée par le Maroc le 21 juin 1993.",
        "full_text": (
            "CONVENTION SUR L'ÉLIMINATION DE TOUTES LES FORMES DE DISCRIMINATION À L'ÉGARD DES FEMMES\n\n"
            "Article 1er\n"
            "Aux fins de la présente Convention, l'expression « discrimination à l'égard des femmes » vise toute distinction, "
            "exclusion ou restriction fondée sur le sexe.\n\n"
            "Article 2\n"
            "Les États parties condamnent la discrimination à l'égard des femmes sous toutes ses formes.\n\n"
            "Article 3\n"
            "Les États parties prennent toutes les mesures appropriées pour assurer le plein développement des femmes.\n\n"
            "Article 5\n"
            "Les États parties prennent toutes les mesures appropriées pour modifier les schémas de comportement social et culturel.\n\n"
            "Article 10\n"
            "Les États parties prennent toutes les mesures pour éliminer la discrimination à l'égard des femmes dans l'éducation.\n\n"
            "Article 16\n"
            "Les États parties prennent toutes les mesures pour éliminer la discrimination à l'égard des femmes dans le mariage."
        ),
        "source_url": "https://www.ohchr.org/fr/instruments-mechanisms/instruments/convention-elimination-all-forms-discrimination-against-women",
        "source_name": "Haut-Commissariat aux droits de l'homme",
        "ratification_date": "1993-06-21",
    },
    {
        "title": "Pacte international relatif aux droits civils et politiques",
        "title_ar": "العهد الدولي الخاص بالحقوق المدنية والسياسية",
        "category": "حقوق الإنسان",
        "description": "Adopté le 16 décembre 1966. Ratifié par le Maroc le 3 mai 1979.",
        "full_text": (
            "PACTE INTERNATIONAL RELATIF AUX DROITS CIVILS ET POLITIQUES\n\n"
            "Article 1er\n"
            "Tous les peuples ont le droit de disposer d'eux-mêmes.\n\n"
            "Article 2\n"
            "Chaque État partie au présent Pacte s'engage à respecter et à garantir à tous les individus se trouvant sur son territoire les droits reconnus.\n\n"
            "Article 6\n"
            "Le droit à la vie est inhérent à la personne humaine.\n\n"
            "Article 7\n"
            "Nul ne sera soumis à la torture ni à des peines ou traitements cruels, inhumains ou dégradants.\n\n"
            "Article 9\n"
            "Tout individu a droit à la liberté et à la sûreté de sa personne.\n\n"
            "Article 14\n"
            "Toute personne est égale devant les tribunaux et cours de justice.\n\n"
            "Article 18\n"
            "Toute personne a droit à la liberté de pensée, de conscience et de religion.\n\n"
            "Article 19\n"
            "Toute personne a droit à la liberté d'opinion et d'expression.\n\n"
            "Article 25\n"
            "Tout citoyen a le droit et la possibilité, sans discrimination, de prendre part à la direction des affaires publiques."
        ),
        "source_url": "https://www.ohchr.org/fr/instruments-mechanisms/instruments/international-covenant-civil-and-political-rights",
        "source_name": "Haut-Commissariat aux droits de l'homme",
        "ratification_date": "1979-05-03",
    },
    {
        "title": "Pacte international relatif aux droits économiques, sociaux et culturels",
        "title_ar": "العهد الدولي الخاص بالحقوق الاقتصادية والاجتماعية والثقافية",
        "category": "حقوق الإنسان",
        "description": "Adopté le 16 décembre 1966. Ratifié par le Maroc le 3 mai 1979.",
        "full_text": (
            "PACTE INTERNATIONAL RELATIF AUX DROITS ÉCONOMIQUES, SOCIAUX ET CULTURELS\n\n"
            "Article 1er\n"
            "Tous les peuples ont le droit de disposer d'eux-mêmes.\n\n"
            "Article 2\n"
            "Chaque État partie s'engage à garantir le droit à un travail, à des conditions de travail justes.\n\n"
            "Article 6\n"
            "Les États parties reconnaissent le droit au travail.\n\n"
            "Article 7\n"
            "Les États parties reconnaissent le droit de toute personne à des conditions de travail justes et favorables.\n\n"
            "Article 11\n"
            "Toute personne a droit à un niveau de vie suffisant.\n\n"
            "Article 12\n"
            "Toute personne a droit au meilleur état de santé possible.\n\n"
            "Article 13\n"
            "Les États parties reconnaissent le droit de toute personne à l'éducation."
        ),
        "source_url": "https://www.ohchr.org/fr/instruments-mechanisms/instruments/international-covenant-economic-social-and-cultural-rights",
        "source_name": "Haut-Commissariat aux droits de l'homme",
        "ratification_date": "1979-05-03",
    },
    {
        "title": "Convention contre la torture et autres peines ou traitements cruels, inhumains ou dégradants",
        "title_ar": "الاتفاقية ضد التعذيب وغيره من المعاملات أو العقوبات القاسية أو الحاطة بالكرامة",
        "category": "حقوق الإنسان",
        "description": "Adoptée le 10 décembre 1984. Ratifiée par le Maroc le 21 juin 1993.",
        "full_text": (
            "CONVENTION CONTRE LA TORTURE\n\n"
            "Article 1er\n"
            "L'expression « torture » désigne tout acte par lequel une douleur ou des souffrances aiguës, physiques ou mentales, "
            "sont intentionnellement infligées à une personne.\n\n"
            "Article 2\n"
            "Chaque État partie prend des mesures législatives, administratives, judiciaires et autres mesures efficaces "
            "pour empêcher que des actes de torture soient commis.\n\n"
            "Article 3\n"
            "Aucun État partie n'expulsera, ne refoulera ni n'extradera une personne vers un autre État s'il existe des motifs "
            "sérieux de croire qu'elle risque d'être soumise à la torture.\n\n"
            "Article 12\n"
            "Chaque État partie fait en sorte que ses autorités compétentes procèdent à une enquête prompte et impartiale "
            "toutes les fois qu'il y a des motifs de croire qu'un acte de torture a été commis."
        ),
        "source_url": "https://www.ohchr.org/fr/instruments-mechanisms/instruments/convention-against-torture",
        "source_name": "Haut-Commissariat aux droits de l'homme",
        "ratification_date": "1993-06-21",
    },
    {
        "title": "Convention relative aux droits des personnes handicapées",
        "title_ar": "اتفاقية حقوق الأشخاص ذوي الإعاقة",
        "category": "حقوق الإنسان",
        "description": "Adoptée le 13 décembre 2006. Ratifiée par le Maroc le 8 avril 2009.",
        "full_text": (
            "CONVENTION RELATIVE AUX DROITS DES PERSONNES HANDICAPÉES\n\n"
            "Article 1er\n"
            "La présente Convention a pour objet de promouvoir, de protéger et d'assurer la pleine et égale jouissance "
            "de tous les droits de l'homme et de toutes les libertés fondamentales par les personnes handicapées.\n\n"
            "Article 3\n"
            "Les principes de la présente Convention sont: le respect de la dignité inhérente, la non-discrimination, "
            "la participation et l'inclusion complètes, l'égalité des chances, l'accessibilité, l'égalité entre hommes et femmes.\n\n"
            "Article 9\n"
            "Les États parties adoptent des mesures appropriées pour assurer l'accessibilité des personnes handicapées.\n\n"
            "Article 19\n"
            "Les personnes handicapées ont le droit de vivre en toute autonomie et de disposer de choix.\n\n"
            "Article 24\n"
            "Les États parties reconnaissent le droit des personnes handicapées à l'éducation."
        ),
        "source_url": "https://www.ohchr.org/fr/instruments-mechanisms/instruments/convention-rights-persons-disabilities",
        "source_name": "Haut-Commissariat aux droits de l'homme",
        "ratification_date": "2009-04-08",
    },
    {
        "title": "Convention de Genève relative à l'amélioration du sort des blessés et des malades dans les armées en campagne",
        "title_ar": "اتفاقية جنيف بشأن تحسين حالة الجرحى والمرضى في القوات المسلحة في الحملات",
        "category": "القانون الدولي الإنساني",
        "description": "Adoptée le 12 août 1949. Ratifiée par le Maroc le 26 mai 1956.",
        "full_text": (
            "CONVENTION DE GENÈVE (I) — BLESSÉS ET MALADES\n\n"
            "Article 12\n"
            "Les membres des forces armées et les autres personnes mentionnées à la présente Convention, qui seront blessés "
            "ou malades, seront respectés et protégés dans tous les cas.\n\n"
            "Article 16\n"
            "Les parties au conflit seront tenues de recueillir, sans délai, tout renseignement qui permette d'identifier "
            "les personnes qui ne peuvent être traitées conformément aux dispositions de la présente Convention.\n\n"
            "Article 24\n"
            "Le personnel médical exclusivement affecté à la recherche du traitement des blessés ou malades, "
            "au diagnostic ou à l'administration des secours est respecté et protégé."
        ),
        "source_url": "https://www.icrc.org/fr/doc/resources/documents/treaty/06dc70b17552cfa6c125641e00528f6f/convention-geneve-i-f",
        "source_name": "Comité international de la Croix-Rouge",
        "ratification_date": "1956-05-26",
    },
    {
        "title": "Convention de Genève relative au traitement des prisonniers de guerre",
        "title_ar": "اتفاقية جنيف بشأن معاملة أسرى الحرب",
        "category": "القانون الدولي الإنساني",
        "description": "Adoptée le 12 août 1949. Ratifiée par le Maroc le 26 mai 1956.",
        "full_text": (
            "CONVENTION DE GENÈVE (III) — PRISONNIERS DE GUERRE\n\n"
            "Article 12\n"
            "Les prisonniers de guerre sont sous la responsabilité du Puissance détentrice.\n\n"
            "Article 13\n"
            "Les prisonniers de guerre ont droit au respect de leur personne et de leur honneur.\n\n"
            "Article 27\n"
            "Les prisonniers de guerre auront droit à des vêtements, à l'alimentation et au logement.\n\n"
            "Article 132\n"
            "Dès la fin des hostilités actives, les prisonniers de guerre seront rendus sans délai."
        ),
        "source_url": "https://www.icrc.org/fr/doc/resources/documents/treaty/2c0b4f92c5f194c9c125641e00328f6f/convention-geneve-iii-f",
        "source_name": "Comité international de la Croix-Rouge",
        "ratification_date": "1956-05-26",
    },
    {
        "title": "Convention de Genève relative à la protection des personnes civiles en temps de guerre",
        "title_ar": "اتفاقية جنيف بشأن حماية المدنيين في wartime",
        "category": "القانون الدولي الإنساني",
        "description": "Adoptée le 12 août 1949. Ratifiée par le Maroc le 26 mai 1956.",
        "full_text": (
            "CONVENTION DE GENÈVE (IV) — PERSONNES CIVILES\n\n"
            "Article 13\n"
            "La présente Convention s'applique aux personnes civiles qui se trouvent, en cas de conflit ou d'occupation, "
            "du côté d'une partie au conflit.\n\n"
            "Article 27\n"
            "Les personnes protégées ont droit au respect de leur personne, de leur honneur, de leurs droits de famille.\n\n"
            "Article 49\n"
            "Il est interdit aux Puissances déplacantes de procéder à la déportation totale ou partielle."
        ),
        "source_url": "https://www.icrc.org/fr/doc/resources/documents/treaty/3b8ab105c810c51bc125641e004ee36f/convention-geneve-iv-f",
        "source_name": "Comité international de la Croix-Rouge",
        "ratification_date": "1956-05-26",
    },
    {
        "title": "Convention de Vienne sur le droit des traités",
        "title_ar": "اتفاقية فيينا بشأن قانون المعاهدات",
        "category": "حقوق الإنسان",
        "description": "Adoptée le 23 mai 1969. Ratifiée par le Maroc le 9 décembre 1974.",
        "full_text": (
            "CONVENTION DE VIENNE SUR LE DROIT DES TRAITÉS\n\n"
            "Article 26 — PACTA SUNT SERVANDA\n"
            "Tout traité en vigueur lie les parties et doit être exécuté par elles de bonne foi.\n\n"
            "Article 27\n"
            "Une partie ne peut invoquer les dispositions de son droit interne pour justifier la non-exécution d'un traité.\n\n"
            "Article 31 — Règle générale d'interprétation\n"
            "Un traité doit être interprété de bonne foi suivant le sens ordinaire à attribuer aux termes du traité.\n\n"
            "Article 53\n"
            "Est nul tout traité qui, au moment de sa conclusion, est en conflit avec une norme impérative du droit international général."
        ),
        "source_url": "https://legal.un.org/ils/publications/volumes/vol_1111/vol_1111-French-pp.219-379.pdf",
        "source_name": "Nations Unies — Droit des traités",
        "ratification_date": "1974-12-09",
    },
    {
        "title": "Convention 29 de l'OIT sur le travail forcé",
        "title_ar": "اتفاقية منظمة العمل الدولية رقم 29 بشأن العمل القسري",
        "category": "العمل والضمان الاجتماعي",
        "description": "Adoptée le 28 juin 1930. Ratifiée par le Maroc le 18 septembre 1957.",
        "full_text": (
            "CONVENTION (n° 29) CONCERNANT LE TRAVAIL FORCÉ OU OBLIGATOIRE\n\n"
            "Article 2\n"
            "Le terme travail forcé ou obligatoire désigne tout travail ou service exigé d'un individu sous la menace "
            "d'une peine quelconque et pour lequel ledit individu ne s'est pas offert de plein gré.\n\n"
            "Article 3\n"
            "Le terme travail forcé ou obligatoire ne comporte pas:\n"
            "a) Tout travail ou service exigé en vertu des lois sur le service militaire;\n"
            "b) Tout travail ou service faisant partie des obligations civiques normales;\n"
            "c) Tout travail ou service en exécution d'une condamnation prononcée par une juridiction répressive.\n\n"
            "Article 4\n"
            "L'autorité publique ne devra pas imposer le travail forcé ou obligatoire."
        ),
        "source_url": "https://www.ilo.org/dyn/normlex/en/f?p=NORMLEXPUB:12100:0::NO::P12100_ILO_CODE:C029",
        "source_name": "Organisation internationale du Travail",
        "ratification_date": "1957-09-18",
    },
    {
        "title": "Convention 87 de l'OIT sur la liberté syndicale",
        "title_ar": "اتفاقية منظمة العمل الدولية رقم 87 بشأن حرية النقابات",
        "category": "العمل والضمان الاجتماعي",
        "description": "Adoptée le 9 juillet 1948. Ratifiée par le Maroc le 22 mai 1958.",
        "full_text": (
            "CONVENTION (n° 87) SUR LA LIBERTÉ SYNDICALE ET LA PROTECTION DU DROIT SYNDICAL\n\n"
            "Article 2\n"
            "Les travailleurs et les employeurs, sans aucune distinction quelconque et sans autorisation préalable, "
            "ont le droit de constituer les organisations de leur choix.\n\n"
            "Article 3\n"
            "Les organisations de travailleurs et d'employeurs ont le droit de rédiger leurs statuts et règlements.\n\n"
            "Article 5\n"
            "Les organisations de travailleurs et d'employeurs ont le droit d'élire leurs représentants."
        ),
        "source_url": "https://www.ilo.org/dyn/normlex/en/f?p=NORMLEXPUB:12100:0::NO::P12100_ILO_CODE:C087",
        "source_name": "Organisation internationale du Travail",
        "ratification_date": "1958-05-22",
    },
    {
        "title": "Convention 98 de l'OIT sur le droit d'organisation et de négociation collective",
        "title_ar": "اتفاقية منظمة العمل الدولية رقم 98 بشأن حق التنظيم والتفاوض الجماعي",
        "category": "العمل والضمان الاجتماعي",
        "description": "Adoptée le 1er juillet 1949. Ratifiée par le Maroc le 13 janvier 1960.",
        "full_text": (
            "CONVENTION (n° 98) SUR LE DROIT D'ORGANISATION ET DE NÉGOCIATION COLLECTIVE\n\n"
            "Article 1\n"
            "Les travailleurs doivent bénéficier d'une protection adéquate contre tout acte de discrimination syndicale.\n\n"
            "Article 4\n"
            "Des mesures appropriées au pays doivent être encouragées pour favoriser la négociation collective."
        ),
        "source_url": "https://www.ilo.org/dyn/normlex/en/f?p=NORMLEXPUB:12100:0::NO::P12100_ILO_CODE:C098",
        "source_name": "Organisation internationale du Travail",
        "ratification_date": "1960-01-13",
    },
    {
        "title": "Convention 100 de l'OIT sur l'égalité de rémunération",
        "title_ar": "اتفاقية منظمة العمل الدولية رقم 100 بشأن المساواة في الأجر",
        "category": "العمل والضمان الاجتماعي",
        "description": "Adoptée le 29 juin 1951. Ratifiée par le Maroc le 17 février 1964.",
        "full_text": (
            "CONVENTION (n° 100) SUR L'ÉGALITÉ DE RÉMUNÉRATION\n\n"
            "Article 1\n"
            "Chaque État partie s'engage à appliquer le principe de l'égalité de rémunération entre les travailleurs "
            "des deux sexes pour un travail de valeur égale.\n\n"
            "Article 2\n"
            "La rémunération des sexes pour un même travail ou pour un travail de valeur égale doit être fixée "
            "sans discrimination fondée sur le sexe."
        ),
        "source_url": "https://www.ilo.org/dyn/normlex/en/f?p=NORMLEXPUB:12100:0::NO::P12100_ILO_CODE:C100",
        "source_name": "Organisation internationale du Travail",
        "ratification_date": "1964-02-17",
    },
    {
        "title": "Convention 105 de l'OIT sur l'abolition du travail forcé",
        "title_ar": "اتفاقية منظمة العمل الدولية رقم 105 بشأن إلغاء العمل القسري",
        "category": "العمل والضمان الاجتماعي",
        "description": "Adoptée le 25 juin 1957. Ratifiée par le Maroc le 18 septembre 1957.",
        "full_text": (
            "CONVENTION (n° 105) SUR L'ABOLITION DU TRAVAIL FORCÉ\n\n"
            "Article 1\n"
            "Chaque État partie qui a ratifié la Convention s'engage à abolir le travail forcé ou obligatoire dans les cas suivants:\n"
            "a) Comme moyen de coercition ou d'éducation politique;\n"
            "b) Comme moyen de mobilisation pour des travaux publics;\n"
            "c) Comme moyen de sanction;\n"
            "d) Comme mesure de discrimination.\n\n"
            "Article 2\n"
            "Chaque État partie prend des mesures pour abolir immédiatement le travail forcé."
        ),
        "source_url": "https://www.ilo.org/dyn/normlex/en/f?p=NORMLEXPUB:12100:0::NO::P12100_ILO_CODE:C105",
        "source_name": "Organisation internationale du Travail",
        "ratification_date": "1957-09-18",
    },
    {
        "title": "Convention 111 de l'OIT sur la discrimination (emploi et profession)",
        "title_ar": "اتفاقية منظمة العمل الدولية رقم 111 بشأن التمييز في التوظيف والمهنة",
        "category": "العمل والضمان الاجتماعي",
        "description": "Adoptée le 25 juin 1958. Ratifiée par le Maroc le 15 octobre 1963.",
        "full_text": (
            "CONVENTION (n° 111) SUR LA DISCRIMINATION (EMPLOI ET PROFESSION)\n\n"
            "Article 1\n"
            "Aux fins de la présente Convention, l'expression « discrimination » comprend toute distinction, exclusion "
            "ou préférence fondée sur la race, la couleur, le sexe, la religion, l'opinion politique.\n\n"
            "Article 2\n"
            "Chaque État partie s'engage à élaborer une politique nationale visant à éliminer toute discrimination.\n\n"
            "Article 3\n"
            "Chaque État partie prend des mesures incompatibles avec les dispositions de la présente Convention."
        ),
        "source_url": "https://www.ilo.org/dyn/normlex/en/f?p=NORMLEXPUB:12100:0::NO::P12100_ILO_CODE:C111",
        "source_name": "Organisation internationale du Travail",
        "ratification_date": "1963-10-15",
    },
    {
        "title": "Convention 138 de l'OIT sur l'âge minimum",
        "title_ar": "اتفاقية منظمة العمل الدولية رقم 138 بشأن الحد الأدنى للسن",
        "category": "العمل والضمان الاجتماعي",
        "description": "Adoptée le 26 juin 1973. Ratifiée par le Maroc le 5 juin 2000.",
        "full_text": (
            "CONVENTION (n° 138) SUR L'ÂGE MINIMUM\n\n"
            "Article 1\n"
            "Chaque État partie s'engage à établir un âge minimum pour l'admission à l'emploi.\n\n"
            "Article 2\n"
            "L'âge minimum ne doit pas être inférieur à l'âge de fin de scolarité obligatoire.\n\n"
            "Article 3\n"
            "L'âge minimum pour le travail dangereux ne doit pas être inférieur à dix-huit ans."
        ),
        "source_url": "https://www.ilo.org/dyn/normlex/en/f?p=NORMLEXPUB:12100:0::NO::P12100_ILO_CODE:C138",
        "source_name": "Organisation internationale du Travail",
        "ratification_date": "2000-06-05",
    },
    {
        "title": "Convention 182 de l'OIT sur les pires formes de travail des enfants",
        "title_ar": "اتفاقية منظمة العمل الدولية رقم 182 بشأن أسوأ أشكال عمل الأطفال",
        "category": "العمل والضمان الاجتماعي",
        "description": "Adoptée le 17 juin 1999. Ratifiée par le Maroc le 13 juin 2001.",
        "full_text": (
            "CONVENTION (n° 182) SUR LES PIRES FORMES DE TRAVAIL DES ENFANTS\n\n"
            "Article 1\n"
            "Chaque État partie prend des mesures immédiates et efficaces pour assurer l'interdiction et l'élimination "
            "des pires formes de travail des enfants.\n\n"
            "Article 3\n"
            "Aux fins de la présente Convention, l'expression « les pires formes de travail des enfants » comprend:\n"
            "a) La traite des enfants;\n"
            "b) L'utilisation, le recrutement ou l'offre d'enfants pour la prostitution;\n"
            "c) L'utilisation, le recrutement ou l'offre d'enfants pour la pornographie;\n"
            "d) L'utilisation, le recrutement ou l'offre d'enfants pour des activités illicites."
        ),
        "source_url": "https://www.ilo.org/dyn/normlex/en/f?p=NORMLEXPUB:12100:0::NO::P12100_ILO_CODE:C182",
        "source_name": "Organisation internationale du Travail",
        "ratification_date": "2001-06-13",
    },
    {
        "title": "Convention-cadre des Nations Unies sur les changements climatiques",
        "title_ar": "اتفاقية إطار الأمم المتحدة بشأن تغير المناخ",
        "category": "البيئة والتنمية",
        "description": "Adoptée le 9 mai 1992. Ratifiée par le Maroc le 12 septembre 1995.",
        "full_text": (
            "CONVENTION-CADRE DES NATIONS UNIES SUR LES CHANGEMENTS CLIMATIQUES\n\n"
            "Article 2\n"
            "L'objectif final de la présente Convention est de stabiliser les concentrations de gaz à effet de serre dans l'atmosphère.\n\n"
            "Article 3\n"
            "Les Parties doivent protéger le climat pour le bénéfice des générations présentes et futures.\n\n"
            "Article 4\n"
            "Chaque Partie a le droit et le devoir de promouvoir le développement durable."
        ),
        "source_url": "https://unfccc.int/files/essential_background/background_publications/pdf/application/pdf/unfccc_conv.pdf",
        "source_name": "ONU — Convention-cadre sur les changements climatiques",
        "ratification_date": "1995-09-12",
    },
    {
        "title": "Convention sur la diversité biologique",
        "title_ar": "اتفاقية التنوع البيولوجي",
        "category": "البيئة والتنمية",
        "description": "Adoptée le 22 mai 1992. Ratifiée par le Maroc le 3 novembre 1995.",
        "full_text": (
            "CONVENTION SUR LA DIVERSITÉ BIOLOGIQUE\n\n"
            "Article 1 — Objectifs\n"
            "Les objectifs de la présente Convention sont la conservation de la diversité biologique, l'utilisation durable "
            "de ses éléments et le partage équitable des avantages découlant de l'exploitation des ressources génétiques.\n\n"
            "Article 2 — Définitions\n"
            "La diversité biologique comprend la variabilité des organismes vivants de toute origine.\n\n"
            "Article 6 — Mesures générales de conservation et d'utilisation durable\n"
            "Chaque Partie élabore des stratégies, plans ou programmes nationaux concernant la conservation et l'utilisation durable."
        ),
        "source_url": "https://www.cbd.int/convention/text/",
        "source_name": "Convention sur la diversité biologique",
        "ratification_date": "1995-11-03",
    },
    {
        "title": "Convention des Nations Unies contre la criminalité transnationale organisée",
        "title_ar": "اتفاقية الأمم المتحدة لمكافحة الجريمة المنظمة عبر الوطنية",
        "category": "الجرائم المنظمة",
        "description": "Adoptée le 15 novembre 2000. Ratifiée par le Maroc le 12 septembre 2002.",
        "full_text": (
            "CONVENTION CONTRE LA CRIMINALITÉ ORGANISÉE TRANSNATIONALE\n\n"
            "Article 1 — Objectifs\n"
            "Les objectifs de la présente Convention sont: a) Promouvoir la coopération pour prévenir et combattre plus efficacement la criminalité transnationale organisée;\n"
            "b) Protéger les droits des victimes.\n\n"
            "Article 3 — Infractions visées\n"
            "Les infractions suivantes sont établies conformément à la présente Convention:\n"
            "a) Participation à un groupe criminel;\n"
            "b) Blanchiment des produits du crime;\n"
            "c) Corruption;\n"
            "d) Obstruction à la justice.\n\n"
            "Article 18 — Entraide judiciaire\n"
            "Les États parties s'entraident le plus largement possible."
        ),
        "source_url": "https://www.unodc.org/unodc/fr/organized-crime/intro/TOC.html",
        "source_name": "ONUDC — Criminalité organisée",
        "ratification_date": "2002-09-12",
    },
    {
        "title": "Convention des Nations Unies contre la corruption",
        "title_ar": "اتفاقية الأمم المتحدة لمكافحة الفساد",
        "category": "الجرائم المنظمة",
        "description": "Adoptée le 31 octobre 2003. Ratifiée par le Maroc le 7 novembre 2007.",
        "full_text": (
            "CONVENTION CONTRE LA CORRUPTION\n\n"
            "Article 1 — Objectifs\n"
            "Les objectifs de la présente Convention sont: a) Prévenir et combattre la corruption; b) Promouvoir et faciliter la coopération internationale; c) Promouvoir l'intégrité et la responsabilité.\n\n"
            "Article 9 — Secteurs publics et privés\n"
            "Chaque État partie adopte des mesures législatives, administratives ou autres pour prévenir la corruption.\n\n"
            "Article 15 — Corruption d'agents publics nationaux\n"
            "Chaque État partie prend les mesures nécessaires pour ériger en infraction pénale la corruption d'agents publics.\n\n"
            "Article 36 — Offices indépendants\n"
            "Chaque État partie considère l'adoption de mesures législatives pour améliorer la lutte contre la corruption."
        ),
        "source_url": "https://www.unodc.org/unodc/fr/corruption/convention.html",
        "source_name": "ONUDC — Convention contre la corruption",
        "ratification_date": "2007-11-07",
    },
    {
        "title": "Convention de La Haye sur les aspects civils de l'enlèvement international d'enfants",
        "title_ar": "اتفاقية لاهاي بشأن الجوانب المدنية لاختطاف الأطفال دولياً",
        "category": "حقوق الإنسان",
        "description": "Adoptée le 25 octobre 1980. Ratifiée par le Maroc le 1er août 2010.",
        "full_text": (
            "CONVENTION DE LA HAYE SUR L'ENLÈVEMENT D'ENFANTS\n\n"
            "Article 1\n"
            "La présente Convention a pour objet d'assurer la restitution immédiate des enfants déplacés illicitement.\n\n"
            "Article 3\n"
            "Le déplacement ou le non-retour d'un enfant est considéré comme illicite lorsqu'il viole un droit de garde.\n\n"
            "Article 12\n"
            "L'autorité centrale du pays de résidence prend toutes les mesures pour organiser la restitution.\n\n"
            "Article 13\n"
            "Il n'y a pas lieu d'ordonner la restitution de l'enfant lorsque celle-ci est contraire aux principes fondamentaux."
        ),
        "source_url": "https://www.hcch.net/fr/instruments/conventions/full-text/?cid=24",
        "source_name": "Organisation de la Coopération et du Développement Économiques",
            "ratification_date": "2010-08-01",
    },
    # ── French Legal Codes (language: "fr") ──────────────────────────────
    {
        "title": "Code civil marocain (Mudawwana)",
        "title_ar": "المدونة المدنية المغربية",
        "category": "القوانين المدنية",
        "language": "fr",
        "description": "Code civil marocain — lois personnelles, obligations, contrats, successions.",
        "full_text": """CODE CIVIL MAROCAIN — MUDAWWANA

Livre premier: Des personnes
Titre I: De la jouissance des droits civils
Art. 1er — La jouissance des droits civils est acquise par la naissance. Chaque être humain jouit des droits civils.

Titre II: De l'état des personnes
Art. 11 — L'acte de naissance est dressé dans les deux semaines suivant l'accouchement.
Art. 12 — Toute personne doit un nom à ses parents.

Livre deuxième: Des obligations et des contrats
Titre I: Des obligations en général
Art. 193 — L'obligation naît des conventions, des quasi-contrats, des délits et des quasi-délits.
Art. 194 — Une obligation ne peut exister sans cause licite.

Titre II: Des contrats
Art. 233 — Le contrat est un accord de volontés tendant à créer des obligations juridiques.
Art. 234 — Les conditions essentielles du contrat sont: le consentement, la capacité, un objet licite et une cause licite.

Livre troisième: Des successions
Art. 242 — La succession s'ouvre au dernier domicile du défunt.
Art. 273 — Les héritiers sont appelés à la succession dans l'ordre suivant: descendants, ascendants, collatéraux.

Source: Journal Officiel du Royaume du Maroc""",
        "source_url": "https://www.droitmarocain.com/codes/civil",
        "source_name": "Journal Officiel — Code civil",
        "ratification_date": "2004-02-03",
    },
    {
        "title": "Code pénal marocain",
        "title_ar": "القانون الجنائي المغربي",
        "category": "القوانين الجنائية",
        "language": "fr",
        "description": "Code pénal marocain — infractions, peines, circonstances aggravantes et atténuantes.",
        "full_text": """CODE PÉNAL MAROCAIN

Livre premier: Des infractions en général
Titre I: De la classification des infractions
Art. 1er — Est qualifié crime l'acte puni de la réclusion ou de la détention.
Art. 2 — Est qualifié délit l'acte puni de l'emprisonnement.
Art. 3 — Est qualifié contravention l'acte puni d'amende.

Titre II: De la tentative
Art. 15 — La tentative de crime est punissable lorsqu'elle est manifestée par un ou plusieurs actes extérieurs.
Art. 16 — La tentative de délit n'est punissable que dans les cas déterminés par la loi.

Titre III: De la récidive
Art. 57 — Quiconque aura été condamné pour crime à un emprisonnement de plus de six mois sera en cas de crime puni de la réclusion criminelle.

Livre deuxième: Des peines
Titre I: Des peines criminelles
Art. 18 — Les peines criminelles sont: la peine de mort, la réclusion à perpétuité, la réclusion temporaire, la détention.

Titre II: Des peines correctionnelles
Art. 20 — Les peines correctionnelles sont: l'emprisonnement et l'amende.

Source: Journal Officiel du Royaume du Maroc""",
        "source_url": "https://www.droitmarocain.com/codes/penal",
        "source_name": "Journal Officiel — Code pénal",
        "ratification_date": "1962-06-15",
    },
    {
        "title": "Code de commerce marocain",
        "title_ar": "قانون التجارة المغربي",
        "category": "القوانين التجارية",
        "language": "fr",
        "description": "Code de commerce — actes de commerce, sociétés commerciales, procédure collective.",
        "full_text": """CODE DE COMMERCE MAROCAIN

Livre premier: Des commerçants
Art. 1er — Est commerçant celui qui exerce des actes de commerce et en fait sa profession habituelle.
Art. 2 — Le mineur émancipé peut faire le commerce avec l'autorisation de ses parents.

Livre deuxième: Des sociétés commerciales
Art. 74 — La société commerciale est celle qui a pour objet des actes de commerce.
Art. 75 — Les sociétés commerciales sont: la société en nom collectif, la société en commandite, la société à responsabilité limitée, la société anonyme.

Art. 38 — La SARL peut être constituée par une seule personne.
Art. 39 — Le capital social est divisé en parts sociales.

Livre troisième: Des faillites
Art. 640 — Le jugement déclaratif de la faillite fixe la cessation des paiements.
Art. 641 — L'ouverture de la procédure collective ne peut intervenir qu'en cas de cessation des paiements.

Source: Journal Officiel du Royaume du Maroc""",
        "source_url": "https://www.droitmarocain.com/codes/commerce",
        "source_name": "Journal Officiel — Code de commerce",
        "ratification_date": "1996-10-01",
    },
    {
        "title": "Code de procédure civile marocain",
        "title_ar": "قانون أصول المحاكمات المدنية المغربي",
        "category": "قوانين الإجراءات",
        "language": "fr",
        "description": "Code de procédure civile — juridictions, instances, voies d'exécution, procédures collectives.",
        "full_text": """CODE DE PROCÉDURE CIVILE MAROCAIN

Livre premier: De l'organisation judiciaire
Titre I: Des juridictions
Art. 1er — Les juridictions civiles sont: le tribunal de première instance, la cour d'appel, la cour suprême.

Titre II: De la compétence
Art. 40 — Le tribunal de première instance est compétent pour les litiges dont le montant excède 5000 dirhams.
Art. 41 — Le tribunal de proximité est compétent pour les litiges dont le montant ne dépasse pas 5000 dirhams.

Livre deuxième: Des instances
Art. 80 — L'instance est liée par l'assignation.
Art. 81 — L'assignation doit contenir l'objet de la demande et les moyens invoqués.

Art. 149 — Le jugement doit être rendu dans les trois mois suivant les conclusions.
Art. 150 — Le jugement est signifié aux parties par voie d'huissier.

Source: Journal Officiel du Royaume du Maroc""",
        "source_url": "https://www.droitmarocain.com/codes/proc civile",
        "source_name": "Journal Officiel — Code de procédure civile",
        "ratification_date": "1996-10-01",
    },
    {
        "title": "Code de procédure pénale marocain",
        "title_ar": "قانون أصول المحاكمات الجنائية المغربي",
        "category": "قوانين الإجراءات",
        "language": "fr",
        "description": "Code de procédure pénale — instruction, poursuites, jugement, voies de recours.",
        "full_text": """CODE DE PROCÉDURE PÉNALE MAROCAIN

Livre premier: De la police judiciaire
Art. 1er — La police judiciaire recherche les infractions, rassemble les preuves et en搜père les auteurs.
Art. 2 — Les officiers de police judiciaire sont les juges d'instruction, les procureurs, les commissaires.

Livre deuxième: De l'instruction
Art. 201 — L'instruction est obligatoire en matière de crime.
Art. 202 — Le juge d'instruction procède à tous les actes d'information qu'il juge utiles.

Art. 248 — L'ordonnance de mise en accusation est rendue lorsque les charges suffisantes réunies.

Livre troisième: Du jugement
Art. 400 — Le tribunal correctionnel est composé de trois juges.
Art. 401 — Le président dirige les débats et assure le bon ordre des débats.

Source: Journal Officiel du Royaume du Maroc""",
        "source_url": "https://www.droitmarocain.com/codes/proc penale",
        "source_name": "Journal Officiel — Code de procédure pénale",
        "ratification_date": "1959-10-12",
    },
    {
        "title": "Code du travail marocain",
        "title_ar": "قانون الشغل المغربي",
        "category": "قانون الشغل",
        "language": "fr",
        "description": "Code du travail — contrat de travail, salaires, durée du travail, hygiène et sécurité, licenciement.",
        "full_text": """CODE DU TRAVAIL MAROCAIN

Livre premier: Du contrat de travail
Art. 1er — Le contrat de travail est l'accord par lequel une personne s'engage à mettre son travail, moyennant rémunération, sous la direction et l'autorité d'une autre personne physique ou morale.
Art. 3 — Le contrat de travail peut être conclu pour une durée déterminée ou indéterminée.
Art. 4 — La durée du travail ne peut excéder 44 heures par semaine en principe.

Livre deuxième: De la rémunération
Art. 145 — Le salaire minimum garanti est fixé par voie législative.
Art. 146 — La rémunération doit être payée à terme échu au plus tard une fois par mois.

Livre troisième: De la rupture du contrat
Art. 39 — Le contrat à durée indéterminée peut être rompu par l'une ou l'autre des parties moyennant un préavis.
Art. 40 — La durée du préavis est de: un mois pour la première année, deux mois pour la deuxième, trois mois pour la troisième et au-delà.

Art. 44 — Le licenciement doit être motivé et notifié par écrit.
Art. 45 — Le licenciement pour faute grave ou faute lourde ne donne pas lieu à indemnité.

Source: Journal Officiel du Royaume du Maroc""",
        "source_url": "https://www.droitmarocain.com/codes/travail",
        "source_name": "Journal Officiel — Code du travail",
        "ratification_date": "2004-04-12",
    },
    {
        "title": "Famille et droit marocain (Mudawwana — livre de la famille)",
        "title_ar": "مدونة الأسرة المغربية",
        "category": "قانون الأسرة",
        "language": "fr",
        "description": "Mudawwana — mariage, divorce, garde des enfants, pensions alimentaires, succession familiale.",
        "full_text": """MODAWWANA — LIVRE DE LA FAMILLE

Titre I: Du mariage
Art. 19 — Le mariage est un contrat juridique fondé sur le consentement libre des deux époux.
Art. 20 — L'âge légal du mariage est fixé à 18 ans pour les deux époux.
Art. 21 — Le consentement des épouses est requis pour la validité du mariage.
Art. 22 — Le mariage doit être célébré devant un officier d'état civil.

Art. 40 — Dot mahr: Le mari est tenu de verser à son épouse une dot à titre de contrepartie du mariage.

Titre II: Du divorce
Art. 76 — Le divorce peut être prononcé pour cause déterminée ou par consentement mutuel.
Art. 80 — Les causes de divorce sont: l'inconduite, le préjudice grave, l'abandon, la non-contribution aux charges du ménage.

Art. 102 — Le juge peut ordonner la médiation avant le prononcé du divorce.
Art. 113 — La garde des enfants est confiée à la mère si elle remplit les conditions d'aptitude.

Source: Journal Officiel du Royaume du Maroc""",
        "source_url": "https://www.droitmarocain.com/codes/famille",
        "source_name": "Journal Officiel — Mudawwana",
        "ratification_date": "2004-02-03",
    },
    {
        "title": "Code des obligations et des contrats (LOC)",
        "title_ar": "قانون الالتزامات والعقود",
        "category": "القوانين المدنية",
        "language": "fr",
        "description": "LOC — obligations, contrats, responsabilité civile, preuves, prescription.",
        "full_text": """CODE DES OBLIGATIONS ET DES CONTRATS

Livre premier: Des obligations en général
Art. 193 — L'obligation naît des conventions, des quasi-contrats, des délits et des quasi-délits.
Art. 194 — L'obligation ne peut exister sans cause licite.
Art. 195 — L'objet de l'obligation doit être possible, déterminé et licite.
Art. 210 — L'obligation naturelle est celle qui ne confère pas d'action en justice, mais qui a été volontairement exécutée.

Livre deuxième: Des contrats
Art. 233 — Le contrat est un accord de volontés tendant à créer des obligations juridiques.
Art. 234 — Les conditions essentielles sont: le consentement, la capacité, l'objet, la cause.
Art. 252 — Le dol est la cause de nullité du contrat lorsqu'il a déterminé le consentement.
Art. 253 — L'erreur est une cause de nullité lorsqu'elle porte sur la substance de la chose.

Livre troisième: De la responsabilité civile
Art. 82 — Tout fait de l'homme qui cause un dommage à autrui oblige celui par la faute duquel il est arrivé à le réparer.
Art. 83 — Le fait de l'animal ou de la chose est imposé à celui qui en est le gardien.
Art. 84 — Le fait personnel est imposé à son auteur.

Livre quatrième: De la preuve
Art. 93 — La preuve des obligations et de leur extinction est rapportée par écrit, par témoignage, par présomptions.
Art. 106 — L'aveu judiciaire constitue une preuve intégrale.

Livre cinquième: De la prescription
Art. 142 — La prescription trentenaire éteint toute action réelle ou personnelle.
Art. 143 — La prescription quinquennale s'applique aux actions en nullité.

Source: Code des obligations et des contrats — Maroc""",
        "source_url": "https://www.droitmarocain.com/codes/obligations",
        "source_name": "Journal Officiel — Code des obligations",
        "ratification_date": "1913-08-12",
    },
    # ── English Treaties (language: "en") ─────────────────────────────────
    {
        "title": "Universal Declaration of Human Rights",
        "title_ar": "الإعلان العالمي لحقوق الإنسان",
        "category": "حقوق الإنسان",
        "language": "en",
        "description": "Adopted by the UN General Assembly on 10 December 1948.",
        "full_text": """UNIVERSAL DECLARATION OF HUMAN RIGHTS

Adopted by General Assembly resolution 217 A (III) of 10 December 1948

PREAMBLE

WHEREAS recognition of the inherent dignity and of the equal and inalienable rights of all members of the human family is the foundation of freedom, justice and peace in the world,

WHEREAS disregard and contempt for human rights have resulted in barbarous acts which have outraged the conscience of mankind,

WHEREAS it is essential, if man is not to be compelled to have recourse, as a last resort, to rebellion against tyranny and oppression, that human rights should be protected by the rule of law,

Article 1.
All human beings are born free and equal in dignity and rights. They are endowed with reason and conscience and should act towards one another in a spirit of brotherhood.

Article 2.
Everyone is entitled to all the rights and freedoms set forth in this Declaration, without distinction of any kind, such as race, colour, sex, language, religion, political or other opinion, national or social origin, property, birth or other status.

Article 3.
Everyone has the right to life, liberty and security of person.

Article 4.
No one shall be held in slavery or servitude; slavery and the slave trade shall be prohibited in all their forms.

Article 5.
No one shall be subjected to torture or to cruel, inhuman or degrading treatment or punishment.

Article 6.
Everyone has the right to recognition everywhere as a person before the law.

Article 7.
All are equal before the law and are entitled without any discrimination to equal protection of the law.

Article 8.
Everyone has the right to an effective remedy by the competent national tribunals for acts violating the fundamental rights granted him by the constitution or by law.

Article 9.
No one shall be subjected to arbitrary arrest, detention or exile.

Article 10.
Everyone is entitled in full equality to a fair and public hearing by an independent and impartial tribunal.

Article 11.
Everyone charged with a penal offence has the right to be presumed innocent until proved guilty according to law in a public trial.

Article 12.
No one shall be subjected to arbitrary interference with his privacy, family, home or correspondence.

Article 13.
Everyone has the right to freedom of movement within the borders of each state.
Everyone has the right to leave any country, including his own, and to return to his country.

Article 14.
Everyone has the right to seek and to enjoy in other countries asylum from persecution.
This right may not be invoked in the case of prosecutions genuinely arising from non-political crimes.

Article 15.
Everyone has the right to a nationality.
No one shall be arbitrarily deprived of his nationality nor denied the right to change his nationality.

Article 16.
Men and women of full age, without any limitation due to race, nationality or religion, have the right to marry and to found a family.

Article 17.
Everyone has the right to own property alone as well as in association with others.
No one shall be arbitrarily deprived of his property.

Article 18.
Everyone has the right to freedom of thought, conscience and religion; this right includes freedom to change his religion or belief.

Article 19.
Everyone has the right to freedom of opinion and expression; this right includes freedom to hold opinions without interference and to seek, receive and impart information and ideas through any media.

Article 20.
Everyone has the right to freedom of peaceful assembly and association.

Article 21.
Everyone has the right to take part in the government of his country, directly or through freely chosen representatives.

Article 22.
Everyone, as a member of society, has the right to social security.

Article 23.
Everyone has the right to work, to free choice of employment, to just and favourable conditions of work.

Article 24.
Everyone has the right to rest and leisure.

Article 25.
Everyone has the right to a standard of living adequate for the health and well-being of himself and of his family.

Article 26.
Everyone has the right to education. Education shall be free, at least in the elementary and fundamental stages.

Article 27.
Everyone has the right freely to participate in the cultural life of the community.

Article 28.
Everyone is entitled to a social and international order in which the rights set forth in this Declaration can be fully realized.""",
        "source_url": "https://www.un.org/en/about-us/universal-declaration-of-human-rights",
        "source_name": "United Nations",
        "ratification_date": "1948-12-10",
    },
    {
        "title": "Convention on the Rights of the Child",
        "title_ar": "اتفاقية حقوق الطفل",
        "category": "حقوق الإنسان",
        "language": "en",
        "description": "Adopted by the UN General Assembly on 20 November 1989. Ratified by Morocco on 21 June 1993.",
        "full_text": """CONVENTION ON THE RIGHTS OF THE CHILD

Adopted by General Assembly resolution 44/25 of 20 November 1989

PREAMBLE

The States Parties to the present Convention,

Considering that, in accordance with the principles proclaimed in the Charter of the United Nations, recognition of the inherent dignity and of the equal and inalienable rights of all members of the human family is the foundation of freedom, justice and peace in the world,

Bearing in mind that the peoples of the United Nations have, in the Charter, reaffirmed their faith in fundamental human rights and in the dignity and worth of the human person,

Article 1.
For the purposes of the present Convention, a child means every human being below the age of eighteen years unless under the law applicable to the child, majority is attained earlier.

Article 2.
States Parties shall respect the rights set forth in the present Convention without distinction of any kind.

Article 3.
In all actions concerning children, whether undertaken by public or private social welfare institutions, courts of law, administrative authorities or legislative bodies, the best interests of the child shall be a primary consideration.

Article 4.
States Parties shall undertake all appropriate legislative, administrative, and other measures for the implementation of the rights recognized in the present Convention.

Article 5.
States Parties shall respect the responsibilities, rights and duties of parents to provide appropriate guidance.

Article 6.
1. States Parties recognize that every child has the inherent right to life.
2. States Parties shall ensure to the maximum extent possible the survival and development of the child.

Article 7.
1. The child shall be registered immediately after birth and shall have the right to acquire a name and a nationality.

Article 8.
1. States Parties undertake to respect the right of the child to preserve his or her identity.

Article 9.
1. States Parties shall ensure that a child shall not be separated from his or her parents against their will.

Article 12.
1. States Parties shall assure to the child who is capable of forming his or her own views the right to express those views freely in all matters affecting the child.

Article 13.
1. The child shall have the right to freedom of expression; this right shall include freedom to seek, receive and impart information and ideas of all kinds.

Article 19.
1. States Parties shall take all appropriate legislative, administrative, social and educational measures to protect the child from all forms of physical or mental violence, injury or abuse, neglect or maltreatment.

Article 28.
1. States Parties recognize the right of the child to education.""",
        "source_url": "https://www.ohchr.org/en/instruments-mechanisms/instruments/convention-rights-child",
        "source_name": "United Nations — OHCHR",
        "ratification_date": "1993-06-21",
    },
    {
        "title": "International Covenant on Civil and Political Rights",
        "title_ar": "العهد الدولي الخاص بالحقوق المدنية والسياسية",
        "category": "حقوق الإنسان",
        "language": "en",
        "description": "Adopted on 16 December 1966. Ratified by Morocco on 3 May 1979.",
        "full_text": """INTERNATIONAL COVENANT ON CIVIL AND POLITICAL RIGHTS

Adopted by General Assembly resolution 2200A (XXI) of 16 December 1966

Article 1.
All peoples have the right of self-determination.

Article 2.
Each State Party to the present Covenant undertakes to respect and to ensure to all individuals within its territory and subject to its jurisdiction the rights recognized in the present Covenant.

Article 6.
Every human being has the inherent right to life.

Article 7.
No one shall be subjected to torture or to cruel, inhuman or degrading treatment or punishment.

Article 9.
Everyone has the right to liberty and security of person.

Article 14.
All persons shall be equal before the courts and tribunals.

Article 18.
Everyone shall have the right to freedom of thought, conscience and religion.

Article 19.
Everyone shall have the right to hold opinions without interference and the right to freedom of expression.

Article 25.
Every citizen shall have the right and the opportunity, without unreasonable restrictions, to take part in the conduct of public affairs.""",
        "source_url": "https://www.ohchr.org/en/instruments-mechanisms/instruments/international-covenant-civil-and-political-rights",
        "source_name": "United Nations — OHCHR",
        "ratification_date": "1979-05-03",
    },
    {
        "title": "Convention against Torture and Other Cruel, Inhuman or Degrading Treatment or Punishment",
        "title_ar": "الاتفاقية ضد التعذيب وغيره من المعاملات أو العقوبات القاسية أو الحاطة بالكرامة",
        "category": "حقوق الإنسان",
        "language": "en",
        "description": "Adopted on 10 December 1984. Ratified by Morocco on 21 June 1993.",
        "full_text": """CONVENTION AGAINST TORTURE AND OTHER CRUEL, INHUMAN OR DEGRADING TREATMENT OR PUNISHMENT

Adopted by General Assembly resolution 39/46 of 10 December 1984

Article 1.
For the purposes of this Convention, torture means any act by which severe pain or suffering, whether physical or mental, is intentionally inflicted on a person.

Article 2.
Each State Party shall take effective legislative, administrative, judicial or other measures to prevent acts of torture in any territory under its jurisdiction.

Article 3.
No State Party shall expel, return or extradite a person to another State where there are substantial grounds for believing that he would be in danger of being subjected to torture.

Article 12.
Each State Party shall ensure that its competent authorities proceed to a prompt and impartial investigation wherever there is reasonable ground to believe that an act of torture has been committed.""",
        "source_url": "https://www.ohchr.org/en/instruments-mechanisms/instruments/convention-against-torture",
        "source_name": "United Nations — OHCHR",
        "ratification_date": "1993-06-21",
    },
    {
        "title": "Convention on the Elimination of All Forms of Discrimination Against Women",
        "title_ar": "اتفاقية القضاء على جميع أشكال التمييز ضد المرأة",
        "category": "حقوق الإنسان",
        "language": "en",
        "description": "Adopted on 18 December 1979. Ratified by Morocco on 21 June 1993.",
        "full_text": """CONVENTION ON THE ELIMINATION OF ALL FORMS OF DISCRIMINATION AGAINST WOMEN

Adopted by General Assembly resolution 34/180 of 18 December 1979

Article 1.
For the purposes of the present Convention, the term "discrimination against women" means any distinction, exclusion or restriction made on the basis of sex.

Article 2.
States Parties condemn discrimination against women in all its forms and agree to pursue by all appropriate means a policy of eliminating discrimination against women.

Article 3.
States Parties shall take in all fields, in particular in the political, social, economic and cultural fields, all appropriate measures, including legislation, to ensure the full development and advancement of women.

Article 5.
States Parties shall take all appropriate measures to modify the social and cultural patterns of conduct of men and women.

Article 10.
States Parties shall take all appropriate measures to eliminate discrimination against women in the field of education.

Article 16.
States Parties shall take all appropriate measures to eliminate discrimination against women in all matters relating to marriage and family relations.""",
        "source_url": "https://www.ohchr.org/en/instruments-mechanisms/instruments/convention-elimination-all-forms-discrimination-against-women",
        "source_name": "United Nations — OHCHR",
        "ratification_date": "1993-06-21",
    },
    {
        "title": "Convention on the Rights of Persons with Disabilities",
        "title_ar": "اتفاقية حقوق الأشخاص ذوي الإعاقة",
        "category": "حقوق الإنسان",
        "language": "en",
        "description": "Adopted on 13 December 2006. Ratified by Morocco on 8 April 2009.",
        "full_text": """CONVENTION ON THE RIGHTS OF PERSONS WITH DISABILITIES

Adopted by General Assembly resolution 61/106 of 13 December 2006

Article 1.
The purpose of the present Convention is to promote, protect and ensure the full and equal enjoyment of all human rights and fundamental freedoms by all persons with disabilities.

Article 3.
The principles of the present Convention are: respect for inherent dignity, non-discrimination, full participation, equality of opportunity, accessibility, equality between men and women.

Article 9.
States Parties shall take appropriate measures to ensure accessibility for persons with disabilities.

Article 19.
Persons with disabilities have the right to live independently and to be included in the community.

Article 24.
States Parties recognize the right of persons with disabilities to education.""",
        "source_url": "https://www.ohchr.org/en/instruments-mechanisms/instruments/convention-rights-persons-disabilities",
        "source_name": "United Nations — OHCHR",
        "ratification_date": "2009-04-08",
    },
    # ── Spanish Treaties (language: "es") ─────────────────────────────────
    {
        "title": "Declaración Universal de los Derechos Humanos",
        "title_ar": "الإعلان العالمي لحقوق الإنسان",
        "category": "حقوق الإنسان",
        "language": "es",
        "description": "Adoptada por la Asamblea General de las Naciones Unidas el 10 de diciembre de 1948.",
        "full_text": """DECLARACIÓN UNIVERSAL DE LOS DERECHOS HUMANOS

Aprobada por la Asamblea General en su resolución 217 A (III), de 10 de diciembre de 1948

PREÁMBULO

Considerando que la libertad, la justicia y la paz en el mundo tienen por base el reconocimiento de la dignidad intrínseca y de los derechos iguales e inalienables de todos los miembros de la familia humana,

Considerando que el desconocimiento y el menosprecio de los derechos humanos han originado actos de barbarie que han conmovido la conciencia de la humanidad,

Considerando que es esencial que los derechos humanos sean protegidos por un régimen de derecho,

Artículo 1.
Todos los seres humanos nacen libres e iguales en dignidad y en derechos y, dotados como están de razón y conciencia, deben comportarse fraternalmente los unos con los otros.

Artículo 2.
Toda persona tiene los derechos y libertades proclamados en esta Declaración, sin distinción alguna de raza, color, sexo, idioma, religión, opinión política o de cualquier otra índole.

Artículo 3.
Todo individuo tiene derecho a la vida, a la libertad y a la seguridad de su persona.

Artículo 4.
Nadie estará sometido a esclavitud ni a servidumbre; la esclavitud y la trata de esclavos están prohibidas en todas sus formas.

Artículo 5.
Nadie será sometido a torturas ni a penas o tratos crueles, inhumanos o degradantes.

Artículo 6.
Todo ser humano tiene derecho, en todas partes, al reconocimiento de su personalidad jurídica.

Artículo 7.
Todos son iguales ante la ley y tienen, sin distinción, derecho a igual protección de la ley.

Artículo 18.
Todo individuo tiene derecho a la libertad de pensamiento, de conciencia y de religión.

Artículo 19.
Todo individuo tiene derecho a la libertad de opinión y de expresión.

Artículo 25.
Todo ser humano tiene derecho a un nivel de vida adecuado que le asegure, así como a su familia, la salud y el bienestar.

Artículo 26.
Todo ser humano tiene derecho a la educación.""",
        "source_url": "https://www.un.org/es/about-us/universal-declaration-of-human-rights",
        "source_name": "Naciones Unidas",
        "ratification_date": "1948-12-10",
    },
    {
        "title": "Convención sobre los Derechos del Niño",
        "title_ar": "اتفاقية حقوق الطفل",
        "category": "حقوق الإنسان",
        "language": "es",
        "description": "Aprobada por la Asamblea General de las Naciones Unidas el 20 de noviembre de 1989. Ratificada por Marruecos el 21 de junio de 1993.",
        "full_text": """CONVENCIÓN SOBRE LOS DERECHOS DEL NIÑO

Aprobada por la Asamblea General en su resolución 44/25, de 20 de noviembre de 1989

PREÁMBULO

Los Estados Partes en la presente Convención,

Considerando que, de conformidad con los principios proclamados en la Carta de las Naciones Unias, la libre determinación de los pueblos es un principio del derecho internacional,

Artículo 1.
A los efectos de la presente Convención, se entiende por niño todo ser humano menor de dieciocho años de edad.

Artículo 2.
Los Estados Partes respetarán los derechos enunciados en la presente Convención y los garantizarán a todo niño de su jurisdicción.

Artículo 3.
En todas las decisiones que se adopten respecto de los niños, la consideración primordial que se tendrá en cuenta será el interés superior del niño.

Artículo 6.
1. Los Estados Partes reconocen que todo niño tiene el derecho intrínseco a la vida.
2. Los Estados Partes velarán por la supervivencia y el desarrollo del niño.

Artículo 12.
1. Los Estados Partes garantizarán al niño que esté en condiciones de formarse un juicio propio el derecho de expresar su opinión libremente.

Artículo 13.
1. El niño tendrá derecho a la libertad de expresión; este derecho incluirá la libertad de buscar, recibir y difundir informaciones e ideas de toda índole.

Artículo 19.
1. Los Estados Partes adoptarán todas las medidas legislativas, administrativas, sociales y educacionales apropiadas para proteger al niño contra toda forma de violencia física o mental.

Artículo 28.
1. Los Estados Partes reconocen el derecho del niño a la educación.""",
        "source_url": "https://www.ohchr.org/es/instruments-mechanisms/instruments/convention-rights-child",
        "source_name": "Naciones Unidas — ACNUDH",
        "ratification_date": "1993-06-21",
    },
    {
        "title": "Convenio 29 de la OIT sobre el trabajo forzado",
        "title_ar": "اتفاقية منظمة العمل الدولية رقم 29 بشأن العمل القسري",
        "category": "العمل والضمان الاجتماعي",
        "language": "es",
        "description": "Adoptada el 28 de junio de 1930. Ratificada por Marruecos el 18 de septiembre de 1957.",
        "full_text": """CONVENIO (N.° 29) SOBRE EL TRABAJO FORZOSO U OBLIGATORIO

Adoptado por la Conferencia Internacional del Trabajo en su 14.ª reunión, Ginebra, 28 de junio de 1930

Artículo 2.
Para los fines del presente Convenio, la expresión trabajo forzoso u obligatorio designará todo trabajo o servicio exigido a un individuo bajo la amenaza de una pena cualquiera y para el cual dicho individuo no se haya ofrecido espontáneamente.

Artículo 3.
La expresión trabajo forzoso u obligatorio no comprenderá:
a) Todo trabajo o servicio exigido con fines militaires;
b) Todo trabajo o servicio que forme parte de las obligaciones cívicas normales;
c) Todo trabajo o servicio en ejecución de una condena impuesta por una autoridad judicial competente.

Artículo 4.
La autoridad pública no podrá imponer trabajo forzoso u obligatorio.""",
        "source_url": "https://www.ilo.org/dyn/normlex/en/f?p=NORMLEXPUB:12100:0::NO::P12100_ILO_CODE:C029",
        "source_name": "Organización Internacional del Trabajo",
        "ratification_date": "1957-09-18",
    },
    {
        "title": "Convención sobre la eliminación de todas las formas de discriminación contra la mujer",
        "title_ar": "اتفاقية القضاء على جميع أشكال التمييز ضد المرأة",
        "category": "حقوق الإنسان",
        "language": "es",
        "description": "Adoptada el 18 de diciembre de 1979. Ratificada por Marruecos el 21 de junio de 1993.",
        "full_text": """CONVENCIÓN SOBRE LA ELIMINACIÓN DE TODAS LAS FORMAS DE DISCRIMINACIÓN CONTRA LA MUJER

Adoptada por la Asamblea General en su resolución 34/180, de 18 de diciembre de 1979

Artículo 1.
A los efectos de la presente Convención, la expresión "discriminación contra la mujer" denotará toda distinción, exclusión o restricción basada en el sexo.

Artículo 2.
Los Estados Partes condenan la discriminación contra la mujer en todas sus formas y convienen en perseguir por todos los medios apropiados y sin dilaciones una política de eliminación de la discriminación contra la mujer.

Artículo 3.
Los Estados Partes tomarán en todos los ámbitos, en particular en los políticos, sociales, económicos y culturales, todas las medidas apropiadas, incluso de carácter legislativo, para asegurar el pleno desarrollo y el adelanto de la mujer.

Artículo 5.
Los Estados Partes tomarán todas las medidas apropiadas para modificar los patrones socioculturares de conducta de hombres y mujeres.

Artículo 10.
Los Estados Partes tomarán todas las medidas apropiadas para eliminar la discriminación contra la mujer en el campo de la educación.

Artículo 16.
Los Estados Partes tomarán todas las medidas apropiadas para eliminar la discriminación contra la mujer en todos los asuntos relativos al matrimonio y las relaciones familiares.""",
        "source_url": "https://www.ohchr.org/es/instruments-mechanisms/instruments/convention-elimination-all-forms-discrimination-against-women",
        "source_name": "Naciones Unidas — ACNUDH",
        "ratification_date": "1993-06-21",
    },
    # ── Arabic Treaties (language: "ar") ──────────────────────────────────
    {
        "title": "الإعلان العالمي لحقوق الإنسان",
        "title_ar": "الإعلان العالمي لحقوق الإنسان",
        "category": "حقوق الإنسان",
        "language": "ar",
        "description": "أُadopted by the UN General Assembly on 10 December 1948. صدر عن الجمعية العامة للأمم المتحدة في 10 ديسمبر 1948.",
        "full_text": """الإعلان العالمي لحقوق الإنسان

أقرته الجمعية العامة للأمم المتحدة بموجب قرارها 217 (أ) (الثالث) الصادر في 10 ديسمبر 1948

الديباجة

إذ كان الاعتراف بالكرامة المتأصلة في جميع أعضاء الأسرة البشرية وبحقوقهم المتساوية والغير قابلة للتصرف هو أساس الحرية والعدالة والسلام في العالم،
وإذا كان إغفال وازدراء حقوق الإنسان قد أدّى إلى أعمال بربرية هزّت ضمير الإنسانية،
وإذا كان من الضروري أن تحمي الحقوق_human rights by the rule of law،

المادة 1.
يولد جميع الناس أحرارًا متساوين في الكرامة والحقوق. هم قدّرة على العقل والضمير وعليهم أن يتعاملوا مع بعضهم البعض في روح الإخاء.

المادة 2.
لكل إنسان حق التمتع بجميع الحقوق والحرية المنصوص عليها في هذا الإعلان دون أي تمييز.

المادة 3.
لكل شخص الحق في الحياة والحرية وأمن شخصه.

المادة 4.
لا يجوز لأحد أن يُحتقر ولا أن يُستعبَد؛lar slavery and the slave trade are prohibited in all their forms.

المادة 5.
لا يجوز إخضاع أحد للتعذيب أو لمعاملة أو عقوبة قاسية أو وحشية أو مهينة.

المادة 6.
لكل شخص الحق في أن يُعترف به في كل مكان شخصًا أمام القانون.

المادة 7.
جميع الناس متساوون أمام القانون ولهم دون أي تمييز حق الحماية المتساوية أمامه.

المادة 18.
لكل شخص الحق في حرية الفكر والضمير والدين.

المادة 19.
لكل شخص الحق في حرية الرأي والتعبير.

المادة 25.
لكل شخص الحق في مستوى معيشي كافٍ يضمن صحته ورفاهيته وصحة ورفاهية عائلته.

المادة 26.
لكل شخص الحق في التعليم.""",
        "source_url": "https://www.un.org/ar/about-us/universal-declaration-of-human-rights",
        "source_name": "الأمم المتحدة",
        "ratification_date": "1948-12-10",
    },
    {
        "title": "اتفاقية حقوق الطفل",
        "title_ar": "اتفاقية حقوق الطفل",
        "category": "حقوق الإنسان",
        "language": "ar",
        "description": "أقرتها الجمعية العامة للأمم المتحدة في 20 نوفمبر 1989. صادق عليها المغرب في 21 يونيو 1993.",
        "full_text": """اتفاقية حقوق الطفل

أقرتها الجمعية العامة للأمم المتحدة بموجب قرارها 44/25 الصادر في 20 نوفمبر 1989

المادة 1.
لأغراض هذه الاتفاقية، يعني الطفل كل إنسان لم يتجاوز الثامنة عشرة من عمره ما لم يبلغ الرشد قبل ذلك بموجب القانون المعمول به.

المادة 2.
تحترم الدول الأطراف الحقوق المنصوص عليها في هذه الاتفاقية وتضمنها لكل طفل خاضع لسلطتها دون أي تمييز.

المادة 3.
اتخذ جميع القرارات المتعلقة بالأطفال考量 المصلحة الفضلى للطفل.

المادة 6.
1. تعترف الدول الأطراف بأن للطفل حقًا جوهريًا في الحياة.
2. تضمن الدول الأطراف إلى أقصى حد ممكن بقاء الطفل وتطوره.

المادة 12.
1. تكفل الدول الأطراف للطفل القادر على تكوين رأي خاص به حق التعبير عن رأيه بحرية في جميع مسائله.

المادة 13.
1. للطفل حق حرية التعبير ويشمل ذلك حرية طلب وتلقي ونشر المعلومات والأفكار من كل نوع.

المادة 19.
1. تتخذ الدول الأطراف جميع التدابير المناسبة لحماية الطفل من جميع أشكال العنف الجسدي أو النفسي.

المادة 28.
1. تعترف الدول الأطراف بحق الطفل في التعليم.""",
        "source_url": "https://www.ohchr.org/ar/instruments-mechanisms/instruments/convention-rights-child",
        "source_name": "الأمم المتحدة — المفوضية السامية لحقوق الإنسان",
        "ratification_date": "1993-06-21",
    },
    {
        "title": "الاتفاقية الدولية بشأن الحقوق المدنية والسياسية",
        "title_ar": "العهد الدولي الخاص بالحقوق المدنية والسياسية",
        "category": "حقوق الإنسان",
        "language": "ar",
        "description": "أقرتها الجمعية العامة للأمم المتحدة في 16 ديسمبر 1966. صادق عليها المغرب في 3 مايو 1979.",
        "full_text": """العهد الدولي الخاص بالحقوق المدنية والسياسية

أقرته الجمعية العامة للأمم المتحدة بموجب قرارها 2200 أ (الحادية والعشرون) الصادر في 16 ديسمبر 1966

المادة 1.
لجميع الشعوب حق تقرير المصير.

المادة 2.
تلتزم كل دولة طرف في هذا العهد احترام الحقوق المنصوص عليها فيه وضمانها لكل فرد في إقليمها وخاضع لسلطتها.

المادة 6.
لكل إنسان حق متأصل في الحياة.

المادة 7.
لا يجوز إخضاع أحد للتعذيب ولا لمعاملة أو عقوبة قاسية أو وحشية أو مهينة.

المادة 9.
لكل شخص حق الحرية والأمن الشخصي.

المادة 14.
جميع الأشخاص متساوون أمام المحاكم والCourts.

المادة 18.
لكل شخص حق حرية الفكر والضمير والدين.

المادة 19.
لكل شخص حق حرية الرأي والتعبير.

المادة 25.
لكل مواطن الحق والفرصة في المشاركة في إدارة شؤون بلده.""",
        "source_url": "https://www.ohchr.org/ar/instruments-mechanisms/instruments/international-covenant-civil-and-political-rights",
        "source_name": "الأمم المتحدة — المفوضية السامية لحقوق الإنسان",
        "ratification_date": "1979-05-03",
    },
]


def _ensure_table():
    with db_session() as conn:
        conn.executescript(TABLE_DDL)


def seed_treaties():
    """Insert seed treaties if the table is empty (idempotent)."""
    _ensure_table()
    with db_session() as conn:
        count = conn.execute("SELECT COUNT(*) FROM french_legal_texts").fetchone()[0]
        if count > 0:
            return
        for t in SEED_DATA:
            conn.execute(
                """INSERT INTO french_legal_texts
                   (title, title_ar, category, description, full_text,
                    source_url, source_name, ratification_date, language)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    t["title"], t["title_ar"], t["category"], t["description"],
                    t["full_text"], t["source_url"], t["source_name"],
                    t["ratification_date"], t.get("language", "fr"),
                ),
            )


def list_treaties(category: str | None = None, query: str | None = None, language: str | None = None):
    _ensure_table()
    seed_treaties()
    with db_session() as conn:
        sql = (
            "SELECT id, title, title_ar, category, description, "
            "ratification_date, source_name, language FROM french_legal_texts WHERE 1=1"
        )
        params: list = []
        if category:
            sql += " AND category = ?"
            params.append(category)
        if language:
            sql += " AND language = ?"
            params.append(language)
        if query:
            sql += " AND (title LIKE ? OR title_ar LIKE ? OR description LIKE ?)"
            like = f"%{query}%"
            params.extend([like, like, like])
        sql += " ORDER BY ratification_date ASC"
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


def get_treaty(treaty_id: int):
    _ensure_table()
    with db_session() as conn:
        row = conn.execute(
            "SELECT * FROM french_legal_texts WHERE id = ?", (treaty_id,)
        ).fetchone()
        return dict(row) if row else None


def search_treaties(query: str):
    return list_treaties(query=query)


def list_categories(language: str | None = None):
    _ensure_table()
    with db_session() as conn:
        sql = "SELECT DISTINCT category FROM french_legal_texts"
        params: list = []
        if language:
            sql += " WHERE language = ?"
            params.append(language)
        sql += " ORDER BY category"
        rows = conn.execute(sql, params).fetchall()
        return [r["category"] for r in rows]
