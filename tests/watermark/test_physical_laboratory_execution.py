"""
Tests for Workstream Chat 19 — Real Physical Laboratory Execution
=================================================================
Verifies hardware discovery honesty, anti-fabrication enforcement,
lab run manifest binding, physical chain of custody, negative corpus,
separation matrices, error rate calculations, and evidence package integration.
"""

import os
import sys
import json
import pytest
import hashlib
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import cv2

from core.device.hardware_discovery import (
    probe_system_hardware,
    HardwareInventory,
    DiscoveredDevice,
    DeviceModalityStatus
)
from core.security.anti_fabrication import (
    AntiFabricationGuard,
    ValidationClassification,
    FabricationViolationError
)
from core.lineage.physical_custody import (
    PhysicalCustodyAction,
    PhysicalCustodyEvent,
    PhysicalCustodyChain
)
from core.watermark.physical_lab import (
    PhysicalLabOrchestrator,
    PhysicalLabManifest,
    ControlledSourceDocument,
    PhysicalTrialResult,
    PhysicalNegativeResult,
    wilson_score_interval
)
from core.physical.evidence_bridge import PhysicalEvidenceBridge
from core.physical.trial_engine import PhysicalTrialSessionRecord
from core.physical.experiments import PhysicalTrialResult as CorePhysicalTrialResult
from core.physical.custody import PhysicalChainOfCustodyTracker


def test_hardware_discovery_honesty():
    """Hardware discovery probe must be non-fabricating and accurate."""
    inv = probe_system_hardware()
    assert isinstance(inv, HardwareInventory)
    assert inv.inventory_id.startswith("HINV-")
    assert inv.host_environment in ["AIRGAP_CONTAINER_HOST", "WORKSTATION_WIN32", "WORKSTATION_LINUX", "WORKSTATION_DARWIN"]
    assert inv.os_name != ""
    assert isinstance(inv.cameras, list)
    assert isinstance(inv.printers, list)
    assert isinstance(inv.scanners, list)
    assert isinstance(inv.displays, list)
    
    # Verify no software virtual printers are labeled as physical
    for pr in inv.printers:
        assert pr.is_physical is True
        for virt in ["onenote", "xps", "pdf", "fax", "software"]:
            assert virt not in pr.model.lower()
            assert virt not in pr.driver.lower()


def test_anti_fabrication_guard_enforcement():
    """Attempting to claim MEASURED_PHYSICAL without hardware must raise FabricationViolationError."""
    # 1. Illegal claim when hardware is unavailable
    with pytest.raises(FabricationViolationError):
        AntiFabricationGuard.enforce_classification_integrity(
            classification=ValidationClassification.MEASURED_PHYSICAL,
            is_hardware_available=False,
            device_id="cam_mock_01",
            raw_capture_hash="a" * 64
        )

    # 2. Illegal claim when artifact is synthetic
    with pytest.raises(FabricationViolationError):
        AntiFabricationGuard.enforce_classification_integrity(
            classification=ValidationClassification.MEASURED_PHYSICAL,
            is_hardware_available=True,
            device_id="cam_brio_4k",
            raw_capture_hash="b" * 64,
            is_synthetic=True
        )

    # 3. Illegal claim without device ID
    with pytest.raises(FabricationViolationError):
        AntiFabricationGuard.enforce_classification_integrity(
            classification=ValidationClassification.MEASURED_PHYSICAL,
            is_hardware_available=True,
            device_id="UNKNOWN",
            raw_capture_hash="c" * 64
        )

    # 4. Valid simulation claim passes
    AntiFabricationGuard.enforce_classification_integrity(
        classification=ValidationClassification.SIMULATION,
        is_hardware_available=False,
        is_synthetic=True,
        transformation_type="GAUSSIAN_BLUR"
    )


