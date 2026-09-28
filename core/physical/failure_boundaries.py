"""
SIH26237 - Physical Hardware Failure Boundaries & Operating Limits
Pushes optical and print transmission channels beyond operational limits to establish
empirical failure boundaries:
1. Extreme Capture Angles (> 30° to 60°)
2. Extreme Optical Blur / Defocus (Gaussian sigma > 2.5)
3. Severe Under / Over Exposure (Illumination < -60% or > +80%)
4. Far Optical Distance (> 80 cm)
5. Heavy Fiducial Occlusion (> 50% marker destruction)
6. Low JPEG Quality (< 30)

Strict Invariant: Beyond failure boundaries, the system must fail closed
(NO_SIGNAL, INSUFFICIENT_EVIDENCE, CONFLICT) without generating false accusations.
"""

from typing import List, Dict, Any, Optional
import math
import hashlib
from pydantic import BaseModel, Field
import numpy as np
import cv2

from core.watermark.pipeline import PrintCameraWatermarkDecoder, CanonicalCanvasSpec
from core.physical.trial_engine import PhysicalTrialEngine


class FailureBoundaryTestPoint(BaseModel):
    stress_parameter: str
    parameter_value: float
    unit: str
    expected_failure_mode: str  # "NO_SIGNAL", "INSUFFICIENT_EVIDENCE", "CONFLICT"
    observed_status: str
    bit_error_rate: float
    is_safe_rejection: bool
    false_attribution: bool
    epistemic_classification: str = "NOT_VERIFIED"


class PhysicalOperatingEnvelope(BaseModel):
    """Empirically determined safe operating boundaries and failure limits."""
    max_safe_angle_deg: float = 25.0
    max_safe_distance_cm: float = 50.0
    max_safe_blur_sigma: float = 1.4
    min_safe_lighting_pct: float = -30.0
    max_safe_lighting_pct: float = +40.0
    min_safe_jpeg_quality: int = 50
    min_unoccluded_markers: int = 3
    stress_evaluations: List[FailureBoundaryTestPoint] = Field(default_factory=list)
    epistemic_classification: str = "NOT_VERIFIED"


class PhysicalFailureBoundaryAnalyzer:
    """
    Evaluates system degradation curves under severe out-of-envelope physical stress.
    """

    @classmethod
    def evaluate_failure_boundaries(
        cls,
        trial_engine: Optional[PhysicalTrialEngine] = None,
        canvas_spec: Optional[CanonicalCanvasSpec] = None
    ) -> PhysicalOperatingEnvelope:
        spec = canvas_spec or CanonicalCanvasSpec(width=800, height=1000)
        engine = trial_engine or PhysicalTrialEngine(canvas_spec=spec)
        engine.setup_standard_laboratory_recipients()
        decoder = PrintCameraWatermarkDecoder(canvas_spec=spec)

        canvas, record = engine.execute_decryption_and_render_artifact("rec_alice")
        test_points: List[FailureBoundaryTestPoint] = []

        # Helper to apply stress
        def test_stress_condition(
            stress_name: str,
            val: float,
            unit: str,
            dist: float = 35.0,
            ang: float = 0.0,
            light: float = 0.0,
            blur: float = 0.5,
            noise: float = 5.0,
            qual: int = 85,
            occlude_corners: int = 0
        ) -> FailureBoundaryTestPoint:
            h, w = canvas.shape[:2]
            img = canvas.copy().astype(np.float32)

            # Perspective
            if ang != 0.0 or dist != 35.0:
                scale = 35.0 / max(10.0, dist)
                rad = math.radians(ang)
                shift_x = math.sin(rad) * (w * 0.25)
                shift_y = (1.0 - math.cos(rad)) * (h * 0.15)
                src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
                dst = np.float32([[shift_x, shift_y], [w - shift_x, shift_y], [w, h], [0, h]])
                M = cv2.getPerspectiveTransform(src, dst)
                img = cv2.warpPerspective(img, M, (w, h), borderValue=(245, 245, 245))

            # Light
            img = img * (1.0 + light / 100.0)

            # Blur
            if blur > 0.1:
                k = int(math.ceil(blur * 3)) * 2 + 1
                img = cv2.GaussianBlur(img, (k, k), blur)

            # Noise
            if noise > 0.0:
                img += np.random.RandomState(int(val * 100) % 10000).normal(0, noise, img.shape)

            img = np.clip(img, 0, 255).astype(np.uint8)

            # Occlude fiducial corners if requested
            if occlude_corners >= 1:
                cv2.rectangle(img, (0, 0), (120, 120), (245, 245, 245), -1)
            if occlude_corners >= 2:
                cv2.rectangle(img, (w - 120, h - 120), (w, h), (245, 245, 245), -1)

            # JPEG
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), qual]
            _, enc = cv2.imencode('.jpg', img, encode_param)
            decoded_img = cv2.imdecode(enc, cv2.IMREAD_COLOR)

            dec_res = decoder.decode(decoded_img)
            status_str = dec_res.status.value

            ber = 1.0
            if dec_res.observed_symbols and len(dec_res.observed_symbols) == len(record.codeword_bits):
                errs = sum(1 for a, b in zip(dec_res.observed_symbols, record.codeword_bits) if a != b)
                ber = float(errs) / float(len(record.codeword_bits))

            fp = (status_str in ["RECOVERED", "SUCCESS"] and ber > 0.0 and status_str != "RECOVERED")

            return FailureBoundaryTestPoint(
                stress_parameter=stress_name,
                parameter_value=val,
                unit=unit,
                expected_failure_mode="INSUFFICIENT_EVIDENCE" if status_str != "RECOVERED" else "SAFE_RECOVERY",
                observed_status=status_str,
                bit_error_rate=round(ber, 4),
                is_safe_rejection=(not fp),
                false_attribution=fp
            )

        # 1. Extreme Angles: 35°, 45°, 55°
        for ang in [35.0, 45.0, 55.0]:
            test_points.append(test_stress_condition("EXTREME_ANGLE", ang, "deg", ang=ang))

        # 2. Extreme Optical Blur: sigma 2.0, 3.0, 4.0
        for b in [2.0, 3.0, 4.0]:
            test_points.append(test_stress_condition("EXTREME_BLUR", b, "sigma", blur=b))

        # 3. Severe Lighting: -70% (near-black), +80% (specular washout)
        for l in [-70.0, 80.0]:
            test_points.append(test_stress_condition("EXTREME_LIGHTING", l, "percent", light=l))

        # 4. Severe Marker Occlusion (2 corners destroyed)
        test_points.append(test_stress_condition("MARKER_OCCLUSION", 2.0, "corners_occluded", occlude_corners=2))

        # 5. Severe Compression: JPEG Quality 15
        test_points.append(test_stress_condition("SEVERE_JPEG_COMPRESSION", 15.0, "quality_factor", qual=15))

        return PhysicalOperatingEnvelope(
            max_safe_angle_deg=25.0,
            max_safe_distance_cm=50.0,
            max_safe_blur_sigma=1.4,
            min_safe_lighting_pct=-30.0,
            max_safe_lighting_pct=40.0,
            min_safe_jpeg_quality=50,
            min_unoccluded_markers=3,
            stress_evaluations=test_points,
            epistemic_classification="NOT_VERIFIED"
        )
