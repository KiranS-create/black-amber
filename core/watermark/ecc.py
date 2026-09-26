"""
SIH26237 - Watermark Error Correction & Payload Codec
Implements Reed-Solomon error correction via 'reedsolo' (v1.7.0),
cryptographic document-release binding, CRC-32 integrity checking,
and pseudo-random bit interleaving for burst error resilience.
"""

import zlib
import hashlib
import struct
from typing import Tuple, List, Optional, Dict, Any
import numpy as np
import reedsolo

PREAMBLE_MAGIC = 0xE9B6  # 16-bit Barker-like frame sync pattern
DEFAULT_RS_PARITY_BYTES = 32  # Corrects up to 16 byte errors (or 32 erasures)
INTERLEAVER_SEED = 0x51483236  # "SIH26" deterministic seed




def compute_doc_release_binding(document_id: str, release_id: str) -> bytes:
    """
    Computes a 4-byte (32-bit) truncated SHA-256 digest binding the payload
    to the specific document and release instance.
    
    Security note: This is an integrity and document-release binding check
    (collision probability 2^-32 ~= 2.33e-10) designed to prevent accidental
    or malicious payload transplantation across documents/releases without
    expanding watermark payload size.
    """
    msg = f"{document_id}:{release_id}".encode("utf-8")
    return hashlib.sha256(msg).digest()[:4]


def bits_to_bytes(bits: List[int]) -> bytes:
    """Packs a list of binary bits {0, 1} into a bytes object (big-endian)."""
    byte_vals = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        chunk = bits[i:i + 8]
        for b in chunk:
            byte = (byte << 1) | (1 if b else 0)
        # Left-shift if the last byte has fewer than 8 bits
        if len(chunk) < 8:
            byte <<= (8 - len(chunk))
        byte_vals.append(byte)
    return bytes(byte_vals)


def bytes_to_bits(data: bytes, total_bits: Optional[int] = None) -> List[int]:
    """Unpacks a bytes object into a list of integer bits {0, 1}."""
    bits = []
    for byte in data:
        for bit_idx in range(7, -1, -1):
            bits.append((byte >> bit_idx) & 1)
    if total_bits is not None:
        return bits[:total_bits]
    return bits


def interleave_bytes(data: bytes, seed: int = INTERLEAVER_SEED) -> bytes:
    """
    Permutes bytes using a deterministic pseudo-random permutation.
    Disperses localized 2D spatial blotches/scratches across non-consecutive
    Reed-Solomon symbols with exact mathematical invertibility for any length n.
    """
    n = len(data)
    rng = np.random.RandomState(seed)
    perm = rng.permutation(n)
    arr = bytearray(n)
    for orig_idx, perm_idx in enumerate(perm):
        arr[perm_idx] = data[orig_idx]
    return bytes(arr)


def deinterleave_bytes(data: bytes, seed: int = INTERLEAVER_SEED) -> bytes:
    """Inverts the deterministic pseudo-random byte permutation."""
    n = len(data)
    rng = np.random.RandomState(seed)
    perm = rng.permutation(n)
    arr = bytearray(n)
    for orig_idx, perm_idx in enumerate(perm):
        arr[orig_idx] = data[perm_idx]
    return bytes(arr)




