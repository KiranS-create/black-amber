#!/usr/bin/env python3
"""
AegisTrace API Security & Zero-Trust Operational Performance Benchmark.

Executes real, unsimulated performance measurements for:
- Authentication & Zero-Trust Authorization evaluation overhead
- Input validation, ID regex, and polyglot payload sanitization throughput
- Sliding-window rate limiter throughput under high concurrency
- Anti-replay nonce cache verification throughput
- End-to-end API response latency under security middleware and headers

Outputs structured results to:
`artifacts/performance/api_security_benchmark_results.json`
"""

import concurrent.futures
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from fastapi.testclient import TestClient
from apps.api.config import config
from apps.api.main import app
from apps.api.security import (
    SecurityPrincipal,
    SlidingWindowRateLimiter,
    ReplayProtectionCache,
    default_rate_limiter,
    has_role_permission,
    verify_tenant_boundary,
    validate_id_format,
    validate_hash_hex,
    validate_uploaded_payload,
    sanitize_header_value,
)

def benchmark_auth_and_authz(iterations: int = 10_000) -> Dict[str, Any]:
    """Measure raw server-side token resolution and role hierarchy evaluation overhead."""
    # 1. Token lookup overhead
    token = "token_investigator_tenant_a"
    start = time.perf_counter()
    for _ in range(iterations):
        entry = config.local_auth_tokens.get(token)
        principal = SecurityPrincipal(
            actor_id=entry["actor_id"],
            tenant_id=entry["tenant_id"],
            role=entry["role"],
            scopes=entry.get("scopes", []),
            is_authenticated=True
        )
    duration_sec = time.perf_counter() - start
    token_ops_sec = iterations / duration_sec
    token_latency_us = (duration_sec / iterations) * 1_000_000

    # 2. Role hierarchy evaluation overhead
    start = time.perf_counter()
    for _ in range(iterations):
        _ = has_role_permission("administrator", "viewer")
        _ = has_role_permission("investigator", "operator")
        _ = has_role_permission("operator", "viewer")
    duration_sec = time.perf_counter() - start
    role_evals = iterations * 3
    role_ops_sec = role_evals / duration_sec
    role_latency_us = (duration_sec / role_evals) * 1_000_000

    # 3. Tenant boundary check overhead
    principal_a = SecurityPrincipal(actor_id="user_a", tenant_id="tenant_a", role="investigator")
    start = time.perf_counter()
    for _ in range(iterations):
        verify_tenant_boundary("tenant_a", principal_a, "document", "doc_123")
    duration_sec = time.perf_counter() - start
    tenant_ops_sec = iterations / duration_sec
    tenant_latency_us = (duration_sec / iterations) * 1_000_000

    total_zero_trust_overhead_us = token_latency_us + role_latency_us + tenant_latency_us
    total_zero_trust_overhead_ms = total_zero_trust_overhead_us / 1000.0

    return {
        "iterations": iterations,
        "token_resolution_ops_sec": round(token_ops_sec, 2),
        "token_resolution_latency_us": round(token_latency_us, 3),
        "role_hierarchy_eval_ops_sec": round(role_ops_sec, 2),
        "role_hierarchy_eval_latency_us": round(role_latency_us, 3),
        "tenant_boundary_check_ops_sec": round(tenant_ops_sec, 2),
        "tenant_boundary_check_latency_us": round(tenant_latency_us, 3),
        "composite_zero_trust_overhead_us": round(total_zero_trust_overhead_us, 3),
        "composite_zero_trust_overhead_ms": round(total_zero_trust_overhead_ms, 4),
        "meets_sub_millisecond_sla": total_zero_trust_overhead_ms < 1.0
    }

