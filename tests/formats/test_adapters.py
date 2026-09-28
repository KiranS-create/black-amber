"""
SIH26237 - Format Adapters Contract & Functionality Unit Tests.
Tests all Tier 1, Tier 2, and Tier 3 adapters for correct capability reporting,
canonicalization, visual carrier rendering, and watermark embedding/extraction.
"""

import pytest
import numpy as np

from core.formats.registry import default_adapter_registry
from core.formats.models import (
    FormatTier,
    CapabilityState,
    CarrierMode,
    ForensicCarrier
)
from core.watermark.base import WatermarkPayload, WatermarkStatus
from tests.formats.fixtures import (
    create_minimal_pdf_bytes,
    create_minimal_docx_bytes,
    create_minimal_pptx_bytes,
    create_minimal_xlsx_bytes,
    create_minimal_png_bytes,
    create_minimal_jpeg_bytes,
    create_minimal_txt_bytes,
    create_minimal_csv_bytes,
    create_minimal_rtf_bytes,
    create_minimal_odt_bytes,
)


class TestFormatAdapters:
    """Validates contract implementation across all format adapters."""

    def test_adapter_registry_completeness(self):
        """Verify all 17 target formats are registered in capability registry."""
        caps = default_adapter_registry.get_all_capabilities()
        required_formats = ["PDF", "DOCX", "PPTX", "XLSX", "PNG", "JPEG", "TXT", "CSV", "RTF", "ODT", "ODS", "ODP", "ZIP", "VIDEO", "AUDIO", "CAD", "SCIENTIFIC"]
        for fmt in required_formats:
            assert fmt in caps, f"Format {fmt} missing from registry"

    def test_pdf_adapter_lifecycle(self):
        """Test PDF adapter identification, canonicalization, rendering, watermarking, extraction."""
        adapter = default_adapter_registry.get_adapter("PDF")
        assert adapter.get_capabilities().tier == FormatTier.TIER_1
        assert adapter.get_capabilities().capability_state == CapabilityState.SUPPORTED

        pdf_bytes = create_minimal_pdf_bytes("Secret Briefing", "Top Secret PDF Paragraph")
        sec_res = adapter.validate_security(pdf_bytes, "briefing.pdf")
        assert sec_res.is_safe is True

        canonical_doc = adapter.canonicalize(pdf_bytes, "doc_pdf_01", "briefing.pdf")
        assert canonical_doc.source_format == "PDF"
        assert len(canonical_doc.pages) >= 1

        carriers = adapter.render_carriers(canonical_doc)
        assert len(carriers) >= 1
        assert carriers[0].width_px == 800
        assert carriers[0].height_px == 1000

        # Embed watermark
        codeword = [1, 0, 1, 1, 0, 0, 1, 0] * 16  # 128-bit
        payload = WatermarkPayload(
            document_id="doc_pdf_01",
            release_id="rel_pdf_01",
            codeword=codeword,
            metadata={"recipient_id": "usr_alice"}
        )
        wm_carrier, meta = adapter.embed_watermark(carriers[0], payload)
        assert wm_carrier.image_bytes is not None

        # Extract watermark
        obs = adapter.extract_watermark(
            wm_carrier.image_bytes,
            expected_document_id="doc_pdf_01",
            expected_release_id="rel_pdf_01",
            expected_codeword_length=128
        )
        assert obs.status == WatermarkStatus.RECOVERED
        assert obs.is_valid is True
        assert obs.observed_symbols == codeword

    def test_docx_adapter_lifecycle(self):
        """Test DOCX adapter identification, canonicalization, rendering, watermarking, extraction."""
        adapter = default_adapter_registry.get_adapter("DOCX")
        assert adapter.get_capabilities().tier == FormatTier.TIER_1
        assert adapter.get_capabilities().capability_state == CapabilityState.SUPPORTED

        docx_bytes = create_minimal_docx_bytes("Executive Memo", "Classified Word Text")
        sec_res = adapter.validate_security(docx_bytes, "memo.docx")
        assert sec_res.is_safe is True

        canonical_doc = adapter.canonicalize(docx_bytes, "doc_docx_01", "memo.docx")
        assert canonical_doc.source_format == "DOCX"
        assert len(canonical_doc.pages) >= 1
        assert len(canonical_doc.text_blocks) >= 2
        assert len(canonical_doc.tables) >= 1

        carriers = adapter.render_carriers(canonical_doc)
        assert len(carriers) >= 1

        # Embed & Extract
        codeword = [0, 1, 0, 1, 1, 1, 0, 0] * 16
        payload = WatermarkPayload(
            document_id="doc_docx_01",
            release_id="rel_docx_01",
            codeword=codeword,
            metadata={"recipient_id": "usr_bob"}
        )
        wm_carrier, _ = adapter.embed_watermark(carriers[0], payload)
        obs = adapter.extract_watermark(
            wm_carrier.image_bytes,
            expected_document_id="doc_docx_01",
            expected_release_id="rel_docx_01",
            expected_codeword_length=128
        )
        assert obs.status == WatermarkStatus.RECOVERED
        assert obs.observed_symbols == codeword

    def test_pptx_adapter_lifecycle(self):
        """Test PPTX adapter per-slide identity, rendering, watermarking, extraction."""
        adapter = default_adapter_registry.get_adapter("PPTX")
        assert adapter.get_capabilities().tier == FormatTier.TIER_1

        pptx_bytes = create_minimal_pptx_bytes("Strategy Deck", "Key Bullet Point")
        sec_res = adapter.validate_security(pptx_bytes, "deck.pptx")
        assert sec_res.is_safe is True

        canonical_doc = adapter.canonicalize(pptx_bytes, "doc_pptx_01", "deck.pptx")
        assert canonical_doc.source_format == "PPTX"
        assert len(canonical_doc.slides) >= 1
        assert canonical_doc.slides[0].slide_name == "slide-001"

        carriers = adapter.render_carriers(canonical_doc)
        assert len(carriers) >= 1
        assert carriers[0].component_type == "SLIDE"

        codeword = [1, 1, 0, 0, 1, 0, 1, 0] * 16
        payload = WatermarkPayload(
            document_id="doc_pptx_01",
            release_id="rel_pptx_01",
            codeword=codeword,
            metadata={"recipient_id": "usr_charlie"}
        )
        wm_carrier, _ = adapter.embed_watermark(carriers[0], payload)
        obs = adapter.extract_watermark(
            wm_carrier.image_bytes,
            expected_document_id="doc_pptx_01",
            expected_release_id="rel_pptx_01",
            expected_codeword_length=128
        )
        assert obs.status == WatermarkStatus.RECOVERED
        assert obs.observed_symbols == codeword

    def test_xlsx_adapter_lifecycle(self):
        """Test XLSX adapter cell matrix extraction, grid rendering, watermarking."""
        adapter = default_adapter_registry.get_adapter("XLSX")
        assert adapter.get_capabilities().tier == FormatTier.TIER_1

        xlsx_bytes = create_minimal_xlsx_bytes("Financial Model")
        sec_res = adapter.validate_security(xlsx_bytes, "model.xlsx")
        assert sec_res.is_safe is True

        canonical_doc = adapter.canonicalize(xlsx_bytes, "doc_xlsx_01", "model.xlsx")
        assert canonical_doc.source_format == "XLSX"
        assert len(canonical_doc.sheets) >= 1
        assert "A1" in canonical_doc.sheets[0].cells

        carriers = adapter.render_carriers(canonical_doc)
        assert len(carriers) >= 1
        assert carriers[0].component_type == "SHEET"

        codeword = [1, 0, 0, 1, 1, 0, 1, 1] * 16
        payload = WatermarkPayload(
            document_id="doc_xlsx_01",
            release_id="rel_xlsx_01",
            codeword=codeword,
            metadata={"recipient_id": "usr_dave"}
        )
        wm_carrier, _ = adapter.embed_watermark(carriers[0], payload)
        obs = adapter.extract_watermark(
            wm_carrier.image_bytes,
            expected_document_id="doc_xlsx_01",
            expected_release_id="rel_xlsx_01",
            expected_codeword_length=128
        )
        assert obs.status == WatermarkStatus.RECOVERED
        assert obs.observed_symbols == codeword

    def test_raster_adapter_lifecycle(self):
        """Test PNG and JPEG direct raster image modulation and extraction."""
        for fmt, gen in [("PNG", create_minimal_png_bytes), ("JPEG", create_minimal_jpeg_bytes)]:
            adapter = default_adapter_registry.get_adapter(fmt)
            assert adapter.get_capabilities().tier == FormatTier.TIER_1
            assert adapter.get_capabilities().carrier_mode == CarrierMode.DIRECTLY_IN_ORIGINAL

            img_bytes = gen(500, 400)
            sec_res = adapter.validate_security(img_bytes, f"image.{fmt.lower()}")
            assert sec_res.is_safe is True

            canonical_doc = adapter.canonicalize(img_bytes, f"doc_{fmt.lower()}_01")
            assert canonical_doc.source_format == fmt
            assert len(canonical_doc.images) == 1

            carriers = adapter.render_carriers(canonical_doc)
            assert len(carriers) == 1

            codeword = [0, 0, 1, 1, 1, 1, 0, 0] * 16
            payload = WatermarkPayload(
                document_id=f"doc_{fmt.lower()}_01",
                release_id=f"rel_{fmt.lower()}_01",
                codeword=codeword,
                metadata={"recipient_id": "usr_eve"}
            )
            wm_carrier, _ = adapter.embed_watermark(carriers[0], payload)
            obs = adapter.extract_watermark(
                wm_carrier.image_bytes,
                expected_document_id=f"doc_{fmt.lower()}_01",
                expected_release_id=f"rel_{fmt.lower()}_01",
                expected_codeword_length=128
            )
            assert obs.status == WatermarkStatus.RECOVERED
            assert obs.observed_symbols == codeword

    def test_tier2_adapters_lifecycle(self):
        """Test Tier 2 text, csv, rtf, and odf adapters."""
        # TXT
        txt_adapter = default_adapter_registry.get_adapter("TXT")
        assert txt_adapter.get_capabilities().tier == FormatTier.TIER_2
        assert txt_adapter.get_capabilities().capability_state == CapabilityState.PARTIAL
        txt_doc = txt_adapter.canonicalize(create_minimal_txt_bytes(), "doc_txt_01")
        assert len(txt_doc.pages) >= 1

        # CSV
        csv_adapter = default_adapter_registry.get_adapter("CSV")
        assert csv_adapter.get_capabilities().tier == FormatTier.TIER_2
        csv_doc = csv_adapter.canonicalize(create_minimal_csv_bytes(), "doc_csv_01")
        assert len(csv_doc.tables) == 1
        assert csv_doc.tables[0].row_count == 3

        # RTF
        rtf_adapter = default_adapter_registry.get_adapter("RTF")
        assert rtf_adapter.get_capabilities().tier == FormatTier.TIER_2
        rtf_doc = rtf_adapter.canonicalize(create_minimal_rtf_bytes(), "doc_rtf_01")
        assert len(rtf_doc.text_blocks) >= 1

        # ODT
        odt_adapter = default_adapter_registry.get_adapter("ODT")
        assert odt_adapter.get_capabilities().tier == FormatTier.TIER_2
        odt_doc = odt_adapter.canonicalize(create_minimal_odt_bytes(), "doc_odt_01")
        assert len(odt_doc.text_blocks) >= 1

    def test_tier3_adapters_metadata_only(self):
        """Test Tier 3 modeled adapters return METADATA_ONLY and refuse visual watermarking."""
        zip_adapter = default_adapter_registry.get_adapter("ZIP")
        caps = zip_adapter.get_capabilities()
        assert caps.tier == FormatTier.TIER_3
        assert caps.capability_state == CapabilityState.METADATA_ONLY
        assert caps.carrier_mode == CarrierMode.UNSUPPORTED
        assert caps.can_render_visual_carrier is False
        assert caps.can_embed_watermark is False
