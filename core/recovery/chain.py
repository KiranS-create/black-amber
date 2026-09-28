"""
AegisTrace Incremental Backup Chain Engine.

Manages cryptographically bound backup chains:
FULL BACKUP (Sequence 0)
  ↓
DELTA 1 (Sequence 1, Parent = FULL)
  ↓
DELTA 2 (Sequence 2, Parent = DELTA 1)
  ...

Enforces strict sequence continuity, parent cryptographic digest binding,
tenant isolation, and fail-closed detection of tampering, reordering, or rollback.
"""

from enum import Enum
from typing import List, Dict, Optional, Tuple, Set, Any
from pydantic import BaseModel, Field

from core.recovery.models import (
    SignedBackupManifest,
    BackupType,
    RecoveryState,
)
from core.recovery.crypto import BackupCryptoEngine


class ChainValidationStatus(str, Enum):
    VALID = "VALID"
    MISSING_DELTA = "MISSING_DELTA"
    REORDERED_DELTA = "REORDERED_DELTA"
    DUPLICATE_DELTA = "DUPLICATE_DELTA"
    ALTERED_DELTA = "ALTERED_DELTA"
    WRONG_PARENT = "WRONG_PARENT"
    ROLLBACK_DETECTED = "ROLLBACK_DETECTED"
    CROSS_TENANT_SUBSTITUTION = "CROSS_TENANT_SUBSTITUTION"
    INVALID_GENESIS = "INVALID_GENESIS"