def benchmark_input_validation(iterations: int = 10_000) -> Dict[str, Any]:
    """Measure input sanitization, ID regex, and polyglot detection throughput."""
    # 1. ID format validation
    sample_id = "doc_20260927_secret_lineage_0123"
    start = time.perf_counter()
    for _ in range(iterations):
        validate_id_format(sample_id, "document_id")
    dur_id = time.perf_counter() - start
    id_ops_sec = iterations / dur_id

    # 2. SHA-256 hex validation
    sample_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    start = time.perf_counter()
    for _ in range(iterations):
        validate_hash_hex(sample_hash, "artifact_hash")
    dur_hash = time.perf_counter() - start
    hash_ops_sec = iterations / dur_hash

    # 3. Header sanitization
    sample_header = "Report_2026_Analysis\r\nDangerous-Header: evil"
    start = time.perf_counter()
    for _ in range(iterations):
        sanitize_header_value(sample_header)
    dur_header = time.perf_counter() - start
    header_ops_sec = iterations / dur_header

    # 4. Upload payload validation & polyglot checks across payload sizes
    payload_benchmarks = {}
    sizes = [
        ("10_KB", 10 * 1024),
        ("100_KB", 100 * 1024),
        ("1_MB", 1024 * 1024),
        ("10_MB", 10 * 1024 * 1024),
    ]
    for label, sz in sizes:
        pdf_payload = b"%PDF-1.4\n" + (b"0" * (sz - 16)) + b"\n%%EOF"
        num_runs = 200 if sz <= 1024 * 1024 else 20
        start = time.perf_counter()
        for _ in range(num_runs):
            validate_uploaded_payload(pdf_payload, "application/pdf")
        dur_payload = time.perf_counter() - start
        throughput_mb_s = (sz * num_runs / (1024 * 1024)) / dur_payload
        payload_benchmarks[label] = {
            "size_bytes": sz,
            "validation_throughput_mb_s": round(throughput_mb_s, 2),
            "latency_ms": round((dur_payload / num_runs) * 1000.0, 3)
        }

    return {
        "id_format_validation_ops_sec": round(id_ops_sec, 2),
        "hash_validation_ops_sec": round(hash_ops_sec, 2),
        "header_sanitization_ops_sec": round(header_ops_sec, 2),
        "payload_validation_by_size": payload_benchmarks
    }

def benchmark_rate_limiter_and_replay() -> Dict[str, Any]:
    """Measure rate limiter and anti-replay cache performance under load and concurrency."""
    # 1. Sequential Rate Limiter
    limiter = SlidingWindowRateLimiter()
    key = "bench_key_seq"
    num_requests = 100_000
    start = time.perf_counter()
    for _ in range(num_requests):
        limiter.is_allowed(key, max_requests=1_000_000, window_seconds=60.0)
    dur_seq = time.perf_counter() - start
    limiter_seq_ops_sec = num_requests / dur_seq

    # 2. Concurrent Rate Limiter across 8 threads
    limiter_par = SlidingWindowRateLimiter()
    num_threads = 8
    requests_per_thread = 10_000
    total_concurrent = num_threads * requests_per_thread

    def _limiter_worker(thread_idx: int):
        t_key = f"bench_key_par_{thread_idx % 2}"
        for _ in range(requests_per_thread):
            limiter_par.is_allowed(t_key, max_requests=1_000_000, window_seconds=60.0)

    start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(_limiter_worker, i) for i in range(num_threads)]
        for f in futures:
            f.result()
    dur_par = time.perf_counter() - start
    limiter_concurrent_ops_sec = total_concurrent / dur_par

    # 3. Anti-Replay Cache Throughput
    replay_cache = ReplayProtectionCache(window_seconds=300)
    num_nonces = 50_000
    nonces = [f"nonce_{i:08x}" for i in range(num_nonces)]
    start = time.perf_counter()
    for n in nonces:
        replay_cache.check_and_record(n)
    dur_replay = time.perf_counter() - start
    replay_ops_sec = num_nonces / dur_replay

    return {
        "rate_limiter_sequential_ops_sec": round(limiter_seq_ops_sec, 2),
        "rate_limiter_concurrent_ops_sec": round(limiter_concurrent_ops_sec, 2),
        "rate_limiter_threads": num_threads,
        "anti_replay_cache_ops_sec": round(replay_ops_sec, 2),
    }

