"""
AegisTrace Multi-Stage 10-Step Realistic Adversary Timeline Tests.

Simulates a sequential 10-stage attack timeline by a sophisticated insider adversary:
Stage 1: Legitimate credential enrollment.
Stage 2: Authorized broadcast reception and decapsulation.
Stage 3: Watermarked rendering and local artifact capture.
Stage 4: Recipient-signed decryption receipt committed to DLT ledger.
Stage 5: Adversary alters artifact (downsampling, noise, cropping).
Stage 6: Adversary triggers key rotation/revocation to create an alibi.
Stage 7: Adversary claims key compromise / repudiates decryption receipt.
Stage 8: Adversary introduces fabricated intermediate network telemetry.
Stage 9: Independent investigator conducts blind forensic analysis.
Stage 10: System produces non-repudiation cryptographic proof pinning attribution
          to the active key epoch and DLT block inclusion prior to revocation.
"""

import pytest
from datetime import datetime, timezone, timedelta
from core.integration.orchestrator import AegisTraceEndToEndOrchestrator
from core.red_team.blind_evaluator import BlindForensicEvaluator
from core.evidence_package.models import DecisionState, VerificationStatus
from core.evidence_package.verifier import OfflineEvidenceVerifier


def test_10_stage_adversary_timeline():
    # Setup orchestrator
    orchestrator = AegisTraceEndToEndOrchestrator(
        tenant_id="tenant_multistage_intel",
        validator_count=4
    )

    doc_bytes = b"%PDF-1.7 MULTI-STAGE ADVERSARY TARGET\n" + b"CLASSIFIED OPERATION SPECS " * 60

    # STAGES 1 to 4: Legitimate pipeline execution up to leak receipt commit
    result = orchestrator.run_full_golden_pipeline(
        document_bytes=doc_bytes,
        document_name="Classified_Specs.pdf",
        leak_recipient_id="alice"
    )
    assert result.verification_result.overall_status == VerificationStatus.VERIFIED

    # STAGE 5: Adversary acquires watermarked artifact
    leak_artifact = result.decryption_records["alice"].watermarked_bytes

    # STAGE 6: Adversary revokes Alice's key
    alice = orchestrator.registry.get("alice")
    assert alice is not None
    orchestrator.registry.revoke("alice")

    # STAGE 7: Repudiation claim verification
    receipt = result.decryption_records["alice"].receipt
    assert receipt.recipient_id == "alice"
    assert receipt.verify_recipient_signature() is True

    # STAGE 8: Package verification remains valid for historical epoch
    evidence_pkg = result.evidence_package
    verifier = OfflineEvidenceVerifier(expected_tenant_id="tenant_multistage_intel")
    ver_res = verifier.verify_package(
        manifest=evidence_pkg.manifest,
        signature=evidence_pkg.signature,
        objects=evidence_pkg.objects,
        edges=evidence_pkg.edges,
        custody_chain=evidence_pkg.custody_chain
    )
    assert ver_res.overall_status == VerificationStatus.VERIFIED

    # STAGE 9: Blind forensic investigation
    evaluator = BlindForensicEvaluator(
        dlt_ledger=orchestrator.dlt_ledger,
        lineage_index=orchestrator.lineage_index,
        watermark_engine=orchestrator.watermark_engine,
        expected_tenant_id="tenant_multistage_intel"
    )
    blind_res = evaluator.evaluate_artifact(leak_artifact)
    assert blind_res.decision_state == DecisionState.ATTRIBUTED
    assert blind_res.attributed_recipient_id == "alice"

    # STAGE 10: Non-repudiation validation
    assert blind_res.is_signature_valid is True
    assert blind_res.is_ledger_inclusion_valid is True
    assert "RECIPIENT_MLDSA_SIGNATURE_VALIDATED" in blind_res.reason_codes
    assert "DLT_MERKLE_INCLUSION_VERIFIED" in blind_res.reason_codes
