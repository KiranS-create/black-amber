"""
SIH26237 - DOCX Format Adapter (Tier 1 Production).
Implements secure OpenXML container inspection, paragraph/heading/table/image extraction,
deterministic visual page carrier rendering, and watermark embedding/extraction.
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
    CanonicalPage,
    TextBlock,
    TableBlock,
    CanonicalImage,
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


# OpenXML Namespaces
W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
DC_NS = "{http://purl.org/dc/elements/1.1/}"
CP_NS = "{http://schemas.openxmlformats.org/package/2006/metadata/core-properties}"
DCTERMS_NS = "{http://purl.org/dc/terms/}"


class DocxFormatAdapter(FileTypeAdapter):
    """
    Tier 1 Production Adapter for DOCX documents.
    """

    def __init__(self):
        self.encoder = PrintCameraWatermarkEncoder()
        self.decoder = PrintCameraWatermarkDecoder()

    def get_capabilities(self) -> FormatCapabilities:
        return FormatCapabilities(
            format_name="DOCX",
            primary_extension="docx",
            supported_extensions=["docx", "dotx"],
            mime_types=[
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.template"
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
            description="Production DOCX adapter with OOXML structural extraction, deterministic visual page rendering, and DSSS watermarking.",
            known_limitations=["Macro-enabled .docm files strictly rejected by security policy"]
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

        meta = MetadataBlock()
        # Parse docProps/core.xml if present
        if "docProps/core.xml" in zf.namelist():
            try:
                core_xml = zf.read("docProps/core.xml")
                root = ET.fromstring(core_xml)
                title_elem = root.find(f".//{DC_NS}title")
                creator_elem = root.find(f".//{DC_NS}creator")
                meta.title = title_elem.text if title_elem is not None else None
                meta.author = creator_elem.text if creator_elem is not None else None
            except Exception:
                pass

        # Parse word/document.xml
        text_blocks: List[TextBlock] = []
        tables: List[TableBlock] = []

        if "word/document.xml" in zf.namelist():
            doc_xml = zf.read("word/document.xml")
            root = ET.fromstring(doc_xml)

            # Traverse paragraphs and tables in body
            body = root.find(f"{W_NS}body")
            if body is not None:
                p_idx = 0
                tbl_idx = 0
                for elem in body:
                    if elem.tag == f"{W_NS}p":
                        # Extract text from runs
                        p_text = "".join(t.text for t in elem.findall(f".//{W_NS}t") if t.text)
                        if p_text.strip():
                            # Check if heading
                            is_h = False
                            h_lvl = 0
                            pstyle = elem.find(f".//{W_NS}pStyle")
                            if pstyle is not None:
                                val = pstyle.get(f"{W_NS}val", "")
                                if "Heading" in val:
                                    is_h = True
                                    try:
                                        h_lvl = int("".join(c for c in val if c.isdigit()) or 1)
                                    except Exception:
                                        h_lvl = 1

                            text_blocks.append(
                                TextBlock(
                                    block_id=f"p_{p_idx}",
                                    text=p_text.strip(),
                                    is_heading=is_h,
                                    heading_level=h_lvl
                                )
                            )
                            p_idx += 1

                    elif elem.tag == f"{W_NS}tbl":
                        # Extract table rows and cells
                        rows_data: List[List[str]] = []
                        for tr in elem.findall(f"{W_NS}tr"):
                            row_cells: List[str] = []
                            for tc in tr.findall(f"{W_NS}tc"):
                                cell_text = "".join(t.text for t in tc.findall(f".//{W_NS}t") if t.text)
                                row_cells.append(cell_text.strip())
                            if row_cells:
                                rows_data.append(row_cells)

                        if rows_data:
                            tables.append(
                                TableBlock(
                                    table_id=f"tbl_{tbl_idx}",
                                    row_count=len(rows_data),
                                    col_count=len(rows_data[0]) if rows_data else 0,
                                    headers=rows_data[0] if len(rows_data) > 1 else [],
                                    rows=rows_data[1:] if len(rows_data) > 1 else rows_data
                                )
                            )
                            tbl_idx += 1

        # Partition into canonical pages (standard flow layout: ~25 lines per page)
        canonical_pages: List[CanonicalPage] = []
        page_num = 1
        curr_tbs: List[TextBlock] = []
        curr_tbls: List[TableBlock] = []
        lines_count = 0

        for tb in text_blocks:
            curr_tbs.append(tb)
            lines_count += max(1, len(tb.text) // 50 + 1)
            if lines_count >= 25:
                canonical_pages.append(
                    CanonicalPage(
                        page_number=page_num,
                        text_blocks=list(curr_tbs),
                        tables=list(curr_tbls)
                    )
                )
                page_num += 1
                curr_tbs.clear()
                curr_tbls.clear()
                lines_count = 0

        if curr_tbs or curr_tbls or not canonical_pages:
            canonical_pages.append(
                CanonicalPage(
                    page_number=page_num,
                    text_blocks=list(curr_tbs),
                    tables=list(curr_tbls)
                )
            )

        return CanonicalDocument(
            document_id=document_id,
            original_hash=orig_hash,
            source_format="DOCX",
            title=meta.title or filename or "Untitled Document",
            metadata=meta,
            pages=canonical_pages,
            text_blocks=text_blocks,
            tables=tables
        )

    def render_carriers(
        self,
        canonical_doc: CanonicalDocument,
        options: Optional[Dict[str, Any]] = None
    ) -> List[ForensicCarrier]:
        """
        Renders deterministic visual page carriers for the DOCX document ($800 \times 1000$ BGR).
        """
        carriers: List[ForensicCarrier] = []
        pages = canonical_doc.pages or [CanonicalPage(page_number=1)]
        total_p = len(pages)

        for p_idx, page in enumerate(pages):
            canvas = np.full((1000, 800, 3), 255, dtype=np.uint8)

            # Draw document title / header on page 1
            if p_idx == 0 and canonical_doc.title:
                cv2.putText(
                    canvas,
                    canonical_doc.title[:45],
                    (100, 90),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (20, 20, 20),
                    2,
                    cv2.LINE_AA
                )
                cv2.line(canvas, (100, 105), (700, 105), (200, 200, 200), 1)

            # Draw page indicator
            cv2.putText(
                canvas,
                f"DOCX PAGE {page.page_number} / {total_p}",
                (100, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (140, 140, 140),
                1,
                cv2.LINE_AA
            )

            y_cursor = 135
            for tb in page.text_blocks:
                font_scale = 0.55 if tb.is_heading else 0.45
                color = (10, 10, 10) if tb.is_heading else (40, 40, 40)
                thickness = 2 if tb.is_heading else 1

                words = tb.text.split()
                line = ""
                for w in words:
                    if len(line) + len(w) > 55:
                        if y_cursor < 860:
                            cv2.putText(canvas, line, (100, y_cursor), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness, cv2.LINE_AA)
                            y_cursor += 22
                        line = w + " "
                    else:
                        line += w + " "
                if line and y_cursor < 860:
                    cv2.putText(canvas, line, (100, y_cursor), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness, cv2.LINE_AA)
                    y_cursor += 26

            # Render tables if present
            for tbl in page.tables:
                if y_cursor < 820:
                    y_cursor += 10
                    for row in tbl.rows[:5]:  # render top rows
                        row_str = " | ".join(row[:4])
                        cv2.putText(canvas, row_str[:60], (100, y_cursor), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (60, 60, 60), 1, cv2.LINE_AA)
                        y_cursor += 20

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
                    rendering_profile="CANONICAL_DOCX_PAGE_800X1000_BGR",
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
