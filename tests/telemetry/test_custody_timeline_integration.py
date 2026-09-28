"""
AegisTrace Custody Timeline & Lineage Integration Tests.

Validates the full end-to-end integration:
Identity -> Recipient Principal -> Device -> Viewer Session -> Decryption Event
-> Watermarked Copy -> Observed Access -> Export/Forward -> External Telemetry
-> Lineage Correlation -> Evidence Dependency Graph -> Forensic Attribution/Abstention.
"""

import pytest
from datetime import datetime, timezone, timedelta
import hashlib
import os

from core.telemetry.models import (
    TelemetrySource,
    IntegrityLevel,
    TelemetryTrustLevel,
    DeviceAttestationState,
    CanonicalEventType,
    EndpointEvidence,
    DLPEvent,
    NetworkEvidence,
    USBTransferEvent,
    PublicUploadEvent,
)
from core.telemetry.event import ForensicEvent
from core.telemetry.custody import (
    UnifiedCustodyTimelineBuilder,
    CustodyTimelineReport,
    CustodyTimelineItem,
    CompoundCustodyAction,
    CustodyCausalStatus,
)
from core.telemetry.bundle import TelemetryBundleManager
from core.telemetry.fusion_adapter import TelemetryFusionAdapter
from core.telemetry.adapters import TelemetryNormalizationLayer
from core.lineage.models import (
    DocumentRoot,
    CopyInstance,
    AccessSession,
    ForwardingEvent,
    ExportEvent,
    ExportFormat,
    TransitionActionType,
    DeviceBinding,
    DeviceAttestationStatus,
    PlatformType,
    ForensicAttributionLevel,
    ForensicBoundaryState,
)
from core.attribution.evidence import (
    EvidenceBundle,
    EvidenceFamily,
    DependencyType,
    TargetBinding,
)
from core.crypto.signatures import MLDSA65


