"""
scripts/deployment/sign_release.py

CLI tool to sign and verify AegisTrace release manifests using post-quantum ML-DSA-65.
Usage:
    python scripts/deployment/sign_release.py --sign
    python scripts/deployment/sign_release.py --verify
"""

import sys
import argparse
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from core.deployment.manifest import ArtifactManifestManager
from core.deployment.signer import ReleaseManifestSigner


def main():
    parser = argparse.ArgumentParser(description="AegisTrace Post-Quantum Release Signer & Verifier")
    parser.add_argument("--sign", action="store_true", help="Generate fresh manifest and sign with ML-DSA-65")
    parser.add_argument("--verify", action="store_true", help="Verify release manifest and ML-DSA-65 signature")
    parser.add_argument("--manifest", type=str, default=None, help="Custom manifest path")
    parser.add_argument("--sig", type=str, default=None, help="Custom signature path")

    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    manifest_mgr = ArtifactManifestManager(repo_root=repo_root)
    signer = ReleaseManifestSigner(repo_root=repo_root)

    manifest_p = Path(args.manifest) if args.manifest else None
    sig_p = Path(args.sig) if args.sig else None

    if args.sign or (not args.sign and not args.verify):
        print("[+] Generating fresh release manifest...")
        manifest = manifest_mgr.generate_manifest(output_path=manifest_p)
        print(f"    Total files tracked: {manifest['file_count']}")
        print(f"    Manifest root digest: {manifest['manifest_root_digest']}")

        print("[+] Cryptographically signing manifest with ML-DSA-65 (NIST FIPS 204)...")
        sig_doc = signer.sign_manifest(manifest_path=manifest_p, output_sig_path=sig_p)
        print(f"    Algorithm: {sig_doc['algorithm']} ({sig_doc['standard']})")
        print(f"    Signer ID: {sig_doc['signer_id']}")
        print(f"    Signature size (hex): {len(sig_doc['signature_hex'])} characters ({len(sig_doc['signature_hex'])//2} bytes)")
        print("[OK] Manifest successfully signed.")

    if args.verify or args.sign:
        print("\n[+] Verifying artifact integrity and post-quantum signature...")
        manifest_res = manifest_mgr.verify_manifest(manifest_path=manifest_p)
        if manifest_res["status"] != "VALID":
            print(f"[!] Integrity verification FAILED: {manifest_res}", file=sys.stderr)
            sys.exit(1)
        print(f"    Artifact hash checks passed: {manifest_res['matched_count']} files verified.")

        sig_res = signer.verify_manifest_signature(manifest_path=manifest_p, sig_path=sig_p)
        if not sig_res["valid"]:
            print(f"[!] Signature verification FAILED: {sig_res.get('error')}", file=sys.stderr)
            sys.exit(1)
        print(f"    Signature validity: {sig_res['valid']}")
        print(f"    Signer verified: {sig_res['signer_id']}")
        print(f"    Root digest match: {sig_res['manifest_root_digest']}")
        print("[OK] Release manifest cryptographically valid.")


if __name__ == "__main__":
    main()
