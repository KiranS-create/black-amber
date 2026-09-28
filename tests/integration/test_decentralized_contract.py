import base64
import hashlib
import os
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from apps.api.config import config
from apps.api.main import app
from apps.api.models import CreateReleaseRequest, DecryptRequest
from apps.api.orchestrator import default_orchestrator
from core.crypto.signatures import MLDSA65
from core.ledger.ledger import EvidenceEvent, TamperEvidentLedger
from core.provenance.decryption import RecipientDecryptionClient
from core.recipient import default_registry, PublicRecipient
from core.release import ReleaseRecipientPackage
from demo.end_to_end import create_sample_pdf

@pytest.fixture(autouse=True)
def init_clean_state():
    default_registry.init_demo_recipients()
    yield

# --------------------------------------------------------------------------
# 1. Key Custody & Anti-Manufacture Assertions
# --------------------------------------------------------------------------
def test_private_keys_absent_from_api_models(client: TestClient):
    """
    Asserts that POST /recipients and GET /recipients never serialize or expose
    private key bytes in the API contract.
    """
    res = client.post(
        "/recipients",
        json={"name": "Audited User", "recipient_id": "audited_user"},
        headers={"Authorization": "Bearer token_authority_hq"}
    )
    assert res.status_code == 201
    data = res.json()
    assert "kem_public_key_b64" in data
    assert "dsa_public_key_b64" in data
    assert "private_key" not in str(data).lower()
    assert "secret_key" not in str(data).lower()
    assert "private_key_bytes" not in data

    list_res = client.get("/recipients", headers={"Authorization": "Bearer token_auditor_sec"})
    assert list_res.status_code == 200
    for rec in list_res.json():
        assert "private_key_bytes" not in rec
        assert "kem_public_key_b64" in rec

# --------------------------------------------------------------------------
# 2. Decentralized Client-Side Provenance & Server Signature Verification
# --------------------------------------------------------------------------
def test_client_side_provenance_submission_flow(client: TestClient, sample_pdf_bytes: bytes):
    """
    Tests the 10-step decentralized recipient workflow:
    1. Authority creates release.
    2. Bob client fetches isolated recipient package.
    3. Bob decapsulates ML-KEM and decrypts AES-GCM locally (offline).
    4. Bob signs EvidenceEvent with his ML-DSA-65 private key.
    5. Bob submits signed event to POST /evidence/decryption-events.
    6. Server cryptographically verifies ML-DSA-65 signature and binds to ledger.
    """
    pdf_b64 = base64.b64encode(sample_pdf_bytes).decode('utf-8')
    rel = default_orchestrator.create_release(
        CreateReleaseRequest(
            document_name="ContractDoc.pdf",
            document_base64=pdf_b64,
            issuer_id="HQ_AUTHORITY",
            recipient_ids=["alice", "bob", "charlie"]
        )
    )

    # 1. Bob fetches his isolated package
    pkg_res = client.get(
        f"/releases/{rel.release_id}/packages/bob",
        headers={"Authorization": "Bearer token_bob"}
    )
    assert pkg_res.status_code == 200
    package = ReleaseRecipientPackage(**pkg_res.json())

    # 2. Client-side local offline decryption and signing
    bob_rec = default_registry.get("bob")
    dec_client = RecipientDecryptionClient(ledger=None)
    tip_hash = default_orchestrator.ledger.get_last_event_hash()

    plaintext, traceable_bytes, signed_event, _ = dec_client.decrypt_package(
        package=package,
        recipient=bob_rec,
        last_event_hash=tip_hash,
        record_to_ledger=False
    )
    assert hashlib.sha256(plaintext).hexdigest() == rel.original_hash

    # 3. Submit to POST /evidence/decryption-events
    ev_res = client.post(
        "/evidence/decryption-events",
        json=signed_event.model_dump(),
        headers={"Authorization": "Bearer token_bob"}
    )
    assert ev_res.status_code == 201
    assert ev_res.json()["status"] == "SUCCESS"
    assert ev_res.json()["event_id"] == signed_event.event_id

    # 4. Verify also accepted at POST /releases/{release_id}/provenance
    # Create another event with distinct ID for release endpoint testing
    dec_client2 = RecipientDecryptionClient(ledger=None)
    tip_hash2 = default_orchestrator.ledger.get_last_event_hash()
    _, _, signed_event2, _ = dec_client2.decrypt_package(
        package=package,
        recipient=bob_rec,
        last_event_hash=tip_hash2,
        record_to_ledger=False
    )
    rel_prov_res = client.post(
        f"/releases/{rel.release_id}/provenance",
        json=signed_event2.model_dump(),
        headers={"Authorization": "Bearer token_bob"}
    )
    assert rel_prov_res.status_code == 201
    assert rel_prov_res.json()["status"] == "SUCCESS"

