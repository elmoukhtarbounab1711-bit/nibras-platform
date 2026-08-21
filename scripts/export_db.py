import gzip, os, shutil, sqlite3

print("Backing up database...")
src = sqlite3.connect("nibras.db")
dst = sqlite3.connect("nibras_prod.db")
src.backup(dst)
src.close()
dst.execute("VACUUM")
dst.execute("PRAGMA journal_mode=WAL")
dst.close()

print("Compressing...")
with open("nibras_prod.db", "rb") as f_in:
    with gzip.open("nibras_prod.db.gz", "wb", compresslevel=9) as f_out:
        shutil.copyfileobj(f_in, f_out)

size = os.path.getsize("nibras_prod.db.gz") / 1024 / 1024
print(f"Done: nibras_prod.db.gz = {size:.1f} MB")
