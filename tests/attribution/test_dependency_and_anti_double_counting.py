import pytest
from core.attribution.evidence import (
    EvidenceBundle,
    EvidenceObservation,
    WatermarkObservation,
    TraceabilityObservation,
    DependencyType,
    EvidenceFamily,
    TargetBinding,
)
from core.attribution.dependency import EvidenceDependencyGraph

def test_independent_additive_fusion():
    """Verify that independent channels add their log-likelihood ratios."""
    graph = EvidenceDependencyGraph()
    bundle = EvidenceBundle(bundle_id="b_indep")

    # Two completely independent channels supporting Alice
    obs1 = EvidenceObservation(
        source_id="indep_1",
        family=EvidenceFamily.AUDIT_LEDGER,
        dependency_type=DependencyType.INDEPENDENT,
        title="Ledger Evidence",
        log_likelihood_ratio=4.0,
        primary_candidate="alice",
        effective_reliability=1.0
    )
    obs2 = EvidenceObservation(
        source_id="indep_2",
        family=EvidenceFamily.DOCUMENT_STRUCTURE,
        dependency_type=DependencyType.INDEPENDENT,
        title="Structural Evidence",
        log_likelihood_ratio=3.0,
        primary_candidate="alice",
        effective_reliability=1.0
    )
    bundle.add_observation(obs1)
    bundle.add_observation(obs2)

    scores = graph.compute_fused_candidate_scores(bundle)
    # Expected: 4.0 + 3.0 = 7.0
    assert pytest.approx(scores["alice"], 0.01) == 7.0

def test_derived_maximum_evidentiary_bound():
    """
    CRITICAL: Verify that a derived score (e.g. Tardos statistic computed from raw watermark)
    does NOT double-count with its parent raw extraction, but rather uses the Maximum Evidentiary Bound.
    """
    graph = EvidenceDependencyGraph()
    bundle = EvidenceBundle(bundle_id="b_derived")

    parent_wm = WatermarkObservation(
        source_id="raw_wm_stream",
        title="Raw Watermark Bitstream",
        dependency_type=DependencyType.INDEPENDENT,
        log_likelihood_ratio=5.0,
        primary_candidate="alice",
        effective_reliability=1.0
    )
    derived_tardos = TraceabilityObservation(
        source_id="tardos_calc",
        title="Tardos Derived Statistic",
        dependency_type=DependencyType.DERIVED,
        parent_source_id="raw_wm_stream",
        log_likelihood_ratio=8.0,
        primary_candidate="alice",
        effective_reliability=1.0
    )
    bundle.add_observation(parent_wm)
    bundle.add_observation(derived_tardos)

    scores = graph.compute_fused_candidate_scores(bundle)
    # With double-counting, score would be 5.0 + 8.0 = 13.0
    # With Maximum Evidentiary Bound, score MUST be max(5.0, 8.0) = 8.0
    assert pytest.approx(scores["alice"], 0.01) == 8.0

def test_partially_dependent_correlation_discounting():
    """Verify that partially dependent channels apply correlation discount gamma."""
    discount = 0.60
    graph = EvidenceDependencyGraph(correlation_discount=discount)
    bundle = EvidenceBundle(bundle_id="b_partial")

    obs_part = EvidenceObservation(
        source_id="partial_1",
        family=EvidenceFamily.WATERMARK_PAYLOAD,
        dependency_type=DependencyType.PARTIALLY_DEPENDENT,
        title="Dual Layer Watermark Channel",
        log_likelihood_ratio=5.0,
        primary_candidate="bob",
        effective_reliability=1.0
    )
    bundle.add_observation(obs_part)

    scores = graph.compute_fused_candidate_scores(bundle)
    # Expected: 5.0 * 0.60 = 3.0
    assert pytest.approx(scores["bob"], 0.01) == 3.0
