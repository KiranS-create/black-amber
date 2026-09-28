"""
SIH26237 - Controlled Viewer Boundary
Implements the secure viewer environment that enforces:
- In-memory document decryption inside active session window
- Dynamic session watermarking / pseudonymous overlay (sf_...)
- Mandatory re-fingerprinting on export / print / save actions
- Transition receipt generation linking exported artifacts to child copies
"""

import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone

from core.crypto.symmetric import (
    generate_symmetric_key,
    encrypt_aes_gcm,
    decrypt_aes_gcm,
)
from core.crypto.models import SymmetricCiphertext
from core.crypto.signatures import MLDSA65
import base64
import hashlib
from core.lineage.models import (
    CopyInstance,
    AccessSession,
    ExportFormat,
    ExportEvent,
    LineageEdge,
)
from core.lineage.service import LineageService
from core.ledger.dlt import (
    PermissionedDLTLedger,
    default_dlt_ledger,
    DecryptionReceipt,
    DLTBlock,
)
from core.watermark.dynamic import (
    DynamicWatermarkEngine,
    generate_dynamic_watermark,
    DynamicWatermarkIdentity,
)
from core.provenance.decryption import (
    RecipientDecryptionClient,
    default_decryption_client,
)
from core.recipient import Recipient
from core.release import ReleaseRecipientPackage


