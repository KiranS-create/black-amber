"""
AegisTrace Forensic State Inventory & Operational Recovery Objectives.

Provides the comprehensive inventory of all 24 stateful/security-sensitive components
that must survive a disaster, along with formal RPO/RTO operational specifications.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from core.recovery.models import (
    ComponentStateClass,
    CriticalityTier,
    TargetClassification,
    RecoveryRequirement,
)


class InventoryItem(BaseModel):
    """Catalog record for a stateful AegisTrace component."""
    component_id: str
    name: str
    description: str
    state_class: ComponentStateClass
    criticality: CriticalityTier
    tenant_scoped: bool
    recovery_requirement: RecoveryRequirement
    target_backup_frequency: str
    data_store: str
    model_schema: str
    can_reconstruct_from_source_code: bool = False


class OperationalObjective(BaseModel):
    """Formal RPO or RTO operational parameter with rigorous epistemic classification."""
    metric_name: str
    metric_type: str  # "RPO" or "RTO"
    target_value: str
    target_seconds: float
    classification: TargetClassification
    subsystem: str
    rationale: str


class ForensicStateInventory:
    """
    Authoritative catalog of all stateful components, storage representations,
    recoverability constraints, and RPO/RTO operational objectives.
    """

    ITEMS: Dict[str, InventoryItem] = {
        "release_metadata": InventoryItem(
            component_id="release_metadata",
            name="Encrypted Document Release Metadata",
            description="DocumentRelease records, original document hash, parameters, recipient rosters",
            state_class=ComponentStateClass.AUTHORITATIVE,
            criticality=CriticalityTier.SECURITY_CRITICAL,
            tenant_scoped=True,
            recovery_requirement=RecoveryRequirement.EXACT_CRYPTOGRAPHIC,
            target_backup_frequency="Continuous / Per Release",
            data_store="core.release.ReleaseManager.releases",
            model_schema="core.release.DocumentRelease",
        ),
        "recipient_capsules": InventoryItem(
            component_id="recipient_capsules",
            name="Recipient Cryptographic Capsules",
            description="ML-KEM-768 ciphertexts, wrapped keys, and symmetric envelopes per recipient",
            state_class=ComponentStateClass.AUTHORITATIVE,
            criticality=CriticalityTier.SECURITY_CRITICAL,
            tenant_scoped=True,
            recovery_requirement=RecoveryRequirement.EXACT_CRYPTOGRAPHIC,
            target_backup_frequency="Continuous / Per Release",
            data_store="core.release.ReleaseRecipientPackage",
            model_schema="core.release.ReleaseRecipientPackage",
        ),
        "recipient_identities": InventoryItem(
            component_id="recipient_identities",
            name="Recipient Cryptographic Identities",
            description="Public ML-KEM and ML-DSA keys, enrollment metadata, principal mapping",
            state_class=ComponentStateClass.AUTHORITATIVE,
            criticality=CriticalityTier.SECURITY_CRITICAL,
            tenant_scoped=True,
            recovery_requirement=RecoveryRequirement.EXACT_CRYPTOGRAPHIC,
            target_backup_frequency="Daily / On Enrollment",
            data_store="core.recipient.RecipientRegistry",
            model_schema="core.recipient.Recipient",
        ),
        "device_identities": InventoryItem(
            component_id="device_identities",
            name="Device Hardware & Cryptographic Identities",
            description="TPM/Secure Enclave public keys, platform fingerprints, device UUIDs",
            state_class=ComponentStateClass.AUTHORITATIVE,
            criticality=CriticalityTier.SECURITY_CRITICAL,
            tenant_scoped=True,
            recovery_requirement=RecoveryRequirement.EXACT_CRYPTOGRAPHIC,
            target_backup_frequency="Daily / On Enrollment",
            data_store="core.device.enrollment.DeviceRegistry",
            model_schema="core.device.models.DeviceRecord",
        ),
        "device_attestation_state": InventoryItem(
            component_id="device_attestation_state",
            name="Device Attestation Verification State",
            description="Attestation tokens, quote verification records, PCR hashes",
            state_class=ComponentStateClass.AUTHORITATIVE,
            criticality=CriticalityTier.EVIDENCE_CRITICAL,
            tenant_scoped=True,
            recovery_requirement=RecoveryRequirement.EXACT_CRYPTOGRAPHIC,
            target_backup_frequency="Hourly / Per Session",
            data_store="core.device.attestation.AttestationVerifier",
            model_schema="core.device.models.AttestationEvidence",
        ),
        "decryption_receipts": InventoryItem(
            component_id="decryption_receipts",
            name="Decryption Receipts (ML-DSA-65 Signed)",
            description="Recipient-signed cryptographic proofs of document plaintext access",
            state_class=ComponentStateClass.AUTHORITATIVE,
            criticality=CriticalityTier.EVIDENCE_CRITICAL,
            tenant_scoped=True,
            recovery_requirement=RecoveryRequirement.EXACT_CRYPTOGRAPHIC,
            target_backup_frequency="Real-time / Per Decrypt",
            data_store="core.ledger.dlt.DLTNode.receipts",
            model_schema="core.ledger.dlt.DecryptionReceipt",
        ),
        "controlled_view_sessions": InventoryItem(
            component_id="controlled_view_sessions",
            name="Controlled Viewing Sessions",
            description="Active and historical viewing sessions, session watermark keys, bounds",
            state_class=ComponentStateClass.AUTHORITATIVE,
            criticality=CriticalityTier.EVIDENCE_CRITICAL,
            tenant_scoped=True,
            recovery_requirement=RecoveryRequirement.EXACT_CRYPTOGRAPHIC,
            target_backup_frequency="Hourly / Session Close",
            data_store="core.lineage.storage.LineageStorage._sessions",
            model_schema="core.lineage.models.AccessSession",
        ),
        "dynamic_watermark_metadata": InventoryItem(
            component_id="dynamic_watermark_metadata",
            name="Dynamic Watermark Metadata & Tokens",
            description="DSSS/Tardos codeword allocations, bit indices, carrier mappings",
            state_class=ComponentStateClass.AUTHORITATIVE,
            criticality=CriticalityTier.EVIDENCE_CRITICAL,
            tenant_scoped=True,
            recovery_requirement=RecoveryRequirement.EXACT_CRYPTOGRAPHIC,
            target_backup_frequency="Real-time / Per Instance",
            data_store="core.traceability.provider.TardosTraceabilityProvider",
            model_schema="core.attribution.evidence.TargetBinding",
        ),
        "lineage_graph": InventoryItem(
            component_id="lineage_graph",
            name="Active Copy Lineage Graph Nodes",
            description="DocumentRoot master documents, CopyInstance derived nodes, depth counters",
            state_class=ComponentStateClass.AUTHORITATIVE,
            criticality=CriticalityTier.EVIDENCE_CRITICAL,
            tenant_scoped=True,
            recovery_requirement=RecoveryRequirement.EXACT_CRYPTOGRAPHIC,
            target_backup_frequency="Real-time / Per Copy",
            data_store="core.lineage.storage.LineageStorage._copies",
            model_schema="core.lineage.models.CopyInstance",
        ),
        "copy_relationships": InventoryItem(
            component_id="copy_relationships",
            name="Copy Relationship Transitions (Edges)",
            description="ForwardingEvents, ExportEvents, signed lineage transition receipts",
            state_class=ComponentStateClass.AUTHORITATIVE,
            criticality=CriticalityTier.EVIDENCE_CRITICAL,
            tenant_scoped=True,
            recovery_requirement=RecoveryRequirement.EXACT_CRYPTOGRAPHIC,
            target_backup_frequency="Real-time / Per Copy",
            data_store="core.lineage.storage.LineageStorage._edges",
            model_schema="core.lineage.models.ForwardingEvent",
        ),
        "telemetry_events": InventoryItem(
            component_id="telemetry_events",
            name="Forensic Telemetry Events & Timelines",
            description="Normalized ForensicEvents from EDR/DLP/IdP/Cloud, unified causal timeline",
            state_class=ComponentStateClass.AUTHORITATIVE,
            criticality=CriticalityTier.EVIDENCE_CRITICAL,
            tenant_scoped=True,
            recovery_requirement=RecoveryRequirement.DEDUPLICATED_APPEND,
            target_backup_frequency="Hourly Batch",
            data_store="core.telemetry.engine.TelemetryEngine",
            model_schema="core.telemetry.event.ForensicEvent",
        ),
        "attribution_results": InventoryItem(
            component_id="attribution_results",
            name="Forensic Attribution Inquiries & Decisions",
            description="AttributionResult models, candidate likelihood ratios, fail-closed decisions",
            state_class=ComponentStateClass.AUTHORITATIVE,
            criticality=CriticalityTier.EVIDENCE_CRITICAL,
            tenant_scoped=True,
            recovery_requirement=RecoveryRequirement.EXACT_CRYPTOGRAPHIC,
            target_backup_frequency="Daily / Per Inquiry",
            data_store="core.attribution.engine.AttributionEngine",
            model_schema="core.attribution.engine.AttributionResult",
        ),
        "evidence_packages": InventoryItem(
            component_id="evidence_packages",
            name="Evidence Packages & Bundles",
            description="EvidenceBundle containers, cross-channel observations, target bindings",
            state_class=ComponentStateClass.AUTHORITATIVE,
            criticality=CriticalityTier.EVIDENCE_CRITICAL,
            tenant_scoped=True,
            recovery_requirement=RecoveryRequirement.EXACT_CRYPTOGRAPHIC,
            target_backup_frequency="Real-time / Per Inquiry",
            data_store="core.attribution.evidence.EvidenceBundle",
            model_schema="core.attribution.evidence.EvidenceBundle",
        ),
        "ledger_events": InventoryItem(
            component_id="ledger_events",
            name="Audit Ledger Hash-Chained Events",
            description="EvidenceEvent records, sequential SHA-256 hash chain linking from genesis",
            state_class=ComponentStateClass.AUTHORITATIVE,
            criticality=CriticalityTier.EVIDENCE_CRITICAL,
            tenant_scoped=True,
            recovery_requirement=RecoveryRequirement.EXACT_CRYPTOGRAPHIC,
            target_backup_frequency="Real-time / Per Event",
            data_store="core.ledger.ledger.TamperEvidentLedger.events",
            model_schema="core.ledger.ledger.EvidenceEvent",
        ),
        "ledger_checkpoints": InventoryItem(
            component_id="ledger_checkpoints",
            name="DLT Epoch Checkpoints & Blocks",
            description="DLTBlock headers, quorum endorsements, round checkpoints",
            state_class=ComponentStateClass.AUTHORITATIVE,
            criticality=CriticalityTier.SECURITY_CRITICAL,
            tenant_scoped=False,
            recovery_requirement=RecoveryRequirement.BFT_QUORUM,
            target_backup_frequency="Per Epoch / Block",
            data_store="core.ledger.dlt.DLTNode.blocks",
            model_schema="core.ledger.dlt.DLTBlock",
        ),
        "merkle_roots": InventoryItem(
            component_id="merkle_roots",
            name="Merkle Roots & Inclusion Proof Trees",
            description="RFC-6962 double-domain binary Merkle roots and branch node hashes",
            state_class=ComponentStateClass.DERIVED,
            criticality=CriticalityTier.SECURITY_CRITICAL,
            tenant_scoped=False,
            recovery_requirement=RecoveryRequirement.EXACT_CRYPTOGRAPHIC,
            target_backup_frequency="Per Block / Epoch",
            data_store="core.ledger.dlt.build_merkle_tree",
            model_schema="core.ledger.dlt.MerkleProof",
        ),
        "validator_state": InventoryItem(
            component_id="validator_state",
            name="Permissioned Validator State & Topology",
            description="DLTValidator identities, public keys, voting weights, quorum thresholds",
            state_class=ComponentStateClass.AUTHORITATIVE,
            criticality=CriticalityTier.SECURITY_CRITICAL,
            tenant_scoped=False,
            recovery_requirement=RecoveryRequirement.BFT_QUORUM,
            target_backup_frequency="On Topology Mutation",
            data_store="core.ledger.dlt.DLTNode.authorized_validators",
            model_schema="core.ledger.dlt.DLTValidator",
        ),
        "federated_identity_cache": InventoryItem(
            component_id="federated_identity_cache",
            name="Federated Identity Directory & Claims Cache",
            description="OIDC/SAML/SCIM claims cache, identity-to-principal bindings",
            state_class=ComponentStateClass.REBUILDABLE,
            criticality=CriticalityTier.OPERATIONAL,
            tenant_scoped=True,
            recovery_requirement=RecoveryRequirement.RECONSTITUTED_INDEX,
            target_backup_frequency="Daily Sync",
            data_store="core.identity.federated.FederatedIdentityDirectory",
            model_schema="core.identity.models.Identity",
        ),
        "configuration_state": InventoryItem(
            component_id="configuration_state",
            name="Tenant & Engine Configuration State",
            description="Security policies, quorum parameters, watermarking strengths, storage paths",
            state_class=ComponentStateClass.AUTHORITATIVE,
            criticality=CriticalityTier.SECURITY_CRITICAL,
            tenant_scoped=True,
            recovery_requirement=RecoveryRequirement.EXACT_CRYPTOGRAPHIC,
            target_backup_frequency="On Config Mutation",
            data_store="core.attribution.policy.AttributionPolicy",
            model_schema="core.attribution.policy.AttributionPolicy",
        ),
        "schema_version_metadata": InventoryItem(
            component_id="schema_version_metadata",
            name="Schema & Protocol Version Metadata",
            description="Protocol version tags, schema digests, migration history",
            state_class=ComponentStateClass.AUTHORITATIVE,
            criticality=CriticalityTier.SECURITY_CRITICAL,
            tenant_scoped=False,
            recovery_requirement=RecoveryRequirement.EXACT_CRYPTOGRAPHIC,
            target_backup_frequency="On Schema Upgrade",
            data_store="core.recovery.models.SignedBackupManifest.schema_version",
            model_schema="core.recovery.models.SignedBackupManifest",
        ),
        "cryptographic_key_metadata": InventoryItem(
            component_id="cryptographic_key_metadata",
            name="Cryptographic Key Lifecycle Records",
            description="KeyRecord models, epoch sequences, algorithms, custody tiers, key status",
            state_class=ComponentStateClass.AUTHORITATIVE,
            criticality=CriticalityTier.SECURITY_CRITICAL,
            tenant_scoped=True,
            recovery_requirement=RecoveryRequirement.EXACT_CRYPTOGRAPHIC,
            target_backup_frequency="On Key Generation / Rotation",
            data_store="core.crypto.lifecycle.manager.KeyLifecycleManager",
            model_schema="core.crypto.lifecycle.models.KeyRecord",
        ),
        "revocation_state": InventoryItem(
            component_id="revocation_state",
            name="Revocation State & Compromise Logs",
            description="Key revocation lists (KRLs), certificate revocation lists, compromise details",
            state_class=ComponentStateClass.AUTHORITATIVE,
            criticality=CriticalityTier.SECURITY_CRITICAL,
            tenant_scoped=True,
            recovery_requirement=RecoveryRequirement.EXACT_CRYPTOGRAPHIC,
            target_backup_frequency="Real-time / On Revocation",
            data_store="core.crypto.lifecycle.manager.KeyLifecycleManager._revocation_log",
            model_schema="core.crypto.lifecycle.models.KeyRecord",
        ),
        "audit_logs": InventoryItem(
            component_id="audit_logs",
            name="System & Recovery Audit Trail",
            description="RecoveryAuditRecord hash-chained sequence recording operator actions",
            state_class=ComponentStateClass.AUTHORITATIVE,
            criticality=CriticalityTier.SECURITY_CRITICAL,
            tenant_scoped=True,
            recovery_requirement=RecoveryRequirement.EXACT_CRYPTOGRAPHIC,
            target_backup_frequency="Continuous / Real-time",
            data_store="core.recovery.audit.RecoveryAuditLog",
            model_schema="core.recovery.models.RecoveryAuditRecord",
        ),
        "forensic_policy_calibration": InventoryItem(
            component_id="forensic_policy_calibration",
            name="Forensic Policy & Statistical Calibration State",
            description="Likelihood ratio thresholds, Tardos epsilon bounds, false positive bounds",
            state_class=ComponentStateClass.AUTHORITATIVE,
            criticality=CriticalityTier.EVIDENCE_CRITICAL,
            tenant_scoped=True,
            recovery_requirement=RecoveryRequirement.EXACT_CRYPTOGRAPHIC,
            target_backup_frequency="On Policy Update",
            data_store="core.attribution.policy.AttributionPolicy",
            model_schema="core.attribution.policy.AttributionPolicy",
        ),
    }

    OBJECTIVES: Dict[str, OperationalObjective] = {
        "rpo_ledger": OperationalObjective(
            metric_name="RPO: Tamper-Evident Ledger",
            metric_type="RPO",
            target_value="0 seconds (Zero data loss)",
            target_seconds=0.0,
            classification=TargetClassification.DESIGN_TARGET,
            subsystem="Ledger",
            rationale="Synchronous append with hash chain commit ensures committed transactions are never lost."
        ),
        "rpo_evidence": OperationalObjective(
            metric_name="RPO: Evidence Metadata & Packages",
            metric_type="RPO",
            target_value="<= 60 seconds",
            target_seconds=60.0,
            classification=TargetClassification.DESIGN_TARGET,
            subsystem="Attribution",
            rationale="Content-addressed evidence bundle snapshots occur upon conclusion of forensic inquiries."
        ),
        "rpo_telemetry": OperationalObjective(
            metric_name="RPO: External Telemetry Datasets",
            metric_type="RPO",
            target_value="<= 300 seconds (5 minutes)",
            target_seconds=300.0,
            classification=TargetClassification.DESIGN_TARGET,
            subsystem="Telemetry",
            rationale="Heterogeneous sensor events stream into micro-batch buffers flushed every 5 minutes."
        ),
        "rto_ledger_verify_10k": OperationalObjective(
            metric_name="RTO: Ledger Hash-Chain Verification (10K events)",
            metric_type="RTO",
            target_value="<= 1.50 seconds",
            target_seconds=1.5,
            classification=TargetClassification.MEASURED,
            subsystem="Ledger",
            rationale="Batch SHA-256 hash chaining executes in vectorized Python memory."
        ),
        "rto_lineage_rebuild_10k": OperationalObjective(
            metric_name="RTO: Lineage Sparse Index Rebuild (10K copies)",
            metric_type="RTO",
            target_value="<= 0.25 seconds",
            target_seconds=0.25,
            classification=TargetClassification.MEASURED,
            subsystem="Lineage",
            rationale="SparseLineageIndex non-recursive insertion operates at >40K ops/sec."
        ),
        "rto_identity_resolve_1k": OperationalObjective(
            metric_name="RTO: Identity Resolution (1K principals)",
            metric_type="RTO",
            target_value="<= 0.10 seconds",
            target_seconds=0.1,
            classification=TargetClassification.MEASURED,
            subsystem="Identity",
            rationale="O(1) in-memory dictionary hydration."
        ),
        "rto_forensic_inquiry": OperationalObjective(
            metric_name="RTO: Forensic Evidence Package Reconstitution",
            metric_type="RTO",
            target_value="<= 5.0 seconds",
            target_seconds=5.0,
            classification=TargetClassification.DESIGN_TARGET,
            subsystem="Attribution",
            rationale="Deserialization, target binding verification, and observation tree reconstruction."
        ),
        "rto_controlled_release": OperationalObjective(
            metric_name="RTO: Controlled Document Release Service",
            metric_type="RTO",
            target_value="<= 10.0 seconds",
            target_seconds=10.0,
            classification=TargetClassification.DESIGN_TARGET,
            subsystem="Release",
            rationale="Reconstitution of RecipientRegistry, active keys, and release packages."
        ),
        "rto_airgapped_recovery": OperationalObjective(
            metric_name="RTO: Full Air-Gapped Bare-Metal Recovery",
            metric_type="RTO",
            target_value="<= 60.0 seconds",
            target_seconds=60.0,
            classification=TargetClassification.DESIGN_TARGET,
            subsystem="DisasterRecovery",
            rationale="Offline recovery media unpack, manifest signature verification, and service hydration."
        ),
    }

    @classmethod
    def get_inventory_items(cls) -> List[InventoryItem]:
        return list(cls.ITEMS.values())

    @classmethod
    def get_operational_objectives(cls) -> List[OperationalObjective]:
        return list(cls.OBJECTIVES.values())
