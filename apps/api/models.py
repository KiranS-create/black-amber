from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from core.recipient import PublicRecipient
from core.release import DocumentRelease, ReleaseRecipientPackage
from core.attribution.engine import AttributionResult, Candidate, EvidenceItem
from core.attribution.evidence import AttributionState, EvidenceConfidenceLevel
from core.identity.models import Identity, Group, ResolvedIdentitySummary

# --- Artifact & Plane Identity Models ---

class ArtifactType(str, Enum):
    ORIGINAL_DOCUMENT = "ORIGINAL_DOCUMENT"
    RELEASE_PACKAGE = "RELEASE_PACKAGE"
    DECRYPTED_TRACEABLE = "DECRYPTED_TRACEABLE"
    LEAK_ARTIFACT = "LEAK_ARTIFACT"

class ArtifactMetadata(BaseModel):
    artifact_id: str
    artifact_type: ArtifactType
    sha256_hash: str
    tenant_id: str = "default_tenant"
    document_id: Optional[str] = None
    release_id: Optional[str] = None
    recipient_id: Optional[str] = None
    mime_type: str
    size_bytes: int
    storage_path: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# --- Document Models ---

class DocumentMetadata(BaseModel):
    document_id: str
    document_name: str
    original_document_hash: str
    tenant_id: str = "default_tenant"
    size_bytes: int
    mime_type: str
    created_at: str
    artifact_id: str

class DocumentListResponse(BaseModel):
    documents: List[DocumentMetadata]
    total: int

# --- Directory & Identity Models ---

class IdentityResponse(BaseModel):
    identity_id: str
    provider: str
    provider_subject: str
    display_name: str
    email: str
    organization_id: str
    department: Optional[str] = None
    title: Optional[str] = None
    status: str
    created_at: str

class DirectorySearchResponse(BaseModel):
    identities: List[IdentityResponse]
    total: int

class GroupResponse(BaseModel):
    group_id: str
    display_name: str
    description: Optional[str] = None
    organization_id: str
    member_count: int
    member_identity_ids: List[str]

class GroupListResponse(BaseModel):
    groups: List[GroupResponse]
    total: int

# --- Recipient Models ---

class EnrollRecipientRequest(BaseModel):
    name: Optional[str] = Field(None, description="Human-readable name of the recipient (optional if identity_id given)")
    identity_id: Optional[str] = Field(None, description="Directory identity ID to enroll")
    recipient_id: Optional[str] = Field(None, description="Custom recipient ID (auto-generated if omitted)")

# --- Release Models ---

class CreateReleaseRequest(BaseModel):
    document_id: Optional[str] = Field(None, description="ID of pre-registered document")
    document_name: Optional[str] = Field(None, max_length=256, description="Document title if uploaded inline")
    document_base64: Optional[str] = Field(None, description="Base64 document bytes if not pre-registered")
    issuer_id: str = Field("HQ_AUTHORITY", description="Issuing authority identity")
    recipient_ids: Optional[List[str]] = Field(None, description="List of authorized recipient IDs")
    target_type: Optional[str] = Field("recipients", description="'recipients', 'identities', or 'groups'")
    target_ids: Optional[List[str]] = Field(None, description="Target identity or group IDs")
    tenant_id: Optional[str] = Field(None, description="Tenant boundary scope")
    tardos_enabled: bool = Field(False, description="Enable Tardos fingerprinting code generation")
    coalition_size: int = Field(3, ge=1, le=10, description="Target maximum collusion coalition size")
    false_accusation_epsilon: float = Field(1e-4, gt=0.0, lt=1.0, description="Max acceptable false alarm bound")
    carrier_budget: Optional[int] = Field(None, description="Available carrier capacity symbol budget")

class ReleaseSummary(BaseModel):
    release_id: str
    document_id: str
    document_name: str
    original_document_hash: str
    tenant_id: str = "default_tenant"
    issuer_id: str
    recipient_ids: List[str]
    created_at: str
    package_count: int
    target_summary: Optional[Dict[str, Any]] = None

