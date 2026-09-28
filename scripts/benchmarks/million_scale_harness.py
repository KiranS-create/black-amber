#!/usr/bin/env python3
"""
AegisTrace Million-Scale Forensic Benchmark Execution Harness.

Executes real, unsimulated performance and memory benchmarks for:
- Sparse Lineage Indexing (up to 1,000,000 nodes)
- Scalable Ledger Indexing & Checkpointing (up to 1,000,000 events)
- Federated Identity Cache Routing (up to 100,000 identities)
- Scalable Telemetry Store (up to 1,000,000 records)
- Forensic Investigation Multi-Index Joins (up to 100,000 joined entities)
- Cross-Tenant Isolation under scale differential (100K vs 1K)

Outputs structured, un-faked results to:
`artifacts/performance/scale_benchmark_results.json`
"""

import os
import sys
import json
import time
from datetime import datetime, timezone
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.scale.benchmark import ScaleBenchmarkRunner


def main():
    print("=" * 70)
    print("AEGISTRACE MILLION-SCALE FORENSIC ARCHITECTURE BENCHMARK HARNESS")
    print("=" * 70)
    print("Environment: Windows Air-Gapped Local System")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("Initializing benchmark runner with deterministic seed...")

    runner = ScaleBenchmarkRunner(seed=1337)
    results = {
        "benchmark_metadata": {
            "title": "AegisTrace Million-Scale Forensic Lineage & Federated Identity Benchmark",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "python_version": sys.version,
            "platform": sys.platform,
            "air_gapped": True,
            "target_scales": [1_000, 10_000, 100_000, 1_000_000]
        },
        "sparse_lineage": {},
        "scalable_ledger": {},
        "federated_identity": {},
        "scalable_telemetry": {},
        "investigation_multi_index_join": {},
        "tenant_isolation": {}
    }

    # 1. Sparse Lineage Indexing across 1K, 10K, 100K, 1M
    lineage_scales = [1_000, 10_000, 100_000, 1_000_000]
    print("\n--- 1. BENCHMARKING SPARSE LINEAGE INDEX ---")
    for s in lineage_scales:
        print(f"Running SparseLineageIndex at scale N={s:,}...")
        res = runner.benchmark_sparse_lineage(scale=s)
        results["sparse_lineage"][str(s)] = res
        print(f"  -> Insert: {res['insert_throughput_ops_sec']:,.0f} ops/sec | "
              f"RAM: +{res['memory_delta_mb']:.1f} MB ({res['bytes_per_node']:.0f} B/node) | "
              f"Lookup P50: {res['lookup_p50_us']:.2f} µs | "
              f"Traversal ({res['traversal_avg_hops']:.0f} hops) P50: {res['traversal_p50_us']:.2f} µs")

    # 2. Scalable Ledger Indexing across 1K, 10K, 100K, 1M
    ledger_scales = [1_000, 10_000, 100_000, 1_000_000]
    print("\n--- 2. BENCHMARKING SCALABLE TAMPER-EVIDENT LEDGER ---")
    for s in ledger_scales:
        print(f"Running ScalableLedger at scale N={s:,}...")
        res = runner.benchmark_scalable_ledger(scale=s, checkpoint_interval=5000)
        results["scalable_ledger"][str(s)] = res
        print(f"  -> Append: {res['append_throughput_ops_sec']:,.0f} ops/sec | "
              f"RAM: +{res['memory_delta_mb']:.1f} MB | "
              f"Query P50: {res['query_p50_us']:.2f} µs | "
              f"Incremental Verify: {res['verification_incremental_ms']:.2f} ms "
              f"(vs Full: {res['verification_full_ms']:.2f} ms, {res['speedup_factor']:.1f}x speedup)")

    # 3. Federated Identity Directory across 1K, 10K, 100K
    identity_scales = [1_000, 10_000, 100_000]
    print("\n--- 3. BENCHMARKING FEDERATED IDENTITY DIRECTORY ---")
    for s in identity_scales:
        print(f"Running FederatedIdentityDirectory at scale N={s:,}...")
        res = runner.benchmark_federated_identity(scale=s)
        results["federated_identity"][str(s)] = res
        print(f"  -> Ingest: {res['insert_throughput_ops_sec']:,.0f} ops/sec | "
              f"RAM: +{res['memory_delta_mb']:.1f} MB ({res['bytes_per_identity']:.0f} B/id) | "
              f"Resolve P50: {res['resolve_p50_us']:.2f} µs | "
              f"P99: {res['resolve_p99_us']:.2f} µs")

    # 4. Scalable Telemetry Provider across 1K, 10K, 100K, 1M
    telemetry_scales = [1_000, 10_000, 100_000, 1_000_000]
    print("\n--- 4. BENCHMARKING SCALABLE TELEMETRY STORE ---")
    for s in telemetry_scales:
        print(f"Running ScalableTelemetryProvider at scale N={s:,}...")
        res = runner.benchmark_scalable_telemetry(scale=s)
        results["scalable_telemetry"][str(s)] = res
        print(f"  -> Ingest: {res['insert_throughput_ops_sec']:,.0f} ops/sec | "
              f"RAM: +{res['memory_delta_mb']:.1f} MB ({res['bytes_per_record']:.0f} B/rec) | "
              f"Copy Query P50: {res['query_copy_p50_us']:.2f} µs | "
              f"Bisect Time Window P50: {res['time_window_p50_us']:.2f} µs")

    # 5. Multi-Index Join Query across 1K, 10K, 100K
    join_scales = [1_000, 10_000, 100_000]
    print("\n--- 5. BENCHMARKING FORENSIC INVESTIGATION MULTI-INDEX JOIN ---")
    for s in join_scales:
        print(f"Running ForensicInvestigationEngine at scale N={s:,}...")
        res = runner.benchmark_multi_index_join(scale=s)
        results["investigation_multi_index_join"][str(s)] = res
        print(f"  -> Join P50: {res['join_p50_ms']:.3f} ms | "
              f"P95: {res['join_p95_ms']:.3f} ms | "
              f"P99: {res['join_p99_ms']:.3f} ms")

    # 6. Strict Tenant Isolation
    print("\n--- 6. BENCHMARKING CROSS-TENANT ISOLATION UNDER SCALE ---")
    res_iso = runner.benchmark_tenant_isolation(scale_a=100_000, scale_b=1_000)
    results["tenant_isolation"] = res_iso
    print(f"  -> Tenant A: {res_iso['scale_tenant_a']:,} nodes | "
          f"Tenant B: {res_iso['scale_tenant_b']:,} nodes | "
          f"Cross-Tenant Leaks: {res_iso['cross_tenant_lineage_leaks']} lineage, {res_iso['cross_tenant_ledger_leaks']} ledger | "
          f"Preserved: {res_iso['isolation_preserved']}")

    # Save to artifacts/performance/scale_benchmark_results.json
    out_dir = Path("artifacts/performance")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "scale_benchmark_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 70)
    print(f"BENCHMARK COMPLETE. Results written to: {out_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
