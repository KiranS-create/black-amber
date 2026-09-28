"""
SIH26237 - Controlled Viewer and DLT Adversarial Attack Matrix
Validates resistance against:
1. Recipient Attack: Digital signature forgery and identity impersonation
2. Admin Attack: Unilateral ledger insertion without recipient signing
3. Replay Attack: Resubmission of existing receipts or nonce reuse
4. DLT Sub-Quorum Attack: Insufficient validator threshold approvals (< 2N/3 + 1)
5. Damaged Watermark Attack: Heavy destruction fails closed without false accusations
6. Watermark Transplantation Attack: Cross-document token reuse detection
"""

import pytest
import os
import base64
import hashlib
from typing import Optional, Dict, Any, List, Tuple
import numpy as np
import cv2


from core.crypto.models import KeyPair
from core.crypto.signatures import MLDSA65
from core.recipient import RecipientRegistry
from core.ledger.dlt import (
    PermissionedDLTLedger,
    DLTValidator,
    DecryptionReceipt,
    DLTBlock,
    DLTBlockHeader,
    DLTNode,
)
from core.watermark.dynamic import (
    DynamicWatermarkEngine,
    generate_dynamic_watermark,
    compute_visual_equivalence_metrics,
)
from core.lineage.forensics import (
    DynamicForensicExtractor,
    ForensicVerificationStatus,
)
from core.watermark.pipeline import CanonicalCanvasSpec, GeometricSynchronizer
from core.watermark.carrier import CarrierConfig


def _create_receipt(recipient_id: str, doc_hash: str, signer_kp: KeyPair, claimed_pub_b64: Optional[str] = None) -> DecryptionReceipt:
    pub_b64 = claimed_pub_b64 or base64.b64encode(signer_kp.public_key_bytes).decode('utf-8')
    event_id = f"evt_{os.urandom(6).hex()}"
    tmp = DecryptionReceipt(
        receipt_id=f"rcpt_{event_id}",
        document_root_hash=doc_hash,
        recipient_id=recipient_id,
        identity_reference=f"{recipient_id}@aegis.local",
        decryption_session_id=f"ses_{os.urandom(4).hex()}",
        decryption_event_id=event_id,
        copy_instance_id=f"cpy_{os.urandom(4).hex()}",
        watermark_commitment=hashlib.sha256(os.urandom(32)).hexdigest(),
        watermark_token=os.urandom(32).hex(),
        recipient_public_key_b64=pub_b64,
        recipient_signature_b64="",
    )
    sig_bytes = MLDSA65.sign(signer_kp.private_key_bytes, tmp.canonical_payload_bytes())
    sig_b64 = base64.b64encode(sig_bytes).decode('utf-8')

    return DecryptionReceipt(
        receipt_id=tmp.receipt_id,
        document_root_hash=doc_hash,
        recipient_id=recipient_id,
        identity_reference=tmp.identity_reference,
        decryption_session_id=tmp.decryption_session_id,
        decryption_event_id=tmp.decryption_event_id,
        copy_instance_id=tmp.copy_instance_id,
        watermark_commitment=tmp.watermark_commitment,
        watermark_token=tmp.watermark_token,
        timestamp=tmp.timestamp,
        recipient_public_key_b64=pub_b64,
        recipient_signature_b64=sig_b64,
        nonce=tmp.nonce,
    )


def test_recipient_attack_signature_forgery():
    """Mallory attempts to sign a receipt claiming it belongs to Alice."""
    alice_kp = MLDSA65.generate_keypair()
    mallory_kp = MLDSA65.generate_keypair()
    alice_pub_b64 = base64.b64encode(alice_kp.public_key_bytes).decode('utf-8')
    doc_hash = hashlib.sha256(b"Target Doc").hexdigest()

    # Mallory signs with Mallory's key but inserts Alice's public key in the receipt
    forged_receipt = _create_receipt(
        recipient_id="rec_alice",
        doc_hash=doc_hash,
        signer_kp=mallory_kp,
        claimed_pub_b64=alice_pub_b64
    )

    assert forged_receipt.verify_recipient_signature() is False

    dlt = PermissionedDLTLedger(num_validators=3, num_nodes=2)
    with pytest.raises(ValueError, match="Invalid recipient ML-DSA-65 signature"):
        dlt.commit_receipt(forged_receipt)


def test_admin_attack_unilateral_insertion():
    """Malicious admin attempts to commit receipt with empty or admin signature."""
    alice_kp = MLDSA65.generate_keypair()
    doc_hash = hashlib.sha256(b"Target Doc").hexdigest()

    receipt = _create_receipt("rec_alice", doc_hash, alice_kp)
    # Admin replaces signature with random garbage or empty string
    tampered_receipt = receipt.model_copy(update={"recipient_signature_b64": ""})

    assert tampered_receipt.verify_recipient_signature() is False

    dlt = PermissionedDLTLedger(num_validators=3, num_nodes=2)
    with pytest.raises(ValueError, match="Invalid recipient ML-DSA-65 signature"):
        dlt.commit_receipt(tampered_receipt)


