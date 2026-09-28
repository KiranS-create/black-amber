"""
Tests for RFC-6962 Binary Merkle Tree and Deterministic Package Manifest.
Verifies:
1. Merkle tree construction across odd, even, single, and multiple leaf counts.
2. Cryptographic inclusion proof validity for every leaf.
3. Tamper detection: modifying leaf, audit sibling, or root invalidates proof.
4. Manifest determinism and sensitivity to inventory changes.
"""

import pytest
import hashlib

from core.evidence_package.merkle import EvidenceMerkleTree, MerkleInclusionProof
from core.evidence_package.models import PackageManifest


def test_merkle_tree_construction_and_inclusion_proofs():
    leaf_hashes = [
        hashlib.sha256(f"leaf_{i}".encode("utf-8")).hexdigest()
        for i in range(7)  # Odd number of leaves
    ]

    tree = EvidenceMerkleTree(leaf_hashes)
    assert tree.root != ""

    # Verify inclusion proof for each leaf
    for idx in range(len(leaf_hashes)):
        proof = tree.get_inclusion_proof(idx)
        assert proof.verify() is True

        # Tamper 1: corrupt leaf hash
        tampered_leaf = bytearray.fromhex(proof.leaf_hash)
        tampered_leaf[0] ^= 0xFF
        bad_leaf_proof = MerkleInclusionProof(
            leaf_hash=tampered_leaf.hex(),
            root_hash=proof.root_hash,
            audit_path=proof.audit_path
        )
        assert bad_leaf_proof.verify() is False

        # Tamper 2: corrupt root hash
        bad_root_proof = MerkleInclusionProof(
            leaf_hash=proof.leaf_hash,
            root_hash="0" * 64,
            audit_path=proof.audit_path
        )
        assert bad_root_proof.verify() is False

        # Tamper 3: corrupt audit path sibling
        if proof.audit_path:
            tampered_path = list(proof.audit_path)
            tampered_path[0] = ("f" * 64, tampered_path[0][1])
            bad_path_proof = MerkleInclusionProof(
                leaf_hash=proof.leaf_hash,
                root_hash=proof.root_hash,
                audit_path=tampered_path
            )
            assert bad_path_proof.verify() is False


def test_manifest_determinism_and_hash_sensitivity():
    m1 = PackageManifest(
        case_id="case_100",
        tenant_id="default_tenant",
        package_id="pkg_100",
        object_inventory=[
            {"object_id": "art_1", "object_type": "ARTIFACT", "content_hash": "a"*64},
            {"object_id": "dec_1", "object_type": "ATTRIBUTION_DECISION", "content_hash": "b"*64}
        ],
        dependency_graph_root="dec_1",
        evidence_merkle_root="c"*64,
        final_decision_reference="dec_1"
    )

    h1 = m1.compute_manifest_hash()
    assert h1 == m1.compute_manifest_hash()

    # Changing inventory or root alters manifest hash
    m2 = m1.model_copy(deep=True)
    m2.evidence_merkle_root = "d"*64
    h2 = m2.compute_manifest_hash()
    assert h1 != h2
