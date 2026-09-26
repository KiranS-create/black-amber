import pytest
from core.attribution.evidence import (
    EvidenceBundle,
    WatermarkObservation,
    DependencyType,
    TargetBinding,
    AttributionState
)
from core.attribution.fusion import EvidenceFusionEngine
from core.attribution.dependency import EvidenceDependencyGraph

def test_identical_observation_repeated_100_times():
    """
    Adversarial Attack: An attacker injects 100 copies of the exact same watermark observation
    hoping to artificially inflate log-likelihood score from 5.0 to 500.0.
    """
    engine = EvidenceFusionEngine()
    bundle = EvidenceBundle(bundle_id="b_repeat")

    base_obs = WatermarkObservation(
        source_id="wm_duplicate_target",
        title="Spatial Watermark",
        primary_candidate="alice",
        log_likelihood_ratio=5.0,
        bit_error_rate=0.01,
        target_binding=TargetBinding(document_id="doc_1", release_id="rel_1")
    )

    # Add 100 identical observations
    for _ in range(100):
        bundle.add_observation(base_obs)

    res = engine.fuse(bundle)

    # Score MUST NOT be 500.0, but deduplicated down to single effective contribution ~4.5 (after reliability calibration)
    assert res.fused_score < 10.0
    assert pytest.approx(res.fused_score, 0.5) == 4.5

def test_different_source_id_identical_payload_deduplication():
    """
    Adversarial Attack: An attacker submits the same forensic signal payload
    under 10 different source_id strings ('source_1', 'source_2', ..., 'source_10').
    """
    graph = EvidenceDependencyGraph()
    bundle = EvidenceBundle(bundle_id="b_diff_sources")

    for i in range(10):
        obs = WatermarkObservation(
            source_id=f"spoofed_source_{i}",
            title="Spatial Watermark",
            primary_candidate="alice",
            log_likelihood_ratio=6.0,
            bit_error_rate=0.02,
            target_binding=TargetBinding(document_id="doc_1", release_id="rel_1")
        )
        bundle.add_observation(obs)

    deduped = graph.deduplicate_observations(bundle.observations)
    assert len(deduped) == 1
