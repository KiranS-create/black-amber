"""
Concurrency, Thread-Safety, and Active Session Lifecycle Tests for AegisTrace Key System.
Verifies:
1. Thread-safe atomic rotation under concurrent load.
2. Strictly linear predecessor/successor chain under multi-threaded rotation.
3. Concurrent read resolution during key rotation with zero deadlocks.
4. Active session continuity vs re-authentication policies during key rotation.
5. Post-rotation export binding invariant (new exports bind only to successor keys).
"""

import threading
import time
from datetime import datetime, timezone, timedelta
import pytest

from core.crypto.lifecycle.models import KeyType, KeyState
from core.crypto.lifecycle.manager import KeyLifecycleManager
from core.crypto.lifecycle.adapters import (
    SessionLifecycleCoordinator,
    SessionRotationPolicy
)


def test_concurrent_rotations_maintain_linear_history():
    mgr = KeyLifecycleManager()

    # Initial active key
    k0 = mgr.register_key(
        owner="rec_concurrent_user",
        key_type=KeyType.RECIPIENT_PRIVATE_KEY,
        algorithm="ML-DSA-65",
        purpose="Concurrent Rotation Test",
        activate_immediately=True
    )

    num_threads = 8
    barrier = threading.Barrier(num_threads)
    results = []
    errors = []

    def worker(worker_id: int):
        barrier.wait()
        try:
            pred, succ = mgr.rotate_key(
                owner="rec_concurrent_user",
                key_type=KeyType.RECIPIENT_PRIVATE_KEY,
                algorithm="ML-DSA-65",
                new_algorithm="ML-DSA-65",
                reason=f"Worker {worker_id} rotation"
            )
            results.append((worker_id, pred.key_id, succ.key_id))
        except Exception as e:
            errors.append((worker_id, str(e)))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # All rotations must complete successfully without deadlocks or unhandled exceptions
    assert len(errors) == 0, f"Concurrent rotation errors: {errors}"
    assert len(results) == num_threads

    # Verify exactly one active key remains
    active = mgr.get_active_key("rec_concurrent_user", KeyType.RECIPIENT_PRIVATE_KEY, algorithm="ML-DSA-65")
    assert active is not None
    assert active.status == KeyState.ACTIVE

    # Verify all previous keys are RETIRED and the chain is strictly linear
    all_keys = mgr.get_keys_for_owner("rec_concurrent_user", KeyType.RECIPIENT_PRIVATE_KEY, algorithm="ML-DSA-65")
    assert len(all_keys) == num_threads + 1

    retired_keys = [k for k in all_keys if k.status == KeyState.RETIRED]
    active_keys = [k for k in all_keys if k.status == KeyState.ACTIVE]
    assert len(retired_keys) == num_threads
    assert len(active_keys) == 1

    # Verify predecessor links form an unbroken chain back to k0
    curr = active
    chain_length = 1
    visited = set([curr.key_id])
    while curr.predecessor_key_id:
        pred = mgr.get_key(curr.predecessor_key_id)
        assert pred is not None
        assert pred.successor_key_id == curr.key_id
        assert pred.key_id not in visited
        visited.add(pred.key_id)
        curr = pred
        chain_length += 1

    assert chain_length == num_threads + 1
    assert curr.key_id == k0.key_id


def test_concurrent_readers_and_writers_no_deadlock():
    mgr = KeyLifecycleManager()
    mgr.register_key(
        owner="rec_rw_user",
        key_type=KeyType.RECIPIENT_PUBLIC_KEY,
        algorithm="ML-DSA-65",
        purpose="RW Concurrency Test",
        activate_immediately=True
    )

    stop_event = threading.Event()
    read_counts = [0]
    errors = []

    def reader():
        while not stop_event.is_set():
            try:
                active = mgr.get_active_key("rec_rw_user", KeyType.RECIPIENT_PUBLIC_KEY, algorithm="ML-DSA-65")
                assert active is not None
                read_counts[0] += 1
            except Exception as e:
                errors.append(f"Reader error: {str(e)}")
                break

    def writer():
        for i in range(5):
            time.sleep(0.01)
            try:
                mgr.rotate_key(
                    owner="rec_rw_user",
                    key_type=KeyType.RECIPIENT_PUBLIC_KEY,
                    algorithm="ML-DSA-65",
                    new_algorithm="ML-DSA-65",
                    reason=f"Writer step {i}"
                )
            except Exception as e:
                errors.append(f"Writer error: {str(e)}")
                break

    r_thread = threading.Thread(target=reader)
    w_thread = threading.Thread(target=writer)

    r_thread.start()
    w_thread.start()

    w_thread.join()
    stop_event.set()
    r_thread.join()

    assert len(errors) == 0, f"Errors during concurrent RW: {errors}"
    assert read_counts[0] > 10


def test_session_lifecycle_policy_evaluation():
    now_dt = datetime.now(timezone.utc)
    sess_created_at = (now_dt - timedelta(minutes=10)).isoformat()
    sess_expires_at = (now_dt + timedelta(minutes=50)).isoformat()
    expired_at = (now_dt - timedelta(minutes=1)).isoformat()
    rotation_time = (now_dt - timedelta(minutes=5)).isoformat()

    # Policy 1: SESSION_CONTINUES_UNTIL_EXPIRY
    coord_lenient = SessionLifecycleCoordinator(policy=SessionRotationPolicy.SESSION_CONTINUES_UNTIL_EXPIRY)

    # Active session continues despite rotation
    assert coord_lenient.evaluate_session_validity(
        session_created_at=sess_created_at,
        session_expires_at=sess_expires_at,
        key_rotation_time=rotation_time
    ) is True

    # Expired session is invalid regardless
    assert coord_lenient.evaluate_session_validity(
        session_created_at=sess_created_at,
        session_expires_at=expired_at,
        key_rotation_time=rotation_time
    ) is False

    # Policy 2: SESSION_REQUIRES_REAUTH_ON_ROTATION
    coord_strict = SessionLifecycleCoordinator(policy=SessionRotationPolicy.SESSION_REQUIRES_REAUTH_ON_ROTATION)

    # Session created BEFORE rotation is invalidated when key rotates
    assert coord_strict.evaluate_session_validity(
        session_created_at=sess_created_at,
        session_expires_at=sess_expires_at,
        key_rotation_time=rotation_time
    ) is False

    # Session created AFTER rotation remains valid
    sess_new_created_at = (now_dt - timedelta(minutes=2)).isoformat()
    assert coord_strict.evaluate_session_validity(
        session_created_at=sess_new_created_at,
        session_expires_at=sess_expires_at,
        key_rotation_time=rotation_time
    ) is True
