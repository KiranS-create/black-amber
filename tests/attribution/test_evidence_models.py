import pytest
from core.attribution.evidence import (
    AttributionState,
    EvidenceFamily,
    DependencyType,
    EvidenceConfidenceLevel,
    EvidenceSource,
    TargetBinding,
    EvidenceObservation,
    WatermarkObservation,
    TraceabilityObservation,
    ProvenanceObservation,
    LedgerObservation,
    IntegrityObservation,
    AttackContextObservation,
    EvidenceBundle,
)

def test_target_binding_matching():
    b1 = TargetBinding(document_id="doc_1", release_id="rel_A", artifact_hash="hash_123")
    b2 = TargetBinding(document_id="doc_1", release_id="rel_A", artifact_hash="hash_123")
    assert b1.matches(b2) is True

    # Partial binding matching
    b3 = TargetBinding(document_id="doc_1", release_id="rel_A")
    assert b1.matches(b3) is True

    # Mismatched document_id
    b4 = TargetBinding(document_id="doc_2", release_id="rel_A")
    assert b1.matches(b4) is False

def test_evidence_observations_creation():
    wm = WatermarkObservation(
        source_id="wm_spatial_1",
        title="Spatial Watermark",
        is_valid=True,
        log_likelihood_ratio=4.5,
        primary_candidate="alice",
        bit_error_rate=0.05,
        symbol_count=128,
        symbols_extracted=128
    )
    assert wm.family == EvidenceFamily.WATERMARK_PAYLOAD
    assert wm.get_candidate_llr("alice") == 4.5
    assert wm.get_candidate_llr("bob") == 0.0

    trace = TraceabilityObservation(
        source_id="tardos_1",
        title="Tardos Fingerprint",
        dependency_type=DependencyType.DERIVED,
        parent_source_id="wm_spatial_1",
        log_likelihood_ratio=9.2,
        primary_candidate="alice",
        observed_length=2048,
        margin_over_threshold=4.5,
        theoretical_false_alarm_bound=1e-5
    )
    assert trace.family == EvidenceFamily.TARDOS_FINGERPRINT
    assert trace.dependency_type == DependencyType.DERIVED
    assert trace.parent_source_id == "wm_spatial_1"

def test_evidence_bundle_aggregation():
    bundle = EvidenceBundle(
        bundle_id="bnd_001",
        target_binding=TargetBinding(document_id="doc_10", release_id="rel_99")
    )
    obs1 = WatermarkObservation(
        source_id="wm_1",
        title="Watermark 1",
        primary_candidate="alice",
        log_likelihood_ratio=5.0
    )
    obs2 = ProvenanceObservation(
        source_id="prov_1",
        title="ML-DSA Signature",
        signer_recipient_id="alice",
        signature_valid=True,
        log_likelihood_ratio=10.0
    )
    bundle.add_observation(obs1)
    bundle.add_observation(obs2)

    assert len(bundle.observations) == 2
    assert "alice" in bundle.get_candidate_ids()
    assert len(bundle.get_by_family(EvidenceFamily.WATERMARK_PAYLOAD)) == 1
    assert len(bundle.get_by_family(EvidenceFamily.PROVENANCE_SIGNATURE)) == 1