# --- Decryption & Provenance Models ---

class DecryptRequest(BaseModel):
    recipient_id: str = Field(..., description="ID of the recipient decrypting the package")

class DecryptionResponse(BaseModel):
    status: str = "SUCCESS"
    release_id: str
    document_id: str
    recipient_id: str
    original_document_hash: str
    traceable_artifact_hash: str
    event_id: str
    event_hash: str
    timestamp: str
    simulation_mode: bool = True
    provenance_mode: str = "SIMULATED_LOCAL_ORACLE"
    traceable_document_base64: Optional[str] = None
    artifact_download_url: Optional[str] = None

# --- Leak & Ingestion Models ---

class LeakMetadata(BaseModel):
    leak_id: str
    leak_artifact_hash: str
    tenant_id: str = "default_tenant"
    size_bytes: int
    mime_type: str
    suspected_document_id: Optional[str] = None
    suspected_release_id: Optional[str] = None
    created_at: str
    artifact_id: str

# --- Attack Context Ingestion ---

class AttackTelemetryInput(BaseModel):
    attack_id: Optional[str] = None
    attack_family: Optional[str] = None
    attack_name: Optional[str] = None
    execution_mode: str = "SIMULATED"  # "PHYSICAL" or "SIMULATED"
    parameters: Dict[str, Any] = Field(default_factory=dict)
    input_hash: Optional[str] = None
    output_hash: Optional[str] = None
    psnr: Optional[float] = None
    ssim: Optional[float] = None
    crop_ratio: Optional[float] = None
    noise_level: Optional[float] = None

# --- Analysis & Jobs Models ---

class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABSTAINED = "ABSTAINED"

class AnalyzeRequest(BaseModel):
    leak_id: Optional[str] = Field(None, description="ID of pre-uploaded leak artifact")
    leaked_document_base64: Optional[str] = Field(None, description="Inline base64 bytes if not pre-uploaded")
    expected_release_id: Optional[str] = Field(None, description="Expected release scope (optional)")
    expected_document_id: Optional[str] = Field(None, description="Expected document scope (optional)")
    tenant_id: Optional[str] = Field(None, description="Tenant boundary scope")
    attack_telemetry: Optional[AttackTelemetryInput] = Field(None, description="Observed attack lab telemetry")
    async_execution: bool = Field(False, description="Whether to execute as an asynchronous job")

class AnalysisJobResponse(BaseModel):
    analysis_id: str
    status: JobStatus
    tenant_id: str = "default_tenant"
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    leak_id: Optional[str] = None
    leak_artifact_hash: Optional[str] = None
    result: Optional[AttributionResult] = None
    error: Optional[str] = None

    @property
    def job_id(self) -> str:
        return self.analysis_id

class AnalysisListResponse(BaseModel):
    jobs: List[AnalysisJobResponse]
    total: int

# --- System & Capabilities Models ---

class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = "SIH26237 API"
    version: str = "1.0.0"
    ledger_events_count: int
    registered_documents_count: int
    enrolled_recipients_count: int
    releases_count: int
    active_jobs_count: int

class CapabilitiesResponse(BaseModel):
    service_name: str
    version: str
    offline_mode: bool = True
    authentication_mode: str = "BEARER_TOKEN_ACTOR"
    key_custody_model: str = "DECENTRALIZED_CLIENT_CUSTODY"
    simulation_mode: bool = False
    cryptography: Dict[str, Any]
    traceability: Dict[str, Any]
    evidence_fusion: Dict[str, Any]
    watermarking: Dict[str, Any] = Field(default_factory=dict)
    client_workflows: Dict[str, Any] = Field(default_factory=dict)
    supported_formats: List[str]

class LedgerVerifyResponse(BaseModel):
    is_valid: bool
    total_events: int
    chain_tip: str
    errors: List[str] = Field(default_factory=list)
