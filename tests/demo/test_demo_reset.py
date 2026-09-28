"""
Test Suite: Demo Reset & Production Zero-State Invariant.
Smart India Hackathon 2026 — Project ID: SIH26237
Code Name: Black Amber
"""

import pytest
from pathlib import Path
from core.demo.golden_case import GoldenDemoEngine
from apps.api.orchestrator import default_orchestrator


def test_demo_reset_zero_state(tmp_path):
    """
    Ensure reset purges all generated demo files and leaves zero residue.
    """
    demo_dir = tmp_path / "golden_run_reset_test"
    engine = GoldenDemoEngine(demo_dir=demo_dir)

    # Generate some artifacts
    engine.start()
    engine.distribute()
    assert demo_dir.exists()
    assert len(list(demo_dir.glob("*"))) > 0

    # Reset
    res_reset = engine.reset()
    assert res_reset["status"] == "PASS"
    assert res_reset["production_zero_state"] is True
    assert not demo_dir.exists() or len(list(demo_dir.glob("*"))) == 0

    # Test reset idempotency (calling reset on empty state)
    res_reset2 = engine.reset()
    assert res_reset2["status"] == "PASS"
    assert res_reset2["deleted_artifacts_count"] == 0


def test_orchestrator_demo_reset_collections():
    """
    Ensure orchestrator.reset_demo_state() verifies that all collections are 0.
    """
    counts = default_orchestrator.reset_demo_state(clear_recipients=True)
    assert counts["documents"] == 0
    assert counts["releases"] == 0
    assert counts["recipients"] == 0
    assert counts["investigations"] == 0
    assert counts["evidence"] == 0
    assert counts["ledger_events"] == 0
