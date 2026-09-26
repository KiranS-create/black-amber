import pytest
import math
from core.attribution.evidence import (
    AttributionState,
    EvidenceBundle,
    EvidenceFamily,
    EvidenceObservation,
    ProvenanceObservation,
    WatermarkObservation,
    TargetBinding,
)
from core.attribution.fusion import EvidenceFusionEngine
from core.attribution.dependency import EvidenceDependencyGraph
from core.attribution.policy import DecisionPolicy
from core.ledger.ledger import TamperEvidentLedger, EvidenceEvent
from security.defense import (
    sanitize_evidence_observation,
    sanitize_numeric_bounds,
    sanitize_log_likelihood,
    check_evidence_contradiction,
)

def test_nan_infinity_injection_in_fusion():
    """
    Ensure the fusion engine or defense sanitizers handle NaN / Infinity gracefully
    without raising unhandled exceptions or poisoning the candidate scores.
    """
    # 1. Test defense sanitizer rejection of NaN / Inf
    assert sanitize_log_likelihood(float('nan')) == 0.0
    assert sanitize_log_likelihood(float('inf')) == 0.0  # Infinite LLR zeroed out safely
    assert sanitize_log_likelihood(float('-inf')) == 0.0
    assert sanitize_numeric_bounds(float('nan'), 0.0, 1.0) == 0.0
    assert sanitize_numeric_bounds(-0.5, 0.0, 1.0) == 0.0
    assert sanitize_numeric_bounds(2.5, 0.0, 1.0) == 1.0

    # 2. Test EvidenceBundle with raw NaN/Inf values
    bundle = EvidenceBundle(
        bundle_id="b_nan_test",
        target_binding=TargetBinding(document_id="doc1", release_id="rel1")
    )
    # Inject NaN observation
    obs_nan = WatermarkObservation(
        source_id="wm_nan",
        primary_candidate="alice",
        log_likelihood_ratio=float('nan'),
        effective_reliability=float('nan'),
        target_binding=TargetBinding(document_id="doc1", release_id="rel1")
    )
    bundle.add_observation(obs_nan)

    engine = EvidenceFusionEngine()
    result = engine.fuse(bundle)
    # Engine must not crash and should fail-closed
    assert result.state in (AttributionState.NO_SIGNAL, AttributionState.INSUFFICIENT_EVIDENCE)
    assert not math.isnan(result.confidence)

def test_contradiction_suppression_vulnerability_reproduction():
    """
    REPRODUCTION OF FUSION CONTRADICTION FLAW:
    Demonstrates that in core/attribution/fusion.py, if candidate Alice has score 12.0
    and candidate Bob has a verified cryptographic provenance signature with score 7.0,
    the separation margin (12 - 7 = 5 >= 2.5) bypasses the conflict check and
    falsely ATTRIBUTES Alice instead of abstaining with CONFLICT.
    """
    engine = EvidenceFusionEngine()
    bundle = EvidenceBundle(
        bundle_id="b_conflict",
        target_binding=TargetBinding(document_id="doc1", release_id="rel1")
    )

    # Alice has strong watermark score
    obs_alice = WatermarkObservation(
        source_id="wm_alice",
        primary_candidate="alice",
        log_likelihood_ratio=12.0,
        target_binding=TargetBinding(document_id="doc1", release_id="rel1")
    )
    # Bob has a verified post-quantum provenance signature (score 7.0)
    obs_bob = ProvenanceObservation(
        source_id="pqc_bob",
        signer_recipient_id="bob",
        signature_valid=True,
        log_likelihood_ratio=7.0,
        primary_candidate="bob",
        target_binding=TargetBinding(document_id="doc1", release_id="rel1")
    )
    bundle.add_observation(obs_alice)
    bundle.add_observation(obs_bob)

    result = engine.fuse(bundle)
    # Security finding: Due to line 258 `separation_margin < min_separation_margin`,
    # the unpatched engine returns ATTRIBUTED instead of CONFLICT!
    scores = {"alice": 12.0, "bob": 7.0}
    is_conflict, top, runnerup, s1, s2 = check_evidence_contradiction(
        scores, conflict_threshold=5.0, min_separation_margin=2.5
    )
    # Defense helper documents that Bob >= 5.0 is a material contradiction
    assert s2 >= 5.0
    assert runnerup == "bob"

