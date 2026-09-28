"""
Tests for AegisTrace Independent Offline Evidence Verifier and CLI.

Validates that an independent offline verifier executes completely without
network access, database access, or server dependencies, producing authoritative
forensic verdicts.
"""

import os
import sys
import json
import base64
import hashlib
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta

import pytest

from core.crypto.signatures import MLDSA65
from core.crypto.models import KeyPair
from core.evidence_package.models import (
    BaseEvidenceObject,
    EvidenceObjectType,
    VerificationStatus,
    VerificationResult,
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
    CustodyAction,
    ChainOfCustodyEvent
)
from core.evidence_package.builder import EvidencePackageBuilder
from core.evidence_package.verifier import OfflineEvidenceVerifier
from core.evidence_package.exporter import EvidencePackageExporter
from core.evidence_package.custody import ChainOfCustodyLedger
from core.ledger.dlt import build_merkle_tree


def create_sample_valid_package_data():
    """Helper to assemble a fully valid, self-contained evidence package."""
    tenant_id = "tenant-defense-01"
    case_id = "case_2026_audit_001"
    doc_id = "classified_brief_v2"
    rel_id = "rel_001"
    recipient_id = "rec_officer_alice"

    # Investigator keypair for package signing
    inv_kp = MLDSA65.generate_keypair()
    inv_pk_b64 = base64.b64encode(inv_kp.public_key_bytes).decode("utf-8")

    # Recipient keypair for decryption receipt
    rec_kp = MLDSA65.generate_keypair()
    rec_pk_b64 = base64.b64encode(rec_kp.public_key_bytes).decode("utf-8")
    key_id = "key_alice_mldsa_01"

    # Validator keypairs for ledger proof
    val1_kp = MLDSA65.generate_keypair()
    val2_kp = MLDSA65.generate_keypair()
    val1_pk_b64 = base64.b64encode(val1_kp.public_key_bytes).decode("utf-8")
    val2_pk_b64 = base64.b64encode(val2_kp.public_key_bytes).decode("utf-8")

    now = datetime.now(timezone.utc)
    ts_str = now.isoformat()

    # 1. Case Object
    case_obj = CaseObject(
        object_id=f"case_{case_id}",
        case_name="Operation Amber Leak Investigation",
        investigator_id="inv-lead-forensics",
        description="Air-gapped verification audit test",
        classification_level="SECRET"
    )
    case_obj.seal_content_hash()

    # 2. Artifact Evidence
    artifact_content = b"PDF_WATERMARKED_LEAK_BODY_BYTES_VERIFIER"
    art_hash = hashlib.sha256(artifact_content).hexdigest()
    art_obj = ArtifactEvidenceObject(
        object_id="art_leak_pdf",
        artifact_category="LEAK",
        filename="leak_sample.pdf",
        byte_size=len(artifact_content),
        sha256_digest=art_hash,
        document_id=doc_id,
        release_id=rel_id
    )
    art_obj.seal_content_hash()

    # 3. Watermark Evidence
    token = "wm_token_alice_alpha"
    wm_obj = WatermarkEvidenceObject(
        object_id="wm_extracted_01",
        artifact_hash=art_hash,
        extracted_token=token,
        confidence_score=0.98,
        expected_recipient_id=recipient_id,
        detection_state="DETECTED"
    )
    wm_obj.seal_content_hash()

    # 4. Decryption Receipt
    commit = hashlib.sha256(f"{doc_id}:{recipient_id}:{token}".encode("utf-8")).hexdigest()
    receipt_obj = DecryptionReceiptObject(
        object_id="receipt_decrypt_alice",
        receipt_id="rec-alice-101",
        document_id=doc_id,
        release_id=rel_id,
        recipient_id=recipient_id,
        session_id="sess-101",
        key_id=key_id,
        key_epoch=1,
        timestamp=ts_str,
        watermark_token=token,
        watermark_commitment=commit,
        recipient_signature_b64="",
        recipient_public_key_b64=rec_pk_b64
    )
    canonical_receipt_payload = receipt_obj.construct_canonical_payload()
    rec_sig = MLDSA65.sign(rec_kp.private_key_bytes, canonical_receipt_payload)
    receipt_obj.recipient_signature_b64 = base64.b64encode(rec_sig).decode("utf-8")
    receipt_obj.seal_content_hash()

    # 5. Recipient Identity Proof
    id_obj = RecipientIdentityProofObject(
        object_id=f"idproof_{recipient_id}",
        recipient_id=recipient_id,
        key_id=key_id,
        public_key_b64=rec_pk_b64,
        key_epoch=1,
        activation_timestamp=(now - timedelta(days=10)).isoformat(),
        revocation_timestamp=None
    )
    id_obj.seal_content_hash()

    # 6. Ledger Proof
    rec_hash = hashlib.sha256(receipt_obj.content_hash.encode("utf-8")).hexdigest()
    merkle_root, proofs = build_merkle_tree([rec_hash.encode("utf-8")])
    audit_path = proofs[0].audit_path if proofs else []

    block_hash = "bh_" + hashlib.sha256(f"BLOCK:5001:{merkle_root}".encode("utf-8")).hexdigest()[:59]
    block_msg = f"AEGIS-BLOCK-CONFIRM:{block_hash}".encode("utf-8")
    val1_sig = base64.b64encode(MLDSA65.sign(val1_kp.private_key_bytes, block_msg)).decode("utf-8")
    val2_sig = base64.b64encode(MLDSA65.sign(val2_kp.private_key_bytes, block_msg)).decode("utf-8")

    ledger_obj = LedgerProofObject(
        object_id="ledger_proof_block_5001",
        receipt_id="rec-alice-101",
        receipt_hash=rec_hash,
        block_height=5001,
        block_hash=block_hash,
        previous_block_hash="prev_" + "0" * 59,
        timestamp=ts_str,
        merkle_root=merkle_root,
        merkle_audit_path=audit_path,
        proposer_validator_id="val-01",
        proposer_signature_b64=val1_sig,
        quorum_signatures={"val-01": val1_sig, "val-02": val2_sig},
        quorum_threshold=2,
        authorized_validators={"val-01": val1_pk_b64, "val-02": val2_pk_b64}
    )
    ledger_obj.seal_content_hash()

    # 7. Lineage Evidence
    lineage_obj = LineageEvidenceObject(
        object_id="lineage_tree_01",
        document_id=doc_id,
        root_copy_id=f"root_{doc_id}",
        target_copy_id="copy_alice_export",
        has_downstream_gap=False,
        last_known_holder=recipient_id
    )
    lineage_obj.seal_content_hash()

    # 8. Attribution Decision
    decision_obj = AttributionDecisionObject(
        object_id="decision_final_01",
        case_id=case_id,
        evidence_merkle_root="0" * 64,
        decision_state=DecisionState.ATTRIBUTED,
        attributed_principal_id=recipient_id,
        confidence_score=0.98
    )
    decision_obj.seal_content_hash()

    # Assemble objects & edges
    builder = EvidencePackageBuilder(
        case_id=case_id,
        tenant_id=tenant_id
    )
    for o in [case_obj, art_obj, wm_obj, receipt_obj, id_obj, ledger_obj, lineage_obj]:
        builder.add_object(o)

    builder.set_decision(decision_obj)

    # Dependency DAG edges
    builder.add_edge(decision_obj.object_id, wm_obj.object_id, TelemetryDependencyRelation.DIRECTLY_SUPPORTS.value)
    builder.add_edge(decision_obj.object_id, receipt_obj.object_id, TelemetryDependencyRelation.DIRECTLY_SUPPORTS.value)
    builder.add_edge(decision_obj.object_id, ledger_obj.object_id, TelemetryDependencyRelation.CORROBORATES.value)
    builder.add_edge(wm_obj.object_id, art_obj.object_id, TelemetryDependencyRelation.IS_DEPENDENT_ON.value)
    builder.add_edge(receipt_obj.object_id, id_obj.object_id, TelemetryDependencyRelation.IS_DEPENDENT_ON.value)

    # Custody chain
    events = []
    prev_h = ChainOfCustodyLedger.GENESIS_HASH

    ev_specs = [
        (CustodyAction.COLLECTED, art_obj.object_id, "Physical artifact recovered"),
        (CustodyAction.ANALYZED, wm_obj.object_id, "Watermark extracted"),
        (CustodyAction.SEALED, decision_obj.object_id, "Package sealed")
    ]
    for act, obj_id, reason in ev_specs:
        ev = ChainOfCustodyLedger.create_event(
            action=act,
            evidence_object_id=obj_id,
            operator_identity="inv-lead-forensics",
            device_identity="dev-secure-01",
            resulting_evidence_hash="res_" + "a" * 60,
            reason=reason,
            previous_custody_hash=prev_h,
            tenant_id=tenant_id
        )
        events.append(ev)
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

    package = builder.build_and_sign(
        signing_keypair=inv_kp,
        signer_id="OFFICIAL_FORENSIC_EXAMINER"
    )

    return package, tenant_id


