"""
SIH26237 - Dynamic Decryption Watermark Tests
Validates:
- Uniqueness across recipients and sessions
- Salted commitment verification and hiding
- Transplantation resistance & domain separation
- Reed-Solomon / DSSS carrier embedding and recovery
"""

import pytest
import os
import hashlib
import numpy as np
from PIL import Image

from core.watermark.dynamic import (
    DynamicWatermarkIdentity,
    generate_dynamic_watermark,
    verify_dynamic_watermark_commitment,
    derive_dynamic_codeword,
    DynamicWatermarkEngine,
    compute_visual_equivalence_metrics,
)


def test_dynamic_watermark_uniqueness_across_recipients():
    doc_hash = hashlib.sha256(b"Confidential Board Resolution 2026").hexdigest()
    
    wm_alice = generate_dynamic_watermark(
        document_root_hash=doc_hash,
        recipient_id="rec_alice",
        session_id="ses_001",
        event_id="evt_001",
        copy_id="cpy_001",
    )
    wm_bob = generate_dynamic_watermark(
        document_root_hash=doc_hash,
        recipient_id="rec_bob",
        session_id="ses_001",
        event_id="evt_001",
        copy_id="cpy_001",
    )

    assert wm_alice.token != wm_bob.token
    assert wm_alice.commitment != wm_bob.commitment
    assert wm_alice.codeword != wm_bob.codeword
    # Bit distance should be close to random (~50% difference)
    diff_bits = sum(a != b for a, b in zip(wm_alice.codeword, wm_bob.codeword))
    assert diff_bits > 40, f"Expected uncorrelated codewords, got diff: {diff_bits}"


def test_dynamic_watermark_uniqueness_across_sessions_same_recipient():
    doc_hash = hashlib.sha256(b"Confidential Board Resolution 2026").hexdigest()

    wm_ses1 = generate_dynamic_watermark(
        document_root_hash=doc_hash,
        recipient_id="rec_alice",
        session_id="ses_alice_001",
        event_id="evt_alice_001",
        copy_id="cpy_alice_001",
    )
    wm_ses2 = generate_dynamic_watermark(
        document_root_hash=doc_hash,
        recipient_id="rec_alice",
        session_id="ses_alice_002",
        event_id="evt_alice_002",
        copy_id="cpy_alice_001",
    )

    assert wm_ses1.token != wm_ses2.token
    assert wm_ses1.commitment != wm_ses2.commitment
    assert wm_ses1.codeword != wm_ses2.codeword


def test_commitment_hiding_and_verification():
    doc_hash = hashlib.sha256(b"Payload Data").hexdigest()
    wm = generate_dynamic_watermark(
        document_root_hash=doc_hash,
        recipient_id="rec_alice",
        session_id="ses_001",
        event_id="evt_001",
        copy_id="cpy_001",
    )

    # Valid verification
    assert verify_dynamic_watermark_commitment(wm.token, wm.salt, wm.commitment) is True

    # Tampered token
    tampered_token = ("0" if wm.token[0] != "0" else "1") + wm.token[1:]
    assert verify_dynamic_watermark_commitment(tampered_token, wm.salt, wm.commitment) is False

    # Tampered salt
    tampered_salt = ("0" if wm.salt[0] != "0" else "1") + wm.salt[1:]
    assert verify_dynamic_watermark_commitment(wm.token, tampered_salt, wm.commitment) is False


def test_codeword_derivation_determinism_and_length():
    token = "a" * 64
    cw1 = derive_dynamic_codeword(token, length=128)
    cw2 = derive_dynamic_codeword(token, length=128)

    assert len(cw1) == 128
    assert cw1 == cw2
    assert all(b in (0, 1) for b in cw1)
    # Check balance of 0s and 1s
    num_ones = sum(cw1)
    assert 40 <= num_ones <= 88, f"Unbalanced codeword: {num_ones} ones"


def test_transplantation_resistance_and_domain_separation():
    doc_hash1 = hashlib.sha256(b"Doc A").hexdigest()
    doc_hash2 = hashlib.sha256(b"Doc B").hexdigest()

    wm1 = generate_dynamic_watermark(doc_hash1, "rec_alice", "ses_1", "evt_1", "cpy_1", nonce="static_nonce")
    wm2 = generate_dynamic_watermark(doc_hash2, "rec_alice", "ses_1", "evt_1", "cpy_1", nonce="static_nonce")

    assert wm1.token != wm2.token
    assert wm1.codeword != wm2.codeword


def test_embedding_and_decoding_pipeline():
    engine = DynamicWatermarkEngine()
    # Create synthetic test canvas (600x600 grayscale with texture)
    arr = np.full((600, 600), 200, dtype=np.uint8)
    arr[100:500:20, :] = 50  # Add horizontal stripes (document-like content)

    doc_hash = hashlib.sha256(b"Test Artifact").hexdigest()
    dyn_id = generate_dynamic_watermark(
        document_root_hash=doc_hash,
        recipient_id="rec_bob",
        session_id="ses_bob_100",
        event_id="evt_bob_100",
        copy_id="cpy_bob_100",
    )

    embedded_bytes = engine.embed_watermark(
        carrier_input=arr,
        dynamic_identity=dyn_id,
        document_id="doc_test_001",
        release_id="rel_test_001",
        as_bytes=True,
    )
    assert isinstance(embedded_bytes, bytes)
    assert len(embedded_bytes) > 0

    # Decode
    success, symbols, telemetry = engine.decode_watermark(
        captured_input=embedded_bytes,
        expected_document_id="doc_test_001",
        expected_release_id="rel_test_001",
        expected_codeword_length=128
    )
    assert success is True
    assert len(symbols) == 128
    assert symbols == dyn_id.codeword
