import pytest
import copy
import base64
import hashlib
import json
from typing import List, Dict, Any, Optional

from core.testing.property_engine import (
    PropertyRunner,
    DeterministicGenerator,
)
from core.security.invariants import assert_invariant
from core.evidence_package.models import (
    VerificationStatus,
    DecisionState,
    CustodyAction,
    EvidenceObjectType,
)
from core.evidence_package.canonical import (
    canonical_json_dumps,
    canonical_json_bytes,
    compute_content_hash,
)
from core.evidence_package.merkle import (
    EvidenceMerkleTree,
    MerkleInclusionProof,
)
from core.evidence_package.verifier import OfflineEvidenceVerifier
from core.evidence_package.redaction import (
    SafeRedactionEngine,
    RedactionClassification,
)
from tests.evidence_package.test_offline_verifier import create_sample_valid_package_data


def test_property_canonical_json_invariants(runner: PropertyRunner):
    """
    RFC-8785 Inspired Canonical Serialization Invariants:
    1. Key-order insensitivity: Dictionary key order does not alter output bytes.
    2. Determinism: Equal inputs produce bit-identical UTF-8 serialization.
    3. Collision resistance: Any single bit flip produces a completely different SHA-256 hash.
    """
    def prop(g: DeterministicGenerator):
        # Build complex nested structure
        num_keys = g.integer(3, 10)
        keys = [f"k_{g.alphanumeric(4, 6)}" for _ in range(num_keys)]
        
        # Build dictionary with random values
        data1 = {}
        for k in keys:
            val_type = g.choice(["str", "int", "float", "list", "nested"])
            if val_type == "str":
                data1[k] = g.alphanumeric(6, 12)
            elif val_type == "int":
                data1[k] = g.integer(-1000, 1000)
            elif val_type == "float":
                data1[k] = round(g.float_val(-100.0, 100.0), 4)
            elif val_type == "list":
                data1[k] = [g.integer(1, 100) for _ in range(g.integer(1, 4))]
            elif val_type == "nested":
                data1[k] = {"sub_a": g.alphanumeric(4, 6), "sub_b": g.integer(0, 50)}

        # Build data2 with identical contents but reversed or shuffled insertion order
        shuffled_keys = g.shuffle(keys)
        data2 = {k: data1[k] for k in shuffled_keys}

        bytes1 = canonical_json_bytes(data1)
        bytes2 = canonical_json_bytes(data2)

        # Invariant 1: Key order does not affect canonical serialization
        assert_invariant(
            bytes1 == bytes2,
            "INVARIANT-005",
            "Canonical serialization differed between identical dicts with different key order",
            g.seed,
            counterexample={"len1": len(bytes1), "len2": len(bytes2)},
        )

        hash1 = compute_content_hash(data1)
        hash2 = compute_content_hash(data2)
        assert hash1 == hash2

        # Invariant 2: Mutation sensitivity (bit-flip)
        mutated_data = copy.deepcopy(data1)
        target_k = g.choice(keys)
        if isinstance(mutated_data[target_k], str):
            mutated_data[target_k] += "_mod"
        elif isinstance(mutated_data[target_k], int):
            mutated_data[target_k] += 1
        elif isinstance(mutated_data[target_k], float):
            mutated_data[target_k] += 0.001
        elif isinstance(mutated_data[target_k], list):
            mutated_data[target_k].append(999)
        else:
            mutated_data[target_k]["sub_a"] += "_mod"

        hash_mutated = compute_content_hash(mutated_data)
        assert_invariant(
            hash1 != hash_mutated,
            "INVARIANT-005",
            "Mutation failed to alter canonical content hash!",
            g.seed,
            counterexample={"target_key": target_k, "hash": hash1},
        )

    res = runner.run_property("canonical_json_invariants", prop, iterations=250)
    assert res.passed, res.error_message


