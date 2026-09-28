"""
SIH26237 - Test Physical Evidence Package Creation and Offline Verifier
"""

import pytest
import numpy as np
from core.physical.trial_engine import PhysicalTrialEngine
from core.physical.experiments import PhysicalTrialResult
from core.physical.custody import PhysicalChainOfCustodyTracker
from core.physical.evidence_bridge import PhysicalEvidenceBridge
from core.evidence_package.models import DecisionState, VerificationStatus


def test_physical_evidence_package_creation_and_offline_verification(tmp_path):
    """Verify physical evidence package binds physical metadata, ML-DSA-65 signs, and verifies offline."""
    engine = PhysicalTrialEngine(document_id="DOC_BRIDGE_001")
    engine.setup_standard_laboratory_recipients()
    watermarked_img, session_record = engine.execute_decryption_and_render_artifact("rec_alice")

    tracker = PhysicalChainOfCustodyTracker(
        run_id="run_test_bridge_001",
        base_dir=str(tmp_path / "bridge_runs")
    )
    ev_cap = tracker.record_transition(
        action="CAPTURED",
        artifact_bytes=watermarked_img.tobytes(),
        filename="test_cap.raw",
        device_id="DEV_01",
        notes="Capture"
    )
    tracker.record_transition(
        action="ANALYZED",
        artifact_bytes=watermarked_img.tobytes(),
        filename="test_cap.raw",
        device_id="DEV_01",
        notes="Analysis"
    )
    tracker.record_transition(
        action="SEALED",
        artifact_bytes=b"SEAL",
        filename="seal.sig",
        device_id="DEV_01",
        notes="Sealed"
    )

    trial_res = PhysicalTrialResult(
        trial_id="TR_BRIDGE_001",
        experiment_type="SCREEN_CAMERA",
        scenario_name="Screen Photo Normal Angle",
        recipient_id="rec_alice",
        document_id=session_record.document_id,
        release_id=session_record.release_id,
        session_id=session_record.session_id,
        source_artifact_hash=session_record.rendered_artifact_hash,
        capture_artifact_hash=ev_cap.artifact_hash,
        device_modality="CAMERA",
        device_name="TestCam 12MP",
        resolution="4000x3000",
        distance_cm=35.0,
        angle_deg=0.0,
        lighting_pct=0.0,
        bit_error_rate=0.0,
        raw_bit_errors=0,
        ecc_recovered=True,
        commitment_match=True,
        decision_state="RECOVERED_CORRECT",
        is_correct_attribution=True,
        epistemic_classification="NOT_VERIFIED"
    )

    pkg, verif = PhysicalEvidenceBridge.assemble_physical_evidence_package(
        case_id="CASE_BRIDGE_001",
        trial_record=session_record,
        trial_result=trial_res,
        custody_tracker=tracker,
        is_downstream_gap=False
    )

    assert pkg is not None
    assert pkg.manifest.case_id == "CASE_BRIDGE_001"
    assert verif.overall_status == VerificationStatus.VERIFIED
    assert len(verif.errors) == 0


def test_physical_evidence_package_downstream_gap(tmp_path):
    """Verify physical evidence package honesty under downstream unmonitored leak transitions."""
    engine = PhysicalTrialEngine(document_id="DOC_BRIDGE_002")
    engine.setup_standard_laboratory_recipients()
    watermarked_img, session_record = engine.execute_decryption_and_render_artifact("rec_bob")

    tracker = PhysicalChainOfCustodyTracker(
        run_id="run_test_bridge_002",
        base_dir=str(tmp_path / "bridge_runs_2")
    )
    ev_cap = tracker.record_transition(
        action="CAPTURED",
        artifact_bytes=watermarked_img.tobytes(),
        filename="test_cap_gap.raw",
        device_id="DEV_01",
        notes="Capture"
    )
    tracker.record_transition(
        action="SEALED",
        artifact_bytes=b"SEAL",
        filename="seal.sig",
        device_id="DEV_01",
        notes="Sealed"
    )

    trial_res = PhysicalTrialResult(
        trial_id="TR_BRIDGE_002",
        experiment_type="SCREEN_CAMERA",
        scenario_name="Screen Photo Downstream Gap",
        recipient_id="rec_bob",
        document_id=session_record.document_id,
        release_id=session_record.release_id,
        session_id=session_record.session_id,
        source_artifact_hash=session_record.rendered_artifact_hash,
        capture_artifact_hash=ev_cap.artifact_hash,
        device_modality="CAMERA",
        device_name="TestCam 12MP",
        resolution="4000x3000",
        distance_cm=35.0,
        angle_deg=0.0,
        lighting_pct=0.0,
        bit_error_rate=0.0,
        raw_bit_errors=0,
        ecc_recovered=True,
        commitment_match=True,
        decision_state="RECOVERED_CORRECT",
        is_correct_attribution=True,
        epistemic_classification="NOT_VERIFIED"
    )

    pkg, verif = PhysicalEvidenceBridge.assemble_physical_evidence_package(
        case_id="CASE_BRIDGE_002",
        trial_record=session_record,
        trial_result=trial_res,
        custody_tracker=tracker,
        is_downstream_gap=True
    )

    assert verif.overall_status == VerificationStatus.VERIFIED
    dec_obj = pkg.object_map[pkg.manifest.final_decision_reference]
    assert dec_obj.decision_state == DecisionState.INSUFFICIENT_EVIDENCE
    assert dec_obj.last_known_holder_id == "rec_bob"
    assert dec_obj.attributed_principal_id is None
