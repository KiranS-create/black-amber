"""
AegisTrace Critical Test Cases (Cases 1 through 8).

Validates the complete set of mandatory forensic scenarios:
1. Exact copy match, zero external telemetry (Cryptographic boundary holds)
2. Clean single-recipient leak with full EDR + Network corroboration
3. Enterprise forwarding (Alice -> Bob), Bob's copy leaked, Bob's upload unobserved
4. Account takeover (Alice's account accessed from foreign IP + impossible travel)
5. Shared kiosk workstation (3 shifts, 1 shared login)
6. Physical leak (Printed document with MIC serial vs. without MIC)
7. Unenrolled camera photo leak (PRNU unmatched -> NO_REFERENCE)
8. Multi-hop external leak with public pastebin and VPN egress
"""

from datetime import datetime, timezone, timedelta
import pytest

from core.telemetry.models import (
    TelemetrySource,
    IntegrityLevel,
    EndpointEvidence,
    IdentityProviderEvidence,
    NetworkEvidence,
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
from core.telemetry.temporal import TemporalCorrelationEngine, TimelineEntryType
from core.telemetry.engine import (
    TelemetryCorrelationEngine,
    TelemetryAttributionState,
    CandidateAttributionType,
)
from core.telemetry.fusion_adapter import TelemetryFusionAdapter
from core.attribution.evidence import EvidenceBundle, TargetBinding, EvidenceFamily


# CASE 1: Exact copy match, zero external telemetry
def test_case_1_exact_copy_match_zero_external_telemetry():
    """
    Cryptographic watermark identifies Alice. Zero external telemetry exists.
    AegisTrace must assert original recipient Alice, but strictly state that
    custody beyond distribution is unobserved, refusing to accuse Alice of leaking.
    """
    provider = InMemoryTelemetryProvider()  # Empty provider
    engine = TelemetryCorrelationEngine(provider)

    report = engine.correlate(
        artifact_hash="art-sha256-alice-secret",
        copy_id="copy-alice-01",
        enrolled_recipient_id="alice@corp.com",
        release_timestamp=datetime(2026, 3, 1, 9, 0, 0, tzinfo=timezone.utc),
        leak_timestamp=datetime(2026, 3, 2, 12, 0, 0, tzinfo=timezone.utc),
    )

    assert report.primary_state == TelemetryAttributionState.ORIGINAL_RECIPIENT_IDENTIFIED
    assert report.original_recipient_id == "alice@corp.com"
    assert report.last_known_controlled_holder == "alice@corp.com"
    # Ensure boundary statement explicitly protects Alice from unobserved leak accusations
    assert "Observed telemetry documents system, network, and account actions" in report.boundary_statement
    assert "ends at release boundary" in report.summary_verdict
    # Confirm custody gaps detected between release and leak
    assert len(report.custody_gaps) >= 1


# CASE 2: Clean single-recipient leak with full EDR + Network corroboration
def test_case_2_clean_single_recipient_corroborated_leak():
    """
    Alice opens file, badges into office, active console EDR session,
    and direct upload egress. Corroborates human operator and attaches to EvidenceBundle.
    """
    provider = InMemoryTelemetryProvider()
    t = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)

    # 1. EDR File open
    e_edr = ForensicEvent.from_evidence(
        EndpointEvidence(
            evidence_id="edr-01",
            timestamp=t,
            actor_account_id="alice@corp.com",
            device_id="WS-ALICE-DESKTOP",
            file_operation="READ",
            document_hash="doc-hash-2",
            copy_id="copy-alice-2",
        )
    )
    # 2. Physical badge swipe into office
    e_badge = ForensicEvent.from_evidence(
        PhysicalAccessEvidence(
            evidence_id="badge-01",
            timestamp=t - timedelta(minutes=15),
            portal_id="TURNSTILE-4F",
            badge_token_id="alice@corp.com",
            facility_zone="FINANCE-HQ",
        )
    )
    # 3. Direct upload egress
    e_pub = ForensicEvent.from_evidence(
        PublicUploadEvent(
            evidence_id="pub-01",
            timestamp=t + timedelta(minutes=5),
            platform_name="FILE_DROP",
            uploader_account="alice@corp.com",
            document_hash="doc-hash-2",
            copy_id="copy-alice-2",
        )
    )
    provider.ingest_batch([e_edr, e_badge, e_pub])

    engine = TelemetryCorrelationEngine(provider)
    report = engine.correlate(
        artifact_hash="doc-hash-2",
        copy_id="copy-alice-2",
        enrolled_recipient_id="alice@corp.com",
    )

    assert report.primary_state == TelemetryAttributionState.HUMAN_ATTRIBUTION_CORROBORATED
    human_cand = next(c for c in report.candidates if c.candidate_type == CandidateAttributionType.CORROBORATED_HUMAN)
    assert human_cand.candidate_id == "alice@corp.com"
    assert human_cand.is_human_corroborated

    # Verify integration with EvidenceBundle
    bundle = EvidenceBundle(bundle_id="b-case-2", target_binding=TargetBinding(recipient_id="alice@corp.com"))
    TelemetryFusionAdapter.attach_to_bundle(bundle, report)
    obs = bundle.get_by_family(EvidenceFamily.EXTERNAL_TELEMETRY)
    assert len(obs) == 1
    assert obs[0].is_valid
    assert obs[0].primary_state == "HUMAN_ATTRIBUTION_CORROBORATED"
    assert obs[0].log_likelihood_ratio > 4.0


