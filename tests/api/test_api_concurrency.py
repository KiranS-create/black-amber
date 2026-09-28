import base64
import concurrent.futures
import threading
import pytest
from fastapi.testclient import TestClient

from apps.api.config import config
from apps.api.main import app
from apps.api.orchestrator import default_orchestrator
from apps.api.security import default_rate_limiter, SlidingWindowRateLimiter
from demo.end_to_end import create_sample_pdf

client = TestClient(app)

def create_valid_pdf_b64() -> str:
    pdf_bytes = create_sample_pdf()
    return base64.b64encode(pdf_bytes).decode("utf-8")

# =====================================================================
# 1. CONCURRENT RELEASE CREATIONS
# =====================================================================

def test_concurrent_release_creations():
    """
    Verify that multiple concurrent release creation requests from different threads
    execute safely without race conditions, ID collisions, or corrupted storage.
    """
    headers = {"Authorization": "Bearer token_operator_tenant_a"}
    num_concurrent = 5
    pdf_b64 = create_valid_pdf_b64()

    def _create_release(idx: int):
        # Use TestClient in each thread
        res = client.post(
            "/releases",
            headers=headers,
            json={
                "document_name": f"ConcurrentDoc_{idx}.pdf",
                "document_base64": pdf_b64,
                "issuer_id": f"HQ_CONCURRENT_{idx}",
                "recipient_ids": ["alice", "bob"]
            }
        )
        return res.status_code, res.json()

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent) as executor:
        futures = [executor.submit(_create_release, i) for i in range(num_concurrent)]
        results = [f.result() for f in futures]

    release_ids = set()
    for status_code, body in results:
        assert status_code == 200
        rel_id = body["release_id"]
        assert rel_id not in release_ids
        release_ids.add(rel_id)

    assert len(release_ids) == num_concurrent

# =====================================================================
# 2. CONCURRENT DECRYPTION ON SAME RELEASE
# =====================================================================

def test_concurrent_decryptions_on_same_release():
    """
    Verify that Alice and Bob concurrently decrypting their respective packages
    on the same release both succeed without ledger race conditions or file collision.
    """
    headers_op = {"Authorization": "Bearer token_operator_tenant_a"}
    pdf_b64 = create_valid_pdf_b64()

    # 1. Create release for alice and bob
    rel_res = client.post(
        "/releases",
        headers=headers_op,
        json={
            "document_name": "SharedRelease.pdf",
            "document_base64": pdf_b64,
            "issuer_id": "HQ_TEST",
            "recipient_ids": ["alice", "bob"]
        }
    )
    assert rel_res.status_code == 200
    release_id = rel_res.json()["release_id"]

    # 2. Concurrent decryption
    def _decrypt(recipient_id: str, token: str):
        headers = {"Authorization": f"Bearer {token}"}
        res = client.post(
            f"/releases/{release_id}/decrypt",
            headers=headers,
            json={"recipient_id": recipient_id}
        )
        return res.status_code, res.json()

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f_alice = executor.submit(_decrypt, "alice", "token_alice_tenant_a")
        f_bob = executor.submit(_decrypt, "bob", "token_bob_tenant_a")
        status_alice, body_alice = f_alice.result()
        status_bob, body_bob = f_bob.result()

    assert status_alice == 200
    assert body_alice["status"] == "SUCCESS"
    assert status_bob == 200
    assert body_bob["status"] == "SUCCESS"

    # Both must have distinct traceable artifact hashes
    assert body_alice["traceable_artifact_hash"] != body_bob["traceable_artifact_hash"]

    # 3. Ledger verification: hash chain must remain strictly unbroken
    ledger_res = client.get("/ledger/verify")
    assert ledger_res.status_code == 200
    assert ledger_res.json()["is_valid"] is True

# =====================================================================
# 3. RATE LIMITER THREAD SAFETY UNDER EXTREME CONCURRENCY
# =====================================================================

def test_rate_limiter_multithreaded_safety():
    """
    Directly verify that SlidingWindowRateLimiter is thread-safe under high concurrency,
    accurately limiting requests without race conditions or lost updates.
    """
    limiter = SlidingWindowRateLimiter()
    key = "test_concurrent_subject"
    max_requests = 50
    total_threads = 10
    calls_per_thread = 10
    total_calls = total_threads * calls_per_thread  # 100 calls

    allowed_count = 0
    denied_count = 0
    count_lock = threading.Lock()

    def _worker():
        nonlocal allowed_count, denied_count
        for _ in range(calls_per_thread):
            allowed, _ = limiter.is_allowed(key, max_requests=max_requests, window_seconds=60.0)
            with count_lock:
                if allowed:
                    allowed_count += 1
                else:
                    denied_count += 1

    with concurrent.futures.ThreadPoolExecutor(max_workers=total_threads) as executor:
        futures = [executor.submit(_worker) for _ in range(total_threads)]
        for f in futures:
            f.result()

    assert allowed_count == max_requests
    assert denied_count == total_calls - max_requests
