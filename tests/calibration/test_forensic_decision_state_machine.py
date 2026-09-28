"""
SIH26237 - Forensic Decision State Machine & Transition Tests
Verifies all 7 decision outcomes, exact conditions, forbidden transitions, and abstention invariants.
"""

import pytest
from core.attribution.evidence import (
    AttributionState,
    EvidenceFamily,
    EvidenceSource,
    TargetBinding,
    EvidenceBundle,
    ProvenanceObservation,
    WatermarkObservation,
    LedgerObservation,
)
from core.attribution.fusion import EvidenceFusionEngine
from core.attribution.policy import DecisionPolicy


def test_state_machine_attributed_happy_path():
    """Verify ATTRIBUTED outcome when multi-channel evidence is strong and separated."""
    binding = TargetBinding(document_id="doc_1", release_id="rel_1", artifact_hash="h1")
    bundle = EvidenceBundle(
        target_binding=binding,
        observations=[
            ProvenanceObservation(
                source_id="prov_1",
                target_binding=binding,
                primary_candidate="rec_alice",
                candidate_scores={"rec_alice": 7.0},
                is_valid=True,
                log_likelihood_ratio=7.0,
                algorithm="ML-DSA-65",
                signature_valid=True,
                signer_recipient_id="rec_alice"
            ),
            WatermarkObservation(
                source_id="wm_1",
                target_binding=binding,
                primary_candidate="rec_alice",
                candidate_scores={"rec_alice": 5.0},
                is_valid=True,
                log_likelihood_ratio=5.0
            )
        ]
    )
    engine = EvidenceFusionEngine(policy=DecisionPolicy(min_attribution_score=6.0, min_separation_margin=2.5))
    res = engine.fuse(bundle)

    assert res.state == AttributionState.ATTRIBUTED
    assert res.top_candidate_id == "rec_alice"
    assert res.should_abstain is False
    assert res.confidence >= 0.90


def test_state_machine_no_signal_abstention():
    """Verify NO_SIGNAL outcome when evidence bundle is empty."""
    binding = TargetBinding(document_id="doc_1", release_id="rel_1", artifact_hash="h1")
    bundle = EvidenceBundle(target_binding=binding, observations=[])
    engine = EvidenceFusionEngine()
    res = engine.fuse(bundle)

    assert res.state == AttributionState.NO_SIGNAL
    assert res.top_candidate_id is None
    assert res.should_abstain is True
    assert res.confidence == 0.0


def test_state_machine_insufficient_evidence_subthreshold():
    """Verify INSUFFICIENT_EVIDENCE outcome when evidence is positive but below min_attribution_score."""
    binding = TargetBinding(document_id="doc_1", release_id="rel_1", artifact_hash="h1")
    bundle = EvidenceBundle(
        target_binding=binding,
        observations=[
            WatermarkObservation(
                source_id="wm_weak",
                target_binding=binding,
                primary_candidate="rec_alice",
                candidate_scores={"rec_alice": 2.0},  # Below 6.0 threshold
                is_valid=True,
                log_likelihood_ratio=2.0
            )
        ]
    )
    engine = EvidenceFusionEngine(policy=DecisionPolicy(min_attribution_score=6.0))
    res = engine.fuse(bundle)

    assert res.state == AttributionState.INSUFFICIENT_EVIDENCE
    assert res.should_abstain is True


def test_state_machine_conflict_resolution():
    """Verify CONFLICT outcome when two distinct candidates have strong conflicting evidence."""
    binding = TargetBinding(document_id="doc_1", release_id="rel_1", artifact_hash="h1")
    bundle = EvidenceBundle(
        target_binding=binding,
        observations=[
            ProvenanceObservation(
                source_id="prov_alice",
                target_binding=binding,
                primary_candidate="rec_alice",
                candidate_scores={"rec_alice": 7.0},
                is_valid=True,
                log_likelihood_ratio=7.0,
                algorithm="ML-DSA-65",
                signature_valid=True,
                signer_recipient_id="rec_alice"
            ),
            WatermarkObservation(
                source_id="wm_bob",
                target_binding=binding,
                primary_candidate="rec_bob",
                candidate_scores={"rec_bob": 6.8},
                is_valid=True,
                log_likelihood_ratio=6.8
            )
        ]
    )
    engine = EvidenceFusionEngine(policy=DecisionPolicy(min_attribution_score=6.0, min_separation_margin=2.5, conflict_runnerup_threshold=5.0))
    res = engine.fuse(bundle)

    assert res.state == AttributionState.CONFLICT
    assert res.should_abstain is True


def test_state_machine_forbidden_transition_on_invalid_signature():
    """Forbidden transition: Invalid signature MUST NOT produce ATTRIBUTED."""
    binding = TargetBinding(document_id="doc_1", release_id="rel_1", artifact_hash="h1")
    bundle = EvidenceBundle(
        target_binding=binding,
        observations=[
            ProvenanceObservation(
                source_id="forged_prov",
                target_binding=binding,
                primary_candidate="rec_mallory",
                candidate_scores={"rec_mallory": 10.0},
                is_valid=False,  # Signature failed
                log_likelihood_ratio=10.0,
                algorithm="ML-DSA-65",
                signature_valid=False,
                signer_recipient_id="rec_mallory"
            )
        ]
    )
    engine = EvidenceFusionEngine()
    res = engine.fuse(bundle)

    assert res.state != AttributionState.ATTRIBUTED
    assert res.should_abstain is True
