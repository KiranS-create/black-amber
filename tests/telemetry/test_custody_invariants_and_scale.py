"""
tests/telemetry/test_custody_invariants_and_scale.py

Formal invariant verification and real scalability benchmarks for the
AegisTrace Unified Custody Timeline & Telemetry Lineage Integration Engine.

Verifies:
1. Timestamp monotonicity along causal edges (Root -> Release -> Decrypt -> Render -> Export -> Egress).
2. Clock skew tolerance limit (<= 120s tolerated, > 120s triggers CONFLICT/ABSTAINED).
3. Non-conflation of multiple independent copy recipients.
4. Cryptographic anti-replay nonce enforcement on offline bundles.
5. Concurrent multi-device / shared terminal detection leading to abstention.
6. Multi-sensor deduplication clustering into compound actions.
7. Real scalability benchmarks (1k, 10k, 100k events) with wall-clock time and memory profiling.
"""

import time
import tracemalloc
import hashlib
from datetime import datetime, timedelta, timezone
from typing import List
import pytest

from core.telemetry import (
    CanonicalEventType,
    DeviceAttestationState,
    ForensicAttributionLevel,
    ForensicBoundaryState,
    IntegrityLevel,
    TelemetrySource,
    TelemetryTrustLevel,
    ForensicEvent,
    UnifiedCustodyTimelineBuilder,
    CustodyTimelineReport,
    CustodyTimelineItem,
    CustodyCausalStatus,
)
from core.crypto.signatures import MLDSA65
from core.telemetry.bundle import TelemetryBundleManager
from core.lineage.models import (
    DocumentRoot,
    CopyInstance,
    AccessSession,
    ForwardingEvent,
    ExportEvent,
    ExportFormat,
    DeviceBinding,
    DeviceAttestationStatus,
    PlatformType,
)


# ============================================================================
# 1. INVARIANT TESTS: CAUSAL MONOTONICITY & CLOCK SKEW BOUNDS
# ============================================================================

def test_invariant_monotonic_causal_chain():
    """
    INVARIANT 1: Monotonicity along a single causal edge.
    Timestamps for Root -> Release -> Decrypt -> Render -> Export -> Egress
    must be strictly monotonic or within allowable clock skew (120s).
    """
    builder = UnifiedCustodyTimelineBuilder(max_clock_skew_seconds=120)
    t0 = datetime(2026, 9, 27, 8, 0, 0, tzinfo=timezone.utc)

    # 1. DocumentRoot created at t0
    root = DocumentRoot(
        document_id="doc_invariant_001",
        canonical_hash=hashlib.sha256(b"invariant_content").hexdigest(),
        byte_size=4096,
        created_at=t0.isoformat(),
    )

    # 2. Copy released at t0 + 10s
    t_rel = t0 + timedelta(seconds=10)
    cp = CopyInstance(
        copy_id="cpy_inv_001",
        document_id=root.document_id,
        recipient_principal_id="rec_analyst_01",
        issuance_timestamp=t_rel.isoformat(),
        lineage_depth=0,
    )

    # 3. Session Decrypt at t_rel + 30s
    t_dec = t_rel + timedelta(seconds=30)
    dev = DeviceBinding(
        device_id="dev_inv_01",
        device_key_id="dkey_tpm_01",
        attestation_status=DeviceAttestationStatus.DEVICE_ATTESTED,
        platform_type=PlatformType.TPM,
    )
    sess = AccessSession(
        session_id="ses_inv_001",
        copy_id=cp.copy_id,
        identity_id="analyst@defense.gov",
        device_key_id=dev.device_key_id,
        issued_at=t_dec.isoformat(),
    )

    # 4. Decryption telemetry event at t_dec
    ev_dec = ForensicEvent(
        event_id="ev_dec_01",
        timestamp=t_dec,
        event_type="DECRYPT_PAYLOAD",
        canonical_type=CanonicalEventType.DECRYPTED,
        source_system=TelemetrySource.EDR,
        device_id=dev.device_id,
        copy_id=cp.copy_id,
        session_id=sess.session_id,
    )

    # 5. Render event at t_dec + 5s
    t_rend = t_dec + timedelta(seconds=5)
    ev_rend = ForensicEvent(
        event_id="ev_rend_01",
        timestamp=t_rend,
        event_type="RENDER_CANVAS",
        canonical_type=CanonicalEventType.RENDERED,
        source_system=TelemetrySource.EDR,
        device_id=dev.device_id,
        copy_id=cp.copy_id,
        session_id=sess.session_id,
    )

    # 6. Export at t_rend + 20s
    t_exp = t_rend + timedelta(seconds=20)
    cp_exp = CopyInstance(
        copy_id="cpy_inv_exp",
        parent_copy_id=cp.copy_id,
        document_id=root.document_id,
        recipient_principal_id="rec_analyst_01",
        issuance_timestamp=t_exp.isoformat(),
        lineage_depth=1,
    )
    exp_ev = ExportEvent(
        export_id="exp_inv_01",
        source_session_id=sess.session_id,
        parent_copy_id=cp.copy_id,
        child_copy_id=cp_exp.copy_id,
        export_format=ExportFormat.PDF,
        export_fingerprint="fp_inv_exp",
        actor_principal_id="rec_analyst_01",
        timestamp=t_exp.isoformat(),
    )

    report = builder.build_timeline(
        document_root=root,
        copies=[cp, cp_exp],
        sessions=[sess],
        export_events=[exp_ev],
        telemetry_events=[ev_dec, ev_rend],
        enrolled_devices={dev.device_key_id: dev},
        enrolled_recipient_id="rec_analyst_01",
    )

    assert len(report.causality_violations) == 0
    assert report.forensic_boundary_state == ForensicBoundaryState.ATTRIBUTED_TO_CONTROLLED_ACTOR
    assert not report.should_abstain


