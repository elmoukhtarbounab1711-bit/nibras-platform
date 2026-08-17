"""
نبراس — زرع نصوص قانونية واجتهادات قضائية حقيقية لفرنسا ومصر (المرحلة 20).
يستدعي واجهة الإدارة المحلية على المنفذ 8000 عبر urllib فقط.
لا يمسّ المغرب إطلاقًا (jurisdiction_id=1 لا يُعدَّل).
"""
import json
import sys
import urllib.request
import urllib.error

BASE = "http://localhost:8000"


def load_token():
    with open(sys.argv[1] if len(sys.argv) > 1 else "admintoken.txt", "r",
              encoding="ascii") as fh:
        return fh.read().strip()


TOKEN = load_token()


def call(method, path, payload=None):
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(BASE + path, data=body, method=method)
    req.add_header("Authorization", "Bearer " + TOKEN)
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        return e.code, (json.loads(raw) if raw else {"error": str(e)})


def create_text(t):
    code, data = call("POST", "/api/admin/texts", {
        "category_id": t["category_id"], "type": t["type"], "title": t["title"],
        "official_ref": t.get("official_ref"), "enacted_date": t.get("enacted_date"),
        "last_amended": t.get("last_amended"), "source_note": t.get("source_note"),
        "jurisdiction_id": t["jurisdiction_id"], "is_sample_data": 0,
    })
    if code not in (200, 201):
        print(f"  ! text FAIL ({code}): {data}")
        return None
    return data["id"]


def add_articles(text_id, articles):
    ok = 0
    for a in articles:
        code, data = call("POST", f"/api/admin/texts/{text_id}/articles", {
            "number": a["number"], "label": a["label"], "content": a["content"],
            "plain_explanation": a.get("plain_explanation", ""),
            "keywords": a.get("keywords", ""),
        })
        if code in (200, 201):
            ok += 1
        else:
            print(f"  ! article FAIL ({code}): {a['number']} {data}")
    print(f"  articles ok: {ok}/{len(articles)}")


def create_decision(d):
    code, data = call("POST", "/api/admin/jurisprudence", {
        "title": d["title"], "content": d["content"], "principles": d.get("principles", ""),
        "category_slug": d["category_slug"], "jurisdiction_id": d["jurisdiction_id"],
        "court": d.get("court", ""), "decision_number": d.get("decision_number", ""),
        "decision_date": d.get("decision_date", ""), "source_note": d.get("source_note", ""),
        "published": True,
    })
    if code not in (200, 201):
        print(f"  ! decision FAIL ({code}): {d['title']} {data}")
        return None
    print(f"  + decision id={data.get('id')} — {d['title'][:60]}")
    return data.get("id")


def delete_text(text_id):
    code, data = call("DELETE", f"/api/admin/texts/{text_id}")
    print(f"  delete text {text_id} -> {code}")


def delete_decision(did):
    code, data = call("DELETE", f"/api/admin/jurisprudence/{did}")
    print(f"  delete decision {did} -> {code}")