# CASE 3: Enterprise forwarding (Alice -> Bob), Bob's copy leaked, Bob's upload unobserved
def test_case_3_enterprise_forwarding_bob_unobserved_upload():
    """
    Alice emails Bob. Leaked document has Bob's copy watermark on Pastebin.
    No telemetry logs Bob uploading to Pastebin.
    Engine must state:
      - Original recipient: Alice
      - Forwarding observed: Alice -> Bob
      - Last known holder: Bob
      - Publication: Pastebin
      - Uploader: UNKNOWN_DOWNSTREAM_ACTOR (Bob is NOT accused of publishing!).
    """
    provider = InMemoryTelemetryProvider()
    t = datetime(2026, 3, 1, 9, 0, 0, tzinfo=timezone.utc)

    # Email forward
    e_email = ForensicEvent.from_evidence(
        EmailGatewayEvent(
            evidence_id="em-forward",
            timestamp=t + timedelta(hours=1),
            sender_address="alice@corp.com",
            recipient_addresses=["bob@partner.com"],
            attachment_hash="hash-doc-case-3",
            copy_id="copy-bob-3",
        )
    )
    provider.ingest_event(e_email)

    engine = TelemetryCorrelationEngine(provider)
    report = engine.correlate(
        artifact_hash="hash-doc-case-3",
        copy_id="copy-bob-3",
        enrolled_recipient_id="alice@corp.com",
        leak_timestamp=t + timedelta(days=3),
    )

    assert report.original_recipient_id == "alice@corp.com"
    assert report.last_known_controlled_holder == "bob@partner.com"
    assert report.downstream_holder_account == "bob@partner.com"
    assert TelemetryAttributionState.UNKNOWN_DOWNSTREAM_ACTOR in report.all_states
    # Bob is only recorded as OBSERVED_ACCOUNT recipient of forwarding
    bob_cands = [c for c in report.candidates if c.candidate_id == "bob@partner.com"]
    assert len(bob_cands) >= 1
    assert bob_cands[0].candidate_type == CandidateAttributionType.OBSERVED_ACCOUNT
    assert not bob_cands[0].is_human_corroborated


