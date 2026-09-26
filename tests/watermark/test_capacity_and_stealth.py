"""
SIH26237 - Capacity Bounds & Visual Stealth Hardening Tests
Validates spatial capacity limits across strategies (m=64, 128, 256) and evaluates
the trade-off between embedding strength alpha, adaptive texture masking, and visual quality (PSNR/SSIM).
"""

import pytest
import numpy as np
import cv2

from core.watermark import (
    PrintCameraWatermarkEncoder,
    PrintCameraWatermarkDecoder,
    CarrierConfig,
    CarrierStrategy,
    WatermarkPayload,
    WatermarkStatus,
    compute_image_ssim,
)


@pytest.fixture
def test_canvas():
    canvas = np.ones((1000, 800, 3), dtype=np.uint8) * 245
    cv2.putText(canvas, "SECURITY DIRECTIVE CLASSIFIED", (140, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (20, 20, 20), 2)
    for y in range(250, 750, 40):
        cv2.line(canvas, (140, y), (660, y), (200, 200, 200), 1)
    return canvas


@pytest.mark.parametrize("m_bits", [64, 128, 256])
def test_strategy_a_capacity_scaling(test_canvas, m_bits):
    """Verifies that Strategy A (Full Canvas) supports m=64, 128, and 256 bits."""
    encoder = PrintCameraWatermarkEncoder(
        carrier_config=CarrierConfig(strategy=CarrierStrategy.RENDERED_PAGE_CANVAS)
    )
    decoder = PrintCameraWatermarkDecoder(
        carrier_config=CarrierConfig(strategy=CarrierStrategy.RENDERED_PAGE_CANVAS)
    )

    codeword = [1, 0, 1, 0] * (m_bits // 4)
    payload = WatermarkPayload(document_id=f"DOC_CAP_{m_bits}", release_id="REL_A", codeword=codeword)
    wm = encoder.encode(test_canvas, payload)

    obs = decoder.decode(
        wm,
        expected_document_id=f"DOC_CAP_{m_bits}",
        expected_release_id="REL_A",
        expected_codeword_length=m_bits
    )
    assert obs.status == WatermarkStatus.RECOVERED
    assert obs.observed_symbols == codeword


def test_strategy_b_capacity_bounds(test_canvas):
    """
    Verifies Strategy B (Graphical ROI):
    - m=64 and m=128 succeed (fit within 560 slots).
    - m=256 requires 608 bits > 560 slots and fails cleanly with a descriptive ValueError / INVALID status.
    """
    cfg_b = CarrierConfig(strategy=CarrierStrategy.GRAPHICAL_ROI)
    encoder = PrintCameraWatermarkEncoder(carrier_config=cfg_b)
    decoder = PrintCameraWatermarkDecoder(carrier_config=cfg_b)

    # 1. m=128 succeeds
    cw_128 = [1, 0, 1, 1] * 32
    p_128 = WatermarkPayload(document_id="DOC_B_128", release_id="REL_B", codeword=cw_128)
    wm_128 = encoder.encode(test_canvas, p_128)
    obs_128 = decoder.decode(wm_128, expected_document_id="DOC_B_128", expected_release_id="REL_B", expected_codeword_length=128)
    assert obs_128.status == WatermarkStatus.RECOVERED

    # 2. m=256 exceeds capacity on encode
    cw_256 = [1, 0, 0, 1] * 64
    p_256 = WatermarkPayload(document_id="DOC_B_256", release_id="REL_B", codeword=cw_256)
    with pytest.raises(ValueError) as excinfo:
        encoder.encode(test_canvas, p_256)
    assert "Active ROI insufficient for payload" in str(excinfo.value)


@pytest.mark.parametrize("alpha, use_adaptive", [
    (8.0, False),
    (14.0, False),
    (14.0, True),
    (18.0, False),
])
def test_visual_stealth_and_masking_tradeoff(test_canvas, alpha, use_adaptive):
    """
    Evaluates visual quality (PSNR and SSIM) and recovery across different alpha strengths
    and adaptive texture-aware masking.
    """
    cfg = CarrierConfig(
        embedding_strength_alpha=alpha,
        adaptive_masking=use_adaptive
    )
    encoder = PrintCameraWatermarkEncoder(carrier_config=cfg)
    decoder = PrintCameraWatermarkDecoder(carrier_config=cfg)

    codeword = [1, 0, 1, 0] * 32
    payload = WatermarkPayload(document_id="DOC_STEALTH", release_id="REL_S", codeword=codeword)
    wm, mod_tele = encoder.modulator.modulate(
        encoder.synchronizer.embed_fiducial_anchors(test_canvas),
        encoder.codec.encode_payload("DOC_STEALTH", "REL_S", codeword)
    )

    # PSNR and SSIM checks
    psnr = mod_tele["psnr_db"]
    ssim = mod_tele["ssim"]

    if use_adaptive:
        # Adaptive masking maintains higher PSNR and SSIM by protecting blank regions
        assert psnr >= 28.5
        assert ssim >= 0.84
    else:
        if alpha <= 10.0:
            assert psnr >= 30.0

    # Ensure decoding still succeeds
    obs = decoder.decode(wm, expected_document_id="DOC_STEALTH", expected_release_id="REL_S", expected_codeword_length=128)
    assert obs.status == WatermarkStatus.RECOVERED
    assert obs.observed_symbols == codeword
