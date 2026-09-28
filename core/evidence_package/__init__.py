"""
AegisTrace Forensic Evidence Package Subsystem.

Provides portable, tamper-evident, machine-verifiable evidence packaging,
RFC-6962 Merkle tree commitments, post-quantum ML-DSA-65 signatures,
and autonomous offline verification.
"""

from core.evidence_package.canonical import (
    canonical_json_dumps,
    canonical_json_bytes,
    compute_content_hash,
)
from core.evidence_package.models import (
    EvidenceObjectType,
    VerificationStatus,
    VerificationResult,
    DecisionState,
    CustodyAction,
    TelemetryDependencyRelation,
    BaseEvidenceObject,
    CaseObject,
    ArtifactEvidenceObject,
    WatermarkEvidenceObject,
    DecryptionReceiptObject,
    RecipientIdentityProofObject,
    DeviceEvidenceObject,
    SessionEvidenceObject,
    LineageEvidenceObject,
    LedgerProofObject,
    TelemetryEvidenceObject,
    ChainOfCustodyEvent,
    AttributionDecisionObject,
    DependencyEdge,
    PackageManifest,
    PackageSignature,
)
from core.evidence_package.merkle import (
    EvidenceMerkleTree,
    MerkleInclusionProof,
)
from core.evidence_package.dependency import (
    EvidenceDependencyDAG,
    EvidenceDAGError,
)
from core.evidence_package.custody import (
    ChainOfCustodyLedger,
    CustodyVerificationError,
)
from core.evidence_package.redaction import (
    SafeRedactionEngine,
    RedactedEvidenceStub,
    RedactionClassification,
)
from core.evidence_package.builder import (
    EvidencePackage,
    EvidencePackageBuilder,
)
from core.evidence_package.verifier import (
    OfflineEvidenceVerifier,
)
from core.evidence_package.exporter import (
    EvidencePackageExporter,
    deserialize_evidence_object,
)

__all__ = [
    "canonical_json_dumps",
    "canonical_json_bytes",
    "compute_content_hash",
    "EvidenceObjectType",
    "VerificationStatus",
    "VerificationResult",
    "DecisionState",
    "CustodyAction",
    "TelemetryDependencyRelation",
    "BaseEvidenceObject",
    "CaseObject",
    "ArtifactEvidenceObject",
    "WatermarkEvidenceObject",
    "DecryptionReceiptObject",
    "RecipientIdentityProofObject",
    "DeviceEvidenceObject",
    "SessionEvidenceObject",
    "LineageEvidenceObject",
    "LedgerProofObject",
    "TelemetryEvidenceObject",
    "ChainOfCustodyEvent",
    "AttributionDecisionObject",
    "DependencyEdge",
    "PackageManifest",
    "PackageSignature",
    "EvidenceMerkleTree",
    "MerkleInclusionProof",
    "EvidenceDependencyDAG",
    "EvidenceDAGError",
    "ChainOfCustodyLedger",
    "CustodyVerificationError",
    "SafeRedactionEngine",
    "RedactedEvidenceStub",
    "RedactionClassification",
    "EvidencePackage",
    "EvidencePackageBuilder",
    "OfflineEvidenceVerifier",
    "EvidencePackageExporter",
    "deserialize_evidence_object",
]
