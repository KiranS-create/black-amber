"""
SIH26237 - Canonical Forensic Content Representation.
Provides format-independent hierarchical structural models for normalized documents,
pages, slides, worksheets, text blocks, tables, images, and embedded objects.
Enables deterministic content hashing and forensic comparison across transformations.
"""

from typing import Dict, List, Optional, Any, Tuple, Union
from pydantic import BaseModel, Field
import hashlib
import json


class MetadataBlock(BaseModel):
    """Normalized metadata extracted from document container or headers."""
    title: Optional[str] = None
    author: Optional[str] = None
    creator: Optional[str] = None
    subject: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    created_date: Optional[str] = None
    modified_date: Optional[str] = None
    application: Optional[str] = None
    custom_properties: Dict[str, Any] = Field(default_factory=dict)


class TextBlock(BaseModel):
    """Normalized text block (paragraph, heading, or caption)."""
    block_id: str
    text: str
    is_heading: bool = False
    heading_level: int = 0
    font_name: Optional[str] = None
    font_size: Optional[float] = None
    is_bold: bool = False
    is_italic: bool = False
    bounding_box: Optional[Tuple[float, float, float, float]] = None  # (left, top, right, bottom) in points


class TableBlock(BaseModel):
    """Normalized tabular data structure."""
    table_id: str
    row_count: int
    col_count: int
    headers: List[str] = Field(default_factory=list)
    rows: List[List[str]] = Field(default_factory=list)
    bounding_box: Optional[Tuple[float, float, float, float]] = None


class DrawingObject(BaseModel):
    """Vector shape or drawing container."""
    object_id: str
    object_type: str  # "RECTANGLE", "TEXT_BOX", "ARROW", "GROUP"
    text: Optional[str] = None
    geometry: Dict[str, Any] = Field(default_factory=dict)
    bounding_box: Optional[Tuple[float, float, float, float]] = None


class CanonicalImage(BaseModel):
    """Embedded or standalone raster/vector image representation."""
    image_id: str
    format: str  # "PNG", "JPEG", "EMF", "TIFF"
    width_px: int
    height_px: int
    content_hash: str  # SHA-256 of raw image bytes
    image_bytes: Optional[bytes] = None
    bounding_box: Optional[Tuple[float, float, float, float]] = None


class CellData(BaseModel):
    """Individual spreadsheet cell representation."""
    row: int
    col: int
    coordinate: str  # e.g. "A1", "C14"
    value: Any = None
    formula: Optional[str] = None
    data_type: str = "string"  # "string", "number", "boolean", "date", "empty"
    formatted_text: str = ""
    is_merged: bool = False


class CanonicalSheet(BaseModel):
    """Spreadsheet worksheet canonical representation."""
    sheet_index: int
    sheet_name: str
    max_row: int = 0
    max_col: int = 0
    cells: Dict[str, CellData] = Field(default_factory=dict)
    tables: List[TableBlock] = Field(default_factory=list)
    is_hidden: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CanonicalSlide(BaseModel):
    """Presentation slide canonical representation."""
    slide_index: int
    slide_name: str
    width_pts: float = 720.0
    height_pts: float = 540.0
    text_blocks: List[TextBlock] = Field(default_factory=list)
    tables: List[TableBlock] = Field(default_factory=list)
    shapes: List[DrawingObject] = Field(default_factory=list)
    images: List[CanonicalImage] = Field(default_factory=list)
    speaker_notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CanonicalPage(BaseModel):
    """Paginated document page canonical representation."""
    page_number: int
    width_pts: float = 595.0   # A4 width
    height_pts: float = 842.0  # A4 height
    text_blocks: List[TextBlock] = Field(default_factory=list)
    tables: List[TableBlock] = Field(default_factory=list)
    images: List[CanonicalImage] = Field(default_factory=list)
    header_text: Optional[str] = None
    footer_text: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EmbeddedObjectRef(BaseModel):
    """Reference to an embedded binary or active object inside container."""
    object_id: str
    object_name: str
    mime_type: str
    content_hash: str
    size_bytes: int
    is_active_macro: bool = False
    is_external_target: bool = False
    relationship_target: Optional[str] = None


