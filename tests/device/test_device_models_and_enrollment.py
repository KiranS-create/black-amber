"""
Unit tests for AegisTrace Device Models & Enrollment Service.

Verifies:
- DevicePrincipal schema and validation
- HardwareClass and PlatformType classification
- Multi-tenant isolation (org_a vs org_b separation)
- Key derivation and fingerprinting
- Enrollment lifecycle transitions (ACTIVE -> SUSPENDED -> REVOKED)
- Permanent block on re-registering or activating REVOKED devices
- Preserving audit trail of revocation events
"""

import pytest
from Crypto.PublicKey import ECC

from core.device.models import (
    DevicePrincipal,
    DeviceStatus,
    AttestationState,
    PlatformType,
    HardwareClass,
    AttestationEvidence,
    AttestationProviderType,
)
from core.device.enrollment import DeviceEnrollmentService
from core.device.challenge import ChallengeManager


def generate_ecc_pem() -> str:
    key = ECC.generate(curve="P-256")
    return key.public_key().export_key(format="PEM")


def test_device_principal_validation():
    pem = generate_ecc_pem()
    dev = DevicePrincipal(
        device_id="dev_alpha",
        organization_id="org_cyber_command",
        device_key_id="dkey_1234567890abcdef",
        public_key_pem=pem,
        public_key_algorithm="P-256",
        platform=PlatformType.TPM_2_0,
        hardware_class=HardwareClass.DEDICATED_HARDWARE_HSM,
        attestation_state=AttestationState.DEVICE_ATTESTED,
        registered_to_recipient_id="rec_analyst_01",
    )
    assert dev.device_id == "dev_alpha"
    assert dev.organization_id == "org_cyber_command"
    assert dev.platform == PlatformType.TPM_2_0
    assert dev.hardware_class == HardwareClass.DEDICATED_HARDWARE_HSM
    assert dev.status == DeviceStatus.ACTIVE
    assert dev.key_epoch == 1


def test_enrollment_service_basic_registration():
    svc = DeviceEnrollmentService()
    pem = generate_ecc_pem()

    dev = svc.register_device(
        device_id="dev_laptop_1",
        organization_id="org_defense",
        public_key_pem=pem,
        public_key_algorithm="P-256",
        platform=PlatformType.SOFTWARE_LOCAL,
        registered_to_recipient_id="rec_user_1",
    )

    assert dev.device_id == "dev_laptop_1"
    assert dev.organization_id == "org_defense"
    assert dev.status == DeviceStatus.ACTIVE
    # Unattested initial registration without evidence
    assert dev.attestation_state == AttestationState.DEVICE_UNATTESTED
    assert dev.hardware_class == HardwareClass.SOFTWARE_FALLBACK
    assert dev.device_key_id.startswith("dkey_")

    # Retrieval
    retrieved = svc.get_device("dev_laptop_1", "org_defense")
    assert retrieved is not None
    assert retrieved.device_id == dev.device_id


def test_enrollment_multi_tenant_isolation():
    svc = DeviceEnrollmentService()
    pem1 = generate_ecc_pem()
    pem2 = generate_ecc_pem()

    # Same device_id in two distinct organizations
    dev_org1 = svc.register_device(
        device_id="workstation_99",
        organization_id="org_alpha",
        public_key_pem=pem1,
        registered_to_recipient_id="rec_alice",
    )

    dev_org2 = svc.register_device(
        device_id="workstation_99",
        organization_id="org_beta",
        public_key_pem=pem2,
        registered_to_recipient_id="rec_bob",
    )

    assert dev_org1.organization_id == "org_alpha"
    assert dev_org2.organization_id == "org_beta"
    assert dev_org1.registered_to_recipient_id == "rec_alice"
    assert dev_org2.registered_to_recipient_id == "rec_bob"

    # Cross-tenant retrieval returns only the matching org
    assert svc.get_device("workstation_99", "org_alpha").registered_to_recipient_id == "rec_alice"
    assert svc.get_device("workstation_99", "org_beta").registered_to_recipient_id == "rec_bob"
    assert svc.get_device("workstation_99", "org_gamma") is None

    # Listing by org
    org_alpha_devs = svc.list_devices_for_organization("org_alpha")
    assert len(org_alpha_devs) == 1
    assert org_alpha_devs[0].organization_id == "org_alpha"


def test_duplicate_device_registration_rejection():
    svc = DeviceEnrollmentService()
    pem = generate_ecc_pem()

    svc.register_device(
        device_id="dev_unique",
        organization_id="org_finance",
        public_key_pem=pem,
    )

    with pytest.raises(ValueError, match="already enrolled"):
        svc.register_device(
            device_id="dev_unique",
            organization_id="org_finance",
            public_key_pem=pem,
        )


def test_device_lifecycle_suspension_and_reactivation():
    svc = DeviceEnrollmentService()
    pem = generate_ecc_pem()

    svc.register_device(
        device_id="dev_tablet",
        organization_id="org_aerospace",
        public_key_pem=pem,
    )

    # Suspend
    dev = svc.suspend_device("dev_tablet", "org_aerospace", reason="Device missing in transit")
    assert dev.status == DeviceStatus.SUSPENDED

    # Reactivate
    dev = svc.reactivate_device("dev_tablet", "org_aerospace")
    assert dev.status == DeviceStatus.ACTIVE


def test_device_permanent_revocation():
    svc = DeviceEnrollmentService()
    pem = generate_ecc_pem()

    svc.register_device(
        device_id="dev_compromised",
        organization_id="org_aerospace",
        public_key_pem=pem,
    )

    # Revoke
    revoked = svc.revoke_device(
        device_id="dev_compromised",
        organization_id="org_aerospace",
        reason="Security breach: physical key extraction",
    )
    assert revoked.status == DeviceStatus.REVOKED
    assert revoked.attestation_state == AttestationState.DEVICE_REVOKED
    assert revoked.revocation_reason == "Security breach: physical key extraction"
    assert revoked.revoked_at is not None

    # Revocation audit log
    log = svc.get_revocation_log()
    assert len(log) == 1
    assert log[0]["device_id"] == "dev_compromised"
    assert log[0]["reason"] == "Security breach: physical key extraction"

    # Cannot reactivate revoked device
    with pytest.raises(PermissionError, match="permanently REVOKED"):
        svc.reactivate_device("dev_compromised", "org_aerospace")

    # Cannot re-register revoked device
    with pytest.raises(PermissionError, match="permanently REVOKED"):
        svc.register_device(
            device_id="dev_compromised",
            organization_id="org_aerospace",
            public_key_pem=pem,
        )


def test_key_rotation_epoch_advancement():
    svc = DeviceEnrollmentService()
    pem1 = generate_ecc_pem()
    pem2 = generate_ecc_pem()

    dev = svc.register_device(
        device_id="dev_rotator",
        organization_id="org_defense",
        public_key_pem=pem1,
    )
    assert dev.key_epoch == 1
    initial_key_id = dev.device_key_id

    # Rotate
    rotated = svc.rotate_device_key(
        device_id="dev_rotator",
        organization_id="org_defense",
        new_public_key_pem=pem2,
    )
    assert rotated.key_epoch == 2
    assert rotated.device_key_id != initial_key_id
    assert rotated.public_key_pem == pem2
    # Rotating resets attestation to UNATTESTED until proven
    assert rotated.attestation_state == AttestationState.DEVICE_UNATTESTED
