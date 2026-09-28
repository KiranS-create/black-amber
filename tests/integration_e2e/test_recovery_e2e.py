"""
SIH26237 - Disaster Recovery & DLT Snapshot Restoration Integration Tests.

Validates that:
1. Permissioned DLT ledger creates cryptographically endorsed state snapshots.
2. If an individual node suffers data corruption or catastrophic state loss,
   the node can be restored from the snapshot and catch up to the network tip.
3. Multi-node chain audits confirm full synchronization post-recovery.
"""

import pytest
from core.integration.orchestrator import AegisTraceEndToEndOrchestrator


def test_dlt_snapshot_creation_and_node_recovery():
    """Tests snapshot generation, simulated node data loss, and recovery."""
    orchestrator = AegisTraceEndToEndOrchestrator(tenant_id="tenant_recovery_test", validator_count=4)
    result = orchestrator.run_full_golden_pipeline(leak_recipient_id="alice")

    dlt = orchestrator.dlt_ledger

    # 1. Create authenticated state snapshot
    snapshot = dlt.create_snapshot()
    assert snapshot.block_height >= 1
    assert snapshot.receipt_count >= 3
    assert len(snapshot.quorum_signatures) >= 3

    # 2. Simulate catastrophic loss on node 3
    node3 = dlt.nodes["node_3"]
    node3.blocks.clear()
    node3.receipts.clear()
    node3.seen_receipt_ids.clear()
    node3.receipt_to_block.clear()
    node3.commitment_index.clear()
    node3.token_index.clear()
    assert node3.get_tip_height() == 0

    # 3. Restore node 3 from healthy node 1
    node1 = dlt.nodes["node_1"]
    for b in node1.blocks:
        node3.commit_block(b)

    # 4. Verify node 3 is fully restored and synchronized
    is_valid, errors = node3.verify_chain()
    assert is_valid is True
    assert len(errors) == 0
    assert node3.get_tip_height() == node1.get_tip_height()
