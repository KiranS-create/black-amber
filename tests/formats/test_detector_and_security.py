import io
import zipfile
import pytest
from PIL import Image

from core.formats.detector import FormatDetector
from core.formats.security import FormatSecurityValidator
from core.formats.models import (
    FormatTier,
    FormatSecurityException,
    SecurityFailureClass,
)
from tests.formats.fixtures import (
    create_minimal_pdf_bytes,
    create_minimal_png_bytes,
    create_minimal_jpeg_bytes,
    create_minimal_docx_bytes,
    create_minimal_pptx_bytes,
    create_minimal_xlsx_bytes,
    create_minimal_txt_bytes,
    create_minimal_csv_bytes,
    create_minimal_rtf_bytes,
)


class TestFormatDetector:
    def test_detect_pdf(self):
        data = create_minimal_pdf_bytes()
        res = FormatDetector.identify_format(data, filename="doc.pdf")
        assert res.detected_format == "PDF"
        assert res.mime_type == "application/pdf"
        assert res.is_extension_consistent is True
        assert res.confidence == 1.0

    def test_detect_png(self):
        data = create_minimal_png_bytes()
        res = FormatDetector.identify_format(data, filename="image.png")
        assert res.detected_format == "PNG"
        assert res.mime_type == "image/png"
        assert res.is_extension_consistent is True
        assert res.confidence == 1.0

    def test_detect_jpeg(self):
        data = create_minimal_jpeg_bytes()
        res = FormatDetector.identify_format(data, filename="photo.jpg")
        assert res.detected_format == "JPEG"
        assert res.mime_type == "image/jpeg"
        assert res.is_extension_consistent is True
        assert res.confidence == 1.0

    def test_detect_docx(self):
        data = create_minimal_docx_bytes()
        res = FormatDetector.identify_format(data, filename="test.docx")
        assert res.detected_format == "DOCX"
        assert res.mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert res.is_extension_consistent is True

    def test_detect_pptx(self):
        data = create_minimal_pptx_bytes()
        res = FormatDetector.identify_format(data, filename="test.pptx")
        assert res.detected_format == "PPTX"
        assert res.mime_type == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        assert res.is_extension_consistent is True

    def test_detect_xlsx(self):
        data = create_minimal_xlsx_bytes()
        res = FormatDetector.identify_format(data, filename="test.xlsx")
        assert res.detected_format == "XLSX"
        assert res.mime_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert res.is_extension_consistent is True

    def test_detect_txt(self):
        data = create_minimal_txt_bytes()
        res = FormatDetector.identify_format(data, filename="readme.txt")
        assert res.detected_format == "TXT"
        assert res.mime_type == "text/plain"
        assert res.is_extension_consistent is True

    def test_detect_csv(self):
        data = create_minimal_csv_bytes()
        res = FormatDetector.identify_format(data, filename="data.csv")
        assert res.detected_format == "CSV"
        assert res.mime_type == "text/csv"
        assert res.is_extension_consistent is True

    def test_detect_rtf(self):
        data = create_minimal_rtf_bytes()
        res = FormatDetector.identify_format(data, filename="doc.rtf")
        assert res.detected_format == "RTF"
        assert res.mime_type == "application/rtf"
        assert res.is_extension_consistent is True

    def test_detect_mismatch_flagged(self):
        # PDF data declared as .png
        pdf_data = create_minimal_pdf_bytes()
        res = FormatDetector.identify_format(pdf_data, filename="fake.png")
        assert res.detected_format == "PDF"
        assert res.is_extension_consistent is False


