"""
SIH26237 - CSV Format Adapter (Tier 2 Architecture Ready: CSV).
Implements safe delimiter sniffing, tabular canonicalization, visual grid carrier rendering,
and watermark embedding/extraction without modifying original tabular values or row semantics.
"""

import io
import csv
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
    TableBlock,
    CanonicalSheet,
    CellData,
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


class CsvFormatAdapter(FileTypeAdapter):
    """
    Tier 2 Architecture-Ready Adapter for CSV / TSV files.
    """

    def __init__(self):
        self.encoder = PrintCameraWatermarkEncoder()
        self.decoder = PrintCameraWatermarkDecoder()

    def get_capabilities(self) -> FormatCapabilities:
        return FormatCapabilities(
            format_name="CSV",
            primary_extension="csv",
            supported_extensions=["csv", "tsv"],
            mime_types=["text/csv", "text/tab-separated-values"],
            tier=FormatTier.TIER_2,
            capability_state=CapabilityState.PARTIAL,
            carrier_mode=CarrierMode.IN_RENDERED_CARRIER,
            can_inspect_structure=True,
            can_canonicalize=True,
            can_render_visual_carrier=True,
            can_embed_watermark=True,
            can_extract_watermark=True,
            can_transform_robustness_test=True,
            description="Tier 2 CSV adapter with tabular canonicalization, visual grid rendering, and DSSS watermarking. Zero cell or row semantic modifications.",
            known_limitations=["Watermarking occurs strictly in rendered visual grid; CSV raw bytes remain un-modulated"]
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
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("latin-1", errors="replace")

        # Sniff delimiter
        delimiter = ','
        sample = text[:4096]
        if '\t' in sample and sample.count('\t') > sample.count(','):
            delimiter = '\t'
        elif ';' in sample and sample.count(';') > sample.count(','):
            delimiter = ';'

        reader = csv.reader(io.StringIO(text), delimiter=delimiter)
        raw_rows = list(reader)

        headers = raw_rows[0] if raw_rows else []
        rows = raw_rows[1:] if len(raw_rows) > 1 else []
        col_count = len(headers) if headers else 0

        tbl = TableBlock(
            table_id="csv_table_1",
            row_count=len(raw_rows),
            col_count=col_count,
            headers=headers,
            rows=rows
        )

        meta = MetadataBlock(
            title=filename or f"CSV_{orig_hash[:8]}",
            custom_properties={"delimiter": delimiter, "row_count": len(raw_rows), "col_count": col_count}
        )

        return CanonicalDocument(
            document_id=document_id,
            original_hash=orig_hash,
            source_format="CSV",
            title=meta.title,
            metadata=meta,
            tables=[tbl]
        )

    def render_carriers(
        self,
        canonical_doc: CanonicalDocument,
        options: Optional[Dict[str, Any]] = None
    ) -> List[ForensicCarrier]:
        carriers: List[ForensicCarrier] = []
        tbl = canonical_doc.tables[0] if canonical_doc.tables else TableBlock(table_id="t1", row_count=0, col_count=0)

        canvas = np.full((1000, 800, 3), 255, dtype=np.uint8)

        # Draw Header
        cv2.rectangle(canvas, (100, 70), (700, 120), (245, 245, 248), -1)
        cv2.rectangle(canvas, (100, 70), (700, 120), (200, 200, 210), 1)
        cv2.putText(
            canvas,
            f"CSV TABULAR DATA: {canonical_doc.title or 'DATASET'}",
            (120, 102),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (30, 30, 40),
            2,
            cv2.LINE_AA
        )

        # Draw Grid
        grid_left = 100
        grid_top = 140
        grid_right = 700
        grid_bottom = 860
        num_cols = min(6, max(1, tbl.col_count or 4))
        num_rows = min(22, max(1, tbl.row_count or 10))

        col_w = (grid_right - grid_left) // num_cols
        row_h = (grid_bottom - grid_top) // (num_rows + 1)

        # Draw Headers
        for c_i in range(num_cols):
            c_x = grid_left + c_i * col_w
            header_str = tbl.headers[c_i] if c_i < len(tbl.headers) else f"Col{c_i+1}"
            cv2.rectangle(canvas, (c_x, grid_top), (c_x + col_w, grid_top + row_h), (235, 235, 235), -1)
            cv2.rectangle(canvas, (c_x, grid_top), (c_x + col_w, grid_top + row_h), (180, 180, 180), 1)
            cv2.putText(
                canvas,
                header_str[:max(1, col_w // 10)],
                (c_x + 6, grid_top + row_h // 2 + 4),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.35,
                (40, 40, 40),
                1,
                cv2.LINE_AA
            )

        # Draw Rows
        for r_i, row in enumerate(tbl.rows[:num_rows]):
            r_y = grid_top + (r_i + 1) * row_h
            for c_i in range(num_cols):
                c_x = grid_left + c_i * col_w
                val_str = str(row[c_i]) if c_i < len(row) else ""
                cv2.rectangle(canvas, (c_x, r_y), (c_x + col_w, r_y + row_h), (210, 210, 210), 1)
                cv2.putText(
                    canvas,
                    val_str[:max(1, col_w // 9)],
                    (c_x + 6, r_y + row_h // 2 + 4),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.35,
                    (20, 20, 20),
                    1,
                    cv2.LINE_AA
                )

        _, png_buf = cv2.imencode(".png", canvas)

        carriers.append(
            ForensicCarrier(
                carrier_id=f"{canonical_doc.document_id}_carrier_1",
                parent_artifact_id=canonical_doc.document_id,
                component_type="PAGE",
                component_index=0,
                total_components=1,
                width_px=800,
                height_px=1000,
                carrier_mode=CarrierMode.IN_RENDERED_CARRIER,
                rendering_profile="CANONICAL_CSV_GRID_800X1000_BGR",
                image_bytes=bytes(png_buf),
                metadata={"row_count": tbl.row_count, "col_count": tbl.col_count}
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
