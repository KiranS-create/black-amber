"""
Tests for AegisTrace Cryptographic Key Backup and Recovery.
Verifies:
1. Encrypted export and restore using AES-256-GCM + HKDF.
2. Hardware-bound keys (HARDWARE_BACKED / HARDWARE_BOUND) refuse private key export.
3. NON_RECOVERABLE keys refuse private key export.
4. Tampered ciphertext or wrong passphrase fails closed (AEAD tag mismatch).
5. Cross-tenant isolation during backup export and restore.
"""

import pytest
import base64
from core.crypto.lifecycle.models import (
    KeyType,
    KeyCustodyClass,
    KeyRecoveryClassification,
    KeyState
)
from core.crypto.lifecycle.manager import KeyLifecycleManager
from core.crypto.lifecycle.backup import (
    KeyBackupEngine,
    KeyBackupSecurityError,
    KeyBackupIntegrityError
)


def test_encrypted_backup_and_restore_cycle():
    mgr = KeyLifecycleManager()

    # Register recoverable keys
    k1 = mgr.register_key(
        owner="rec_alice",
        key_type=KeyType.RECIPIENT_PRIVATE_KEY,
        algorithm="ML-DSA-65",
        purpose="Signing",
        custody_class=KeyCustodyClass.SECURE_KEYSTORE,
        recovery_class=KeyRecoveryClassification.RECOVERABLE,
        public_material_b64="cHVibGljX21hdGVyaWFsX2FsaWNl",
        activate_immediately=True
    )

    private_key_bytes = b"SUPER_SECRET_RECIPIENT_PRIVATE_KEY_BYTES_MLDSA65"
    passphrase = "Correct-Horse-Battery-Staple-Airgap-2026!"

    # Export backup package
    backup_pkg = KeyBackupEngine.create_backup_package(
        record=k1,
        private_key_bytes=private_key_bytes,
        passphrase=passphrase,
        tenant_id="default_tenant"
    )

    assert backup_pkg["version"] == "1.0"
    assert backup_pkg["key_id"] == k1.key_id
    assert backup_pkg["tenant_id"] == "default_tenant"
    assert "ciphertext_b64" in backup_pkg
    assert "tag_b64" in backup_pkg

    # Restore backup package
    restored_record, restored_priv_bytes = KeyBackupEngine.restore_backup_package(
        backup_pkg=backup_pkg,
        passphrase=passphrase,
        target_tenant_id="default_tenant"
    )

    assert restored_record.key_id == k1.key_id
    assert restored_record.owner == "rec_alice"
    assert restored_record.status == KeyState.ACTIVE
    assert restored_record.public_material_b64 == "cHVibGljX21hdGVyaWFsX2FsaWNl"
    assert restored_priv_bytes == private_key_bytes


def test_hardware_bound_and_non_recoverable_refuse_export():
    mgr = KeyLifecycleManager()

    # 1. Hardware bound key (e.g. Device HSM/YubiKey)
    hw_key = mgr.register_key(
        owner="dev_hardware_token_01",
        key_type=KeyType.DEVICE_PRIVATE_KEY,
        algorithm="P-256",
        purpose="Device Attestation",
        custody_class=KeyCustodyClass.HARDWARE_BACKED,
        recovery_class=KeyRecoveryClassification.HARDWARE_BOUND,
        public_material_b64="aHdfcHVi",
        activate_immediately=True
    )

    # 2. Non-recoverable session key
    ephem_key = mgr.register_key(
        owner="sess_temp_001",
        key_type=KeyType.MASTER_EPHEMERAL_KEY,
        algorithm="AES-256-GCM",
        purpose="Transient Decryption",
        custody_class=KeyCustodyClass.LOCAL_PROTECTED_STORE,
        recovery_class=KeyRecoveryClassification.NON_RECOVERABLE,
        public_material_b64="ZXBoX3B1Yg==",
        activate_immediately=True
    )

    passphrase = "Master-Recovery-Key-999"

    # Attempting to export hardware-bound key raises KeyBackupSecurityError
    with pytest.raises(KeyBackupSecurityError, match="NON_EXPORTABLE_KEY"):
        KeyBackupEngine.create_backup_package(
            record=hw_key,
            private_key_bytes=b"SHOULD_NOT_LEAK",
            passphrase=passphrase
        )

    # Attempting to export non-recoverable key raises KeyBackupSecurityError
    with pytest.raises(KeyBackupSecurityError, match="NON_RECOVERABLE_KEY"):
        KeyBackupEngine.create_backup_package(
            record=ephem_key,
            private_key_bytes=b"EPHEMERAL_SECRET",
            passphrase=passphrase
        )


