"""
Test Suite: Downstream Lineage Gap & Incomplete Trace Abstention.
Smart India Hackathon 2026 — Project ID: SIH26237
Code Name: Black Amber
"""

import pytest
from pathlib import Path
from core.demo.golden_case import GoldenDemoEngine


def test_downstream_gap_abstention(tmp_path):
    """
    Assert that the forensic engine identifies unmonitored lineage boundaries,
    recording DOWNSTREAM_GAP / INSUFFICIENT_EVIDENCE without over-attributing guilt.
    """
    engine = GoldenDemoEngine(demo_dir=tmp_path / "golden_run_gap")
    res = engine.downstream_gap_case()

    assert res["status"] == "PASS"
    assert res["scenario"] == "DOWNSTREAM_GAP_UNMONITORED_TRANSFER"
    assert res["has_downstream_gap"] is True
    assert res["boundary_state"] == "DOWNSTREAM_GAP"
    assert res["last_known_holder"] == "demo-recipient-b"
    assert res["decision_state"] == "INSUFFICIENT_EVIDENCE"
    assert res["attributed_principal"] is None
    assert res["over_attribution_prevented"] is True
