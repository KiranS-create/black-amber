"""
SIH26237 - Format Confusion & Adversarial Input Test Suite.
Validates zero-trust rejection of format extension mismatches, polyglot containers, and malformed files.
"""

import pytest
from core.formats.api import ForensicFormatAPI
from core.formats.models import FormatSecurityException, SecurityFailureClass


class TestE2ECrossFormatConfusion:
    """Verifies fail-closed zero-trust validation against format confusion attacks."""

    def setup_method(self):
        self.api = ForensicFormatAPI()

    def test_pdf_renamed_to_docx(self):
        """PDF binary with .docx extension must trigger extension mismatch / magic byte detection."""
        pdf_bytes = b"%PDF-1.7 header content sample"
        id_res = self.api.identify_format(pdf_bytes, filename="fake.docx", declared_mime="application/pdf")
        assert id_res.detected_format == "PDF"
        assert id_res.is_extension_consistent is False

    def test_docx_renamed_to_zip(self):
        """DOCX archive with .zip extension identifies as DOCX."""
        from tests.formats.fixtures import create_minimal_docx_bytes
        docx_bytes = create_minimal_docx_bytes()
        id_res = self.api.identify_format(docx_bytes, filename="document.zip")
        assert id_res.detected_format == "DOCX"

    def test_png_renamed_to_jpeg(self):
        """PNG image with .jpg extension detects as PNG."""
        png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\x00\x00\x00\x1f\xf3\xff"
        id_res = self.api.identify_format(png_bytes, filename="photo.jpg")
        assert id_res.detected_format == "PNG"
        assert id_res.is_extension_consistent is False

    def test_malformed_container_rejection(self):
        """Malformed garbage payload fails closed during security validation raising FormatSecurityException."""
        garbage = b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A\x0B\x0C\x0D\x0E\x0F"
        with pytest.raises(FormatSecurityException) as exc_info:
            self.api.validate_artifact(garbage, filename="test.bin")
        assert exc_info.value.failure_class == SecurityFailureClass.UNSUPPORTED_FORMAT