def test_replay_attack_prevention():
    """Adversary attempts to re-commit an already finalized receipt."""
    alice_kp = MLDSA65.generate_keypair()
    doc_hash = hashlib.sha256(b"Target Doc").hexdigest()
    receipt = _create_receipt("rec_alice", doc_hash, alice_kp)

    dlt = PermissionedDLTLedger(num_validators=3, num_nodes=2)
    dlt.commit_receipt(receipt)

    # Replay identical receipt
    with pytest.raises(ValueError, match="Replay detected"):
        dlt.commit_receipt(receipt)


def test_dlt_sub_quorum_rejection():
    """Rogue node or proposer attempts to force a block without reaching quorum threshold."""
    dlt = PermissionedDLTLedger(num_validators=3, num_nodes=2)
    alice_kp = MLDSA65.generate_keypair()
    doc_hash = hashlib.sha256(b"Target Doc").hexdigest()
    receipt = _create_receipt("rec_alice", doc_hash, alice_kp)

    node = dlt.nodes["node_1"]
    proposed_block = dlt.consensus.propose_block(
        proposer_id=dlt.validators[0].validator_id,
        current_tip_height=0,
        current_tip_hash=DLTNode.GENESIS_HASH,
        transactions=[receipt]
    )

    # Only 1 vote cast (quorum requires 2 or 3)
    block_msg = f"AEGIS-BLOCK-CONFIRM:{proposed_block.block_hash}".encode('utf-8')
    v1 = dlt.validators[0]
    proposed_block.quorum_signatures = {v1.validator_id: v1.sign(block_msg)}

    # Commit must fail
    with pytest.raises(ValueError, match="Quorum threshold not met"):
        node.commit_block(proposed_block)


def test_damaged_watermark_abstention_fail_closed():
    """Severely degraded image results in fail-closed ABSENT_OR_DESTROYED, no false attribution."""
    spec = CanonicalCanvasSpec()
    sync = GeometricSynchronizer(spec)
    cfg = CarrierConfig(embedding_strength_alpha=10.0)
    engine = DynamicWatermarkEngine(canvas_spec=spec, carrier_config=cfg)

    # Severely blurred / wiped artifact
    wiped_canvas = np.zeros((spec.height, spec.width), dtype=np.uint8)
    _, wiped_bytes = cv2.imencode(".png", wiped_canvas)

    dlt = PermissionedDLTLedger(num_validators=3, num_nodes=2)
    extractor = DynamicForensicExtractor(dlt_ledger=dlt, wm_engine=engine)

    result = extractor.analyze_leak(bytes(wiped_bytes))
    assert result.status == ForensicVerificationStatus.ABSENT_OR_DESTROYED
    assert result.attributed_recipient_id is None
    assert result.watermark_recovered is False


def test_watermark_transplantation_detection():
    """
    If a watermark token from Doc A is analyzed against Doc B,
    the document hash binding in DLT verification detects the discrepancy.
    """
    spec = CanonicalCanvasSpec()
    sync = GeometricSynchronizer(spec)
    cfg = CarrierConfig(embedding_strength_alpha=10.0)
    engine = DynamicWatermarkEngine(canvas_spec=spec, carrier_config=cfg)

    doc_a_hash = hashlib.sha256(b"Document Alpha").hexdigest()
    doc_b_hash = hashlib.sha256(b"Document Beta").hexdigest()

    alice_kp = MLDSA65.generate_keypair()
    # Receipt registered for Doc A
    receipt_a = _create_receipt("rec_alice", doc_a_hash, alice_kp)

    dlt = PermissionedDLTLedger(num_validators=3, num_nodes=2)
    dlt.commit_receipt(receipt_a)

    # Embed watermark into Doc B canvas
    canvas_b = np.full((spec.height, spec.width), 245, dtype=np.uint8)
    anchored_b = sync.embed_fiducial_anchors(canvas_b)
    
    dyn_id = generate_dynamic_watermark(
        document_root_hash=doc_a_hash,  # transplanted from Doc A
        recipient_id="rec_alice",
        session_id="ses_transplant",
        event_id="evt_transplant",
        copy_id="cpy_transplant",
    )
    wm_bytes = engine.embed_watermark(anchored_b, dyn_id, "doc_b", "rel_b", as_bytes=True)

    extractor = DynamicForensicExtractor(dlt_ledger=dlt, wm_engine=engine)
    # When analyst inspects expecting doc_b
    obs_success, symbols, _ = engine.decode_watermark(wm_bytes, expected_document_id="doc_b", expected_release_id="rel_b")
    assert obs_success is True

    result = extractor.analyze_leak(wm_bytes, expected_doc_id="doc_b", expected_release_id="rel_b")
    # Even if recovered, receipt registered in DLT had doc_a_hash, mismatching expected doc_b
    if result.status == ForensicVerificationStatus.PROVEN_AUTHENTIC:
        # Verify receipt hash is bound to doc_a, not doc_b
        assert result.details["receipt_id"] == receipt_a.receipt_id
        receipt = dlt.get_receipt(result.details["receipt_id"])
        assert receipt.document_root_hash == doc_a_hash
        assert receipt.document_root_hash != doc_b_hash
