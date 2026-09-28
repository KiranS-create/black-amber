"""
SIH26237 - Corpora & Dataset Partition Isolation Tests
Verifies that CALIBRATION, VALIDATION, and HELD_OUT_TEST splits have strict zero overlap
in sample IDs, content hashes, and document bindings.
"""

import pytest
from core.calibration.models import DatasetSplit, PopulationCategory
from core.calibration.corpora import ForensicCorporaBuilder


def test_corpora_population_completeness():
    """Verify all 12 population categories are generated."""
    builder = ForensicCorporaBuilder(random_seed=42)
    splits = builder.generate_full_evaluation_corpus(samples_per_category=20)

    for split in DatasetSplit:
        samples = splits[split]
        assert len(samples) > 0
        categories_present = {s.ground_truth.population for s in samples}
        assert len(categories_present) == len(PopulationCategory)


def test_strict_split_disjointness():
    """Verify strict non-overlapping partition across all three dataset splits."""
    builder = ForensicCorporaBuilder(random_seed=42)
    splits = builder.generate_full_evaluation_corpus(samples_per_category=40)

    calib_samples = splits[DatasetSplit.CALIBRATION]
    val_samples = splits[DatasetSplit.VALIDATION]
    test_samples = splits[DatasetSplit.HELD_OUT_TEST]

    calib_ids = {s.sample_id for s in calib_samples}
    val_ids = {s.sample_id for s in val_samples}
    test_ids = {s.sample_id for s in test_samples}

    assert calib_ids.isdisjoint(val_ids)
    assert calib_ids.isdisjoint(test_ids)
    assert val_ids.isdisjoint(test_ids)

    # Content hash disjointness
    calib_hashes = {s.ground_truth.content_hash for s in calib_samples}
    val_hashes = {s.ground_truth.content_hash for s in val_samples}
    test_hashes = {s.ground_truth.content_hash for s in test_samples}

    assert calib_hashes.isdisjoint(val_hashes)
    assert calib_hashes.isdisjoint(test_hashes)
    assert val_hashes.isdisjoint(test_hashes)


def test_ground_truth_honesty_invariants():
    """Verify ground truth annotations preserve forensic honesty invariants."""
    builder = ForensicCorporaBuilder(random_seed=42)
    sample_unknown = builder.generate_population_sample(
        PopulationCategory.UNKNOWN_DOWNSTREAM,
        1,
        DatasetSplit.CALIBRATION
    )

    # Unknown downstream must never invent a false downstream name
    assert sample_unknown.ground_truth.metadata.get("honesty_boundary") == "LAST_KNOWN_HOLDER"
    assert sample_unknown.ground_truth.is_attributable is True

    # Negative clean sample must have None as true recipient
    sample_neg = builder.generate_population_sample(
        PopulationCategory.NEGATIVE_CLEAN,
        1,
        DatasetSplit.CALIBRATION
    )
    assert sample_neg.ground_truth.true_recipient_id is None
    assert sample_neg.ground_truth.is_attributable is False
