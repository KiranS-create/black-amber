import base64
import hashlib
import pytest
from fastapi.testclient import TestClient
from demo.end_to_end import create_sample_pdf

def test_deterministic_lifecycle_reproducibility(client: TestClient):
    """
    Executes identical document release and attribution lifecycles twice.
    Verifies that all deterministic fields (document hash, candidate decisions,
    confidence ratings, abstention flags) are 100% reproducible.
    """
    doc_bytes = create_sample_pdf("REPRODUCIBILITY REPETITION TEST SPECIFICATION")
    doc_hash = hashlib.sha256(doc_bytes).hexdigest()

    runs = []
    for i in range(2):
        # 1. Register Document
        doc_res = client.post(
            "/documents",
            files={"file": (f"doc_run_{i}.pdf", doc_bytes, "application/pdf")},
            data={"document_name": f"Repro Document {i}"}
        )
        assert doc_res.status_code == 201
        doc_id = doc_res.json()["document_id"]
        assert doc_res.json()["original_document_hash"] == doc_hash

        # 2. Create Release
        rel_res = client.post("/releases", json={
            "document_id": doc_id,
            "issuer_id": "HQ_TEST",
            "recipient_ids": ["alice", "bob"]
        })
        assert rel_res.status_code == 200
        rel_data = rel_res.json()
        release_id = rel_data["release_id"]

        # 3. Decrypt as Bob
        dec_res = client.post(f"/releases/{release_id}/decrypt", json={"recipient_id": "bob"})
        assert dec_res.status_code == 200
        dec_data = dec_res.json()
        bob_traceable_b64 = dec_data["traceable_document_base64"]

        # 4. Analyze Bob Leak
        anlz_res = client.post("/analyze", json={
            "leaked_document_base64": bob_traceable_b64,
            "expected_release_id": release_id,
            "async_execution": False
        })
        assert anlz_res.status_code == 200
        result = anlz_res.json()["result"]

        # 5. Analyze Tampered Leak
        bob_bytes = base64.b64decode(bob_traceable_b64)
        tampered_bytes = bob_bytes.replace(b"SIH26237-TRACEABILITY-MARKER-START", b"CORRUPTED-XXXX")
        tamper_res = client.post("/analyze", json={
            "leaked_document_base64": base64.b64encode(tampered_bytes).decode('utf-8'),
            "expected_release_id": release_id,
            "async_execution": False
        })
        tamper_result = tamper_res.json()["result"]

        runs.append({
            "doc_hash": doc_hash,
            "decision_state": result["state"],
            "candidate_id": result["candidate"]["recipient_id"],
            "confidence": result["confidence"],
            "confidence_level": result["confidence_level"],
            "should_abstain": result["should_abstain"],
            "tamper_state": tamper_result["state"],
            "tamper_abstain": tamper_result["should_abstain"]
        })

    # Compare Run 0 vs Run 1
    assert runs[0]["doc_hash"] == runs[1]["doc_hash"]
    assert runs[0]["decision_state"] == runs[1]["decision_state"] == "ATTRIBUTED"
    assert runs[0]["candidate_id"] == runs[1]["candidate_id"] == "bob"
    assert runs[0]["confidence"] == runs[1]["confidence"] == 0.99
    assert runs[0]["confidence_level"] == runs[1]["confidence_level"] == "HIGH"
    assert runs[0]["should_abstain"] == runs[1]["should_abstain"] is False
    assert runs[0]["tamper_state"] == runs[1]["tamper_state"]
    assert runs[0]["tamper_abstain"] == runs[1]["tamper_abstain"] is True
