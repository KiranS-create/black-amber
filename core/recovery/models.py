"""
AegisTrace Disaster Recovery & Forensic State Models.

Defines the formal data models, schemas, state enumerations, verification reports,
and audit records for the disaster recovery, state recovery, and incident response architecture.
"""

from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import os
from typing import Dict, List, Optional, Any, Set, Tuple
from pydantic import BaseModel, Field


# ==============================================================================
# 1. State Classifications & Operational Targets
# ==============================================================================

class ComponentStateClass(str, Enum):
    """Classification of state mutability and reconstructibility."""
    AUTHORITATIVE = "AUTHORITATIVE"          # Primary source of truth; loss is permanent without backup
    DERIVED = "DERIVED"                      # Computed deterministically from authoritative state
    REBUILDABLE = "REBUILDABLE"              # Secondary index or cache rebuildable from local/peer data


class CriticalityTier(str, Enum):
    """Criticality level for forensic defensibility and security integrity."""
    SECURITY_CRITICAL = "SECURITY_CRITICAL"  # System keys, validator state, tenant boundaries
    EVIDENCE_CRITICAL = "EVIDENCE_CRITICAL"  # Ledger events, lineage nodes, signatures, watermark tokens
    OPERATIONAL = "OPERATIONAL"              # Ephemeral caches, runtime telemetry buffers


class TargetClassification(str, Enum):
    """Epistemic status of an operational RPO/RTO metric."""
    DESIGN_TARGET = "DESIGN_TARGET"          # Formal architectural specification
    MEASURED = "MEASURED"                    # Empirically measured in automated benchmarks
    NOT_VERIFIED = "NOT_VERIFIED"            # Pending hardware or operational verification


class RecoveryRequirement(str, Enum):
    """Strictness of recovery reconstruction."""
    EXACT_CRYPTOGRAPHIC = "EXACT_CRYPTOGRAPHIC"      # Must match exact SHA-256 / Merkle root
    DEDUPLICATED_APPEND = "DEDUPLICATED_APPEND"      # Can merge idempotently without duplicate inflation
    RECONSTITUTED_INDEX = "RECONSTITUTED_INDEX"      # Rebuilt from authoritative records
    BFT_QUORUM = "BFT_QUORUM"                        # Re-verified against Byzantine validator quorum


# ==============================================================================
# 2. Recovery Status States & Invariants
# ==============================================================================

class RecoveryState(str, Enum):
    """
    Formal outcome states for a state recovery attempt.
    Fail-closed semantics: ABSTAIN on any ambiguity, corruption, or conflict.
    """
    VALID_RECOVERY = "VALID_RECOVERY"                # All cryptographic chains, hashes, and signatures verified
    PARTIAL_RECOVERY = "PARTIAL_RECOVERY"            # Clean prefix recovered, tail corrupted/truncated safely
    CORRUPTED_RECOVERY = "CORRUPTED_RECOVERY"        # Corrupted records detected; rejected
    ROLLBACK_DETECTED = "ROLLBACK_DETECTED"          # Monotonic counter violation (stale state)
    CONFLICTING_RECOVERY = "CONFLICTING_RECOVERY"    # Fork or competing state branches detected
    TENANT_MISMATCH = "TENANT_MISMATCH"              # Cross-tenant data substitution attempt
    UNRECOVERABLE = "UNRECOVERABLE"                  # Essential authoritative state missing or destroyed


class FinalRecoveryOutcome(str, Enum):
    """Executive status of a completed restoration run."""
    RECOVERED = "RECOVERED"
    PARTIALLY_RECOVERED = "PARTIALLY_RECOVERED"
    RECOVERY_REQUIRES_REVIEW = "RECOVERY_REQUIRES_REVIEW"
    RECOVERY_FAILED = "RECOVERY_FAILED"


# ==============================================================================
# 3. Incident Response States
# ==============================================================================

class IncidentState(str, Enum):
    """
    Formal 12-state incident response lifecycle for AegisTrace systems.
    """
    NORMAL = "NORMAL"                                # Baseline production operation
    SUSPECTED_COMPROMISE = "SUSPECTED_COMPROMISE"    # Anomaly detected, initial triage
    CONTAINMENT = "CONTAINMENT"                      # Tenant isolation, credential revocation
    FORENSIC_PRESERVATION = "FORENSIC_PRESERVATION"  # State frozen; mutation blocked; evidence preserved
    RECOVERY_VALIDATION = "RECOVERY_VALIDATION"      # Backup verification and staging restoration
    RESTORED = "RESTORED"                            # State reconstituted and cryptographically verified
    POST_INCIDENT_REVIEW = "POST_INCIDENT_REVIEW"    # Root cause analysis, policy update
    
    # Failure & Exception States
    RECOVERY_FAILED = "RECOVERY_FAILED"              # Backup verification or restore crashed/failed
    EVIDENCE_CONFLICT = "EVIDENCE_CONFLICT"          # Conflicting historical evidence observed
    KEY_COMPROMISED = "KEY_COMPROMISED"              # Master or operational key confirmed compromised
    ROLLBACK_DETECTED = "ROLLBACK_DETECTED"          # Attempted restoration of stale/older state
    REQUIRES_MANUAL_REVIEW = "REQUIRES_MANUAL_REVIEW"# Operator quorum or break-glass approval required


