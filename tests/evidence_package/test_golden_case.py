"""
Full End-to-End SIH Golden Case Test Suite.

Simulates the entire AegisTrace lifecycle from multi-recipient enrollment
through controlled decryption, watermark binding, permissioned DLT ledger commitment,
document leak, forensic extraction, lineage reconstruction, package export to ZIP,
and 100% independent offline verification under strict air-gapped zero-trust constraints.
"""

import base64
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from core.crypto.signatures import MLDSA65
from core.crypto.models import KeyPair
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
    TelemetryEvidenceObject,
    AttributionDecisionObject,
    DependencyEdge,
    TelemetryDependencyRelation,
    DecisionState,
    CustodyAction,
    ChainOfCustodyEvent
)
from core.evidence_package.builder import EvidencePackageBuilder
from core.evidence_package.verifier import OfflineEvidenceVerifier
from core.evidence_package.exporter import EvidencePackageExporter
from core.evidence_package.custody import ChainOfCustodyLedger
from core.ledger.dlt import build_merkle_tree


def test_sih_golden_case_end_to_end(tmp_path):
    """
    Executes the definitive SIH golden case test:
    Alice, Bob, Charlie enrolled -> Alice decrypts -> Document leaks ->
    Watermark extracted -> Attribution confirmed -> Package sealed & exported ->
    Offline verifier evaluates package from ZIP archive -> Status VERIFIED.
    """
    tenant_id = "tenant_sih_gov_in"
    case_id = "case_golden_leak_2026"
    doc_id = "classified_defense_whitepaper"
    rel_id = "rel_v2_final"

    # 1. Recipient Enrollment (Alice, Bob, Charlie)
    alice_kp = MLDSA65.generate_keypair()
    bob_kp = MLDSA65.generate_keypair()
    charlie_kp = MLDSA65.generate_keypair()

    alice_pk_b64 = base64.b64encode(alice_kp.public_key_bytes).decode("utf-8")
    bob_pk_b64 = base64.b64encode(bob_kp.public_key_bytes).decode("utf-8")
    charlie_pk_b64 = base64.b64encode(charlie_kp.public_key_bytes).decode("utf-8")

    # 2. DLT Validator Committee (Val-1, Val-2, Val-3)
    val1_kp = MLDSA65.generate_keypair()
    val2_kp = MLDSA65.generate_keypair()
    val3_kp = MLDSA65.generate_keypair()

    val1_pk_b64 = base64.b64encode(val1_kp.public_key_bytes).decode("utf-8")
    val2_pk_b64 = base64.b64encode(val2_kp.public_key_bytes).decode("utf-8")
    val3_pk_b64 = base64.b64encode(val3_kp.public_key_bytes).decode("utf-8")
    validators = {
        "val_delhi_01": val1_pk_b64,
        "val_mumbai_02": val2_pk_b64,
        "val_bengaluru_03": val3_pk_b64
    }

    # 3. Investigator / Examiner Keypair
    examiner_kp = MLDSA65.generate_keypair()

    now = datetime.now(timezone.utc)
    now_ts = now.isoformat()

    # --------------------------------------------------------------------------
    # EVIDENTIARY OBJECT ASSEMBLY
    # --------------------------------------------------------------------------

    # Object 1: Case Object
    case_obj = CaseObject(
        object_id=f"case_{case_id}",
        case_name="Operation Golden Shield Leak Attribution",
        investigator_id="inv_chief_forensic_examiner",
        description="Comprehensive forensic inquiry into unauthorized dissemination of Defense Whitepaper",
        classification_level="TOP_SECRET"
    )
    case_obj.seal_content_hash()

    # Object 2: Leaked Artifact
    leaked_bytes = b"TOP_SECRET_DEFENSE_DOCUMENT_BODY_WITH_ALICE_WATERMARK_CARRIER"
    art_hash = hashlib.sha256(leaked_bytes).hexdigest()
    art_obj = ArtifactEvidenceObject(
        object_id="art_seized_leak_pdf",
        artifact_category="LEAK",
        filename="unauthorized_leak.pdf",
        byte_size=len(leaked_bytes),
        sha256_digest=art_hash,
        document_id=doc_id,
        release_id=rel_id
    )
    art_obj.seal_content_hash()

    # Object 3: Watermark Evidence
    token_alice = "wm_token_alice_sih_9921"
    wm_obj = WatermarkEvidenceObject(
        object_id="wm_evidence_01",
        artifact_hash=art_hash,
        extraction_method="DYNAMIC_SPATIAL_DSSS_V1",
        extracted_token=token_alice,
        confidence_score=0.985,
        p_value=1.2e-9,
        detection_state="DETECTED",
        is_simulated=False,
        expected_recipient_id="officer_alice"
    )
    wm_obj.seal_content_hash()

    # Object 4: Decryption Receipt (Signed by Alice's ML-DSA-65 private key)
    session_id = "sess_alice_7701"
    key_id = "key_alice_pqc_v1"
    commit_hash = hashlib.sha256(f"{doc_id}:{token_alice}".encode("utf-8")).hexdigest()

    receipt_obj = DecryptionReceiptObject(
        object_id="rcpt_alice_decryption_01",
        receipt_id="rec_sih_alice_001",
        document_id=doc_id,
        release_id=rel_id,
        recipient_id="officer_alice",
        session_id=session_id,
        key_id=key_id,
        key_epoch=1,
        timestamp=now_ts,
        watermark_token=token_alice,
        watermark_commitment=commit_hash,
        recipient_signature_b64="",
        recipient_public_key_b64=alice_pk_b64
    )
    alice_sig = MLDSA65.sign(alice_kp.private_key_bytes, receipt_obj.construct_canonical_payload())
    receipt_obj.recipient_signature_b64 = base64.b64encode(alice_sig).decode("utf-8")
    receipt_obj.seal_content_hash()

    # Object 5: Recipient Identity Proof
    id_obj = RecipientIdentityProofObject(
        object_id="rip_officer_alice",
        recipient_id="officer_alice",
        key_id=key_id,
        algorithm="ML-DSA-65",
        key_epoch=1,
        public_key_b64=alice_pk_b64,
        activation_timestamp=(now - timedelta(days=30)).isoformat(),
        revocation_timestamp=None
    )
    id_obj.seal_content_hash()

    # Object 6: DLT Ledger Proof (Block 1042 with Merkle proof and Quorum)
    receipt_hash = hashlib.sha256(receipt_obj.content_hash.encode("utf-8")).hexdigest()
    # Build Merkle tree with receipt and 2 other receipts in block
    other_r1 = hashlib.sha256(b"receipt_bob").hexdigest()
    other_r2 = hashlib.sha256(b"receipt_charlie").hexdigest()
    m_root, proofs = build_merkle_tree([
        receipt_hash.encode("utf-8"),
        other_r1.encode("utf-8"),
        other_r2.encode("utf-8")
    ])
    audit_path = proofs[0].audit_path

    block_hash = "bh_" + hashlib.sha256(f"BLOCK:1042:{m_root}".encode("utf-8")).hexdigest()[:59]
    block_msg = f"AEGIS-BLOCK-CONFIRM:{block_hash}".encode("utf-8")

    val1_sig = base64.b64encode(MLDSA65.sign(val1_kp.private_key_bytes, block_msg)).decode("utf-8")
    val2_sig = base64.b64encode(MLDSA65.sign(val2_kp.private_key_bytes, block_msg)).decode("utf-8")
    val3_sig = base64.b64encode(MLDSA65.sign(val3_kp.private_key_bytes, block_msg)).decode("utf-8")

    ledger_obj = LedgerProofObject(
        object_id="lp_block_1042",
        receipt_id=receipt_obj.receipt_id,
        receipt_hash=receipt_hash,
        block_height=1042,
        block_hash=block_hash,
        previous_block_hash="bh_prev_" + "0" * 54,
        timestamp=now_ts,
        merkle_root=m_root,
        merkle_audit_path=audit_path,
        proposer_validator_id="val_delhi_01",
        proposer_signature_b64=val1_sig,
        quorum_signatures={
            "val_delhi_01": val1_sig,
            "val_mumbai_02": val2_sig,
            "val_bengaluru_03": val3_sig
        },
        quorum_threshold=2,
        authorized_validators=validators
    )
    ledger_obj.seal_content_hash()

    # Object 7: Lineage Evidence (Direct chain of custody, no downstream gap)
    lineage_obj = LineageEvidenceObject(
        object_id="lin_tree_defense_doc",
        document_id=doc_id,
        root_copy_id=f"root_{doc_id}",
        target_copy_id="copy_alice_terminal_export",
        boundary_state="LAST_KNOWN_HOLDER",
        last_known_holder="officer_alice",
        has_downstream_gap=False
    )
    lineage_obj.seal_content_hash()

    # Object 8: Telemetry Evidence (Corroborating session execution)
    telemetry_obj = TelemetryEvidenceObject(
        object_id="tel_session_alice_01",
        event_id="evt_decryption_session_7701",
        event_hash=hashlib.sha256(f"SESSION:{session_id}".encode("utf-8")).hexdigest(),
        timestamp=now_ts,
        source_system="AEGIS_ENCLAVE_AGENT",
        source_trust_level="HIGH_CONFIDENCE_ATTESTED",
        actor_id="officer_alice",
        device_id="workstation_delhi_44",
        dependency_relation=TelemetryDependencyRelation.CORROBORATES,
        relationship_details="Session logs corroborate decryption timestamp and client machine attestation"
    )
    telemetry_obj.seal_content_hash()

    # Object 9: Final Attribution Decision (ATTRIBUTED to Alice)
    decision_obj = AttributionDecisionObject(
        object_id="decision_golden_case_01",
        case_id=case_id,
        evidence_merkle_root="0" * 64,
        decision_state=DecisionState.ATTRIBUTED,
        attributed_principal_id="officer_alice",
        last_known_holder_id="officer_alice",
        confidence_score=0.985
    )
    decision_obj.seal_content_hash()

    # --------------------------------------------------------------------------
    # BUILD PACKAGE AND BIND DEPENDENCY GRAPH
    # --------------------------------------------------------------------------
    builder = EvidencePackageBuilder(case_id=case_id, tenant_id=tenant_id)
    for obj in [
        case_obj,
        art_obj,
        wm_obj,
        receipt_obj,
        id_obj,
        ledger_obj,
        lineage_obj,
        telemetry_obj
    ]:
        builder.add_object(obj)

    builder.set_decision(decision_obj)

    # Dependency Edges
    builder.add_edge(decision_obj.object_id, wm_obj.object_id, TelemetryDependencyRelation.DIRECTLY_SUPPORTS.value)
    builder.add_edge(decision_obj.object_id, receipt_obj.object_id, TelemetryDependencyRelation.DIRECTLY_SUPPORTS.value)
    builder.add_edge(decision_obj.object_id, lineage_obj.object_id, TelemetryDependencyRelation.DIRECTLY_SUPPORTS.value)
    builder.add_edge(decision_obj.object_id, ledger_obj.object_id, TelemetryDependencyRelation.CORROBORATES.value)
    builder.add_edge(decision_obj.object_id, telemetry_obj.object_id, TelemetryDependencyRelation.CORROBORATES.value)
    builder.add_edge(wm_obj.object_id, art_obj.object_id, TelemetryDependencyRelation.IS_DEPENDENT_ON.value)
    builder.add_edge(receipt_obj.object_id, id_obj.object_id, TelemetryDependencyRelation.IS_DEPENDENT_ON.value)

    # --------------------------------------------------------------------------
    # APPEND-ONLY CHAIN OF CUSTODY
    # --------------------------------------------------------------------------
    prev_h = ChainOfCustodyLedger.GENESIS_HASH
    timeline = [
        (CustodyAction.COLLECTED, art_obj.object_id, "Physical USB drive seized by military police", "mp_officer_101"),
        (CustodyAction.IMPORTED, art_obj.object_id, "Extracted forensic disk image ingested to air-gapped lab", "lab_tech_42"),
        (CustodyAction.ANALYZED, wm_obj.object_id, "DSSS watermark extracted with 98.5% confidence", "dr_forensic_analyst"),
        (CustodyAction.VERIFIED, receipt_obj.object_id, "Decryption receipt verified against Alice's enrolled ML-DSA-65 public key", "senior_examiner"),
        (CustodyAction.VERIFIED, ledger_obj.object_id, "Block 1042 verified via DLT 3-node validator consensus", "senior_examiner"),
        (CustodyAction.SEALED, decision_obj.object_id, "Attribution decision finalized and package sealed", "inv_chief_forensic_examiner")
    ]

    for action, obj_id, reason, op_id in timeline:
        ev = ChainOfCustodyLedger.create_event(
            action=action,
            evidence_object_id=obj_id,
            operator_identity=op_id,
            device_identity="lab_terminal_secure_01",
            resulting_evidence_hash="hash_" + hashlib.sha256(f"{action}:{obj_id}".encode("utf-8")).hexdigest()[:59],
            reason=reason,
            previous_custody_hash=prev_h,
            tenant_id=tenant_id
        )
        builder.add_custody_event(ev)
        prev_h = ChainOfCustodyLedger.compute_custody_event_hash(
            previous_hash=ev.previous_custody_hash,
            custody_event_id=ev.custody_event_id,
            evidence_object_id=ev.evidence_object_id,
            operator_identity=ev.operator_identity,
            device_identity=ev.device_identity,
            action=ev.action,
            timestamp=ev.timestamp,
            resulting_evidence_hash=ev.resulting_evidence_hash,
            tenant_id=ev.tenant_id,
            reason=ev.reason
        )

    # --------------------------------------------------------------------------
    # SIGN PACKAGE AND EXPORT TO ZIP
    # --------------------------------------------------------------------------
    package = builder.build_and_sign(
        signing_keypair=examiner_kp,
        signer_id="CHIEF_JUDICIAL_FORENSIC_EXAMINER"
    )

    zip_file = tmp_path / "golden_case_evidence_package.zip"
    EvidencePackageExporter.export_to_zip(package, zip_file)
    assert zip_file.exists()
    assert zip_file.stat().st_size > 0

    # --------------------------------------------------------------------------
    # INDEPENDENT OFFLINE AUDIT FROM ZIP ARCHIVE
    # --------------------------------------------------------------------------
    reloaded_pkg = EvidencePackageExporter.load_from_zip(zip_file)
    assert reloaded_pkg.manifest.package_id == package.manifest.package_id
    assert len(reloaded_pkg.objects) == len(package.objects)

    verifier = OfflineEvidenceVerifier(expected_tenant_id=tenant_id)
    result = verifier.verify_package(
        manifest=reloaded_pkg.manifest,
        signature=reloaded_pkg.signature,
        objects=reloaded_pkg.objects,
        edges=reloaded_pkg.edges,
        custody_chain=reloaded_pkg.custody_chain
    )

    # --------------------------------------------------------------------------
    # 12-PILLAR VERIFICATION ASSERTIONS
    # --------------------------------------------------------------------------
    assert result.overall_status == VerificationStatus.VERIFIED
    assert result.manifest_signature_valid is True
    assert result.merkle_root_valid is True
    assert result.object_hashes_valid is True
    assert result.dependency_graph_valid is True
    assert result.recipient_signature_valid is True
    assert result.historical_keys_valid is True
    assert result.ledger_proof_valid is True
    assert result.watermark_binding_valid is True
    assert result.lineage_valid is True
    assert result.custody_chain_valid is True
    assert result.decision_consistent is True
    assert len(result.errors) == 0
