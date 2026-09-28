"""
AegisTrace Blind Forensic Evaluation Tests.

Verifies that the forensic investigation engine operates in strict blind mode:
1. Blind Golden Case: Attribution emerges purely from extracted signal and ledger receipts
   without passing recipient_id, session_id, or expected token hints.
2. Blind Negative Case (Clean Document): Emits NO_SIGNAL / ABSTAINED and never selects nearest recipient.
3. Blind Cross-Recipient Evaluation: Alice, Bob, and Charlie leaks attribute uniquely and correctly.
4. Blind Tampered/Mutated Watermark: Conflicting signal leads to INSUFFICIENT_EVIDENCE / CONFLICT.
"""

import pytest
import os
from core.integration.orchestrator import AegisTraceEndToEndOrchestrator
from core.red_team.blind_evaluator import BlindForensicEvaluator
from core.evidence_package.models import DecisionState
from core.watermark.dynamic import DynamicWatermarkEngine, generate_dynamic_watermark


@pytest.fixture
def trained_orchestrator():
    orchestrator = AegisTraceEndToEndOrchestrator(
        tenant_id="tenant_blind_eval_defense",
        validator_count=4
    )
    return orchestrator


def test_blind_golden_case_attribution(trained_orchestrator):
    """
    Executes a golden leak for Alice and passes only raw artifact bytes to BlindForensicEvaluator.
    Asserts exact attribution to Alice without ground-truth hint.
    """
    doc_bytes = b"%PDF-1.7 BLIND EVALUATION GOLDEN EXPERIMENT\n" + b"RESTRICTED DEFENSE INTEL " * 40
    res = trained_orchestrator.run_full_golden_pipeline(
        document_bytes=doc_bytes,
        document_name="Blind_Test_Intel.pdf",
        leak_recipient_id="alice"
    )

    leak_artifact = res.decryption_records["alice"].watermarked_bytes
    evaluator = BlindForensicEvaluator(
        dlt_ledger=trained_orchestrator.dlt_ledger,
        lineage_index=trained_orchestrator.lineage_index,
        watermark_engine=trained_orchestrator.watermark_engine,
        expected_tenant_id="tenant_blind_eval_defense"
    )

    # Strictly blind call: NO recipient_id, NO token, NO session_id passed
    eval_result = evaluator.evaluate_artifact(leak_artifact)

    assert eval_result.watermark_detected is True
    assert eval_result.decision_state == DecisionState.ATTRIBUTED
    assert eval_result.attributed_recipient_id == "alice"
    assert eval_result.is_signature_valid is True
    assert eval_result.is_ledger_inclusion_valid is True
    assert eval_result.confidence_score >= 0.85
    assert "WATERMARK_CORRELATED_WITH_DLT_RECEIPT" in eval_result.reason_codes
    assert "RECIPIENT_MLDSA_SIGNATURE_VALIDATED" in eval_result.reason_codes


def test_blind_negative_case_clean_document(trained_orchestrator):
    """
    Tests an unwatermarked, clean document.
    Must fail closed: NO_SIGNAL, attributed_recipient_id is None, zero nearest-neighbor guessing.
    """
    clean_doc = b"%PDF-1.7 UNWATERMARKED BENIGN PUBLIC DOCUMENT\n" + b"PUBLIC SPECIFICATION " * 50

    evaluator = BlindForensicEvaluator(
        dlt_ledger=trained_orchestrator.dlt_ledger,
        lineage_index=trained_orchestrator.lineage_index,
        watermark_engine=trained_orchestrator.watermark_engine,
        expected_tenant_id="tenant_blind_eval_defense"
    )

    eval_result = evaluator.evaluate_artifact(clean_doc)

    assert eval_result.watermark_detected is False
    assert eval_result.decision_state == DecisionState.NO_SIGNAL
    assert eval_result.attributed_recipient_id is None
    assert "WATERMARK_NO_SIGNAL_FOUND" in eval_result.reason_codes


def test_blind_multi_recipient_separation(trained_orchestrator):
    """
    Generates leaks for Alice, Bob, and Charlie and verifies BlindForensicEvaluator
    distinguishes them with 100% precision.
    """
    doc_bytes = b"%PDF-1.7 MULTI RECIPIENT SEPARATION TEST\n" + b"CONFIDENTIAL BATCH " * 40

    evaluator = BlindForensicEvaluator(
        dlt_ledger=trained_orchestrator.dlt_ledger,
        lineage_index=trained_orchestrator.lineage_index,
        watermark_engine=trained_orchestrator.watermark_engine,
        expected_tenant_id="tenant_blind_eval_defense"
    )

    for recipient in ["alice", "bob", "charlie"]:
        res = trained_orchestrator.run_full_golden_pipeline(
            document_bytes=doc_bytes,
            document_name=f"Separation_{recipient}.pdf",
            leak_recipient_id=recipient
        )
        
        leak_artifact = res.decryption_records[recipient].watermarked_bytes
        eval_result = evaluator.evaluate_artifact(leak_artifact)
        assert eval_result.decision_state == DecisionState.ATTRIBUTED
        assert eval_result.attributed_recipient_id == recipient
        assert eval_result.is_signature_valid is True
        assert eval_result.is_ledger_inclusion_valid is True


def test_blind_unindexed_watermark_rejection(trained_orchestrator):
    """
    Tests an artifact embedded with a watermark token that was never registered/committed to DLT.
    Must yield INSUFFICIENT_EVIDENCE with no attribution.
    """
    # Embed a rogue watermark token not in ledger
    engine = DynamicWatermarkEngine()
    fake_doc = b"%PDF-1.7 UNREGISTERED SHADOW WATERMARK TEST\n" + b"ROGUE EMBED " * 50
    dyn_id = generate_dynamic_watermark(
        doc_root_hash="0" * 64,
        recipient_id="rogue_user",
        session_id="sess_fake_999",
        event_id="evt_fake_999",
        copy_id="copy_fake_999"
    )
    watermarked_fake = engine.embed_watermark(
        carrier_input=fake_doc,
        dynamic_identity=dyn_id,
        document_id="doc_fake_999",
        release_id="rel_fake_999",
        as_bytes=True
    )

    evaluator = BlindForensicEvaluator(
        dlt_ledger=trained_orchestrator.dlt_ledger,
        lineage_index=trained_orchestrator.lineage_index,
        watermark_engine=trained_orchestrator.watermark_engine,
        expected_tenant_id="tenant_blind_eval_defense"
    )

    eval_result = evaluator.evaluate_artifact(watermarked_fake)
    assert eval_result.watermark_detected is True
    assert eval_result.decision_state == DecisionState.INSUFFICIENT_EVIDENCE
    assert eval_result.attributed_recipient_id is None
    assert "NO_MATCHING_DLT_RECEIPT_CORRELATION" in eval_result.reason_codes
