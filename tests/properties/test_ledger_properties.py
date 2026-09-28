"""
tests/properties/test_ledger_properties.py

Property-based testing and mutation fuzzing for TamperEvidentLedger:
- INVARIANT-004: Modified, deleted, or reordered events strictly fail verification
- Anti-replay and anti-duplicate event enforcement
- Fork detection and stale snapshot rejection [INVARIANT-012]
"""

import copy
import hashlib
import json
import pytest
from core.ledger.ledger import TamperEvidentLedger, EvidenceEvent
from core.testing.property_engine import PropertyRunner, DeterministicGenerator
from core.security.invariants import assert_invariant


def build_random_ledger(g: DeterministicGenerator, length: int = 10) -> TamperEvidentLedger:
    """Helper to generate a valid hash-chained ledger of length N."""
    ledger = TamperEvidentLedger()
    prev_hash = TamperEvidentLedger.GENESIS_HASH
    tenant_id = g.generate_tenant_id()

    for i in range(length):
        eid = f"ev-{g.alphanumeric(8, 12)}"
        doc_id = g.generate_document_id()
        rel_id = f"REL-{g.alphanumeric(6, 8)}"
        rec_id = g.generate_recipient_id()

        ev = EvidenceEvent(
            event_id=eid,
            event_type=g.choice(["DECRYPTION_EVENT", "RELEASE_EVENT", "FORWARDING_EVENT", "EXPORT_EVENT"]),
            timestamp=f"2026-09-27T10:{i:02d}:00Z",
            document_id=doc_id,
            release_id=rel_id,
            recipient_id=rec_id,
            algorithm="ML-DSA-65",
            artifact_hash=hashlib.sha256(g.bytes_data(32)).hexdigest(),
            evidence_hash=hashlib.sha256(g.bytes_data(32)).hexdigest(),
            previous_event_hash=prev_hash,
            signature=g.bytes_data(64).hex(),
            metadata={"tenant_id": tenant_id, "step": i},
        )
        prev_hash = ledger.append_event(ev)

    return ledger


def test_property_ledger_mutation_fuzzing(runner: PropertyRunner):
    """
    INVARIANT-004: Any mutation (content tampering, previous_hash alteration,
    reordering, deletion, or insertion) must cause verify_chain() to fail closed.
    """
    def prop(g: DeterministicGenerator):
        chain_len = g.integer(5, 20)
        ledger = build_random_ledger(g, length=chain_len)

        # Baseline: fresh valid ledger must verify cleanly
        valid, errors = ledger.verify_chain()
        assert valid, f"Fresh ledger failed verification: {errors}"

        # Choose a mutation type
        mutation_type = g.choice([
            "mutate_body",
            "mutate_prev_hash",
            "mutate_event_id",
            "reorder_events",
            "delete_event",
            "insert_event",
        ])

        target_idx = g.integer(0, chain_len - 1)

        if mutation_type == "mutate_body":
            # Tamper with an event's metadata or payload
            ledger.events[target_idx].metadata["tampered"] = True
        elif mutation_type == "mutate_prev_hash":
            # Corrupt previous_event_hash
            ledger.events[target_idx].previous_event_hash = "deadbeef" * 8
        elif mutation_type == "mutate_event_id":
            # Alter event_id
            ledger.events[target_idx].event_id = f"tampered-{g.alphanumeric(8, 8)}"
        elif mutation_type == "reorder_events":
            if chain_len >= 2:
                idx1 = g.integer(0, chain_len - 2)
                idx2 = g.integer(idx1 + 1, chain_len - 1)
                ledger.events[idx1], ledger.events[idx2] = ledger.events[idx2], ledger.events[idx1]
        elif mutation_type == "delete_event":
            del ledger.events[target_idx]
        elif mutation_type == "insert_event":
            # Inject an alien event
            alien_ev = EvidenceEvent(
                event_id=f"alien-{g.alphanumeric(8, 8)}",
                event_type="UNAUTHORIZED_INJECTION",
                document_id="DOC-999",
                release_id="REL-999",
                recipient_id="rec-intruder",
                algorithm="ML-DSA-65",
                artifact_hash="00" * 32,
                evidence_hash="00" * 32,
                previous_event_hash="00" * 32,
                signature="00" * 64,
            )
            ledger.events.insert(target_idx, alien_ev)

        # Invariant assertion: chain MUST NOT verify
        tampered_valid, tampered_errors = ledger.verify_chain()
        assert_invariant(
            not tampered_valid,
            "INVARIANT-004",
            f"Ledger verified as valid after mutation '{mutation_type}' at index {target_idx}",
            g.seed,
            counterexample={"mutation": mutation_type, "index": target_idx},
        )
        assert len(tampered_errors) > 0

    res = runner.run_property("ledger_mutation_fuzzing", prop, iterations=250)
    assert res.passed, res.error_message


