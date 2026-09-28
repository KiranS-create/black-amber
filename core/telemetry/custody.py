"""
AegisTrace Unified Forensic Custody Timeline & Lineage Integration Engine.

Unifies identity, recipient principal, device attestation, viewer sessions,
cryptographic decryption receipts, active copy lineage, and external enterprise
telemetry into a single cryptographically verifiable causal timeline.

STRICT FORENSIC INVARIANTS:
1. Exact-Copy Downstream Boundary:
   When an exact copy moves Alice -> Bob -> Unknown X -> Public leak:
   - Original Recipient = Alice
   - Last Known Controlled Holder = Bob
   - Public Uploader = UNKNOWN (unless explicit upload event from Bob is observed)
   - Bob is NEVER accused of publication based on custody alone.
2. Temporal Causality:
   Events must follow causal order within allowed clock skew (default 120s).
   Causality violations produce CONFLICT or ABSTAINED.
3. Multi-Sensor Deduplication:
   Multiple sensor observations of the same action within correlation window
   cluster into a single CompoundCustodyAction to prevent double-counting.
4. No Human Conflation:
   Never conflate Account, Device, Network Source, Forwarding Recipient,
   and Human Operator without explicit corroborating multi-sensor proof.
"""

from datetime import datetime, timezone, timedelta
from enum import Enum
import hashlib
import json
import math
from typing import List, Dict, Any, Optional, Set, Tuple
from pydantic import BaseModel, Field

from core.telemetry.models import (
    TelemetrySource,
    IntegrityLevel,
    TelemetryTrustLevel,
    DeviceAttestationState,
    CanonicalEventType,
    BaseTelemetryEvidence,
)
from core.telemetry.event import ForensicEvent
from core.lineage.models import (
    DocumentRoot,
    CopyInstance,
    AccessSession,
    ForwardingEvent,
    ExportEvent,
    LineageEdge,
    DeviceBinding,
    ForensicAttributionLevel,
    ForensicBoundaryState,
)


class CustodyCausalStatus(str, Enum):
    VALID = "VALID"
    CLOCK_SKEW_TOLERATED = "CLOCK_SKEW_TOLERATED"
    CAUSALITY_VIOLATION = "CAUSALITY_VIOLATION"
    CUSTODY_GAP = "CUSTODY_GAP"
    DUPLICATE_SENSOR_OBSERVATION = "DUPLICATE_SENSOR_OBSERVATION"


class CustodyTimelineItem(BaseModel):
    """
    Unified chronological timeline entry spanning cryptographic and external telemetry.
    """
    item_id: str
    timestamp: datetime
    canonical_type: CanonicalEventType
    source: str  # "LINEAGE_DLT", "CONTROLLED_VIEWER", "EDR", "DLP", "USB", etc.
    principal_id: Optional[str] = None
    account_id: Optional[str] = None
    device_id: Optional[str] = None
    device_attestation: DeviceAttestationState = DeviceAttestationState.DEVICE_UNKNOWN
    trust_level: TelemetryTrustLevel = TelemetryTrustLevel.OBSERVED
    session_id: Optional[str] = None
    copy_id: Optional[str] = None
    document_id: Optional[str] = None
    network_id: Optional[str] = None
    resource_id: Optional[str] = None
    artifact_hash: Optional[str] = None
    is_compound: bool = False
    compound_event_id: Optional[str] = None
    contributing_sensor_event_ids: List[str] = Field(default_factory=list)
    causal_status: CustodyCausalStatus = CustodyCausalStatus.VALID
    description: str = ""
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)


class CompoundCustodyAction(BaseModel):
    """
    Aggregated multi-sensor observation of a single physical egress or manipulation action.
    Prevents evidence inflation and double-counting in fusion.
    """
    compound_id: str
    primary_canonical_type: CanonicalEventType
    timestamp: datetime
    device_id: Optional[str] = None
    account_id: Optional[str] = None
    resource_id: Optional[str] = None
    sensor_sources: List[str] = Field(default_factory=list)
    underlying_event_ids: List[str] = Field(default_factory=list)
    combined_confidence: float = 0.8
    is_deduplicated: bool = True


