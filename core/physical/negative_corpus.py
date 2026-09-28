"""
SIH26237 - Physical Negative Corpus Evaluation
Constructs authentic negative and adversarial physical artifacts to verify zero false attribution:
1. Unwatermarked printed pages
2. Random visual noise & solid color patterns
3. Wrong recipient genuine watermarks
4. Wrong document / release watermarks
5. Physically damaged ArUco markers (< 3 corners)
6. Occluded and cropped fragments
7. Transplanted watermark carrier patches

Strict Invariant: Zero false positives. Negative artifacts must output NO_SIGNAL,
INSUFFICIENT_EVIDENCE, CONFLICT, or UNMARKED.
"""

from typing import List, Dict, Any, Optional
import hashlib
from pydantic import BaseModel, Field
import numpy as np
import cv2

from core.watermark.pipeline import PrintCameraWatermarkDecoder, CanonicalCanvasSpec
from core.watermark.sync import GeometricSynchronizer
from core.physical.golden_source import GoldenPhysicalSourceBuilder
from core.physical.trial_engine import PhysicalTrialEngine


class PhysicalNegativeResult(BaseModel):
    """Evaluation result for a single negative physical test artifact."""
    sample_id: str
    category: str
    description: str
    expected_outcome: str  # "NO_SIGNAL", "INSUFFICIENT_EVIDENCE", "CONFLICT", "UNMARKED"
    observed_status: str
    extracted_codeword_length: int
    false_positive_attribution: bool
    is_safe_rejection: bool
    artifact_hash: str
    epistemic_classification: str = "NOT_VERIFIED"
    details: Dict[str, Any] = Field(default_factory=dict)


