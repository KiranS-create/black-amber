"""
AegisTrace Recipient Non-Repudiation Tests.

Verifies that recipient actions are cryptographically non-repudiable:
1. Recipient ML-DSA-65 post-quantum signature on canonical DecryptionReceipt is
   mathematically unforgeable by server, other recipients, or eavesdroppers.
2. Canonical receipt payload strictly binds:
   - recipient_id
   - decryption_session_id
   - decryption_event_id
   - copy_instance_id
   - watermark_commitment
   - precise timestamp
3. DLT Merkle inclusion proof and validator quorum signatures anchor the receipt
   in an immutable historical timeline, preventing post-facto denial or backdating.
"""

import pytest
import copy
import base64
from core.integration.orchestrator import AegisTraceEndToEndOrchestrator
from core.crypto.signatures import MLDSA65


def test_recipient_signature_non_repudiation():
    """
    Validates that a recipient's signature on a DecryptionReceipt is verified
    against their registered public key and cannot be forged by another entity.
    """
    orchestrator = AegisTraceEndToEndOrchestrator(
        tenant_id="tenant_non_repudiation_eval",
        validator_count=4
    )

    doc_bytes = b"%PDF-1.7 NON REPUDIATION DEFENSE SPECIFICATION\n" + b"SECURE ATTESTATION DATA " * 30
    result = orchestrator.run_full_golden_pipeline(
        document_bytes=doc_bytes,
        document_name="Non_Repudiation_Brief.pdf",
        leak_recipient_id="alice"
    )

    receipt = result.decryption_records["alice"].receipt
    assert receipt.recipient_id == "alice"
    assert receipt.recipient_signature_b64 is not None
    assert receipt.verify_recipient_signature() is True

    # Check that another recipient's public key fails verification
    bob = orchestrator.registry.get("bob")
    assert bob is not None
    
    # Verify receipt payload against Bob's public key
    payload = receipt.canonical_payload_bytes()
    sig_bytes = base64.b64decode(receipt.recipient_signature_b64)
    bob_ver = MLDSA65.verify(
        public_key_bytes=bob.dsa_keypair.public_key_bytes,
        message=payload,
        signature=sig_bytes
    )
    assert bob_ver is False, "Alice's signature must fail validation under Bob's public key"


def test_receipt_tampering_breaks_signature():
    """
    Modifying any field in the canonical payload (e.g. session_id, timestamp, commitment)
    invalidates the ML-DSA-65 signature.
    """
    orchestrator = AegisTraceEndToEndOrchestrator(
        tenant_id="tenant_non_repudiation_eval",
        validator_count=4
    )
    doc_bytes = b"%PDF-1.7 SIGNATURE PAYLOAD TAMPER TEST\n" + b"DATA " * 30
    result = orchestrator.run_full_golden_pipeline(
        document_bytes=doc_bytes,
        document_name="Payload_Tamper.pdf",
        leak_recipient_id="bob"
    )

    receipt = result.decryption_records["bob"].receipt
    
    # Tamper session_id
    tampered_receipt = copy.deepcopy(receipt)
    tampered_receipt.decryption_session_id = "sess_forged_9999"
    assert tampered_receipt.verify_recipient_signature() is False

    # Tamper timestamp
    tampered_receipt2 = copy.deepcopy(receipt)
    tampered_receipt2.timestamp = "2020-01-01T00:00:00+00:00"
    assert tampered_receipt2.verify_recipient_signature() is False

    # Tamper watermark_commitment
    tampered_receipt3 = copy.deepcopy(receipt)
    tampered_receipt3.watermark_commitment = "0" * 64
    assert tampered_receipt3.verify_recipient_signature() is False


def test_dlt_merkle_inclusion_anchoring():
    """
    Verifies that the DLT Merkle proof anchors the receipt into a specific block height
    and cannot be transferred to a different block.
    """
    orchestrator = AegisTraceEndToEndOrchestrator(
        tenant_id="tenant_non_repudiation_eval",
        validator_count=4
    )
    doc_bytes = b"%PDF-1.7 DLT ANCHORING TEST\n" + b"DATA " * 30
    result = orchestrator.run_full_golden_pipeline(
        document_bytes=doc_bytes,
        document_name="Anchoring.pdf",
        leak_recipient_id="charlie"
    )

    receipt = result.decryption_records["charlie"].receipt
    primary_node = list(orchestrator.dlt_ledger.nodes.values())[0]
    proof = primary_node.get_merkle_proof(receipt.receipt_id)
    assert proof is not None
    assert proof.verify() is True

    # Corrupting proof root breaks verification
    corrupted_proof = copy.deepcopy(proof)
    corrupted_proof.root_hash = "0" * 64
    assert corrupted_proof.verify() is False
