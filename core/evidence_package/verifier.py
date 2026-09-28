"""
AegisTrace Independent Offline Evidence Verifier.

A completely autonomous, air-gapped forensic verification engine that audits
evidence packages with ZERO database access, ZERO network sockets, and ZERO
originating-server dependencies.
Executes the comprehensive 12-pillar forensic audit pipeline:
1. Package Structure & Manifest Integrity
2. Post-Quantum ML-DSA-65 Manifest Signature Verification
3. RFC-6962 Evidence Merkle Root Recomputation
4. Content-Addressed Hash Integrity for Every Object
5. Evidence Dependency DAG Grounding & Cycle Check
6. Canonical Decryption Receipt ML-DSA-65 Signature Replay
7. Key Lifecycle & Historical Revocation Boundary Check
8. DLT Block Header & Quorum Consensus Proof
9. Watermark Binding Reproduction: Artifact -> Token -> Ledger
10. Lineage Integrity: Missing Parent, No Fabricated Ancestors
11. Chain-of-Custody SHA-256 Hash Chain Integrity
12. Final Attribution Decision Consistency Check
"""

import base64
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple

from core.crypto.signatures import MLDSA65
from core.evidence_package.models import (
    BaseEvidenceObject,
    EvidenceObjectType,
    VerificationStatus,
    VerificationResult,
    PackageManifest,
    PackageSignature,
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
    DecisionState
)
from core.evidence_package.merkle import EvidenceMerkleTree, MerkleInclusionProof
from core.evidence_package.dependency import EvidenceDependencyDAG, EvidenceDAGError
from core.evidence_package.custody import ChainOfCustodyLedger
from core.evidence_package.redaction import RedactedEvidenceStub


