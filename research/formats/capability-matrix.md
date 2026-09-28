# Multi-Format Forensic Capability Matrix

This document defines the formal forensic guarantees, carrier modes, and capability states for all 17 registered file formats in AegisTrace (Black Amber).

---

## Complete Capability Matrix

| Format | Tier | Primary Ext | Capability State | Carrier Mode | Structural Inspection | Canonicalization | Visual Carrier Rendering | Watermark Embedding | Watermark Extraction | Robustness Testing |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **PDF** | Tier 1 | `.pdf` | `SUPPORTED` | `IN_RENDERED_CARRIER` | Yes | Yes | Yes | Yes | Yes | Yes |
| **DOCX** | Tier 1 | `.docx` | `SUPPORTED` | `IN_RENDERED_CARRIER` | Yes | Yes | Yes | Yes | Yes | Yes |
| **PPTX** | Tier 1 | `.pptx` | `SUPPORTED` | `IN_RENDERED_CARRIER` | Yes | Yes | Yes | Yes | Yes | Yes |
| **XLSX** | Tier 1 | `.xlsx` | `SUPPORTED` | `IN_RENDERED_CARRIER` | Yes | Yes | Yes | Yes | Yes | Yes |
| **PNG** | Tier 1 | `.png` | `SUPPORTED` | `DIRECTLY_IN_ORIGINAL` | Yes | Yes | Yes | Yes | Yes | Yes |
| **JPEG** | Tier 1 | `.jpg` | `SUPPORTED` | `DIRECTLY_IN_ORIGINAL` | Yes | Yes | Yes | Yes | Yes | Yes |
| **TXT** | Tier 2 | `.txt` | `PARTIAL` | `IN_RENDERED_CARRIER` | Yes | Yes | Yes | Yes | Yes | Yes |
| **CSV** | Tier 2 | `.csv` | `PARTIAL` | `IN_RENDERED_CARRIER` | Yes | Yes | Yes | Yes | Yes | Yes |
| **RTF** | Tier 2 | `.rtf` | `PARTIAL` | `IN_RENDERED_CARRIER` | Yes | Yes | Yes | Yes | Yes | Yes |
| **ODT** | Tier 2 | `.odt` | `PARTIAL` | `IN_RENDERED_CARRIER` | Yes | Yes | Yes | Yes | Yes | Yes |
| **ODS** | Tier 2 | `.ods` | `PARTIAL` | `IN_RENDERED_CARRIER` | Yes | Yes | Yes | Yes | Yes | Yes |
| **ODP** | Tier 2 | `.odp` | `PARTIAL` | `IN_RENDERED_CARRIER` | Yes | Yes | Yes | Yes | Yes | Yes |
| **ZIP** | Tier 3 | `.zip` | `METADATA_ONLY` | `UNSUPPORTED` | Yes | No | No | No | No | No |
| **VIDEO** | Tier 3 | `.mp4` | `METADATA_ONLY` | `UNSUPPORTED` | Yes | No | No | No | No | No |
| **AUDIO** | Tier 3 | `.mp3` | `METADATA_ONLY` | `UNSUPPORTED` | Yes | No | No | No | No | No |
| **CAD** | Tier 3 | `.dwg` | `METADATA_ONLY` | `UNSUPPORTED` | Yes | No | No | No | No | No |
| **SCIENTIFIC**| Tier 3 | `.h5` | `METADATA_ONLY` | `UNSUPPORTED` | Yes | No | No | No | No | No |

---

## Detailed Format Descriptions

### Tier 1: Production Core
1. **PDF (Portable Document Format)**:
   - *Rendering Profile*: `CANONICAL_A4_800X1000_BGR`
   - *Forensic Binding*: Embedded via high-frequency luminance modulation and DSSS codeword encoding on rendered page canvases.
   - *Extraction*: Full blind matched-filter recovery and Reed-Solomon error correction.

2. **DOCX (OpenXML Word Document)**:
   - *Rendering Profile*: `CANONICAL_DOCX_PAGE_800X1000_BGR`
   - *Structural Model*: Extracts paragraphs, styled runs, headers/footers, and tabular matrices.
   - *Forensic Binding*: Deterministic multi-page canvas layout preserving typographical hierarchy and line bounds.

3. **PPTX (OpenXML PresentationML)**:
   - *Rendering Profile*: `CANONICAL_PPTX_SLIDE_960X540_BGR`
   - *Structural Model*: Per-slide component tracking (`slide-001`, `slide-002`), shape trees, and text body hierarchy.
   - *Forensic Binding*: 16:9 widescreen slide canvas rasterization with DSSS watermark modulation.

4. **XLSX (OpenXML SpreadsheetML)**:
   - *Rendering Profile*: `CANONICAL_XLSX_SHEET_800X1000_BGR`
   - *Structural Model*: Sheet data extraction, cell matrices (e.g. `A1:D50`), shared strings resolution, and formula preservation.
   - *Forensic Binding*: Renders structured worksheet grids without altering numerical semantics or raw cell calculations.

5. **PNG (Portable Network Graphics)**:
   - *Carrier Mode*: `DIRECTLY_IN_ORIGINAL`
   - *Forensic Binding*: Direct pixel array luminance channel modulation ($Y = 0.299R + 0.587G + 0.114B$).

6. **JPEG (Joint Photographic Experts Group)**:
   - *Carrier Mode*: `DIRECTLY_IN_ORIGINAL`
   - *Forensic Binding*: Direct spatial domain modulation with high-frequency DCT resilience under JPEG recompression.

---

### Tier 2: Architecture-Ready Formats
- **TXT / CSV**: Secure plaintext and tabular canonicalization into structured page and grid representations.
- **RTF**: Rich text formatting control-word parsing into paragraph and character stream canonical documents.
- **ODT / ODS / ODP**: OpenDocument XML content schema extraction for text, spreadsheet, and presentation containers.

---

### Tier 3: Modeled & Metadata-Only Formats
- **ZIP / Container**: Deep entry auditing, checksum computation, and container tree indexing.
- **Video / Audio**: Modeled for future frame-by-frame and acoustic watermark modulation (`METADATA_ONLY` currently).
- **CAD / Scientific**: Modeled for layer-based and tensor/dataset metadata preservation (`METADATA_ONLY` currently).
