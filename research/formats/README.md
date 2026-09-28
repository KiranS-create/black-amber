# Multi-Format Forensic Content Architecture

## Overview & Mission
AegisTrace (Black Amber) provides a unified, security-first, format-independent forensic content architecture. It extends the platform beyond legacy single-format assumptions to ingest, inspect, canonicalize, render, watermark, extract, and attribute evidence across a wide spectrum of file formats—without creating fragmented or incompatible forensic stacks.

## Core Architectural Invariants

1. **Original Artifact Identity vs. Forensic Carrier Identity**:
   - The bitwise identity (SHA-256) of the original uploaded file is permanently preserved in `OriginalArtifactIdentity` and never overwritten or conflated with rendered forensic carrier images or watermarked outputs.
   - Forensic carriers maintain independent cryptographic identities (`ForensicCarrierIdentity`) tracking dimensions, component indices, rendering profiles, and watermark embedding metadata.

2. **Explicit Capability Reporting**:
   - Every supported or modeled format declares its capabilities transparently via `FormatCapabilities`:
     - `SUPPORTED`: Production-ready full pipeline (PDF, DOCX, PPTX, XLSX, PNG, JPEG).
     - `PARTIAL`: Architecture-ready canonicalization and visual rendering (TXT, CSV, RTF, ODT, ODS, ODP).
     - `METADATA_ONLY`: Secure container inspection and metadata binding (ZIP, Video, Audio, CAD, Scientific).
     - `UNSUPPORTED`: Explicitly rejected formats.

3. **Zero-Trust Security & Fail-Closed Invariants**:
   - Ingestion enforces strict checks against ZIP bombs (max $100:1$ ratio, $150\text{ MB}$ uncompressed ceiling, $10,000$ entries), path traversals, VBA/macros, external entity expansion (XXE/Billion Laughs), external relationships (.rels SSRF), Pillow decompression bombs ($100\text{ MP}$ limit), and polyglots.

4. **100% Offline & Pure Determinism**:
   - All format parsers, canonicalizers, and rasterizers operate fully offline with zero cloud runtime dependencies.

---

## Architectural Pipeline

```
ORIGINAL ARTIFACT
      │
      ▼
FORMAT IDENTIFICATION & SECURITY AUDIT (Zero-Trust Validation)
      │
      ▼
FORMAT ADAPTER (Type-Specific Engine)
      │
      ▼
CANONICAL FORENSIC REPRESENTATION (CanonicalDocument)
      │
      ▼
FORENSIC CARRIER GENERATION (Visual Rasterization / Per-Component Bitmaps)
      │
      ▼
WATERMARK MODULATION (DSSS / RS Code Robust Carrier Embedding)
      │
      ▼
CONTROLLED DISTRIBUTION / RELEASE
      │
      ▼
LEAKED ARTIFACT CAPTURE / EXTRACTION
      │
      ▼
FORENSIC ATTRIBUTION & RFC 8785 EVIDENCE PACKAGE
```

---

## Format Tier Classification

| Tier | Format Class | Formats | Capability State | Carrier Mode |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1** | Document / Presentation / Sheet / Image | PDF, DOCX, PPTX, XLSX, PNG, JPEG | `SUPPORTED` | `IN_RENDERED_CARRIER` / `DIRECTLY_IN_ORIGINAL` |
| **Tier 2** | Text / Tabular / Formatted / ODF | TXT, CSV, RTF, ODT, ODS, ODP | `PARTIAL` | `IN_RENDERED_CARRIER` |
| **Tier 3** | Archive / Media / Engineering / Data | ZIP, VIDEO, AUDIO, CAD, SCIENTIFIC | `METADATA_ONLY` | `IN_METADATA` / `UNSUPPORTED` |

---

## Repository Layout
- `core/formats/models.py`: Pydantic data models for original identity, carrier identity, capabilities, and security classifications.
- `core/formats/canonical.py`: Canonical representation schema (`CanonicalDocument`, `CanonicalPage`, `CanonicalSlide`, `CanonicalSheet`, `CanonicalImage`).
- `core/formats/detector.py`: Sniffing engine for magic bytes, MIME types, extension cross-checks, and polyglot detection.
- `core/formats/security.py`: Zero-trust security validator and attack mitigations.
- `core/formats/base.py`: Abstract contract (`FileTypeAdapter`) for all adapters.
- `core/formats/registry.py`: Singleton registry managing all 17 format adapters.
- `core/formats/adapters/`: Individual adapter implementations (`pdf`, `docx`, `pptx`, `xlsx`, `raster`, `text`, `csv`, `rtf`, `opendocument`, `tier3_modeled`).
- `core/formats/api.py`: High-level `ForensicFormatAPI` orchestrating the entire lifecycle.
- `core/formats/transformations.py`: Physical and digital distortion simulator.
- `core/formats/evidence_integration.py`: RFC 8785 canonical JSON evidence packaging.
- `core/formats/lineage_integration.py`: Sparse Merkle lineage tree integration.
