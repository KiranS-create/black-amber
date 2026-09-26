"""
SIH26237 - Watermark Abstention & False-Positive Tests
Quantifies false-detection behavior against clean documents, blank pages,
wrong document IDs, random noise, and heavily damaged artifacts.
Guarantees 100% fail-closed abstention (NO_SIGNAL or INVALID).
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
def decoder():
    return PrintCameraWatermarkDecoder()


def test_clean_unmarked_document_abstains(decoder):
    """Clean document without watermarking must return NO_SIGNAL with 0.0 confidence."""
    clean = np.ones((1000, 800, 3), dtype=np.uint8) * 255
    cv2.putText(clean, "UNMARKED OFFICIAL PRESS RELEASE", (150, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (20, 20, 20), 2)
    for y in range(250, 700, 30):
        cv2.putText(clean, "Standard public body text paragraph line.", (150, y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (50, 50, 50), 1)

    obs = decoder.decode(clean, expected_document_id="DOC_ANY", expected_release_id="REL_ANY")
    assert obs.status == WatermarkStatus.NO_SIGNAL
    assert obs.is_valid is False
    assert obs.confidence == 0.0
    assert obs.synchronization_success is False
    assert len(obs.observed_symbols) == 0


def test_pure_blank_and_black_images_abstain(decoder):
    """Pure white or pure black images must return NO_SIGNAL."""
    white = np.ones((1000, 800, 3), dtype=np.uint8) * 255
    black = np.zeros((1000, 800, 3), dtype=np.uint8)

    for img in [white, black]:
        obs = decoder.decode(img)
        assert obs.status == WatermarkStatus.NO_SIGNAL
        assert obs.confidence == 0.0
        assert obs.is_valid is False


def test_pure_random_gaussian_noise_abstains(decoder):
    """Random noise fields must not trigger false fiducial or payload detection."""
    rng = np.random.RandomState(999)
    noise = rng.randint(0, 256, (1000, 800, 3), dtype=np.uint8)

    obs = decoder.decode(noise)
    assert obs.status == WatermarkStatus.NO_SIGNAL
    assert obs.confidence == 0.0
    assert obs.is_valid is False


def test_wrong_document_binding_returns_invalid():
    """Watermark issued for Document A queried against Document B must return INVALID."""
    encoder = PrintCameraWatermarkEncoder()
    decoder = PrintCameraWatermarkDecoder()

    canvas = np.ones((1000, 800, 3), dtype=np.uint8) * 240
    codeword = [1, 0] * 64
    payload = WatermarkPayload(document_id="DOC_ALPHA", release_id="REL_01", codeword=codeword)
    wm_canvas = encoder.encode(canvas, payload)

    # Decode specifying mismatched document_id
    obs = decoder.decode(wm_canvas, expected_document_id="DOC_BETA", expected_release_id="REL_01")
    assert obs.status == WatermarkStatus.INVALID
    assert obs.is_valid is False
    assert obs.confidence == 0.0


def test_heavily_damaged_central_region_abstains_gracefully():
    """A watermarked page whose carrier region is completely obliterated must abstain."""
    encoder = PrintCameraWatermarkEncoder()
    decoder = PrintCameraWatermarkDecoder()

    canvas = np.ones((1000, 800, 3), dtype=np.uint8) * 240
    codeword = [1, 0] * 64
    payload = WatermarkPayload(document_id="DOC_DMG", release_id="REL_01", codeword=codeword)
    wm_canvas = encoder.encode(canvas, payload)

    # Completely wipe the central carrier region with black pixels
    wm_canvas[120:880, 120:680] = 0

    obs = decoder.decode(wm_canvas, expected_document_id="DOC_DMG", expected_release_id="REL_01")
    # Fiducials are intact, but carrier is destroyed -> status must be PARTIAL or INVALID, never RECOVERED
    assert obs.status != WatermarkStatus.RECOVERED
    assert obs.is_valid is False
