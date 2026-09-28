"""
AegisTrace Blind Forensic Evaluator.

Executes blind forensic investigations where the target recipient identity,
watermark token, session ID, and decryption event are strictly UNKNOWN to the engine.
The attribution emerges strictly from cryptographic and signal evidence extracted
from the leak artifact and correlated against the immutable DLT ledger.
"""

import hashlib
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field

from core.provenance.decryption import DecryptionReceipt
from core.watermark.dynamic import DynamicWatermarkEngine, derive_dynamic_codeword
from core.ledger.dlt import PermissionedDLTLedger
from core.lineage.scale import SparseLineageIndex
from core.evidence_package.models import DecisionState


class BlindEvaluationResult(BaseModel):
    """Result of a blind forensic evaluation."""
    artifact_hash: str
    watermark_detected: bool
    extracted_token: Optional[str] = None
    extracted_codeword: Optional[List[int]] = None
    confidence_score: float = 0.0
    matched_receipt_id: Optional[str] = None
    attributed_recipient_id: Optional[str] = None
    decision_state: DecisionState
    is_signature_valid: bool = False
    is_ledger_inclusion_valid: bool = False
    last_known_holder: Optional[str] = None
    reason_codes: List[str] = Field(default_factory=list)
    telemetry_summary: Dict[str, Any] = Field(default_factory=dict)


