"""
SIH26237 - Statistical Uncertainty & Binomial Confidence Interval Tests
"""

import pytest
import math
from core.calibration.uncertainty import (
    compute_wilson_score_interval,
    compute_clopper_pearson_interval,
    compute_zero_numerator_rule_of_three,
)


def test_wilson_score_zero_numerator():
    """Verify Wilson score interval for zero false positives (k = 0, n = 200)."""
    ci = compute_wilson_score_interval(0, 200)
    assert ci.point_estimate == 0.0
    assert ci.lower_bound_95 == 0.0
    assert 0.015 < ci.upper_bound_95 < 0.025
    assert ci.sample_size == 200
    assert ci.success_count == 0


def test_clopper_pearson_zero_numerator():
    """Verify Clopper-Pearson exact interval for zero false positives (k = 0, n = 200)."""
    ci = compute_clopper_pearson_interval(0, 200)
    assert ci.point_estimate == 0.0
    assert ci.lower_bound_95 == 0.0
    # Exact: 1 - 0.025^(1/200) ~ 0.018275
    assert round(ci.upper_bound_95, 3) == 0.018


def test_clopper_pearson_full_success():
    """Verify Clopper-Pearson exact interval for 100% recall (k = 100, n = 100)."""
    ci = compute_clopper_pearson_interval(100, 100)
    assert ci.point_estimate == 1.0
    assert ci.upper_bound_95 == 1.0
    assert 0.95 < ci.lower_bound_95 < 1.0


def test_rule_of_three_approximation():
    """Verify Rule of Three upper bound aligns with conservative estimates."""
    bound_200 = compute_zero_numerator_rule_of_three(200)
    assert round(bound_200, 4) == 0.0150
    bound_1000 = compute_zero_numerator_rule_of_three(1000)
    assert round(bound_1000, 4) == 0.0030


def test_empty_sample_edge_case():
    """Verify graceful handling when sample size n = 0."""
    ci_w = compute_wilson_score_interval(0, 0)
    assert ci_w.point_estimate == 0.0
    assert ci_w.upper_bound_95 == 1.0

    ci_cp = compute_clopper_pearson_interval(0, 0)
    assert ci_cp.point_estimate == 0.0
    assert ci_cp.upper_bound_95 == 1.0
