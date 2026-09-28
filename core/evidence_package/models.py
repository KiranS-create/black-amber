"""
AegisTrace Strongly-Typed Forensic Evidence Object Model.

Defines the formal schema for 17 evidence object categories participating
in portable, tamper-evident, machine-verifiable forensic evidence packages.
Guarantees content addressing, canonical serialization, and provenance tracking.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import hashlib

from core.evidence_package.canonical import canonical_json_bytes, canonical_json_dumps, compute_content_hash


# ==============================================================================
# 1. Enums
# ==============================================================================

class EvidenceObjectType(str, Enum):
    CASE = "CASE"
    EVIDENCE_OBJECT = "EVIDENCE_OBJECT"
    ARTIFACT = "ARTIFACT"
    WATERMARK_EVIDENCE = "WATERMARK_EVIDENCE"
    DECRYPTION_RECEIPT = "DECRYPTION_RECEIPT"
    RECIPIENT_IDENTITY_PROOF = "RECIPIENT_IDENTITY_PROOF"
    DEVICE_EVIDENCE = "DEVICE_EVIDENCE"
    SESSION_EVIDENCE = "SESSION_EVIDENCE"
    LINEAGE_EVIDENCE = "LINEAGE_EVIDENCE"
    LEDGER_PROOF = "LEDGER_PROOF"
    TELEMETRY_EVIDENCE = "TELEMETRY_EVIDENCE"
    CHAIN_OF_CUSTODY_EVENT = "CHAIN_OF_CUSTODY_EVENT"
    ATTRIBUTION_DECISION = "ATTRIBUTION_DECISION"
    DEPENDENCY_EDGE = "DEPENDENCY_EDGE"
    PACKAGE_MANIFEST = "PACKAGE_MANIFEST"
    SIGNATURE = "SIGNATURE"
    VERIFICATION_RESULT = "VERIFICATION_RESULT"


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    INVALID = "INVALID"
    INCOMPLETE = "INCOMPLETE"
    CONFLICT = "CONFLICT"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"


class TelemetryDependencyRelation(str, Enum):
    DIRECTLY_SUPPORTS = "DIRECTLY_SUPPORTS"
    CORROBORATES = "CORROBORATES"
    CONFLICTS = "CONFLICTS"
    IS_DEPENDENT_ON = "IS_DEPENDENT_ON"
    DEPENDS_ON = "IS_DEPENDENT_ON"
    IS_UNAVAILABLE = "IS_UNAVAILABLE"


class CustodyAction(str, Enum):
    COLLECTED = "COLLECTED"
    IMPORTED = "IMPORTED"
    VERIFIED = "VERIFIED"
    ANALYZED = "ANALYZED"
    EXPORTED = "EXPORTED"
    SEALED = "SEALED"
    REVIEWED = "REVIEWED"


class DecisionState(str, Enum):
    ATTRIBUTED = "ATTRIBUTED"
    NO_SIGNAL = "NO_SIGNAL"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CONFLICT = "CONFLICT"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    ABSTAINED = "ABSTAINED"
    FAILED = "FAILED"


# ==============================================================================
# 2. Base Evidence Object Envelope
# ==============================================================================

class BaseEvidenceObject(BaseModel):
    """
    Cryptographic content-addressed base model for all evidence objects.
    Computes deterministic content_hash from payload fields.
    """
    object_id: str
    object_type: EvidenceObjectType
    schema_version: str = "1.0"
    tenant_id: str = "default_tenant"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    parent_ids: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    content_hash: Optional[str] = None

    def compute_content_digest(self) -> str:
        """
        Computes SHA-256 digest of canonical serialization excluding content_hash itself.
        """
        data = self.model_dump(mode="json")
        data.pop("content_hash", None)
        return compute_content_hash(data)

    def seal_content_hash(self) -> str:
        """Sets content_hash to computed digest and returns it."""
        self.content_hash = self.compute_content_digest()
        return self.content_hash

    def verify_content_integrity(self) -> bool:
        """Verifies that stored content_hash matches computed digest."""
        if not self.content_hash:
            return False
        return self.content_hash.lower() == self.compute_content_digest().lower()


# ==============================================================================
# 3. Domain Specific Evidence Objects
# ==============================================================================

class CaseObject(BaseEvidenceObject):
    object_type: EvidenceObjectType = EvidenceObjectType.CASE
    case_name: str
    investigator_id: str
    description: str
    classification_level: str = "CONFIDENTIAL"


class ArtifactEvidenceObject(BaseEvidenceObject):
    object_type: EvidenceObjectType = EvidenceObjectType.ARTIFACT
    artifact_category: str  # ORIGINAL, RELEASE, LEAK
    filename: str
    mime_type: str = "application/pdf"
    byte_size: int
    sha256_digest: str
    document_id: Optional[str] = None
    release_id: Optional[str] = None


class WatermarkEvidenceObject(BaseEvidenceObject):
    object_type: EvidenceObjectType = EvidenceObjectType.WATERMARK_EVIDENCE
    artifact_hash: str
    extraction_method: str = "DYNAMIC_SPATIAL_DSSS_V1"
    extracted_token: str
    extracted_codeword: Optional[str] = None
    confidence_score: float = 0.0
    p_value: Optional[float] = None
    detection_state: str = "DETECTED"  # DETECTED, NO_SIGNAL, CORRUPTED
    is_simulated: bool = False  # Explicit physical vs simulation separation
    carrier_parameters: Dict[str, Any] = Field(default_factory=dict)
    expected_recipient_id: Optional[str] = None
    expected_session_id: Optional[str] = None


class DecryptionReceiptObject(BaseEvidenceObject):
    object_type: EvidenceObjectType = EvidenceObjectType.DECRYPTION_RECEIPT
    receipt_id: str
    document_id: str
    release_id: str
    recipient_id: str
    session_id: str
    key_id: str
    key_epoch: int
    timestamp: str
    watermark_token: str
    watermark_commitment: str
    recipient_signature_b64: str
    recipient_public_key_b64: str
    canonical_payload: Optional[str] = None

    def construct_canonical_payload(self) -> bytes:
        """
        Reconstructs the canonical recipient-signed payload:
        AEGIS-DECRYPT-CONFIRM:v1:<doc>:<rel>:<rec>:<sess>:<key_id>:<epoch>:<token>:<commit>:<ts>
        """
        raw = f"AEGIS-DECRYPT-CONFIRM:v1:{self.document_id}:{self.release_id}:{self.recipient_id}:{self.session_id}:{self.key_id}:{self.key_epoch}:{self.watermark_token}:{self.watermark_commitment}:{self.timestamp}"
        return raw.encode("utf-8")


class RecipientIdentityProofObject(BaseEvidenceObject):
    object_type: EvidenceObjectType = EvidenceObjectType.RECIPIENT_IDENTITY_PROOF
    recipient_id: str
    key_id: str
    algorithm: str = "ML-DSA-65"
    key_epoch: int = 1
    public_key_b64: str
    custody_class: str = "LOCAL_PROTECTED_STORE"
    recovery_class: str = "RECOVERABLE"
    predecessor_key_id: Optional[str] = None
    successor_key_id: Optional[str] = None
    activation_timestamp: Optional[str] = None
    revocation_timestamp: Optional[str] = None


class DeviceEvidenceObject(BaseEvidenceObject):
    object_type: EvidenceObjectType = EvidenceObjectType.DEVICE_EVIDENCE
    device_id: str
    attestation_status: str = "DEVICE_ATTESTED"  # DEVICE_ATTESTED, DEVICE_UNATTESTED
    platform_type: str = "TPM"  # TPM, SECURE_ENCLAVE, WEBAUTHN, SOFTWARE_LOCAL
    hardware_key_id: Optional[str] = None
    hardware_public_key_b64: Optional[str] = None
    attestation_signature_b64: Optional[str] = None


class SessionEvidenceObject(BaseEvidenceObject):
    object_type: EvidenceObjectType = EvidenceObjectType.SESSION_EVIDENCE
    session_id: str
    copy_id: str
    recipient_id: str
    device_id: Optional[str] = None
    issued_at: str
    expires_at: Optional[str] = None
    session_nonce: str
    session_fingerprint_key: str


class LineageEvidenceObject(BaseEvidenceObject):
    object_type: EvidenceObjectType = EvidenceObjectType.LINEAGE_EVIDENCE
    document_id: str
    root_copy_id: str
    target_copy_id: Optional[str] = None
    lineage_subgraph: List[Dict[str, Any]] = Field(default_factory=list)
    boundary_state: str = "LAST_KNOWN_HOLDER"
    last_known_holder: Optional[str] = None
    has_downstream_gap: bool = False
    missing_parent_id: Optional[str] = None


class LedgerProofObject(BaseEvidenceObject):
    object_type: EvidenceObjectType = EvidenceObjectType.LEDGER_PROOF
    receipt_id: str
    receipt_hash: str
    block_height: int
    block_hash: str
    previous_block_hash: str
    timestamp: str
    merkle_root: str
    merkle_audit_path: List[Tuple[str, str]] = Field(default_factory=list)  # (sibling_hash, 'L'|'R')
    proposer_validator_id: str
    proposer_signature_b64: str
    quorum_signatures: Dict[str, str] = Field(default_factory=dict)
    quorum_threshold: int = 2
    authorized_validators: Dict[str, str] = Field(default_factory=dict)  # vid -> pub_key_b64


class TelemetryEvidenceObject(BaseEvidenceObject):
    object_type: EvidenceObjectType = EvidenceObjectType.TELEMETRY_EVIDENCE
    event_id: str
    event_hash: str
    timestamp: str
    source_system: str
    source_trust_level: str
    actor_id: Optional[str] = None
    device_id: Optional[str] = None
    network_id: Optional[str] = None
    dependency_relation: TelemetryDependencyRelation = TelemetryDependencyRelation.CORROBORATES
    relationship_details: str = ""


class ChainOfCustodyEvent(BaseEvidenceObject):
    object_type: EvidenceObjectType = EvidenceObjectType.CHAIN_OF_CUSTODY_EVENT
    custody_event_id: str
    evidence_object_id: str
    operator_identity: str
    device_identity: str
    action: CustodyAction
    timestamp: str
    previous_custody_hash: str
    resulting_evidence_hash: str
    reason: str


class AttributionDecisionObject(BaseEvidenceObject):
    object_type: EvidenceObjectType = EvidenceObjectType.ATTRIBUTION_DECISION
    case_id: str
    evidence_merkle_root: str
    decision_state: DecisionState
    attributed_principal_id: Optional[str] = None
    last_known_holder_id: Optional[str] = None
    confidence_score: float = 0.0
    evidence_dependency_ids: List[str] = Field(default_factory=list)
    policy_version: str = "1.0"
    reason_codes: List[str] = Field(default_factory=list)
    abstention_rationale: Optional[str] = None


class DependencyEdge(BaseEvidenceObject):
    object_type: EvidenceObjectType = EvidenceObjectType.DEPENDENCY_EDGE
    source_id: str
    target_id: str
    relationship_type: str = "GROUNDED_IN"  # GROUNDED_IN, COMMITTED_IN, DERIVED_FROM, CORROBORATED_BY


# ==============================================================================
# 4. Manifest, Signatures & Verification Report
# ==============================================================================

class PackageManifest(BaseModel):
    """
    Deterministic manifest committing to all objects, Merkle root, and metadata.
    """
    case_id: str
    tenant_id: str
    package_id: str
    package_version: str = "1.0"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    application_version: str = "AegisTrace-2.4-PQC"
    schema_versions: Dict[str, str] = Field(default_factory=lambda: {"evidence_schema": "1.0", "manifest_schema": "1.0"})
    object_inventory: List[Dict[str, str]] = Field(
        default_factory=list,
        description="List of {object_id, object_type, content_hash}"
    )
    dependency_graph_root: str
    evidence_merkle_root: str
    ledger_commitment_references: List[str] = Field(default_factory=list)
    final_decision_reference: str
    verifier_requirements: Dict[str, Any] = Field(
        default_factory=lambda: {
            "min_verifier_version": "1.0",
            "supported_signature_algorithms": ["ML-DSA-65"],
            "hash_algorithm": "SHA-256"
        }
    )
    is_redacted: bool = False
    redacted_object_ids: List[str] = Field(default_factory=list)

    def compute_manifest_hash(self) -> str:
        """Deterministic digest of the manifest."""
        data = self.model_dump(mode="json")
        data.pop("is_redacted", None)
        data.pop("redacted_object_ids", None)
        return compute_content_hash(data)


class PackageSignature(BaseModel):
    """Post-quantum ML-DSA-65 signature over PackageManifest."""
    signer_id: str
    signer_algorithm: str = "ML-DSA-65"
    signer_public_key_b64: str
    signed_manifest_hash: str
    signature_b64: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def signature_bytes_b64(self) -> str:
        return self.signature_b64

    @signature_bytes_b64.setter
    def signature_bytes_b64(self, val: str) -> None:
        self.signature_b64 = val


class VerificationResult(BaseModel):
    """Comprehensive machine-readable evaluation report produced by offline verifier."""
    package_id: str
    overall_status: VerificationStatus
    verified_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    manifest_signature_valid: bool = False
    merkle_root_valid: bool = False
    object_hashes_valid: bool = False
    dependency_graph_valid: bool = False
    recipient_signature_valid: bool = False
    historical_keys_valid: bool = False
    ledger_proof_valid: bool = False
    watermark_binding_valid: bool = False
    lineage_valid: bool = False
    custody_chain_valid: bool = False
    decision_consistent: bool = False
    step_details: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
