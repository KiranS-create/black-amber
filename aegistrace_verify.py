"""
AegisTrace Standalone Offline Evidence Verifier CLI.

Enables judicial examiners, external auditors, or sovereign intelligence agencies
to independently audit an AegisTrace forensic evidence package with ZERO network access,
ZERO cloud KMS calls, and ZERO connection to the originating application server or database.

Usage:
    python aegistrace_verify.py /path/to/evidence_package/ [--tenant EXPECTED_TENANT] [--json]
    python aegistrace_verify.py /path/to/package.zip [--tenant EXPECTED_TENANT] [--json]
"""

import sys
import os
import argparse
import json
from pathlib import Path

# Add repo root to sys.path if running as standalone script
repo_root = Path(__file__).resolve().parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from core.evidence_package.exporter import EvidencePackageExporter
from core.evidence_package.verifier import OfflineEvidenceVerifier
from core.evidence_package.models import VerificationStatus


def main():
    parser = argparse.ArgumentParser(
        description="AegisTrace Independent Offline Forensic Evidence Package Verifier"
    )
    parser.add_argument("package_path", help="Path to evidence package directory or .zip archive")
    parser.add_argument("--tenant", dest="tenant_id", default=None, help="Expected tenant ID for isolation check")
    parser.add_argument("--json", dest="output_json", action="store_true", help="Output machine-readable JSON report")

    args = parser.parse_args()
    pkg_path = Path(args.package_path)

    if not pkg_path.exists():
        sys.stderr.write(f"Error: Target evidence package not found: {pkg_path}\n")
        sys.exit(2)

    try:
        if pkg_path.is_file() and pkg_path.suffix.lower() == ".zip":
            package = EvidencePackageExporter.load_from_zip(pkg_path)
        elif pkg_path.is_dir():
            package = EvidencePackageExporter.load_from_directory(pkg_path)
        else:
            sys.stderr.write(f"Error: Target path must be a directory or .zip archive: {pkg_path}\n")
            sys.exit(2)
    except Exception as e:
        sys.stderr.write(f"Error parsing evidence package: {str(e)}\n")
        sys.exit(3)

    verifier = OfflineEvidenceVerifier(expected_tenant_id=args.tenant_id)
    result = verifier.verify_package(
        manifest=package.manifest,
        signature=package.signature,
        objects=package.objects,
        edges=package.edges,
        custody_chain=package.custody_chain
    )

    if args.output_json:
        print(json.dumps(result.model_dump(mode="json"), indent=2))
    else:
        print("=" * 70)
        print("AEGISTRACE FORENSIC EVIDENCE PACKAGE VERIFICATION REPORT")
        print("=" * 70)
        print(f"Package ID:           {result.package_id}")
        print(f"Overall Status:       {result.overall_status.value}")
        print(f"Verified At:          {result.verified_at}")
        print("-" * 70)
        print(f"Manifest Signature:   {'VALID (ML-DSA-65)' if result.manifest_signature_valid else 'INVALID'}")
        print(f"Merkle Commitment:    {'VALID (RFC-6962)' if result.merkle_root_valid else 'INVALID'}")
        print(f"Content-Addressed:    {'VALID (SHA-256)' if result.object_hashes_valid else 'INVALID'}")
        print(f"Dependency DAG:       {'VALID (Acyclic Grounded)' if result.dependency_graph_valid else 'INVALID'}")
        print(f"Recipient Signature:  {'VALID (ML-DSA-65)' if result.recipient_signature_valid else 'INVALID'}")
        print(f"Historical Key Bound: {'VALID (Temporal Invariant)' if result.historical_keys_valid else 'INVALID'}")
        print(f"Ledger / DLT Proof:   {'VALID (Quorum Verified)' if result.ledger_proof_valid else 'INVALID'}")
        print(f"Watermark Binding:    {'VALID (Artifact Bound)' if result.watermark_binding_valid else 'INVALID'}")
        print(f"Lineage Integrity:    {'VALID (Boundary Preserved)' if result.lineage_valid else 'INVALID'}")
        print(f"Chain of Custody:     {'VALID (Append-Only Hash Chain)' if result.custody_chain_valid else 'INVALID'}")
        print(f"Attribution Decision: {'CONSISTENT (Ground Truth Followed)' if result.decision_consistent else 'INVALID'}")
        print("=" * 70)

        if result.errors:
            print("\nVERIFICATION ERRORS DETECTED:")
            for err in result.errors:
                print(f"  [!] {err}")
        if result.warnings:
            print("\nADVISORY FORENSIC WARNINGS:")
            for warn in result.warnings:
                print(f"  [*] {warn}")

    if result.overall_status == VerificationStatus.VERIFIED:
        sys.exit(0)
    elif result.overall_status == VerificationStatus.PARTIALLY_VERIFIED:
        sys.exit(1)
    else:
        sys.exit(4)


if __name__ == "__main__":
    main()
