"""
tests/properties/test_telemetry_custody_properties.py

Property-based testing and causal fuzzing for Unified Custody Timeline:
- Exact-Copy Downstream Boundary Invariant (Custody != Publication)
- Temporal causality and clock-skew tolerance (120s limit)
- Multi-sensor egress deduplication (anti-double-counting)
- Account compromise & shared workstation mandatory abstention
"""

import copy
from datetime import datetime, timezone, timedelta
import pytest
from core.telemetry.models import (
    TelemetrySource,
    IntegrityLevel,
    TelemetryTrustLevel,
    DeviceAttestationState,
    CanonicalEventType,
)
from core.telemetry.event import ForensicEvent
from core.telemetry.custody import (
    UnifiedCustodyTimelineBuilder,
    CustodyTimelineReport,
    CustodyCausalStatus,
)
from core.lineage.models import (
    DocumentRoot,
    CopyInstance,
    AccessSession,
    ForwardingEvent,
    ExportEvent,
    ExportFormat,
    ForensicAttributionLevel,
    ForensicBoundaryState,
)
from core.testing.property_engine import PropertyRunner, DeterministicGenerator
from core.security.invariants import assert_invariant


def test_property_exact_copy_downstream_boundary_invariant(runner: PropertyRunner):
    """
    Property: When an exact copy moves Alice -> Bob -> public drop:
    - If NO upload event from Bob is observed, Bob is LAST_KNOWN_HOLDER,
      confirmed_publisher is UNKNOWN, and engine abstains.
    - If an authentic upload event from Bob IS observed, Bob is confirmed publisher.
    """
    builder = UnifiedCustodyTimelineBuilder()

    def prop(g: DeterministicGenerator):
        t0 = datetime(2026, 9, 27, 10, 0, 0, tzinfo=timezone.utc)
        doc_id = g.generate_document_id()
        root_hash = "aa" * 32

        # 1. Root Creation
        doc_root = DocumentRoot(
            document_id=doc_id,
            canonical_hash=root_hash,
            mime_type="application/pdf",
            byte_size=1024,
            created_at=t0.isoformat(),
            status="ACTIVE",
        )

        # 2. Copy 0 issued to Alice
        alice_copy_id = f"cpy-alice-{g.alphanumeric(4, 6)}"
        copy_alice = CopyInstance(
            copy_id=alice_copy_id,
            parent_copy_id=None,
            document_id=doc_id,
            recipient_principal_id="rec-alice",
            issuance_timestamp=(t0 + timedelta(minutes=5)).isoformat(),
            lineage_depth=0,
            status="ACTIVE",
        )

        # 3. Controlled Forwarding to Bob (Copy 1)
        bob_copy_id = f"cpy-bob-{g.alphanumeric(4, 6)}"
        copy_bob = CopyInstance(
            copy_id=bob_copy_id,
            parent_copy_id=alice_copy_id,
            document_id=doc_id,
            recipient_principal_id="rec-bob",
            issuance_timestamp=(t0 + timedelta(minutes=10)).isoformat(),
            lineage_depth=1,
            status="ACTIVE",
        )
        fwd_event = ForwardingEvent(
            forwarding_event_id=f"fwd-{g.alphanumeric(6, 8)}",
            parent_copy_id=alice_copy_id,
            child_copy_id=bob_copy_id,
            actor_principal_id="rec-alice",
            recipient_principal_id="rec-bob",
            timestamp=(t0 + timedelta(minutes=10)).isoformat(),
        )

        # 4. Public drop event
        is_bob_uploader = g.boolean(0.5)
        uploader_account = "rec-bob" if is_bob_uploader else f"anon_drop_{g.alphanumeric(4, 6)}"

        pub_event = ForensicEvent(
            event_id=f"pub-{g.alphanumeric(6, 8)}",
            timestamp=t0 + timedelta(hours=2),
            event_type="PUBLIC_FILE_UPLOAD",
            source_system=TelemetrySource.PUBLIC_UPLOAD,
            canonical_type=CanonicalEventType.PUBLICATION_OBSERVED,
            subject_type="ACCOUNT",
            subject_id=uploader_account,
            resource_id=doc_id,
            artifact_hash=root_hash,
            trust_level=TelemetryTrustLevel.OBSERVED,
            raw_payload={"platform_name": "Pastebin", "url": "https://pastebin.com/leak"},
        )

        report = builder.build_timeline(
            document_root=doc_root,
            copies=[copy_alice, copy_bob],
            forwarding_events=[fwd_event],
            telemetry_events=[pub_event],
            enrolled_recipient_id="rec-alice",
        )

        # Verify exact copy downstream boundary
        assert report.original_recipient_id == "rec-alice"
        assert report.last_known_controlled_holder == "rec-bob"

        if is_bob_uploader:
            assert report.confirmed_publisher_id == "rec-bob"
            assert report.forensic_boundary_state == ForensicBoundaryState.ATTRIBUTED_TO_CONTROLLED_ACTOR
            assert report.should_abstain is False
        else:
            # Downstream leak barrier: Bob was custody holder, but leak was by unknown actor
            assert report.confirmed_publisher_id is None
            assert report.forensic_boundary_state == ForensicBoundaryState.UNKNOWN_DOWNSTREAM_ACTOR
            assert report.should_abstain is True
            assert "custody does not prove publication" in report.boundary_statement.lower()

    res = runner.run_property("exact_copy_downstream_boundary", prop, iterations=100)
    assert res.passed, res.error_message


