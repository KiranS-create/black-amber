"""
SIH26237 - Recipient Separation & Cross-Attribution Protection Test Suite.
Validates multi-recipient signal distinctness and zero cross-attribution across all formats.
"""

import pytest
from core.formats.orchestrator import MultiFormatForensicOrchestrator
from core.formats.golden_cases import GOLDEN_CASE_REGISTRY


class TestRecipientFormatSeparation:
    """Verifies cross-recipient separation matrix and non-substitution invariants."""

    def setup_method(self):
        self.orchestrator = MultiFormatForensicOrchestrator()

    @pytest.mark.parametrize("case_id", list(GOLDEN_CASE_REGISTRY.keys()))
    def test_multi_recipient_signal_separation(self, case_id: str):
        """Verifies 3 distinct recipients receive unique forensic carrier signals."""
        eq_res = self.orchestrator.execute_multi_recipient_equivalence(case_id, recipient_count=3)

        assert eq_res.recipient_count == 3
        assert eq_res.recipient_signals_distinct is True
        assert len(set(eq_res.recipient_carrier_hashes)) == 3
        assert eq_res.cross_attribution_prevented is True
        assert eq_res.min_hamming_distance >= 16
