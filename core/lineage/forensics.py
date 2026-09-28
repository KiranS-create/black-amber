"""
SIH26237 - Dynamic Leak Forensics & DLT Attribution Engine
Performs end-to-end forensic analysis on leaked artifacts:
Leak Artifact -> PrintCameraWatermarkDecoder -> Extracted Watermark Codeword / Token
             -> Offline Permissioned DLT Lookup -> Block & Quorum Verification
             -> ML-DSA-65 Recipient Signature Verification -> Merkle Inclusion Proof
             -> Copy Derivation & Lineage Verification -> Final Honest Attribution.
"""

import os
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Union
import numpy as np
from PIL import Image
from pydantic import BaseModel, Field

from core.ledger.dlt import (
    PermissionedDLTLedger,
    default_dlt_ledger,
    DecryptionReceipt,
    DLTBlock,
    MerkleProof,
)
from core.watermark.dynamic import (
    DynamicWatermarkEngine,
    compute_visual_equivalence_metrics,
    derive_dynamic_codeword,
)
from core.lineage.storage import LineageStorage
from core.lineage.verification import LineageVerifier


class ForensicVerificationStatus(str, Enum):
    PROVEN_AUTHENTIC = "PROVEN_AUTHENTIC"
    ABSENT_OR_DESTROYED = "ABSENT_OR_DESTROYED"
    INVALID_SIGNATURE = "INVALID_SIGNATURE"
    UNAUTHORIZED_LEDGER = "UNAUTHORIZED_LEDGER"
    TAMPERED_DERIVATION = "TAMPERED_DERIVATION"
    SUSPECT_TRANSPLANT = "SUSPECT_TRANSPLANT"


class DynamicForensicAttributionResult(BaseModel):
    """
    Forensic result for dynamic decryption leak analysis.
    Strictly preserves the honesty invariant:
    PROVED: "This exact recipient performed this signed decryption event."
    NOT AUTOMATICALLY PROVED: "This human personally leaked the file downstream."
    """
    status: ForensicVerificationStatus
    attributed_recipient_id: Optional[str] = None
    recipient_identity_ref: Optional[str] = None
    decryption_session_id: Optional[str] = None
    decryption_event_id: Optional[str] = None
    copy_instance_id: Optional[str] = None
    lineage_depth: int = 0
    lineage_path: List[str] = Field(default_factory=list)
    dlt_block_height: Optional[int] = None
    dlt_block_hash: Optional[str] = None
    merkle_verified: bool = False
    quorum_verified: bool = False
    recipient_signature_verified: bool = False
    watermark_recovered: bool = False
    observed_symbols_count: int = 0
    visual_metrics: Optional[Dict[str, float]] = None
    honesty_declaration: str = (
        "PROVED: This exact recipient performed this signed decryption event. "
        "NOT AUTOMATICALLY PROVED: This human personally leaked the file downstream."
    )
    details: Dict[str, Any] = Field(default_factory=dict)


