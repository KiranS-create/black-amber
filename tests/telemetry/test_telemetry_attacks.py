"""
AegisTrace External Telemetry Adversarial Attack Test Suite (Tests A through V).

Validates the forensic invariants, boundary preservation, tamper resistance,
and fail-closed behavior of the external telemetry correlation engine under
adversarial manipulation.
"""

from datetime import datetime, timezone, timedelta
import json
import pytest

from core.telemetry.models import (
    TelemetrySource,
    IntegrityLevel,
    EndpointEvidence,
    IdentityProviderEvidence,
    NetworkEvidence,
    DLPEvent,
    CASBEvent,
    EmailGatewayEvent,
    USBTransferEvent,
    PrintEvent,
    PublicUploadEvent,
    PhysicalAccessEvidence,
    DeviceForensicEvidence,
)
from core.telemetry.event import ForensicEvent
from core.telemetry.provider import InMemoryTelemetryProvider
from core.telemetry.adapters import (
    EDRAdapter,
    DLPAdapter,
    IdPAdapter,
    NetworkAdapter,
    USBAdapter,
    PrintAdapter,
    PublicUploadAdapter,
    DeviceForensicsProvider,
)
from core.telemetry.temporal import (
    TemporalCorrelationEngine,
    TimelineEntryType,
)
from core.telemetry.engine import (
    TelemetryCorrelationEngine,
    TelemetryAttributionState,
    CandidateAttributionType,
)
from core.telemetry.privacy import TelemetryPrivacyManager
from core.telemetry.bundle import TelemetryBundleManager


# TEST A: Clock Skew Tampering
def test_attack_a_clock_skew_tampering():
    temporal = TemporalCorrelationEngine(default_clock_skew_tolerance_sec=30.0)
    t_release = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
    # Attacker sets timestamp to 1 hour earlier
    t_tampered = t_release - timedelta(hours=1)

    ev_release = ForensicEvent(
        event_id="ev-rel",
        timestamp=t_release,
        event_type="RELEASE",
        source_system=TelemetrySource.EDR,
    )
    ev_exfil = ForensicEvent(
        event_id="ev-exfil",
        timestamp=t_tampered,
        event_type="EXFIL_ATTEMPT",
        source_system=TelemetrySource.EDR,
    )

    res = temporal.validate_causal_pair(ev_release, ev_exfil)
    assert not res.is_valid
    assert "Causal violation" in res.violation_reason
    assert res.clock_skew_seconds == 3600.0


# TEST B: Fake EDR Event Spoofing (Unsigned / Tampered Bundle)
def test_attack_b_fake_edr_event_spoofing():
    provider = InMemoryTelemetryProvider()
    fake_ev = ForensicEvent(
        event_id="spoofed-01",
        timestamp=datetime.now(timezone.utc),
        event_type="FILE_WRITE",
        source_system=TelemetrySource.EDR,
        subject_id="alice@corp.com",
        integrity_status=IntegrityLevel.UNTRUSTED,
        artifact_hash="hash123",
    )
    provider.ingest_event(fake_ev)

    engine = TelemetryCorrelationEngine(provider)
    report = engine.correlate(artifact_hash="hash123", enrolled_recipient_id="alice@corp.com")
    assert report.primary_state == TelemetryAttributionState.ABSTAINED
    assert "ABSTAINED" in report.summary_verdict


# TEST C: Deduplication Inflation Prevention
def test_attack_c_deduplication_inflation_prevention():
    temporal = TemporalCorrelationEngine(dedup_window_sec=5.0)
    t = datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone.utc)

    # 4 sensors firing for the exact same physical action
    e1 = ForensicEvent(event_id="e1", timestamp=t, event_type="FILE_WRITE", source_system=TelemetrySource.EDR, subject_id="bob", artifact_hash="h1", device_id="ws1")
    e2 = ForensicEvent(event_id="e2", timestamp=t + timedelta(seconds=1), event_type="DLP_ALERT", source_system=TelemetrySource.DLP, subject_id="bob", artifact_hash="h1", device_id="ws1")
    e3 = ForensicEvent(event_id="e3", timestamp=t + timedelta(seconds=2), event_type="USB_WRITE", source_system=TelemetrySource.USB, subject_id="bob", artifact_hash="h1", device_id="ws1")

    deduped = temporal.deduplicate_events([e1, e2, e3])
    assert len(deduped) == 1
    assert "concurrent_telemetry_sources" in deduped[0].raw_payload
    assert len(deduped[0].raw_payload["concurrent_telemetry_sources"]) == 2