def test_lab_run_manifest_determinism_and_hashing():
    """Run manifest must have unique PHYSICAL_RUN_ID, valid source doc, and accurate SHA-256 hash."""
    orchestrator = PhysicalLabOrchestrator()
    manifest = orchestrator.manifest
    
    assert manifest.physical_run_id.startswith("PLAB-")
    assert manifest.aegistrace_version == "2.4.0-hardened"
    assert manifest.crypto_version == "FIPS203-MLKEM768/FIPS204-MLDSA65"
    assert manifest.manifest_hash != ""
    assert manifest.manifest_hash == manifest.compute_hash()
    assert orchestrator.source_doc.document_id == "DOC_PHYSICAL_STANDARD_V1"
    assert len(orchestrator.source_doc.sha256) == 64


def test_physical_chain_of_custody_hashing_and_sealing():
    """Physical custody chain must enforce cryptographic hash chaining and terminal sealing."""
    art_hash = "d" * 64
    chain = PhysicalCustodyChain(
        chain_id="PCHAIN-TEST-001",
        run_id="PLAB-20260927-TEST",
        initial_artifact_hash=art_hash
    )

    # Append PRINTED -> CAPTURED -> IMPORTED -> HASHED -> ANALYZED -> SEALED
    e1 = chain.append_event(PhysicalCustodyAction.PRINTED, art_hash, device_id="prn_hp_laserjet")
    assert e1.previous_custody_hash == "GENESIS"
    assert e1.custody_hash != ""

    e2 = chain.append_event(PhysicalCustodyAction.CAPTURED, art_hash, device_id="cam_brio_4k")
    assert e2.previous_custody_hash == e1.custody_hash

    e3 = chain.append_event(PhysicalCustodyAction.IMPORTED, art_hash)
    assert e3.previous_custody_hash == e2.custody_hash

    e4 = chain.append_event(PhysicalCustodyAction.HASHED, art_hash)
    assert e4.previous_custody_hash == e3.custody_hash

    e5 = chain.append_event(PhysicalCustodyAction.ANALYZED, art_hash)
    assert e5.previous_custody_hash == e4.custody_hash

    e6 = chain.append_event(PhysicalCustodyAction.SEALED, art_hash)
    assert e6.previous_custody_hash == e5.custody_hash
    assert chain.is_sealed is True
    assert chain.final_seal_hash == e6.custody_hash

    # Verify chain integrity
    valid, errors = chain.verify_integrity()
    assert valid is True
    assert len(errors) == 0

    # Cannot append to sealed chain
    with pytest.raises(ValueError, match="Cannot append event to sealed custody chain"):
        chain.append_event(PhysicalCustodyAction.ANALYZED, art_hash)

    # Tampering with intermediate event breaks integrity
    chain.events[1].device_id = "tampered_device"
    valid_tampered, errors_tampered = chain.verify_integrity()
    assert valid_tampered is False
    assert len(errors_tampered) > 0


def test_real_decryption_time_watermark_session_generation(tmp_path):
    """Generates real ML-KEM-768/ML-DSA-65 decryption sessions for Alice, Bob, Charlie."""
    orchestrator = PhysicalLabOrchestrator(base_artifacts_dir=tmp_path)
    pkgs = orchestrator.execute_real_decryption_pipeline()
    
    assert len(pkgs) == 3
    for rec_id in ["alice", "bob", "charlie"]:
        assert rec_id in pkgs
        pkg = pkgs[rec_id]
        assert pkg.recipient_id == rec_id
        assert pkg.session_id == f"sess_{rec_id}_01"
        assert pkg.watermark_event_id.startswith("dyn_wm_")
        assert pkg.decryption_receipt_id.startswith("evt_dec_")
        assert len(pkg.raw_render_hash) == 64
        assert os.path.exists(pkg.raw_image_path)
        
        # Verify custody chain initialized
        chain = orchestrator.custody_chains[rec_id]
        assert len(chain.events) >= 1
        assert chain.events[0].artifact_hash == pkg.raw_render_hash


