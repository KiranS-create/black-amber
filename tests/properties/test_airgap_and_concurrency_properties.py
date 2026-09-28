"""
tests/properties/test_airgap_and_concurrency_properties.py

Property-based testing and concurrency fuzzing for:
- INVARIANT-009: Air-Gap Non-Loopback Egress Prohibition
- Concurrent Key Lifecycle Management thread safety
- Concurrent TamperEvidentLedger sequential consistency
- Concurrent SlidingWindowRateLimiter strict boundary enforcement
"""

import socket
import threading
import concurrent.futures
import pytest
from core.security.airgap import (
    NetworkEgressGuard,
    AirgapViolationError,
    enforce_airgap,
    is_loopback,
)
from core.crypto.lifecycle.manager import KeyLifecycleManager
from core.crypto.lifecycle.models import KeyType, KeyState
from core.ledger.ledger import TamperEvidentLedger, EvidenceEvent
from apps.api.security import SlidingWindowRateLimiter
from core.testing.property_engine import PropertyRunner, DeterministicGenerator
from core.security.invariants import assert_invariant


def test_property_invariant_009_airgap_non_loopback_prohibition(runner: PropertyRunner):
    """
    INVARIANT-009: When air-gap enforcement is active, all socket connection
    and DNS resolution attempts to non-loopback destinations strictly raise
    AirgapViolationError, while valid local loopback addresses are permitted.
    """
    def prop(g: DeterministicGenerator):
        is_loopback_dest = g.boolean(0.5)

        if is_loopback_dest:
            # Generate valid loopback destination
            loopback_candidate = g.choice([
                "127.0.0.1",
                "::1",
                "localhost",
                f"127.{g.integer(0, 255)}.{g.integer(0, 255)}.{g.integer(1, 254)}",
                "0.0.0.0",
                "::",
            ])
            port = g.integer(1024, 65535)

            with enforce_airgap():
                # Helper predicate must identify as loopback
                assert is_loopback(loopback_candidate) is True

                # getaddrinfo on loopback must NOT raise AirgapViolationError
                # (it may fail with socket.gaierror if host is unresolvable, but NOT AirgapViolationError)
                try:
                    socket.getaddrinfo(loopback_candidate, port)
                except AirgapViolationError:
                    assert_invariant(
                        False,
                        "INVARIANT-009",
                        f"Airgap guard falsely blocked loopback destination '{loopback_candidate}'",
                        g.seed,
                    )
                except Exception:
                    # Non-airgap socket errors are acceptable for mock ports/hosts
                    pass

        else:
            # Generate non-loopback destination (Public IP, LAN, external domain)
            oct1 = g.choice([1, 8, 10, 172, 192, 203])
            oct2 = g.integer(0, 255)
            oct3 = g.integer(0, 255)
            oct4 = g.integer(1, 254)
            if oct1 == 127:
                oct1 = 128

            external_ip = f"{oct1}.{oct2}.{oct3}.{oct4}"
            external_domain = f"{g.alphanumeric(6, 10)}.external-{g.alphanumeric(4, 6)}.org"
            target = g.choice([external_ip, external_domain])
            port = g.integer(80, 8080)

            with enforce_airgap():
                assert is_loopback(target) is False

                # 1. Check getaddrinfo raises AirgapViolationError
                with pytest.raises(AirgapViolationError) as exc_info:
                    socket.getaddrinfo(target, port)
                assert_invariant(
                    "blocked in air-gap mode" in str(exc_info.value),
                    "INVARIANT-009",
                    f"External destination '{target}' was not properly blocked by getaddrinfo",
                    g.seed,
                )

                # 2. Check create_connection raises AirgapViolationError
                with pytest.raises(AirgapViolationError) as exc_info_conn:
                    socket.create_connection((target, port), timeout=0.01)
                assert_invariant(
                    "blocked in air-gap mode" in str(exc_info_conn.value),
                    "INVARIANT-009",
                    f"External destination '{target}' was not properly blocked by create_connection",
                    g.seed,
                )

    res = runner.run_property("invariant_009_airgap_egress_prohibition", prop, iterations=250)
    assert res.passed, res.error_message


