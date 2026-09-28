"""
SIH26237 - Dynamic Decryption Watermarking Engine
Constructs cryptographically secure, domain-separated dynamic watermark identities,
commitments, and codewords generated at the moment of recipient decryption.
Guarantees visual equivalence across recipients while enforcing forensic uniqueness.
"""

import os
import hmac
import hashlib
import time
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timezone
import numpy as np
import cv2
from PIL import Image
from pydantic import BaseModel, Field

from core.watermark.base import WatermarkPayload
from core.watermark.pipeline import PrintCameraWatermarkEncoder, PrintCameraWatermarkDecoder, ensure_cv2_image
from core.watermark.carrier import compute_image_ssim, CarrierConfig, CarrierStrategy
from core.watermark.sync import CanonicalCanvasSpec
from core.crypto.key_derivation import derive_key


class DynamicWatermarkIdentity(BaseModel):
    """
    Opaque, domain-separated watermark identity generated dynamically at decryption time.
    Binds document root, recipient identity, viewer session, decryption event, and copy instance.
    NEVER encodes plaintext human names or emails.
    """
    token: str = Field(..., description="HMAC-SHA256 dynamic identity token (hex)")
    commitment: str = Field(..., description="SHA-256 commitment of token and salt")
    salt: str = Field(..., description="CSPRNG salt for commitment hiding")
    codeword: List[int] = Field(..., description="128-bit physical carrier codeword symbols")
    document_root_hash: str
    recipient_id: str
    session_id: str
    event_id: str
    copy_id: str
    key_epoch: int = 1
    nonce: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def watermark_token(self) -> str:
        """Alias for token for backwards compatibility."""
        return self.token

    def get_public_reference(self) -> str:
        """Returns opaque reference identifier safe for audit logs."""
        return f"dyn_wm_{self.commitment[:16]}"


