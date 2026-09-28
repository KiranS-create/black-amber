"""
SIH26237 - Air-Gapped Standalone Offline Verifier Test Suite.
Validates offline verification of signed evidence packages across all Tier-1 formats with zero network sockets.
"""

import pytest
from core.formats.orchestrator import MultiFormatForensicOrchestrator
from core.formats.golden_cases import GOLDEN_CASE_REGISTRY


class TestOfflineVerifierAllFormats:
    """Verifies standalone offline verifier across all formats."""

    def setup_method(self):
        self.orchestrator = MultiFormatForensicOrchestrator()

    @pytest.mark.parametrize("case_id", list(GOLDEN_CASE_REGISTRY.keys()))
    def test_offline_verifier_pass(self, case_id: str):
        """Verifies signature, Merkle root, content hashes, and custody chain offline."""
        res = self.orchestrator.execute_golden_case(case_id)

        assert res.offline_verified is True
        assert res.verdict == "VERIFIED_DEVICE_IN_LOOP"
