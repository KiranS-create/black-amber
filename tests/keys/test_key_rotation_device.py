"""
Tests for Device Attestation Key Lifecycle, Rotation & Anti-Replay.

Verifies:
- Enrolling a hardware-backed device key D1 at Epoch 1.
- Rotation to D2 at Epoch 2.
- Device identity continuity: device_id remains constant across epochs.
- Historical D1 events remain cryptographically verifiable.
- Future high-assurance sessions require D2.
- Anti-Replay: D1 signature replayed into a D2 session is strictly rejected.
- Anti-History-Rewriting: Presenting D2 identity for a historical D1 event fails verification.
- Hardware-bound export prevention: Hardware-backed device key cannot be exported via backup.
"""

import base64
import pytest
from datetime import datetime, timezone, timedelta

from core.crypto.lifecycle.manager import KeyLifecycleManager
from core.crypto.lifecycle.resolver import HistoricalKeyResolver, HistoricalResolutionStatus
from core.crypto.lifecycle.adapters import DeviceKeyLifecycleAdapter
from core.crypto.lifecycle.backup import KeyBackupEngine, KeyBackupSecurityError
from core.crypto.lifecycle.models import KeyState, KeyType, KeyCustodyClass, KeyRecoveryClassification
from core.crypto.signatures import MLDSA65


def test_device_key_rotation_and_historical_verification():
    mgr = KeyLifecycleManager()
    resolver = HistoricalKeyResolver(mgr)
    adapter = DeviceKeyLifecycleAdapter(mgr)

    device_id = "dev_secured_workstation_9c2a"

    # Step 1: Enroll Device D1 at Epoch 1
    # Use real ML-DSA-65 keys for cryptographic testing
    kp1 = MLDSA65.generate_keypair()
    pub1_pem = base64.b64encode(kp1.public_key_bytes).decode("utf-8")

    rec1 = adapter.enroll_device(
        device_id=device_id,
        public_key_pem=pub1_pem,
        algorithm="ML-DSA-65",
        is_hardware_backed=True
    )
    assert rec1.owner == device_id
    assert rec1.creation_epoch == 1
    assert rec1.status == KeyState.ACTIVE
    assert rec1.storage_class == KeyCustodyClass.HARDWARE_BACKED
    assert rec1.recovery_class == KeyRecoveryClassification.HARDWARE_BOUND

    # Step 2: Device D1 signs Attestation Challenge at T1
    t0_dt = datetime.fromisoformat(rec1.creation_timestamp)
    t1 = (t0_dt + timedelta(minutes=1)).isoformat()
    challenge1 = b"AEGIS-DEVICE-CHALLENGE:1:nonce_alpha_001"
    sig1 = MLDSA65.sign(kp1.private_key_bytes, challenge1)

    # Historical resolution for T1 under Epoch 1 succeeds
    hist_res1 = resolver.resolve_historical_key(
        owner=device_id,
        key_type=KeyType.DEVICE_PUBLIC_KEY,
        event_timestamp=t1,
        event_epoch=1
    )
    assert hist_res1.is_valid is True
    assert hist_res1.status == HistoricalResolutionStatus.HISTORICALLY_VALID
    pub1_bytes = base64.b64decode(hist_res1.public_material_b64)
    assert MLDSA65.verify(pub1_bytes, challenge1, sig1) is True

    # Step 3: Rotate Device Key to D2 at T2
    t2 = (t0_dt + timedelta(minutes=2)).isoformat()
    kp2 = MLDSA65.generate_keypair()
    pub2_pem = base64.b64encode(kp2.public_key_bytes).decode("utf-8")

    prev_dev, next_dev = adapter.rotate_device_key(
        device_id=device_id,
        new_public_key_pem=pub2_pem,
        algorithm="ML-DSA-65",
        is_hardware_backed=True,
        reason="TPM Endorsement Key renewal"
    )

    # Invariant: Device Identity Continuity
    assert next_dev.owner == device_id
    assert next_dev.creation_epoch == 2
    assert next_dev.status == KeyState.ACTIVE
    assert prev_dev.status == KeyState.RETIRED
    assert next_dev.predecessor_key_id == prev_dev.key_id

    # Step 4: Device signs new Session Challenge under D2 at T3
    t3 = (t0_dt + timedelta(minutes=3)).isoformat()
    challenge2 = b"AEGIS-DEVICE-CHALLENGE:2:nonce_beta_002"
    sig2 = MLDSA65.sign(kp2.private_key_bytes, challenge2)

    active_dev_key = mgr.get_active_key(device_id, KeyType.DEVICE_PUBLIC_KEY)
    assert active_dev_key.key_id == next_dev.key_id
    pub2_bytes = base64.b64decode(active_dev_key.public_material_b64)
    assert MLDSA65.verify(pub2_bytes, challenge2, sig2) is True

    # Step 5: Anti-Replay Invariant!
    # Replaying D1 signature into D2 session MUST FAIL
    assert MLDSA65.verify(pub2_bytes, challenge2, sig1) is False

    # Step 6: Anti-History-Rewriting Invariant!
    # Presenting D2 identity for D1 historical challenge MUST FAIL
    assert MLDSA65.verify(pub2_bytes, challenge1, sig1) is False

    # Step 7: Historical Verifiability Invariant!
    # D1 challenge at T1 remains verifiable after rotation
    hist_after_rot = resolver.resolve_historical_key(
        owner=device_id,
        key_type=KeyType.DEVICE_PUBLIC_KEY,
        event_timestamp=t1,
        event_epoch=1
    )
    assert hist_after_rot.is_valid is True
    assert MLDSA65.verify(base64.b64decode(hist_after_rot.public_material_b64), challenge1, sig1) is True


def test_device_hardware_bound_backup_prevention():
    """Hardware-backed TPM device keys cannot be exported via backup."""
    mgr = KeyLifecycleManager()
    adapter = DeviceKeyLifecycleAdapter(mgr)
    dev_rec = adapter.enroll_device("dev_tpm_isolated", "pub_pem_fake", is_hardware_backed=True)

    with pytest.raises(KeyBackupSecurityError, match="NON_EXPORTABLE_KEY"):
        KeyBackupEngine.create_backup_package(
            record=dev_rec,
            private_key_bytes=b"attempted_private_export",
            passphrase="master_passphrase"
        )
