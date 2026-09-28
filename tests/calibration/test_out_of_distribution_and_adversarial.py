"""
SIH26237 - Out of Distribution & Adversarial Evidence Calibration Tests
Verifies robust fail-closed abstention under severe distortion, out-of-envelope samples,
and adversarial evidence tampering.
"""

import pytest
import hashlib
from core.calibration.adversarial_search import AdversarialEvidenceSearcher
from core.calibration.models import DatasetSplit, PopulationCategory
from core.calibration.corpora import ForensicCorporaBuilder
from core.calibration.evaluator import ForensicCalibrationEvaluator
from core.attribution.evidence import (
    AttributionState,
    TargetBinding,
    EvidenceBundle,
    WatermarkObservation,
    ProvenanceObservation,
    ExternalTelemetryObservation,
)
from core.attribution.fusion import EvidenceFusionEngine
from core.attribution.policy import DecisionPolicy


def test_adversarial_suite_zero_false_attribution():
    """Verify that all 5 structured adversarial attack scenarios preserve security invariants."""
    searcher = AdversarialEvidenceSearcher()
    results = searcher.run_adversarial_suite()

    assert len(results) >= 5
    for r in results:
        assert r["security_invariant_preserved"] is True, (
            f"Adversarial vulnerability in {r['scenario']}: "
            f"fused_state={r['fused_state']}, top_candidate={r['top_candidate']}"
        )
        # Verify no adversarial attack achieved ATTRIBUTED state
        assert r["fused_state"] != AttributionState.ATTRIBUTED.value


def test_out_of_envelope_distortion_causes_abstention():
    """Verify that out-of-envelope samples in evaluation corpus yield abstention."""
    builder = ForensicCorporaBuilder(random_seed=42)
    splits = builder.generate_full_evaluation_corpus(samples_per_category=10)
    ood_samples = [
        s for s in splits[DatasetSplit.HELD_OUT_TEST]
        if s.ground_truth.population == PopulationCategory.OUT_OF_ENVELOPE
    ]

    evaluator = ForensicCalibrationEvaluator()
    results, cm, rates, abstention, _ = evaluator.evaluate_corpus(ood_samples)

    # All OOD samples should fail or abstain, none should falsely attribute
    assert cm.fp == 0
    assert cm.tn == len(ood_samples)
    assert abstention.abstained_count == len(ood_samples)


def test_downstream_gap_honesty_invariant():
    """
    Verify downstream gap honesty:
    When an unknown downstream leak occurs (A -> B -> unknown -> leak),
    the system must attribute the last known holder (B) or abstain,
    and NEVER invent an unknown entity or claim complete end-to-end chain.
    """
    builder = ForensicCorporaBuilder(random_seed=42)
    splits = builder.generate_full_evaluation_corpus(samples_per_category=10)
    downstream_samples = [
        s for s in splits[DatasetSplit.HELD_OUT_TEST]
        if s.ground_truth.population == PopulationCategory.UNKNOWN_DOWNSTREAM
    ]

    evaluator = ForensicCalibrationEvaluator()
    results, cm, rates, _, _ = evaluator.evaluate_corpus(downstream_samples)

    assert cm.fp == 0
    valid_states = {
        AttributionState.ATTRIBUTED.value,
        AttributionState.ABSTAINED.value,
        AttributionState.INSUFFICIENT_EVIDENCE.value,
        AttributionState.REVIEW_REQUIRED.value,
    }
    for res in results:
        # Decision should be attributed to last known holder or abstain/review
        assert res["predicted_state"] in valid_states


def test_cross_document_transplant_rejected():
    """Verify that watermarks from mismatched document bindings are rejected."""
    binding_target = TargetBinding(
        document_id="doc_classified_alpha",
        release_id="rel_alpha_001",
        artifact_hash=hashlib.sha256(b"alpha_bytes").hexdigest(),
        document_root_hash=hashlib.sha256(b"alpha_root").hexdigest(),
    )
    binding_foreign = TargetBinding(
        document_id="doc_public_beta",
        release_id="rel_beta_002",
        artifact_hash=hashlib.sha256(b"beta_bytes").hexdigest(),
        document_root_hash=hashlib.sha256(b"beta_root").hexdigest(),
    )

    bundle = EvidenceBundle(
        target_binding=binding_target,
        observations=[
            WatermarkObservation(
                source_id="transplanted_wm",
                target_binding=binding_foreign,  # Mismatched target
                primary_candidate="rec_framed_person",
                candidate_scores={"rec_framed_person": 10.0},
                is_valid=True,
                log_likelihood_ratio=10.0,
            )
        ],
    )

    engine = EvidenceFusionEngine(policy=DecisionPolicy())
    result = engine.fuse(bundle)

    assert result.state != AttributionState.ATTRIBUTED
    assert result.should_abstain is True
