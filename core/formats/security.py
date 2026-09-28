"""
SIH26237 - Multi-Format Zero-Trust Security Validator.
Enforces strict container integrity, decompression limits, path traversal defenses,
macro/active content rejection, external relationship auditing, and XML entity expansion bounds.
"""

import io
import os
import re
import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple, Any, Set
from PIL import Image

from core.formats.models import (
    SecurityFailureClass,
    SecurityValidationResult,
    FormatSecurityException,
    FormatTier
)
from core.formats.detector import FormatDetector


# Configure PIL decompression bomb ceiling (100 Megapixels max)
Image.MAX_IMAGE_PIXELS = 100_000_000

MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024       # 100 MB max uploaded file
MAX_UNCOMPRESSED_SIZE_BYTES = 150 * 1024 * 1024 # 150 MB max uncompressed container
MAX_COMPRESSION_RATIO = 100.0                 # Max 100:1 compression ratio
MAX_CONTAINER_ENTRIES = 10_000                # Max 10,000 files in archive
MAX_IMAGE_DIMENSION_PX = 16_384               # Max 16,384 px width or height


class FormatSecurityValidator:
    """
    Comprehensive zero-trust security validator for all ingested multi-format artifacts.
    """

    MACRO_FILE_PATTERNS = [
        re.compile(r"vbaProject\.bin$", re.IGNORECASE),
        re.compile(r"word/vba.*\.xml$", re.IGNORECASE),
        re.compile(r"xl/vba.*\.xml$", re.IGNORECASE),
        re.compile(r"ppt/vba.*\.xml$", re.IGNORECASE),
        re.compile(r"activeX.*\.bin$", re.IGNORECASE),
        re.compile(r"activeX.*\.xml$", re.IGNORECASE),
        re.compile(r"oleObject.*\.bin$", re.IGNORECASE),
        re.compile(r".*\.vbs$", re.IGNORECASE),
        re.compile(r".*\.exe$", re.IGNORECASE),
        re.compile(r".*\.dll$", re.IGNORECASE),
        re.compile(r".*\.bat$", re.IGNORECASE),
        re.compile(r".*\.ps1$", re.IGNORECASE),
    ]

    EXTERNAL_RELATIONSHIP_PATTERNS = [
        re.compile(r'TargetMode=["\']External["\']', re.IGNORECASE),
        re.compile(r'Target=["\']https?://', re.IGNORECASE),
        re.compile(r'Target=["\']ftp://', re.IGNORECASE),
        re.compile(r'Target=["\']file://', re.IGNORECASE),
        re.compile(r'Target=["\']script:', re.IGNORECASE),
    ]

    XML_ENTITY_HAZARD_PATTERNS = [
        re.compile(r'<!ENTITY', re.IGNORECASE),
        re.compile(r'<!DOCTYPE[^>]*\[', re.IGNORECASE),
        re.compile(r'SYSTEM\s+["\']', re.IGNORECASE),
        re.compile(r'PUBLIC\s+["\']', re.IGNORECASE),
    ]

    @classmethod
    def validate_artifact(
        cls,
        data: bytes,
        filename: Optional[str] = None,
        declared_mime: Optional[str] = None,
        max_size: Optional[int] = None
    ) -> SecurityValidationResult:
        """
        Executes full multi-stage security validation on raw artifact bytes.
        Fails closed on any security anomaly.
        """
        effective_max = max_size or MAX_FILE_SIZE_BYTES

        # 1. Size bounds check
        if not data or len(data) == 0:
            raise FormatSecurityException(
                failure_class=SecurityFailureClass.PARSER_REJECTED,
                message="Uploaded payload is empty (0 bytes)."
            )

        if len(data) > effective_max:
            raise FormatSecurityException(
                failure_class=SecurityFailureClass.RESOURCE_LIMIT,
                message=f"Payload size ({len(data)} bytes) exceeds maximum limit ({effective_max} bytes).",
                details={"max_size": effective_max, "actual_size": len(data)}
            )

        # 2. Format identification
        id_result = FormatDetector.identify_format(data, filename, declared_mime)

        if id_result.is_polyglot:
            raise FormatSecurityException(
                failure_class=SecurityFailureClass.POLYGLOT_DETECTED,
                message="Polyglot payload detected: file contains conflicting embedded container headers.",
                details={"detected_format": id_result.detected_format}
            )

        # 3. Format-specific zero-trust deep validation
        fmt = id_result.detected_format
        warnings: List[str] = []
        security_details: Dict[str, Any] = {"format": fmt}

        if fmt in ["DOCX", "PPTX", "XLSX", "ODT", "ODS", "ODP", "ZIP"]:
            cls._validate_zip_ooxml_container(data, fmt, security_details)
        elif fmt == "PDF":
            cls._validate_pdf(data, security_details)
        elif fmt in ["PNG", "JPEG"]:
            cls._validate_raster_image(data, fmt, security_details)
        elif fmt in ["TXT", "CSV"]:
            cls._validate_text(data, fmt, security_details)
        elif fmt == "UNKNOWN":
            raise FormatSecurityException(
                failure_class=SecurityFailureClass.UNSUPPORTED_FORMAT,
                message="File format is unrecognized or unsupported."
            )

        return SecurityValidationResult(
            is_safe=True,
            failure_class=None,
            detected_mime=id_result.mime_type,
            detected_extension=id_result.extension,
            file_size_bytes=len(data),
            uncompressed_size_bytes=security_details.get("uncompressed_size_bytes", len(data)),
            compression_ratio=security_details.get("compression_ratio", 1.0),
            container_entry_count=security_details.get("entry_count", 1),
            warnings=warnings,
            security_details=security_details
        )

    @classmethod
    def _validate_zip_ooxml_container(cls, data: bytes, fmt: str, details: Dict[str, Any]) -> None:
        """
        Deep security audit of ZIP and OpenXML containers.
        Guards against ZIP bombs, path traversals, macros, external references, and XML bombs.
        """
        try:
            zf = zipfile.ZipFile(io.BytesIO(data), 'r')
        except zipfile.BadZipFile:
            raise FormatSecurityException(
                failure_class=SecurityFailureClass.MALFORMED_CONTAINER,
                message="Corrupted or invalid ZIP container structure."
            )
        except Exception as e:
            raise FormatSecurityException(
                failure_class=SecurityFailureClass.MALFORMED_CONTAINER,
                message=f"ZIP inspection failure: {str(e)}"
            )

        infolist = zf.infolist()
        entry_count = len(infolist)
        details["entry_count"] = entry_count

        if entry_count > MAX_CONTAINER_ENTRIES:
            raise FormatSecurityException(
                failure_class=SecurityFailureClass.RESOURCE_LIMIT,
                message=f"Container entry count ({entry_count}) exceeds limit ({MAX_CONTAINER_ENTRIES})."
            )

        total_uncompressed = 0
        seen_names: Set[str] = set()

        for info in infolist:
            name = info.filename
            
            # Path traversal checks
            if ".." in name or name.startswith("/") or name.startswith("\\") or "\x00" in name or os.path.isabs(name):
                raise FormatSecurityException(
                    failure_class=SecurityFailureClass.PATH_TRAVERSAL_DETECTED,
                    message=f"Path traversal or illegal characters detected in container entry: '{name}'"
                )

            # Duplicate entry attack check
            if name in seen_names:
                raise FormatSecurityException(
                    failure_class=SecurityFailureClass.DUPLICATE_ENTRY,
                    message=f"Duplicate entry detected in ZIP archive: '{name}'"
                )
            seen_names.add(name)

            # Macro and dangerous binary detection
            for pattern in cls.MACRO_FILE_PATTERNS:
                if pattern.search(name):
                    raise FormatSecurityException(
                        failure_class=SecurityFailureClass.MACRO_PRESENT,
                        message=f"Embedded macro, script, or executable component detected: '{name}'"
                    )

            total_uncompressed += info.file_size

        details["uncompressed_size_bytes"] = total_uncompressed
        ratio = float(total_uncompressed) / max(1, len(data))
        details["compression_ratio"] = round(ratio, 2)

        # ZIP Bomb defenses
        if total_uncompressed > MAX_UNCOMPRESSED_SIZE_BYTES:
            raise FormatSecurityException(
                failure_class=SecurityFailureClass.DECOMPRESSION_LIMIT,
                message=f"Total uncompressed size ({total_uncompressed} bytes) exceeds limit ({MAX_UNCOMPRESSED_SIZE_BYTES} bytes)."
            )

        if ratio > MAX_COMPRESSION_RATIO:
            raise FormatSecurityException(
                failure_class=SecurityFailureClass.DECOMPRESSION_LIMIT,
                message=f"Excessive compression ratio ({ratio:.1f}:1) indicates possible decompression bomb."
            )

        # XML entity expansion & external relationship audit on XML files
        for info in infolist:
            if info.filename.endswith(".xml") or info.filename.endswith(".rels"):
                try:
                    entry_data = zf.read(info.filename)
                except Exception as e:
                    raise FormatSecurityException(
                        failure_class=SecurityFailureClass.MALFORMED_CONTAINER,
                        message=f"Failed to read container entry '{info.filename}': {str(e)}"
                    )

                text_content = entry_data.decode("utf-8", errors="ignore")

                # XML entity hazard check
                for pat in cls.XML_ENTITY_HAZARD_PATTERNS:
                    if pat.search(text_content):
                        raise FormatSecurityException(
                            failure_class=SecurityFailureClass.XML_ENTITY_HAZARD,
                            message=f"XML entity expansion or DTD declaration detected in '{info.filename}'"
                        )

                # External relationship check (SSRF prevention)
                if info.filename.endswith(".rels"):
                    for pat in cls.EXTERNAL_RELATIONSHIP_PATTERNS:
                        if pat.search(text_content):
                            raise FormatSecurityException(
                                failure_class=SecurityFailureClass.EXTERNAL_REFERENCE_PRESENT,
                                message=f"External relationship reference rejected in '{info.filename}'"
                            )

    @classmethod
    def _validate_pdf(cls, data: bytes, details: Dict[str, Any]) -> None:
        """Validates PDF structure, rejects unauthenticated encryption and embedded active scripts."""
        if not data.startswith(b"%PDF-"):
            raise FormatSecurityException(
                failure_class=SecurityFailureClass.MALFORMED_CONTAINER,
                message="Malformed PDF header: missing %PDF- magic signature."
            )

        # Check for trailing EOF marker in last 4 KB
        tail = data[-4096:]
        if b"%%EOF" not in tail:
            raise FormatSecurityException(
                failure_class=SecurityFailureClass.MALFORMED_CONTAINER,
                message="Malformed or truncated PDF: missing %%EOF trailer marker."
            )

        # Check for active script payloads (/JavaScript, /JS, /Launch)
        sample = data[:65536] + tail
        if b"/JavaScript" in sample or b"/JS " in sample or b"/Launch " in sample:
            raise FormatSecurityException(
                failure_class=SecurityFailureClass.MACRO_PRESENT,
                message="Active JavaScript or Launch action detected in PDF document."
            )

        # Check for password-protected / encrypted PDF
        if b"/Encrypt" in data:
            raise FormatSecurityException(
                failure_class=SecurityFailureClass.UNSUPPORTED_ENCRYPTION,
                message="Unsupported password-protected or encrypted PDF payload."
            )

    @classmethod
    def _validate_raster_image(cls, data: bytes, fmt: str, details: Dict[str, Any]) -> None:
        """Validates raster image integrity and prevents decompression bombs."""
        try:
            with Image.open(io.BytesIO(data)) as img:
                w, h = img.size
                details["width_px"] = w
                details["height_px"] = h
                details["image_mode"] = img.mode

                if w > MAX_IMAGE_DIMENSION_PX or h > MAX_IMAGE_DIMENSION_PX:
                    raise FormatSecurityException(
                        failure_class=SecurityFailureClass.OVERSIZED_DIMENSIONS,
                        message=f"Image dimensions ({w}x{h}) exceed maximum allowable limit ({MAX_IMAGE_DIMENSION_PX}px)."
                    )

                total_pixels = w * h
                if total_pixels > Image.MAX_IMAGE_PIXELS:
                    raise FormatSecurityException(
                        failure_class=SecurityFailureClass.DECOMPRESSION_LIMIT,
                        message=f"Total pixel count ({total_pixels}) exceeds decompression bomb limit."
                    )

                # Verify image can be decoded without crashing
                img.verify()
        except FormatSecurityException:
            raise
        except Exception as e:
            raise FormatSecurityException(
                failure_class=SecurityFailureClass.MALFORMED_CONTAINER,
                message=f"Malformed or corrupted {fmt} image: {str(e)}"
            )

    @classmethod
    def _validate_text(cls, data: bytes, fmt: str, details: Dict[str, Any]) -> None:
        """Validates plain text or CSV data."""
        if b"\x00" in data:
            raise FormatSecurityException(
                failure_class=SecurityFailureClass.TYPE_MISMATCH,
                message="Null bytes detected in text payload; binary payload rejected."
            )

        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = data.decode("latin-1")
            except Exception as e:
                raise FormatSecurityException(
                    failure_class=SecurityFailureClass.PARSER_REJECTED,
                    message=f"Text decoding failed: {str(e)}"
                )

        lines = text.splitlines()
        details["line_count"] = len(lines)

        # Check line length bounds (max 1 MB per line)
        for idx, line in enumerate(lines[:1000]):
            if len(line) > 1024 * 1024:
                raise FormatSecurityException(
                    failure_class=SecurityFailureClass.RESOURCE_LIMIT,
                    message=f"Line {idx+1} exceeds maximum line length limit (1 MB)."
                )
