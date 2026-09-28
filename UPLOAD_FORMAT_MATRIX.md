# AegisTrace Multi-Format Upload & Ingestion Matrix

This specification details the comprehensive multi-format support across AegisTrace Data and Control Planes, defining format tiers, MIME classification, magic signature detection, forensic carrier modes, capability states, and endpoint integration.

---

## 1. Multi-Format Support Classification

| Tier | Category | Format Name | Canonical Extension | MIME Type | Magic Bytes / Header Signature | Carrier Mechanism | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Tier 1** | Document | Portable Document Format | `.pdf` | `application/pdf` | `%PDF-` (`25 50 44 46`) | Zero-width stego, cross-page spatial fiducials, metadata | **ACTIVE / FULL** |
| **Tier 1** | Office Document | Word Document | `.docx` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | `PK\x03\x04` (`50 4b 03 04`) with `[Content_Types].xml` containing `word/` | OpenXML paragraph tracking, XML metadata injection | **ACTIVE / FULL** |
| **Tier 1** | Office Presentation | PowerPoint Slide Deck | `.pptx` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` | `PK\x03\x04` (`50 4b 03 04`) with `[Content_Types].xml` containing `ppt/` | OpenXML shape text stego, slide relationship tracking | **ACTIVE / FULL** |
| **Tier 1** | Office Spreadsheet | Excel Workbook | `.xlsx` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | `PK\x03\x04` (`50 4b 03 04`) with `[Content_Types].xml` containing `xl/` | Shared string table encoding, cell comment tracking | **ACTIVE / FULL** |
| **Tier 1** | Digital Raster Image | Portable Network Graphics | `.png` | `image/png` | `\x89PNG\r\n\x1a\n` (`89 50 4e 47 0d 0a 1a 0a`) | Spatial DWT-DCT spread spectrum, LSB carrier, chunk injection | **ACTIVE / FULL** |
| **Tier 1** | Digital Raster Image | Joint Photographic Experts | `.jpg`, `.jpeg` | `image/jpeg` | `\xff\xd8\xff` (`ff d8 ff`) | Discrete Cosine Transform (DCT) block modulation, EXIF metadata | **ACTIVE / FULL** |
| **Tier 2** | Text | Plain Text | `.txt` | `text/plain` | Valid UTF-8 / ASCII text stream without binary control chars | Invisible unicode whitespace modulation (ZWSP/ZWNJ) | **ACTIVE / FULL** |
| **Tier 2** | Structured Text | Comma Separated Values | `.csv` | `text/csv` | Valid delimited text lines with commas / semicolons | Header whitespace encoding, trailing line modulation | **ACTIVE / FULL** |
| **Tier 2** | Formatted Document | Rich Text Format | `.rtf` | `application/rtf` | `{\rtf` (`7b 5c 72 74 66`) | RTF control word annotations, font table steganography | **ACTIVE / FULL** |
| **Tier 2** | OpenDocument | OpenDocument Text | `.odt` | `application/vnd.oasis.opendocument.text` | `PK\x03\x04` with `mimetype` = `application/vnd.oasis.opendocument.text` | ODF XML text stream injection, packaging metadata | **ACTIVE / FULL** |
| **Tier 2** | OpenDocument | OpenDocument Spreadsheet | `.ods` | `application/vnd.oasis.opendocument.spreadsheet` | `PK\x03\x04` with `mimetype` = `application/vnd.oasis.opendocument.spreadsheet` | ODF table text injection, content XML metadata | **ACTIVE / FULL** |
| **Tier 2** | OpenDocument | OpenDocument Presentation | `.odp` | `application/vnd.oasis.opendocument.presentation` | `PK\x03\x04` with `mimetype` = `application/vnd.oasis.opendocument.presentation` | ODF presentation slide stream injection | **ACTIVE / FULL** |
| **Container** | Archive | Sealed Evidence Package | `.zip` | `application/zip` | `PK\x03\x04` (`50 4b 03 04`) with generic structure | Manifest SHA-256 verification, Merkle tree traversal | **ACTIVE / FULL** |
| **Container** | Metadata | Manifest / Ledger Audit | `.json` | `application/json` | Valid JSON object `{...}` or `[...]` UTF-8 | Cryptographic signature validation, schema enforcement | **ACTIVE / FULL** |

---

## 2. API Endpoint Matrix

| Format | `POST /documents` (Master Store) | `GET /documents/{id}/download` | `POST /releases` (Encrypted Multi-Recipient) | `POST /leaks` (Ingest Intercept) | `POST /analyze` (Forensic Attribution) | `VerifyTab` (Package Audit) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **PDF** | Supported | Byte-Identical | Supported | Supported | Full Watermark + Tardos + Metadata | N/A |
| **DOCX** | Supported | Byte-Identical | Supported | Supported | OpenXML Structure + Metadata | N/A |
| **PPTX** | Supported | Byte-Identical | Supported | Supported | OpenXML Slide + Metadata | N/A |
| **XLSX** | Supported | Byte-Identical | Supported | Supported | OpenXML Sheet + Metadata | N/A |
| **PNG** | Supported | Byte-Identical | Supported | Supported | Full Spatial DWT-DCT + Tardos | N/A |
| **JPEG** | Supported | Byte-Identical | Supported | Supported | DCT Robust Spread-Spectrum | N/A |
| **TXT** | Supported | Byte-Identical | Supported | Supported | Unicode Homoglyph / Whitespace | N/A |
| **CSV** | Supported | Byte-Identical | Supported | Supported | Text Structure Analysis | N/A |
| **RTF** | Supported | Byte-Identical | Supported | Supported | RTF Control Word Parser | N/A |
| **ODT** | Supported | Byte-Identical | Supported | Supported | ODF Container Validation | N/A |
| **ZIP** | Supported | Byte-Identical | Supported | Supported | Sealed Archive Unpack | Supported (Primary) |
| **JSON** | Supported | Byte-Identical | Supported | Supported | Manifest Verification | Supported (Primary) |

---

## 3. Strict Security Rejection Policies

In accordance with AegisTrace Zero-Trust Security Policy:

1. **Portable Executables (PE / Windows):**
   - Header: `MZ` (`4d 5a`)
   - Rejection Status: `415 Unsupported Media Type` or `400 Bad Request`
   - Policy Code: `UNSUPPORTED_ARTIFACT_TYPE`

2. **ELF Binaries (Linux / Unix):**
   - Header: `\x7fELF` (`7f 45 4c 46`)
   - Rejection Status: `415 Unsupported Media Type`
   - Policy Code: `UNSUPPORTED_ARTIFACT_TYPE`

3. **Active HTML / Web Scripts:**
   - Signatures: `<script>`, `<!DOCTYPE html>`, `<svg onload=`
   - Rejection Status: `415 Unsupported Media Type`
   - Policy Code: `UNSUPPORTED_ARTIFACT_TYPE` (Strict XSS & Polyglot Prevention)

4. **Oversized Payloads:**
   - Threshold: Greater than `config.max_upload_size_bytes` (50 MB default)
   - Rejection Status: `413 Payload Too Large`
