"""
scripts/deployment/generate_requirements_hashes.py

Generates deployment/requirements-hashes.txt containing cryptographic SHA-256 hashes
for all pinned packages in deployment/requirements-lock.txt.
Ensures pip install --require-hashes can be executed for zero-trust dependency verification.
"""

import sys
import json
import urllib.request
from pathlib import Path


def generate_hashes():
    repo_root = Path(__file__).resolve().parent.parent.parent
    lock_file = repo_root / "deployment" / "requirements-lock.txt"
    hash_file = repo_root / "deployment" / "requirements-hashes.txt"

    if not lock_file.exists():
        print(f"Error: {lock_file} not found.", file=sys.stderr)
        sys.exit(1)

    with open(lock_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    entries = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "==" in line:
            pkg, ver = line.split("==", 1)
            entries.append((pkg.strip(), ver.strip()))

    print(f"Resolving SHA-256 hashes for {len(entries)} pinned packages...")

    output_lines = [
        "# AegisTrace Cryptographically Pinned & Hashed Dependencies",
        "# Generated for pip install --require-hashes verification",
        "# Enforces zero-trust defense against package tampering and MITM substitution",
        "",
    ]

    for pkg, ver in entries:
        print(f"  Fetching hashes for {pkg}=={ver}...")
        url = f"https://pypi.org/pypi/{pkg}/{ver}/json"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AegisTrace-SupplyChain-Auditor/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            
            urls = data.get("urls", [])
            hashes = sorted(list(set(u["digests"]["sha256"] for u in urls if "digests" in u and "sha256" in u["digests"])))
            
            if not hashes:
                print(f"    WARNING: No sha256 digests found for {pkg}=={ver}")
                output_lines.append(f"{pkg}=={ver}")
            else:
                formatted = f"{pkg}=={ver} \\\n"
                hash_lines = [f"    --hash=sha256:{h}" for h in hashes]
                formatted += " \\\n".join(hash_lines)
                output_lines.append(formatted)
        except Exception as e:
            print(f"    ERROR fetching {pkg}=={ver}: {e}")
            output_lines.append(f"{pkg}=={ver}")

    with open(hash_file, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines) + "\n")

    print(f"\nSuccessfully wrote {hash_file}")


if __name__ == "__main__":
    generate_hashes()
