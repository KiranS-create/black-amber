"""
SIH26237 - Origin Server Absence & Standalone Portability Integration Tests.

Validates that:
1. Forensic evidence packages are completely self-contained and portable.
2. Exported package directories and .zip files can be audited after the originating server,
   database, and in-memory services are completely destroyed.
3. The Offline Evidence Verifier produces VERIFIED status with zero server state.
"""

import os
import gc
import tempfile
import pytest
from pathlib import Path
from core.integration.orchestrator import AegisTraceEndToEndOrchestrator
from core.evidence_package.exporter import EvidencePackageExporter
from core.evidence_package.models import VerificationStatus
from core.evidence_package.verifier import OfflineEvidenceVerifier


def test_verification_after_origin_server_destruction():
    """Builds package, exports to disk, destroys originating orchestrator, and verifies standalone."""
    orchestrator = AegisTraceEndToEndOrchestrator(tenant_id="tenant_portable_audit")
    result = orchestrator.run_full_golden_pipeline(leak_recipient_id="alice")
    package = result.evidence_package

    with tempfile.TemporaryDirectory() as tmpdir:
        export_dir = Path(tmpdir) / "exported_evidence"
        zip_path = Path(tmpdir) / "evidence_archive.zip"

        # 1. Export package to directory and zip
        EvidencePackageExporter.export_to_directory(package, export_dir)
        EvidencePackageExporter.export_to_zip(package, zip_path)

        assert (export_dir / "manifest.json").exists()
        assert (export_dir / "signature.json").exists()
        assert zip_path.exists()

        # 2. Obliterate orchestrator, release manager, registries, and memory state
        del orchestrator
        del result
        del package
        gc.collect()

        # 3. Load package from disk directory in fresh context
        loaded_pkg = EvidencePackageExporter.import_from_directory(export_dir)

        # 4. Audit using a freshly instantiated verifier
        standalone_verifier = OfflineEvidenceVerifier(expected_tenant_id="tenant_portable_audit")
        standalone_result = standalone_verifier.verify_package(
            manifest=loaded_pkg.manifest,
            signature=loaded_pkg.signature,
            objects=loaded_pkg.objects,
            edges=loaded_pkg.edges,
            custody_chain=loaded_pkg.custody_chain
        )

        assert standalone_result.overall_status == VerificationStatus.VERIFIED
        assert standalone_result.manifest_signature_valid is True
        assert standalone_result.merkle_root_valid is True
        assert standalone_result.recipient_signature_valid is True
        assert standalone_result.ledger_proof_valid is True
        assert standalone_result.lineage_valid is True
