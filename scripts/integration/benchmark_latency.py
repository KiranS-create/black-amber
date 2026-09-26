import base64
import json
import os
import sys
import time
from pathlib import Path

# Ensure project root is in python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from fastapi.testclient import TestClient
from apps.api.main import app
from apps.api.config import config
from apps.api.orchestrator import default_orchestrator
from demo.end_to_end import create_sample_pdf
from core.crypto.kem import MLKEM768
from core.crypto.signatures import MLDSA65
from core.crypto.symmetric import generate_symmetric_key, encrypt_aes_gcm
from core.provenance.decryption import RecipientDecryptionClient
from core.recipient import default_registry
from core.release import ReleaseRecipientPackage
from core.traceability.provider import PrototypeTraceabilityProvider, TardosTraceabilityProvider
from core.attribution.engine import AttributionEngine

def run_benchmark():
    client = TestClient(app)
    results = {}
    print("=" * 70)
    print("  SIH26237 POST-SECURITY ORCHESTRATION LATENCY BENCHMARK")
    print("  Decentralized Client-Side Provenance & Server Verification")
    print("=" * 70)

    # Ensure demo recipients are present
    default_registry.init_demo_recipients()

    # Prepare document
    pdf_bytes = create_sample_pdf("BENCHMARK SAMPLE DOCUMENT - SIH26237")
    pdf_size_kb = len(pdf_bytes) / 1024.0
    print(f"Sample PDF Size: {pdf_size_kb:.2f} KB ({len(pdf_bytes)} bytes)\n")

    # 1. Document Registration
    t0 = time.perf_counter()
    doc_res = client.post(
        "/documents",
        files={"file": ("bench_doc.pdf", pdf_bytes, "application/pdf")},
        data={"document_name": "Benchmark Document"},
        headers={"Authorization": "Bearer token_authority_hq"}
    )
    t_doc = (time.perf_counter() - t0) * 1000.0
    assert doc_res.status_code == 201
    doc_data = doc_res.json()
    doc_id = doc_data["document_id"]
    results["document_registration_ms"] = round(t_doc, 2)
    print(f"[1] Document Registration (Server):               {t_doc:7.2f} ms")

    # 2. Release Creation (3 recipients: Alice, Bob, Charlie)
    t0 = time.perf_counter()
    rel_res = client.post(
        "/releases",
        json={
            "document_id": doc_id,
            "issuer_id": "HQ_BENCHMARK",
            "recipient_ids": ["alice", "bob", "charlie"]
        },
        headers={"Authorization": "Bearer token_authority_hq"}
    )
    t_rel = (time.perf_counter() - t0) * 1000.0
    assert rel_res.status_code == 200
    rel_data = rel_res.json()
    release_id = rel_data["release_id"]
    results["release_creation_3_recipients_ms"] = round(t_rel, 2)
    print(f"[2] Release Packaging (Server ML-KEM Encap):     {t_rel:7.2f} ms")

    # 3. Recipient Package Retrieval (Bob)
    t0 = time.perf_counter()
    pkg_res = client.get(
        f"/releases/{release_id}/packages/bob",
        headers={"Authorization": "Bearer token_bob"}
    )
    t_pkg = (time.perf_counter() - t0) * 1000.0
    assert pkg_res.status_code == 200
    pkg_dict = pkg_res.json()
    package = ReleaseRecipientPackage(**pkg_dict)
    results["recipient_package_retrieval_ms"] = round(t_pkg, 2)
    print(f"[3] Recipient Package Fetch (Server IDOR check): {t_pkg:7.2f} ms")

    # 4. Client-Side Cryptographic Decryption & ML-DSA-65 Signing (Local/Offline)
    bob_rec = default_registry.get("bob")
    dec_client = RecipientDecryptionClient(ledger=None)
    tip_hash = default_orchestrator.ledger.get_last_event_hash()

    t0 = time.perf_counter()
    plaintext, traceable_bytes, signed_event, _ = dec_client.decrypt_package(
        package=package,
        recipient=bob_rec,
        last_event_hash=tip_hash,
        record_to_ledger=False
    )
    t_client_dec = (time.perf_counter() - t0) * 1000.0
    results["client_side_decryption_and_signing_ms"] = round(t_client_dec, 2)
    print(f"[4] Client Decapsulation & ML-DSA Signing (Local):{t_client_dec:7.2f} ms")

    # 5. Server-Side Provenance Ingestion & ML-DSA Verification
    t0 = time.perf_counter()
    prov_res = client.post(
        "/evidence/decryption-events",
        json=signed_event.model_dump(),
        headers={"Authorization": "Bearer token_bob"}
    )
    t_server_prov = (time.perf_counter() - t0) * 1000.0
    assert prov_res.status_code == 201
    results["server_provenance_verification_and_append_ms"] = round(t_server_prov, 2)
    print(f"[5] Server Provenance Verification & Ledger Append: {t_server_prov:7.2f} ms")

    # 6. End-to-End Verified Provenance Workflow Total
    t_e2e_prov = t_pkg + t_client_dec + t_server_prov
    results["end_to_end_verified_provenance_workflow_ms"] = round(t_e2e_prov, 2)
    print(f"[*] End-to-End Verified Provenance Workflow:     {t_e2e_prov:7.2f} ms")

    # 7. Simulated Local Demo Oracle (Comparison)
    t0 = time.perf_counter()
    sim_res = client.post(
        f"/releases/{release_id}/decrypt",
        json={"recipient_id": "alice"},
        headers={"Authorization": "Bearer token_alice"}
    )
    t_sim = (time.perf_counter() - t0) * 1000.0
    assert sim_res.status_code == 200
    results["simulated_local_oracle_decrypt_ms"] = round(t_sim, 2)
    print(f"[6] [Simulated Demo Oracle] Local Decrypt Route: {t_sim:7.2f} ms")

    # 8. Leak Ingestion (Upload to Data Plane)
    t0 = time.perf_counter()
    leak_res = client.post(
        "/leaks",
        files={"file": ("leak.pdf", traceable_bytes, "application/pdf")},
        data={"suspected_release_id": release_id},
        headers={"Authorization": "Bearer token_auditor_sec"}
    )
    t_leak = (time.perf_counter() - t0) * 1000.0
    assert leak_res.status_code == 201
    leak_data = leak_res.json()
    leak_id = leak_data["leak_id"]
    results["leak_artifact_upload_ms"] = round(t_leak, 2)
    print(f"[7] Leak Artifact Ingestion:                     {t_leak:7.2f} ms")

    # 9. Complete Synchronous Forensic Analysis
    t0 = time.perf_counter()
    sync_res = client.post(
        "/analyze",
        json={
            "leak_id": leak_id,
            "expected_release_id": release_id,
            "async_execution": False
        },
        headers={"Authorization": "Bearer token_auditor_sec"}
    )
    t_sync = (time.perf_counter() - t0) * 1000.0
    assert sync_res.status_code == 200
    assert sync_res.json()["result"]["state"] == "ATTRIBUTED"
    results["complete_analysis_pipeline_ms"] = round(t_sync, 2)
    print(f"[8] Complete Forensic Attribution Pipeline:       {t_sync:7.2f} ms")

    # -------------------------------------------------------------
    # Granular Component Isolation Benchmarks (Pure Computation)
    # -------------------------------------------------------------
    print("\n" + "-" * 70)
    print("  GRANULAR COMPONENT ISOLATION (Pure Computation)")
    print("-" * 70)

    # A. ML-KEM-768 Encapsulation
    bob_kem_pub = base64.b64decode(bob_rec.to_public().kem_public_key_b64)
    t0 = time.perf_counter()
    encap_res = MLKEM768.encapsulate(bob_kem_pub)
    t_kem_enc = (time.perf_counter() - t0) * 1000.0
    results["isolated_ml_kem_encapsulate_ms"] = round(t_kem_enc, 3)
    print(f"[-] ML-KEM-768 Encapsulation:                    {t_kem_enc:7.3f} ms")

    # B. ML-KEM-768 Decapsulation
    t0 = time.perf_counter()
    MLKEM768.decapsulate(bob_rec.kem_keypair.private_key_bytes, encap_res.ciphertext)
    t_kem_dec = (time.perf_counter() - t0) * 1000.0
    results["isolated_ml_kem_decapsulate_ms"] = round(t_kem_dec, 3)
    print(f"[-] ML-KEM-768 Decapsulation:                    {t_kem_dec:7.3f} ms")

    # C. Symmetric Encryption & Decryption (AES-256-GCM)
    doc_key = generate_symmetric_key()
    t0 = time.perf_counter()
    sym_ct = encrypt_aes_gcm(doc_key, pdf_bytes)
    t_sym_enc = (time.perf_counter() - t0) * 1000.0
    results["isolated_aes_256_gcm_encrypt_ms"] = round(t_sym_enc, 3)
    print(f"[-] AES-256-GCM Encryption (10KB):               {t_sym_enc:7.3f} ms")

    # D. Post-Quantum Provenance Signature (ML-DSA-65 Sign)
    dsa_priv = bob_rec.dsa_keypair.private_key_bytes
    sign_msg = b"BENCHMARK_PROVENANCE_PAYLOAD_TEST"
    t0 = time.perf_counter()
    sig = MLDSA65.sign(dsa_priv, sign_msg)
    t_dsa_sign = (time.perf_counter() - t0) * 1000.0
    results["isolated_ml_dsa_sign_ms"] = round(t_dsa_sign, 3)
    print(f"[-] ML-DSA-65 Event Signing:                     {t_dsa_sign:7.3f} ms")

    # E. Post-Quantum Signature Verification (ML-DSA-65 Verify)
    dsa_pub = bob_rec.dsa_keypair.public_key_bytes
    t0 = time.perf_counter()
    MLDSA65.verify(dsa_pub, sign_msg, sig)
    t_dsa_verify = (time.perf_counter() - t0) * 1000.0
    results["isolated_ml_dsa_verify_ms"] = round(t_dsa_verify, 3)
    print(f"[-] ML-DSA-65 Signature Verify:                  {t_dsa_verify:7.3f} ms")

    # F. Traceability Marker Extraction
    proto_prov = PrototypeTraceabilityProvider()
    t0 = time.perf_counter()
    ev = proto_prov.get_evidence(traceable_bytes)
    t_trace = (time.perf_counter() - t0) * 1000.0
    results["isolated_traceability_extraction_ms"] = round(t_trace, 3)
    print(f"[-] Traceability Marker Extraction:               {t_trace:7.3f} ms")

    # G. Full Evidence Fusion & Decision
    engine = AttributionEngine()
    t0 = time.perf_counter()
    engine.analyze_leak(traceable_bytes, expected_release_id=release_id)
    t_fusion = (time.perf_counter() - t0) * 1000.0
    results["isolated_evidence_fusion_ms"] = round(t_fusion, 3)
    print(f"[-] Full Evidence Fusion & Decision:             {t_fusion:7.3f} ms")

    # Save to artifacts directory
    artifact_dir = Path(__file__).resolve().parent.parent.parent / "artifacts" / "integration"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_file = artifact_dir / "latency_benchmark.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n[+] Latency Benchmark results saved to: {out_file}")
    print("=" * 70)
    return results

if __name__ == "__main__":
    run_benchmark()
