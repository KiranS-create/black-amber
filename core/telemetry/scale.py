"""
Scalable Telemetry Store with Slotted Compact Records & Multi-Attribute Inverted Indexes.

Optimized for 1,000 to 1,000,000 forensic telemetry events:
- Compact slotted records (~120 bytes vs ~2.5 KB for Pydantic BaseModel).
- Multi-attribute secondary indexes: (tenant_id, key) -> list of record indices.
- Bisect-based chronological indexing for O(log N + K) time-window queries.
- Strict multi-tenant isolation.
"""

import time
import bisect
import threading
from typing import List, Dict, Optional, Set, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timezone


class CompactTelemetryRecord:
    """Slotted, memory-compact telemetry event representation (~120 bytes)."""
    __slots__ = (
        "event_id",
        "event_type",
        "source_system",
        "artifact_hash",
        "copy_id",
        "device_id",
        "subject_id",
        "network_id",
        "timestamp_epoch",
        "tenant_id",
        "payload_summary",
    )

    def __init__(
        self,
        event_id: str,
        event_type: str = "",
        source_system: str = "",
        artifact_hash: Optional[str] = None,
        copy_id: Optional[str] = None,
        device_id: Optional[str] = None,
        subject_id: Optional[str] = None,
        network_id: Optional[str] = None,
        timestamp_epoch: float = 0.0,
        tenant_id: str = "default_tenant",
        payload_summary: str = "",
    ):
        self.event_id = event_id
        self.event_type = event_type
        self.source_system = source_system
        self.artifact_hash = artifact_hash
        self.copy_id = copy_id
        self.device_id = device_id
        self.subject_id = subject_id
        self.network_id = network_id
        self.timestamp_epoch = timestamp_epoch
        self.tenant_id = tenant_id
        self.payload_summary = payload_summary

    def __repr__(self) -> str:
        return f"CompactTelemetryRecord(event_id={self.event_id!r}, type={self.event_type!r}, tenant={self.tenant_id!r})"


