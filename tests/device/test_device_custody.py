"""
SIH26237 - Test Device Custody Chain & Transition Rules
=======================================================
Verifies custody tracking and anti-fabrication enforcement on capture vs transfer actions.
"""

import pytest
from core.physical.device_custody import DeviceCustodyLedger, DeviceCustodyAction
from core.physical.epistemic import EpistemicStatus, AntiFabricationViolation


def test_device_custody_lifecycle():
    """Verify append-only custody chain recording and sealing."""
    ledger = DeviceCustodyLedger(ledger_id="LEDGER-001")

    ev1 = ledger.record_transition(
        action=DeviceCustodyAction.CONNECTED,
        device_id="phone_a",
        artifact_hash="hash_art_01",
        epistemic_status=EpistemicStatus.DEVICE_IN_LOOP
    )
    assert ev1.previous_event_hash == "GENESIS"

    ev2 = ledger.record_transition(
        action=DeviceCustodyAction.TRANSFERRED,
        device_id="phone_a",
        artifact_hash="hash_art_02",
        is_optical_capture=False,
        epistemic_status=EpistemicStatus.DEVICE_IN_LOOP
    )
    assert ev2.previous_event_hash == ev1.event_hash

    root = ledger.seal_ledger()
    assert ledger.is_sealed is True
    assert len(root) == 64

    # Appending after seal must raise ValueError
    with pytest.raises(ValueError, match="Cannot append event to a sealed"):
        ledger.record_transition(action=DeviceCustodyAction.ANALYZED, device_id="phone_a", artifact_hash="h")


def test_device_custody_rejects_false_captured_action():
    """Verify AntiFabricationGuard rejects declaring CAPTURED without genuine optical capture."""
    ledger = DeviceCustodyLedger(ledger_id="LEDGER-002")
    with pytest.raises(AntiFabricationViolation, match="Cannot declare custody action 'CAPTURED'"):
        ledger.record_transition(
            action=DeviceCustodyAction.CAPTURED,
            device_id="phone_a",
            artifact_hash="hash_art_01",
            is_optical_capture=False
        )
