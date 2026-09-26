import pytest
import base64
from fastapi.testclient import TestClient
from apps.api.main import app
from demo.end_to_end import create_sample_pdf

client = TestClient(app)

def test_api_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_api_recipients():
    # List demo recipients
    response = client.get("/recipients")
    assert response.status_code == 200
    recipients = response.json()
    assert len(recipients) >= 3
    ids = [r["recipient_id"] for r in recipients]
    assert "alice" in ids
    assert "bob" in ids
    assert "charlie" in ids

def test_api_full_flow():
    pdf_bytes = create_sample_pdf()
    pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')

    # 1. Create release
    rel_res = client.post("/releases", json={
        "document_name": "TestDoc.pdf",
        "document_base64": pdf_b64,
        "issuer_id": "HQ_TEST",
        "recipient_ids": ["alice", "bob", "charlie"]
    })
    assert rel_res.status_code == 200
    rel_data = rel_res.json()
    release_id = rel_data["release_id"]
    assert "bob" in rel_data["packages"]

    # 2. Bob decrypts
    dec_res = client.post(f"/releases/{release_id}/decrypt", json={"recipient_id": "bob"})
    assert dec_res.status_code == 200
    dec_data = dec_res.json()
    assert dec_data["status"] == "SUCCESS"
    bob_traceable_b64 = dec_data["traceable_document_base64"]

    # 3. Analyze leak
    leak_res = client.post("/leaks/analyze", json={
        "leaked_document_base64": bob_traceable_b64,
        "release_id": release_id
    })
    assert leak_res.status_code == 200
    leak_data = leak_res.json()
    assert leak_data["state"] == "ATTRIBUTED"
    assert leak_data["candidate"]["recipient_id"] == "bob"

    # 4. Check ledger evidence & verify
    ev_res = client.get(f"/evidence/{release_id}")
    assert ev_res.status_code == 200
    assert len(ev_res.json()) >= 1

    ledger_res = client.get("/ledger/verify")
    assert ledger_res.status_code == 200
    assert ledger_res.json()["is_valid"] is True
