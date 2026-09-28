"""
AegisTrace Disaster Recovery & Rollback Attack Tests.

Tests recovery integrity under adversarial conditions:
1. Detecting rollback attempts from stale database snapshots.
2. Catching corrupted block headers and invalid state transitions during node recovery.
3. Synchronizing an erased/desynchronized node back to the authoritative tip.
"""

import pytest
import copy
from core.integration.orchestrator import AegisTraceEndToEndOrchestrator
from core.ledger.dlt import DLTBlock, DLTBlockHeader


def test_dlt_state_snapshot_and_node_resync():
    """
    Ensures that an authenticated snapshot captures quorum signatures,
    and a corrupted/cleared node can recover by replaying the validated blocks.
    """
    orchestrator = AegisTraceEndToEndOrchestrator(
        tenant_id="tenant_dr_eval",
        validator_count=4
    )
    doc_bytes = b"%PDF-1.7 DISASTER RECOVERY INTEGRITY TEST\n" + b"DATA " * 30
    res = orchestrator.run_full_golden_pipeline(
        document_bytes=doc_bytes,
        document_name="DR_Test.pdf",
        leak_recipient_id="alice"
    )

    dlt = orchestrator.dlt_ledger
    snapshot = dlt.create_snapshot()
    assert snapshot.block_height >= 1
    assert snapshot.receipt_count >= 1
    assert len(snapshot.quorum_signatures) >= dlt.quorum_threshold

    # Simulate catastrophic corruption on node_2
    node2 = dlt.nodes["node_2"]
    node2.blocks.clear()
    node2.receipts.clear()
    node2.seen_receipt_ids.clear()
    assert node2.get_tip_height() == 0

    # Resync from primary node
    node1 = dlt.nodes["node_1"]
    for block in node1.blocks:
        node2.commit_block(block)

    is_valid, errors = node2.verify_chain()
    assert is_valid is True
    assert len(errors) == 0
    assert node2.get_tip_height() == node1.get_tip_height()


def test_rollback_rejection_on_node_recovery():
    """
    Adversary attempts to inject an older block (rollback) into a recovered node.
    Enforces that height monotonicity and parent hash continuity prevent the rollback.
    """
    orchestrator = AegisTraceEndToEndOrchestrator(
        tenant_id="tenant_dr_eval",
        validator_count=4
    )
    res = orchestrator.run_full_golden_pipeline(
        document_bytes=b"%PDF-1.7 TEST MONOTONICITY " + b"DATA " * 20,
        document_name="Monotonicity.pdf",
        leak_recipient_id="bob"
    )

    dlt = orchestrator.dlt_ledger
    node1 = dlt.nodes["node_1"]
    current_height = node1.get_tip_height()

    # Attempt to commit a block with height 1 (when tip is already >= 1)
    stale_header = DLTBlockHeader(
        block_height=1,
        previous_block_hash="0" * 64,
        proposer_validator_id=list(dlt.val_map.keys())[0],
        round_number=1,
        merkle_root="0" * 64
    )
    stale_block = DLTBlock(
        header=stale_header,
        block_hash=stale_header.compute_header_hash(),
        transactions=[]
    )

    # Committing to node1 must raise ValueError (Rollback/height failure)
    with pytest.raises(ValueError) as excinfo:
        node1.commit_block(stale_block)
    
    assert "height" in str(excinfo.value).lower() or "validation failed" in str(excinfo.value).lower()
