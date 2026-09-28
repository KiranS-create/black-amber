"""
AegisTrace Composed Adversary Attack Simulator.

Executes multi-action attack chains and multi-stage adversary simulations:
- CHAIN A: Stolen Account + Device Mismatch + Partial Telemetry + Valid Old Session
- CHAIN B: Valid Receipt + Modified Ledger Tail + Stale Checkpoint
- CHAIN C: Watermark Fragment + Wrong Document Binding + Forged Metadata (Transplantation)
- CHAIN D: Replayed Receipt + Rotated Key + Stale Evidence Package
- CHAIN E: Cross-Tenant Artifact + Valid Foreign Signature + Wrong Tenant Metadata
- CHAIN F: Valid Artifact + Modified Lineage + Conflicting Telemetry
- CHAIN G: Corrupted Evidence Package + Attempted Recovery + Stale State Rollback
- Multi-Stage 10-Step Realistic Adversary Timeline
"""

import copy
import base64
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone, timedelta
from enum import Enum
from pydantic import BaseModel, Field

from core.integration.orchestrator import AegisTraceEndToEndOrchestrator, GoldenPipelineResult
from core.evidence_package.models import (
    VerificationStatus,
    VerificationResult,
    DecisionState,
    DecryptionReceiptObject,
    RecipientIdentityProofObject,
    LedgerProofObject,
    LineageEvidenceObject,
    TelemetryEvidenceObject,
    TelemetryDependencyRelation,
)
from core.evidence_package.verifier import OfflineEvidenceVerifier


class ComposedAttackVerdict(str, Enum):
    DETECTED = "DETECTED"
    ABSTAINED = "ABSTAINED"
    CONFLICT = "CONFLICT"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    SECURITY_FAILURE = "SECURITY_FAILURE"


class ComposedAttackResult(BaseModel):
    chain_id: str
    chain_name: str
    description: str
    verdict: ComposedAttackVerdict
    security_maintained: bool
    evidence_errors: List[str] = Field(default_factory=list)
    mitigating_pillar: Optional[str] = None


