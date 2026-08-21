"""Delete all legal texts from Nibras"""
import sqlite3, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB = os.path.join(os.path.dirname(__file__), '..', 'nibras.db')
conn = sqlite3.connect(DB)

t = conn.execute("SELECT COUNT(*) FROM legal_texts").fetchone()[0]
a = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
j = conn.execute("SELECT COUNT(*) FROM jurisprudence").fetchone()[0]

print(f"Before: {t} texts, {a} articles, {j} jurisprudence")

conn.execute("DELETE FROM articles")
conn.execute("DELETE FROM legal_texts")
conn.commit()

print(f"After: {conn.execute('SELECT COUNT(*) FROM legal_texts').fetchone()[0]} texts, {conn.execute('SELECT COUNT(*) FROM articles').fetchone()[0]} articles, {conn.execute('SELECT COUNT(*) FROM jurisprudence').fetchone()[0]} jurisprudence")
conn.close()