class AttachmentRef(BaseModel):
    """Document attachment reference."""
    attachment_id: str
    filename: str
    content_hash: str
    size_bytes: int


class CanonicalDocument(BaseModel):
    """
    Format-agnostic canonical document representation.
    Holds normalized structural content for PDF, DOCX, PPTX, XLSX, images, or text.
    """
    document_id: str
    original_hash: str             # SHA-256 of original input artifact
    source_format: str             # e.g. "DOCX", "PDF", "PPTX", "PNG"
    title: Optional[str] = None
    metadata: MetadataBlock = Field(default_factory=MetadataBlock)
    
    # Structural components
    pages: List[CanonicalPage] = Field(default_factory=list)
    slides: List[CanonicalSlide] = Field(default_factory=list)
    sheets: List[CanonicalSheet] = Field(default_factory=list)
    images: List[CanonicalImage] = Field(default_factory=list)
    text_blocks: List[TextBlock] = Field(default_factory=list)
    tables: List[TableBlock] = Field(default_factory=list)
    embedded_objects: List[EmbeddedObjectRef] = Field(default_factory=list)
    attachments: List[AttachmentRef] = Field(default_factory=list)

    def compute_content_digest(self) -> str:
        """
        Computes deterministic SHA-256 digest of normalized structural content.
        Distinct from raw byte hash (BYTE_IDENTITY) and visual rendered hash (VISUAL_IDENTITY).
        """
        hasher = hashlib.sha256()
        hasher.update(self.source_format.encode("utf-8"))

        # Digest text content
        for tb in self.text_blocks:
            hasher.update(f"|TB:{tb.text}".encode("utf-8"))
        for p in self.pages:
            hasher.update(f"|PAGE:{p.page_number}".encode("utf-8"))
            for tb in p.text_blocks:
                hasher.update(f"|PTB:{tb.text}".encode("utf-8"))
            for t in p.tables:
                for row in t.rows:
                    hasher.update(f"|PROW:{','.join(row)}".encode("utf-8"))
        for s in self.slides:
            hasher.update(f"|SLIDE:{s.slide_index}".encode("utf-8"))
            for tb in s.text_blocks:
                hasher.update(f"|STB:{tb.text}".encode("utf-8"))
            if s.speaker_notes:
                hasher.update(f"|SNOTE:{s.speaker_notes}".encode("utf-8"))
        for sh in self.sheets:
            hasher.update(f"|SHEET:{sh.sheet_name}".encode("utf-8"))
            # Sort cell keys for deterministic ordering
            for k in sorted(sh.cells.keys()):
                c = sh.cells[k]
                hasher.update(f"|CELL:{k}={c.formatted_text or c.value}".encode("utf-8"))
        for img in self.images:
            hasher.update(f"|IMG:{img.content_hash}".encode("utf-8"))

        return hasher.hexdigest()

    def get_full_text(self) -> str:
        """Extracts complete plain text representation across all pages, slides, or sheets."""
        lines = []
        if self.text_blocks:
            lines.extend(tb.text for tb in self.text_blocks)
        for p in self.pages:
            if p.header_text:
                lines.append(p.header_text)
            lines.extend(tb.text for tb in p.text_blocks)
            for t in p.tables:
                for row in t.rows:
                    lines.append(" | ".join(row))
            if p.footer_text:
                lines.append(p.footer_text)
        for s in self.slides:
            lines.extend(tb.text for tb in s.text_blocks)
            for shp in s.shapes:
                if shp.text:
                    lines.append(shp.text)
            if s.speaker_notes:
                lines.append(f"[Notes: {s.speaker_notes}]")
        for sh in self.sheets:
            lines.append(f"--- Sheet: {sh.sheet_name} ---")
            for k in sorted(sh.cells.keys()):
                c = sh.cells[k]
                lines.append(f"{k}: {c.formatted_text or c.value}")
        return "\n".join(lines)