def test_property_ledger_anti_replay_invariant(runner: PropertyRunner):
    """
    Property: An event with an already-seen event_id is strictly rejected upon append.
    """
    def prop(g: DeterministicGenerator):
        ledger = build_random_ledger(g, length=g.integer(3, 8))
        existing_event = g.choice(ledger.events)

        # Attempt to append duplicate event_id
        replayed = existing_event.model_copy(deep=True) if hasattr(existing_event, "model_copy") else copy.deepcopy(existing_event)
        replayed.previous_event_hash = ledger.get_last_event_hash()

        with pytest.raises(ValueError, match="Replay detected"):
            ledger.append_event(replayed)

    res = runner.run_property("ledger_anti_replay", prop, iterations=150)
    assert res.passed, res.error_message


def clone_ledger(orig: TamperEvidentLedger) -> TamperEvidentLedger:
    """Helper to clone a ledger without pickling thread locks."""
    clone = TamperEvidentLedger()
    for ev in orig.events:
        clone.append_event(ev.model_copy(deep=True) if hasattr(ev, "model_copy") else copy.deepcopy(ev))
    return clone


def test_property_ledger_fork_and_stale_detection(runner: PropertyRunner):
    """
    INVARIANT-012: Stale ledger snapshots or divergent forks are detected
    by tip desynchronization.
    """
    def prop(g: DeterministicGenerator):
        # Create common trunk
        trunk_len = g.integer(3, 6)
        ledger_a = build_random_ledger(g, length=trunk_len)
        ledger_b = clone_ledger(ledger_a)

        # Diverge branch A
        ev_a = EvidenceEvent(
            event_id=f"forkA-{g.alphanumeric(8, 8)}",
            event_type="BRANCH_A",
            document_id="DOC-A",
            release_id="REL-A",
            recipient_id="rec-A",
            algorithm="ML-DSA-65",
            artifact_hash="aa" * 32,
            evidence_hash="aa" * 32,
            previous_event_hash=ledger_a.get_last_event_hash(),
            signature="aa" * 64,
        )
        tip_a = ledger_a.append_event(ev_a)

        # Diverge branch B
        ev_b = EvidenceEvent(
            event_id=f"forkB-{g.alphanumeric(8, 8)}",
            event_type="BRANCH_B",
            document_id="DOC-B",
            release_id="REL-B",
            recipient_id="rec-B",
            algorithm="ML-DSA-65",
            artifact_hash="bb" * 32,
            evidence_hash="bb" * 32,
            previous_event_hash=ledger_b.get_last_event_hash(),
            signature="bb" * 64,
        )
        tip_b = ledger_b.append_event(ev_b)

        # Invariant: Tips must diverge and detect fork
        assert tip_a != tip_b
        assert ledger_a.get_last_event_hash() != ledger_b.get_last_event_hash()

    res = runner.run_property("ledger_fork_detection", prop, iterations=100)
    assert res.passed, res.error_message
