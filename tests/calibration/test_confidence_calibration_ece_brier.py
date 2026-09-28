"""
SIH26237 - Confidence Calibration & Reliability Tests (ECE, MCE, Brier Score)
"""

import pytest
import numpy as np
from core.calibration.metrics import ForensicMetricsCalculator


def test_perfectly_calibrated_synthetic_distribution():
    """Verify ECE and Brier score on perfectly calibrated predictions."""
    probs = [0.1] * 90 + [0.9] * 10
    labels = [0] * 81 + [1] * 9 + [0] * 1 + [1] * 9

    calib = ForensicMetricsCalculator.compute_calibration_metrics(probs, labels, num_bins=10)
    assert calib.expected_calibration_error < 0.05
    assert calib.brier_score < 0.15
    assert len(calib.reliability_bins) == 10


def test_overconfident_uncalibrated_distribution():
    """Verify ECE identifies overconfident uncalibrated predictions."""
    # Predicts 0.99 for all samples, but true accuracy is only 50%
    probs = [0.99] * 100
    labels = [1] * 50 + [0] * 50

    calib = ForensicMetricsCalculator.compute_calibration_metrics(probs, labels, num_bins=10)
    # Expected Calibration Error should be ~ |0.99 - 0.50| = 0.49
    assert calib.expected_calibration_error >= 0.45
    assert calib.maximum_calibration_error >= 0.45
    assert calib.brier_score >= 0.20


def test_empty_calibration_inputs():
    """Verify graceful handling on empty input arrays."""
    calib = ForensicMetricsCalculator.compute_calibration_metrics([], [])
    assert calib.expected_calibration_error == 0.0
    assert calib.brier_score == 0.0
