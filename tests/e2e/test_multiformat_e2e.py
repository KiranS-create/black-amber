"""
SIH26237 - Multi-Format End-to-End Integration Test Suite.
Validates the complete 16-step forensic lifecycle for all six Tier-1 formats:
PDF, DOCX, PPTX, XLSX, PNG, and JPEG.
"""

import pytest
from core.formats.orchestrator import MultiFormatForensicOrchestrator
from core.formats.golden_cases import GOLDEN_CASE_REGISTRY


class TestMultiFormatE2E:
    """Comprehensive test suite for the MultiFormatForensicOrchestrator."""

    def setup_method(self):
        self.orchestrator = MultiFormatForensicOrchestrator()

    @pytest.mark.parametrize("case_id", list(GOLDEN_CASE_REGISTRY.keys()))
    def test_golden_case_lifecycle(self, case_id: str):
        """Validates that each Tier-1 format successfully completes the 16-step forensic lifecycle."""
        res = self.orchestrator.execute_golden_case(case_id)

        assert res.case_id == case_id
        assert res.steps_passed == 16
        assert res.total_steps == 16
        assert res.verdict == "VERIFIED_DEVICE_IN_LOOP"
        assert res.watermark_extracted is True
        assert res.extracted_recipient_id == "recipient_alpha"
        assert res.offline_verified is True
        assert res.attribution_confidence > 0.90
        assert len(res.lineage_merkle_root) == 64
        assert len(res.custody_root_hash) == 64
        assert res.evidence_package_id.startswith("PKG-") or len(res.evidence_package_id) > 10
