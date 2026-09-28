"""
Tests for Independent Decryption Receipt Verification, Historical Keys, and DLT Ledger Proofs.
Verifies:
1. Canonical receipt payload reconstruction and independent ML-DSA-65 signature verification.
2. Historical key temporal boundary enforcement (before rotation/revocation vs after).
3. Offline DLT block Merkle inclusion proof and quorum consensus audit.
4. Tamper detection on receipts, signatures, block hashes, and quorum votes.
"""

import pytest
import base64
import hashlib
from datetime import datetime, timezone, timedelta

from core.crypto.signatures import MLDSA65
from core.evidence_package.models import (
    DecryptionReceiptObject,
    RecipientIdentityProofObject,
    LedgerProofObject
)
from core.ledger.dlt import build_merkle_tree
from core.evidence_package.verifier import OfflineEvidenceVerifier
from core.evidence_package.builder import EvidencePackageBuilder
from core.evidence_package.models import (
    ArtifactEvidenceObject,
    AttributionDecisionObject,
    DecisionState
)


def test_decryption_receipt_independent_signature_verification():
    rec_kp = MLDSA65.generate_keypair()
    rec_pub_b64 = base64.b64encode(rec_kp.public_key_bytes).decode("utf-8")

    now_ts = datetime.now(timezone.utc).isoformat()

    receipt = DecryptionReceiptObject(
        object_id="rcpt_alice_01",
        receipt_id="rec_001",
        document_id="doc_alpha",
        release_id="rel_001",
        recipient_id="rec_alice_4f9a",
        session_id="sess_001",
        key_id="kid_alice_k1",
        key_epoch=1,
        timestamp=now_ts,
        watermark_token="wm_token_alice_4f9a",
        watermark_commitment="commit_" + "c" * 57,
        recipient_signature_b64="",
        recipient_public_key_b64=rec_pub_b64
    )

    # Sign canonical payload
    payload_bytes = receipt.construct_canonical_payload()
    sig_bytes = MLDSA65.sign(rec_kp.private_key_bytes, payload_bytes)
    receipt.recipient_signature_b64 = base64.b64encode(sig_bytes).decode("utf-8")
    receipt.seal_content_hash()

    # Identity proof object
    id_proof = RecipientIdentityProofObject(
        object_id="rip_alice_01",
        recipient_id="rec_alice_4f9a",
        key_id="kid_alice_k1",
        public_key_b64=rec_pub_b64,
        key_epoch=1
    )
    id_proof.seal_content_hash()

    signer_kp = MLDSA65.generate_keypair()
    builder = EvidencePackageBuilder(case_id="case_receipt_01")
    builder.add_object(receipt)
    builder.add_object(id_proof)
    dec = AttributionDecisionObject(
        object_id="dec_01",
        case_id="case_receipt_01",
        evidence_merkle_root="0"*64,
        decision_state=DecisionState.ATTRIBUTED,
        attributed_principal_id="rec_alice_4f9a"
    )
    builder.set_decision(dec)
    builder.add_edge("dec_01", "rcpt_alice_01")

    pkg = builder.build_and_sign(signing_keypair=signer_kp)

    verifier = OfflineEvidenceVerifier()
    res = verifier.verify_package(pkg.manifest, pkg.signature, pkg.objects, pkg.edges)
    assert res.recipient_signature_valid is True
    assert res.historical_keys_valid is True


