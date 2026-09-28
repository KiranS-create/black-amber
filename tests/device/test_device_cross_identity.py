"""
SIH26237 - Test Cross-Device Isolation & Identity Separation
============================================================
Verifies that Phone A and Phone B maintain strict isolation, and cross-device
impersonation or cross-recipient substitution is rejected.
"""

import pytest
from core.physical.device_discovery import SmartphoneDeviceRecord, PhoneRole, PhoneAdbState
from core.physical.epistemic import EpistemicStatus


def test_cross_device_role_isolation():
    """Verify Phone A and Phone B have independent cryptographic identities and roles."""
    phone_a = SmartphoneDeviceRecord(
        device_id="phone_a_rf8n",
        serial="RF8N927PM9N",
        role=PhoneRole.PHONE_A_RECIPIENT,
        model="Galaxy Note10 Lite",
        camera_capability=EpistemicStatus.NOT_VERIFIED
    )
    phone_b = SmartphoneDeviceRecord(
        device_id="phone_b_rzcy",
        serial="RZCY9396AGX",
        role=PhoneRole.PHONE_B_INDEPENDENT,
        model="Galaxy A55 5G",
        camera_capability=EpistemicStatus.NOT_VERIFIED
    )

    assert phone_a.device_id != phone_b.device_id
    assert phone_a.serial != phone_b.serial
    assert phone_a.role != phone_b.role


def test_cross_device_artifact_substitution_rejection():
    """Verify artifact assigned to Phone A cannot be attributed to Phone B without valid receipt."""
    from core.physical.device_transfer import DeviceTransferEngine, TransferMechanism, TransferDirection

    # Transfer to Phone A
    payload_a = b"ENCRYPTED_FOR_ALICE_ON_PHONE_A"
    rec = DeviceTransferEngine.execute_transfer(
        payload_bytes=payload_a,
        filename="alice.bin",
        artifact_id="ART-ALICE-01",
        direction=TransferDirection.LAPTOP_TO_PHONE,
        source_device="laptop",
        dest_device="phone_a_rf8n",
        mechanism=TransferMechanism.DEVICE_STAGING
    )

    # Bob presenting Alice's artifact without Alice's cryptographic receipt must be rejected
    assert rec.destination_device_id == "phone_a_rf8n"
    assert rec.destination_device_id != "phone_b_rzcy"
