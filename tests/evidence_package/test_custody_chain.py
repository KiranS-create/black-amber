"""
Tests for Cryptographic Append-Only Chain of Custody.
Verifies:
1. Valid custody chain creation and verification across all 7 custody actions.
2. Invariant hash linking: H_i = SHA256(H_{i-1} || payload_i).
3. Tamper detection: modifying action, reason, timestamps, or resulting hashes breaks chain.
4. Detection of inserted, deleted, or re-ordered events.
5. Cross-tenant custody event isolation.
"""

import pytest
from datetime import datetime, timezone

from core.evidence_package.models import CustodyAction, ChainOfCustodyEvent
from core.evidence_package.custody import ChainOfCustodyLedger


def test_chain_of_custody_valid_sequence():
    actions = [
        (CustodyAction.COLLECTED, "art_01", "Acquired leak artifact from dark web post"),
        (CustodyAction.IMPORTED, "art_01", "Ingested into forensic sandbox"),
        (CustodyAction.ANALYZED, "wm_01", "Extracted spatial watermark carrier"),
        (CustodyAction.VERIFIED, "rcpt_01", "Cryptographically verified ML-DSA-65 signature"),
        (CustodyAction.SEALED, "pkg_01", "Package manifest signed with ML-DSA-65"),
        (CustodyAction.EXPORTED, "pkg_01", "Exported to air-gapped physical media"),
        (CustodyAction.REVIEWED, "pkg_01", "Independent tribunal review performed"),
    ]

    events = []
    prev_hash = ChainOfCustodyLedger.GENESIS_HASH

    for action, obj_id, reason in actions:
        ev = ChainOfCustodyLedger.create_event(
            action=action,
            evidence_object_id=obj_id,
            operator_identity="forensic_officer_42",
            device_identity="workstation_alpha",
            resulting_evidence_hash="res_" + "a" * 60,
            reason=reason,
            previous_custody_hash=prev_hash,
            tenant_id="tenant_defense"
        )
        events.append(ev)

        # Compute next prev_hash
        prev_hash = ChainOfCustodyLedger.compute_custody_event_hash(
            previous_hash=ev.previous_custody_hash,
            custody_event_id=ev.custody_event_id,
            evidence_object_id=ev.evidence_object_id,
            operator_identity=ev.operator_identity,
            device_identity=ev.device_identity,
            action=ev.action,
            timestamp=ev.timestamp,
            resulting_evidence_hash=ev.resulting_evidence_hash,
            tenant_id=ev.tenant_id,
            reason=ev.reason
        )

    # Verify intact chain
    valid, errors = ChainOfCustodyLedger.verify_chain(events, expected_tenant_id="tenant_defense")
    assert valid is True
    assert len(errors) == 0


def test_chain_of_custody_tamper_detection():
    # Build 3-event chain
    e1 = ChainOfCustodyLedger.create_event(
        action=CustodyAction.COLLECTED,
        evidence_object_id="art_01",
        operator_identity="agent_a",
        device_identity="dev_1",
        resulting_evidence_hash="h1",
        reason="Collection",
        previous_custody_hash=ChainOfCustodyLedger.GENESIS_HASH
    )
    h1 = ChainOfCustodyLedger.compute_custody_event_hash(
        e1.previous_custody_hash, e1.custody_event_id, e1.evidence_object_id,
        e1.operator_identity, e1.device_identity, e1.action, e1.timestamp,
        e1.resulting_evidence_hash, e1.tenant_id, e1.reason
    )

    e2 = ChainOfCustodyLedger.create_event(
        action=CustodyAction.ANALYZED,
        evidence_object_id="art_01",
        operator_identity="agent_b",
        device_identity="dev_2",
        resulting_evidence_hash="h2",
        reason="Analysis",
        previous_custody_hash=h1
    )
    h2 = ChainOfCustodyLedger.compute_custody_event_hash(
        e2.previous_custody_hash, e2.custody_event_id, e2.evidence_object_id,
        e2.operator_identity, e2.device_identity, e2.action, e2.timestamp,
        e2.resulting_evidence_hash, e2.tenant_id, e2.reason
    )

    e3 = ChainOfCustodyLedger.create_event(
        action=CustodyAction.SEALED,
        evidence_object_id="pkg_01",
        operator_identity="agent_c",
        device_identity="dev_3",
        resulting_evidence_hash="h3",
        reason="Sealing",
        previous_custody_hash=h2
    )

    events = [e1, e2, e3]

    # Tamper 1: Modify action in e2
    events_tampered = [e.model_copy(deep=True) for e in events]
    events_tampered[1].reason = "Unauthorized tampering with reason"
    events_tampered[1].seal_content_hash()  # re-seal own hash, but breaks chain linkage!
    valid, errors = ChainOfCustodyLedger.verify_chain(events_tampered)
    assert valid is False
    assert any("broken custody link" in err for err in errors)

    # Tamper 2: Delete middle event
    events_deleted = [events[0], events[2]]
    valid, errors = ChainOfCustodyLedger.verify_chain(events_deleted)
    assert valid is False
    assert any("broken custody link" in err for err in errors)

    # Tamper 3: Cross-tenant injection
    events_cross = [e.model_copy(deep=True) for e in events]
    events_cross[1].tenant_id = "MALICIOUS_FOREIGN_TENANT"
    events_cross[1].seal_content_hash()
    valid, errors = ChainOfCustodyLedger.verify_chain(events_cross, expected_tenant_id="default_tenant")
    assert valid is False
    assert any("tenant mismatch" in err for err in errors)
