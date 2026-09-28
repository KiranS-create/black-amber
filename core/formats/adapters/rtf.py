"""
SIH26237 - RTF Format Adapter (Tier 2 Architecture Ready: RTF).
Implements safe RTF control-word stripping, text canonicalization, visual carrier rendering,
and DSSS watermarking.
"""

import re
import cv2
import hashlib
import numpy as np
from typing import Dict, List, Optional, Any, Union, Tuple

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
from core.watermark.base import WatermarkPayload, WatermarkObservation


class RtfFormatAdapter(FileTypeAdapter):
    """
    Tier 2 Architecture-Ready Adapter for Rich Text Format (.rtf) documents.
    """

    def __init__(self):
        self.encoder = PrintCameraWatermarkEncoder()
        self.decoder = PrintCameraWatermarkDecoder()

    def get_capabilities(self) -> FormatCapabilities:
        return FormatCapabilities(
            format_name="RTF",
            primary_extension="rtf",
            supported_extensions=["rtf"],
            mime_types=["application/rtf", "text/rtf"],
            tier=FormatTier.TIER_2,
            capability_state=CapabilityState.PARTIAL,
            carrier_mode=CarrierMode.IN_RENDERED_CARRIER,
            can_inspect_structure=True,
            can_canonicalize=True,
            can_render_visual_carrier=True,
            can_embed_watermark=True,
            can_extract_watermark=True,
            can_transform_robustness_test=True,
            description="Tier 2 RTF adapter with control-word stripping, safe plain text canonicalization, and visual page carrier rendering.",
            known_limitations=["Embedded OLE objects in RTF are safely ignored and not executed"]
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
        orig_hash = hashlib.sha256(data).hexdigest()
        try:
            raw_text = data.decode("utf-8", errors="ignore")
        except Exception:
            raw_text = data.decode("latin-1", errors="replace")

        # Strip RTF control words: \rtf1, \fonttbl, \par, etc.
        # 1. Remove escaped characters
        clean = re.sub(r'\\([{}\\])', r'\1', raw_text)
        # 2. Replace \par and \line with newlines
        clean = re.sub(r'\\(par|line)\b', '\n', clean)
        # 3. Remove all other control words like \b, \fs24, \cf0
        clean = re.sub(r'\\[a-zA-Z0-9\-]+ ?', '', clean)
        # 4. Remove curly braces
        clean = re.sub(r'[{}]', '', clean)

        lines = [l.strip() for l in clean.splitlines() if l.strip()]
        text_blocks = [TextBlock(block_id=f"rtf_p_{i+1}", text=l) for i, l in enumerate(lines)]
        canonical_pages = [CanonicalPage(page_number=1, text_blocks=text_blocks)]

        meta = MetadataBlock(title=filename or f"RTF_{orig_hash[:8]}")

        return CanonicalDocument(
            document_id=document_id,
            original_hash=orig_hash,
            source_format="RTF",
            title=meta.title,
            metadata=meta,
            pages=canonical_pages,
            text_blocks=text_blocks
        )

    def render_carriers(
        self,
        canonical_doc: CanonicalDocument,
        options: Optional[Dict[str, Any]] = None
    ) -> List[ForensicCarrier]:
        carriers: List[ForensicCarrier] = []
        pages = canonical_doc.pages or [CanonicalPage(page_number=1)]

        for p_idx, page in enumerate(pages):
            canvas = np.full((1000, 800, 3), 255, dtype=np.uint8)

            cv2.putText(
                canvas,
                f"RTF DOCUMENT: PAGE {page.page_number}",
                (100, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (100, 100, 100),
                1,
                cv2.LINE_AA
            )

            y_cursor = 130
            for tb in page.text_blocks:
                if y_cursor < 860:
                    cv2.putText(
                        canvas,
                        tb.text[:65],
                        (100, y_cursor),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.4,
                        (30, 30, 30),
                        1,
                        cv2.LINE_AA
                    )
                    y_cursor += 22

            _, png_buf = cv2.imencode(".png", canvas)

            carriers.append(
                ForensicCarrier(
                    carrier_id=f"{canonical_doc.document_id}_page_{page.page_number}",
                    parent_artifact_id=canonical_doc.document_id,
                    component_type="PAGE",
                    component_index=p_idx,
                    total_components=len(pages),
                    width_px=800,
                    height_px=1000,
                    carrier_mode=CarrierMode.IN_RENDERED_CARRIER,
                    rendering_profile="CANONICAL_RTF_PAGE_800X1000_BGR",
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
        return self.decoder.decode(
            captured_input,
            expected_document_id=expected_document_id,
            expected_release_id=expected_release_id,
            expected_codeword_length=expected_codeword_length or 128
        )
