"""
SIH26237 - Test Cross-Recipient Physical Separation Matrix
"""

import pytest
from core.physical.separation import PhysicalSeparationMatrixAnalyzer, PhysicalSeparationMatrixSummary


def test_cross_recipient_separation_matrix():
    """Verify cross-recipient codeword Hamming distances and collision-free separation."""
    summary = PhysicalSeparationMatrixAnalyzer.analyze_cross_recipient_separation()

    assert isinstance(summary, PhysicalSeparationMatrixSummary)
    assert summary.observed_cross_recipient_collisions == 0
    assert summary.empirical_collision_rate_str == "0 / 3"
    assert summary.min_pairwise_hamming_distance >= 40
    assert len(summary.pairwise_entries) == 3  # (Alice, Bob), (Alice, Charlie), (Bob, Charlie)
    for entry in summary.pairwise_entries:
        assert entry.collision_detected is False
        assert entry.is_orthogonal is True
