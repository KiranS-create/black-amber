"""
SIH26237 - Test Epistemic Status Integrity & Non-Collapsing
==========================================================
Verifies that all 6 epistemic states are recognized and never collapsed
into a generic or misleading 'physically validated' score.
"""

import pytest
from core.physical.epistemic import (
    EpistemicStatus,
    SubsystemEpistemicClaim,
    ExperimentEpistemicRecord
)


def test_all_epistemic_states_defined():
    """Verify all 6 required epistemic states are defined and distinct."""
    expected_states = [
        "MEASURED_PHYSICAL",
        "DEVICE_IN_LOOP",
        "HYBRID_VALIDATION",
        "SIMULATION_CALIBRATION",
        "NOT_VERIFIED",
        "UNAVAILABLE"
    ]
    for s in expected_states:
        assert hasattr(EpistemicStatus, s)
        assert EpistemicStatus(s).value == s


def test_subsystem_epistemic_segregation():
    """Verify granular subcomponent epistemic claims preserve distinct statuses."""
    rec = ExperimentEpistemicRecord(
        experiment_id="EXP-01",
        overall_status=EpistemicStatus.HYBRID_VALIDATION,
        summary_declaration="Hybrid validation with real phones and simulated optics",
        subcomponents={
            "PHONE_A": SubsystemEpistemicClaim(
                subsystem="PHONE_A",
                status=EpistemicStatus.DEVICE_IN_LOOP,
                required_hardware="Phone",
                detected_hardware="Note10",
                actual_procedure="Session access"
            ),
            "CAMERA": SubsystemEpistemicClaim(
                subsystem="CAMERA",
                status=EpistemicStatus.NOT_VERIFIED,
                required_hardware="Camera",
                detected_hardware="None",
                actual_procedure="Probe"
            ),
            "OPTICAL_MODEL": SubsystemEpistemicClaim(
                subsystem="OPTICAL_MODEL",
                status=EpistemicStatus.SIMULATION_CALIBRATION,
                required_hardware="None",
                detected_hardware="N/A",
                actual_procedure="Gaussian blur",
                provenance_basis="COMPUTATIONAL_MODEL"
            )
        }
    )

    assert rec.subcomponents["PHONE_A"].status == EpistemicStatus.DEVICE_IN_LOOP
    assert rec.subcomponents["CAMERA"].status == EpistemicStatus.NOT_VERIFIED
    assert rec.subcomponents["OPTICAL_MODEL"].status == EpistemicStatus.SIMULATION_CALIBRATION
    assert rec.overall_status == EpistemicStatus.HYBRID_VALIDATION
