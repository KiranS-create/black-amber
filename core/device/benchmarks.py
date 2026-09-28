"""
AegisTrace Device Identity & Hardware Attestation Performance Benchmarks.

Measures latency and throughput across device enrollment, challenge-response,
attestation verification, and session binding.
"""

import time
import base64
from typing import Dict, Any, List
from pydantic import BaseModel
from Crypto.PublicKey import ECC
from Crypto.Signature import DSS
from Crypto.Hash import SHA256

from core.device.models import (
    PlatformType,
    HardwareClass,
    AttestationProviderType,
    AttestationEvidence,
)
from core.device.enrollment import DeviceEnrollmentService
from core.device.challenge import ChallengeManager
from core.device.session import DeviceSessionManager


class DeviceBenchmarkMetrics(BaseModel):
    key_generation_rate_ops_per_sec: float
    enrollment_latency_ms: float
    challenge_generation_latency_ms: float
    challenge_verification_latency_ms: float
    attestation_verification_latency_ms: float
    session_binding_latency_ms: float
    full_flow_latency_ms: float


def run_device_benchmarks(iterations: int = 50) -> DeviceBenchmarkMetrics:
    """
    Executes a comprehensive performance benchmark over the device subsystem.
    """
    enrollment_service = DeviceEnrollmentService()
    challenge_mgr = ChallengeManager()
    session_mgr = DeviceSessionManager()
    org_id = "org_benchmark"

    # 1. Key generation benchmark
    t0 = time.perf_counter()
    sample_keys = []
    for _ in range(iterations):
        k = ECC.generate(curve="P-256")
        sample_keys.append(k)
    t_keygen = time.perf_counter() - t0
    keygen_rate = iterations / max(t_keygen, 1e-6)

    # 2. Challenge generation benchmark
    t0 = time.perf_counter()
    challenges = []
    for i in range(iterations):
        ch = challenge_mgr.create_challenge(device_id=f"dev_bench_{i}", organization_id=org_id)
        challenges.append(ch)
    t_ch_gen = (time.perf_counter() - t0) * 1000.0 / iterations

    # 3. Enrollment benchmark (Standard / Software)
    t0 = time.perf_counter()
    enrolled_devices = []
    for i in range(iterations):
        pub_pem = sample_keys[i].public_key().export_key(format="PEM")
        dev = enrollment_service.register_device(
            device_id=f"dev_bench_{i}",
            organization_id=org_id,
            public_key_pem=pub_pem,
            platform=PlatformType.SOFTWARE_LOCAL,
            registered_to_recipient_id=f"rec_bench_{i}",
        )
        enrolled_devices.append(dev)
    t_enroll = (time.perf_counter() - t0) * 1000.0 / iterations

    # 4. Attestation / Challenge verification benchmark
    t0 = time.perf_counter()
    for i in range(iterations):
        ch = challenge_mgr.create_challenge(device_id=f"dev_att_{i}", organization_id=org_id)
        # Sign challenge with private key
        h = SHA256.new(ch.nonce_hex.encode('utf-8'))
        sig = DSS.new(sample_keys[i % len(sample_keys)], 'fips-186-3').sign(h)

        evidence = AttestationEvidence(
            evidence_id=f"ev_bench_{i}",
            device_id=f"dev_att_{i}",
            provider_type=AttestationProviderType.LOCAL_SOFTWARE,
            challenge_nonce=ch.nonce_hex,
            evidence_payload={"signature_b64": base64.b64encode(sig).decode('ascii')},
        )
        res = enrollment_service.verifier.verify(evidence, enrolled_devices[i % len(enrolled_devices)], ch.nonce_hex)
    t_attest_verif = (time.perf_counter() - t0) * 1000.0 / iterations

    # 5. Challenge verification latency
    t0 = time.perf_counter()
    for i in range(iterations):
        ch = challenge_mgr.create_challenge(device_id=f"dev_val_{i}", organization_id=org_id)
        challenge_mgr.validate_nonce(ch.nonce_hex, f"dev_val_{i}", org_id, consume=True)
    t_ch_val = (time.perf_counter() - t0) * 1000.0 / iterations

    # 6. Session binding benchmark
    t0 = time.perf_counter()
    for i in range(iterations):
        dev = enrolled_devices[i]
        session_mgr.create_bound_session(
            session_id=f"ses_bench_{i}",
            recipient_id=f"rec_bench_{i}",
            device=dev,
            document_root_hash="a" * 64,
        )
    t_sess = (time.perf_counter() - t0) * 1000.0 / iterations

    full_flow = t_ch_gen + t_attest_verif + t_sess

    return DeviceBenchmarkMetrics(
        key_generation_rate_ops_per_sec=round(keygen_rate, 1),
        enrollment_latency_ms=round(t_enroll, 3),
        challenge_generation_latency_ms=round(t_ch_gen, 3),
        challenge_verification_latency_ms=round(t_ch_val, 3),
        attestation_verification_latency_ms=round(t_attest_verif, 3),
        session_binding_latency_ms=round(t_sess, 3),
        full_flow_latency_ms=round(full_flow, 3),
    )


if __name__ == "__main__":
    print("=" * 60)
    print("AEGISTRACE DEVICE IDENTITY & ATTESTATION BENCHMARKS")
    print("=" * 60)
    metrics = run_device_benchmarks(iterations=50)
    for k, v in metrics.model_dump().items():
        print(f"  {k:38s}: {v}")
    print("=" * 60)
