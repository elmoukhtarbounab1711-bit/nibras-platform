import requests, sys, os

FILE = "nibras_prod.db.gz"
SIZE_MB = os.path.getsize(FILE) / 1024 / 1024
print(f"Uploading {FILE} ({SIZE_MB:.1f} MB) to tmpfiles.org...")

with open(FILE, "rb") as f:
    resp = requests.post(
        "https://tmpfiles.org/api/v1/upload",
        files={"file": (FILE, f)},
        timeout=600,
    )

print(f"Status: {resp.status_code}")
data = resp.json()
print(f"Response: {data}")

if data.get("status") == "success" or data.get("data", {}).get("url"):
    url = data["data"]["url"]
    # tmpfiles.org returns viewing URL, download URL has /dl/ prefix
    dl_url = url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
    print(f"\nDownload URL: {dl_url}")
    print(f"Add this to Railway: NIBRAS_DB_URL={dl_url}")
else:
    print("Upload failed, trying transfer.sh...")
    with open(FILE, "rb") as f:
        resp2 = requests.put(
            f"https://transfer.sh/nibras_prod.db.gz",
            data=f,
            timeout=600,
        )
    if resp2.status_code == 200:
        dl_url = resp2.text.strip()
        print(f"\nDownload URL: {dl_url}")
        print(f"Add this to Railway: NIBRAS_DB_URL={dl_url}")
    else:
        print(f"transfer.sh also failed: {resp2.status_code} {resp2.text}")
        sys.exit(1)