def test_physical_negative_corpus_fail_closed_guarantees(tmp_path):
    """Negative corpus samples must abstain fail-closed with zero false positives."""
    orchestrator = PhysicalLabOrchestrator(base_artifacts_dir=tmp_path)
    orchestrator.execute_real_decryption_pipeline()
    negatives = orchestrator.run_physical_negative_corpus()
    
    assert len(negatives) >= 3
    for neg in negatives:
        assert neg.is_false_positive is False
        assert neg.abstention_enforced is True
        assert neg.observed_outcome in ["NO_SIGNAL", "INVALID", "CONFLICT", "INSUFFICIENT_EVIDENCE"]


def test_separation_matrix_and_visual_equivalence(tmp_path):
    """Pairwise distances and visual equivalence metrics must meet specifications."""
    orchestrator = PhysicalLabOrchestrator(base_artifacts_dir=tmp_path)
    orchestrator.execute_real_decryption_pipeline()
    
    sep = orchestrator.compute_separation_matrix()
    assert len(sep.recipients) == 3
    assert sep.collision_count == 0
    assert sep.wrong_recipient_attributions == 0
    for key, dist in sep.pairwise_hamming_distances.items():
        assert dist > 0

    veq = orchestrator.compute_visual_equivalence()
    assert veq.sample_count == 3
    assert veq.ssim_median >= 0.95
    assert veq.psnr_median_db >= 35.0
    assert veq.ocr_text_equality == 1.0


def test_wilson_confidence_intervals():
    """Wilson score confidence intervals must compute accurately."""
    # 0 false positives out of 100 trials
    low, high = wilson_score_interval(0, 100)
    assert low == 0.0
    assert 0.0 < high <= 0.05

    # 100 true positives out of 100 trials
    low_tp, high_tp = wilson_score_interval(100, 100)
    assert 0.95 <= low_tp < 1.0
    assert high_tp == pytest.approx(1.0, abs=1e-6)


def test_offline_evidence_package_physical_integration(tmp_path):
    """Physical trial record and custody chain can be packaged into an offline verifiable evidence package."""
    from core.physical.trial_engine import PhysicalTrialEngine
    from core.physical.experiments import PhysicalExperimentRunner
    engine = PhysicalTrialEngine()
    engine.setup_standard_laboratory_recipients()
    canvas, session_rec = engine.execute_decryption_and_render_artifact("rec_alice")
    
    runner = PhysicalExperimentRunner(trial_engine=engine)
    trials = runner.run_screen_photo_experiments("rec_alice")
    trial_res = trials[0]

    custody = PhysicalChainOfCustodyTracker(run_id="RUN_PHYS_TEST_01", base_dir=str(tmp_path))
    custody.record_transition("PRINTED", b"mock_print_bytes", "print_alice.raw", "prn_laserjet_600", "raw")
    custody.record_transition("CAPTURED", b"mock_capture_bytes", "capture_alice.png", "cam_brio_4k", "raw")
    custody.record_transition("IMPORTED", b"mock_capture_bytes", "capture_alice_imported.png", "HOST_SYSTEM", "processed")
    custody.record_transition("SEALED", b"mock_capture_bytes", "capture_alice_sealed.png", "HOST_SYSTEM", "results")

    pkg, ver_res = PhysicalEvidenceBridge.assemble_physical_evidence_package(
        case_id="CASE_PHYSICAL_LAB_001",
        trial_record=session_rec,
        trial_result=trial_res,
        custody_tracker=custody
    )

    from core.evidence_package.models import VerificationStatus
    assert pkg.manifest.case_id == "CASE_PHYSICAL_LAB_001"
    assert len(pkg.objects) >= 3
    assert ver_res.overall_status == VerificationStatus.VERIFIED
    assert ver_res.manifest_signature_valid is True
    assert ver_res.merkle_root_valid is True
    assert ver_res.recipient_signature_valid is True
    assert ver_res.custody_chain_valid is True
