"""Download DejaVuSans TTF fonts for PDF generation on Lambda."""
import os
import urllib.request

FONT_DIR = os.path.join(os.path.dirname(__file__), "..", "fonts")
os.makedirs(FONT_DIR, exist_ok=True)

FONTS = [
    ("DejaVuSans.ttf", "https://github.com/dejavu-fonts/dejavu-fonts/raw/refs/heads/master/ttf/DejaVuSans.ttf"),
    ("DejaVuSans-Bold.ttf", "https://github.com/dejavu-fonts/dejavu-fonts/raw/refs/heads/master/ttf/DejaVuSans-Bold.ttf"),
]

for name, url in FONTS:
    dest = os.path.join(FONT_DIR, name)
    if os.path.exists(dest):
        print(f"Exists: {name}")
        continue
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
        with open(dest, "wb") as f:
            f.write(data)
        print(f"OK: {name} ({len(data)} bytes)")
    except Exception as e:
        print(f"FAIL: {name} - {e}")

# Verify
from reportlab.pdfbase.ttfonts import TTFont
regular = os.path.join(FONT_DIR, "DejaVuSans.ttf")
if os.path.exists(regular):
    TTFont("TestDejaVu", regular)
    print("Font verification: OK")
else:
    print("Font verification: SKIPPED (no file)")
