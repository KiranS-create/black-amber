import pytest
import os
import hashlib
import base64
from core.recipient import RecipientRegistry
from core.release import ReleaseManager
from core.provenance.decryption import RecipientDecryptionClient
from core.traceability.provider import PrototypeTraceabilityProvider
from core.ledger.ledger import TamperEvidentLedger, EvidenceEvent
from core.crypto.signatures import MLDSA65

def setup_crypto_environment():
    registry = RecipientRegistry()
    ledger = TamperEvidentLedger()
    provider = PrototypeTraceabilityProvider()
    release_mgr = ReleaseManager(registry=registry)
    decrypt_client = RecipientDecryptionClient(ledger=ledger, traceability_provider=provider)

    alice = registry.enroll("Alice", "alice")
    bob = registry.enroll("Bob", "bob")
    charlie = registry.enroll("Charlie", "charlie")

    doc_bytes = b"%PDF-1.7 Cryptographic provenance baseline document"
    release = release_mgr.create_release(
        document_bytes=doc_bytes,
        document_name="Briefing.pdf",
        issuer_id="HQ_COMMAND",
        recipient_ids=["alice", "bob", "charlie"]
    )

    return {
        "registry": registry,
        "ledger": ledger,
        "provider": provider,
        "release_mgr": release_mgr,
        "decrypt_client": decrypt_client,
        "alice": alice,
        "bob": bob,
        "charlie": charlie,
        "doc_bytes": doc_bytes,
        "release": release
    }

def test_full_recipient_isolation_matrix():
    """Verify that every recipient can only decrypt their own package and fails on all others."""
    env = setup_crypto_environment()
    release = env["release"]
    client = env["decrypt_client"]

    recipients = [("alice", env["alice"]), ("bob", env["bob"]), ("charlie", env["charlie"])]

    # 1. Legitimate decryptions succeed
    for rec_id, rec in recipients:
        pkg = release.packages[rec_id]
        plain, traceable, event, _ = client.decrypt_package(pkg, rec)
        assert plain == env["doc_bytes"]
        assert event.recipient_id == rec_id

    # 2. Cross decryptions fail
    for rec_id_pkg, _ in recipients:
        pkg = release.packages[rec_id_pkg]
        for rec_id_actor, actor in recipients:
            if rec_id_pkg != rec_id_actor:
                # With recipient mismatch check
                with pytest.raises(ValueError, match="Recipient mismatch"):
                    client.decrypt_package(pkg, actor)

def test_package_substitution():
    """Verify that substituting Bob's KEM ciphertext into Alice's package fails decryption."""
    env = setup_crypto_environment()
    client = env["decrypt_client"]
    alice = env["alice"]
    alice_pkg = env["release"].packages["alice"]
    bob_pkg = env["release"].packages["bob"]

    # Attacker swaps Bob's KEM ciphertext into Alice's package
    substituted_pkg = alice_pkg.model_copy(update={
        "kem_ciphertext_b64": bob_pkg.kem_ciphertext_b64
    })

    with pytest.raises(Exception):
        client.decrypt_package(substituted_pkg, alice)

def test_release_binding():
    """Verify that tampering with package release_id or document_id fails key unwrapping or decryption."""
    env = setup_crypto_environment()
    client = env["decrypt_client"]
    bob = env["bob"]
    bob_pkg = env["release"].packages["bob"]

    tampered_pkg = bob_pkg.model_copy(update={"release_id": "forged_release_999"})
    with pytest.raises(Exception):
        client.decrypt_package(tampered_pkg, bob)

def test_document_binding():
    """Verify that tampering with document ciphertext or expected document hash fails decryption."""
    env = setup_crypto_environment()
    client = env["decrypt_client"]
    bob = env["bob"]
    bob_pkg = env["release"].packages["bob"]

    tampered_pkg = bob_pkg.model_copy(update={"document_hash": "deadbeef" * 8})
    with pytest.raises(ValueError, match="Integrity check failed"):
        client.decrypt_package(tampered_pkg, bob)

def test_provenance_signature():
    """Verify that provenance events are genuinely signed by the recipient's ML-DSA private key."""
    env = setup_crypto_environment()
    client = env["decrypt_client"]
    bob = env["bob"]
    bob_pkg = env["release"].packages["bob"]

    _, _, event, _ = client.decrypt_package(bob_pkg, bob)
    
    # Reconstruct canonical signed payload
    sign_payload = (
        f"DECRYPTION_PROVENANCE:{event.event_id}:{event.document_id}:"
        f"{event.release_id}:{event.recipient_id}:{event.artifact_hash}:"
        f"{event.previous_event_hash}:{event.timestamp}"
    ).encode('utf-8')

    sig_bytes = base64.b64decode(event.signature)
    pub_bytes = bob.dsa_keypair.public_key_bytes

    assert MLDSA65.verify(pub_bytes, sign_payload, sig_bytes) is True

def test_provenance_tampering():
    """Verify that tampering with any field of the provenance event breaks signature verification."""
    env = setup_crypto_environment()
    client = env["decrypt_client"]
    bob = env["bob"]
    bob_pkg = env["release"].packages["bob"]

    _, _, event, _ = client.decrypt_package(bob_pkg, bob)
    sig_bytes = base64.b64decode(event.signature)
    pub_bytes = bob.dsa_keypair.public_key_bytes

    # Tampered timestamp
    tampered_payload = (
        f"DECRYPTION_PROVENANCE:{event.event_id}:{event.document_id}:"
        f"{event.release_id}:{event.recipient_id}:{event.artifact_hash}:"
        f"{event.previous_event_hash}:2020-01-01T00:00:00Z"
    ).encode('utf-8')

    assert MLDSA65.verify(pub_bytes, tampered_payload, sig_bytes) is False

def test_ledger_tampering_and_duplicate_rejection():
    """Verify that duplicate events and modified chain histories are strictly caught by the ledger."""
    ledger = TamperEvidentLedger()
    
    ev1 = EvidenceEvent(
        event_id="evt_alpha",
        event_type="RELEASE_EVENT",
        document_id="doc_1",
        release_id="rel_1",
        recipient_id="alice",
        algorithm="ML-DSA-65",
        artifact_hash="hash_a",
        evidence_hash="ev_a",
        previous_event_hash=TamperEvidentLedger.GENESIS_HASH,
        signature="sig_a"
    )
    h1 = ledger.append_event(ev1)

    # Attempt duplicate event_id
    ev_duplicate = ev1.model_copy()
    with pytest.raises(ValueError, match="Replay detected"):
        ledger.append_event(ev_duplicate)

    ev2 = EvidenceEvent(
        event_id="evt_beta",
        event_type="DECRYPTION_EVENT",
        document_id="doc_1",
        release_id="rel_1",
        recipient_id="bob",
        algorithm="ML-DSA-65",
        artifact_hash="hash_b",
        evidence_hash="ev_b",
        previous_event_hash=h1,
        signature="sig_b"
    )
    ledger.append_event(ev2)

    # Chain is valid initially
    is_valid, errors = ledger.verify_chain()
    assert is_valid is True
    assert len(errors) == 0

    # Tamper with event 1 payload
    ledger.events[0].recipient_id = "attacker_mallory"
    is_valid_after, errors_after = ledger.verify_chain()
    assert is_valid_after is False
    assert len(errors_after) > 0
