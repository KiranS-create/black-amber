"""
scripts/deployment/prepare_offline_bundle.py

CLI tool to prepare and verify offline wheelhouse bundles for air-gapped installation.

Usage:
    python scripts/deployment/prepare_offline_bundle.py --verify ./wheelhouse
    python scripts/deployment/prepare_offline_bundle.py --download ./wheelhouse
    python scripts/deployment/prepare_offline_bundle.py --print-command
"""

import sys
import subprocess
import argparse
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from core.deployment.offline_bundle import OfflineBundleManager


def main():
    parser = argparse.ArgumentParser(description="AegisTrace Offline Wheelhouse Tool")
    parser.add_argument("--download", type=str, default=None, help="Directory to download wheels to using pip")
    parser.add_argument("--verify", type=str, default=None, help="Directory containing wheels to verify")
    parser.add_argument("--manifest", type=str, default=None, help="Generate wheelhouse manifest for directory")
    parser.add_argument("--print-command", action="store_true", help="Print air-gapped pip install command")

    args = parser.parse_args()
    mgr = OfflineBundleManager(repo_root=repo_root)

    if args.print_command:
        print("[*] Air-Gapped Installation Command:")
        print(f"    {mgr.get_offline_install_command()}")
        return

    if args.download:
        dest_dir = Path(args.download)
        dest_dir.mkdir(parents=True, exist_ok=True)
        print(f"[+] Downloading hashed wheels to {dest_dir}...")
        cmd = [
            sys.executable, "-m", "pip", "download",
            "--dest", str(dest_dir),
            "--require-hashes",
            "-r", str(repo_root / "deployment" / "requirements-hashes.txt")
        ]
        res = subprocess.run(cmd)
        if res.returncode != 0:
            print(f"[!] pip download exited with code {res.returncode}", file=sys.stderr)
            sys.exit(res.returncode)
        print("[+] Download complete. Generating manifest...")
        mgr.generate_wheelhouse_manifest(dest_dir)
        print(f"[OK] Wheelhouse ready at {dest_dir}")
        return

    target_dir = Path(args.verify) if args.verify else (Path(args.manifest) if args.manifest else None)
    if target_dir:
        print(f"[+] Verifying wheelhouse at {target_dir}...")
        res = mgr.verify_wheelhouse(target_dir)
        print(f"    Status: {res['status']}")
        print(f"    Total required packages: {res['total_required']}")
        print(f"    Present & verified packages: {res['present_count']}")
        print(f"    Missing packages: {res['missing_count']}")
        print(f"    Corrupted/tampered wheels: {res['corrupted_count']}")

        if args.manifest or res["present_count"] > 0:
            manifest_file = target_dir / "wheelhouse_manifest.json"
            mgr.generate_wheelhouse_manifest(target_dir, manifest_file)
            print(f"    Wrote manifest: {manifest_file}")

        if res["status"] != "COMPLETE":
            print(f"[!] Warning: Wheelhouse is incomplete or corrupted: missing={len(res['missing'])}, corrupted={len(res['corrupted'])}")
    else:
        print("[*] No action specified. Run with --help for options.")
        print(f"[*] Offline install command:\n    {mgr.get_offline_install_command()}")


if __name__ == "__main__":
    main()
