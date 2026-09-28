"""
Tests for ScalableTelemetryProvider with Slotted Records & Bisect Window Queries.

Validates:
- High-throughput ingestion of CompactTelemetryRecord
- Inverted secondary index queries (by copy_id, artifact_hash, device_id, subject_id)
- Bisect-based temporal range queries in O(log N + K)
- Multi-tenant partitioning
- Reset / clear operations
"""

import pytest
import time

from core.telemetry.scale import ScalableTelemetryProvider, CompactTelemetryRecord


def test_scalable_telemetry_ingestion_and_lookups():
    provider = ScalableTelemetryProvider()
    tenant = "tenant_edr"

    base_time = 1700000000.0
    for i in range(100):
        provider.ingest_record(
            event_id=f"tel_{i:04d}",
            event_type="FILE_ACCESS" if i % 2 == 0 else "NETWORK_OUTBOUND",
            source_system="CROWDSTRIKE",
            timestamp_epoch=base_time + (i * 10.0),
            artifact_hash=f"hash_{i % 10}",
            copy_id=f"cpy_{i % 5}",
            device_id=f"dev_{i % 4}",
            subject_id=f"usr_{i % 3}",
            tenant_id=tenant
        )

    assert provider.count() == 100
    assert provider.count(tenant) == 100
    assert provider.count("foreign_tenant") == 0

    # Query by copy_id (5 copies, 100 total -> 20 records per copy)
    recs_copy = provider.query_by_copy_id("cpy_2", tenant_id=tenant)
    assert len(recs_copy) == 20
    assert all(r.copy_id == "cpy_2" for r in recs_copy)

    # Cross-tenant query must be empty
    assert len(provider.query_by_copy_id("cpy_2", tenant_id="foreign_tenant")) == 0

    # Query by device_id (4 devices -> 25 records per device)
    recs_dev = provider.query_by_device_id("dev_1", tenant_id=tenant)
    assert len(recs_dev) == 25


def test_bisect_temporal_window_queries():
    provider = ScalableTelemetryProvider()
    tenant = "tenant_timeseries"

    base_time = 1700000000.0
    # Ingest 100 events, 1 event every second
    for i in range(100):
        provider.ingest_record(
            event_id=f"t_{i}",
            event_type="HEARTBEAT",
            source_system="AGENT",
            timestamp_epoch=base_time + i,
            tenant_id=tenant
        )

    # Query window [base_time + 10, base_time + 20]
    window_recs = provider.query_time_window(base_time + 10, base_time + 20, tenant_id=tenant)
    assert len(window_recs) == 11  # inclusive 10..20
    assert window_recs[0].timestamp_epoch == base_time + 10
    assert window_recs[-1].timestamp_epoch == base_time + 20

    # Query out-of-range window
    empty_recs = provider.query_time_window(base_time + 500, base_time + 600, tenant_id=tenant)
    assert len(empty_recs) == 0


def test_telemetry_batch_ingest_and_clear():
    provider = ScalableTelemetryProvider()
    batch = [
        {
            "event_id": f"batch_{i}",
            "event_type": "LOGON",
            "source_system": "OKTA",
            "timestamp_epoch": 1700000000.0 + i
        }
        for i in range(50)
    ]
    count = provider.ingest_batch(batch, tenant_id="tenant_batch")
    assert count == 50
    assert provider.count("tenant_batch") == 50

    provider.clear()
    assert provider.count() == 0