# TEST D: Account vs Human Conflation Prevention
def test_attack_d_account_vs_human_conflation_prevention():
    provider = InMemoryTelemetryProvider()
    t = datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone.utc)
    ev = ForensicEvent(
        event_id="e-acct",
        timestamp=t,
        event_type="FILE_READ",
        source_system=TelemetrySource.EDR,
        subject_id="contractor_bob",
        device_id="WS-REMOTE-01",
        artifact_hash="art999",
    )
    provider.ingest_event(ev)

    engine = TelemetryCorrelationEngine(provider)
    report = engine.correlate(artifact_hash="art999", copy_id="copy-bob", enrolled_recipient_id="contractor_bob")

    # In the absence of multi-factor physical badge corroboration, must be OBSERVED_ACCOUNT, not CORROBORATED_HUMAN
    for cand in report.candidates:
        assert cand.candidate_type != CandidateAttributionType.CORROBORATED_HUMAN
        assert not cand.is_human_corroborated
    assert report.primary_state != TelemetryAttributionState.HUMAN_ATTRIBUTION_CORROBORATED


# TEST E: Shared Workstation Multi-Badge Ambiguity
def test_attack_e_shared_workstation_multi_badge_ambiguity():
    provider = InMemoryTelemetryProvider()
    t = datetime(2026, 3, 1, 14, 0, 0, tzinfo=timezone.utc)

    # 2 different physical badge swipes during same kiosk session
    b1 = PhysicalAccessEvidence(evidence_id="b1", portal_id="KIOSK-01", badge_token_id="USER-A", facility_zone="ROOM-101", timestamp=t)
    b2 = PhysicalAccessEvidence(evidence_id="b2", portal_id="KIOSK-01", badge_token_id="USER-B", facility_zone="ROOM-101", timestamp=t + timedelta(minutes=5))
    provider.ingest_event(ForensicEvent.from_evidence(b1))
    provider.ingest_event(ForensicEvent.from_evidence(b2))

    engine = TelemetryCorrelationEngine(provider)
    report = engine.correlate(enrolled_recipient_id="USER-A")
    assert report.account_compromised_or_shared
    assert report.primary_state == TelemetryAttributionState.ABSTAINED


# TEST F: Multi-Hop Forwarding Chain (Alice -> Bob -> X -> Y)
def test_attack_f_multi_hop_forwarding_chain():
    provider = InMemoryTelemetryProvider()
    t = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)

    # Alice emails Bob
    email = EmailGatewayEvent(
        evidence_id="em1",
        timestamp=t + timedelta(minutes=10),
        sender_address="alice@corp.com",
        recipient_addresses=["bob@partner.com"],
        attachment_hash="art-hash-secret",
    )
    provider.ingest_event(ForensicEvent.from_evidence(email))

    engine = TelemetryCorrelationEngine(provider)
    report = engine.correlate(
        artifact_hash="art-hash-secret",
        copy_id="copy-alice",
        enrolled_recipient_id="alice@corp.com",
        leak_timestamp=t + timedelta(days=2),
    )

    assert report.original_recipient_id == "alice@corp.com"
    assert report.last_known_controlled_holder == "bob@partner.com"
    assert report.downstream_holder_account == "bob@partner.com"
    # Bob is NOT accused of being the public uploader!
    assert TelemetryAttributionState.UNKNOWN_DOWNSTREAM_ACTOR in report.all_states


# TEST G: Missing Downstream Custody Gap (UNKNOWN Link)
def test_attack_g_missing_downstream_custody_gap():
    temporal = TemporalCorrelationEngine(gap_threshold_sec=300.0)
    t1 = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 3, 3, 10, 0, 0, tzinfo=timezone.utc)  # 2 days later

    e1 = ForensicEvent(event_id="e1", timestamp=t1, event_type="EXPORT", source_system=TelemetrySource.USB)
    e2 = ForensicEvent(event_id="e2", timestamp=t2, event_type="UPLOAD", source_system=TelemetrySource.PUBLIC_UPLOAD)

    timeline = temporal.build_timeline([e1, e2])
    unknown_gaps = [e for e in timeline if e.entry_type == TimelineEntryType.UNKNOWN]
    assert len(unknown_gaps) >= 1
    assert unknown_gaps[0].gap_duration_seconds > 100000


# TEST H: PRNU Device Forensics with NO_REFERENCE
def test_attack_h_prnu_device_forensics_no_reference():
    dfp = DeviceForensicsProvider()
    t = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
    ev, status = dfp.analyze_sensor_prnu("unknown_sensor_hash_9999", t, "art_hash")
    assert status == "NO_REFERENCE"
    assert not ev.raw_payload["reference_corpus_matched"]

    provider = InMemoryTelemetryProvider()
    provider.ingest_event(ev)
    engine = TelemetryCorrelationEngine(provider)
    report = engine.correlate(artifact_hash="art_hash")
    cand = next(c for c in report.candidates if c.candidate_id == "NO_REFERENCE")
    assert cand.confidence <= 0.3
    assert report.downstream_device_id is None