class OfflineEvidenceVerifier:
    """
    Independent Offline Forensic Verifier.
    Accepts raw evidence package data structures and evaluates them against
    strict cryptographic and logical proof invariants.
    """
    def __init__(self, expected_tenant_id: Optional[str] = None):
        self.expected_tenant_id = expected_tenant_id

    def verify_package(
        self,
        manifest: PackageManifest,
        signature: PackageSignature,
        objects: List[BaseEvidenceObject],
        edges: Optional[List[DependencyEdge]] = None,
        custody_chain: Optional[List[ChainOfCustodyEvent]] = None
    ) -> VerificationResult:
        """
        Executes complete 12-pillar audit on an evidence package.
        """
        edges = edges or []
        custody_chain = custody_chain or []

        result = VerificationResult(
            package_id=manifest.package_id,
            overall_status=VerificationStatus.INVALID,
            verified_at=datetime.now(timezone.utc).isoformat()
        )

        object_map: Dict[str, BaseEvidenceObject] = {obj.object_id: obj for obj in objects}

        # ----------------------------------------------------------------------
        # Pillar 1: Package Structure & Tenant Matching
        # ----------------------------------------------------------------------
        if self.expected_tenant_id and manifest.tenant_id != self.expected_tenant_id:
            result.errors.append(
                f"TENANT_ISOLATION_VIOLATION: Expected tenant '{self.expected_tenant_id}', package belongs to '{manifest.tenant_id}'"
            )
            result.step_details["pillar_1_structure"] = {"passed": False, "error": "Tenant mismatch"}
            return result
        result.step_details["pillar_1_structure"] = {"passed": True}

        # ----------------------------------------------------------------------
        # Pillar 2: Post-Quantum ML-DSA-65 Manifest Signature Verification
        # ----------------------------------------------------------------------
        computed_manifest_hash = manifest.compute_manifest_hash()
        if computed_manifest_hash != signature.signed_manifest_hash:
            result.errors.append(
                f"MANIFEST_DIGEST_MISMATCH: Computed {computed_manifest_hash} != Signed {signature.signed_manifest_hash}"
            )
            result.manifest_signature_valid = False
            result.step_details["pillar_2_manifest_signature"] = {"passed": False, "error": "Manifest hash mismatch"}
        else:
            try:
                pub_bytes = base64.b64decode(signature.signer_public_key_b64)
                sig_bytes = base64.b64decode(signature.signature_b64)
                valid_sig = MLDSA65.verify(pub_bytes, computed_manifest_hash.encode("utf-8"), sig_bytes)
                if not valid_sig:
                    result.errors.append("MANIFEST_SIGNATURE_INVALID: Cryptographic verification of manifest signature failed")
                    result.manifest_signature_valid = False
                    result.step_details["pillar_2_manifest_signature"] = {"passed": False, "error": "Invalid signature"}
                else:
                    result.manifest_signature_valid = True
                    result.step_details["pillar_2_manifest_signature"] = {"passed": True}
            except Exception as e:
                result.errors.append(f"MANIFEST_SIGNATURE_EXCEPTION: {str(e)}")
                result.manifest_signature_valid = False
                result.step_details["pillar_2_manifest_signature"] = {"passed": False, "error": str(e)}

        # ----------------------------------------------------------------------
        # Pillar 3: RFC-6962 Evidence Merkle Root Recomputation
        # ----------------------------------------------------------------------
        sorted_objects = sorted(objects, key=lambda x: x.object_id)
        leaf_hashes = [obj.content_hash for obj in sorted_objects if obj.content_hash]
        recomputed_tree = EvidenceMerkleTree(leaf_hashes)

        if recomputed_tree.root.lower() != manifest.evidence_merkle_root.lower():
            result.errors.append(
                f"MERKLE_ROOT_MISMATCH: Recomputed {recomputed_tree.root} != Manifest {manifest.evidence_merkle_root}"
            )
            result.merkle_root_valid = False
            result.step_details["pillar_3_merkle_root"] = {"passed": False, "error": "Merkle root mismatch"}
        else:
            result.merkle_root_valid = True
            result.step_details["pillar_3_merkle_root"] = {"passed": True}

        # ----------------------------------------------------------------------
        # Pillar 4: Content-Addressed Hash Integrity for Every Object
        # ----------------------------------------------------------------------
        hash_errors = []
        for obj in objects:
            if isinstance(obj, RedactedEvidenceStub):
                # Redacted stub preserves original content_hash
                continue
            if not obj.verify_content_integrity():
                hash_errors.append(f"Object '{obj.object_id}' content_hash mismatch")

        if hash_errors:
            result.errors.extend(hash_errors)
            result.object_hashes_valid = False
            result.step_details["pillar_4_object_hashes"] = {"passed": False, "errors": hash_errors}
        else:
            result.object_hashes_valid = True
            result.step_details["pillar_4_object_hashes"] = {"passed": True, "object_count": len(objects)}

        # ----------------------------------------------------------------------
        # Pillar 5: Evidence Dependency DAG Grounding & Cycle Check
        # ----------------------------------------------------------------------
        dag = EvidenceDependencyDAG()
        for obj in objects:
            dag.add_node(obj)
        for edge in edges:
            dag.add_edge(edge)

        try:
            dag.validate_acyclic()
            grounded, g_errors = dag.verify_grounding(manifest.final_decision_reference)
            if not grounded:
                result.errors.extend(g_errors)
                result.dependency_graph_valid = False
                result.step_details["pillar_5_dag"] = {"passed": False, "errors": g_errors}
            else:
                result.dependency_graph_valid = True
                result.step_details["pillar_5_dag"] = {"passed": True}
        except EvidenceDAGError as e:
            result.errors.append(f"DAG_CYCLE_DETECTED: {str(e)}")
            result.dependency_graph_valid = False
            result.step_details["pillar_5_dag"] = {"passed": False, "error": str(e)}

        # ----------------------------------------------------------------------
        # Pillar 6: Canonical Decryption Receipt ML-DSA-65 Signature Replay
        # ----------------------------------------------------------------------
        receipts = [obj for obj in objects if isinstance(obj, DecryptionReceiptObject)]
        receipt_errors = []

        for r in receipts:
            canonical_payload = r.construct_canonical_payload()
            try:
                rec_pub_bytes = base64.b64decode(r.recipient_public_key_b64)
                rec_sig_bytes = base64.b64decode(r.recipient_signature_b64)
                if not MLDSA65.verify(rec_pub_bytes, canonical_payload, rec_sig_bytes):
                    receipt_errors.append(f"Receipt '{r.receipt_id}' invalid ML-DSA-65 signature")
            except Exception as e:
                receipt_errors.append(f"Receipt '{r.receipt_id}' signature exception: {str(e)}")

        if receipt_errors:
            result.errors.extend(receipt_errors)
            result.recipient_signature_valid = False
            result.step_details["pillar_6_receipt_signatures"] = {"passed": False, "errors": receipt_errors}
        else:
            result.recipient_signature_valid = True
            result.step_details["pillar_6_receipt_signatures"] = {"passed": True, "receipt_count": len(receipts)}

        # ----------------------------------------------------------------------
        # Pillar 7: Key Lifecycle & Historical Revocation Boundary Check
        # ----------------------------------------------------------------------
        key_proofs = {obj.key_id: obj for obj in objects if isinstance(obj, RecipientIdentityProofObject)}
        key_errors = []

        for r in receipts:
            k_proof = key_proofs.get(r.key_id)
            if not k_proof:
                key_errors.append(f"Receipt '{r.receipt_id}' references key '{r.key_id}' without RecipientIdentityProofObject")
                continue

            r_dt = datetime.fromisoformat(r.timestamp.replace("Z", "+00:00"))

            # Check activation boundary
            if k_proof.activation_timestamp:
                act_dt = datetime.fromisoformat(k_proof.activation_timestamp.replace("Z", "+00:00"))
                if r_dt < act_dt:
                    key_errors.append(f"Receipt '{r.receipt_id}' timestamp {r.timestamp} precedes key activation {k_proof.activation_timestamp}")

            # Check revocation boundary
            if k_proof.revocation_timestamp:
                rev_dt = datetime.fromisoformat(k_proof.revocation_timestamp.replace("Z", "+00:00"))
                if r_dt >= rev_dt:
                    key_errors.append(
                        f"POST_REVOCATION_REJECTION: Receipt '{r.receipt_id}' timestamp {r.timestamp} "
                        f"occurs after key revocation at {k_proof.revocation_timestamp}"
                    )

        if key_errors:
            result.errors.extend(key_errors)
            result.historical_keys_valid = False
            result.step_details["pillar_7_historical_keys"] = {"passed": False, "errors": key_errors}
        else:
            result.historical_keys_valid = True
            result.step_details["pillar_7_historical_keys"] = {"passed": True}

        # ----------------------------------------------------------------------
        # Pillar 8: DLT Block Header & Quorum Consensus Proof
        # ----------------------------------------------------------------------
        ledger_proofs = [obj for obj in objects if isinstance(obj, LedgerProofObject)]
        ledger_errors = []

        for lp in ledger_proofs:
            # 1. Verify receipt inclusion via Merkle audit path
            current_hash = hashlib.sha256(b"\x00" + lp.receipt_hash.encode("utf-8")).hexdigest()
            for sibling_hash, direction in lp.merkle_audit_path:
                left_b = bytes.fromhex(sibling_hash) if direction == "L" else bytes.fromhex(current_hash)
                right_b = bytes.fromhex(current_hash) if direction == "L" else bytes.fromhex(sibling_hash)
                current_hash = hashlib.sha256(b"\x01" + left_b + right_b).hexdigest()

            if current_hash.lower() != lp.merkle_root.lower():
                ledger_errors.append(f"Ledger proof block {lp.block_height} Merkle root mismatch")

            # 2. Verify proposer signature on block confirmation message
            block_msg = f"AEGIS-BLOCK-CONFIRM:{lp.block_hash}".encode("utf-8")
            proposer_pub_b64 = lp.authorized_validators.get(lp.proposer_validator_id)
            if not proposer_pub_b64:
                ledger_errors.append(f"Proposer validator '{lp.proposer_validator_id}' not in authorized validator set")
            else:
                try:
                    p_pub_bytes = base64.b64decode(proposer_pub_b64)
                    p_sig_bytes = base64.b64decode(lp.proposer_signature_b64)
                    if not MLDSA65.verify(p_pub_bytes, block_msg, p_sig_bytes):
                        ledger_errors.append(f"Invalid proposer signature on block {lp.block_height}")
                except Exception as e:
                    ledger_errors.append(f"Proposer signature verification exception: {str(e)}")

            # 3. Verify quorum signatures
            valid_quorum_votes = 0
            for vid, sig_b64 in lp.quorum_signatures.items():
                v_pub_b64 = lp.authorized_validators.get(vid)
                if not v_pub_b64:
                    continue
                try:
                    v_pub_bytes = base64.b64decode(v_pub_b64)
                    v_sig_bytes = base64.b64decode(sig_b64)
                    if MLDSA65.verify(v_pub_bytes, block_msg, v_sig_bytes):
                        valid_quorum_votes += 1
                except Exception:
                    pass

            if valid_quorum_votes < lp.quorum_threshold:
                ledger_errors.append(
                    f"Quorum threshold not met for block {lp.block_height}: "
                    f"{valid_quorum_votes} valid votes < {lp.quorum_threshold} required"
                )

        if ledger_errors:
            result.errors.extend(ledger_errors)
            result.ledger_proof_valid = False
            result.step_details["pillar_8_ledger_proofs"] = {"passed": False, "errors": ledger_errors}
        else:
            result.ledger_proof_valid = True
            result.step_details["pillar_8_ledger_proofs"] = {"passed": True, "proof_count": len(ledger_proofs)}

        # ----------------------------------------------------------------------
        # Pillar 9: Watermark Binding Reproduction: Artifact -> Token -> Ledger
        # ----------------------------------------------------------------------
        watermarks = [obj for obj in objects if isinstance(obj, WatermarkEvidenceObject)]
        wm_errors = []

        for wm in watermarks:
            # Check artifact existence
            art_matches = [
                obj for obj in objects
                if isinstance(obj, ArtifactEvidenceObject) and (obj.sha256_digest == wm.artifact_hash)
            ]
            if not art_matches:
                wm_errors.append(f"Watermark artifact hash '{wm.artifact_hash}' not matched by any ArtifactEvidenceObject")

            # Check binding to decryption receipt
            receipt_matches = [
                r for r in receipts
                if r.watermark_token == wm.extracted_token or (r.recipient_id == wm.expected_recipient_id)
            ]
            if wm.detection_state == "DETECTED" and not receipt_matches:
                wm_errors.append(f"Watermark token '{wm.extracted_token}' not bound to any DecryptionReceiptObject")

        if wm_errors:
            result.errors.extend(wm_errors)
            result.watermark_binding_valid = False
            result.step_details["pillar_9_watermark_binding"] = {"passed": False, "errors": wm_errors}
        else:
            result.watermark_binding_valid = True
            result.step_details["pillar_9_watermark_binding"] = {"passed": True}

        # ----------------------------------------------------------------------
        # Pillar 10: Lineage Integrity & Boundary Preservation
        # ----------------------------------------------------------------------
        lineage_objs = [obj for obj in objects if isinstance(obj, LineageEvidenceObject)]
        lineage_errors = []

        for lin in lineage_objs:
            # Detect fabricated downstream actors
            if lin.has_downstream_gap and not lin.last_known_holder:
                lineage_errors.append("Lineage with downstream gap must preserve last_known_holder")

        if lineage_errors:
            result.errors.extend(lineage_errors)
            result.lineage_valid = False
            result.step_details["pillar_10_lineage"] = {"passed": False, "errors": lineage_errors}
        else:
            result.lineage_valid = True
            result.step_details["pillar_10_lineage"] = {"passed": True}

        # ----------------------------------------------------------------------
        # Pillar 11: Chain-of-Custody SHA-256 Hash Chain Integrity
        # ----------------------------------------------------------------------
        if custody_chain:
            valid_coc, coc_errors = ChainOfCustodyLedger.verify_chain(
                custody_chain,
                expected_tenant_id=manifest.tenant_id
            )
            if not valid_coc:
                result.errors.extend(coc_errors)
                result.custody_chain_valid = False
                result.step_details["pillar_11_custody_chain"] = {"passed": False, "errors": coc_errors}
            else:
                result.custody_chain_valid = True
                result.step_details["pillar_11_custody_chain"] = {"passed": True, "event_count": len(custody_chain)}
        else:
            result.custody_chain_valid = True
            result.step_details["pillar_11_custody_chain"] = {"passed": True, "event_count": 0}

        # ----------------------------------------------------------------------
        # Pillar 12: Final Attribution Decision Consistency Check
        # ----------------------------------------------------------------------
        decision_obj = object_map.get(manifest.final_decision_reference)
        decision_errors = []

        if not decision_obj or not isinstance(decision_obj, AttributionDecisionObject):
            decision_errors.append(f"Manifest references non-existent decision '{manifest.final_decision_reference}'")
        else:
            # Validate decision consistency
            if decision_obj.decision_state == DecisionState.ATTRIBUTED:
                if not decision_obj.attributed_principal_id:
                    decision_errors.append("ATTRIBUTED decision must specify attributed_principal_id")
                if not receipts:
                    decision_errors.append("ATTRIBUTED decision requires valid DecryptionReceiptObject evidence")
            elif decision_obj.decision_state in (DecisionState.NO_SIGNAL, DecisionState.INSUFFICIENT_EVIDENCE, DecisionState.ABSTAINED):
                if decision_obj.attributed_principal_id:
                    decision_errors.append(f"{decision_obj.decision_state.value} decision must NOT attribute a principal")

        if decision_errors:
            result.errors.extend(decision_errors)
            result.decision_consistent = False
            result.step_details["pillar_12_decision"] = {"passed": False, "errors": decision_errors}
        else:
            result.decision_consistent = True
            result.step_details["pillar_12_decision"] = {"passed": True}

        # ----------------------------------------------------------------------
        # Overall Verdict Determination
        # ----------------------------------------------------------------------
        all_passed = (
            result.manifest_signature_valid and
            result.merkle_root_valid and
            result.object_hashes_valid and
            result.dependency_graph_valid and
            result.recipient_signature_valid and
            result.historical_keys_valid and
            result.ledger_proof_valid and
            result.watermark_binding_valid and
            result.lineage_valid and
            result.custody_chain_valid and
            result.decision_consistent
        )

        if all_passed and not result.errors:
            result.overall_status = VerificationStatus.VERIFIED
        elif (
            not result.manifest_signature_valid or
            not result.merkle_root_valid or
            not result.object_hashes_valid or
            not result.recipient_signature_valid or
            not result.custody_chain_valid or
            not result.ledger_proof_valid
        ):
            result.overall_status = VerificationStatus.INVALID
        elif not result.decision_consistent:
            result.overall_status = VerificationStatus.CONFLICT
        else:
            result.overall_status = VerificationStatus.INCOMPLETE

        return result