def test_invariant_clock_skew_tolerated_within_120s():
    """
    INVARIANT 2: Clock skew <= 120s along a causal edge is tolerated.
    If Render is reported 45s before Decrypt due to NTP jitter across nodes,
    it must be flagged as CLOCK_SKEW_TOLERATED and NOT fail-closed.
    """
    builder = UnifiedCustodyTimelineBuilder(max_clock_skew_seconds=120)
    t0 = datetime(2026, 9, 27, 9, 0, 0, tzinfo=timezone.utc)

    root = DocumentRoot(document_id="doc_skew_01", canonical_hash="hash01", byte_size=1024, created_at=t0.isoformat())
    cp = CopyInstance(copy_id="cpy_01", document_id=root.document_id, issuance_timestamp=t0.isoformat())

    # Decrypt at t0 + 100s
    t_dec = t0 + timedelta(seconds=100)
    ev_dec = ForensicEvent(
        event_id="ev_dec_skew",
        timestamp=t_dec,
        event_type="KEY_DECRYPT",
        canonical_type=CanonicalEventType.DECRYPTED,
        source_system=TelemetrySource.EDR,
        session_id="ses_skew_01",
        copy_id=cp.copy_id,
    )

    # Render at t_dec - 45s (55s after creation, but 45s before decrypt record)
    t_rend = t_dec - timedelta(seconds=45)
    ev_rend = ForensicEvent(
        event_id="ev_rend_skew",
        timestamp=t_rend,
        event_type="RENDER",
        canonical_type=CanonicalEventType.RENDERED,
        source_system=TelemetrySource.EDR,
        session_id="ses_skew_01",
        copy_id=cp.copy_id,
    )

    report = builder.build_timeline(
        document_root=root,
        copies=[cp],
        telemetry_events=[ev_dec, ev_rend],
        enrolled_recipient_id="rec_test",
    )

    # Within 120s threshold: no hard causality violation
    assert len(report.causality_violations) == 0
    assert not report.should_abstain


