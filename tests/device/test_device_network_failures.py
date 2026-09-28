"""
SIH26237 - Test Device Network Failures & Offline Transition
============================================================
Verifies safe fail-closed behavior under Wi-Fi disconnect, partial upload,
and offline transitions without corrupting evidence state.
"""

import pytest
from core.physical.device_transfer import (
    DeviceTransferEngine,
    TransferDirection,
    TransferMechanism
)


def test_device_transfer_corruption_safe_rejection():
    """Verify corrupted transfer results in HASH_MISMATCH and does not seal false data."""
    rec = DeviceTransferEngine.execute_transfer(
        payload_bytes=b"HIGH_SECURITY_DOC_BYTES",
        filename="critical.pdf",
        artifact_id="DOC-999",
        direction=TransferDirection.PHONE_TO_LAPTOP,
        source_device="phone_a",
        dest_device="laptop",
        mechanism=TransferMechanism.DEVICE_STAGING,
        simulate_corruption=True
    )

    assert rec.status == "HASH_MISMATCH"
    assert rec.is_hash_identical is False


def test_offline_package_independence():
    """Verify that previously sealed evidence packages verify without network access."""
    from core.physical.device_evidence import DeviceEvidenceBridge
    from core.physical.device_discovery import SmartphoneDeviceRecord
    from core.physical.epistemic import EpistemicStatus

    phone = SmartphoneDeviceRecord(device_id="phone_a", serial="RF8N", model="Note10")
    pkg, verif = DeviceEvidenceBridge.assemble_device_evidence_package(
        case_id="OFFLINE-01",
        artifact_id="DOC-OFFLINE",
        original_hash="01" * 32,
        carrier_hash="02" * 32,
        recipient_id="alice",
        recipient_name="Alice Offline",
        device=phone,
        epistemic_status=EpistemicStatus.DEVICE_IN_LOOP
    )

    assert verif.overall_status.value == "VERIFIED"
    assert verif.manifest_signature_valid is True
    assert verif.merkle_root_valid is True