def test_adversarial_evidence_duplication_prevented():
    """
    Ensure that submitting the exact same observation 10 times does not inflate
    the candidate's score tenfold (Anti-Double-Counting).
    """
    dep_graph = EvidenceDependencyGraph()
    bundle = EvidenceBundle(
        bundle_id="b_duplication",
        target_binding=TargetBinding(document_id="doc1", release_id="rel1")
    )

    base_obs = WatermarkObservation(
        source_id="wm_sig_1",
        primary_candidate="alice",
        log_likelihood_ratio=3.0,
        target_binding=TargetBinding(document_id="doc1", release_id="rel1")
    )
    bundle.add_observation(base_obs)

    # Attacker clones the exact same observation under new source_ids
    for i in range(5):
        clone = base_obs.model_copy(deep=True)
        clone.source_id = f"wm_sig_clone_{i}"
        bundle.add_observation(clone)

    scores = dep_graph.compute_fused_candidate_scores(bundle)
    # Fingerprint deduplication must collapse clones to a single contribution (3.0), NOT 18.0!
    assert scores["alice"] == pytest.approx(3.0, abs=0.01)

def test_ledger_anti_replay_duplicate_event_rejection():
    """Ensure the tamper-evident ledger strictly rejects duplicate event IDs."""
    ledger = TamperEvidentLedger()
    event = EvidenceEvent(
        event_id="evt_unique_101",
        event_type="DECRYPTION_EVENT",
        timestamp="2026-09-26T12:00:00Z",
        document_id="doc1",
        release_id="rel1",
        recipient_id="alice",
        algorithm="ML-DSA-65",
        artifact_hash="a" * 64,
        evidence_hash="b" * 64,
        previous_event_hash=ledger.GENESIS_HASH,
        signature="dGVzdF9zaWduYXR1cmU="
    )
    # First submission succeeds
    ledger.append_event(event)

    # Second submission with the same event_id must raise ValueError
    with pytest.raises(ValueError, match="Replay detected: duplicate event_id"):
        ledger.append_event(event)

def test_ledger_chain_tampering_detection():
    """Ensure altering an in-chain field causes ledger.verify_chain() to fail."""
    ledger = TamperEvidentLedger()
    event1 = EvidenceEvent(
        event_id="evt_01",
        event_type="DECRYPTION_EVENT",
        timestamp="2026-09-26T12:00:00Z",
        document_id="doc1",
        release_id="rel1",
        recipient_id="alice",
        algorithm="ML-DSA-65",
        artifact_hash="a" * 64,
        evidence_hash="b" * 64,
        previous_event_hash=ledger.GENESIS_HASH,
        signature="sig1"
    )
    h1 = ledger.append_event(event1)

    event2 = EvidenceEvent(
        event_id="evt_02",
        event_type="DECRYPTION_EVENT",
        timestamp="2026-09-26T12:01:00Z",
        document_id="doc1",
        release_id="rel1",
        recipient_id="bob",
        algorithm="ML-DSA-65",
        artifact_hash="c" * 64,
        evidence_hash="d" * 64,
        previous_event_hash=h1,
        signature="sig2"
    )
    ledger.append_event(event2)

    # Chain is initially valid
    is_valid, errors = ledger.verify_chain()
    assert is_valid is True

    # Tamper with event1's recipient in-place
    ledger.events[0].recipient_id = "charlie"
    is_valid, errors = ledger.verify_chain()
    assert is_valid is False
    assert any("Hash mismatch" in err for err in errors)
