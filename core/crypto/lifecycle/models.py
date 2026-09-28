"""
AegisTrace Cryptographic Key Lifecycle Models.

Defines the formal key lifecycle states, classifications, custody assurance tiers,
recovery categories, and metadata schemas for all security-relevant keys in AegisTrace.
"""

from datetime import datetime, timezone
from enum import Enum
import hashlib
import os
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class KeyState(str, Enum):
    """
    Formal 9-state lifecycle model for cryptographic keys and secrets.
    """
    GENERATED = "GENERATED"                    # Freshly generated, not yet enrolled
    PENDING_ACTIVATION = "PENDING_ACTIVATION"  # Enrolled, awaiting epoch boundary or verification
    ACTIVE = "ACTIVE"                          # Authorized for new signing, encryption, consensus
    SUSPENDED = "SUSPENDED"                    # Temporarily halted; new operations forbidden
    ROTATING = "ROTATING"                      # Preparing successor key before atomic cutover
    REVOKED = "REVOKED"                        # Permanently invalidated for new operations at T_revocation
    RETIRED = "RETIRED"                        # Decommissioned after orderly rotation and retention period
    COMPROMISED = "COMPROMISED"                # Revoked due to confirmed/suspected key exposure
    UNKNOWN = "UNKNOWN"                        # Unregistered key identity presenting claims


class KeyType(str, Enum):
    """Classification of keys and secrets across AegisTrace subsystems."""
    RECIPIENT_PRIVATE_KEY = "RECIPIENT_PRIVATE_KEY"
    RECIPIENT_PUBLIC_KEY = "RECIPIENT_PUBLIC_KEY"
    DEVICE_PRIVATE_KEY = "DEVICE_PRIVATE_KEY"
    DEVICE_PUBLIC_KEY = "DEVICE_PUBLIC_KEY"
    TRACEABILITY_SECRET = "TRACEABILITY_SECRET"
    WATERMARK_SECRET = "WATERMARK_SECRET"
    LEDGER_VALIDATOR_KEY = "LEDGER_VALIDATOR_KEY"
    TELEMETRY_AUTHENTICATION_KEY = "TELEMETRY_AUTHENTICATION_KEY"
    BACKUP_ENCRYPTION_KEY = "BACKUP_ENCRYPTION_KEY"
    MASTER_EPHEMERAL_KEY = "MASTER_EPHEMERAL_KEY"
    OTHER = "OTHER"


class KeyCustodyClass(str, Enum):
    """Custody assurance tiers for private keys and master secrets."""
    HARDWARE_BACKED = "HARDWARE_BACKED"             # Discrete crypto chip (TPM 2.0, Secure Enclave, YubiKey)
    SECURE_KEYSTORE = "SECURE_KEYSTORE"             # OS/Enclave-protected keystore with access control
    EXTERNAL_SECRET_STORE = "EXTERNAL_SECRET_STORE" # Local air-gapped secret vault/vault daemon
    LOCAL_PROTECTED_STORE = "LOCAL_PROTECTED_STORE" # Air-gapped in-memory/encrypted local file
    DEVELOPMENT_ONLY = "DEVELOPMENT_ONLY"           # Development/ephemeral fallback (BANNED in production)


class KeyRecoveryClassification(str, Enum):
    """Recovery and exportability classification."""
    RECOVERABLE = "RECOVERABLE"                     # Software keys permitted for air-gapped encrypted backup
    NON_RECOVERABLE = "NON_RECOVERABLE"             # Ephemeral or one-time keys that must never be exported
    HARDWARE_BOUND = "HARDWARE_BOUND"               # Keys non-exportably locked in TPM/Secure Enclave hardware


def generate_key_id(owner: str, key_type: KeyType, epoch: int, entropy: Optional[bytes] = None) -> str:
    """
    Generates an opaque, collision-resistant, non-secret key identifier.
    Format: kid_<sha256_prefix>
    INVARIANT: Does not include raw secrets, emails, hostnames, or MAC addresses.
    """
    seed = entropy or os.urandom(16)
    digest = hashlib.sha256(
        f"AEGIS-KEY-ID:v1:{owner}:{key_type.value}:{epoch}:".encode("utf-8") + seed
    ).hexdigest()[:24]
    return f"kid_{digest}"


class KeyRecord(BaseModel):
    """
    Complete cryptographic key metadata record.
    Preserves historical lineage, custody class, timestamps, and recovery status.
    """
    key_id: str = Field(..., description="Opaque unique key identifier (kid_<hash>)")
    key_type: KeyType = Field(..., description="Key classification")
    algorithm: str = Field(..., description="Cryptographic algorithm (ML-DSA-65, ML-KEM-768, AES-256-GCM, etc.)")
    purpose: str = Field(..., description="Human/operational purpose description")
    owner: str = Field(..., description="Principal owner identifier (e.g. rec_alice, dev_9c2a, val_node1)")
    tenant_id: str = Field("default_tenant", description="Multi-tenant isolation identifier")
    creation_epoch: int = Field(1, description="Key epoch number (monotonic)")
    status: KeyState = Field(KeyState.GENERATED, description="Current lifecycle state")
    
    # Timestamps (ISO 8601 UTC)
    creation_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    activation_timestamp: Optional[str] = None
    rotation_timestamp: Optional[str] = None
    revocation_timestamp: Optional[str] = None
    
    # Lineage links
    predecessor_key_id: Optional[str] = None
    successor_key_id: Optional[str] = None
    
    # Custody & Recovery
    storage_class: KeyCustodyClass = Field(KeyCustodyClass.LOCAL_PROTECTED_STORE)
    recovery_class: KeyRecoveryClassification = Field(KeyRecoveryClassification.RECOVERABLE)
    verification_dependencies: List[str] = Field(default_factory=list)
    
    # Non-secret public verification material (base64 or hex)
    public_material_b64: Optional[str] = None
    
    # Encrypted private material (ONLY present if recoverable and encrypted under backup envelope)
    encrypted_private_material_b64: Optional[str] = None
    
    # Compromise annotations
    compromise_details: Optional[str] = None
    
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_public_metadata(self) -> Dict[str, Any]:
        """
        Returns a sanitized dictionary safe for audit logs, reports, and API responses.
        Guaranteed to contain zero private key bytes or secret material.
        """
        return {
            "key_id": self.key_id,
            "key_type": self.key_type.value,
            "algorithm": self.algorithm,
            "purpose": self.purpose,
            "owner": self.owner,
            "tenant_id": self.tenant_id,
            "creation_epoch": self.creation_epoch,
            "status": self.status.value,
            "creation_timestamp": self.creation_timestamp,
            "activation_timestamp": self.activation_timestamp,
            "rotation_timestamp": self.rotation_timestamp,
            "revocation_timestamp": self.revocation_timestamp,
            "predecessor_key_id": self.predecessor_key_id,
            "successor_key_id": self.successor_key_id,
            "storage_class": self.storage_class.value,
            "recovery_class": self.recovery_class.value,
            "public_material_b64": self.public_material_b64,
            "compromise_details": self.compromise_details,
        }
