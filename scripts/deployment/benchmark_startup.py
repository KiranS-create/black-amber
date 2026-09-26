import json
import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.deployment.reset_demo import reset_demo_environment
from scripts.deployment.health_check import run_health_check
from scripts.deployment.generate_demo_fixtures import generate_fixtures

def run_startup_benchmark():
    print("=" * 60)
    print("SIH26237 DEPLOYMENT & STARTUP BENCHMARK")
    print("=" * 60)

    benchmarks = {}

    # 1. Measure Demo Reset Time
    t0 = time.perf_counter()
    reset_demo_environment()
    t_reset = (time.perf_counter() - t0) * 1000.0
    benchmarks["demo_reset_ms"] = round(t_reset, 2)
    print(f"[+] Demo Reset Latency:                   {t_reset:7.2f} ms")

    # 2. Measure Fixture Generation Time
    t0 = time.perf_counter()
    generate_fixtures()
    t_fix = (time.perf_counter() - t0) * 1000.0
    benchmarks["fixture_generation_ms"] = round(t_fix, 2)
    print(f"[+] Fixture Generation Latency:           {t_fix:7.2f} ms")

    # 3. Measure Health Check Time
    t0 = time.perf_counter()
    run_health_check()
    t_health = (time.perf_counter() - t0) * 1000.0
    benchmarks["health_check_execution_ms"] = round(t_health, 2)
    print(f"[+] Health Check Execution Latency:       {t_health:7.2f} ms")

    # 4. Measure Vite Production Build Time
    web_dir = PROJECT_ROOT / "apps" / "web"
    t0 = time.perf_counter()
    fe_build = subprocess.run(["npx", "vite", "build"], cwd=str(web_dir), capture_output=True, text=True, check=False, shell=True)
    t_vite = (time.perf_counter() - t0) * 1000.0
    benchmarks["vite_production_build_ms"] = round(t_vite, 2)
    print(f"[+] Frontend Production Build (Vite):     {t_vite:7.2f} ms")

    # Save to artifacts/deployment
    out_dir = PROJECT_ROOT / "artifacts" / "deployment"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "startup_benchmark.json"
    with open(out_file, "w") as f:
        json.dump(benchmarks, f, indent=2)

    print(f"\n[+] Startup benchmark results saved to: {out_file}")
    print("=" * 60)
    return benchmarks

if __name__ == "__main__":
    run_startup_benchmark()
