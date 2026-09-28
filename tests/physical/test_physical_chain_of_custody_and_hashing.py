"""
SIH26237 - Test Physical Chain of Custody & Cryptographic Hashing
"""

import pytest
import numpy as np
from pathlib import Path
from core.physical.custody import PhysicalChainOfCustodyTracker


def test_physical_custody_tracker_lifecycle(tmp_path):
    """Verify physical chain of custody logs actions and seals artifact hashes correctly."""
    tracker = PhysicalChainOfCustodyTracker(
        run_id="run_test_custody_001",
        base_dir=str(tmp_path / "custody_runs")
    )

    fake_img = np.zeros((100, 100, 3), dtype=np.uint8)
    ev1 = tracker.record_transition(
        action="CAPTURED",
        artifact_bytes=fake_img.tobytes(),
        filename="test_capture.raw",
        device_id="DEV_TEST_01",
        notes="Physical capture test"
    )

    ev2 = tracker.record_transition(
        action="ANALYZED",
        artifact_bytes=fake_img.tobytes(),
        filename="test_analysis.raw",
        device_id="DEV_WS_01",
        notes="Watermark decoding pass"
    )

    ev3 = tracker.record_transition(
        action="SEALED",
        artifact_bytes=b"SEAL_SIGNATURE",
        filename="seal.sig",
        device_id="DEV_WS_01",
        notes="Package cryptographically sealed"
    )

    out_file = tracker.save_and_seal_ledger()
    assert Path(out_file).exists()
    assert tracker.ledger.is_sealed is True
    assert len(tracker.ledger.events) == 3
    assert tracker.ledger.events[0].action == "CAPTURED"
    assert tracker.ledger.events[-1].action == "SEALED"
    assert len(tracker.ledger.root_custody_hash) == 64
