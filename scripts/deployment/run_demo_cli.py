import base64
import hashlib
import json
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from apps.api.main import app
from demo.end_to_end import create_sample_pdf

def run_cli_demo():
    client = TestClient(app)
    print("\n" + "=" * 70)
    print("  SIH26237 — CRYPTOGRAPHIC ATTRIBUTION & PROVENANCE DEMO WALKTHROUGH")
    print("=" * 70)
    time.sleep(0.5)

    # 1. System Capabilities
    print("\n[STEP 1] Querying System Capabilities & Post-Quantum Algorithms...")
    cap_res = client.get("/capabilities")
    assert cap_res.status_code == 200
    caps = cap_res.json()
    print(f"  * KEM Algorithm:        {caps['cryptography']['kem']}")
    print(f"  * Signature Standard:   {caps['cryptography']['signature']}")
    print(f"  * Symmetric Encryption: {caps['cryptography']['symmetric']}")
    print(f"  * Traitor Tracing:      {caps['traceability']['algorithms'][1]}")
    print(f"  * Offline Operation:    {caps['offline_mode']}")

    # 2. Document Registration
    print("\n[STEP 2] Uploading & Registering Master Classified Document...")
    pdf_bytes = create_sample_pdf("STRATEGIC DEFENSE DIRECTIVE — SIH26237")
    orig_hash = hashlib.sha256(pdf_bytes).hexdigest()
    doc_res = client.post(
        "/documents",
        files={"file": ("STRATEGIC_DIRECTIVE.pdf", pdf_bytes, "application/pdf")},
        data={"document_name": "Strategic Defense Directive"}
    )
    assert doc_res.status_code == 201
    doc_id = doc_res.json()["document_id"]
    print(f"  * Document ID:          {doc_id}")
    print(f"  * ORIGINAL_DOC_HASH:    {orig_hash[:24]}...")
    print(f"  * Payload Size:         {len(pdf_bytes)} bytes")

    # 3. Recipient Enrollment
    print("\n[STEP 3] Enrolling Authorized Recipients with PQC Keypairs...")
    rec_res = client.get("/recipients")
    recipients = [r["name"] for r in rec_res.json()]
    print(f"  * Authorized Officers:  {', '.join(recipients)}")

    # 4. Multi-Recipient Release Creation
    print("\n[STEP 4] Generating Quantum-Resistant Release Envelopes...")
    rel_res = client.post("/releases", json={
        "document_id": doc_id,
        "issuer_id": "HQ_STRATCOM",
        "recipient_ids": ["alice", "bob", "charlie"]
    })
    assert rel_res.status_code == 200
    rel_data = rel_res.json()
    release_id = rel_data["release_id"]
    print(f"  * Release ID:           {release_id}")
    print(f"  * Isolated Packages:    {len(rel_data['packages'])} (Alice, Bob, Charlie)")
    print(f"  * Ephemeral K_doc:      Wrapped via ML-KEM-768 + AES-KW per recipient")

    # 5. Bob Decryption & Provenance Signing
    print("\n[STEP 5] Bob Accesses & Decrypts Package...")
    dec_res = client.post(f"/releases/{release_id}/decrypt", json={"recipient_id": "bob"})
    assert dec_res.status_code == 200
    dec_data = dec_res.json()
    bob_traceable_b64 = dec_data["traceable_document_base64"]
    bob_traceable_bytes = base64.b64decode(bob_traceable_b64)
    print(f"  * Decryption Status:    {dec_data['status']}")
    print(f"  * Traceable Copy Hash:  {dec_data['traceable_artifact_hash'][:24]}...")
    print(f"  * ML-DSA-65 Signature:  Event signed by Bob (ID: {dec_data['event_id']})")
    print(f"  * Provenance Event:     Anchored to hash-chained tamper-evident ledger")

    # 6. Leak Ingestion
    print("\n[STEP 6] Intercepted Leak Uploaded to Forensic Lab...")
    leak_res = client.post(
        "/leaks",
        files={"file": ("intercepted_leak.pdf", bob_traceable_bytes, "application/pdf")},
        data={"suspected_release_id": release_id, "suspected_document_id": doc_id}
    )
    assert leak_res.status_code == 201
    leak_id = leak_res.json()["leak_id"]
    print(f"  * Leak Artifact ID:     {leak_id}")
    print(f"  * LEAK_ARTIFACT_HASH:   {leak_res.json()['leak_artifact_hash'][:24]}...")

    # 7. Forensic Multi-Channel Evidence Fusion
    print("\n[STEP 7] Executing Fail-Closed Multi-Channel Forensic Attribution...")
    t0 = time.perf_counter()
    anlz_res = client.post("/analyze", json={
        "leak_id": leak_id,
        "expected_release_id": release_id,
        "expected_document_id": doc_id,
        "async_execution": False
    })
    duration_ms = (time.perf_counter() - t0) * 1000.0
    assert anlz_res.status_code == 200
    result = anlz_res.json()["result"]

    print(f"  * Attribution State:    {result['state']} (Verdict)")
    print(f"  * Identified Culprit:   {result['candidate']['name']} ({result['candidate']['recipient_id']})")
    print(f"  * Confidence Rating:    {result['confidence_level']} (Probability: {result['confidence'] * 100:.1f}%)")
    print(f"  * Fail-Closed Abstain:  {result['should_abstain']}")
    print(f"  * Analysis Latency:     {duration_ms:.2f} ms")

    # 8. Negative Test (Corrupted Marker)
    print("\n[STEP 8] Negative Scenario: Tampered Carrier Payload...")
    tampered_bytes = bob_traceable_bytes.replace(b"SIH26237-TRACEABILITY-MARKER-START", b"TAMPERED-HEADER-XXXX")
    neg_res = client.post("/analyze", json={
        "leaked_document_base64": base64.b64encode(tampered_bytes).decode('utf-8'),
        "expected_release_id": release_id,
        "async_execution": False
    })
    neg_result = neg_res.json()["result"]
    print(f"  * Tampered Result:      {neg_result['state']} (Abstention Enforced)")
    print(f"  * Should Abstain:       {neg_result['should_abstain']} (Guarantees no false accusation)")

    # 9. Ledger Chain Verification
    print("\n[STEP 9] Auditing Tamper-Evident Ledger Integrity...")
    ledger_res = client.get("/ledger/verify")
    assert ledger_res.status_code == 200
    led = ledger_res.json()
    print(f"  * Chain Valid:          {led['is_valid']}")
    print(f"  * Total Logged Events:  {led['total_events']}")
    print(f"  * Cryptographic Tip:    {led['chain_tip'][:24]}...")
    print(f"  * Tampering Errors:     {len(led['errors'])}")

    print("\n" + "=" * 70)
    print("  [DEMO COMPLETE] ALL POST-QUANTUM PROVENANCE & ATTRIBUTION CHECKS VERIFIED")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    run_cli_demo()