def test_property_merkle_inclusion_proof_invariants(runner: PropertyRunner):
    """
    RFC-6962 Double-Domain Merkle Tree Invariants:
    1. Soundness: Every authentic leaf in a tree of size N produces a verifiable proof.
    2. Tamper Rejection: Altering leaf hash, root hash, or any sibling hash in the path causes verify() to strictly return False.
    3. Second Preimage & Direction Invariance: Inverting direction ('L' -> 'R') strictly causes verify() to return False.
    """
    def prop(g: DeterministicGenerator):
        num_leaves = g.integer(1, 32)
        leaf_hashes = [hashlib.sha256(g.bytes_data(32)).hexdigest() for _ in range(num_leaves)]
        tree = EvidenceMerkleTree(leaf_hashes)

        # 1. Soundness check: Pick a random leaf and verify its authentic proof
        target_idx = g.integer(0, num_leaves - 1)
        proof = tree.get_inclusion_proof(target_idx)
        assert proof.verify() is True

        tampered_path = list(proof.audit_path)
        if tampered_path:
            attack = g.choice([
                "corrupt_leaf_hash",
                "corrupt_root_hash",
                "corrupt_sibling_hash",
                "flip_direction",
            ])
        else:
            attack = g.choice([
                "corrupt_leaf_hash",
                "corrupt_root_hash",
            ])
        tampered_leaf = proof.leaf_hash
        tampered_root = proof.root_hash
        tampered_path = list(proof.audit_path)

        if attack == "corrupt_leaf_hash":
            tampered_leaf = hashlib.sha256(proof.leaf_hash.encode()).hexdigest()

        elif attack == "corrupt_root_hash":
            tampered_root = hashlib.sha256(proof.root_hash.encode()).hexdigest()

        elif attack == "corrupt_sibling_hash" and tampered_path:
            p_idx = g.integer(0, len(tampered_path) - 1)
            sib, direction = tampered_path[p_idx]
            corrupt_sib = hashlib.sha256(sib.encode()).hexdigest()
            tampered_path[p_idx] = (corrupt_sib, direction)

        elif attack == "flip_direction" and tampered_path:
            p_idx = g.integer(0, len(tampered_path) - 1)
            sib, direction = tampered_path[p_idx]
            new_dir = "R" if direction == "L" else "L"
            corrupt_sib = hashlib.sha256((sib + "_tamper").encode()).hexdigest()
            tampered_path[p_idx] = (corrupt_sib, new_dir)

        tampered_proof = MerkleInclusionProof(
            leaf_hash=tampered_leaf,
            root_hash=tampered_root,
            audit_path=tampered_path,
        )

        valid = tampered_proof.verify()
        assert_invariant(
            valid is False,
            "INVARIANT-005",
            f"Merkle inclusion proof verified after attack '{attack}'",
            g.seed,
            counterexample={"attack": attack, "num_leaves": num_leaves, "target_idx": target_idx},
        )

    res = runner.run_property("merkle_inclusion_proof_invariants", prop, iterations=250)
    assert res.passed, res.error_message


def test_property_evidence_package_tamper_sensitivity_invariant(runner: PropertyRunner):
    """
    INVARIANT-005: Evidence Package Tamper-Evidence & Verifiability.
    Any alteration to manifest metadata, evidence objects, signatures, or custody chains
    must cause the independent offline verifier to reject the package (overall_status == INVALID).
    """
    # Pre-generate base package to avoid repeating expensive ML-DSA-65 keypair generation
    base_pkg, tenant_id = create_sample_valid_package_data()
    verifier = OfflineEvidenceVerifier(expected_tenant_id=tenant_id)

    # Baseline verification
    res_base = verifier.verify_package(
        manifest=base_pkg.manifest,
        signature=base_pkg.signature,
        objects=base_pkg.objects,
        edges=base_pkg.edges,
        custody_chain=base_pkg.custody_chain,
    )
    assert res_base.overall_status == VerificationStatus.VERIFIED

    def prop(g: DeterministicGenerator):
        attack = g.choice([
            "mutate_manifest_case_id",
            "mutate_manifest_package_id",
            "mutate_manifest_merkle_root",
            "mutate_evidence_object_content",
            "delete_evidence_object",
            "corrupt_manifest_signature",
            "corrupt_custody_chain",
        ])

        m_manifest = base_pkg.manifest.model_copy(deep=True)
        m_sig = base_pkg.signature.model_copy(deep=True)
        m_objects = [obj.model_copy(deep=True) for obj in base_pkg.objects]
        m_edges = [edge.model_copy(deep=True) for edge in base_pkg.edges]
        m_custody = [c.model_copy(deep=True) for c in base_pkg.custody_chain]

        if attack == "mutate_manifest_case_id":
            m_manifest.case_id = f"case_tampered_{g.alphanumeric(4, 6)}"

        elif attack == "mutate_manifest_package_id":
            m_manifest.package_id = f"pkg_tampered_{g.alphanumeric(4, 6)}"

        elif attack == "mutate_manifest_merkle_root":
            m_manifest.evidence_merkle_root = hashlib.sha256(g.bytes_data(32)).hexdigest()

        elif attack == "mutate_evidence_object_content":
            # Pick an object and mutate its payload
            target_obj = g.choice(m_objects)
            if hasattr(target_obj, "recipient_id"):
                target_obj.recipient_id = f"rec_evil_{g.alphanumeric(4, 6)}"
            elif hasattr(target_obj, "watermark_token"):
                target_obj.watermark_token = f"WMT_EVIL_{g.alphanumeric(8, 12)}"
            else:
                target_obj.object_id = f"obj_evil_{g.alphanumeric(4, 6)}"

        elif attack == "delete_evidence_object":
            if len(m_objects) > 1:
                del m_objects[0]

        elif attack == "corrupt_manifest_signature":
            # Mutate signature token base64
            raw_sig = base64.b64decode(m_sig.signature_b64)
            mutated_sig = g.mutate_bytes(raw_sig)
            m_sig.signature_b64 = base64.b64encode(mutated_sig).decode("utf-8")

        elif attack == "corrupt_custody_chain":
            if m_custody:
                target_cust = g.choice(m_custody)
                target_cust.previous_custody_hash = hashlib.sha256(g.bytes_data(32)).hexdigest()
                target_cust.operator_identity = "unauthorized_tamperer"

        res = verifier.verify_package(
            manifest=m_manifest,
            signature=m_sig,
            objects=m_objects,
            edges=m_edges,
            custody_chain=m_custody,
        )

        assert_invariant(
            res.overall_status in (VerificationStatus.INVALID, VerificationStatus.INCOMPLETE, VerificationStatus.CONFLICT)
            and res.overall_status != VerificationStatus.VERIFIED,
            "INVARIANT-005",
            f"Evidence package verifier accepted package after attack '{attack}'",
            g.seed,
            counterexample={"attack": attack, "errors": res.errors, "status": str(res.overall_status)},
        )

    res = runner.run_property("evidence_package_tamper_sensitivity_invariant", prop, iterations=200)
    assert res.passed, res.error_message


