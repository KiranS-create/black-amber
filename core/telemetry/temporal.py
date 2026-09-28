"""
AegisTrace Temporal Correlation & Causal Predecessor Engine.

Validates event causality, compensates for network/endpoint clock skew,
deduplicates multi-sensor alerts from single user actions to prevent score
inflation, and constructs structured timelines (OBSERVED, DERIVED, UNKNOWN).
"""

from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple, Set
from pydantic import BaseModel, Field

from core.telemetry.event import ForensicEvent
from core.telemetry.models import TelemetrySource, IntegrityLevel


class TimelineEntryType(str, Enum):
    OBSERVED = "OBSERVED"   # Direct sensor/log event
    DERIVED = "DERIVED"     # Inferred causal transition between observed events
    UNKNOWN = "UNKNOWN"     # Unaccounted temporal gap where custody was unmonitored


class TimelineEntry(BaseModel):
    entry_id: str
    entry_type: TimelineEntryType
    timestamp_start: datetime
    timestamp_end: datetime
    description: str
    event_ids: List[str] = Field(default_factory=list)
    confidence: float = 1.0
    gap_duration_seconds: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CausalValidationResult(BaseModel):
    is_valid: bool
    clock_skew_seconds: float = 0.0
    violation_reason: Optional[str] = None
    tolerance_applied: float = 0.0


