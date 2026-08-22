import urllib.request
import sqlite3

conn = sqlite3.connect('nibras.db')
rows = conn.execute('SELECT id, source_url FROM legal_texts WHERE source_url LIKE "%r2.dev%" ORDER BY id LIMIT 20').fetchall()
ok = 0
fail = 0
for text_id, url in rows:
    try:
        req = urllib.request.Request(url, method='HEAD', headers={"User-Agent": "nibras/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.getcode()
            print(f"  ID {text_id}: {status} OK ({resp.headers.get('Content-Length', '?')} bytes)")
            ok += 1
    except Exception as e:
        print(f"  ID {text_id}: FAIL {e}")
        fail += 1
conn.close()
print(f"\nResults: {ok} OK, {fail} FAIL out of {len(rows)}")
