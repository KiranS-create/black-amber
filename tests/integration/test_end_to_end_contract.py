import base64
import hashlib
import pytest
from fastapi.testclient import TestClient

def test_deterministic_end_to_end_contract(client: TestClient, sample_pdf_bytes: bytes):
    """
    Deterministic End-to-End Contract Test:
    1. Master document registration.
    2. Recipient enrollment (Alice, Bob, Charlie).
    3. Multi-recipient quantum-resistant release creation.
    4. Bob decrypts release package (signed provenance logged in ledger).
    5. Bob leak artifact is intercepted and submitted for analysis.
    6. Verify:
       - Exact attribution to Bob (state == ATTRIBUTED).
       - Confidence >= 0.99 (HIGH).
       - Verified events correspond to Bob's signed decryption event.
       - Non-repudiation signature verified.
       - Fail-closed abstention is False.
    """
    # 1. Register Document
    doc_res = client.post(
        "/documents",
        files={"file": ("TOP_SECRET_ORCHESTRATION.pdf", sample_pdf_bytes, "application/pdf")},
        data={"document_name": "Classified Project Directive"}
    )
    assert doc_res.status_code == 201
    doc_meta = doc_res.json()
    doc_id = doc_meta["document_id"]
    orig_hash = doc_meta["original_document_hash"]
    assert orig_hash == hashlib.sha256(sample_pdf_bytes).hexdigest()

    # 2. Verify Recipients
    rec_res = client.get("/recipients")
    assert rec_res.status_code == 200
    recipients = {r["recipient_id"]: r for r in rec_res.json()}
    assert "alice" in recipients
    assert "bob" in recipients
    assert "charlie" in recipients

    # 3. Create Multi-Recipient Release
    rel_res = client.post("/releases", json={
        "document_id": doc_id,
        "issuer_id": "HQ_STRATCOM",
        "recipient_ids": ["alice", "bob", "charlie"]
    })
    assert rel_res.status_code == 200
    release = rel_res.json()
    release_id = release["release_id"]
    assert release["document_id"] == doc_id
    assert release["original_hash"] == orig_hash
    assert len(release["packages"]) == 3

    # 4. Bob Decrypts Package
    dec_res = client.post(f"/releases/{release_id}/decrypt", json={"recipient_id": "bob"})
    assert dec_res.status_code == 200
    dec_data = dec_res.json()
    assert dec_data["status"] == "SUCCESS"
    assert dec_data["recipient_id"] == "bob"
    assert dec_data["original_document_hash"] == orig_hash
    bob_traceable_bytes = base64.b64decode(dec_data["traceable_document_base64"])
    bob_traceable_hash = dec_data["traceable_artifact_hash"]
    assert hashlib.sha256(bob_traceable_bytes).hexdigest() == bob_traceable_hash

    # 5. Ingest Bob's Leaked Copy
    leak_res = client.post(
        "/leaks",
        files={"file": ("bob_intercepted_leak.pdf", bob_traceable_bytes, "application/pdf")},
        data={"suspected_document_id": doc_id, "suspected_release_id": release_id}
    )
    assert leak_res.status_code == 201
    leak_id = leak_res.json()["leak_id"]
    assert leak_res.json()["leak_artifact_hash"] == bob_traceable_hash

    # 6. Execute Analysis
    analyze_res = client.post("/analyze", json={
        "leak_id": leak_id,
        "expected_release_id": release_id,
        "expected_document_id": doc_id,
        "async_execution": False
    })
    assert analyze_res.status_code == 200
    job_data = analyze_res.json()
    assert job_data["status"] == "COMPLETED"
    result = job_data["result"]

    # Attribution verification
    assert result["state"] == "ATTRIBUTED"
    assert result["should_abstain"] is False
    assert result["candidate"] is not None
    assert result["candidate"]["recipient_id"] == "bob"
    assert result["candidate"]["name"] == "Bob"
    assert result["confidence"] >= 0.99
    assert result["confidence_level"] == "HIGH"
    assert dec_data["event_id"] in result["candidate"]["verified_events"]

    # Evidence items verification
    evidence_sources = [item["source"] for item in result["evidence_items"]]
    assert "TRACEABILITY_MARKER" in evidence_sources
    assert "AUDIT_LEDGER" in evidence_sources
    assert "RECIPIENT_SIGNATURE" in evidence_sources