class WatermarkPayloadCodec:
    """
    Encodes and decodes the structured watermark payload with Reed-Solomon ECC.
    Structure:
      [PREAMBLE (2B)] || [DOC_REL_ID (4B)] || [CODE_LEN (2B)] || [CODEWORD (ceil(m/8) B)] || [CRC32 (4B)] || [RS PARITY (2t B)]
    """

    def __init__(self, rs_parity_bytes: int = DEFAULT_RS_PARITY_BYTES):
        self.rs_parity_bytes = rs_parity_bytes
        self.rsc = reedsolo.RSCodec(rs_parity_bytes)

    def encode_payload(
        self,
        document_id: str,
        release_id: str,
        codeword: List[int]
    ) -> List[int]:
        """
        Assembles, protects with CRC32 and Reed-Solomon ECC, and interleaves the payload.
        Returns the final bitstream ready for carrier modulation.
        """
        preamble_bytes = struct.pack(">H", PREAMBLE_MAGIC)
        doc_rel_bytes = compute_doc_release_binding(document_id, release_id)
        m = len(codeword)
        code_len_bytes = struct.pack(">H", m)
        codeword_bytes = bits_to_bytes(codeword)

        # Assemble core payload before CRC
        core = preamble_bytes + doc_rel_bytes + code_len_bytes + codeword_bytes
        crc = struct.pack(">I", zlib.crc32(core) & 0xFFFFFFFF)
        full_payload = core + crc

        # Reed-Solomon encode
        encoded_bytes = bytes(self.rsc.encode(full_payload))

        # Interleave payload bytes, keeping preamble bytes at the front un-interleaved
        # so preamble bits always reside at bit indices 0..15 for carrier phase synchronization
        interleaved_bytes = encoded_bytes[:2] + interleave_bytes(encoded_bytes[2:])

        # Convert to bits
        raw_bits = bytes_to_bits(interleaved_bytes)
        return raw_bits

    def decode_payload(
        self,
        raw_bits: List[int],
        expected_document_id: Optional[str] = None,
        expected_release_id: Optional[str] = None,
        expected_codeword_length: Optional[int] = None
    ) -> Tuple[bool, Optional[List[int]], Dict[str, Any]]:
        """
        De-interleaves, applies Reed-Solomon error correction, and validates CRC-32,
        document-release binding, and expected codeword length.

        Returns:
          (success: bool, recovered_codeword: Optional[List[int]], telemetry: Dict[str, Any])
        """
        telemetry: Dict[str, Any] = {
            "ecc_success": False,
            "crc_verified": False,
            "binding_verified": False,
            "length_verified": False,
            "errata_count": -1,
            "uncorrectable": False
        }

        # 1. Convert to bytes and de-interleave (preserving preamble prefix)
        interleaved_bytes = bits_to_bytes(raw_bits)
        if len(interleaved_bytes) < 2:
            telemetry["error"] = "Bitstream too short"
            return False, None, telemetry
        encoded_bytes = interleaved_bytes[:2] + deinterleave_bytes(interleaved_bytes[2:])

        # 2. Reed-Solomon Decode
        try:
            decoded_bytearray, _, errata_pos = self.rsc.decode(encoded_bytes)
            decoded_bytes = bytes(decoded_bytearray)
            telemetry["ecc_success"] = True
            telemetry["errata_count"] = len(errata_pos) if errata_pos else 0
        except (reedsolo.ReedSolomonError, Exception) as e:
            telemetry["uncorrectable"] = True
            telemetry["error"] = str(e)
            return False, None, telemetry

        # 3. Parse and Verify Framing
        if len(decoded_bytes) < 12:  # Min header: 2 (preamble) + 4 (doc_rel) + 2 (len) + 4 (crc)
            telemetry["error"] = "Decoded payload too short for standard framing"
            return False, None, telemetry

        core_part = decoded_bytes[:-4]
        crc_received = struct.unpack(">I", decoded_bytes[-4:])[0]
        crc_calculated = zlib.crc32(core_part) & 0xFFFFFFFF

        if crc_received != crc_calculated:
            telemetry["error"] = "CRC-32 checksum mismatch"
            return False, None, telemetry
        telemetry["crc_verified"] = True

        preamble = struct.unpack(">H", decoded_bytes[:2])[0]
        if preamble != PREAMBLE_MAGIC:
            telemetry["error"] = f"Invalid preamble magic 0x{preamble:04X} != 0x{PREAMBLE_MAGIC:04X}"
            return False, None, telemetry

        doc_rel_bytes = decoded_bytes[2:6]
        m = struct.unpack(">H", decoded_bytes[6:8])[0]
        codeword_bytes = decoded_bytes[8:-4]

        # Verify expected codeword length if provided
        if expected_codeword_length is not None and m != expected_codeword_length:
            telemetry["error"] = f"Codeword length mismatch: expected {expected_codeword_length}, decoded {m}"
            telemetry["length_verified"] = False
            return False, None, telemetry
        telemetry["length_verified"] = True

        # Verify Document-Release Binding if expected values provided
        if expected_document_id and expected_release_id:
            expected_binding = compute_doc_release_binding(expected_document_id, expected_release_id)
            if doc_rel_bytes != expected_binding:
                telemetry["error"] = "Document-release binding mismatch (transplantation detected)"
                telemetry["binding_verified"] = False
                return False, None, telemetry
            telemetry["binding_verified"] = True

        # Extract bits
        recovered_codeword = bytes_to_bits(codeword_bytes, total_bits=m)
        telemetry["codeword_length"] = len(recovered_codeword)
        return True, recovered_codeword, telemetry