class ComposedAttackSimulator:
    """
    Executes composed adversary attacks against AegisTrace.
    """

    @classmethod
    def execute_chain_a(cls, pipeline_result: GoldenPipelineResult) -> ComposedAttackResult:
        """
        CHAIN A: Stolen Account + Device Mismatch + Partial Telemetry + Valid Old Session.
        Attacker possesses credentials but operates from untrusted hardware and attempts session forging.
        """
        tampered_pkg = copy.deepcopy(pipeline_result.evidence_package)
        
        # Inject mismatched device and conflicting telemetry
        for obj in tampered_pkg.objects:
            if isinstance(obj, TelemetryEvidenceObject):
                obj.device_id = "dev_rogue_unregistered_attacker_node"
                obj.dependency_relation = TelemetryDependencyRelation.CONFLICTS
                obj.seal_content_hash()
            elif isinstance(obj, DecryptionReceiptObject):
                # Receipt still has Alice's signature, but telemetry conflicts
                pass

        verifier = OfflineEvidenceVerifier(expected_tenant_id=pipeline_result.tenant_id)
        res = verifier.verify_package(
            manifest=tampered_pkg.manifest,
            signature=tampered_pkg.signature,
            objects=tampered_pkg.objects,
            edges=tampered_pkg.edges,
            custody_chain=tampered_pkg.custody_chain
        )

        # Pillar 4 content hash or pillar 3 Merkle tree catches object mutation without signature update
        is_safe = (res.overall_status != VerificationStatus.VERIFIED)
        return ComposedAttackResult(
            chain_id="CHAIN_A",
            chain_name="Stolen Account & Device/Telemetry Conflict",
            description="Attacker accesses from unauthorized device and tampers telemetry",
            verdict=ComposedAttackVerdict.DETECTED if is_safe else ComposedAttackVerdict.SECURITY_FAILURE,
            security_maintained=is_safe,
            evidence_errors=res.errors,
            mitigating_pillar="Pillar 4 (Content Integrity) & Pillar 3 (Merkle Commitment)"
        )

    @classmethod
    def execute_chain_b(cls, orchestrator: AegisTraceEndToEndOrchestrator) -> ComposedAttackResult:
        """
        CHAIN B: Valid Receipt + Modified Ledger Tail + Stale Checkpoint.
        Attacker attempts to fork or rollback the DLT ledger with a modified block tail.
        """
        dlt = orchestrator.dlt_ledger
        node = list(dlt.nodes.values())[0]

        # Attempt to commit a block with modified previous hash (Fork attack)
        from core.ledger.dlt import DLTBlock, DLTBlockHeader
        forged_header = DLTBlockHeader(
            block_height=node.get_tip_height() + 1,
            previous_block_hash="forged_prev_" + "0" * 52,
            proposer_validator_id=list(dlt.val_map.keys())[0],
            round_number=99,
            merkle_root="0" * 64
        )
        forged_block = DLTBlock(
            header=forged_header,
            block_hash=forged_header.compute_header_hash(),
            transactions=[]
        )

        try:
            node.commit_block(forged_block)
            # If committed, attack succeeded (bad)
            return ComposedAttackResult(
                chain_id="CHAIN_B",
                chain_name="Ledger Tail Mutation & Fork Injection",
                description="Attacker attempts to append block with broken parent hash",
                verdict=ComposedAttackVerdict.SECURITY_FAILURE,
                security_maintained=False,
                evidence_errors=["Forged block accepted onto ledger"]
            )
        except Exception as e:
            return ComposedAttackResult(
                chain_id="CHAIN_B",
                chain_name="Ledger Tail Mutation & Fork Injection",
                description="Attacker attempts to append block with broken parent hash",
                verdict=ComposedAttackVerdict.DETECTED,
                security_maintained=True,
                evidence_errors=[str(e)],
                mitigating_pillar="DLT Continuity & Parent Hash Enforcement"
            )

    @classmethod
    def execute_chain_c(cls, pipeline_result: GoldenPipelineResult) -> ComposedAttackResult:
        """
        CHAIN C: Watermark Fragment + Wrong Document Binding + Forged Metadata (Transplantation).
        Attacker transplants watermark from Doc A onto Doc B.
        """
        tampered_pkg = copy.deepcopy(pipeline_result.evidence_package)
        
        for obj in tampered_pkg.objects:
            if isinstance(obj, DecryptionReceiptObject):
                # Bind receipt to a completely different document root hash
                obj.document_id = "doc_transplanted_wrong_target"
                obj.seal_content_hash()
                break

        verifier = OfflineEvidenceVerifier(expected_tenant_id=pipeline_result.tenant_id)
        res = verifier.verify_package(
            manifest=tampered_pkg.manifest,
            signature=tampered_pkg.signature,
            objects=tampered_pkg.objects,
            edges=tampered_pkg.edges,
            custody_chain=tampered_pkg.custody_chain
        )

        is_safe = (res.overall_status != VerificationStatus.VERIFIED)
        return ComposedAttackResult(
            chain_id="CHAIN_C",
            chain_name="Watermark Transplantation & Document Binding Breach",
            description="Attacker transplants watermark token onto unrelated document",
            verdict=ComposedAttackVerdict.DETECTED if is_safe else ComposedAttackVerdict.SECURITY_FAILURE,
            security_maintained=is_safe,
            evidence_errors=res.errors,
            mitigating_pillar="Pillar 6 (Canonical Payload Replay) & Pillar 9 (Watermark Binding)"
        )

    @classmethod
    def execute_chain_d(cls, pipeline_result: GoldenPipelineResult) -> ComposedAttackResult:
        """
        CHAIN D: Replayed Receipt + Rotated Key + Stale Evidence Package.
        Attacker replays a receipt dated after key revocation.
        """
        tampered_pkg = copy.deepcopy(pipeline_result.evidence_package)
        now = datetime.now(timezone.utc)
        
        # Set receipt timestamp after key revocation
        for obj in tampered_pkg.objects:
            if isinstance(obj, RecipientIdentityProofObject):
                obj.revocation_timestamp = (now - timedelta(days=5)).isoformat()
                obj.seal_content_hash()
                break

        verifier = OfflineEvidenceVerifier(expected_tenant_id=pipeline_result.tenant_id)
        res = verifier.verify_package(
            manifest=tampered_pkg.manifest,
            signature=tampered_pkg.signature,
            objects=tampered_pkg.objects,
            edges=tampered_pkg.edges,
            custody_chain=tampered_pkg.custody_chain
        )

        is_safe = (res.overall_status != VerificationStatus.VERIFIED and not res.historical_keys_valid)
        return ComposedAttackResult(
            chain_id="CHAIN_D",
            chain_name="Post-Revocation Replay & Stale Key Replay",
            description="Attacker replays receipt signed by revoked key",
            verdict=ComposedAttackVerdict.DETECTED if is_safe else ComposedAttackVerdict.SECURITY_FAILURE,
            security_maintained=is_safe,
            evidence_errors=res.errors,
            mitigating_pillar="Pillar 7 (Key Lifecycle & Revocation Boundary)"
        )

    @classmethod
    def execute_chain_e(cls, pipeline_result: GoldenPipelineResult) -> ComposedAttackResult:
        """
        CHAIN E: Cross-Tenant Artifact + Valid Foreign Signature + Wrong Tenant Metadata.
        Attacker injects an authentic Tenant Alpha artifact into Tenant Bravo audit.
        """
        verifier = OfflineEvidenceVerifier(expected_tenant_id="tenant_bravo_foreign")
        res = verifier.verify_package(
            manifest=pipeline_result.evidence_package.manifest,
            signature=pipeline_result.evidence_package.signature,
            objects=pipeline_result.evidence_package.objects,
            edges=pipeline_result.evidence_package.edges,
            custody_chain=pipeline_result.evidence_package.custody_chain
        )

        is_safe = (res.overall_status == VerificationStatus.INVALID and any("TENANT_ISOLATION_VIOLATION" in e for e in res.errors))
        return ComposedAttackResult(
            chain_id="CHAIN_E",
            chain_name="Cross-Tenant Foreign Package Injection",
            description="Tenant Alpha package audited under Tenant Bravo context",
            verdict=ComposedAttackVerdict.DETECTED if is_safe else ComposedAttackVerdict.SECURITY_FAILURE,
            security_maintained=is_safe,
            evidence_errors=res.errors,
            mitigating_pillar="Pillar 1 (Tenant Isolation Partition)"
        )

    @classmethod
    def execute_chain_f(cls, pipeline_result: GoldenPipelineResult) -> ComposedAttackResult:
        """
        CHAIN F: Valid Artifact + Modified Lineage + Conflicting Telemetry.
        Attacker fabricates an ungrounded intermediary lineage node.
        """
        tampered_pkg = copy.deepcopy(pipeline_result.evidence_package)
        
        for obj in tampered_pkg.objects:
            if isinstance(obj, LineageEvidenceObject):
                obj.has_downstream_gap = True
                obj.last_known_holder = None  # Breach: gap without preserving last known holder
                obj.seal_content_hash()
                break

        verifier = OfflineEvidenceVerifier(expected_tenant_id=pipeline_result.tenant_id)
        res = verifier.verify_package(
            manifest=tampered_pkg.manifest,
            signature=tampered_pkg.signature,
            objects=tampered_pkg.objects,
            edges=tampered_pkg.edges,
            custody_chain=tampered_pkg.custody_chain
        )

        is_safe = (res.overall_status != VerificationStatus.VERIFIED and not res.lineage_valid)
        return ComposedAttackResult(
            chain_id="CHAIN_F",
            chain_name="Lineage Downstream Gap Violation",
            description="Downstream gap introduced without preserving last known holder",
            verdict=ComposedAttackVerdict.DETECTED if is_safe else ComposedAttackVerdict.SECURITY_FAILURE,
            security_maintained=is_safe,
            evidence_errors=res.errors,
            mitigating_pillar="Pillar 10 (Lineage Integrity & Boundary Preservation)"
        )

    @classmethod
    def execute_chain_g(cls, pipeline_result: GoldenPipelineResult) -> ComposedAttackResult:
        """
        CHAIN G: Corrupted Evidence Package + Attempted Recovery + Stale State Rollback.
        Attacker forges manifest hash to bypass corrupted objects.
        """
        tampered_pkg = copy.deepcopy(pipeline_result.evidence_package)
        # Mutate manifest signed hash
        tampered_pkg.signature.signed_manifest_hash = "forged_manifest_" + "0" * 48

        verifier = OfflineEvidenceVerifier(expected_tenant_id=pipeline_result.tenant_id)
        res = verifier.verify_package(
            manifest=tampered_pkg.manifest,
            signature=tampered_pkg.signature,
            objects=tampered_pkg.objects,
            edges=tampered_pkg.edges,
            custody_chain=tampered_pkg.custody_chain
        )

        is_safe = (res.overall_status == VerificationStatus.INVALID and not res.manifest_signature_valid)
        return ComposedAttackResult(
            chain_id="CHAIN_G",
            chain_name="Corrupted Package Manifest Forgery",
            description="Attacker attempts to replace signed manifest digest",
            verdict=ComposedAttackVerdict.DETECTED if is_safe else ComposedAttackVerdict.SECURITY_FAILURE,
            security_maintained=is_safe,
            evidence_errors=res.errors,
            mitigating_pillar="Pillar 2 (ML-DSA-65 Manifest Signature)"
        )
