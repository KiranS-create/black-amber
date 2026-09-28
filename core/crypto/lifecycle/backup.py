"""
AegisTrace Air-Gapped Key Backup & Recovery Engine.

Provides authenticated encryption, integrity verification, and strict tenant isolation
for recoverable software keys. Refuses to export hardware-bound or non-recoverable keys.
"""

import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from typing import Dict, Any, Tuple, Optional
from pydantic import BaseModel, Field

from core.crypto.symmetric import encrypt_aes_gcm, decrypt_aes_gcm
from core.crypto.models import SymmetricCiphertext
from core.crypto.key_derivation import derive_key
from core.crypto.lifecycle.models import (
    KeyRecord,
    KeyRecoveryClassification,
    KeyType,
    KeyCustodyClass,
)


class KeyBackupSecurityError(PermissionError):
    """Raised when backup policies are violated (e.g. exporting hardware-bound keys)."""
    pass


class KeyBackupIntegrityError(ValueError):
    """Raised when a backup is corrupted, tampered, or fails authentication."""
    pass


class KeyBackupBundle(BaseModel):
    version: str = "1.0"
    key_id: str
    tenant_id: str
    owner: str
    key_type: str
    epoch: int
    algorithm: str
    salt_b64: str
    nonce_b64: str
    ciphertext_b64: str
    tag_b64: str
    metadata_digest: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class KeyBackupEngine:
    """
    Air-gapped Key Backup & Offline Recovery Engine.
    Operates 100% locally with zero external network or cloud KMS dependencies.
    """
    BACKUP_VERSION = "1.0"
    DOMAIN_SALT = b"AEGIS-BACKUP-SALT-ENVELOPE-V1"
    BACKUP_INFO = b"AEGIS-BACKUP-AES-256-GCM-KEY"

    @classmethod
    def _derive_backup_key(cls, passphrase: str, salt: bytes) -> bytes:
        """Derives a 256-bit AES-GCM key from passphrase using HKDF-SHA256."""
        ikm = passphrase.encode("utf-8")
        return derive_key(
            shared_secret=ikm,
            salt=salt,
            info=cls.BACKUP_INFO,
            length=32
        )

    @classmethod
    def create_backup_package(
        cls,
        record: KeyRecord,
        private_key_bytes: bytes,
        passphrase: str,
        tenant_id: str = "default_tenant"
    ) -> Dict[str, Any]:
        """
        Creates an encrypted, authenticated backup envelope for a recoverable key.
        Fails closed if the key is HARDWARE_BOUND or NON_RECOVERABLE.
        """
        if record.recovery_class == KeyRecoveryClassification.HARDWARE_BOUND:
            raise KeyBackupSecurityError(
                f"NON_EXPORTABLE_KEY: Key '{record.key_id}' is HARDWARE_BOUND to a secure processor and cannot be exported."
            )
        if record.recovery_class == KeyRecoveryClassification.NON_RECOVERABLE:
            raise KeyBackupSecurityError(
                f"NON_RECOVERABLE_KEY: Key '{record.key_id}' is marked NON_RECOVERABLE by policy."
            )
        if record.tenant_id != tenant_id:
            raise KeyBackupSecurityError(
                f"TENANT_MISMATCH: Cannot backup key from tenant '{record.tenant_id}' using tenant '{tenant_id}'"
            )

        salt = os.urandom(16)
        backup_key = cls._derive_backup_key(passphrase, salt)
        nonce = os.urandom(12)

        # Authenticated Associated Data (AAD) binds key identity and tenant
        aad = f"AEGIS-BACKUP:{cls.BACKUP_VERSION}:{record.key_id}:{record.tenant_id}:{record.owner}:{record.creation_epoch}".encode("utf-8")

        sym_cipher = encrypt_aes_gcm(backup_key, private_key_bytes, associated_data=aad, nonce=nonce)
        ciphertext = sym_cipher.ciphertext
        tag = sym_cipher.tag

        metadata_digest = hashlib.sha256(
            json.dumps(record.to_public_metadata(), sort_keys=True).encode("utf-8")
        ).hexdigest()

        return {
            "version": cls.BACKUP_VERSION,
            "key_id": record.key_id,
            "tenant_id": record.tenant_id,
            "owner": record.owner,
            "key_type": record.key_type.value,
            "epoch": record.creation_epoch,
            "algorithm": record.algorithm,
            "salt_b64": base64.b64encode(salt).decode("utf-8"),
            "nonce_b64": base64.b64encode(nonce).decode("utf-8"),
            "ciphertext_b64": base64.b64encode(ciphertext).decode("utf-8"),
            "tag_b64": base64.b64encode(tag).decode("utf-8"),
            "metadata_digest": metadata_digest,
            "metadata": record.to_public_metadata(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }

    @classmethod
    def restore_backup_package(
        cls,
        backup_pkg: Dict[str, Any],
        passphrase: str,
        target_tenant_id: str = "default_tenant"
    ) -> Tuple[KeyRecord, bytes]:
        """
        Restores a key from an encrypted backup envelope.
        Verifies tenant boundary, integrity hash, and authenticated decryption tag.
        """
        if backup_pkg.get("version") != cls.BACKUP_VERSION:
            raise KeyBackupIntegrityError(f"Unsupported backup version: {backup_pkg.get('version')}")

        pkg_tenant = backup_pkg.get("tenant_id")
        if pkg_tenant != target_tenant_id:
            raise KeyBackupSecurityError(
                f"CROSS_TENANT_RECOVERY_REJECTED: Backup belongs to tenant '{pkg_tenant}', cannot restore into '{target_tenant_id}'."
            )

        # Verify metadata integrity
        metadata = backup_pkg.get("metadata", {})
        computed_digest = hashlib.sha256(json.dumps(metadata, sort_keys=True).encode("utf-8")).hexdigest()
        if computed_digest != backup_pkg.get("metadata_digest"):
            raise KeyBackupIntegrityError("BACKUP_METADATA_TAMPERED: Metadata digest mismatch.")

        try:
            salt = base64.b64decode(backup_pkg["salt_b64"])
            nonce = base64.b64decode(backup_pkg["nonce_b64"])
            ciphertext = base64.b64decode(backup_pkg["ciphertext_b64"])
            tag = base64.b64decode(backup_pkg["tag_b64"])
        except Exception as e:
            raise KeyBackupIntegrityError(f"MALFORMED_BACKUP_ENCODING: {str(e)}")

        backup_key = cls._derive_backup_key(passphrase, salt)
        aad = f"AEGIS-BACKUP:{cls.BACKUP_VERSION}:{backup_pkg['key_id']}:{pkg_tenant}:{backup_pkg['owner']}:{backup_pkg['epoch']}".encode("utf-8")

        sym_cipher = SymmetricCiphertext(
            nonce=nonce,
            ciphertext=ciphertext,
            tag=tag,
            associated_data=aad
        )

        try:
            decrypted_private_bytes = decrypt_aes_gcm(backup_key, sym_cipher)
        except Exception:
            raise KeyBackupIntegrityError(
                "BACKUP_AUTHENTICATION_FAILED: Passphrase incorrect or backup payload corrupted/tampered."
            )

        # Reconstruct KeyRecord
        record = KeyRecord(
            key_id=metadata["key_id"],
            key_type=KeyType(metadata["key_type"]),
            algorithm=metadata["algorithm"],
            purpose=metadata["purpose"],
            owner=metadata["owner"],
            tenant_id=metadata["tenant_id"],
            creation_epoch=metadata["creation_epoch"],
            status=metadata["status"],
            creation_timestamp=metadata["creation_timestamp"],
            activation_timestamp=metadata.get("activation_timestamp"),
            rotation_timestamp=metadata.get("rotation_timestamp"),
            revocation_timestamp=metadata.get("revocation_timestamp"),
            predecessor_key_id=metadata.get("predecessor_key_id"),
            successor_key_id=metadata.get("successor_key_id"),
            storage_class=metadata["storage_class"],
            recovery_class=metadata["recovery_class"],
            public_material_b64=metadata.get("public_material_b64")
        )

        return record, decrypted_private_bytes
