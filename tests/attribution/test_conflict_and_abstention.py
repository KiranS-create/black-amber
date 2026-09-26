import pytest
from core.attribution.evidence import (
    AttributionState,
    EvidenceBundle,
    EvidenceObservation,
    WatermarkObservation,
    ProvenanceObservation,
    EvidenceFamily,
    DependencyType
)
from core.attribution.policy import DecisionPolicy
from core.attribution.fusion import EvidenceFusionEngine

def test_empty_bundle_returns_no_signal():
    engine = EvidenceFusionEngine()
    bundle = EvidenceBundle(bundle_id="b_empty")
    result = engine.fuse(bundle)

    assert result.state == AttributionState.NO_SIGNAL
    assert result.should_abstain is True
    assert result.top_candidate_id is None

def test_subthreshold_score_returns_insufficient_evidence():
    policy = DecisionPolicy(min_attribution_score=8.0)
    engine = EvidenceFusionEngine(policy=policy)
    bundle = EvidenceBundle(bundle_id="b_weak")

    obs = EvidenceObservation(
        source_id="weak_obs",
        family=EvidenceFamily.WATERMARK_PAYLOAD,
        log_likelihood_ratio=3.5,  # 3.5 < 8.0
        primary_candidate="alice"
    )
    bundle.add_observation(obs)

    result = engine.fuse(bundle)
    assert result.state == AttributionState.INSUFFICIENT_EVIDENCE
    assert result.should_abstain is True
    assert result.top_candidate_id == "alice"

def test_narrow_candidate_margin_returns_insufficient_evidence():
    policy = DecisionPolicy(min_attribution_score=6.0, min_separation_margin=3.0)
    engine = EvidenceFusionEngine(policy=policy)
    bundle = EvidenceBundle(bundle_id="b_close")

    # Alice has 9.0, Bob has 8.0 -> Delta = 1.0 < 3.0
    obs1 = EvidenceObservation(
        source_id="obs_alice",
        family=EvidenceFamily.TARDOS_FINGERPRINT,
        candidate_scores={"alice": 9.0, "bob": 8.0}
    )
    bundle.add_observation(obs1)

    result = engine.fuse(bundle)
    assert result.state in (AttributionState.INSUFFICIENT_EVIDENCE, AttributionState.CONFLICT)
    assert result.should_abstain is True
    assert result.separation_margin < policy.min_separation_margin

def test_multi_source_conflict_returns_conflict():
    """
    Two independent, strong channels pointing to different candidates:
    Channel 1 says Alice (score=10.0), Channel 2 says Bob (score=9.5)
    """
    policy = DecisionPolicy(
        min_attribution_score=6.0,
        min_separation_margin=2.5,
        conflict_runnerup_threshold=5.0
    )
    engine = EvidenceFusionEngine(policy=policy)
    bundle = EvidenceBundle(bundle_id="b_conflict")

    obs1 = EvidenceObservation(
        source_id="obs_channel1",
        family=EvidenceFamily.WATERMARK_PAYLOAD,
        log_likelihood_ratio=10.0,
        primary_candidate="alice"
    )
    obs2 = EvidenceObservation(
        source_id="obs_channel2",
        family=EvidenceFamily.DOCUMENT_STRUCTURE,
        log_likelihood_ratio=9.5,
        primary_candidate="bob"
    )
    bundle.add_observation(obs1)
    bundle.add_observation(obs2)

    result = engine.fuse(bundle)
    assert result.state == AttributionState.CONFLICT
    assert result.should_abstain is True
    assert "conflict" in result.summary.lower()
