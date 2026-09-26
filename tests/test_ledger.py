import pytest
import os
import hashlib
from core.ledger.ledger import EvidenceEvent, TamperEvidentLedger

def test_ledger_append_and_verify():
    """Verify appending events and verifying chain integrity."""
    ledger = TamperEvidentLedger()
    
    # Event 1
    ev1 = EvidenceEvent(
        event_id="evt_001",
        event_type="RELEASE_EVENT",
        document_id="doc_1",
        release_id="rel_1",
        recipient_id="alice",
        algorithm="ML-DSA-65",
        artifact_hash="hash1",
        evidence_hash="evhash1",
        previous_event_hash=TamperEvidentLedger.GENESIS_HASH,
        signature="sig1",
        metadata={}
    )
    h1 = ledger.append_event(ev1)
    
    # Event 2
    ev2 = EvidenceEvent(
        event_id="evt_002",
        event_type="DECRYPTION_EVENT",
        document_id="doc_1",
        release_id="rel_1",
        recipient_id="alice",
        algorithm="ML-DSA-65",
        artifact_hash="hash2",
        evidence_hash="evhash2",
        previous_event_hash=h1,
        signature="sig2",
        metadata={}
    )
    h2 = ledger.append_event(ev2)

    is_valid, errors = ledger.verify_chain()
    assert is_valid is True
    assert len(errors) == 0

def test_ledger_tampering():
    """Verify that changing an old event causes verification failure."""
    ledger = TamperEvidentLedger()
    
    ev1 = EvidenceEvent(
        event_id="evt_001",
        event_type="RELEASE_EVENT",
        document_id="doc_1",
        release_id="rel_1",
        recipient_id="alice",
        algorithm="ML-DSA-65",
        artifact_hash="hash1",
        evidence_hash="evhash1",
        previous_event_hash=TamperEvidentLedger.GENESIS_HASH,
        signature="sig1",
        metadata={}
    )
    h1 = ledger.append_event(ev1)

    ev2 = EvidenceEvent(
        event_id="evt_002",
        event_type="DECRYPTION_EVENT",
        document_id="doc_1",
        release_id="rel_1",
        recipient_id="bob",
        algorithm="ML-DSA-65",
        artifact_hash="hash2",
        evidence_hash="evhash2",
        previous_event_hash=h1,
        signature="sig2",
        metadata={}
    )
    h2 = ledger.append_event(ev2)

    # Tamper with event 1
    ledger.events[0].recipient_id = "mallory_attacker"

    is_valid, errors = ledger.verify_chain()
    assert is_valid is False
    assert len(errors) > 0
    assert "Hash mismatch at index 0" in errors[0] or "broken" in errors[0]
