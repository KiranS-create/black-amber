"""
SIH26237 - Test Physical Negative Corpus Fail-Closed Robustness
"""

import pytest
from core.physical.negative_corpus import PhysicalNegativeCorpusBuilder, PhysicalNegativeResult


def test_physical_negative_corpus_zero_false_positives():
    """Verify negative corpus produces 0 false positives across all baseline noise and carrier corruption samples."""
    builder = PhysicalNegativeCorpusBuilder()
    results = builder.evaluate_negative_corpus()

    assert len(results) == 40
    for res in results:
        assert isinstance(res, PhysicalNegativeResult)
        assert res.false_positive_attribution is False
        assert res.is_safe_rejection is True
        assert res.observed_status in [
            "NO_SIGNAL", "INSUFFICIENT_EVIDENCE", "CONFLICT", "UNMARKED", "CORRUPTED", "PARTIAL"
        ]
