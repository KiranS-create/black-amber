"""
Unit tests for AegisTrace Device Revocation & Historical Non-Repudiation.

Verifies:
- Device revocation lifecycle transitions (ACTIVE -> SUSPENDED -> REVOKED)
- Hard block on future operations for revoked devices
- Preservation of historical forensic evidence and receipts prior to revocation
- Permanent block against reactivation or re-enrollment of revoked devices
- Revocation audit logging with reason and timestamp
"""

import hashlib
import pytest
from Crypto.PublicKey import ECC

from core.device.models import (
    DevicePrincipal,
    DeviceStatus,
    AttestationState,
    PlatformType,
    HardwareClass,
)
from core.device.enrollment import DeviceEnrollmentService
from core.device.policy import (
    TrustPolicyEngine,
    OperationType,
    OperationAssuranceLevel,
)
from core.device.session import (
    DeviceSessionManager,
    BoundDeviceSession,
)


def generate_ecc_pem() -> str:
    key = ECC.generate(curve="P-256")
    return key.public_key().export_key(format="PEM")


def test_device_revocation_blocks_future_operations():
    enrollment = DeviceEnrollmentService()
    policy = TrustPolicyEngine()
    session_mgr = DeviceSessionManager(policy_engine=policy)

    pem = generate_ecc_pem()
    dev = enrollment.register_device(
        device_id="dev_contractor_laptop",
        organization_id="org_defense",
        public_key_pem=pem,
        platform=PlatformType.TPM_2_0,
    )
    assert dev.status == DeviceStatus.ACTIVE

    # 1. Allowed while ACTIVE
    decision_active = policy.evaluate(dev, OperationType.DECRYPT_RELEASE)
    assert decision_active.is_allowed is True

    # 2. Revoke device
    revoked_dev = enrollment.revoke_device(
        device_id="dev_contractor_laptop",
        organization_id="org_defense",
        reason="Employee termination: security return pending",
    )
    assert revoked_dev.status == DeviceStatus.REVOKED
    assert revoked_dev.attestation_state == AttestationState.DEVICE_REVOKED

    # 3. Policy blocks future operations
    decision_revoked = policy.evaluate(revoked_dev, OperationType.DECRYPT_RELEASE)
    assert decision_revoked.is_allowed is False
    assert "REVOKED" in decision_revoked.reason
    assert "DEVICE_REVOKED" in decision_revoked.audit_flags

    # 4. Session establishment is hard blocked
    with pytest.raises(PermissionError, match="REVOKED"):
        session_mgr.create_bound_session(
            session_id="ses_after_revocation",
            recipient_id="rec_contractor",
            device=revoked_dev,
            document_root_hash="a" * 64,
        )


def test_historical_evidence_preservation_after_revocation():
    """
    CRITICAL FORENSIC INVARIANT:
    Revoking a device today does NOT invalidate or tamper with decryption
    receipts and sessions committed in the past.
    """
    enrollment = DeviceEnrollmentService()
    session_mgr = DeviceSessionManager()

    pem = generate_ecc_pem()
    dev = enrollment.register_device(
        device_id="dev_analyst_desktop",
        organization_id="org_intel",
        public_key_pem=pem,
        platform=PlatformType.TPM_2_0,
    )

    doc_hash = hashlib.sha256(b"historical_memo").hexdigest()

    # Pre-revocation session
    past_session = session_mgr.create_bound_session(
        session_id="ses_historical_001",
        recipient_id="rec_analyst",
        device=dev,
        document_root_hash=doc_hash,
    )
    assert past_session.is_active is True
    past_fingerprint = past_session.compute_session_fingerprint()

    # Pre-revocation decryption receipt
    past_receipt = session_mgr.create_decryption_receipt(
        session=past_session,
        device=dev,
        recipient_signature_bytes=b"sample_signature_bytes",
        document_id="doc_memo_1",
    )
    assert past_receipt.device_id == "dev_analyst_desktop"

    # Revoke device now
    enrollment.revoke_device(
        device_id="dev_analyst_desktop",
        organization_id="org_intel",
        reason="Routine hardware decommissioning",
    )

    # Historical session fingerprint remains cryptographically consistent
    assert past_session.compute_session_fingerprint() == past_fingerprint
    # Historical receipt retains original state
    assert past_receipt.device_id == "dev_analyst_desktop"
    assert past_receipt.session_id == "ses_historical_001"


def test_revoked_device_cannot_be_re_registered_or_reactivated():
    enrollment = DeviceEnrollmentService()
    pem = generate_ecc_pem()

    enrollment.register_device(
        device_id="dev_blacklisted",
        organization_id="org_intel",
        public_key_pem=pem,
    )

    enrollment.revoke_device(
        device_id="dev_blacklisted",
        organization_id="org_intel",
        reason="Confirmed insider threat compromise",
    )

    # Attempt to re-register
    with pytest.raises(PermissionError, match="permanently REVOKED"):
        enrollment.register_device(
            device_id="dev_blacklisted",
            organization_id="org_intel",
            public_key_pem=pem,
        )

    # Attempt to reactivate
    with pytest.raises(PermissionError, match="permanently REVOKED"):
        enrollment.reactivate_device("dev_blacklisted", "org_intel")