def test_property_temporal_causality_and_skew_invariant(runner: PropertyRunner):
    """
    Property: Actions occurring chronologically prior to master document creation
    or copy issuance beyond allowed clock skew (120s) strictly trigger CAUSALITY_VIOLATION
    and cause the timeline report to enter CONFLICT state and abstain.
    """
    builder = UnifiedCustodyTimelineBuilder(max_clock_skew_seconds=120.0)

    def prop(g: DeterministicGenerator):
        t_root = datetime(2026, 9, 27, 12, 0, 0, tzinfo=timezone.utc)
        doc_id = g.generate_document_id()

        doc_root = DocumentRoot(
            document_id=doc_id,
            canonical_hash="bb" * 32,
            mime_type="application/pdf",
            byte_size=2048,
            created_at=t_root.isoformat(),
            status="ACTIVE",
        )

        # Pre-seed copy 0 for recipient
        copy_alice = CopyInstance(
            copy_id="cpy-001",
            parent_copy_id=None,
            document_id=doc_id,
            recipient_principal_id="rec-alice",
            issuance_timestamp=(t_root + timedelta(minutes=1)).isoformat(),
            lineage_depth=0,
            status="ACTIVE",
        )

        is_causality_violation = g.boolean(0.5)

        if is_causality_violation:
            # Action happened 300s to 3600s BEFORE root creation
            offset_seconds = g.integer(300, 3600)
            t_action = t_root - timedelta(seconds=offset_seconds)
        else:
            # Action happened in the future or within allowable skew (-30s)
            offset_seconds = g.integer(-30, 3600)
            t_action = t_root + timedelta(seconds=offset_seconds)

        export_ev = ExportEvent(
            export_id=f"exp-{g.alphanumeric(6, 8)}",
            source_session_id="sess-001",
            parent_copy_id="cpy-001",
            child_copy_id="cpy-child-002",
            export_format=ExportFormat.PDF,
            export_fingerprint=f"fp_{g.alphanumeric(8, 12)}",
            actor_principal_id="rec-alice",
            timestamp=t_action.isoformat(),
        )

        report = builder.build_timeline(
            document_root=doc_root,
            copies=[copy_alice],
            export_events=[export_ev],
            enrolled_recipient_id="rec-alice",
        )

        if is_causality_violation:
            assert len(report.causality_violations) > 0
            assert report.forensic_boundary_state == ForensicBoundaryState.CONFLICT
            assert report.should_abstain is True
            assert report.confidence_score == 0.0
        else:
            assert len(report.causality_violations) == 0

    res = runner.run_property("temporal_causality_and_skew", prop, iterations=150)
    assert res.passed, res.error_message


def test_property_multi_sensor_deduplication_invariant(runner: PropertyRunner):
    """
    Property: Multiple external sensor observations of the same egress action
    within the 5-second clustering window are deduplicated into a single CompoundCustodyAction.
    """
    builder = UnifiedCustodyTimelineBuilder(sensor_cluster_window_seconds=5.0)

    def prop(g: DeterministicGenerator):
        t_base = datetime(2026, 9, 27, 14, 0, 0, tzinfo=timezone.utc)
        doc_id = g.generate_document_id()
        device_id = g.generate_device_id()
        account_id = "rec-alice"

        doc_root = DocumentRoot(
            document_id=doc_id,
            canonical_hash="cc" * 32,
            mime_type="application/pdf",
            byte_size=1024,
            created_at=(t_base - timedelta(minutes=10)).isoformat(),
            status="ACTIVE",
        )

        num_sensors = g.integer(2, 4)
        sensors = g.sample([TelemetrySource.EDR, TelemetrySource.DLP, TelemetrySource.USB, TelemetrySource.NETWORK], num_sensors)

        events = []
        for i, s in enumerate(sensors):
            # Stagger timestamps within 0 to 3 seconds
            delta_s = g.float_val(0.0, 3.0)
            ev = ForensicEvent(
                event_id=f"ev-{s.value}-{g.alphanumeric(4, 6)}",
                timestamp=t_base + timedelta(seconds=delta_s),
                event_type="FILE_TRANSFER_OBSERVED",
                source_system=s,
                canonical_type=CanonicalEventType.WRITTEN_TO_USB if s == TelemetrySource.USB else CanonicalEventType.EXPORTED,
                subject_type="ACCOUNT",
                subject_id=account_id,
                device_id=device_id,
                resource_id=doc_id,
                artifact_hash="cc" * 32,
                trust_level=TelemetryTrustLevel.AUTHENTICATED,
            )
            events.append(ev)

        report = builder.build_timeline(
            document_root=doc_root,
            telemetry_events=events,
            enrolled_recipient_id=account_id,
        )

        # Invariant: Must cluster into exactly 1 CompoundCustodyAction
        assert len(report.compound_actions) == 1
        compound = report.compound_actions[0]
        assert compound.is_deduplicated is True
        assert len(compound.sensor_sources) == num_sensors
        assert len(compound.underlying_event_ids) == num_sensors

    res = runner.run_property("multi_sensor_deduplication", prop, iterations=100)
    assert res.passed, res.error_message


