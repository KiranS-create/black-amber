import pytest
from core.attribution.evidence import (
    EvidenceBundle,
    WatermarkObservation,
    ProvenanceObservation,
    LedgerObservation,
    TargetBinding,
    AttributionState
)
from core.attribution.fusion import EvidenceFusionEngine

def test_bob_evidence_with_charlie_release():
    """Verify that Bob's watermark evidence submitted under Charlie's target release is rejected as CONFLICT."""
    engine = EvidenceFusionEngine()
    b = EvidenceBundle(
        bundle_id="b_mismatch",
        target_binding=TargetBinding(document_id="doc_100", release_id="rel_CHARLIE")
    )

    obs_bob = WatermarkObservation(
        source_id="wm_bob",
        primary_candidate="bob",
        log_likelihood_ratio=8.0,
        target_binding=TargetBinding(document_id="doc_100", release_id="rel_BOB")  # Mismatch!
    )
    b.add_observation(obs_bob)

    res = engine.fuse(b)
    assert res.state == AttributionState.CONFLICT
    assert res.should_abstain is True
    assert "cross-document" in res.summary.lower()

def test_provenance_signature_verification_failure():
    """Verify that an invalid ML-DSA-65 signature on decryption event yields INSUFFICIENT_EVIDENCE when strict provenance is required."""
    from core.attribution.policy import DecisionPolicy

    policy = DecisionPolicy(strict_provenance_required=True)
    engine = EvidenceFusionEngine(policy=policy)

    b = EvidenceBundle(
        bundle_id="b_invalid_sig",
        target_binding=TargetBinding(document_id="doc_1", release_id="rel_1")
    )
    obs_sig = ProvenanceObservation(
        source_id="pqc_invalid",
        signer_recipient_id="bob",
        signature_valid=False,  # Failed cryptographic verification!
        log_likelihood_ratio=10.0,
        primary_candidate="bob",
        target_binding=TargetBinding(document_id="doc_1", release_id="rel_1")
    )
    b.add_observation(obs_sig)

    res = engine.fuse(b)
    assert res.state in (AttributionState.INSUFFICIENT_EVIDENCE, AttributionState.NO_SIGNAL)
    assert res.should_abstain is True
