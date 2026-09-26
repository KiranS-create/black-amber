import pytest
from core.traceability.tardos import SymmetricTardosEngine, AccusationStatus, TardosAccusationResult
from core.traceability.planner import TardosCapacityPlanner, CapacityPlanRequest, PlannerStatus
from core.watermark.base import WatermarkObservation, WatermarkStatus
from core.watermark.adapter import WatermarkTraceabilityAdapter

def test_tardos_invalid_coalition_and_length_rejection():
    """Ensure Tardos engine strictly validates parameter bounds (c > 0, m > 0, epsilon in (0, 1))."""
    # Negative or zero coalition size
    with pytest.raises(ValueError, match="Coalition size c must be positive"):
        SymmetricTardosEngine.compute_cutoff(0)

    with pytest.raises(ValueError, match="Coalition size c must be positive"):
        SymmetricTardosEngine.generate_biases(m=100, c=-1)

    # Negative or zero code length
    with pytest.raises(ValueError, match="Code length m must be positive"):
        SymmetricTardosEngine.generate_biases(m=0, c=3)

    # Invalid false alarm epsilon
    with pytest.raises(ValueError, match="Invalid parameters for threshold computation"):
        SymmetricTardosEngine.compute_threshold(m=100, recipient_count=10, epsilon_1=0.0)

    with pytest.raises(ValueError, match="Invalid parameters for threshold computation"):
        SymmetricTardosEngine.compute_threshold(m=100, recipient_count=10, epsilon_1=1.5)

def test_tardos_malformed_observed_symbols_erasure_handling():
    """
    Ensure symbols other than 0 and 1 (such as -1 for erasure, or unexpected ints)
    are safely mapped to 0.0 contribution and do not cause division by zero or NaN.
    """
    p = 0.5
    # Standard symbols
    assert SymmetricTardosEngine.score_symbol(y_j=1, x_ij=1, p_j=p) > 0.0
    assert SymmetricTardosEngine.score_symbol(y_j=1, x_ij=0, p_j=p) < 0.0

    # Erasure symbol (-1)
    assert SymmetricTardosEngine.score_symbol(y_j=-1, x_ij=1, p_j=p) == 0.0

    # Unrecognized symbol (999 or -99)
    assert SymmetricTardosEngine.score_symbol(y_j=999, x_ij=1, p_j=p) == 0.0

def test_tardos_capacity_planner_under_budget_rejection():
    """Ensure capacity planner rejects insufficient carrier capacity."""
    req = CapacityPlanRequest(
        recipient_count=100,
        coalition_size=5,
        false_accusation_epsilon=1e-4,
        available_carrier_budget=10  # Grossly insufficient capacity
    )
    plan = TardosCapacityPlanner.plan(req)
    assert plan.status == PlannerStatus.CAPACITY_INSUFFICIENT
    assert plan.required_code_length > 10

def test_watermark_adapter_fail_closed_on_no_signal():
    """Ensure WatermarkTraceabilityAdapter abstains when watermark observation has NO_SIGNAL."""
    adapter = WatermarkTraceabilityAdapter()
    obs = WatermarkObservation(
        status=WatermarkStatus.NO_SIGNAL,
        is_valid=False,
        confidence=0.0,
        synchronization_success=False
    )
    result = adapter.evaluate_observation(
        observation=obs,
        all_recipient_ids=["alice", "bob"],
        document_id="doc1",
        release_id="rel1"
    )
    assert result.watermark_status == WatermarkStatus.NO_SIGNAL
    assert result.attribution_status == AccusationStatus.NO_SIGNAL
    assert len(result.accused_recipients) == 0
    assert result.fused_confidence == 0.0

def test_watermark_adapter_fail_closed_on_invalid_marker():
    """Ensure WatermarkTraceabilityAdapter abstains when watermark is INVALID (e.g. binding mismatch)."""
    adapter = WatermarkTraceabilityAdapter()
    obs = WatermarkObservation(
        status=WatermarkStatus.INVALID,
        is_valid=False,
        confidence=0.0,
        synchronization_success=True
    )
    result = adapter.evaluate_observation(
        observation=obs,
        all_recipient_ids=["alice", "bob"],
        document_id="doc1",
        release_id="rel1"
    )
    assert result.watermark_status == WatermarkStatus.INVALID
    assert result.attribution_status == AccusationStatus.INSUFFICIENT_EVIDENCE
    assert len(result.accused_recipients) == 0
    assert result.fused_confidence == 0.0
