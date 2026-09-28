"""
tests/properties/test_dlt_bft_properties.py

Property-based testing and adversarial fuzzing for Offline Permissioned DLT:
- RFC-6962 double-domain Merkle tree inclusion proofs soundness & completeness
- Byzantine Fault Tolerant (BFT) quorum threshold enforcement (floor(2N/3) + 1)
- DecryptionReceipt ML-DSA-65 recipient signature tamper sensitivity
- Replicated DLT node multi-validator state consistency & fork/rollback detection
"""

import base64
import copy
import hashlib
import os
import pytest
from core.crypto.signatures import MLDSA65
from core.ledger.dlt import (
    build_merkle_tree,
    MerkleProof,
    DecryptionReceipt,
    DLTValidator,
    DLTBlockHeader,
    DLTBlock,
    DLTNode,
    DLTConsensus,
    PermissionedDLTLedger,
)
from core.testing.property_engine import PropertyRunner, DeterministicGenerator
from core.security.invariants import assert_invariant


def test_property_dlt_merkle_tree_soundness_and_tamper_fuzzing(runner: PropertyRunner):
    """
    Property: RFC-6962 binary Merkle tree over arbitrary leaf counts (1..32)
    produces sound and complete inclusion proofs. Any mutation strictly fails verify().
    """
    def prop(g: DeterministicGenerator):
        num_leaves = g.integer(1, 32)
        leaf_payloads = [g.bytes_data(g.integer(16, 64)) for _ in range(num_leaves)]

        root_hex, proofs = build_merkle_tree(leaf_payloads)
        assert len(proofs) == num_leaves

        # 1. Baseline: All generated inclusion proofs must verify
        for idx, proof in enumerate(proofs):
            assert proof.verify() is True, f"Valid Merkle proof for leaf {idx}/{num_leaves} failed verification"

        # 2. Tampering fuzzing on a selected proof
        target_proof = g.choice(proofs)
        tamper_type = g.choice(["corrupt_leaf", "corrupt_root", "corrupt_sibling", "flip_direction"])

        tampered_proof = copy.deepcopy(target_proof)

        if tamper_type == "corrupt_leaf":
            tampered_proof.leaf_hash = hashlib.sha256(g.bytes_data(32)).hexdigest()
        elif tamper_type == "corrupt_root":
            tampered_proof.root_hash = hashlib.sha256(g.bytes_data(32)).hexdigest()
        elif tamper_type == "corrupt_sibling":
            if tampered_proof.audit_path:
                step_idx = g.integer(0, len(tampered_proof.audit_path) - 1)
                sib_hash, direction = tampered_proof.audit_path[step_idx]
                corrupted_sib = hashlib.sha256(g.bytes_data(32)).hexdigest()
                tampered_proof.audit_path[step_idx] = (corrupted_sib, direction)
            else:
                tampered_proof.leaf_hash = "deadbeef" * 8
        elif tamper_type == "flip_direction":
            if tampered_proof.audit_path:
                step_idx = g.integer(0, len(tampered_proof.audit_path) - 1)
                sib_hash, direction = tampered_proof.audit_path[step_idx]
                new_dir = "L" if direction == "R" else "R"
                corrupted_sib = hashlib.sha256(g.bytes_data(32)).hexdigest()
                tampered_proof.audit_path[step_idx] = (corrupted_sib, new_dir)
            else:
                tampered_proof.leaf_hash = "deadbeef" * 8

        # Invariant: Tampered proof must fail verification
        tampered_res = tampered_proof.verify()
        assert tampered_res is False, f"Tampered Merkle proof ({tamper_type}) verified as valid!"

    res = runner.run_property("dlt_merkle_tree_soundness_and_tamper", prop, iterations=150)
    assert res.passed, res.error_message


