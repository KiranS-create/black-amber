"""
AegisTrace Benchmark Runner CLI.

Executes the comprehensive cryptographic performance suite, measures multi-core scaling,
and exports structured JSON and CSV artifacts to artifacts/performance/.
"""

import os
import sys
import time
import argparse

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.performance.benchmarks import (
    BenchmarkHarness,
    run_mlkem_benchmarks,
    run_mldsa_benchmarks,
    run_symmetric_benchmarks,
    run_e2e_critical_path_benchmarks,
    run_batch_benchmarks,
    run_multicore_scaling_benchmarks,
    export_all_benchmark_artifacts,
)


def main():
    parser = argparse.ArgumentParser(description="AegisTrace Cryptographic Benchmark Runner")
    parser.add_argument("--quick", action="store_true", help="Run with reduced iteration counts for rapid verification")
    parser.add_argument("--export-dir", default=os.path.join(REPO_ROOT, "artifacts", "performance"), help="Directory for exported artifacts")
    args = parser.parse_args()

    harness = BenchmarkHarness()
    hw = harness.get_hardware_profile()

    print("=" * 78)
    print("AEGISTRACE CRYPTOGRAPHIC PERFORMANCE & RESOURCE BENCHMARK HARNESS")
    print("=" * 78)
    print(f"Platform:      {hw['os']} {hw['os_release']} ({hw['architecture']})")
    print(f"Processor:     {hw['processor']}")
    print(f"Cores:         {hw['physical_cores']} physical / {hw['logical_cores']} logical")
    print(f"RAM:           {hw['total_ram_gb']} GB")
    print(f"Python:        {hw['python_version']} ({hw['python_compiler']})")
    print(f"KEM Provider:  {hw['crypto_providers']['ml_kem_768']['provider']} ({hw['crypto_providers']['ml_kem_768']['standard']})")
    print(f"DSA Provider:  {hw['crypto_providers']['ml_dsa_65']['provider']} ({hw['crypto_providers']['ml_dsa_65']['standard']})")
    print(f"Symmetric:     {hw['crypto_providers']['symmetric']}")
    print(f"Air-Gapped:    {hw['air_gapped_offline']}")
    print("=" * 78 + "\n")

    iterations_kem = 10 if args.quick else 30
    iterations_dsa = 8 if args.quick else 25
    iterations_sym = 15 if args.quick else 50
    iterations_e2e = 5 if args.quick else 15
    batch_sizes = [1, 5, 10] if args.quick else [1, 10, 50, 100]
    worker_counts = [1, 2, 4] if args.quick else [1, 2, 4, 8]
    total_multicore_ops = 16 if args.quick else 40

    all_results = []

    # 1. ML-KEM-768
    print("[1/5] Benchmarking Post-Quantum ML-KEM-768 (FIPS 203)...")
    kem_results = run_mlkem_benchmarks(harness, iterations=iterations_kem)
    all_results.extend(kem_results)
    for r in kem_results:
        print(f"  -> {r.name:36s} | Median: {r.median_ms:7.3f} ms | Mean: {r.mean_ms:7.3f} ms | P95: {r.p95_ms:7.3f} ms | Ops/s: {r.throughput_ops_sec:6.1f}")

    # 2. ML-DSA-65
    print("\n[2/5] Benchmarking Post-Quantum ML-DSA-65 (FIPS 204)...")
    dsa_results = run_mldsa_benchmarks(harness, iterations=iterations_dsa)
    all_results.extend(dsa_results)
    for r in dsa_results:
        print(f"  -> {r.name:36s} | Median: {r.median_ms:7.3f} ms | Mean: {r.mean_ms:7.3f} ms | P95: {r.p95_ms:7.3f} ms | Ops/s: {r.throughput_ops_sec:6.1f}")

    # 3. Symmetric & KDF
    print("\n[3/5] Benchmarking Symmetric Primitives, KDF & Key Wrap...")
    sym_results = run_symmetric_benchmarks(harness, iterations=iterations_sym)
    all_results.extend(sym_results)
    for r in sym_results:
        mb_str = f"{r.throughput_mb_sec:7.1f} MB/s" if r.throughput_mb_sec is not None else "        N/A"
        print(f"  -> {r.name:44s} | Mean: {r.mean_ms:7.3f} ms | {mb_str} | PeakMem: {r.peak_memory_kb:6.1f} KB")

    # 4. End-to-End Critical Path
    print("\n[4/5] Benchmarking AegisTrace Critical-Path Lifecycle...")
    e2e_results, stage_breakdown = run_e2e_critical_path_benchmarks(harness, iterations=iterations_e2e)
    all_results.extend(e2e_results)
    for r in e2e_results:
        print(f"  -> {r.name:60s} | Mean: {r.mean_ms:7.3f} ms | P95: {r.p95_ms:7.3f} ms")

    print("\n  Critical Path Dominance Breakdown:")
    for stage, pct in stage_breakdown["stage_percentages"].items():
        print(f"     * {stage.replace('_', ' ').title():28s}: {pct:5.1f}%")

    # 5. Batch & Multicore Scaling
    print("\n[5/5] Measuring Batch Recipient & Multi-Core Worker Scaling...")
    batch_results = run_batch_benchmarks(harness, batch_sizes=batch_sizes)
    print("\n  Batch Recipient Packaging Scaling:")
    for b in batch_results:
        print(f"     * {b['recipient_count']:3d} Recipients: Total {b['total_mean_ms']:8.2f} ms | {b['avg_per_recipient_ms']:6.3f} ms/rec | {b['recipients_per_sec']:6.1f} rec/s")

    print("\n  Multi-Core Worker Scaling (ProcessPool):")
    scaling_results = run_multicore_scaling_benchmarks(worker_counts=worker_counts, total_ops=total_multicore_ops)
    for s in scaling_results:
        print(f"     * {s['worker_count']:2d} Workers: {s['total_ops']:2d} ops in {s['elapsed_seconds']:6.2f}s | {s['ops_per_second']:5.2f} ops/s | Speedup: {s['speedup']:4.2f}x (Efficiency: {s['scaling_efficiency_pct']:5.1f}%)")

    # Export Artifacts
    json_p, csv_p, scale_p = export_all_benchmark_artifacts(
        hardware_profile=hw,
        all_results=all_results,
        stage_breakdown=stage_breakdown,
        batch_results=batch_results,
        scaling_results=scaling_results,
        output_dir=args.export_dir
    )

    print("\n" + "=" * 78)
    print("BENCHMARK ARTIFACTS EXPORTED SUCCESSFULLY:")
    print(f"  -> JSON:    {json_p}")
    print(f"  -> CSV:     {csv_p}")
    print(f"  -> Scaling: {scale_p}")
    print("=" * 78)


if __name__ == "__main__":
    main()
