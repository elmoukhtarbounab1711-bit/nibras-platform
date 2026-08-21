"""
compare_nibras_vs_ansvar.py
============================
Compares Nibras articles against Ansvar provisions using TITLE-based matching.
Shows exact before/after content for sample articles.
"""
import sqlite3
import os
import hashlib
import sys
import io

# Fix Windows encoding for Arabic output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

NIBRAS_DB = os.path.join(os.path.dirname(__file__), '..', 'nibras.db')
ANSVAR_DB = r"C:\Users\Bounab\AppData\Local\Temp\opencode\ansvar\node_modules\@ansvar\moroccan-law-mcp\data\database.db"

def sha256(text):
    if not text:
        return None
    return hashlib.sha256(text.strip().encode('utf-8')).hexdigest()

def main():
    nibras_conn = sqlite3.connect(NIBRAS_DB)
    nibras_conn.row_factory = sqlite3.Row
    ansvar_conn = sqlite3.connect(ANSVAR_DB)
    ansvar_conn.row_factory = sqlite3.Row

    # Step 1: Build Ansvar title -> document_id mapping
    ansvar_docs = {}
    for row in ansvar_conn.execute("SELECT id, title, title_en, url FROM legal_documents"):
        ansvar_docs[row['title']] = {
            'id': row['id'],
            'title_en': row['title_en'],
            'url': row['url']
        }

    print(f"=== Ansvar DB: {len(ansvar_docs)} documents ===\n")

    # Step 2: Build Ansvar document_id -> provisions mapping
    ansvar_provisions = {}
    for row in ansvar_conn.execute("SELECT document_id, provision_ref, content, title FROM legal_provisions ORDER BY id"):
        doc_id = row['document_id']
        if doc_id not in ansvar_provisions:
            ansvar_provisions[doc_id] = []
        ansvar_provisions[doc_id].append({
            'ref': row['provision_ref'],
            'content': row['content'],
            'title': row['title']
        })

    total_provisions = sum(len(v) for v in ansvar_provisions.values())
    print(f"=== Ansvar DB: {total_provisions} provisions across {len(ansvar_provisions)} documents ===\n")

    # Step 3: Match Nibras texts against Ansvar by title
    nibras_texts = nibras_conn.execute(
        "SELECT id, title, source_url, source_name, content_hash FROM legal_texts ORDER BY id"
    ).fetchall()

    matched = 0
    unmatched = 0
    unmatched_titles = []
    
    # Article comparison stats
    total_articles = 0
    exact_match = 0
    hash_match = 0
    content_differs = 0
    missing_in_nibras = 0
    missing_in_ansvar = 0
    sample_diffs = []

    for nt in nibras_texts:
        title = nt['title']
        if title in ansvar_docs:
            matched += 1
            ansvar_info = ansvar_docs[title]
            doc_id = ansvar_info['id']
            
            # Get Ansvar provisions for this document
            a_provisions = ansvar_provisions.get(doc_id, [])
            
            # Get Nibras articles for this text
            n_articles = nibras_conn.execute(
                "SELECT id, number, label, content, content_hash, official_text_raw FROM articles WHERE legal_text_id = ? ORDER BY number",
                (nt['id'],)
            ).fetchall()
            
            total_articles += len(n_articles)
            
            # Compare article by article
            a_prov_dict = {}
            for ap in a_provisions:
                # Extract number from provision_ref like "art1", "art_1", "2" etc.
                import re
                m = re.search(r'(\d+)', ap['ref'])
                if m:
                    a_prov_dict[int(m.group(1))] = ap
            
            for na in n_articles:
                num = int(na['number']) if na['number'] else 0
                if num in a_prov_dict:
                    a_prov = a_prov_dict[num]
                    a_content = (a_prov['content'] or '').strip()
                    n_content = (na['content'] or '').strip()
                    n_raw = (na['official_text_raw'] or '').strip()
                    
                    # Compare content with Ansvar provision
                    if a_content == n_content:
                        exact_match += 1
                    elif sha256(a_content) == sha256(n_content):
                        hash_match += 1
                    else:
                        content_differs += 1
                        if len(sample_diffs) < 10:
                            sample_diffs.append({
                                'text_title': title[:80],
                                'text_id': nt['id'],
                                'article_num': num,
                                'ansvar_ref': a_prov['ref'],
                                'ansvar_content': a_content[:300],
                                'nibras_content': n_content[:300],
                                'nibras_raw': n_raw[:300] if n_raw else None,
                                'ansvar_len': len(a_content),
                                'nibras_len': len(n_content),
                            })
                else:
                    missing_in_ansvar += 1
        else:
            unmatched += 1
            if len(unmatched_titles) < 20:
                unmatched_titles.append(title[:100])

    # Step 4: Check for articles in Ansvar but not in Nibras
    nibras_article_count = nibras_conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    ansvar_provision_count = ansvar_conn.execute("SELECT COUNT(*) FROM legal_provisions").fetchone()[0]

    print("=" * 80)
    print("COMPARISON RESULTS: Nibras vs Ansvar (legislation.gov.ma)")
    print("=" * 80)
    print(f"\nTexts matched by title:      {matched}/{len(nibras_texts)} ({100*matched/len(nibras_texts):.1f}%)")
    print(f"Texts unmatched:             {unmatched}")
    print(f"\nTotal Nibras articles:       {nibras_article_count}")
    print(f"Total Ansvar provisions:     {ansvar_provision_count}")
    print(f"\nArticles compared:           {total_articles}")
    print(f"  EXACT MATCH:               {exact_match} ({100*exact_match/total_articles:.1f}%)" if total_articles else "")
    print(f"  Hash match (whitespace):   {hash_match}" if total_articles else "")
    print(f"  CONTENT DIFFERS:           {content_differs} ({100*content_differs/total_articles:.1f}%)" if total_articles else "")
    print(f"  Missing in Ansvar:         {missing_in_ansvar}" if total_articles else "")

    if unmatched_titles:
        print(f"\n--- Sample unmatched Nibras titles ---")
        for t in unmatched_titles[:10]:
            print(f"  - {t}")

    if sample_diffs:
        print(f"\n{'=' * 80}")
        print(f"SAMPLE DIFFERENCES (up to 10):")
        print(f"{'=' * 80}")
        for i, d in enumerate(sample_diffs, 1):
            print(f"\n--- Diff #{i} ---")
            print(f"Text: {d['text_title']} (id={d['text_id']})")
            print(f"Article: {d['article_num']} (Ansvar ref: {d['ansvar_ref']})")
            print(f"Ansvar length: {d['ansvar_len']} chars | Nibras length: {d['nibras_len']} chars")
            print(f"ANSVAR content:\n  {d['ansvar_content']}")
            print(f"NIBRAS content:\n  {d['nibras_content']}")
            if d['nibras_raw']:
                print(f"NIBRAS official_text_raw:\n  {d['nibras_raw']}")
    elif total_articles > 0 and content_differs == 0:
        print(f"\n*** ALL COMPARED ARTICLES ARE EXACT MATCHES ***")

    nibras_conn.close()
    ansvar_conn.close()

if __name__ == '__main__':
    main()