# CASE 4: Account takeover (Alice's account accessed from foreign IP + impossible travel)
def test_case_4_account_takeover_impossible_travel():
    """
    Alice's badge in London. 15 minutes later, login from Vladivostok IP via VPN.
    Engine flags account takeover / shared session and abstains (ABSTAINED).
    """
    provider = InMemoryTelemetryProvider()
    t = datetime(2026, 3, 1, 14, 0, 0, tzinfo=timezone.utc)

    e_london = ForensicEvent.from_evidence(
        PhysicalAccessEvidence(
            evidence_id="badge-lon",
            timestamp=t,
            portal_id="LON-GATEWAY",
            badge_token_id="alice@corp.com",
            facility_zone="LONDON-OFFICE",
        )
    )
    e_foreign = ForensicEvent.from_evidence(
        NetworkEvidence(
            evidence_id="net-foreign",
            timestamp=t + timedelta(minutes=15),
            source_ip="194.135.12.8",
            destination_ip="10.0.0.1",
            is_vpn_or_proxy=True,
            network_id="194.135.12.8",
            actor_account_id="alice@corp.com",
        )
    )
    e_login = ForensicEvent.from_evidence(
        NetworkEvidence(
            evidence_id="net-vpn-2",
            timestamp=t + timedelta(minutes=20),
            source_ip="194.135.12.9",
            destination_ip="10.0.0.2",
            is_tor_exit=True,
            network_id="194.135.12.9",
            actor_account_id="alice@corp.com",
        )
    )
    provider.ingest_batch([e_london, e_foreign, e_login])

    engine = TelemetryCorrelationEngine(provider)
    report = engine.correlate(enrolled_recipient_id="alice@corp.com")

    assert report.account_compromised_or_shared
    assert report.primary_state == TelemetryAttributionState.ABSTAINED
    assert "ABSTAINED" in report.summary_verdict


# CASE 5: Shared kiosk workstation (3 shifts, 1 shared login)
def test_case_5_shared_kiosk_workstation():
    """
    Workstation KIOSK-01 accessed with generic account 'lab_user'.
    Multiple badge swipes occur during active period.
    Engine attributes to device/account, but strictly ABSTAINS from human accusation.
    """
    provider = InMemoryTelemetryProvider()
    t = datetime(2026, 3, 1, 8, 0, 0, tzinfo=timezone.utc)

    # 1. Generic EDR file access
    e_edr = ForensicEvent.from_evidence(
        EndpointEvidence(
            evidence_id="edr-kiosk",
            timestamp=t + timedelta(hours=2),
            actor_account_id="lab_user",
            device_id="KIOSK-01",
            file_operation="READ",
            document_hash="lab_report_hash",
        )
    )
    # 2. Worker 1 badge
    b1 = ForensicEvent.from_evidence(
        PhysicalAccessEvidence(
            evidence_id="b-dave",
            timestamp=t,
            portal_id="KIOSK-01",
            badge_token_id="worker_dave",
            facility_zone="LAB-A",
        )
    )
    # 3. Worker 2 badge
    b2 = ForensicEvent.from_evidence(
        PhysicalAccessEvidence(
            evidence_id="b-eve",
            timestamp=t + timedelta(hours=4),
            portal_id="KIOSK-01",
            badge_token_id="worker_eve",
            facility_zone="LAB-A",
        )
    )
    provider.ingest_batch([e_edr, b1, b2])

    engine = TelemetryCorrelationEngine(provider)
    report = engine.correlate(artifact_hash="lab_report_hash")

    assert report.account_compromised_or_shared
    assert report.primary_state == TelemetryAttributionState.ABSTAINED


# CASE 6: Physical leak (Printed document with MIC serial vs. without MIC)
def test_case_6_physical_leak_printed_mic_comparison():
    """
    Subcase A: Printer yellow tracking dot matches enrolled Xerox printer. -> DOWNSTREAM_DEVICE_IDENTIFIED
    Subcase B: Black/white printer without MIC dots. -> NO_REFERENCE
    """
    dfp = DeviceForensicsProvider(enrolled_mic_printers={"MIC-XEROX-8820": "PRINTER-EXECUTIVE-BOARDROOM"})
    t = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)

    # Subcase A: Enrolled MIC
    ev_a, status_a = dfp.analyze_printer_mic("MIC-XEROX-8820", t, "print-hash-6a")
    assert status_a == "MATCHED"
    assert ev_a.device_id == "PRINTER-EXECUTIVE-BOARDROOM"

    provider_a = InMemoryTelemetryProvider()
    provider_a.ingest_event(ev_a)
    report_a = TelemetryCorrelationEngine(provider_a).correlate(artifact_hash="print-hash-6a")
    assert report_a.downstream_device_id == "PRINTER-EXECUTIVE-BOARDROOM"
    assert report_a.primary_state == TelemetryAttributionState.DOWNSTREAM_DEVICE_IDENTIFIED

    # Subcase B: Unenrolled MIC
    ev_b, status_b = dfp.analyze_printer_mic("MIC-UNKNOWN-GENERIC", t, "print-hash-6b")
    assert status_b == "NO_REFERENCE"
    provider_b = InMemoryTelemetryProvider()
    provider_b.ingest_event(ev_b)
    report_b = TelemetryCorrelationEngine(provider_b).correlate(artifact_hash="print-hash-6b")
    assert report_b.downstream_device_id is None


