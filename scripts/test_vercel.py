"""Quick smoke test for Vercel entry point."""
import os, sys
os.environ["NIBRAS_DB_PATH"] = "C:/Users/Bounab/Documents/Default Project/nibras-backend/nibras.db"
sys.path.insert(0, "C:/Users/Bounab/Documents/Default Project/nibras-backend")

from app import create_app
app = create_app()

with app.test_client() as c:
    r = c.get("/api/ready")
    status = r.get_json()["status"]
    print(f"API ready: {r.status_code} {status}")

    r = c.get("/api/texts?limit=1")
    count = r.get_json()["count"]
    print(f"Texts: {r.status_code} count={count}")

    r = c.get("/api/texts/1158/pdf")
    print(f"PDF: {r.status_code} len={len(r.data)} type={r.content_type}")

    r = c.get("/")
    print(f"Frontend: {r.status_code} len={len(r.data)}")

    r = c.get("/vendor/pdfjs/pdf.min.js")
    print(f"pdf.js: {r.status_code} len={len(r.data)}")

    r = c.get("/api/documents/templates")
    print(f"Templates: {r.status_code} count={len(r.get_json())}")
