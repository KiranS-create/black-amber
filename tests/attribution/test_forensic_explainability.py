import pytest
from core.attribution.evidence import (
    AttributionState,
    EvidenceBundle,
    EvidenceObservation,
    ProvenanceObservation,
    WatermarkObservation,
    EvidenceFamily,
    EvidenceConfidenceLevel,
)
from core.attribution.fusion import EvidenceFusionEngine

def test_explainability_reasoning_and_sources():
    engine = EvidenceFusionEngine()
    bundle = EvidenceBundle(bundle_id="b_explain")

    obs1 = WatermarkObservation(
        source_id="wm_extract_01",
        title="Spatial Watermark Extraction",
        log_likelihood_ratio=7.0,
        primary_candidate="alice",
        bit_error_rate=0.02
    )
    obs2 = ProvenanceObservation(
        source_id="pqc_sig_01",
        title="ML-DSA-65 Recipient Decryption Signature",
        signer_recipient_id="alice",
        signature_valid=True,
        log_likelihood_ratio=8.0,
        primary_candidate="alice"
    )
    bundle.add_observation(obs1)
    bundle.add_observation(obs2)

    result = engine.fuse(bundle)
    assert result.state == AttributionState.ATTRIBUTED
    assert result.top_candidate_id == "alice"
    assert result.confidence_level in (EvidenceConfidenceLevel.HIGH, EvidenceConfidenceLevel.MEDIUM)
    assert result.should_abstain is False

    # Check explainability fields
    assert len(result.reasoning_steps) >= 3
    assert "wm_extract_01" in result.supporting_sources
    assert "pqc_sig_01" in result.supporting_sources
    assert len(result.recommended_next_steps) >= 1
    assert "alice" in result.summary
