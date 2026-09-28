"""
AegisTrace Key Lifecycle Adapters.

Subsystem-specific bridges integrating key lifecycle management, epoch progression,
and identity continuity across:
- Recipient ML-DSA-65 and ML-KEM-768 keys
- Hardware Attested Device keys
- Traceability / Tardos secret epochs
- Dynamic Watermark carrier key epochs
- Permissioned DLT Validator keys
- Active Controlled Viewer Session policies
"""

import base64
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional, Tuple, List

from core.crypto.models import KeyPair
from core.crypto.kem import MLKEM768
from core.crypto.signatures import MLDSA65
from core.crypto.lifecycle.models import (
    KeyRecord,
    KeyState,
    KeyType,
    KeyCustodyClass,
    KeyRecoveryClassification,
)
from core.crypto.lifecycle.manager import KeyLifecycleManager, default_key_lifecycle_manager
from core.crypto.lifecycle.resolver import HistoricalKeyResolver, default_historical_resolver


# ==============================================================================
# 1. Recipient Key Lifecycle Adapter
# ==============================================================================

class RecipientKeyLifecycleAdapter:
    """
    Manages ML-DSA-65 and ML-KEM-768 key lifecycles for recipient principals.
    Guarantees cryptographic identity continuity (recipient_id remains constant).
    """
    def __init__(
        self,
        manager: Optional[KeyLifecycleManager] = None,
        resolver: Optional[HistoricalKeyResolver] = None
    ):
        self.manager = manager or default_key_lifecycle_manager
        self.resolver = resolver or default_historical_resolver

    def enroll_recipient_keys(
        self,
        recipient_id: str,
        dsa_keypair: Optional[KeyPair] = None,
        kem_keypair: Optional[KeyPair] = None,
        tenant_id: str = "default_tenant"
    ) -> Tuple[KeyRecord, KeyRecord]:
        """Enrolls initial ML-DSA and ML-KEM keys for a recipient at epoch 1."""
        dsa_kp = dsa_keypair or MLDSA65.generate_keypair()
        kem_kp = kem_keypair or MLKEM768.generate_keypair()

        dsa_pub_b64 = base64.b64encode(dsa_kp.public_key_bytes).decode("utf-8")
        kem_pub_b64 = base64.b64encode(kem_kp.public_key_bytes).decode("utf-8")

        dsa_rec = self.manager.register_key(
            owner=recipient_id,
            key_type=KeyType.RECIPIENT_PRIVATE_KEY,
            algorithm="ML-DSA-65",
            purpose="Provenance Decryption Signing & Non-Repudiation",
            tenant_id=tenant_id,
            epoch=1,
            custody_class=KeyCustodyClass.LOCAL_PROTECTED_STORE,
            recovery_class=KeyRecoveryClassification.RECOVERABLE,
            public_material_b64=dsa_pub_b64,
            activate_immediately=True,
            metadata={"key_use": "SIGNATURE", "raw_keypair": dsa_kp}
        )

        kem_rec = self.manager.register_key(
            owner=recipient_id,
            key_type=KeyType.RECIPIENT_PRIVATE_KEY,
            algorithm="ML-KEM-768",
            purpose="In-Memory Document Release Decapsulation",
            tenant_id=tenant_id,
            epoch=1,
            custody_class=KeyCustodyClass.LOCAL_PROTECTED_STORE,
            recovery_class=KeyRecoveryClassification.RECOVERABLE,
            public_material_b64=kem_pub_b64,
            activate_immediately=True,
            metadata={"key_use": "ENCAPSULATION", "raw_keypair": kem_kp}
        )

        return dsa_rec, kem_rec

    def rotate_signing_key(
        self,
        recipient_id: str,
        tenant_id: str = "default_tenant",
        reason: str = "Scheduled recipient signing key rotation"
    ) -> Tuple[KeyRecord, KeyRecord, KeyPair]:
        """
        Rotates recipient ML-DSA-65 key: K1 -> K2.
        Returns: (predecessor_record, successor_record, new_keypair)
        """
        new_kp = MLDSA65.generate_keypair()
        new_pub_b64 = base64.b64encode(new_kp.public_key_bytes).decode("utf-8")

        prev_rec, next_rec = self.manager.rotate_key(
            owner=recipient_id,
            key_type=KeyType.RECIPIENT_PRIVATE_KEY,
            algorithm="ML-DSA-65",
            new_algorithm="ML-DSA-65",
            new_purpose="Provenance Decryption Signing & Non-Repudiation",
            new_public_material_b64=new_pub_b64,
            tenant_id=tenant_id,
            reason=reason
        )
        next_rec.metadata["raw_keypair"] = new_kp
        return prev_rec, next_rec, new_kp

    def rotate_kem_key(
        self,
        recipient_id: str,
        tenant_id: str = "default_tenant",
        reason: str = "Scheduled recipient KEM key rotation"
    ) -> Tuple[KeyRecord, KeyRecord, KeyPair]:
        """
        Rotates recipient ML-KEM-768 key: K1 -> K2.
        Returns: (predecessor_record, successor_record, new_keypair)
        """
        new_kp = MLKEM768.generate_keypair()
        new_pub_b64 = base64.b64encode(new_kp.public_key_bytes).decode("utf-8")

        prev_rec, next_rec = self.manager.rotate_key(
            owner=recipient_id,
            key_type=KeyType.RECIPIENT_PRIVATE_KEY,
            algorithm="ML-KEM-768",
            new_algorithm="ML-KEM-768",
            new_purpose="In-Memory Document Release Decapsulation",
            new_public_material_b64=new_pub_b64,
            tenant_id=tenant_id,
            reason=reason
        )
        next_rec.metadata["raw_keypair"] = new_kp
        return prev_rec, next_rec, new_kp


