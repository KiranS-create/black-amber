"""
SIH26237 - Full Watermark-to-Tardos Traceability Integration Tests
Validates the complete pipeline:
Tardos Codeword Issuance -> Watermark Embedding -> Physical Simulation ->
Watermark Decoding -> Evidence Adapter -> Tardos Accusation.
"""

import pytest
import numpy as np
import cv2

from core.traceability import TardosTraceabilityProvider
from core.traceability.tardos import AccusationStatus
from core.watermark import (
    PrintCameraWatermarkEncoder,
    PrintCameraWatermarkDecoder,
    WatermarkTraceabilityAdapter,
    WatermarkPayload,
    WatermarkStatus,
)
from attacks.physical.simulation import PrintCameraSimulationAttack


@pytest.fixture
def recipients():
    return ["alice", "bob", "charlie", "david", "eve"]


@pytest.fixture
def tardos_provider():
    return TardosTraceabilityProvider(
        coalition_size=2,
        false_accusation_epsilon=0.01,
        kappa_factor=5.0,
        recipient_count_hint=5
    )



@pytest.fixture
def document_canvas():
    canvas = np.ones((1000, 800, 3), dtype=np.uint8) * 240
    cv2.putText(canvas, "INTELLIGENCE ESTIMATE 2026", (150, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (20, 20, 20), 2)
    cv2.putText(canvas, "Recipient Copy for Authorized Review", (150, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (60, 60, 60), 1)
    for y in range(270, 750, 40):
        cv2.line(canvas, (140, y), (660, y), (210, 210, 210), 1)
    return canvas


def test_end_to_end_single_recipient_physical_attribution(
    tardos_provider, recipients, document_canvas
):
    """
    Verifies that a recipient-specific copy for 'alice', subjected to compound
    PrintCameraSimulationAttack, is accurately decoded and solely attributes 'alice'.
    """
    doc_id = "DOC_INTEG_01"
    rel_id = "REL_2026_A"

    # 1. Issue Tardos marker for Alice
    marker_alice = tardos_provider.issue_marker(doc_id, rel_id, "alice", "doc_hash_1234")
    alice_codeword = marker_alice.metadata["tardos_codeword"]
    m = len(alice_codeword)

    # 2. Watermark embedding
    encoder = PrintCameraWatermarkEncoder()
    decoder = PrintCameraWatermarkDecoder()
    adapter = WatermarkTraceabilityAdapter(tardos_provider)

    payload = WatermarkPayload(document_id=doc_id, release_id=rel_id, codeword=alice_codeword)
    wm_bytes = encoder.encode(document_canvas, payload, as_bytes=True, format="PNG")

    # 3. Simulate physical print-camera capture
    attack = PrintCameraSimulationAttack()
    attack_output = attack._execute_transform(wm_bytes, attack.DEFAULT_PARAMETERS, seed=42)

    # 4. Decode observation from simulated capture
    obs = decoder.decode(
        attack_output.artifact_bytes,
        expected_document_id=doc_id,
        expected_release_id=rel_id,
        codeword_length_hint=m
    )
    assert obs.status == WatermarkStatus.RECOVERED
    assert obs.observed_symbols == alice_codeword

    # 5. Evaluate forensic attribution via Adapter
    result = adapter.evaluate_observation(
        observation=obs,
        all_recipient_ids=recipients,
        document_id=doc_id,
        release_id=rel_id
    )

    assert result.attribution_status in (AccusationStatus.ATTRIBUTED, AccusationStatus.COLLUSION_DETECTED)
    assert "alice" in result.accused_recipients
    assert len(result.accused_recipients) == 1
    assert result.fused_confidence > 0.60
    assert result.scores["alice"] >= result.threshold

    # Innocent recipients must have scores below threshold
    for innocent in ["bob", "charlie", "david", "eve"]:
        assert innocent not in result.accused_recipients
        assert result.scores[innocent] < result.threshold


def test_clean_document_attribution_abstains(tardos_provider, recipients, document_canvas):
    """
    Verifies that an unmarked document produces NO_SIGNAL and zeroes out
    all forensic accusation confidences.
    """
    decoder = PrintCameraWatermarkDecoder()
    adapter = WatermarkTraceabilityAdapter(tardos_provider)

    # Decode completely clean document
    obs = decoder.decode(document_canvas, expected_document_id="DOC_UNMARKED", expected_release_id="REL_01")
    assert obs.status == WatermarkStatus.NO_SIGNAL

    result = adapter.evaluate_observation(
        observation=obs,
        all_recipient_ids=recipients,
        document_id="DOC_UNMARKED",
        release_id="REL_01"
    )

    assert result.watermark_status == WatermarkStatus.NO_SIGNAL
    assert result.attribution_status == AccusationStatus.NO_SIGNAL
    assert len(result.accused_recipients) == 0
    assert result.fused_confidence == 0.0
