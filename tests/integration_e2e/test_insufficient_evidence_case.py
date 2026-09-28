"""
SIH26237 - Insufficient Evidence & Fail-Closed Abstention Integration Tests.

Validates that when a leak artifact is degraded, corrupted, or completely devoid of signal:
1. The watermark extraction engine yields NO_SIGNAL or CORRUPTED.
2. The attribution engine gracefully degrades to NO_SIGNAL / ABSTAINED.
3. The system NEVER falsely accuses an innocent recipient.
4. The offline evidence verifier validates the ABSTAINED decision package.
"""

import os
import pytest
import hashlib
from datetime import datetime, timezone
from core.integration.orchestrator import AegisTraceEndToEndOrchestrator
from core.evidence_package.models import (
    CaseObject,
    ArtifactEvidenceObject,
    WatermarkEvidenceObject,
    AttributionDecisionObject,
    DecisionState,
    VerificationStatus,
)
from core.evidence_package.builder import EvidencePackageBuilder
from core.evidence_package.verifier import OfflineEvidenceVerifier


def test_corrupted_leak_artifact_fail_closed_abstention():
    """Tests that random/corrupted noise fails closed to NO_SIGNAL without blaming anyone."""
    orchestrator = AegisTraceEndToEndOrchestrator(tenant_id="tenant_abstention_test")

    # 1. Enroll recipients & create release
    alice = orchestrator.enroll_recipient("Alice", "alice")
    bob = orchestrator.enroll_recipient("Bob", "bob")
    doc_bytes = b"%PDF-1.7 Classified Strategic Plan 2026 TOP SECRET"
    release, packages = orchestrator.create_release(
        document_bytes=doc_bytes,
        document_name="Plan.pdf",
        issuer_id="HQ",
        recipient_ids=["alice", "bob"]
    )

    # 2. Decrypt for Alice and Bob
    d_alice = orchestrator.decrypt_and_watermark(packages[0], alice)
    d_bob = orchestrator.decrypt_and_watermark(packages[1], bob)
    known = {"alice": d_alice, "bob": d_bob}

    # 3. Simulate heavily wiped / corrupted leak bytes
    corrupted_leak_bytes = os.urandom(2048)
    corrupted_hash = hashlib.sha256(corrupted_leak_bytes).hexdigest()

    # 4. Attribute leak
    attr_res = orchestrator.attribute_leak(
        leak_bytes=corrupted_leak_bytes,
        document_id=release.document_id,
        release_id=release.release_id,
        known_decryptions=known
    )

    # Assert fail-closed
    assert attr_res.detection_state == "NO_SIGNAL"
    assert attr_res.decision_state == DecisionState.NO_SIGNAL
    assert attr_res.attributed_principal_id is None
    assert attr_res.matched_recipient_id is None

    # 5. Build self-consistent ABSTAINED evidence package
    case_id = "CASE_CORRUPTED_LEAK_01"
    builder = EvidencePackageBuilder(case_id=case_id, tenant_id="tenant_abstention_test")
    
    case_obj = CaseObject(
        object_id=f"case_{case_id}",
        case_name="Investigation of Unidentified Corrupted Leak",
        investigator_id="INV_LEAD",
        description="Fail-closed evaluation of unparseable leak artifact",
        tenant_id="tenant_abstention_test"
    )
    builder.add_object(case_obj)

    leak_art = ArtifactEvidenceObject(
        object_id=f"art_corrupt_{corrupted_hash[:8]}",
        artifact_category="LEAK",
        filename="corrupted_leak.bin",
        byte_size=len(corrupted_leak_bytes),
        sha256_digest=corrupted_hash,
        tenant_id="tenant_abstention_test"
    )
    builder.add_object(leak_art)

    wm_obj = WatermarkEvidenceObject(
        object_id=f"wm_corrupt_{corrupted_hash[:8]}",
        artifact_hash=corrupted_hash,
        extraction_method="DYNAMIC_SPATIAL_DSSS_V1",
        extracted_token="",
        confidence_score=0.0,
        detection_state="NO_SIGNAL",
        tenant_id="tenant_abstention_test"
    )
    builder.add_object(wm_obj)

    decision_obj = AttributionDecisionObject(
        object_id=f"decision_{case_id}",
        case_id=case_id,
        evidence_merkle_root="",
        decision_state=DecisionState.NO_SIGNAL,
        attributed_principal_id=None,
        last_known_holder_id=None,
        confidence_score=0.0,
        evidence_dependency_ids=[case_obj.object_id, leak_art.object_id, wm_obj.object_id],
        abstention_rationale="Watermark signal destroyed; insufficient evidence to attribute any principal",
        tenant_id="tenant_abstention_test"
    )
    builder.set_decision(decision_obj)
    builder.add_edge(decision_obj.object_id, wm_obj.object_id, "GROUNDED_IN")
    builder.add_edge(wm_obj.object_id, leak_art.object_id, "DERIVED_FROM")

    pkg = builder.build_and_sign(orchestrator.investigator_keypair)
    verifier = OfflineEvidenceVerifier(expected_tenant_id="tenant_abstention_test")
    verif_res = verifier.verify_package(pkg.manifest, pkg.signature, pkg.objects, pkg.edges, pkg.custody_chain)

    assert verif_res.overall_status == VerificationStatus.VERIFIED
    assert verif_res.decision_consistent is True