class BlindForensicEvaluator:
    """
    Independent blind investigation engine.
    Does NOT accept ground truth shortcuts (no recipient_id, expected_token, or event_id).
    """

    def __init__(
        self,
        dlt_ledger: PermissionedDLTLedger,
        lineage_index: Optional[SparseLineageIndex] = None,
        watermark_engine: Optional[DynamicWatermarkEngine] = None,
        expected_tenant_id: Optional[str] = None,
    ):
        self.dlt_ledger = dlt_ledger
        self.lineage_index = lineage_index
        self.watermark_engine = watermark_engine or DynamicWatermarkEngine()
        self.expected_tenant_id = expected_tenant_id

    def evaluate_artifact(
        self,
        artifact_bytes: bytes,
        document_id: Optional[str] = None,
        release_id: Optional[str] = None,
    ) -> BlindEvaluationResult:
        """
        Performs blind extraction, ledger lookup, signature verification, and attribution.
        """
        artifact_hash = hashlib.sha256(artifact_bytes).hexdigest()
        reason_codes: List[str] = []

        # 1. Blind watermark decode
        is_recovered, observed_symbols, telemetry = self.watermark_engine.decode_watermark(
            captured_input=artifact_bytes,
            expected_document_id=document_id,
            expected_release_id=release_id,
            expected_codeword_length=128,
        )

        matched_receipt: Optional[DecryptionReceipt] = None
        best_match_ratio = 0.0
        primary_node = list(self.dlt_ledger.nodes.values())[0]

        # 2. Search DLT Ledger index across all committed receipts
        if observed_symbols:
            for r_id, receipt in primary_node.receipts.items():
                if self.expected_tenant_id:
                    rec_tenant = receipt.metadata.get("tenant_id")
                    if rec_tenant and rec_tenant != self.expected_tenant_id:
                        continue

                if receipt.watermark_token:
                    ref_cw = derive_dynamic_codeword(receipt.watermark_token, length=128)
                    if len(observed_symbols) == len(ref_cw):
                        matches = sum(1 for a, b in zip(observed_symbols, ref_cw) if a == b)
                        ratio = matches / len(ref_cw)
                        if ratio > best_match_ratio:
                            best_match_ratio = ratio
                            if ratio >= 0.85:
                                matched_receipt = receipt

        # Secondary match: byte containment of dynamic commitment/token in digital payload
        if not matched_receipt:
            for r_id, receipt in primary_node.receipts.items():
                if self.expected_tenant_id:
                    rec_tenant = receipt.metadata.get("tenant_id")
                    if rec_tenant and rec_tenant != self.expected_tenant_id:
                        continue

                if receipt.watermark_commitment and receipt.watermark_commitment.encode('utf-8') in artifact_bytes:
                    matched_receipt = receipt
                    best_match_ratio = 1.0
                    break
                if receipt.watermark_token and receipt.watermark_token.encode('utf-8') in artifact_bytes:
                    matched_receipt = receipt
                    best_match_ratio = 1.0
                    break

        if not matched_receipt:
            if not is_recovered and not observed_symbols:
                return BlindEvaluationResult(
                    artifact_hash=artifact_hash,
                    watermark_detected=False,
                    decision_state=DecisionState.NO_SIGNAL,
                    attributed_recipient_id=None,
                    reason_codes=["WATERMARK_NO_SIGNAL_FOUND"]
                )
            else:
                return BlindEvaluationResult(
                    artifact_hash=artifact_hash,
                    watermark_detected=True,
                    extracted_codeword=observed_symbols,
                    confidence_score=float(best_match_ratio),
                    decision_state=DecisionState.INSUFFICIENT_EVIDENCE,
                    attributed_recipient_id=None,
                    reason_codes=["NO_MATCHING_DLT_RECEIPT_CORRELATION"]
                )

        reason_codes.append("WATERMARK_CORRELATED_WITH_DLT_RECEIPT")

        # 3. Cryptographic Verification of Recipient ML-DSA-65 Signature
        sig_valid = matched_receipt.verify_recipient_signature()
        if not sig_valid:
            return BlindEvaluationResult(
                artifact_hash=artifact_hash,
                watermark_detected=True,
                extracted_token=matched_receipt.watermark_token,
                confidence_score=float(best_match_ratio),
                matched_receipt_id=matched_receipt.receipt_id,
                attributed_recipient_id=None,
                decision_state=DecisionState.CONFLICT,
                is_signature_valid=False,
                reason_codes=["RECIPIENT_MLDSA_SIGNATURE_INVALID"]
            )
        reason_codes.append("RECIPIENT_MLDSA_SIGNATURE_VALIDATED")

        # 4. Merkle Inclusion in DLT Block
        merkle_proof = primary_node.get_merkle_proof(matched_receipt.receipt_id)
        inclusion_valid = merkle_proof.verify() if merkle_proof else False
        if not inclusion_valid:
            return BlindEvaluationResult(
                artifact_hash=artifact_hash,
                watermark_detected=True,
                extracted_token=matched_receipt.watermark_token,
                confidence_score=float(best_match_ratio),
                matched_receipt_id=matched_receipt.receipt_id,
                attributed_recipient_id=None,
                decision_state=DecisionState.CONFLICT,
                is_signature_valid=True,
                is_ledger_inclusion_valid=False,
                reason_codes=["DLT_MERKLE_INCLUSION_PROOF_FAILED"]
            )
        reason_codes.append("DLT_MERKLE_INCLUSION_VERIFIED")

        # 5. Lineage Check
        last_known = matched_receipt.recipient_id
        if self.lineage_index:
            node = self.lineage_index.get_node(matched_receipt.copy_instance_id)
            if node:
                last_known = node.recipient_id

        return BlindEvaluationResult(
            artifact_hash=artifact_hash,
            watermark_detected=True,
            extracted_token=matched_receipt.watermark_token,
            extracted_codeword=observed_symbols or derive_dynamic_codeword(matched_receipt.watermark_token or "0"*64, 128),
            confidence_score=float(best_match_ratio),
            matched_receipt_id=matched_receipt.receipt_id,
            attributed_recipient_id=matched_receipt.recipient_id,
            decision_state=DecisionState.ATTRIBUTED,
            is_signature_valid=True,
            is_ledger_inclusion_valid=True,
            last_known_holder=last_known,
            reason_codes=reason_codes,
            telemetry_summary=telemetry
        )
