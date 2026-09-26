import time
import statistics
import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.crypto.kem import MLKEM768
from core.crypto.signatures import MLDSA65
from core.crypto.symmetric import generate_symmetric_key, encrypt_aes_gcm, decrypt_aes_gcm
from core.release import ReleaseManager
from core.recipient import RecipientRegistry

def benchmark_op(name, func, iterations=50):
    durations = []
    # Warmup
    for _ in range(3):
        func()
    
    for _ in range(iterations):
        t0 = time.perf_counter()
        func()
        t1 = time.perf_counter()
        durations.append((t1 - t0) * 1000.0)  # ms

    durations.sort()
    mean_val = statistics.mean(durations)
    median_val = statistics.median(durations)
    p95_idx = int(0.95 * len(durations))
    p95_val = durations[p95_idx]

    return {
        "operation": name,
        "iterations": iterations,
        "mean_ms": mean_val,
        "median_ms": median_val,
        "p95_ms": p95_val
    }

def run_benchmarks():
    print("=" * 65)
    print("SIH26237 CRYPTOGRAPHIC PERFORMANCE BASELINE (NIST FIPS 203 & 204)")
    print("=" * 65)

    kem_meta = MLKEM768.get_metadata()
    dsa_meta = MLDSA65.get_metadata()
    print(f"ML-KEM-768 Provider: {kem_meta['provider']} (Standard: {kem_meta['standard']})")
    print(f"ML-DSA-65  Provider: {dsa_meta['provider']} (Standard: {dsa_meta['standard']})\n")

    results = []

    # 1. ML-KEM key generation
    results.append(benchmark_op("ML-KEM-768 Key Generation", lambda: MLKEM768.generate_keypair(), iterations=30))

    # 2. ML-KEM encapsulation
    kp_kem = MLKEM768.generate_keypair()
    results.append(benchmark_op("ML-KEM-768 Encapsulation", lambda: MLKEM768.encapsulate(kp_kem.public_key_bytes), iterations=30))

    # 3. ML-KEM decapsulation
    encap_res = MLKEM768.encapsulate(kp_kem.public_key_bytes)
    results.append(benchmark_op("ML-KEM-768 Decapsulation", lambda: MLKEM768.decapsulate(kp_kem.private_key_bytes, encap_res.ciphertext), iterations=30))

    # 4. ML-DSA key generation
    results.append(benchmark_op("ML-DSA-65 Key Generation", lambda: MLDSA65.generate_keypair(), iterations=20))

    # 5. ML-DSA signing
    kp_dsa = MLDSA65.generate_keypair()
    bench_msg = b"Benchmark provenance payload: release_101:alice:event_202"
    results.append(benchmark_op("ML-DSA-65 Signing", lambda: MLDSA65.sign(kp_dsa.private_key_bytes, bench_msg), iterations=20))

    # 6. ML-DSA verification
    sig = MLDSA65.sign(kp_dsa.private_key_bytes, bench_msg)
    results.append(benchmark_op("ML-DSA-65 Verification", lambda: MLDSA65.verify(kp_dsa.public_key_bytes, bench_msg, sig), iterations=20))

    # 7. AES-256-GCM encryption (100 KB payload)
    sym_key = generate_symmetric_key()
    sample_doc = b"A" * (100 * 1024)  # 100 KB
    results.append(benchmark_op("AES-256-GCM Encrypt (100KB)", lambda: encrypt_aes_gcm(sym_key, sample_doc), iterations=100))

    # 8. AES-256-GCM decryption (100 KB payload)
    enc_sym = encrypt_aes_gcm(sym_key, sample_doc)
    results.append(benchmark_op("AES-256-GCM Decrypt (100KB)", lambda: decrypt_aes_gcm(sym_key, enc_sym), iterations=100))

    # 9. Release Creation (3 recipients: Alice, Bob, Charlie)
    reg = RecipientRegistry()
    reg.enroll("Alice", "alice")
    reg.enroll("Bob", "bob")
    reg.enroll("Charlie", "charlie")
    rel_mgr = ReleaseManager(registry=reg)

    results.append(benchmark_op(
        "Release Creation (100KB doc, 3 Recipients)",
        lambda: rel_mgr.create_release(
            document_bytes=sample_doc,
            document_name="Bench.pdf",
            issuer_id="HQ_BENCH",
            recipient_ids=["alice", "bob", "charlie"]
        ),
        iterations=15
    ))

    # Print Formatted Table
    print(f"{'Operation':<40} | {'Mean (ms)':<10} | {'Median (ms)':<12} | {'P95 (ms)':<10}")
    print("-" * 78)
    for r in results:
        print(f"{r['operation']:<40} | {r['mean_ms']:<10.2f} | {r['median_ms']:<12.2f} | {r['p95_ms']:<10.2f}")
    print("-" * 78)

if __name__ == "__main__":
    run_benchmarks()