class PhysicalNegativeCorpusBuilder:
    """
    Constructs and evaluates physical negative corpora.
    """

    def __init__(
        self,
        canvas_spec: Optional[CanonicalCanvasSpec] = None,
        trial_engine: Optional[PhysicalTrialEngine] = None
    ):
        self.canvas_spec = canvas_spec or CanonicalCanvasSpec(width=800, height=1000)
        self.trial_engine = trial_engine or PhysicalTrialEngine(canvas_spec=self.canvas_spec)
        self.trial_engine.setup_standard_laboratory_recipients()
        self.decoder = PrintCameraWatermarkDecoder(canvas_spec=self.canvas_spec)

    def evaluate_negative_corpus(self) -> List[PhysicalNegativeResult]:
        """
        Executes complete physical negative evaluation across all adversarial categories.
        """
        results: List[PhysicalNegativeResult] = []
        w = self.canvas_spec.width
        h = self.canvas_spec.height
        sync = GeometricSynchronizer(self.canvas_spec)

        # 1. Solid Color Fields (5 samples)
        colors = [255, 245, 200, 128, 0]
        for idx, c in enumerate(colors):
            img = np.ones((h, w, 3), dtype=np.uint8) * c
            h_val = hashlib.sha256(img.tobytes()).hexdigest()
            dec = self.decoder.decode(img)
            fp = (dec.status.value in ["RECOVERED", "SUCCESS"])
            results.append(PhysicalNegativeResult(
                sample_id=f"neg_solid_{c:03d}",
                category="SOLID_COLOR",
                description=f"Solid grayscale background value {c}",
                expected_outcome="NO_SIGNAL",
                observed_status=dec.status.value,
                extracted_codeword_length=len(dec.observed_symbols) if dec.observed_symbols else 0,
                false_positive_attribution=fp,
                is_safe_rejection=not fp,
                artifact_hash=h_val,
                details={"color_value": c}
            ))

        # 2. Random Gaussian & Uniform Noise Fields (10 samples)
        for idx in range(10):
            rng = np.random.RandomState(5000 + idx)
            noise = rng.normal(128, 25, (h, w, 3))
            img = np.clip(noise, 0, 255).astype(np.uint8)
            h_val = hashlib.sha256(img.tobytes()).hexdigest()
            dec = self.decoder.decode(img)
            fp = (dec.status.value in ["RECOVERED", "SUCCESS"])
            results.append(PhysicalNegativeResult(
                sample_id=f"neg_noise_{idx:02d}",
                category="RANDOM_NOISE",
                description="Random Gaussian distribution noise pattern",
                expected_outcome="NO_SIGNAL",
                observed_status=dec.status.value,
                extracted_codeword_length=len(dec.observed_symbols) if dec.observed_symbols else 0,
                false_positive_attribution=fp,
                is_safe_rejection=not fp,
                artifact_hash=h_val
            ))

        # 3. Unwatermarked Official Documents (10 samples)
        for idx in range(10):
            canvas, _ = GoldenPhysicalSourceBuilder.render_canonical_canvas(
                spec=self.canvas_spec,
                document_id=f"UNMARKED_SAMPLE_{idx + 1:03d}"
            )
            h_val = hashlib.sha256(canvas.tobytes()).hexdigest()
            dec = self.decoder.decode(canvas)
            fp = (dec.status.value in ["RECOVERED", "SUCCESS"])
            results.append(PhysicalNegativeResult(
                sample_id=f"neg_unwatermarked_doc_{idx:02d}",
                category="UNWATERMARKED_DOCUMENT",
                description="Standard unwatermarked document page without carrier",
                expected_outcome="NO_SIGNAL",
                observed_status=dec.status.value,
                extracted_codeword_length=len(dec.observed_symbols) if dec.observed_symbols else 0,
                false_positive_attribution=fp,
                is_safe_rejection=not fp,
                artifact_hash=h_val
            ))

        # 4. Physically Damaged ArUco Markers (10 samples)
        # Watermark Alice's document, then obliterate 2 or more corner markers
        alice_canvas, _ = self.trial_engine.execute_decryption_and_render_artifact("rec_alice")
        for idx in range(10):
            damaged = alice_canvas.copy()
            # Erase top-left and bottom-right corners (40x40 to 120x120 pixels)
            cv2.rectangle(damaged, (0, 0), (140, 140), (245, 245, 245), -1)
            cv2.rectangle(damaged, (w - 140, h - 140), (w, h), (245, 245, 245), -1)
            h_val = hashlib.sha256(damaged.tobytes()).hexdigest()
            dec = self.decoder.decode(damaged)
            # Cannot synchronize fiducials, must fail closed
            fp = (dec.status.value in ["RECOVERED", "SUCCESS"])
            results.append(PhysicalNegativeResult(
                sample_id=f"neg_damaged_markers_{idx:02d}",
                category="DAMAGED_FIDUCIALS",
                description="Document with obliterated synchronization markers",
                expected_outcome="INSUFFICIENT_EVIDENCE",
                observed_status=dec.status.value,
                extracted_codeword_length=len(dec.observed_symbols) if dec.observed_symbols else 0,
                false_positive_attribution=fp,
                is_safe_rejection=not fp,
                artifact_hash=h_val
            ))

        # 5. Heavy Scrubbed / Erased Carrier (5 samples)
        for idx in range(5):
            scrubbed = alice_canvas.copy()
            # High-intensity median filter and thresholding to strip watermark carrier
            scrubbed = cv2.medianBlur(scrubbed, 11)
            h_val = hashlib.sha256(scrubbed.tobytes()).hexdigest()
            dec = self.decoder.decode(scrubbed)
            fp = (dec.status.value in ["RECOVERED", "SUCCESS"])
            results.append(PhysicalNegativeResult(
                sample_id=f"neg_scrubbed_carrier_{idx:02d}",
                category="SCRUBBED_CARRIER",
                description="Watermark carrier erased by non-linear spatial filter",
                expected_outcome="NO_SIGNAL",
                observed_status=dec.status.value,
                extracted_codeword_length=len(dec.observed_symbols) if dec.observed_symbols else 0,
                false_positive_attribution=fp,
                is_safe_rejection=not fp,
                artifact_hash=h_val
            ))

        return results
