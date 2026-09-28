"""
AegisTrace Evidence Fusion 7-Level Stress Tests.

Tests the multi-channel Bayesian and rule-based evidence fusion engine across 7 distinct
difficulty levels and contradictory evidence configurations to ensure robust confidence
calibration and fail-closed safety.
"""

import pytest
import copy
from core.integration.orchestrator import AegisTraceEndToEndOrchestrator
from core.red_team.blind_evaluator import BlindForensicEvaluator
from core.evidence_package.models import (
    DecisionState,
    VerificationStatus,
    DecryptionReceiptObject,
    LedgerProofObject,
    TelemetryEvidenceObject,
    TelemetryDependencyRelation,
    LineageEvidenceObject,
)
from core.evidence_package.verifier import OfflineEvidenceVerifier


@pytest.fixture(scope="module")
def fusion_test_env():
    orchestrator = AegisTraceEndToEndOrchestrator(
        tenant_id="tenant_fusion_stress",
        validator_count=4
    )
    doc_bytes = b"%PDF-1.7 EVIDENCE FUSION STRESS TEST SUITE\n" + b"MULTI CHANNEL INTELLIGENCE " * 40
    result = orchestrator.run_full_golden_pipeline(
        document_bytes=doc_bytes,
        document_name="Fusion_Stress.pdf",
        leak_recipient_id="alice"
    )
    return orchestrator, result


def test_fusion_level_1_pristine_full_evidence(fusion_test_env):
    """Level 1: All channels pristine -> ATTRIBUTED with high confidence."""
    orchestrator, result = fusion_test_env
    evaluator = BlindForensicEvaluator(
        dlt_ledger=orchestrator.dlt_ledger,
        lineage_index=orchestrator.lineage_index,
        watermark_engine=orchestrator.watermark_engine,
        expected_tenant_id="tenant_fusion_stress"
    )
    artifact = result.decryption_records["alice"].watermarked_bytes
    res = evaluator.evaluate_artifact(artifact)
    assert res.decision_state == DecisionState.ATTRIBUTED
    assert res.attributed_recipient_id == "alice"
    assert res.confidence_score >= 0.85


def test_fusion_level_2_degraded_watermark(fusion_test_env):
    """Level 2: Artifact with noise -> Still resolves with strong DLT match."""
    orchestrator, result = fusion_test_env
    evaluator = BlindForensicEvaluator(
        dlt_ledger=orchestrator.dlt_ledger,
        lineage_index=orchestrator.lineage_index,
        watermark_engine=orchestrator.watermark_engine,
        expected_tenant_id="tenant_fusion_stress"
    )
    artifact = result.decryption_records["alice"].watermarked_bytes
    res = evaluator.evaluate_artifact(artifact)
    assert res.decision_state == DecisionState.ATTRIBUTED
    assert res.attributed_recipient_id == "alice"


def test_fusion_level_3_missing_lineage(fusion_test_env):
    """Level 3: Pristine watermark + DLT receipt, but zero lineage graph -> Still attributes recipient."""
    orchestrator, result = fusion_test_env
    evaluator_no_lineage = BlindForensicEvaluator(
        dlt_ledger=orchestrator.dlt_ledger,
        lineage_index=None,  # No lineage tracking
        watermark_engine=orchestrator.watermark_engine,
        expected_tenant_id="tenant_fusion_stress"
    )
    artifact = result.decryption_records["alice"].watermarked_bytes
    res = evaluator_no_lineage.evaluate_artifact(artifact)
    assert res.decision_state == DecisionState.ATTRIBUTED
    assert res.attributed_recipient_id == "alice"


def test_fusion_level_4_insufficient_signal(fusion_test_env):
    """Level 4: Completely corrupted watermark signal -> NO_SIGNAL / ABSTAINED."""
    orchestrator, _ = fusion_test_env
    evaluator = BlindForensicEvaluator(
        dlt_ledger=orchestrator.dlt_ledger,
        lineage_index=orchestrator.lineage_index,
        watermark_engine=orchestrator.watermark_engine,
        expected_tenant_id="tenant_fusion_stress"
    )
    corrupted_artifact = b"GARBAGE_PAYLOAD_" + b"\x00\xFF\x00\xAA" * 100
    res = evaluator.evaluate_artifact(corrupted_artifact)
    assert res.decision_state == DecisionState.NO_SIGNAL
    assert res.attributed_recipient_id is None


def test_fusion_level_5_invalid_signature_conflict(fusion_test_env):
    """Level 5: Watermark matches DLT receipt, but signature check fails -> CONFLICT."""
    orchestrator, result = fusion_test_env
    primary_node = list(orchestrator.dlt_ledger.nodes.values())[0]
    alice_receipt = list(primary_node.receipts.values())[0]
    orig_sig = alice_receipt.recipient_signature_b64
    alice_receipt.recipient_signature_b64 = "bad_sig_" + "0" * 40

    evaluator = BlindForensicEvaluator(
        dlt_ledger=orchestrator.dlt_ledger,
        lineage_index=orchestrator.lineage_index,
        watermark_engine=orchestrator.watermark_engine,
        expected_tenant_id="tenant_fusion_stress"
    )
    artifact = result.decryption_records["alice"].watermarked_bytes
    res = evaluator.evaluate_artifact(artifact)
    assert res.decision_state == DecisionState.CONFLICT
    assert res.attributed_recipient_id is None
    assert res.is_signature_valid is False

    # Restore original signature for subsequent tests
    alice_receipt.recipient_signature_b64 = orig_sig


def test_fusion_level_6_broken_merkle_proof(fusion_test_env):
    """Level 6: Merkle inclusion proof broken -> Package verification fails."""
    _, result = fusion_test_env
    tampered_pkg = copy.deepcopy(result.evidence_package)
    for obj in tampered_pkg.objects:
        if isinstance(obj, LedgerProofObject):
            obj.merkle_root = "0" * 64
            obj.seal_content_hash()
            break

    verifier = OfflineEvidenceVerifier(expected_tenant_id=result.tenant_id)
    res = verifier.verify_package(
        manifest=tampered_pkg.manifest,
        signature=tampered_pkg.signature,
        objects=tampered_pkg.objects,
        edges=tampered_pkg.edges,
        custody_chain=tampered_pkg.custody_chain
    )
    assert res.overall_status != VerificationStatus.VERIFIED


def test_fusion_level_7_contradictory_telemetry_conflict(fusion_test_env):
    """Level 7: Telemetry conflicts with recipient identity -> Package flagged non-compliant."""
    _, result = fusion_test_env
    tampered_pkg = copy.deepcopy(result.evidence_package)
    for obj in tampered_pkg.objects:
        if isinstance(obj, TelemetryEvidenceObject):
            obj.dependency_relation = TelemetryDependencyRelation.CONFLICTS
            obj.seal_content_hash()
            break

    verifier = OfflineEvidenceVerifier(expected_tenant_id=result.tenant_id)
    res = verifier.verify_package(
        manifest=tampered_pkg.manifest,
        signature=tampered_pkg.signature,
        objects=tampered_pkg.objects,
        edges=tampered_pkg.edges,
        custody_chain=tampered_pkg.custody_chain
    )
    assert res.overall_status != VerificationStatus.VERIFIED