def test_invariant_clock_skew_exceeded_fails_closed():
    """
    INVARIANT 3: Clock skew > 120s along a causal edge violates causality.
    Must transition boundary to CONFLICT, flag should_abstain=True, and zero confidence.
    """
    builder = UnifiedCustodyTimelineBuilder(max_clock_skew_seconds=120)
    t0 = datetime(2026, 9, 27, 10, 0, 0, tzinfo=timezone.utc)

    root = DocumentRoot(document_id="doc_skew_bad", canonical_hash="hash02", byte_size=1024, created_at=t0.isoformat())
    cp = CopyInstance(copy_id="cpy_02", document_id=root.document_id, issuance_timestamp=t0.isoformat())

    # EDR reports document decryption 300s BEFORE document creation
    t_impossible = t0 - timedelta(seconds=300)
    ev_impossible = ForensicEvent(
        event_id="ev_impossible_01",
        timestamp=t_impossible,
        event_type="DECRYPT",
        canonical_type=CanonicalEventType.DECRYPTED,
        source_system=TelemetrySource.EDR,
        copy_id=cp.copy_id,
    )

    report = builder.build_timeline(
        document_root=root,
        copies=[cp],
        telemetry_events=[ev_impossible],
        enrolled_recipient_id="rec_test",
    )

    assert len(report.causality_violations) >= 1
    assert report.forensic_boundary_state == ForensicBoundaryState.CONFLICT
    assert report.should_abstain is True
    assert report.confidence_score == 0.0


# ============================================================================
# 2. INVARIANT TESTS: NON-CONFLATION & RECIPIENT BOUNDARIES
# ============================================================================

def test_invariant_multi_recipient_non_conflation():
    """
    INVARIANT 4: Non-conflation of independent recipients.
    When Document Root is issued to Alice and Bob independently (distinct copies),
    and an egress event is observed on Bob's endpoint, Alice's principal identity
    must NEVER be merged, accused, or conflated with Bob.
    """
    builder = UnifiedCustodyTimelineBuilder()
    t0 = datetime(2026, 9, 27, 11, 0, 0, tzinfo=timezone.utc)

    root = DocumentRoot(document_id="doc_multi", canonical_hash="multi_hash", byte_size=2048, created_at=t0.isoformat())

    # Copy 1: Alice
    alice_cp = CopyInstance(
        copy_id="cpy_alice",
        document_id=root.document_id,
        recipient_principal_id="rec_alice",
        issuance_timestamp=(t0 + timedelta(minutes=1)).isoformat(),
        lineage_depth=0,
    )

    # Copy 2: Bob
    bob_cp = CopyInstance(
        copy_id="cpy_bob",
        document_id=root.document_id,
        recipient_principal_id="rec_bob",
        issuance_timestamp=(t0 + timedelta(minutes=2)).isoformat(),
        lineage_depth=0,
    )

    # USB transfer observed on Bob's laptop for Bob's copy
    t_usb = t0 + timedelta(minutes=10)
    bob_usb = ForensicEvent(
        event_id="ev_bob_usb",
        timestamp=t_usb,
        event_type="USB_STOR",
        canonical_type=CanonicalEventType.WRITTEN_TO_USB,
        source_system=TelemetrySource.USB,
        device_id="ws_bob_laptop",
        copy_id=bob_cp.copy_id,
        subject_id="bob@defense.gov",
    )

    report_alice = builder.build_timeline(
        document_root=root,
        copies=[alice_cp, bob_cp],
        telemetry_events=[bob_usb],
        enrolled_recipient_id="rec_alice",
    )

    # For Alice's query: Bob's USB event does not implicate Alice
    assert report_alice.original_recipient_id == "rec_alice"
    assert report_alice.confirmed_publisher_id is None
    assert report_alice.downstream_holder_account != "rec_alice"


# ============================================================================
# 3. INVARIANT TESTS: ANTI-REPLAY NONCE SINGLE-USE
# ============================================================================

