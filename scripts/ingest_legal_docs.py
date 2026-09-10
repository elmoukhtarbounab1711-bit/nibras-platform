"""Ingest the public MEGA legal-document library into data/legal_docs/.

Downloads every file (mostly .doc/.docx/.pdf) from the shared MEGA folder,
organizes them under data/legal_docs/<category>/..., and writes
data/legal_docs/index.json as the runtime catalog.

Resumable: files already present with matching size are skipped. Re-run to
continue after interruptions or MEGA bandwidth limits (HTTP 509).
"""

import base64
import concurrent.futures
import json
import os
import random
import re
import time
import urllib.request

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(PROJECT_ROOT, "data", "legal_docs")
INDEX_PATH = os.path.join(DEST, "index.json")

MEGA_URL = "https://mega.nz/folder/Gk01DACK#mAKKqKTfAgxt5o1jttRbuw"
FID, KEY_B64 = MEGA_URL.split("folder/")[1].split("#")

WORKERS = 6
IGNORED_SUFFIXES = (".lnk", ".tmp")
IGNORED_PREFIXES = ("~$",)


def d64(s):
    pad = "=" * ((4 - len(s) % 4) % 4)
    return base64.urlsafe_b64decode(s + pad)


def aes_ecb_decrypt(key16, data):
    return Cipher(algorithms.AES(key16), modes.ECB()).decryptor().update(data)


def aes_cbc_decrypt(key16, data):
    return Cipher(algorithms.AES(key16), modes.CBC(b"\x00" * 16)).decryptor().update(data)


def cipher_key(node_key):
    if len(node_key) == 16:
        return node_key
    out = bytearray(16)
    for i in range(16):
        out[i] = node_key[i] ^ node_key[16 + i]
    return bytes(out)


def decrypt_attrs(a_str, node_key):
    if not a_str:
        return None
    raw = aes_cbc_decrypt(cipher_key(node_key), d64(a_str))
    end = 0
    while end < len(raw) and raw[end]:
        end += 1
    txt = raw[:end].decode("utf-8", "replace")
    if not txt.startswith("MEGA{"):
        return None
    try:
        return json.loads(txt[4:])
    except (ValueError, UnicodeDecodeError):
        return None


def unwrap(k_str, parent_key):
    return aes_ecb_decrypt(parent_key, d64(k_str.split(":")[-1]))


def api_cs(params, nid=None, tries=8):
    for i in range(tries):
        url = "https://g.api.mega.co.nz/cs?id=" + str(random.randint(1, 2**31))
        if nid:
            url += "&n=" + nid
        req = urllib.request.Request(url, data=json.dumps(params).encode(),
                                     headers={"Content-Type": "application/json"},
                                     method="POST")
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 509:
                wait = int(e.headers.get("x-mega-time-left") or 0) + 1
                print(f"  bandwidth limit, sleeping {wait}s...")
                time.sleep(min(wait, 600))
            else:
                time.sleep(min(5 * (2 ** i), 60))
    raise RuntimeError("API failed after retries")


def get_share():
    nodes = api_cs([{"a": "f", "c": 1, "r": 1, "ca": 1}], FID)[0]["f"]
    share_key = d64(KEY_B64)
    keys = {}
    for n in nodes:
        if n.get("k"):
            keys[n["h"]] = unwrap(n["k"], share_key)
    attrs = {n["h"]: decrypt_attrs(n.get("a"), keys[n["h"]]) for n in nodes
             if n["h"] in keys}
    return nodes, keys, attrs


def sanitize(name):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    name = name.strip().strip(".")
    return name[:150] or "file"


