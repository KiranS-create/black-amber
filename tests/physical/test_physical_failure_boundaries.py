"""
SIH26237 - Test Physical Failure Boundaries & Safe Fail-Closed Operation
"""

import pytest
from core.physical.failure_boundaries import PhysicalFailureBoundaryAnalyzer, PhysicalOperatingEnvelope, FailureBoundaryTestPoint


def test_physical_failure_boundaries_fail_closed():
    """Verify system fails closed without false attributions under extreme physical stress."""
    envelope = PhysicalFailureBoundaryAnalyzer.evaluate_failure_boundaries()

    assert isinstance(envelope, PhysicalOperatingEnvelope)
    assert envelope.max_safe_angle_deg == 25.0
    assert envelope.max_safe_distance_cm == 50.0
    assert envelope.max_safe_blur_sigma == 1.4
    assert len(envelope.stress_evaluations) > 0

    for point in envelope.stress_evaluations:
        assert isinstance(point, FailureBoundaryTestPoint)
        assert point.false_attribution is False
        assert point.is_safe_rejection is True
        assert point.observed_status in [
            "NO_SIGNAL", "INSUFFICIENT_EVIDENCE", "CONFLICT", "CORRUPTED", "UNMARKED", "PARTIAL", "RECOVERED"
        ]