# ------------------------------------------------ FRANCE (jurisdiction 3)
FRANCE = [
    {
        "title": "Code civil (Code Napoléon)",
        "category_id": 2, "type": "code", "jurisdiction_id": 3,
        "official_ref": "Code civil — promulgué le 21 mars 1804 (30 ventôse an XII)",
        "enacted_date": "1804-03-21", "last_amended": "2016-10-01",
        "source_note": "Texte officiel en vigueur (Légifrance). Les articles 1103, 1104, 1240, 1241 et 1353 reprennent la numérotation de l'ordonnance n° 2016-131 du 10 février 2016.",
        "articles": [
            {"number": "544", "label": "Article 544", "content": "La propriété est le droit de jouir et disposer des choses de la manière la plus absolue, pourvu qu'on n'en fasse pas un usage prohibé par les lois ou par les règlements.", "keywords": "ملكية, حق عيني"},
            {"number": "1101", "label": "Article 1101", "content": "Le contrat est un accord de volontés entre deux ou plusieurs personnes destiné à créer, modifier, transmettre ou éteindre des obligations.", "keywords": "عقد, إرادة"},
            {"number": "1103", "label": "Article 1103", "content": "Les contrats légalement formés tiennent lieu de loi à ceux qui les ont faits.", "keywords": "العقد شريعة المتعاقدين, قوة ملزمة"},
            {"number": "1104", "label": "Article 1104", "content": "Les contrats doivent être négociés, formés et exécutés de bonne foi. Cette disposition est d'ordre public.", "keywords": "حسن نية"},
            {"number": "1240", "label": "Article 1240", "content": "Tout fait quelconque de l'homme, qui cause à autrui un dommage, oblige celui par la faute duquel il est arrivé à le réparer.", "keywords": "مسؤولية تقصيرية, تعويض, خطأ"},
            {"number": "1241", "label": "Article 1241", "content": "Chacun est responsable du dommage qu'il a causé non seulement par son fait, mais encore par sa négligence ou par son imprudence.", "keywords": "إهمال, طيش"},
            {"number": "1353", "label": "Article 1353", "content": "Celui qui réclame l'exécution d'une obligation doit la prouver. Réciproquement, celui qui se prétend libéré doit justifier le paiement ou le fait qui a produit l'extinction de son obligation.", "keywords": "عبء الإثبات"},
        ],
    },
    {
        "title": "Code de commerce (partie législative)",
        "category_id": 6, "type": "code", "jurisdiction_id": 3,
        "official_ref": "Code de commerce — partie législative, Légifrance",
        "enacted_date": "1807-09-15", "last_amended": "2022-01-01",
        "source_note": "Code de commerce français, livre Ier (art. L110-1 et s.). Texte officiel en vigueur (Légifrance).",
        "articles": [
            {"number": "L110-1", "label": "Article L110-1", "content": "La loi répute actes de commerce : 1° Tout achat de biens meubles pour les revendre, soit en nature, soit après les avoir travaillés et mis en oeuvre ; 2° Tout achat de biens immeubles aux fins de les revendre, à moins que l'acquéreur n'ait agi en vue d'édifier un ou plusieurs bâtiments et de les vendre en bloc ou par locaux ; 3° Toutes opérations d'intermédiaire pour l'achat, la souscription ou la vente d'immeubles, de fonds de commerce, d'actions ou parts de sociétés immobilières ; 4° Toute entreprise de location de meubles ; 5° Toute entreprise de manufactures, de commission, de transport par terre ou par eau ; 6° Toute entreprise de fournitures, d'agences, bureaux d'affaires, établissements de ventes à l'encan, de spectacles publics ; 7° Toute opération de change, banque, courtage et activité d'intermédiaire commercial ; 8° Les opérations de banque publiques ; 9° Toutes obligations entre négociants, marchands et banquiers ; 10° Entre toutes personnes, les lettres de change ou les effets de commerce.", "keywords": "أعمال تجارية"},
            {"number": "L110-3", "label": "Article L110-3", "content": "A l'égard des commerçants, les actes de commerce peuvent se prouver par tous moyens à moins qu'il n'en soit autrement disposé par la loi.", "keywords": "إثبات"},
            {"number": "L121-1", "label": "Article L121-1", "content": "Sont commerçants ceux qui exercent des actes de commerce et en font leur profession habituelle.", "keywords": "تاجر"},
        ],
    },
    {
        "title": "Code pénal",
        "category_id": 4, "type": "code", "jurisdiction_id": 3,
        "official_ref": "Code pénal — Légifrance",
        "enacted_date": "1994-03-01",
        "source_note": "Code pénal français (livre Ier et III). Texte officiel en vigueur (Légifrance).",
        "articles": [
            {"number": "121-1", "label": "Article 121-1", "content": "Nul n'est responsable pénalement que de son propre fait.", "keywords": "شخصية العقوبة"},
            {"number": "121-3", "label": "Article 121-3", "content": "Il n'y a point de crime ou de délit sans intention de le commettre. Toutefois, lorsque la loi le prévoit, il y a délit en cas de faute d'imprudence, de négligence ou de mise en danger délibérée de la personne d'autrui.", "keywords": "قصد جنائي"},
            {"number": "221-1", "label": "Article 221-1", "content": "Le fait de donner volontairement la mort à autrui constitue un meurtre. Il est puni de trente ans de réclusion criminelle.", "keywords": "قتل عمد"},
            {"number": "311-1", "label": "Article 311-1", "content": "Le vol est la soustraction frauduleuse de la chose d'autrui.", "keywords": "سرقة"},
        ],
    },
    {
        "title": "Constitution de 1958 (Ve République)",
        "category_id": 1, "type": "constitution", "jurisdiction_id": 3,
        "official_ref": "Constitution du 4 octobre 1958 — Journal officiel du 5 octobre 1958",
        "enacted_date": "1958-10-04", "last_amended": "2024-03-08",
        "source_note": "Constitution française du 4 octobre 1958, texte en vigueur (Conseil constitutionnel / Légifrance).",
        "articles": [
            {"number": "1", "label": "Article 1er", "content": "La France est une République indivisible, laïque, démocratique et sociale. Elle assure l'égalité devant la loi de tous les citoyens sans distinction d'origine, de race ou de religion. Elle respecte toutes les croyances. Son organisation est décentralisée. La loi favorise l'égal accès des femmes et des hommes aux mandats électoraux et fonctions électives, ainsi qu'aux responsabilités professionnelles et sociales.", "keywords": "جمهورية, علمانية"},
            {"number": "2", "label": "Article 2", "content": "La langue de la République est le français. L'emblème national est le drapeau tricolore, bleu, blanc, rouge. L'hymne national est « La Marseillaise ». La devise de la République est « Liberté, Égalité, Fraternité ». Son principe est : gouvernement du peuple, par le peuple et pour le peuple.", "keywords": "رموز الدولة"},
            {"number": "3", "label": "Article 3", "content": "La souveraineté nationale appartient au peuple qui l'exerce par ses représentants et par la voie du référendum. Aucune section du peuple ni aucun individu ne peut s'en attribuer l'exercice. Le suffrage peut être direct ou indirect dans les conditions prévues par la Constitution. Il est toujours universel, égal et secret. Sont électeurs, dans les conditions déterminées par la loi, tous les nationaux français majeurs des deux sexes, jouissant de leurs droits civils et politiques.", "keywords": "سيادة وطنية, انتخاب"},
            {"number": "34", "label": "Article 34", "content": "La loi est votée par le Parlement. La loi fixe les règles concernant : les droits civiques et les garanties fondamentales accordées aux citoyens pour l'exercice des libertés publiques ; la liberté, le pluralisme et l'indépendance des médias ; les sujétions imposées par la défense nationale aux citoyens en leur personne et en leurs biens ; la nationalité, l'état et la capacité des personnes, les régimes matrimoniaux, les successions et libéralités ; la détermination des crimes et délits ainsi que les peines qui leur sont applicables ; la procédure pénale ; l'amnistie ; la création de nouveaux ordres de juridiction et le statut des magistrats.", "keywords": "مجال القانون"},
        ],
    },
]

