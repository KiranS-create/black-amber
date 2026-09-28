"""
SIH26237 - External Telemetry Integration Adapter
Provides integration with enterprise telemetry sources (EDR, CASB, DLP)
to corroborate forensic observations and bridge from Level 4 (Copy Lineage)
to Level 5 (Resolved Human Identity) only when external corroboration is present.
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class TelemetryEventType(str, Enum):
    FILE_ACCESS = "FILE_ACCESS"
    FILE_WRITE = "FILE_WRITE"
    CLIPBOARD_COPY = "CLIPBOARD_COPY"
    SCREENSHOT_TAKEN = "SCREENSHOT_TAKEN"
    PROCESS_EXECUTION = "PROCESS_EXECUTION"
    NETWORK_EXFILTRATION = "NETWORK_EXFILTRATION"
    REMOVABLE_MEDIA_WRITE = "REMOVABLE_MEDIA_WRITE"
    PRINT_JOB_SPOOLED = "PRINT_JOB_SPOOLED"


class TelemetryEvent(BaseModel):
    event_id: str
    event_type: TelemetryEventType
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    principal_id: Optional[str] = None
    identity_id: Optional[str] = None
    device_id: Optional[str] = None
    source_process: Optional[str] = None
    target_destination: Optional[str] = None
    file_hash: Optional[str] = None
    confidence: float = 1.0
    raw_telemetry: Dict[str, Any] = Field(default_factory=dict)


class ExternalTelemetryProvider:
    """
    Interface for ingesting and querying enterprise host/network telemetry.
    """

    def query_events(
        self,
        principal_id: Optional[str] = None,
        device_id: Optional[str] = None,
        event_types: Optional[List[TelemetryEventType]] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> List[TelemetryEvent]:
        raise NotImplementedError

    def corroborate_leak(
        self,
        candidate_principal_id: str,
        leak_approx_timestamp: str,
        expected_events: Optional[List[TelemetryEventType]] = None,
    ) -> Tuple[bool, float, List[TelemetryEvent]]:
        """
        Determines whether external host/network telemetry corroborates that
        the candidate principal executed an exfiltration action (e.g. print, screenshot, USB copy).
        Returns (corroborated: bool, confidence: float, matching_events: List[TelemetryEvent]).
        """
        raise NotImplementedError


class MockTelemetryProvider(ExternalTelemetryProvider):
    """
    Deterministic telemetry provider for testing and validation.
    """

    def __init__(self):
        self._events: List[TelemetryEvent] = []

    def record_event(self, event: TelemetryEvent) -> None:
        self._events.append(event)

    def query_events(
        self,
        principal_id: Optional[str] = None,
        device_id: Optional[str] = None,
        event_types: Optional[List[TelemetryEventType]] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> List[TelemetryEvent]:
        results = []
        for ev in self._events:
            if principal_id and ev.principal_id != principal_id:
                continue
            if device_id and ev.device_id != device_id:
                continue
            if event_types and ev.event_type not in event_types:
                continue
            results.append(ev)
        return results

    def corroborate_leak(
        self,
        candidate_principal_id: str,
        leak_approx_timestamp: str,
        expected_events: Optional[List[TelemetryEventType]] = None,
    ) -> Tuple[bool, float, List[TelemetryEvent]]:
        types = expected_events or [
            TelemetryEventType.SCREENSHOT_TAKEN,
            TelemetryEventType.PRINT_JOB_SPOOLED,
            TelemetryEventType.REMOVABLE_MEDIA_WRITE,
            TelemetryEventType.NETWORK_EXFILTRATION,
        ]
        matching = [
            ev for ev in self._events
            if ev.principal_id == candidate_principal_id and ev.event_type in types
        ]
        if matching:
            avg_conf = sum(e.confidence for e in matching) / len(matching)
            return True, avg_conf, matching
        return False, 0.0, []
