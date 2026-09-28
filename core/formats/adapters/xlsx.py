"""
SIH26237 - XLSX Format Adapter (Tier 1 Production).
Implements secure SpreadsheetML container inspection, worksheet/cell matrix extraction,
formula vs value tracking, deterministic worksheet visual grid rendering, and watermark embedding/extraction.
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
    CanonicalSheet,
    CellData,
    TableBlock,
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


# SpreadsheetML Namespaces
S_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
R_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


class XlsxFormatAdapter(FileTypeAdapter):
    """
    Tier 1 Production Adapter for XLSX spreadsheets.
    """

    def __init__(self):
        self.encoder = PrintCameraWatermarkEncoder()
        self.decoder = PrintCameraWatermarkDecoder()

    def get_capabilities(self) -> FormatCapabilities:
        return FormatCapabilities(
            format_name="XLSX",
            primary_extension="xlsx",
            supported_extensions=["xlsx", "xltx"],
            mime_types=[
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.template"
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
            description="Production XLSX adapter with SpreadsheetML extraction, cell matrix preservation, visual worksheet grid rendering, and DSSS watermarking.",
            known_limitations=["Macro-enabled .xlsm files strictly rejected by security policy"]
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

        meta = MetadataBlock(title=filename or "Untitled Spreadsheet")

        # 1. Parse shared strings table (xl/sharedStrings.xml)
        shared_strings: List[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            try:
                sst_xml = zf.read("xl/sharedStrings.xml")
                root = ET.fromstring(sst_xml)
                for si in root.findall(f"{S_NS}si"):
                    t_elems = si.findall(f".//{S_NS}t")
                    shared_strings.append("".join(t.text for t in t_elems if t.text))
            except Exception:
                pass

        # 2. Parse workbook structure (xl/workbook.xml)
        sheet_info: List[Dict[str, Any]] = []
        if "xl/workbook.xml" in zf.namelist():
            try:
                wb_xml = zf.read("xl/workbook.xml")
                root = ET.fromstring(wb_xml)
                sheets_elem = root.find(f"{S_NS}sheets")
                if sheets_elem is not None:
                    for s in sheets_elem.findall(f"{S_NS}sheet"):
                        s_name = s.get("name", "Sheet")
                        s_id = s.get("sheetId", "1")
                        state = s.get("state", "visible")
                        sheet_info.append({
                            "name": s_name,
                            "sheet_id": s_id,
                            "is_hidden": (state == "hidden")
                        })
            except Exception:
                pass

        # 3. Discover and parse worksheet files (xl/worksheets/sheet*.xml)
        sheet_files = sorted(
            [n for n in zf.namelist() if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")],
            key=lambda x: int("".join(c for c in x if c.isdigit()) or 0)
        )

        canonical_sheets: List[CanonicalSheet] = []

        for s_idx, s_file in enumerate(sheet_files):
            info = sheet_info[s_idx] if s_idx < len(sheet_info) else {"name": f"Sheet{s_idx+1}", "is_hidden": False}
            sheet_xml = zf.read(s_file)
            root = ET.fromstring(sheet_xml)

            cells_dict: Dict[str, CellData] = {}
            sheet_data = root.find(f"{S_NS}sheetData")
            max_r = 0
            max_c = 0

            if sheet_data is not None:
                for row in sheet_data.findall(f"{S_NS}row"):
                    r_idx = int(row.get("r", 1))
                    max_r = max(max_r, r_idx)

                    for c in row.findall(f"{S_NS}c"):
                        coord = c.get("r", "A1")
                        cell_type = c.get("t", "")
                        v_elem = c.find(f"{S_NS}v")
                        f_elem = c.find(f"{S_NS}f")
                        raw_val = v_elem.text if v_elem is not None else ""
                        formula_str = f_elem.text if f_elem is not None else None

                        # Resolve shared string value
                        if cell_type == "s" and raw_val.isdigit():
                            idx = int(raw_val)
                            val_str = shared_strings[idx] if idx < len(shared_strings) else raw_val
                        else:
                            val_str = raw_val

                        # Parse column number from coord e.g. "C14" -> col 3
                        col_letters = "".join(ch for ch in coord if ch.isalpha())
                        col_num = 0
                        for ch in col_letters:
                            col_num = col_num * 26 + (ord(ch.upper()) - ord('A') + 1)
                        max_c = max(max_c, col_num)

                        cells_dict[coord] = CellData(
                            row=r_idx,
                            col=col_num,
                            coordinate=coord,
                            value=val_str,
                            formula=formula_str,
                            formatted_text=val_str
                        )

            canonical_sheets.append(
                CanonicalSheet(
                    sheet_index=s_idx + 1,
                    sheet_name=info["name"],
                    max_row=max_r,
                    max_col=max_c,
                    cells=cells_dict,
                    is_hidden=info.get("is_hidden", False)
                )
            )

        if not canonical_sheets:
            canonical_sheets.append(
                CanonicalSheet(
                    sheet_index=1,
                    sheet_name="Sheet1",
                    cells={"A1": CellData(row=1, col=1, coordinate="A1", value="Empty Sheet")}
                )
            )

        return CanonicalDocument(
            document_id=document_id,
            original_hash=orig_hash,
            source_format="XLSX",
            title=meta.title,
            metadata=meta,
            sheets=canonical_sheets
        )

    def render_carriers(
        self,
        canonical_doc: CanonicalDocument,
        options: Optional[Dict[str, Any]] = None
    ) -> List[ForensicCarrier]:
        """
        Renders each worksheet as a clean visual grid canvas carrier ($800 \times 1000$ BGR).
        """
        carriers: List[ForensicCarrier] = []
        sheets = canonical_doc.sheets or [CanonicalSheet(sheet_index=1, sheet_name="Sheet1")]
        total_s = len(sheets)

        for s_idx, sheet in enumerate(sheets):
            canvas = np.full((1000, 800, 3), 255, dtype=np.uint8)

            # Draw Sheet Banner
            cv2.rectangle(canvas, (100, 70), (700, 120), (240, 244, 248), -1)
            cv2.rectangle(canvas, (100, 70), (700, 120), (180, 200, 220), 1)

            cv2.putText(
                canvas,
                f"WORKSHEET {sheet.sheet_index}/{total_s}: {sheet.sheet_name.upper()}",
                (120, 102),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (20, 40, 60),
                2,
                cv2.LINE_AA
            )

            # Draw Spreadsheet Grid Matrix
            grid_left = 100
            grid_top = 140
            grid_right = 700
            grid_bottom = 860
            num_cols = min(6, max(1, sheet.max_col or 4))
            num_rows = min(20, max(1, sheet.max_row or 10))

            col_w = (grid_right - grid_left) // num_cols
            row_h = (grid_bottom - grid_top) // (num_rows + 1)

            # Draw Column Headers (A, B, C, ...)
            for c_i in range(num_cols):
                c_x = grid_left + c_i * col_w
                col_letter = chr(ord('A') + c_i)
                cv2.rectangle(canvas, (c_x, grid_top), (c_x + col_w, grid_top + row_h), (230, 230, 230), -1)
                cv2.rectangle(canvas, (c_x, grid_top), (c_x + col_w, grid_top + row_h), (180, 180, 180), 1)
                cv2.putText(
                    canvas,
                    col_letter,
                    (c_x + col_w // 2 - 5, grid_top + row_h // 2 + 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    (50, 50, 50),
                    1,
                    cv2.LINE_AA
                )

            # Draw Row Cells & Values
            for r_i in range(num_rows):
                r_y = grid_top + (r_i + 1) * row_h
                for c_i in range(num_cols):
                    c_x = grid_left + c_i * col_w
                    cv2.rectangle(canvas, (c_x, r_y), (c_x + col_w, r_y + row_h), (200, 200, 200), 1)

                    # Look up cell coordinate e.g. "A1", "B2"
                    coord = f"{chr(ord('A') + c_i)}{r_i + 1}"
                    cell = sheet.cells.get(coord)
                    if cell and cell.formatted_text:
                        val_display = str(cell.formatted_text)[:max(1, col_w // 9)]
                        cv2.putText(
                            canvas,
                            val_display,
                            (c_x + 6, r_y + row_h // 2 + 4),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.35,
                            (25, 25, 25),
                            1,
                            cv2.LINE_AA
                        )

            _, png_buf = cv2.imencode(".png", canvas)

            carriers.append(
                ForensicCarrier(
                    carrier_id=f"{canonical_doc.document_id}_sheet_{sheet.sheet_index}",
                    parent_artifact_id=canonical_doc.document_id,
                    component_type="SHEET",
                    component_index=s_idx,
                    total_components=total_s,
                    width_px=800,
                    height_px=1000,
                    carrier_mode=CarrierMode.IN_RENDERED_CARRIER,
                    rendering_profile="CANONICAL_XLSX_SHEET_800X1000_BGR",
                    image_bytes=bytes(png_buf),
                    metadata={"sheet_name": sheet.sheet_name, "sheet_index": sheet.sheet_index}
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