def test_e2e_full_custody_chain_to_confirmed_publication():
    """
    Scenario 1: Complete legitimate custody chain leading to an observed leak by the holder.
    Alice receives document -> opens attested viewer session -> forwards to Bob ->
    Bob opens session -> exports file -> writes to USB -> uploads to Pastebin.
    Result: Confirmed publication by Bob.
    """
    builder = UnifiedCustodyTimelineBuilder(max_clock_skew_seconds=120.0)

    t0 = datetime(2026, 9, 27, 10, 0, 0, tzinfo=timezone.utc)
    doc_hash = hashlib.sha256(b"classified_spec").hexdigest()

    # 1. Document Root
    root = DocumentRoot(
        document_id="doc_defense_001",
        canonical_hash=doc_hash,
        byte_size=10240,
        created_at=t0.isoformat(),
    )

    # 2. Issuance to Alice
    t1 = t0 + timedelta(minutes=5)
    alice_copy = CopyInstance(
        copy_id="cpy_alice_root",
        document_id=root.document_id,
        recipient_principal_id="rec_alice",
        issuance_timestamp=t1.isoformat(),
        lineage_depth=0,
    )

    # 3. Alice Session on Attested Workstation
    t2 = t1 + timedelta(minutes=5)
    dev_alice = DeviceBinding(
        device_id="dev_ws_alice",
        device_key_id="dkey_alice_tpm",
        attestation_status=DeviceAttestationStatus.DEVICE_ATTESTED,
        platform_type=PlatformType.TPM,
    )
    alice_session = AccessSession(
        session_id="ses_alice_001",
        copy_id=alice_copy.copy_id,
        identity_id="alice@defense.gov",
        device_key_id=dev_alice.device_key_id,
        issued_at=t2.isoformat(),
    )

    # 4. Forwarding to Bob
    t3 = t2 + timedelta(minutes=10)
    bob_copy = CopyInstance(
        copy_id="cpy_bob_fwd",
        parent_copy_id=alice_copy.copy_id,
        document_id=root.document_id,
        recipient_principal_id="rec_bob",
        issuance_timestamp=t3.isoformat(),
        lineage_depth=1,
    )
    fwd_event = ForwardingEvent(
        forwarding_event_id="fwd_alice_to_bob",
        parent_copy_id=alice_copy.copy_id,
        child_copy_id=bob_copy.copy_id,
        actor_principal_id="rec_alice",
        recipient_principal_id="rec_bob",
        timestamp=t3.isoformat(),
        signature_b64="valid_mldsa_sig",
    )

    # 5. Bob Session on Laptop
    t4 = t3 + timedelta(minutes=15)
    dev_bob = DeviceBinding(
        device_id="dev_laptop_bob",
        device_key_id="dkey_bob_tpm",
        attestation_status=DeviceAttestationStatus.DEVICE_ATTESTED,
        platform_type=PlatformType.TPM,
    )
    bob_session = AccessSession(
        session_id="ses_bob_001",
        copy_id=bob_copy.copy_id,
        identity_id="bob@defense.gov",
        device_key_id=dev_bob.device_key_id,
        issued_at=t4.isoformat(),
    )

    # 6. Bob Export
    t5 = t4 + timedelta(minutes=5)
    bob_export_copy = CopyInstance(
        copy_id="cpy_bob_export",
        parent_copy_id=bob_copy.copy_id,
        document_id=root.document_id,
        recipient_principal_id="rec_bob",
        issuance_timestamp=t5.isoformat(),
        lineage_depth=2,
    )
    export_event = ExportEvent(
        export_id="exp_bob_001",
        source_session_id=bob_session.session_id,
        parent_copy_id=bob_copy.copy_id,
        child_copy_id=bob_export_copy.copy_id,
        export_format=ExportFormat.PDF,
        export_fingerprint="fp_bob_export",
        actor_principal_id="rec_bob",
        device_identity_id=dev_bob.device_id,
        timestamp=t5.isoformat(),
        signature_b64="valid_mldsa_sig",
    )

    # 7. Bob External Telemetry: USB Write + Public Upload
    t6 = t5 + timedelta(minutes=5)
    usb_ev = ForensicEvent(
        event_id="tele_usb_bob",
        timestamp=t6,
        event_type="USB_WRITE",
        canonical_type=CanonicalEventType.WRITTEN_TO_USB,
        source_system=TelemetrySource.USB,
        subject_type="ACCOUNT",
        subject_id="bob@defense.gov",
        recipient_principal_id="rec_bob",
        device_id=dev_bob.device_id,
        copy_id=bob_export_copy.copy_id,
        trust_level=TelemetryTrustLevel.AUTHENTICATED,
    )

    t7 = t6 + timedelta(minutes=5)
    pub_ev = ForensicEvent(
        event_id="tele_pastebin_bob",
        timestamp=t7,
        event_type="PASTEBIN_DROP",
        canonical_type=CanonicalEventType.PUBLICATION_OBSERVED,
        source_system=TelemetrySource.PUBLIC_UPLOAD,
        subject_type="ACCOUNT",
        subject_id="rec_bob",
        recipient_principal_id="rec_bob",
        device_id=dev_bob.device_id,
        copy_id=bob_export_copy.copy_id,
        trust_level=TelemetryTrustLevel.OBSERVED,
        raw_payload={"platform": "PASTEBIN", "uploader": "bob_leaker"},
    )

    enrolled = {
        dev_alice.device_key_id: dev_alice,
        dev_bob.device_key_id: dev_bob,
    }

    report = builder.build_timeline(
        document_root=root,
        copies=[alice_copy, bob_copy, bob_export_copy],
        sessions=[alice_session, bob_session],
        forwarding_events=[fwd_event],
        export_events=[export_event],
        telemetry_events=[usb_ev, pub_ev],
        enrolled_devices=enrolled,
        enrolled_recipient_id="rec_alice",
    )

    assert report.original_recipient_id == "rec_alice"
    assert report.last_known_controlled_holder == "rec_bob"
    assert report.confirmed_publisher_id == "rec_bob"
    assert report.forensic_boundary_state == ForensicBoundaryState.ATTRIBUTED_TO_CONTROLLED_ACTOR
    assert report.should_abstain is False
    assert len(report.timeline) >= 8