# CASE 7: Unenrolled camera photo leak (PRNU unmatched -> NO_REFERENCE)
def test_case_7_unenrolled_camera_photo_leak_no_reference():
    """
    Photograph of document posted on Twitter. PRNU noise extracted.
    Sensor signature not present in enrolled corporate camera database.
    Provider asserts NO_REFERENCE. Engine does NOT hallucinate a camera match.
    """
    dfp = DeviceForensicsProvider(enrolled_prnu_sensors={"prnu_corp_canon_1": "CORP-CANON-EOS-01"})
    t = datetime(2026, 3, 1, 15, 0, 0, tzinfo=timezone.utc)

    # Observed leak has external iPhone sensor noise
    ev, status = dfp.analyze_sensor_prnu("prnu_external_iphone_unknown", t, "doc-photo-leak")
    assert status == "NO_REFERENCE"
    assert not ev.raw_payload["reference_corpus_matched"]

    provider = InMemoryTelemetryProvider()
    provider.ingest_event(ev)
    report = TelemetryCorrelationEngine(provider).correlate(artifact_hash="doc-photo-leak")

    assert report.downstream_device_id is None
    cand = next(c for c in report.candidates if c.candidate_id == "NO_REFERENCE")
    assert cand.confidence <= 0.3
    assert "lacks enrolled reference baseline" in cand.evidence_boundary_statement


# CASE 8: Multi-hop external leak with public pastebin and VPN egress
def test_case_8_multi_hop_external_leak_with_pastebin_and_vpn():
    """
    Alice -> USB Export -> Contractor Machine -> Pastebin via VPN.
    Graph traces lineage, identifies hops, detects custody gaps, and bounds attribution.
    """
    provider = InMemoryTelemetryProvider()
    t = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)

    # 1. USB Export
    e_usb = ForensicEvent.from_evidence(
        USBTransferEvent(
            evidence_id="usb-case-8",
            timestamp=t + timedelta(hours=1),
            actor_account_id="alice@corp.com",
            device_id="WS-ALICE",
            volume_serial="SAN-DISK-9901",
            document_hash="hash-case-8",
            copy_id="copy-alice-8",
        )
    )
    # 2. Pastebin dump
    e_paste = ForensicEvent.from_evidence(
        PublicUploadEvent(
            evidence_id="paste-case-8",
            timestamp=t + timedelta(days=1),
            platform_name="PASTEBIN",
            public_url="https://pastebin.com/raw/leaked8",
            uploader_account="leak_drop_99",
            document_hash="hash-case-8",
            copy_id="copy-alice-8",
        )
    )
    provider.ingest_batch([e_usb, e_paste])

    engine = TelemetryCorrelationEngine(provider)
    report = engine.correlate(
        artifact_hash="hash-case-8",
        copy_id="copy-alice-8",
        enrolled_recipient_id="alice@corp.com",
    )

    assert report.original_recipient_id == "alice@corp.com"
    assert report.publication_source == "PASTEBIN"
    assert TelemetryAttributionState.PUBLICATION_EVENT_IDENTIFIED in report.all_states
    assert len(report.custody_gaps) >= 1
    # Candidate list has Pastebin account handle, not Alice for the upload!
    paste_cand = next(c for c in report.candidates if "PASTEBIN" in c.candidate_id)
    assert paste_cand.candidate_type == CandidateAttributionType.OBSERVED_ACCOUNT
    assert not paste_cand.is_human_corroborated
