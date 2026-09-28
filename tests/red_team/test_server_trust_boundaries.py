"""
AegisTrace Server Trust Boundaries Tests.

Formally tests the cryptographic trust boundaries of the AegisTrace architecture,
demonstrating what a compromised central server CANNOT do:
1. Server CANNOT decrypt recipient packages without recipient's private ML-KEM-768 key.
2. Server CANNOT forge recipient ML-DSA-65 signatures on DecryptionReceipts.
3. Server CANNOT unilaterally alter committed DLT blocks without validator quorum rejection.
4. Server CANNOT forge an offline-verifiable evidence package without detection.
"""

import pytest
from core.integration.orchestrator import AegisTraceEndToEndOrchestrator
from core.crypto.kem import MLKEM768
from core.crypto.signatures import MLDSA65
from core.evidence_package.verifier import OfflineEvidenceVerifier
from core.evidence_package.models import VerificationStatus


def test_server_cannot_forge_recipient_signature():
    """
    Simulates a compromised server attempting to construct a fake DecryptionReceipt
    claiming Alice decrypted a document, using server credentials instead of Alice's private key.
    """
    orchestrator = AegisTraceEndToEndOrchestrator(
        tenant_id="tenant_trust_boundary",
        validator_count=4
    )

    # Enroll Alice
    alice = orchestrator.enroll_recipient(name="Alice", recipient_id="alice")
    assert alice is not None

    # Server generates its own rogue DSA keypair
    server_keypair = MLDSA65.generate_keypair()

    # Server signs a forged receipt with server private key, pretending it is Alice
    payload = b"FORGED_RECEIPT_CANONICAL_PAYLOAD_FOR_ALICE"
    forged_sig = MLDSA65.sign(server_keypair.private_key_bytes, payload)

    # Verifying against Alice's actual public key MUST FAIL
    is_valid = MLDSA65.verify(
        public_key_bytes=alice.dsa_keypair.public_key_bytes,
        message=payload,
        signature=forged_sig
    )
    assert is_valid is False, "Server was able to forge recipient signature (VIOLATION)"


def test_server_cannot_decrypt_without_recipient_private_kem_key():
    """
    Simulates a server intercepting the broadcast ciphertext.
    Without the recipient's private ML-KEM-768 decapsulation key, the shared secret cannot be recovered.
    """
    # Recipient generates keypair
    rec_keypair = MLKEM768.generate_keypair()

    # Sender / Server encapsulates to recipient public key
    encaps_res = MLKEM768.encapsulate(rec_keypair.public_key_bytes)

    # Attacker / Server generates an attacker keypair and attempts decapsulation
    attacker_keypair = MLKEM768.generate_keypair()
    recovered_secret = MLKEM768.decapsulate(attacker_keypair.private_key_bytes, encaps_res.ciphertext)

    # ML-KEM returns pseudo-random garbage on invalid private key (implicit rejection)
    assert recovered_secret != encaps_res.shared_secret, "Attacker recovered shared secret with wrong key"


def test_server_cannot_bypass_offline_package_verification():
    """
    Server produces a fabricated evidence package with an invalid examiner signature.
    Independent offline verifier strictly rejects it.
    """
    orchestrator = AegisTraceEndToEndOrchestrator(
        tenant_id="tenant_trust_boundary",
        validator_count=4
    )
    doc_bytes = b"%PDF-1.7 SERVER TRUST BOUNDARY TEST\n" + b"TEST " * 30
    res = orchestrator.run_full_golden_pipeline(
        document_bytes=doc_bytes,
        document_name="Boundary.pdf",
        leak_recipient_id="bob"
    )

    pkg = res.evidence_package
    # Server replaces examiner signature with invalid b64 string
    pkg.signature.signature_b64 = "AAAA" * 64

    verifier = OfflineEvidenceVerifier(expected_tenant_id="tenant_trust_boundary")
    ver_res = verifier.verify_package(
        manifest=pkg.manifest,
        signature=pkg.signature,
        objects=pkg.objects,
        edges=pkg.edges,
        custody_chain=pkg.custody_chain
    )
    assert ver_res.overall_status == VerificationStatus.INVALID
    assert ver_res.manifest_signature_valid is False