def test_exact_copy_downstream_boundary_abstains_from_accusing_bob():
    """
    CRITICAL FORENSIC THEOREM:
    Alice forwards to Bob. Bob is the last controlled holder.
    An exact bitwise copy is published to Pastebin by an anonymous or untracked actor.
    Bob has NO observed upload telemetry.
    INVARIANT:
    - Original Recipient = Alice
    - Last Known Controlled Holder = Bob
    - Confirmed Publisher = None
    - Boundary State = UNKNOWN_DOWNSTREAM_ACTOR
    - should_abstain = True
    - Bob MUST NOT be accused of publication based on custody alone!
    """
    builder = UnifiedCustodyTimelineBuilder()

    t0 = datetime(2026, 9, 27, 12, 0, 0, tzinfo=timezone.utc)
    root = DocumentRoot(
        document_id="doc_intel_002",
        canonical_hash=hashlib.sha256(b"intel_copy").hexdigest(),
        byte_size=5000,
        created_at=t0.isoformat(),
    )

    t1 = t0 + timedelta(minutes=5)
    alice_copy = CopyInstance(
        copy_id="cpy_alice_002",
        document_id=root.document_id,
        recipient_principal_id="rec_alice",
        issuance_timestamp=t1.isoformat(),
    )

    t2 = t1 + timedelta(minutes=10)
    bob_copy = CopyInstance(
        copy_id="cpy_bob_002",
        parent_copy_id=alice_copy.copy_id,
        document_id=root.document_id,
        recipient_principal_id="rec_bob",
        issuance_timestamp=t2.isoformat(),
        lineage_depth=1,
    )
    fwd = ForwardingEvent(
        forwarding_event_id="fwd_alice_bob",
        parent_copy_id=alice_copy.copy_id,
        child_copy_id=bob_copy.copy_id,
        actor_principal_id="rec_alice",
        recipient_principal_id="rec_bob",
        timestamp=t2.isoformat(),
    )

    # Leak appears on Pastebin from anonymous TOR exit node with NO connection to Bob
    t3 = t2 + timedelta(hours=2)
    pastebin_drop = ForensicEvent(
        event_id="tele_anon_drop",
        timestamp=t3,
        event_type="ANONYMOUS_DROP",
        canonical_type=CanonicalEventType.PUBLICATION_OBSERVED,
        source_system=TelemetrySource.PUBLIC_UPLOAD,
        subject_type="ANONYMOUS",
        subject_id="tor_exit_node_77",
        device_id="unknown_external_device",
        copy_id=bob_copy.copy_id,
        trust_level=TelemetryTrustLevel.OBSERVED,
    )

    report = builder.build_timeline(
        document_root=root,
        copies=[alice_copy, bob_copy],
        forwarding_events=[fwd],
        telemetry_events=[pastebin_drop],
        enrolled_recipient_id="rec_alice",
    )

    assert report.original_recipient_id == "rec_alice"
    assert report.last_known_controlled_holder == "rec_bob"
    assert report.confirmed_publisher_id is None
    assert report.forensic_boundary_state == ForensicBoundaryState.UNKNOWN_DOWNSTREAM_ACTOR
    assert report.should_abstain is True
    assert "DO NOT accuse 'rec_bob' of publishing" in report.boundary_statement


def test_causal_violation_clock_skew_exceeded_fails_closed():
    """
    Security check: If an event arrives with an inverted timestamp that exceeds
    allowable clock skew (> 120s), the system must reject with CONFLICT and abstain.
    """
    builder = UnifiedCustodyTimelineBuilder(max_clock_skew_seconds=120.0)

    t0 = datetime(2026, 9, 27, 14, 0, 0, tzinfo=timezone.utc)
    root = DocumentRoot(
        document_id="doc_causal_test",
        canonical_hash=hashlib.sha256(b"causal_test").hexdigest(),
        byte_size=1024,
        created_at=t0.isoformat(),
    )

    # Document created at 14:00, but an export event claims to have occurred at 13:30 (30 minutes earlier!)
    t_tampered = t0 - timedelta(minutes=30)
    tampered_export = ExportEvent(
        export_id="exp_tampered",
        source_session_id="ses_ghost",
        parent_copy_id="cpy_root",
        child_copy_id="cpy_child",
        export_format=ExportFormat.PDF,
        export_fingerprint="fp_tampered",
        timestamp=t_tampered.isoformat(),
    )

    report = builder.build_timeline(
        document_root=root,
        export_events=[tampered_export],
        enrolled_recipient_id="rec_alice",
    )

    assert report.forensic_boundary_state == ForensicBoundaryState.CONFLICT
    assert report.should_abstain is True
    assert len(report.causality_violations) >= 1
    assert "Causality Violation" in report.causality_violations[0]


