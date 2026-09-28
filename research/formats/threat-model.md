# Multi-Format Threat Model & Attack Vector Catalog

## Executive Summary
This document provides an exhaustive inventory of the 30 threat vectors evaluated against the AegisTrace Multi-Format Forensic Content Architecture, documenting the vulnerability mechanism, risk class, and deterministic fail-closed defense.

---

## 30-Vector Multi-Format Threat Matrix

| # | Vector Name | Target Formats | Risk Class | Mechanism | Defense & Status |
| :- | :--- | :--- | :--- | :--- | :--- |
| **01** | Extension Spoofing | All | Spoofing | Declaring `.xlsx` for a raw PDF payload | Extension cross-check flags mismatch (`is_extension_consistent=False`). `PASS` |
| **02** | MIME Spoofing | All | Spoofing | Sending `text/html` claiming `application/pdf` | Magic byte sniffer detects true MIME. `PASS` |
| **03** | Unknown Binary / Junk | Binary | Tampering | Arbitrary high-entropy random bytes | Rejection with `UNSUPPORTED_FORMAT`. `PASS` |
| **04** | Malformed PDF Header | PDF | DoS / Parser Crash | Corrupted `%PDF-` signature | Fail-closed with `MALFORMED_CONTAINER`. `PASS` |
| **05** | Truncated PDF Trailer | PDF | DoS | Missing `%%EOF` marker in trailing 4KB | Fail-closed with `MALFORMED_CONTAINER`. `PASS` |
| **06** | Malformed DOCX ZIP | DOCX | DoS / Memory Leak | Corrupted central directory headers | Python `zipfile` audit catches `MALFORMED_CONTAINER`. `PASS` |
| **07** | Malformed PPTX | PPTX | DoS | Truncated PresentationML XML stream | Caught with `MALFORMED_CONTAINER`. `PASS` |
| **08** | Malformed XLSX | XLSX | DoS | Broken SpreadsheetML structure | Caught with `MALFORMED_CONTAINER`. `PASS` |
| **09** | ZIP Bomb (Ratio) | OOXML / ODF | DoS / Disk Fill | $> 100:1$ compression ratio | Blocked with `DECOMPRESSION_LIMIT`. `PASS` |
| **10** | ZIP Bomb (Size) | OOXML / ODF | DoS / OOM | $> 150\text{ MB}$ uncompressed expansion | Blocked with `DECOMPRESSION_LIMIT`. `PASS` |
| **11** | Excessive ZIP Entries | OOXML / ODF | DoS / File Table | $> 10,000$ files in archive | Blocked with `RESOURCE_LIMIT`. `PASS` |
| **12** | Path Traversal (Relative) | OOXML / ODF | RCE / Overwrite | Entries like `../../etc/passwd` | Caught with `PATH_TRAVERSAL_DETECTED`. `PASS` |
| **13** | Path Traversal (Absolute) | OOXML / ODF | RCE / Overwrite | Entries starting with `/` or `C:\` | Caught with `PATH_TRAVERSAL_DETECTED`. `PASS` |
| **14** | Duplicate ZIP Entries | OOXML / ODF | Parser Confusion | Two entries with identical filenames | Caught with `DUPLICATE_ENTRY`. `PASS` |
| **15** | Macro-Bearing DOCX | DOCX | Code Execution | Embedded `word/vbaProject.bin` | Blocked with `MACRO_PRESENT`. `PASS` |
| **16** | Macro-Bearing XLSX | XLSX | Code Execution | Embedded `xl/vbaProject.bin` | Blocked with `MACRO_PRESENT`. `PASS` |
| **17** | Macro-Bearing PPTX | PPTX | Code Execution | Embedded `ppt/vbaProject.bin` | Blocked with `MACRO_PRESENT`. `PASS` |
| **18** | External Rel SSRF (DOCX)| DOCX | SSRF / Exfil | Target `http://169.254.169.254/` | Blocked with `EXTERNAL_REFERENCE_PRESENT`. `PASS` |
| **19** | External Rel File (PPTX)| PPTX | Info Leak | Target `file:///C:/Windows/...` | Blocked with `EXTERNAL_REFERENCE_PRESENT`. `PASS` |
| **20** | External Rel FTP (XLSX) | XLSX | Data Exfiltration | Target `ftp://evil.com/` | Blocked with `EXTERNAL_REFERENCE_PRESENT`. `PASS` |
| **21** | XML Entity (XXE DOCX) | DOCX | SSRF / File Read | `<!ENTITY` / `<!DOCTYPE` injection | Blocked with `XML_ENTITY_HAZARD`. `PASS` |
| **22** | XML Entity (XXE XLSX) | XLSX | SSRF / File Read | DTD entity expansion | Blocked with `XML_ENTITY_HAZARD`. `PASS` |
| **23** | Oversized File Upload | All | DoS / Memory Fill | Upload exceeding $100\text{ MB}$ max limit | Blocked with `RESOURCE_LIMIT`. `PASS` |
| **24** | Oversized Image Pixels | PNG / JPEG | DoS / OOM | Dimensions $> 16,384\text{ px}$ | Blocked with `OVERSIZED_DIMENSIONS`. `PASS` |
| **25** | Image Decompression Bomb| PNG / JPEG | DoS / Memory Crash| Pixel count $> 100,000,000\text{ px}$ | Blocked with `DECOMPRESSION_LIMIT`. `PASS` |
| **26** | Polyglot ZIP + JPEG | JPEG / ZIP | Filter Evasion | Appended ZIP archive in JPEG body | Detected with `POLYGLOT_DETECTED`. `PASS` |
| **27** | Polyglot ZIP + PNG | PNG / ZIP | Filter Evasion | Embedded PK header in PNG stream | Detected with `POLYGLOT_DETECTED`. `PASS` |
| **28** | Truncated Image Bytes | PNG / JPEG | Parser Crash | Incomplete bitstream | Caught with `MALFORMED_CONTAINER`. `PASS` |
| **29** | Zero-Byte Payload | All | Logic Error | Empty (0 bytes) upload | Caught with `PARSER_REJECTED`. `PASS` |
| **30** | Executable Binaries | Windows/Linux | Malware Injection | PE `MZ` or ELF `\x7fELF` binaries | Blocked with `TYPE_MISMATCH`. `PASS` |
