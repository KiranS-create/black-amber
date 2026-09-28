"""
Test Suite: Negative Control & Clean Document Abstention.
Smart India Hackathon 2026 — Project ID: SIH26237
Code Name: Black Amber
"""

import pytest
from pathlib import Path
from core.demo.golden_case import GoldenDemoEngine


def test_clean_document_abstention(tmp_path):
    """
    Assert that the forensic engine cleanly abstains on an unwatermarked document,
    emitting NO_SIGNAL with zero false accusations.
    """
    engine = GoldenDemoEngine(demo_dir=tmp_path / "golden_run_neg")
    res = engine.negative_case()

    assert res["status"] == "PASS"
    assert res["scenario"] == "NEGATIVE_CASE_CLEAN_DOCUMENT"
    assert res["should_abstain"] is True
    assert res["attributed_recipient"] is None
    assert res["zero_false_accusation_guarantee"] is True