def test_property_key_lifecycle_manager_concurrency(runner: PropertyRunner):
    """
    Property: Concurrent thread execution across multiple tenants rotating,
    activating, and querying keys maintains strict atomicity and no deadlocks.
    """
    def prop(g: DeterministicGenerator):
        klm = KeyLifecycleManager()
        tenant_ids = [g.generate_tenant_id(i) for i in range(4)]
        owners = [f"principal_{i}" for i in range(4)]
        num_workers = 8
        ops_per_worker = 15

        # Seed initial active keys
        for t in tenant_ids:
            for o in owners:
                klm.register_key(
                    owner=o,
                    key_type=KeyType.RECIPIENT_PRIVATE_KEY,
                    algorithm="ML-DSA-65",
                    purpose="concurrency-test",
                    tenant_id=t,
                    activate_immediately=True,
                )

        errors = []

        def worker_task(worker_id: int):
            for step in range(ops_per_worker):
                t = tenant_ids[worker_id % len(tenant_ids)]
                o = owners[(worker_id + step) % len(owners)]
                action = (worker_id + step) % 4

                try:
                    if action == 0:
                        # Read active key
                        ak = klm.get_active_key(o, KeyType.RECIPIENT_PRIVATE_KEY, "ML-DSA-65", tenant_id=t)
                        if ak:
                            assert ak.status == KeyState.ACTIVE
                            assert ak.tenant_id == t
                    elif action == 1:
                        # Rotate key
                        klm.rotate_key(
                            owner=o,
                            key_type=KeyType.RECIPIENT_PRIVATE_KEY,
                            algorithm="ML-DSA-65",
                            tenant_id=t,
                            reason=f"Worker {worker_id} rotation {step}",
                        )
                    elif action == 2:
                        # Query owner history
                        keys = klm.get_keys_for_owner(o, KeyType.RECIPIENT_PRIVATE_KEY, "ML-DSA-65", tenant_id=t)
                        assert len(keys) >= 1
                        # Assert epoch monotonicity
                        for k_idx in range(len(keys) - 1):
                            assert keys[k_idx].creation_epoch < keys[k_idx + 1].creation_epoch
                    elif action == 3:
                        # Verify single active key invariant
                        keys = klm.get_keys_for_owner(o, KeyType.RECIPIENT_PRIVATE_KEY, "ML-DSA-65", tenant_id=t)
                        active_count = sum(1 for k in keys if k.status == KeyState.ACTIVE)
                        assert active_count <= 1
                except Exception as ex:
                    errors.append(f"Worker {worker_id} error: {ex}")

        threads = [threading.Thread(target=worker_task, args=(w,)) for w in range(num_workers)]
        for th in threads:
            th.start()
        for th in threads:
            th.join(timeout=10.0)

        assert len(errors) == 0, f"Concurrency errors in KeyLifecycleManager: {errors}"

    res = runner.run_property("key_lifecycle_concurrency", prop, iterations=10)
    assert res.passed, res.error_message


def test_property_tamper_evident_ledger_concurrency(runner: PropertyRunner):
    """
    Property: Parallel threads concurrently appending verified events to a shared
    TamperEvidentLedger under thread synchronization maintain linear hash-chain integrity.
    """
    def prop(g: DeterministicGenerator):
        ledger = TamperEvidentLedger()
        num_workers = 6
        events_per_worker = 10
        lock = threading.Lock()
        errors = []

        def worker(worker_id: int):
            for i in range(events_per_worker):
                try:
                    eid = f"ev-w{worker_id}-{i}-{g.alphanumeric(6, 8)}"
                    with lock:
                        prev_hash = ledger.get_last_event_hash()
                        ev = EvidenceEvent(
                            event_id=eid,
                            event_type="DECRYPTION_EVENT",
                            document_id=f"DOC-{worker_id}",
                            release_id="REL-CONC",
                            recipient_id=f"rec-{worker_id}",
                            algorithm="ML-DSA-65",
                            artifact_hash="aa" * 32,
                            evidence_hash="ee" * 32,
                            previous_event_hash=prev_hash,
                            signature="ss" * 64,
                        )
                        ledger.append_event(ev)
                except Exception as ex:
                    errors.append(f"Ledger concurrency error in worker {worker_id}: {ex}")

        threads = [threading.Thread(target=worker, args=(w,)) for w in range(num_workers)]
        for th in threads:
            th.start()
        for th in threads:
            th.join(timeout=10.0)

        assert len(errors) == 0, f"Ledger append errors: {errors}"
        assert len(ledger.events) == num_workers * events_per_worker

        # Full chain verification must pass 100%
        valid, verification_errors = ledger.verify_chain()
        assert valid is True, f"Ledger chain broken after concurrent appends: {verification_errors}"

    res = runner.run_property("ledger_concurrency_integrity", prop, iterations=15)
    assert res.passed, res.error_message


def test_property_sliding_window_rate_limiter_concurrency(runner: PropertyRunner):
    """
    Property: Highly concurrent requests against a SlidingWindowRateLimiter
    strictly enforce the request quota and never allow more requests than allowed.
    """
    def prop(g: DeterministicGenerator):
        limiter = SlidingWindowRateLimiter()
        limit = 20
        window = 2.0
        key = f"key-{g.alphanumeric(8, 12)}"
        num_threads = 10
        reqs_per_thread = 5  # Total 50 requests (> limit 20)

        results = []

        def client_request():
            for _ in range(reqs_per_thread):
                allowed, _ = limiter.is_allowed(key, max_requests=limit, window_seconds=window)
                results.append(allowed)

        threads = [threading.Thread(target=client_request) for _ in range(num_threads)]
        for th in threads:
            th.start()
        for th in threads:
            th.join(timeout=5.0)

        allowed_count = sum(1 for r in results if r is True)
        assert allowed_count == limit, f"Rate limiter allowed {allowed_count} requests, expected exactly {limit}"

    res = runner.run_property("rate_limiter_concurrency", prop, iterations=10)
    assert res.passed, res.error_message
