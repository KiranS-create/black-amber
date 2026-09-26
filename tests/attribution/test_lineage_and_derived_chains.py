import pytest
from core.attribution.evidence import (
    EvidenceBundle,
    WatermarkObservation,
    TraceabilityObservation,
    LedgerObservation,
    DependencyType,
    TargetBinding,
    AttributionState
)
from core.attribution.fusion import EvidenceFusionEngine

def test_multi_tier_derivation_chain_max_bound():
    """
    Test multi-tier derived chain:
    raw_watermark (score=4.0) -> norm_watermark (score=6.0) -> tardos_score (score=8.5)
    
    Maximum Evidentiary Bound MUST take max(4.0, 6.0, 8.5) = 8.5 across the entire derivation tree.
    It MUST NOT sum them to 18.5!
    """
    engine = EvidenceFusionEngine()
    b = EvidenceBundle(bundle_id="b_tier", target_binding=TargetBinding(document_id="doc1", release_id="rel1"))

    obs1 = WatermarkObservation(
        source_id="raw_wm", primary_candidate="alice", log_likelihood_ratio=4.0,
        dependency_type=DependencyType.INDEPENDENT,
        target_binding=TargetBinding(document_id="doc1", release_id="rel1")
    )
    obs2 = WatermarkObservation(
        source_id="norm_wm", primary_candidate="alice", log_likelihood_ratio=6.0,
        dependency_type=DependencyType.DERIVED, parent_source_id="raw_wm",
        target_binding=TargetBinding(document_id="doc1", release_id="rel1")
    )
    obs3 = TraceabilityObservation(
        source_id="tardos_calc", primary_candidate="alice", log_likelihood_ratio=8.5,
        dependency_type=DependencyType.DERIVED, parent_source_id="norm_wm",
        margin_over_threshold=5.0,
        target_binding=TargetBinding(document_id="doc1", release_id="rel1")
    )

    b.add_observation(obs1)
    b.add_observation(obs2)
    b.add_observation(obs3)

    res = engine.fuse(b)
    # The score must be max(4.0, 6.0, 8.5) * effective_reliability = 8.5 * 0.95 = ~8.075
    assert res.fused_score < 10.0
    assert pytest.approx(res.fused_score, 0.5) == 8.075

def test_ledger_integrity_without_recipient_decryption_does_not_score_attribution():
    """
    Test that a valid tamper-evident audit ledger chain alone (without matching recipient decryption record)
    does not attribute the leak to any candidate.
    """
    engine = EvidenceFusionEngine()
    b = EvidenceBundle(bundle_id="b_ledger_only", target_binding=TargetBinding(document_id="doc1", release_id="rel1"))

    # Pure ledger integrity event without candidate binding
    obs_ledger = LedgerObservation(
        source_id="ledg_chain",
        title="SHA-256 Ledger Chain Intact",
        chain_valid=True,
        matching_events_count=10,
        event_ids=["evt1", "evt2"],
        dependency_type=DependencyType.INDEPENDENT
    )
    b.add_observation(obs_ledger)

    res = engine.fuse(b)
    assert res.state == AttributionState.NO_SIGNAL
    assert res.top_candidate_id is None
    assert res.should_abstain is True
