"""
Unit & Integration Tests for AegisTrace Backup Format, Content-Addressed Storage,
and ML-DSA-65 Signed Manifests.
"""

import json
import pytest
from core.crypto.signatures import MLDSA65
from core.recovery.format import ContentAddressedStore, BackupPackageBuilder, canonical_json_bytes
from core.recovery.models import BackupType, SignedBackupManifest, BackupObjectRecord
from core.recovery.crypto import BackupCryptoEngine


def test_canonical_json_bytes_deterministic():
    data1 = {"b": 2, "a": 1, "c": [3, 2, 1]}
    data2 = {"a": 1, "c": [3, 2, 1], "b": 2}
    assert canonical_json_bytes(data1) == canonical_json_bytes(data2)
    assert b" " not in canonical_json_bytes(data1)  # Strict compact separators


def test_content_addressed_store_put_and_get():
    store = ContentAddressedStore()
    payload = b"Sample forensic document root content bytes"
    digest = store.put_bytes(payload)
    
    assert len(digest) == 64
    recovered = store.get_bytes(digest)
    assert recovered == payload
    assert store.has_object(digest) is True


def test_content_addressed_store_detects_tamper():
    store = ContentAddressedStore()
    payload = b"Original uncorrupted content"
    digest = store.put_bytes(payload)
    
    # Tamper with internal byte store
    store._memory_objects[digest] = b"Tampered malicious content"
    
    with pytest.raises(ValueError, match="CORRUPTED_OBJECT"):
        store.get_bytes(digest)


def test_backup_package_builder_merkle_root():
    store = ContentAddressedStore()
    builder = BackupPackageBuilder(store)
    
    rec1 = builder.add_dataset("dataset_a", [{"id": 1}], tenant_id="tenant_x")
    rec2 = builder.add_dataset("dataset_b", [{"id": 2}], tenant_id="tenant_x")
    
    merkle_root = builder.compute_merkle_root()
    assert len(merkle_root) == 64
    assert len(builder.objects) == 2


def test_mldsa65_manifest_signing_and_verification():
    kp = MLDSA65.generate_keypair()
    store = ContentAddressedStore()
    builder = BackupPackageBuilder(store)
    builder.add_dataset("test_events", [{"ev_id": "ev_001"}], tenant_id="tenant_alpha")
    
    merkle_root = builder.compute_merkle_root()
    manifest = SignedBackupManifest(
        backup_id="bkp_001",
        backup_type=BackupType.FULL,
        tenant_id="tenant_alpha",
        backup_sequence=0,
        source_system_id="node_1",
        datasets=list(builder.datasets),
        objects=builder.objects,
        merkle_root=merkle_root,
        cryptographic_digest="",
        signer_id="operator_alice",
        signer_public_key_b64=base64_encode(kp.public_key_bytes),
        signature_b64=""
    )
    
    signed = BackupCryptoEngine.sign_manifest(manifest, kp.private_key_bytes)
    assert len(signed.cryptographic_digest) == 64
    assert len(signed.signature_b64) > 0
    
    # Offline verification with embedded key
    is_valid, err = BackupCryptoEngine.verify_manifest(signed)
    assert is_valid is True
    assert err is None
    
    # Offline verification with explicit authority key
    is_valid_auth, _ = BackupCryptoEngine.verify_manifest(signed, expected_signer_public_key_bytes=kp.public_key_bytes)
    assert is_valid_auth is True


def test_modified_manifest_fails_verification():
    kp = MLDSA65.generate_keypair()
    store = ContentAddressedStore()
    builder = BackupPackageBuilder(store)
    builder.add_dataset("test_events", [{"ev_id": "ev_001"}], tenant_id="tenant_alpha")
    
    manifest = SignedBackupManifest(
        backup_id="bkp_002",
        backup_type=BackupType.FULL,
        tenant_id="tenant_alpha",
        backup_sequence=0,
        source_system_id="node_1",
        datasets=list(builder.datasets),
        objects=builder.objects,
        merkle_root=builder.compute_merkle_root(),
        cryptographic_digest="",
        signer_id="operator_alice",
        signer_public_key_b64=base64_encode(kp.public_key_bytes),
        signature_b64=""
    )
    signed = BackupCryptoEngine.sign_manifest(manifest, kp.private_key_bytes)
    
    # Modify manifest field after signing
    signed.backup_sequence = 1
    is_valid, err = BackupCryptoEngine.verify_manifest(signed)
    assert is_valid is False
    assert "DIGEST_MISMATCH" in err


def test_wrong_signing_key_fails_verification():
    kp1 = MLDSA65.generate_keypair()
    kp2 = MLDSA65.generate_keypair()
    
    store = ContentAddressedStore()
    builder = BackupPackageBuilder(store)
    builder.add_dataset("data", [{"val": 1}], tenant_id="tenant_1")
    
    manifest = SignedBackupManifest(
        backup_id="bkp_003",
        backup_type=BackupType.FULL,
        tenant_id="tenant_1",
        backup_sequence=0,
        source_system_id="node_1",
        datasets=list(builder.datasets),
        objects=builder.objects,
        merkle_root=builder.compute_merkle_root(),
        cryptographic_digest="",
        signer_id="operator_1",
        signer_public_key_b64=base64_encode(kp1.public_key_bytes),
        signature_b64=""
    )
    signed = BackupCryptoEngine.sign_manifest(manifest, kp1.private_key_bytes)
    
    # Verify against kp2 authority public key
    is_valid, err = BackupCryptoEngine.verify_manifest(signed, expected_signer_public_key_bytes=kp2.public_key_bytes)
    assert is_valid is False
    assert "SIGNATURE_VERIFICATION_FAILED" in err


def test_encrypted_backup_payload_with_aad_binding():
    payload = b'{"secret_forensic_evidence": "highly_sensitive_data_12345"}'
    passphrase = "correct-horse-battery-staple-passphrase"
    tenant = "tenant_secure"
    bkp_id = "bkp_enc_01"
    seq = 0
    
    envelope = BackupCryptoEngine.encrypt_payload(
        plaintext=payload,
        passphrase=passphrase,
        tenant_id=tenant,
        backup_id=bkp_id,
        backup_sequence=seq
    )
    
    # Decrypt with correct credentials
    decrypted = BackupCryptoEngine.decrypt_payload(
        envelope=envelope,
        passphrase=passphrase,
        expected_tenant_id=tenant,
        expected_backup_id=bkp_id,
        expected_sequence=seq
    )
    assert decrypted == payload
    
    # Decrypt with wrong passphrase fails closed
    with pytest.raises(ValueError, match="DECRYPTION_FAILED"):
        BackupCryptoEngine.decrypt_payload(
            envelope=envelope,
            passphrase="wrong-passphrase",
            expected_tenant_id=tenant,
            expected_backup_id=bkp_id,
            expected_sequence=seq
        )
    
    # Decrypt with wrong tenant fails closed
    with pytest.raises(PermissionError, match="CROSS_TENANT_REJECTED"):
        BackupCryptoEngine.decrypt_payload(
            envelope=envelope,
            passphrase=passphrase,
            expected_tenant_id="tenant_attacker",
            expected_backup_id=bkp_id,
            expected_sequence=seq
        )


def base64_encode(data: bytes) -> str:
    import base64
    return base64.b64encode(data).decode('utf-8')
