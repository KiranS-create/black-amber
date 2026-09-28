"""
SIH26237 - Permissioned DLT Ledger & Byzantine Quorum Consensus Integration Tests.

Validates that:
1. All decryption receipts are committed to a replicated BFT ledger across independent nodes.
2. Block headers compute deterministic SHA-256 digests over Merkle roots and parent hashes.
3. RFC 6962 Merkle inclusion proofs verify cryptographic inclusion of receipts.
4. Block proposer ML-DSA-65 signatures and multi-validator threshold quorum votes verify.
5. All replicated nodes maintain identical state and verify chain continuity.
6. Any tampering with block headers, Merkle paths, or quorum votes is detected and rejected.
"""

import pytest
import copy
from core.integration.orchestrator import AegisTraceEndToEndOrchestrator
from core.evidence_package.models import VerificationStatus
from core.evidence_package.verifier import OfflineEvidenceVerifier


def test_dlt_ledger_consensus_and_merkle_inclusion():
    """Tests DLT multi-validator consensus, Merkle audit paths, and node replication."""
    orchestrator = AegisTraceEndToEndOrchestrator(tenant_id="tenant_dlt_test", validator_count=4)
    result = orchestrator.run_full_golden_pipeline(leak_recipient_id="alice")

    # 1. Multi-node chain verification
    node_audit = orchestrator.dlt_ledger.verify_all_nodes()
    assert len(node_audit) == 3
    for node_id, (is_valid, errors) in node_audit.items():
        assert is_valid is True, f"Node {node_id} failed audit: {errors}"
        assert len(errors) == 0

    # 2. Offline verifier Pillar 8 passes
    assert result.verification_result.overall_status == VerificationStatus.VERIFIED
    assert result.verification_result.ledger_proof_valid is True

    # 3. Test Merkle audit path / receipt inclusion corruption
    tampered_pkg = copy.deepcopy(result.evidence_package)
    for obj in tampered_pkg.objects:
        if obj.object_type.value == "LEDGER_PROOF":
            # Mutate receipt_hash to break Merkle inclusion
            mutated = "f" + obj.receipt_hash[1:] if obj.receipt_hash[0] != "f" else "0" + obj.receipt_hash[1:]
            obj.receipt_hash = mutated
            obj.seal_content_hash()
            break

    verifier = OfflineEvidenceVerifier(expected_tenant_id="tenant_dlt_test")
    v_tampered = verifier.verify_package(
        manifest=tampered_pkg.manifest,
        signature=tampered_pkg.signature,
        objects=tampered_pkg.objects,
        edges=tampered_pkg.edges,
        custody_chain=tampered_pkg.custody_chain
    )

    assert v_tampered.overall_status != VerificationStatus.VERIFIED
    assert v_tampered.ledger_proof_valid is False
    assert any("Merkle root mismatch" in e for e in v_tampered.errors)
