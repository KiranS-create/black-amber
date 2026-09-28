"""
Unit tests for AegisTrace Device-Bound Sessions & Decryption Integration.

Verifies:
- BoundDeviceSession cryptographic binding (recipient, device, document, nonce, epoch)
- Replay prevention: presentation of Device A's session token from Device B is rejected
- Separation of powers in DecryptionDeviceBindingReceipt:
  * Recipient authorization (ML-DSA-65 signature)
  * Platform trust (Hardware attestation state)
- Policy enforcement: HIGH_ASSURANCE operations fail closed on UNATTESTED devices
- Graceful permission on ATTESTED hardware devices
"""

import hashlib
import pytest
from datetime import datetime, timezone
from Crypto.PublicKey import ECC

from core.crypto.signatures import MLDSA65
from core.device.models import (
    DevicePrincipal,
    AttestationState,
    DeviceStatus,
    PlatformType,
    HardwareClass,
)
from core.device.policy import (
    TrustPolicyEngine,
    OperationType,
    OperationAssuranceLevel,
)
from core.device.session import (
    DeviceSessionManager,
    BoundDeviceSession,
    DecryptionDeviceBindingReceipt,
)


def make_device(dev_id: str, att_state: AttestationState, hw_class: HardwareClass) -> DevicePrincipal:
    key = ECC.generate(curve="P-256")
    pem = key.public_key().export_key(format="PEM")
    key_id = f"dkey_{hashlib.sha256(pem.encode()).hexdigest()[:16]}"

    return DevicePrincipal(
        device_id=dev_id,
        organization_id="org_cyber_command",
        device_key_id=key_id,
        public_key_pem=pem,
        platform=PlatformType.TPM_2_0 if att_state == AttestationState.DEVICE_ATTESTED else PlatformType.SOFTWARE_LOCAL,
        hardware_class=hw_class,
        attestation_state=att_state,
        status=DeviceStatus.ACTIVE,
    )


def test_bound_session_creation_and_fingerprint():
    mgr = DeviceSessionManager()
    dev = make_device("dev_workstation", AttestationState.DEVICE_ATTESTED, HardwareClass.DEDICATED_HARDWARE_HSM)
    doc_hash = hashlib.sha256(b"classified_spec_doc").hexdigest()

    session = mgr.create_bound_session(
        session_id="ses_abc123",
        recipient_id="rec_analyst_bob",
        device=dev,
        document_root_hash=doc_hash,
        required_assurance=OperationAssuranceLevel.STANDARD,
    )

    assert session.session_id == "ses_abc123"
    assert session.recipient_id == "rec_analyst_bob"
    assert session.device_id == "dev_workstation"
    assert session.attestation_state == AttestationState.DEVICE_ATTESTED
    assert session.is_active is True

    fp1 = session.compute_session_fingerprint()
    fp2 = session.compute_session_fingerprint()
    assert fp1 == fp2
    assert len(fp1) == 64


def test_cross_device_replay_attack_rejected():
    """
    CRITICAL THREAT DEFENSE:
    Session token established on Device A presented from Device B MUST BE REJECTED.
    """
    mgr = DeviceSessionManager()
    dev_a = make_device("dev_secure_laptop", AttestationState.DEVICE_ATTESTED, HardwareClass.DEDICATED_HARDWARE_HSM)
    dev_b = make_device("dev_attacker_laptop", AttestationState.DEVICE_UNATTESTED, HardwareClass.SOFTWARE_FALLBACK)
    doc_hash = hashlib.sha256(b"intel_briefing").hexdigest()

    # Bob creates session on Device A
    session = mgr.create_bound_session(
        session_id="ses_legit_001",
        recipient_id="rec_bob",
        device=dev_a,
        document_root_hash=doc_hash,
    )

    # Legitimate access from Device A succeeds
    valid_a, reason_a = mgr.validate_session_access(
        session_id="ses_legit_001",
        presented_device=dev_a,
        document_root_hash=doc_hash,
    )
    assert valid_a is True
    assert reason_a is None

    # Replay attack: Attacker steals session token "ses_legit_001" and presents from Device B
    valid_b, reason_b = mgr.validate_session_access(
        session_id="ses_legit_001",
        presented_device=dev_b,
        document_root_hash=doc_hash,
    )
    assert valid_b is False
    assert "DEVICE_SESSION_MISMATCH" in (reason_b or "")


