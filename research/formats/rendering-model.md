# Multi-Format Rendering & Visual Carrier Model

## Overview
Forensic watermarking in AegisTrace relies on a deterministic visual carrier model. Rather than attempting to hide bits directly inside complex, fragile binary ASTs of office files (which are easily stripped or corrupted upon resaving), AegisTrace converts documents, presentations, and spreadsheets into **Canonical Forensic Representations**, from which high-fidelity, deterministic visual carriers are rendered and watermarked.

---

## Canonical Representation Hierarchy

```
CanonicalDocument (Document ID, Source Format, Metadata, Digest)
 │
 ├── pages: List[CanonicalPage] (Width, Height, DPI, Blocks)
 │     ├── text_blocks: List[TextBlock] (Text, Style, Position, Font)
 │     └── table_blocks: List[TableBlock] (Rows, Cols, Matrix)
 │
 ├── slides: List[CanonicalSlide] (Slide ID, Layout, Shapes)
 │     └── drawings: List[DrawingObject] (Type, Coordinates, Fill)
 │
 ├── sheets: List[CanonicalSheet] (Sheet Name, Index, Cell Grid)
 │     └── cells: Dict[str, CellData] (Row, Col, Formula, Value)
 │
 └── images: List[CanonicalImage] (Dimensions, Format, Raw Stream)
```

---

## Deterministic Rendering Profiles

| Component Type | Source Format | Profile Identifier | Target Resolution | Color Space | DPI |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Page** | PDF | `CANONICAL_A4_800X1000_BGR` | $800 \times 1000\text{ px}$ | BGR 3-channel | 150 |
| **Page** | DOCX | `CANONICAL_DOCX_PAGE_800X1000_BGR` | $800 \times 1000\text{ px}$ | BGR 3-channel | 150 |
| **Slide** | PPTX | `CANONICAL_PPTX_SLIDE_960X540_BGR` | $960 \times 540\text{ px}$ | BGR 3-channel | 150 |
| **Sheet** | XLSX | `CANONICAL_XLSX_SHEET_800X1000_BGR` | $800 \times 1000\text{ px}$ | BGR 3-channel | 150 |
| **Image** | PNG / JPEG | `CANONICAL_RASTER_ORIGINAL` | Native Dimensions | BGR 3-channel | Native |
| **Page** | TXT / RTF | `CANONICAL_TEXT_PAGE_800X1000_BGR` | $800 \times 1000\text{ px}$ | BGR 3-channel | 150 |
| **Sheet** | CSV / ODS | `CANONICAL_CSV_GRID_800X1000_BGR` | $800 \times 1000\text{ px}$ | BGR 3-channel | 150 |

---

## Watermark Modulation on Visual Carriers

1. **Luminance Channel Separation**:
   $$\begin{aligned}
   Y &= 0.299 R + 0.587 G + 0.114 B \\
   Cr &= (R - Y) \times 0.713 + 128 \\
   Cb &= (B - Y) \times 0.564 + 128
   \end{aligned}$$

2. **DSSS Codeword Spreading**:
   - Codeword length: $N = 128\text{ bits}$.
   - Orthogonal pseudo-noise sequences modulate luminance blocks across the spatial canvas.
   - Energy is distributed across high-entropy textural regions to maintain human imperceptibility while maximizing matched-filter SNR under physical and digital attacks.

3. **Spreadsheet Semantic Invariance**:
   - Original formulas (`=SUM(B2:B50)`), exact floating-point decimals, and CSV raw cell strings are never altered.
   - Forensic protection is bound to the rendered worksheet canvas or export artifact, guaranteeing mathematical integrity.
