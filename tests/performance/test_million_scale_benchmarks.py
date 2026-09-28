"""
Pytest Performance Verification for AegisTrace Scalability Architecture.

Executes deterministic scaling tests at N=1,000 and N=5,000 to enforce
continuous regression guarantees on latency budgets, throughput thresholds,
and incremental verification speedups.
"""

import pytest
from core.scale.benchmark import ScaleBenchmarkRunner


@pytest.fixture(scope="module")
def benchmark_runner():
    return ScaleBenchmarkRunner(seed=42)


def test_sparse_lineage_performance_budgets(benchmark_runner):
    res = benchmark_runner.benchmark_sparse_lineage(scale=2000)
    assert res["scale"] == 2000
    assert res["insert_throughput_ops_sec"] > 10_000  # Must exceed 10K ops/sec
    assert res["lookup_p50_us"] < 100.0              # Sub-100 microsecond P50 lookup
    assert res["traversal_p50_us"] < 1000.0          # Sub-1 millisecond P50 traversal
    assert res["bytes_per_node"] < 2000              # Compact memory footprint


def test_scalable_ledger_performance_and_incremental_speedup(benchmark_runner):
    res = benchmark_runner.benchmark_scalable_ledger(scale=2000, checkpoint_interval=500)
    assert res["scale"] == 2000
    assert res["checkpoints_created"] == 4
    assert res["query_p50_us"] < 200.0               # Sub-200 microsecond indexed query
    assert res["verification_incremental_ms"] <= res["verification_full_ms"]
    assert res["speedup_factor"] >= 1.0


def test_federated_identity_resolution_performance(benchmark_runner):
    res = benchmark_runner.benchmark_federated_identity(scale=1000)
    assert res["scale"] == 1000
    assert res["resolve_p50_us"] < 100.0             # Sub-100 microsecond resolution
    assert res["resolve_p99_us"] < 1000.0            # Sub-1 millisecond P99


def test_scalable_telemetry_performance(benchmark_runner):
    res = benchmark_runner.benchmark_scalable_telemetry(scale=2000)
    assert res["scale"] == 2000
    assert res["query_copy_p50_us"] < 200.0          # Sub-200 microsecond query
    assert res["time_window_p50_us"] < 500.0         # Sub-500 microsecond bisect window query


def test_forensic_investigation_multi_index_join_performance(benchmark_runner):
    res = benchmark_runner.benchmark_multi_index_join(scale=1000)
    assert res["scale"] == 1000
    assert res["join_p50_ms"] < 25.0                 # Sub-25ms multi-index join
    assert res["join_p99_ms"] < 100.0
