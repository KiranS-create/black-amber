"""
Unit & Integration Tests for AegisTrace Incremental Backup Chain Engine.
"""

import pytest
from core.crypto.signatures import MLDSA65
from core.recovery.models import BackupType, SignedBackupManifest, BackupObjectRecord
from core.recovery.format import ContentAddressedStore, BackupPackageBuilder
from core.recovery.crypto import BackupCryptoEngine
from core.recovery.chain import BackupChainManager, ChainValidationStatus


def build_manifest(
    backup_id: str,
    backup_type: BackupType,
    seq: int,
    tenant_id: str,
    kp,
    parent_id=None,
    parent_commitment=None,
):
    store = ContentAddressedStore()
    builder = BackupPackageBuilder(store)
    builder.add_dataset("data", [{"seq": seq}], tenant_id=tenant_id)
    
    m = SignedBackupManifest(
        backup_id=backup_id,
        backup_type=backup_type,
        tenant_id=tenant_id,
        backup_sequence=seq,
        source_system_id="node_1",
        parent_backup_id=parent_id,
        parent_backup_commitment=parent_commitment,
        datasets=list(builder.datasets),
        objects=builder.objects,
        merkle_root=builder.compute_merkle_root(),
        cryptographic_digest="",
        signer_id="operator_1",
        signer_public_key_b64=base64_encode(kp.public_key_bytes),
        signature_b64=""
    )
    return BackupCryptoEngine.sign_manifest(m, kp.private_key_bytes)


def test_valid_full_and_incremental_deltas_chain():
    kp = MLDSA65.generate_keypair()
    m0 = build_manifest("bkp_0", BackupType.FULL, 0, "tenant_a", kp)
    m1 = build_manifest("bkp_1", BackupType.DELTA, 1, "tenant_a", kp, m0.backup_id, m0.cryptographic_digest)
    m2 = build_manifest("bkp_2", BackupType.DELTA, 2, "tenant_a", kp, m1.backup_id, m1.cryptographic_digest)
    m3 = build_manifest("bkp_3", BackupType.DELTA, 3, "tenant_a", kp, m2.backup_id, m2.cryptographic_digest)

    res = BackupChainManager.validate_chain([m0, m1, m2, m3], expected_tenant_id="tenant_a")
    assert res.is_valid is True
    assert res.status == ChainValidationStatus.VALID
    assert res.verified_sequence_count == 4
    assert res.last_verified_sequence == 3
    assert res.tip_backup_id == "bkp_3"


def test_missing_delta_detected():
    kp = MLDSA65.generate_keypair()
    m0 = build_manifest("bkp_0", BackupType.FULL, 0, "tenant_a", kp)
    # Skip seq 1 directly to seq 2
    m2 = build_manifest("bkp_2", BackupType.DELTA, 2, "tenant_a", kp, m0.backup_id, m0.cryptographic_digest)

    res = BackupChainManager.validate_chain([m0, m2], expected_tenant_id="tenant_a")
    assert res.is_valid is False
    assert res.status == ChainValidationStatus.MISSING_DELTA
    assert "MISSING_DELTA" in res.error_message


def test_reordered_delta_detected():
    kp = MLDSA65.generate_keypair()
    m0 = build_manifest("bkp_0", BackupType.FULL, 0, "tenant_a", kp)
    m1 = build_manifest("bkp_1", BackupType.DELTA, 1, "tenant_a", kp, m0.backup_id, m0.cryptographic_digest)
    m2 = build_manifest("bkp_2", BackupType.DELTA, 2, "tenant_a", kp, m1.backup_id, m1.cryptographic_digest)

    # Reorder deltas [m0, m2, m1]
    res = BackupChainManager.validate_chain([m0, m2, m1], expected_tenant_id="tenant_a")
    assert res.is_valid is False
    # m2 received with expected seq 1, so gap detected
    assert res.status in (ChainValidationStatus.MISSING_DELTA, ChainValidationStatus.ROLLBACK_DETECTED)


def test_duplicate_delta_detected():
    kp = MLDSA65.generate_keypair()
    m0 = build_manifest("bkp_0", BackupType.FULL, 0, "tenant_a", kp)
    m1 = build_manifest("bkp_1", BackupType.DELTA, 1, "tenant_a", kp, m0.backup_id, m0.cryptographic_digest)

    res = BackupChainManager.validate_chain([m0, m1, m1], expected_tenant_id="tenant_a")
    assert res.is_valid is False
    assert res.status == ChainValidationStatus.DUPLICATE_DELTA


def test_wrong_parent_commitment_detected():
    kp = MLDSA65.generate_keypair()
    m0 = build_manifest("bkp_0", BackupType.FULL, 0, "tenant_a", kp)
    # Incorrect parent commitment
    m1 = build_manifest("bkp_1", BackupType.DELTA, 1, "tenant_a", kp, m0.backup_id, "0"*64)

    res = BackupChainManager.validate_chain([m0, m1], expected_tenant_id="tenant_a")
    assert res.is_valid is False
    assert res.status == ChainValidationStatus.WRONG_PARENT
    assert "ALTERED_PARENT_COMMITMENT" in res.error_message


def test_cross_tenant_backup_substitution_fails_closed():
    kp = MLDSA65.generate_keypair()
    m0 = build_manifest("bkp_0", BackupType.FULL, 0, "tenant_a", kp)
    # Delta belonging to tenant_b
    m1 = build_manifest("bkp_1", BackupType.DELTA, 1, "tenant_b", kp, m0.backup_id, m0.cryptographic_digest)

    res = BackupChainManager.validate_chain([m0, m1], expected_tenant_id="tenant_a")
    assert res.is_valid is False
    assert res.status == ChainValidationStatus.CROSS_TENANT_SUBSTITUTION


def base64_encode(data: bytes) -> str:
    import base64
    return base64.b64encode(data).decode('utf-8')
