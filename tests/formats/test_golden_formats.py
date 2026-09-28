"""
SIH26237 - Multi-Format Golden Pipeline End-to-End Test Suite.
Validates the complete lifecycle for all Tier 1 formats:
Original Ingest -> Security Audit -> Canonicalization -> Forensic Carrier Rendering ->
Watermark Embedding -> Watermark Extraction -> Forensic Lineage & Evidence Generation.
"""

import pytest
import numpy as np

from core.formats.api import ForensicFormatAPI
from core.formats.models import (
    CarrierMode,
    OriginalArtifactIdentity,
    ForensicCarrierIdentity,
)
from core.watermark.base import WatermarkPayload, WatermarkStatus
from core.formats.evidence_integration import MultiFormatArtifactEvidence
from core.evidence_package.canonical import canonical_json_dumps
from tests.formats.fixtures import (
    create_minimal_pdf_bytes,
    create_minimal_docx_bytes,
    create_minimal_pptx_bytes,
    create_minimal_xlsx_bytes,
    create_minimal_png_bytes,
    create_minimal_jpeg_bytes,
)


class TestGoldenMultiFormatPipeline:
    """Golden pipeline validation across PDF, DOCX, PPTX, XLSX, PNG, and JPEG."""

    def setup_method(self):
        self.api = ForensicFormatAPI()

    def _execute_golden_lifecycle(self, raw_bytes: bytes, filename: str, expected_format: str, recipient_id: str):
        # 1. Ingestion & Security Validation
        orig_identity, canonical, sec_res = self.api.ingest_artifact(
            data=raw_bytes,
            filename=filename,
            tenant_id="tenant_alpha"
        )
        assert sec_res.is_safe is True
        assert orig_identity.detected_format == expected_format
        assert orig_identity.byte_length == len(raw_bytes)
        assert orig_identity.tenant_id == "tenant_alpha"

        # 2. Canonicalization
        assert canonical.source_format == expected_format
        digest = canonical.compute_content_digest()
        assert digest is not None
        assert len(digest) == 64

        # 3. Carrier Rendering
        carriers = self.api.render_forensic_carriers(canonical)
        assert len(carriers) >= 1
        primary_carrier = carriers[0]
        assert primary_carrier.image_bytes is not None

        # 4. Watermark Embedding
        codeword = [1, 0, 1, 1, 0, 0, 1, 0] * 16  # 128 bits
        payload = WatermarkPayload(
            document_id=orig_identity.artifact_id,
            release_id="rel_2026_golden",
            codeword=codeword,
            metadata={"recipient_id": recipient_id, "format": expected_format}
        )
        wm_carrier, embed_details = self.api.watermark_carrier(
            carrier=primary_carrier,
            payload=payload,
            format_hint=expected_format
        )
        assert embed_details["status"] == "SUCCESS"
        assert wm_carrier.image_bytes is not None

        # 5. Watermark Extraction & Verification
        observation = self.api.extract_watermark(
            captured_input=wm_carrier.image_bytes,
            format_hint=expected_format,
            expected_document_id=orig_identity.artifact_id,
            expected_release_id="rel_2026_golden",
            expected_codeword_length=128
        )
        assert observation.status == WatermarkStatus.RECOVERED
        assert observation.is_valid is True
        assert observation.observed_symbols == codeword

        # 6. Evidence Packaging & Canonical RFC 8785 Export
        evidence = MultiFormatArtifactEvidence.create(
            artifact=orig_identity,
            canonical_doc=canonical,
            sec_result=sec_res,
            carriers=[wm_carrier],
            extraction_obs={
                "status": observation.status.value,
                "is_valid": observation.is_valid,
                "confidence": observation.confidence,
                "extracted_symbols": observation.observed_symbols
            }
        )
        assert evidence.security_status == "PASSED"
        assert evidence.content_hash is not None
        canonical_json = canonical_json_dumps(evidence.model_dump(mode="json"))
        assert len(canonical_json) > 0
        assert "PASSED" in canonical_json

    def test_golden_pdf(self):
        data = create_minimal_pdf_bytes(title="Golden PDF", content="Security Classified")
        self._execute_golden_lifecycle(data, "report.pdf", "PDF", "recip_alice")

    def test_golden_docx(self):
        data = create_minimal_docx_bytes(title="Golden DOCX", content="Contract Clause Alpha")
        self._execute_golden_lifecycle(data, "brief.docx", "DOCX", "recip_bob")

    def test_golden_pptx(self):
        data = create_minimal_pptx_bytes(title="Golden PPTX", content="Strategy Slide 1")
        self._execute_golden_lifecycle(data, "deck.pptx", "PPTX", "recip_charlie")

    def test_golden_xlsx(self):
        data = create_minimal_xlsx_bytes(title="Golden XLSX")
        self._execute_golden_lifecycle(data, "budget.xlsx", "XLSX", "recip_david")

    def test_golden_png(self):
        data = create_minimal_png_bytes(width=500, height=400)
        self._execute_golden_lifecycle(data, "diagram.png", "PNG", "recip_eve")

    def test_golden_jpeg(self):
        data = create_minimal_jpeg_bytes(width=500, height=400)
        self._execute_golden_lifecycle(data, "photo.jpg", "JPEG", "recip_frank")
