"""
SIH26237 - Adversarial Tamper Rejection Test Suite.
Validates deterministic fail-closed rejection across 7 adversarial tampering categories for all formats.
"""

import pytest
from core.formats.orchestrator import MultiFormatForensicOrchestrator
from core.formats.golden_cases import GOLDEN_CASE_REGISTRY


class TestTamperAllFormats:
    """Verifies tamper rejection matrix across all Tier-1 formats."""

    def setup_method(self):
        self.orchestrator = MultiFormatForensicOrchestrator()

    @pytest.mark.parametrize("case_id", list(GOLDEN_CASE_REGISTRY.keys()))
    def test_tamper_rejection_matrix(self, case_id: str):
        """Verifies 7 tamper categories are rejected deterministically."""
        tamper_results = self.orchestrator.execute_tamper_matrix(case_id)

        assert len(tamper_results) == 7
        for tr in tamper_results:
            assert tr.rejected is True
            assert tr.rejection_reason is not None
            assert tr.exception_class is not None
