"""
SIH26237 - Negative and Positive Corpora Stress Tests
Verifies zero false positives on negative corpus and robust recovery on positive corpus.
"""

import pytest
from core.calibration.corpora import ForensicCorporaBuilder
from core.calibration.models import DatasetSplit, PopulationCategory
from core.calibration.evaluator import ForensicCalibrationEvaluator


def test_negative_corpus_zero_false_positives():
    """Verify that no negative or corrupted sample produces a false positive attribution."""
    builder = ForensicCorporaBuilder(random_seed=999)
    splits = builder.generate_full_evaluation_corpus(samples_per_category=20)
    test_samples = splits[DatasetSplit.HELD_OUT_TEST]

    # Filter for non-attributable categories
    negative_categories = {
        PopulationCategory.NEGATIVE_CLEAN,
        PopulationCategory.WRONG_RECIPIENT,
        PopulationCategory.WRONG_DOCUMENT,
        PopulationCategory.TAMPERED_ARTIFACT,
        PopulationCategory.REPLAYED_EVIDENCE,
        PopulationCategory.CONFLICTING_EVIDENCE,
        PopulationCategory.INSUFFICIENT_EVIDENCE,
        PopulationCategory.OUT_OF_ENVELOPE,
    }
    neg_samples = [s for s in test_samples if s.ground_truth.population in negative_categories]

    evaluator = ForensicCalibrationEvaluator()
    _, cm, rates, _, _ = evaluator.evaluate_corpus(neg_samples)

    assert cm.fp == 0, f"Violation: Observed {cm.fp} false positive attributions on negative corpus!"
    assert rates.precision == 1.0


def test_positive_corpus_robust_recovery():
    """Verify high recall on legitimate positive samples."""
    builder = ForensicCorporaBuilder(random_seed=999)
    splits = builder.generate_full_evaluation_corpus(samples_per_category=20)
    test_samples = splits[DatasetSplit.HELD_OUT_TEST]

    pos_samples = [s for s in test_samples if s.ground_truth.population == PopulationCategory.POSITIVE_CORRECT]

    evaluator = ForensicCalibrationEvaluator()
    _, cm, rates, _, _ = evaluator.evaluate_corpus(pos_samples)

    assert cm.tp == len(pos_samples)
    assert rates.recall == 1.0
