"""
AegisTrace Evidence Package Builder.

Assembles, content-addresses, builds Merkle trees over, and cryptographically signs
complete forensic evidence packages using post-quantum ML-DSA-65.
Guarantees:
1. Deterministic ordering of objects and Merkle leaves.
2. Independent validation of DAG acyclicity and chain of custody prior to signing.
3. Post-quantum signature binding over the package manifest.
4. Safe preservation of signer public key without leaking private material.
"""

import base64
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone

from core.crypto.signatures import MLDSA65
from core.crypto.models import KeyPair
from core.evidence_package.models import (
    BaseEvidenceObject,
    CaseObject,
    AttributionDecisionObject,
    DependencyEdge,
    ChainOfCustodyEvent,
    PackageManifest,
    PackageSignature
)
from core.evidence_package.merkle import EvidenceMerkleTree
from core.evidence_package.dependency import EvidenceDependencyDAG
from core.evidence_package.custody import ChainOfCustodyLedger


class EvidencePackage:
    """
    Self-contained in-memory representation of an authentic forensic evidence package.
    """
    def __init__(
        self,
        manifest: PackageManifest,
        signature: PackageSignature,
        objects: List[BaseEvidenceObject],
        edges: List[DependencyEdge],
        custody_chain: List[ChainOfCustodyEvent]
    ):
        self.manifest = manifest
        self.signature = signature
        self.objects = objects
        self.edges = edges
        self.custody_chain = custody_chain
        self.object_map: Dict[str, BaseEvidenceObject] = {obj.object_id: obj for obj in objects}

    @property
    def decision(self) -> Optional[AttributionDecisionObject]:
        """Returns the final AttributionDecisionObject if present in the package."""
        return next((obj for obj in self.objects if isinstance(obj, AttributionDecisionObject)), None)



class EvidencePackageBuilder:
    """
    Orchestrates assembly and post-quantum signing of evidence packages.
    """
    def __init__(self, case_id: str, tenant_id: str = "default_tenant", package_id: Optional[str] = None):
        self.case_id = case_id
        self.tenant_id = tenant_id
        self.package_id = package_id or f"pkg_{case_id}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        self.objects: List[BaseEvidenceObject] = []
        self.edges: List[DependencyEdge] = []
        self.custody_chain: List[ChainOfCustodyEvent] = []
        self.decision_object_id: Optional[str] = None
        self.ledger_commitments: List[str] = []

    def add_object(self, obj: BaseEvidenceObject) -> "EvidencePackageBuilder":
        """Adds an evidence object and seals its content hash."""
        obj.tenant_id = self.tenant_id
        obj.seal_content_hash()
        self.objects.append(obj)
        return self

    def add_edge(self, source_id: str, target_id: str, relationship_type: str = "GROUNDED_IN") -> "EvidencePackageBuilder":
        """Adds a dependency edge between evidence nodes."""
        edge_id = f"edge_{len(self.edges):04d}_{source_id}_{target_id}"
        edge = DependencyEdge(
            object_id=edge_id,
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
            tenant_id=self.tenant_id
        )
        edge.seal_content_hash()
        self.edges.append(edge)
        return self

    def add_custody_event(self, event: ChainOfCustodyEvent) -> "EvidencePackageBuilder":
        """Adds an event to the package's chain of custody."""
        event.tenant_id = self.tenant_id
        event.seal_content_hash()
        self.custody_chain.append(event)
        return self

    def set_decision(self, decision: AttributionDecisionObject) -> "EvidencePackageBuilder":
        """Sets the final attribution decision object."""
        self.decision_object_id = decision.object_id
        self.add_object(decision)
        return self

    def add_ledger_commitment(self, block_hash: str) -> "EvidencePackageBuilder":
        self.ledger_commitments.append(block_hash)
        return self

    def build_and_sign(
        self,
        signing_keypair: KeyPair,
        signer_id: str = "OFFICIAL_FORENSIC_EXAMINER"
    ) -> EvidencePackage:
        """
        Builds Merkle commitments, validates DAG and custody, and signs package with ML-DSA-65.
        """
        if not self.decision_object_id:
            raise ValueError("Cannot build evidence package without an AttributionDecisionObject")

        # 1. Validate DAG
        dag = EvidenceDependencyDAG()
        for obj in self.objects:
            dag.add_node(obj)
        for edge in self.edges:
            dag.add_edge(edge)
        dag.validate_acyclic()
        grounded, errors = dag.verify_grounding(self.decision_object_id)
        if not grounded:
            raise ValueError(f"Evidence DAG grounding validation failed: {errors}")

        # 2. Validate Chain of Custody
        if self.custody_chain:
            valid_coc, coc_errors = ChainOfCustodyLedger.verify_chain(self.custody_chain, expected_tenant_id=self.tenant_id)
            if not valid_coc:
                raise ValueError(f"Chain of custody validation failed: {coc_errors}")

        # 3. Build Merkle Tree over sorted object content hashes
        sorted_objects = sorted(self.objects, key=lambda x: x.object_id)
        leaf_hashes = [obj.content_hash for obj in sorted_objects]
        merkle_tree = EvidenceMerkleTree(leaf_hashes)

        # 4. Inventory
        inventory = [
            {
                "object_id": obj.object_id,
                "object_type": obj.object_type.value if hasattr(obj.object_type, "value") else str(obj.object_type),
                "content_hash": obj.content_hash
            }
            for obj in sorted_objects
        ]

        # 5. Manifest
        manifest = PackageManifest(
            case_id=self.case_id,
            tenant_id=self.tenant_id,
            package_id=self.package_id,
            object_inventory=inventory,
            dependency_graph_root=self.decision_object_id,
            evidence_merkle_root=merkle_tree.root,
            ledger_commitment_references=self.ledger_commitments,
            final_decision_reference=self.decision_object_id
        )

        # 6. Post-Quantum Signing with ML-DSA-65
        manifest_hash = manifest.compute_manifest_hash()
        manifest_bytes = manifest_hash.encode("utf-8")
        sig_bytes = MLDSA65.sign(signing_keypair.private_key_bytes, manifest_bytes)

        pub_b64 = base64.b64encode(signing_keypair.public_key_bytes).decode("utf-8")
        sig_b64 = base64.b64encode(sig_bytes).decode("utf-8")

        pkg_signature = PackageSignature(
            signer_id=signer_id,
            signer_algorithm="ML-DSA-65",
            signer_public_key_b64=pub_b64,
            signed_manifest_hash=manifest_hash,
            signature_b64=sig_b64
        )

        return EvidencePackage(
            manifest=manifest,
            signature=pkg_signature,
            objects=sorted_objects,
            edges=self.edges,
            custody_chain=self.custody_chain
        )
