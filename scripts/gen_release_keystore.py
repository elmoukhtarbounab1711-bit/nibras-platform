"""Generate a release signing keystore (PKCS12) for the Nibras TWA app.

Google Play / digital-Asset-Links requirements baked in:
  * RSA 2048 + SHA-256
  * certificate validity >= 25 years (Android app signing requirement)
  * single self-signed key, alias "nibras"

Usage:
    python gen_release_keystore.py [--out nibras-release.p12] [--alias nibras]

If the keystore already exists it is left untouched and the fingerprint
is printed (idempotent).
"""
import argparse
import base64
import hashlib
import os
import secrets
import string
from datetime import datetime, timedelta, timezone

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID


def main() -> None:
    args = argparse.ArgumentParser()
    args.add_argument("--out", default="nibras-release.p12")
    args.add_argument("--alias", default="nibras")
    args.add_argument("--password", default=None, help="keystore & key password (generated if absent)")
    ns = args.parse_args()

    password = ns.password
    if os.path.exists(ns.out):
        print(f"Keystore already exists: {ns.out} (skipped generation)")
    else:
        password = password or "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(24))
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Nibras")])
        now = datetime.now(timezone.utc)
        cert = (
            x509.CertificateBuilder()
            .subject_name(name)
            .issuer_name(name)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(days=1))
            .not_valid_after(now + timedelta(days=365 * 30))
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(
                x509.SubjectKeyIdentifier.from_public_key(key.public_key()), critical=False
            )
            .sign(key, hashes.SHA256())
        )
        blob = pkcs12.serialize_key_and_certificates(
            b"nibras", key, cert, None,
            serialization.BestAvailableEncryption(password.encode("utf-8")),
        )
        with open(ns.out, "wb") as fh:
            fh.write(blob)
        print(f"Keystore created: {ns.out}")

    # Fingerprint (SHA-256 of the DER cert, colon-separated uppercase).
    with open(ns.out, "rb") as fh:
        loaded = pkcs12.load_key_and_certificates(
            fh.read(), password.encode("utf-8")
        )
    cert = loaded[1]
    if cert is None:
        raise SystemExit("No certificate found in keystore")
    der = cert.public_bytes(serialization.Encoding.DER)
    fp = ":".join(f"{b:02X}" for b in hashlib.sha256(der).digest())
    print("SHA256 fingerprint:", fp)

    if ns.password is None:
        b64 = base64.b64encode(open(ns.out, "rb").read()).decode()
        print("\nSecret to add to GitHub (Actions secrets):")
        print("  ANDROID_KEYSTORE_B64 =", b64)
        print("  KEYSTORE_PASSWORD    =", password)
        print("  KEY_PASSWORD         =", password)
        print("  KEY_ALIAS            =", ns.alias)
        print("\nNote: keystore and key share one password (printed above).")


if __name__ == "__main__":
    main()