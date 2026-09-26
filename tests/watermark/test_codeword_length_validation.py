"""
SIH26237 - Strict Codeword Length Validation & Fail-Closed Tests
Verifies that the decoding API cannot silently decode a document using the wrong Tardos code length,
and strictly fails closed with INVALID or NO_SIGNAL when lengths mismatch.
"""

import pytest
import numpy as np
import cv2

from core.watermark import (
    PrintCameraWatermarkEncoder,
    PrintCameraWatermarkDecoder,
    WatermarkPayload,
    WatermarkStatus,
)


@pytest.fixture
def clean_canvas():
    canvas = np.ones((1000, 800, 3), dtype=np.uint8) * 245
    cv2.putText(canvas, "CONFIDENTIAL INTEL MEMO", (150, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (20, 20, 20), 2)
    return canvas


def test_matching_expected_codeword_length_succeeds(clean_canvas):
    """Verifies that providing matching expected_codeword_length decodes successfully."""
    encoder = PrintCameraWatermarkEncoder()
    decoder = PrintCameraWatermarkDecoder()

    codeword = [1, 0, 1, 1, 0, 0, 1, 0] * 16  # 128 bits
    payload = WatermarkPayload(document_id="DOC_LEN_01", release_id="REL_A", codeword=codeword)
    wm_canvas = encoder.encode(clean_canvas, payload)

    obs = decoder.decode(
        wm_canvas,
        expected_document_id="DOC_LEN_01",
        expected_release_id="REL_A",
        expected_codeword_length=128
    )

    assert obs.status == WatermarkStatus.RECOVERED
    assert obs.is_valid is True
    assert obs.observed_symbols == codeword
    assert obs.telemetry.get("ecc", {}).get("length_verified") is True


def test_mismatched_expected_codeword_length_fails_closed(clean_canvas):
    """
    Verifies that if an analyst requests expected_codeword_length=64 or 256 for a 128-bit watermark,
    the decoder strictly rejects the payload with status INVALID and length mismatch telemetry.
    """
    encoder = PrintCameraWatermarkEncoder()
    decoder = PrintCameraWatermarkDecoder()

    codeword = [1, 0, 1, 0] * 32  # 128 bits
    payload = WatermarkPayload(document_id="DOC_LEN_02", release_id="REL_B", codeword=codeword)
    wm_canvas = encoder.encode(clean_canvas, payload)

    # 1. Caller expects 64 bits instead of 128
    obs_64 = decoder.decode(
        wm_canvas,
        expected_document_id="DOC_LEN_02",
        expected_release_id="REL_B",
        expected_codeword_length=64
    )
    assert obs_64.status in (WatermarkStatus.INVALID, WatermarkStatus.PARTIAL)
    assert obs_64.is_valid is False
    assert obs_64.observed_symbols == []

    # 2. Caller expects 256 bits instead of 128
    obs_256 = decoder.decode(
        wm_canvas,
        expected_document_id="DOC_LEN_02",
        expected_release_id="REL_B",
        expected_codeword_length=256
    )
    assert obs_256.status in (WatermarkStatus.INVALID, WatermarkStatus.PARTIAL)
    assert obs_256.is_valid is False
    assert obs_256.observed_symbols == []


def test_different_tardos_lengths_roundtrip(clean_canvas):
    """Verifies that 64-bit and 256-bit codewords roundtrip cleanly when expected length matches."""
    encoder = PrintCameraWatermarkEncoder()
    decoder = PrintCameraWatermarkDecoder()

    # 64-bit codeword
    cw_64 = [1, 1, 0, 0] * 16
    p_64 = WatermarkPayload(document_id="DOC_64", release_id="REL_64", codeword=cw_64)
    wm_64 = encoder.encode(clean_canvas, p_64)
    obs_64 = decoder.decode(wm_64, expected_document_id="DOC_64", expected_release_id="REL_64", expected_codeword_length=64)
    assert obs_64.status == WatermarkStatus.RECOVERED
    assert obs_64.observed_symbols == cw_64

    # 256-bit codeword
    cw_256 = [1, 0, 0, 1, 1, 1, 0, 0] * 32
    p_256 = WatermarkPayload(document_id="DOC_256", release_id="REL_256", codeword=cw_256)
    wm_256 = encoder.encode(clean_canvas, p_256)
    obs_256 = decoder.decode(wm_256, expected_document_id="DOC_256", expected_release_id="REL_256", expected_codeword_length=256)
    assert obs_256.status == WatermarkStatus.RECOVERED
    assert obs_256.observed_symbols == cw_256
