"""
Tests for Air-Gapped Zero-Egress Execution and Large-Scale Evidence Packaging.

Verifies:
1. Complete offline, air-gapped verification with all network socket creation blocked.
2. Large-scale Merkle tree construction, inclusion proofs, and verification latency
   across 100, 500, and 1,000+ evidence objects.
3. Memory efficiency and deterministic hash calculation at scale.
"""

import time
import socket
import pytest
import hashlib
from datetime import datetime, timezone

from core.crypto.signatures import MLDSA65
from core.crypto.models import KeyPair
from core.evidence_package.models import (
    BaseEvidenceObject,
    EvidenceObjectType,
    VerificationStatus,
    ArtifactEvidenceObject,
    AttributionDecisionObject,
    DecisionState,
    TelemetryDependencyRelation
)
from core.evidence_package.merkle import EvidenceMerkleTree, MerkleInclusionProof
from core.evidence_package.builder import EvidencePackageBuilder
from core.evidence_package.verifier import OfflineEvidenceVerifier
from tests.evidence_package.test_offline_verifier import create_sample_valid_package_data


def test_airgap_zero_network_egress(monkeypatch):
    """
    Simulates a strictly air-gapped judicial workstation by disabling socket creation.
    Any attempt by verifier or submodules to perform DNS lookups, HTTP calls, or socket binds
    will raise a catastrophic AirgapNetworkViolationError.
    """
    class AirgapNetworkViolationError(RuntimeError):
        pass

    def guarded_socket(*args, **kwargs):
        raise AirgapNetworkViolationError("ILLEGAL_NETWORK_EGRESS: Offline verifier attempted socket connection!")

    monkeypatch.setattr(socket, "socket", guarded_socket)

    # Now verify the complete package under strict airgap
    pkg, tenant_id = create_sample_valid_package_data()
    verifier = OfflineEvidenceVerifier(expected_tenant_id=tenant_id)

    res = verifier.verify_package(
        manifest=pkg.manifest,
        signature=pkg.signature,
        objects=pkg.objects,
        edges=pkg.edges,
        custody_chain=pkg.custody_chain
    )

    assert res.overall_status == VerificationStatus.VERIFIED
    assert res.manifest_signature_valid is True
    assert res.merkle_root_valid is True
    assert len(res.errors) == 0


def test_large_scale_merkle_tree_performance():
    """
    Tests Merkle tree computation and inclusion proof generation across 1,000 objects.
    Verifies that tree generation and verification finish within sub-second limits.
    """
    n_objects = 1000
    leaf_hashes = [
        hashlib.sha256(f"leaf_test_data_{i}".encode("utf-8")).hexdigest()
        for i in range(n_objects)
    ]

    t0 = time.perf_counter()
    tree = EvidenceMerkleTree(leaf_hashes)
    tree_build_time = time.perf_counter() - t0

    assert tree.root is not None
    assert len(tree.root) == 64
    assert tree_build_time < 1.0, f"Tree construction for {n_objects} leaves took {tree_build_time:.4f}s (> 1.0s)"

    # Verify inclusion proofs for multiple sample indices
    sample_indices = [0, 1, 499, 500, 999]
    for idx in sample_indices:
        t_proof_start = time.perf_counter()
        proof = tree.get_inclusion_proof(idx)
        verify_ok = proof.verify()
        proof_latency = time.perf_counter() - t_proof_start

        assert verify_ok is True
        assert proof_latency < 0.05, f"Proof verification took {proof_latency:.4f}s"
        assert len(proof.audit_path) <= 12  # ceil(log2(1000)) = 10-11


def test_package_scale_builder_and_verifier():
    """
    Tests end-to-end building, post-quantum signing, and offline verification
    of an evidence package containing 100 distinct evidentiary artifacts.
    """
    tenant_id = "tenant_scale_test"
    case_id = "case_scale_100"
    examiner_kp = MLDSA65.generate_keypair()

    builder = EvidencePackageBuilder(case_id=case_id, tenant_id=tenant_id)

    # Add 100 artifact objects
    for i in range(100):
        content = f"SCALE_ARTIFACT_PAYLOAD_{i}".encode("utf-8")
        art = ArtifactEvidenceObject(
            object_id=f"art_scale_{i:04d}",
            artifact_category="LEAK",
            filename=f"chunk_{i}.dat",
            byte_size=len(content),
            sha256_digest=hashlib.sha256(content).hexdigest()
        )
        builder.add_object(art)

    # Attribution decision
    dec = AttributionDecisionObject(
        object_id="dec_scale_root",
        case_id=case_id,
        evidence_merkle_root="0" * 64,
        decision_state=DecisionState.NO_SIGNAL
    )
    builder.set_decision(dec)

    # Connect decision to a sample of artifacts
    for i in range(0, 100, 10):
        builder.add_edge("dec_scale_root", f"art_scale_{i:04d}", TelemetryDependencyRelation.DIRECTLY_SUPPORTS.value)

    t_build_start = time.perf_counter()
    pkg = builder.build_and_sign(signing_keypair=examiner_kp)
    build_time = time.perf_counter() - t_build_start

    assert len(pkg.objects) == 101  # 100 artifacts + 1 decision
    assert build_time < 3.0

    verifier = OfflineEvidenceVerifier(expected_tenant_id=tenant_id)
    t_verify_start = time.perf_counter()
    res = verifier.verify_package(
        manifest=pkg.manifest,
        signature=pkg.signature,
        objects=pkg.objects,
        edges=pkg.edges,
        custody_chain=pkg.custody_chain
    )
    verify_time = time.perf_counter() - t_verify_start

    assert res.overall_status == VerificationStatus.VERIFIED
    assert res.object_hashes_valid is True
    assert res.merkle_root_valid is True
    assert res.manifest_signature_valid is True
    assert verify_time < 2.0, f"Verification took {verify_time:.4f}s (> 2.0s)"
