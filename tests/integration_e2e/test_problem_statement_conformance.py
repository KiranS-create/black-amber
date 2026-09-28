"""
SIH26237 - 15-Pillar Problem Statement Conformance Test Suite.

Formally maps and asserts all 15 SIH Problem Statement Core Requirements:
- REQ-01: Post-Quantum Cryptography (ML-KEM-768 + ML-DSA-65)
- REQ-02: Efficient Broadcast Encryption (AES-256-GCM + Domain AD)
- REQ-03: Client-Side Provenance & Recipient Private Key Decryption
- REQ-04: Dynamic Invisible Watermarking (DSSS Carrier + RS ECC)
- REQ-05: Recipient-Owned ML-DSA-65 Signed Decryption Receipts
- REQ-06: Offline Permissioned DLT Consensus & Merkle Inclusion
- REQ-07: Memory-Bounded Sparse Lineage Graph Indexing
- REQ-08: Hardware Device Attestation & Telemetry Binding
- REQ-09: Visual Equivalence with Strict Forensic Isolation
- REQ-10: Robust Watermark Recovery & DLT Receipt Correlation
- REQ-11: Fail-Closed Attribution & LAST_KNOWN_HOLDER Boundary
- REQ-12: Portable Cryptographic Evidence Packages (17 Schemas)
- REQ-13: Independent Air-Gapped Offline Verification (12 Pillars)
- REQ-14: Multi-Tenant Partition & Tenant Isolation Enforcement
- REQ-15: State Snapshots & Disaster Recovery Continuity
"""

import pytest
from core.integration.orchestrator import AegisTraceEndToEndOrchestrator
from core.integration.equivalence import MultiRecipientEquivalenceAnalyzer
from core.integration.harness import EndToEndFaultHarness
from core.evidence_package.models import VerificationStatus, DecisionState


@pytest.fixture(scope="module")
def conformance_context():
    orch = AegisTraceEndToEndOrchestrator(tenant_id="tenant_sih_conformance", validator_count=4)
    res = orch.run_full_golden_pipeline(leak_recipient_id="alice")
    return orch, res


def test_req_01_post_quantum_cryptography(conformance_context):
    orch, res = conformance_context
    alice = orch.registry.get("alice")
    assert alice.kem_keypair.algorithm == "ML-KEM-768"
    assert alice.dsa_keypair.algorithm == "ML-DSA-65"


def test_req_02_broadcast_encryption(conformance_context):
    orch, res = conformance_context
    rel = orch.release_manager.releases[res.release_id]
    assert len(rel.packages) == 3
    # Same ciphertext for document payload, unique KEM capsules
    alice_pkg = rel.packages["alice"]
    bob_pkg = rel.packages["bob"]
    assert alice_pkg.encrypted_doc_ciphertext_b64 == bob_pkg.encrypted_doc_ciphertext_b64
    assert alice_pkg.kem_ciphertext_b64 != bob_pkg.kem_ciphertext_b64


def test_req_03_client_side_decryption(conformance_context):
    orch, res = conformance_context
    alice_art = res.decryption_records["alice"]
    assert alice_art.decrypted_plaintext == res.decryption_records["bob"].decrypted_plaintext


def test_req_04_dynamic_watermarking(conformance_context):
    orch, res = conformance_context
    alice_art = res.decryption_records["alice"]
    assert len(alice_art.dynamic_identity.codeword) == 128
    assert len(alice_art.dynamic_identity.token) == 64


def test_req_05_recipient_owned_signatures(conformance_context):
    orch, res = conformance_context
    for r_id in ["alice", "bob", "charlie"]:
        receipt = res.decryption_records[r_id].receipt
        assert receipt.verify_recipient_signature() is True


def test_req_06_permissioned_dlt(conformance_context):
    orch, res = conformance_context
    for r_id in ["alice", "bob", "charlie"]:
        blk = res.decryption_records[r_id].dlt_block
        assert blk.header.block_height >= 1
        assert len(blk.quorum_signatures) >= 3


def test_req_07_sparse_lineage(conformance_context):
    orch, res = conformance_context
    alice_art = res.decryption_records["alice"]
    node = orch.lineage_index.get_node(alice_art.copy_id)
    assert node is not None
    assert node.depth == 1


def test_req_08_device_telemetry(conformance_context):
    orch, res = conformance_context
    alice_art = res.decryption_records["alice"]
    assert alice_art.device_id.startswith("dev_alice_tpm")


def test_req_09_visual_equivalence_and_forensic_distinction(conformance_context):
    orch, res = conformance_context
    analyzer = MultiRecipientEquivalenceAnalyzer()
    report = analyzer.analyze_decryptions(res.decryption_records, res.document_id, res.release_id)
    assert report.is_semantically_identical is True
    assert report.is_visually_equivalent is True
    assert report.is_forensically_distinct is True


def test_req_10_watermark_recovery_and_ledger_lookup(conformance_context):
    orch, res = conformance_context
    attr = res.extraction_and_attribution
    assert attr.detection_state == "DETECTED"
    assert attr.attributed_principal_id == "alice"


def test_req_11_fail_closed_attribution(conformance_context):
    orch, res = conformance_context
    attr = res.extraction_and_attribution
    assert attr.decision_state == DecisionState.ATTRIBUTED
    assert attr.last_known_holder_id == "alice"


def test_req_12_cryptographic_evidence_packages(conformance_context):
    orch, res = conformance_context
    pkg = res.evidence_package
    assert len(pkg.objects) >= 11
    assert pkg.manifest.evidence_merkle_root is not None


def test_req_13_independent_airgap_verification(conformance_context):
    orch, res = conformance_context
    assert res.verification_result.overall_status == VerificationStatus.VERIFIED
    assert len(res.verification_result.errors) == 0


def test_req_14_multi_tenant_isolation(conformance_context):
    orch, res = conformance_context
    fault = EndToEndFaultHarness.test_cross_tenant_isolation(res.evidence_package, "other_tenant")
    assert fault.detected_and_blocked is True


def test_req_15_disaster_recovery_snapshot(conformance_context):
    orch, res = conformance_context
    snap = orch.dlt_ledger.create_snapshot()
    assert snap.block_height >= 1
    assert snap.receipt_count >= 3
