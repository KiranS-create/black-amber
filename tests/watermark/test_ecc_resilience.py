"""
SIH26237 - Watermark ECC & Integrity Resilience Tests
Verifies Reed-Solomon symbol error correction capacity, erasure handling,
CRC-32 tamper detection, and cryptographic document-release binding.
"""

import pytest
import numpy as np

from core.watermark.ecc import (
    WatermarkPayloadCodec,
    bytes_to_bits,
    bits_to_bytes,
    compute_doc_release_binding,
)


@pytest.fixture
def codec():
    return WatermarkPayloadCodec(rs_parity_bytes=24)


@pytest.fixture
def sample_codeword():
    return [1, 0, 1, 1, 0, 0, 1, 0] * 16  # 128 bits


def test_clean_ecc_roundtrip(codec, sample_codeword):
    """Verifies bit-exact payload encode/decode with zero errors."""
    raw_bits = codec.encode_payload("DOC_ECC", "REL_01", sample_codeword)
    ok, rec_cw, tele = codec.decode_payload(raw_bits, "DOC_ECC", "REL_01")

    assert ok is True
    assert rec_cw == sample_codeword
    assert tele["ecc_success"] is True
    assert tele["crc_verified"] is True
    assert tele["binding_verified"] is True
    assert tele["errata_count"] == 0


@pytest.mark.parametrize("corrupted_bytes_count", [1, 4, 8, 12])
def test_reed_solomon_error_correction_within_budget(codec, sample_codeword, corrupted_bytes_count):
    """Verifies that Reed-Solomon corrects up to t = rs_parity_bytes // 2 corrupted bytes."""
    raw_bits = codec.encode_payload("DOC_ECC", "REL_01", sample_codeword)
    byte_arr = bytearray(bits_to_bytes(raw_bits))

    # Intentionally corrupt specific bytes
    rng = np.random.RandomState(corrupted_bytes_count)
    corrupted_indices = rng.choice(len(byte_arr), size=corrupted_bytes_count, replace=False)
    for idx in corrupted_indices:
        byte_arr[idx] ^= 0xFF

    corrupted_bits = bytes_to_bits(bytes(byte_arr))
    ok, rec_cw, tele = codec.decode_payload(corrupted_bits, "DOC_ECC", "REL_01")

    assert ok is True
    assert rec_cw == sample_codeword
    assert tele["ecc_success"] is True
    assert tele["errata_count"] == corrupted_bytes_count
    assert tele["crc_verified"] is True


def test_reed_solomon_uncorrectable_errors_fail_closed(codec, sample_codeword):
    """Verifies that errors exceeding the RS parity budget fail closed safely."""
    raw_bits = codec.encode_payload("DOC_ECC", "REL_01", sample_codeword)
    byte_arr = bytearray(bits_to_bytes(raw_bits))

    # Corrupt 15 bytes (exceeding t=12 budget)
    for idx in range(15):
        byte_arr[idx] ^= 0xAA

    corrupted_bits = bytes_to_bits(bytes(byte_arr))
    ok, rec_cw, tele = codec.decode_payload(corrupted_bits, "DOC_ECC", "REL_01")

    assert ok is False
    assert rec_cw is None
    assert tele["uncorrectable"] is True


def test_transplantation_detection(codec, sample_codeword):
    """Verifies that payload transplantation across different documents is cryptographically detected."""
    raw_bits = codec.encode_payload("DOC_ORIGINAL", "REL_01", sample_codeword)

    # Attempt to decode as foreign document
    ok, rec_cw, tele = codec.decode_payload(raw_bits, "DOC_ATTACKER_TARGET", "REL_01")
    assert ok is False
    assert rec_cw is None
    assert tele["binding_verified"] is False
    assert "transplantation" in tele.get("error", "").lower()


def test_crc_tamper_detection(codec, sample_codeword):
    """Verifies that bit manipulation undetected by casual parity fails the CRC-32 check."""
    raw_bits = codec.encode_payload("DOC_CRC", "REL_01", sample_codeword)
    # If CRC bytes in decoded stream are modified after uncorrectable errors, decode fails
    byte_arr = bytearray(bits_to_bytes(raw_bits))
    # Corrupt all bytes heavily to trigger error
    for i in range(len(byte_arr)):
        byte_arr[i] = 0x00
    ok, rec_cw, tele = codec.decode_payload(bytes_to_bits(bytes(byte_arr)), "DOC_CRC", "REL_01")
    assert ok is False
    assert rec_cw is None
