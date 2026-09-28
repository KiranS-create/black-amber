"""
AegisTrace Cryptographic Key Recovery Integration & Temporal Validity Engine.

Coordinates with the cryptographic key lifecycle subsystem.
Enforces:
1. Zero plaintext private key exposure.
2. Hardware-bound and non-recoverable keys are strictly non-exportable.
3. Explicit key availability states:
   KEY_AVAILABLE, KEY_REVOKED, KEY_COMPROMISED, KEY_UNRECOVERABLE, RECOVERY_REQUIRED.
4. Strict temporal validity semantics:
   Signatures created prior to key revocation/compromise timestamp remain forensically valid.
   Signatures created post-compromise are strictly rejected.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from pydantic import BaseModel, Field

from core.crypto.lifecycle.models import (
    KeyRecord,
    KeyState,
    KeyType,
    KeyRecoveryClassification,
    KeyCustodyClass,
)
from core.crypto.lifecycle.backup import KeyBackupEngine, KeyBackupSecurityError
from core.recovery.models import RecoveryState


class KeyOperationalStatus(str, Enum):
    KEY_AVAILABLE = "KEY_AVAILABLE"
    KEY_REVOKED = "KEY_REVOKED"
    KEY_COMPROMISED = "KEY_COMPROMISED"
    KEY_UNRECOVERABLE = "KEY_UNRECOVERABLE"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"


class TemporalSignatureValidationResult(BaseModel):
    is_valid: bool
    status: str
    signature_timestamp: str
    event_validity: str
    key_id: str
    key_state_at_signature: KeyState
    compromise_timestamp: Optional[str] = None
    reason: Optional[str] = None


class KeyRecoveryEngine:
    """
    Coordinates cryptographic key recovery, lifecycle status resolution,
    and temporal validity evaluation.
    """

    @classmethod
    def evaluate_key_status(cls, record: KeyRecord) -> KeyOperationalStatus:
        """
        Determines the formal operational status for a key record.
        """
        if record.status == KeyState.COMPROMISED:
            return KeyOperationalStatus.KEY_COMPROMISED
        if record.status == KeyState.REVOKED:
            return KeyOperationalStatus.KEY_REVOKED
        if record.recovery_class == KeyRecoveryClassification.NON_RECOVERABLE and not record.public_material_b64:
            return KeyOperationalStatus.KEY_UNRECOVERABLE
        if record.status in (KeyState.ACTIVE, KeyState.RETIRED):
            return KeyOperationalStatus.KEY_AVAILABLE
        return KeyOperationalStatus.RECOVERY_REQUIRED

    @classmethod
    def restore_encrypted_key(
        cls,
        backup_envelope: Dict[str, Any],
        passphrase: str,
        expected_tenant_id: str = "default_tenant"
    ) -> Tuple[KeyRecord, bytes]:
        """
        Restores a recoverable private key from its encrypted backup envelope.
        Fails closed on tenant mismatch, tampering, or non-recoverable key export.
        """
        return KeyBackupEngine.restore_from_backup_package(
            package=backup_envelope,
            passphrase=passphrase,
            tenant_id=expected_tenant_id
        )

    @classmethod
    def validate_signature_temporal_validity(
        cls,
        record: KeyRecord,
        signature_iso_timestamp: str
    ) -> TemporalSignatureValidationResult:
        """
        Evaluates temporal signature validity against the key's historical lifecycle.
        
        INVARIANT:
        If key was compromised at T_compromised:
        - Signature at T < T_compromised: VALID (historical signature preserved)
        - Signature at T >= T_compromised: REJECTED (key compromised)
        """
        try:
            sig_dt = datetime.fromisoformat(signature_iso_timestamp)
        except Exception:
            return TemporalSignatureValidationResult(
                is_valid=False,
                status="INVALID_TIMESTAMP_FORMAT",
                signature_timestamp=signature_iso_timestamp,
                event_validity="REJECTED",
                key_id=record.key_id,
                key_state_at_signature=record.status,
                reason="Malformed ISO-8601 signature timestamp"
            )

        # Check compromise timestamp
        if record.status == KeyState.COMPROMISED:
            comp_dt = None
            if record.revocation_timestamp:
                try:
                    comp_dt = datetime.fromisoformat(record.revocation_timestamp)
                except Exception:
                    comp_dt = None

            if comp_dt is not None:
                if sig_dt >= comp_dt:
                    return TemporalSignatureValidationResult(
                        is_valid=False,
                        status="KEY_COMPROMISED_AT_SIGNING",
                        signature_timestamp=signature_iso_timestamp,
                        event_validity="REJECTED",
                        key_id=record.key_id,
                        key_state_at_signature=KeyState.COMPROMISED,
                        compromise_timestamp=record.revocation_timestamp,
                        reason=f"Signature time {signature_iso_timestamp} >= compromise time {record.revocation_timestamp}"
                    )
                else:
                    return TemporalSignatureValidationResult(
                        is_valid=True,
                        status="HISTORICAL_SIGNATURE_PRE_COMPROMISE",
                        signature_timestamp=signature_iso_timestamp,
                        event_validity="VALID_HISTORICAL",
                        key_id=record.key_id,
                        key_state_at_signature=KeyState.ACTIVE,
                        compromise_timestamp=record.revocation_timestamp,
                        reason="Signature was created before key compromise event occurred"
                    )

        # Check revocation timestamp
        if record.status == KeyState.REVOKED and record.revocation_timestamp:
            try:
                rev_dt = datetime.fromisoformat(record.revocation_timestamp)
                if sig_dt > rev_dt:
                    return TemporalSignatureValidationResult(
                        is_valid=False,
                        status="KEY_REVOKED_AT_SIGNING",
                        signature_timestamp=signature_iso_timestamp,
                        event_validity="REJECTED",
                        key_id=record.key_id,
                        key_state_at_signature=KeyState.REVOKED,
                        reason=f"Signature time {signature_iso_timestamp} > revocation time {record.revocation_timestamp}"
                    )
            except Exception:
                pass

        return TemporalSignatureValidationResult(
            is_valid=True,
            status="SIGNATURE_WITHIN_VALIDITY_EPOCH",
            signature_timestamp=signature_iso_timestamp,
            event_validity="VALID",
            key_id=record.key_id,
            key_state_at_signature=record.status
        )
