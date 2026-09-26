import pytest
from core.attribution.evidence import (
    EvidenceBundle,
    EvidenceObservation,
    WatermarkObservation,
    ProvenanceObservation,
    EvidenceFamily,
    TargetBinding,
    AttributionState,
    DependencyType
)
from core.attribution.fusion import EvidenceFusionEngine

def test_property_a_unrelated_evidence_does_not_change_attribution():
    """Adding unrelated evidence for an uninvolved candidate should not alter top attribution."""
    engine = EvidenceFusionEngine()
    
    # Bundle with strong support for Alice
    b1 = EvidenceBundle(bundle_id="b1", target_binding=TargetBinding(document_id="doc1", release_id="rel1"))
    b1.add_observation(WatermarkObservation(
        source_id="wm_alice", primary_candidate="alice", log_likelihood_ratio=9.0,
        target_binding=TargetBinding(document_id="doc1", release_id="rel1")
    ))
    res1 = engine.fuse(b1)
    assert res1.state == AttributionState.ATTRIBUTED
    assert res1.top_candidate_id == "alice"

    # Add weak neutral/unrelated evidence for Bob
    b1.add_observation(EvidenceObservation(
        source_id="struct_bob", family=EvidenceFamily.DOCUMENT_STRUCTURE,
        primary_candidate="bob", log_likelihood_ratio=1.0,
        target_binding=TargetBinding(document_id="doc1", release_id="rel1")
    ))
    res2 = engine.fuse(b1)
    assert res2.state == AttributionState.ATTRIBUTED
    assert res2.top_candidate_id == "alice"

def test_property_b_invalid_evidence_does_not_strengthen_attribution():
    """Adding an invalid (corrupted/failed) observation must not increase fused score."""
    engine = EvidenceFusionEngine()
    b = EvidenceBundle(bundle_id="b2", target_binding=TargetBinding(document_id="doc1", release_id="rel1"))
    
    obs_valid = WatermarkObservation(
        source_id="wm1", primary_candidate="alice", log_likelihood_ratio=7.0,
        target_binding=TargetBinding(document_id="doc1", release_id="rel1")
    )
    b.add_observation(obs_valid)
    res_before = engine.fuse(b)

    obs_invalid = WatermarkObservation(
        source_id="wm2_corrupt", primary_candidate="alice", log_likelihood_ratio=10.0,
        is_valid=False, target_binding=TargetBinding(document_id="doc1", release_id="rel1")
    )
    b.add_observation(obs_invalid)
    res_after = engine.fuse(b)

    assert res_after.fused_score <= res_before.fused_score

def test_property_c_removing_supporting_evidence_does_not_strengthen_attribution():
    """Removing a supporting observation must not increase fused score for that candidate."""
    engine = EvidenceFusionEngine()
    b = EvidenceBundle(bundle_id="b3", target_binding=TargetBinding(document_id="doc1", release_id="rel1"))
    
    obs1 = WatermarkObservation(
        source_id="wm1", primary_candidate="alice", log_likelihood_ratio=5.0,
        target_binding=TargetBinding(document_id="doc1", release_id="rel1")
    )
    obs2 = ProvenanceObservation(
        source_id="pqc1", signer_recipient_id="alice", signature_valid=True,
        log_likelihood_ratio=8.0, primary_candidate="alice",
        target_binding=TargetBinding(document_id="doc1", release_id="rel1")
    )
    b.add_observation(obs1)
    b.add_observation(obs2)
    res_full = engine.fuse(b)

    # Remove obs2
    b_reduced = EvidenceBundle(bundle_id="b3_red", target_binding=TargetBinding(document_id="doc1", release_id="rel1"))
    b_reduced.add_observation(obs1)
    res_reduced = engine.fuse(b_reduced)

    assert res_reduced.fused_score <= res_full.fused_score

def test_property_e_f_changing_document_or_release_id_invalidates():
    """Changing target document_id or release_id triggers binding violation -> CONFLICT / Abstention."""
    engine = EvidenceFusionEngine()
    b = EvidenceBundle(bundle_id="b4", target_binding=TargetBinding(document_id="doc_ALPHA", release_id="rel_1"))
    
    obs_mismatched = WatermarkObservation(
        source_id="wm1", primary_candidate="alice", log_likelihood_ratio=10.0,
        target_binding=TargetBinding(document_id="doc_BETA", release_id="rel_1")  # Mismatched doc!
    )
    b.add_observation(obs_mismatched)

    res = engine.fuse(b)
    assert res.state == AttributionState.CONFLICT
    assert res.should_abstain is True

def test_property_h_contradiction_does_not_disappear():
    """Two reliable independent sources for different recipients trigger CONFLICT even if one score is larger."""
    engine = EvidenceFusionEngine()
    b = EvidenceBundle(bundle_id="b5", target_binding=TargetBinding(document_id="doc1", release_id="rel1"))
    
    obs1 = WatermarkObservation(
        source_id="wm_alice", primary_candidate="alice", log_likelihood_ratio=12.0,
        target_binding=TargetBinding(document_id="doc1", release_id="rel1")
    )
    obs2 = ProvenanceObservation(
        source_id="pqc_bob", signer_recipient_id="bob", signature_valid=True,
        log_likelihood_ratio=7.0, primary_candidate="bob",
        target_binding=TargetBinding(document_id="doc1", release_id="rel1")
    )
    b.add_observation(obs1)
    b.add_observation(obs2)

    res = engine.fuse(b)
    assert res.state == AttributionState.CONFLICT
    assert res.should_abstain is True
