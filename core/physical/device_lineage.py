"""
SIH26237 - Device Session Lineage & Sparse Merkle Tracking Engine
=================================================================
Binds real-device lifecycle actions to the cryptographic lineage tree:
- DEVICE_CONNECTED
- SESSION_STARTED
- RECIPIENT_AUTHENTICATED
- ARTIFACT_RENDERED
- ARTIFACT_TRANSFERRED
- ARTIFACT_DOWNLOADED
- ARTIFACT_UPLOADED
- DEVICE_SESSION_CLOSED

Every event preserves parent/child relationships, device identity, actor,
timestamp, artifact SHA-256 hash, tenant ID, and epistemic validation status.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import hashlib
import json
from pydantic import BaseModel, Field

from core.physical.epistemic import EpistemicStatus
from core.lineage.storage import LineageStorage
from core.lineage.models import LineageEdge, TransitionActionType


class DeviceLineageAction(str):
    DEVICE_CONNECTED = "DEVICE_CONNECTED"
    SESSION_STARTED = "SESSION_STARTED"
    RECIPIENT_AUTHENTICATED = "RECIPIENT_AUTHENTICATED"
    ARTIFACT_RENDERED = "ARTIFACT_RENDERED"
    ARTIFACT_TRANSFERRED = "ARTIFACT_TRANSFERRED"
    ARTIFACT_DOWNLOADED = "ARTIFACT_DOWNLOADED"
    ARTIFACT_UPLOADED = "ARTIFACT_UPLOADED"
    DEVICE_SESSION_CLOSED = "DEVICE_SESSION_CLOSED"


class DeviceLineageEventRecord(BaseModel):
    """Cryptographically anchored device lineage event."""
    event_id: str
    parent_event_id: Optional[str] = None
    parent_artifact_id: Optional[str] = None
    child_artifact_id: Optional[str] = None
    action: str
    device_id: str
    actor_recipient_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    artifact_hash: str
    tenant_id: str = "TENANT-SIH-2026"
    transformation_type: str = "DIRECT_DEVICE_FLOW"
    epistemic_status: EpistemicStatus = EpistemicStatus.DEVICE_IN_LOOP
    merkle_leaf_hash: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DeviceLineageEngine:
    """
    Records and verifies chronological device session actions in the lineage graph.
    """

    def __init__(self, storage: Optional[LineageStorage] = None, tenant_id: str = "TENANT-SIH-2026"):
        self.storage = storage or LineageStorage()
        self.tenant_id = tenant_id
        self.events: List[DeviceLineageEventRecord] = []
        self._last_event_by_device: Dict[str, str] = {}

    def record_device_event(
        self,
        action: str,
        device_id: str,
        actor_recipient_id: str,
        artifact_hash: str,
        parent_artifact_id: Optional[str] = None,
        child_artifact_id: Optional[str] = None,
        transformation_type: str = "DIRECT_DEVICE_FLOW",
        epistemic_status: EpistemicStatus = EpistemicStatus.DEVICE_IN_LOOP,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DeviceLineageEventRecord:
        """
        Creates and seals a device lineage event with cryptographic hash chaining.
        """
        ts = datetime.now(timezone.utc).isoformat()
        entropy = hashlib.sha256(f"{device_id}:{action}:{ts}:{artifact_hash}".encode()).hexdigest()[:10]
        event_id = f"DEVEVT-{entropy}"

        parent_event_id = self._last_event_by_device.get(device_id)

        meta = metadata or {}
        # Compute Merkle leaf hash
        leaf_raw = f"{event_id}|{parent_event_id or 'ROOT'}|{action}|{device_id}|{actor_recipient_id}|{artifact_hash}|{ts}|{epistemic_status.value}"
        leaf_hash = hashlib.sha256(leaf_raw.encode("utf-8")).hexdigest()

        rec = DeviceLineageEventRecord(
            event_id=event_id,
            parent_event_id=parent_event_id,
            parent_artifact_id=parent_artifact_id,
            child_artifact_id=child_artifact_id,
            action=action,
            device_id=device_id,
            actor_recipient_id=actor_recipient_id,
            timestamp=ts,
            artifact_hash=artifact_hash,
            tenant_id=self.tenant_id,
            transformation_type=transformation_type,
            epistemic_status=epistemic_status,
            merkle_leaf_hash=leaf_hash,
            metadata=meta
        )

        self.events.append(rec)
        self._last_event_by_device[device_id] = event_id

        # Also insert edge into central LineageStorage if parent_artifact_id exists
        if parent_artifact_id and child_artifact_id:
            try:
                edge = LineageEdge(
                    edge_id=f"EDGE-{entropy}",
                    parent_copy_id=parent_artifact_id,
                    child_copy_id=child_artifact_id,
                    transition_type=TransitionActionType.EXPORT,
                    timestamp=ts,
                    source_device_id=device_id,
                    target_device_id=device_id
                )
                self.storage.add_edge(edge)
            except Exception:
                pass

        return rec

    def compute_merkle_root(self) -> str:
        """Computes incremental Merkle tree root over all recorded device events."""
        if not self.events:
            return hashlib.sha256(b"EMPTY_DEVICE_LINEAGE").hexdigest()

        leaves = [bytes.fromhex(ev.merkle_leaf_hash) for ev in self.events]
        # Pad to power of 2
        while len(leaves) & (len(leaves) - 1) != 0:
            leaves.append(hashlib.sha256(b"LINEAGE_PAD").digest())

        while len(leaves) > 1:
            next_level = []
            for i in range(0, len(leaves), 2):
                combined = leaves[i] + leaves[i + 1]
                next_level.append(hashlib.sha256(combined).digest())
            leaves = next_level

        return leaves[0].hex()

    def get_events_for_device(self, device_id: str) -> List[DeviceLineageEventRecord]:
        return [ev for ev in self.events if ev.device_id == device_id]
