"""
AegisTrace Fail-Closed Audit Tests.

Executes automated static scanning and dynamic fault injection to verify that
AegisTrace source code and runtime components strictly adhere to fail-closed semantics:
- Zero heuristic shortcuts (no nearest recipient guesses).
- Zero skipped signature verifications in core paths.
- Proper exception handling and safe abstention on corrupted inputs.
"""

import pytest
from pathlib import Path
from datetime import datetime, timezone
from core.red_team.audit_fail_closed import FailClosedAuditor, FailClosedAuditReport
from core.evidence_package.verifier import OfflineEvidenceVerifier
from core.evidence_package.models import (
    VerificationStatus,
    PackageManifest,
    PackageSignature,
)


def test_static_fail_closed_code_audit():
    """
    Scans the core/ codebase for prohibited heuristic fallback patterns.
    """
    repo_root = Path(__file__).resolve().parent.parent.parent
    auditor = FailClosedAuditor(repo_root=repo_root)
    
    report: FailClosedAuditReport = auditor.scan_codebase()
    
    assert report.is_compliant is True, (
        f"Fail-closed audit discovered {report.total_findings} violation(s):\n"
        + "\n".join(f"[{f.rule_id}] {f.file_path}:{f.line_number} - {f.description}" for f in report.findings)
    )
    assert report.scanned_files_count >= 20


def test_dynamic_verifier_corrupted_inputs_fail_closed():
    """
    Injects malformed, empty, and corrupted structures into the OfflineEvidenceVerifier.
    Verifies that the verifier fails closed (INVALID / FAILED) without unhandled crashes.
    """
    verifier = OfflineEvidenceVerifier(expected_tenant_id="tenant_fail_closed_test")

    # 1. Test mismatched tenant in manifest
    manifest = PackageManifest(
        package_id="pkg_test_001",
        tenant_id="tenant_different_foreign",
        case_id="case_001",
        created_at=datetime.now(timezone.utc).isoformat(),
        dependency_graph_root="0" * 64,
        evidence_merkle_root="0" * 64,
        final_decision_reference="decision_001"
    )
    sig = PackageSignature(
        signer_id="examiner_001",
        signer_public_key_b64="00" * 32,
        signed_manifest_hash="00" * 32,
        signature_b64="00" * 64,
        timestamp=datetime.now(timezone.utc).isoformat()
    )

    res_foreign = verifier.verify_package(
        manifest=manifest,
        signature=sig,
        objects=[],
        edges=[],
        custody_chain=[]
    )
    assert res_foreign.overall_status == VerificationStatus.INVALID
    assert any("TENANT_ISOLATION_VIOLATION" in err for err in res_foreign.errors)
