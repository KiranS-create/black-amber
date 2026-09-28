"""
SIH26237 - Identity Tripartite Segregation Test Suite.
Validates that ORIGINAL_ARTIFACT_IDENTITY, FORENSIC_CARRIER_IDENTITY, and RECOVERED_ARTIFACT_IDENTITY
remain strictly separate and immutable across all Tier-1 formats.
"""

import pytest
import hashlib
from core.formats.orchestrator import MultiFormatForensicOrchestrator
from core.formats.golden_cases import GOLDEN_CASE_REGISTRY


class TestFormatIdentitySegregation:
    """Verifies strict identity separation rules across all formats."""

    def setup_method(self):
        self.orchestrator = MultiFormatForensicOrchestrator()

    @pytest.mark.parametrize("case_id", list(GOLDEN_CASE_REGISTRY.keys()))
    def test_identity_tripartite_separation(self, case_id: str):
        """Verifies original, carrier, and recovered identity separation."""
        res = self.orchestrator.execute_golden_case(case_id)

        # 1. Original identity must be non-empty valid 64-char SHA-256 digest
        assert len(res.original_identity.original_hash) == 64

        # 2. Carrier identity hash must NOT equal raw input hash (since it is rendered/watermarked)
        assert res.carrier_identity.carrier_hash != res.original_identity.original_hash

        # 3. Recovered identity hash must equal carrier hash on uncorrupted staged transfer
        assert res.recovered_identity.recovered_hash == res.carrier_identity.carrier_hash

        # 4. Identity flags must be explicit
        assert res.recovered_identity.is_bitwise_identical_to_carrier is True
        assert res.recovered_identity.is_bitwise_identical_to_original is False
