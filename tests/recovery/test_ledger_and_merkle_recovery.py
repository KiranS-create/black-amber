"""
Unit & Integration Tests for AegisTrace Ledger & Merkle Checkpoint Recovery Engine.
"""

import pytest
from core.ledger.ledger import TamperEvidentLedger, EvidenceEvent
from core.ledger.dlt import (
    DLTNode,
    DLTBlock,
    DLTBlockHeader,
    DLTValidator,
    DecryptionReceipt,
    build_merkle_tree,
)
from core.crypto.signatures import MLDSA65
from core.recovery.models import RecoveryState
from core.recovery.ledger_recovery import LedgerRecoveryEngine


def make_test_event(event_id: str, prev_hash: str) -> EvidenceEvent:
    ev = EvidenceEvent(
        event_id=event_id,
        event_type="DECRYPTION_EVENT",
        document_id="doc_test",
        release_id="rel_test",
        recipient_id="alice",
        algorithm="ML-DSA-65",
        artifact_hash="art_hash_1",
        evidence_hash="ev_hash_1",
        previous_event_hash=prev_hash,
        signature=""
    )
    return ev


def test_recover_intact_ledger():
    ledger = TamperEvidentLedger()
    prev = TamperEvidentLedger.GENESIS_HASH
    events = []
    for i in range(5):
        ev = make_test_event(f"ev_{i}", prev)
        h = ledger.append_event(ev)
        events.append(ev)
        prev = h

    res = LedgerRecoveryEngine.recover_ledger(events)
    assert res.state == RecoveryState.VALID_RECOVERY
    assert res.events_recovered == 5
    assert res.events_quarantined == 0
    assert res.last_valid_hash == prev


def test_recover_ledger_partial_tail_corruption_with_quarantine():
    prev = TamperEvidentLedger.GENESIS_HASH
    events = []
    for i in range(4):
        ev = make_test_event(f"ev_{i}", prev)
        events.append(ev)
        prev = ev.compute_event_hash()

    # Create corrupted 5th and 6th event (broken previous_event_hash)
    corrupt_5 = make_test_event("ev_4", "malicious_bad_hash")
    corrupt_6 = make_test_event("ev_5", corrupt_5.compute_event_hash())
    events.extend([corrupt_5, corrupt_6])

    # 1. Without allow_tail_truncation -> CORRUPTED_RECOVERY
    res_strict = LedgerRecoveryEngine.recover_ledger(events, allow_tail_truncation=False)
    assert res_strict.state == RecoveryState.CORRUPTED_RECOVERY
    assert res_strict.events_recovered == 0
    assert res_strict.events_quarantined == 2

    # 2. With allow_tail_truncation -> PARTIAL_RECOVERY (first 4 recovered, 2 quarantined)
    res_partial = LedgerRecoveryEngine.recover_ledger(events, allow_tail_truncation=True)
    assert res_partial.state == RecoveryState.PARTIAL_RECOVERY
    assert res_partial.events_recovered == 4
    assert res_partial.events_quarantined == 2
    assert len(res_partial.quarantined_events) == 2
    assert res_partial.quarantined_events[0].event_id == "ev_4"


def test_ledger_merkle_root_mismatch_detected():
    prev = TamperEvidentLedger.GENESIS_HASH
    events = []
    for i in range(3):
        ev = make_test_event(f"ev_{i}", prev)
        events.append(ev)
        prev = ev.compute_event_hash()

    # Pass wrong expected checkpoint root
    wrong_root = "f" * 64
    res = LedgerRecoveryEngine.recover_ledger(events, expected_checkpoint_root=wrong_root)
    assert res.state == RecoveryState.CORRUPTED_RECOVERY
    assert "MERKLE_ROOT_MISMATCH" in res.errors[0]


def test_ledger_rollback_detected():
    prev = TamperEvidentLedger.GENESIS_HASH
    events = []
    for i in range(3):
        ev = make_test_event(f"ev_{i}", prev)
        events.append(ev)
        prev = ev.compute_event_hash()

    # Trusted tip height is 5, but we only recovered 3 events
    res = LedgerRecoveryEngine.recover_ledger(events, trusted_tip_height=5)
    assert res.state == RecoveryState.ROLLBACK_DETECTED
    assert "ROLLBACK_DETECTED" in res.errors[0]


def test_ledger_conflicting_fork_detected():
    prev = TamperEvidentLedger.GENESIS_HASH
    events = []
    for i in range(3):
        ev = make_test_event(f"ev_{i}", prev)
        events.append(ev)
        prev = ev.compute_event_hash()

    # Trusted tip hash differs from recovered tip hash
    different_trusted_tip = "e" * 64
    res = LedgerRecoveryEngine.recover_ledger(events, trusted_tip_hash=different_trusted_tip)
    assert res.state == RecoveryState.CONFLICTING_RECOVERY
    assert "CONFLICTING_RECOVERY" in res.errors[0]


def test_reconstitute_dlt_validator_node():
    val1 = DLTValidator.generate("val_1", 1)
    validators = {"val_1": val1}

    # Create dummy block 1
    hdr = DLTBlockHeader(
        block_height=1,
        previous_block_hash="0"*64,
        proposer_validator_id="val_1",
        round_number=0,
        merkle_root="0"*64,
        state_root="0"*64
    )
    b_hash = hdr.compute_header_hash()
    sig = val1.sign(f"BLOCK_HEADER:v1:{b_hash}".encode('utf-8'))
    block = DLTBlock(header=hdr, block_hash=b_hash, endorsements={"val_1": sig})

    state, node, errs = LedgerRecoveryEngine.reconstitute_dlt_node(
        node_id="recovered_node_1",
        authorized_validators=validators,
        blocks=[block],
        receipts=[]
    )
    assert state == RecoveryState.VALID_RECOVERY
    assert node is not None
    assert node.get_tip_height() == 1
