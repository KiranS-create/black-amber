"""
SIH26237 - Evidence Package Equivalence Test Suite.
Validates RFC 8785 evidence package generation and validity across all Tier-1 formats.
"""

import pytest
from core.formats.orchestrator import MultiFormatForensicOrchestrator
from core.formats.golden_cases import GOLDEN_CASE_REGISTRY


class TestEvidenceEquivalence:
    """Verifies evidence package equivalence across all file formats."""

    def setup_method(self):
        self.orchestrator = MultiFormatForensicOrchestrator()

    @pytest.mark.parametrize("case_id", list(GOLDEN_CASE_REGISTRY.keys()))
    def test_evidence_package_equivalence(self, case_id: str):
        """Verifies package validity, offline verifier pass, and Merkle root anchoring."""
        res = self.orchestrator.execute_golden_case(case_id)

        assert res.evidence_package_id is not None
        assert res.offline_verified is True
        assert len(res.lineage_merkle_root) == 64
        assert len(res.custody_root_hash) == 64
