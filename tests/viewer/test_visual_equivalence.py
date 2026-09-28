"""
SIH26237 - Visual Equivalence Tests
Validates that dynamic decryption watermarking guarantees visual equivalence:
- SSIM >= 0.98 across all recipient instances (Alice, Bob, Charlie)
- PSNR > 38.0 dB (or >= 35.0 dB)
- Cross-recipient visual equivalence (Alice copy vs Bob copy)
- Cryptographic distinction: identical visual appearance, completely distinct forensic payloads
"""

import pytest
import hashlib
import numpy as np
import cv2

from core.watermark.pipeline import CanonicalCanvasSpec, GeometricSynchronizer
from core.watermark.carrier import CarrierConfig
from core.watermark.dynamic import (
    generate_dynamic_watermark,
    DynamicWatermarkEngine,
    compute_visual_equivalence_metrics,
)


def _generate_synthetic_document_image(width: int = 800, height: int = 1000) -> np.ndarray:
    """Creates a high-contrast document image simulating scanned text and headers."""
    canvas = np.full((height, width), 245, dtype=np.uint8)

    # Header line
    cv2.rectangle(canvas, (120, 80), (680, 110), (40,), -1)
    cv2.putText(canvas, "CONFIDENTIAL FORENSIC REPORT", (140, 102), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,), 2)

    # Simulated text lines within active content margins
    for y in range(150, 850, 30):
        cv2.line(canvas, (130, y), (670, y), (50,), 2)
        cv2.line(canvas, (130, y + 8), (620, y + 8), (80,), 1)

    return canvas


def test_visual_equivalence_alice_bob_charlie():
    spec = CanonicalCanvasSpec()
    sync = GeometricSynchronizer(spec)
    cfg = CarrierConfig(embedding_strength_alpha=1.0)
    engine = DynamicWatermarkEngine(canvas_spec=spec, carrier_config=cfg)

    raw_base = _generate_synthetic_document_image(spec.width, spec.height)
    base_image = sync.embed_fiducial_anchors(raw_base)
    doc_hash = hashlib.sha256(base_image.tobytes()).hexdigest()

    recipients = ["rec_alice", "rec_bob", "rec_charlie"]
    watermarked_instances = {}
    dynamic_identities = {}


    for rec_id in recipients:
        dyn_id = generate_dynamic_watermark(
            document_root_hash=doc_hash,
            recipient_id=rec_id,
            session_id=f"ses_{rec_id}",
            event_id=f"evt_{rec_id}",
            copy_id=f"cpy_{rec_id}",
        )
        dynamic_identities[rec_id] = dyn_id
        wm_bytes = engine.embed_watermark(
            carrier_input=base_image,
            dynamic_identity=dyn_id,
            document_id="doc_demo_root",
            release_id="rel_demo_2026",
            as_bytes=True,
        )
        # Decode bytes back to numpy array for metric calculation
        nparr = np.frombuffer(wm_bytes, np.uint8)
        img_np = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        watermarked_instances[rec_id] = img_np

    # 1. Verify metrics against reference base document
    for rec_id, img_np in watermarked_instances.items():
        metrics = compute_visual_equivalence_metrics(base_image, img_np)
        assert metrics["ssim"] >= 0.98, f"SSIM failed for {rec_id}: {metrics['ssim']}"
        assert metrics["psnr_db"] >= 35.0, f"PSNR failed for {rec_id}: {metrics['psnr_db']}"
        assert metrics["is_visually_equivalent"] is True

    # 2. Verify cross-recipient visual equivalence (Alice vs Bob, Bob vs Charlie)
    alice_img = watermarked_instances["rec_alice"]
    bob_img = watermarked_instances["rec_bob"]
    charlie_img = watermarked_instances["rec_charlie"]

    cross_metrics_ab = compute_visual_equivalence_metrics(alice_img, bob_img)
    cross_metrics_bc = compute_visual_equivalence_metrics(bob_img, charlie_img)

    assert cross_metrics_ab["ssim"] >= 0.98
    assert cross_metrics_ab["psnr_db"] >= 35.0
    assert cross_metrics_bc["ssim"] >= 0.98
    assert cross_metrics_bc["psnr_db"] >= 35.0

    # 3. Verify cryptographic payload divergence
    assert dynamic_identities["rec_alice"].token != dynamic_identities["rec_bob"].token
    assert dynamic_identities["rec_alice"].commitment != dynamic_identities["rec_bob"].commitment
    assert dynamic_identities["rec_alice"].codeword != dynamic_identities["rec_bob"].codeword


def test_visual_metrics_identical_images():
    img = np.full((300, 300), 128, dtype=np.uint8)
    metrics = compute_visual_equivalence_metrics(img, img)
    assert metrics["ssim"] == 1.0
    assert metrics["psnr_db"] == 100.0
    assert metrics["max_diff"] == 0.0
    assert metrics["is_visually_equivalent"] is True
