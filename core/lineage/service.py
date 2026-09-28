"""
SIH26237 - Active Cryptographic Copy Lineage Service
Provides the core service layer for document root registration,
copy derivation, session tracking, controlled shares, export receipts,
and lineage query / verification.
"""

import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone, timedelta

from core.crypto.signatures import MLDSA65
from core.lineage.models import (
    DocumentRoot,
    CopyInstance,
    AccessSession,
    ForwardingEvent,
    ExportEvent,
    LineageEdge,
    LineageProof,
    TransitionActionType,
    ExportFormat,
    generate_copy_id,
)
from core.lineage.storage import LineageStorage
from core.lineage.verification import LineageVerifier


class LineageService:
    """
    Central service orchestrating document instance lineage, session lifecycle,
    cryptographic transition receipts, and ancestry resolution.
    """

    def __init__(self, storage: Optional[LineageStorage] = None):
        self.storage = storage or LineageStorage()
        self.verifier = LineageVerifier(self.storage)

    def create_document_root(
        self,
        document_bytes: bytes,
        document_id: Optional[str] = None,
        mime_type: str = "application/pdf",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DocumentRoot:
        """
        Registers an immutable document root anchor from master document bytes.
        """
        import hashlib
        canonical_hash = hashlib.sha256(document_bytes).hexdigest()
        doc_id = document_id or f"doc_root_{canonical_hash[:16]}"

        root = DocumentRoot(
            document_id=doc_id,
            canonical_hash=canonical_hash,
            mime_type=mime_type,
            byte_size=len(document_bytes),
            creation_metadata=metadata or {},
            created_at=datetime.now(timezone.utc).isoformat(),
            status="ACTIVE",
        )
        self.storage.store_document_root(root)
        return root

    def issue_initial_copy(
        self,
        document_id: str,
        recipient_principal_id: str,
        release_id: Optional[str] = None,
        embedded_fingerprint_reference: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CopyInstance:
        """
        Issues the genesis copy instance (depth 0) for a recipient.
        """
        root = self.storage.get_document_root(document_id)
        if not root:
            raise ValueError(f"Document root '{document_id}' not found.")

        now_str = datetime.now(timezone.utc).isoformat()
        nonce = os.urandom(16).hex()
        copy_id = generate_copy_id(
            canonical_hash=root.canonical_hash,
            parent_copy_id=None,
            recipient_or_session_id=recipient_principal_id,
            timestamp=now_str,
            nonce=nonce,
        )

        copy = CopyInstance(
            copy_id=copy_id,
            parent_copy_id=None,
            document_id=document_id,
            release_id=release_id,
            recipient_principal_id=recipient_principal_id,
            issuance_timestamp=now_str,
            instance_nonce=nonce,
            embedded_fingerprint_reference=embedded_fingerprint_reference,
            status="ACTIVE",
            lineage_depth=0,
            metadata=metadata or {},
        )
        self.storage.store_copy(copy)

        # Record root issuance edge
        edge = LineageEdge(
            edge_id=f"edge_init_{os.urandom(8).hex()}",
            parent_copy_id=None,
            child_copy_id=copy_id,
            transition_type=TransitionActionType.ISSUANCE,
            event_id=f"init_{copy_id}",
            actor_principal_id=None,
            recipient_principal_id=recipient_principal_id,
            timestamp=now_str,
            is_verified=True,
        )
        self.storage.store_edge(edge)
        self.storage.set_latest_event_hash_for_copy(copy_id, root.canonical_hash)
        self.storage.set_latest_event_hash(document_id, root.canonical_hash)
        return copy

    def start_access_session(
        self,
        copy_id: str,
        identity_id: Optional[str] = None,
        device_key_id: Optional[str] = None,
        expires_in_seconds: int = 3600,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AccessSession:
        """
        Creates a time-bounded, dynamic watermarking session for viewing a copy.
        """
        copy = self.storage.get_copy(copy_id)
        if not copy:
            raise ValueError(f"Copy instance '{copy_id}' not found.")

        now = datetime.now(timezone.utc)
        expires_at = (now + timedelta(seconds=expires_in_seconds)).isoformat()
        session_id = f"ses_{os.urandom(8).hex()}"
        session_fingerprint_key = f"sf_{os.urandom(12).hex()}"

        session = AccessSession(
            session_id=session_id,
            copy_id=copy_id,
            identity_id=identity_id,
            device_key_id=device_key_id,
            issued_at=now.isoformat(),
            expires_at=expires_at,
            session_nonce=os.urandom(16).hex(),
            session_fingerprint_key=session_fingerprint_key,
            is_active=True,
            metadata=metadata or {},
        )
        self.storage.store_session(session)
        return session

    def share_copy(
        self,
        parent_copy_id: str,
        actor_principal_id: str,
        target_recipient_principal_id: str,
        signer_keypair: Optional[Tuple[bytes, bytes]] = None,
        action_type: TransitionActionType = TransitionActionType.CONTROLLED_SHARE,
        sender_device_id: Optional[str] = None,
        actor_identity_id: Optional[str] = None,
        target_identity_id: Optional[str] = None,
        embedded_fingerprint_reference: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[CopyInstance, ForwardingEvent, LineageEdge]:
        """
        Performs a controlled forwarding/sharing transition within the AegisTrace boundary.
        Generates a new derivative child copy and a cryptographically signed ForwardingEvent receipt.
        """
        import base64
        parent_copy = self.storage.get_copy(parent_copy_id)
        if not parent_copy:
            raise ValueError(f"Parent copy '{parent_copy_id}' not found.")

        root = self.storage.get_document_root(parent_copy.document_id)
        if not root:
            raise ValueError(f"Document root '{parent_copy.document_id}' not found.")

        now_str = datetime.now(timezone.utc).isoformat()
        nonce = os.urandom(16).hex()
        child_copy_id = generate_copy_id(
            canonical_hash=root.canonical_hash,
            parent_copy_id=parent_copy_id,
            recipient_or_session_id=target_recipient_principal_id,
            timestamp=now_str,
            nonce=nonce,
        )

        child_copy = CopyInstance(
            copy_id=child_copy_id,
            parent_copy_id=parent_copy_id,
            document_id=parent_copy.document_id,
            release_id=parent_copy.release_id,
            recipient_principal_id=target_recipient_principal_id,
            issuance_timestamp=now_str,
            instance_nonce=nonce,
            embedded_fingerprint_reference=embedded_fingerprint_reference or f"fp_{child_copy_id}",
            status="ACTIVE",
            lineage_depth=parent_copy.lineage_depth + 1,
            metadata=metadata or {},
        )

        fwd_id = f"fwd_{os.urandom(8).hex()}"
        prev_event_hash = self.storage.get_latest_event_hash_for_copy(parent_copy_id)
        fwd_event = ForwardingEvent(
            forwarding_event_id=fwd_id,
            parent_copy_id=parent_copy_id,
            child_copy_id=child_copy_id,
            actor_identity_id=actor_identity_id,
            actor_principal_id=actor_principal_id,
            sender_device_id=sender_device_id,
            recipient_identity_id=target_identity_id,
            recipient_principal_id=target_recipient_principal_id,
            timestamp=now_str,
            action_type=action_type,
            previous_event_hash=prev_event_hash,
            metadata=metadata or {},
        )

        # Compute hash and sign if keypair provided
        preimage = fwd_event.compute_preimage()
        event_hash = fwd_event.compute_event_hash()
        fwd_event.signed_event_hash = event_hash

        if signer_keypair:
            priv_key, pub_key = signer_keypair
            sig_bytes = MLDSA65.sign(priv_key, preimage)
            fwd_event.signature_b64 = base64.b64encode(sig_bytes).decode('ascii')
            fwd_event.signer_public_key_b64 = base64.b64encode(pub_key).decode('ascii')

        # Persist event and child copy
        self.storage.store_forwarding_event(fwd_event)
        self.storage.store_copy(child_copy)
        self.storage.set_latest_event_hash_for_copy(child_copy_id, event_hash)
        self.storage.set_latest_event_hash(parent_copy.document_id, event_hash)

        # Create directed edge
        edge = LineageEdge(
            edge_id=f"edge_fwd_{os.urandom(8).hex()}",
            parent_copy_id=parent_copy_id,
            child_copy_id=child_copy_id,
            transition_type=action_type,
            event_id=fwd_id,
            actor_principal_id=actor_principal_id,
            recipient_principal_id=target_recipient_principal_id,
            timestamp=now_str,
            is_verified=True,
        )
        self.storage.store_edge(edge)

        return child_copy, fwd_event, edge

    def export_copy(
        self,
        session_id: str,
        export_format: ExportFormat,
        actor_principal_id: Optional[str] = None,
        actor_identity_id: Optional[str] = None,
        export_fingerprint: Optional[str] = None,
        signer_keypair: Optional[Tuple[bytes, bytes]] = None,
        device_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[CopyInstance, ExportEvent, LineageEdge]:
        """
        Controlled export boundary: re-fingerprints document to produce a new
        child CopyInstance and cryptographically signed ExportEvent receipt.
        """
        import base64
        session = self.storage.get_session(session_id)
        if not session or not session.is_active:
            raise ValueError(f"Active session '{session_id}' not found.")

        parent_copy = self.storage.get_copy(session.copy_id)
        if not parent_copy:
            raise ValueError(f"Parent copy '{session.copy_id}' not found.")

        root = self.storage.get_document_root(parent_copy.document_id)
        if not root:
            raise ValueError(f"Document root '{parent_copy.document_id}' not found.")

        now_str = datetime.now(timezone.utc).isoformat()
        nonce = os.urandom(16).hex()
        fingerprint = export_fingerprint or f"exp_fp_{os.urandom(12).hex()}"

        rec_id = actor_principal_id or parent_copy.recipient_principal_id
        child_copy_id = generate_copy_id(
            canonical_hash=root.canonical_hash,
            parent_copy_id=parent_copy.copy_id,
            recipient_or_session_id=rec_id,
            timestamp=now_str,
            nonce=nonce,
        )

        child_copy = CopyInstance(
            copy_id=child_copy_id,
            parent_copy_id=parent_copy.copy_id,
            document_id=parent_copy.document_id,
            release_id=parent_copy.release_id,
            recipient_principal_id=rec_id,
            issuance_timestamp=now_str,
            instance_nonce=nonce,
            embedded_fingerprint_reference=fingerprint,
            status="EXPORTED",
            lineage_depth=parent_copy.lineage_depth + 1,
            metadata={"export_format": export_format.value, "source_session_id": session_id, **(metadata or {})},
        )

        exp_id = f"exp_{os.urandom(8).hex()}"
        prev_event_hash = self.storage.get_latest_event_hash_for_copy(parent_copy.copy_id)
        exp_event = ExportEvent(
            export_id=exp_id,
            source_session_id=session_id,
            parent_copy_id=parent_copy.copy_id,
            child_copy_id=child_copy_id,
            export_format=export_format,
            export_fingerprint=fingerprint,
            timestamp=now_str,
            actor_identity_id=actor_identity_id or session.identity_id,
            actor_principal_id=actor_principal_id or parent_copy.recipient_principal_id,
            device_identity_id=device_id or session.device_key_id,
            previous_event_hash=prev_event_hash,
            metadata=metadata or {},
        )

        preimage = exp_event.compute_preimage()
        event_hash = exp_event.compute_event_hash()
        exp_event.signed_event_hash = event_hash

        if signer_keypair:
            priv_key, pub_key = signer_keypair
            sig_bytes = MLDSA65.sign(priv_key, preimage)
            exp_event.signature_b64 = base64.b64encode(sig_bytes).decode('ascii')
            exp_event.signer_public_key_b64 = base64.b64encode(pub_key).decode('ascii')

        # Persist event and child copy
        self.storage.store_export_event(exp_event)
        self.storage.store_copy(child_copy)
        self.storage.set_latest_event_hash_for_copy(child_copy_id, event_hash)
        self.storage.set_latest_event_hash(parent_copy.document_id, event_hash)

        # Create directed edge
        edge = LineageEdge(
            edge_id=f"edge_exp_{os.urandom(8).hex()}",
            parent_copy_id=parent_copy.copy_id,
            child_copy_id=child_copy_id,
            transition_type=TransitionActionType.EXPORT,
            event_id=exp_id,
            actor_principal_id=actor_principal_id or parent_copy.recipient_principal_id,
            recipient_principal_id=actor_principal_id or parent_copy.recipient_principal_id,
            timestamp=now_str,
            is_verified=True,
        )
        self.storage.store_edge(edge)

        return child_copy, exp_event, edge

    def get_lineage(self, copy_id: str) -> LineageProof:
        """
        Reconstructs and cryptographically verifies the full lineage proof for a copy.
        """
        return self.verifier.verify_lineage(copy_id)

    def verify_lineage(self, copy_id: str) -> LineageProof:
        """Alias for get_lineage."""
        return self.verifier.verify_lineage(copy_id)

    def get_children(self, copy_id: str) -> List[CopyInstance]:
        """Returns direct derivative child copy instances."""
        child_ids = self.storage.get_children_copy_ids(copy_id)
        return [self.storage.get_copy(cid) for cid in child_ids if self.storage.get_copy(cid) is not None]

    def get_parent(self, copy_id: str) -> Optional[CopyInstance]:
        """Returns immediate parent copy instance."""
        copy = self.storage.get_copy(copy_id)
        if copy and copy.parent_copy_id:
            return self.storage.get_copy(copy.parent_copy_id)
        return None

    def get_last_known_holder(self, copy_id: str) -> Optional[str]:
        """
        Returns the last verified controlled actor holding or originating this copy.
        """
        proof = self.verifier.verify_lineage(copy_id)
        return proof.last_known_controlled_holder

    def get_lineage_breaks(self, copy_id: str) -> List[str]:
        """
        Returns any identified break reasons in the copy's ancestry chain.
        """
        proof = self.verifier.verify_lineage(copy_id)
        if not proof.is_valid and proof.break_reason:
            return [proof.break_reason]
        return []

    def find_copy_by_fingerprint(self, fingerprint: str) -> Optional[CopyInstance]:
        """O(1) lookup of copy instance from embedded fingerprint reference."""
        return self.storage.find_copy_by_fingerprint(fingerprint)

    def find_session_by_fingerprint(self, session_fingerprint: str) -> Optional[AccessSession]:
        """O(1) lookup of active access session from session watermark material."""
        return self.storage.find_session_by_fingerprint(session_fingerprint)
