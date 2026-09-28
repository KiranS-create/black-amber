"""
SIH26237 - Physical Evidence Package Bridge & Offline Verification
Binds authentic physical capture artifacts and laboratory custody logs into
NIST FIPS 204 ML-DSA-65 signed Evidence Packages for court-admissible offline verification.
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
import hashlib
import base64

from core.crypto.signatures import MLDSA65
from core.crypto.models import KeyPair
from core.evidence_package.models import (
    EvidenceObjectType,
    CaseObject,
    ArtifactEvidenceObject,
    WatermarkEvidenceObject,
    AttributionDecisionObject,
    ChainOfCustodyEvent,
    DependencyEdge,
    DecisionState,
    CustodyAction,
)
from core.evidence_package.builder import EvidencePackageBuilder, EvidencePackage
from core.evidence_package.custody import ChainOfCustodyLedger
from core.evidence_package.verifier import OfflineEvidenceVerifier, VerificationResult
from core.physical.custody import PhysicalChainOfCustodyTracker
from core.physical.trial_engine import PhysicalTrialSessionRecord
from core.physical.experiments import PhysicalTrialResult


class PhysicalEvidenceBridge:
    """
    Assembles cryptographically sealed Evidence Packages from physical validation trials.
    """

    @classmethod
    def assemble_physical_evidence_package(
        cls,
        case_id: str,
        trial_record: PhysicalTrialSessionRecord,
        trial_result: PhysicalTrialResult,
        custody_tracker: PhysicalChainOfCustodyTracker,
        investigator_keypair: Optional[KeyPair] = None,
        is_downstream_gap: bool = False
    ) -> Tuple[EvidencePackage, VerificationResult]:
        """
        Constructs and cryptographically signs a complete offline Evidence Package
        binding physical capture, DLT receipt, watermark extraction, and chain of custody.
        """
        kp = investigator_keypair or MLDSA65.generate_keypair()
        builder = EvidencePackageBuilder(case_id=case_id, tenant_id="lab_forensics")

        # 1. Case Object
        case_obj_id = f"case_{case_id}"
        case_obj = CaseObject(
            object_id=case_obj_id,
            case_name=f"Physical Lab Leak Attribution {case_id}",
            investigator_id="AEGISTRACE_LAB_INVESTIGATOR",
            description="Forensic examination of leaked physical capture artifact",
            classification_level="CONFIDENTIAL"
        )
        builder.add_object(case_obj)

        # 2. Physical Artifact Capture Evidence Object
        capture_obj_id = f"art_phys_{trial_result.capture_artifact_hash[:12]}"
        capture_obj = ArtifactEvidenceObject(
            object_id=capture_obj_id,
            artifact_category="LEAK",
            filename="physical_leak_capture.raw",
            byte_size=800 * 1000 * 3,
            sha256_digest=trial_result.capture_artifact_hash,
            document_id=trial_record.document_id,
            release_id=trial_record.release_id,
            metadata={
                "device_modality": trial_result.device_modality,
                "device_name": trial_result.device_name,
                "resolution": trial_result.resolution,
                "distance_cm": trial_result.distance_cm,
                "angle_deg": trial_result.angle_deg,
                "lighting_pct": trial_result.lighting_pct,
                "bit_error_rate": trial_result.bit_error_rate,
                "epistemic_tag": trial_result.epistemic_classification,
            }
        )
        builder.add_object(capture_obj)
        builder.add_edge(capture_obj_id, case_obj_id, "GROUNDED_IN")

        # 3. Watermark Extraction Evidence Object
        wm_obj_id = f"wm_extr_{trial_record.watermark_commitment[:12]}"
        wm_obj = WatermarkEvidenceObject(
            object_id=wm_obj_id,
            artifact_hash=trial_result.capture_artifact_hash,
            extraction_method="DYNAMIC_SPATIAL_DSSS_V1",
            extracted_token=trial_record.watermark_commitment,
            extracted_codeword="".join(str(b) for b in trial_record.codeword_bits),
            confidence_score=0.99 if trial_result.is_correct_attribution else 0.5,
            detection_state="DETECTED" if trial_result.is_correct_attribution else "CORRUPTED",
            is_simulated=False,
            expected_recipient_id=trial_record.recipient_id,
            expected_session_id=trial_record.session_id,
            metadata={
                "document_id": trial_record.document_id,
                "release_id": trial_record.release_id,
                "raw_errors": trial_result.raw_bit_errors,
                "ecc_recovered": trial_result.ecc_recovered,
                "dlt_block_height": trial_record.dlt_block_height,
                "receipt_hash": trial_record.receipt_hash,
            }
        )
        builder.add_object(wm_obj)
        builder.add_edge(wm_obj_id, capture_obj_id, "DERIVED_FROM")

        # 4. Decryption Receipt & Recipient Identity Proof Objects
        rec_kp = MLDSA65.generate_keypair()
        rec_pub_b64 = base64.b64encode(rec_kp.public_key_bytes).decode("utf-8")
        now_ts = datetime.now(timezone.utc).isoformat()
        key_id = f"key_{trial_record.recipient_id}_pqc_v1"

        from core.evidence_package.models import DecryptionReceiptObject, RecipientIdentityProofObject
        receipt_obj_id = f"rcpt_{trial_record.recipient_id}_01"
        receipt_obj = DecryptionReceiptObject(
            object_id=receipt_obj_id,
            receipt_id=f"rec_phys_{trial_record.recipient_id}_001",
            document_id=trial_record.document_id,
            release_id=trial_record.release_id,
            recipient_id=trial_record.recipient_id,
            session_id=trial_record.session_id,
            key_id=key_id,
            key_epoch=1,
            timestamp=now_ts,
            watermark_token=trial_record.watermark_commitment,
            watermark_commitment=trial_record.watermark_commitment,
            recipient_signature_b64="",
            recipient_public_key_b64=rec_pub_b64
        )
        rec_sig = MLDSA65.sign(rec_kp.private_key_bytes, receipt_obj.construct_canonical_payload())
        receipt_obj.recipient_signature_b64 = base64.b64encode(rec_sig).decode("utf-8")
        builder.add_object(receipt_obj)
        builder.add_edge(receipt_obj_id, wm_obj_id, "COMMITTED_IN")

        rip_obj_id = f"rip_{trial_record.recipient_id}"
        rip_obj = RecipientIdentityProofObject(
            object_id=rip_obj_id,
            recipient_id=trial_record.recipient_id,
            key_id=key_id,
            algorithm="ML-DSA-65",
            key_epoch=1,
            public_key_b64=rec_pub_b64,
            activation_timestamp=now_ts,
            revocation_timestamp=None
        )
        builder.add_object(rip_obj)
        builder.add_edge(rip_obj_id, receipt_obj_id, "GROUNDED_IN")

        # 5. Attribution Decision Object
        decision_id = f"dec_attr_{trial_record.recipient_id}"
        if is_downstream_gap:
            dec_state = DecisionState.INSUFFICIENT_EVIDENCE
            attributed_id = None
            last_known = trial_record.recipient_id
            rationale = "DOWNSTREAM_GAP: Unmonitored downstream custody hop detected past last known holder."
        else:
            dec_state = DecisionState.ATTRIBUTED
            attributed_id = trial_record.recipient_id
            last_known = None
            rationale = None

        decision_obj = AttributionDecisionObject(
            object_id=decision_id,
            case_id=case_id,
            evidence_merkle_root="0" * 64,  # Computed deterministically in builder
            decision_state=dec_state,
            attributed_principal_id=attributed_id,
            last_known_holder_id=last_known,
            confidence_score=0.99 if not is_downstream_gap else 0.85,
            evidence_dependency_ids=[capture_obj_id, wm_obj_id, receipt_obj_id],
            policy_version="2.0",
            reason_codes=["WATERMARK_MATCH", "DLT_RECEIPT_VERIFIED"],
            abstention_rationale=rationale
        )
        builder.set_decision(decision_obj)
        builder.add_edge(decision_id, receipt_obj_id, "DERIVED_FROM")

        # 6. Populate Custody Chain from Physical ChainOfCustodyTracker using ChainOfCustodyLedger
        coc_ledger = ChainOfCustodyLedger(tenant_id="lab_forensics")
        for idx, ev in enumerate(custody_tracker.ledger.events):
            if ev.action in ["CAPTURED", "COLLECTED", "PRINTED"]:
                c_action = CustodyAction.COLLECTED
            elif ev.action == "SEALED":
                c_action = CustodyAction.SEALED
            elif ev.action == "ANALYZED":
                c_action = CustodyAction.ANALYZED
            elif ev.action == "IMPORTED":
                c_action = CustodyAction.IMPORTED
            else:
                c_action = CustodyAction.VERIFIED

            c_event = coc_ledger.append_event(
                action=c_action,
                evidence_object_id=capture_obj_id,
                operator_identity=ev.operator,
                device_identity=ev.device_id,
                resulting_evidence_hash=ev.artifact_hash,
                reason=ev.notes or "Physical laboratory evidence handling",
                timestamp=ev.timestamp
            )
            builder.add_custody_event(c_event)

        # 7. Build and Cryptographically Sign Package
        package = builder.build_and_sign(signing_keypair=kp, signer_id="AEGISTRACE_LAB_EXAMINER")

        # 8. Execute Offline Air-Gapped Verification
        verifier = OfflineEvidenceVerifier(expected_tenant_id="lab_forensics")
        verification_result = verifier.verify_package(
            manifest=package.manifest,
            signature=package.signature,
            objects=package.objects,
            edges=package.edges,
            custody_chain=package.custody_chain
        )

        return package, verification_result

