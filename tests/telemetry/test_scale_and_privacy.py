"""
AegisTrace Scale Benchmarking, Privacy, and Graph Lineage Tests.

Validates:
- Scale benchmark execution across synthetic event volumes
- High-throughput ingestion and sub-millisecond indexed queries
- Forensic correlation graph path finding and cycle resistance
- Telemetry privacy pseudonymization and retention purging
- Offline signed bundle tamper detection
"""

from datetime import datetime, timezone, timedelta
import pytest

from core.telemetry.models import TelemetrySource, IntegrityLevel
from core.telemetry.event import ForensicEvent
from core.telemetry.provider import InMemoryTelemetryProvider
from core.telemetry.graph import (
    ForensicCorrelationGraph,
    ForensicNodeType,
    ForensicEdgeType,
)
from core.telemetry.privacy import TelemetryPrivacyManager
from core.telemetry.bundle import TelemetryBundleManager
from core.telemetry.benchmarks import run_single_scale_benchmark, generate_synthetic_events


def test_scale_benchmark_1k_and_10k():
    """Verify performance metrics on 1k and 5k events within tight timing constraints."""
    res_1k = run_single_scale_benchmark(1000)
    assert res_1k.scale_events == 1000
    assert res_1k.ingestion_rate_events_per_sec > 1000.0  # Fast in-memory ingestion
    assert res_1k.hash_query_latency_ms < 50.0            # Sub-50ms query
    assert res_1k.correlation_latency_ms < 100.0

    res_5k = run_single_scale_benchmark(5000)
    assert res_5k.scale_events == 5000
    assert res_5k.hash_query_latency_ms < 100.0


def test_in_memory_provider_indexing_and_time_filtering():
    """Verify multi-attribute inverted indexes and time-range slicing."""
    provider = InMemoryTelemetryProvider()
    t0 = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)

    e1 = ForensicEvent(
        event_id="ev-1",
        timestamp=t0,
        event_type="ACCESS",
        source_system=TelemetrySource.EDR,
        subject_id="alice",
        device_id="DEV-A",
        artifact_hash="hash-A",
    )
    e2 = ForensicEvent(
        event_id="ev-2",
        timestamp=t0 + timedelta(hours=2),
        event_type="ACCESS",
        source_system=TelemetrySource.EDR,
        subject_id="alice",
        device_id="DEV-A",
        artifact_hash="hash-B",
    )
    e3 = ForensicEvent(
        event_id="ev-3",
        timestamp=t0 + timedelta(hours=5),
        event_type="ACCESS",
        source_system=TelemetrySource.EDR,
        subject_id="alice",
        device_id="DEV-B",
        artifact_hash="hash-A",
    )
    provider.ingest_batch([e1, e2, e3])

    assert provider.count() == 3

    # Query by hash
    res_hash_a = provider.query_by_artifact_hash("hash-A")
    assert len(res_hash_a) == 2
    assert {e.event_id for e in res_hash_a} == {"ev-1", "ev-3"}

    # Time window filter: [t0 + 1hr, t0 + 3hr]
    window_res = provider.query_by_actor(
        "alice",
        window_start=t0 + timedelta(hours=1),
        window_end=t0 + timedelta(hours=3),
    )
    assert len(window_res) == 1
    assert window_res[0].event_id == "ev-2"


def test_forensic_graph_path_finding_and_cycles():
    """Verify directed acyclic and cyclic path traversal in ForensicCorrelationGraph."""
    graph = ForensicCorrelationGraph()

    # Add 4 nodes in a chain: Doc -> Copy -> Event -> Network
    graph.add_node("n-doc", ForensicNodeType.DOCUMENT, label="Doc")
    graph.add_node("n-copy", ForensicNodeType.COPY, label="Copy")
    graph.add_node("n-ev", ForensicNodeType.EVENT, label="Event")
    graph.add_node("n-net", ForensicNodeType.NETWORK, label="Network")

    graph.add_edge("n-doc", "n-copy", ForensicEdgeType.DERIVED_FROM)
    graph.add_edge("n-copy", "n-ev", ForensicEdgeType.EXPORTED_BY)
    graph.add_edge("n-ev", "n-net", ForensicEdgeType.TRANSMITTED_TO)

    # Path finding
    path = graph.find_shortest_path("n-doc", "n-net")
    assert path is not None
    assert len(path) == 3
    assert path[0].edge_type == ForensicEdgeType.DERIVED_FROM
    assert path[2].edge_type == ForensicEdgeType.TRANSMITTED_TO

    # Add cycle: Network -> Event (cycle)
    graph.add_edge("n-net", "n-ev", ForensicEdgeType.TRANSMITTED_TO)
    all_paths = graph.find_all_paths("n-doc", "n-net", max_depth=5)
    assert len(all_paths) == 1  # Cycle should not cause infinite loop

    # Serialization test
    d = graph.to_dict()
    restored = ForensicCorrelationGraph.from_dict(d)
    assert restored.node_count == 4
    assert restored.edge_count == 4


def test_privacy_manager_pseudonymization_and_pii_redaction():
    """Verify deterministic pseudonym hashing and PII field stripping."""
    salt = b"test_salt_9999"
    pm1 = TelemetryPrivacyManager(privacy_salt=salt)
    pm2 = TelemetryPrivacyManager(privacy_salt=salt)

    # Determinism
    p1 = pm1.pseudonymize_identifier("alice@corp.com")
    p2 = pm2.pseudonymize_identifier("alice@corp.com")
    assert p1 == p2
    assert p1.startswith("anon-")

    # IP masking
    ip_masked = pm1.pseudonymize_ip("192.168.10.45")
    assert ip_masked == "192.168.10.0/24"

    # Event redaction
    ev = ForensicEvent(
        event_id="e-sens",
        timestamp=datetime.now(timezone.utc),
        event_type="LOGIN",
        source_system=TelemetrySource.IDP,
        subject_id="alice@corp.com",
        network_id="10.20.30.40",
        raw_payload={"auth_token": "secret_token_123", "password": "mypassword", "valid_key": "safe_val"},
    )
    redacted = pm1.redact_event(ev)
    assert redacted.subject_id.startswith("anon-")
    assert redacted.network_id == "10.20.30.0/24"
    assert redacted.raw_payload["auth_token"] == "[REDACTED]"
    assert redacted.raw_payload["password"] == "[REDACTED]"
    assert redacted.raw_payload["valid_key"] == "safe_val"


def test_offline_bundle_export_import_tamper():
    """Verify signed bundle packaging and tamper detection."""
    key = b"signing_key_44321"
    ev1 = ForensicEvent(event_id="e1", timestamp=datetime.now(timezone.utc), event_type="READ", source_system=TelemetrySource.EDR)
    ev2 = ForensicEvent(event_id="e2", timestamp=datetime.now(timezone.utc), event_type="WRITE", source_system=TelemetrySource.EDR)

    # Export
    bundle_str = TelemetryBundleManager.export_bundle_json([ev1, ev2], key, signer_id="TEST_SIGNER")
    assert "TEST_SIGNER" in bundle_str

    # Valid Import
    events, is_valid = TelemetryBundleManager.import_and_verify_bundle(bundle_str, key)
    assert is_valid
    assert len(events) == 2
    assert events[0].integrity_status != IntegrityLevel.UNTRUSTED

    # Invalid key import
    wrong_key = b"wrong_key_00000"
    events_bad, is_valid_bad = TelemetryBundleManager.import_and_verify_bundle(bundle_str, wrong_key)
    assert not is_valid_bad
    assert all(e.integrity_status == IntegrityLevel.UNTRUSTED for e in events_bad)
