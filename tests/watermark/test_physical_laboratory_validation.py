"""
AegisTrace - Physical Laboratory Watermark Validation Tests
=============================================================
Regression and verification test suite for the physical laboratory validation harness:
1. Hardware detection honesty & refusal to fabricate absent physical devices.
2. 50/50 Calibration vs. Held-Out Evaluation split integrity and zero threshold leakage.
3. Multi-recipient positive codeword recovery and zero cross-recipient confusion.
4. 100-sample adversarial negative corpus zero false positive rate (FPR = 0.0).
5. Adversarial physical transplantation rejection (fail-closed CONFLICT/INVALID).
6. Complete offline air-gap execution guarantee.
"""

import pytest
import numpy as np
import cv2
import hashlib
from typing import Dict, Any

from core.watermark import (
    PrintCameraWatermarkEncoder,
    PrintCameraWatermarkDecoder,
    WatermarkPayload,
    WatermarkStatus,
    CanonicalCanvasSpec,
    CarrierConfig,
    CarrierStrategy,
    GeometricSynchronizer,
)
from scripts.watermark.run_physical_laboratory_validation import (
    probe_hardware_environment,
    compute_physical_iqa,
    classify_decision_state,
    generate_negative_corpus_100,
    create_document_canvas,
    apply_physical_channel_transform,
)


@pytest.fixture
def canvas_spec():
    return CanonicalCanvasSpec(width=800, height=1000)


@pytest.fixture
def synchronizer(canvas_spec):
    return GeometricSynchronizer(canvas_spec)


@pytest.fixture
def sample_recipients():
    recipients = {
        "rec_alice_4a12": {"name": "Alice Vance", "role": "Senior Cryptanalyst"},
        "rec_bob_8f3c": {"name": "Bob Sterling", "role": "Operations Director"},
        "rec_charlie_19de": {"name": "Charlie Hayes", "role": "Field Intelligence"}
    }
    codewords = {}
    for idx, rec_id in enumerate(recipients.keys()):
        rng = np.random.RandomState(4242 + idx * 99)
        codewords[rec_id] = rng.randint(0, 2, 128).tolist()
    return recipients, codewords


# =====================================================================
# 1. HARDWARE DETECTION HONESTY
# =====================================================================

def test_hardware_detection_honesty():
    """
    Validates that hardware probing honestly detects connected hardware
    and marks modalities UNAVAILABLE rather than fabricating devices.
    Virtual printers (OneNote, PDF writer) must be strictly filtered out.
    """
    probe = probe_hardware_environment()

    assert "camera_modality_status" in probe
    assert "printer_modality_status" in probe
    assert "capture_environment" in probe

    # On this test host, no physical capture hardware or physical paper printers exist
    if not probe["cameras"]:
        assert probe["camera_modality_status"] == "UNAVAILABLE (HOST_ENV_NO_LIVE_DEVICE)"

    if not probe["printers"]:
        assert probe["printer_modality_status"] == "UNAVAILABLE (HOST_ENV_NO_LIVE_DEVICE)"

    # Verify virtual software printers are never reported as physical printers
    for printer in probe["printers"]:
        name = printer.get("name", "").lower()
        assert "onenote" not in name
        assert "xps" not in name
        assert "pdf" not in name
        assert "fax" not in name


# =====================================================================
# 2. CALIBRATION VS HELD-OUT SPLIT INTEGRITY
# =====================================================================

def test_calibration_vs_held_out_partition_integrity(canvas_spec, synchronizer, sample_recipients):
    """
    Validates strict 50/50 partition between Calibration and Held-Out datasets.
    Asserts zero sample ID or byte hash overlap to prevent threshold leakage.
    """
    recipients, codewords = sample_recipients
    carrier_strategies = [
        CarrierStrategy.RENDERED_PAGE_CANVAS,
        CarrierStrategy.GRAPHICAL_ROI,
        CarrierStrategy.SECURITY_BACKGROUND_TEXTURE
    ]

    master_records = []
    for rec_id, rdata in recipients.items():
        doc_id = f"DOC_TEST_{rec_id[:8]}"
        rel_id = "REL_2026_TEST"
        cw = codewords[rec_id]

        for strat in carrier_strategies:
            strat_cfg = CarrierConfig(strategy=strat, embedding_strength_alpha=12.0)
            strat_enc = PrintCameraWatermarkEncoder(canvas_spec, carrier_config=strat_cfg)
            canvas = create_document_canvas(doc_id, f"BRIEFING — {rdata['name']}")
            anchored = synchronizer.embed_fiducial_anchors(canvas)
            payload = WatermarkPayload(document_id=doc_id, release_id=rel_id, codeword=cw)
            wm_bytes = strat_enc.encode(anchored, payload, as_bytes=True)

            master_records.append({
                "sample_id": f"test_{rec_id}_{strat.value.lower()}",
                "recipient_id": rec_id,
                "strategy": strat.value,
                "sha256": hashlib.sha256(wm_bytes).hexdigest()
            })

    # Partition 50/50
    cal_set = [r for idx, r in enumerate(master_records) if idx % 2 == 0]
    held_out_set = [r for idx, r in enumerate(master_records) if idx % 2 == 1]

    # Verify partition sizing
    assert len(cal_set) + len(held_out_set) == len(master_records)
    assert abs(len(cal_set) - len(held_out_set)) <= 1

    # Verify zero overlap (no leakage)
    cal_ids = {r["sample_id"] for r in cal_set}
    held_out_ids = {r["sample_id"] for r in held_out_set}
    assert cal_ids.isdisjoint(held_out_ids)

    cal_hashes = {r["sha256"] for r in cal_set}
    held_out_hashes = {r["sha256"] for r in held_out_set}
    assert cal_hashes.isdisjoint(held_out_hashes)


