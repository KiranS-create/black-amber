from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class IdentityStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"
    DEPROVISIONED = "DEPROVISIONED"

class Identity(BaseModel):
    """
    Enterprise Human Identity Representation.
    Owned and managed by external Identity Providers (Entra ID, Okta, LDAP, Google Workspace).
    AegisTrace stores only references and participants in forensic workflows.
    """
    identity_id: str = Field(..., description="Stable opaque unique identifier (e.g. usr_8f7a9c2b)")
    provider: str = Field(..., description="Source Identity Provider (e.g. entra, okta, local_directory)")
    provider_subject: str = Field(..., description="Immutable subject identifier from IdP (e.g. sub_10492842)")
    display_name: str = Field(..., description="Human display name (e.g. John Doe)")
    email: str = Field(..., description="Primary email address")
    organization_id: str = Field(..., description="Tenant or organization identifier")
    department: Optional[str] = Field(None, description="Department or division")
    title: Optional[str] = Field(None, description="Job title or organizational role")
    status: IdentityStatus = Field(IdentityStatus.ACTIVE, description="Lifecycle provisioning status")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom IdP claims and attributes")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class RecipientPrincipal(BaseModel):
    """
    Cryptographic Security Principal participating in AegisTrace releases.
    Binds an opaque recipient identifier to an Identity and post-quantum keys.
    """
    recipient_id: str = Field(..., description="Opaque cryptographic recipient identifier (e.g. rec_9a8b7c6d)")
    identity_id: str = Field(..., description="Reference to Identity.identity_id")
    identity_provider: str = Field("local_directory", description="Source IdP reference")
    display_name: Optional[str] = Field(None, description="Human display name for principal")
    kem_public_key_b64: str = Field(..., description="ML-KEM-768 public key for recipient-specific wrapping")
    dsa_public_key_b64: str = Field(..., description="ML-DSA-65 public key for provenance signature verification")
    algorithm_kem: str = "ML-KEM-768"
    algorithm_dsa: str = "ML-DSA-65"
    traceability_key_id: Optional[str] = Field(None, description="Tardos codeword or HMAC marker key reference")
    epoch: int = 1
    status: IdentityStatus = Field(IdentityStatus.ACTIVE, description="Recipient authorization status")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    revoked_at: Optional[str] = Field(None, description="Timestamp if revoked or deprovisioned")

class Group(BaseModel):
    """
    Directory Group or Team.
    Used for release targeting without creating shared cryptographic identities.
    """
    group_id: str = Field(..., description="Opaque group identifier (e.g. grp_legal_counsel)")
    display_name: str = Field(..., description="Human-readable group title")
    description: Optional[str] = None
    organization_id: str = Field(..., description="Organization identifier")
    member_identity_ids: List[str] = Field(default_factory=list, description="List of Identity.identity_id members")

class ResolvedIdentitySummary(BaseModel):
    """
    Resolved human identity details produced after forensic evidence attribution.
    """
    identity_id: str
    display_name: str
    email: str
    organization_id: str
    provider: str
    status: str
    department: Optional[str] = None
    title: Optional[str] = None
    source: str = "DIRECTORY"  # DIRECTORY, CACHE, PENDING, UNKNOWN

class IdentityResolutionResult(BaseModel):
    """
    Result of resolving an identity via IdentityResolver.
    """
    recipient_id: str
    status: str = "RESOLVED"  # RESOLVED, CACHED, PENDING, NOT_FOUND
    display_name: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None
    account_status: Optional[str] = None
    confidence: float = 1.0
    source: str = "DIRECTORY"
