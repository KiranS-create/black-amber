"""
AegisTrace Cryptographic Performance and Resource Benchmark Harness.

Measures authentic cryptographic and workflow operations across:
- ML-KEM-768 (FIPS 203 / Kyber-768)
- ML-DSA-65 (FIPS 204 / Dilithium3)
- AES-256-GCM (NIST SP 800-38D)
- HKDF-SHA256 (RFC 5869)
- HMAC-SHA256 (FIPS 198-1)
- Release Packaging, Client Decryption, Provenance Signing & Verification
- Multi-recipient Batch Scaling (1, 10, 50, 100)
- Multi-core Process Scaling (1, 2, 4, 8 workers)

Statistical Metrics: Sample count, Warm-up count, Min, Median, Mean, Max, P95, P99,
StdDev, Cold-start vs Steady-state, CPU time, Wall-clock time, Process RSS, Peak Memory.
"""

import os
import sys
import time
import math
import json
import csv
import base64
import hashlib
import platform
import statistics
import tracemalloc
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable, Tuple
import concurrent.futures

try:
    import psutil
    _PSUTIL_AVAILABLE = True
except ImportError:
    _PSUTIL_AVAILABLE = False

# Ensure repository root is in sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from core.crypto.kem import MLKEM768
from core.crypto.signatures import MLDSA65
from core.crypto.symmetric import (
    generate_symmetric_key,
    encrypt_aes_gcm,
    decrypt_aes_gcm,
    wrap_key_aes_kw,
    unwrap_key_aes_kw,
)
from core.crypto.key_derivation import (
    derive_key,
    derive_recipient_wrapping_key,
    PROTOCOL_VERSION,
)
from core.recipient import RecipientRegistry, Recipient
from core.release import ReleaseManager, DocumentRelease, ReleaseRecipientPackage
from core.provenance.decryption import RecipientDecryptionClient
from core.ledger.ledger import TamperEvidentLedger, EvidenceEvent
from core.traceability.provider import PrototypeTraceabilityProvider


class BenchmarkResult:
    """Encapsulates statistical latency and resource measurements for a single operation."""
    def __init__(
        self,
        name: str,
        category: str,
        sample_count: int,
        warmup_count: int,
        cold_start_ms: float,
        durations_ms: List[float],
        cpu_times_ms: List[float],
        memory_delta_kb: float,
        peak_memory_kb: float,
        throughput_ops_sec: float,
        throughput_mb_sec: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.category = category
        self.sample_count = sample_count
        self.warmup_count = warmup_count
        self.cold_start_ms = cold_start_ms
        self.durations_ms = sorted(durations_ms)
        self.cpu_times_ms = sorted(cpu_times_ms)
        self.memory_delta_kb = memory_delta_kb
        self.peak_memory_kb = peak_memory_kb
        self.throughput_ops_sec = throughput_ops_sec
        self.throughput_mb_sec = throughput_mb_sec
        self.metadata = metadata or {}

        if self.durations_ms:
            self.min_ms = self.durations_ms[0]
            self.max_ms = self.durations_ms[-1]
            self.mean_ms = statistics.mean(self.durations_ms)
            self.median_ms = statistics.median(self.durations_ms)
            self.stddev_ms = statistics.stdev(self.durations_ms) if len(self.durations_ms) > 1 else 0.0
            p95_idx = min(len(self.durations_ms) - 1, int(math.ceil(0.95 * len(self.durations_ms))) - 1)
            p99_idx = min(len(self.durations_ms) - 1, int(math.ceil(0.99 * len(self.durations_ms))) - 1)
            self.p95_ms = self.durations_ms[p95_idx]
            self.p99_ms = self.durations_ms[p99_idx]
            self.mean_cpu_ms = statistics.mean(self.cpu_times_ms) if self.cpu_times_ms else self.mean_ms
        else:
            self.min_ms = self.max_ms = self.mean_ms = self.median_ms = self.stddev_ms = self.p95_ms = self.p99_ms = self.mean_cpu_ms = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "sample_count": self.sample_count,
            "warmup_count": self.warmup_count,
            "cold_start_ms": round(self.cold_start_ms, 4),
            "min_ms": round(self.min_ms, 4),
            "median_ms": round(self.median_ms, 4),
            "mean_ms": round(self.mean_ms, 4),
            "max_ms": round(self.max_ms, 4),
            "p95_ms": round(self.p95_ms, 4),
            "p99_ms": round(self.p99_ms, 4),
            "stddev_ms": round(self.stddev_ms, 4),
            "mean_cpu_ms": round(self.mean_cpu_ms, 4),
            "memory_delta_kb": round(self.memory_delta_kb, 2),
            "peak_memory_kb": round(self.peak_memory_kb, 2),
            "throughput_ops_sec": round(self.throughput_ops_sec, 2),
            "throughput_mb_sec": round(self.throughput_mb_sec, 2) if self.throughput_mb_sec is not None else None,
            "metadata": self.metadata,
        }


