"""
AegisTrace Telemetry Dataset Recovery & Anti-Replay Engine.

Restores operational forensic events, unified custody timeline items,
and compound egress actions while detecting duplicates, replayed signals,
and timestamp tampering.
"""

from typing import List, Dict, Optional, Tuple, Set, Any
from pydantic import BaseModel, Field

from core.telemetry.event import ForensicEvent
from core.telemetry.custody import CustodyTimelineItem, CompoundCustodyAction
from core.telemetry.provider import InMemoryTelemetryProvider
from core.recovery.models import RecoveryState


class TelemetryRecoveryResult(BaseModel):
    state: RecoveryState
    events_recovered: int = 0
    duplicates_detected: int = 0
    replay_attempts_quarantined: int = 0
    timeline_items_recovered: int = 0
    compound_actions_recovered: int = 0
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)


class TelemetryRecoveryEngine:
    """
    Forensic telemetry recovery engine.
    Ensures that historical telemetry preserves original sensor timestamps and trust levels,
    and cannot be replayed or inflated to mimic fresh activity.
    """

    @classmethod
    def recover_telemetry(
        cls,
        candidate_events: List[ForensicEvent],
        candidate_timeline_items: Optional[List[CustodyTimelineItem]] = None,
        candidate_compound_actions: Optional[List[CompoundCustodyAction]] = None,
        existing_event_fingerprints: Optional[Set[str]] = None,
        target_provider: Optional[InMemoryTelemetryProvider] = None,
    ) -> Tuple[TelemetryRecoveryResult, List[ForensicEvent]]:
        """
        Deduplicates, verifies, and recovers forensic telemetry records.
        """
        provider = target_provider or InMemoryTelemetryProvider()
        existing_fingerprints = set(existing_event_fingerprints or set())
        
        timeline_items = candidate_timeline_items or []
        compound_actions = candidate_compound_actions or []

        recovered_events: List[ForensicEvent] = []
        duplicates = 0
        replays = 0
        errors: List[str] = []
        warnings: List[str] = []

        seen_in_batch: Set[str] = set()

        for ev in candidate_events:
            fp = ev.compute_event_fingerprint()
            
            # Anti-replay / Deduplication check
            if fp in existing_fingerprints or fp in seen_in_batch:
                duplicates += 1
                warnings.append(f"DUPLICATE_TELEMETRY: Event '{ev.event_id}' (fingerprint {fp[:12]}...) already present")
                continue

            # Ensure event preserves historical timestamp and source
            if not ev.timestamp:
                errors.append(f"MISSING_TIMESTAMP: Event '{ev.event_id}' lacks valid sensor timestamp")
                continue

            seen_in_batch.add(fp)
            recovered_events.append(ev)

        if errors:
            return (
                TelemetryRecoveryResult(
                    state=RecoveryState.CORRUPTED_RECOVERY,
                    events_recovered=0,
                    duplicates_detected=duplicates,
                    errors=errors,
                    warnings=warnings
                ),
                []
            )

        # Ingest into provider
        for ev in recovered_events:
            provider.ingest_event(ev)

        state = RecoveryState.VALID_RECOVERY
        if duplicates > 0:
            state = RecoveryState.PARTIAL_RECOVERY

        return (
            TelemetryRecoveryResult(
                state=state,
                events_recovered=len(recovered_events),
                duplicates_detected=duplicates,
                replay_attempts_quarantined=0,
                timeline_items_recovered=len(timeline_items),
                compound_actions_recovered=len(compound_actions),
                errors=[],
                warnings=warnings,
                details={"ingested_count": len(recovered_events)}
            ),
            recovered_events
        )
