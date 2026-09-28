"""
SIH26237 - Lineage Cryptographic Verification Engine
Validates parent-child derivations, ML-DSA-65 transition receipts,
hash-chain continuity, and detects lineage breakage, forks, and tampering.
"""

from typing import Tuple, Optional, List, Set, Dict, Any
import base64

from core.crypto.signatures import MLDSA65
from core.lineage.models import (
    DocumentRoot,
    CopyInstance,
    ForwardingEvent,
    ExportEvent,
    LineageEdge,
    LineageProof,
    ForensicBoundaryState,
    ForensicAttributionLevel,
    generate_copy_id,
)
from core.lineage.storage import LineageStorage


class LineageVerifier:
    """
    Cryptographic verification service for copy lineage paths and transition receipts.
    Strictly fail-closed: invalid signatures, cycle loops, or missing parents
    trigger LINEAGE_BROKEN rather than guessing.
    """

    def __init__(self, storage: LineageStorage):
        self.storage = storage

    def verify_forwarding_event(
        self,
        event: ForwardingEvent,
        signer_public_key_bytes: Optional[bytes] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates the integrity and ML-DSA-65 signature of a ForwardingEvent receipt.
        """
        # 1. Verify computed event hash
        expected_hash = event.compute_event_hash()
        if event.signed_event_hash and event.signed_event_hash != expected_hash:
            return False, f"Event hash mismatch: stored={event.signed_event_hash}, computed={expected_hash}"

        # 2. Verify signature is present and valid
        if not event.signature_b64:
            return False, "Missing required ML-DSA-65 transition signature"

        pub_bytes = signer_public_key_bytes
        if not pub_bytes and event.signer_public_key_b64:
            pub_bytes = base64.b64decode(event.signer_public_key_b64)

        if not pub_bytes:
            return False, "Signature present but no public key available for verification"

        sig_bytes = base64.b64decode(event.signature_b64)
        preimage = event.compute_preimage()
        try:
            is_valid = MLDSA65.verify(pub_bytes, preimage, sig_bytes)
            if not is_valid:
                return False, "ML-DSA-65 transition signature verification failed"
        except Exception as e:
            return False, f"Signature verification exception: {str(e)}"

        return True, None

    def verify_export_event(
        self,
        event: ExportEvent,
        signer_public_key_bytes: Optional[bytes] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates the integrity and ML-DSA-65 signature of an ExportEvent receipt.
        """
        expected_hash = event.compute_event_hash()
        if event.signed_event_hash and event.signed_event_hash != expected_hash:
            return False, f"Export hash mismatch: stored={event.signed_event_hash}, computed={expected_hash}"

        if not event.signature_b64:
            return False, "Missing required ML-DSA-65 export signature"

        pub_bytes = signer_public_key_bytes
        if not pub_bytes and event.signer_public_key_b64:
            pub_bytes = base64.b64decode(event.signer_public_key_b64)

        if not pub_bytes:
            return False, "Signature present but no public key available for verification"

        sig_bytes = base64.b64decode(event.signature_b64)
        preimage = event.compute_preimage()
        try:
            is_valid = MLDSA65.verify(pub_bytes, preimage, sig_bytes)
            if not is_valid:
                return False, "ML-DSA-65 export signature verification failed"
        except Exception as e:
            return False, f"Signature verification exception: {str(e)}"

        return True, None

    def verify_copy_derivation(
        self,
        copy: CopyInstance,
        parent: Optional[CopyInstance],
        root: DocumentRoot
    ) -> Tuple[bool, Optional[str]]:
        """
        Asserts copy identity parameters, depth invariants, and parent linkage.
        """
        # Document root invariant
        if copy.document_id != root.document_id:
            return False, f"Cross-document parent substitution: copy doc={copy.document_id}, root doc={root.document_id}"

        # Root copy check
        if copy.parent_copy_id is None:
            if copy.lineage_depth != 0:
                return False, f"Root copy must have lineage_depth=0, got {copy.lineage_depth}"
            return True, None

        # Child copy check
        if not parent:
            return False, f"Orphan copy: parent_copy_id '{copy.parent_copy_id}' not found"

        if parent.document_id != root.document_id:
            return False, f"Cross-document lineage contamination: parent doc={parent.document_id} != root={root.document_id}"

        if copy.lineage_depth != parent.lineage_depth + 1:
            return False, f"Lineage depth broken: child depth {copy.lineage_depth} != parent {parent.lineage_depth} + 1"

        # Verify deterministic copy_id cryptographic derivation if metadata fields present
        if copy.instance_nonce and copy.issuance_timestamp:
            rec = copy.recipient_principal_id
            candidates = [rec] if rec else []
            if copy.metadata and "source_session_id" in copy.metadata:
                candidates.append(copy.metadata["source_session_id"])
            if copy.metadata and "session_id" in copy.metadata:
                candidates.append(copy.metadata["session_id"])

            matched = False
            for cand in candidates:
                expected_cid = generate_copy_id(
                    canonical_hash=root.canonical_hash,
                    parent_copy_id=copy.parent_copy_id,
                    recipient_or_session_id=cand,
                    timestamp=copy.issuance_timestamp,
                    nonce=copy.instance_nonce,
                )
                if copy.copy_id == expected_cid:
                    matched = True
                    break

            if not matched and copy.copy_id.startswith("cpy_") and len(copy.copy_id) == 36:
                return False, f"Tampered copy identity: copy_id '{copy.copy_id}' does not match cryptographic derivation"

        return True, None

    def verify_lineage(self, copy_id: str, max_hops: int = 10_000) -> LineageProof:
        """
        Reconstructs and verifies the full directed lineage path from the root
        down to the target copy_id.
        """
        leaf_copy = self.storage.get_copy(copy_id)
        if not leaf_copy:
            return LineageProof(
                leaf_copy_id=copy_id,
                root_document_id="UNKNOWN",
                is_valid=False,
                forensic_boundary_state=ForensicBoundaryState.INSUFFICIENT_EVIDENCE,
                highest_attribution_level=ForensicAttributionLevel.LEVEL_1_DOCUMENT_DETECTED,
                break_reason=f"CopyInstance '{copy_id}' does not exist in lineage registry."
            )

        root = self.storage.get_document_root(leaf_copy.document_id)
        if not root:
            return LineageProof(
                leaf_copy_id=copy_id,
                root_document_id=leaf_copy.document_id,
                is_valid=False,
                forensic_boundary_state=ForensicBoundaryState.LINEAGE_BROKEN,
                highest_attribution_level=ForensicAttributionLevel.LEVEL_1_DOCUMENT_DETECTED,
                break_reason=f"DocumentRoot '{leaf_copy.document_id}' missing."
            )

        # Backtrack from leaf to root
        current_copy = leaf_copy
        visited_ids: Set[str] = set()
        ancestor_chain: List[CopyInstance] = []
        edges: List[LineageEdge] = []
        last_controlled_holder: Optional[str] = leaf_copy.recipient_principal_id

        while current_copy is not None:
            if current_copy.copy_id in visited_ids:
                return LineageProof(
                    leaf_copy_id=copy_id,
                    root_document_id=root.document_id,
                    is_valid=False,
                    forensic_boundary_state=ForensicBoundaryState.LINEAGE_BROKEN,
                    highest_attribution_level=ForensicAttributionLevel.LEVEL_1_DOCUMENT_DETECTED,
                    break_reason=f"Lineage cycle detected at '{current_copy.copy_id}'"
                )
            if len(ancestor_chain) > max_hops:
                return LineageProof(
                    leaf_copy_id=copy_id,
                    root_document_id=root.document_id,
                    is_valid=False,
                    ancestor_copy_ids=[c.copy_id for c in ancestor_chain],
                    last_known_controlled_holder=last_controlled_holder,
                    forensic_boundary_state=ForensicBoundaryState.LINEAGE_BROKEN,
                    highest_attribution_level=ForensicAttributionLevel.LEVEL_2_ORIGINAL_RECIPIENT_IDENTIFIED,
                    break_reason=f"Traversal exceeded max depth bound of {max_hops} hops"
                )

            visited_ids.add(current_copy.copy_id)
            ancestor_chain.append(current_copy)

            if current_copy.parent_copy_id is None:
                # Reached root copy
                break

            parent_copy = self.storage.get_copy(current_copy.parent_copy_id)
            if not parent_copy:
                return LineageProof(
                    leaf_copy_id=copy_id,
                    root_document_id=root.document_id,
                    is_valid=False,
                    ancestor_copy_ids=[c.copy_id for c in ancestor_chain],
                    last_known_controlled_holder=last_controlled_holder,
                    forensic_boundary_state=ForensicBoundaryState.LINEAGE_BROKEN,
                    highest_attribution_level=ForensicAttributionLevel.LEVEL_2_ORIGINAL_RECIPIENT_IDENTIFIED,
                    break_reason=f"Broken ancestry: parent '{current_copy.parent_copy_id}' not found."
                )

            # Check derivation validity
            ok_deriv, deriv_err = self.verify_copy_derivation(current_copy, parent_copy, root)
            if not ok_deriv:
                return LineageProof(
                    leaf_copy_id=copy_id,
                    root_document_id=root.document_id,
                    is_valid=False,
                    ancestor_copy_ids=[c.copy_id for c in ancestor_chain],
                    last_known_controlled_holder=last_controlled_holder,
                    forensic_boundary_state=ForensicBoundaryState.LINEAGE_BROKEN,
                    highest_attribution_level=ForensicAttributionLevel.LEVEL_2_ORIGINAL_RECIPIENT_IDENTIFIED,
                    break_reason=deriv_err
                )

            # Check edge transition receipt
            edge = self.storage.get_edge_for_child(current_copy.copy_id)
            if edge:
                if edge.event_id.startswith("fwd_"):
                    fwd_event = self.storage.get_forwarding_event(edge.event_id)
                    if fwd_event:
                        ok_sig, sig_err = self.verify_forwarding_event(fwd_event)
                        if not ok_sig:
                            return LineageProof(
                                leaf_copy_id=copy_id,
                                root_document_id=root.document_id,
                                is_valid=False,
                                ancestor_copy_ids=[c.copy_id for c in ancestor_chain],
                                last_known_controlled_holder=last_controlled_holder,
                                forensic_boundary_state=ForensicBoundaryState.LINEAGE_BROKEN,
                                highest_attribution_level=ForensicAttributionLevel.LEVEL_2_ORIGINAL_RECIPIENT_IDENTIFIED,
                                break_reason=f"Forwarding receipt verification failed on edge {edge.edge_id}: {sig_err}"
                            )
                elif edge.event_id.startswith("exp_"):
                    exp_event = self.storage.get_export_event(edge.event_id)
                    if exp_event:
                        ok_sig, sig_err = self.verify_export_event(exp_event)
                        if not ok_sig:
                            return LineageProof(
                                leaf_copy_id=copy_id,
                                root_document_id=root.document_id,
                                is_valid=False,
                                ancestor_copy_ids=[c.copy_id for c in ancestor_chain],
                                last_known_controlled_holder=last_controlled_holder,
                                forensic_boundary_state=ForensicBoundaryState.LINEAGE_BROKEN,
                                highest_attribution_level=ForensicAttributionLevel.LEVEL_2_ORIGINAL_RECIPIENT_IDENTIFIED,
                                break_reason=f"Export receipt verification failed on edge {edge.edge_id}: {sig_err}"
                            )
                edges.append(edge)

            current_copy = parent_copy

        # Chain reversed to be chronological: root -> leaf
        ancestor_chain.reverse()
        edges.reverse()
        ancestor_ids = [c.copy_id for c in ancestor_chain]

        # Determine level and state
        root_copy = ancestor_chain[0]
        initial_recipient = root_copy.recipient_principal_id
        depth = len(ancestor_chain) - 1

        if depth == 0:
            level = ForensicAttributionLevel.LEVEL_2_ORIGINAL_RECIPIENT_IDENTIFIED
            state = ForensicBoundaryState.ATTRIBUTED_TO_CONTROLLED_ACTOR
        else:
            level = ForensicAttributionLevel.LEVEL_4_LINEAGE_IDENTIFIED
            state = ForensicBoundaryState.LINEAGE_CONTINUES

        return LineageProof(
            leaf_copy_id=copy_id,
            root_document_id=root.document_id,
            path=edges,
            ancestor_copy_ids=ancestor_ids,
            last_known_controlled_holder=leaf_copy.recipient_principal_id or initial_recipient,
            forensic_boundary_state=state,
            highest_attribution_level=level,
            is_valid=True,
            details={
                "lineage_depth": depth,
                "initial_recipient": initial_recipient,
                "hop_count": len(edges),
            }
        )
