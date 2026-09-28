import io
import random
from typing import Optional, Dict, Any, List, Tuple
import numpy as np
from PIL import Image

from attacks.base import (
    BaseAttack,
    AttackFamily,
    ArtifactType,
    AttackOutput,
    DegradationMetrics,
)
from attacks.digital.image_attacks import bytes_to_pil, pil_to_bytes, bytes_to_cv2, cv2_to_bytes

class CarrierDilutionAttack(BaseAttack):
    """
    Dilutes the watermark carrier density by expanding canvas size with large padding,
    adding large unwatermarked regions around the carrier payload.
    """
    ATTACK_NAME = "carrier_dilution"
    ATTACK_FAMILY = AttackFamily.DIGITAL_IMAGE
    DEFAULT_PARAMETERS = {"pad_factor": 1.5, "fill_color": (255, 255, 255)}

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        pad_factor = float(parameters.get("pad_factor", 1.5))
        fill_color = parameters.get("fill_color", (255, 255, 255))

        img = bytes_to_pil(artifact_bytes)
        w, h = img.width, img.height
        new_w = max(w, int(w * pad_factor))
        new_h = max(h, int(h * pad_factor))

        canvas = Image.new("RGB", (new_w, new_h), color=fill_color)
        # Paste original at center
        offset_x = (new_w - w) // 2
        offset_y = (new_h - h) // 2
        canvas.paste(img, (offset_x, offset_y))

        out_bytes = pil_to_bytes(canvas, format_name="PNG")
        return AttackOutput(artifact_bytes=out_bytes, artifact_type=ArtifactType.IMAGE_PNG)


class LocalizedBitCorruptionAttack(BaseAttack):
    """
    Corrupts carrier blocks by flipping discrete bits at a controlled bit error rate (BER).
    Tests ECC Reed-Solomon correction boundaries and fail-closed CRC validation.
    """
    ATTACK_NAME = "localized_bit_corruption"
    ATTACK_FAMILY = AttackFamily.DIGITAL_IMAGE
    DEFAULT_PARAMETERS = {"corruption_rate": 0.05, "burst": False}

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        rate = float(parameters.get("corruption_rate", 0.05))
        burst = bool(parameters.get("burst", False))
        rng = random.Random(seed if seed is not None else 42)

        data = bytearray(artifact_bytes)
        n = len(data)
        flips = int(n * rate)

        if burst and n > 100:
            start_idx = rng.randint(0, max(0, n - flips - 1))
            for i in range(start_idx, min(n, start_idx + flips)):
                data[i] ^= rng.randint(1, 255)
        else:
            indices = rng.sample(range(n), min(n, flips))
            for i in indices:
                data[i] ^= (1 << rng.randint(0, 7))

        return AttackOutput(artifact_bytes=bytes(data), artifact_type=ArtifactType.RAW_BYTES)


class RegionReplacementAttack(BaseAttack):
    """
    Slices a region of a watermarked carrier image and splices it into an unwatermarked decoy image.
    Tests spatial localization and false-positive resilience under region splicing.
    """
    ATTACK_NAME = "region_replacement"
    ATTACK_FAMILY = AttackFamily.DIGITAL_IMAGE
    DEFAULT_PARAMETERS = {"region_box": (50, 50, 250, 250)}

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        box = parameters.get("region_box", (50, 50, 250, 250))
        img = bytes_to_pil(artifact_bytes)

        # Create blank decoy image
        decoy = Image.new("RGB", (img.width, img.height), color=(240, 240, 240))
        patch = img.crop(box)
        decoy.paste(patch, (box[0], box[1]))

        out_bytes = pil_to_bytes(decoy, format_name="PNG")
        return AttackOutput(artifact_bytes=out_bytes, artifact_type=ArtifactType.IMAGE_PNG)


class WatermarkStrippingAttack(BaseAttack):
    """
    Attempts to wipe structural or metadata markers from a binary or PDF document.
    """
    ATTACK_NAME = "watermark_stripping"
    ATTACK_FAMILY = AttackFamily.DIGITAL_DOCUMENT

    def _execute_transform(self, artifact_bytes: bytes, parameters: Dict[str, Any], seed: Optional[int]) -> AttackOutput:
        # Strip all marker headers and delimiters
        cleaned = artifact_bytes
        patterns = [
            b"SIH26237-TRACEABILITY-MARKER-START",
            b"SIH26237-TRACEABILITY-MARKER-END",
            b"SIH26237-TARDOS-MARKER-START",
            b"SIH26237-TARDOS-MARKER-END",
        ]
        # Locate marker blocks and excise them
        for start_pat in [b"%% SIH26237-TRACEABILITY-MARKER-START", b"%% SIH26237-TARDOS-MARKER-START"]:
            start_pos = cleaned.find(start_pat)
            if start_pos != -1:
                end_pat = b"%% SIH26237-TRACEABILITY-MARKER-END" if b"TRACEABILITY" in start_pat else b"%% SIH26237-TARDOS-MARKER-END"
                end_pos = cleaned.find(end_pat, start_pos)
                if end_pos != -1:
                    cleaned = cleaned[:start_pos] + cleaned[end_pos + len(end_pat) + 1:]

        return AttackOutput(artifact_bytes=cleaned, artifact_type=ArtifactType.DOCUMENT_PDF)


class AdversarialPayloadForgeryAttack:
    """
    Simulates an attacker crafting forged watermark bitstreams
    with single-bit flips targeting a different recipient.
    """
    @staticmethod
    def forge_payload_bits(original_bits: List[int], target_bit_index: int = 0) -> List[int]:
        forged = list(original_bits)
        if 0 <= target_bit_index < len(forged):
            forged[target_bit_index] = 1 - forged[target_bit_index]
        return forged