# ==============================================================================
# 2. Device Key Lifecycle Adapter
# ==============================================================================

class DeviceKeyLifecycleAdapter:
    """
    Manages Device Attestation Keys.
    Enforces hardware-bound custody and prevents cross-epoch session replays.
    """
    def __init__(self, manager: Optional[KeyLifecycleManager] = None):
        self.manager = manager or default_key_lifecycle_manager

    @staticmethod
    def _to_pub_b64(pub_material: Any) -> str:
        if isinstance(pub_material, bytes):
            return base64.b64encode(pub_material).decode("utf-8")
        if isinstance(pub_material, str):
            try:
                base64.b64decode(pub_material, validate=True)
                return pub_material
            except Exception:
                return base64.b64encode(pub_material.encode("utf-8")).decode("utf-8")
        return str(pub_material)

    def enroll_device(
        self,
        device_id: str,
        public_key_pem: str,
        algorithm: str = "P-256",
        is_hardware_backed: bool = True,
        tenant_id: str = "default_tenant"
    ) -> KeyRecord:
        custody = KeyCustodyClass.HARDWARE_BACKED if is_hardware_backed else KeyCustodyClass.LOCAL_PROTECTED_STORE
        recovery = KeyRecoveryClassification.HARDWARE_BOUND if is_hardware_backed else KeyRecoveryClassification.RECOVERABLE
        pub_b64 = self._to_pub_b64(public_key_pem)

        return self.manager.register_key(
            owner=device_id,
            key_type=KeyType.DEVICE_PUBLIC_KEY,
            algorithm=algorithm,
            purpose="Hardware Attestation & Platform Trust",
            tenant_id=tenant_id,
            epoch=1,
            custody_class=custody,
            recovery_class=recovery,
            public_material_b64=pub_b64,
            activate_immediately=True
        )

    def rotate_device_key(
        self,
        device_id: str,
        new_public_key_pem: str,
        algorithm: str = "P-256",
        is_hardware_backed: bool = True,
        tenant_id: str = "default_tenant",
        reason: str = "Hardware security key re-enrollment"
    ) -> Tuple[KeyRecord, KeyRecord]:
        new_pub_b64 = self._to_pub_b64(new_public_key_pem)
        custody = KeyCustodyClass.HARDWARE_BACKED if is_hardware_backed else KeyCustodyClass.LOCAL_PROTECTED_STORE

        return self.manager.rotate_key(
            owner=device_id,
            key_type=KeyType.DEVICE_PUBLIC_KEY,
            algorithm=algorithm,
            new_algorithm=algorithm,
            new_public_material_b64=new_pub_b64,
            tenant_id=tenant_id,
            custody_class=custody,
            reason=reason
        )


# ==============================================================================
# 3. Traceability / Tardos Epoch Adapter
# ==============================================================================

class TraceabilityEpochAdapter:
    """
    Integrates key epoch lifecycle with the multi-epoch TraceabilityKeystore.
    """
    def __init__(self, manager: Optional[KeyLifecycleManager] = None):
        self.manager = manager or default_key_lifecycle_manager

    def register_traceability_epoch(
        self,
        epoch: int,
        secret_bytes: bytes,
        tenant_id: str = "default_tenant",
        activate: bool = True
    ) -> KeyRecord:
        import hashlib
        key_digest = hashlib.sha256(secret_bytes).hexdigest()

        rec = self.manager.register_key(
            owner="SYSTEM_TRACEABILITY",
            key_type=KeyType.TRACEABILITY_SECRET,
            algorithm="HMAC-SHA256",
            purpose=f"Tardos Codeword Generation Epoch {epoch}",
            tenant_id=tenant_id,
            epoch=epoch,
            custody_class=KeyCustodyClass.SECURE_KEYSTORE,
            recovery_class=KeyRecoveryClassification.RECOVERABLE,
            public_material_b64=base64.b64encode(key_digest.encode("utf-8")).decode("utf-8"),
            activate_immediately=activate,
            metadata={"secret_bytes": secret_bytes}
        )
        return rec


# ==============================================================================
# 4. Watermark Key Epoch Adapter
# ==============================================================================

