"""
Unit and Scalability Tests for ScalableLedger.

Validates:
- Hash-chaining integrity and O(1) indexing
- Epoch Merkle checkpointing
- Incremental verification vs full chain verification
- Duplicate event rejection
- Tampering and corruption detection
- Multi-tenant query isolation
"""

import pytest
import hashlib
from datetime import datetime, timezone

from core.ledger.scale import ScalableLedger
from core.ledger.ledger import EvidenceEvent


def create_test_event(
    event_id: str,
    prev_hash: str,
    recipient_id: str = "rec_alice",
    release_id: str = "rel_001",
    document_id: str = "doc_001",
    event_type: str = "DECRYPTION_EVENT"
) -> EvidenceEvent:
    art_hash = hashlib.sha256(f"artifact_{event_id}".encode()).hexdigest()
    ev_hash = hashlib.sha256(f"evidence_{event_id}".encode()).hexdigest()
    return EvidenceEvent(
        event_id=event_id,
        timestamp="2026-09-27T12:00:00Z",
        event_type=event_type,
        document_id=document_id,
        release_id=release_id,
        recipient_id=recipient_id,
        artifact_hash=art_hash,
        evidence_hash=ev_hash,
        algorithm="ML-DSA-65",
        signature="dummysig",
        previous_event_hash=prev_hash
    )


def test_scalable_ledger_append_and_indexed_queries():
    ledger = ScalableLedger(checkpoint_interval=10)
    tenant = "tenant_crypto"

    # Append 5 events
    prev_h = ledger.get_last_event_hash()
    for i in range(5):
        ev = create_test_event(f"ev_{i:03d}", prev_h, recipient_id=f"rec_{i % 2}")
        prev_h = ledger.append_event(ev, tenant_id=tenant)

    assert ledger.count() == 5
    assert ledger.count(tenant) == 5
    assert ledger.count("other_tenant") == 0

    # Test O(1) lookup by event_id
    ev_ref = ledger.get_event_by_id("ev_002")
    assert ev_ref is not None
    assert ev_ref.event_id == "ev_002"

    # Test O(1) find_decryption_event
    found = ledger.find_decryption_event("rec_0", "rel_001", "doc_001", tenant_id=tenant)
    assert found is not None
    assert found.recipient_id == "rec_0"

    # Cross-tenant query must return None
    assert ledger.find_decryption_event("rec_0", "rel_001", "doc_001", tenant_id="other_tenant") is None


def test_checkpointing_and_incremental_verification():
    ledger = ScalableLedger(checkpoint_interval=5)
    tenant = "tenant_corp"

    prev_h = ledger.get_last_event_hash()
    for i in range(12):
        ev = create_test_event(f"ev_{i:03d}", prev_h)
        prev_h = ledger.append_event(ev, tenant_id=tenant)

    # 12 events with checkpoint interval 5 -> 2 checkpoints created (at 5 and 10)
    assert len(ledger.checkpoints) == 2
    assert ledger.checkpoints[0].event_count == 5
    assert ledger.checkpoints[1].event_count == 10

    # Incremental verification
    valid, errors = ledger.verify_chain_incremental()
    assert valid is True
    assert len(errors) == 0

    # Full chain verification
    full_valid, full_errors = ledger.verify_full_chain()
    assert full_valid is True
    assert len(full_errors) == 0


def test_replay_duplicate_rejection():
    ledger = ScalableLedger()
    prev_h = ledger.get_last_event_hash()
    ev1 = create_test_event("ev_unique_01", prev_h)
    ledger.append_event(ev1)

    # Duplicate append must fail
    with pytest.raises(ValueError, match="Replay detected"):
        ledger.append_event(ev1)


def test_tamper_detection():
    ledger = ScalableLedger()
    prev_h = ledger.get_last_event_hash()
    for i in range(4):
        ev = create_test_event(f"ev_tamper_{i}", prev_h)
        prev_h = ledger.append_event(ev)

    # Tamper with an event in internal storage
    ledger._events[2].recipient_id = "rec_malicious"

    valid, errors = ledger.verify_full_chain()
    assert valid is False
    assert any("Hash mismatch" in err for err in errors)
