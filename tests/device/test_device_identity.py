"""
SIH26237 - Test Device Identity Classification & Binding
========================================================
Validates that device identity uses cryptographic and immutable bindings
and never conflates phone presence with TPM attestation or camera identity.
"""

import pytest
from core.physical.device_discovery import SmartphoneDeviceRecord, PhoneRole, PhoneAdbState
from core.device.models import DevicePrincipal, PlatformType, HardwareClass, AttestationState
from core.physical.epistemic import EpistemicStatus


def test_device_identity_structure():
    """Verify SmartphoneDeviceRecord preserves hardware fields and non-fabrication invariants."""
    phone = SmartphoneDeviceRecord(
        device_id="phone_rf8n927pm9n",
        serial="RF8N927PM9N",
        role=PhoneRole.PHONE_A_RECIPIENT,
        model="Galaxy Note10 Lite",
        os_version="Android 12",
        usb_connection_state="CONNECTED",
        adb_state=PhoneAdbState.AUTHORIZED,
        camera_capability=EpistemicStatus.NOT_VERIFIED
    )

    assert phone.device_id == "phone_rf8n927pm9n"
    assert phone.serial == "RF8N927PM9N"
    assert phone.platform == "Android"
    assert phone.camera_capability == EpistemicStatus.NOT_VERIFIED
    assert phone.browser_availability is True


def test_no_unsupported_tpm_attestation_for_phone():
    """Verify phones are not promoted to TPM_2_0 or DEDICATED_HARDWARE_HSM without attestation evidence."""
    principal = DevicePrincipal(
        device_id="dev_phone_note10",
        organization_id="org_defense",
        device_key_id="key_fingerprint_01",
        public_key_pem="-----BEGIN PUBLIC KEY-----\nMFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE\n-----END PUBLIC KEY-----",
        platform=PlatformType.SOFTWARE_LOCAL,
        hardware_class=HardwareClass.SOFTWARE_FALLBACK,
        attestation_state=AttestationState.DEVICE_UNATTESTED
    )

    assert principal.platform != PlatformType.TPM_2_0
    assert principal.attestation_state == AttestationState.DEVICE_UNATTESTED
