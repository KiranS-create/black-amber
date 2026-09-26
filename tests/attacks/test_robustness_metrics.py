import pytest
import numpy as np
from attacks.corpus.baseline_generator import BaselineTestCorpus
from attacks.digital.image_attacks import compute_image_metrics, GaussianBlurAttack
from attacks.measurement.metrics import TraceabilityMetricsEvaluator, EvaluationOutcome

def test_image_quality_metrics_identical_images():
    img_bytes = BaselineTestCorpus.generate_high_res_page_image()
    metrics = compute_image_metrics(img_bytes, img_bytes)
    assert metrics is not None
    assert metrics.psnr == 100.0
    assert metrics.ssim == 1.0
    assert metrics.mae == 0.0
    assert metrics.file_size_ratio == 1.0

def test_image_quality_metrics_degraded_image():
    img_bytes = BaselineTestCorpus.generate_high_res_page_image()
    attack = GaussianBlurAttack()
    blurred = attack._execute_transform(img_bytes, {"kernel_size": 15, "sigma": 5.0}, seed=None)
    metrics = compute_image_metrics(img_bytes, blurred.artifact_bytes)
    assert metrics.psnr < 40.0
    assert metrics.ssim < 0.95
    assert metrics.mae > 0.0

def test_traceability_metrics_symbol_survival_and_ber():
    orig = [1, 1, 0, 0, 1, 0, 1, 0, 1, 1]
    obs =  [1, 1, 0, 0, 1, 1, 1, 0, 0, 1]  # 2 errors at idx 5 and 8

    survival = TraceabilityMetricsEvaluator.symbol_survival_rate(orig, obs)
    assert survival == 0.8
    ber = TraceabilityMetricsEvaluator.bit_error_rate(orig, obs)
    assert ber == 0.2
    hamming = TraceabilityMetricsEvaluator.hamming_distance(orig, obs)
    assert hamming == 2

def test_traceability_metrics_erasure_rate():
    obs = [1, -1, 0, -1, 1, 0, 1, 0]
    erasure = TraceabilityMetricsEvaluator.erasure_rate(obs, erasure_value=-1)
    assert erasure == 0.25

def test_normalized_cross_correlation():
    v1 = [1.0, 2.0, 3.0, 4.0]
    v2 = [1.0, 2.0, 3.0, 4.0]
    corr_perfect = TraceabilityMetricsEvaluator.normalized_cross_correlation(v1, v2)
    assert corr_perfect == 1.0

    v3 = [-1.0, -2.0, -3.0, -4.0]
    corr_neg = TraceabilityMetricsEvaluator.normalized_cross_correlation(v1, v3)
    assert corr_neg == -1.0

def test_classification_outcomes():
    # 1. PASS: high survival + attributed to culprit
    outcome, _ = TraceabilityMetricsEvaluator.classify_outcome(
        survival_rate=0.98,
        attribution_status="ATTRIBUTED",
        attributed_to_culprit=True
    )
    assert outcome == EvaluationOutcome.PASS

    # 2. DEGRADE: moderate survival
    outcome, _ = TraceabilityMetricsEvaluator.classify_outcome(
        survival_rate=0.78,
        attribution_status="ATTRIBUTED",
        attributed_to_culprit=True
    )
    assert outcome == EvaluationOutcome.DEGRADE

    # 3. ABSTAIN: low survival + engine abstained
    outcome, _ = TraceabilityMetricsEvaluator.classify_outcome(
        survival_rate=0.30,
        attribution_status="NO_SIGNAL",
        attributed_to_culprit=False
    )
    assert outcome == EvaluationOutcome.ABSTAIN

    # 4. FAIL: false accusation of innocent party
    outcome, _ = TraceabilityMetricsEvaluator.classify_outcome(
        survival_rate=0.95,
        attribution_status="ATTRIBUTED",
        attributed_to_culprit=False
    )
    assert outcome == EvaluationOutcome.FAIL
