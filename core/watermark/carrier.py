"""
SIH26237 - Watermark Carrier Modulation & Demodulation Subsystem
Implements Direct Sequence Spread Spectrum (DSSS) 2D spatial modulation,
supporting three document carrier strategies (Full Page Canvas, Graphical ROI,
and Security Background Texture) with spatial tiling redundancy and local-mean invariance.
"""

from enum import Enum
from typing import Tuple, List, Optional, Dict, Any
import numpy as np
import cv2
from pydantic import BaseModel, Field


class CarrierStrategy(str, Enum):
    """The document carrier embedding strategy."""
    RENDERED_PAGE_CANVAS = "RENDERED_PAGE_CANVAS"            # Strategy A: Full rendered page canvas
    GRAPHICAL_ROI = "GRAPHICAL_ROI"                          # Strategy B: Designated security banner / seal box
    SECURITY_BACKGROUND_TEXTURE = "SECURITY_BACKGROUND_TEXTURE"  # Strategy C: Faint guilloche / micro-dot texture


class CarrierConfig(BaseModel):
    """Configuration parameters for carrier modulation and spatial layout."""
    strategy: CarrierStrategy = CarrierStrategy.RENDERED_PAGE_CANVAS
    block_size: int = 20          # 20x20 pixel block per bit (400 chips)
    chip_scale: int = 2           # Oversampling factor per PN chip (2x2 pixels) to survive optical blur & downsampling
    embedding_strength_alpha: float = 14.0  # Luminance modulation amplitude (+- alpha)
    carrier_seed: int = 0x53494832        # "SIH2" deterministic pseudo-random PN seed

    fine_offset_search_radius: int = 2    # Fine sub-grid search radius (+- 2 pixels)
    # Active embedding region inside canonical canvas (margin-inset)
    roi_top: int = 120
    roi_bottom: int = 880
    roi_left: int = 120
    roi_right: int = 680
    # For Graphical ROI (Strategy B) - Security banner / authentication region
    graphical_roi_rect: Tuple[int, int, int, int] = (120, 480, 680, 880)  # (left, top, right, bottom)

    # Adaptive texture-aware masking parameters
    adaptive_masking: bool = False        # Scale alpha higher on text/edges, lower in blank margins
    texture_mask_gain: float = 1.5        # Scaling multiplier for high-gradient regions
    min_alpha_ratio: float = 0.4          # Minimum alpha fraction applied in pristine blank areas


def compute_image_ssim(img1: np.ndarray, img2: np.ndarray) -> float:
    """Computes Structural Similarity Index (SSIM) between two grayscale/luminance images."""
    f1 = img1.astype(np.float64)
    f2 = img2.astype(np.float64)
    c1 = (0.01 * 255.0) ** 2
    c2 = (0.03 * 255.0) ** 2

    mu1 = cv2.GaussianBlur(f1, (11, 11), 1.5)
    mu2 = cv2.GaussianBlur(f2, (11, 11), 1.5)
    mu1_sq = mu1 ** 2
    mu2_sq = mu2 ** 2
    mu1_mu2 = mu1 * mu2

    sigma1_sq = cv2.GaussianBlur(f1 ** 2, (11, 11), 1.5) - mu1_sq
    sigma2_sq = cv2.GaussianBlur(f2 ** 2, (11, 11), 1.5) - mu2_sq
    sigma12 = cv2.GaussianBlur(f1 * f2, (11, 11), 1.5) - mu1_mu2

    ssim_map = ((2.0 * mu1_mu2 + c1) * (2.0 * sigma12 + c2)) / (
        (mu1_sq + mu2_sq + c1) * (sigma1_sq + sigma2_sq + c2) + 1e-10
    )
    return float(np.mean(ssim_map))


