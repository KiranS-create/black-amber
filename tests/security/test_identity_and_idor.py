import pytest
import base64
from fastapi.testclient import TestClient

from core.recipient import default_registry, Recipient
from core.release import default_release_manager, DocumentRelease
from core.provenance.decryption import default_decryption_client
from demo.end_to_end import create_sample_pdf

def test_unauthenticated_decryption_oracle_exploit(client: TestClient, sample_pdf_b64):
    """
    RED-TEAM EXPLOIT PROOF:
    Demonstrates that the API allows ANY unauthenticated caller to decrypt a release
    for an arbitrary recipient, causing the server to sign a provenance event with
    that recipient's private key.
    """
    # 1. Authority creates release for Alice and Bob
    rel_res = client.post("/releases", json={
        "document_name": "Classified_Plans.pdf",
        "document_base64": sample_pdf_b64,
        "issuer_id": "HQ_AUTHORITY",
        "recipient_ids": ["alice", "bob"]
    })
    assert rel_res.status_code == 200
    release_id = rel_res.json()["release_id"]

    # 2. Attacker (without Alice's consent or credentials) calls /decrypt for Alice
    dec_res = client.post(f"/releases/{release_id}/decrypt", json={"recipient_id": "alice"})
    assert dec_res.status_code == 200
    dec_data = dec_res.json()

    # VULNERABILITY CONFIRMATION:
    # Server returned Alice's traceable copy and an event signed with Alice's private key!
    assert dec_data["recipient_id"] == "alice"
    assert "traceable_document_base64" in dec_data
    assert dec_data["event_id"] is not None

def test_recipient_private_key_custody_vulnerability():
    """
    AUDIT CHECK:
    Verifies whether the central recipient registry holds private keys in server memory,
    violating SECURITY.md Section 4 (Key Isolation).
    """
    alice: Recipient = default_registry.get("alice")
    assert alice is not None
    # Vulnerability: Server has custody of private KEM and private DSA keys!
    assert alice.kem_keypair.private_key_bytes is not None
    assert len(alice.kem_keypair.private_key_bytes) > 0
    assert alice.dsa_keypair.private_key_bytes is not None
    assert len(alice.dsa_keypair.private_key_bytes) > 0

def test_idor_cross_recipient_package_retrieval(client: TestClient, sample_pdf_b64):
    """
    Demonstrates Insecure Direct Object Reference (IDOR):
    Any caller can enumerate and retrieve any recipient's encrypted key capsule.
    """
    rel_res = client.post("/releases", json={
        "document_name": "Target_Doc.pdf",
        "document_base64": sample_pdf_b64,
        "issuer_id": "HQ_AUTHORITY",
        "recipient_ids": ["alice", "bob"]
    })
    assert rel_res.status_code == 200
    release_id = rel_res.json()["release_id"]

    # Unauthenticated caller directly fetches Bob's package
    bob_pkg_res = client.get(f"/releases/{release_id}/packages/bob")
    assert bob_pkg_res.status_code == 200
    bob_pkg = bob_pkg_res.json()
    assert bob_pkg["recipient_id"] == "bob"
    assert "kem_ciphertext_b64" in bob_pkg

def test_recipient_substitution_mismatch_rejection(sample_pdf_bytes):
    """
    Ensure the decryption engine rejects a package when the attempting recipient
    does not match the package.recipient_id.
    """
    release = default_release_manager.create_release(
        document_bytes=sample_pdf_bytes,
        document_name="Confidential.pdf",
        issuer_id="HQ",
        recipient_ids=["alice", "bob"]
    )
    alice_pkg = release.packages["alice"]
    bob_recipient = default_registry.get("bob")

    # Bob attempts to decrypt Alice's package
    with pytest.raises(ValueError, match="Recipient mismatch"):
        default_decryption_client.decrypt_package(
            package=alice_pkg,
            recipient=bob_recipient
        )

def test_cross_document_release_tampering_detected(sample_pdf_bytes):
    """
    Ensure that tampering with package.document_id breaks AES-GCM Associated Data authentication.
    """
    release = default_release_manager.create_release(
        document_bytes=sample_pdf_bytes,
        document_name="Document1.pdf",
        issuer_id="HQ",
        recipient_ids=["alice"]
    )
    pkg = release.packages["alice"].model_copy(deep=True)
    # Tamper with document_id in the package
    pkg.document_id = "doc_spoofed_unauthorized_999"

    alice = default_registry.get("alice")
    with pytest.raises(Exception):
        # Must fail AES-GCM tag verification due to mismatched associated data
        default_decryption_client.decrypt_package(package=pkg, recipient=alice)