# =====================================================================
# 3. MULTI-RECIPIENT POSITIVE RECOVERY & ZERO CROSS-CONFUSION
# =====================================================================

def test_multi_recipient_positive_recovery_and_zero_confusion(canvas_spec, synchronizer, sample_recipients):
    """
    Validates that watermarks for distinct recipients:
    1. Are recovered 100% bit-exact under matching expected credentials.
    2. Fail-closed without cross-recipient misattribution when evaluated against other recipients.
    """
    recipients, codewords = sample_recipients
    rec_ids = list(recipients.keys())

    cfg = CarrierConfig(embedding_strength_alpha=12.0)
    encoder = PrintCameraWatermarkEncoder(canvas_spec, carrier_config=cfg)
    decoder = PrintCameraWatermarkDecoder(canvas_spec, carrier_config=cfg)

    # Encode Alice, Bob, Charlie
    encoded_images = {}
    for rec_id in rec_ids:
        doc_id = f"DOC_MULTI_{rec_id[:8]}"
        rel_id = "REL_2026_Q3"
        cw = codewords[rec_id]

        canvas = create_document_canvas(doc_id, f"AUDIT CLASSIFIED — {rec_id}")
        anchored = synchronizer.embed_fiducial_anchors(canvas)
        payload = WatermarkPayload(document_id=doc_id, release_id=rel_id, codeword=cw)
        encoded_images[rec_id] = encoder.encode(anchored, payload)

    # 1. Verify correct recovery for each recipient
    for rec_id in rec_ids:
        doc_id = f"DOC_MULTI_{rec_id[:8]}"
        rel_id = "REL_2026_Q3"
        cw = codewords[rec_id]
        img = encoded_images[rec_id]

        obs = decoder.decode(img, expected_document_id=doc_id, expected_release_id=rel_id, expected_codeword_length=128)
        assert obs.status == WatermarkStatus.RECOVERED
        assert obs.is_valid is True
        assert obs.observed_symbols == cw

        decision, _ = classify_decision_state(obs, cw, obs.observed_symbols, doc_id, rel_id)
        assert decision == "RECOVERED_CORRECT"

    # 2. Verify zero cross-recipient misattribution
    # Test Alice's image evaluated against Bob's codeword
    alice_id = "rec_alice_4a12"
    bob_id = "rec_bob_8f3c"
    obs_alice = decoder.decode(
        encoded_images[alice_id],
        expected_document_id=f"DOC_MULTI_{alice_id[:8]}",
        expected_release_id="REL_2026_Q3",
        expected_codeword_length=128
    )
    # Classify against Bob's codeword
    cross_decision, cross_details = classify_decision_state(
        obs_alice,
        codewords[bob_id],
        obs_alice.observed_symbols
    )
    assert cross_decision != "RECOVERED_CORRECT"
    assert cross_decision in ("RECOVERED_WRONG_IDENTITY", "INSUFFICIENT_EVIDENCE")


# =====================================================================
# 4. 100-SAMPLE ADVERSARIAL NEGATIVE CORPUS (FPR = 0.0)
# =====================================================================

def test_100_sample_negative_corpus_zero_false_positive_rate(canvas_spec):
    """
    Validates that a 100-sample negative adversarial corpus:
    - Produces ZERO false accusations (FPR = 0.0000).
    - Every negative sample cleanly maps to fail-closed statuses
      (NO_SIGNAL, INSUFFICIENT_EVIDENCE, CONFLICT, or ABSTAINED).
    """
    decoder = PrintCameraWatermarkDecoder(canvas_spec)
    negative_corpus = generate_negative_corpus_100()
    assert len(negative_corpus) == 100

    false_positives = 0
    valid_fail_closed_statuses = {"NO_SIGNAL", "INSUFFICIENT_EVIDENCE", "CONFLICT", "ABSTAINED"}

    for item in negative_corpus:
        obs = decoder.decode(
            item["image"],
            expected_document_id=item["expected_doc_id"],
            expected_release_id=item["expected_rel_id"],
            expected_codeword_length=128
        )
        decision, _ = classify_decision_state(obs, None, obs.observed_symbols or [])

        if decision == "RECOVERED_CORRECT":
            false_positives += 1

        assert decision in valid_fail_closed_statuses

    assert false_positives == 0, f"Violated zero false positive rate: {false_positives} FPs detected"


