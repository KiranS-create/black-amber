"""
AegisTrace External Telemetry Provider Interface and In-Memory Indexer.

Defines the pluggable abstraction for querying and ingesting telemetry events,
with a multi-indexed in-memory provider optimized for fast forensic lookups.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Set
import bisect

from core.telemetry.event import ForensicEvent
from core.telemetry.models import TelemetrySource, IntegrityLevel


class ExternalTelemetryProvider(ABC):
    """
    Abstract interface for external telemetry providers (EDR, SIEM, CloudTrail, etc.).
    """

    @abstractmethod
    def ingest_event(self, event: ForensicEvent) -> None:
        """Ingest a single forensic event."""
        pass

    @abstractmethod
    def ingest_batch(self, events: List[ForensicEvent]) -> None:
        """Ingest a batch of forensic events."""
        pass

    @abstractmethod
    def query_by_artifact_hash(
        self,
        artifact_hash: str,
        window_start: Optional[datetime] = None,
        window_end: Optional[datetime] = None,
    ) -> List[ForensicEvent]:
        """Find events referencing a specific artifact SHA-256 hash."""
        pass

    @abstractmethod
    def query_by_copy_id(
        self,
        copy_id: str,
        window_start: Optional[datetime] = None,
        window_end: Optional[datetime] = None,
    ) -> List[ForensicEvent]:
        """Find events referencing a recipient-specific copy ID."""
        pass

    @abstractmethod
    def query_by_device_id(
        self,
        device_id: str,
        window_start: Optional[datetime] = None,
        window_end: Optional[datetime] = None,
    ) -> List[ForensicEvent]:
        """Find events associated with a specific endpoint or peripheral device."""
        pass

    @abstractmethod
    def query_by_actor(
        self,
        actor_id: str,
        window_start: Optional[datetime] = None,
        window_end: Optional[datetime] = None,
    ) -> List[ForensicEvent]:
        """Find events associated with a specific enterprise account or actor ID."""
        pass

    @abstractmethod
    def query_by_network(
        self,
        network_id: str,
        window_start: Optional[datetime] = None,
        window_end: Optional[datetime] = None,
    ) -> List[ForensicEvent]:
        """Find events associated with a source or destination IP/CIDR."""
        pass

    @abstractmethod
    def query_events(
        self,
        source: Optional[TelemetrySource] = None,
        event_type: Optional[str] = None,
        window_start: Optional[datetime] = None,
        window_end: Optional[datetime] = None,
    ) -> List[ForensicEvent]:
        """Generic filtered query."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Total number of events stored."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all indexed events."""
        pass


class InMemoryTelemetryProvider(ExternalTelemetryProvider):
    """
    High-performance in-memory telemetry store with multi-attribute inverted indexes
    and chronological indexing.
    """

    def __init__(self):
        self._events: Dict[str, ForensicEvent] = {}
        self._by_hash: Dict[str, Set[str]] = {}
        self._by_copy: Dict[str, Set[str]] = {}
        self._by_device: Dict[str, Set[str]] = {}
        self._by_actor: Dict[str, Set[str]] = {}
        self._by_network: Dict[str, Set[str]] = {}
        self._by_source: Dict[TelemetrySource, Set[str]] = {}
        self._by_event_type: Dict[str, Set[str]] = {}

        # Chronological index: list of tuples (timestamp_epoch, event_id)
        self._timeline: List[tuple] = []
        self._is_sorted: bool = True

    def ingest_event(self, event: ForensicEvent) -> None:
        eid = event.event_id
        if eid in self._events:
            # Event already present, skip or update
            return

        self._events[eid] = event

        # Index by artifact hash
        if event.artifact_hash:
            self._by_hash.setdefault(event.artifact_hash, set()).add(eid)

        # Index by copy ID
        if event.copy_id:
            self._by_copy.setdefault(event.copy_id, set()).add(eid)

        # Index by device ID
        if event.device_id:
            self._by_device.setdefault(event.device_id, set()).add(eid)

        # Index by subject / actor ID
        if event.subject_id:
            self._by_actor.setdefault(event.subject_id, set()).add(eid)

        # Index by network ID
        if event.network_id:
            self._by_network.setdefault(event.network_id, set()).add(eid)

        # Index by source system
        self._by_source.setdefault(event.source_system, set()).add(eid)

        # Index by event type
        self._by_event_type.setdefault(event.event_type, set()).add(eid)

        # Timeline entry
        ts = event.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        epoch = ts.timestamp()
        self._timeline.append((epoch, eid))
        self._is_sorted = False

    def ingest_batch(self, events: List[ForensicEvent]) -> None:
        for ev in events:
            self.ingest_event(ev)
        self._sort_timeline()

    def _sort_timeline(self):
        if not self._is_sorted:
            self._timeline.sort(key=lambda x: x[0])
            self._is_sorted = True

    def _filter_time_window(
        self,
        event_ids: Set[str],
        window_start: Optional[datetime] = None,
        window_end: Optional[datetime] = None,
    ) -> List[ForensicEvent]:
        start_epoch = window_start.timestamp() if window_start else None
        end_epoch = window_end.timestamp() if window_end else None

        results = []
        for eid in event_ids:
            ev = self._events.get(eid)
            if not ev:
                continue
            ts = ev.timestamp
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            ep = ts.timestamp()
            if start_epoch is not None and ep < start_epoch:
                continue
            if end_epoch is not None and ep > end_epoch:
                continue
            results.append(ev)

        # Return in chronological order
        results.sort(key=lambda x: x.timestamp)
        return results

    def query_by_artifact_hash(
        self,
        artifact_hash: str,
        window_start: Optional[datetime] = None,
        window_end: Optional[datetime] = None,
    ) -> List[ForensicEvent]:
        matching_ids = self._by_hash.get(artifact_hash, set())
        return self._filter_time_window(matching_ids, window_start, window_end)

    def query_by_copy_id(
        self,
        copy_id: str,
        window_start: Optional[datetime] = None,
        window_end: Optional[datetime] = None,
    ) -> List[ForensicEvent]:
        matching_ids = self._by_copy.get(copy_id, set())
        return self._filter_time_window(matching_ids, window_start, window_end)

    def query_by_device_id(
        self,
        device_id: str,
        window_start: Optional[datetime] = None,
        window_end: Optional[datetime] = None,
    ) -> List[ForensicEvent]:
        matching_ids = self._by_device.get(device_id, set())
        return self._filter_time_window(matching_ids, window_start, window_end)

    def query_by_actor(
        self,
        actor_id: str,
        window_start: Optional[datetime] = None,
        window_end: Optional[datetime] = None,
    ) -> List[ForensicEvent]:
        matching_ids = self._by_actor.get(actor_id, set())
        return self._filter_time_window(matching_ids, window_start, window_end)

    def query_by_network(
        self,
        network_id: str,
        window_start: Optional[datetime] = None,
        window_end: Optional[datetime] = None,
    ) -> List[ForensicEvent]:
        matching_ids = self._by_network.get(network_id, set())
        return self._filter_time_window(matching_ids, window_start, window_end)

    def query_events(
        self,
        source: Optional[TelemetrySource] = None,
        event_type: Optional[str] = None,
        window_start: Optional[datetime] = None,
        window_end: Optional[datetime] = None,
    ) -> List[ForensicEvent]:
        candidate_ids: Optional[Set[str]] = None

        if source is not None:
            candidate_ids = set(self._by_source.get(source, set()))

        if event_type is not None:
            type_ids = self._by_event_type.get(event_type, set())
            if candidate_ids is None:
                candidate_ids = set(type_ids)
            else:
                candidate_ids &= type_ids

        if candidate_ids is None:
            candidate_ids = set(self._events.keys())

        return self._filter_time_window(candidate_ids, window_start, window_end)

    def count(self) -> int:
        return len(self._events)

    def clear(self) -> None:
        self._events.clear()
        self._by_hash.clear()
        self._by_copy.clear()
        self._by_device.clear()
        self._by_actor.clear()
        self._by_network.clear()
        self._by_source.clear()
        self._by_event_type.clear()
        self._timeline.clear()
        self._is_sorted = True