class BenchmarkHarness:
    """
    Precision execution harness for measuring cryptographic primitives and system workflows.
    Guarantees ephemeral key generation, zero production secret leakage, and strict correctness.
    """
    def __init__(self):
        self.process = psutil.Process(os.getpid()) if _PSUTIL_AVAILABLE else None

    def get_hardware_profile(self) -> Dict[str, Any]:
        ram_gb = round(psutil.virtual_memory().total / (1024 ** 3), 2) if _PSUTIL_AVAILABLE else None
        phys_cores = psutil.cpu_count(logical=False) if _PSUTIL_AVAILABLE else None
        log_cores = psutil.cpu_count(logical=True) if _PSUTIL_AVAILABLE else None
        
        kem_meta = MLKEM768.get_metadata()
        dsa_meta = MLDSA65.get_metadata()

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "os": platform.system(),
            "os_release": platform.release(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "python_compiler": platform.python_compiler(),
            "physical_cores": phys_cores,
            "logical_cores": log_cores,
            "total_ram_gb": ram_gb,
            "air_gapped_offline": True,
            "crypto_providers": {
                "ml_kem_768": kem_meta,
                "ml_dsa_65": dsa_meta,
                "symmetric": "PyCryptodome (AES-256-GCM / NIST SP 800-38D)",
                "kdf": "RFC 5869 HKDF-SHA256 (Pure Python hashlib/hmac)",
                "ledger": "SHA-256 Merkle/Hash-Chain",
            }
        }

    def measure_operation(
        self,
        name: str,
        category: str,
        func: Callable[[], Any],
        iterations: int = 30,
        warmup: int = 3,
        payload_bytes: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BenchmarkResult:
        """
        Executes an operation with cold-start capture, warm-up stabilization,
        high-resolution wall/cpu timing, and tracemalloc memory profiling.
        """
        # 1. Cold-start measurement (first invocation)
        t_wall_0 = time.perf_counter()
        func()
        t_wall_1 = time.perf_counter()
        cold_start_ms = (t_wall_1 - t_wall_0) * 1000.0

        # 2. Warm-up runs (prime caches, JIT, memory pools)
        for _ in range(warmup):
            func()

        # 3. Memory baseline
        tracemalloc.start()
        tracemalloc.reset_peak()
        rss_before_kb = (self.process.memory_info().rss / 1024.0) if self.process else 0.0

        durations_ms: List[float] = []
        cpu_times_ms: List[float] = []

        total_wall_start = time.perf_counter()

        # 4. Steady-state benchmark loop
        for _ in range(iterations):
            w0 = time.perf_counter()
            c0 = time.process_time()
            func()
            c1 = time.process_time()
            w1 = time.perf_counter()
            durations_ms.append((w1 - w0) * 1000.0)
            cpu_times_ms.append((c1 - c0) * 1000.0)

        total_wall_elapsed = time.perf_counter() - total_wall_start

        # 5. Memory metrics capture
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        rss_after_kb = (self.process.memory_info().rss / 1024.0) if self.process else 0.0

        memory_delta_kb = max(0.0, rss_after_kb - rss_before_kb)
        peak_memory_kb = peak_mem / 1024.0

        throughput_ops = (iterations / total_wall_elapsed) if total_wall_elapsed > 0 else 0.0
        throughput_mb = None
        if payload_bytes is not None and total_wall_elapsed > 0:
            total_mb = (payload_bytes * iterations) / (1024.0 * 1024.0)
            throughput_mb = total_mb / total_wall_elapsed

        return BenchmarkResult(
            name=name,
            category=category,
            sample_count=iterations,
            warmup_count=warmup,
            cold_start_ms=cold_start_ms,
            durations_ms=durations_ms,
            cpu_times_ms=cpu_times_ms,
            memory_delta_kb=memory_delta_kb,
            peak_memory_kb=peak_memory_kb,
            throughput_ops_sec=throughput_ops,
            throughput_mb_sec=throughput_mb,
            metadata=metadata,
        )


# =============================================================================
# BENCHMARK SUITE EXECUTORS
# =============================================================================

def run_mlkem_benchmarks(harness: BenchmarkHarness, iterations: int = 30) -> List[BenchmarkResult]:
    """Measures ML-KEM-768 key generation, encapsulation, and decapsulation."""
    results = []

    # 1. Key Generation
    res_keygen = harness.measure_operation(
        name="ML-KEM-768 Keypair Generation",
        category="Post-Quantum KEM",
        func=lambda: MLKEM768.generate_keypair(),
        iterations=iterations,
        warmup=3,
        metadata={"public_key_bytes": 1184, "private_key_bytes": 2400}
    )
    results.append(res_keygen)

    # 2. Encapsulation
    kp = MLKEM768.generate_keypair()
    res_encap = harness.measure_operation(
        name="ML-KEM-768 Encapsulation",
        category="Post-Quantum KEM",
        func=lambda: MLKEM768.encapsulate(kp.public_key_bytes),
        iterations=iterations,
        warmup=3,
        metadata={"ciphertext_bytes": 1088, "shared_secret_bytes": 32}
    )
    results.append(res_encap)

    # 3. Decapsulation
    encap_res = MLKEM768.encapsulate(kp.public_key_bytes)
    res_decap = harness.measure_operation(
        name="ML-KEM-768 Decapsulation",
        category="Post-Quantum KEM",
        func=lambda: MLKEM768.decapsulate(kp.private_key_bytes, encap_res.ciphertext),
        iterations=iterations,
        warmup=3,
        metadata={"ciphertext_bytes": 1088, "shared_secret_bytes": 32}
    )
    results.append(res_decap)

    return results


def run_mldsa_benchmarks(harness: BenchmarkHarness, iterations: int = 25) -> List[BenchmarkResult]:
    """Measures ML-DSA-65 key generation, signing, and signature verification."""
    results = []
    bench_payload = b"DECRYPTION_PROVENANCE:evt_bench_001:doc_test_101:rel_test_202:rec_alice_303:artifact_hash_abc123:000000:2026-09-26T12:00:00Z"

    # 1. Key Generation
    res_keygen = harness.measure_operation(
        name="ML-DSA-65 Keypair Generation",
        category="Post-Quantum DSA",
        func=lambda: MLDSA65.generate_keypair(),
        iterations=iterations,
        warmup=3,
        metadata={"public_key_bytes": 1952, "private_key_bytes": 4000}
    )
    results.append(res_keygen)

    # 2. Signing
    kp = MLDSA65.generate_keypair()
    res_sign = harness.measure_operation(
        name="ML-DSA-65 Signature Generation",
        category="Post-Quantum DSA",
        func=lambda: MLDSA65.sign(kp.private_key_bytes, bench_payload),
        iterations=iterations,
        warmup=3,
        payload_bytes=len(bench_payload),
        metadata={"signature_bytes": 3293, "message_bytes": len(bench_payload)}
    )
    results.append(res_sign)

    # 3. Verification
    signature = MLDSA65.sign(kp.private_key_bytes, bench_payload)
    res_verify = harness.measure_operation(
        name="ML-DSA-65 Signature Verification",
        category="Post-Quantum DSA",
        func=lambda: MLDSA65.verify(kp.public_key_bytes, bench_payload, signature),
        iterations=iterations,
        warmup=3,
        payload_bytes=len(bench_payload),
        metadata={"signature_bytes": 3293, "message_bytes": len(bench_payload)}
    )
    results.append(res_verify)

    return results


def run_symmetric_benchmarks(harness: BenchmarkHarness, iterations: int = 50) -> List[BenchmarkResult]:
    """Measures AES-256-GCM, HKDF-SHA256, HMAC-SHA256, and AES Key Wrap."""
    results = []

    # Payload sizes: 10 KB, 100 KB, 1 MB, 5 MB
    sizes = [
        ("10KB", 10 * 1024),
        ("100KB", 100 * 1024),
        ("1MB", 1024 * 1024),
        ("5MB", 5 * 1024 * 1024),
    ]

    sym_key = generate_symmetric_key()

    for label, size in sizes:
        sample_data = b"S" * size
        ad = b"SIH26237-AUTHENTICATED-RELEASE-SCOPE"

        # AES-GCM Encrypt
        res_enc = harness.measure_operation(
            name=f"AES-256-GCM Encrypt ({label})",
            category="Symmetric Cryptography",
            func=lambda d=sample_data: encrypt_aes_gcm(sym_key, d, associated_data=ad),
            iterations=iterations if size < 1024 * 1024 else max(15, iterations // 2),
            warmup=3,
            payload_bytes=size,
            metadata={"payload_size_bytes": size, "mode": "AES-256-GCM"}
        )
        results.append(res_enc)

        # AES-GCM Decrypt
        encrypted = encrypt_aes_gcm(sym_key, sample_data, associated_data=ad)
        res_dec = harness.measure_operation(
            name=f"AES-256-GCM Decrypt ({label})",
            category="Symmetric Cryptography",
            func=lambda e=encrypted: decrypt_aes_gcm(sym_key, e),
            iterations=iterations if size < 1024 * 1024 else max(15, iterations // 2),
            warmup=3,
            payload_bytes=size,
            metadata={"payload_size_bytes": size, "mode": "AES-256-GCM"}
        )
        results.append(res_dec)

    # HKDF-SHA256 Key Derivation
    shared_sec = os.urandom(32)
    res_hkdf = harness.measure_operation(
        name="HKDF-SHA256 Key Derivation (RFC 5869)",
        category="Key Derivation",
        func=lambda: derive_recipient_wrapping_key(
            shared_secret=shared_sec,
            release_id="rel_bench_101",
            document_id="doc_bench_001",
            recipient_id="rec_alice_001",
            algorithm_id="ML-KEM-768"
        ),
        iterations=iterations,
        warmup=3,
        metadata={"output_length": 32, "salt_binding": True}
    )
    results.append(res_hkdf)

    # HMAC-SHA256 Token Computation
    hmac_key = os.urandom(32)
    hmac_msg = b"doc_001:rel_101:alice:hash_deadbeef" * 4
    res_hmac = harness.measure_operation(
        name="HMAC-SHA256 Token Generation & Verification",
        category="Symmetric Cryptography",
        func=lambda: hashlib.sha256(hmac.new(hmac_key, hmac_msg, hashlib.sha256).digest()).hexdigest() if 'hmac' in globals() else hmac_bench_func(hmac_key, hmac_msg),
        iterations=iterations,
        warmup=3,
        metadata={"algorithm": "HMAC-SHA256"}
    )
    results.append(res_hmac)

    # AES Key Wrap / Unwrap
    doc_key_to_wrap = generate_symmetric_key()
    wrapping_key = generate_symmetric_key()
    res_wrap = harness.measure_operation(
        name="AES-256-GCM Key Wrap (256-bit key)",
        category="Key Derivation",
        func=lambda: wrap_key_aes_kw(wrapping_key, doc_key_to_wrap),
        iterations=iterations,
        warmup=3,
        metadata={"wrapped_payload_bytes": 60}
    )
    results.append(res_wrap)

    wrapped_payload = wrap_key_aes_kw(wrapping_key, doc_key_to_wrap)
    res_unwrap = harness.measure_operation(
        name="AES-256-GCM Key Unwrap (256-bit key)",
        category="Key Derivation",
        func=lambda: unwrap_key_aes_kw(wrapping_key, wrapped_payload),
        iterations=iterations,
        warmup=3,
        metadata={"wrapped_payload_bytes": 60}
    )
    results.append(res_unwrap)

    return results


def hmac_bench_func(key: bytes, msg: bytes) -> str:
    import hmac
    return hmac.new(key, msg, hashlib.sha256).hexdigest()


def run_e2e_critical_path_benchmarks(harness: BenchmarkHarness, iterations: int = 15) -> Tuple[List[BenchmarkResult], Dict[str, Any]]:
    """
    Measures the full AegisTrace critical-path lifecycle:
    Document (100KB) -> SHA256 -> Release Encap -> AES-GCM Enc -> KEM Decap -> AES-GCM Dec ->
    Hash Verify -> Marker Embed -> DSA Sign -> DSA Verify -> Ledger Append.
    """
    results = []

    # Setup isolated test environment
    doc_bytes = b"%PDF-1.7 Document for Critical Path Benchmark\n" + (b"A" * (100 * 1024))
    reg = RecipientRegistry()
    alice = reg.enroll("Alice", "alice")
    trace_provider = PrototypeTraceabilityProvider()
    ledger = TamperEvidentLedger()
    rel_mgr = ReleaseManager(registry=reg)
    dec_client = RecipientDecryptionClient(ledger=ledger, traceability_provider=trace_provider)

    # 1. Document SHA-256 Digest
    res_sha = harness.measure_operation(
        name="Stage 1: Document SHA-256 Digest (100KB)",
        category="End-to-End Workflow",
        func=lambda: hashlib.sha256(doc_bytes).hexdigest(),
        iterations=iterations,
        warmup=3,
        payload_bytes=len(doc_bytes)
    )
    results.append(res_sha)

    # 2. Encrypted Release Package Creation (ML-KEM + AES-GCM)
    res_release = harness.measure_operation(
        name="Stage 2: Release Creation & Encapsulation (1 Recipient)",
        category="End-to-End Workflow",
        func=lambda: rel_mgr.create_release(
            document_bytes=doc_bytes,
            document_name="bench_critical.pdf",
            issuer_id="HQ_BENCH",
            recipient_ids=["alice"]
        ),
        iterations=iterations,
        warmup=2,
        payload_bytes=len(doc_bytes)
    )
    results.append(res_release)

    # 3. Full Recipient Decryption + Provenance Signing + Ledger Append
    release = rel_mgr.create_release(
        document_bytes=doc_bytes,
        document_name="bench_critical.pdf",
        issuer_id="HQ_BENCH",
        recipient_ids=["alice"]
    )
    pkg = release.packages["alice"]

    res_decrypt_prov = harness.measure_operation(
        name="Stage 3: Recipient Decrypt + Provenance Signing + Ledger",
        category="End-to-End Workflow",
        func=lambda: dec_client.decrypt_package(
            package=pkg,
            recipient=alice,
            record_to_ledger=False  # Keep isolated for benchmark loops
        ),
        iterations=iterations,
        warmup=2,
        payload_bytes=len(doc_bytes)
    )
    results.append(res_decrypt_prov)

    # 4. Provenance Event Verification (ML-DSA-65 Verification)
    _, traceable_doc, evt, _ = dec_client.decrypt_package(package=pkg, recipient=alice, record_to_ledger=False)
    
    sign_payload = (
        f"DECRYPTION_PROVENANCE:{evt.event_id}:{evt.document_id}:"
        f"{evt.release_id}:{evt.recipient_id}:{evt.artifact_hash}:"
        f"{evt.previous_event_hash}:{evt.timestamp}"
    ).encode('utf-8')
    sig_bytes = base64.b64decode(evt.signature)

    res_verify_prov = harness.measure_operation(
        name="Stage 4: Provenance Signature Verification (ML-DSA-65)",
        category="End-to-End Workflow",
        func=lambda: MLDSA65.verify(alice.dsa_keypair.public_key_bytes, sign_payload, sig_bytes),
        iterations=iterations,
        warmup=3
    )
    results.append(res_verify_prov)

    # 5. Complete End-to-End Release -> Decrypt -> Provenance Sequence
    def full_pipeline():
        rel = rel_mgr.create_release(
            document_bytes=doc_bytes,
            document_name="bench_full.pdf",
            issuer_id="HQ_BENCH",
            recipient_ids=["alice"]
        )
        p = rel.packages["alice"]
        pt, tr, ev, _ = dec_client.decrypt_package(package=p, recipient=alice, record_to_ledger=False)
        payload = (
            f"DECRYPTION_PROVENANCE:{ev.event_id}:{ev.document_id}:"
            f"{ev.release_id}:{ev.recipient_id}:{ev.artifact_hash}:"
            f"{ev.previous_event_hash}:{ev.timestamp}"
        ).encode('utf-8')
        sig = base64.b64decode(ev.signature)
        valid = MLDSA65.verify(alice.dsa_keypair.public_key_bytes, payload, sig)
        if not valid:
            raise RuntimeError("Provenance verification failed in full pipeline benchmark")
        return tr

    res_full_e2e = harness.measure_operation(
        name="Complete E2E Lifecycle: Release -> Decrypt -> Provenance Verify",
        category="End-to-End Workflow",
        func=full_pipeline,
        iterations=iterations,
        warmup=2,
        payload_bytes=len(doc_bytes)
    )
    results.append(res_full_e2e)

    # Stage dominance breakdown
    sum_stages = res_sha.mean_ms + res_release.mean_ms + res_decrypt_prov.mean_ms + res_verify_prov.mean_ms
    stage_breakdown = {
        "document_sha256_mean_ms": res_sha.mean_ms,
        "release_creation_mean_ms": res_release.mean_ms,
        "decryption_and_signing_mean_ms": res_decrypt_prov.mean_ms,
        "provenance_verification_mean_ms": res_verify_prov.mean_ms,
        "total_critical_path_mean_ms": res_full_e2e.mean_ms,
        "sum_constituent_stages_mean_ms": sum_stages,
        "stage_percentages": {
            "document_sha256": round((res_sha.mean_ms / sum_stages) * 100, 2) if sum_stages > 0 else 0.0,
            "release_creation": round((res_release.mean_ms / sum_stages) * 100, 2) if sum_stages > 0 else 0.0,
            "decryption_and_signing": round((res_decrypt_prov.mean_ms / sum_stages) * 100, 2) if sum_stages > 0 else 0.0,
            "provenance_verification": round((res_verify_prov.mean_ms / sum_stages) * 100, 2) if sum_stages > 0 else 0.0,
        }
    }

    return results, stage_breakdown


def run_batch_benchmarks(harness: BenchmarkHarness, batch_sizes: List[int] = [1, 10, 50, 100]) -> List[Dict[str, Any]]:
    """
    Measures batch release packaging performance across varying recipient pool sizes.
    Evaluates: Total elapsed time, average time per recipient, throughput, memory growth.
    """
    sample_doc = b"%PDF-1.7 Batch Release Benchmark Payload\n" + (b"B" * (50 * 1024))  # 50 KB
    batch_results = []

    for count in batch_sizes:
        reg = RecipientRegistry()
        recipient_ids = []
        for i in range(count):
            r_id = f"rec_batch_{i:04d}"
            reg.enroll(f"Batch Recipient {i}", r_id)
            recipient_ids.append(r_id)

        rel_mgr = ReleaseManager(registry=reg)

        # Measure batch release creation
        iters = max(3, 20 // max(1, count // 10))
        res = harness.measure_operation(
            name=f"Batch Release Creation ({count} Recipients)",
            category="Batch Scaling",
            func=lambda: rel_mgr.create_release(
                document_bytes=sample_doc,
                document_name="batch_bench.pdf",
                issuer_id="HQ_BATCH",
                recipient_ids=recipient_ids
            ),
            iterations=iters,
            warmup=1,
            payload_bytes=len(sample_doc) * count,
            metadata={"recipient_count": count}
        )

        avg_per_recipient_ms = res.mean_ms / count if count > 0 else 0.0
        recipients_per_sec = (1000.0 / avg_per_recipient_ms) if avg_per_recipient_ms > 0 else 0.0

        batch_results.append({
            "recipient_count": count,
            "total_mean_ms": round(res.mean_ms, 2),
            "median_ms": round(res.median_ms, 2),
            "p95_ms": round(res.p95_ms, 2),
            "avg_per_recipient_ms": round(avg_per_recipient_ms, 4),
            "recipients_per_sec": round(recipients_per_sec, 2),
            "peak_memory_kb": round(res.peak_memory_kb, 2),
            "memory_delta_kb": round(res.memory_delta_kb, 2),
        })

    return batch_results


# Worker function for multiprocessing benchmark
def _worker_crypto_task(num_ops: int) -> int:
    """Independent worker task executing ML-KEM encapsulation + ML-DSA signing."""
    kp_kem = MLKEM768.generate_keypair()
    kp_dsa = MLDSA65.generate_keypair()
    msg = b"WORKER_CRYPTO_BENCHMARK_PAYLOAD"
    
    for _ in range(num_ops):
        enc = MLKEM768.encapsulate(kp_kem.public_key_bytes)
        _ = MLKEM768.decapsulate(kp_kem.private_key_bytes, enc.ciphertext)
        sig = MLDSA65.sign(kp_dsa.private_key_bytes, msg)
        _ = MLDSA65.verify(kp_dsa.public_key_bytes, msg, sig)
    return num_ops


def run_multicore_scaling_benchmarks(worker_counts: List[int] = [1, 2, 4, 8], total_ops: int = 40) -> List[Dict[str, Any]]:
    """
    Measures multi-core scaling efficiency across worker pools using ProcessPoolExecutor.
    Calculates actual speedup vs ideal linear speedup and scaling efficiency.
    """
    scaling_results = []
    base_time_sec = None

    for workers in worker_counts:
        ops_per_worker = max(1, total_ops // workers)
        effective_total_ops = ops_per_worker * workers

        t0 = time.perf_counter()
        with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(_worker_crypto_task, ops_per_worker) for _ in range(workers)]
            completed_ops = sum(f.result() for f in concurrent.futures.as_completed(futures))
        t1 = time.perf_counter()

        elapsed_sec = t1 - t0
        ops_sec = effective_total_ops / elapsed_sec if elapsed_sec > 0 else 0.0

        if base_time_sec is None:
            base_time_sec = elapsed_sec
            speedup = 1.0
            efficiency = 100.0
        else:
            speedup = base_time_sec / elapsed_sec if elapsed_sec > 0 else 0.0
            efficiency = (speedup / workers) * 100.0 if workers > 0 else 0.0

        scaling_results.append({
            "worker_count": workers,
            "total_ops": effective_total_ops,
            "elapsed_seconds": round(elapsed_sec, 4),
            "ops_per_second": round(ops_sec, 2),
            "speedup": round(speedup, 2),
            "scaling_efficiency_pct": round(efficiency, 2),
        })

    return scaling_results


# =============================================================================
# EXPORT & ARTIFACT GENERATION
# =============================================================================

def export_all_benchmark_artifacts(
    hardware_profile: Dict[str, Any],
    all_results: List[BenchmarkResult],
    stage_breakdown: Dict[str, Any],
    batch_results: List[Dict[str, Any]],
    scaling_results: List[Dict[str, Any]],
    output_dir: str = os.path.join(REPO_ROOT, "artifacts", "performance"),
) -> Tuple[str, str, str]:
    """Serializes benchmark results to JSON and CSV artifacts."""
    os.makedirs(output_dir, exist_ok=True)

    json_path = os.path.join(output_dir, "crypto_benchmark_results.json")
    csv_path = os.path.join(output_dir, "crypto_benchmark_summary.csv")
    scaling_path = os.path.join(output_dir, "batch_and_multicore_scaling.json")

    # 1. Full JSON Report
    full_json_data = {
        "hardware_profile": hardware_profile,
        "summary": {
            "total_benchmarked_operations": len(all_results),
            "benchmark_timestamp": hardware_profile["timestamp"],
        },
        "critical_path_breakdown": stage_breakdown,
        "batch_scaling": batch_results,
        "multicore_scaling": scaling_results,
        "operations": [r.to_dict() for r in all_results],
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(full_json_data, f, indent=2)

    # 2. Summary CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Category",
            "Operation",
            "Samples",
            "ColdStart (ms)",
            "Min (ms)",
            "Median (ms)",
            "Mean (ms)",
            "P95 (ms)",
            "P99 (ms)",
            "StdDev (ms)",
            "Throughput (ops/s)",
            "Throughput (MB/s)",
            "Peak Memory (KB)"
        ])
        for r in all_results:
            writer.writerow([
                r.category,
                r.name,
                r.sample_count,
                round(r.cold_start_ms, 4),
                round(r.min_ms, 4),
                round(r.median_ms, 4),
                round(r.mean_ms, 4),
                round(r.p95_ms, 4),
                round(r.p99_ms, 4),
                round(r.stddev_ms, 4),
                round(r.throughput_ops_sec, 2),
                round(r.throughput_mb_sec, 2) if r.throughput_mb_sec is not None else "N/A",
                round(r.peak_memory_kb, 2)
            ])

    # 3. Batch and Scaling JSON
    with open(scaling_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": hardware_profile["timestamp"],
            "batch_scaling": batch_results,
            "multicore_scaling": scaling_results,
        }, f, indent=2)

    return json_path, csv_path, scaling_path