# --------------------------------------------------------------------------
# 3. Adversarial Provenance Rejection Tests
# --------------------------------------------------------------------------
def test_forged_signature_rejected(client: TestClient, sample_pdf_bytes: bytes):
    """Corrupted / forged signature bytes must be rejected with 400 INVALID_SIGNATURE."""
    pdf_b64 = base64.b64encode(sample_pdf_bytes).decode('utf-8')
    rel = default_orchestrator.create_release(
        CreateReleaseRequest(
            document_name="ForgedDoc.pdf",
            document_base64=pdf_b64,
            issuer_id="HQ_AUTHORITY",
            recipient_ids=["bob"]
        )
    )
    package = default_orchestrator.get_recipient_package(rel.release_id, "bob")
    bob_rec = default_registry.get("bob")

    dec_client = RecipientDecryptionClient(ledger=None)
    tip_hash = default_orchestrator.ledger.get_last_event_hash()
    _, _, event, _ = dec_client.decrypt_package(
        package=package,
        recipient=bob_rec,
        last_event_hash=tip_hash,
        record_to_ledger=False
    )

    # Forgery: Random signature bytes
    forged_sig = base64.b64encode(os.urandom(3309)).decode('utf-8')
    tampered_event = event.model_copy(update={"signature": forged_sig})

    res = client.post(
        "/evidence/decryption-events",
        json=tampered_event.model_dump(),
        headers={"Authorization": "Bearer token_bob"}
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "INVALID_SIGNATURE"

def test_recipient_substitution_attack_rejected(client: TestClient, sample_pdf_bytes: bytes):
    """
    Attacker (Alice) signs an event specifying recipient_id="bob".
    Server verifies against Bob's registered public key and rejects with 400.
    """
    pdf_b64 = base64.b64encode(sample_pdf_bytes).decode('utf-8')
    rel = default_orchestrator.create_release(
        CreateReleaseRequest(
            document_name="SubstDoc.pdf",
            document_base64=pdf_b64,
            issuer_id="HQ_AUTHORITY",
            recipient_ids=["alice", "bob"]
        )
    )
    package = default_orchestrator.get_recipient_package(rel.release_id, "bob")
    alice_rec = default_registry.get("alice")

    # Alice decrypts package or signs payload purporting to be Bob
    tip_hash = default_orchestrator.ledger.get_last_event_hash()
    event_id = f"evt_impersonate_{os.urandom(4).hex()}"
    timestamp_now = datetime.now(timezone.utc).isoformat()
    traceable_hash = hashlib.sha256(b"fake").hexdigest()

    sign_payload = (
        f"DECRYPTION_PROVENANCE:{event_id}:{package.document_id}:"
        f"{package.release_id}:bob:{traceable_hash}:"
        f"{tip_hash}:{timestamp_now}"
    ).encode('utf-8')

    # Alice signs with ALICE's private key
    alice_sig = base64.b64encode(MLDSA65.sign(alice_rec.dsa_keypair.private_key_bytes, sign_payload)).decode('utf-8')

    impersonation_event = EvidenceEvent(
        event_id=event_id,
        event_type="DECRYPTION_EVENT",
        timestamp=timestamp_now,
        document_id=package.document_id,
        release_id=package.release_id,
        recipient_id="bob",  # Claims to be Bob
        algorithm="ML-DSA-65",
        artifact_hash=traceable_hash,
        evidence_hash=hashlib.sha256(b"ev").hexdigest(),
        previous_event_hash=tip_hash,
        signature=alice_sig  # But signed by Alice
    )

    res = client.post(
        "/evidence/decryption-events",
        json=impersonation_event.model_dump(),
        headers={"Authorization": "Bearer token_bob"}
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "INVALID_SIGNATURE"

def test_wrong_release_and_document_binding_rejected(client: TestClient, sample_pdf_bytes: bytes):
    """
    Submitting provenance event with mismatched document ID or unlinked release ID is rejected.
    """
    pdf_b64 = base64.b64encode(sample_pdf_bytes).decode('utf-8')
    rel = default_orchestrator.create_release(
        CreateReleaseRequest(
            document_name="BindingDoc.pdf",
            document_base64=pdf_b64,
            issuer_id="HQ_AUTHORITY",
            recipient_ids=["bob"]
        )
    )
    package = default_orchestrator.get_recipient_package(rel.release_id, "bob")
    bob_rec = default_registry.get("bob")

    dec_client = RecipientDecryptionClient(ledger=None)
    tip_hash = default_orchestrator.ledger.get_last_event_hash()
    _, _, event, _ = dec_client.decrypt_package(
        package=package,
        recipient=bob_rec,
        last_event_hash=tip_hash,
        record_to_ledger=False
    )

    # 1. Wrong document binding
    mismatched_doc_event = event.model_copy(update={"document_id": "doc_unrelated_12345"})
    res1 = client.post(
        "/evidence/decryption-events",
        json=mismatched_doc_event.model_dump(),
        headers={"Authorization": "Bearer token_bob"}
    )
    assert res1.status_code == 400
    assert res1.json()["error"]["code"] == "INVALID_RELEASE"

    # 2. Wrong release binding
    mismatched_rel_event = event.model_copy(update={"release_id": "rel_nonexistent_99999"})
    res2 = client.post(
        "/evidence/decryption-events",
        json=mismatched_rel_event.model_dump(),
        headers={"Authorization": "Bearer token_bob"}
    )
    assert res2.status_code in (400, 404)

def test_replay_and_duplicate_event_rejection(client: TestClient, sample_pdf_bytes: bytes):
    """
    Submitting the exact same EvidenceEvent twice is rejected by ledger deduplication.
    """
    pdf_b64 = base64.b64encode(sample_pdf_bytes).decode('utf-8')
    rel = default_orchestrator.create_release(
        CreateReleaseRequest(
            document_name="ReplayDoc.pdf",
            document_base64=pdf_b64,
            issuer_id="HQ_AUTHORITY",
            recipient_ids=["bob"]
        )
    )
    package = default_orchestrator.get_recipient_package(rel.release_id, "bob")
    bob_rec = default_registry.get("bob")

    dec_client = RecipientDecryptionClient(ledger=None)
    tip_hash = default_orchestrator.ledger.get_last_event_hash()
    _, _, event, _ = dec_client.decrypt_package(
        package=package,
        recipient=bob_rec,
        last_event_hash=tip_hash,
        record_to_ledger=False
    )

    # First submission succeeds
    res1 = client.post(
        "/evidence/decryption-events",
        json=event.model_dump(),
        headers={"Authorization": "Bearer token_bob"}
    )
    assert res1.status_code == 201

    # Replay of identical event is rejected
    res2 = client.post(
        "/evidence/decryption-events",
        json=event.model_dump(),
        headers={"Authorization": "Bearer token_bob"}
    )
    assert res2.status_code in (400, 409)
    assert res2.json()["error"]["code"] in ("INVALID_RELEASE", "REPLAY_DETECTED")

# --------------------------------------------------------------------------
# 4. Full-System End-to-End Contract with Evidence Fusion & Adversarial Sweeps
# --------------------------------------------------------------------------
def test_full_system_contract_with_fusion(client: TestClient, sample_pdf_bytes: bytes):
    """
    Full deterministic contract test across Alice, Bob, Charlie and Document A.
    - Bob receives and decapsulates package locally.
    - Bob signs provenance event.
    - Server verifies and logs event.
    - Bob leak is analyzed.
    - Fusion pipeline verifies target binding, Tardos observation, provenance signature, ledger event.
    - Verify ATTRIBUTED to Bob.
    """
    pdf_b64 = base64.b64encode(sample_pdf_bytes).decode('utf-8')

    # 1. Authority creates release
    rel_res = client.post(
        "/releases",
        json={
            "document_name": "Classified_Alpha.pdf",
            "document_base64": pdf_b64,
            "issuer_id": "HQ_AUTHORITY",
            "recipient_ids": ["alice", "bob", "charlie"]
        },
        headers={"Authorization": "Bearer token_authority_hq"}
    )
    assert rel_res.status_code == 200
    release_id = rel_res.json()["release_id"]
    doc_id = rel_res.json()["document_id"]

    # 2. Bob retrieves package
    pkg_res = client.get(
        f"/releases/{release_id}/packages/bob",
        headers={"Authorization": "Bearer token_bob"}
    )
    assert pkg_res.status_code == 200
    package = ReleaseRecipientPackage(**pkg_res.json())

    # 3. Bob local decryption & signing
    bob_rec = default_registry.get("bob")
    dec_client = RecipientDecryptionClient(ledger=None)
    tip_hash = default_orchestrator.ledger.get_last_event_hash()
    plaintext, bob_traceable_bytes, event, _ = dec_client.decrypt_package(
        package=package,
        recipient=bob_rec,
        last_event_hash=tip_hash,
        record_to_ledger=False
    )

    # 4. Bob submits signed provenance event to server
    prov_res = client.post(
        "/evidence/decryption-events",
        json=event.model_dump(),
        headers={"Authorization": "Bearer token_bob"}
    )
    assert prov_res.status_code == 201

    # 5. Ingest Bob's leak
    leak_res = client.post(
        "/leaks",
        files={"file": ("bob_leak.pdf", bob_traceable_bytes, "application/pdf")},
        data={"suspected_release_id": release_id, "suspected_document_id": doc_id},
        headers={"Authorization": "Bearer token_auditor_sec"}
    )
    assert leak_res.status_code == 201
    leak_id = leak_res.json()["leak_id"]

    # 6. Execute Evidence Fusion Analysis
    analyze_res = client.post(
        "/analyze",
        json={
            "leak_id": leak_id,
            "expected_release_id": release_id,
            "expected_document_id": doc_id,
            "async_execution": False
        },
        headers={"Authorization": "Bearer token_auditor_sec"}
    )
    assert analyze_res.status_code == 200
    result = analyze_res.json()["result"]

    assert result["state"] == "ATTRIBUTED"
    assert result["should_abstain"] is False
    assert result["candidate"]["recipient_id"] == "bob"
    assert result["confidence"] >= 0.99
    assert result["confidence_level"] == "HIGH"
    assert event.event_id in result["candidate"]["verified_events"]

    # 7. Capabilities check reflects the new architecture
    cap_res = client.get("/capabilities")
    assert cap_res.status_code == 200
    caps = cap_res.json()
    assert caps["key_custody_model"] == "DECENTRALIZED_CLIENT_CUSTODY"
    assert "POST /evidence/decryption-events" in caps["client_workflows"]["server_provenance_endpoints"]