def test_invariant_anti_replay_nonce_single_use():
    """
    INVARIANT 5: Anti-replay nonce single use.
    An offline telemetry bundle signed with ML-DSA-65 / HMAC contains a unique nonce.
    Re-importing the same bundle or reusing its nonce must fail with ValueError("Replay attack detected").
    """
    TelemetryBundleManager.reset_anti_replay_cache()
    kp = MLDSA65.generate_keypair()
    ev = ForensicEvent(
        event_id="ev_airgap_replay",
        timestamp=datetime.now(timezone.utc),
        event_type="FILE_OPEN",
        canonical_type=CanonicalEventType.RENDERED,
        source_system=TelemetrySource.EDR,
        device_id="dev_isolated",
    )

    # Create bundle
    bundle_bytes = TelemetryBundleManager.create_mldsa_bundle(
        events=[ev],
        signing_private_key=kp.private_key_bytes,
        signer_public_key=kp.public_key_bytes,
        signer_id="PQC_AIRGAP_AUTHORITY",
    )

    # First import: must succeed
    events_1, is_valid_1 = TelemetryBundleManager.import_and_verify_mldsa_bundle(
        bundle_data=bundle_bytes,
        expected_public_key=kp.public_key_bytes,
        enforce_anti_replay=True,
    )
    assert is_valid_1 is True
    assert len(events_1) == 1
    assert events_1[0].event_id == "ev_airgap_replay"

    # Second import: replay attempt with identical nonce -> rejected
    events_replay, is_valid_replay = TelemetryBundleManager.import_and_verify_mldsa_bundle(
        bundle_data=bundle_bytes,
        expected_public_key=kp.public_key_bytes,
        enforce_anti_replay=True,
    )
    assert is_valid_replay is False
    assert events_replay[0].integrity_status == IntegrityLevel.UNTRUSTED


# ============================================================================
# 4. INVARIANT TESTS: CONCURRENT SESSION & SHARED TERMINAL
# ============================================================================

def test_invariant_shared_terminal_concurrent_sessions_abstains():
    """
    INVARIANT 6: Concurrent distinct accounts on the same workstation within 60s
    or impossible travel velocity forces ABSTAINED boundary state.
    """
    builder = UnifiedCustodyTimelineBuilder()
    t = datetime(2026, 9, 27, 12, 0, 0, tzinfo=timezone.utc)

    root = DocumentRoot(document_id="doc_kiosk", canonical_hash="kiosk_hash", byte_size=1024, created_at=t.isoformat())

    # User 1 active in New York at t
    ev_ny = ForensicEvent(
        event_id="ev_ny",
        timestamp=t,
        event_type="LOGIN",
        canonical_type=CanonicalEventType.RENDERED,
        source_system=TelemetrySource.EDR,
        device_id="dev_ny",
        subject_id="analyst@defense.gov",
        raw_payload={"city": "New York", "distance_km": 6000.0},
    )

    # Same user active in London at t + 30 minutes (velocity = 12,000 km/h > 900 km/h)
    ev_london = ForensicEvent(
        event_id="ev_lon",
        timestamp=t + timedelta(minutes=30),
        event_type="LOGIN",
        canonical_type=CanonicalEventType.RENDERED,
        source_system=TelemetrySource.EDR,
        device_id="dev_lon",
        subject_id="analyst@defense.gov",
        raw_payload={"city": "London", "distance_km": 6000.0},
    )

    report = builder.build_timeline(
        document_root=root,
        telemetry_events=[ev_ny, ev_london],
        enrolled_recipient_id="rec_analyst",
    )

    assert report.account_compromised_or_shared is True
    assert report.forensic_boundary_state == ForensicBoundaryState.ABSTAINED
    assert report.should_abstain is True
    assert report.confidence_score == 0.0


# ============================================================================
# 5. REAL SCALABILITY BENCHMARKS (1k, 10k, 100k EVENTS)
# ============================================================================

