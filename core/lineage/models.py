"""
SIH26237 - Active Cryptographic Copy Lineage Models
Defines core primitives, lifecycle states, transitions, forensic boundaries,
and lineage proofs for AegisTrace document instances.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
import hashlib
import os
from pydantic import BaseModel, Field


class ForensicAttributionLevel(str, Enum):
    """
    Hierarchical forensic attribution levels.
    Strictly enforced: if only Level 2 is established, Level 4/5 must NOT be claimed.
    """
    LEVEL_1_DOCUMENT_DETECTED = "LEVEL_1_DOCUMENT_DETECTED"
    LEVEL_2_ORIGINAL_RECIPIENT_IDENTIFIED = "LEVEL_2_ORIGINAL_RECIPIENT_IDENTIFIED"
    LEVEL_3_COPY_INSTANCE_IDENTIFIED = "LEVEL_3_COPY_INSTANCE_IDENTIFIED"
    LEVEL_4_LINEAGE_IDENTIFIED = "LEVEL_4_LINEAGE_IDENTIFIED"
    LEVEL_5_HUMAN_IDENTITY_RESOLVED = "LEVEL_5_HUMAN_IDENTITY_RESOLVED"


class ForensicBoundaryState(str, Enum):
    """
    Forensic boundary and lineage status classification.
    Explicitly distinguishes controlled custody from uncontrolled dissemination.
    """
    ATTRIBUTED_TO_CONTROLLED_ACTOR = "ATTRIBUTED_TO_CONTROLLED_ACTOR"
    LAST_KNOWN_HOLDER = "LAST_KNOWN_HOLDER"
    LINEAGE_CONTINUES = "LINEAGE_CONTINUES"
    LINEAGE_BROKEN = "LINEAGE_BROKEN"
    UNKNOWN_DOWNSTREAM_ACTOR = "UNKNOWN_DOWNSTREAM_ACTOR"
    IDENTITY_UNRESOLVED = "IDENTITY_UNRESOLVED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CONFLICT = "CONFLICT"
    ABSTAINED = "ABSTAINED"


class TransitionActionType(str, Enum):
    """Types of controlled document transitions."""
    ISSUANCE = "ISSUANCE"
    CONTROLLED_SHARE = "CONTROLLED_SHARE"
    EXPORT = "EXPORT"
    SESSION_VIEW = "SESSION_VIEW"
    PRINT = "PRINT"
    SCREEN_CAPTURE = "SCREEN_CAPTURE"
    DELEGATE = "DELEGATE"
    TRANSFER = "TRANSFER"


class ExportFormat(str, Enum):
    """Formats supported by the controlled export boundary."""
    PDF = "PDF"
    IMAGE = "IMAGE"
    PRINT = "PRINT"
    SCREEN = "SCREEN"


class DeviceAttestationStatus(str, Enum):
    """Hardware attestation states. Never fakes attestation."""
    DEVICE_ATTESTED = "DEVICE_ATTESTED"
    DEVICE_UNATTESTED = "DEVICE_UNATTESTED"


class PlatformType(str, Enum):
    """Hardware platform security module classification."""
    TPM = "TPM"
    SECURE_ENCLAVE = "SECURE_ENCLAVE"
    STRONGBOX = "STRONGBOX"
    WEBAUTHN = "WEBAUTHN"
    SOFTWARE_LOCAL = "SOFTWARE_LOCAL"


class DocumentRoot(BaseModel):
    """
    Immutable root anchor for a protected document in AegisTrace.
    """
    document_id: str = Field(..., description="Stable opaque unique identifier (e.g. doc_root_8f7a9c2b)")
    canonical_hash: str = Field(..., description="SHA-256 hash of original master plaintext")
    mime_type: str = Field("application/pdf", description="Document MIME type")
    byte_size: int = Field(..., description="Byte length of original master document")
    creation_metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata, classification, issuer")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = Field("ACTIVE", description="Lifecycle status (ACTIVE, ARCHIVED, REVOKED)")


def generate_copy_id(
    canonical_hash: str,
    parent_copy_id: Optional[str],
    recipient_or_session_id: str,
    timestamp: str,
    nonce: str
) -> str:
    """
    Cryptographically derives a unique, collision-resistant, privacy-preserving Copy ID:
    copy_id = "cpy_" + SHA256(canonical_hash || parent_copy_id || recipient_or_session_id || timestamp || nonce)[:32]
    """
    parent_str = parent_copy_id or "ROOT"
    preimage = f"{canonical_hash}:{parent_str}:{recipient_or_session_id}:{timestamp}:{nonce}".encode('utf-8')
    digest = hashlib.sha256(preimage).hexdigest()[:32]
    return f"cpy_{digest}"


class CopyInstance(BaseModel):
    """
    Cryptographically unique document copy instance participating in lineage.
    Never exposes names or emails; uses opaque identifiers.
    """
    copy_id: str = Field(..., description="Opaque deterministic copy identifier")
    parent_copy_id: Optional[str] = Field(None, description="Immediate ancestor copy ID (None for root issuance)")
    document_id: str = Field(..., description="DocumentRoot.document_id reference")
    release_id: Optional[str] = Field(None, description="DocumentRelease.release_id if issued via batch release")
    recipient_principal_id: Optional[str] = Field(None, description="Opaque cryptographic recipient principal ID")
    issuance_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    instance_nonce: str = Field(default_factory=lambda: os.urandom(16).hex())
    embedded_fingerprint_reference: Optional[str] = Field(None, description="Tardos / DSSS / HMAC marker reference")
    status: str = Field("ACTIVE", description="Instance status: ACTIVE, EXPORTED, REVOKED, LEAKED")
    lineage_depth: int = Field(0, description="0 for root issuance, parent.depth + 1 for child derivatives")
    document_root_hash: Optional[str] = Field(None, description="SHA-256 hash of document root")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AccessSession(BaseModel):
    """
    Session-bound controlled interaction with a protected document instance.
    Generates dynamic session-unique fingerprinting material without leaking human PII.
    """
    session_id: str = Field(..., description="Opaque session identifier (e.g. ses_7c91a0b3)")
    copy_id: str = Field(..., description="Target CopyInstance.copy_id")
    identity_id: Optional[str] = Field(None, description="Authenticated enterprise identity reference")
    device_key_id: Optional[str] = Field(None, description="DeviceBinding key ID if attested/bound")
    issued_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: Optional[str] = Field(None, description="Session expiry timestamp")
    session_nonce: str = Field(default_factory=lambda: os.urandom(16).hex())
    session_fingerprint_key: str = Field(
        default_factory=lambda: f"sf_{os.urandom(12).hex()}",
        description="Pseudonymous session watermark/fingerprint material"
    )
    is_active: bool = Field(True, description="Whether session is currently valid")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ForwardingEvent(BaseModel):
    """
    Cryptographic transition receipt for a controlled share/forwarding action.
    Signed by the actor using ML-DSA-65.
    """
    forwarding_event_id: str = Field(..., description="Opaque forwarding event ID (e.g. fwd_4a2c1f8d)")
    parent_copy_id: str = Field(..., description="Source CopyInstance.copy_id")
    child_copy_id: str = Field(..., description="Target CopyInstance.copy_id issued to recipient")
    actor_identity_id: Optional[str] = Field(None, description="Sender's Identity.identity_id")
    actor_principal_id: Optional[str] = Field(None, description="Sender's RecipientPrincipal.recipient_id")
    sender_device_id: Optional[str] = Field(None, description="Sender's DeviceBinding.device_id")
    recipient_identity_id: Optional[str] = Field(None, description="Recipient's Identity.identity_id")
    recipient_principal_id: Optional[str] = Field(None, description="Recipient's RecipientPrincipal.recipient_id")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    action_type: TransitionActionType = Field(TransitionActionType.CONTROLLED_SHARE)
    signed_event_hash: Optional[str] = Field(None, description="SHA-256 hash of event preimage")
    signature_b64: Optional[str] = Field(None, description="ML-DSA-65 signature over event preimage")
    signer_public_key_b64: Optional[str] = Field(None, description="ML-DSA-65 public key of signer")
    previous_event_hash: Optional[str] = Field("0" * 64, description="Parent event hash in hash chain")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def compute_preimage(self) -> bytes:
        """
        Canonical preimage binding all transition parameters:
        LINEAGE_FORWARDING:{fwd_id}:{parent_copy}:{child_copy}:{actor}:{device}:{action}:{prev_hash}:{timestamp}
        """
        actor = self.actor_principal_id or self.actor_identity_id or "ANONYMOUS"
        device = self.sender_device_id or "UNATTESTED"
        prev = self.previous_event_hash or ("0" * 64)
        raw = f"LINEAGE_FORWARDING:{self.forwarding_event_id}:{self.parent_copy_id}:{self.child_copy_id}:{actor}:{device}:{self.action_type.value}:{prev}:{self.timestamp}"
        return raw.encode('utf-8')

    def compute_event_hash(self) -> str:
        return hashlib.sha256(self.compute_preimage()).hexdigest()


class ExportEvent(BaseModel):
    """
    Cryptographic transition receipt for an export/print/screen-capture event.
    Re-fingerprints document to produce a new child copy instance.
    """
    export_id: str = Field(..., description="Opaque export event ID (e.g. exp_6b3e8a1d)")
    source_session_id: str = Field(..., description="AccessSession.session_id where export occurred")
    parent_copy_id: str = Field(..., description="CopyInstance.copy_id being exported")
    child_copy_id: str = Field(..., description="New child CopyInstance.copy_id generated for exported file")
    export_format: ExportFormat = Field(ExportFormat.PDF, description="Export format")
    export_fingerprint: str = Field(..., description="Child copy fingerprint token embedded in export")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    actor_identity_id: Optional[str] = Field(None, description="Identity ID of user executing export")
    actor_principal_id: Optional[str] = Field(None, description="Principal ID of user executing export")
    device_identity_id: Optional[str] = Field(None, description="Device ID where export occurred")
    signed_event_hash: Optional[str] = Field(None, description="SHA-256 hash of export preimage")
    signature_b64: Optional[str] = Field(None, description="ML-DSA-65 signature over export preimage")
    signer_public_key_b64: Optional[str] = Field(None, description="ML-DSA-65 public key of signer")
    previous_event_hash: Optional[str] = Field("0" * 64, description="Parent event hash in hash chain")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def compute_preimage(self) -> bytes:
        """
        Canonical preimage binding all export parameters:
        LINEAGE_EXPORT:{exp_id}:{session_id}:{parent_copy}:{child_copy}:{format}:{fingerprint}:{prev_hash}:{timestamp}
        """
        prev = self.previous_event_hash or ("0" * 64)
        raw = f"LINEAGE_EXPORT:{self.export_id}:{self.source_session_id}:{self.parent_copy_id}:{self.child_copy_id}:{self.export_format.value}:{self.export_fingerprint}:{prev}:{self.timestamp}"
        return raw.encode('utf-8')

    def compute_event_hash(self) -> str:
        return hashlib.sha256(self.compute_preimage()).hexdigest()


class DeviceBinding(BaseModel):
    """
    Hardware and cryptographic device identity representation.
    """
    device_id: str = Field(..., description="Opaque device identifier (e.g. dev_9c2a8f1b)")
    device_key_id: str = Field(..., description="Key identifier for device public key")
    attestation_status: DeviceAttestationStatus = Field(DeviceAttestationStatus.DEVICE_UNATTESTED)
    platform_type: PlatformType = Field(PlatformType.SOFTWARE_LOCAL)
    public_key_b64: Optional[str] = None
    enrolled_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LineageEdge(BaseModel):
    """
    Directed parent-child edge in the document copy lineage graph.
    """
    edge_id: str = Field(..., description="Opaque edge identifier")
    parent_copy_id: Optional[str] = Field(None, description="Parent CopyInstance ID (None for root issuance)")
    child_copy_id: str = Field(..., description="Child CopyInstance ID")
    transition_type: TransitionActionType
    event_id: str = Field(..., description="Associated ForwardingEvent.forwarding_event_id or ExportEvent.export_id")
    actor_principal_id: Optional[str] = None
    recipient_principal_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_verified: bool = Field(True, description="Whether transition signature and hashes verified")


class LineageProof(BaseModel):
    """
    Deterministic cryptographic proof and ancestry summary for a copy instance.
    Explicitly flags boundary conditions and broken chains.
    """
    leaf_copy_id: str
    root_document_id: str
    path: List[LineageEdge] = Field(default_factory=list)
    ancestor_copy_ids: List[str] = Field(default_factory=list)
    last_known_controlled_holder: Optional[str] = None
    forensic_boundary_state: ForensicBoundaryState = ForensicBoundaryState.LINEAGE_CONTINUES
    highest_attribution_level: ForensicAttributionLevel = ForensicAttributionLevel.LEVEL_1_DOCUMENT_DETECTED
    is_valid: bool = True
    break_reason: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