# ==============================================================================
# 4. Backup Object & Manifest Models
# ==============================================================================

class BackupType(str, Enum):
    FULL = "FULL"
    DELTA = "DELTA"


class BackupObjectRecord(BaseModel):
    """Metadata record for a content-addressed object stored in backup repository."""
    object_id: str = Field(..., description="SHA-256 hash of canonical object payload")
    dataset_type: str = Field(..., description="Target dataset (ledger, lineage, keys, etc.)")
    tenant_id: str = Field("default_tenant", description="Tenant isolation scope")
    byte_size: int = Field(..., description="Payload size in bytes")
    object_count: int = Field(1, description="Number of logical entities in this object")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SignedBackupManifest(BaseModel):
    """
    Cryptographically verifiable backup manifest binding datasets, hashes,
    Merkle roots, parent commitments, and post-quantum digital signature.
    """
    backup_id: str = Field(..., description="Unique backup identifier (e.g. bkp_9f8a2c1b)")
    backup_type: BackupType = Field(BackupType.FULL, description="FULL or DELTA")
    tenant_id: str = Field("default_tenant", description="Tenant isolation boundary")
    backup_sequence: int = Field(0, description="Monotonically increasing sequence number")
    creation_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source_system_id: str = Field("aegis_node_primary", description="Originating node/cluster identity")
    schema_version: str = Field("1.0", description="Forensic backup schema version")
    application_version: str = Field("2.0.0", description="AegisTrace engine version")
    
    # Cryptographic commitments
    parent_backup_id: Optional[str] = Field(None, description="Previous backup ID (None for FULL seq 0)")
    parent_backup_commitment: Optional[str] = Field(None, description="SHA-256 digest of parent signed manifest")
    
    # Datasets and object commitments
    datasets: List[str] = Field(default_factory=list, description="List of included dataset names")
    objects: List[BackupObjectRecord] = Field(default_factory=list, description="Content-addressed object inventory")
    merkle_root: str = Field(..., description="RFC-6962 Merkle root over object digests")
    cryptographic_digest: str = Field(..., description="SHA-256 digest over canonical manifest payload")
    
    # Authenticated Encryption (if encrypted backup)
    is_encrypted: bool = Field(False, description="True if payload objects are AES-256-GCM encrypted")
    encryption_algorithm: Optional[str] = Field(None, description="AES-256-GCM")
    key_derivation_algorithm: Optional[str] = Field(None, description="HKDF-SHA256")
    encryption_key_id: Optional[str] = Field(None, description="Opaque backup encryption key ID")
    
    # Post-Quantum Digital Signature (ML-DSA-65)
    signer_id: str = Field(..., description="Identity of signing authority or backup operator")
    signer_public_key_b64: str = Field(..., description="ML-DSA-65 public key in base64")
    signature_b64: str = Field(..., description="ML-DSA-65 signature over canonical manifest payload")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def canonical_manifest_bytes(self) -> bytes:
        """
        Deterministic canonical serialization for digital signature and digest computation.
        Omits signature_b64 and cryptographic_digest to prevent circular dependency.
        """
        data = {
            "backup_id": self.backup_id,
            "backup_type": self.backup_type.value,
            "tenant_id": self.tenant_id,
            "backup_sequence": self.backup_sequence,
            "creation_timestamp": self.creation_timestamp,
            "source_system_id": self.source_system_id,
            "schema_version": self.schema_version,
            "application_version": self.application_version,
            "parent_backup_id": self.parent_backup_id,
            "parent_backup_commitment": self.parent_backup_commitment,
            "datasets": sorted(self.datasets),
            "objects": [
                {
                    "object_id": o.object_id,
                    "dataset_type": o.dataset_type,
                    "tenant_id": o.tenant_id,
                    "byte_size": o.byte_size,
                    "object_count": o.object_count,
                    "created_at": o.created_at,
                }
                for o in sorted(self.objects, key=lambda x: x.object_id)
            ],
            "merkle_root": self.merkle_root,
            "is_encrypted": self.is_encrypted,
            "encryption_algorithm": self.encryption_algorithm,
            "key_derivation_algorithm": self.key_derivation_algorithm,
            "encryption_key_id": self.encryption_key_id,
            "signer_id": self.signer_id,
            "signer_public_key_b64": self.signer_public_key_b64,
            "metadata": self.metadata,
        }
        canonical_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return f"AEGIS-BACKUP-MANIFEST:v1:{canonical_str}".encode('utf-8')

    def compute_manifest_digest(self) -> str:
        """Computes deterministic SHA-256 digest of the canonical manifest payload."""
        return hashlib.sha256(self.canonical_manifest_bytes()).hexdigest()


