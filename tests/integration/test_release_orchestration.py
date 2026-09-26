import base64
import hashlib
import pytest
from fastapi.testclient import TestClient

def test_recipient_enrollment_and_queries(client: TestClient):
    # Enroll new recipient
    enroll_res = client.post("/recipients", json={"name": "David Wallace", "recipient_id": "david"})
    assert enroll_res.status_code == 201
    data = enroll_res.json()
    assert data["recipient_id"] == "david"
    assert data["algorithm_kem"] == "ML-KEM-768"
    assert data["algorithm_dsa"] == "ML-DSA-65"
    assert "kem_public_key_b64" in data
    assert "dsa_public_key_b64" in data
    # Ensure private key is NOT present
    assert "kem_keypair" not in data
    assert "dsa_keypair" not in data

    # Retrieve individual recipient
    get_res = client.get("/recipients/david")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "David Wallace"

    # List recipients
    list_res = client.get("/recipients")
    assert list_res.status_code == 200
    recipients = list_res.json()
    assert any(r["recipient_id"] == "david" for r in recipients)

def test_release_creation_with_registered_document(client: TestClient, sample_pdf_bytes: bytes):
    # 1. Register document
    doc_res = client.post(
        "/documents",
        files={"file": ("release_spec.pdf", sample_pdf_bytes, "application/pdf")},
        data={"document_name": "Release Target"}
    )
    assert doc_res.status_code == 201
    doc_id = doc_res.json()["document_id"]
    orig_hash = doc_res.json()["original_document_hash"]

    # 2. Create release
    rel_res = client.post("/releases", json={
        "document_id": doc_id,
        "issuer_id": "HQ_ALPHA",
        "recipient_ids": ["alice", "bob", "charlie"]
    })
    assert rel_res.status_code == 200
    rel_data = rel_res.json()
    release_id = rel_data["release_id"]
    assert rel_data["original_hash"] == orig_hash
    assert len(rel_data["packages"]) == 3
    assert "alice" in rel_data["packages"]
    assert "bob" in rel_data["packages"]

    # 3. Retrieve release by ID
    get_rel = client.get(f"/releases/{release_id}")
    assert get_rel.status_code == 200
    assert get_rel.json()["release_id"] == release_id

    # 4. Retrieve single recipient package
    pkg_res = client.get(f"/releases/{release_id}/packages/bob")
    assert pkg_res.status_code == 200
    pkg_data = pkg_res.json()
    assert pkg_data["recipient_id"] == "bob"
    assert pkg_data["algorithm_kem"] == "ML-KEM-768"
    assert pkg_data["algorithm_sym"] == "AES-256-GCM"

    # 5. Verify cryptographic isolation: Alice's package != Bob's package
    alice_pkg = rel_data["packages"]["alice"]
    bob_pkg = rel_data["packages"]["bob"]
    assert alice_pkg["kem_ciphertext_b64"] != bob_pkg["kem_ciphertext_b64"]
    assert alice_pkg["wrapped_doc_key_b64"] != bob_pkg["wrapped_doc_key_b64"]

def test_release_decryption_and_provenance(client: TestClient, sample_pdf_bytes: bytes):
    # Create release
    pdf_b64 = base64.b64encode(sample_pdf_bytes).decode('utf-8')
    rel_res = client.post("/releases", json={
        "document_name": "DecryptionTest.pdf",
        "document_base64": pdf_b64,
        "issuer_id": "HQ_TEST",
        "recipient_ids": ["alice", "bob"]
    })
    assert rel_res.status_code == 200
    release_id = rel_res.json()["release_id"]

    # Decrypt as Bob
    dec_res = client.post(f"/releases/{release_id}/decrypt", json={"recipient_id": "bob"})
    assert dec_res.status_code == 200
    dec_data = dec_res.json()
    assert dec_data["status"] == "SUCCESS"
    assert dec_data["recipient_id"] == "bob"
    assert "traceable_document_base64" in dec_data
    assert "event_id" in dec_data
    assert "event_hash" in dec_data

    # Check that ledger contains this signed event
    ev_res = client.get(f"/evidence/{release_id}")
    assert ev_res.status_code == 200
    events = ev_res.json()
    assert any(e["event_id"] == dec_data["event_id"] for e in events)

def test_release_capacity_insufficiency(client: TestClient, sample_pdf_bytes: bytes):
    # Register document
    doc_res = client.post(
        "/documents",
        files={"file": ("capacity_doc.pdf", sample_pdf_bytes, "application/pdf")},
        data={"document_name": "Capacity Test"}
    )
    doc_id = doc_res.json()["document_id"]

    # Attempt release with Tardos enabled but carrier budget smaller than required
    # For c=3, N=3, epsilon=1e-4, required m is > 2000
    rel_res = client.post("/releases", json={
        "document_id": doc_id,
        "issuer_id": "HQ_TEST",
        "recipient_ids": ["alice", "bob", "charlie"],
        "tardos_enabled": True,
        "coalition_size": 3,
        "false_accusation_epsilon": 1e-4,
        "carrier_budget": 50  # Far too small!
    })
    assert rel_res.status_code == 400
    err = rel_res.json()["error"]
    assert err["code"] == "CAPACITY_INSUFFICIENT"
    assert "required_symbols" in err["details"]

def test_release_unregistered_recipient(client: TestClient, sample_pdf_bytes: bytes):
    pdf_b64 = base64.b64encode(sample_pdf_bytes).decode('utf-8')
    rel_res = client.post("/releases", json={
        "document_name": "Ghost.pdf",
        "document_base64": pdf_b64,
        "issuer_id": "HQ_TEST",
        "recipient_ids": ["ghost_user_999"]
    })
    assert rel_res.status_code == 404
    assert rel_res.json()["error"]["code"] == "RECIPIENT_NOT_FOUND"
