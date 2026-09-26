"""
SIH26237 - Large Negative Corpus & False Positive Rate Benchmark Tests
Evaluates a diverse corpus of 50+ unwatermarked, blank, noise, natural, damaged,
and mismatched documents to rigorously verify empirical 0.0% false attribution rate.
"""

import pytest
import numpy as np
import cv2

from core.watermark import (
    PrintCameraWatermarkEncoder,
    PrintCameraWatermarkDecoder,
    WatermarkTraceabilityAdapter,
    WatermarkPayload,
    WatermarkStatus,
    CanonicalCanvasSpec,
    GeometricSynchronizer,
)
from core.traceability import TardosTraceabilityProvider
from core.traceability.tardos import AccusationStatus


@pytest.fixture
def tardos_provider():
    return TardosTraceabilityProvider(
        coalition_size=2,
        false_accusation_epsilon=0.01,
        kappa_factor=5.0,
        recipient_count_hint=5
    )


@pytest.fixture
def recipients():
    return ["alice", "bob", "charlie", "david", "eve"]


def generate_negative_corpus():
    """Generates a list of 50 diverse negative / adversarial images."""
    corpus = []

    # 1. Blank solid color fields (5 images)
    for val, name in [(255, "pure_white"), (0, "pure_black"), (128, "medium_gray"), (240, "off_white"), (60, "dark_gray")]:
        img = np.ones((1000, 800, 3), dtype=np.uint8) * val
        corpus.append((f"solid_{name}", img, "DOC_TARGET", "REL_01"))

    # 2. Random Gaussian noise fields at different seeds & sigmas (10 images)
    for seed in range(10):
        rng = np.random.RandomState(1000 + seed)
        noise = rng.normal(128, 20 + seed * 5, (1000, 800, 3))
        img = np.clip(noise, 0, 255).astype(np.uint8)
        corpus.append((f"gaussian_noise_seed_{seed}", img, "DOC_TARGET", "REL_01"))

    # 3. Unwatermarked text & business documents (10 variations)
    for i in range(10):
        img = np.ones((1000, 800, 3), dtype=np.uint8) * 245
        cv2.putText(img, f"CORPORATE FINANCIAL REPORT {2020 + i}", (100, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (30, 30, 30), 2)
        for y in range(220, 850, 40):
            cv2.line(img, (100, y), (700, y), (200, 200, 200), 1)
        corpus.append((f"unwatermarked_doc_{i}", img, "DOC_TARGET", "REL_01"))

    # 4. Partial ArUco marker placements (< 3 markers) (10 variations)
    sync = GeometricSynchronizer(CanonicalCanvasSpec(width=800, height=1000))
    for i in range(10):
        base = np.ones((1000, 800, 3), dtype=np.uint8) * 250
        anchored = sync.embed_fiducial_anchors(base)
        # Destroy 2 or 3 markers randomly
        if i % 2 == 0:
            anchored[0:120, 0:120] = 255          # Erase TL
            anchored[880:1000, 680:800] = 255     # Erase BR
        else:
            anchored[0:120, 680:800] = 255        # Erase TR
            anchored[880:1000, 0:120] = 255       # Erase BL
            anchored[0:120, 0:120] = 255          # Erase TL
        corpus.append((f"partial_aruco_{i}", anchored, "DOC_TARGET", "REL_01"))

    # 5. Wrong document & release transplantation (10 variations)
    encoder = PrintCameraWatermarkEncoder()
    for i in range(10):
        base = np.ones((1000, 800, 3), dtype=np.uint8) * 240
        payload = WatermarkPayload(
            document_id=f"FOREIGN_DOC_{i}",
            release_id=f"FOREIGN_REL_{i}",
            codeword=[1, 0, 1, 0] * 32
        )
        wm = encoder.encode(base, payload)
        # Query with expected DOC_TARGET instead of FOREIGN_DOC_i
        corpus.append((f"transplanted_doc_{i}", wm, "DOC_TARGET", "REL_01"))

    # 6. Heavily scrubbed/damaged watermarked pages (5 variations)
    for i in range(5):
        base = np.ones((1000, 800, 3), dtype=np.uint8) * 240
        payload = WatermarkPayload(
            document_id="DOC_TARGET",
            release_id="REL_01",
            codeword=[1, 1, 0, 0] * 32
        )
        wm = encoder.encode(base, payload)
        # Heavy central wipe
        wm[200:800, 150:650] = 255
        corpus.append((f"scrubbed_doc_{i}", wm, "DOC_TARGET", "REL_01"))

    return corpus


def test_large_negative_corpus_zero_false_accusations(tardos_provider, recipients):
    """
    Evaluates all 50 negative corpus samples.
    Asserts 100% fail-closed abstention and 0 false accusations across the entire corpus.
    """
    decoder = PrintCameraWatermarkDecoder()
    adapter = WatermarkTraceabilityAdapter(tardos_provider)

    corpus = generate_negative_corpus()
    assert len(corpus) >= 50

    false_accusations = 0
    clean_abstentions = 0

    for test_name, img, exp_doc, exp_rel in corpus:
        obs = decoder.decode(img, expected_document_id=exp_doc, expected_release_id=exp_rel, expected_codeword_length=128)
        result = adapter.evaluate_observation(
            observation=obs,
            all_recipient_ids=recipients,
            document_id=exp_doc,
            release_id=exp_rel
        )

        # Verification rules:
        # 1. Status must NEVER be RECOVERED on negative samples
        assert obs.status in (WatermarkStatus.NO_SIGNAL, WatermarkStatus.INVALID, WatermarkStatus.PARTIAL), \
            f"Sample {test_name} unexpectedly recovered with status {obs.status}"

        # 2. Forensic accused list must be empty
        if len(result.accused_recipients) > 0:
            false_accusations += 1

        if result.attribution_status in (AccusationStatus.NO_SIGNAL, AccusationStatus.INSUFFICIENT_EVIDENCE):
            clean_abstentions += 1

        assert len(result.accused_recipients) == 0, f"False accusation produced on negative sample {test_name}!"
        assert result.fused_confidence == 0.0

    assert false_accusations == 0
    assert clean_abstentions == len(corpus)