def test_multi_sensor_deduplication_anti_double_counting():
    """
    Verifies that concurrent sensor observations of the same action within 5s
    (e.g. EDR file export + DLP alert + USB write) cluster into a single compound action.
    """
    builder = UnifiedCustodyTimelineBuilder(sensor_cluster_window_seconds=5.0)

    t = datetime(2026, 9, 27, 15, 0, 0, tzinfo=timezone.utc)
    dev_id = "ws_finance_42"
    copy_id = "cpy_secret_ledger"

    # Sensor 1: EDR file export at t
    edr_ev = ForensicEvent(
        event_id="edr_001",
        timestamp=t,
        event_type="FILE_EXPORT",
        canonical_type=CanonicalEventType.EXPORTED,
        source_system=TelemetrySource.EDR,
        device_id=dev_id,
        copy_id=copy_id,
        subject_id="alice@finance",
    )

    # Sensor 2: DLP policy violation at t + 1s
    dlp_ev = ForensicEvent(
        event_id="dlp_001",
        timestamp=t + timedelta(seconds=1),
        event_type="DLP_ALERT",
        canonical_type=CanonicalEventType.EXPORTED,
        source_system=TelemetrySource.DLP,
        device_id=dev_id,
        copy_id=copy_id,
        subject_id="alice@finance",
    )

    # Sensor 3: USB write at t + 2s
    usb_ev = ForensicEvent(
        event_id="usb_001",
        timestamp=t + timedelta(seconds=2),
        event_type="USB_TRANSFER",
        canonical_type=CanonicalEventType.WRITTEN_TO_USB,
        source_system=TelemetrySource.USB,
        device_id=dev_id,
        copy_id=copy_id,
        subject_id="alice@finance",
    )

    report = builder.build_timeline(
        telemetry_events=[edr_ev, dlp_ev, usb_ev],
    )

    # 3 raw events should cluster into 1 compound action
    assert len(report.compound_actions) == 1
    compound = report.compound_actions[0]
    assert len(compound.sensor_sources) == 3
    assert set(compound.sensor_sources) == {"EDR", "DLP", "USB"}
    assert len(report.timeline) == 1
    assert report.timeline[0].is_compound is True


def test_impossible_travel_forces_abstention_from_human_attribution():
    """
    Shared workstation / Account Takeover test:
    Account logs in from London, then 15 minutes later logs in from New York (speed > 900 km/h).
    System flags account_compromised_or_shared = True and abstains from human attribution.
    """
    builder = UnifiedCustodyTimelineBuilder()

    t1 = datetime(2026, 9, 27, 8, 0, 0, tzinfo=timezone.utc)
    ev_london = ForensicEvent(
        event_id="idp_london",
        timestamp=t1,
        event_type="USER_AUTH",
        canonical_type=CanonicalEventType.RENDERED,
        source_system=TelemetrySource.IDP,
        subject_id="charlie@enterprise.com",
        device_id="dev_london_laptop",
        raw_payload={"city": "London", "country": "UK"},
    )

    t2 = t1 + timedelta(minutes=15)  # 15 minutes later
    ev_newyork = ForensicEvent(
        event_id="idp_newyork",
        timestamp=t2,
        event_type="USER_AUTH",
        canonical_type=CanonicalEventType.RENDERED,
        source_system=TelemetrySource.IDP,
        subject_id="charlie@enterprise.com",
        device_id="dev_ny_desktop",
        raw_payload={"city": "New York", "country": "USA", "distance_km": 5570.0},
    )

    report = builder.build_timeline(
        telemetry_events=[ev_london, ev_newyork],
        enrolled_recipient_id="rec_charlie",
    )

    assert report.account_compromised_or_shared is True
    assert report.should_abstain is True
    assert report.forensic_boundary_state == ForensicBoundaryState.ABSTAINED
    assert "Impossible Travel" in report.compromise_indicators[0]


