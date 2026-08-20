import sqlite3, sys, hashlib, json, time, re
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

ANSVAR_DB = r'C:\Users\Bounab\AppData\Local\Temp\opencode\ansvar\node_modules\@ansvar\moroccan-law-mcp\data\database.db'
NIBRAS_DB = 'nibras.db'

CATEGORY_MAP = {
    1: ['دستور', 'الدستور', 'fundamenta'],
    2: ['القانون المدني', 'civil', 'التزامات', 'عقود', 'الالتزامات'],
    3: ['الأسرة', 'مدونة الأسرة', 'family'],
    4: ['الجنائي', 'الجريمة', 'العقوبات', 'penal', 'pénal', 'الجمع بين', 'النوع الإجرامي'],
    5: ['الشغل', 'labour', 'travail', 'مدونة الشغل'],
    6: ['التجاري', 'commerce', 'مدونة التجارة', 'شركات المساهمة', 'مدونة التأمينات', 'ال保險'],
    7: ['المسطرة', 'procedure', 'procédure', 'المسطرة المدنية', 'المسطرة الجنائية'],
    1848: ['الثقافة', 'الإعلام', 'الاتصال', 'culture'],
    1849: ['الإلكتروني', 'electronic', 'رقمي', 'التجارة الإلكترونية'],
    1850: ['الفلاحة', 'agriculture', 'الزراعي', 'الفلاحي'],
    1853: ['الشؤون الدينية', 'الأوقاف', 'religie', 'المساجد', 'ال鼪فق'],
    1854: ['الطاقة', 'energy', 'الماء', 'كهرباء', 'الوقود'],
    1855: ['البيئة', 'environment', 'التلوث'],
    1858: ['الاجتماعي', 'الضمان الاجتماعي'],
    1859: ['التربية', 'التعليم', 'education', 'مدرس', 'جامعة', 'تعليم', 'جامعات', 'التعليم العالي'],
    1860: ['مرسوم', 'décret', 'decree'],
    1864: ['النقل', 'transport', 'الطرق', 'الجوي', 'البحري', 'السكك الحديدية'],
    1868: ['المالي', 'الجبائي', 'fiscal', 'ضريب', 'ميزانية', 'Générale'],
    1869: ['الصحة', 'الحماية الاجتماعية', 'santé', 'صحة', 'تأمين', 'الأدوية', 'ال_badal'],
    1870: ['الحقوق', 'الحريات', 'حقوق الإنسان', 'liberté', 'مناهضة التعذيب', 'الإنصاف'],
    1872: ['العقاري', 'foncier', 'عقار'],
    1874: ['الاقتصادي', 'économique', 'منافسة', 'concurrence', 'النقد', 'الDefi'],
    1877: ['القضاء', 'المحاكم', 'justice', 'procureur', 'المحكمة الدستورية'],
    1878: ['الإداري', 'administratif', 'تقاضي', 'وظيفة عمومية', 'الطعن الإداري', 'التدبير الإداري'],
    1880: ['المهن', 'professions', 'libérale', 'الهندسة', 'الطب', 'ال小编'],
    1881: ['الانتخاب', 'élection', 'electoral', 'الاقتراع', 'الهما'],
    1882: ['المؤسسات الدستورية', 'institution', 'الSelector'],
}


def classify_document(title, title_en):
    combined = (title or '') + ' ' + (title_en or '')
    combined_lower = combined.lower()
    for cat_id, keywords in CATEGORY_MAP.items():
        if not keywords:
            continue
        for kw in keywords:
            if kw.lower() in combined_lower:
                return cat_id
    return 1852


def content_hash(text):
    if not text:
        return None
    return hashlib.sha256(text.strip().encode('utf-8')).hexdigest()


