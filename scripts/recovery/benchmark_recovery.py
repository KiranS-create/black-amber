"""
AegisTrace Disaster Recovery & Performance Benchmarking Tool.

Executes empirical benchmarks across 1K, 10K, and 100K scales for:
- Backup creation & packaging
- ML-DSA-65 post-quantum manifest signing & verification
- Full state restoration
- Ledger hash-chain verification ops/sec
- Lineage index rebuild ops/sec
- Telemetry deduplication ops/sec
"""

import json
import os
import sys
import time

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from core.recovery.benchmark import RecoveryBenchmarkHarness, ScaleBenchmarkResult
from core.recovery.models import TargetClassification


def main():
    print("=" * 80)
    print("   AEGISTRACE DISASTER RECOVERY & FORENSIC STATE BENCHMARKS")
    print("=" * 80)
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    print("Running empirical benchmarks across 1K, 10K, and 100K scales...\n")

    results = RecoveryBenchmarkHarness.run_full_suite()

    print("-" * 80)
    print(f"{'Scale':<12} | {'Class':<12} | {'Sign (ms)':<10} | {'Verify (ms)':<11} | {'Ledger (ops/s)':<14} | {'Lineage (ops/s)':<15}")
    print("-" * 80)

    results_data = []
    for r in results:
        results_data.append(r.dict())
        print(f"{r.scale_label:<12} | {r.classification.value:<12} | {r.manifest_sign_time_ms:<10.3f} | {r.manifest_verify_time_ms:<11.3f} | {r.ledger_verify_ops_sec:<14.1f} | {r.lineage_rebuild_ops_sec:<15.1f}")
    print("-" * 80)

    # Save artifact
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "artifacts", "performance"))
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "recovery_benchmarks.json")

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results_data, f, indent=2)

    print(f"\n[+] Benchmark artifact saved to: {out_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