def test_property_dlt_byzantine_quorum_threshold(runner: PropertyRunner):
    """
    Property: BFT quorum threshold floor(2N/3) + 1 is strictly enforced.
    Blocks with fewer valid validator votes or any corrupted signatures strictly fail validation.
    """
    # Pre-generate validators once for deterministic fast execution
    validators = [DLTValidator.generate(f"val_{i+1}", voting_weight=1) for i in range(7)]

    def prop(g: DeterministicGenerator):
        num_validators = g.integer(3, 7)
        current_validators = validators[:num_validators]
        val_map = {v.validator_id: v for v in current_validators}
        quorum_threshold = (2 * num_validators // 3) + 1

        # Propose block
        proposer = current_validators[0]
        header = DLTBlockHeader(
            block_height=1,
            previous_block_hash="0" * 64,
            proposer_validator_id=proposer.validator_id,
            round_number=1,
            merkle_root="0" * 64,
        )
        block_hash = header.compute_header_hash()
        block_msg = f"AEGIS-BLOCK-CONFIRM:{block_hash}".encode('utf-8')
        proposer_sig = proposer.sign(block_msg)

        # Decide vote count
        num_votes = g.integer(0, num_validators)
        voting_validators = g.sample(current_validators, num_votes)
        quorum_sigs = {}
        has_corrupted_vote = False

        for v in voting_validators:
            if g.boolean(0.15):
                # Corrupted signature
                quorum_sigs[v.validator_id] = base64.b64encode(g.bytes_data(64)).decode('utf-8')
                has_corrupted_vote = True
            else:
                quorum_sigs[v.validator_id] = v.sign(block_msg)

        block = DLTBlock(
            header=header,
            block_hash=block_hash,
            transactions=[],
            proposer_signature_b64=proposer_sig,
            quorum_signatures=quorum_sigs,
        )

        valid, errors = block.verify_block_integrity(val_map, quorum_threshold)

        # Count truly valid votes
        valid_vote_count = sum(
            1 for v_id, s in quorum_sigs.items()
            if v_id in val_map and val_map[v_id].verify(block_msg, s)
        )

        # A block is only valid if NO corrupted votes exist AND valid votes meet quorum
        if not has_corrupted_vote and valid_vote_count >= quorum_threshold:
            assert valid is True, f"Valid quorum rejected: {errors}"
        else:
            assert valid is False, f"Sub-quorum or corrupted block accepted! {errors}"
            assert len(errors) > 0

    res = runner.run_property("dlt_byzantine_quorum_threshold", prop, iterations=100)
    assert res.passed, res.error_message


def test_property_decryption_receipt_ml_dsa_65_authenticity(runner: PropertyRunner):
    """
    Property: DecryptionReceipt is signed exclusively by the recipient.
    Any mutation of payload parameters destroys signature validity.
    """
    kp = MLDSA65.generate_keypair()
    pub_b64 = base64.b64encode(kp.public_key_bytes).decode('utf-8')

    def prop(g: DeterministicGenerator):
        rec_id = g.generate_recipient_id()
        session_id = g.generate_session_id()
        event_id = f"evt_{g.alphanumeric(8, 12)}"
        doc_root_hash = hashlib.sha256(g.bytes_data(32)).hexdigest()
        copy_id = f"cpy_{g.alphanumeric(8, 12)}"
        commitment = hashlib.sha256(g.bytes_data(32)).hexdigest()
        nonce = g.alphanumeric(16, 32)

        tmp_receipt = DecryptionReceipt(
            receipt_id=f"rcpt_{g.alphanumeric(8, 12)}",
            document_root_hash=doc_root_hash,
            recipient_id=rec_id,
            identity_reference=f"{rec_id}@corp.internal",
            decryption_session_id=session_id,
            decryption_event_id=event_id,
            copy_instance_id=copy_id,
            watermark_commitment=commitment,
            key_epoch=1,
            nonce=nonce,
            recipient_public_key_b64=pub_b64,
            recipient_signature_b64="",
            metadata={"test_field": "val"},
        )
        msg_bytes = tmp_receipt.canonical_payload_bytes()
        sig_bytes = MLDSA65.sign(kp.private_key_bytes, msg_bytes)
        sig_b64 = base64.b64encode(sig_bytes).decode('utf-8')

        valid_receipt = copy.deepcopy(tmp_receipt)
        valid_receipt.recipient_signature_b64 = sig_b64

        # Baseline: Valid receipt verifies
        assert valid_receipt.verify_recipient_signature() is True

        # Mutation: Tamper one parameter
        mutation_field = g.choice([
            "document_root_hash",
            "recipient_id",
            "identity_reference",
            "decryption_session_id",
            "copy_instance_id",
            "watermark_commitment",
            "nonce",
            "signature",
            "metadata",
        ])

        tampered_receipt = copy.deepcopy(valid_receipt)
        if mutation_field == "document_root_hash":
            tampered_receipt.document_root_hash = hashlib.sha256(g.bytes_data(32)).hexdigest()
        elif mutation_field == "recipient_id":
            tampered_receipt.recipient_id = f"rec-attacker-{g.alphanumeric(4, 6)}"
        elif mutation_field == "identity_reference":
            tampered_receipt.identity_reference = "attacker@evil.corp"
        elif mutation_field == "decryption_session_id":
            tampered_receipt.decryption_session_id = g.generate_session_id()
        elif mutation_field == "copy_instance_id":
            tampered_receipt.copy_instance_id = f"cpy-spoofed-{g.alphanumeric(4, 6)}"
        elif mutation_field == "watermark_commitment":
            tampered_receipt.watermark_commitment = hashlib.sha256(b"corrupted_commitment").hexdigest()
        elif mutation_field == "nonce":
            tampered_receipt.nonce = "spoofed_nonce_999"
        elif mutation_field == "signature":
            tampered_receipt.recipient_signature_b64 = base64.b64encode(g.bytes_data(64)).decode('utf-8')
        elif mutation_field == "metadata":
            tampered_receipt.metadata["tampered"] = True

        # Invariant: Tampered receipt must fail signature verification
        tampered_valid = tampered_receipt.verify_recipient_signature()
        assert tampered_valid is False, f"Tampered receipt ({mutation_field}) verified as valid!"

    res = runner.run_property("decryption_receipt_ml_dsa_65_authenticity", prop, iterations=100)
    assert res.passed, res.error_message


def test_property_dlt_node_replicated_state_and_fork_detection(runner: PropertyRunner):
    """
    Property: Replicated DLT cluster maintains synchronized tip height and detects
    competing forks or rollback attacks.
    """
    fixed_validators = [DLTValidator.generate(f"val_{i+1}", voting_weight=1) for i in range(3)]
    recipient_kp = MLDSA65.generate_keypair()
    pub_b64 = base64.b64encode(recipient_kp.public_key_bytes).decode('utf-8')

    def prop(g: DeterministicGenerator):
        dlt = PermissionedDLTLedger(validators=fixed_validators, num_nodes=3)

        # Commit N receipts
        num_receipts = g.integer(2, 4)
        for i in range(num_receipts):
            rec_id = f"rec_{i}_{g.alphanumeric(4, 6)}"
            rcpt_id = f"rcpt_{i}_{g.alphanumeric(6, 8)}"
            tmp_r = DecryptionReceipt(
                receipt_id=rcpt_id,
                document_root_hash="aa" * 32,
                recipient_id=rec_id,
                identity_reference=f"{rec_id}@corp.internal",
                decryption_session_id=f"sess_{i}",
                decryption_event_id=f"evt_{i}",
                copy_instance_id=f"cpy_{i}",
                watermark_commitment="bb" * 32,
                key_epoch=1,
                recipient_public_key_b64=pub_b64,
                recipient_signature_b64="",
            )
            sig_bytes = MLDSA65.sign(recipient_kp.private_key_bytes, tmp_r.canonical_payload_bytes())
            r = copy.deepcopy(tmp_r)
            r.recipient_signature_b64 = base64.b64encode(sig_bytes).decode('utf-8')

            dlt.commit_receipt(r)

        # Invariant 1: All nodes must have identical tip height and hash
        for nid, node in dlt.nodes.items():
            assert node.get_tip_height() == num_receipts
            assert node.get_tip_hash() == list(dlt.nodes.values())[0].get_tip_hash()

        # Invariant 2: Fork attempt on node 1
        node1 = dlt.nodes["node_1"]
        tip_h = node1.get_tip_height()
        fork_header = DLTBlockHeader(
            block_height=tip_h,  # Same height as current tip
            previous_block_hash="ff" * 32,
            proposer_validator_id=dlt.validators[0].validator_id,
            round_number=99,
            merkle_root="ff" * 32,
        )
        fork_block = DLTBlock(
            header=fork_header,
            block_hash="fork_block_hash_9999",
            transactions=[],
        )

        with pytest.raises(ValueError, match="Fork detected"):
            node1.commit_block(fork_block)

        assert len(node1.fork_alerts) > 0
        assert node1.fork_alerts[-1]["type"] == "FORK_DETECTED"

    res = runner.run_property("dlt_replicated_state_and_fork_detection", prop, iterations=15)
    assert res.passed, res.error_message
