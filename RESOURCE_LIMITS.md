# AegisTrace API Resource Limits & Operational Bounds

**Document Version:** 1.0.0  
**Classification:** Operational Specification  
**Status:** ENFORCED  

---

## 1. Overview & Objective

To prevent resource starvation, denial-of-service (DoS) conditions, and out-of-memory (OOM) failures in production air-gapped environments, AegisTrace establishes deterministic, strictly-enforced resource bounds at the API perimeter. Every parameter, array length, request frequency, and payload size is bounded before evaluation.

---

## 2. Payload & Ingestion Limits

| Resource Category | Limit | Enforcement Mechanism | Failure Response |
| :--- | :--- | :--- | :--- |
| **Max Artifact Upload Size** | **50 MB** (`52,428,800` bytes) | `validate_uploaded_payload()` checks raw bytes length | `413 PAYLOAD_TOO_LARGE` |
| **Max Base64 Decoded Payload** | **50 MB** | `validate_base64_payload(max_size_bytes)` | `400 BAD_REQUEST` / `413` |
| **Max Document Name Length** | **256 characters** | Pydantic model validation (`Field(max_length=256)`) | `422 UNPROCESSABLE_ENTITY` |
| **Max Identifier Length** | **128 characters** | Strict Regex `^[a-zA-Z0-9_\-\.]{1,128}$` | `400 INVALID_INPUT` / `403` |
| **Max Directory Search Query** | **200 characters** | FastAPI Query parameter validation | `422 UNPROCESSABLE_ENTITY` |
| **Directory Search Pagination** | **Max 100 items** per page (Default: 20) | FastAPI Query parameter (`ge=1, le=100`) | `422 UNPROCESSABLE_ENTITY` |
| **Max Recipient Coalition Size**| **10 recipients** per release | Release manager coalition cap | `400 INVALID_RELEASE` |

---

## 3. Sliding-Window Rate Limiting Tiers

Rate limiting is governed by an in-memory, thread-safe `SlidingWindowRateLimiter` configured per IP address and authenticated Bearer token:

| Tier | Window | Limit (Req / Window) | Targeted Endpoints | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **Upload Tier** | 60 seconds | **10 requests** | `POST /documents`, `POST /leaks` | Protects disk I/O, prevents storage flooding and magic-byte scanning exhaustion. |
| **Crypto Tier** | 60 seconds | **20 requests** | `POST /releases`, `POST /releases/{id}/decrypt`, `POST /analyze`, `GET /ledger/verify` | Protects CPU from compute-heavy post-quantum lattice operations (ML-KEM-768, ML-DSA-65). |
| **Default Tier** | 60 seconds | **100 requests** | All other authenticated endpoints (`GET /documents`, `GET /recipients`, `GET /directory/*`) | Standard operational API traffic. |
| **Exempt Tier** | Unmetered | Unlimited | `GET /health`, `/docs`, `/openapi.json` | Liveness and health probing must never be rate-limited. |

### Rate Limit Exceeded Behavior
When a caller exceeds their allotted tier, the API returns:
- **HTTP Status:** `429 Too Many Requests`
- **Header:** `Retry-After: <seconds_until_oldest_request_expires>`
- **Structured JSON Body:**
  ```json
  {
    "error": {
      "code": "RATE_LIMITED",
      "message": "Rate limit exceeded for tier 'crypto'. Retry after 24 seconds.",
      "details": {
        "tier": "crypto",
        "limit": 20,
        "retry_after_seconds": 24
      },
      "request_id": "req_8f1a302c"
    }
  }
  ```

---

## 4. Anti-Replay & Nonce Windowing

- **Sliding Window:** `300 seconds` (5 minutes).
- **Enforcement Cache:** `ReplayProtectionCache`.
- **Clock Skew Tolerance:** Timestamps with `|server_epoch - event_epoch| > 300` are rejected immediately.
- **Deduplication:** Repeated submission of any `event_id` or cryptographic nonce within the window returns `409 REPLAY_DETECTED`.
- **Automatic Pruning:** Expired nonces older than the 5-minute window are pruned upon subsequent evaluations to maintain $O(1)$ memory bounds.

---

## 5. Concurrency & Locking Architecture

- **Tamper-Evident Ledger:** Protected by a dedicated `threading.RLock`. Multi-threaded provenance commits are strictly serialized to ensure unbroken hash-chain progression ($H_i = \text{SHA256}(H_{i-1} \parallel E_i)$).
- **Artifact Storage Engine:** Atomic filesystem writes with temporary file swapping (`AtomicFileWriter`) prevent partial writes or corrupted files during concurrent downloads and uploads.
- **Metadata Database:** SQLite in WAL (Write-Ahead Logging) mode with `threading.RLock` ensuring zero database locks or race conditions during multi-worker processing.
