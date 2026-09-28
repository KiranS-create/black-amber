"""
SIH26237 - Complete 24-Step End-to-End Golden Forensic Pipeline Test.

Asserts every step of the real, unmocked AegisTrace pipeline:
1. Document Ingestion & SHA-256 Digest
2. Post-Quantum ML-KEM-768 & ML-DSA-65 Keypair Generation
3. Key Lifecycle Verification & Enrollment
4. Broadcast Encryption (AES-256-GCM + Domain-Separated AD)
5. ML-KEM-768 Shared Secret Encapsulation per Recipient
6. HKDF-SHA256 Key Derivation & AES-KW Wrapping
7. Authenticated Release Package Distribution
8. Recipient ML-KEM-768 Decapsulation
9. AES-KW Unwrapping with Authenticated Release Context
10. AES-256-GCM Decryption & Document Hash Integrity Check
11. Dynamic Watermark Identity Derivation (Binding Doc, Recipient, Session, Copy)
12. DSSS Invisible Watermark Codeword Modulation & Embedding
13. Recipient Canonical DecryptionReceipt Construction
14. Recipient ML-DSA-65 Signature Generation over Canonical Payload
15. Permissioned DLT Ledger Block Confirmation & Quorum Endorsements
16. Sparse Lineage Graph Indexing & Derivation Edge Tracking
17. Hardware Device Attestation (TPM) & Telemetry Recording
18. Leak Artifact Ingestion into Forensic Custody
19. Forensic Watermark Codeword & Telemetry Decoding
20. DLT Ledger Receipt Lookup & Merkle Inclusion Verification
21. Recipient ML-DSA-65 Signature Verification
22. Lineage Graph Traversal & LAST_KNOWN_HOLDER Invariant Verification
23. Bayesian Multi-Channel Evidence Fusion & Attribution Decision
24. Strongly-Typed Evidence Package Assembly (17 Schemas, RFC 6962 Tree, DAG, CoC)
    and Independent Offline Air-Gapped Verification (Verdict: VERIFIED).
"""

import pytest
from core.integration.orchestrator import AegisTraceEndToEndOrchestrator
from core.evidence_package.models import VerificationStatus, DecisionState


def test_complete_golden_forensic_pipeline():
    """Executes the full 24-step golden path test and validates every cryptographic invariant."""
    orchestrator = AegisTraceEndToEndOrchestrator(
        tenant_id="tenant_sih_defense_01",
        validator_count=4
    )

    doc_content = (
        b"%PDF-1.7 Master Defense Deployment Brief 2026 TOP SECRET\n"
        b"PROJECT AEGISTRACE POST-QUANTUM FORENSIC DOCUMENT TRACKING SPECIFICATION\n"
        b"CONFIDENTIAL AIR-GAP VERIFICATION PAYLOAD CONTENT " + (b"A" * 2048)
    )

    result = orchestrator.run_full_golden_pipeline(
        document_bytes=doc_content,
        document_name="Strategic_Deployment_2026.pdf",
        leak_recipient_id="alice"
    )

    # 1. Pipeline execution assertions
    assert result.case_id.startswith("CASE_SIH_")
    assert result.tenant_id == "tenant_sih_defense_01"
    assert len(result.recipients) == 3
    assert set(result.recipients) == {"alice", "bob", "charlie"}
    assert result.leak_target_recipient_id == "alice"

    # 2. Decryption & DLT assertions
    assert "alice" in result.decryption_records
    alice_art = result.decryption_records["alice"]
    assert alice_art.decrypted_plaintext == doc_content
    assert alice_art.dynamic_identity.recipient_id == "alice"
    assert alice_art.receipt.verify_recipient_signature() is True
    assert alice_art.dlt_block.header.block_height >= 1
    assert len(alice_art.dlt_block.quorum_signatures) >= 3

    # 3. Attribution decision assertions
    attr = result.extraction_and_attribution
    assert attr.detection_state == "DETECTED"
    assert attr.decision_state == DecisionState.ATTRIBUTED
    assert attr.attributed_principal_id == "alice"
    assert attr.is_signature_valid is True
    assert attr.is_ledger_proof_valid is True

    # 4. Evidence Package & Offline Verification assertions
    pkg = result.evidence_package
    assert pkg.manifest.tenant_id == "tenant_sih_defense_01"
    assert pkg.manifest.final_decision_reference.startswith("decision_")
    assert len(pkg.objects) >= 11

    verif = result.verification_result
    assert verif.overall_status == VerificationStatus.VERIFIED
    assert verif.manifest_signature_valid is True
    assert verif.merkle_root_valid is True
    assert verif.object_hashes_valid is True
    assert verif.dependency_graph_valid is True
    assert verif.recipient_signature_valid is True
    assert verif.historical_keys_valid is True
    assert verif.ledger_proof_valid is True
    assert verif.watermark_binding_valid is True
    assert verif.lineage_valid is True
    assert verif.custody_chain_valid is True
    assert verif.decision_consistent is True
    assert len(verif.errors) == 0

    # 5. Timing & Performance assertion
    assert result.total_latency_ms > 0.0
    print(f"\n[PASS] Golden Pipeline complete in {result.total_latency_ms:.2f} ms")
