"""
SIH26237 - Test Decryption Physical Trial Workflow
"""

import pytest
import numpy as np
from core.physical.trial_engine import PhysicalTrialEngine, PhysicalTrialSessionRecord


def test_physical_trial_engine_enrollment_and_preparation():
    """Verify trial engine enrolls standard laboratory cohort."""
    engine = PhysicalTrialEngine(document_id="DOC_TRIAL_001")
    recipients = engine.setup_standard_laboratory_recipients()

    assert len(recipients) == 3
    for r_id in ["rec_alice", "rec_bob", "rec_charlie"]:
        assert r_id in engine._enrolled_recipients


def test_physical_trial_session_decryption_watermarking():
    """Verify trial session executes dynamic volatile decryption watermarking with DLT commit."""
    engine = PhysicalTrialEngine(document_id="DOC_TRIAL_002")
    engine.setup_standard_laboratory_recipients()

    rendered_canvas, session_record = engine.execute_decryption_and_render_artifact(
        recipient_id="rec_alice",
        session_id="SESS_TEST_001"
    )

    assert isinstance(session_record, PhysicalTrialSessionRecord)
    assert session_record.recipient_id == "rec_alice"
    assert session_record.session_id == "SESS_TEST_001"
    assert session_record.document_id == "DOC_TRIAL_002"
    assert len(session_record.watermark_commitment) == 64
    assert len(session_record.codeword_bits) in [64, 128]
    assert session_record.dlt_block_height >= 1
    assert len(session_record.receipt_hash) == 64

    # Verify watermarked image properties
    assert isinstance(rendered_canvas, np.ndarray)
    assert rendered_canvas.shape == (1000, 800, 3)
    assert rendered_canvas.dtype == np.uint8
