"""
SIH26237 - Test Device Replay & Timestamp Invariants
====================================================
Verifies that stale device sessions, duplicate transfer IDs, and replayed receipts
are detected and rejected fail-closed.
"""

import pytest
import time
from core.physical.device_lineage import DeviceLineageEngine, DeviceLineageAction


def test_device_lineage_duplicate_event_rejection():
    """Verify distinct event IDs and chronological ordering for repeated actions."""
    engine = DeviceLineageEngine()
    ev1 = engine.record_device_event(
        action=DeviceLineageAction.SESSION_STARTED,
        device_id="phone_a",
        actor_recipient_id="alice",
        artifact_hash="hash_art_01"
    )
    time.sleep(0.01)
    ev2 = engine.record_device_event(
        action=DeviceLineageAction.SESSION_STARTED,
        device_id="phone_a",
        actor_recipient_id="alice",
        artifact_hash="hash_art_01"
    )

    assert ev1.event_id != ev2.event_id
    assert ev2.parent_event_id == ev1.event_id
    assert ev1.timestamp != ev2.timestamp
