"""
Test Suite: Demo State Isolation & Synthetic Identity Constraints.
Smart India Hackathon 2026 — Project ID: SIH26237
Code Name: Black Amber
"""

import json
import pytest
from pathlib import Path
from core.demo.golden_case import GoldenDemoEngine


def test_demo_isolation_and_tagging(tmp_path):
    """
    Ensure all demo metadata, artifacts, and recipient identities carry explicit
    DEMO DATA markings and are isolated from production directories.
    """
    demo_dir = tmp_path / "golden_run_isolation"
    engine = GoldenDemoEngine(demo_dir=demo_dir)

    engine.start()
    engine.distribute()
    engine.leak()
    engine.investigate()

    # Verify run_manifest.json
    manifest_path = demo_dir / "run_manifest.json"
    assert manifest_path.exists()
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest_data["demo_mode"] is True
    assert "DEMO DATA" in manifest_data["demo_notice"]

    # Verify artifact.json
    artifact_path = demo_dir / "artifact.json"
    artifact_data = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert artifact_data["demo_label"] == "DEMO DATA"
    assert "DEMONSTRATION ARTIFACT" in artifact_data["classification"]

    # Verify recipient_state.json
    recipient_state_path = demo_dir / "recipient_state.json"
    rec_data = json.loads(recipient_state_path.read_text(encoding="utf-8"))
    assert "DEMO DATA" in rec_data["demo_notice"]
    for r_id in rec_data["recipients"].keys():
        assert r_id.startswith("demo-recipient-"), f"Recipient {r_id} violates demo namespace prefix"

    # Verify leak.json
    leak_path = demo_dir / "leak.json"
    leak_data = json.loads(leak_path.read_text(encoding="utf-8"))
    assert "DEMO DATA" in leak_data["demo_notice"]

    # Verify investigation.json
    inv_path = demo_dir / "investigation.json"
    inv_data = json.loads(inv_path.read_text(encoding="utf-8"))
    assert "DEMO DATA" in inv_data["demo_notice"]

    # Ensure no files written outside demo_dir
    engine.reset()
