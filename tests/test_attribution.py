import pytest
import hashlib
from core.recipient import RecipientRegistry
from core.release import ReleaseManager
from core.provenance.decryption import RecipientDecryptionClient
from core.traceability.provider import PrototypeTraceabilityProvider
from core.ledger.ledger import TamperEvidentLedger
from core.attribution.engine import AttributionEngine, AttributionState

def setup_system():
    registry = RecipientRegistry()
    ledger = TamperEvidentLedger()
    provider = PrototypeTraceabilityProvider()
    release_mgr = ReleaseManager(registry=registry)
    decrypt_client = RecipientDecryptionClient(ledger=ledger, traceability_provider=provider)
    engine = AttributionEngine(traceability_provider=provider, ledger=ledger, registry=registry)

    alice = registry.enroll("Alice", "alice")
    bob = registry.enroll("Bob", "bob")
    charlie = registry.enroll("Charlie", "charlie")

    doc_bytes = b"%PDF-1.4 Mock document for attribution test"
    release = release_mgr.create_release(
        document_bytes=doc_bytes,
        document_name="doc.pdf",
        issuer_id="HQ",
        recipient_ids=["alice", "bob", "charlie"]
    )

    return {
        "registry": registry,
        "ledger": ledger,
        "provider": provider,
        "release_mgr": release_mgr,
        "decrypt_client": decrypt_client,
        "engine": engine,
        "alice": alice,
        "bob": bob,
        "charlie": charlie,
        "doc_bytes": doc_bytes,
        "release": release
    }

def test_recipient_isolation():
    """Verify that packages contain only recipient-specific KEM ciphertexts and keys."""
    env = setup_system()
    release = env["release"]
    
    alice_pkg = release.packages["alice"]
    bob_pkg = release.packages["bob"]

    # Ciphertexts and wrapped keys must be strictly isolated and distinct
    assert alice_pkg.kem_ciphertext_b64 != bob_pkg.kem_ciphertext_b64
    assert alice_pkg.wrapped_doc_key_b64 != bob_pkg.wrapped_doc_key_b64

def test_wrong_recipient():
    """Verify that Bob cannot decrypt Alice's package."""
    env = setup_system()
    alice_pkg = env["release"].packages["alice"]
    bob = env["bob"]

    with pytest.raises(ValueError, match="Recipient mismatch"):
        env["decrypt_client"].decrypt_package(alice_pkg, bob)

def test_release_integrity():
    """Verify release metadata and document hash matching."""
    env = setup_system()
    release = env["release"]
    doc_hash = hashlib.sha256(env["doc_bytes"]).hexdigest()

    assert release.original_hash == doc_hash
    assert set(release.recipient_ids) == {"alice", "bob", "charlie"}

def test_attribution_bob_leak():
    """Verify that Bob's legitimate leak correctly attributes to Bob."""
    env = setup_system()
    bob_pkg = env["release"].packages["bob"]
    _, bob_copy, _, _ = env["decrypt_client"].decrypt_package(bob_pkg, env["bob"])

    result = env["engine"].analyze_leak(bob_copy, expected_release_id=env["release"].release_id)
    assert result.state == AttributionState.ATTRIBUTED
    assert result.candidate is not None
    assert result.candidate.recipient_id == "bob"
    assert result.should_abstain is False

def test_attribution_forged_marker_abstains():
    """Verify that a forged marker produces ABSTAIN / INSUFFICIENT_EVIDENCE."""
    env = setup_system()
    forged_marker = env["provider"].issue_marker("doc_1", "rel_1", "bob", "hash123")
    forged_marker.signature_token = "invalid_token_123"
    forged_artifact = env["provider"].embed_marker(env["doc_bytes"], forged_marker)

    result = env["engine"].analyze_leak(forged_artifact, expected_release_id=env["release"].release_id)
    assert result.state in (AttributionState.INSUFFICIENT_EVIDENCE, AttributionState.NO_SIGNAL)
    assert result.should_abstain is True

def test_end_to_end():
    """End-to-end multi-recipient cycle test."""
    env = setup_system()
    release = env["release"]
    
    # Alice decrypts
    _, alice_copy, _, _ = env["decrypt_client"].decrypt_package(release.packages["alice"], env["alice"])
    res_alice = env["engine"].analyze_leak(alice_copy, expected_release_id=release.release_id)
    assert res_alice.state == AttributionState.ATTRIBUTED
    assert res_alice.candidate.recipient_id == "alice"

    # Charlie decrypts
    _, charlie_copy, _, _ = env["decrypt_client"].decrypt_package(release.packages["charlie"], env["charlie"])
    res_charlie = env["engine"].analyze_leak(charlie_copy, expected_release_id=release.release_id)
    assert res_charlie.state == AttributionState.ATTRIBUTED
    assert res_charlie.candidate.recipient_id == "charlie"