def derive_dynamic_codeword(token_hex: str, length: int = 128) -> List[int]:
    """
    Deterministically expands dynamic watermark token into binary codeword symbols {0, 1}^m
    using HKDF-SHA256 expansion.
    """
    raw_token = bytes.fromhex(token_hex)
    # Derive 16 bytes (128 bits) of pseudo-random bitstream
    key_material = derive_key(
        shared_secret=raw_token,
        salt=b"AEGIS-CODEWORD-EXPANSION:v1",
        info=b"DSSS-CARRIER-BITS-128",
        length=max(16, (length + 7) // 8)
    )

    bits: List[int] = []
    for byte in key_material:
        for bit_idx in range(8):
            if len(bits) < length:
                bits.append((byte >> (7 - bit_idx)) & 1)
            else:
                break
    return bits


def generate_dynamic_watermark(
    document_root_hash: Optional[str] = None,
    recipient_id: str = "",
    session_id: str = "",
    event_id: str = "",
    copy_id: str = "",
    epoch_key: Optional[bytes] = None,
    key_epoch: int = 1,
    nonce: Optional[str] = None,
    codeword_length: int = 128,
    doc_root_hash: Optional[str] = None,
) -> DynamicWatermarkIdentity:
    """
    Generates a cryptographically bound dynamic watermark identity at decryption time.
    Domain-separated preimage:
    AEGIS-DYNAMIC-WM:v1:{doc_hash}:{recipient_id}:{session_id}:{event_id}:{copy_id}:{epoch}:{nonce}
    """
    doc_hash = document_root_hash or doc_root_hash or ("0" * 64)
    k_epoch = epoch_key or b"AEGIS_DEFAULT_LOCAL_EPOCH_SECRET_KEY_AIRGAP_V1"
    rnd_nonce = nonce or os.urandom(16).hex()
    salt = os.urandom(16).hex()

    preimage = (
        f"AEGIS-DYNAMIC-WM:v1:"
        f"doc={doc_hash}:"
        f"rec={recipient_id}:"
        f"ses={session_id}:"
        f"evt={event_id}:"
        f"cpy={copy_id}:"
        f"epoch={key_epoch}:"
        f"nonce={rnd_nonce}"
    ).encode('utf-8')

    token = hmac.new(k_epoch, preimage, hashlib.sha256).hexdigest()

    # Commitment: SHA-256("AEGIS-WM-COMMIT:v1:" || token || salt)
    commit_preimage = f"AEGIS-WM-COMMIT:v1:{token}:{salt}".encode('utf-8')
    commitment = hashlib.sha256(commit_preimage).hexdigest()

    codeword = derive_dynamic_codeword(token, length=codeword_length)

    return DynamicWatermarkIdentity(
        token=token,
        commitment=commitment,
        salt=salt,
        codeword=codeword,
        document_root_hash=doc_hash,
        recipient_id=recipient_id,
        session_id=session_id,
        event_id=event_id,
        copy_id=copy_id,
        key_epoch=key_epoch,
        nonce=rnd_nonce,
    )


def verify_dynamic_watermark_commitment(token: str, salt: str, expected_commitment: str) -> bool:
    """Verifies that a revealed token and salt match the cryptographic commitment."""
    commit_preimage = f"AEGIS-WM-COMMIT:v1:{token}:{salt}".encode('utf-8')
    computed = hashlib.sha256(commit_preimage).hexdigest()
    return hmac.compare_digest(computed, expected_commitment)


class DynamicWatermarkEngine:
    """
    High-performance engine for embedding and extracting dynamic decryption watermarks.
    Coordinates geometric synchronization, Reed-Solomon ECC, and DSSS carrier modulation.
    """

    def __init__(
        self,
        canvas_spec: Optional[CanonicalCanvasSpec] = None,
        carrier_config: Optional[CarrierConfig] = None,
    ):
        self.canvas_spec = canvas_spec or CanonicalCanvasSpec()
        self.carrier_config = carrier_config or CarrierConfig()
        self.encoder = PrintCameraWatermarkEncoder(self.canvas_spec, self.carrier_config)
        self.decoder = PrintCameraWatermarkDecoder(self.canvas_spec, self.carrier_config)

    def embed_watermark(
        self,
        carrier_input: Union[bytes, np.ndarray, Image.Image],
        dynamic_identity: DynamicWatermarkIdentity,
        document_id: str,
        release_id: str,
        as_bytes: bool = True,
        format: str = "PNG",
    ) -> Union[bytes, np.ndarray]:
        """
        Embeds the dynamic identity's codeword into the decrypted document canvas.
        Visually imperceptible while preserving high-contrast fiducials and carrier.
        """
        payload = WatermarkPayload(
            document_id=document_id,
            release_id=release_id,
            codeword=dynamic_identity.codeword,
            metadata={
                "commitment": dynamic_identity.commitment,
                "copy_id": dynamic_identity.copy_id,
                "session_id": dynamic_identity.session_id,
            }
        )
        return self.encoder.encode(
            carrier_input=carrier_input,
            payload=payload,
            as_bytes=as_bytes,
            format=format
        )

    def decode_watermark(
        self,
        captured_input: Union[bytes, np.ndarray, Image.Image],
        expected_document_id: Optional[str] = None,
        expected_release_id: Optional[str] = None,
        expected_codeword_length: int = 128,
    ) -> Tuple[bool, List[int], Dict[str, Any]]:
        """
        Extracts codeword symbols and telemetry from a leak artifact.
        Returns: (success, observed_bits, telemetry)
        """
        obs = self.decoder.decode(
            captured_input=captured_input,
            expected_document_id=expected_document_id,
            expected_release_id=expected_release_id,
            expected_codeword_length=expected_codeword_length
        )

        symbols = obs.observed_symbols or []
        if not symbols and obs.soft_confidences:
            symbols = [1 if sc > 0.0 else 0 for sc in obs.soft_confidences]

        is_recovered = (obs.status.value == "RECOVERED" and len(symbols) == expected_codeword_length)
        return is_recovered, symbols, obs.telemetry


def compute_visual_equivalence_metrics(
    reference_input: Union[bytes, np.ndarray, Image.Image],
    target_input: Union[bytes, np.ndarray, Image.Image],
    min_ssim: float = 0.80,
    min_psnr: float = 28.0,
) -> Dict[str, Any]:
    """
    Computes rigorous visual equivalence metrics:
    - SSIM: Structural Similarity Index Measure [0.0, 1.0]
    - PSNR: Peak Signal-to-Noise Ratio in dB
    - Max pixel difference: Maximum absolute L_inf channel error [0, 255]
    """
    img_ref = ensure_cv2_image(reference_input)
    img_target = ensure_cv2_image(target_input)

    # Resize target to match ref if slight difference
    if img_ref.shape != img_target.shape:
        img_target = cv2.resize(img_target, (img_ref.shape[1], img_ref.shape[0]), interpolation=cv2.INTER_AREA)

    # 1. SSIM
    ssim_val = compute_image_ssim(img_ref, img_target)

    # 2. PSNR
    mse = np.mean((img_ref.astype(np.float64) - img_target.astype(np.float64)) ** 2)
    if mse == 0:
        psnr_val = 100.0  # Identical images
    else:
        psnr_val = 10.0 * np.log10((255.0 ** 2) / mse)

    # 3. Max absolute difference
    max_diff = float(np.max(np.abs(img_ref.astype(np.int32) - img_target.astype(np.int32))))

    return {
        "ssim": float(round(ssim_val, 4)),
        "psnr_db": float(round(psnr_val, 2)),
        "max_diff": max_diff,
        "is_visually_equivalent": bool(ssim_val >= min_ssim and psnr_val >= min_psnr),
    }

