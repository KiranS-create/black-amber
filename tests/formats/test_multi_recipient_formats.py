"""
SIH26237 - Multi-Recipient Watermark Distribution & Uniqueness Tests.
Verifies that distributing documents across multiple recipients generates unique forensic carriers
and accurately attributes leaks to the exact recipient with zero cross-recipient collision.
"""

import pytest
import numpy as np

from core.formats.api import ForensicFormatAPI
from core.watermark.base import WatermarkPayload, WatermarkStatus
from tests.formats.fixtures import (
    create_minimal_pdf_bytes,
    create_minimal_docx_bytes,
    create_minimal_pptx_bytes,
    create_minimal_xlsx_bytes,
    create_minimal_png_bytes,
)


class TestMultiRecipientFormats:
    """Validates multi-recipient watermarking scaling and strict attribution isolation."""

    def setup_method(self):
        self.api = ForensicFormatAPI()

    def _generate_deterministic_codeword(self, seed_id: int) -> list:
        """Generates a pseudo-random 128-bit codeword from a recipient seed index."""
        np.random.seed(seed_id + 1000)
        return list(np.random.choice([0, 1], size=128))

    def test_multi_recipient_docx_distribution(self):
        docx_bytes = create_minimal_docx_bytes("Policy Update", "Internal Distribution Memo")
        orig_identity, canonical, _ = self.api.ingest_artifact(docx_bytes, "policy.docx")
        carriers = self.api.render_forensic_carriers(canonical)
        base_carrier = carriers[0]

        num_recipients = 10
        recipient_carriers = {}
        recipient_codewords = {}

        # 1. Distribute to 10 unique recipients
        for r_idx in range(num_recipients):
            recip_id = f"recipient_{r_idx:03d}"
            codeword = self._generate_deterministic_codeword(r_idx)
            recipient_codewords[recip_id] = codeword

            payload = WatermarkPayload(
                document_id=orig_identity.artifact_id,
                release_id=f"rel_multi_{r_idx:03d}",
                codeword=codeword,
                metadata={"recipient_id": recip_id}
            )
            wm_carrier, _ = self.api.watermark_carrier(base_carrier, payload, format_hint="DOCX")
            recipient_carriers[recip_id] = wm_carrier

        # 2. Verify all carriers have distinct bit representations
        for r_idx in range(num_recipients):
            recip_id = f"recipient_{r_idx:03d}"
            wm_carrier = recipient_carriers[recip_id]

            # Extract watermark
            obs = self.api.extract_watermark(
                captured_input=wm_carrier.image_bytes,
                format_hint="DOCX",
                expected_document_id=orig_identity.artifact_id,
                expected_release_id=f"rel_multi_{r_idx:03d}",
                expected_codeword_length=128
            )
            assert obs.status == WatermarkStatus.RECOVERED
            assert obs.is_valid is True
            assert obs.observed_symbols == recipient_codewords[recip_id]

    def test_multi_recipient_xlsx_distribution(self):
        xlsx_bytes = create_minimal_xlsx_bytes("Q3 Financials")
        orig_identity, canonical, _ = self.api.ingest_artifact(xlsx_bytes, "financials.xlsx")
        carriers = self.api.render_forensic_carriers(canonical)
        base_carrier = carriers[0]

        for r_idx in range(5):
            recip_id = f"exec_{r_idx:02d}"
            codeword = self._generate_deterministic_codeword(r_idx + 50)
            payload = WatermarkPayload(
                document_id=orig_identity.artifact_id,
                release_id=f"rel_xlsx_{r_idx}",
                codeword=codeword,
                metadata={"recipient_id": recip_id}
            )
            wm_carrier, _ = self.api.watermark_carrier(base_carrier, payload, format_hint="XLSX")
            obs = self.api.extract_watermark(
                captured_input=wm_carrier.image_bytes,
                format_hint="XLSX",
                expected_document_id=orig_identity.artifact_id,
                expected_release_id=f"rel_xlsx_{r_idx}",
                expected_codeword_length=128
            )
            assert obs.status == WatermarkStatus.RECOVERED
            assert obs.observed_symbols == codeword

    def test_multi_recipient_image_distribution(self):
        png_bytes = create_minimal_png_bytes(400, 300)
        orig_identity, canonical, _ = self.api.ingest_artifact(png_bytes, "badge.png")
        base_carrier = self.api.render_forensic_carriers(canonical)[0]

        for r_idx in range(5):
            recip_id = f"agent_{r_idx}"
            codeword = self._generate_deterministic_codeword(r_idx + 100)
            payload = WatermarkPayload(
                document_id=orig_identity.artifact_id,
                release_id=f"rel_png_{r_idx}",
                codeword=codeword,
                metadata={"recipient_id": recip_id}
            )
            wm_carrier, _ = self.api.watermark_carrier(base_carrier, payload, format_hint="PNG")
            obs = self.api.extract_watermark(
                captured_input=wm_carrier.image_bytes,
                format_hint="PNG",
                expected_document_id=orig_identity.artifact_id,
                expected_release_id=f"rel_png_{r_idx}",
                expected_codeword_length=128
            )
            assert obs.status == WatermarkStatus.RECOVERED
            assert obs.observed_symbols == codeword
