"""
AegisTrace Complete End-to-End Forensic Integration Subsystem.

Stitches all core subsystems into a unified, cryptographically bound,
tamper-evident forensic pipeline:
- Broadcast encryption & PQC decapsulation (ML-KEM-768)
- Dynamic session-specific watermarking & DSSS carrier embedding
- Recipient-authored ML-DSA-65 signed decryption receipts
- Byzantine-fault-tolerant Permissioned DLT Ledger
- Sparse memory-bounded lineage graph indexing
- Telemetry, device attestation, and custody tracking
- Bayesian multi-channel evidence fusion & fail-closed attribution
- Cryptographically verifiable evidence package assembly
- Independent offline air-gapped forensic verification
"""

from core.integration.orchestrator import (
    AegisTraceEndToEndOrchestrator,
    GoldenPipelineResult,
    DecryptionArtifacts,
    ExtractionAndAttributionResult,
)
from core.integration.equivalence import (
    MultiRecipientEquivalenceAnalyzer,
    MultiRecipientEquivalenceReport,
    RecipientForensicProfile,
)
from core.integration.harness import (
    EndToEndFaultHarness,
    FaultInjectionResult,
    FaultType,
)

__all__ = [
    "AegisTraceEndToEndOrchestrator",
    "GoldenPipelineResult",
    "DecryptionArtifacts",
    "ExtractionAndAttributionResult",
    "MultiRecipientEquivalenceAnalyzer",
    "MultiRecipientEquivalenceReport",
    "RecipientForensicProfile",
    "EndToEndFaultHarness",
    "FaultInjectionResult",
    "FaultType",
]