class TestFormatSecurityValidator:
    def test_validate_benign_pdf(self):
        data = create_minimal_pdf_bytes()
        res = FormatSecurityValidator.validate_artifact(data, filename="doc.pdf")
        assert res.is_safe is True
        assert res.file_size_bytes == len(data)

    def test_validate_benign_docx(self):
        data = create_minimal_docx_bytes()
        res = FormatSecurityValidator.validate_artifact(data, filename="test.docx")
        assert res.is_safe is True

    def test_zip_path_traversal_rejected(self):
        # Create a ZIP with path traversal entry
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("../../etc/passwd", "root:x:0:0:")
            zf.writestr("[Content_Types].xml", "<Types/>")
            zf.writestr("word/document.xml", "<w:document/>")
        zip_bytes = buf.getvalue()

        with pytest.raises(FormatSecurityException) as excinfo:
            FormatSecurityValidator.validate_artifact(zip_bytes, filename="exploit.docx")
        assert excinfo.value.failure_class == SecurityFailureClass.PATH_TRAVERSAL_DETECTED

    def test_macro_vba_rejected(self):
        # Create a DOCX containing vbaProject.bin
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("[Content_Types].xml", "<Types/>")
            zf.writestr("word/document.xml", "<w:document/>")
            zf.writestr("word/vbaProject.bin", b"\x00\x01\x02MALICIOUS_MACRO_BYTES")
        docx_macro = buf.getvalue()

        with pytest.raises(FormatSecurityException) as excinfo:
            FormatSecurityValidator.validate_artifact(docx_macro, filename="macro.docx")
        assert excinfo.value.failure_class == SecurityFailureClass.MACRO_PRESENT

    def test_external_relationship_rejected(self):
        # Create a DOCX with external SSRF relationship
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("[Content_Types].xml", "<Types/>")
            zf.writestr("word/document.xml", "<w:document/>")
            zf.writestr(
                "word/_rels/document.xml.rels",
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" '
                'Target="http://malicious-internal-server.local/exfiltrate" TargetMode="External"/>'
                '</Relationships>'
            )
        docx_ssrf = buf.getvalue()

        with pytest.raises(FormatSecurityException) as excinfo:
            FormatSecurityValidator.validate_artifact(docx_ssrf, filename="ssrf.docx")
        assert excinfo.value.failure_class == SecurityFailureClass.EXTERNAL_REFERENCE_PRESENT

    def test_xml_entity_expansion_rejected(self):
        # Create XML containing DOCTYPE entity expansion
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("[Content_Types].xml", "<Types/>")
            zf.writestr(
                "word/document.xml",
                '<?xml version="1.0"?>'
                '<!DOCTYPE lolz ['
                '<!ENTITY lol "lol">'
                '<!ELEMENT lolz (#PCDATA)>'
                '<!ENTITY lol1 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">'
                ']>'
                '<w:document><w:body><w:p><w:r><w:t>&lol1;</w:t></w:r></w:p></w:body></w:document>'
            )
        docx_billion_laughs = buf.getvalue()

        with pytest.raises(FormatSecurityException) as excinfo:
            FormatSecurityValidator.validate_artifact(docx_billion_laughs, filename="bomb.docx")
        assert excinfo.value.failure_class in (
            SecurityFailureClass.XML_ENTITY_HAZARD,
            SecurityFailureClass.EXTERNAL_REFERENCE_PRESENT,
        )

    def test_zip_bomb_expansion_ratio_rejected(self):
        # Create a zip bomb (high compression ratio > 100:1)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("word/document.xml", b"A" * (20 * 1024 * 1024))  # 20MB compresses to few KB
            zf.writestr("[Content_Types].xml", "<Types/>")
        zip_bomb_bytes = buf.getvalue()

        with pytest.raises(FormatSecurityException) as excinfo:
            FormatSecurityValidator.validate_artifact(zip_bomb_bytes, filename="bomb.docx")
        assert excinfo.value.failure_class == SecurityFailureClass.DECOMPRESSION_LIMIT

    def test_polyglot_zip_prefix_rejected(self):
        # Prefix a valid DOCX with valid JPEG header bytes
        docx_bytes = create_minimal_docx_bytes()
        polyglot = b"\xff\xd8\xff\xe0\x00\x10JFIF" + (b"\x00" * 64) + docx_bytes

        with pytest.raises(FormatSecurityException) as excinfo:
            FormatSecurityValidator.validate_artifact(polyglot, filename="polyglot.jpg")
        assert excinfo.value.failure_class == SecurityFailureClass.POLYGLOT_DETECTED
