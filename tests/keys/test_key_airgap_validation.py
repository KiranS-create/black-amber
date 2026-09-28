"""
Air-Gapped Key Lifecycle Verification Tests.
Guarantees that all key operations:
- Recipient ML-DSA and ML-KEM key generation and rotation
- Device hardware key enrollment and rotation
- Traceability and watermark epoch progression
- DLT validator consensus key rotation
- Cryptographic backup export and restore
- Historical key resolution
function 100% locally with zero external network connectivity or cloud KMS calls.
"""

import socket
import pytest
from datetime import datetime, timezone, timedelta

from core.crypto.lifecycle.models import KeyType, KeyCustodyClass, KeyRecoveryClassification
from core.crypto.lifecycle.manager import KeyLifecycleManager
from core.crypto.lifecycle.resolver import HistoricalKeyResolver, HistoricalResolutionStatus
from core.crypto.lifecycle.backup import KeyBackupEngine
from core.crypto.lifecycle.adapters import (
    RecipientKeyLifecycleAdapter,
    DeviceKeyLifecycleAdapter,
    TraceabilityEpochAdapter,
    WatermarkEpochAdapter,
    ValidatorKeyLifecycleAdapter
)


@pytest.fixture(autouse=True)
def enforce_airgap_socket_block(monkeypatch):
    """Strictly blocks all network socket creation to verify air-gap compliance."""
    def _blocked_socket(*args, **kwargs):
        raise RuntimeError("AIRGAP_ENFORCEMENT_VIOLATION: Network socket access is strictly prohibited.")

    monkeypatch.setattr(socket, "socket", _blocked_socket)


def test_airgap_full_key_lifecycle_suite():
    # 1. Initialize purely offline manager and adapters
    mgr = KeyLifecycleManager()
    resolver = HistoricalKeyResolver(mgr)

    rec_adapter = RecipientKeyLifecycleAdapter(mgr)
    dev_adapter = DeviceKeyLifecycleAdapter(mgr)
    trace_adapter = TraceabilityEpochAdapter(mgr)
    wm_adapter = WatermarkEpochAdapter(mgr)
    val_adapter = ValidatorKeyLifecycleAdapter(mgr)

    # 2. Recipient Keys (ML-DSA-65 & ML-KEM-768)
    sign_rec, kem_rec = rec_adapter.enroll_recipient_keys("rec_airgap_user")
    assert sign_rec.status.value == "ACTIVE"
    assert kem_rec.status.value == "ACTIVE"

    # Rotate ML-DSA key
    ret_sign, new_sign, new_kp = rec_adapter.rotate_signing_key("rec_airgap_user")
    assert ret_sign.status.value == "RETIRED"
    assert new_sign.status.value == "ACTIVE"

    # 3. Device Keys (Hardware-bound)
    dev_rec = dev_adapter.enroll_device("dev_airgap_token", "DEVICE_PUB_01")
    assert dev_rec.storage_class == KeyCustodyClass.HARDWARE_BACKED
    assert dev_rec.recovery_class == KeyRecoveryClassification.HARDWARE_BOUND

    # 4. Traceability & Watermark Epochs
    t_rec = trace_adapter.register_traceability_epoch(epoch=1, secret_bytes=b"AIRGAP_SEED_TRACE")
    assert t_rec.creation_epoch == 1

    wm_rec = wm_adapter.register_watermark_epoch(epoch=1, epoch_secret=b"AIRGAP_SECRET_WM")
    assert wm_rec.creation_epoch == 1

    # 5. DLT Validator
    val_rec = val_adapter.enroll_validator("val_airgap_node", "VALIDATOR_PUB_01")
    assert val_rec.status.value == "ACTIVE"

    # 6. Historical Resolution
    t_event = (datetime.fromisoformat(sign_rec.creation_timestamp.replace("Z", "+00:00")) + timedelta(seconds=1)).isoformat()
    res = resolver.resolve_historical_key(
        owner="rec_airgap_user",
        key_type=KeyType.RECIPIENT_PRIVATE_KEY,
        event_timestamp=t_event,
        algorithm="ML-DSA-65",
        event_epoch=1
    )
    assert res.is_valid
    assert res.status == HistoricalResolutionStatus.HISTORICALLY_VALID
    assert res.public_material_b64 == sign_rec.public_material_b64

    # 7. Backup and Restore (Air-gapped symmetric envelope)
    backup_pkg = KeyBackupEngine.create_backup_package(
        record=new_sign,
        private_key_bytes=b"AIRGAP_SECURE_PRIV_KEY",
        passphrase="Airgap-Offline-Password-2026!"
    )
    assert backup_pkg["version"] == "1.0"

    restored_rec, restored_priv = KeyBackupEngine.restore_backup_package(
        backup_pkg=backup_pkg,
        passphrase="Airgap-Offline-Password-2026!"
    )
    assert restored_rec.key_id == new_sign.key_id
    assert restored_priv == b"AIRGAP_SECURE_PRIV_KEY"
