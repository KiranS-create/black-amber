"""
tests/properties/test_lineage_properties.py

Property-based testing and graph fuzzing for Active Copy Lineage:
- Cycle detection and termination guarantees
- Deep linear chain traversal (up to 1,500+ hops)
- INVARIANT-008: Downstream lineage transition anti-fabrication
- Missing parent explicit boundary enforcement
- Cross-document lineage isolation
"""

import os
from datetime import datetime, timezone
import pytest

from core.lineage.models import (
    DocumentRoot,
    CopyInstance,
    LineageEdge,
    TransitionActionType,
    ForensicBoundaryState,
)
from core.lineage.storage import LineageStorage
from core.lineage.verification import LineageVerifier
from core.testing.property_engine import PropertyRunner, DeterministicGenerator
from core.security.invariants import assert_invariant


def test_property_lineage_cycle_detection_and_termination(runner: PropertyRunner):
    """
    Property: Lineage traversal on arbitrary cyclic graphs ALWAYS terminates
    and returns LINEAGE_BROKEN without hanging or stack overflow.
    """
    def prop(g: DeterministicGenerator):
        storage = LineageStorage()
        verifier = LineageVerifier(storage)

        doc_id = g.generate_document_id()
        root = DocumentRoot(
            document_id=doc_id,
            canonical_hash="00" * 32,
            mime_type="application/pdf",
            byte_size=1024,
            creation_metadata={},
            created_at=datetime.now(timezone.utc).isoformat(),
            status="ACTIVE",
        )
        storage.store_document_root(root)

        # Create cycle of length K (e.g. 1 to 5)
        cycle_len = g.integer(1, 5)
        copies = []
        for i in range(cycle_len):
            cid = f"cpy-cycle-{i}-{g.alphanumeric(6, 6)}"
            copies.append(cid)

        for i, cid in enumerate(copies):
            # i=0 parent is last copy (forming cycle)
            parent_id = copies[(i - 1) % cycle_len]
            copy_inst = CopyInstance(
                copy_id=cid,
                parent_copy_id=parent_id,
                document_id=doc_id,
                recipient_principal_id=f"rec-{i}",
                issuance_timestamp=datetime.now(timezone.utc).isoformat(),
                status="ACTIVE",
                lineage_depth=i,
            )
            storage.store_copy(copy_inst)

        # Target any node in cycle
        target_cid = g.choice(copies)
        proof = verifier.verify_lineage(target_cid)

        # Traversal must terminate, reject the cycle, and report broken lineage
        assert proof.is_valid is False
        assert proof.forensic_boundary_state == ForensicBoundaryState.LINEAGE_BROKEN
        assert any(term in proof.break_reason.lower() for term in ["cycle", "broken", "depth"])

    res = runner.run_property("lineage_cycle_detection", prop, iterations=100)
    assert res.passed, res.error_message


def test_property_lineage_deep_chains(runner: PropertyRunner):
    """
    Property: Lineage safely traverses deep linear graphs (> 1,200 hops)
    without recursion errors or memory exhaustion.
    """
    def prop(g: DeterministicGenerator):
        storage = LineageStorage()
        verifier = LineageVerifier(storage)

        doc_id = g.generate_document_id()
        root = DocumentRoot(
            document_id=doc_id,
            canonical_hash="11" * 32,
            mime_type="application/pdf",
            byte_size=2048,
            creation_metadata={},
            created_at=datetime.now(timezone.utc).isoformat(),
            status="ACTIVE",
        )
        storage.store_document_root(root)

        chain_depth = g.integer(1200, 1500)
        parent_id = None

        # Build linear chain
        for depth in range(chain_depth):
            cid = f"cpy-deep-{depth}"
            copy_inst = CopyInstance(
                copy_id=cid,
                parent_copy_id=parent_id,
                document_id=doc_id,
                recipient_principal_id=f"rec-{depth}",
                issuance_timestamp=datetime.now(timezone.utc).isoformat(),
                status="ACTIVE",
                lineage_depth=depth,
            )
            storage.store_copy(copy_inst)
            parent_id = cid

        # Verify deepest leaf
        proof = verifier.verify_lineage(parent_id, max_hops=10_000)
        assert proof.is_valid is True
        assert len(proof.ancestor_copy_ids) == chain_depth

    # Run on single deep generated case
    res = runner.run_property("lineage_deep_chains", prop, iterations=1)
    assert res.passed, res.error_message


