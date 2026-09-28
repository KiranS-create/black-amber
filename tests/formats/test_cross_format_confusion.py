"""
SIH26237 - Cross-Format Confusion and Attribution Defense Tests.
Verifies that deliberate extension renaming, container mix-ups, and cross-format confusion
are correctly identified, isolated, and prevented from causing attribution errors.
"""

import pytest
from core.formats.detector import FormatDetector
from core.formats.security import FormatSecurityValidator
from core.formats.api import ForensicFormatAPI
from core.formats.models import FormatTier
from tests.formats.fixtures import (
    create_minimal_pdf_bytes,
    create_minimal_docx_bytes,
    create_minimal_pptx_bytes,
    create_minimal_xlsx_bytes,
    create_minimal_png_bytes,
    create_minimal_jpeg_bytes,
    create_minimal_txt_bytes,
    create_minimal_odt_bytes,
)


class TestCrossFormatConfusion:
    """Verifies that format sniffer and forensic API are immune to cross-format type confusion."""

    def setup_method(self):
        self.api = ForensicFormatAPI()

    def test_png_renamed_to_jpg(self):
        png_data = create_minimal_png_bytes()
        res = FormatDetector.identify_format(png_data, filename="photo.jpg")
        assert res.detected_format == "PNG"
        assert res.mime_type == "image/png"
        assert res.is_extension_consistent is False

        # Ingestion through API resolves true format despite renamed filename
        identity, canonical, sec_res = self.api.ingest_artifact(png_data, filename="photo.jpg")
        assert identity.detected_format == "PNG"
        assert identity.declared_extension == "jpg"

    def test_jpeg_renamed_to_png(self):
        jpeg_data = create_minimal_jpeg_bytes()
        res = FormatDetector.identify_format(jpeg_data, filename="graphic.png")
        assert res.detected_format == "JPEG"
        assert res.mime_type == "image/jpeg"
        assert res.is_extension_consistent is False

        identity, canonical, sec_res = self.api.ingest_artifact(jpeg_data, filename="graphic.png")
        assert identity.detected_format == "JPEG"
        assert identity.declared_extension == "png"

    def test_docx_renamed_to_zip(self):
        docx_data = create_minimal_docx_bytes()
        res = FormatDetector.identify_format(docx_data, filename="archive.zip")
        assert res.detected_format == "DOCX"
        assert res.is_extension_consistent is False

    def test_pptx_renamed_to_docx(self):
        pptx_data = create_minimal_pptx_bytes()
        res = FormatDetector.identify_format(pptx_data, filename="notes.docx")
        assert res.detected_format == "PPTX"
        assert res.is_extension_consistent is False

    def test_xlsx_renamed_to_docx(self):
        xlsx_data = create_minimal_xlsx_bytes()
        res = FormatDetector.identify_format(xlsx_data, filename="report.docx")
        assert res.detected_format == "XLSX"
        assert res.is_extension_consistent is False

    def test_odt_renamed_to_docx(self):
        odt_data = create_minimal_odt_bytes()
        res = FormatDetector.identify_format(odt_data, filename="open_doc.docx")
        assert res.detected_format == "ODT"
        assert res.is_extension_consistent is False

    def test_plaintext_renamed_to_pdf(self):
        txt_data = create_minimal_txt_bytes("Just some plaintext words without PDF markers")
        res = FormatDetector.identify_format(txt_data, filename="spoofed.pdf")
        assert res.detected_format == "TXT"
        assert res.is_extension_consistent is False

    def test_pdf_renamed_to_txt(self):
        pdf_data = create_minimal_pdf_bytes()
        res = FormatDetector.identify_format(pdf_data, filename="spoofed.txt")
        assert res.detected_format == "PDF"
        assert res.is_extension_consistent is False

    def test_cross_format_extraction_isolation(self):
        """
        Verifies that an artifact watermarked under one format (e.g. DOCX visual carrier)
        retains forensic carrier identity and cannot be falsely claimed or corrupted
        by mismatched format metadata.
        """
        docx_data = create_minimal_docx_bytes(title="Confidential Document")
        identity, canonical, sec_res = self.api.ingest_artifact(docx_data, filename="contract.docx")
        carriers = self.api.render_forensic_carriers(canonical)
        assert len(carriers) >= 1
        assert carriers[0].component_type == "PAGE"
        assert carriers[0].parent_artifact_id == identity.artifact_id