def main():
    print("=== Fresh import from Ansvar MCP ===")
    start = time.time()
    
    ansvar = sqlite3.connect(ANSVAR_DB)
    nibras = sqlite3.connect(NIBRAS_DB)
    nibras.row_factory = sqlite3.Row
    
    # Disable all FTS triggers before dropping tables
    print("[0] Disabling FTS triggers and dropping FTS tables...")
    # Get all triggers
    triggers = [r[0] for r in nibras.execute(
        "SELECT name FROM sqlite_master WHERE type='trigger'"
    ).fetchall()]
    for t in triggers:
        try:
            nibras.execute(f"DROP TRIGGER IF EXISTS [{t}]")
        except:
            pass
    
    fts_tables = ['articles_fts', 'jurisprudence_fts', 'research_books_fts', 
                  'comp_law_articles_fts', 'comp_jurisprudence_fts']
    for t in fts_tables:
        try:
            nibras.execute(f"DROP TABLE IF EXISTS [{t}]")
            print(f"  Dropped {t}")
        except Exception as e:
            print(f"  Drop {t}: {e}")
    
    # Step 1: Delete
    print("\n[1] Deleting existing articles and legal_texts...")
    nibras.execute("DELETE FROM articles")
    nibras.execute("DELETE FROM legal_texts")
    nibras.commit()
    print("  Done.")
    
    # Step 2: Fetch
    print("\n[2] Fetching from Ansvar...")
    documents = ansvar.execute("""
        SELECT id, type, title, title_en, short_name, status, 
               issued_date, url, description 
        FROM legal_documents ORDER BY id
    """).fetchall()
    print(f"  Documents: {len(documents)}")
    
    provisions_map = {}
    for p in ansvar.execute("""
        SELECT document_id, provision_ref, chapter, section, title, content
        FROM legal_provisions ORDER BY id
    """).fetchall():
        doc_id = p[0]
        if doc_id not in provisions_map:
            provisions_map[doc_id] = []
        provisions_map[doc_id].append({
            'ref': p[1], 'chapter': p[2], 'section': p[3],
            'title': p[4], 'content': p[5],
        })
    total_provs = sum(len(v) for v in provisions_map.values())
    print(f"  Provisions: {total_provs}")
    
    # Step 3: Import
    print("\n[3] Importing...")
    text_count = 0
    article_count = 0
    cat_counts = {}
    
    for doc in documents:
        doc_id, doc_type, title, title_en, short_name, status, issued_date, url, description = doc
        if not title:
            continue
        
        cat_id = classify_document(title, title_en)
        cat_counts[cat_id] = cat_counts.get(cat_id, 0) + 1
        
        nibras_type = 'law'
        t_lower = (doc_type or '').lower()
        title_lower = (title or '').lower()
        if 'decree' in t_lower or 'décret' in t_lower or 'مرسوم' in title_lower:
            nibras_type = 'decree'
        elif 'code' in t_lower or 'مدونة' in title_lower:
            nibras_type = 'code'
        elif 'organic' in t_lower or 'تنظيمي' in title_lower:
            nibras_type = 'organic_law'
        elif 'constitution' in t_lower or 'دستور' in title_lower:
            nibras_type = 'constitution'
        
        provs = provisions_map.get(doc_id, [])
        text_content = description or title
        h = content_hash(text_content)
        source_url = url or f'https://legislation.gov.ma/d/{doc_id}'
        
        nibras.execute("""
            INSERT INTO legal_texts 
            (category_id, type, title, is_sample_data, tenant_id, 
             source_url, source_name, official_source, content_hash, 
             version_type, verification_status, published_date, language)
            VALUES (?, ?, ?, 0, 1, ?, ?, 1, ?, 'ORIGINAL_OFFICIAL', 'UNVERIFIED', ?, 'ar')
        """, (cat_id, nibras_type, title, source_url,
              'le legislation.gov.ma — الجريدة الرسمية',
              h, issued_date))
        text_id = nibras.execute("SELECT last_insert_rowid()").fetchone()[0]
        text_count += 1
        
        for i, prov in enumerate(provs, 1):
            content = prov['content'] or ''
            if not content.strip():
                continue
            label = prov['title'] or f"المادة {i}"
            ref = prov['ref'] or ''
            num_match = re.search(r'(\d+)', ref)
            number = num_match.group(1) if num_match else str(i)
            art_h = content_hash(content)
            
            nibras.execute("""
                INSERT INTO articles 
                (legal_text_id, number, label, content, tenant_id, 
                 content_hash, official_text_raw)
                VALUES (?, ?, ?, ?, 1, ?, ?)
            """, (text_id, number, label, content, art_h, content))
            article_count += 1
        
        if text_count % 500 == 0:
            nibras.commit()
            print(f"  ... {text_count} texts / {article_count} articles ({time.time()-start:.1f}s)")
    
    nibras.commit()
    
    print(f"\n=== DONE ===")
    print(f"  Texts: {text_count}")
    print(f"  Articles: {article_count}")
    print(f"  Time: {time.time()-start:.1f}s")
    
    cat_names = {r[0]: r[1] for r in nibras.execute("SELECT id, name FROM categories").fetchall()}
    print(f"\n  Category distribution:")
    for cid, cnt in sorted(cat_counts.items(), key=lambda x: -x[1]):
        print(f"    {cat_names.get(cid, f'?{cid}')}: {cnt}")
    
    total_texts = nibras.execute("SELECT COUNT(*) FROM legal_texts").fetchone()[0]
    total_arts = nibras.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    juris = nibras.execute("SELECT COUNT(*) FROM jurisprudence").fetchone()[0]
    print(f"\n  Final: {total_texts} texts, {total_arts} articles, {juris} jurisprudence")
    
    ansvar.close()
    nibras.close()


if __name__ == '__main__':
    main()
