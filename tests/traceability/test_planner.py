import pytest
import math
from pydantic import ValidationError
from core.traceability.planner import (
    TardosCapacityPlanner,
    CapacityPlanRequest,
    PlannerStatus,
)

def test_planner_feasible_default():
    """Verify standard feasible parameter request."""
    req = CapacityPlanRequest(
        recipient_count=10,
        coalition_size=2,
        false_accusation_epsilon=1e-4,
        kappa_factor=20.0
    )
    result = TardosCapacityPlanner.plan(req)

    assert result.status == PlannerStatus.FEASIBLE
    assert result.is_feasible is True
    assert result.required_code_length > 0
    assert result.accusation_threshold > 0.0
    assert result.cutoff_parameter_t == pytest.approx(1.0 / (300.0 * 2))
    assert len(result.assumptions) >= 4

    # Mathematical verification: m >= ceil(20 * 4 * ln(10 / 1e-4))
    expected_log = math.log(10.0 / 1e-4)
    expected_m = int(math.ceil(20.0 * 4.0 * expected_log))
    assert result.required_code_length == expected_m

    expected_z = math.sqrt(2.0 * expected_m * expected_log)
    assert result.accusation_threshold == pytest.approx(expected_z)


def test_planner_capacity_insufficient():
    """Verify that insufficient carrier budget returns fail-closed CAPACITY_INSUFFICIENT."""
    # Budget of only 200 bits when required is ~900+ bits
    req = CapacityPlanRequest(
        recipient_count=10,
        coalition_size=2,
        false_accusation_epsilon=1e-4,
        available_carrier_budget=200,
        kappa_factor=20.0
    )
    result = TardosCapacityPlanner.plan(req)

    assert result.status == PlannerStatus.CAPACITY_INSUFFICIENT
    assert result.is_feasible is False
    assert result.available_code_length == 200
    assert result.required_code_length > 200
    assert result.metadata["deficit_symbols"] == result.required_code_length - 200
    assert "Carrier budget (200 symbols) is insufficient" in (result.reason or "")
    assert len(result.recommendations) > 0


def test_planner_carrier_budget_sufficient():
    """Verify that carrier budget greater than required passes as FEASIBLE."""
    req = CapacityPlanRequest(
        recipient_count=5,
        coalition_size=2,
        false_accusation_epsilon=1e-3,
        available_carrier_budget=2000,
        kappa_factor=20.0
    )
    result = TardosCapacityPlanner.plan(req)

    assert result.status == PlannerStatus.FEASIBLE
    assert result.is_feasible is True
    assert result.available_code_length == 2000
    assert result.metadata["margin_symbols"] == 2000 - result.required_code_length


def test_planner_quadratic_scaling_with_coalition_size():
    """Verify that code length scales quadratically with coalition size c."""
    req_c2 = CapacityPlanRequest(recipient_count=20, coalition_size=2, kappa_factor=20.0)
    req_c4 = CapacityPlanRequest(recipient_count=20, coalition_size=4, kappa_factor=20.0)

    res_c2 = TardosCapacityPlanner.plan(req_c2)
    res_c4 = TardosCapacityPlanner.plan(req_c4)

    # c doubled (2 -> 4) => c^2 quadrupled (4 -> 16)
    ratio = res_c4.required_code_length / res_c2.required_code_length
    assert ratio == pytest.approx(4.0, rel=0.05)


def test_planner_logarithmic_scaling_with_population():
    """Verify that code length scales logarithmically with population N."""
    req_n10 = CapacityPlanRequest(recipient_count=10, coalition_size=2, false_accusation_epsilon=1e-4)
    req_n100 = CapacityPlanRequest(recipient_count=100, coalition_size=2, false_accusation_epsilon=1e-4)

    res_n10 = TardosCapacityPlanner.plan(req_n10)
    res_n100 = TardosCapacityPlanner.plan(req_n100)

    ratio = res_n100.required_code_length / res_n10.required_code_length
    # ln(100/1e-4) / ln(10/1e-4) = ln(10^6) / ln(10^5) = 6/5 = 1.2
    assert ratio == pytest.approx(1.2, rel=0.05)


def test_planner_invalid_pydantic_bounds():
    """Verify that non-positive parameters are rejected at schema level."""
    with pytest.raises(ValidationError):
        CapacityPlanRequest(recipient_count=0, coalition_size=2)

    with pytest.raises(ValidationError):
        CapacityPlanRequest(recipient_count=10, coalition_size=0)

    with pytest.raises(ValidationError):
        CapacityPlanRequest(recipient_count=10, coalition_size=2, false_accusation_epsilon=1.5)
