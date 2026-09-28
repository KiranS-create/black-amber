"""
SIH26237 - Multi-Format Identification & Magic-Byte Detection Engine.
Performs zero-trust file signature sniffing, MIME classification, extension cross-validation,
and polyglot container detection without relying on untrusted client headers.
"""

import io
import os
import zipfile
import csv
from typing import Dict, List, Optional, Tuple, Any

from core.formats.models import (
    FormatTier,
    FormatIdentificationResult,
    SecurityFailureClass,
    FormatSecurityException
)


class FormatDetector:
    """
    Robust file type detector operating strictly on raw magic bytes,
    internal container structure, and content signatures.
    """

    MAGIC_SIGNATURES: List[Tuple[bytes, str, str, str, FormatTier]] = [
        # Magic bytes, format_name, extension, mime_type, tier
        (b"%PDF", "PDF", "pdf", "application/pdf", FormatTier.TIER_1),
        (b"\x89PNG\r\n\x1a\n", "PNG", "png", "image/png", FormatTier.TIER_1),
        (b"\xff\xd8\xff", "JPEG", "jpg", "image/jpeg", FormatTier.TIER_1),
        (b"{\\rtf", "RTF", "rtf", "application/rtf", FormatTier.TIER_2),
        (b"GIF87a", "GIF", "gif", "image/gif", FormatTier.TIER_3),
        (b"GIF89a", "GIF", "gif", "image/gif", FormatTier.TIER_3),
        (b"II*\x00", "TIFF", "tiff", "image/tiff", FormatTier.TIER_3),
        (b"MM\x00*", "TIFF", "tiff", "image/tiff", FormatTier.TIER_3),
        (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1", "OLE2", "doc", "application/x-ole-storage", FormatTier.TIER_3),
    ]

    DANGEROUS_EXECUTABLE_SIGNATURES: List[Tuple[bytes, str]] = [
        (b"MZ", "Windows PE Executable / DLL"),
        (b"\x7fELF", "Linux ELF Executable"),
        (b"#!", "Unix Shell Script"),
        (b"\xca\xfe\xba\xbe", "Java Class File / Mach-O Binary"),
        (b"\xfe\xed\xfa\xce", "Mach-O 32-bit"),
        (b"\xfe\xed\xfa\xcf", "Mach-O 64-bit"),
    ]

    @classmethod
    def identify_format(
        cls,
        data: bytes,
        filename: Optional[str] = None,
        declared_mime: Optional[str] = None
    ) -> FormatIdentificationResult:
        """
        Identifies the exact format and verifies consistency across bytes, extension, and MIME.
        """
        if not data or len(data) == 0:
            raise FormatSecurityException(
                failure_class=SecurityFailureClass.PARSER_REJECTED,
                message="Uploaded payload is empty (0 bytes)."
            )

        declared_ext = ""
        if filename:
            _, ext = os.path.splitext(filename)
            declared_ext = ext.lstrip(".").lower()

        magic_hex = data[:16].hex()

        # 1. Check for prohibited dangerous binaries
        for sig, desc in cls.DANGEROUS_EXECUTABLE_SIGNATURES:
            if data.startswith(sig):
                raise FormatSecurityException(
                    failure_class=SecurityFailureClass.TYPE_MISMATCH,
                    message=f"Executable binary payload ({desc}) rejected by zero-trust policy.",
                    details={"signature_hex": magic_hex, "description": desc}
                )

        # 2. Check direct magic byte signatures
        for sig, fmt, ext, mime, tier in cls.MAGIC_SIGNATURES:
            if data.startswith(sig):
                # Check for polyglot container embedding (e.g. image with appended ZIP archive)
                is_poly = cls._check_polyglot_zip(data, expected_format=fmt)
                is_ext_consistent = True
                if declared_ext:
                    # jpg vs jpeg aliases
                    if fmt == "JPEG" and declared_ext in ["jpg", "jpeg", "jpe", "jfif"]:
                        is_ext_consistent = True
                    elif fmt == "TIFF" and declared_ext in ["tif", "tiff"]:
                        is_ext_consistent = True
                    else:
                        is_ext_consistent = (declared_ext == ext)

                is_mime_consistent = True
                if declared_mime:
                    is_mime_consistent = (declared_mime.lower() == mime.lower())

                return FormatIdentificationResult(
                    detected_format=fmt,
                    mime_type=mime,
                    extension=ext,
                    format_tier=tier,
                    magic_bytes_hex=magic_hex,
                    is_extension_consistent=is_ext_consistent,
                    is_mime_consistent=is_mime_consistent,
                    is_polyglot=is_poly,
                    confidence=1.0
                )

        # 3. Check ZIP-based containers (DOCX, PPTX, XLSX, ODT, ODS, ODP, ZIP)
        if data.startswith(b"PK\x03\x04") or data.startswith(b"PK\x05\x06") or data.startswith(b"PK\x07\x08"):
            return cls._identify_zip_container(data, declared_ext, declared_mime, magic_hex)

        # 4. Check Plaintext / CSV
        text_id = cls._identify_text_or_csv(data, declared_ext, declared_mime, magic_hex)
        if text_id:
            return text_id

        # 5. Unsupported / Unknown Binary
        return FormatIdentificationResult(
            detected_format="UNKNOWN",
            mime_type="application/octet-stream",
            extension=declared_ext or "bin",
            format_tier=FormatTier.TIER_3,
            magic_bytes_hex=magic_hex,
            is_extension_consistent=False,
            is_mime_consistent=False,
            is_polyglot=False,
            confidence=0.1
        )

    @classmethod
    def _identify_zip_container(
        cls,
        data: bytes,
        declared_ext: str,
        declared_mime: Optional[str],
        magic_hex: str
    ) -> FormatIdentificationResult:
        """Inspects internal ZIP structure to distinguish OOXML, ODF, and generic ZIPs."""
        try:
            with zipfile.ZipFile(io.BytesIO(data), 'r') as zf:
                namelist = zf.namelist()
                name_set = set(namelist)

                # OOXML Detection
                # Check [Content_Types].xml or internal directory structure
                is_ooxml = "[Content_Types].xml" in name_set or "_rels/.rels" in name_set

                if is_ooxml:
                    # Check content types if readable
                    content_types_data = b""
                    if "[Content_Types].xml" in name_set:
                        try:
                            content_types_data = zf.read("[Content_Types].xml")
                        except Exception:
                            pass

                    # DOCX
                    if any(n.startswith("word/") for n in name_set) or b"wordprocessingml" in content_types_data:
                        return FormatIdentificationResult(
                            detected_format="DOCX",
                            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            extension="docx",
                            format_tier=FormatTier.TIER_1,
                            magic_bytes_hex=magic_hex,
                            is_extension_consistent=(declared_ext == "docx"),
                            is_mime_consistent=(declared_mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" if declared_mime else True),
                            is_polyglot=False,
                            confidence=1.0
                        )

                    # PPTX
                    if any(n.startswith("ppt/") for n in name_set) or b"presentationml" in content_types_data:
                        return FormatIdentificationResult(
                            detected_format="PPTX",
                            mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                            extension="pptx",
                            format_tier=FormatTier.TIER_1,
                            magic_bytes_hex=magic_hex,
                            is_extension_consistent=(declared_ext == "pptx"),
                            is_mime_consistent=(declared_mime == "application/vnd.openxmlformats-officedocument.presentationml.presentation" if declared_mime else True),
                            is_polyglot=False,
                            confidence=1.0
                        )

                    # XLSX
                    if any(n.startswith("xl/") for n in name_set) or b"spreadsheetml" in content_types_data:
                        return FormatIdentificationResult(
                            detected_format="XLSX",
                            mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            extension="xlsx",
                            format_tier=FormatTier.TIER_1,
                            magic_bytes_hex=magic_hex,
                            is_extension_consistent=(declared_ext == "xlsx"),
                            is_mime_consistent=(declared_mime == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if declared_mime else True),
                            is_polyglot=False,
                            confidence=1.0
                        )

                # OpenDocument (ODF) Detection via 'mimetype' or 'content.xml' entry
                if "mimetype" in name_set or "content.xml" in name_set:
                    mime_content = ""
                    if "mimetype" in name_set:
                        mime_content = zf.read("mimetype").decode("utf-8", errors="ignore").strip()
                    if not mime_content and "content.xml" in name_set:
                        content_data = zf.read("content.xml").decode("utf-8", errors="ignore")
                        if "office:document-content" in content_data or "urn:oasis:names:tc:opendocument" in content_data:
                            mime_content = "oasis.opendocument.text"

                    if "oasis.opendocument.text" in mime_content or "opendocument.text" in mime_content:
                        return FormatIdentificationResult(
                            detected_format="ODT",
                            mime_type="application/vnd.oasis.opendocument.text",
                            extension="odt",
                            format_tier=FormatTier.TIER_2,
                            magic_bytes_hex=magic_hex,
                            is_extension_consistent=(declared_ext == "odt"),
                            is_mime_consistent=(declared_mime == "application/vnd.oasis.opendocument.text" if declared_mime else True),
                            is_polyglot=False,
                            confidence=1.0
                        )
                    if "oasis.opendocument.spreadsheet" in mime_content or "opendocument.spreadsheet" in mime_content:
                        return FormatIdentificationResult(
                            detected_format="ODS",
                            mime_type="application/vnd.oasis.opendocument.spreadsheet",
                            extension="ods",
                            format_tier=FormatTier.TIER_2,
                            magic_bytes_hex=magic_hex,
                            is_extension_consistent=(declared_ext == "ods"),
                            is_mime_consistent=(declared_mime == "application/vnd.oasis.opendocument.spreadsheet" if declared_mime else True),
                            is_polyglot=False,
                            confidence=1.0
                        )
                    if "oasis.opendocument.presentation" in mime_content or "opendocument.presentation" in mime_content:
                        return FormatIdentificationResult(
                            detected_format="ODP",
                            mime_type="application/vnd.oasis.opendocument.presentation",
                            extension="odp",
                            format_tier=FormatTier.TIER_2,
                            magic_bytes_hex=magic_hex,
                            is_extension_consistent=(declared_ext == "odp"),
                            is_mime_consistent=(declared_mime == "application/vnd.oasis.opendocument.presentation" if declared_mime else True),
                            is_polyglot=False,
                            confidence=1.0
                        )

                # Generic ZIP
                return FormatIdentificationResult(
                    detected_format="ZIP",
                    mime_type="application/zip",
                    extension="zip",
                    format_tier=FormatTier.TIER_3,
                    magic_bytes_hex=magic_hex,
                    is_extension_consistent=(declared_ext == "zip"),
                    is_mime_consistent=(declared_mime in ["application/zip", "application/x-zip-compressed"] if declared_mime else True),
                    is_polyglot=False,
                    confidence=0.9
                )
        except zipfile.BadZipFile:
            raise FormatSecurityException(
                failure_class=SecurityFailureClass.MALFORMED_CONTAINER,
                message="Corrupted or malformed ZIP header."
            )
        except Exception as e:
            raise FormatSecurityException(
                failure_class=SecurityFailureClass.MALFORMED_CONTAINER,
                message=f"ZIP parsing failure: {str(e)}"
            )

    @classmethod
    def _identify_text_or_csv(
        cls,
        data: bytes,
        declared_ext: str,
        declared_mime: Optional[str],
        magic_hex: str
    ) -> Optional[FormatIdentificationResult]:
        """Sniffs whether binary data is valid plaintext or structured CSV."""
        # Null bytes indicate binary data, not plain text
        if b"\x00" in data[:4096]:
            return None

        # Attempt UTF-8 decode
        try:
            sample_text = data[:8192].decode("utf-8")
        except UnicodeDecodeError:
            return None

        # Verify that sample consists almost entirely of printable characters or standard whitespace
        printable_count = sum(1 for ch in sample_text if ch.isprintable() or ch in ('\n', '\r', '\t'))
        if len(sample_text) == 0 or (printable_count / len(sample_text)) < 0.95:
            return None

        # Check for HTML / Script injections
        lower_sample = sample_text.lower()
        if "<!doctype html" in lower_sample or "<html" in lower_sample:
            return FormatIdentificationResult(
                detected_format="HTML",
                mime_type="text/html",
                extension="html",
                format_tier=FormatTier.TIER_3,
                magic_bytes_hex=magic_hex,
                is_extension_consistent=(declared_ext in ["html", "htm"]),
                is_mime_consistent=True,
                confidence=0.95
            )

        # Check for CSV structure
        lines = [line.strip() for line in sample_text.splitlines() if line.strip()]
        if len(lines) >= 2:
            # Check for delimiters: comma, semicolon, tab
            for delimiter in [',', ';', '\t']:
                counts = [line.count(delimiter) for line in lines[:10]]
                if counts[0] > 0 and all(c == counts[0] for c in counts):
                    return FormatIdentificationResult(
                        detected_format="CSV",
                        mime_type="text/csv",
                        extension="csv",
                        format_tier=FormatTier.TIER_2,
                        magic_bytes_hex=magic_hex,
                        is_extension_consistent=(declared_ext == "csv"),
                        is_mime_consistent=(declared_mime in ["text/csv", "text/plain"] if declared_mime else True),
                        confidence=0.9
                    )

        # Generic Plaintext
        return FormatIdentificationResult(
            detected_format="TXT",
            mime_type="text/plain",
            extension="txt",
            format_tier=FormatTier.TIER_2,
            magic_bytes_hex=magic_hex,
            is_extension_consistent=(declared_ext in ["txt", "text", "log"]),
            is_mime_consistent=(declared_mime in ["text/plain"] if declared_mime else True),
            confidence=0.85
        )

    @classmethod
    def _check_polyglot_zip(cls, data: bytes, expected_format: str) -> bool:
        """
        Detects polyglot payloads where a valid file format (e.g. PNG, JPEG, PDF)
        contains an embedded ZIP archive header at an offset.
        """
        if expected_format in ["PNG", "JPEG", "PDF"]:
            # Search for embedded PK header after offset 64
            pk_pos = data.find(b"PK\x03\x04", 64)
            if pk_pos > 0:
                # Validate if it constitutes a functional ZIP trailer
                if b"PK\x05\x06" in data[pk_pos:]:
                    return True
        return False
