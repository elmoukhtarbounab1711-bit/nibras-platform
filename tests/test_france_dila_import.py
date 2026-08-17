"""اختبارات محلِّل مستورد النصوص الرسمية الفرنسية (DILA).

تغطي دالتي _text و_body ضد عينات XML رسمية (Conseil constitutionnel،
Cour de cassation) للتأكد من القراءة الحرفية: العنوان، المحكمة، الرقم،
التاريخ، الحل، ونص القرار (تحويل <br/> إلى أسطر وإزالة الوسوم دون فقدان).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import import_france_dila as fr

CONSTIT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<TEXTE_JURI_CONSTIT>
<META><META_COMMUN><ID>CONSTEXT000054617305</ID></META_COMMUN>
<META_SPEC><META_JURI>
<TITRE>Loi visant à renforcer la sécurité</TITRE>
<DATE_DEC>2026-07-23</DATE_DEC>
<JURIDICTION>Conseil constitutionnel</JURIDICTION>
<NUMERO>2026-906</NUMERO>
<SOLUTION>Conformité - réserve</SOLUTION>
</META_JURI>
<META_JURI_CONSTIT><URL_CC>https://www.conseil-constitutionnel.fr/decision/2026/2026906DC.htm</URL_CC>
<ECLI>ECLI:FR:CC:2026:2026.906.DC</ECLI></META_JURI_CONSTIT>
</META_SPEC></META>
<TEXTE><BLOC_TEXTUEL><CONTENU>LE CONSEIL CONSTITUTIONNEL A ÉTÉ SAISI.<br/><br/>Article 61.<br/>Conformité.</CONTENU></BLOC_TEXTUEL></TEXTE>
</TEXTE_JURI_CONSTIT>
"""

CASS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<TEXTE_JURI_JUDI>
<META><META_COMMUN><ID>JURITEXT000052384123</ID></META_COMMUN>
<META_SPEC><META_JURI>
<TITRE>Cour de cassation, civile, Chambre commerciale, 8 octobre 2025, 24-16.995, Publié au bulletin</TITRE>
<DATE_DEC>2025-10-08</DATE_DEC>
<JURIDICTION>Cour de cassation</JURIDICTION>
<SOLUTION>Cassation partielle</SOLUTION>
</META_JURI>
<META_JURI_JUDI>
<NUMERO_AFFAIRE>24-16995</NUMERO_AFFAIRE>
<ECLI>ECLI:FR:CCASS:2025:CO00504</ECLI>
</META_JURI_JUDI>
</META_SPEC></META>
<TEXTE><BLOC_TEXTUEL><CONTENU>LA COUR DE CASSATION a rendu l'arrêt suivant&nbsp;: <br/> Cassation partielle.<br/> Dispositif.</CONTENU></BLOC_TEXTUEL></TEXTE>
</TEXTE_JURI_JUDI>
"""


def test_text_field_constit():
    assert fr._text("TITRE", CONSTIT_XML) == "Loi visant à renforcer la sécurité"
    assert fr._text("NUMERO", CONSTIT_XML) == "2026-906"
    assert fr._text("DATE_DEC", CONSTIT_XML) == "2026-07-23"
    assert fr._text("SOLUTION", CONSTIT_XML) == "Conformité - réserve"
    assert fr._text("ECLI", CONSTIT_XML) == "ECLI:FR:CC:2026:2026.906.DC"


def test_text_field_cass():
    assert fr._text("JURIDICTION", CASS_XML) == "Cour de cassation"
    assert fr._text("NUMERO_AFFAIRE", CASS_XML) == "24-16995"
    assert fr._text("ECLI", CASS_XML) == "ECLI:FR:CCASS:2025:CO00504"


def test_body_strips_tags_keeps_text():
    body = fr._body(CONSTIT_XML)
    assert "LE CONSEIL CONSTITUTIONNEL A ÉTÉ SAISI." in body
    assert "Article 61." in body
    assert "Conformité." in body
    assert "<br" not in body and "<" not in body
    # كل سطر = فقرة (تحويل br إلى أسطر)
    lines = [l for l in body.splitlines() if l.strip()]
    assert len(lines) >= 3


def test_body_unescapes_entities():
    body = fr._body(CASS_XML)
    assert "l'arrêt suivant" in body
    assert "&nbsp;" not in body
    # الفضاء غير المنكسر (U+00A0) من &nbsp; يُحفظ حرفيًا كما في المصدر
    assert "\u00a0" in body


def test_datasets_config():
    assert set(fr.DATASETS) == {"constitu", "cass"}
    assert fr.DATASETS["constitu"]["cat_slug"] == "dostouri"
    assert fr.DATASETS["cass"]["cat_slug"] == "cassation"
    for cfg in fr.DATASETS.values():
        assert cfg["url"].startswith("https://echanges.dila.gouv.fr/")