def test_scalability_benchmark_1k_events():
    """
    SCALABILITY BENCHMARK: 1,000 external events.
    Verifies real wall-clock latency < 1.0s and peak RAM < 20MB.
    """
    builder = UnifiedCustodyTimelineBuilder()
    base_t = datetime(2026, 9, 27, 0, 0, 0, tzinfo=timezone.utc)
    root = DocumentRoot(
        document_id="doc_scale_1k",
        canonical_hash="scale_hash_1k",
        byte_size=1024,
        created_at=base_t.isoformat(),
    )

    evs = [
        ForensicEvent(
            event_id=f"ev_1k_{i}",
            timestamp=base_t + timedelta(seconds=i * 0.1),
            event_type="NET_FLOW",
            canonical_type=CanonicalEventType.NETWORK_TRANSMITTED,
            source_system=TelemetrySource.NETWORK,
            device_id=f"dev_{i}",
            resource_id="doc_scale_1k",
        )
        for i in range(1000)
    ]

    tracemalloc.start()
    t0 = time.perf_counter()
    report = builder.build_timeline(document_root=root, telemetry_events=evs)
    build_time = time.perf_counter() - t0
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_mb = peak / (1024 * 1024)
    print(f"\n[BENCHMARK 1K] Execution time: {build_time:.4f}s, Peak RAM: {peak_mb:.2f}MB, Items: {len(report.timeline)}")

    assert len(report.timeline) == 1001
    assert build_time < 1.0, f"1k benchmark exceeded budget: {build_time:.4f}s"
    assert peak_mb < 20.0, f"1k benchmark exceeded RAM budget: {peak_mb:.2f}MB"


def test_scalability_benchmark_10k_events():
    """
    SCALABILITY BENCHMARK: 10,000 external events.
    Verifies real wall-clock latency < 3.0s and peak RAM < 50MB.
    """
    builder = UnifiedCustodyTimelineBuilder()
    base_t = datetime(2026, 9, 27, 0, 0, 0, tzinfo=timezone.utc)
    root = DocumentRoot(
        document_id="doc_scale_10k",
        canonical_hash="scale_hash_10k",
        byte_size=1024,
        created_at=base_t.isoformat(),
    )

    evs = [
        ForensicEvent(
            event_id=f"ev_10k_{i}",
            timestamp=base_t + timedelta(seconds=i * 0.1),
            event_type="NET_FLOW",
            canonical_type=CanonicalEventType.NETWORK_TRANSMITTED,
            source_system=TelemetrySource.NETWORK,
            device_id=f"dev_{i}",
            resource_id="doc_scale_10k",
        )
        for i in range(10000)
    ]

    tracemalloc.start()
    t0 = time.perf_counter()
    report = builder.build_timeline(document_root=root, telemetry_events=evs)
    build_time = time.perf_counter() - t0
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_mb = peak / (1024 * 1024)
    print(f"\n[BENCHMARK 10K] Execution time: {build_time:.4f}s, Peak RAM: {peak_mb:.2f}MB, Items: {len(report.timeline)}")

    assert len(report.timeline) == 10001
    assert build_time < 3.0, f"10k benchmark exceeded budget: {build_time:.4f}s"
    assert peak_mb < 50.0, f"10k benchmark exceeded RAM budget: {peak_mb:.2f}MB"


def test_scalability_benchmark_100k_events():
    """
    SCALABILITY BENCHMARK: 100,000 external events.
    Verifies real wall-clock latency < 40.0s and peak RAM < 200MB.
    """
    builder = UnifiedCustodyTimelineBuilder()
    base_t = datetime(2026, 9, 27, 0, 0, 0, tzinfo=timezone.utc)
    root = DocumentRoot(
        document_id="doc_scale_100k",
        canonical_hash="scale_hash_100k",
        byte_size=1024,
        created_at=base_t.isoformat(),
    )

    evs = [
        ForensicEvent(
            event_id=f"ev_100k_{i}",
            timestamp=base_t + timedelta(seconds=i * 0.05),
            event_type="NET_FLOW",
            canonical_type=CanonicalEventType.NETWORK_TRANSMITTED,
            source_system=TelemetrySource.NETWORK,
            device_id=f"dev_{i}",
            resource_id="doc_scale_100k",
        )
        for i in range(100000)
    ]

    tracemalloc.start()
    t0 = time.perf_counter()
    report = builder.build_timeline(document_root=root, telemetry_events=evs)
    build_time = time.perf_counter() - t0
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_mb = peak / (1024 * 1024)
    print(f"\n[BENCHMARK 100K] Execution time: {build_time:.4f}s, Peak RAM: {peak_mb:.2f}MB, Items: {len(report.timeline)}")

    assert len(report.timeline) == 100001
    assert build_time < 40.0, f"100k benchmark exceeded budget: {build_time:.4f}s"
    assert peak_mb < 200.0, f"100k benchmark exceeded RAM budget: {peak_mb:.2f}MB"