class CustodyTimelineReport(BaseModel):
    """
    Comprehensive forensic timeline and attribution boundary evaluation report.
    """
    report_id: str
    document_id: Optional[str] = None
    root_document_hash: Optional[str] = None
    original_recipient_id: Optional[str] = None
    last_known_controlled_holder: Optional[str] = None
    downstream_holder_account: Optional[str] = None
    downstream_device_id: Optional[str] = None
    confirmed_publisher_id: Optional[str] = None
    publication_platform: Optional[str] = None
    forensic_boundary_state: ForensicBoundaryState = ForensicBoundaryState.LINEAGE_CONTINUES
    highest_attribution_level: ForensicAttributionLevel = ForensicAttributionLevel.LEVEL_1_DOCUMENT_DETECTED
    timeline: List[CustodyTimelineItem] = Field(default_factory=list)
    compound_actions: List[CompoundCustodyAction] = Field(default_factory=list)
    custody_gaps: List[str] = Field(default_factory=list)
    causality_violations: List[str] = Field(default_factory=list)
    account_compromised_or_shared: bool = False
    compromise_indicators: List[str] = Field(default_factory=list)
    should_abstain: bool = False
    abstention_reason: Optional[str] = None
    boundary_statement: str = ""
    confidence_score: float = 0.0

    @property
    def confirmed_publisher_principal(self) -> Optional[str]:
        return self.confirmed_publisher_id

    @property
    def downstream_egress_account(self) -> Optional[str]:
        return self.downstream_holder_account