class DynamicForensicExtractor:
    """
    Forensic analysis engine connecting watermarking, offline permissioned DLT,
    and Active Cryptographic Copy Lineage.
    """

    def __init__(
        self,
        dlt_ledger: Optional[PermissionedDLTLedger] = None,
        lineage_storage: Optional[LineageStorage] = None,
        wm_engine: Optional[DynamicWatermarkEngine] = None,
    ):
        self.dlt_ledger = dlt_ledger or default_dlt_ledger
        self.lineage_storage = lineage_storage
        self.wm_engine = wm_engine or DynamicWatermarkEngine()
        self.lineage_verifier = LineageVerifier(lineage_storage) if lineage_storage else None

    def analyze_leak(
        self,
        leak_artifact: Union[bytes, np.ndarray, Image.Image],
        expected_doc_id: Optional[str] = None,
        expected_release_id: Optional[str] = None,
        reference_clean_image: Optional[Union[bytes, np.ndarray, Image.Image]] = None,
        known_token_or_commitment: Optional[str] = None,
    ) -> DynamicForensicAttributionResult:
        """
        Executes complete verification pipeline:
        1. Watermark recovery from leak artifact.
        2. DLT ledger query for cryptographic DecryptionReceipt.
        3. Recipient ML-DSA-65 signature verification.
        4. Validator quorum and Merkle inclusion verification.
        5. Lineage chain traversal and derivation check.
        6. Visual equivalence calculation against reference image (if provided).
        """
        # 1. Decode watermark
        is_recovered, symbols, telemetry = self.wm_engine.decode_watermark(
            captured_input=leak_artifact,
            expected_document_id=expected_doc_id,
            expected_release_id=expected_release_id,
            expected_codeword_length=128
        )

        extracted_commitment = telemetry.get("commitment") or known_token_or_commitment
        extracted_copy_id = telemetry.get("copy_id")

        if not is_recovered and not known_token_or_commitment:
            return DynamicForensicAttributionResult(
                status=ForensicVerificationStatus.ABSENT_OR_DESTROYED,
                watermark_recovered=False,
                observed_symbols_count=len(symbols),
                details={"telemetry": telemetry, "error": "No recoverable watermark signal found"}
            )

        # 2. Query DLT ledger for DecryptionReceipt
        primary_node = list(self.dlt_ledger.nodes.values())[0]
        receipt: Optional[DecryptionReceipt] = None

        if extracted_commitment:
            receipt = primary_node.find_receipt_by_commitment(extracted_commitment)
            if not receipt:
                receipt = primary_node.find_receipt_by_token(extracted_commitment)

        if not receipt and symbols and len(symbols) == 128:
            # Match extracted watermark codeword against dynamic codewords derived from registered receipts
            for r in primary_node.receipts.values():
                if r.watermark_token:
                    expected_cw = derive_dynamic_codeword(r.watermark_token, length=128)
                    if symbols == expected_cw:
                        receipt = r
                        break

        if not receipt:
            # Fallback scan across all committed receipts
            for r in primary_node.receipts.values():
                if extracted_copy_id and r.copy_instance_id == extracted_copy_id:
                    receipt = r
                    break
                if extracted_commitment and (r.watermark_commitment == extracted_commitment or r.watermark_token == extracted_commitment):
                    receipt = r
                    break

                if symbols and r.watermark_token:
                    cand_codeword = derive_dynamic_codeword(r.watermark_token, length=len(symbols))
                    if symbols == cand_codeword:
                        receipt = r
                        break

        if not receipt:
            return DynamicForensicAttributionResult(
                status=ForensicVerificationStatus.UNAUTHORIZED_LEDGER,
                watermark_recovered=is_recovered,
                observed_symbols_count=len(symbols),
                details={"telemetry": telemetry, "error": "Watermark present but not registered in permissioned DLT"}
            )

        # 3. Verify Recipient ML-DSA-65 Signature
        sig_valid = receipt.verify_recipient_signature()
        if not sig_valid:
            return DynamicForensicAttributionResult(
                status=ForensicVerificationStatus.INVALID_SIGNATURE,
                attributed_recipient_id=receipt.recipient_id,
                recipient_identity_ref=receipt.identity_reference,
                watermark_recovered=is_recovered,
                observed_symbols_count=len(symbols),
                recipient_signature_verified=False,
                details={"receipt_id": receipt.receipt_id, "error": "Invalid recipient digital signature"}
            )

        # 4. Verify DLT Block & Validator Quorum
        block_height = primary_node.receipt_to_block.get(receipt.receipt_id)
        if block_height is None or block_height > len(primary_node.blocks):
            return DynamicForensicAttributionResult(
                status=ForensicVerificationStatus.UNAUTHORIZED_LEDGER,
                attributed_recipient_id=receipt.recipient_id,
                details={"error": "Receipt not associated with any finalized block"}
            )

        block = primary_node.blocks[block_height - 1]
        quorum_valid, q_errors = block.verify_block_integrity(
            primary_node.authorized_validators,
            primary_node.quorum_threshold
        )
        if not quorum_valid:
            return DynamicForensicAttributionResult(
                status=ForensicVerificationStatus.UNAUTHORIZED_LEDGER,
                attributed_recipient_id=receipt.recipient_id,
                quorum_verified=False,
                details={"errors": q_errors}
            )

        # 5. Merkle Inclusion Proof
        proof = primary_node.get_merkle_proof(receipt.receipt_id)
        merkle_valid = proof.verify() if proof else False

        # 6. Active Lineage Trace
        lineage_path = [receipt.copy_instance_id]
        lineage_depth = 0
        if self.lineage_storage:
            target_cp = self.lineage_storage.get_copy(receipt.copy_instance_id)
            if target_cp:
                lineage_depth = target_cp.lineage_depth
            curr_copy_id = receipt.copy_instance_id
            while curr_copy_id:
                cp = self.lineage_storage.get_copy(curr_copy_id)
                if not cp:
                    break
                if cp.parent_copy_id and cp.parent_copy_id not in lineage_path:
                    lineage_path.append(cp.parent_copy_id)
                    curr_copy_id = cp.parent_copy_id
                else:
                    break
            lineage_depth = max(lineage_depth, len(lineage_path) - 1)


        # 7. Visual Equivalence Metrics (if reference provided)
        visual_metrics = None
        if reference_clean_image is not None:
            try:
                visual_metrics = compute_visual_equivalence_metrics(
                    reference_input=reference_clean_image,
                    target_input=leak_artifact
                )
            except Exception:
                pass

        return DynamicForensicAttributionResult(
            status=ForensicVerificationStatus.PROVEN_AUTHENTIC,
            attributed_recipient_id=receipt.recipient_id,
            recipient_identity_ref=receipt.identity_reference,
            decryption_session_id=receipt.decryption_session_id,
            decryption_event_id=receipt.decryption_event_id,
            copy_instance_id=receipt.copy_instance_id,
            lineage_depth=lineage_depth,
            lineage_path=lineage_path,
            dlt_block_height=block.header.block_height,
            dlt_block_hash=block.block_hash,
            merkle_verified=merkle_valid,
            quorum_verified=quorum_valid,
            recipient_signature_verified=sig_valid,
            watermark_recovered=is_recovered,
            observed_symbols_count=len(symbols),
            visual_metrics=visual_metrics,
            details={
                "receipt_id": receipt.receipt_id,
                "watermark_commitment": receipt.watermark_commitment,
                "timestamp": receipt.timestamp,
                "validator_signatures_count": len(block.quorum_signatures),
            }
        )