def test_tampered_backup_fails_closed():
    mgr = KeyLifecycleManager()

    k = mgr.register_key(
        owner="rec_bob",
        key_type=KeyType.RECIPIENT_PRIVATE_KEY,
        algorithm="ML-DSA-65",
        purpose="Signing",
        custody_class=KeyCustodyClass.SECURE_KEYSTORE,
        recovery_class=KeyRecoveryClassification.RECOVERABLE,
        public_material_b64="Ym9iX3B1Yg==",
        activate_immediately=True
    )

    passphrase = "Secret-Password-12345"
    priv_bytes = b"BOB_PRIVATE_KEY"
    pkg = KeyBackupEngine.create_backup_package(k, priv_bytes, passphrase)

    # 1. Wrong passphrase test
    with pytest.raises(KeyBackupIntegrityError, match="BACKUP_AUTHENTICATION_FAILED"):
        KeyBackupEngine.restore_backup_package(pkg, passphrase="WRONG-PASSWORD-67890")

    # 2. Tampered ciphertext test (flip byte in ciphertext_b64)
    raw_ct = base64.b64decode(pkg["ciphertext_b64"])
    tampered_ct = bytearray(raw_ct)
    tampered_ct[0] ^= 0xFF
    pkg_tampered_ct = dict(pkg)
    pkg_tampered_ct["ciphertext_b64"] = base64.b64encode(tampered_ct).decode("utf-8")

    with pytest.raises(KeyBackupIntegrityError, match="BACKUP_AUTHENTICATION_FAILED"):
        KeyBackupEngine.restore_backup_package(pkg_tampered_ct, passphrase=passphrase)

    # 3. Tampered metadata test
    pkg_tampered_meta = dict(pkg)
    pkg_tampered_meta["metadata"] = dict(pkg["metadata"])
    pkg_tampered_meta["metadata"]["owner"] = "rec_eve_attacker"

    with pytest.raises(KeyBackupIntegrityError, match="BACKUP_METADATA_TAMPERED"):
        KeyBackupEngine.restore_backup_package(pkg_tampered_meta, passphrase=passphrase)


def test_cross_tenant_isolation_in_backup():
    mgr = KeyLifecycleManager()

    k_alpha = mgr.register_key(
        owner="tenant_a_user",
        key_type=KeyType.RECIPIENT_PRIVATE_KEY,
        algorithm="ML-DSA-65",
        purpose="Tenant A Key",
        tenant_id="TENANT_ALPHA",
        custody_class=KeyCustodyClass.SECURE_KEYSTORE,
        recovery_class=KeyRecoveryClassification.RECOVERABLE,
        public_material_b64="YWxwaGFfcHVi",
        activate_immediately=True
    )

    passphrase = "Alpha-Tenant-Passphrase"
    pkg_alpha = KeyBackupEngine.create_backup_package(
        record=k_alpha,
        private_key_bytes=b"TENANT_A_SECRET",
        passphrase=passphrase,
        tenant_id="TENANT_ALPHA"
    )

    assert pkg_alpha["tenant_id"] == "TENANT_ALPHA"

    # Attempting to restore into TENANT_BETA without matching tenant ID fails
    with pytest.raises(KeyBackupSecurityError, match="CROSS_TENANT_RECOVERY_REJECTED"):
        KeyBackupEngine.restore_backup_package(
            backup_pkg=pkg_alpha,
            passphrase=passphrase,
            target_tenant_id="TENANT_BETA"
        )