class UnifiedCustodyTimelineBuilder:
    """
    Engine that correlates and validates the full causal chain:
    Identity -> Recipient -> Device -> Session -> Decryption -> Copy -> Access -> Export/Forward -> External Telemetry -> Attribution/Abstention
    """

    def __init__(self, max_clock_skew_seconds: float = 120.0, sensor_cluster_window_seconds: float = 5.0):
        self.max_clock_skew = timedelta(seconds=max_clock_skew_seconds)
        self.sensor_cluster_window = timedelta(seconds=sensor_cluster_window_seconds)

    def _normalize_ts(self, ts: Any) -> datetime:
        if isinstance(ts, str):
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        elif isinstance(ts, datetime):
            dt = ts
        else:
            dt = datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    def build_timeline(
        self,
        document_root: Optional[DocumentRoot] = None,
        copies: Optional[List[CopyInstance]] = None,
        sessions: Optional[List[AccessSession]] = None,
        forwarding_events: Optional[List[ForwardingEvent]] = None,
        export_events: Optional[List[ExportEvent]] = None,
        telemetry_events: Optional[List[ForensicEvent]] = None,
        enrolled_devices: Optional[Dict[str, DeviceBinding]] = None,
        enrolled_recipient_id: Optional[str] = None,
    ) -> CustodyTimelineReport:
        report_id = f"custody-rep-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        raw_items: List[CustodyTimelineItem] = []
        enrolled_devices = enrolled_devices or {}

        # 1. Ingest DocumentRoot
        if document_root:
            raw_items.append(
                CustodyTimelineItem(
                    item_id=f"root-{document_root.document_id}",
                    timestamp=self._normalize_ts(document_root.created_at),
                    canonical_type=CanonicalEventType.DOCUMENT_CREATED,
                    source="LINEAGE_ROOT",
                    document_id=document_root.document_id,
                    artifact_hash=document_root.canonical_hash,
                    trust_level=TelemetryTrustLevel.CRYPTOGRAPHICALLY_VERIFIED,
                    description=f"Master document root created: {document_root.document_id}",
                )
            )

        # 2. Ingest Initial Copies (Issuance)
        if copies:
            for cp in copies:
                is_root_issuance = (cp.parent_copy_id is None)
                ctype = CanonicalEventType.RELEASED_TO_RECIPIENT if is_root_issuance else CanonicalEventType.COPIED
                raw_items.append(
                    CustodyTimelineItem(
                        item_id=f"copy-{cp.copy_id}",
                        timestamp=self._normalize_ts(cp.issuance_timestamp),
                        canonical_type=ctype,
                        source="LINEAGE_COPY",
                        document_id=cp.document_id,
                        copy_id=cp.copy_id,
                        principal_id=cp.recipient_principal_id,
                        trust_level=TelemetryTrustLevel.CRYPTOGRAPHICALLY_VERIFIED,
                        description=f"Copy issued (depth={cp.lineage_depth}) to {cp.recipient_principal_id or 'ANONYMOUS'}",
                        raw_metadata={"depth": cp.lineage_depth, "parent_copy_id": cp.parent_copy_id},
                    )
                )

        # 3. Ingest Access Sessions
        if sessions:
            for s in sessions:
                dev_state = DeviceAttestationState.DEVICE_UNKNOWN
                if s.device_key_id and s.device_key_id in enrolled_devices:
                    b = enrolled_devices[s.device_key_id]
                    dev_state = (
                        DeviceAttestationState.DEVICE_ATTESTED
                        if b.attestation_status.value == "DEVICE_ATTESTED"
                        else DeviceAttestationState.DEVICE_UNATTESTED
                    )

                raw_items.append(
                    CustodyTimelineItem(
                        item_id=f"sess-{s.session_id}",
                        timestamp=self._normalize_ts(s.issued_at),
                        canonical_type=CanonicalEventType.RENDERED,
                        source="CONTROLLED_VIEWER",
                        session_id=s.session_id,
                        copy_id=s.copy_id,
                        account_id=s.identity_id,
                        device_id=s.device_key_id,
                        device_attestation=dev_state,
                        trust_level=TelemetryTrustLevel.HARDWARE_SEALED if dev_state == DeviceAttestationState.DEVICE_ATTESTED else TelemetryTrustLevel.AUTHENTICATED,
                        description=f"Active viewer session started on device {s.device_key_id or 'UNBOUND'}",
                        raw_metadata={"fingerprint": s.session_fingerprint_key},
                    )
                )

        # 4. Ingest Forwarding Events
        if forwarding_events:
            for fe in forwarding_events:
                raw_items.append(
                    CustodyTimelineItem(
                        item_id=f"fwd-{fe.forwarding_event_id}",
                        timestamp=self._normalize_ts(fe.timestamp),
                        canonical_type=CanonicalEventType.FORWARDED,
                        source="LINEAGE_FORWARDING",
                        copy_id=fe.child_copy_id,
                        principal_id=fe.recipient_principal_id or fe.actor_principal_id,
                        account_id=fe.actor_identity_id,
                        device_id=fe.sender_device_id,
                        trust_level=TelemetryTrustLevel.SIGNED if fe.signature_b64 else TelemetryTrustLevel.OBSERVED,
                        description=f"Controlled document forward: {fe.parent_copy_id} -> {fe.child_copy_id} by {fe.actor_principal_id}",
                        raw_metadata={"actor": fe.actor_principal_id, "recipient": fe.recipient_principal_id},
                    )
                )

        # 5. Ingest Export Events
        if export_events:
            for ee in export_events:
                ctype = CanonicalEventType.PRINTED if ee.export_format.value == "PRINT" else CanonicalEventType.EXPORTED
                raw_items.append(
                    CustodyTimelineItem(
                        item_id=f"exp-{ee.export_id}",
                        timestamp=self._normalize_ts(ee.timestamp),
                        canonical_type=ctype,
                        source="CONTROLLED_EXPORT",
                        session_id=ee.source_session_id,
                        copy_id=ee.child_copy_id,
                        principal_id=ee.actor_principal_id,
                        account_id=ee.actor_identity_id,
                        device_id=ee.device_identity_id,
                        trust_level=TelemetryTrustLevel.SIGNED if ee.signature_b64 else TelemetryTrustLevel.OBSERVED,
                        description=f"Controlled document export ({ee.export_format.value}): child {ee.child_copy_id}",
                        raw_metadata={"format": ee.export_format.value, "parent_copy": ee.parent_copy_id},
                    )
                )

        # 6. Ingest External Telemetry Events
        if telemetry_events:
            for te in telemetry_events:
                raw_items.append(
                    CustodyTimelineItem(
                        item_id=f"tele-{te.event_id}",
                        timestamp=self._normalize_ts(te.timestamp),
                        canonical_type=te.canonical_type,
                        source=te.source_system.value,
                        principal_id=te.recipient_principal_id,
                        account_id=te.subject_id if te.subject_type == "ACCOUNT" else None,
                        device_id=te.device_id,
                        device_attestation=te.device_attestation_state,
                        trust_level=te.trust_level,
                        session_id=te.session_id,
                        copy_id=te.copy_id,
                        document_id=te.resource_id,
                        network_id=te.network_id,
                        resource_id=te.resource_id,
                        artifact_hash=te.artifact_hash,
                        description=f"External telemetry {te.source_system.value}:{te.event_type} on {te.device_id or te.subject_id or 'UNKNOWN'}",
                        raw_metadata=te.raw_payload,
                    )
                )

        # 7. Sort items chronologically
        raw_items.sort(key=lambda x: x.timestamp)

        # 8. Multi-Sensor Deduplication & Clustering
        deduped_timeline, compound_actions = self._cluster_multi_sensor_events(raw_items)

        # 9. Temporal Ordering & Causality Validation
        causality_violations, custody_gaps = self._validate_causality_and_gaps(deduped_timeline)

        # 10. Impossible Travel & Concurrent Session Detection
        is_compromised, indicators = self._check_account_compromise(deduped_timeline)

        # 11. Exact-Copy Downstream Boundary & Attribution Decision
        report = self._evaluate_attribution_boundary(
            report_id=report_id,
            timeline=deduped_timeline,
            compound_actions=compound_actions,
            causality_violations=causality_violations,
            custody_gaps=custody_gaps,
            is_compromised=is_compromised,
            compromise_indicators=indicators,
            enrolled_recipient_id=enrolled_recipient_id,
            document_root=document_root,
        )

        return report

    def _cluster_multi_sensor_events(
        self, items: List[CustodyTimelineItem]
    ) -> Tuple[List[CustodyTimelineItem], List[CompoundCustodyAction]]:
        """
        Deduplicates concurrent sensor logs of the same physical action (e.g. EDR file write + DLP transfer).
        """
        if not items:
            return [], []

        external_sources = {it.source for it in items if it.source not in ("LINEAGE_ROOT", "LINEAGE_COPY")}
        if len(external_sources) <= 1:
            return list(items), []

        deduped: List[CustodyTimelineItem] = []
        compounds: List[CompoundCustodyAction] = []
        skip_indices: Set[int] = set()

        for i in range(len(items)):
            if i in skip_indices:
                continue

            current = items[i]
            # Look ahead for concurrent sensor events within window
            cluster = [current]
            cluster_indices = [i]
            cluster_sources = {current.source}

            for j in range(i + 1, len(items)):
                candidate = items[j]
                delta = candidate.timestamp - current.timestamp
                if delta > self.sensor_cluster_window:
                    break

                if candidate.source in cluster_sources:
                    continue

                # Same device or resource or account performing egress / copy / export
                matches_actor = (
                    (current.device_id and candidate.device_id and current.device_id == candidate.device_id)
                    or (current.account_id and candidate.account_id and current.account_id == candidate.account_id)
                    or (current.copy_id and candidate.copy_id and current.copy_id == candidate.copy_id)
                )

                # Both are external sensor events
                is_external_pair = current.source not in ("LINEAGE_ROOT", "LINEAGE_COPY") and candidate.source not in ("LINEAGE_ROOT", "LINEAGE_COPY")

                if matches_actor and is_external_pair:
                    cluster.append(candidate)
                    cluster_indices.append(j)
                    cluster_sources.add(candidate.source)

            if len(cluster) > 1 and len(cluster_sources) > 1:
                # Create CompoundCustodyAction
                cid = f"compound-{hashlib.sha256(f'{current.item_id}:{len(cluster)}'.encode()).hexdigest()[:12]}"
                sources = list({c.source for c in cluster})
                event_ids = [c.item_id for c in cluster]

                # Select most specific canonical type
                type_priority = [
                    CanonicalEventType.PUBLICATION_OBSERVED,
                    CanonicalEventType.WRITTEN_TO_USB,
                    CanonicalEventType.PRINTED,
                    CanonicalEventType.EMAILED,
                    CanonicalEventType.UPLOADED,
                    CanonicalEventType.NETWORK_TRANSMITTED,
                    CanonicalEventType.EXPORTED,
                    CanonicalEventType.COPIED,
                    CanonicalEventType.RENDERED,
                ]
                chosen_type = current.canonical_type
                for tp in type_priority:
                    if any(c.canonical_type == tp for c in cluster):
                        chosen_type = tp
                        break

                comp = CompoundCustodyAction(
                    compound_id=cid,
                    primary_canonical_type=chosen_type,
                    timestamp=current.timestamp,
                    device_id=current.device_id,
                    account_id=current.account_id,
                    resource_id=current.resource_id,
                    sensor_sources=sources,
                    underlying_event_ids=event_ids,
                    combined_confidence=min(0.98, max(c.trust_level != TelemetryTrustLevel.UNVERIFIED for c in cluster) * 0.9 + 0.05),
                )
                compounds.append(comp)

                # Replace in timeline with single compound item
                compound_item = CustodyTimelineItem(
                    item_id=cid,
                    timestamp=current.timestamp,
                    canonical_type=chosen_type,
                    source=f"MULTI_SENSOR({'+'.join(sources)})",
                    principal_id=current.principal_id,
                    account_id=current.account_id,
                    device_id=current.device_id,
                    device_attestation=current.device_attestation,
                    trust_level=TelemetryTrustLevel.AUTHENTICATED,
                    session_id=current.session_id,
                    copy_id=current.copy_id,
                    document_id=current.document_id,
                    network_id=current.network_id,
                    resource_id=current.resource_id,
                    artifact_hash=current.artifact_hash,
                    is_compound=True,
                    compound_event_id=cid,
                    contributing_sensor_event_ids=event_ids,
                    description=f"Deduplicated compound event across sensors: {sources}",
                )
                deduped.append(compound_item)
                skip_indices.update(cluster_indices)
            else:
                deduped.append(current)

        return deduped, compounds

    def _validate_causality_and_gaps(
        self, timeline: List[CustodyTimelineItem]
    ) -> Tuple[List[str], List[str]]:
        """
        Validates causal ordering:
        DOCUMENT_CREATED -> RELEASED_TO_RECIPIENT -> RENDERED/DECRYPTED -> EXPORTED/FORWARDED -> EGRESS/PUBLISHED
        Tolerates up to max_clock_skew (120s). Flags custody gaps.
        """
        causality_violations: List[str] = []
        custody_gaps: List[str] = []

        # Track seen states
        created_seen = False
        release_seen = False
        decrypt_or_render_seen = False
        export_seen = False

        # Check root creation time
        root_time: Optional[datetime] = None
        for it in timeline:
            if it.canonical_type == CanonicalEventType.DOCUMENT_CREATED:
                root_time = it.timestamp
                break

        # Track copy issuance times and session decrypt times along causal edges
        copy_issuance_time: Dict[str, datetime] = {}
        session_decrypt_time: Dict[str, datetime] = {}

        for item in timeline:
            if item.canonical_type == CanonicalEventType.DOCUMENT_CREATED:
                created_seen = True
            elif item.canonical_type == CanonicalEventType.RELEASED_TO_RECIPIENT:
                release_seen = True
                if item.copy_id:
                    copy_issuance_time[item.copy_id] = item.timestamp
            elif item.canonical_type == CanonicalEventType.DECRYPTED:
                decrypt_or_render_seen = True
                if item.session_id:
                    session_decrypt_time[item.session_id] = item.timestamp
            elif item.canonical_type == CanonicalEventType.RENDERED:
                decrypt_or_render_seen = True
                if item.session_id and item.session_id in session_decrypt_time:
                    dec_t = session_decrypt_time[item.session_id]
                    if item.timestamp < (dec_t - self.max_clock_skew):
                        diff = (dec_t - item.timestamp).total_seconds()
                        causality_violations.append(
                            f"Causality Violation: RENDERED for session {item.session_id} timestamped at "
                            f"{item.timestamp.isoformat()} occurred {diff:.1f}s BEFORE DECRYPTED at {dec_t.isoformat()}."
                        )
                        item.causal_status = CustodyCausalStatus.CAUSALITY_VIOLATION
            elif item.canonical_type in (CanonicalEventType.EXPORTED, CanonicalEventType.FORWARDED):
                export_seen = True

            # Causality check: cannot access/export before root document creation beyond allowable clock skew
            if root_time and item.canonical_type != CanonicalEventType.DOCUMENT_CREATED:
                if item.timestamp < (root_time - self.max_clock_skew):
                    diff = (root_time - item.timestamp).total_seconds()
                    causality_violations.append(
                        f"Causality Violation: {item.canonical_type.value} ({item.item_id}) timestamped at "
                        f"{item.timestamp.isoformat()} occurred {diff:.1f}s BEFORE document creation at {root_time.isoformat()}."
                    )
                    item.causal_status = CustodyCausalStatus.CAUSALITY_VIOLATION

            # Causality check: cannot observe actions on copy before copy issuance beyond allowable clock skew
            if item.copy_id and item.copy_id in copy_issuance_time and item.canonical_type != CanonicalEventType.RELEASED_TO_RECIPIENT:
                cp_t = copy_issuance_time[item.copy_id]
                if item.timestamp < (cp_t - self.max_clock_skew):
                    diff = (cp_t - item.timestamp).total_seconds()
                    causality_violations.append(
                        f"Causality Violation: {item.canonical_type.value} ({item.item_id}) timestamped at "
                        f"{item.timestamp.isoformat()} occurred {diff:.1f}s BEFORE copy issuance at {cp_t.isoformat()}."
                    )
                    item.causal_status = CustodyCausalStatus.CAUSALITY_VIOLATION

        # Check custody gaps
        if export_seen and not release_seen:
            custody_gaps.append("Export/Forward observed without documented release to recipient.")
        if decrypt_or_render_seen and not release_seen:
            custody_gaps.append("Decryption/Rendering observed without documented release to recipient.")

        return causality_violations, custody_gaps

    def _check_account_compromise(
        self, timeline: List[CustodyTimelineItem]
    ) -> Tuple[bool, List[str]]:
        """
        Detects impossible travel velocity (> 900 km/h) or concurrent sessions.
        """
        indicators: List[str] = []
        is_compromised = False

        # Group items by account_id
        by_account: Dict[str, List[CustodyTimelineItem]] = {}
        for item in timeline:
            if item.account_id:
                by_account.setdefault(item.account_id, []).append(item)

        for acct, events in by_account.items():
            if len(events) < 2:
                continue

            for i in range(len(events) - 1):
                e1 = events[i]
                e2 = events[i + 1]

                loc1 = e1.raw_metadata.get("city") or e1.raw_metadata.get("country")
                loc2 = e2.raw_metadata.get("city") or e2.raw_metadata.get("country")

                delta_hours = (e2.timestamp - e1.timestamp).total_seconds() / 3600.0

                # 1. Impossible travel
                if loc1 and loc2 and loc1 != loc2:
                    dist_km = float(e2.raw_metadata.get("distance_km", 1500.0))
                    velocity = dist_km / max(delta_hours, 0.001)
                    if velocity > 900.0:
                        is_compromised = True
                        indicators.append(
                            f"Impossible Travel: Account '{acct}' observed in '{loc1}' and '{loc2}' "
                            f"within {delta_hours:.2f}h (implied speed {velocity:.0f} km/h > 900 km/h threshold)."
                        )

                # 2. Concurrent sessions on distinct devices within 60s
                if e1.device_id and e2.device_id and e1.device_id != e2.device_id:
                    delta_sec = (e2.timestamp - e1.timestamp).total_seconds()
                    if 0.0 <= delta_sec < 60.0:
                        is_compromised = True
                        indicators.append(
                            f"Concurrent Session / Shared Device: Account '{acct}' active on distinct devices "
                            f"'{e1.device_id}' and '{e2.device_id}' within {delta_sec:.1f}s."
                        )

        return is_compromised, indicators

    def _evaluate_attribution_boundary(
        self,
        report_id: str,
        timeline: List[CustodyTimelineItem],
        compound_actions: List[CompoundCustodyAction],
        causality_violations: List[str],
        custody_gaps: List[str],
        is_compromised: bool,
        compromise_indicators: List[str],
        enrolled_recipient_id: Optional[str],
        document_root: Optional[DocumentRoot],
    ) -> CustodyTimelineReport:
        """
        Enforces exact-copy downstream boundary theorems.
        """
        # A. Fail-closed on severe causality violations
        if causality_violations:
            return CustodyTimelineReport(
                report_id=report_id,
                document_id=document_root.document_id if document_root else None,
                root_document_hash=document_root.canonical_hash if document_root else None,
                original_recipient_id=enrolled_recipient_id,
                forensic_boundary_state=ForensicBoundaryState.CONFLICT,
                highest_attribution_level=ForensicAttributionLevel.LEVEL_1_DOCUMENT_DETECTED,
                timeline=timeline,
                compound_actions=compound_actions,
                custody_gaps=custody_gaps,
                causality_violations=causality_violations,
                should_abstain=True,
                abstention_reason=f"Temporal causality violations detected: {causality_violations[0]}",
                boundary_statement="Attribution aborted: chronological sequence is physically or causally contradictory.",
                confidence_score=0.0,
            )

        # B. Fail-closed on account compromise / shared workstation
        if is_compromised:
            return CustodyTimelineReport(
                report_id=report_id,
                document_id=document_root.document_id if document_root else None,
                root_document_hash=document_root.canonical_hash if document_root else None,
                original_recipient_id=enrolled_recipient_id,
                forensic_boundary_state=ForensicBoundaryState.ABSTAINED,
                highest_attribution_level=ForensicAttributionLevel.LEVEL_3_COPY_INSTANCE_IDENTIFIED,
                timeline=timeline,
                compound_actions=compound_actions,
                custody_gaps=custody_gaps,
                account_compromised_or_shared=True,
                compromise_indicators=compromise_indicators,
                should_abstain=True,
                abstention_reason="Account compromise or shared workstation concurrency detected.",
                boundary_statement="Abstained from human attribution: telemetry indicates compromised account or shared multi-user terminal.",
                confidence_score=0.0,
            )

        # C. Track custody chain
        original_recipient = enrolled_recipient_id
        last_controlled_holder = enrolled_recipient_id
        downstream_account = None
        downstream_device = None
        confirmed_publisher = None
        pub_platform = None

        has_forwarding = False
        has_publication = False
        publication_event: Optional[CustodyTimelineItem] = None

        for item in timeline:
            if item.canonical_type == CanonicalEventType.RELEASED_TO_RECIPIENT:
                if not original_recipient and item.principal_id:
                    original_recipient = item.principal_id
                if not last_controlled_holder and item.principal_id:
                    last_controlled_holder = item.principal_id

            elif item.canonical_type == CanonicalEventType.FORWARDED:
                has_forwarding = True
                # Recipient of forwarding becomes new last known controlled holder
                forward_rec = item.raw_metadata.get("recipient") or item.principal_id or item.account_id
                if forward_rec:
                    last_controlled_holder = forward_rec
                    downstream_account = forward_rec

            elif item.canonical_type == CanonicalEventType.PUBLICATION_OBSERVED:
                has_publication = True
                publication_event = item
                pub_platform = item.source

        # Exact-Copy Downstream Boundary Logic:
        # If Bob is last controlled holder and file leaks to public drop,
        # but NO upload event from Bob was observed:
        # Bob is LAST_KNOWN_HOLDER, NOT confirmed publisher!
        if has_publication and publication_event:
            # Check if publication event is linked to Bob's device or account
            pub_account = publication_event.account_id
            pub_device = publication_event.device_id

            if last_controlled_holder and (
                (pub_account and pub_account == last_controlled_holder)
                or (pub_device and downstream_device and pub_device == downstream_device)
            ):
                # Confirmed publication by Bob
                confirmed_publisher = last_controlled_holder
                boundary_state = ForensicBoundaryState.ATTRIBUTED_TO_CONTROLLED_ACTOR
                level = ForensicAttributionLevel.LEVEL_5_HUMAN_IDENTITY_RESOLVED if publication_event.trust_level == TelemetryTrustLevel.CRYPTOGRAPHICALLY_VERIFIED else ForensicAttributionLevel.LEVEL_4_LINEAGE_IDENTIFIED
                statement = f"Confirmed publication: last controlled holder '{last_controlled_holder}' executed observed publication to '{pub_platform}'."
                should_abstain = False
                conf = 0.95
            else:
                # Downstream leak barrier: Bob was custody holder, but leak was by unknown actor
                boundary_state = ForensicBoundaryState.UNKNOWN_DOWNSTREAM_ACTOR
                level = ForensicAttributionLevel.LEVEL_4_LINEAGE_IDENTIFIED
                statement = (
                    f"Exact-Copy Downstream Boundary: Original recipient was '{original_recipient}'. "
                    f"Last known controlled holder was '{last_controlled_holder}'. "
                    f"Publication occurred via '{pub_platform}' by unknown downstream entity. "
                    f"DO NOT accuse '{last_controlled_holder}' of publishing: custody does not prove publication."
                )
                should_abstain = True
                abstention_reason = f"Last controlled holder '{last_controlled_holder}' has no observed publication telemetry; leak occurred downstream."
                conf = 0.65

        elif has_forwarding:
            boundary_state = ForensicBoundaryState.LAST_KNOWN_HOLDER
            level = ForensicAttributionLevel.LEVEL_4_LINEAGE_IDENTIFIED
            statement = f"Controlled forwarding observed: last known controlled holder is '{last_controlled_holder}'."
            should_abstain = False
            conf = 0.85

        elif original_recipient:
            boundary_state = ForensicBoundaryState.ATTRIBUTED_TO_CONTROLLED_ACTOR
            level = ForensicAttributionLevel.LEVEL_2_ORIGINAL_RECIPIENT_IDENTIFIED
            statement = f"Original release recipient '{original_recipient}' identified with no recorded downstream transfers."
            should_abstain = False
            conf = 0.90

        else:
            boundary_state = ForensicBoundaryState.INSUFFICIENT_EVIDENCE
            level = ForensicAttributionLevel.LEVEL_1_DOCUMENT_DETECTED
            statement = "Insufficient telemetry or cryptographic evidence to establish document custody."
            should_abstain = True
            abstention_reason = "No recipient or custody events recorded."
            conf = 0.20

        return CustodyTimelineReport(
            report_id=report_id,
            document_id=document_root.document_id if document_root else None,
            root_document_hash=document_root.canonical_hash if document_root else None,
            original_recipient_id=original_recipient,
            last_known_controlled_holder=last_controlled_holder,
            downstream_holder_account=downstream_account,
            downstream_device_id=downstream_device,
            confirmed_publisher_id=confirmed_publisher,
            publication_platform=pub_platform,
            forensic_boundary_state=boundary_state,
            highest_attribution_level=level,
            timeline=timeline,
            compound_actions=compound_actions,
            custody_gaps=custody_gaps,
            causality_violations=causality_violations,
            account_compromised_or_shared=is_compromised,
            compromise_indicators=compromise_indicators,
            should_abstain=should_abstain,
            abstention_reason=abstention_reason if should_abstain else None,
            boundary_statement=statement,
            confidence_score=conf,
        )
