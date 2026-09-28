"""
SIH26237 - PDF Format Adapter (Tier 1 Production).
Conforms PDF ingestion, canonicalization, page rendering, and watermark embedding/extraction
to the unified FileTypeAdapter contract without regressing existing PDF functionality.
"""

import io
import cv2
import numpy as np
from typing import Dict, List, Optional, Any, Union, Tuple
from pypdf import PdfReader

from core.formats.models import (
    FormatCapabilities,
    FormatTier,
    CapabilityState,
    CarrierMode,
    FormatIdentificationResult,
    SecurityValidationResult,
    ForensicCarrier
)
from core.formats.canonical import (
    CanonicalDocument,
    CanonicalPage,
    TextBlock,
    MetadataBlock
)
from core.formats.base import FileTypeAdapter
from core.formats.detector import FormatDetector
from core.formats.security import FormatSecurityValidator
from core.watermark.pipeline import (
    PrintCameraWatermarkEncoder,
    PrintCameraWatermarkDecoder
)
from core.watermark.base import WatermarkPayload, WatermarkObservation, WatermarkStatus


class PdfFormatAdapter(FileTypeAdapter):
    """
    Tier 1 Production Adapter for PDF documents.
    """

    def __init__(self):
        self.encoder = PrintCameraWatermarkEncoder()
        self.decoder = PrintCameraWatermarkDecoder()

    def get_capabilities(self) -> FormatCapabilities:
        return FormatCapabilities(
            format_name="PDF",
            primary_extension="pdf",
            supported_extensions=["pdf"],
            mime_types=["application/pdf"],
            tier=FormatTier.TIER_1,
            capability_state=CapabilityState.SUPPORTED,
            carrier_mode=CarrierMode.IN_RENDERED_CARRIER,
            can_inspect_structure=True,
            can_canonicalize=True,
            can_render_visual_carrier=True,
            can_embed_watermark=True,
            can_extract_watermark=True,
            can_transform_robustness_test=True,
            description="Production PDF adapter with geometric ArUco sync, Reed-Solomon ECC, and DSSS carrier modulation.",
            known_limitations=["Encrypted/password-protected PDFs fail-closed"]
        )

    def identify(
        self,
        data: bytes,
        filename: Optional[str] = None,
        declared_mime: Optional[str] = None
    ) -> FormatIdentificationResult:
        return FormatDetector.identify_format(data, filename, declared_mime)

    def validate_security(
        self,
        data: bytes,
        filename: Optional[str] = None,
        declared_mime: Optional[str] = None,
        max_size: Optional[int] = None
    ) -> SecurityValidationResult:
        return FormatSecurityValidator.validate_artifact(data, filename, declared_mime, max_size)

    def canonicalize(
        self,
        data: bytes,
        document_id: str,
        filename: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> CanonicalDocument:
        import hashlib
        orig_hash = hashlib.sha256(data).hexdigest()

        reader = PdfReader(io.BytesIO(data))
        meta_info = reader.metadata or {}

        meta = MetadataBlock(
            title=meta_info.get("/Title"),
            author=meta_info.get("/Author"),
            creator=meta_info.get("/Creator"),
            subject=meta_info.get("/Subject")
        )

        canonical_pages: List[CanonicalPage] = []
        for p_idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            tbs = [TextBlock(block_id=f"p{p_idx+1}_b1", text=text)] if text else []
            # Extract dimensions (points)
            w = float(page.mediabox.width) if hasattr(page.mediabox, 'width') else 595.0
            h = float(page.mediabox.height) if hasattr(page.mediabox, 'height') else 842.0

            canonical_pages.append(
                CanonicalPage(
                    page_number=p_idx + 1,
                    width_pts=w,
                    height_pts=h,
                    text_blocks=tbs
                )
            )

        return CanonicalDocument(
            document_id=document_id,
            original_hash=orig_hash,
            source_format="PDF",
            title=meta.title or filename or "Untitled Document",
            metadata=meta,
            pages=canonical_pages
        )

    def render_carriers(
        self,
        canonical_doc: CanonicalDocument,
        options: Optional[Dict[str, Any]] = None
    ) -> List[ForensicCarrier]:
        """
        Renders each canonical page into a high-resolution visual canvas carrier ($800 \times 1000$ BGR).
        """
        carriers: List[ForensicCarrier] = []
        total_p = max(1, len(canonical_doc.pages))

        for p_idx, page in enumerate(canonical_doc.pages or [CanonicalPage(page_number=1)]):
            canvas = np.full((1000, 800, 3), 255, dtype=np.uint8)

            # Draw page header / text if present
            cv2.putText(
                canvas,
                f"PAGE {page.page_number} / {total_p}",
                (100, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (120, 120, 120),
                1,
                cv2.LINE_AA
            )

            y_cursor = 140
            for tb in page.text_blocks:
                # Wrap text lines
                words = tb.text.split()
                line = ""
                for w in words:
                    if len(line) + len(w) > 55:
                        if y_cursor < 860:
                            cv2.putText(canvas, line, (100, y_cursor), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (30, 30, 30), 1, cv2.LINE_AA)
                            y_cursor += 22
                        line = w + " "
                    else:
                        line += w + " "
                if line and y_cursor < 860:
                    cv2.putText(canvas, line, (100, y_cursor), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (30, 30, 30), 1, cv2.LINE_AA)
                    y_cursor += 26

            # Encode as PNG bytes
            _, png_buf = cv2.imencode(".png", canvas)

            carriers.append(
                ForensicCarrier(
                    carrier_id=f"{canonical_doc.document_id}_page_{page.page_number}",
                    parent_artifact_id=canonical_doc.document_id,
                    component_type="PAGE",
                    component_index=p_idx,
                    total_components=total_p,
                    width_px=800,
                    height_px=1000,
                    carrier_mode=CarrierMode.IN_RENDERED_CARRIER,
                    rendering_profile="CANONICAL_A4_800X1000_BGR",
                    image_bytes=bytes(png_buf),
                    metadata={"page_number": page.page_number}
                )
            )

        return carriers

    def embed_watermark(
        self,
        carrier: ForensicCarrier,
        payload: WatermarkPayload,
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[ForensicCarrier, Dict[str, Any]]:
        """
        Embeds watermark payload into the rendered page carrier.
        """
        # Decode image bytes to cv2 BGR
        nparr = np.frombuffer(carrier.image_bytes, np.uint8)
        canvas = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        watermarked_canvas = self.encoder.encode(canvas, payload)
        _, wm_png = cv2.imencode(".png", watermarked_canvas)

        out_carrier = carrier.model_copy(update={
            "image_bytes": bytes(wm_png),
            "metadata": {**carrier.metadata, "watermarked": True, "recipient_id": payload.metadata.get("recipient_id", "")}
        })
        return out_carrier, {"status": "SUCCESS", "carrier_id": out_carrier.carrier_id}

    def extract_watermark(
        self,
        captured_input: Union[bytes, np.ndarray],
        expected_document_id: Optional[str] = None,
        expected_release_id: Optional[str] = None,
        expected_codeword_length: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> WatermarkObservation:
        """
        Extracts watermark signal from captured page image or bytes.
        """
        return self.decoder.decode(
            captured_input,
            expected_document_id=expected_document_id,
            expected_release_id=expected_release_id,
            expected_codeword_length=expected_codeword_length or 128
        )
