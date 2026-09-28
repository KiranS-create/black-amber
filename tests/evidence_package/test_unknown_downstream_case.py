"""
Tests for Unknown Downstream Recipient and Unmonitored Transition Handling.

Verifies the fundamental forensic invariant of AegisTrace:
When a document transitions beyond the controlled perimeter into an unmonitored
medium, the system:
1. Strictly preserves the LAST_KNOWN_HOLDER boundary.
2. Formally notes DOWNSTREAM_GAP in lineage evidence.
3. Strictly refuses to fabricate or speculate on downstream identities.
4. Correctly reaches ABSTAINED or INSUFFICIENT_EVIDENCE forensic verdicts.
5. Independent offline verifier validates that conclusion matches evidence without over-attribution.
"""

import base64
import hashlib
from datetime import datetime, timezone, timedelta

import pytest

from core.crypto.signatures import MLDSA65
from core.evidence_package.models import (
    BaseEvidenceObject,
    EvidenceObjectType,
    VerificationStatus,
    CaseObject,
    ArtifactEvidenceObject,
    WatermarkEvidenceObject,
    DecryptionReceiptObject,
    RecipientIdentityProofObject,
    LedgerProofObject,
    LineageEvidenceObject,
    AttributionDecisionObject,
    DependencyEdge,
    TelemetryDependencyRelation,
    DecisionState,
    CustodyAction
)
from core.evidence_package.builder import EvidencePackageBuilder
from core.evidence_package.verifier import OfflineEvidenceVerifier
from core.evidence_package.custody import ChainOfCustodyLedger
from core.ledger.dlt import build_merkle_tree


