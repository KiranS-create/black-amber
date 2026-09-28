"""
AegisTrace Telemetry Scale & Performance Benchmark Harness.

Measures event ingestion throughput, multi-index lookup latency, graph
construction performance, and correlation runtime across dataset sizes:
1,000, 10,000, 100,000, and 1,000,000 events.
"""

from datetime import datetime, timezone, timedelta
import hashlib
import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from core.telemetry.event import ForensicEvent
from core.telemetry.models import TelemetrySource, IntegrityLevel
from core.telemetry.provider import InMemoryTelemetryProvider
from core.telemetry.engine import TelemetryCorrelationEngine


class BenchmarkResult(BaseModel):
    scale_events: int
    ingestion_time_seconds: float
    ingestion_rate_events_per_sec: float
    hash_query_latency_ms: float
    actor_query_latency_ms: float
    correlation_latency_ms: float
    memory_mb_approx: float


def generate_synthetic_events(count: int, target_hash: str, target_recipient: str) -> List[ForensicEvent]:
    """Generate synthetic deterministic forensic events for scale benchmarking."""
    events = []
    base_time = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
    sources = list(TelemetrySource)

    for i in range(count):
        source = sources[i % len(sources)]
        ts = base_time + timedelta(seconds=i * 2)

        # 5% of events match the target hash / recipient
        is_target = (i % 20 == 0)
        artifact_hash = target_hash if is_target else f"hash-{hashlib.sha256(str(i).encode()).hexdigest()[:16]}"
        actor = target_recipient if is_target else f"user_{i % 500}@corp.local"
        device = f"WS-CORP-{(i % 200):03d}"
        net = f"10.0.{(i // 256) % 256}.{i % 256}"

        ev = ForensicEvent(
            event_id=f"bench-ev-{i:07d}",
            timestamp=ts,
            event_type="FILE_ACCESS" if i % 2 == 0 else "NETWORK_EGRESS",
            source_system=source,
            subject_type="ACCOUNT",
            subject_id=actor,
            device_id=device,
            network_id=net,
            resource_id=f"/shared/docs/spec_{i % 100}.pdf",
            artifact_hash=artifact_hash,
            copy_id=f"copy-{target_recipient}" if is_target else None,
            session_id=f"sess-{(i % 1000):04d}",
            integrity_status=IntegrityLevel.HIGH_SYSTEM if i % 10 != 0 else IntegrityLevel.MEDIUM_LOG,
            source_reliability=0.9,
            raw_payload={"bench_idx": i},
        )
        events.append(ev)

    return events


def run_single_scale_benchmark(scale: int) -> BenchmarkResult:
    """Run benchmark for a specific scale count."""
    target_hash = "a" * 64
    target_rec = "recipient_alice"

    # 1. Generation
    events = generate_synthetic_events(scale, target_hash, target_rec)

    # 2. Ingestion
    provider = InMemoryTelemetryProvider()
    t0 = time.perf_counter()
    provider.ingest_batch(events)
    t_ingest = time.perf_counter() - t0
    rate = scale / max(t_ingest, 1e-6)

    # 3. Hash Query Latency
    t0 = time.perf_counter()
    res_hash = provider.query_by_artifact_hash(target_hash)
    t_hash_ms = (time.perf_counter() - t0) * 1000.0

    # 4. Actor Query Latency
    t0 = time.perf_counter()
    res_actor = provider.query_by_actor(target_rec)
    t_actor_ms = (time.perf_counter() - t0) * 1000.0

    # 5. Correlation Engine Latency
    engine = TelemetryCorrelationEngine(provider)
    t0 = time.perf_counter()
    rep = engine.correlate(
        artifact_hash=target_hash,
        copy_id=f"copy-{target_rec}",
        enrolled_recipient_id=target_rec,
        release_timestamp=datetime(2026, 3, 1, 9, 59, 0, tzinfo=timezone.utc),
        leak_timestamp=datetime(2026, 3, 1, 14, 0, 0, tzinfo=timezone.utc),
    )
    t_corr_ms = (time.perf_counter() - t0) * 1000.0

    # Rough memory approximation (500 bytes per event in index)
    mem_mb = (scale * 550) / (1024 * 1024)

    return BenchmarkResult(
        scale_events=scale,
        ingestion_time_seconds=round(t_ingest, 4),
        ingestion_rate_events_per_sec=round(rate, 1),
        hash_query_latency_ms=round(t_hash_ms, 3),
        actor_query_latency_ms=round(t_actor_ms, 3),
        correlation_latency_ms=round(t_corr_ms, 3),
        memory_mb_approx=round(mem_mb, 2),
    )


def run_scale_benchmarks(scales: Optional[List[int]] = None) -> List[BenchmarkResult]:
    """Execute scale benchmark across all configured scales."""
    target_scales = scales or [1000, 10000, 100000]
    results = []
    for sc in target_scales:
        res = run_single_scale_benchmark(sc)
        results.append(res)
    return results