def test_document_mismatch_rejected():
    mgr = DeviceSessionManager()
    dev = make_device("dev_workstation", AttestationState.DEVICE_ATTESTED, HardwareClass.DEDICATED_HARDWARE_HSM)
    doc_hash_1 = hashlib.sha256(b"doc_1").hexdigest()
    doc_hash_2 = hashlib.sha256(b"doc_2").hexdigest()

    session = mgr.create_bound_session(
        session_id="ses_doc1",
        recipient_id="rec_bob",
        device=dev,
        document_root_hash=doc_hash_1,
    )

    # Attempting to use session for doc 2 is rejected
    valid, reason = mgr.validate_session_access(
        session_id="ses_doc1",
        presented_device=dev,
        document_root_hash=doc_hash_2,
    )
    assert valid is False
    assert "DOCUMENT_HASH_MISMATCH" in (reason or "")


def test_high_assurance_policy_blocks_unattested_device():
    """
    In HIGH_ASSURANCE mode, an UNATTESTED device cannot decrypt or open sessions.
    """
    mgr = DeviceSessionManager()
    soft_dev = make_device("dev_vm", AttestationState.DEVICE_UNATTESTED, HardwareClass.SOFTWARE_FALLBACK)
    doc_hash = hashlib.sha256(b"top_secret_plans").hexdigest()

    # Fails closed on UNATTESTED device
    with pytest.raises(PermissionError, match="HIGH_ASSURANCE"):
        mgr.create_bound_session(
            session_id="ses_fail",
            recipient_id="rec_alice",
            device=soft_dev,
            document_root_hash=doc_hash,
            required_assurance=OperationAssuranceLevel.HIGH_ASSURANCE,
        )


def test_decryption_receipt_separation_of_powers():
    """
    SEPARATION OF POWERS:
    - Recipient signs decryption authorization using post-quantum ML-DSA-65.
    - Device attestation state reflects hardware platform trust.
    Neither conflates with the other.
    """
    mgr = DeviceSessionManager()
    dev = make_device("dev_tpm_box", AttestationState.DEVICE_ATTESTED, HardwareClass.DEDICATED_HARDWARE_HSM)
    doc_hash = hashlib.sha256(b"payload").hexdigest()

    session = mgr.create_bound_session(
        session_id="ses_bind_1",
        recipient_id="rec_charlie",
        device=dev,
        document_root_hash=doc_hash,
    )

    # Recipient generates ML-DSA-65 signature
    kp = MLDSA65.generate_keypair()
    auth_preimage = f"DECRYPT_AUTH:{session.session_id}:{doc_hash}:{dev.device_id}".encode()
    sig = MLDSA65.sign(kp.private_key_bytes, auth_preimage)

    receipt = mgr.create_decryption_receipt(
        session=session,
        device=dev,
        recipient_signature_bytes=sig,
        recipient_signature_alg="ML-DSA-65",
        document_id="doc_alpha",
        dynamic_watermark_id="dyn_wm_98765",
    )

    assert receipt.recipient_id == "rec_charlie"
    assert receipt.device_id == dev.device_id
    assert receipt.device_attestation_state == AttestationState.DEVICE_ATTESTED
    assert receipt.recipient_signature_alg == "ML-DSA-65"
    assert receipt.dynamic_watermark_id == "dyn_wm_98765"
    assert receipt.session_fingerprint == session.compute_session_fingerprint()