class ScalableTelemetryProvider:
    """
    High-throughput, memory-bounded forensic telemetry store.
    Provides sub-millisecond multi-attribute and temporal range queries at 1,000,000 event scale.
    """
    def __init__(self):
        self._lock = threading.RLock()
        self._records: List[CompactTelemetryRecord] = []
        
        # Primary key index: event_id -> index
        self._by_id: Dict[str, int] = {}
        
        # Inverted secondary indexes: (tenant_id, attribute_value) -> List[record_index]
        self._by_hash: Dict[Tuple[str, str], List[int]] = {}
        self._by_copy: Dict[Tuple[str, str], List[int]] = {}
        self._by_device: Dict[Tuple[str, str], List[int]] = {}
        self._by_actor: Dict[Tuple[str, str], List[int]] = {}
        self._by_network: Dict[Tuple[str, str], List[int]] = {}
        self._by_type: Dict[Tuple[str, str], List[int]] = {}
        self._by_tenant: Dict[str, List[int]] = {}

        # Chronological index per tenant: tenant_id -> list of (timestamp_epoch, record_index)
        self._timelines: Dict[str, List[Tuple[float, int]]] = {}
        self._timeline_keys: Dict[str, List[float]] = {}
        self._timelines_sorted: Dict[str, bool] = {}

    def ingest_record(
        self,
        event_id: Any,
        event_type: str = "",
        source_system: str = "",
        timestamp_epoch: float = 0.0,
        artifact_hash: Optional[str] = None,
        copy_id: Optional[str] = None,
        device_id: Optional[str] = None,
        subject_id: Optional[str] = None,
        network_id: Optional[str] = None,
        tenant_id: str = "default_tenant",
        payload_summary: str = ""
    ) -> int:
        with self._lock:
            if isinstance(event_id, CompactTelemetryRecord):
                rec = event_id
                event_id = rec.event_id
                event_type = rec.event_type
                source_system = rec.source_system
                timestamp_epoch = rec.timestamp_epoch
                artifact_hash = rec.artifact_hash
                copy_id = rec.copy_id
                device_id = rec.device_id
                subject_id = rec.subject_id
                network_id = rec.network_id
                tenant_id = rec.tenant_id
                payload_summary = rec.payload_summary
            else:
                rec = None

            if event_id in self._by_id:
                return self._by_id[event_id]

            idx = len(self._records)
            if rec is None:
                rec = CompactTelemetryRecord(
                    event_id=event_id,
                    event_type=event_type,
                    source_system=source_system,
                    artifact_hash=artifact_hash,
                    copy_id=copy_id,
                    device_id=device_id,
                    subject_id=subject_id,
                    network_id=network_id,
                    timestamp_epoch=timestamp_epoch,
                    tenant_id=tenant_id,
                    payload_summary=payload_summary
                )
            self._records.append(rec)
            self._by_id[event_id] = idx

            # Update tenant partition
            self._by_tenant.setdefault(tenant_id, []).append(idx)

            # Update secondary inverted indexes
            if artifact_hash:
                self._by_hash.setdefault((tenant_id, artifact_hash), []).append(idx)
            if copy_id:
                self._by_copy.setdefault((tenant_id, copy_id), []).append(idx)
            if device_id:
                self._by_device.setdefault((tenant_id, device_id), []).append(idx)
            if subject_id:
                self._by_actor.setdefault((tenant_id, subject_id), []).append(idx)
            if network_id:
                self._by_network.setdefault((tenant_id, network_id), []).append(idx)
            self._by_type.setdefault((tenant_id, event_type), []).append(idx)

            # Update timeline
            tl = self._timelines.setdefault(tenant_id, [])
            tl.append((timestamp_epoch, idx))
            self._timelines_sorted[tenant_id] = False

            return idx

    def ingest_batch(self, records: List[Dict[str, Any]], tenant_id: str = "default_tenant") -> int:
        count = 0
        with self._lock:
            for r in records:
                self.ingest_record(
                    event_id=r["event_id"],
                    event_type=r.get("event_type", "GENERIC_EVENT"),
                    source_system=r.get("source_system", "EDR"),
                    timestamp_epoch=r.get("timestamp_epoch", time.time()),
                    artifact_hash=r.get("artifact_hash"),
                    copy_id=r.get("copy_id"),
                    device_id=r.get("device_id"),
                    subject_id=r.get("subject_id"),
                    network_id=r.get("network_id"),
                    tenant_id=tenant_id,
                    payload_summary=r.get("payload_summary", "")
                )
                count += 1
            self._ensure_sorted_timeline(tenant_id)
        return count

    def _ensure_sorted_timeline(self, tenant_id: str) -> None:
        if not self._timelines_sorted.get(tenant_id, True):
            self._timelines[tenant_id].sort(key=lambda x: x[0])
            self._timeline_keys[tenant_id] = [x[0] for x in self._timelines[tenant_id]]
            self._timelines_sorted[tenant_id] = True

    def query_by_copy_id(
        self,
        copy_id: str,
        tenant_id: str = "default_tenant"
    ) -> List[CompactTelemetryRecord]:
        with self._lock:
            indices = self._by_copy.get((tenant_id, copy_id), [])
            return [self._records[i] for i in indices]

    def query_by_artifact_hash(
        self,
        artifact_hash: str,
        tenant_id: str = "default_tenant"
    ) -> List[CompactTelemetryRecord]:
        with self._lock:
            indices = self._by_hash.get((tenant_id, artifact_hash), [])
            return [self._records[i] for i in indices]

    def query_by_device_id(
        self,
        device_id: str,
        tenant_id: str = "default_tenant"
    ) -> List[CompactTelemetryRecord]:
        with self._lock:
            indices = self._by_device.get((tenant_id, device_id), [])
            return [self._records[i] for i in indices]

    def query_by_actor(
        self,
        actor_id: str,
        tenant_id: str = "default_tenant"
    ) -> List[CompactTelemetryRecord]:
        with self._lock:
            indices = self._by_actor.get((tenant_id, actor_id), [])
            return [self._records[i] for i in indices]

    def query_time_window(
        self,
        start_epoch: float,
        end_epoch: float,
        tenant_id: str = "default_tenant"
    ) -> List[CompactTelemetryRecord]:
        """
        O(log N + K) binary search window query using bisect on pre-indexed timeline keys.
        Avoids allocating a new keys list on each query.
        """
        with self._lock:
            self._ensure_sorted_timeline(tenant_id)
            tl = self._timelines.get(tenant_id, [])
            if not tl:
                return []

            keys = self._timeline_keys.get(tenant_id)
            if keys is None or len(keys) != len(tl):
                keys = [item[0] for item in tl]
                self._timeline_keys[tenant_id] = keys

            left = bisect.bisect_left(keys, start_epoch)
            right = bisect.bisect_right(keys, end_epoch)

            return [self._records[tl[i][1]] for i in range(left, right)]

    def count(self, tenant_id: Optional[str] = None) -> int:
        with self._lock:
            if tenant_id:
                return len(self._by_tenant.get(tenant_id, []))
            return len(self._records)

    def clear(self) -> None:
        with self._lock:
            self._records.clear()
            self._by_id.clear()
            self._by_hash.clear()
            self._by_copy.clear()
            self._by_device.clear()
            self._by_actor.clear()
            self._by_network.clear()
            self._by_type.clear()
            self._by_tenant.clear()
            self._timelines.clear()
            self._timeline_keys.clear()
            self._timelines_sorted.clear()


default_scalable_telemetry = ScalableTelemetryProvider()
