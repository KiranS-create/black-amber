"""
Test Suite: Deterministic Reproducibility Under Fixed Seed.
Smart India Hackathon 2026 — Project ID: SIH26237
Code Name: Black Amber
"""

import json
import pytest
from pathlib import Path
from core.demo.golden_case import GoldenDemoEngine


def test_deterministic_reproducibility(tmp_path):
    """
    Ensure bitwise identical keypairs, watermark carriers, and hashes across repeated runs.
    """
    dir1 = tmp_path / "run_1"
    dir2 = tmp_path / "run_2"

    engine1 = GoldenDemoEngine(demo_dir=dir1, seed=42)
    engine2 = GoldenDemoEngine(demo_dir=dir2, seed=42)

    # Run 1: start + distribute
    res1_start = engine1.start()
    res1_dist = engine1.distribute()

    # Run 2: start + distribute
    res2_start = engine2.start()
    res2_dist = engine2.distribute()

    # Assert canonical original document hashes match exactly
    assert res1_start["sha256"] == res2_start["sha256"]

    # Assert recipient states match exactly
    rec1 = json.loads((dir1 / "recipient_state.json").read_text(encoding="utf-8"))
    rec2 = json.loads((dir2 / "recipient_state.json").read_text(encoding="utf-8"))

    for r_id in ["demo-recipient-a", "demo-recipient-b", "demo-recipient-c"]:
        assert rec1["recipients"][r_id]["kem_public_key_b64"] == rec2["recipients"][r_id]["kem_public_key_b64"]
        assert rec1["recipients"][r_id]["dsa_public_key_b64"] == rec2["recipients"][r_id]["dsa_public_key_b64"]

    # Assert watermarked images match byte-for-byte
    for r_id in ["demo-recipient-a", "demo-recipient-b", "demo-recipient-c"]:
        fname = f"watermarked_{r_id.replace('-', '_')}.png"
        bytes1 = (dir1 / fname).read_bytes()
        bytes2 = (dir2 / fname).read_bytes()
        assert bytes1 == bytes2, f"Watermarked image for {r_id} differed across runs with identical seed"