def download_one(handle, key32, target, expected_size):
    # fetch ciphertext URL once (API), then stream-decrypt
    for i in range(8):
        try:
            resp = api_cs([{"a": "g", "g": 1, "ssl": 2, "n": handle}], FID)[0]
            if "g" not in resp:
                return ("error", "no-url")
            url = resp["g"]
            cip = urllib.request.urlopen(urllib.request.Request(url), timeout=120).read()
            if not cip and resp.get("s", 0) == 0:
                open(target, "wb").close()
                return ("ok", 0)
            ckey = cipher_key(key32)
            iv = key32[16:24] + b"\x00" * 8
            dec = Cipher(algorithms.AES(ckey), modes.CTR(iv)).decryptor()
            plain = dec.update(cip) + dec.finalize()
            tmp = target + ".part"
            with open(tmp, "wb") as f:
                f.write(plain)
            os.replace(tmp, target)
            return ("ok", len(plain))
        except urllib.error.HTTPError as e:
            if e.code == 509:
                wait = int(e.headers.get("x-mega-time-left") or 0) + 1
                print(f"  dl bandwidth limit, sleeping {wait}s...")
                time.sleep(min(wait, 600))
            else:
                time.sleep(min(5 * (2 ** i), 60))
        except Exception:  # noqa: BLE001 — أحد شبكي متقلب، نعيد المحاولة بالتزايد
            time.sleep(min(5 * (2 ** i), 60))
    return ("error", "retries-exhausted")


def main():
    print("listing share...")
    nodes, keys, attrs = get_share()
    by = {n["h"]: n for n in nodes}

    top = next(n for n in nodes if n.get("p") not in {x["h"] for x in nodes})
    children_of = {}
    for n in nodes:
        children_of.setdefault(n.get("p"), []).append(n)

    # build (path, node) for every file
    files = []

    def walk(h, path):
        a = attrs.get(h) or {}
        name = (a.get("n") or "?") if a else "?"
        if by[h].get("t") == 0:
            files.append((path + [name], h, by[h]))
            return
        for c in children_of.get(h, []):
            walk(c["h"], path + [name])

    for c in children_of.get(top["h"], []):
        walk(c["h"], [])

    print("total files:", len(files))

    jobs = []
    for rel, h, node in files:
        name = rel[-1]
        if name.startswith(IGNORED_PREFIXES) or name.lower().endswith(IGNORED_SUFFIXES):
            continue
        dirpath = os.path.join(DEST, *[sanitize(p) for p in rel[:-1]])
        full = os.path.join(dirpath, sanitize(name))
        jobs.append((rel, h, node, full))

    os.makedirs(DEST, exist_ok=True)
    todo = []
    for rel, h, node, full in jobs:
        size = node.get("s", 0)
        if os.path.exists(full) and os.path.getsize(full) == size:
            continue
        todo.append((rel, h, node, full))

    print("to download:", len(todo), "of", len(jobs))
    done = ok = 0
    errs = []
    t0 = time.time()

    def run(job):
        _rel, h, node, full = job
        os.makedirs(os.path.dirname(full), exist_ok=True)
        return download_one(h, keys[h], full, node.get("s", 0))

    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = {ex.submit(run, j): j for j in todo}
        for fut in concurrent.futures.as_completed(futures):
            job = futures[fut]
            try:
                st, n = fut.result()
            except Exception as e:  # noqa: BLE001
                st, n = ("error", repr(e))
            done += 1
            if st == "ok":
                ok += 1
            else:
                errs.append((job[2].get("s", 0), job[0][-1], n))
            if done % 100 == 0 or done == len(todo):
                print(f"  {done}/{len(todo)} ok={ok} err={len(errs)} "
                      f"elapsed={time.time() - t0:.0f}s")

    print(f"finished: ok={ok} err={len(errs)} in {time.time() - t0:.0f}s")
    for size, name, err in errs[:15]:
        print("  ERR", name, err)

    # index.json
    cats = {}
    for rel, h, node, full in jobs:
        if not os.path.exists(full):
            continue
        cat = sanitize(rel[0]) if len(rel) > 1 else "(root)"
        cats.setdefault(cat, []).append({
            "title": rel[-1],
            "file": os.path.relpath(full, DEST).replace("\\", "/"),
            "size": node.get("s", 0),
            "ext": (rel[-1].rsplit(".", 1)[-1].lower() if "." in rel[-1] else ""),
        })
    index = {
        "source": MEGA_URL,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_files": sum(len(v) for v in cats.values()),
        "categories": [{"name": k, "slug": f"c{i:02d}", "docs": v}
                       for i, (k, v) in enumerate(sorted(cats.items()), 1)],
    }
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=1)
    print("index written:", INDEX_PATH, "files indexed:", index["total_files"])


if __name__ == "__main__":
    main()