class CarrierModulator:
    """
    Direct Sequence Spread Spectrum (DSSS) carrier modulator and matched-filter demodulator.
    Invariant to ambient lighting ramps and low-frequency shading via local mean subtraction.
    """

    def __init__(self, config: Optional[CarrierConfig] = None):
        self.config = config or CarrierConfig()

    def _get_embedding_bounds(self) -> Tuple[int, int, int, int]:
        """Returns (left, top, right, bottom) pixel boundaries based on strategy."""
        if self.config.strategy == CarrierStrategy.GRAPHICAL_ROI:
            return self.config.graphical_roi_rect
        return (
            self.config.roi_left,
            self.config.roi_top,
            self.config.roi_right,
            self.config.roi_bottom
        )

    def _generate_pn_chips(self, num_bits: int) -> np.ndarray:
        """
        Generates deterministic 2D bipolar pseudo-noise chip sequences P_k in {-1, +1}^(B x B).
        Oversamples sub-chips by chip_scale x chip_scale to ensure mid-band frequency survival
        against optical defocus, sensor downsampling, and halftoning.
        Shape: (num_bits, block_size, block_size).
        """
        rng = np.random.RandomState(self.config.carrier_seed)
        bs = self.config.block_size
        scale = max(1, self.config.chip_scale)
        sub_bs = max(1, bs // scale)

        sub_chips = rng.choice([-1.0, 1.0], size=(num_bits, sub_bs, sub_bs)).astype(np.float32)
        chips = np.repeat(np.repeat(sub_chips, scale, axis=1), scale, axis=2)
        if chips.shape[1] != bs or chips.shape[2] != bs:
            chips = chips[:, :bs, :bs]
        return chips


    def modulate(
        self,
        canvas: np.ndarray,
        payload_bits: List[int]
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Modulates the payload bitstream onto the document canvas using DSSS.
        Preserves existing text/graphics by additive modulation in the luminance channel.
        """
        output = canvas.copy()
        is_color = len(output.shape) == 3
        if is_color:
            yuv = cv2.cvtColor(output, cv2.COLOR_BGR2YUV)
            lum = yuv[:, :, 0].astype(np.float32)
        else:
            lum = output.astype(np.float32)

        left, top, right, bottom = self._get_embedding_bounds()
        bs = self.config.block_size
        num_bits = len(payload_bits)
        pn_chips = self._generate_pn_chips(num_bits)

        grid_cols = (right - left) // bs
        grid_rows = (bottom - top) // bs
        total_slots = grid_cols * grid_rows

        if total_slots < num_bits:
            raise ValueError(
                f"Active ROI insufficient for payload: {total_slots} slots < {num_bits} bits needed "
                f"under strategy {self.config.strategy.value}. Reduce block_size or use RENDERED_PAGE_CANVAS."
            )

        tile_count = max(1, total_slots // num_bits)
        base_alpha = self.config.embedding_strength_alpha

        # Precompute gradient map if adaptive masking is enabled
        grad_map = None
        if self.config.adaptive_masking:
            sobelx = cv2.Sobel(lum, cv2.CV_32F, 1, 0, ksize=3)
            sobely = cv2.Sobel(lum, cv2.CV_32F, 0, 1, ksize=3)
            grad_mag = np.sqrt(sobelx ** 2 + sobely ** 2)
            # Normalize local gradient energy to [0, 1] range
            grad_map = np.clip(grad_mag / 100.0, 0.0, 1.0)

        slot_idx = 0
        for _ in range(tile_count):
            for b_idx, bit in enumerate(payload_bits):
                r_slot = slot_idx // grid_cols
                c_slot = slot_idx % grid_cols
                y0 = top + r_slot * bs
                x0 = left + c_slot * bs
                val = 1.0 if bit == 1 else -1.0

                # Compute local block alpha
                if self.config.adaptive_masking and grad_map is not None:
                    block_grad = float(np.mean(grad_map[y0:y0 + bs, x0:x0 + bs]))
                    local_scale = np.clip(
                        self.config.min_alpha_ratio + self.config.texture_mask_gain * block_grad,
                        self.config.min_alpha_ratio,
                        1.5
                    )
                    effective_alpha = base_alpha * local_scale
                else:
                    effective_alpha = base_alpha

                mod_pattern = effective_alpha * val * pn_chips[b_idx]

                # If Strategy C (Security Texture), add faint background pattern
                if self.config.strategy == CarrierStrategy.SECURITY_BACKGROUND_TEXTURE:
                    # Add a subtle guilloche-like harmonic texture
                    yy, xx = np.mgrid[0:bs, 0:bs]
                    texture = 1.5 * np.sin(xx / 2.0) * np.cos(yy / 2.0)
                    mod_pattern += texture

                # Apply modulation to luminance
                lum[y0:y0 + bs, x0:x0 + bs] += mod_pattern
                slot_idx += 1

        # Clip to valid 8-bit range
        lum_clipped = np.clip(lum, 0, 255).astype(np.uint8)

        if is_color:
            yuv[:, :, 0] = lum_clipped
            watermarked = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)
        else:
            watermarked = lum_clipped

        # Calculate PSNR and SSIM
        orig_f = canvas.astype(np.float32)
        wm_f = watermarked.astype(np.float32)
        mse = float(np.mean((orig_f - wm_f) ** 2))
        psnr = float(10.0 * np.log10((255.0 ** 2) / max(mse, 1e-10)))
        ssim_val = compute_image_ssim(
            cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY) if is_color else canvas,
            lum_clipped
        )

        telemetry = {
            "strategy": self.config.strategy.value,
            "block_size": bs,
            "payload_bits": num_bits,
            "total_slots": total_slots,
            "tile_count": tile_count,
            "embedding_strength": base_alpha,
            "adaptive_masking": self.config.adaptive_masking,
            "psnr_db": round(psnr, 2),
            "ssim": round(ssim_val, 4),
            "mse": round(mse, 3)
        }
        return watermarked, telemetry

    def demodulate(
        self,
        rectified_canvas: np.ndarray,
        num_bits: int,
        preamble_bits: Optional[List[int]] = None
    ) -> Tuple[List[int], List[float], Dict[str, Any]]:
        """
        Demodulates raw bits from a rectified canonical canvas using matched-filter correlation.
        Performs local mean subtraction to eliminate non-uniform illumination and shading gradients.
        Optionally searches a local +-fine_offset_search_radius window on the preamble to lock phase.

        Returns:
          (raw_bits: List[int], soft_confidences: List[float], telemetry: Dict[str, Any])
        """
        if len(rectified_canvas.shape) == 3:
            yuv = cv2.cvtColor(rectified_canvas, cv2.COLOR_BGR2YUV)
            lum = yuv[:, :, 0].astype(np.float32)
        else:
            lum = rectified_canvas.astype(np.float32)

        left, top, right, bottom = self._get_embedding_bounds()
        bs = self.config.block_size
        pn_chips = self._generate_pn_chips(num_bits)

        grid_cols = (right - left) // bs
        grid_rows = (bottom - top) // bs
        total_slots = grid_cols * grid_rows
        tile_count = max(1, total_slots // num_bits)

        # 1. Fine Phase/Offset Search using preamble bits if available
        best_dx, best_dy = 0, 0
        radius = self.config.fine_offset_search_radius
        if preamble_bits is not None and len(preamble_bits) > 0 and radius > 0:
            num_p = min(len(preamble_bits), num_bits)
            best_p_score = -1e9
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    p_score = 0.0
                    for b_idx in range(num_p):
                        r_slot = b_idx // grid_cols
                        c_slot = b_idx % grid_cols
                        y0 = top + r_slot * bs + dy
                        x0 = left + c_slot * bs + dx
                        if y0 < 0 or y0 + bs > lum.shape[0] or x0 < 0 or x0 + bs > lum.shape[1]:
                            continue
                        patch = lum[y0:y0 + bs, x0:x0 + bs]
                        corr = np.sum((patch - np.mean(patch)) * pn_chips[b_idx])
                        expected_val = 1.0 if preamble_bits[b_idx] == 1 else -1.0
                        p_score += corr * expected_val
                    if p_score > best_p_score:
                        best_p_score = p_score
                        best_dx, best_dy = dx, dy

        # 2. Demodulate all payload bits at optimal offset
        accumulated_scores = np.zeros(num_bits, dtype=np.float32)

        slot_idx = 0
        for _ in range(tile_count):
            for b_idx in range(num_bits):
                r_slot = slot_idx // grid_cols
                c_slot = slot_idx % grid_cols
                y0 = top + r_slot * bs + best_dy
                x0 = left + c_slot * bs + best_dx
                if y0 >= 0 and y0 + bs <= lum.shape[0] and x0 >= 0 and x0 + bs <= lum.shape[1]:
                    patch = lum[y0:y0 + bs, x0:x0 + bs]
                    local_mean = np.mean(patch)
                    corr = np.sum((patch - local_mean) * pn_chips[b_idx])
                    accumulated_scores[b_idx] += corr
                slot_idx += 1

        # Normalized average score per bit
        avg_scores = accumulated_scores / float(tile_count * bs * bs)

        # Decision rule: bit = 1 if avg_score > 0 else 0
        raw_bits = [1 if s > 0 else 0 for s in avg_scores]

        # Soft confidence in [-1.0, 1.0] using hyperbolic tangent scaling
        soft_confidences = [float(np.tanh(s * 0.5)) for s in avg_scores]

        telemetry = {
            "demodulated_bits": num_bits,
            "tile_count": tile_count,
            "fine_offset": (best_dx, best_dy),
            "mean_absolute_score": float(np.mean(np.abs(avg_scores))),
            "min_margin": float(np.min(np.abs(avg_scores)))
        }
        return raw_bits, soft_confidences, telemetry

