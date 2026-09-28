"""
SIH26237 - Test Device Lineage Integration
==========================================
Verifies device lifecycle events enter the Sparse Merkle Lineage Graph.
"""

import pytest
from core.physical.device_lineage import DeviceLineageEngine, DeviceLineageAction
from core.physical.epistemic import EpistemicStatus


def test_device_lineage_lifecycle_events():
    """Verify recording of device session events in lineage engine."""
    engine = DeviceLineageEngine(tenant_id="TENANT-TEST")

    ev1 = engine.record_device_event(
        action=DeviceLineageAction.DEVICE_CONNECTED,
        device_id="phone_a",
        actor_recipient_id="alice",
        artifact_hash="hash_root_artifact_01",
        epistemic_status=EpistemicStatus.DEVICE_IN_LOOP
    )
    assert ev1.parent_event_id is None
    assert ev1.merkle_leaf_hash != ""

    ev2 = engine.record_device_event(
        action=DeviceLineageAction.ARTIFACT_TRANSFERRED,
        device_id="phone_a",
        actor_recipient_id="alice",
        artifact_hash="hash_transferred_artifact_01",
        parent_artifact_id="ART-01",
        child_artifact_id="ART-02",
        epistemic_status=EpistemicStatus.DEVICE_IN_LOOP
    )
    assert ev2.parent_event_id == ev1.event_id

    root = engine.compute_merkle_root()
    assert len(root) == 64
    assert root != "0" * 64


def test_device_lineage_device_query():
    """Verify device-specific filtering in lineage history."""
    engine = DeviceLineageEngine()
    engine.record_device_event(action=DeviceLineageAction.SESSION_STARTED, device_id="phone_a", actor_recipient_id="alice", artifact_hash="h1")
    engine.record_device_event(action=DeviceLineageAction.SESSION_STARTED, device_id="phone_b", actor_recipient_id="bob", artifact_hash="h2")

    events_a = engine.get_events_for_device("phone_a")
    events_b = engine.get_events_for_device("phone_b")
    assert len(events_a) == 1
    assert len(events_b) == 1
    assert events_a[0].actor_recipient_id == "alice"
    assert events_b[0].actor_recipient_id == "bob"
