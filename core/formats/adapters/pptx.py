"""
SIH26237 - PPTX Format Adapter (Tier 1 Production).
Implements secure PresentationML container inspection, per-slide geometry/text/shape extraction,
per-slide visual carrier rendering, and slide-level watermark embedding/extraction.
"""

import io
import cv2
import zipfile
import hashlib
import numpy as np
import xml.etree.ElementTree as ET
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
    CanonicalSlide,
    TextBlock,
    TableBlock,
    DrawingObject,
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


# PresentationML Namespaces
P_NS = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
A_NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
R_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


class PptxFormatAdapter(FileTypeAdapter):
    """
    Tier 1 Production Adapter for PPTX presentations.
    """

    def __init__(self):
        self.encoder = PrintCameraWatermarkEncoder()
        self.decoder = PrintCameraWatermarkDecoder()

    def get_capabilities(self) -> FormatCapabilities:
        return FormatCapabilities(
            format_name="PPTX",
            primary_extension="pptx",
            supported_extensions=["pptx", "potx", "ppsx"],
            mime_types=[
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                "application/vnd.openxmlformats-officedocument.presentationml.template",
                "application/vnd.openxmlformats-officedocument.presentationml.slideshow"
            ],
            tier=FormatTier.TIER_1,
            capability_state=CapabilityState.SUPPORTED,
            carrier_mode=CarrierMode.IN_RENDERED_CARRIER,
            can_inspect_structure=True,
            can_canonicalize=True,
            can_render_visual_carrier=True,
            can_embed_watermark=True,
            can_extract_watermark=True,
            can_transform_robustness_test=True,
            description="Production PPTX adapter with per-slide identity mapping, PresentationML parsing, and visual slide carrier watermarking.",
            known_limitations=["Macro-enabled .pptm files strictly rejected by security policy"]
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
        zf = zipfile.ZipFile(io.BytesIO(data), 'r')

        meta = MetadataBlock(title=filename or "Untitled Presentation")

        # Discover and sort slide XML files
        slide_entries = sorted(
            [n for n in zf.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml")],
            key=lambda x: int("".join(c for c in x if c.isdigit()) or 0)
        )

        canonical_slides: List[CanonicalSlide] = []

        for s_idx, s_entry in enumerate(slide_entries):
            slide_xml = zf.read(s_entry)
            root = ET.fromstring(slide_xml)

            text_blocks: List[TextBlock] = []
            shapes: List[DrawingObject] = []

            # Extract all text in shapes
            for sp in root.findall(f".//{P_NS}sp"):
                # Extract text from paragraphs within text body
                sp_texts = []
                for p in sp.findall(f".//{A_NS}p"):
                    p_text = "".join(t.text for t in p.findall(f".//{A_NS}t") if t.text)
                    if p_text.strip():
                        sp_texts.append(p_text.strip())

                if sp_texts:
                    full_sp_text = "\n".join(sp_texts)
                    text_blocks.append(
                        TextBlock(
                            block_id=f"s{s_idx+1}_tb_{len(text_blocks)+1}",
                            text=full_sp_text,
                            is_heading=(len(text_blocks) == 0)  # first shape typically slide title
                        )
                    )
                    shapes.append(
                        DrawingObject(
                            object_id=f"s{s_idx+1}_shp_{len(shapes)+1}",
                            object_type="TEXT_BOX",
                            text=full_sp_text
                        )
                    )

            # Check for speaker notes
            note_entry = f"ppt/notesSlides/notesSlide{s_idx+1}.xml"
            speaker_notes = None
            if note_entry in zf.namelist():
                try:
                    note_xml = zf.read(note_entry)
                    n_root = ET.fromstring(note_xml)
                    n_texts = [t.text for t in n_root.findall(f".//{A_NS}t") if t.text]
                    if n_texts:
                        speaker_notes = " ".join(n_texts).strip()
                except Exception:
                    pass

            canonical_slides.append(
                CanonicalSlide(
                    slide_index=s_idx + 1,
                    slide_name=f"slide-{s_idx+1:03d}",
                    text_blocks=text_blocks,
                    shapes=shapes,
                    speaker_notes=speaker_notes
                )
            )

        if not canonical_slides:
            canonical_slides.append(
                CanonicalSlide(
                    slide_index=1,
                    slide_name="slide-001",
                    text_blocks=[TextBlock(block_id="s1_tb1", text="Empty Slide")]
                )
            )

        return CanonicalDocument(
            document_id=document_id,
            original_hash=orig_hash,
            source_format="PPTX",
            title=meta.title,
            metadata=meta,
            slides=canonical_slides
        )

    def render_carriers(
        self,
        canonical_doc: CanonicalDocument,
        options: Optional[Dict[str, Any]] = None
    ) -> List[ForensicCarrier]:
        """
        Renders each presentation slide into a standard 16:9 / 4:3 canvas carrier ($800 \times 1000$ BGR).
        """
        carriers: List[ForensicCarrier] = []
        slides = canonical_doc.slides or [CanonicalSlide(slide_index=1, slide_name="slide-001")]
        total_s = len(slides)

        for s_idx, slide in enumerate(slides):
            canvas = np.full((1000, 800, 3), 250, dtype=np.uint8)

            # Draw Slide Header Banner
            cv2.rectangle(canvas, (100, 70), (700, 140), (235, 235, 235), -1)
            cv2.rectangle(canvas, (100, 70), (700, 140), (200, 200, 200), 1)

            cv2.putText(
                canvas,
                f"SLIDE {slide.slide_index} / {total_s}: {slide.slide_name.upper()}",
                (120, 110),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (30, 30, 30),
                2,
                cv2.LINE_AA
            )

            # Render Slide Text Content
            y_cursor = 180
            for tb in slide.text_blocks:
                is_title = tb.is_heading
                font_scale = 0.55 if is_title else 0.45
                color = (15, 15, 15) if is_title else (45, 45, 45)
                thickness = 2 if is_title else 1

                for line in tb.text.splitlines():
                    words = line.split()
                    l_str = ""
                    for w in words:
                        if len(l_str) + len(w) > 50:
                            if y_cursor < 860:
                                cv2.putText(canvas, l_str, (120, y_cursor), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness, cv2.LINE_AA)
                                y_cursor += 24
                            l_str = "  • " + w if not is_title else w
                        else:
                            l_str += (" " if l_str else ("• " if not is_title else "")) + w
                    if l_str and y_cursor < 860:
                        cv2.putText(canvas, l_str, (120, y_cursor), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness, cv2.LINE_AA)
                        y_cursor += 28

            # Render Notes summary at bottom if present
            if slide.speaker_notes and y_cursor < 830:
                cv2.line(canvas, (100, 830), (700, 830), (210, 210, 210), 1)
                cv2.putText(
                    canvas,
                    f"Notes: {slide.speaker_notes[:50]}",
                    (110, 855),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.35,
                    (100, 100, 100),
                    1,
                    cv2.LINE_AA
                )

            _, png_buf = cv2.imencode(".png", canvas)

            carriers.append(
                ForensicCarrier(
                    carrier_id=f"{canonical_doc.document_id}_{slide.slide_name}",
                    parent_artifact_id=canonical_doc.document_id,
                    component_type="SLIDE",
                    component_index=s_idx,
                    total_components=total_s,
                    width_px=800,
                    height_px=1000,
                    carrier_mode=CarrierMode.IN_RENDERED_CARRIER,
                    rendering_profile="CANONICAL_PPTX_SLIDE_800X1000_BGR",
                    image_bytes=bytes(png_buf),
                    metadata={"slide_name": slide.slide_name, "slide_index": slide.slide_index}
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
