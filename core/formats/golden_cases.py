"""
SIH26237 - AegisTrace Multi-Format Golden Case Definitions.
Provides golden test case generators and descriptors for Tier-1 formats:
PDF, DOCX, PPTX, XLSX, PNG, and JPEG.
"""

from typing import Dict, Any, NamedTuple
from tests.formats.fixtures import (
    create_minimal_pdf_bytes,
    create_minimal_docx_bytes,
    create_minimal_pptx_bytes,
    create_minimal_xlsx_bytes,
    create_minimal_png_bytes,
    create_minimal_jpeg_bytes,
)


class GoldenCaseDefinition(NamedTuple):
    case_id: str
    format: str
    extension: str
    filename: str
    mime_type: str
    generator: Any


GOLDEN_CASE_REGISTRY: Dict[str, GoldenCaseDefinition] = {
    "GOLDEN-PDF": GoldenCaseDefinition(
        case_id="GOLDEN-PDF",
        format="PDF",
        extension="pdf",
        filename="golden_evidence.pdf",
        mime_type="application/pdf",
        generator=lambda: create_minimal_pdf_bytes("AegisTrace Golden PDF", "Top Secret Evidence Document")
    ),
    "GOLDEN-DOCX": GoldenCaseDefinition(
        case_id="GOLDEN-DOCX",
        format="DOCX",
        extension="docx",
        filename="golden_evidence.docx",
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        generator=lambda: create_minimal_docx_bytes("AegisTrace Golden DOCX", "Classified Intelligence Summary")
    ),
    "GOLDEN-PPTX": GoldenCaseDefinition(
        case_id="GOLDEN-PPTX",
        format="PPTX",
        extension="pptx",
        filename="golden_evidence.pptx",
        mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        generator=lambda: create_minimal_pptx_bytes("AegisTrace Golden Presentation", "Executive Security Briefing")
    ),
    "GOLDEN-XLSX": GoldenCaseDefinition(
        case_id="GOLDEN-XLSX",
        format="XLSX",
        extension="xlsx",
        filename="golden_evidence.xlsx",
        mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        generator=lambda: create_minimal_xlsx_bytes("AegisTrace Golden Spreadsheet")
    ),
    "GOLDEN-PNG": GoldenCaseDefinition(
        case_id="GOLDEN-PNG",
        format="PNG",
        extension="png",
        filename="golden_evidence.png",
        mime_type="image/png",
        generator=lambda: create_minimal_png_bytes(512, 512)
    ),
    "GOLDEN-JPEG": GoldenCaseDefinition(
        case_id="GOLDEN-JPEG",
        format="JPEG",
        extension="jpg",
        filename="golden_evidence.jpg",
        mime_type="image/jpeg",
        generator=lambda: create_minimal_jpeg_bytes(512, 512)
    ),
}


def get_golden_case_bytes(case_id: str) -> bytes:
    """Returns raw pristine bytes for the specified Golden Case."""
    if case_id not in GOLDEN_CASE_REGISTRY:
        raise ValueError(f"Unknown Golden Case ID: {case_id}. Available: {list(GOLDEN_CASE_REGISTRY.keys())}")
    return GOLDEN_CASE_REGISTRY[case_id].generator()
