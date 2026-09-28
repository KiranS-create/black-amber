"""
SIH26237 - Decryption-Time Watermark Physical Trial Engine
Executes genuine broadcast-encrypt / individual-decrypt workflow across enrolled recipients:
1. Sender encrypts canonical golden document using AES-256-GCM + ML-KEM-768 per recipient.
2. Recipient decrypts locally in volatile memory.
3. Decryption-time dynamic watermark (DSSS + RS ECC + ArUco fiducials) embedded into canvas.
4. Recipient signs DecryptionReceipt with private ML-DSA-65 key.
5. Receipt committed to offline permissioned DLT ledger.
6. Rendered physical artifact produced with full cryptographic bindings.
"""

from typing import List, Dict, Any, Tuple, Optional
import hashlib
import base64
from pydantic import BaseModel, Field
import numpy as np

from core.crypto.kem import MLKEM768
from core.crypto.signatures import MLDSA65
from core.recipient import RecipientRegistry, Recipient
from core.release import ReleaseManager, DocumentRelease
from core.provenance.decryption import RecipientDecryptionClient
from core.ledger.dlt import PermissionedDLTLedger, DecryptionReceipt
from core.watermark.pipeline import CanonicalCanvasSpec, GeometricSynchronizer
from core.watermark.dynamic import DynamicWatermarkEngine
from core.physical.golden_source import GoldenPhysicalSourceBuilder, GoldenSourceSpecification


class PhysicalTrialSessionRecord(BaseModel):
    """Cryptographic audit record of a single physical trial decryption session."""
    trial_id: str
    recipient_id: str
    recipient_name: str
    document_id: str
    release_id: str
    session_id: str
    watermark_commitment: str
    receipt_hash: str
    recipient_signature_hex: str
    dlt_block_height: int
    rendered_artifact_hash: str
    codeword_bits: List[int]
    timestamp: str
    epistemic_tag: str = "PHYSICAL_TRIAL"


class PhysicalTrialEngine:
    """
    Coordinates multi-recipient decryption, watermark embedding, and DLT commitment
    for authentic physical laboratory validation trials.
    """

    def __init__(
        self,
        document_id: str = "DOC_PHYSICAL_GOLDEN_2026",
        canvas_spec: Optional[CanonicalCanvasSpec] = None
    ):
        self.document_id = document_id
        self.canvas_spec = canvas_spec or CanonicalCanvasSpec(width=800, height=1000)
        self.registry = RecipientRegistry()
        self.ledger = PermissionedDLTLedger()
        self.release_manager = ReleaseManager(registry=self.registry)
        self.watermark_engine = DynamicWatermarkEngine(canvas_spec=self.canvas_spec)
        self.decryption_client = RecipientDecryptionClient(
            dlt_ledger=self.ledger,
            dynamic_wm_engine=self.watermark_engine
        )

        self._enrolled_recipients: Dict[str, Recipient] = {}

    def setup_standard_laboratory_recipients(self) -> List[Recipient]:
        """Enrolls standard test cohort: Alice, Bob, Charlie."""
        identities = [
            ("rec_alice", "Alice Vance", "Security Directorate"),
            ("rec_bob", "Bob Martinez", "Intelligence Analysis"),
            ("rec_charlie", "Charlie Chen", "Forensic Operations"),
        ]

        enrolled = []
        for r_id, name, dept in identities:
            rec = self.registry.enroll(
                name=name,
                recipient_id=r_id,
                email=f"{r_id}@agency.internal",
                organization_id=dept
            )
            self._enrolled_recipients[r_id] = rec
            enrolled.append(rec)
        return enrolled

    def execute_decryption_and_render_artifact(
        self,
        recipient_id: str,
        session_id: Optional[str] = None
    ) -> Tuple[np.ndarray, PhysicalTrialSessionRecord]:
        """
        Executes full broadcast encryption -> individual decryption -> watermark embedding -> DLT commit.
        """
        if recipient_id not in self._enrolled_recipients:
            raise ValueError(f"Recipient {recipient_id} is not enrolled in trial registry.")

        recipient = self._enrolled_recipients[recipient_id]

        # 1. Render Canonical Golden Document
        golden_canvas, golden_spec = GoldenPhysicalSourceBuilder.render_canonical_canvas(
            spec=self.canvas_spec,
            document_id=self.document_id
        )
        payload_bytes = golden_canvas.tobytes()

        # 2. Release Manager creates broadcast release
        recipient_ids = list(self._enrolled_recipients.keys())
        release = self.release_manager.create_release(
            document_bytes=payload_bytes,
            document_name=f"{self.document_id}.raw",
            issuer_id="LAB_ISSUER",
            recipient_ids=recipient_ids,
            document_id=self.document_id,
        )

        package = release.packages[recipient_id]

        # 3. Recipient Client executes decapsulation, decryption, watermark embedding, and DLT signing
        sid = session_id or f"ses_phys_{hashlib.sha256(recipient_id.encode()).hexdigest()[:8]}"
        (
            plaintext_bytes,
            wm_bytes,
            dynamic_identity,
            receipt,
            dlt_block
        ) = self.decryption_client.decrypt_with_dynamic_watermark(
            package=package,
            recipient=recipient,
            session_id=sid,
            record_to_dlt=True
        )

        # 4. In-memory Dynamic Watermarking on Canvas for Optical Rendering
        rendered_canvas = self.watermark_engine.embed_watermark(
            carrier_input=golden_canvas,
            dynamic_identity=dynamic_identity,
            document_id=self.document_id,
            release_id=release.release_id,
            as_bytes=False,
        )

        rendered_hash = hashlib.sha256(rendered_canvas.tobytes()).hexdigest()
        block_height = dlt_block.header.block_height if dlt_block else (self.ledger.get_current_height() or 0)

        # Decode signature bytes from base64
        sig_bytes = base64.b64decode(receipt.recipient_signature_b64) if receipt.recipient_signature_b64 else b""

        session_record = PhysicalTrialSessionRecord(
            trial_id=f"trial_{recipient_id}_{sid[:8]}",
            recipient_id=recipient_id,
            recipient_name=recipient.name,
            document_id=self.document_id,
            release_id=release.release_id,
            session_id=sid,
            watermark_commitment=dynamic_identity.commitment,
            receipt_hash=hashlib.sha256(receipt.canonical_payload_bytes()).hexdigest(),
            recipient_signature_hex=sig_bytes.hex(),
            dlt_block_height=block_height,
            rendered_artifact_hash=rendered_hash,
            codeword_bits=dynamic_identity.codeword,
            timestamp=receipt.timestamp,
        )

        return rendered_canvas, session_record
