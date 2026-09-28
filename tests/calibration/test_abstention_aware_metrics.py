"""
SIH26237 - Abstention-Aware Metrics & Risk-Coverage Curve Tests
"""

import pytest
from core.calibration.metrics import ForensicMetricsCalculator
from core.calibration.models import ConfusionMatrix


def test_confusion_matrix_and_error_rates():
    """Verify standard classification metrics calculation."""
    cm = ConfusionMatrix(
        tp=95,
        tn=190,
        fp=0,
        fn=5,
        abstentions_valid=5,
        abstentions_negative=190,
        total_evaluated=290
    )
    rates = ForensicMetricsCalculator.compute_error_rates(cm)

    assert rates.precision == 1.0
    assert rates.recall == 0.95
    assert rates.specificity == 1.0
    assert rates.fpr_point_estimate == 0.0
    assert rates.fpr_empirical_str == "0 / 190"
    assert rates.fnr_point_estimate == 0.05
    assert rates.fnr_empirical_str == "5 / 100"


def test_abstention_metrics_coverage_and_selective_accuracy():
    """Verify selective accuracy and coverage calculations."""
    samples = [
        # 4 True Positives
        {"predicted_state": "ATTRIBUTED", "is_attributable": True, "true_recipient_id": "r1", "predicted_recipient_id": "r1", "fused_score": 8.0},
        {"predicted_state": "ATTRIBUTED", "is_attributable": True, "true_recipient_id": "r2", "predicted_recipient_id": "r2", "fused_score": 7.5},
        {"predicted_state": "ATTRIBUTED", "is_attributable": True, "true_recipient_id": "r3", "predicted_recipient_id": "r3", "fused_score": 9.0},
        {"predicted_state": "ATTRIBUTED", "is_attributable": True, "true_recipient_id": "r4", "predicted_recipient_id": "r4", "fused_score": 6.5},
        # 4 Correct Abstentions (Negative clean)
        {"predicted_state": "NO_SIGNAL", "is_attributable": False, "true_recipient_id": None, "predicted_recipient_id": None, "fused_score": 0.0},
        {"predicted_state": "NO_SIGNAL", "is_attributable": False, "true_recipient_id": None, "predicted_recipient_id": None, "fused_score": 0.0},
        {"predicted_state": "INSUFFICIENT_EVIDENCE", "is_attributable": False, "true_recipient_id": None, "predicted_recipient_id": None, "fused_score": 1.5},
        {"predicted_state": "CONFLICT", "is_attributable": False, "true_recipient_id": None, "predicted_recipient_id": None, "fused_score": 4.0},
        # 2 Safe False Negatives (Positive case abstained due to noise)
        {"predicted_state": "INSUFFICIENT_EVIDENCE", "is_attributable": True, "true_recipient_id": "r5", "predicted_recipient_id": None, "fused_score": 2.0},
        {"predicted_state": "NO_SIGNAL", "is_attributable": True, "true_recipient_id": "r6", "predicted_recipient_id": None, "fused_score": 0.0},
    ]

    metrics = ForensicMetricsCalculator.compute_abstention_metrics(samples)

    assert metrics.total_samples == 10
    assert metrics.attributed_count == 4
    assert metrics.abstained_count == 6
    assert metrics.coverage == 0.40
    assert metrics.abstention_rate == 0.60
    assert metrics.selective_accuracy == 1.00
    assert metrics.selective_risk == 0.00
    assert len(metrics.risk_coverage_curve) > 0
