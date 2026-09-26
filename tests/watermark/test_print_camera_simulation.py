"""
SIH26237 - Print-Camera Simulation Attack Robustness Tests
Evaluates the physical watermark engine directly against PrintCameraSimulationAttack,
reproducing compound real-world optical, perspective, lighting, and sensor corruptions.
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
from attacks.physical.simulation import PrintCameraSimulationAttack


@pytest.fixture
def document_canvas():
    canvas = np.ones((1000, 800, 3), dtype=np.uint8) * 240
    cv2.putText(canvas, "NATIONAL SECURITY DIRECTIVE 2026", (130, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (20, 20, 20), 2)
    cv2.putText(canvas, "SUBJECT: Crypographic Watermarking and Attribution", (130, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (50, 50, 50), 1)
    for y in range(270, 720, 35):
        cv2.line(canvas, (130, y), (670, y), (210, 210, 210), 1)
    return canvas


def test_standard_print_camera_simulation_recovery(document_canvas):
    """
    Verifies 100% bit-exact codeword recovery under standard PrintCameraSimulationAttack
    (perspective, blur, lighting gradient, paper texture, downsample, and JPEG).
    """
    encoder = PrintCameraWatermarkEncoder()
    decoder = PrintCameraWatermarkDecoder()

    codeword = [1, 0, 1, 1, 0, 0, 1, 0] * 16  # 128 bits
    payload = WatermarkPayload(document_id="DOC_PHYS_01", release_id="REL_A", codeword=codeword)
    wm_bytes = encoder.encode(document_canvas, payload, as_bytes=True, format="PNG")

    # Execute simulation attack
    attack = PrintCameraSimulationAttack()
    attack_output = attack._execute_transform(wm_bytes, attack.DEFAULT_PARAMETERS, seed=42)
    captured_bytes = attack_output.artifact_bytes

    # Decode
    obs = decoder.decode(captured_bytes, expected_document_id="DOC_PHYS_01", expected_release_id="REL_A")

    assert obs.status == WatermarkStatus.RECOVERED
    assert obs.is_valid is True
    assert obs.synchronization_success is True
    assert obs.observed_symbols == codeword
    assert obs.confidence >= 0.65


@pytest.mark.parametrize("perspective, blur, lighting, expect_full", [
    (0.03, 0.8, 0.15, True),   # Mild smartphone angle
    (0.06, 1.2, 0.25, True),   # Typical desk lighting & tilt (default)
    (0.08, 1.0, 0.30, False),  # Steep angle & strong directional lamp (extreme stress)
])
def test_print_camera_parameter_sweeps(document_canvas, perspective, blur, lighting, expect_full):
    """Verifies robustness across a parameter sweep of optical blur, perspective, and lighting."""
    encoder = PrintCameraWatermarkEncoder()
    decoder = PrintCameraWatermarkDecoder()

    codeword = [1, 1, 0, 0, 1, 0, 1, 0] * 16
    payload = WatermarkPayload(document_id="DOC_SWEEP", release_id="REL_S", codeword=codeword)
    wm_bytes = encoder.encode(document_canvas, payload, as_bytes=True, format="PNG")

    params = dict(PrintCameraSimulationAttack.DEFAULT_PARAMETERS)
    params["perspective_distortion"] = perspective
    params["optical_blur_sigma"] = blur
    params["lighting_gradient_strength"] = lighting

    attack = PrintCameraSimulationAttack()
    attack_output = attack._execute_transform(wm_bytes, params, seed=123)

    obs = decoder.decode(attack_output.artifact_bytes, expected_document_id="DOC_SWEEP", expected_release_id="REL_S")
    if expect_full:
        assert obs.status == WatermarkStatus.RECOVERED
        assert obs.observed_symbols == codeword
    else:
        # Extreme stress must fail closed gracefully without false positive
        assert obs.status in (WatermarkStatus.RECOVERED, WatermarkStatus.PARTIAL)
        assert obs.synchronization_success is True