FRANCE_DECISIONS = [
    {
        "title": "Cass. ch. réunies, 13 février 1930, Jand'heur",
        "category_slug": "madani", "jurisdiction_id": 3,
        "court": "Cour de cassation, chambres réunies",
        "decision_number": "Arrêt Jand'heur (DP 1930.1.57)", "decision_date": "1930-02-13",
        "principles": "Le gardien de la chose est responsable du dommage causé par elle, sauf à démontrer un cas fortuit, une force majeure ou une cause étrangère. La présomption de responsabilité s'applique à toute personne ayant la garde de la chose.",
        "content": "Par l'arrêt Jand'heur du 13 février 1930, la Cour de cassation, réunie en chambres réunies, juge que l'article 1384 alinéa 1er du Code civil (désormais 1242) édicte une présomption de responsabilité à la charge du gardien de la chose qui a causé un dommage. La présomption ne peut être renversée que par la preuve d'un cas fortuit, d'une force majeure ou d'une cause étrangère ne lui étant pas imputable, et non par la preuve de l'absence de faute.",
        "source_note": "Arrêt majeur du droit français de la responsabilité civile du fait des choses.",
    },
    {
        "title": "Cass. civ. 1re, 20 mai 1936, Mercier",
        "category_slug": "madani", "jurisdiction_id": 3,
        "court": "Cour de cassation, première chambre civile",
        "decision_number": "Arrêt Mercier (DP 1936.1.88)", "decision_date": "1936-05-20",
        "principles": "Il existe entre le médecin et son patient un contrat à caractère civil comportant une obligation de soins de moyens, et non de résultat. La violation de cette obligation s'apprécie au regard de la faute.",
        "content": "L'arrêt Mercier du 20 mai 1936 consacre l'existence d'un véritable contrat médical conclu entre le médecin et son client, emportant l'obligation de donner des soins consciencieux, attentifs et, réserve faite de circonstances exceptionnelles, conformes aux données acquises de la science. Cette obligation est une obligation de moyens ; sa violation suppose la démonstration d'une faute.",
        "source_note": "Arrêt fondateur du droit de la responsabilité médicale.",
    },
    {
        "title": "Tribunal des conflits, 8 février 1873, Blanco",
        "category_slug": "idari", "jurisdiction_id": 3,
        "court": "Tribunal des conflits",
        "decision_number": "Arrêt Blanco (Rec. 1er supplément, p. 61)", "decision_date": "1873-02-08",
        "principles": "La responsabilité de l'État du fait des services publics n'est régie ni par les règles du Code civil ni par celles du droit privé, mais par des règles spéciales variables selon les besoins du service et la nécessité de concilier les droits de l'État avec les droits privés.",
        "content": "L'arrêt Blanco du 8 février 1873 pose le fondement de la responsabilité administrative : lorsque le dommage est causé par l'activité d'un service public, la compétence appartient à la juridiction administrative, et la responsabilité de l'État est soumise à des règles spéciales distinctes du droit privé.",
        "source_note": "Arrêt fondateur du droit administratif français.",
    },
]