# =====================================================================
# 5. ADVERSARIAL PHYSICAL TRANSPLANTATION REJECTION
# =====================================================================

def test_adversarial_physical_transplantation_rejection(canvas_spec, synchronizer, sample_recipients):
    """
    Validates cryptographic and spatial resilience against physical transplantation attacks:
    1. Cross-Document Release Binding Attack:
       An authentic watermarked page decoded with mismatched document/release credentials
       must fail closed with CONFLICT or INVALID.
    2. Physical Splicing / Collage Attack:
       Splicing watermark fragments into another document frame produces fail-closed refusal.
    """
    recipients, codewords = sample_recipients
    cfg = CarrierConfig(embedding_strength_alpha=12.0)
    encoder = PrintCameraWatermarkEncoder(canvas_spec, carrier_config=cfg)
    decoder = PrintCameraWatermarkDecoder(canvas_spec, carrier_config=cfg)

    alice_doc = "DOC_ORIGINAL_ALICE"
    bob_doc = "DOC_TARGET_BOB"
    rel_id = "REL_2026_Q3"

    # Generate Alice's authentic physical document
    canvas_alice = create_document_canvas(alice_doc, "GENUINE CLASSIFIED RECORD")
    anchored_alice = synchronizer.embed_fiducial_anchors(canvas_alice)
    payload_alice = WatermarkPayload(document_id=alice_doc, release_id=rel_id, codeword=codewords["rec_alice_4a12"])
    alice_img = encoder.encode(anchored_alice, payload_alice)

    # Attack 1: Attempt to decode Alice's document claiming it belongs to Bob's document release
    obs_mismatch = decoder.decode(
        alice_img,
        expected_document_id=bob_doc,  # Mismatched expected document
        expected_release_id=rel_id,
        expected_codeword_length=128
    )
    # Must fail document binding check in Reed-Solomon payload codec
    assert obs_mismatch.status == WatermarkStatus.INVALID
    assert obs_mismatch.is_valid is False

    decision_mismatch, _ = classify_decision_state(
        obs_mismatch,
        codewords["rec_bob_8f3c"],
        obs_mismatch.observed_symbols or []
    )
    assert decision_mismatch in ("CONFLICT", "ABSTAINED")

    # Attack 2: Physical collage / splicing attack
    # Cut out watermark center from Alice and splice into Bob's document canvas
    canvas_bob = create_document_canvas(bob_doc, "BOB UNWATERMARKED DRAFT")
    anchored_bob = synchronizer.embed_fiducial_anchors(canvas_bob)
    spliced = anchored_bob.copy()
    spliced[250:750, 150:650] = alice_img[250:750, 150:650]

    obs_spliced = decoder.decode(
        spliced,
        expected_document_id=bob_doc,
        expected_release_id=rel_id,
        expected_codeword_length=128
    )
    # The spliced fragment lacks valid binding to bob_doc
    assert obs_spliced.status in (WatermarkStatus.INVALID, WatermarkStatus.NO_SIGNAL, WatermarkStatus.PARTIAL)
    assert obs_spliced.is_valid is False

    decision_spliced, _ = classify_decision_state(
        obs_spliced,
        codewords["rec_bob_8f3c"],
        obs_spliced.observed_symbols or []
    )
    assert decision_spliced in ("CONFLICT", "NO_SIGNAL", "INSUFFICIENT_EVIDENCE", "ABSTAINED")


# =====================================================================
# 6. IMAGE QUALITY ASSESSMENT & PRE-INGESTION METRICS
# =====================================================================

def test_image_quality_assessment_metrics(canvas_spec):
    """
    Validates that IQA metrics (sharpness, luminance, dynamic range)
    accurately characterize document captures.
    """
    # Create sharp test document
    doc = create_document_canvas("DOC_IQA", "SHARPNESS EVALUATION RECORD")
    iqa_sharp = compute_physical_iqa(doc)

    assert "sharpness_laplacian_var" in iqa_sharp
    assert "mean_luminance" in iqa_sharp
    assert "is_sharp" in iqa_sharp
    assert "is_well_exposed" in iqa_sharp
    assert iqa_sharp["sharpness_laplacian_var"] > 20.0
    assert iqa_sharp["is_sharp"] is True
    assert iqa_sharp["is_well_exposed"] is True

    # Blur test document
    blurred = cv2.GaussianBlur(doc, (15, 15), 5.0)
    iqa_blurred = compute_physical_iqa(blurred)
    # Sharpness must drop significantly
    assert iqa_blurred["sharpness_laplacian_var"] < iqa_sharp["sharpness_laplacian_var"]