# ==============================================================================
# 5. Recovery Verification Report
# ==============================================================================

class ComponentRecoveryStatus(BaseModel):
    """Verification status for an individual recovered subsystem."""
    component_name: str
    status: RecoveryState
    records_recovered: int = 0
    records_quarantined: int = 0
    details: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)


class RecoveryVerificationReport(BaseModel):
    """
    Comprehensive, machine-readable verification report generated after restoration.
    Fails closed: outcome cannot be RECOVERED if any security/evidence check fails.
    """
    recovery_id: str = Field(..., description="Unique restoration execution ID (rec_...)")
    backup_id: str = Field(..., description="Source backup ID")
    tenant_id: str = Field(..., description="Verified tenant boundary")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    schema_version: str = "1.0"
    application_version: str = "2.0.0"
    
    # Subsystem statuses
    ledger_status: RecoveryState = RecoveryState.UNRECOVERABLE
    lineage_status: RecoveryState = RecoveryState.UNRECOVERABLE
    telemetry_status: RecoveryState = RecoveryState.UNRECOVERABLE
    identity_status: RecoveryState = RecoveryState.UNRECOVERABLE
    evidence_status: RecoveryState = RecoveryState.UNRECOVERABLE
    key_status: RecoveryState = RecoveryState.UNRECOVERABLE
    
    # Global protection checks
    rollback_status: RecoveryState = RecoveryState.VALID_RECOVERY
    chain_status: RecoveryState = RecoveryState.VALID_RECOVERY
    tenant_boundary_status: RecoveryState = RecoveryState.VALID_RECOVERY
    
    # Executive outcome
    final_recovery_state: FinalRecoveryOutcome = FinalRecoveryOutcome.RECOVERY_FAILED
    components: Dict[str, ComponentRecoveryStatus] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    recovery_duration_ms: float = 0.0


# ==============================================================================
# 6. Tamper-Evident Recovery Audit Record
# ==============================================================================

class RecoveryAuditRecord(BaseModel):
    """
    Cryptographically chained audit record for all recovery and incident operations.
    Maintains independent integrity separate from the state being recovered.
    """
    audit_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    operator_id: str
    operator_role: str
    action: str  # BACKUP_CREATE, RESTORE_INITIATED, ROLLBACK_APPROVED, PRESERVATION_MODE_ENABLED
    tenant_id: str
    target_backup_id: Optional[str] = None
    target_recovery_id: Optional[str] = None
    previous_state: str
    new_state: str
    result: str  # SUCCESS, FAILED, REJECTED
    failure_reason: Optional[str] = None
    dual_authorizer_id: Optional[str] = None  # Required for separation-of-duties operations
    previous_record_hash: str = "0" * 64
    record_hash: Optional[str] = None

    def compute_record_hash(self) -> str:
        data = {
            "audit_id": self.audit_id,
            "timestamp": self.timestamp,
            "operator_id": self.operator_id,
            "operator_role": self.operator_role,
            "action": self.action,
            "tenant_id": self.tenant_id,
            "target_backup_id": self.target_backup_id,
            "target_recovery_id": self.target_recovery_id,
            "previous_state": self.previous_state,
            "new_state": self.new_state,
            "result": self.result,
            "failure_reason": self.failure_reason,
            "dual_authorizer_id": self.dual_authorizer_id,
            "previous_record_hash": self.previous_record_hash,
        }
        canonical_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()


# ==============================================================================
# 7. Incremental Delta & Temporal Validity Models
# ==============================================================================

class IncrementalDelta(BaseModel):
    """Payload container representing delta additions between sequential backups."""
    parent_backup_id: str = Field(..., description="Previous backup in the chain")
    parent_commitment: str = Field(..., description="Parent manifest SHA-256 digest")
    delta_sequence: int = Field(..., description="Sequence number of this delta")
    tenant_id: str = Field("default_tenant", description="Tenant boundary")
    objects: List[BackupObjectRecord] = Field(default_factory=list)
    tombstones: List[str] = Field(default_factory=list, description="IDs of deleted/pruned objects")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class TemporalValidityDecision(BaseModel):
    """Evaluation of evidence admissibility against known compromise timestamps."""
    item_id: str
    item_type: str
    event_timestamp: str
    compromise_timestamp: Optional[str] = None
    is_valid: bool
    status: str  # EVIDENCE_VALID, EVIDENCE_SUSPECT, EVIDENCE_REJECTED
    rationale: str

