"""
scripts/deployment/scan_secrets.py

CLI tool to audit repository files for leaked secrets, API keys, and private keys.

Usage:
    python scripts/deployment/scan_secrets.py
"""

import sys
import argparse
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from core.deployment.secret_scanner import SecretScanner


def main():
    parser = argparse.ArgumentParser(description="AegisTrace Static Secret & Credential Scanner")
    parser.add_argument("--dir", type=str, default=None, help="Target directory to scan")
    parser.add_argument("--strict", action="store_true", help="Exit with non-zero on any findings")

    args = parser.parse_args()
    target_dir = Path(args.dir) if args.dir else repo_root
    scanner = SecretScanner(repo_root=repo_root)

    print(f"=== AegisTrace Secret & Credential Audit ===")
    print(f"[*] Scanning directory: {target_dir}...")

    res = scanner.scan_directory(target_dir=target_dir)

    print(f"[*] Files scanned: {res['scanned_files']}")
    print(f"[*] Findings detected: {res['total_findings']}")

    if res["findings"]:
        print("\n[!] WARNING: Secret candidates identified:")
        for item in res["findings"]:
            print(f"    - [{item['severity']}] {item['file']}:{item['line']} ({item['rule']})")
            print(f"      Snippet: {item['snippet']}")
        if args.strict:
            sys.exit(1)
    else:
        print("[OK] Repository is clean. No hardcoded credentials or private keys detected.")


if __name__ == "__main__":
    main()