def test_property_account_compromise_and_shared_workstation_abstention(runner: PropertyRunner):
    """
    Property: Impossible travel (> 900 km/h) or concurrent sessions on distinct
    devices strictly triggers account_compromised_or_shared = True and forces ABSTAINED.
    """
    builder = UnifiedCustodyTimelineBuilder()

    def prop(g: DeterministicGenerator):
        t_base = datetime(2026, 9, 27, 16, 0, 0, tzinfo=timezone.utc)
        doc_id = g.generate_document_id()
        acct_id = "rec-compromised-user"

        doc_root = DocumentRoot(
            document_id=doc_id,
            canonical_hash="dd" * 32,
            mime_type="application/pdf",
            byte_size=1024,
            created_at=(t_base - timedelta(hours=1)).isoformat(),
            status="ACTIVE",
        )

        compromise_type = g.choice(["impossible_travel", "concurrent_devices"])

        if compromise_type == "impossible_travel":
            # Event 1: London at t_base
            ev1 = ForensicEvent(
                event_id=f"ev1-{g.alphanumeric(4, 6)}",
                timestamp=t_base,
                event_type="AUTH_LOGIN",
                source_system=TelemetrySource.IDP,
                canonical_type=CanonicalEventType.RENDERED,
                subject_type="ACCOUNT",
                subject_id=acct_id,
                raw_payload={"city": "London", "country": "UK"},
            )
            # Event 2: Tokyo (9500 km away) 30 minutes later (implied speed 19,000 km/h)
            ev2 = ForensicEvent(
                event_id=f"ev2-{g.alphanumeric(4, 6)}",
                timestamp=t_base + timedelta(minutes=30),
                event_type="AUTH_LOGIN",
                source_system=TelemetrySource.IDP,
                canonical_type=CanonicalEventType.RENDERED,
                subject_type="ACCOUNT",
                subject_id=acct_id,
                raw_payload={"city": "Tokyo", "country": "JP", "distance_km": 9500.0},
            )
            events = [ev1, ev2]

        elif compromise_type == "concurrent_devices":
            # Event 1 on Device A
            ev1 = ForensicEvent(
                event_id=f"ev1-{g.alphanumeric(4, 6)}",
                timestamp=t_base,
                event_type="DOCUMENT_VIEW",
                source_system=TelemetrySource.EDR,
                canonical_type=CanonicalEventType.RENDERED,
                subject_type="ACCOUNT",
                subject_id=acct_id,
                device_id="dev-workstation-alpha",
            )
            # Event 2 on Device B 10 seconds later
            ev2 = ForensicEvent(
                event_id=f"ev2-{g.alphanumeric(4, 6)}",
                timestamp=t_base + timedelta(seconds=10),
                event_type="DOCUMENT_VIEW",
                source_system=TelemetrySource.EDR,
                canonical_type=CanonicalEventType.RENDERED,
                subject_type="ACCOUNT",
                subject_id=acct_id,
                device_id="dev-workstation-beta",
            )
            events = [ev1, ev2]

        report = builder.build_timeline(
            document_root=doc_root,
            telemetry_events=events,
            enrolled_recipient_id=acct_id,
        )

        assert report.account_compromised_or_shared is True
        assert len(report.compromise_indicators) > 0
        assert report.forensic_boundary_state == ForensicBoundaryState.ABSTAINED
        assert report.should_abstain is True
        assert report.confidence_score == 0.0

    res = runner.run_property("account_compromise_abstention", prop, iterations=100)
    assert res.passed, res.error_message
