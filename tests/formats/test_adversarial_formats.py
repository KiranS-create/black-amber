"""
SIH26237 - 30-Vector Multi-Format Adversarial & Security Attack Test Suite.
Verifies fail-closed zero-trust validation across all format-specific attack vectors.
"""

import io
import zipfile
import pytest
import numpy as np
from PIL import Image

from core.formats.detector import FormatDetector
from core.formats.security import FormatSecurityValidator
from core.formats.models import (
    FormatSecurityException,
    SecurityFailureClass,
    FormatTier
)
from tests.formats.fixtures import (
    create_minimal_pdf_bytes,
    create_minimal_docx_bytes,
    create_minimal_pptx_bytes,
    create_minimal_xlsx_bytes,
    create_minimal_png_bytes,
    create_minimal_jpeg_bytes,
    create_minimal_txt_bytes,
)


class TestAdversarialMultiFormatSuite:
    """Comprehensive 30-vector attack suite covering all format vulnerability surfaces."""

    # 1. Extension Spoofing
    def test_vector_01_extension_spoofing(self):
        pdf_bytes = create_minimal_pdf_bytes()
        res = FormatDetector.identify_format(pdf_bytes, filename="financials.xlsx")
        assert res.detected_format == "PDF"
        assert res.is_extension_consistent is False

    # 2. MIME Spoofing
    def test_vector_02_mime_spoofing(self):
        pdf_bytes = create_minimal_pdf_bytes()
        res = FormatDetector.identify_format(
            pdf_bytes,
            filename="document.pdf",
            declared_mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        assert res.detected_format == "PDF"
        assert res.is_mime_consistent is False

    # 3. Magic Byte Mismatch / Unknown Binary
    def test_vector_03_unknown_binary_rejected(self):
        junk = b"\xde\xad\xbe\xef\x01\x02\x03\x04\x05\x06\x07\x08" * 16
        with pytest.raises(FormatSecurityException) as exc:
            FormatSecurityValidator.validate_artifact(junk, filename="file.unknown")
        assert exc.value.failure_class == SecurityFailureClass.UNSUPPORTED_FORMAT

    # 4. Malformed PDF Header
    def test_vector_04_malformed_pdf_header(self):
        bad_pdf = b"NOT_A_PDF" + (b"\x00" * 200) + b"%%EOF"
        with pytest.raises(FormatSecurityException) as exc:
            FormatSecurityValidator.validate_artifact(bad_pdf, filename="test.pdf")
        assert exc.value.failure_class in (
            SecurityFailureClass.MALFORMED_CONTAINER,
            SecurityFailureClass.UNSUPPORTED_FORMAT
        )

    # 5. Malformed PDF Missing EOF Trailer
    def test_vector_05_malformed_pdf_missing_trailer(self):
        bad_pdf = b"%PDF-1.7\n1 0 obj\n<<>>\nendobj\n"
        with pytest.raises(FormatSecurityException) as exc:
            FormatSecurityValidator.validate_artifact(bad_pdf, filename="test.pdf")
        assert exc.value.failure_class == SecurityFailureClass.MALFORMED_CONTAINER

    # 6. Malformed DOCX ZIP Container
    def test_vector_06_malformed_docx_zip(self):
        truncated_zip = b"PK\x03\x04" + b"\x00" * 50
        with pytest.raises(FormatSecurityException) as exc:
            FormatSecurityValidator.validate_artifact(truncated_zip, filename="corrupt.docx")
        assert exc.value.failure_class == SecurityFailureClass.MALFORMED_CONTAINER

    # 7. Malformed PPTX Container
    def test_vector_07_malformed_pptx_container(self):
        truncated_pptx = b"PK\x03\x04\x14\x00\x00\x00" + b"\xff" * 40
        with pytest.raises(FormatSecurityException) as exc:
            FormatSecurityValidator.validate_artifact(truncated_pptx, filename="broken.pptx")
        assert exc.value.failure_class == SecurityFailureClass.MALFORMED_CONTAINER

    # 8. Malformed XLSX Container
    def test_vector_08_malformed_xlsx_container(self):
        truncated_xlsx = b"PK\x03\x04\x00\x00\x00\x00" + b"\xaa" * 30
        with pytest.raises(FormatSecurityException) as exc:
            FormatSecurityValidator.validate_artifact(truncated_xlsx, filename="broken.xlsx")
        assert exc.value.failure_class == SecurityFailureClass.MALFORMED_CONTAINER

    # 9. ZIP Bomb Decompression Ratio
    def test_vector_09_zip_bomb_ratio(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("word/document.xml", b"0" * (15 * 1024 * 1024))
            zf.writestr("[Content_Types].xml", "<Types/>")
        with pytest.raises(FormatSecurityException) as exc:
            FormatSecurityValidator.validate_artifact(buf.getvalue(), filename="bomb.docx")
        assert exc.value.failure_class == SecurityFailureClass.DECOMPRESSION_LIMIT

    # 10. ZIP Bomb Max Uncompressed Size Limit
    def test_vector_10_zip_bomb_uncompressed_limit(self):
        # Create uncompressed total exceeding 150 MB (mocked via multiple medium parts)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("word/document.xml", b"A" * (60 * 1024 * 1024))
            zf.writestr("word/header1.xml", b"B" * (60 * 1024 * 1024))
            zf.writestr("word/footer1.xml", b"C" * (40 * 1024 * 1024))
            zf.writestr("[Content_Types].xml", "<Types/>")
        with pytest.raises(FormatSecurityException) as exc:
            FormatSecurityValidator.validate_artifact(buf.getvalue(), filename="large_bomb.docx")
        assert exc.value.failure_class == SecurityFailureClass.DECOMPRESSION_LIMIT

    # 11. Excessive ZIP Entries
    def test_vector_11_excessive_zip_entries(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_STORED) as zf:
            zf.writestr("[Content_Types].xml", "<Types/>")
            zf.writestr("word/document.xml", "<w:document/>")
            for i in range(10_005):
                zf.writestr(f"word/media/image_{i}.txt", "x")
        with pytest.raises(FormatSecurityException) as exc:
            FormatSecurityValidator.validate_artifact(buf.getvalue(), filename="many_files.docx")
        assert exc.value.failure_class == SecurityFailureClass.RESOURCE_LIMIT

    # 12. Path Traversal Relative
    def test_vector_12_path_traversal_relative(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr("[Content_Types].xml", "<Types/>")
            zf.writestr("word/document.xml", "<w:document/>")
            zf.writestr("../../../etc/shadow", "root:$6$...")
        with pytest.raises(FormatSecurityException) as exc:
            FormatSecurityValidator.validate_artifact(buf.getvalue(), filename="traversal.docx")
        assert exc.value.failure_class == SecurityFailureClass.PATH_TRAVERSAL_DETECTED

    # 13. Path Traversal Absolute
    def test_vector_13_path_traversal_absolute(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr("[Content_Types].xml", "<Types/>")
            zf.writestr("word/document.xml", "<w:document/>")
            zf.writestr("/var/log/auth.log", "malicious log entry")
        with pytest.raises(FormatSecurityException) as exc:
            FormatSecurityValidator.validate_artifact(buf.getvalue(), filename="abs_traversal.docx")
        assert exc.value.failure_class == SecurityFailureClass.PATH_TRAVERSAL_DETECTED

    # 14. Duplicate ZIP Entry Attack
    def test_vector_14_duplicate_zip_entry(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr("[Content_Types].xml", "<Types/>")
            zf.writestr("word/document.xml", "<w:document>Benign</w:document>")
            zf.writestr("word/document.xml", "<w:document>Malicious</w:document>")
        with pytest.raises(FormatSecurityException) as exc:
            FormatSecurityValidator.validate_artifact(buf.getvalue(), filename="dup.docx")
        assert exc.value.failure_class == SecurityFailureClass.DUPLICATE_ENTRY

    # 15. Macro-bearing DOCX
    def test_vector_15_macro_bearing_docx(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr("[Content_Types].xml", "<Types/>")
            zf.writestr("word/document.xml", "<w:document/>")
            zf.writestr("word/vbaProject.bin", b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")
        with pytest.raises(FormatSecurityException) as exc:
            FormatSecurityValidator.validate_artifact(buf.getvalue(), filename="has_vba.docx")
        assert exc.value.failure_class == SecurityFailureClass.MACRO_PRESENT

    # 16. Macro-bearing XLSX
    def test_vector_16_macro_bearing_xlsx(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr("[Content_Types].xml", "<Types/>")
            zf.writestr("xl/workbook.xml", "<workbook/>")
            zf.writestr("xl/vbaProject.bin", b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")
        with pytest.raises(FormatSecurityException) as exc:
            FormatSecurityValidator.validate_artifact(buf.getvalue(), filename="has_vba.xlsx")
        assert exc.value.failure_class == SecurityFailureClass.MACRO_PRESENT

    # 17. Macro-bearing PPTX
    def test_vector_17_macro_bearing_pptx(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr("[Content_Types].xml", "<Types/>")
            zf.writestr("ppt/presentation.xml", "<presentation/>")
            zf.writestr("ppt/vbaProject.bin", b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")
        with pytest.raises(FormatSecurityException) as exc:
            FormatSecurityValidator.validate_artifact(buf.getvalue(), filename="has_vba.pptx")
        assert exc.value.failure_class == SecurityFailureClass.MACRO_PRESENT

    # 18. External Relationship in DOCX (SSRF)
    def test_vector_18_external_rel_docx(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr("[Content_Types].xml", "<Types/>")
            zf.writestr("word/document.xml", "<w:document/>")
            zf.writestr(
                "word/_rels/document.xml.rels",
                '<Relationships><Relationship Target="http://169.254.169.254/latest/meta-data/" TargetMode="External"/></Relationships>'
            )
        with pytest.raises(FormatSecurityException) as exc:
            FormatSecurityValidator.validate_artifact(buf.getvalue(), filename="ssrf.docx")
        assert exc.value.failure_class == SecurityFailureClass.EXTERNAL_REFERENCE_PRESENT

    # 19. External Relationship in PPTX (file:// leak)
    def test_vector_19_external_rel_pptx(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr("[Content_Types].xml", "<Types/>")
            zf.writestr("ppt/presentation.xml", "<p:presentation/>")
            zf.writestr(
                "ppt/_rels/presentation.xml.rels",
                '<Relationships><Relationship Target="file:///C:/Windows/System32/drivers/etc/hosts" TargetMode="External"/></Relationships>'
            )
        with pytest.raises(FormatSecurityException) as exc:
            FormatSecurityValidator.validate_artifact(buf.getvalue(), filename="file_leak.pptx")
        assert exc.value.failure_class == SecurityFailureClass.EXTERNAL_REFERENCE_PRESENT

    # 20. External Relationship in XLSX (ftp:// exfil)
    def test_vector_20_external_rel_xlsx(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr("[Content_Types].xml", "<Types/>")
            zf.writestr("xl/workbook.xml", "<workbook/>")
            zf.writestr(
                "xl/_rels/workbook.xml.rels",
                '<Relationships><Relationship Target="ftp://evil.com/drop" TargetMode="External"/></Relationships>'
            )
        with pytest.raises(FormatSecurityException) as exc:
            FormatSecurityValidator.validate_artifact(buf.getvalue(), filename="ftp_leak.xlsx")
        assert exc.value.failure_class == SecurityFailureClass.EXTERNAL_REFERENCE_PRESENT

    # 21. XML Entity Expansion in DOCX
    def test_vector_21_xml_entity_expansion_docx(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr("[Content_Types].xml", "<Types/>")
            zf.writestr("word/document.xml", '<!DOCTYPE test [ <!ENTITY xxe "evil"> ]><w:document>&xxe;</w:document>')
        with pytest.raises(FormatSecurityException) as exc:
            FormatSecurityValidator.validate_artifact(buf.getvalue(), filename="xxe.docx")
        assert exc.value.failure_class in (
            SecurityFailureClass.XML_ENTITY_HAZARD,
            SecurityFailureClass.EXTERNAL_REFERENCE_PRESENT
        )

    # 22. XML Entity Expansion in XLSX
    def test_vector_22_xml_entity_expansion_xlsx(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr("[Content_Types].xml", "<Types/>")
            zf.writestr("xl/workbook.xml", '<!DOCTYPE sheet [ <!ENTITY dtd SYSTEM "http://evil.com/dtd"> ]><workbook>&dtd;</workbook>')
        with pytest.raises(FormatSecurityException) as exc:
            FormatSecurityValidator.validate_artifact(buf.getvalue(), filename="xxe.xlsx")
        assert exc.value.failure_class in (
            SecurityFailureClass.XML_ENTITY_HAZARD,
            SecurityFailureClass.EXTERNAL_REFERENCE_PRESENT
        )

    # 23. Oversized File Upload (> 100MB)
    def test_vector_23_oversized_file_upload(self):
        # We test with a small max_size parameter override to keep unit test instant and bounded
        fake_data = b"A" * 1024 * 1024 # 1 MB
        with pytest.raises(FormatSecurityException) as exc:
            FormatSecurityValidator.validate_artifact(fake_data, filename="big.pdf", max_size=512 * 1024)
        assert exc.value.failure_class == SecurityFailureClass.RESOURCE_LIMIT

    # 24. Oversized Image Dimensions (> 16384px)
    def test_vector_24_oversized_image_dimensions(self):
        # Create image metadata exceeding 16384 px
        img = Image.new("RGB", (20000, 100))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        with pytest.raises(FormatSecurityException) as exc:
            FormatSecurityValidator.validate_artifact(buf.getvalue(), filename="wide.png")
        assert exc.value.failure_class in (
            SecurityFailureClass.OVERSIZED_DIMENSIONS,
            SecurityFailureClass.DECOMPRESSION_LIMIT
        )

    # 25. Decompression Bomb in Image (> 100M total pixels)
    def test_vector_25_image_decompression_bomb(self):
        img = Image.new("RGB", (12000, 10000))  # 120M pixels
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        with pytest.raises(FormatSecurityException) as exc:
            FormatSecurityValidator.validate_artifact(buf.getvalue(), filename="pixel_bomb.png")
        assert exc.value.failure_class in (
            SecurityFailureClass.DECOMPRESSION_LIMIT,
            SecurityFailureClass.OVERSIZED_DIMENSIONS
        )

    # 26. Polyglot ZIP + JPEG
    def test_vector_26_polyglot_zip_jpeg(self):
        docx_bytes = create_minimal_docx_bytes()
        polyglot = b"\xff\xd8\xff\xe0\x00\x10JFIF" + (b"\x00" * 64) + docx_bytes
        with pytest.raises(FormatSecurityException) as exc:
            FormatSecurityValidator.validate_artifact(polyglot, filename="poly.jpg")
        assert exc.value.failure_class == SecurityFailureClass.POLYGLOT_DETECTED

    # 27. Polyglot ZIP + PNG
    def test_vector_27_polyglot_zip_png(self):
        docx_bytes = create_minimal_docx_bytes()
        polyglot = b"\x89PNG\r\n\x1a\n" + (b"\x00" * 64) + docx_bytes
        with pytest.raises(FormatSecurityException) as exc:
            FormatSecurityValidator.validate_artifact(polyglot, filename="poly.png")
        assert exc.value.failure_class == SecurityFailureClass.POLYGLOT_DETECTED

    # 28. Truncated Image Bytes
    def test_vector_28_truncated_image_bytes(self):
        png_bytes = create_minimal_png_bytes()
        truncated = png_bytes[:20]  # Chop off middle and end chunks
        with pytest.raises(FormatSecurityException) as exc:
            FormatSecurityValidator.validate_artifact(truncated, filename="broken.png")
        assert exc.value.failure_class in (
            SecurityFailureClass.MALFORMED_CONTAINER,
            SecurityFailureClass.PARSER_REJECTED
        )

    # 29. Zero-Byte Payload
    def test_vector_29_zero_byte_payload(self):
        with pytest.raises(FormatSecurityException) as exc:
            FormatSecurityValidator.validate_artifact(b"", filename="empty.pdf")
        assert exc.value.failure_class == SecurityFailureClass.PARSER_REJECTED

    # 30. Dangerous Executable Payload (PE MZ / ELF)
    def test_vector_30_dangerous_executable_payload(self):
        pe_exe = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00" + (b"\x00" * 100)
        with pytest.raises(FormatSecurityException) as exc:
            FormatSecurityValidator.validate_artifact(pe_exe, filename="report.pdf")
        assert exc.value.failure_class == SecurityFailureClass.TYPE_MISMATCH

        elf_bin = b"\x7fELF\x02\x01\x01\x00" + (b"\x00" * 100)
        with pytest.raises(FormatSecurityException) as exc2:
            FormatSecurityValidator.validate_artifact(elf_bin, filename="data.xlsx")
        assert exc2.value.failure_class == SecurityFailureClass.TYPE_MISMATCH