def test_offline_verifier_full_12_pillars_pass():
    """Verify that OfflineEvidenceVerifier autonomously confirms all 12 pillars."""
    package, tenant_id = create_sample_valid_package_data()

    verifier = OfflineEvidenceVerifier(expected_tenant_id=tenant_id)
    result = verifier.verify_package(
        manifest=package.manifest,
        signature=package.signature,
        objects=package.objects,
        edges=package.edges,
        custody_chain=package.custody_chain
    )

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


def test_standalone_cli_execution_directory_and_zip(tmp_path):
    """
    Test the standalone CLI tool aegistrace_verify.py via subprocess.
    Tests directory loading, zip loading, JSON reporting, and tenant isolation flags.
    """
    package, tenant_id = create_sample_valid_package_data()

    # 1. Export as Directory
    dir_path = tmp_path / "pkg_dir"
    EvidencePackageExporter.export_to_directory(package, dir_path)

    # 2. Export as Zip Archive
    zip_path = tmp_path / "pkg_archive.zip"
    EvidencePackageExporter.export_to_zip(package, zip_path)

    cli_script = Path(__file__).resolve().parents[2] / "aegistrace_verify.py"
    assert cli_script.exists()

    # Test directory verification via CLI
    proc_dir = subprocess.run(
        [sys.executable, str(cli_script), str(dir_path), "--tenant", tenant_id],
        capture_output=True,
        text=True
    )
    assert proc_dir.returncode == 0, f"STDOUT: {proc_dir.stdout}\nSTDERR: {proc_dir.stderr}"
    assert "Overall Status:       VERIFIED" in proc_dir.stdout
    assert "Manifest Signature:   VALID (ML-DSA-65)" in proc_dir.stdout

    # Test zip verification with --json flag
    proc_zip = subprocess.run(
        [sys.executable, str(cli_script), str(zip_path), "--tenant", tenant_id, "--json"],
        capture_output=True,
        text=True
    )
    assert proc_zip.returncode == 0, f"STDOUT: {proc_zip.stdout}\nSTDERR: {proc_zip.stderr}"
    json_output = json.loads(proc_zip.stdout)
    assert json_output["overall_status"] == "VERIFIED"
    assert json_output["manifest_signature_valid"] is True
    assert json_output["merkle_root_valid"] is True

    # Test tenant isolation violation via CLI
    proc_tenant_fail = subprocess.run(
        [sys.executable, str(cli_script), str(zip_path), "--tenant", "foreign-hostile-tenant"],
        capture_output=True,
        text=True
    )
    assert proc_tenant_fail.returncode == 4  # INVALID
    assert "TENANT_ISOLATION_VIOLATION" in proc_tenant_fail.stdout or "TENANT_ISOLATION_VIOLATION" in proc_tenant_fail.stderr
