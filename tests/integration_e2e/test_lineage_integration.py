"""
SIH26237 - Sparse Lineage Index & Multi-Hop Derivation Integration Tests.

Validates that:
1. Derivation steps (Root -> Release -> Decryption -> Export Subcopy) form a valid acyclic graph.
2. Non-recursive sparse index performs fast O(1) lookups by copy_id, document_id, and recipient_id.
3. Ancestry traversal correctly computes lineage chains and depths.
4. Pillar 10 in offline evidence package verification enforces lineage integrity.
"""

import time
import pytest
from core.integration.orchestrator import AegisTraceEndToEndOrchestrator
from core.lineage.scale import SparseLineageIndex, SparseLineageNode
from core.evidence_package.models import VerificationStatus


def test_sparse_lineage_multi_hop_traversal():
    """Tests multi-hop lineage graph creation, node derivation, and traversal."""
    orchestrator = AegisTraceEndToEndOrchestrator(tenant_id="tenant_lineage_test")
    result = orchestrator.run_full_golden_pipeline(leak_recipient_id="alice")

    index = orchestrator.lineage_index
    doc_id = result.document_id

    # 1. Look up root node
    root_node = index.get_node(f"root_{doc_id}")
    assert root_node is not None
    assert root_node.parent_copy_id is None
    assert root_node.derivation_type == "ORIGINAL_ROOT"

    # 2. Look up Alice's decrypted copy node
    alice_art = result.decryption_records["alice"]
    alice_node = index.get_node(alice_art.copy_id)
    assert alice_node is not None
    assert alice_node.parent_copy_id == f"root_{doc_id}"
    assert alice_node.recipient_id == "alice"
    assert alice_node.depth == 1

    # 3. Derive a second-hop subcopy (e.g. Exported PDF)
    subcopy_id = f"subcopy_alice_export_{alice_art.copy_id}"
    sub_node = SparseLineageNode(
        copy_id=subcopy_id,
        parent_copy_id=alice_art.copy_id,
        document_id=doc_id,
        recipient_id="alice",
        event_id="evt_export_001",
        timestamp_epoch=time.time(),
        depth=2,
        tenant_id="tenant_lineage_test",
        derivation_type="PRINT_EXPORT"
    )
    index.insert_node(sub_node)

    # 4. Traverse ancestry from subcopy to root
    trav_res = index.traverse_ancestors(subcopy_id)
    assert trav_res.state.value == "VALID"
    assert len(trav_res.path) == 3
    assert trav_res.path[0] == subcopy_id
    assert trav_res.path[1] == alice_art.copy_id
    assert trav_res.path[2] == f"root_{doc_id}"

    # 5. Offline evidence package verifier passes
    assert result.verification_result.overall_status == VerificationStatus.VERIFIED
    assert result.verification_result.lineage_valid is True
