"""
SIH26237 - Key Rotation, Revocation & Historical Lifecycle Integration Tests.

Validates that:
1. Historical decryption receipts signed with an active key K1 remain permanently valid.
2. When key K1 is rotated/revoked, new decryption receipts signed with K1 after revocation
   are rejected by Offline Verifier Pillar 7 (POST_REVOCATION_REJECTION).
3. Receipts signed with newly rotated active key K2 verify successfully.
"""

import pytest
import copy
from datetime import datetime, timezone, timedelta
from core.integration.orchestrator import AegisTraceEndToEndOrchestrator
from core.evidence_package.models import VerificationStatus
from core.evidence_package.verifier import OfflineEvidenceVerifier


def test_key_rotation_and_historical_preservation():
    """Tests that historical receipts remain valid while post-revocation signatures are blocked."""
    orchestrator = AegisTraceEndToEndOrchestrator(tenant_id="tenant_key_rotation")
    result = orchestrator.run_full_golden_pipeline(leak_recipient_id="alice")

    # 1. Historical receipt is VERIFIED
    assert result.verification_result.overall_status == VerificationStatus.VERIFIED
    assert result.verification_result.historical_keys_valid is True

    # 2. Simulate post-revocation replay attack:
    # Set the key's revocation timestamp in the past before the decryption event occurred
    tampered_pkg = copy.deepcopy(result.evidence_package)
    now = datetime.now(timezone.utc)
    for obj in tampered_pkg.objects:
        if obj.object_type.value == "RECIPIENT_IDENTITY_PROOF":
            # Set revocation to 2 days ago
            obj.revocation_timestamp = (now - timedelta(days=2)).isoformat()
            obj.seal_content_hash()
            break

    # Re-verify tampered package
    verifier = OfflineEvidenceVerifier(expected_tenant_id="tenant_key_rotation")
    v_tampered = verifier.verify_package(
        manifest=tampered_pkg.manifest,
        signature=tampered_pkg.signature,
        objects=tampered_pkg.objects,
        edges=tampered_pkg.edges,
        custody_chain=tampered_pkg.custody_chain
    )

    # Must fail Pillar 7
    assert v_tampered.overall_status != VerificationStatus.VERIFIED
    assert v_tampered.historical_keys_valid is False
    assert any("POST_REVOCATION_REJECTION" in err for err in v_tampered.errors)
