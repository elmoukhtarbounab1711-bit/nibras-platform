"""
import_huquqai.py - Import all laws from huquqai.ma API with PDF URLs
"""
import sqlite3, requests, time, os, sys, io, hashlib

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

DB = os.path.join(os.path.dirname(__file__), '..', 'nibras.db')
API = "https://huquqai.ma/api/laws"

def classify(dt, title):
    dt = (dt or '').lower()
    t = (title or '').lower()
    if 'قانون تنظيمي' in dt or 'قانون تنظيمي' in t: return 'organic_law'
    if 'دستور' in dt or 'دستور' in t: return 'constitution'
    if 'ظهير' in dt or 'ظهير' in t:
        if 'مدونة' in t or 'قانون' in t: return 'code'
        return 'decree'
    if 'مرسوم' in dt or 'مرسوم' in t: return 'decree'
    if 'قرار' in dt or 'قرار' in t: return 'decision'
    if 'مقرر' in dt: return 'decision'
    if 'اتفاقية' in dt or 'معاهدة' in dt or 'بروتوكول' in dt: return 'treaty'
    if 'مدونة' in t: return 'code'
    if 'قانون' in dt or 'قانون' in t: return 'law'
    return 'law'

def main():
    conn = sqlite3.connect(DB)
    existing = {r[0] for r in conn.execute("SELECT title FROM legal_texts")}
    
    page = 1
    total = None
    inserted = 0
    skipped = 0
    
    while True:
        try:
            r = requests.get(f"{API}?page={page}&limit=100", timeout=30)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"Error page {page}: {e}")
            time.sleep(2)
            continue
        
        laws = data.get('data', [])
        if total is None:
            total = data.get('totalCount', 0)
            print(f"Total: {total} laws")
        
        if not laws:
            break
        
        for law in laws:
            title = (law.get('title') or '').strip()
            if not title or title in existing:
                skipped += 1
                continue
            
            pdf_url = law.get('pdf_url', '')
            doc_type = law.get('document_type', '')
            law_type = classify(doc_type, title)
            doc_num = law.get('law_number') or law.get('document_number', '')
            published = law.get('published_date', '')
            chash = hashlib.sha256(title.encode('utf-8')).hexdigest()
            
            try:
                conn.execute("""
                    INSERT INTO legal_texts (title, type, category_id, source_url, source_name,
                        content_hash, official_ref, published_date, language, source_document_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (title, law_type, 1852, pdf_url,
                    'huquqai.ma — محرك البحث القانوني الذكي',
                    chash, doc_num, published, 'ar', pdf_url))
                inserted += 1
                existing.add(title)
            except Exception as e:
                skipped += 1
            
            if inserted % 500 == 0 and inserted > 0:
                conn.commit()
                print(f"  {inserted} inserted, {skipped} skipped")
        
        print(f"Page {page}: {len(laws)} laws (total: {inserted})")
        if len(existing) >= total:
            break
        page += 1
        time.sleep(0.3)
    
    conn.commit()
    final = conn.execute("SELECT COUNT(*) FROM legal_texts").fetchone()[0]
    print(f"\nDone: {inserted} inserted, {skipped} skipped, {final} total")
    conn.close()

if __name__ == '__main__':
    main()
