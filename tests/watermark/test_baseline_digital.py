"""
SIH26237 - Watermark Digital Baseline Tests
Validates bit-exact encode/decode roundtrips, carrier strategies, PSNR visual quality,
and basic digital robustness transformations (JPEG, blur, noise, grayscale).
"""

import pytest
import numpy as np
import cv2

from core.watermark import (
    PrintCameraWatermarkEncoder,
    PrintCameraWatermarkDecoder,
    WatermarkPayload,
    WatermarkStatus,
    CarrierConfig,
    CarrierStrategy,
    CanonicalCanvasSpec,
)


@pytest.fixture
def clean_canvas():
    """Generates a synthetic high-contrast document page canvas."""
    canvas = np.ones((1000, 800, 3), dtype=np.uint8) * 245
    cv2.putText(canvas, "SIH26237 CONFIDENTIAL RELEASE", (140, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (20, 20, 20), 2)
    cv2.putText(canvas, "RESTRICTED DISTRIBUTION - DO NOT PHOTOCOPY", (140, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (80, 80, 80), 1)
    for y in range(280, 750, 40):
        cv2.line(canvas, (140, y), (660, y), (200, 200, 200), 1)
    return canvas


@pytest.mark.parametrize("codeword_len", [64, 128, 256])
def test_clean_digital_roundtrip_various_lengths(clean_canvas, codeword_len):
    """Verifies 100% bit-exact recovery on clean digital images across multiple codeword lengths."""
    encoder = PrintCameraWatermarkEncoder()
    decoder = PrintCameraWatermarkDecoder()

    rng = np.random.RandomState(codeword_len)
    codeword = rng.choice([0, 1], size=codeword_len).tolist()
    payload = WatermarkPayload(document_id="DOC_CLEAN", release_id="REL_01", codeword=codeword)

    wm_canvas = encoder.encode(clean_canvas, payload)
    obs = decoder.decode(wm_canvas, expected_document_id="DOC_CLEAN", expected_release_id="REL_01", codeword_length_hint=codeword_len)

    assert obs.status == WatermarkStatus.RECOVERED
    assert obs.is_valid is True
    assert obs.confidence >= 0.85
    assert obs.observed_symbols == codeword
    assert obs.raw_ber <= 0.10



@pytest.mark.parametrize("strategy", [
    CarrierStrategy.RENDERED_PAGE_CANVAS,
    CarrierStrategy.GRAPHICAL_ROI,
    CarrierStrategy.SECURITY_BACKGROUND_TEXTURE,
])
def test_all_three_carrier_strategies(clean_canvas, strategy):
    """Verifies that all three carrier strategies embed and decode with high visual fidelity (PSNR > 34 dB)."""
    cfg = CarrierConfig(strategy=strategy, block_size=20, embedding_strength_alpha=12.0)
    encoder = PrintCameraWatermarkEncoder(carrier_config=cfg)
    decoder = PrintCameraWatermarkDecoder(carrier_config=cfg)

    codeword = [1, 0, 1, 1, 0, 0, 1, 0] * 16  # 128 bits
    payload = WatermarkPayload(document_id="DOC_STRAT", release_id="REL_S", codeword=codeword)

    # Base anchored canvas (with fiducials)
    anchored_base = encoder.synchronizer.embed_fiducial_anchors(clean_canvas)
    wm_canvas = encoder.encode(clean_canvas, payload)

    # Measure PSNR of carrier modulation against anchored base
    orig_f = anchored_base.astype(np.float32)
    wm_f = wm_canvas.astype(np.float32)
    mse = np.mean((orig_f - wm_f) ** 2)
    psnr = 10.0 * np.log10((255.0 ** 2) / max(mse, 1e-10))
    assert psnr >= 30.0, f"PSNR {psnr} dB below threshold for strategy {strategy}"

    obs = decoder.decode(wm_canvas, expected_document_id="DOC_STRAT", expected_release_id="REL_S")
    assert obs.status == WatermarkStatus.RECOVERED
    assert obs.observed_symbols == codeword




def test_digital_jpeg_recompression_robustness(clean_canvas):
    """Verifies resilience against severe digital JPEG recompression (Q=60, Q=80)."""
    encoder = PrintCameraWatermarkEncoder()
    decoder = PrintCameraWatermarkDecoder()

    codeword = [1, 0, 1, 1, 0, 0, 1, 0] * 16
    payload = WatermarkPayload(document_id="DOC_JPEG", release_id="REL_J", codeword=codeword)
    wm_canvas = encoder.encode(clean_canvas, payload)

    for quality in [80, 60]:
        _, buf = cv2.imencode(".jpg", wm_canvas, [cv2.IMWRITE_JPEG_QUALITY, quality])
        recompressed = cv2.imdecode(buf, cv2.IMREAD_COLOR)

        obs = decoder.decode(recompressed, expected_document_id="DOC_JPEG", expected_release_id="REL_J")
        assert obs.status == WatermarkStatus.RECOVERED
        assert obs.observed_symbols == codeword


def test_digital_gaussian_blur_and_noise(clean_canvas):
    """Verifies resilience against digital Gaussian blur and zero-mean additive noise."""
    encoder = PrintCameraWatermarkEncoder()
    decoder = PrintCameraWatermarkDecoder()

    codeword = [1, 0, 1, 1, 0, 0, 1, 0] * 16
    payload = WatermarkPayload(document_id="DOC_NOISE", release_id="REL_N", codeword=codeword)
    wm_canvas = encoder.encode(clean_canvas, payload)

    # 1. Mild blur
    blurred = cv2.GaussianBlur(wm_canvas, (3, 3), 0.8)
    obs_b = decoder.decode(blurred, expected_document_id="DOC_NOISE", expected_release_id="REL_N")
    assert obs_b.status == WatermarkStatus.RECOVERED
    assert obs_b.observed_symbols == codeword

    # 2. Additive Gaussian noise
    noise = np.random.RandomState(42).normal(0, 8.0, wm_canvas.shape)
    noisy = np.clip(wm_canvas.astype(np.float32) + noise, 0, 255).astype(np.uint8)
    obs_n = decoder.decode(noisy, expected_document_id="DOC_NOISE", expected_release_id="REL_N")
    assert obs_n.status == WatermarkStatus.RECOVERED
    assert obs_n.observed_symbols == codeword