# TEST I: PRNU Device Forensics with Matched Reference
def test_attack_i_prnu_device_forensics_matched_reference():
    dfp = DeviceForensicsProvider(enrolled_prnu_sensors={"prnu_nikon_01": "NIKON-D850-SERIAL-88421"})
    t = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
    ev, status = dfp.analyze_sensor_prnu("prnu_nikon_01", t, "art_hash")
    assert status == "MATCHED"
    assert ev.device_id == "NIKON-D850-SERIAL-88421"

    provider = InMemoryTelemetryProvider()
    provider.ingest_event(ev)
    engine = TelemetryCorrelationEngine(provider)
    report = engine.correlate(artifact_hash="art_hash")
    assert report.downstream_device_id == "NIKON-D850-SERIAL-88421"
    assert TelemetryAttributionState.DOWNSTREAM_DEVICE_IDENTIFIED in report.all_states


# TEST J: Compromised Account / Credential Stuffing
def test_attack_j_compromised_account_credential_stuffing():
    provider = InMemoryTelemetryProvider()
    t = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
    n1 = NetworkEvidence(evidence_id="n1", timestamp=t, source_ip="10.0.0.1", destination_ip="1.1.1.1", is_vpn_or_proxy=False)
    n2 = NetworkEvidence(evidence_id="n2", timestamp=t + timedelta(minutes=5), source_ip="185.220.101.5", destination_ip="1.1.1.1", is_tor_exit=True)
    provider.ingest_event(ForensicEvent.from_evidence(n1))
    provider.ingest_event(ForensicEvent.from_evidence(n2))

    engine = TelemetryCorrelationEngine(provider)
    report = engine.correlate(enrolled_recipient_id="alice@corp.com")
    assert report.account_compromised_or_shared
    assert report.primary_state == TelemetryAttributionState.ABSTAINED


# TEST K: VPN / Proxy / Tor Egress Network Ambiguity
def test_attack_k_vpn_proxy_network_ambiguity():
    raw_net = {
        "flow_id": "net-vpn-01",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_ip": "198.51.100.44",
        "destination_ip": "104.21.4.1",
        "is_vpn_or_proxy": True,
        "protocol": "TLS",
    }
    ev = NetworkAdapter.parse_event(raw_net)
    assert ev.raw_payload["is_vpn_or_proxy"]
    assert ev.subject_type == "NETWORK"


# TEST L: DLP Alert Deduplication with EDR File Write
def test_attack_l_dlp_deduplication_with_edr():
    temporal = TemporalCorrelationEngine(dedup_window_sec=5.0)
    t = datetime(2026, 3, 1, 11, 0, 0, tzinfo=timezone.utc)

    edr_raw = {"event_id": "edr-1", "timestamp": t.isoformat(), "file_hash": "hash_x", "username": "alice", "hostname": "ws1"}
    dlp_raw = {"incident_id": "dlp-1", "timestamp": (t + timedelta(seconds=2)).isoformat(), "file_sha256": "hash_x", "sender": "alice", "endpoint_id": "ws1"}

    e_edr = EDRAdapter.parse_event(edr_raw)
    e_dlp = DLPAdapter.parse_event(dlp_raw)

    deduped = temporal.deduplicate_events([e_edr, e_dlp])
    assert len(deduped) == 1


# TEST M: USB Transfer with Unknown Destination PC
def test_attack_m_usb_transfer_unknown_destination():
    raw_usb = {
        "event_id": "usb-test-01",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "username": "charlie",
        "volume_serial": "KINGSTON-9941",
        "file_sha256": "art-hash-m",
    }
    ev = USBAdapter.parse_event(raw_usb)
    assert ev.source_system == TelemetrySource.USB
    assert ev.artifact_hash == "art-hash-m"


# TEST N: Print Spooler without MIC
def test_attack_n_print_spooler_without_mic():
    raw_print = {
        "job_id": "pj-01",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "document_sha256": "doc-hash-n",
        "has_mic_yellow_dots": False,
        "mic_decoded_serial": None,
    }
    ev = PrintAdapter.parse_event(raw_print)
    assert not ev.raw_payload["has_mic_yellow_dots"]
    assert ev.raw_payload["mic_decoded_serial"] is None


# TEST O: Print Spooler with MIC Yellow Dots
def test_attack_o_print_spooler_with_mic():
    dfp = DeviceForensicsProvider(enrolled_mic_printers={"MIC-XEROX-9000": "PRINTER-HQ-4FL"})
    t = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
    ev, status = dfp.analyze_printer_mic("MIC-XEROX-9000", t, "doc-hash-o")
    assert status == "MATCHED"
    assert ev.device_id == "PRINTER-HQ-4FL"


