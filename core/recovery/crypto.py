"""
AegisTrace Backup Cryptography & Post-Quantum Manifest Signing Engine.

Provides:
1. Authenticated encryption (AES-256-GCM + HKDF-SHA256) for backup confidentiality.
2. Cryptographic binding with Authenticated Associated Data (AAD).
3. Post-quantum digital signature generation and offline verification (ML-DSA-65).
"""

import base64
import hashlib
import json
import os
from typing import Dict, Any, Optional, Tuple

from core.crypto.signatures import MLDSA65
from core.crypto.symmetric import encrypt_aes_gcm, decrypt_aes_gcm
from core.crypto.models import SymmetricCiphertext
from core.crypto.key_derivation import derive_key
from core.recovery.models import SignedBackupManifest


class BackupCryptoEngine:
    """
    Cryptographic operations for backup confidentiality, authenticity, and manifest signing.
    Operates 100% locally with zero cloud KMS or remote certificate authority dependencies.
    """
    SALT_INFO = b"AEGIS-BACKUP-PAYLOAD-ENCRYPTION-V1"

    @classmethod
    def derive_encryption_key(cls, passphrase: str, salt: bytes) -> bytes:
        """Derives a 256-bit AES key from a passphrase/secret using HKDF-SHA256."""
        ikm = passphrase.encode('utf-8')
        return derive_key(
            shared_secret=ikm,
            salt=salt,
            info=cls.SALT_INFO,
            length=32
        )

    @classmethod
    def compute_aad(
        cls,
        tenant_id: str,
        backup_id: str,
        backup_sequence: int,
        schema_version: str
    ) -> bytes:
        """
        Computes Authenticated Associated Data (AAD) binding ciphertext to tenant and backup sequence.
        Prevents cross-tenant ciphertext transplanting, sequence replay, and schema substitution.
        """
        return f"AEGIS-AAD:v{schema_version}:tenant={tenant_id}:bkp={backup_id}:seq={backup_sequence}".encode('utf-8')

    @classmethod
    def encrypt_payload(
        cls,
        plaintext: bytes,
        passphrase: str,
        tenant_id: str,
        backup_id: str,
        backup_sequence: int,
        schema_version: str = "1.0"
    ) -> Dict[str, Any]:
        """
        Encrypts backup payload with AES-256-GCM and authenticated metadata binding.
        """
        salt = os.urandom(16)
        key = cls.derive_encryption_key(passphrase, salt)
        nonce = os.urandom(12)
        aad = cls.compute_aad(tenant_id, backup_id, backup_sequence, schema_version)
        
        sym_cipher = encrypt_aes_gcm(key, plaintext, associated_data=aad, nonce=nonce)
        
        return {
            "salt_b64": base64.b64encode(salt).decode('utf-8'),
            "nonce_b64": base64.b64encode(sym_cipher.nonce).decode('utf-8'),
            "tag_b64": base64.b64encode(sym_cipher.tag).decode('utf-8'),
            "ciphertext_b64": base64.b64encode(sym_cipher.ciphertext).decode('utf-8'),
            "tenant_id": tenant_id,
            "backup_id": backup_id,
            "backup_sequence": backup_sequence,
        }

    @classmethod
    def decrypt_payload(
        cls,
        envelope: Dict[str, Any],
        passphrase: str,
        expected_tenant_id: str,
        expected_backup_id: str,
        expected_sequence: int,
        schema_version: str = "1.0"
    ) -> bytes:
        """
        Decrypts backup payload with AES-256-GCM, verifying all AAD bindings.
        Fails closed on wrong password, tampered ciphertext, or tenant/sequence substitution.
        """
        # Validate metadata before decryption
        if envelope.get("tenant_id") != expected_tenant_id:
            raise PermissionError(
                f"CROSS_TENANT_REJECTED: Envelope tenant '{envelope.get('tenant_id')}' != expected '{expected_tenant_id}'"
            )
        if envelope.get("backup_id") != expected_backup_id:
            raise ValueError(
                f"BACKUP_ID_MISMATCH: Envelope backup '{envelope.get('backup_id')}' != expected '{expected_backup_id}'"
            )
        if envelope.get("backup_sequence") != expected_sequence:
            raise ValueError(
                f"SEQUENCE_MISMATCH: Envelope sequence {envelope.get('backup_sequence')} != expected {expected_sequence}"
            )

        salt = base64.b64decode(envelope["salt_b64"])
        nonce = base64.b64decode(envelope["nonce_b64"])
        tag = base64.b64decode(envelope["tag_b64"])
        ciphertext = base64.b64decode(envelope["ciphertext_b64"])

        key = cls.derive_encryption_key(passphrase, salt)
        aad = cls.compute_aad(expected_tenant_id, expected_backup_id, expected_sequence, schema_version)

        sym_cipher = SymmetricCiphertext(
            nonce=nonce,
            ciphertext=ciphertext,
            tag=tag,
            associated_data=aad
        )
        try:
            return decrypt_aes_gcm(key, sym_cipher)
        except Exception as e:
            raise ValueError(f"DECRYPTION_FAILED: Ciphertext corrupted, wrong key, or tampered AAD: {str(e)}")

    @classmethod
    def sign_manifest(
        cls,
        manifest: SignedBackupManifest,
        signing_private_key_bytes: bytes
    ) -> SignedBackupManifest:
        """
        Signs the canonical backup manifest payload using ML-DSA-65 post-quantum signature.
        Updates cryptographic_digest and signature_b64 in-place.
        """
        canonical_bytes = manifest.canonical_manifest_bytes()
        digest = hashlib.sha256(canonical_bytes).hexdigest()
        
        sig_bytes = MLDSA65.sign(signing_private_key_bytes, canonical_bytes)
        sig_b64 = base64.b64encode(sig_bytes).decode('utf-8')
        
        manifest.cryptographic_digest = digest
        manifest.signature_b64 = sig_b64
        return manifest

    @classmethod
    def verify_manifest(
        cls,
        manifest: SignedBackupManifest,
        expected_signer_public_key_bytes: Optional[bytes] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Verifies the ML-DSA-65 signature and digest over the canonical backup manifest.
        Supports completely offline verification using embedded public key or explicit authority key.
        Returns: (is_valid, error_message_if_any)
        """
        if not manifest.signature_b64:
            return False, "MISSING_SIGNATURE: Manifest contains no digital signature"

        canonical_bytes = manifest.canonical_manifest_bytes()
        computed_digest = hashlib.sha256(canonical_bytes).hexdigest()
        if computed_digest != manifest.cryptographic_digest:
            return False, f"DIGEST_MISMATCH: Computed digest '{computed_digest}' != stored '{manifest.cryptographic_digest}'"

        try:
            sig_bytes = base64.b64decode(manifest.signature_b64)
            pub_bytes = expected_signer_public_key_bytes or base64.b64decode(manifest.signer_public_key_b64)
            
            is_valid = MLDSA65.verify(pub_bytes, canonical_bytes, sig_bytes)
            if not is_valid:
                return False, "SIGNATURE_VERIFICATION_FAILED: Cryptographic signature mismatch"
            return True, None
        except Exception as ex:
            return False, f"VERIFICATION_EXCEPTION: {str(ex)}"
