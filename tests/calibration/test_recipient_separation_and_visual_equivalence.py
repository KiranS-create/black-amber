"""
SIH26237 - Recipient Codeword Separation & Visual Equivalence Tests
Verifies statistical orthogonality across recipient codewords and empirical visual
fidelity distributions while maintaining the strict physical hardware epistemic boundary.
"""

import pytest
from core.calibration.separation import RecipientSeparationAnalyzer
from core.calibration.visual import VisualEquivalenceDistributionAnalyzer
from core.watermark.sync import CanonicalCanvasSpec


def test_recipient_separation_orthogonality():
    """Verify pairwise Hamming distance and cross-correlation across candidate pools."""
    summary = RecipientSeparationAnalyzer.analyze_separation(
        candidate_pool_size=50,
        codeword_length=128,
    )

    assert summary.candidate_pool_size == 50
    assert summary.codeword_length_bits == 128
    assert summary.pairwise_comparisons == (50 * 49) // 2
    assert summary.observed_collisions == 0
    # For independent 128-bit random codewords, mean Hamming distance should be ~64 (between 55 and 73)
    assert 55.0 <= summary.mean_hamming_distance <= 73.0
    assert summary.min_hamming_distance >= 25
    assert summary.max_cross_correlation < 0.60
    assert summary.theoretical_collision_bound < 1e-25


def test_visual_equivalence_fidelity_and_boundary():
    """
    Verify visual equivalence distribution metrics (SSIM, PSNR)
    and ensure the hardware epistemic status is explicitly marked NOT_VERIFIED.
    """
    spec = CanonicalCanvasSpec(width=800, height=1000)
    vis = VisualEquivalenceDistributionAnalyzer.evaluate_visual_distribution(
        sample_count=5,
        spec=spec,
    )

    assert vis.sample_count == 5
    assert vis.ssim_median >= 0.70
    assert vis.psnr_median_db >= 25.0
    assert vis.text_equality_pass_rate == 1.0

    # Epistemic boundary verification: Hardware testing without physical camera rig must be NOT_VERIFIED
    assert vis.hardware_status == "NOT_VERIFIED"
