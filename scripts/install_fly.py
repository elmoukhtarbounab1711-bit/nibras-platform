import urllib.request, zipfile, os, tempfile

url = "https://github.com/superfly/flyctl/releases/download/v0.4.85/flyctl_0.4.85_Windows_x86_64.zip"
dest = os.path.join(os.environ["LOCALAPPDATA"], "fly")
os.makedirs(dest, exist_ok=True)

tmp = os.path.join(tempfile.gettempdir(), "fly.zip")
print(f"Downloading flyctl from {url}...")
urllib.request.urlretrieve(url, tmp)
print(f"Downloaded: {os.path.getsize(tmp)} bytes")

print("Extracting...")
with zipfile.ZipFile(tmp, "r") as z:
    z.extractall(dest)
    for name in z.namelist():
        print(f"  {name}")

os.remove(tmp)

# Find flyctl.exe
for root, dirs, files in os.walk(dest):
    for f in files:
        if "flyctl" in f.lower():
            print(f"Found: {os.path.join(root, f)}")