# TEST P: Public Upload with Anonymous Pastebin
def test_attack_p_public_upload_anonymous_pastebin():
    raw_pub = {
        "upload_id": "paste-99",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "platform_name": "PASTEBIN",
        "public_url": "https://pastebin.com/raw/XYZ123",
        "uploader_handle": "anon_drop",
        "file_sha256": "leaked_hash_p",
    }
    ev = PublicUploadAdapter.parse_event(raw_pub)
    assert ev.source_system == TelemetrySource.PUBLIC_UPLOAD
    assert ev.subject_type == "ANONYMOUS"


# TEST Q: Cloud Storage Pre-Signed URL Leak
def test_attack_q_cloud_storage_presigned_leak():
    t = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
    ev = ForensicEvent.from_evidence(
        CASBEvent(
            evidence_id="casb-01",
            timestamp=t,
            cloud_service="AWS_S3",
            sharing_scope="PUBLIC",
            operation="CREATE_PRESIGNED_URL",
            document_hash="s3_doc_hash",
            actor_account_id="arn:aws:iam::123456789012:user/devops_lead",
        )
    )
    assert ev.source_system == TelemetrySource.CASB
    assert ev.subject_id == "arn:aws:iam::123456789012:user/devops_lead"


# TEST R: Conflicting Telemetry Timestamps (Predecessor Violation)
def test_attack_r_conflicting_timestamps():
    temporal = TemporalCorrelationEngine(default_clock_skew_tolerance_sec=10.0)
    t = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
    e1 = ForensicEvent(event_id="e1", timestamp=t, event_type="UPLOAD", source_system=TelemetrySource.PUBLIC_UPLOAD)
    e2 = ForensicEvent(event_id="e2", timestamp=t - timedelta(minutes=5), event_type="ENCRYPT", source_system=TelemetrySource.EDR)

    res = temporal.validate_causal_pair(e1, e2)
    assert not res.is_valid


# TEST S: Malformed / Corrupted Telemetry Bundle
def test_attack_s_malformed_telemetry_bundle():
    key = b"super_secret_test_key_12345"
    events = [ForensicEvent(event_id="ev1", timestamp=datetime.now(timezone.utc), event_type="TEST", source_system=TelemetrySource.EDR)]
    bundle_json = TelemetryBundleManager.export_bundle_json(events, key)

    # Corrupt bundle JSON
    bundle_dict = json.loads(bundle_json)
    bundle_dict["manifest"]["event_count"] = 999  # Tampered count

    loaded_events, is_valid = TelemetryBundleManager.import_and_verify_bundle(bundle_dict, key)
    assert not is_valid
    assert loaded_events[0].integrity_status == IntegrityLevel.UNTRUSTED


# TEST T: Privacy Redaction and Retention Expiry
def test_attack_t_privacy_redaction_and_retention():
    privacy = TelemetryPrivacyManager()
    t_old = datetime.now(timezone.utc) - timedelta(days=120)  # >90 days old
    t_new = datetime.now(timezone.utc) - timedelta(days=10)

    e_old = ForensicEvent(event_id="old", timestamp=t_old, event_type="READ", source_system=TelemetrySource.EDR, subject_id="alice")
    e_new = ForensicEvent(event_id="new", timestamp=t_new, event_type="READ", source_system=TelemetrySource.EDR, subject_id="alice", network_id="192.168.1.50")

    # Retention purge
    retained = privacy.purge_expired_events([e_old, e_new], retention_days=90)
    assert len(retained) == 1
    assert retained[0].event_id == "new"

    # Redaction
    redacted = privacy.redact_event(e_new)
    assert redacted.subject_id.startswith("anon-")
    assert redacted.network_id == "192.168.1.0/24"


# TEST U: Tamper Detection on HMAC-Signed Bundle
def test_attack_u_hmac_tamper_detection():
    key = b"tamper_detection_key_5678"
    e1 = ForensicEvent(event_id="e1", timestamp=datetime.now(timezone.utc), event_type="TEST", source_system=TelemetrySource.EDR, artifact_hash="orig_hash")
    bundle = TelemetryBundleManager.create_bundle([e1], key)

    # Attacker alters artifact hash in payload
    bundle["events"][0]["artifact_hash"] = "hacked_hash"

    events, is_valid = TelemetryBundleManager.import_and_verify_bundle(bundle, key)
    assert not is_valid
    assert events[0].integrity_status == IntegrityLevel.UNTRUSTED


# TEST V: Abstain on Insufficient Evidence
def test_attack_v_abstain_on_insufficient_evidence():
    provider = InMemoryTelemetryProvider()
    engine = TelemetryCorrelationEngine(provider)
    report = engine.correlate()
    assert report.primary_state == TelemetryAttributionState.INSUFFICIENT_EVIDENCE
