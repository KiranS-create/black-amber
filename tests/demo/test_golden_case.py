"""
Test Suite: Golden Case End-to-End Forensic Investigation.
Smart India Hackathon 2026 — Project ID: SIH26237
Code Name: Black Amber
"""

import pytest
import json
from pathlib import Path
from core.demo.golden_case import GoldenDemoEngine, GoldenStepStatus


def test_golden_case_lifecycle(tmp_path):
    """
    Test the full 16-step golden investigation lifecycle in an isolated directory.
    Verifies: start -> distribute -> leak -> investigate -> verify -> tamper -> restore -> reset.
    """
    engine = GoldenDemoEngine(demo_dir=tmp_path / "golden_run")

    # 1. Start
    res_start = engine.start()
    assert res_start["status"] == "PASS"
    assert (tmp_path / "golden_run" / "original_document.png").exists()
    assert (tmp_path / "golden_run" / "artifact.json").exists()
    assert (tmp_path / "golden_run" / "run_manifest.json").exists()

    artifact_json = json.loads((tmp_path / "golden_run" / "artifact.json").read_text(encoding="utf-8"))
    assert artifact_json["demo_label"] == "DEMO DATA"
    assert artifact_json["dimensions"] == "800x1000"

    # 2. Distribute
    res_dist = engine.distribute()
    assert res_dist["status"] == "PASS"
    assert res_dist["recipients_count"] == 3
    assert (tmp_path / "golden_run" / "recipient_state.json").exists()
    assert (tmp_path / "golden_run" / "distribution.json").exists()
    assert (tmp_path / "golden_run" / "watermarked_demo_recipient_a.png").exists()
    assert (tmp_path / "golden_run" / "watermarked_demo_recipient_b.png").exists()
    assert (tmp_path / "golden_run" / "watermarked_demo_recipient_c.png").exists()

    dist_json = json.loads((tmp_path / "golden_run" / "distribution.json").read_text(encoding="utf-8"))
    for r_id in ["demo-recipient-a", "demo-recipient-b", "demo-recipient-c"]:
        evt = dist_json["decryption_events"][r_id]
        assert evt["ssim"] >= 0.80
        assert evt["is_visually_equivalent"] is True
        assert evt["signature_verified"] is True

    # 3. Leak
    res_leak = engine.leak(recipient_id="demo-recipient-b")
    assert res_leak["status"] == "PASS"
    assert (tmp_path / "golden_run" / "leak.png").exists()
    assert (tmp_path / "golden_run" / "leak.json").exists()

    leak_json = json.loads((tmp_path / "golden_run" / "leak.json").read_text(encoding="utf-8"))
    # Ensure blind leak ingestion: suspect identity must NOT be leaked in leak metadata
    assert "demo-recipient-b" not in leak_json
    assert leak_json["investigation_status"] == "PENDING_FORENSIC_ANALYSIS"

    # 4. Investigate
    res_inv = engine.investigate()
    assert res_inv["status"] == "PASS"
    assert res_inv["attributed_suspect"] == "demo-recipient-b"
    assert res_inv["confidence"] >= 0.99
    assert (tmp_path / "golden_run" / "investigation.json").exists()

    inv_json = json.loads((tmp_path / "golden_run" / "investigation.json").read_text(encoding="utf-8"))
    assert inv_json["verdict"] == "ATTRIBUTED"
    assert inv_json["attributed_recipient_id"] == "demo-recipient-b"
    assert inv_json["should_abstain"] is False
    assert inv_json["candidate_evaluations"]["demo-recipient-b"]["bit_error_rate"] == 0.0
    assert inv_json["candidate_evaluations"]["demo-recipient-a"]["bit_error_rate"] > 0.3
    assert inv_json["candidate_evaluations"]["demo-recipient-c"]["bit_error_rate"] > 0.3

    # 5. Verify (Evidence Package & 12-Pillar Audit)
    res_ver = engine.verify()
    assert res_ver["status"] == "PASS"
    assert res_ver["verification_status"] == "VERIFIED"
    assert res_ver["all_12_pillars_passed"] is True
    assert (tmp_path / "golden_run" / "evidence_package.zip").exists()
    assert (tmp_path / "golden_run" / "verification.json").exists()

    ver_json = json.loads((tmp_path / "golden_run" / "verification.json").read_text(encoding="utf-8"))
    assert all(ver_json["pillars"].values())

    # 6. Tamper (Controlled Merkle Corruption)
    res_tamper = engine.tamper()
    assert res_tamper["status"] == "PASS"
    assert res_tamper["verifier_verdict"] == "INVALID"
    assert res_tamper["rejection_confirmed"] is True
    assert (tmp_path / "golden_run" / "evidence_package_tampered.zip").exists()
    assert (tmp_path / "golden_run" / "tamper.json").exists()

    # 7. Restore
    res_restore = engine.restore()
    assert res_restore["status"] == "PASS"
    assert res_restore["verifier_verdict"] == "VERIFIED"
    assert (tmp_path / "golden_run" / "restore.json").exists()

    # 8. Reset
    res_reset = engine.reset()
    assert res_reset["status"] == "PASS"
    assert res_reset["production_zero_state"] is True
    assert not (tmp_path / "golden_run").exists() or len(list((tmp_path / "golden_run").iterdir())) == 0


def test_golden_case_run_judge(tmp_path):
    """
    Test running the complete judge walkthrough method in one call.
    """
    engine = GoldenDemoEngine(demo_dir=tmp_path / "golden_run_judge")
    res = engine.run_judge(quick=True, output_json=True)
    assert res["status"] == "PASS"
    assert res["verdict"] == "demo-recipient-b"
    assert res["confidence"] >= 0.99
    assert res["verification_status"] == "VERIFIED"
    assert res["tamper_rejected"] is True
    assert len(res["steps"]) == 7
    engine.reset()
