import pytest
from core.attribution.evidence import (
    AttributionState,
    EvidenceBundle,
    EvidenceObservation,
    TargetBinding,
    EvidenceFamily,
)
from core.attribution.fusion import EvidenceFusionEngine
from core.attribution.dependency import EvidenceDependencyGraph

def test_cross_document_binding_mismatch_flagged():
    graph = EvidenceDependencyGraph()
    bundle = EvidenceBundle(
        bundle_id="b_cross_doc",
        target_binding=TargetBinding(document_id="DOC_ALPHA", release_id="REL_001")
    )

    obs_legit = EvidenceObservation(
        source_id="obs_legit",
        family=EvidenceFamily.WATERMARK_PAYLOAD,
        target_binding=TargetBinding(document_id="DOC_ALPHA", release_id="REL_001"),
        log_likelihood_ratio=7.0,
        primary_candidate="alice"
    )
    obs_foreign = EvidenceObservation(
        source_id="obs_foreign",
        family=EvidenceFamily.AUDIT_LEDGER,
        target_binding=TargetBinding(document_id="DOC_BETA", release_id="REL_999"),  # Mismatched!
        log_likelihood_ratio=9.0,
        primary_candidate="alice"
    )
    bundle.add_observation(obs_legit)
    bundle.add_observation(obs_foreign)

    is_valid, violations = graph.validate_bundle_binding(bundle)
    assert is_valid is False
    assert len(violations) >= 1

    engine = EvidenceFusionEngine(dependency_graph=graph)
    result = engine.fuse(bundle)
    assert result.state == AttributionState.CONFLICT
    assert result.should_abstain is True
    assert "cross-document" in result.summary.lower()
