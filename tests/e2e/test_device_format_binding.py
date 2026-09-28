"""
SIH26237 - Device-in-the-Loop & Format Binding Test Suite.
Validates smartphone hardware context binding and bitwise transfer audit across all formats.
"""

import pytest
from core.formats.orchestrator import MultiFormatForensicOrchestrator
from core.formats.golden_cases import GOLDEN_CASE_REGISTRY


class TestDeviceFormatBinding:
    """Verifies physical device binding and bitwise transfer integrity."""

    def setup_method(self):
        self.orchestrator = MultiFormatForensicOrchestrator()

    @pytest.mark.parametrize("case_id", list(GOLDEN_CASE_REGISTRY.keys()))
    def test_device_binding_and_transfer_audit(self, case_id: str):
        """Verifies device delivery, channel context, and custody recording."""
        res = self.orchestrator.execute_golden_case(case_id)

        assert res.recovered_identity.transfer_channel == "DEVICE_STAGING"
        assert res.recovered_identity.byte_length > 0
        assert res.recovered_identity.recovered_hash == res.carrier_identity.carrier_hash
        assert res.custody_root_hash is not None
        assert len(res.custody_root_hash) == 64