def test_historical_revocation_boundary_enforcement():
    rec_kp = MLDSA65.generate_keypair()
    rec_pub_b64 = base64.b64encode(rec_kp.public_key_bytes).decode("utf-8")

    t_rev = datetime.now(timezone.utc)
    t_rev_str = t_rev.isoformat()

    # Event 1: timestamp BEFORE revocation -> Valid
    t_valid = (t_rev - timedelta(hours=2)).isoformat()
    rcpt_valid = DecryptionReceiptObject(
        object_id="rcpt_valid",
        receipt_id="rec_valid",
        document_id="doc_alpha",
        release_id="rel_001",
        recipient_id="rec_alice_4f9a",
        session_id="sess_001",
        key_id="kid_alice_k1",
        key_epoch=1,
        timestamp=t_valid,
        watermark_token="wm_token_alice",
        watermark_commitment="c"*64,
        recipient_signature_b64="",
        recipient_public_key_b64=rec_pub_b64
    )
    sig_valid = MLDSA65.sign(rec_kp.private_key_bytes, rcpt_valid.construct_canonical_payload())
    rcpt_valid.recipient_signature_b64 = base64.b64encode(sig_valid).decode("utf-8")
    rcpt_valid.seal_content_hash()

    # Identity proof with revocation timestamp
    id_proof = RecipientIdentityProofObject(
        object_id="rip_alice_01",
        recipient_id="rec_alice_4f9a",
        key_id="kid_alice_k1",
        public_key_b64=rec_pub_b64,
        revocation_timestamp=t_rev_str
    )
    id_proof.seal_content_hash()

    signer_kp = MLDSA65.generate_keypair()
    b1 = EvidencePackageBuilder(case_id="case_hist_01")
    b1.add_object(rcpt_valid)
    b1.add_object(id_proof)
    dec1 = AttributionDecisionObject(object_id="dec_1", case_id="case_hist_01", evidence_merkle_root="0"*64, decision_state=DecisionState.ATTRIBUTED, attributed_principal_id="rec_alice_4f9a")
    b1.set_decision(dec1)
    b1.add_edge("dec_1", "rcpt_valid")
    pkg1 = b1.build_and_sign(signer_kp)

    verifier = OfflineEvidenceVerifier()
    res1 = verifier.verify_package(pkg1.manifest, pkg1.signature, pkg1.objects, pkg1.edges)
    assert res1.historical_keys_valid is True

    # Event 2: timestamp AFTER revocation -> Rejected
    t_invalid = (t_rev + timedelta(hours=1)).isoformat()
    rcpt_invalid = DecryptionReceiptObject(
        object_id="rcpt_invalid",
        receipt_id="rec_invalid",
        document_id="doc_alpha",
        release_id="rel_001",
        recipient_id="rec_alice_4f9a",
        session_id="sess_002",
        key_id="kid_alice_k1",
        key_epoch=1,
        timestamp=t_invalid,
        watermark_token="wm_token_alice_post",
        watermark_commitment="c"*64,
        recipient_signature_b64="",
        recipient_public_key_b64=rec_pub_b64
    )
    sig_invalid = MLDSA65.sign(rec_kp.private_key_bytes, rcpt_invalid.construct_canonical_payload())
    rcpt_invalid.recipient_signature_b64 = base64.b64encode(sig_invalid).decode("utf-8")
    rcpt_invalid.seal_content_hash()

    b2 = EvidencePackageBuilder(case_id="case_hist_02")
    b2.add_object(rcpt_invalid)
    b2.add_object(id_proof)
    dec2 = AttributionDecisionObject(object_id="dec_2", case_id="case_hist_02", evidence_merkle_root="0"*64, decision_state=DecisionState.ATTRIBUTED, attributed_principal_id="rec_alice_4f9a")
    b2.set_decision(dec2)
    b2.add_edge("dec_2", "rcpt_invalid")
    pkg2 = b2.build_and_sign(signer_kp)

    res2 = verifier.verify_package(pkg2.manifest, pkg2.signature, pkg2.objects, pkg2.edges)
    assert res2.historical_keys_valid is False
    assert any("POST_REVOCATION_REJECTION" in err for err in res2.errors)


def test_offline_dlt_ledger_proof_verification():
    val1_kp = MLDSA65.generate_keypair()
    val2_kp = MLDSA65.generate_keypair()
    val1_pub_b64 = base64.b64encode(val1_kp.public_key_bytes).decode("utf-8")
    val2_pub_b64 = base64.b64encode(val2_kp.public_key_bytes).decode("utf-8")

    receipt_hash = "f" * 64
    root, proofs = build_merkle_tree([receipt_hash.encode("utf-8")])
    audit_path = proofs[0].audit_path if proofs else []

    block_hash = "bh_" + "b" * 61
    block_msg = f"AEGIS-BLOCK-CONFIRM:{block_hash}".encode("utf-8")

    p_sig = base64.b64encode(MLDSA65.sign(val1_kp.private_key_bytes, block_msg)).decode("utf-8")
    v2_sig = base64.b64encode(MLDSA65.sign(val2_kp.private_key_bytes, block_msg)).decode("utf-8")

    lp = LedgerProofObject(
        object_id="lp_01",
        receipt_id="rec_001",
        receipt_hash=receipt_hash,
        block_height=5,
        block_hash=block_hash,
        previous_block_hash="prev_" + "0" * 59,
        timestamp=datetime.now(timezone.utc).isoformat(),
        merkle_root=root,
        merkle_audit_path=audit_path,
        proposer_validator_id="v1",
        proposer_signature_b64=p_sig,
        quorum_signatures={"v1": p_sig, "v2": v2_sig},
        quorum_threshold=2,
        authorized_validators={"v1": val1_pub_b64, "v2": val2_pub_b64}
    )
    lp.seal_content_hash()

    signer_kp = MLDSA65.generate_keypair()
    builder = EvidencePackageBuilder(case_id="case_ledger_01")
    builder.add_object(lp)
    dec = AttributionDecisionObject(object_id="dec_01", case_id="case_ledger_01", evidence_merkle_root="0"*64, decision_state=DecisionState.NO_SIGNAL)
    builder.set_decision(dec)
    builder.add_edge("dec_01", "lp_01")
    pkg = builder.build_and_sign(signer_kp)

    verifier = OfflineEvidenceVerifier()
    res = verifier.verify_package(pkg.manifest, pkg.signature, pkg.objects, pkg.edges)
    assert res.ledger_proof_valid is True

    # Tampering with block hash causes invalid proposer signature and invalid quorum votes
    lp_tampered = lp.model_copy(deep=True)
    lp_tampered.block_hash = "tampered_block_hash"
    lp_tampered.seal_content_hash()

    b_tampered = EvidencePackageBuilder(case_id="case_ledger_02")
    b_tampered.add_object(lp_tampered)
    b_tampered.set_decision(dec)
    b_tampered.add_edge("dec_01", "lp_01")
    pkg_tampered = b_tampered.build_and_sign(signer_kp)

    res_tampered = verifier.verify_package(pkg_tampered.manifest, pkg_tampered.signature, pkg_tampered.objects, pkg_tampered.edges)
    assert res_tampered.ledger_proof_valid is False
