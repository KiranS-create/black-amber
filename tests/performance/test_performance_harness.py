"""
Performance & Benchmark Regression Suite for AegisTrace.

Verifies:
1. Structural integrity and correctness of the benchmark harness.
2. Statistical calculations (min, median, mean, p95, p99, stddev, cold start).
3. Authentic cryptographic execution during benchmarking (no mocks/shortcuts).
4. Full end-to-end critical-path stage breakdown validity.
5. Export artifact generation (JSON & CSV serialization).
"""

import os
import json
import csv
import pytest
from research.performance.benchmarks import (
    BenchmarkHarness,
    BenchmarkResult,
    run_mlkem_benchmarks,
    run_mldsa_benchmarks,
    run_symmetric_benchmarks,
    run_e2e_critical_path_benchmarks,
    run_batch_benchmarks,
    export_all_benchmark_artifacts,
)


def test_benchmark_harness_statistics():
    """Verify statistical calculations on synthetic and deterministic samples."""
    durations = [10.0, 20.0, 30.0, 40.0, 50.0]
    cpu_times = [9.0, 19.0, 29.0, 39.0, 49.0]
    res = BenchmarkResult(
        name="Test Op",
        category="Test",
        sample_count=5,
        warmup_count=1,
        cold_start_ms=100.0,
        durations_ms=durations,
        cpu_times_ms=cpu_times,
        memory_delta_kb=10.0,
        peak_memory_kb=50.0,
        throughput_ops_sec=20.0,
    )

    assert res.min_ms == 10.0
    assert res.max_ms == 50.0
    assert res.median_ms == 30.0
    assert res.mean_ms == 30.0
    assert res.p95_ms == 50.0
    assert res.p99_ms == 50.0
    assert round(res.stddev_ms, 2) == 15.81
    assert res.cold_start_ms == 100.0

    d = res.to_dict()
    assert d["name"] == "Test Op"
    assert d["median_ms"] == 30.0


def test_pqc_primitives_benchmark_execution():
    """Verify ML-KEM-768 and ML-DSA-65 benchmark runners execute authentic crypto."""
    harness = BenchmarkHarness()

    # KEM benchmarks
    kem_results = run_mlkem_benchmarks(harness, iterations=3)
    assert len(kem_results) == 3
    for r in kem_results:
        assert r.sample_count == 3
        assert r.mean_ms > 0.0
        assert r.throughput_ops_sec > 0.0
        assert r.category == "Post-Quantum KEM"

    # DSA benchmarks
    dsa_results = run_mldsa_benchmarks(harness, iterations=2)
    assert len(dsa_results) == 3
    for r in dsa_results:
        assert r.sample_count == 2
        assert r.mean_ms > 0.0
        assert r.throughput_ops_sec > 0.0
        assert r.category == "Post-Quantum DSA"


def test_symmetric_and_kdf_benchmark_execution():
    """Verify symmetric and key derivation benchmark runners execute correctly."""
    harness = BenchmarkHarness()
    sym_results = run_symmetric_benchmarks(harness, iterations=5)

    assert len(sym_results) >= 8
    for r in sym_results:
        assert r.mean_ms > 0.0
        assert r.peak_memory_kb >= 0.0


def test_critical_path_lifecycle_execution():
    """Verify full end-to-end critical path benchmark and dominance breakdown."""
    harness = BenchmarkHarness()
    e2e_results, stage_breakdown = run_e2e_critical_path_benchmarks(harness, iterations=2)

    assert len(e2e_results) == 5
    assert "stage_percentages" in stage_breakdown
    assert stage_breakdown["total_critical_path_mean_ms"] > 0.0

    total_pct = sum(stage_breakdown["stage_percentages"].values())
    assert 99.0 <= total_pct <= 101.0  # Percentage adds up to ~100%


def test_batch_scaling_benchmark():
    """Verify batch recipient benchmark computes valid scaling metrics."""
    harness = BenchmarkHarness()
    batch_res = run_batch_benchmarks(harness, batch_sizes=[1, 3])

    assert len(batch_res) == 2
    for b in batch_res:
        assert b["recipient_count"] in [1, 3]
        assert b["total_mean_ms"] > 0.0
        assert b["avg_per_recipient_ms"] > 0.0
        assert b["recipients_per_sec"] > 0.0


def test_artifact_export_integrity(tmp_path):
    """Verify that export_all_benchmark_artifacts outputs valid, parseable JSON and CSV."""
    harness = BenchmarkHarness()
    hw = harness.get_hardware_profile()
    kem_results = run_mlkem_benchmarks(harness, iterations=2)
    _, stage_breakdown = run_e2e_critical_path_benchmarks(harness, iterations=2)
    batch_res = run_batch_benchmarks(harness, batch_sizes=[1])

    json_p, csv_p, scale_p = export_all_benchmark_artifacts(
        hardware_profile=hw,
        all_results=kem_results,
        stage_breakdown=stage_breakdown,
        batch_results=batch_res,
        scaling_results=[],
        output_dir=str(tmp_path)
    )

    assert os.path.exists(json_p)
    assert os.path.exists(csv_p)
    assert os.path.exists(scale_p)

    # Validate JSON
    with open(json_p, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["hardware_profile"]["os"] == hw["os"]
        assert len(data["operations"]) == 3

    # Validate CSV
    with open(csv_p, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)
        assert len(rows) == 4  # Header + 3 operations
        assert rows[0][0] == "Category"
