"""
SIH26237 - Golden Physical Source Document
Maintains the controlled, immutable source document specification for repeated physical trials.
Guarantees consistent page count, dimensions, dpi, rendering parameters, and content hash.
"""

import hashlib
from typing import Dict, Any, Tuple, Optional
from pydantic import BaseModel, Field
import numpy as np
import cv2

from core.watermark.sync import CanonicalCanvasSpec


class GoldenSourceSpecification(BaseModel):
    """Immutable specification of the golden physical test document."""
    document_id: str = "DOC_PHYSICAL_GOLDEN_2026"
    title: str = "AEGISTRACE SCIENTIFIC LABORATORY AUDIT STANDARD"
    classification: str = "RESTRICTED // FORENSIC TEST HARNESS"
    document_version: str = "2.1.0-golden"
    page_count: int = 1
    width_px: int = 800
    height_px: int = 1000
    target_dpi: int = 300
    source_sha256: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GoldenPhysicalSource(BaseModel):
    """Encapsulates a generated golden source canvas and its cryptographic content hash."""
    document_id: str
    classification: str = "RESTRICTED // FORENSIC TEST HARNESS"
    content_hash: str
    image: Any = None
    created_at: str = "2026-09-28T00:00:00Z"

    model_config = {"arbitrary_types_allowed": True}

    def verify_integrity(self) -> bool:
        if self.image is None:
            return False
        return hashlib.sha256(self.image.tobytes()).hexdigest() == self.content_hash


class GoldenPhysicalSourceBuilder:
    """
    Constructs the canonical golden source canvas and computes its immutable SHA-256 hash.
    """

    @classmethod
    def generate_canvas(
        cls,
        doc_id: str = "DOC_PHYSICAL_GOLDEN_2026",
        created_at: str = "2026-09-28T00:00:00Z"
    ) -> GoldenPhysicalSource:
        """Generates the GoldenPhysicalSource object with verified image and hash."""
        canvas, spec = cls.render_canonical_canvas(document_id=doc_id)
        return GoldenPhysicalSource(
            document_id=doc_id,
            classification=spec.classification,
            content_hash=spec.source_sha256,
            image=canvas,
            created_at=created_at
        )

    @classmethod
    def render_canonical_canvas(
        cls,
        spec: Optional[CanonicalCanvasSpec] = None,
        document_id: str = "DOC_PHYSICAL_GOLDEN_2026"
    ) -> Tuple[np.ndarray, GoldenSourceSpecification]:
        """Renders the official controlled test document canvas."""
        canvas_spec = spec or CanonicalCanvasSpec(width=800, height=1000)
        w = canvas_spec.width
        h = canvas_spec.height

        # Background: high-contrast off-white canonical paper
        canvas = np.ones((h, w, 3), dtype=np.uint8) * 245

        # 1. Header Classification Bar
        cv2.rectangle(canvas, (100, 75), (w - 100, 115), (30, 30, 30), -1)
        cv2.putText(
            canvas,
            "RESTRICTED // FORENSIC TEST HARNESS",
            (120, 102),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2
        )

        # 2. Document Title & Metadata
        cv2.putText(
            canvas,
            "AEGISTRACE SCIENTIFIC AUDIT STANDARD",
            (115, 160),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.70,
            (20, 20, 20),
            2
        )
        cv2.putText(
            canvas,
            f"DOCUMENT IDENTIFIER: {document_id} | REV 2.1",
            (115, 190),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (70, 70, 70),
            1
        )

        # 3. Horizontal Structured Content Rules & Data Rows
        for y in range(240, h - 140, 40):
            cv2.line(canvas, (110, y), (w - 110, y), (210, 210, 210), 1)
            row_idx = (y - 240) // 40
            cv2.putText(
                canvas,
                f"SECTION {row_idx + 1:02d}: Controlled optical and print resilience benchmark verification payload.",
                (115, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.38,
                (50, 50, 50),
                1
            )

        # Compute raw canvas bytes hash
        canvas_bytes = canvas.tobytes()
        sha256_hash = hashlib.sha256(canvas_bytes).hexdigest()

        golden_spec = GoldenSourceSpecification(
            document_id=document_id,
            width_px=w,
            height_px=h,
            source_sha256=sha256_hash,
            metadata={"canvas_bytes_len": len(canvas_bytes)}
        )

        return canvas, golden_spec