def test_airgap_pqc_signed_bundle_import_and_anti_replay():
    """
    Validates air-gapped offline signed bundle transport with Post-Quantum ML-DSA-65 signatures.
    Also validates anti-replay protection.
    """
    TelemetryBundleManager.reset_anti_replay_cache()

    kp = MLDSA65.generate_keypair()
    ev1 = ForensicEvent(
        event_id="evt_bundle_1",
        timestamp=datetime.now(timezone.utc),
        event_type="EXPORT",
        canonical_type=CanonicalEventType.EXPORTED,
        source_system=TelemetrySource.EDR,
        device_id="dev_airgap_vault",
    )

    # 1. Create ML-DSA signed bundle
    bundle = TelemetryBundleManager.create_mldsa_bundle(
        events=[ev1],
        signing_private_key=kp.private_key_bytes,
        signer_public_key=kp.public_key_bytes,
        signer_id="PQC_AIRGAP_AUTHORITY",
    )

    # 2. First import succeeds
    events, is_valid = TelemetryBundleManager.import_and_verify_mldsa_bundle(
        bundle_data=bundle,
        expected_public_key=kp.public_key_bytes,
        enforce_anti_replay=True,
    )
    assert is_valid is True
    assert len(events) == 1
    assert events[0].event_id == "evt_bundle_1"

    # 3. Replay attack: re-submitting the exact same bundle must be rejected
    events_replay, is_valid_replay = TelemetryBundleManager.import_and_verify_mldsa_bundle(
        bundle_data=bundle,
        expected_public_key=kp.public_key_bytes,
        enforce_anti_replay=True,
    )
    assert is_valid_replay is False
    assert events_replay[0].integrity_status == IntegrityLevel.UNTRUSTED


def test_fusion_adapter_attaches_to_evidence_bundle():
    """
    Verifies that TelemetryFusionAdapter attaches CustodyTimelineReport
    to EvidenceBundle with correct dependency type and target binding.
    """
    builder = UnifiedCustodyTimelineBuilder()
    doc_hash = hashlib.sha256(b"fusion_test_doc").hexdigest()
    root = DocumentRoot(
        document_id="doc_fusion_test",
        canonical_hash=doc_hash,
        byte_size=2048,
    )
    cp = CopyInstance(
        copy_id="cpy_fusion_test",
        document_id=root.document_id,
        recipient_principal_id="rec_target_user",
    )

    report = builder.build_timeline(
        document_root=root,
        copies=[cp],
        enrolled_recipient_id="rec_target_user",
    )

    target_bind = TargetBinding(
        document_id=root.document_id,
        recipient_id="rec_target_user",
        original_document_hash=doc_hash,
    )
    bundle = EvidenceBundle(
        bundle_id="bundle_fusion_test",
        target_binding=target_bind,
    )

    TelemetryFusionAdapter.attach_custody_report_to_bundle(bundle, report)

    obs_list = bundle.get_by_family(EvidenceFamily.EXTERNAL_TELEMETRY)
    assert len(obs_list) == 1
    tele_obs = obs_list[0]
    assert tele_obs.is_valid is True
    assert tele_obs.primary_candidate == "rec_target_user"
    assert tele_obs.dependency_type in (DependencyType.INDEPENDENT, DependencyType.PARTIALLY_DEPENDENT)


def test_telemetry_normalization_layer_sysmon_and_edr():
    """
    Verifies that heterogeneous raw logs are normalized deterministically.
    """
    raw_crowdstrike = {
        "source": "CrowdStrike",
        "event_type": "FILE_EXPORT",
        "timestamp": "2026-09-27T10:00:00Z",
        "hostname": "FINANCE-WS-09",
        "username": "dave@corp.com",
        "file_path": "/confidential/q3_forecast.pdf",
    }

    fe = TelemetryNormalizationLayer.normalize_raw_event(raw_crowdstrike)
    assert fe.canonical_type == CanonicalEventType.EXPORTED
    assert fe.device_id == "FINANCE-WS-09"
    assert fe.subject_id == "dave@corp.com"