class ControlledViewer:
    """
    Controlled rendering and interaction boundary.
    Prevents unmonitored plain artifact leakage by:
    1. Requiring an active cryptographic AccessSession for in-memory rendering.
    2. Dynamically compositing session watermark markers (sf_...).
    3. Intercepting export/print actions to generate derivative child copies
       with fresh fingerprint material before generating the exported bytes.
    4. Committing recipient ML-DSA-65 signed DecryptionReceipts to offline permissioned DLT.
    """

    def __init__(
        self,
        lineage_service: LineageService,
        dlt_ledger: Optional[PermissionedDLTLedger] = None,
        dynamic_wm_engine: Optional[DynamicWatermarkEngine] = None,
        decryption_client: Optional[RecipientDecryptionClient] = None,
    ):
        self.lineage_service = lineage_service
        self.dlt_ledger = dlt_ledger or default_dlt_ledger
        self.dynamic_wm_engine = dynamic_wm_engine or DynamicWatermarkEngine()
        self.decryption_client = decryption_client or default_decryption_client
        self._document_store: Dict[str, SymmetricCiphertext] = {}  # doc_id -> ciphertext
        self._encryption_keys: Dict[str, bytes] = {}  # doc_id -> 256-bit AES key
        self._session_decryptions: Dict[str, DecryptionReceipt] = {}  # session_id -> DecryptionReceipt

    def register_master_document(self, document_id: str, document_bytes: bytes) -> bytes:
        """
        Encrypts and stores master document at rest using AES-256-GCM.
        Returns packed ciphertext (nonce || tag || ciphertext).
        """
        key = generate_symmetric_key()
        encrypted = encrypt_aes_gcm(
            key=key,
            plaintext=document_bytes,
            associated_data=document_id.encode('utf-8')
        )
        self._document_store[document_id] = encrypted
        self._encryption_keys[document_id] = key
        return encrypted.nonce + encrypted.tag + encrypted.ciphertext

    def open_session_from_package(
        self,
        package: ReleaseRecipientPackage,
        recipient: Recipient,
        device_key_id: Optional[str] = None,
        expires_in_seconds: int = 3600,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[AccessSession, DecryptionReceipt, Optional[DLTBlock]]:
        """
        Decrypts broadcast release package directly with recipient's ML-KEM private key,
        generates recipient ML-DSA-65 signed DecryptionReceipt, commits to replicated DLT,
        initializes root copy in lineage graph if needed, and starts an active AccessSession.
        """
        # Recipient-side decryption & provenance
        plaintext, _, dyn_id, receipt, dlt_block = self.decryption_client.decrypt_with_dynamic_watermark(
            package=package,
            recipient=recipient,
            record_to_dlt=True,
        )

        doc_id = package.document_id
        # Store encrypted at rest inside viewer memory
        self.register_master_document(doc_id, plaintext)

        # Ensure root copy exists
        root = self.lineage_service.storage.get_document_root(doc_id)
        if not root:
            root = self.lineage_service.create_document_root(
                document_bytes=plaintext,
                document_id=doc_id,
                metadata={"release_id": package.release_id}
            )

        # Issue or locate root copy for this recipient
        copies = self.lineage_service.storage.get_document_copies(doc_id)
        recipient_copies = [c for c in copies if c.recipient_principal_id == recipient.recipient_id]
        if recipient_copies:
            copy = recipient_copies[0]
        else:
            copy = self.lineage_service.issue_initial_copy(
                document_id=doc_id,
                recipient_principal_id=recipient.recipient_id,
                release_id=package.release_id,
                metadata={"dlt_receipt_id": receipt.receipt_id}
            )


        session = self.open_session(
            copy_id=copy.copy_id,
            identity_id=recipient.recipient_id,
            device_key_id=device_key_id,
            expires_in_seconds=expires_in_seconds,
            metadata=metadata,
        )

        self._session_decryptions[session.session_id] = receipt
        return session, receipt, dlt_block

    def open_session(
        self,
        copy_id: str,
        identity_id: Optional[str] = None,
        device_key_id: Optional[str] = None,
        expires_in_seconds: int = 3600,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AccessSession:
        """
        Starts an authenticated access session for viewing a copy.
        """
        return self.lineage_service.start_access_session(
            copy_id=copy_id,
            identity_id=identity_id,
            device_key_id=device_key_id,
            expires_in_seconds=expires_in_seconds,
            metadata=metadata,
        )

    def _validate_session(self, session_id: str) -> AccessSession:
        session = self.lineage_service.storage.get_session(session_id)
        if not session:
            raise PermissionError(f"Session '{session_id}' not found.")
        if not session.is_active:
            raise PermissionError(f"Session '{session_id}' is invalid or expired.")

        # Active time-based expiration enforcement
        if session.expires_at:
            try:
                exp_dt = datetime.fromisoformat(session.expires_at)
                now_dt = datetime.now(timezone.utc)
                if exp_dt.tzinfo is None:
                    exp_dt = exp_dt.replace(tzinfo=timezone.utc)
                if now_dt > exp_dt:
                    session.is_active = False
                    raise PermissionError(f"Session '{session_id}' has expired at {session.expires_at}.")
            except (ValueError, TypeError):
                pass

        return session

    def render_view(
        self,
        session_id: str,
    ) -> Dict[str, Any]:
        """
        Renders document in-memory within active session context.
        Applies dynamic session watermark overlay (sf_...).
        Does NOT expose raw unwatermarked master bytes.
        """
        session = self._validate_session(session_id)

        copy = self.lineage_service.storage.get_copy(session.copy_id)
        if not copy:
            raise ValueError(f"Copy '{session.copy_id}' not found.")

        # Check document exists
        doc_id = copy.document_id
        if doc_id not in self._document_store or doc_id not in self._encryption_keys:
            raise ValueError(f"Document '{doc_id}' not found in controlled viewer store.")

        # Decrypt in memory
        encrypted = self._document_store[doc_id]
        key = self._encryption_keys[doc_id]
        decrypted_bytes = decrypt_aes_gcm(key, encrypted)

        # Prepare dynamic session watermark metadata
        overlay_info = {
            "session_id": session.session_id,
            "copy_id": copy.copy_id,
            "session_fingerprint": session.session_fingerprint_key,
            "rendered_at": datetime.now(timezone.utc).isoformat(),
            "watermark_marker": f"AEGIS:{session.session_fingerprint_key}:{copy.copy_id[:12]}",
        }

        return {
            "session_id": session.session_id,
            "copy_id": copy.copy_id,
            "byte_count": len(decrypted_bytes),
            "overlay": overlay_info,
            "status": "RENDERED_CONTROLLED",
        }

    def controlled_export(
        self,
        session_id: str,
        export_format: ExportFormat,
        actor_principal_id: Optional[str] = None,
        signer_keypair: Optional[Tuple[bytes, bytes]] = None,
        device_id: Optional[str] = None,
        custom_metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bytes, CopyInstance, ExportEvent, LineageEdge]:
        """
        Controlled export boundary:
        1. Invokes LineageService to issue a new derivative CopyInstance (lineage_depth + 1).
        2. Signs cryptographic ExportEvent receipt.
        3. Re-fingerprints exported artifact with child copy's fingerprint.
        4. Returns watermarked bytes and lineage records.
        """
        session = self._validate_session(session_id)

        copy = self.lineage_service.storage.get_copy(session.copy_id)
        if not copy:
            raise ValueError(f"Copy '{session.copy_id}' not found.")

        doc_id = copy.document_id
        if doc_id not in self._document_store or doc_id not in self._encryption_keys:
            raise ValueError(f"Document '{doc_id}' not found in controlled viewer store.")

        # Decrypt master
        encrypted = self._document_store[doc_id]
        key = self._encryption_keys[doc_id]
        raw_bytes = decrypt_aes_gcm(key, encrypted)

        # Perform controlled export in lineage service
        child_copy, exp_event, edge = self.lineage_service.export_copy(
            session_id=session_id,
            export_format=export_format,
            actor_principal_id=actor_principal_id,
            signer_keypair=signer_keypair,
            device_id=device_id,
            metadata=custom_metadata,
        )

        # Synthesize re-fingerprinted output bytes binding child copy fingerprint
        fp_tag = f"\n%AEGIS_CHILD_FINGERPRINT:{child_copy.embedded_fingerprint_reference}:{child_copy.copy_id}%\n".encode('utf-8')
        exported_bytes = raw_bytes + fp_tag

        return exported_bytes, child_copy, exp_event, edge

    def controlled_export_with_dlt(
        self,
        session_id: str,
        export_format: ExportFormat,
        recipient: Recipient,
        device_id: Optional[str] = None,
        custom_metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bytes, CopyInstance, ExportEvent, LineageEdge, DecryptionReceipt, Optional[DLTBlock]]:
        """
        Executes controlled export with recipient-owned ML-DSA-65 signed DecryptionReceipt
        and full offline permissioned DLT consensus commitment.
        """
        signer_kp = (
            recipient.dsa_keypair.private_key_bytes,
            recipient.dsa_keypair.public_key_bytes,
        ) if recipient.dsa_keypair.private_key_bytes else None

        exported_bytes, child_copy, exp_event, edge = self.controlled_export(
            session_id=session_id,
            export_format=export_format,
            actor_principal_id=recipient.recipient_id,
            signer_keypair=signer_kp,
            device_id=device_id,
            custom_metadata=custom_metadata,
        )

        event_id = f"evt_exp_{child_copy.copy_id[:12]}_{os.urandom(4).hex()}"
        root = self.lineage_service.storage.get_document_root(child_copy.document_id)
        doc_root_hash = root.canonical_hash if root else hashlib.sha256(exported_bytes).hexdigest()


        dynamic_id = generate_dynamic_watermark(
            document_root_hash=doc_root_hash,
            recipient_id=recipient.recipient_id,
            session_id=session_id,
            event_id=event_id,
            copy_id=child_copy.copy_id,
        )

        # Attempt invisible watermark embedding into exported image
        try:
            watermarked_bytes = self.dynamic_wm_engine.embed_watermark(
                carrier_input=exported_bytes,
                dynamic_identity=dynamic_id,
                document_id=child_copy.document_id,
                release_id="export_boundary",
                as_bytes=True,
            )
        except Exception:
            watermarked_bytes = exported_bytes

        # Recipient signs DecryptionReceipt with ML-DSA-65
        pub_b64 = base64.b64encode(recipient.dsa_keypair.public_key_bytes).decode('utf-8')
        receipt_id = f"rcpt_{event_id}"
        tmp_receipt = DecryptionReceipt(
            receipt_id=receipt_id,
            document_root_hash=doc_root_hash,
            recipient_id=recipient.recipient_id,
            identity_reference=recipient.email or recipient.recipient_id,
            decryption_session_id=session_id,
            decryption_event_id=event_id,
            copy_instance_id=child_copy.copy_id,
            watermark_commitment=dynamic_id.commitment,
            watermark_token=dynamic_id.token,
            timestamp=datetime.now(timezone.utc).isoformat(),
            parent_lineage_reference=child_copy.parent_copy_id,
            recipient_public_key_b64=pub_b64,
            recipient_signature_b64="",
            metadata={
                "export_format": export_format.value,
                "child_copy_id": child_copy.copy_id,
            }
        )
        canonical_msg = tmp_receipt.canonical_payload_bytes()
        sig_bytes = MLDSA65.sign(recipient.dsa_keypair.private_key_bytes, canonical_msg)
        sig_b64 = base64.b64encode(sig_bytes).decode('utf-8')

        receipt = DecryptionReceipt(
            receipt_id=receipt_id,
            document_root_hash=doc_root_hash,
            recipient_id=recipient.recipient_id,
            identity_reference=recipient.email or recipient.recipient_id,
            decryption_session_id=session_id,
            decryption_event_id=event_id,
            copy_instance_id=child_copy.copy_id,
            watermark_commitment=dynamic_id.commitment,
            watermark_token=dynamic_id.token,
            timestamp=tmp_receipt.timestamp,
            parent_lineage_reference=child_copy.parent_copy_id,
            recipient_public_key_b64=pub_b64,
            recipient_signature_b64=sig_b64,
            nonce=tmp_receipt.nonce,
            metadata=tmp_receipt.metadata,
        )

        dlt_block = None
        if self.dlt_ledger:
            dlt_block = self.dlt_ledger.commit_receipt(receipt)

        self._session_decryptions[session_id] = receipt
        return watermarked_bytes, child_copy, exp_event, edge, receipt, dlt_block

