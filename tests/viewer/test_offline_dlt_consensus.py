"""
SIH26237 - Offline Permissioned DLT Consensus Tests
Validates:
- Multi-validator BFT threshold consensus (quorum >= floor(2N/3) + 1)
- Multi-node replicated ledger consistency
- Merkle tree construction and inclusion proofs (RFC-6962 double-domain)
- Fork and rollback detection and rejection
- Recipient-owned ML-DSA-65 signature enforcement
- Quorum-endorsed state snapshots
"""

import pytest
import os
import base64
import hashlib
from typing import Tuple
from datetime import datetime, timezone

from core.crypto.models import KeyPair
from core.crypto.signatures import MLDSA65

from core.ledger.dlt import (
    PermissionedDLTLedger,
    DLTValidator,
    DecryptionReceipt,
    DLTBlock,
    DLTBlockHeader,
    MerkleProof,
    build_merkle_tree,
    DLTNode,
)


def _create_dummy_signed_receipt(recipient_id: str = "rec_alice") -> Tuple[DecryptionReceipt, KeyPair]:
    kp = MLDSA65.generate_keypair()
    pub_b64 = base64.b64encode(kp.public_key_bytes).decode('utf-8')
    receipt_id = f"rcpt_test_{os.urandom(6).hex()}"
    doc_hash = hashlib.sha256(b"Confidential Report").hexdigest()

    tmp = DecryptionReceipt(
        receipt_id=receipt_id,
        document_root_hash=doc_hash,
        recipient_id=recipient_id,
        identity_reference=f"{recipient_id}@aegis.local",
        decryption_session_id="ses_001",
        decryption_event_id=f"evt_{os.urandom(4).hex()}",
        copy_instance_id=f"cpy_{os.urandom(4).hex()}",
        watermark_commitment=hashlib.sha256(os.urandom(32)).hexdigest(),
        watermark_token=os.urandom(32).hex(),
        recipient_public_key_b64=pub_b64,
        recipient_signature_b64="",
    )
    sig_bytes = MLDSA65.sign(kp.private_key_bytes, tmp.canonical_payload_bytes())
    sig_b64 = base64.b64encode(sig_bytes).decode('utf-8')

    receipt = DecryptionReceipt(
        receipt_id=receipt_id,
        document_root_hash=doc_hash,
        recipient_id=recipient_id,
        identity_reference=f"{recipient_id}@aegis.local",
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
    return receipt, kp


def test_multi_validator_quorum_consensus_and_replication():
    # 3 validators -> quorum = floor(2*3/3)+1 = 3 (or 2 depending on formula, our formula is floor(2*3/3)+1 = 3)
    dlt = PermissionedDLTLedger(num_validators=3, num_nodes=3)
    assert len(dlt.validators) == 3
    assert len(dlt.nodes) == 3

    receipt, _ = _create_dummy_signed_receipt("rec_alice")
    block = dlt.commit_receipt(receipt)

    assert block.header.block_height == 1
    assert len(block.transactions) == 1
    assert block.transactions[0].receipt_id == receipt.receipt_id
    assert len(block.quorum_signatures) >= dlt.quorum_threshold

    # Assert replication across ALL nodes
    for nid, node in dlt.nodes.items():
        assert node.get_tip_height() == 1
        assert node.get_tip_hash() == block.block_hash
        assert node.get_receipt(receipt.receipt_id) is not None
        assert node.find_receipt_by_commitment(receipt.watermark_commitment) is not None
        valid, errors = node.verify_chain()
        assert valid is True
        assert len(errors) == 0


def test_recipient_signature_independent_validation():
    dlt = PermissionedDLTLedger(num_validators=3, num_nodes=3)
    receipt, _ = _create_dummy_signed_receipt("rec_bob")

    # Corrupt recipient signature
    tampered_sig = base64.b64encode(os.urandom(len(base64.b64decode(receipt.recipient_signature_b64)))).decode('utf-8')
    bad_receipt = receipt.model_copy(update={"recipient_signature_b64": tampered_sig})


    with pytest.raises(ValueError, match="Invalid recipient ML-DSA-65 signature"):
        dlt.commit_receipt(bad_receipt)


def test_merkle_tree_inclusion_proof_and_verification():
    leaves = [hashlib.sha256(f"leaf_{i}".encode()).digest() for i in range(8)]
    root, proofs = build_merkle_tree(leaves)

    assert len(proofs) == 8
    for i, proof in enumerate(proofs):
        assert proof.root_hash == root
        assert proof.verify() is True

    # Tampered leaf proof fails
    bad_proof = proofs[0].model_copy(update={"leaf_hash": hashlib.sha256(b"corrupt").hexdigest()})
    assert bad_proof.verify() is False



def test_fork_detection_and_rejection():
    dlt = PermissionedDLTLedger(num_validators=3, num_nodes=2)
    receipt1, _ = _create_dummy_signed_receipt("rec_alice")
    block1 = dlt.commit_receipt(receipt1)

    node = dlt.nodes["node_1"]

    # Attempt to commit a competing block at same height 1
    receipt2, _ = _create_dummy_signed_receipt("rec_charlie")
    competing_block = dlt.consensus.propose_block(
        proposer_id=dlt.validators[0].validator_id,
        current_tip_height=0,
        current_tip_hash=DLTNode.GENESIS_HASH,
        transactions=[receipt2]
    )
    finalized_competing = dlt.consensus.collect_votes_and_finalize(competing_block)

    with pytest.raises(ValueError, match="Fork detected at height 1"):
        node.commit_block(finalized_competing)

    assert len(node.fork_alerts) == 1
    assert node.fork_alerts[0]["type"] == "FORK_DETECTED"


def test_rollback_detection_and_rejection():
    dlt = PermissionedDLTLedger(num_validators=3, num_nodes=2)
    r1, _ = _create_dummy_signed_receipt("rec_alice")
    dlt.commit_receipt(r1)
    r2, _ = _create_dummy_signed_receipt("rec_bob")
    dlt.commit_receipt(r2)

    node = dlt.nodes["node_1"]
    assert node.get_tip_height() == 2

    # Attempt to commit height 1 again
    r3, _ = _create_dummy_signed_receipt("rec_charlie")
    stale_block = dlt.consensus.propose_block(
        proposer_id=dlt.validators[0].validator_id,
        current_tip_height=0,
        current_tip_hash=DLTNode.GENESIS_HASH,
        transactions=[r3]
    )
    finalized_stale = dlt.consensus.collect_votes_and_finalize(stale_block)

    with pytest.raises(ValueError, match="Rollback attempt"):
        node.commit_block(finalized_stale)

    assert len(node.tamper_alerts) == 1


def test_dlt_state_snapshot_quorum_verification():
    dlt = PermissionedDLTLedger(num_validators=3, num_nodes=2)
    r1, _ = _create_dummy_signed_receipt("rec_alice")
    dlt.commit_receipt(r1)

    snapshot = dlt.create_snapshot()
    assert snapshot.block_height == 1
    assert snapshot.receipt_count == 1
    assert len(snapshot.quorum_signatures) >= dlt.quorum_threshold

    # Verify validator signatures on snapshot
    snap_msg = snapshot.canonical_bytes()
    valid_votes = 0
    for v_id, sig in snapshot.quorum_signatures.items():
        val = dlt.val_map[v_id]
        if val.verify(snap_msg, sig):
            valid_votes += val.voting_weight
    assert valid_votes >= dlt.quorum_threshold
