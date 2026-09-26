import pytest
from core.attribution.evidence import (
    EvidenceBundle,
    WatermarkObservation,
    TraceabilityObservation,
    AttackContextObservation,
    EvidenceFamily,
)
from core.attribution.reliability import AttackAwareReliabilityCalibrator

def test_watermark_ber_discounting():
    calibrator = AttackAwareReliabilityCalibrator()
    bundle = EvidenceBundle(bundle_id="b_ber")

    clean_wm = WatermarkObservation(
        source_id="wm_clean",
        title="Clean Watermark",
        bit_error_rate=0.0,
        symbol_count=100,
        symbols_extracted=100,
        reliability_prior=1.0
    )
    noisy_wm = WatermarkObservation(
        source_id="wm_noisy",
        title="Noisy Watermark",
        bit_error_rate=0.30,  # 30% BER
        symbol_count=100,
        symbols_extracted=100,
        reliability_prior=1.0
    )
    corrupted_wm = WatermarkObservation(
        source_id="wm_corrupt",
        title="Corrupted Watermark",
        bit_error_rate=0.55,  # > 50% BER
        symbol_count=100,
        symbols_extracted=100,
        reliability_prior=1.0
    )

    bundle.add_observation(clean_wm)
    bundle.add_observation(noisy_wm)
    bundle.add_observation(corrupted_wm)

    calibrator.calibrate_bundle(bundle)

    # Base prior for WATERMARK_PAYLOAD is 0.90
    assert pytest.approx(clean_wm.effective_reliability, 0.01) == 0.90
    # For BER=0.30: factor is 1.0 - 2(0.3) = 0.40 -> 0.90 * 0.40 = 0.36
    assert pytest.approx(noisy_wm.effective_reliability, 0.01) == 0.36
    # For BER=0.55: factor is max(0, 1 - 1.1) = 0.0
    assert corrupted_wm.effective_reliability == 0.0

def test_physical_capture_discounting():
    calibrator = AttackAwareReliabilityCalibrator()
    bundle = EvidenceBundle(bundle_id="b_phys")

    attack = AttackContextObservation(
        source_id="attack_1",
        title="Attack Context",
        execution_mode="PHYSICAL",
        crop_ratio=0.80,
        ssim=0.65
    )
    bundle.attack_context = attack

    wm = WatermarkObservation(
        source_id="wm_1",
        title="Spatial Watermark",
        bit_error_rate=0.05,
        symbol_count=100,
        symbols_extracted=100,
        reliability_prior=1.0
    )
    bundle.add_observation(wm)

    calibrator.calibrate_bundle(bundle)

    # Effective reliability should be discounted by physical flag, crop ratio, and SSIM
    assert wm.effective_reliability < 0.90
    assert wm.effective_reliability > 0.0

def test_tardos_erasure_and_margin_discounting():
    calibrator = AttackAwareReliabilityCalibrator()
    bundle = EvidenceBundle(bundle_id="b_tardos")

    trace_strong = TraceabilityObservation(
        source_id="tardos_strong",
        title="Strong Tardos",
        erasure_rate=0.0,
        margin_over_threshold=10.0,
        reliability_prior=1.0
    )
    trace_weak = TraceabilityObservation(
        source_id="tardos_weak",
        title="Weak Tardos",
        erasure_rate=0.40,  # 40% erasures
        margin_over_threshold=2.5,  # Narrow margin
        reliability_prior=1.0
    )
    bundle.add_observation(trace_strong)
    bundle.add_observation(trace_weak)

    calibrator.calibrate_bundle(bundle)

    assert trace_strong.effective_reliability == 0.95
    assert trace_weak.effective_reliability < trace_strong.effective_reliability