class WatermarkEpochAdapter:
    """
    Manages active and historical key epochs for dynamic watermarking.
    Ensures watermark generated under epoch N is verifiable under epoch N forever.
    """
    def __init__(self, manager: Optional[KeyLifecycleManager] = None):
        self.manager = manager or default_key_lifecycle_manager

    def register_watermark_epoch(
        self,
        epoch: int,
        epoch_secret: bytes,
        tenant_id: str = "default_tenant",
        activate: bool = True
    ) -> KeyRecord:
        import hashlib
        secret_hash = hashlib.sha256(epoch_secret).hexdigest()

        return self.manager.register_key(
            owner="SYSTEM_WATERMARK",
            key_type=KeyType.WATERMARK_SECRET,
            algorithm="HMAC-SHA256",
            purpose=f"Dynamic Watermark Carrier Modulation Epoch {epoch}",
            tenant_id=tenant_id,
            epoch=epoch,
            custody_class=KeyCustodyClass.SECURE_KEYSTORE,
            recovery_class=KeyRecoveryClassification.RECOVERABLE,
            public_material_b64=base64.b64encode(secret_hash.encode("utf-8")).decode("utf-8"),
            activate_immediately=activate,
            metadata={"epoch_secret": epoch_secret}
        )

    def get_epoch_secret(self, epoch: int, tenant_id: str = "default_tenant") -> Optional[bytes]:
        keys = self.manager.get_keys_for_owner("SYSTEM_WATERMARK", KeyType.WATERMARK_SECRET, tenant_id=tenant_id)
        for k in keys:
            if k.creation_epoch == epoch:
                return k.metadata.get("epoch_secret")
        return None


# ==============================================================================
# 5. DLT Validator Key Lifecycle Adapter
# ==============================================================================

class ValidatorKeyLifecycleAdapter:
    """
    Manages Validator keys participating in permissioned DLT consensus.
    Guarantees historical block verifiability and enforces active quorum membership.
    """
    def __init__(self, manager: Optional[KeyLifecycleManager] = None):
        self.manager = manager or default_key_lifecycle_manager

    def enroll_validator(
        self,
        validator_id: str,
        public_key_b64: str,
        tenant_id: str = "default_tenant"
    ) -> KeyRecord:
        return self.manager.register_key(
            owner=validator_id,
            key_type=KeyType.LEDGER_VALIDATOR_KEY,
            algorithm="ML-DSA-65",
            purpose="Permissioned DLT Consensus Voting & Block Endorsement",
            tenant_id=tenant_id,
            epoch=1,
            custody_class=KeyCustodyClass.SECURE_KEYSTORE,
            recovery_class=KeyRecoveryClassification.RECOVERABLE,
            public_material_b64=public_key_b64,
            activate_immediately=True
        )

    def rotate_validator_key(
        self,
        validator_id: str,
        new_public_key_b64: str,
        tenant_id: str = "default_tenant",
        reason: str = "Validator operational key rotation"
    ) -> Tuple[KeyRecord, KeyRecord]:
        return self.manager.rotate_key(
            owner=validator_id,
            key_type=KeyType.LEDGER_VALIDATOR_KEY,
            new_algorithm="ML-DSA-65",
            new_public_material_b64=new_public_key_b64,
            tenant_id=tenant_id,
            reason=reason
        )

    def is_validator_active(self, validator_id: str, tenant_id: str = "default_tenant") -> bool:
        rec = self.manager.get_active_key(validator_id, KeyType.LEDGER_VALIDATOR_KEY, tenant_id=tenant_id)
        return rec is not None and rec.status == KeyState.ACTIVE


# ==============================================================================
# 6. Active Session Lifecycle Policy
# ==============================================================================

class SessionRotationPolicy(str, Enum):
    SESSION_CONTINUES_UNTIL_EXPIRY = "SESSION_CONTINUES_UNTIL_EXPIRY"
    SESSION_REQUIRES_REAUTH_ON_ROTATION = "SESSION_REQUIRES_REAUTH_ON_ROTATION"


class SessionLifecycleCoordinator:
    """
    Coordinates viewer session behavior during key rotation.
    Default policy: active sessions remain valid in-memory until natural expiration,
    but subsequent exports or releases must bind to active successor keys.
    """
    def __init__(self, policy: SessionRotationPolicy = SessionRotationPolicy.SESSION_CONTINUES_UNTIL_EXPIRY):
        self.policy = policy

    def evaluate_session_validity(
        self,
        session_created_at: str,
        session_expires_at: str,
        key_rotation_time: Optional[str] = None
    ) -> bool:
        now_dt = datetime.now(timezone.utc)
        exp_dt = datetime.fromisoformat(session_expires_at.replace("Z", "+00:00"))

        if now_dt >= exp_dt:
            return False  # Natural expiration

        if self.policy == SessionRotationPolicy.SESSION_REQUIRES_REAUTH_ON_ROTATION and key_rotation_time:
            rot_dt = datetime.fromisoformat(key_rotation_time.replace("Z", "+00:00"))
            sess_dt = datetime.fromisoformat(session_created_at.replace("Z", "+00:00"))
            if rot_dt > sess_dt:
                return False  # Terminated due to rotation

        return True