def test_property_lineage_missing_parent_anti_fabrication(runner: PropertyRunner):
    """
    INVARIANT-008: Lineage traversal must NEVER fabricate a missing parent.
    When a parent copy is missing from registry, the verifier stops at the boundary,
    flags LINEAGE_BROKEN, and identifies the last known controlled holder.
    """
    def prop(g: DeterministicGenerator):
        storage = LineageStorage()
        verifier = LineageVerifier(storage)

        doc_id = g.generate_document_id()
        root = DocumentRoot(
            document_id=doc_id,
            canonical_hash="22" * 32,
            mime_type="application/pdf",
            byte_size=1024,
            creation_metadata={},
            created_at=datetime.now(timezone.utc).isoformat(),
            status="ACTIVE",
        )
        storage.store_document_root(root)

        # Root copy (depth 0)
        root_cid = f"cpy-root-{g.alphanumeric(6, 6)}"
        storage.store_copy(CopyInstance(
            copy_id=root_cid,
            parent_copy_id=None,
            document_id=doc_id,
            recipient_principal_id="rec-alice",
            issuance_timestamp=datetime.now(timezone.utc).isoformat(),
            status="ACTIVE",
            lineage_depth=0,
        ))

        # Missing parent ID (never stored)
        missing_pid = f"cpy-missing-{g.alphanumeric(8, 8)}"

        # Leaf copy pointing to non-existent parent
        leaf_cid = f"cpy-leaf-{g.alphanumeric(6, 6)}"
        storage.store_copy(CopyInstance(
            copy_id=leaf_cid,
            parent_copy_id=missing_pid,
            document_id=doc_id,
            recipient_principal_id="rec-bob",
            issuance_timestamp=datetime.now(timezone.utc).isoformat(),
            status="ACTIVE",
            lineage_depth=2,
        ))

        proof = verifier.verify_lineage(leaf_cid)

        # Invariant check: cannot verify and cannot fabricate parent
        assert_invariant(
            proof.is_valid is False,
            "INVARIANT-008",
            "Missing parent lineage verified as valid!",
            g.seed,
        )
        assert proof.forensic_boundary_state == ForensicBoundaryState.LINEAGE_BROKEN
        assert proof.last_known_controlled_holder == "rec-bob"

    res = runner.run_property("lineage_missing_parent_anti_fabrication", prop, iterations=150)
    assert res.passed, res.error_message


def test_property_lineage_cross_document_isolation(runner: PropertyRunner):
    """
    Property: Lineage links across distinct document roots strictly fail closed.
    """
    def prop(g: DeterministicGenerator):
        storage = LineageStorage()
        verifier = LineageVerifier(storage)

        doc1 = g.generate_document_id(1)
        doc2 = g.generate_document_id(2)

        root1 = DocumentRoot(document_id=doc1, canonical_hash="11" * 32, mime_type="application/pdf", byte_size=1024, status="ACTIVE")
        root2 = DocumentRoot(document_id=doc2, canonical_hash="22" * 32, mime_type="application/pdf", byte_size=1024, status="ACTIVE")
        storage.store_document_root(root1)
        storage.store_document_root(root2)

        parent_copy = CopyInstance(
            copy_id=f"cpy-p-{g.alphanumeric(6, 6)}",
            parent_copy_id=None,
            document_id=doc1,
            recipient_principal_id="rec-alice",
            lineage_depth=0,
        )
        storage.store_copy(parent_copy)

        # Child illegitimately claims doc2 while pointing to parent of doc1
        child_copy = CopyInstance(
            copy_id=f"cpy-c-{g.alphanumeric(6, 6)}",
            parent_copy_id=parent_copy.copy_id,
            document_id=doc2,
            recipient_principal_id="rec-bob",
            lineage_depth=1,
        )
        storage.store_copy(child_copy)

        valid, err = verifier.verify_copy_derivation(child_copy, parent_copy, root2)
        assert valid is False
        assert "cross-document" in err.lower()

    res = runner.run_property("lineage_cross_document_isolation", prop, iterations=150)
    assert res.passed, res.error_message