def test_unknown_downstream_gap_properly_preserved_as_last_known_holder():
    """
    Scenario: Alice decrypted a file, watermarked with Alice's token.
    The document was subsequently transferred off-network via unmonitored USB or camera capture.
    Forensic investigation finds Alice's watermark, but recognizes an unmonitored downstream gap.
    The system correctly documents Alice as LAST_KNOWN_HOLDER, flags has_downstream_gap=True,
    and sets decision_state to ABSTAINED (or INSUFFICIENT_EVIDENCE) with last_known_holder_id="officer_alice"
    and attributed_principal_id=None.
    """
    tenant_id = "tenant_hq_security"
    case_id = "case_downstream_gap_01"
    doc_id = "strategic_plan_2026"
    rel_id = "rel_v1"
    alice_id = "officer_alice"

    alice_kp = MLDSA65.generate_keypair()
    alice_pk_b64 = base64.b64encode(alice_kp.public_key_bytes).decode("utf-8")
    examiner_kp = MLDSA65.generate_keypair()

    val_kp = MLDSA65.generate_keypair()
    val_pk_b64 = base64.b64encode(val_kp.public_key_bytes).decode("utf-8")

    now = datetime.now(timezone.utc)
    ts_str = now.isoformat()

    # 1. Case Object
    case_obj = CaseObject(
        object_id=f"case_{case_id}",
        case_name="Unmonitored USB Extraction Probe",
        investigator_id="examiner_404",
        description="Leak discovered with clear watermark but missing downstream device lineage",
        classification_level="SECRET"
    )
    case_obj.seal_content_hash()

    # 2. Artifact Object
    art_content = b"DISCOVERED_LEAK_BODY_BYTES_WITH_GAP"
    art_hash = hashlib.sha256(art_content).hexdigest()
    art_obj = ArtifactEvidenceObject(
        object_id="art_leak_gap",
        artifact_category="LEAK",
        filename="leak_external.pdf",
        byte_size=len(art_content),
        sha256_digest=art_hash,
        document_id=doc_id,
        release_id=rel_id
    )
    art_obj.seal_content_hash()

    # 3. Watermark Evidence (Alice's watermark detected)
    token_alice = "wm_token_alice_gap_01"
    wm_obj = WatermarkEvidenceObject(
        object_id="wm_gap_01",
        artifact_hash=art_hash,
        extracted_token=token_alice,
        confidence_score=0.96,
        expected_recipient_id=alice_id,
        detection_state="DETECTED"
    )
    wm_obj.seal_content_hash()

    # 4. Decryption Receipt (Alice decrypted legitimately)
    commit = hashlib.sha256(f"{doc_id}:{token_alice}".encode("utf-8")).hexdigest()
    receipt_obj = DecryptionReceiptObject(
        object_id="rcpt_alice_gap",
        receipt_id="rec_gap_01",
        document_id=doc_id,
        release_id=rel_id,
        recipient_id=alice_id,
        session_id="sess_alice_gap",
        key_id="key_alice_k1",
        key_epoch=1,
        timestamp=ts_str,
        watermark_token=token_alice,
        watermark_commitment=commit,
        recipient_signature_b64="",
        recipient_public_key_b64=alice_pk_b64
    )
    sig = MLDSA65.sign(alice_kp.private_key_bytes, receipt_obj.construct_canonical_payload())
    receipt_obj.recipient_signature_b64 = base64.b64encode(sig).decode("utf-8")
    receipt_obj.seal_content_hash()

    # 5. Identity Proof
    id_obj = RecipientIdentityProofObject(
        object_id=f"idproof_{alice_id}",
        recipient_id=alice_id,
        key_id="key_alice_k1",
        public_key_b64=alice_pk_b64,
        key_epoch=1,
        activation_timestamp=(now - timedelta(days=20)).isoformat(),
        revocation_timestamp=None
    )
    id_obj.seal_content_hash()

    # 6. Ledger Proof
    rec_h = hashlib.sha256(receipt_obj.content_hash.encode("utf-8")).hexdigest()
    root, proofs = build_merkle_tree([rec_h.encode("utf-8")])
    audit_path = proofs[0].audit_path if proofs else []
    b_hash = "bh_" + hashlib.sha256(f"BLOCK:77:{root}".encode("utf-8")).hexdigest()[:59]
    b_msg = f"AEGIS-BLOCK-CONFIRM:{b_hash}".encode("utf-8")
    val_sig = base64.b64encode(MLDSA65.sign(val_kp.private_key_bytes, b_msg)).decode("utf-8")

    ledger_obj = LedgerProofObject(
        object_id="lp_gap_block_77",
        receipt_id=receipt_obj.receipt_id,
        receipt_hash=rec_h,
        block_height=77,
        block_hash=b_hash,
        previous_block_hash="prev_" + "0" * 59,
        timestamp=ts_str,
        merkle_root=root,
        merkle_audit_path=audit_path,
        proposer_validator_id="val_01",
        proposer_signature_b64=val_sig,
        quorum_signatures={"val_01": val_sig},
        quorum_threshold=1,
        authorized_validators={"val_01": val_pk_b64}
    )
    ledger_obj.seal_content_hash()

    # 7. Lineage Evidence with DOWNSTREAM GAP
    lineage_obj = LineageEvidenceObject(
        object_id="lin_gap_tree",
        document_id=doc_id,
        root_copy_id=f"root_{doc_id}",
        target_copy_id="copy_alice_terminal",
        boundary_state="LAST_KNOWN_HOLDER",
        last_known_holder=alice_id,
        has_downstream_gap=True,
        missing_parent_id="unknown_external_recipient_device"
    )
    lineage_obj.seal_content_hash()

    # 8. Attribution Decision: ABSTAINED on final culprit, preserving LAST_KNOWN_HOLDER
    decision_obj = AttributionDecisionObject(
        object_id="dec_gap_final",
        case_id=case_id,
        evidence_merkle_root="0" * 64,
        decision_state=DecisionState.ABSTAINED,
        attributed_principal_id=None,  # NEVER fabricate downstream principal
        last_known_holder_id=alice_id,
        confidence_score=0.96
    )
    decision_obj.seal_content_hash()

    # Assemble Package
    builder = EvidencePackageBuilder(case_id=case_id, tenant_id=tenant_id)
    for o in [case_obj, art_obj, wm_obj, receipt_obj, id_obj, ledger_obj, lineage_obj]:
        builder.add_object(o)
    builder.set_decision(decision_obj)

    builder.add_edge(decision_obj.object_id, wm_obj.object_id, TelemetryDependencyRelation.DIRECTLY_SUPPORTS.value)
    builder.add_edge(decision_obj.object_id, lineage_obj.object_id, TelemetryDependencyRelation.DIRECTLY_SUPPORTS.value)
    builder.add_edge(decision_obj.object_id, receipt_obj.object_id, TelemetryDependencyRelation.CORROBORATES.value)
    builder.add_edge(wm_obj.object_id, art_obj.object_id, TelemetryDependencyRelation.IS_DEPENDENT_ON.value)
    builder.add_edge(receipt_obj.object_id, id_obj.object_id, TelemetryDependencyRelation.IS_DEPENDENT_ON.value)

    package = builder.build_and_sign(
        signing_keypair=examiner_kp,
        signer_id="INSPECTOR_GENERAL_OFFICE"
    )

    verifier = OfflineEvidenceVerifier(expected_tenant_id=tenant_id)
    result = verifier.verify_package(
        manifest=package.manifest,
        signature=package.signature,
        objects=package.objects,
        edges=package.edges,
        custody_chain=package.custody_chain
    )

    # Invariants
    assert result.overall_status == VerificationStatus.VERIFIED
    assert result.lineage_valid is True
    assert result.decision_consistent is True
    assert len(result.errors) == 0


def test_downstream_gap_fails_if_last_known_holder_missing():
    """Verify that a lineage with has_downstream_gap=True without last_known_holder fails verification."""
    tenant_id = "tenant_test_gap"
    case_id = "case_gap_fail"

    examiner_kp = MLDSA65.generate_keypair()

    # Lineage with gap but no last_known_holder
    bad_lineage = LineageEvidenceObject(
        object_id="lin_bad_gap",
        document_id="doc_x",
        root_copy_id="root_x",
        boundary_state="LAST_KNOWN_HOLDER",
        last_known_holder=None,  # Invalid: gap exists without recording last known holder!
        has_downstream_gap=True
    )
    bad_lineage.seal_content_hash()

    decision = AttributionDecisionObject(
        object_id="dec_01",
        case_id=case_id,
        evidence_merkle_root="0" * 64,
        decision_state=DecisionState.ABSTAINED,
        attributed_principal_id=None
    )
    decision.seal_content_hash()

    builder = EvidencePackageBuilder(case_id=case_id, tenant_id=tenant_id)
    builder.add_object(bad_lineage)
    builder.set_decision(decision)
    builder.add_edge("dec_01", "lin_bad_gap")

    pkg = builder.build_and_sign(signing_keypair=examiner_kp)

    verifier = OfflineEvidenceVerifier(expected_tenant_id=tenant_id)
    res = verifier.verify_package(pkg.manifest, pkg.signature, pkg.objects, pkg.edges)

    assert res.lineage_valid is False
    assert any("Lineage with downstream gap must preserve last_known_holder" in err for err in res.errors)
