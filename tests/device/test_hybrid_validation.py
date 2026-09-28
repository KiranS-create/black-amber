"""
SIH26237 - Test Hybrid Physical Validation & Golden Experiment
=============================================================
Tests the end-to-end 13-step golden experiment:
- Phone A & Phone B integration
- Multi-format forensic validation (PDF, DOCX, PPTX, XLSX, PNG, JPEG)
- Display & network session participation
- Transfer bitwise integrity & latency auditing
- Sparse Merkle lineage tree & custody ledger root
- NIST FIPS 204 ML-DSA-65 signed Evidence Package & offline verification
- Machine-readable artifact generation and epistemic declarations
"""

import os
import json
import tempfile
import pytest

from core.physical.epistemic import EpistemicStatus
from core.physical.device_in_loop import (
    DeviceInTheLoopGoldenEngine,
    GoldenExperimentReport
)


@pytest.fixture(scope="module")
def golden_experiment_run():
    """Executes the full 13-step golden experiment in an isolated temporary directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        engine = DeviceInTheLoopGoldenEngine(tenant_id="TENANT-SIH-2026")
        report = engine.run_full_golden_experiment(output_dir=tmp_dir)
        yield report, tmp_dir


def test_golden_experiment_epistemic_status(golden_experiment_run):
    """Verify overall experiment classification is HYBRID_VALIDATION with honest subcomponents."""
    report, _ = golden_experiment_run
    
    assert report.epistemic_record.overall_status == EpistemicStatus.HYBRID_VALIDATION
    assert report.epistemic_record.has_unsupported_claim is False
    
    # Subcomponents verification
    sub = report.epistemic_record.subcomponents
    assert "PHONE_A_WORKFLOW" in sub
    assert sub["PHONE_A_WORKFLOW"].status == EpistemicStatus.DEVICE_IN_LOOP
    assert "PHONE_B_WORKFLOW" in sub
    assert sub["PHONE_B_WORKFLOW"].status == EpistemicStatus.DEVICE_IN_LOOP
    assert "DISPLAY" in sub
    assert sub["DISPLAY"].status == EpistemicStatus.DEVICE_IN_LOOP
    assert "CAMERA_CAPTURE" in sub
    assert sub["CAMERA_CAPTURE"].status == EpistemicStatus.NOT_VERIFIED
    assert "PRINT_VALIDATION" in sub
    assert sub["PRINT_VALIDATION"].status == EpistemicStatus.UNAVAILABLE
    assert "SCAN_VALIDATION" in sub
    assert sub["SCAN_VALIDATION"].status == EpistemicStatus.UNAVAILABLE


def test_golden_experiment_13_steps(golden_experiment_run):
    """Verify all 13 experimental steps executed and produced structured output."""
    report, _ = golden_experiment_run
    steps = report.step_results
    
    expected_steps = [
        "step_1_create_artifact",
        "step_2_crypto_state",
        "step_3_phone_a_access",
        "step_4_authenticate_phone_a",
        "step_5_render_artifact",
        "step_6_record_metadata",
        "step_7_phone_b_endpoint",
        "step_8_phone_b_workflow",
        "step_9_transfer",
        "step_10_verify_byte_integrity",
        "step_11_lineage_and_custody",
        "step_12_package_evidence",
        "step_13_verify_offline"
    ]
    
    for s in expected_steps:
        assert s in steps, f"Step '{s}' missing from experiment results"
        assert steps[s]["status"] == "PASS"


def test_golden_experiment_multiformat_coverage(golden_experiment_run):
    """Verify multi-format evaluation across PDF, DOCX, PPTX, XLSX, PNG, JPEG."""
    report, _ = golden_experiment_run
    format_results = report.format_results
    
    formats_evaluated = {r.format_name for r in format_results}
    expected_formats = {"PDF", "DOCX", "PPTX", "XLSX", "PNG", "JPEG"}
    
    assert expected_formats.issubset(formats_evaluated)
    
    for r in format_results:
        assert r.is_hash_identical is True
        assert r.transfer_status == "SUCCESS"
        assert r.watermark_recovered is True
        assert r.verification_status == "VERIFIED_DEVICE_IN_LOOP"
        assert "device-in-loop" in r.epistemic_declaration.lower()


def test_golden_experiment_cryptographic_anchors(golden_experiment_run):
    """Verify cryptographic anchors: Merkle roots, evidence package, and offline verification."""
    report, _ = golden_experiment_run
    
    # Lineage Merkle root
    assert len(report.lineage_merkle_root) == 64
    assert report.lineage_merkle_root != "0" * 64
    
    # Custody root hash
    assert len(report.custody_root_hash) == 64
    assert report.custody_root_hash != "0" * 64
    
    # Evidence Package offline verification
    assert report.evidence_package_id.startswith("pkg_CASE-DITL-")
    assert report.evidence_verified_offline is True


def test_golden_experiment_persisted_artifacts(golden_experiment_run):
    """Verify that all 10 standard JSON artifacts are generated on disk."""
    report, tmp_dir = golden_experiment_run
    
    expected_files = [
        "hardware_inventory.json",
        "device_inventory.json",
        "network_inventory.json",
        "device_run_manifest.json",
        "device_experiment_results.json",
        "device_transfer_results.json",
        "device_identity_results.json",
        "device_lineage_results.json",
        "device_failure_results.json",
        "device_validation_summary.json"
    ]
    
    for fname in expected_files:
        fpath = os.path.join(tmp_dir, fname)
        assert os.path.exists(fpath), f"Artifact file '{fname}' not created on disk"
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data is not None
