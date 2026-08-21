import sqlite3

conn = sqlite3.connect('nibras.db')
tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print(f'Tables: {len(tables)}')
for t in sorted(tables):
    try:
        count = conn.execute(f'SELECT COUNT(*) FROM [{t}]').fetchone()[0]
        if count > 0:
            print(f'  {t}: {count} rows')
    except Exception as e:
        print(f'  {t}: ERROR {e}')
conn.close()