class TemporalCorrelationEngine:
    """
    Engine for causal validation, deduplication, and timeline reconstruction.
    """

    def __init__(
        self,
        default_clock_skew_tolerance_sec: float = 60.0,
        dedup_window_sec: float = 5.0,
        gap_threshold_sec: float = 300.0,  # 5 minutes without telemetry constitutes an UNKNOWN gap
    ):
        self.skew_tolerance_sec = default_clock_skew_tolerance_sec
        self.dedup_window_sec = dedup_window_sec
        self.gap_threshold_sec = gap_threshold_sec

    def validate_causal_pair(
        self,
        earlier_event: ForensicEvent,
        later_event: ForensicEvent,
        skew_tolerance_sec: Optional[float] = None,
    ) -> CausalValidationResult:
        """
        Validate that earlier_event actually preceded later_event,
        accounting for allowable clock skew.
        """
        tol = skew_tolerance_sec if skew_tolerance_sec is not None else self.skew_tolerance_sec
        t1 = earlier_event.timestamp
        t2 = later_event.timestamp
        if t1.tzinfo is None:
            t1 = t1.replace(tzinfo=timezone.utc)
        if t2.tzinfo is None:
            t2 = t2.replace(tzinfo=timezone.utc)

        delta = (t2 - t1).total_seconds()
        # If delta is negative, later_event is timestamped earlier than earlier_event
        if delta < -tol:
            return CausalValidationResult(
                is_valid=False,
                clock_skew_seconds=abs(delta),
                violation_reason=(
                    f"Causal violation: event '{later_event.event_id}' ({later_event.event_type}) "
                    f"timestamped {abs(delta):.2f}s BEFORE predecessor '{earlier_event.event_id}' "
                    f"(tolerance: {tol}s)"
                ),
                tolerance_applied=tol,
            )

        return CausalValidationResult(
            is_valid=True,
            clock_skew_seconds=max(0.0, -delta),
            violation_reason=None,
            tolerance_applied=tol,
        )

    def deduplicate_events(
        self,
        events: List[ForensicEvent],
        window_sec: Optional[float] = None,
    ) -> List[ForensicEvent]:
        """
        Deduplicate concurrent multi-sensor events resulting from the same physical action.
        e.g., EDR file write + DLP policy alert + audit log within 5 seconds for the same
        artifact/resource and actor.

        Retains the highest integrity event and aggregates references in raw_payload
        without inflating candidate evidence count.
        """
        if not events:
            return []

        w_sec = window_sec if window_sec is not None else self.dedup_window_sec
        sorted_events = sorted(events, key=lambda x: x.timestamp)
        deduped: List[ForensicEvent] = []

        def are_concurrent_duplicates(e1: ForensicEvent, e2: ForensicEvent) -> bool:
            # Same artifact hash or same resource or same copy ID
            shared_artifact = (
                (e1.artifact_hash and e2.artifact_hash and e1.artifact_hash == e2.artifact_hash) or
                (e1.copy_id and e2.copy_id and e1.copy_id == e2.copy_id) or
                (e1.resource_id and e2.resource_id and e1.resource_id == e2.resource_id)
            )
            if not shared_artifact:
                return False

            # Same actor or same device
            shared_actor_or_dev = (
                (e1.subject_id and e2.subject_id and e1.subject_id == e2.subject_id) or
                (e1.device_id and e2.device_id and e1.device_id == e2.device_id)
            )
            if not shared_actor_or_dev:
                return False

            # Within time window
            t1 = e1.timestamp.replace(tzinfo=timezone.utc) if e1.timestamp.tzinfo is None else e1.timestamp
            t2 = e2.timestamp.replace(tzinfo=timezone.utc) if e2.timestamp.tzinfo is None else e2.timestamp
            return abs((t2 - t1).total_seconds()) <= w_sec

        for ev in sorted_events:
            ev_ts = ev.timestamp.replace(tzinfo=timezone.utc) if ev.timestamp.tzinfo is None else ev.timestamp
            merged = False
            for existing in reversed(deduped):
                ex_ts = existing.timestamp.replace(tzinfo=timezone.utc) if existing.timestamp.tzinfo is None else existing.timestamp
                if (ev_ts - ex_ts).total_seconds() > w_sec:
                    break
                if are_concurrent_duplicates(existing, ev):
                    merged_refs = existing.raw_payload.setdefault("concurrent_telemetry_sources", [])
                    merged_refs.append({
                        "event_id": ev.event_id,
                        "source": ev.source_system.value,
                        "event_type": ev.event_type,
                        "timestamp": ev.timestamp.isoformat(),
                    })
                    if ev.source_reliability > existing.source_reliability:
                        existing.source_reliability = ev.source_reliability
                    merged = True
                    break

            if not merged:
                deduped.append(ev)

        return deduped

    def build_timeline(
        self,
        events: List[ForensicEvent],
        initial_release_time: Optional[datetime] = None,
        final_leak_time: Optional[datetime] = None,
    ) -> List[TimelineEntry]:
        """
        Construct structured timeline with OBSERVED, DERIVED, and UNKNOWN entries.
        """
        if not events:
            if initial_release_time and final_leak_time:
                t1 = initial_release_time.replace(tzinfo=timezone.utc) if initial_release_time.tzinfo is None else initial_release_time
                t2 = final_leak_time.replace(tzinfo=timezone.utc) if final_leak_time.tzinfo is None else final_leak_time
                gap = (t2 - t1).total_seconds()
                return [
                    TimelineEntry(
                        entry_id="gap-initial-to-leak",
                        entry_type=TimelineEntryType.UNKNOWN,
                        timestamp_start=t1,
                        timestamp_end=t2,
                        description="Complete custody gap between initial release and observed leak",
                        gap_duration_seconds=gap,
                    )
                ]
            return []

        sorted_events = sorted(events, key=lambda x: x.timestamp)
        timeline: List[TimelineEntry] = []

        # Check gap between initial release and first event
        if initial_release_time:
            t0 = initial_release_time.replace(tzinfo=timezone.utc) if initial_release_time.tzinfo is None else initial_release_time
            first_ts = sorted_events[0].timestamp
            if first_ts.tzinfo is None:
                first_ts = first_ts.replace(tzinfo=timezone.utc)
            gap = (first_ts - t0).total_seconds()
            if gap > self.gap_threshold_sec:
                timeline.append(
                    TimelineEntry(
                        entry_id="gap-pre-custody",
                        entry_type=TimelineEntryType.UNKNOWN,
                        timestamp_start=t0,
                        timestamp_end=first_ts,
                        description=f"Initial custody gap ({gap:.0f}s) between release and first observed event",
                        gap_duration_seconds=gap,
                    )
                )

        # Iterate events
        for i, ev in enumerate(sorted_events):
            ev_ts = ev.timestamp.replace(tzinfo=timezone.utc) if ev.timestamp.tzinfo is None else ev.timestamp
            timeline.append(
                TimelineEntry(
                    entry_id=f"entry-{ev.event_id}",
                    entry_type=TimelineEntryType.OBSERVED,
                    timestamp_start=ev_ts,
                    timestamp_end=ev_ts,
                    description=f"{ev.source_system.value}: {ev.event_type} on {ev.resource_id or ev.device_id or 'unknown'}",
                    event_ids=[ev.event_id],
                    confidence=ev.source_reliability,
                    metadata={"source": ev.source_system.value, "integrity": ev.integrity_status.value},
                )
            )

            # Check gap to next event
            if i < len(sorted_events) - 1:
                next_ev = sorted_events[i + 1]
                next_ts = next_ev.timestamp.replace(tzinfo=timezone.utc) if next_ev.timestamp.tzinfo is None else next_ev.timestamp
                diff = (next_ts - ev_ts).total_seconds()
                if diff > self.gap_threshold_sec:
                    timeline.append(
                        TimelineEntry(
                            entry_id=f"gap-{ev.event_id}-to-{next_ev.event_id}",
                            entry_type=TimelineEntryType.UNKNOWN,
                            timestamp_start=ev_ts,
                            timestamp_end=next_ts,
                            description=f"Unmonitored interval ({diff:.0f}s) between events",
                            gap_duration_seconds=diff,
                        )
                    )
                elif diff > 0:
                    # Inferred causal transition
                    timeline.append(
                        TimelineEntry(
                            entry_id=f"derived-{ev.event_id}-to-{next_ev.event_id}",
                            entry_type=TimelineEntryType.DERIVED,
                            timestamp_start=ev_ts,
                            timestamp_end=next_ts,
                            description=f"Derived transition from {ev.source_system.value} to {next_ev.source_system.value}",
                            event_ids=[ev.event_id, next_ev.event_id],
                            confidence=min(ev.source_reliability, next_ev.source_reliability) * 0.9,
                        )
                    )

        # Check gap after last event to final leak
        if final_leak_time:
            last_ts = sorted_events[-1].timestamp
            if last_ts.tzinfo is None:
                last_ts = last_ts.replace(tzinfo=timezone.utc)
            tf = final_leak_time.replace(tzinfo=timezone.utc) if final_leak_time.tzinfo is None else final_leak_time
            gap = (tf - last_ts).total_seconds()
            if gap > self.gap_threshold_sec:
                timeline.append(
                    TimelineEntry(
                        entry_id="gap-post-telemetry",
                        entry_type=TimelineEntryType.UNKNOWN,
                        timestamp_start=last_ts,
                        timestamp_end=tf,
                        description=f"Final unobserved gap ({gap:.0f}s) before public leak appearance",
                        gap_duration_seconds=gap,
                    )
                )

        return timeline
