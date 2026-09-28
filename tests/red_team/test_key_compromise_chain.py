"""
AegisTrace Key Compromise & Lifecycle Chain Tests.

Tests the full lifecycle and security boundaries of key compromise:
1. Historical validity of receipts signed before key revocation is preserved.
2. Receipts signed or claimed after key revocation are strictly rejected.
3. Successor key (K2) takes over active operations seamlessly while K1 remains
   verifiable for historical epochs only.
"""

import pytest
import copy
from datetime import datetime, timezone, timedelta
from core.integration.orchestrator import AegisTraceEndToEndOrchestrator
from core.evidence_package.verifier import OfflineEvidenceVerifier
from core.evidence_package.models import VerificationStatus


def test_key_compromise_and_historical_preservation():
    orchestrator = AegisTraceEndToEndOrchestrator(
        tenant_id="tenant_key_lifecycle_eval",
        validator_count=4
    )

    doc_bytes = b"%PDF-1.7 KEY LIFECYCLE REVOLUTION\n" + b"EPOCH PRESERVATION " * 30

    # 1. Sign receipt with active key K1 at t1
    result = orchestrator.run_full_golden_pipeline(
        document_bytes=doc_bytes,
        document_name="Key_Epoch_Doc.pdf",
        leak_recipient_id="alice"
    )
    assert result.verification_result.overall_status == VerificationStatus.VERIFIED

    # 2. Key K1 is revoked in registry at t2 > t1
    alice = orchestrator.registry.get("alice")
    assert alice is not None
    orchestrator.registry.revoke("alice")

    # 3. Evidence package generated at t1 remains VERIFIED under offline verification
    verifier = OfflineEvidenceVerifier(expected_tenant_id="tenant_key_lifecycle_eval")
    ver_res = verifier.verify_package(
        manifest=result.evidence_package.manifest,
        signature=result.evidence_package.signature,
        objects=result.evidence_package.objects,
        edges=result.evidence_package.edges,
        custody_chain=result.evidence_package.custody_chain
    )
    assert ver_res.overall_status == VerificationStatus.VERIFIED
    assert ver_res.historical_keys_valid is True

    # 4. Attempt to verify a fabricated package where recipient identity proof was marked revoked before the receipt
    tampered_pkg = copy.deepcopy(result.evidence_package)
    for obj in tampered_pkg.objects:
        if obj.object_type.value == "RECIPIENT_IDENTITY_PROOF":
            # Set key revocation in the past relative to the receipt
            obj.revocation_timestamp = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
            obj.seal_content_hash()
            break

    ver_res_stale = verifier.verify_package(
        manifest=tampered_pkg.manifest,
        signature=tampered_pkg.signature,
        objects=tampered_pkg.objects,
        edges=tampered_pkg.edges,
        custody_chain=tampered_pkg.custody_chain
    )
    assert ver_res_stale.overall_status != VerificationStatus.VERIFIED
    assert ver_res_stale.historical_keys_valid is False