class ChainValidationResult(BaseModel):
    is_valid: bool
    status: ChainValidationStatus
    verified_sequence_count: int
    last_verified_sequence: int
    tip_backup_id: Optional[str] = None
    tip_commitment: Optional[str] = None
    error_message: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class BackupChainManager:
    """
    Validates, constructs, and manages incremental forensic backup chains.
    Enforces that every link in the chain is cryptographically verifiable,
    strictly sequential, and untampered from the initial Full backup.
    """

    @classmethod
    def validate_chain(
        cls,
        manifests: List[SignedBackupManifest],
        expected_tenant_id: Optional[str] = None,
        authority_public_key_bytes: Optional[bytes] = None
    ) -> ChainValidationResult:
        """
        Validates an entire backup chain from Full (seq 0) to latest Delta.
        Fails closed on any anomaly.
        """
        if not manifests:
            return ChainValidationResult(
                is_valid=False,
                status=ChainValidationStatus.INVALID_GENESIS,
                verified_sequence_count=0,
                last_verified_sequence=-1,
                error_message="EMPTY_CHAIN: No backup manifests provided"
            )

        # 1. Verify Genesis Backup (Must be FULL, Sequence 0, Parent None)
        genesis = manifests[0]
        if genesis.backup_type != BackupType.FULL or genesis.backup_sequence != 0:
            return ChainValidationResult(
                is_valid=False,
                status=ChainValidationStatus.INVALID_GENESIS,
                verified_sequence_count=0,
                last_verified_sequence=-1,
                error_message=f"INVALID_GENESIS: First backup must be FULL with sequence 0, got {genesis.backup_type.value} seq {genesis.backup_sequence}"
            )
        if genesis.parent_backup_id is not None or genesis.parent_backup_commitment is not None:
            return ChainValidationResult(
                is_valid=False,
                status=ChainValidationStatus.INVALID_GENESIS,
                verified_sequence_count=0,
                last_verified_sequence=-1,
                error_message="INVALID_GENESIS: Genesis backup must have no parent references"
            )

        tenant = expected_tenant_id or genesis.tenant_id
        if genesis.tenant_id != tenant:
            return ChainValidationResult(
                is_valid=False,
                status=ChainValidationStatus.CROSS_TENANT_SUBSTITUTION,
                verified_sequence_count=0,
                last_verified_sequence=-1,
                error_message=f"CROSS_TENANT: Genesis backup tenant '{genesis.tenant_id}' != expected '{tenant}'"
            )

        # Verify Genesis Signature
        is_valid_sig, sig_err = BackupCryptoEngine.verify_manifest(genesis, authority_public_key_bytes)
        if not is_valid_sig:
            return ChainValidationResult(
                is_valid=False,
                status=ChainValidationStatus.ALTERED_DELTA,
                verified_sequence_count=0,
                last_verified_sequence=-1,
                error_message=f"GENESIS_SIGNATURE_INVALID: {sig_err}"
            )

        seen_backup_ids: Set[str] = {genesis.backup_id}
        seen_sequences: Set[int] = {0}
        prev_manifest = genesis

        # 2. Iterate through deltas sequentially
        for idx in range(1, len(manifests)):
            current = manifests[idx]

            # Check tenant isolation
            if current.tenant_id != tenant:
                return ChainValidationResult(
                    is_valid=False,
                    status=ChainValidationStatus.CROSS_TENANT_SUBSTITUTION,
                    verified_sequence_count=idx,
                    last_verified_sequence=prev_manifest.backup_sequence,
                    tip_backup_id=prev_manifest.backup_id,
                    tip_commitment=prev_manifest.cryptographic_digest,
                    error_message=f"CROSS_TENANT: Manifest at index {idx} has tenant '{current.tenant_id}' != expected '{tenant}'"
                )

            # Check duplicate backup ID
            if current.backup_id in seen_backup_ids:
                return ChainValidationResult(
                    is_valid=False,
                    status=ChainValidationStatus.DUPLICATE_DELTA,
                    verified_sequence_count=idx,
                    last_verified_sequence=prev_manifest.backup_sequence,
                    tip_backup_id=prev_manifest.backup_id,
                    tip_commitment=prev_manifest.cryptographic_digest,
                    error_message=f"DUPLICATE_BACKUP_ID: Backup '{current.backup_id}' already seen in chain"
                )
            seen_backup_ids.add(current.backup_id)

            # Check duplicate sequence
            if current.backup_sequence in seen_sequences:
                return ChainValidationResult(
                    is_valid=False,
                    status=ChainValidationStatus.DUPLICATE_DELTA,
                    verified_sequence_count=idx,
                    last_verified_sequence=prev_manifest.backup_sequence,
                    tip_backup_id=prev_manifest.backup_id,
                    tip_commitment=prev_manifest.cryptographic_digest,
                    error_message=f"DUPLICATE_SEQUENCE: Backup sequence {current.backup_sequence} already seen"
                )

            # Check strictly sequential ordering
            expected_seq = prev_manifest.backup_sequence + 1
            if current.backup_sequence < expected_seq:
                return ChainValidationResult(
                    is_valid=False,
                    status=ChainValidationStatus.ROLLBACK_DETECTED,
                    verified_sequence_count=idx,
                    last_verified_sequence=prev_manifest.backup_sequence,
                    tip_backup_id=prev_manifest.backup_id,
                    tip_commitment=prev_manifest.cryptographic_digest,
                    error_message=f"ROLLBACK_DETECTED: Sequence moved backwards from {prev_manifest.backup_sequence} to {current.backup_sequence}"
                )
            if current.backup_sequence > expected_seq:
                return ChainValidationResult(
                    is_valid=False,
                    status=ChainValidationStatus.MISSING_DELTA,
                    verified_sequence_count=idx,
                    last_verified_sequence=prev_manifest.backup_sequence,
                    tip_backup_id=prev_manifest.backup_id,
                    tip_commitment=prev_manifest.cryptographic_digest,
                    error_message=f"MISSING_DELTA: Gap in sequence numbers. Expected {expected_seq}, got {current.backup_sequence}"
                )
            seen_sequences.add(current.backup_sequence)

            # Check parent cryptographic linkage
            if current.parent_backup_id != prev_manifest.backup_id:
                return ChainValidationResult(
                    is_valid=False,
                    status=ChainValidationStatus.WRONG_PARENT,
                    verified_sequence_count=idx,
                    last_verified_sequence=prev_manifest.backup_sequence,
                    tip_backup_id=prev_manifest.backup_id,
                    tip_commitment=prev_manifest.cryptographic_digest,
                    error_message=f"WRONG_PARENT: Delta seq {current.backup_sequence} parent ID '{current.parent_backup_id}' != expected '{prev_manifest.backup_id}'"
                )

            if current.parent_backup_commitment != prev_manifest.cryptographic_digest:
                return ChainValidationResult(
                    is_valid=False,
                    status=ChainValidationStatus.WRONG_PARENT,
                    verified_sequence_count=idx,
                    last_verified_sequence=prev_manifest.backup_sequence,
                    tip_backup_id=prev_manifest.backup_id,
                    tip_commitment=prev_manifest.cryptographic_digest,
                    error_message=f"ALTERED_PARENT_COMMITMENT: Delta seq {current.backup_sequence} parent commitment '{current.parent_backup_commitment}' != actual '{prev_manifest.cryptographic_digest}'"
                )

            # Verify Delta Post-Quantum Signature & Digest
            is_valid_sig, sig_err = BackupCryptoEngine.verify_manifest(current, authority_public_key_bytes)
            if not is_valid_sig:
                return ChainValidationResult(
                    is_valid=False,
                    status=ChainValidationStatus.ALTERED_DELTA,
                    verified_sequence_count=idx,
                    last_verified_sequence=prev_manifest.backup_sequence,
                    tip_backup_id=prev_manifest.backup_id,
                    tip_commitment=prev_manifest.cryptographic_digest,
                    error_message=f"ALTERED_DELTA: Signature verification failed on seq {current.backup_sequence}: {sig_err}"
                )

            prev_manifest = current

        return ChainValidationResult(
            is_valid=True,
            status=ChainValidationStatus.VALID,
            verified_sequence_count=len(manifests),
            last_verified_sequence=prev_manifest.backup_sequence,
            tip_backup_id=prev_manifest.backup_id,
            tip_commitment=prev_manifest.cryptographic_digest,
            error_message=None,
            details={
                "chain_length": len(manifests),
                "genesis_id": genesis.backup_id,
                "tip_id": prev_manifest.backup_id,
                "tenant_id": tenant,
            }
        )