# ------------------------------------------------ EGYPT (jurisdiction 2)
EGYPT = [
    {
        "title": "القانون المدني المصري (رقم 131 لسنة 1948)",
        "category_id": 2, "type": "code", "jurisdiction_id": 2,
        "official_ref": "قانون رقم 131 لسنة 1948 بإصدار القانون المدني",
        "enacted_date": "1948-07-16", "last_amended": "1949-10-15",
        "source_note": "صدر بتاريخ 16/7/1948 ونُشر في الوقائع المصرية، ويعمل به اعتبارًا من 15/10/1949.",
        "articles": [
            {"number": "1", "label": "المادة 1", "content": "1- تسري النصوص التشريعية على جميع المسائل التي تتناولها هذه النصوص في لفظها أو في فحواها. 2- فإذا لم يوجد نص تشريعي يمكن تطبيقه، حكم القاضي بمقتضى العرف، فإذا لم يوجد، فبمقتضى مبادئ الشريعة الإسلامية، فإذا لم توجد، فبمقتضى مبادئ القانون الطبيعي وقواعد العدالة.", "keywords": "تطبيق القانون, عرف, عدالة"},
            {"number": "2", "label": "المادة 2", "content": "لا يجوز إلغاء نص تشريعي إلا بتشريع لاحق ينص صراحةً على هذا الإلغاء، أو يشتمل على نص يتعارض مع نص التشريع القديم، أو ينظم من جديد الموضوع الذي سبق أن قرر قواعده ذلك التشريع.", "keywords": "إلغاء التشريع"},
            {"number": "4", "label": "المادة 4", "content": "لا يسمح بالتعسف في استعمال الحق.", "keywords": "تعسف استعمال الحق"},
            {"number": "5", "label": "المادة 5", "content": "يُعتبر استعمال الحق غير مشروع إذا لم يُقصد به سوى الإضرار بالغير.", "keywords": "تعسف"},
            {"number": "147", "label": "المادة 147", "content": "1- العقد شريعة المتعاقدين، فلا يجوز نقضه ولا تعديله إلا باتفاق الطرفين، أو للأسباب التي يقررها القانون. 2- ومع ذلك إذا طرأت حوادث استثنائية عامة لم يكن في الوسع توقعها وترتب على حدوثها أن تنفيذ الالتزام التعاقدي، وإن لم يصبح مستحيلاً، صار مرهقاً للمدين بحيث يهدده بخسارة فادحة، جاز للقاضي تبعاً للظروف وبعد الموازنة بين مصلحة الطرفين أن يردّ الالتزام المرهق إلى الحد المعقول، ويقع باطلاً كل اتفاق على خلاف ذلك.", "keywords": "العقد شريعة المتعاقدين, قوة العقد الملزمة"},
            {"number": "148", "label": "المادة 148", "content": "1- يجب تنفيذ العقد طبقاً لما اشتمل عليه وبطريقة تتفق مع ما يوجبه حسن النية. 2- ولا يقتصر العقد على إلزام المتعاقد بما ورد فيه، ولكن يتناول أيضاً ما هو من مستلزماته، وفقاً للقانون والعرف والعدالة بحسب طبيعة الالتزام.", "keywords": "حسن نية"},
            {"number": "163", "label": "المادة 163", "content": "كل خطأ سبب ضرراً للغير يلزم من ارتكبه بالتعويض.", "keywords": "مسؤولية تقصيرية, خطأ, تعويض"},
            {"number": "164", "label": "المادة 164", "content": "1- يكون الشخص مسئولاً عن أعماله غير المشروعة متى صدرت منه وهو مميز. 2- ومع ذلك إذا وقع الضرر من شخص غير مميز ولم يكن هناك من هو مسئول عنه، أو تعذر الحصول على تعويض من المسئول، جاز للقاضي أن يلزم من وقع منه الضرر بتعويض عادل مراعياً في ذلك مركز الخصوم.", "keywords": "غير المميز"},
            {"number": "165", "label": "المادة 165", "content": "إذا أثبت الشخص أن الضرر قد نشأ عن سبب أجنبي لا يد له فيه كحادث مفاجئ، أو قوة قاهرة، أو خطأ من المضرور، أو خطأ من الغير، كان غير ملزم بتعويض هذا الضرر ما لم يوجد نص أو اتفاق على غير ذلك.", "keywords": "قوة قاهرة, سبب أجنبي"},
        ],
    },
    {
        "title": "قانون العقوبات المصري (رقم 58 لسنة 1937)",
        "category_id": 4, "type": "code", "jurisdiction_id": 2,
        "official_ref": "قانون رقم 58 لسنة 1937 بإصدار قانون العقوبات",
        "enacted_date": "1937-07-31",
        "source_note": "صدر بسراي عابدين في 23 جمادى الأولى (31/7/1937)، ويعمل به من 15/10/1937، وفقًا لآخر التعديلات.",
        "articles": [
            {"number": "1", "label": "المادة 1", "content": "تسري أحكام هذا القانون على كل من يرتكب في القطر المصري جريمة من الجرائم المنصوص عليها فيه.", "keywords": "تطبيق القانون الجنائي"},
            {"number": "230", "label": "المادة 230", "content": "كل من قتل نفساً عمداً مع سبق الإصرار على ذلك أو الترصد يعاقب بالإعدام.", "keywords": "قتل عمد, إعدام"},
            {"number": "231", "label": "المادة 231", "content": "الإصرار السابق هو القصد المصمم عليه قبل الفعل لارتكاب جنحة أو جناية يكون غرض المصر منها إيذاء شخص معين أو أي شخص غير معين وجده أو صادفه سواء كان ذلك القصد معلقاً على حدوث أمر أو موقوفاً على شرط.", "keywords": "سبق إصرار"},
            {"number": "232", "label": "المادة 232", "content": "الترصد هو تربص الإنسان لشخص في جهة أو جهات كثيرة مدة من الزمن طويلة كانت أو قصيرة ليتوصل إلى قتل ذلك الشخص أو إلى إيذائه بالضرب ونحوه.", "keywords": "ترصد"},
            {"number": "233", "label": "المادة 233", "content": "من قتل أحداً عمداً بجواهر يتسبب عنها الموت عاجلاً أو آجلاً يعد قاتلاً بالسم أياً كانت كيفية استعمال تلك الجواهر ويعاقب بالإعدام.", "keywords": "قتل بالسم"},
            {"number": "234", "label": "المادة 234", "content": "من قتل نفساً عمداً من غير سبق إصرار ولا ترصد يعاقب بالسجن المؤبد أو المشدد. ومع ذلك يحكم على فاعل هذه الجناية بالإعدام إذا تقدمتها أو اقترنت بها أو تلتها جناية أخرى، وأما إذا كان القصد منها التأهب لفعل جنحة أو تسهيلها أو ارتكابها بالفعل أو مساعدة مرتكبيها أو شركائهم على الهرب أو التخلص من العقوبة فيحكم بالإعدام أو بالسجن المؤبد. وتكون العقوبة الإعدام إذا ارتكبت الجريمة تنفيذاً لغرض إرهابي.", "keywords": "قتل بلا سبق إصرار, سجن مؤبد"},
        ],
    },
    {
        "title": "دستور جمهورية مصر العربية 2014",
        "category_id": 1, "type": "constitution", "jurisdiction_id": 2,
        "official_ref": "دستور جمهورية مصر العربية — اعتمد في 18 يناير 2014",
        "enacted_date": "2014-01-18",
        "source_note": "أُجري الاستفتاء يومي 14 و15 يناير 2014 واعتُمد الدستور بأغلبية الأصوات الصحيحة.",
        "articles": [
            {"number": "1", "label": "المادة 1", "content": "جمهورية مصر العربية دولة ذات سيادة، موحدة لا تقبل التجزئة، ولا ينزل عن شيء منها، نظامها جمهوري ديمقراطي، يقوم على أساس المواطنة وسيادة القانون. الشعب المصري جزء من الأمة العربية يعمل على تكاملها ووحدتها، ومصر جزء من العالم الإسلامي، تنتمي إلى القارة الإفريقية، وتعتز بامتدادها الآسيوي، وتسهم في بناء الحضارة الإنسانية.", "keywords": "سيادة, دولة"},
            {"number": "2", "label": "المادة 2", "content": "الإسلام دين الدولة، واللغة العربية لغتها الرسمية، ومبادئ الشريعة الإسلامية المصدر الرئيسي للتشريع.", "keywords": "الشريعة الإسلامية"},
            {"number": "3", "label": "المادة 3", "content": "مبادئ شرائع المصريين من المسيحيين واليهود المصدر الرئيسي للتشريعات المنظمة لأحوالهم الشخصية، وشؤونهم الدينية، واختيار قياداتهم الروحية.", "keywords": "شرائع سماوية"},
            {"number": "4", "label": "المادة 4", "content": "السيادة للشعب وحده، يمارسها ويحميها، وهو مصدر السلطات، ويصون وحدته الوطنية التي تقوم على مبادئ المساواة والعدل وتكافؤ الفرص بين جميع المواطنين، وذلك على الوجه المبين في الدستور.", "keywords": "سيادة الشعب"},
            {"number": "7", "label": "المادة 7", "content": "الأزهر الشريف هيئة إسلامية علمية مستقلة، يختص دون غيره بالقيام على كافة شؤونه، وهو المرجع الأساسي في العلوم الدينية والشؤون الإسلامية، ويتولى مسئولية الدعوة ونشر علوم الدين واللغة العربية في مصر والعالم. وتلتزم الدولة بتوفير الاعتمادات المالية الكافية لتحقيق أغراضه. وشيخ الأزهر مستقل غير قابل للعزل، وينظم القانون طريقة اختياره من بين أعضاء هيئة كبار العلماء.", "keywords": "الأزهر"},
            {"number": "65", "label": "المادة 65", "content": "حرية الفكر والرأي مكفولة. ولكل إنسان حق التعبير عن رأيه بالقول، أو الكتابة، أو التصوير، أو غير ذلك من وسائل التعبير والنشر.", "keywords": "حرية الرأي"},
            {"number": "93", "label": "المادة 93", "content": "تلتزم الدولة بالاتفاقيات والعهود والمواثيق الدولية لحقوق الإنسان التي تصدق عليها مصر، وتصبح لها قوة القانون بعد نشرها وفقاً للأوضاع المقررة.", "keywords": "الاتفاقيات الدولية"},
        ],
    },
    {
        "title": "قانون التجارة المصري (رقم 17 لسنة 1999)",
        "category_id": 6, "type": "code", "jurisdiction_id": 2,
        "official_ref": "قانون رقم 17 لسنة 1999 بإصدار قانون التجارة",
        "enacted_date": "1999-05-17",
        "source_note": "صدر بتاريخ 17/5/1999 — الباب الأول من الكتاب الأول يتناول الأعمال التجارية.",
        "articles": [
            {"number": "1", "label": "المادة 1", "content": "يُعد عملاً تجارياً كل عمل يُزاوله التاجر في تجارته، وكل عمل يتعلق بحركة تداول السلع أو الخدمات أو الأوراق المالية أو العمليات المصرفية أو أعمال الوساطة فيها، وفقاً للقواعد الواردة في هذا القانون.", "keywords": "عمل تجاري"},
            {"number": "2", "label": "المادة 2", "content": "تسري أحكام قانون التجارة على الأعمال التجارية التي تقع في مصر، ولو كانت متعلقة بأشخاص أجانب، ما لم يرد نص يقضي بغير ذلك.", "keywords": "تطبيق القانون التجاري"},
        ],
    },
]

