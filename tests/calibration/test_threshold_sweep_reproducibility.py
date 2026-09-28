"""
SIH26237 - Threshold Sweep Reproducibility & Pareto Policy Selection Tests
"""

import pytest
from core.calibration.corpora import ForensicCorporaBuilder
from core.calibration.models import DatasetSplit
from core.calibration.sweep import ThresholdSweepEngine


def test_threshold_sweep_execution_and_pareto_selection():
    """Verify threshold sweep executes across score grid and selects Pareto optimal policy."""
    builder = ForensicCorporaBuilder(random_seed=12345)
    splits = builder.generate_full_evaluation_corpus(samples_per_category=20)
    calib_samples = splits[DatasetSplit.CALIBRATION]

    sweep_engine = ThresholdSweepEngine(calib_samples)
    grid = [3.0, 5.0, 6.0, 8.0, 10.0]
    sweep_results = sweep_engine.sweep_attribution_score(scores=grid)

    assert len(sweep_results) == len(grid)

    # Check monotonicity of coverage: higher threshold -> equal or lower coverage
    coverages = [r["coverage"] for r in sweep_results]
    for i in range(len(coverages) - 1):
        assert coverages[i] >= coverages[i + 1]

    optimal = sweep_engine.find_optimal_threshold(sweep_results)
    assert optimal is not None
    assert optimal["fp"] == 0
    assert optimal["selective_accuracy"] >= 0.99
    assert optimal["min_attribution_score"] in grid
