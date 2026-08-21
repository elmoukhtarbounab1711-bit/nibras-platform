import sqlite3
for db_file in ['nibras_prod.db', 'nibras.db']:
    conn = sqlite3.connect(db_file)
    total = conn.execute('SELECT COUNT(*) FROM legal_texts').fetchone()[0]
    with_url = conn.execute('SELECT COUNT(*) FROM legal_texts WHERE source_url IS NOT NULL AND source_url != ""').fetchone()[0]
    r2 = conn.execute("SELECT COUNT(*) FROM legal_texts WHERE source_url LIKE '%r2.dev%'").fetchone()[0]
    adala = conn.execute("SELECT COUNT(*) FROM legal_texts WHERE source_url LIKE '%adala%'").fetchone()[0]
    sample = conn.execute('SELECT id, source_url FROM legal_texts LIMIT 3').fetchall()
    print(f'=== {db_file} ===')
    print(f'  Total: {total}, with source_url: {with_url}, r2: {r2}, adala: {adala}')
    for row in sample:
        print(f'  ID {row[0]}: {row[1]}')
    conn.close()