def test_tampered_artifact_abstains(client: TestClient, sample_pdf_bytes: bytes):
    """Tampering with carrier bytes or marker forces fail-closed abstention."""
    pdf_b64 = base64.b64encode(sample_pdf_bytes).decode('utf-8')
    rel_res = client.post("/releases", json={
        "document_name": "TamperTest.pdf",
        "document_base64": pdf_b64,
        "issuer_id": "HQ_TEST",
        "recipient_ids": ["alice"]
    })
    release_id = rel_res.json()["release_id"]

    dec_res = client.post(f"/releases/{release_id}/decrypt", json={"recipient_id": "alice"})
    traceable_bytes = base64.b64decode(dec_res.json()["traceable_document_base64"])

    # Tamper with the marker payload by corrupting the token string
    tampered_bytes = traceable_bytes.replace(b"SIH26237-TRACEABILITY-MARKER-START", b"CORRUPTED-MARKER-HEADER-XXXX")

    analyze_res = client.post("/analyze", json={
        "leaked_document_base64": base64.b64encode(tampered_bytes).decode('utf-8'),
        "expected_release_id": release_id,
        "async_execution": False
    })
    assert analyze_res.status_code == 200
    job = analyze_res.json()
    # When marker header is missing, state is NO_SIGNAL and should_abstain is True
    assert job["result"]["state"] in ("NO_SIGNAL", "INSUFFICIENT_EVIDENCE")
    assert job["result"]["should_abstain"] is True
    assert job["result"]["candidate"] is None

def test_wrong_release_abstains(client: TestClient, sample_pdf_bytes: bytes):
    """Artifact evaluated against an unrelated release ID results in CONFLICT / ABSTAIN."""
    pdf_b64 = base64.b64encode(sample_pdf_bytes).decode('utf-8')
    rel_res = client.post("/releases", json={
        "document_name": "ReleaseA.pdf",
        "document_base64": pdf_b64,
        "issuer_id": "HQ_TEST",
        "recipient_ids": ["alice"]
    })
    release_id_a = rel_res.json()["release_id"]

    dec_res = client.post(f"/releases/{release_id_a}/decrypt", json={"recipient_id": "alice"})
    alice_bytes = base64.b64decode(dec_res.json()["traceable_document_base64"])

    # Analyze with mismatched release ID
    analyze_res = client.post("/analyze", json={
        "leaked_document_base64": base64.b64encode(alice_bytes).decode('utf-8'),
        "expected_release_id": "rel_unrelated_release_99999",
        "async_execution": False
    })
    assert analyze_res.status_code == 200
    job = analyze_res.json()
    assert job["result"]["state"] == "CONFLICT"
    assert job["result"]["should_abstain"] is True

def test_wrong_document_abstains(client: TestClient, sample_pdf_bytes: bytes):
    """Artifact evaluated against an unrelated document ID results in CONFLICT / ABSTAIN."""
    pdf_b64 = base64.b64encode(sample_pdf_bytes).decode('utf-8')
    rel_res = client.post("/releases", json={
        "document_name": "DocA.pdf",
        "document_base64": pdf_b64,
        "issuer_id": "HQ_TEST",
        "recipient_ids": ["alice"]
    })
    release_id = rel_res.json()["release_id"]

    dec_res = client.post(f"/releases/{release_id}/decrypt", json={"recipient_id": "alice"})
    alice_bytes = base64.b64decode(dec_res.json()["traceable_document_base64"])

    # Analyze with mismatched document ID
    analyze_res = client.post("/analyze", json={
        "leaked_document_base64": base64.b64encode(alice_bytes).decode('utf-8'),
        "expected_release_id": release_id,
        "expected_document_id": "doc_unrelated_doc_99999",
        "async_execution": False
    })
    assert analyze_res.status_code == 200
    job = analyze_res.json()
    assert job["result"]["state"] == "CONFLICT"
    assert job["result"]["should_abstain"] is True

def test_untracked_document_no_signal(client: TestClient, sample_pdf_bytes: bytes):
    """Pristine document without any embedded marker produces NO_SIGNAL."""
    clean_b64 = base64.b64encode(sample_pdf_bytes).decode('utf-8')
    analyze_res = client.post("/analyze", json={
        "leaked_document_base64": clean_b64,
        "async_execution": False
    })
    assert analyze_res.status_code == 200
    job = analyze_res.json()
    assert job["result"]["state"] == "NO_SIGNAL"
    assert job["result"]["should_abstain"] is True
    assert job["result"]["candidate"] is None
