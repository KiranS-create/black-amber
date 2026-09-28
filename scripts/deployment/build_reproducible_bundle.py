"""
scripts/deployment/build_reproducible_bundle.py

CLI tool to build bit-for-bit reproducible release bundles of AegisTrace.
Verifies determinism across two consecutive build passes and prints SHA-256 digests.

Usage:
    python scripts/deployment/build_reproducible_bundle.py
    python scripts/deployment/build_reproducible_bundle.py --out dist/aegistrace-1.0.0.zip
    python scripts/deployment/build_reproducible_bundle.py --verify-only
"""

import sys
import argparse
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from core.deployment.builder import ReproducibleBundleBuilder


def main():
    parser = argparse.ArgumentParser(description="AegisTrace Reproducible Build Tool")
    parser.add_argument("--out", type=str, default="artifacts/deployment/aegistrace-release.zip", help="Output path for bundle")
    parser.add_argument("--tar", action="store_true", help="Also generate tar.gz bundle")
    parser.add_argument("--verify-only", action="store_true", help="Only verify reproducible dual-pass determinism")
    parser.add_argument("--epoch", type=int, default=None, help="Custom SOURCE_DATE_EPOCH")

    args = parser.parse_args()
    builder = ReproducibleBundleBuilder(repo_root=repo_root, epoch=args.epoch)

    print(f"=== AegisTrace Reproducible Build Engine ===")
    print(f"[*] Repository root: {repo_root}")
    print(f"[*] SOURCE_DATE_EPOCH: {builder.epoch}")

    print("\n[+] Running dual-pass reproducibility verification...")
    repro_res = builder.verify_reproducibility()
    if not repro_res["reproducible"]:
        print(f"[!] REPRODUCIBILITY FAILURE: Passes produced divergent artifacts!", file=sys.stderr)
        print(f"    ZIP pass 1: {repro_res['pass_1_zip']['sha256']}")
        print(f"    ZIP pass 2: {repro_res['pass_2_zip']['sha256']}")
        print(f"    TAR pass 1: {repro_res['pass_1_tar']['sha256']}")
        print(f"    TAR pass 2: {repro_res['pass_2_tar']['sha256']}")
        sys.exit(1)

    print(f"[OK] Determinism verified! Two clean build passes produced byte-identical hashes:")
    print(f"     ZIP SHA-256: {repro_res['zip_sha256']}")
    print(f"     TAR SHA-256: {repro_res['tar_sha256']}")
    print(f"     File count:  {repro_res['file_count']} files")

    if not args.verify_only:
        out_zip = repo_root / args.out
        print(f"\n[+] Writing production release archive to {out_zip}...")
        zip_res = builder.build_zip(out_zip)
        print(f"    Archive size: {zip_res['size_bytes']} bytes")
        print(f"    SHA-256:      {zip_res['sha256']}")

        if args.tar:
            out_tar = out_zip.with_suffix(".tar.gz")
            print(f"[+] Writing production tar.gz archive to {out_tar}...")
            tar_res = builder.build_tar_gz(out_tar)
            print(f"    Archive size: {tar_res['size_bytes']} bytes")
            print(f"    SHA-256:      {tar_res['sha256']}")

    print("\n[SUCCESS] Reproducible build process completed successfully.")


if __name__ == "__main__":
    main()
