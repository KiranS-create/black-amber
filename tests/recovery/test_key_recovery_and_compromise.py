"""
Unit & Integration Tests for AegisTrace Key Recovery & Temporal Validity Engine.
"""

from datetime import datetime, timezone, timedelta
import pytest
from core.crypto.lifecycle.models import (
    KeyRecord,
    KeyState,
    KeyType,
    KeyRecoveryClassification,
    KeyCustodyClass,
)
from core.crypto.lifecycle.backup import KeyBackupEngine, KeyBackupSecurityError
from core.recovery.key_recovery import (
    KeyRecoveryEngine,
    KeyOperationalStatus,
)


def test_key_status_classification():
    k_active = KeyRecord(
        key_id="kid_act",
        key_type=KeyType.RECIPIENT_PRIVATE_KEY,
        algorithm="ML-DSA-65",
        purpose="signing",
        owner="rec_1",
        status=KeyState.ACTIVE
    )
    assert KeyRecoveryEngine.evaluate_key_status(k_active) == KeyOperationalStatus.KEY_AVAILABLE

    k_comp = KeyRecord(
        key_id="kid_comp",
        key_type=KeyType.RECIPIENT_PRIVATE_KEY,
        algorithm="ML-DSA-65",
        purpose="signing",
        owner="rec_1",
        status=KeyState.COMPROMISED
    )
    assert KeyRecoveryEngine.evaluate_key_status(k_comp) == KeyOperationalStatus.KEY_COMPROMISED

    k_rev = KeyRecord(
        key_id="kid_rev",
        key_type=KeyType.RECIPIENT_PRIVATE_KEY,
        algorithm="ML-DSA-65",
        purpose="signing",
        owner="rec_1",
        status=KeyState.REVOKED
    )
    assert KeyRecoveryEngine.evaluate_key_status(k_rev) == KeyOperationalStatus.KEY_REVOKED


def test_temporal_validity_semantics():
    t_compromise = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    k_record = KeyRecord(
        key_id="kid_temporal",
        key_type=KeyType.RECIPIENT_PRIVATE_KEY,
        algorithm="ML-DSA-65",
        purpose="signing",
        owner="rec_1",
        status=KeyState.COMPROMISED,
        revocation_timestamp=t_compromise.isoformat()
    )

    # 1. Historical signature created BEFORE compromise (e.g. May 15) must be valid
    t_pre = datetime(2026, 5, 15, 10, 0, 0, tzinfo=timezone.utc).isoformat()
    val_pre = KeyRecoveryEngine.validate_signature_temporal_validity(k_record, t_pre)
    assert val_pre.is_valid is True
    assert val_pre.event_validity == "VALID_HISTORICAL"
    assert val_pre.status == "HISTORICAL_SIGNATURE_PRE_COMPROMISE"

    # 2. Signature created AFTER compromise (e.g. June 2) must be REJECTED
    t_post = datetime(2026, 6, 2, 10, 0, 0, tzinfo=timezone.utc).isoformat()
    val_post = KeyRecoveryEngine.validate_signature_temporal_validity(k_record, t_post)
    assert val_post.is_valid is False
    assert val_post.event_validity == "REJECTED"
    assert val_post.status == "KEY_COMPROMISED_AT_SIGNING"


def test_hardware_bound_key_export_strictly_forbidden():
    k_hw = KeyRecord(
        key_id="kid_tpm_01",
        key_type=KeyType.DEVICE_PRIVATE_KEY,
        algorithm="ML-DSA-65",
        purpose="device_auth",
        owner="dev_1",
        storage_class=KeyCustodyClass.HARDWARE_BACKED,
        recovery_class=KeyRecoveryClassification.HARDWARE_BOUND,
        status=KeyState.ACTIVE
    )

    # Must fail closed if attempting to backup hardware-bound key
    with pytest.raises(KeyBackupSecurityError, match="NON_EXPORTABLE_KEY"):
        KeyBackupEngine.create_backup_package(
            record=k_hw,
            private_key_bytes=b"dummy_bytes",
            passphrase="some-passphrase",
            tenant_id="default_tenant"
        )