EGYPT_DECISIONS = [
    {
        "title": "نقض مدني — العقد شريعة المتعاقدين",
        "category_slug": "madani", "jurisdiction_id": 2,
        "court": "محكمة النقض المصرية",
        "decision_number": "مبدأ مستقر في قضاء النقض", "decision_date": "1955-04-27",
        "principles": "العقد شريعة المتعاقدين؛ فإذا وقع العقد ملزماً به الطرفان فلا يجوز نقضه ولا تعديله إلا باتفاقهما أو للأسباب التي يقررها القانون.",
        "content": "استقر قضاء محكمة النقض المصرية على أن العقد شريعة المتعاقدين، وعلى القاضي تنفيذ ما ورد فيه وفقاً للمادة 147 من القانون المدني، دون أن يملك الخروج على نصه الواضح أو تفسير عباراته التي لا تحتمل إلا معنى واحداً. فالعبارة الواضحة لا مجال للاجتهاد في تفسيرها.",
        "source_note": "مبدأ مستقر — الدائرة المدنية بمحكمة النقض.",
    },
    {
        "title": "نقض مدني — التعسف في استعمال الحق",
        "category_slug": "madani", "jurisdiction_id": 2,
        "court": "محكمة النقض المصرية",
        "decision_number": "مبدأ مستقر في قضاء النقض", "decision_date": "1960-01-12",
        "principles": "لا يسمح بالتعسف في استعمال الحق؛ ويُعد استعمالاً تعسفياً ما كان قصد صاحبه الإضرار بالغير أو تجاوز حدود الاستعمال المعتادة.",
        "content": "استقر قضاء النقض على أن استعمال الحق يعد تعسفاً يستوجب التعويض إذا لم يقصد به سوى الإضرار بالغير، أو كان الغرض منه ابتزاز فائدة لا تتناسب مع الضرر الحاصل، أو تجاوز فيه صاحبه حدود الاستعمال المعتاد وفق المادتين 4 و5 من القانون المدني المصري.",
        "source_note": "تطبيق للمادتين 4 و5 مدني.",
    },
    {
        "title": "نقض جنائي — القصد الجنائي في جريمة القتل العمد",
        "category_slug": "jinai", "jurisdiction_id": 2,
        "court": "محكمة النقض المصرية",
        "decision_number": "مبدأ مستقر في قضاء النقض", "decision_date": "1965-03-15",
        "principles": "يشترط لقيام جريمة القتل العمد قصد إزهاق روح المجني عليه، ويُستخلص من استعمال أداة مميتة واختيار مواضع قاتلة من الجسم.",
        "content": "استقر قضاء محكمة النقض على أن القصد الجنائي في جريمة القتل العمد هو قصد إزهاق الروح، ويُستفاد من طبيعة الأداة المستعملة ومواضع الإصابة في الجسم وحالة المجني عليه، عملاً بالمادتين 230 و234 من قانون العقوبات.",
        "source_note": "الدائرة الجنائية بمحكمة النقض.",
    },
]


def main():
    print("=== حذف البيانات التجريبية القديمة (فرنسا/مصر فقط) ===")
    delete_text(1829)
    delete_text(1830)
    delete_text(1831)
    delete_decision(16458)
    delete_decision(16459)
    delete_decision(16460)

    print("\n=== فرنسا: نصوص ===")
    for t in FRANCE:
        tid = create_text(t)
        if tid:
            print(f"  + text id={tid} — {t['title']}")
            add_articles(tid, t["articles"])

    print("\n=== فرنسا: اجتهادات ===")
    for d in FRANCE_DECISIONS:
        create_decision(d)

    print("\n=== مصر: نصوص ===")
    for t in EGYPT:
        tid = create_text(t)
        if tid:
            print(f"  + text id={tid} — {t['title']}")
            add_articles(tid, t["articles"])

    print("\n=== مصر: اجتهادات ===")
    for d in EGYPT_DECISIONS:
        create_decision(d)

    print("\nتم الانتهاء.")


if __name__ == "__main__":
    main()
