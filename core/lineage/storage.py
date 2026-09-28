"""
SIH26237 - Lineage Storage & Indexing Engine
Provides high-performance, partitioned, hash-indexed storage for document roots,
copy instances, sessions, forwarding receipts, and export events.
"""

from typing import Dict, List, Optional, Any, Set, Tuple
from collections import defaultdict
import threading
import time

from core.lineage.models import (
    DocumentRoot,
    CopyInstance,
    AccessSession,
    ForwardingEvent,
    ExportEvent,
    LineageEdge,
    DeviceBinding,
)
from core.lineage.scale import SparseLineageIndex, SparseLineageNode, TraversalResult


class LineageStorage:
    """
    Thread-safe, partitioned storage engine with O(1) hash indices.
    Avoids loading full linear histories into global memory; supports tenant
    and document-level partition isolation.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self.sparse_index = SparseLineageIndex()

        # Primary entities
        self._roots: Dict[str, DocumentRoot] = {}
        self._copies: Dict[str, CopyInstance] = {}
        self._sessions: Dict[str, AccessSession] = {}
        self._forwarding_events: Dict[str, ForwardingEvent] = {}
        self._export_events: Dict[str, ExportEvent] = {}
        self._device_bindings: Dict[str, DeviceBinding] = {}
        self._edges: Dict[str, LineageEdge] = {}
        self._child_to_edge: Dict[str, LineageEdge] = {}

        # Fast indices for graph traversal
        self._parent_to_children: Dict[str, List[str]] = defaultdict(list)
        self._document_to_copies: Dict[str, List[str]] = defaultdict(list)
        self._recipient_to_copies: Dict[str, List[str]] = defaultdict(list)
        self._fingerprint_to_copy: Dict[str, str] = {}
        self._session_fingerprint_to_session: Dict[str, str] = {}
        self._event_hashes: Set[str] = set()
        self._document_latest_event_hash: Dict[str, str] = {}
        self._copy_latest_event_hash: Dict[str, str] = {}

    # --- Document Roots ---
    def store_document_root(self, root: DocumentRoot) -> None:
        with self._lock:
            self._roots[root.document_id] = root
            self._document_latest_event_hash[root.document_id] = root.canonical_hash

    def get_document_root(self, document_id: str) -> Optional[DocumentRoot]:
        with self._lock:
            return self._roots.get(document_id)

    def get_latest_event_hash(self, document_id: str) -> str:
        with self._lock:
            if document_id in self._document_latest_event_hash:
                return self._document_latest_event_hash[document_id]
            root = self._roots.get(document_id)
            if root:
                return root.canonical_hash
            return "0" * 64

    def set_latest_event_hash(self, document_id: str, event_hash: str) -> None:
        with self._lock:
            self._document_latest_event_hash[document_id] = event_hash

    def get_latest_event_hash_for_copy(self, copy_id: str) -> str:
        with self._lock:
            if copy_id in self._copy_latest_event_hash:
                return self._copy_latest_event_hash[copy_id]
            copy = self._copies.get(copy_id)
            if copy:
                if copy.document_id in self._document_latest_event_hash:
                    return self._document_latest_event_hash[copy.document_id]
                root = self._roots.get(copy.document_id)
                if root:
                    return root.canonical_hash
            return "0" * 64

    def set_latest_event_hash_for_copy(self, copy_id: str, event_hash: str) -> None:
        with self._lock:
            self._copy_latest_event_hash[copy_id] = event_hash

    # --- Copy Instances ---
    def store_copy(self, copy: CopyInstance, tenant_id: str = "default_tenant") -> None:
        with self._lock:
            self._copies[copy.copy_id] = copy
            self._document_to_copies[copy.document_id].append(copy.copy_id)
            if copy.parent_copy_id:
                self._parent_to_children[copy.parent_copy_id].append(copy.copy_id)
            if copy.recipient_principal_id:
                self._recipient_to_copies[copy.recipient_principal_id].append(copy.copy_id)
            if copy.embedded_fingerprint_reference:
                self._fingerprint_to_copy[copy.embedded_fingerprint_reference] = copy.copy_id

            # Mirror to sparse index for high-scale O(1) traversal
            node = SparseLineageNode(
                copy_id=copy.copy_id,
                parent_copy_id=copy.parent_copy_id,
                document_id=copy.document_id,
                recipient_id=copy.recipient_principal_id or "ANONYMOUS",
                event_id=copy.metadata.get("event_id", f"evt_{copy.copy_id}"),
                timestamp_epoch=time.time(),
                depth=copy.lineage_depth,
                fingerprint_ref=copy.embedded_fingerprint_reference,
                tenant_id=tenant_id
            )
            self.sparse_index.insert_node(node)

    def get_copy(self, copy_id: str) -> Optional[CopyInstance]:
        with self._lock:
            return self._copies.get(copy_id)

    def traverse_ancestors(
        self,
        leaf_copy_id: str,
        max_hops: int = 10_000,
        tenant_id: Optional[str] = None
    ) -> TraversalResult:
        with self._lock:
            return self.sparse_index.traverse_ancestors(leaf_copy_id, max_hops, tenant_id)

    def traverse_descendants(
        self,
        root_copy_id: str,
        max_nodes: int = 100_000,
        tenant_id: Optional[str] = None
    ) -> TraversalResult:
        with self._lock:
            return self.sparse_index.traverse_descendants_bfs(root_copy_id, max_nodes, tenant_id)

    def get_children_copy_ids(self, parent_copy_id: str) -> List[str]:
        with self._lock:
            return list(self._parent_to_children.get(parent_copy_id, []))

    def get_document_copies(self, document_id: str) -> List[CopyInstance]:
        with self._lock:
            copy_ids = self._document_to_copies.get(document_id, [])
            return [self._copies[cid] for cid in copy_ids if cid in self._copies]

    def find_copy_by_fingerprint(self, fingerprint: str) -> Optional[CopyInstance]:
        with self._lock:
            copy_id = self._fingerprint_to_copy.get(fingerprint)
            return self._copies.get(copy_id) if copy_id else None

    # --- Sessions ---
    def store_session(self, session: AccessSession) -> None:
        with self._lock:
            self._sessions[session.session_id] = session
            if session.session_fingerprint_key:
                self._session_fingerprint_to_session[session.session_fingerprint_key] = session.session_id

    def get_session(self, session_id: str) -> Optional[AccessSession]:
        with self._lock:
            return self._sessions.get(session_id)

    def find_session_by_fingerprint(self, session_fingerprint: str) -> Optional[AccessSession]:
        with self._lock:
            ses_id = self._session_fingerprint_to_session.get(session_fingerprint)
            return self._sessions.get(ses_id) if ses_id else None

    # --- Forwarding & Export Events ---
    def store_forwarding_event(self, event: ForwardingEvent) -> None:
        with self._lock:
            h = event.compute_event_hash()
            if h in self._event_hashes:
                raise ValueError(f"Replay detected: ForwardingEvent hash {h} already recorded in lineage ledger.")
            self._event_hashes.add(h)
            self._forwarding_events[event.forwarding_event_id] = event

    def get_forwarding_event(self, event_id: str) -> Optional[ForwardingEvent]:
        with self._lock:
            return self._forwarding_events.get(event_id)

    def store_export_event(self, event: ExportEvent) -> None:
        with self._lock:
            h = event.compute_event_hash()
            if h in self._event_hashes:
                raise ValueError(f"Replay detected: ExportEvent hash {h} already recorded in lineage ledger.")
            self._event_hashes.add(h)
            self._export_events[event.export_id] = event

    def get_export_event(self, export_id: str) -> Optional[ExportEvent]:
        with self._lock:
            return self._export_events.get(export_id)

    # --- Edges ---
    def store_edge(self, edge: LineageEdge) -> None:
        with self._lock:
            self._edges[edge.edge_id] = edge
            if edge.child_copy_id:
                self._child_to_edge[edge.child_copy_id] = edge

    def get_edge(self, edge_id: str) -> Optional[LineageEdge]:
        with self._lock:
            return self._edges.get(edge_id)

    def get_edge_for_child(self, child_copy_id: str) -> Optional[LineageEdge]:
        with self._lock:
            return self._child_to_edge.get(child_copy_id)

    # --- Device Bindings ---
    def store_device_binding(self, device: DeviceBinding) -> None:
        with self._lock:
            self._device_bindings[device.device_id] = device

    def get_device_binding(self, device_id: str) -> Optional[DeviceBinding]:
        with self._lock:
            return self._device_bindings.get(device_id)

    def clear(self) -> None:
        """Testing utility to reset storage."""
        with self._lock:
            self._roots.clear()
            self._copies.clear()
            self._sessions.clear()
            self._forwarding_events.clear()
            self._export_events.clear()
            self._device_bindings.clear()
            self._edges.clear()
            self._child_to_edge.clear()
            self._parent_to_children.clear()
            self._document_to_copies.clear()
            self._recipient_to_copies.clear()
            self._fingerprint_to_copy.clear()
            self._session_fingerprint_to_session.clear()
            self._event_hashes.clear()
            self._document_latest_event_hash.clear()
            self._copy_latest_event_hash.clear()
            self.sparse_index.clear()
