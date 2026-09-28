# Multi-Format Security & Threat Mitigation Model

## Executive Summary
Ingesting diverse file formats introduces significant attack surfaces, including parser vulnerabilities, memory exhaustion attacks, active code execution, and Server-Side Request Forgery (SSRF). AegisTrace enforces a **zero-trust, fail-closed security model** that halts processing before content is loaded into untrusted parser backends.

---

## Threat Surface & Mitigation Controls

```
                        INGESTED PAYLOAD
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
 [Header & Magic Byte Sniffing]          [Size Bounds Check]
   - Match raw binary signature            - Max 100 MB file limit
   - Flag extension mismatches             - Max 150 MB uncompressed limit
   - Prohibit executable PE/ELF            - Max 100:1 compression ratio
            │                                     │
            └──────────────────┬──────────────────┘
                               ▼
               [Container Deep Inspection]
                 - Path traversal detection (../, absolute)
                 - Duplicate ZIP entry rejection
                 - Embedded Macro/VBA script scanning
                 - External relationship / SSRF blocking
                 - XML entity hazard & XXE defense
                 - Image decompression bomb ceiling
                               │
                               ▼
                   [Strict Fail-Closed Gate]
               Safe? ─── No ───► FormatSecurityException
                 │
                Yes
                 ▼
             [Canonicalization & Processing]
```

---

## Detailed Attack Mitigations

### 1. ZIP Bombs & Decompression Denial of Service
- **Maximum File Size**: $100\text{ MB}$ raw payload size limit.
- **Maximum Uncompressed Size**: $150\text{ MB}$ aggregate uncompressed container size.
- **Maximum Compression Ratio**: $100.0:1$. Any container expanding beyond 100 times its compressed size is immediately rejected with `DECOMPRESSION_LIMIT`.
- **Maximum Container Entries**: $10,000$ files. Archives exceeding this entry count are rejected with `RESOURCE_LIMIT`.

### 2. Path Traversal & Directory Overwrite (Zip Slip)
- All ZIP/archive filenames are inspected for:
  - Relative upward traversals (`../`, `..\`)
  - Absolute system paths (`/`, `C:\`, `\\`)
  - Null bytes (`\x00`)
- Any violation raises `PATH_TRAVERSAL_DETECTED`.

### 3. Macro & Executable Binary Injection
- OpenXML and ODF archives are audited against active scripting payloads:
  - `vbaProject.bin`, `word/vbaData.xml`, `xl/vbaProject.bin`, `ppt/vbaProject.bin`
  - ActiveX binaries (`activeX1.bin`, `activeX1.xml`)
  - OLE objects (`oleObject1.bin`)
  - Standalone executable extensions (`.exe`, `.dll`, `.bat`, `.ps1`, `.vbs`)
- Matches trigger `MACRO_PRESENT`.

### 4. External Entity Expansion (XXE / Billion Laughs)
- All XML streams inside OpenXML and ODF archives are statically audited prior to DOM tree generation:
  - `<!ENTITY` and `<!DOCTYPE` declarations
  - `SYSTEM` and `PUBLIC` identifiers
- Violations raise `XML_ENTITY_HAZARD`.

### 5. External Relationship SSRF Prevention
- OpenXML relationship definitions (`.rels`) are inspected for:
  - `TargetMode="External"`
  - `http://`, `https://`, `file://`, `ftp://`, `script:`
- Any external network or filesystem hook is blocked with `EXTERNAL_REFERENCE_PRESENT`.

### 6. Image Decompression Bombs & Dimension Limits
- Maximum pixel dimensions: $16,384 \times 16,384\text{ px}$.
- Maximum aggregate pixel count: $100,000,000\text{ pixels}$ (`Image.MAX_IMAGE_PIXELS = 100_000_000`).
- Oversized or corrupted image payloads trigger `OVERSIZED_DIMENSIONS` or `DECOMPRESSION_LIMIT`.

### 7. Polyglot Container Detection
- Detects dual-format files (e.g. valid JPEG prepended to a ZIP archive) by scanning for secondary container headers (`PK\x03\x04`) at non-standard offsets.
- Flags and rejects polyglot files with `POLYGLOT_DETECTED`.

---

## Security Failure Classification Matrix

| Error Class | Enum Value | Trigger Condition |
| :--- | :--- | :--- |
| **Type Mismatch** | `TYPE_MISMATCH` | Magic bytes conflict with file payload or executable signature detected |
| **Malformed Container** | `MALFORMED_CONTAINER` | Corrupted headers, truncated archives, or unparseable byte structures |
| **Polyglot Detected** | `POLYGLOT_DETECTED` | Conflicting embedded container signatures |
| **Decompression Limit** | `DECOMPRESSION_LIMIT` | Compression ratio $> 100:1$ or uncompressed total $> 150\text{ MB}$ |
| **Parser Rejected** | `PARSER_REJECTED` | Zero-byte uploads or unparseable document data |
| **Macro Present** | `MACRO_PRESENT` | Embedded VBA, macros, ActiveX, or scripts |
| **External Reference** | `EXTERNAL_REFERENCE_PRESENT` | External URLs, file URI references, or SSRF endpoints |
| **Path Traversal** | `PATH_TRAVERSAL_DETECTED` | Directory traversal sequences (`../`, absolute paths) |
| **XML Entity Hazard** | `XML_ENTITY_HAZARD` | DTD entities, Billion Laughs constructs |
| **Resource Limit** | `RESOURCE_LIMIT` | $> 10,000$ container entries or single line $> 1\text{ MB}$ |
| **Oversized Dimensions**| `OVERSIZED_DIMENSIONS` | Image width or height $> 16,384\text{ px}$ |
| **Duplicate Entry** | `DUPLICATE_ENTRY` | Collision attacks via duplicate filenames in ZIP archives |
