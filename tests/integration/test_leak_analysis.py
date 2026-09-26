import base64
import time
import pytest
from fastapi.testclient import TestClient

def test_leak_upload_and_download(client: TestClient, sample_pdf_bytes: bytes):
    # Upload leak
    leak_res = client.post(
        "/leaks",
        files={"file": ("intercepted_leak.pdf", sample_pdf_bytes, "application/pdf")},
        data={"suspected_document_id": "doc_sample_123"}
    )
    assert leak_res.status_code == 201
    data = leak_res.json()
    assert data["leak_id"].startswith("leak_")
    assert data["suspected_document_id"] == "doc_sample_123"
    leak_id = data["leak_id"]

    # Retrieve leak metadata
    get_res = client.get(f"/leaks/{leak_id}")
    assert get_res.status_code == 200
    assert get_res.json()["leak_id"] == leak_id

    # Download leak bytes
    down_res = client.get(f"/leaks/{leak_id}/download")
    assert down_res.status_code == 200
    assert down_res.content == sample_pdf_bytes

def test_synchronous_analysis_lifecycle(client: TestClient, sample_pdf_bytes: bytes):
    # 1. Create release & decrypt as Alice
    pdf_b64 = base64.b64encode(sample_pdf_bytes).decode('utf-8')
    rel_res = client.post("/releases", json={
        "document_name": "SyncDoc.pdf",
        "document_base64": pdf_b64,
        "issuer_id": "HQ_TEST",
        "recipient_ids": ["alice", "bob"]
    })
    release_id = rel_res.json()["release_id"]

    dec_res = client.post(f"/releases/{release_id}/decrypt", json={"recipient_id": "alice"})
    alice_traceable_b64 = dec_res.json()["traceable_document_base64"]
    alice_traceable_bytes = base64.b64decode(alice_traceable_b64)

    # 2. Upload leak
    leak_res = client.post(
        "/leaks",
        files={"file": ("alice_leak.pdf", alice_traceable_bytes, "application/pdf")},
        data={"suspected_release_id": release_id}
    )
    leak_id = leak_res.json()["leak_id"]

    # 3. Synchronous analysis with attack telemetry
    analyze_res = client.post("/analyze", json={
        "leak_id": leak_id,
        "expected_release_id": release_id,
        "attack_telemetry": {
            "attack_id": "atk_crop_01",
            "attack_family": "DIGITAL_DOCUMENT",
            "parameters": {"pages_removed": 0},
            "physical_or_simulated": "SIMULATED"
        },
        "async_execution": False
    })
    assert analyze_res.status_code == 200
    job = analyze_res.json()
    assert job["status"] == "COMPLETED"
    assert job["result"] is not None
    assert job["result"]["state"] == "ATTRIBUTED"
    assert job["result"]["candidate"]["recipient_id"] == "alice"
    assert job["result"]["should_abstain"] is False

def test_asynchronous_analysis_job(client: TestClient, sample_pdf_bytes: bytes):
    # 1. Create release & decrypt as Bob
    pdf_b64 = base64.b64encode(sample_pdf_bytes).decode('utf-8')
    rel_res = client.post("/releases", json={
        "document_name": "AsyncDoc.pdf",
        "document_base64": pdf_b64,
        "issuer_id": "HQ_TEST",
        "recipient_ids": ["bob"]
    })
    release_id = rel_res.json()["release_id"]

    dec_res = client.post(f"/releases/{release_id}/decrypt", json={"recipient_id": "bob"})
    bob_traceable_b64 = dec_res.json()["traceable_document_base64"]
    bob_bytes = base64.b64decode(bob_traceable_b64)

    # 2. Upload leak
    leak_res = client.post(
        "/leaks",
        files={"file": ("bob_leak.pdf", bob_bytes, "application/pdf")},
        data={"suspected_release_id": release_id}
    )
    leak_id = leak_res.json()["leak_id"]

    # 3. Submit async analysis
    submit_res = client.post("/analyze", json={
        "leak_id": leak_id,
        "expected_release_id": release_id,
        "async_execution": True
    })
    assert submit_res.status_code == 200
    job = submit_res.json()
    analysis_id = job["analysis_id"]

    # 4. Poll job status
    max_retries = 20
    completed = False
    for _ in range(max_retries):
        status_res = client.get(f"/analysis/{analysis_id}")
        assert status_res.status_code == 200
        cur_job = status_res.json()
        if cur_job["status"] in ("COMPLETED", "ABSTAINED", "FAILED"):
            completed = True
            assert cur_job["status"] == "COMPLETED"
            assert cur_job["result"]["candidate"]["recipient_id"] == "bob"
            break
        time.sleep(0.1)

    assert completed is True

def test_analysis_job_listing(client: TestClient):
    res = client.get("/analysis")
    assert res.status_code == 200
    data = res.json()
    assert "jobs" in data
    assert data["total"] >= 1
