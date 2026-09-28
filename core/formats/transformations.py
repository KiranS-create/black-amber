"""
SIH26237 - Multi-Format Transformation Robustness Matrix & Simulator.
Evaluates watermark resilience against format-specific re-encodings, compressions,
rescaling, cropping, brightness/contrast shifts, blur, and print-screen simulations.
"""

import io
import cv2
import numpy as np
from typing import Dict, List, Optional, Any, Union, Tuple
from pydantic import BaseModel, Field

from core.formats.models import TransformationResultState, ForensicCarrier
from core.watermark.pipeline import PrintCameraWatermarkDecoder
from core.watermark.base import WatermarkStatus, WatermarkObservation


class TransformationEvaluation(BaseModel):
    """Result of evaluating a watermark under a specific format transformation."""
    transform_name: str
    target_format: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    state: TransformationResultState
    recovered_bit_accuracy: float = 0.0
    watermark_status: str = "NO_SIGNAL"
    is_valid: bool = False
    telemetry: Dict[str, Any] = Field(default_factory=dict)


class FormatTransformationSimulator:
    """
    Applies realistic digital and physical-channel transformations to forensic carriers.
    """

    def __init__(self):
        self.decoder = PrintCameraWatermarkDecoder()

    def apply_jpeg_compression(self, image_bgr: np.ndarray, quality: int = 75) -> np.ndarray:
        """Simulates lossy JPEG compression and decompression."""
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), max(1, min(100, quality))]
        _, enc_buf = cv2.imencode(".jpg", image_bgr, encode_param)
        return cv2.imdecode(enc_buf, cv2.IMREAD_COLOR)

    def apply_resize_resample(self, image_bgr: np.ndarray, scale: float = 0.5) -> np.ndarray:
        """Simulates downsampling/upsampling transformations."""
        h, w = image_bgr.shape[:2]
        new_w = max(100, int(w * scale))
        new_h = max(100, int(h * scale))
        resized = cv2.resize(image_bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)
        # Restore to canonical dimensions for evaluation
        return cv2.resize(resized, (w, h), interpolation=cv2.INTER_LINEAR)

    def apply_center_crop(self, image_bgr: np.ndarray, crop_percent: float = 0.10) -> np.ndarray:
        """Simulates cropping / border loss and pads back to canonical size."""
        h, w = image_bgr.shape[:2]
        pad_y = int(h * crop_percent * 0.5)
        pad_x = int(w * crop_percent * 0.5)
        cropped = image_bgr[pad_y:h-pad_y, pad_x:w-pad_x]
        # Pad back with neutral white border
        canvas = np.full((h, w, 3), 255, dtype=np.uint8)
        c_h, c_w = cropped.shape[:2]
        canvas[pad_y:pad_y+c_h, pad_x:pad_x+c_w] = cropped
        return canvas

    def apply_brightness_contrast(self, image_bgr: np.ndarray, alpha: float = 1.1, beta: int = 15) -> np.ndarray:
        """Simulates exposure and contrast variations (alpha=contrast, beta=brightness)."""
        return cv2.convertScaleAbs(image_bgr, alpha=alpha, beta=beta)

    def apply_mild_gaussian_blur(self, image_bgr: np.ndarray, ksize: int = 3) -> np.ndarray:
        """Simulates optical defocus or camera sensor blur."""
        k = ksize if ksize % 2 == 1 else ksize + 1
        return cv2.GaussianBlur(image_bgr, (k, k), 0)

    def evaluate_carrier_robustness(
        self,
        watermarked_carrier: ForensicCarrier,
        expected_codeword: List[int],
        expected_document_id: Optional[str] = None,
        expected_release_id: Optional[str] = None
    ) -> List[TransformationEvaluation]:
        """
        Runs comprehensive transformation matrix sweep against a watermarked carrier.
        """
        nparr = np.frombuffer(watermarked_carrier.image_bytes, np.uint8)
        original_canvas = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        results: List[TransformationEvaluation] = []

        transforms = [
            ("Pristine Visual Carrier", original_canvas, {}),
            ("JPEG Compression (Q=95)", self.apply_jpeg_compression(original_canvas, 95), {"quality": 95}),
            ("JPEG Compression (Q=75)", self.apply_jpeg_compression(original_canvas, 75), {"quality": 75}),
            ("JPEG Compression (Q=50)", self.apply_jpeg_compression(original_canvas, 50), {"quality": 50}),
            ("Downsample Rescale (0.75x)", self.apply_resize_resample(original_canvas, 0.75), {"scale": 0.75}),
            ("Mild Crop & Border Loss (5%)", self.apply_center_crop(original_canvas, 0.05), {"crop_pct": 0.05}),
            ("Brightness / Contrast Shift", self.apply_brightness_contrast(original_canvas, 1.08, 12), {"alpha": 1.08, "beta": 12}),
            ("Optical Defocus Blur (k=3)", self.apply_mild_gaussian_blur(original_canvas, 3), {"ksize": 3}),
        ]

        for name, transformed_img, params in transforms:
            obs = self.decoder.decode(
                transformed_img,
                expected_document_id=expected_document_id,
                expected_release_id=expected_release_id,
                expected_codeword_length=len(expected_codeword)
            )

            bit_acc = 0.0
            if obs.observed_symbols and len(obs.observed_symbols) == len(expected_codeword):
                matches = sum(1 for a, b in zip(obs.observed_symbols, expected_codeword) if a == b)
                bit_acc = round(matches / float(len(expected_codeword)), 4)

            state = TransformationResultState.FAIL
            if obs.status == WatermarkStatus.RECOVERED and bit_acc == 1.0:
                state = TransformationResultState.PASS
            elif obs.status in [WatermarkStatus.RECOVERED, WatermarkStatus.PARTIAL] and bit_acc >= 0.85:
                state = TransformationResultState.PARTIAL

            results.append(
                TransformationEvaluation(
                    transform_name=name,
                    target_format=watermarked_carrier.rendering_profile,
                    parameters=params,
                    state=state,
                    recovered_bit_accuracy=bit_acc,
                    watermark_status=obs.status.value,
                    is_valid=obs.is_valid,
                    telemetry=obs.telemetry
                )
            )

        return results