def benchmark_endpoint_latencies(runs_per_endpoint: int = 50) -> Dict[str, Any]:
    """Measure end-to-end HTTP request latencies through FastAPI middleware and security headers."""
    client = TestClient(app)
    headers_inv_a = {"Authorization": "Bearer token_investigator_tenant_a"}

    orig_crypto = config.rate_limit_crypto
    orig_default = config.rate_limit_default
    try:
        config.rate_limit_crypto = 10_000
        config.rate_limit_default = 10_000
        default_rate_limiter.reset()

        endpoints = [
            ("GET /health (unauthenticated)", "/health", {}),
            ("GET /documents (authenticated, tenant-scoped)", "/documents", headers_inv_a),
            ("GET /releases (authenticated, tenant-scoped)", "/releases", headers_inv_a),
            ("GET /ledger/verify (tamper-evident audit)", "/ledger/verify", headers_inv_a),
        ]

        endpoint_results = {}
        for name, path, hdrs in endpoints:
            latencies = []
            for _ in range(runs_per_endpoint):
                t0 = time.perf_counter()
                resp = client.get(path, headers=hdrs)
                t1 = time.perf_counter()
                assert resp.status_code == 200
                # Ensure security headers are present
                assert resp.headers.get("X-Content-Type-Options") == "nosniff"
                assert resp.headers.get("X-Frame-Options") == "DENY"
                latencies.append((t1 - t0) * 1000.0)

            latencies.sort()
            median_ms = latencies[len(latencies) // 2]
            p95_ms = latencies[int(len(latencies) * 0.95)]
            p99_ms = latencies[int(len(latencies) * 0.99)]
            min_ms = latencies[0]
            max_ms = latencies[-1]

            endpoint_results[name] = {
                "samples": runs_per_endpoint,
                "min_latency_ms": round(min_ms, 3),
                "median_latency_ms": round(median_ms, 3),
                "p95_latency_ms": round(p95_ms, 3),
                "p99_latency_ms": round(p99_ms, 3),
                "max_latency_ms": round(max_ms, 3),
            }

        return endpoint_results
    finally:
        config.rate_limit_crypto = orig_crypto
        config.rate_limit_default = orig_default
        default_rate_limiter.reset()

def main():
    print("=" * 70)
    print("AEGISTRACE API SECURITY & ZERO-TRUST PERFORMANCE BENCHMARK")
    print("=" * 70)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("Executing benchmarks...")

    # 1. Auth & Authz evaluation overhead
    print("1. Benchmarking Authentication & Zero-Trust Authorization...")
    auth_results = benchmark_auth_and_authz(iterations=20_000)
    print(f"   Composite Zero-Trust Overhead: {auth_results['composite_zero_trust_overhead_us']:.2f} us "
          f"({auth_results['composite_zero_trust_overhead_ms']:.4f} ms)")
    print(f"   SLA (< 1.0 ms): {'PASS' if auth_results['meets_sub_millisecond_sla'] else 'FAIL'}")

    # 2. Input validation & polyglot checks
    print("2. Benchmarking Input Validation & Payload Sanitization...")
    val_results = benchmark_input_validation(iterations=20_000)
    print(f"   ID Regex Validation: {val_results['id_format_validation_ops_sec']:,.0f} ops/sec")
    print(f"   Hash Validation: {val_results['hash_validation_ops_sec']:,.0f} ops/sec")
    print(f"   1MB Payload Validation: {val_results['payload_validation_by_size']['1_MB']['validation_throughput_mb_s']} MB/s")

    # 3. Rate limiter & anti-replay
    print("3. Benchmarking Rate Limiter & Anti-Replay Cache...")
    rate_results = benchmark_rate_limiter_and_replay()
    print(f"   Rate Limiter (Sequential): {rate_results['rate_limiter_sequential_ops_sec']:,.0f} ops/sec")
    print(f"   Rate Limiter (8 Threads): {rate_results['rate_limiter_concurrent_ops_sec']:,.0f} ops/sec")
    print(f"   Anti-Replay Cache: {rate_results['anti_replay_cache_ops_sec']:,.0f} ops/sec")

    # 4. HTTP endpoint response latencies
    print("4. Benchmarking E2E Endpoint Latencies under Security Middleware...")
    endpoint_results = benchmark_endpoint_latencies(runs_per_endpoint=100)
    for ep_name, metrics in endpoint_results.items():
        print(f"   {ep_name}: median={metrics['median_latency_ms']:.2f} ms, p95={metrics['p95_latency_ms']:.2f} ms")

    # Output artifact
    output_dir = Path(__file__).resolve().parent.parent.parent / "artifacts" / "performance"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "api_security_benchmark_results.json"

    benchmark_bundle = {
        "metadata": {
            "title": "AegisTrace API Security & Zero-Trust Benchmark",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "python_version": sys.version,
            "platform": sys.platform,
            "air_gapped": True
        },
        "authentication_and_authorization": auth_results,
        "input_validation_and_sanitization": val_results,
        "rate_limiting_and_replay_protection": rate_results,
        "endpoint_latencies": endpoint_results
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(benchmark_bundle, f, indent=2)

    print(f"\nBenchmark successfully saved to:\n{output_path}")
    print("=" * 70)

if __name__ == "__main__":
    main()
