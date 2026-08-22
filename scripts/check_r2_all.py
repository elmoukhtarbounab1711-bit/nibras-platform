import urllib.request
import sqlite3

conn = sqlite3.connect('nibras.db')
rows = conn.execute('SELECT id, source_url FROM legal_texts WHERE source_url LIKE "%r2.dev%"').fetchall()
ok = 0
fail_ids = []
for text_id, url in rows:
    try:
        req = urllib.request.Request(url, method='HEAD', headers={"User-Agent": "nibras/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            ok += 1
    except Exception as e:
        fail_ids.append((text_id, url, str(e)))
conn.close()
print(f"Total: {len(rows)}, OK: {ok}, FAIL: {len(fail_ids)}")
if fail_ids:
    print("\nFailed URLs:")
    for tid, url, err in fail_ids[:10]:
        print(f"  ID {tid}: {url} -> {err}")