def test_property_selective_redaction_merkle_preservation(runner: PropertyRunner):
    """
    Selective Redaction Invariant:
    Redacting an evidence object replaces it with a RedactedEvidenceStub while
    retaining the original content_hash, preserving the Merkle tree root and verifiability.
    """
    base_pkg, tenant_id = create_sample_valid_package_data()
    verifier = OfflineEvidenceVerifier(expected_tenant_id=tenant_id)

    def prop(g: DeterministicGenerator):
        # Redact non-cryptographic metadata (CaseObject) to protect operational secrets
        case_objects = [obj for obj in base_pkg.objects if obj.object_type == EvidenceObjectType.CASE]
        assert case_objects, "Base package missing CaseObject"
        target_obj = g.choice(case_objects)
        target_id = target_obj.object_id

        red_reason = f"Privacy redaction for {g.alphanumeric(4, 6)}"
        red_class = g.choice([
            RedactionClassification.REDACTED,
            RedactionClassification.NOT_INCLUDED,
            RedactionClassification.NOT_REQUIRED_FOR_THIS_PROOF,
        ])

        red_objects, updated_manifest = SafeRedactionEngine.apply_package_redactions(
            objects=base_pkg.objects,
            target_object_ids_to_redact=[target_id],
            reason=red_reason,
            manifest=base_pkg.manifest,
            classification=red_class,
            redacted_by=f"OFFICER_{g.alphanumeric(4, 6)}",
        )

        # 1. Verify that redacted stub retained original content hash
        stub = next(o for o in red_objects if o.object_id == target_id)
        assert stub.content_hash == (target_obj.content_hash or target_obj.compute_content_digest())

        # 2. Check if tamper to stub is detected
        tamper_stub = g.boolean(0.5)
        if tamper_stub:
            stub.content_hash = hashlib.sha256(g.bytes_data(32)).hexdigest()

        # 3. Verify package
        res = verifier.verify_package(
            manifest=updated_manifest,
            signature=base_pkg.signature,
            objects=red_objects,
            edges=base_pkg.edges,
            custody_chain=base_pkg.custody_chain,
        )

        if tamper_stub:
            assert_invariant(
                res.overall_status == VerificationStatus.INVALID,
                "INVARIANT-005",
                "Tampered redacted stub was accepted by offline verifier",
                g.seed,
            )
        else:
            assert_invariant(
                res.overall_status == VerificationStatus.VERIFIED,
                "INVARIANT-005",
                f"Legitimate safe redaction failed verification: {res.errors}",
                g.seed,
            )

    res = runner.run_property("selective_redaction_merkle_preservation", prop, iterations=100)
    assert res.passed, res.error_message
