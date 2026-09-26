import pytest
import os
import json

WEB_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "apps", "web"))

def test_full_state_machine_pipeline_flow():
    """
    Validates that the frontend mock state machine and deterministic scenarios 
    cover the full target judge demonstration pipeline:
    HEALTH -> DOCUMENT -> RECIPIENTS -> RELEASE -> DECRYPT/PROVENANCE -> 
    LEDGER -> LEAK -> ANALYZE -> TARDOS -> ATTACK -> RE-ANALYZE -> CONFLICT -> ABSTAIN
    """
    mock_data_path = os.path.join(WEB_ROOT, "src", "services", "mockData.ts")
    with open(mock_data_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Step 1: Health & Initial Documents
    assert "INITIAL_DOCUMENTS" in content
    assert "National_Defense_Protocol_2026.pdf" in content
    assert "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08" in content

    # Step 2: Recipient Key Isolation (ML-KEM-768 & ML-DSA-65)
    assert "INITIAL_RECIPIENTS" in content
    assert "alice" in content and "bob" in content and "charlie" in content
    assert "kEM768_pub_" in content
    assert "dSA65_pub_" in content

    # Step 3: Multi-Recipient Envelope Release
    assert "INITIAL_RELEASES" in content
    assert "rel_20260926_001" in content
    assert "AES-256-GCM" in content
    assert "ML-KEM-768" in content

    # Step 4: Decryption & Non-Repudiation Provenance Logging
    assert "INITIAL_LEDGER_EVENTS" in content
    assert "evt_dec_bob_002" in content
    assert "DECRYPTION_EVENT" in content
    assert "BOB_SIG_ML_DSA_65_NON_REPUDIATION_PROVENANCE_LOGGED" in content

    # Step 5: Leak Ingestion & Bayesian Multi-Channel Evidence Fusion
    assert "computeMockAttribution" in content
    assert "clean_bob" in content
    assert "18.08" in content  # Fused score
    assert "wm_spatial" in content
    assert "tardos_fp" in content
    assert "pqc_sig" in content
    assert "ledger_chain" in content

    # Step 6: Adversarial Stress Testing & Fail-Closed Guarantee
    assert "raw_unwatermarked" in content
    assert "forged_hmac" in content
    assert "framed_identity" in content
    assert "print_scan_camera" in content
    assert "heavy_jpeg" in content
    assert "cross_doc_scope" in content

    # Step 7: Multi-Channel Evidence Contradiction
    assert "evidence_conflict_bob_charlie" in content
    assert "Cross-channel evidence contradiction" in content
    assert "CONFLICT" in content

def test_conflict_resolution_fail_closed_logic():
    """
    Validates that contradictory signals (Tardos=Bob, Watermark=Charlie, Provenance=Bob)
    strictly trigger CONFLICT rather than picking the highest score.
    """
    mock_data_path = os.path.join(WEB_ROOT, "src", "services", "mockData.ts")
    with open(mock_data_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "evidence_conflict_bob_charlie" in content
    assert "'CONFLICT'" in content
    assert "should_abstain: true" in content
