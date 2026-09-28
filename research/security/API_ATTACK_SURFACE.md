# AegisTrace — API Attack Surface & Trust Boundary Specification

**Document Version**: 1.0.0  
**Target Platform**: AegisTrace (SIH26237) — Cryptographic Attribution & Provenance Platform  
**Classification**: Red-Team Security Assessment  
**Author**: Principal Security Engineer & Red-Team Auditor  
**Date**: September 2026  

---

## 1. System Architecture & Trust Boundaries

```
[ UNTRUSTED CLIENT / CALLER ]
       |
       | (HTTP / REST)
       v
+-------------------------------------------------------------------------------+
| API Gateway & Middleware Layer (apps/api/main.py)                             |
|  - Correlation & Timing: X-Request-ID, X-Response-Time-MS                     |
|  - CORS: Controlled origins (localhost/127.0.0.1:3000, 5173, 8000)             |
|  - Global Error Handler: Uniform ErrorResponse, stack traces suppressed       |
+-------------------------------------------------------------------------------+
       |
       | Bearer Token / Role Header (X-API-Role, X-Actor-ID)
       v
+-------------------------------------------------------------------------------+
| Security & Authorization Layer (apps/api/security.py)                         |
|  - Token Resolution: local_auth_tokens validation                             |
|  - Role Boundary: authority | recipient | auditor | system                    |
|  - IDOR Guards: require_recipient_access(), require_document_access()         |
|  - Payload Validation: validate_base64_payload(), validate_uploaded_payload() |
+-------------------------------------------------------------------------------+
       |
       +--------------------+--------------------+--------------------+
       |                    |                    |                    |
       v                    v                    v                    v
+--------------+     +--------------+     +--------------+     +--------------+
| Documents    |     | Releases     |     | Forensic     |     | Tamper-      |
| & Recipient  |     | & Decryption |     | Attribution  |     | Evident      |
| Control      |     | Provenance   |     | Engine       |     | Ledger       |
+--------------+     +--------------+     +--------------+     +--------------+
```

---

## 2. API Endpoint Attack Surface Catalog

### 2.1 System & Discovery Endpoints

| Endpoint | Method | Auth Req. | Role Required | Input Parameters | Sensitive Operations | Expected Failure Modes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `/health` | `GET` | None | Public | None | Metric aggregation (ledger, docs, recipients, releases, jobs) | Returns 200 OK |
| `/capabilities` | `GET` | None | Public | None | Discloses supported cryptography, formats, and API endpoints | Returns 200 OK |
| `/ledger/verify` | `GET` | None | Public | None | Cryptographic hash-chain integrity verification from genesis | 200 OK with `is_valid: False` if compromised |

### 2.2 Document Management Endpoints

| Endpoint | Method | Auth Req. | Role Required | Input Parameters | Sensitive Operations | Expected Failure Modes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `/documents` | `POST` | Bearer / Role | `authority`, `system` | Multipart Form: `file: UploadFile`, `document_name: Optional[str]`, `document_id: Optional[str]` | Data Plane storage, SHA-256 hash indexing | 400 (empty payload), 413 (>50MB), 415 (executable MIME), 401 (no auth), 403 (wrong role) |
| `/documents` | `GET` | Bearer / Role | `authority`, `auditor`, `system` | None | Enumerates master document metadata | 401 Unauthorized, 403 Forbidden |
| `/documents/{document_id}` | `GET` | Bearer / Role | `authority`, `auditor`, `system` | Path: `document_id: str` | Reads master document metadata | 404 (not found), 401 (unauthorized), 403 (forbidden) |
| `/documents/{document_id}/download` | `GET` | Bearer / Role | `authority`, `auditor`, `system` | Path: `document_id: str` | Exfiltrates unencrypted master document binary | 404 (not found), 401 (unauthorized), 403 (forbidden, IDOR guard) |

### 2.3 Recipient Management Endpoints

| Endpoint | Method | Auth Req. | Role Required | Input Parameters | Sensitive Operations | Expected Failure Modes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `/recipients` | `POST` | Bearer / Role | `authority`, `system` | JSON: `name: str`, `recipient_id: Optional[str]` | Generates ML-KEM-768 and ML-DSA-65 post-quantum keypairs | 422 (missing name), 401 (unauthorized), 403 (forbidden) |
| `/recipients` | `GET` | Bearer / Role | Any Authenticated | None | Enumerates public identities and public keys | 401 Unauthorized |
| `/recipients/{recipient_id}` | `GET` | Bearer / Role | Any Authenticated | Path: `recipient_id: str` | Reads public identity and public keys | 404 (not found), 401 (unauthorized) |

### 2.4 Cryptographic Release & Decryption Endpoints

| Endpoint | Method | Auth Req. | Role Required | Input Parameters | Sensitive Operations | Expected Failure Modes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `/releases` | `POST` | Bearer / Role | `authority`, `system` | JSON: `CreateReleaseRequest` (document_id, recipient_ids, tardos_enabled, coalition_size, carrier_budget) | AES-256-GCM encryption, ML-KEM-768 encapsulation, Tardos codebook generation | 400 (invalid payload, insufficient carrier capacity), 404 (doc/recipient missing), 401, 403 |
| `/releases` | `GET` | Bearer / Role | `authority`, `auditor`, `system` | None | Lists release packages and recipient lists | 401 Unauthorized, 403 Forbidden |
| `/releases/{release_id}` | `GET` | Bearer / Role | `authority`, `auditor`, `system` | Path: `release_id: str` | Reads release metadata and encapsulation capsules | 404 Not Found, 401, 403 |
| `/releases/{release_id}/packages/{recipient_id}` | `GET` | Bearer / Role | Designated `recipient`, `authority`, `system` | Path: `release_id: str`, `recipient_id: str` | Retrieves isolated recipient ciphertext and ML-KEM capsule (IDOR-guarded) | 404 Not Found, 401, 403 (cross-recipient IDOR) |
| `/releases/{release_id}/decrypt` | `POST` | Bearer / Role | Designated `recipient`, `system` | Path: `release_id: str`, JSON: `recipient_id: str` | Simulated local oracle: decapsulates key, decrypts ciphertext, embeds watermark, signs provenance | 400 (AES tag mismatch, wrong recipient), 404, 401, 403 (unauthorized decryption) |
| `/releases/{release_id}/provenance` | `POST` | Bearer / Role | Designated `recipient`, `system` | Path: `release_id: str`, JSON: `EvidenceEvent` | Verifies ML-DSA-65 signature, checks document/release binding and replay, appends to ledger | 400 (bad signature, replay, chain break), 401, 403 (forged provenance) |

### 2.5 Leak Ingestion & Forensic Attribution Endpoints

| Endpoint | Method | Auth Req. | Role Required | Input Parameters | Sensitive Operations | Expected Failure Modes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `/leaks` | `POST` | Bearer / Role | `authority`, `auditor`, `system` | Multipart Form: `file: UploadFile`, `suspected_document_id`, `suspected_release_id` | Stores suspected leak artifact, indexes under LEAK_ARTIFACT_HASH | 400 (empty payload), 413 (>50MB), 415 (executable), 401, 403 |
| `/leaks/{leak_id}` | `GET` | Bearer / Role | `authority`, `auditor`, `system` | Path: `leak_id: str` | Reads leak artifact metadata | 404 Not Found, 401, 403 |
| `/leaks/{leak_id}/download` | `GET` | Bearer / Role | `authority`, `auditor`, `system` | Path: `leak_id: str` | Downloads raw leak binary payload | 404 Not Found, 401, 403 |
| `/analyze` | `POST` | Bearer / Role | `authority`, `auditor`, `system` | JSON: `AnalyzeRequest` (leak_id, leaked_document_base64, expected_release_id, attack_telemetry, async_execution) | DSSS watermark recovery, Tardos traitor tracing, Bayesian multi-channel fusion | 400 (malformed base64, missing inputs), 404 (leak not found), 401, 403 |
| `/analysis` | `GET` | Bearer / Role | `authority`, `auditor`, `system` | None | Lists forensic analysis jobs and outcomes | 401 Unauthorized, 403 Forbidden |
| `/analysis/{analysis_id}` | `GET` | Bearer / Role | `authority`, `auditor`, `system` | Path: `analysis_id: str` | Retrieves forensic decision, scores, and channel telemetry | 404 Not Found, 401, 403 |

### 2.6 Evidence & Provenance Audit Endpoints

| Endpoint | Method | Auth Req. | Role Required | Input Parameters | Sensitive Operations | Expected Failure Modes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `/evidence/{release_id}` | `GET` | Bearer / Role | `authority`, `auditor`, `system` | Path: `release_id: str` | Retrieves all ledger events for a release | 401 Unauthorized, 403 Forbidden |
| `/evidence/decryption-events` | `POST` | Bearer / Role | Designated `recipient`, `system` | JSON: `EvidenceEvent` | Cryptographic signature verification (ML-DSA-65), ledger append | 400 (bad signature, replay, broken hash chain), 401, 403 |
| `/leaks/analyze` | `POST` | None (Legacy) | Public / Backward Compatibility | JSON: `LegacyAnalyzeLeakRequest` | Synchronous direct leak analysis returning raw `AttributionResult` | 400 (malformed base64) |

---

## 3. Threat Matrix & Vulnerability Classification

| Threat Vector | Affected Endpoints | Potential Impact | Primary Defense |
| :--- | :--- | :--- | :--- |
| **Insecure Direct Object Reference (IDOR)** | `GET /releases/{id}/packages/{recipient_id}`, `POST /releases/{id}/decrypt` | Recipient exfiltrates another party's package or decrypts unauthorized materials | `require_recipient_access()` verifies authenticated actor ID matches target recipient |
| **Header Injection / CRLF Splitting** | `GET /documents/{id}/download`, `GET /leaks/{id}/download` | HTTP response splitting, session fixation via Set-Cookie injection | `sanitize_header_value()` strips `\r`, `\n`, quotes, semicolons |
| **Path Traversal** | Artifact storage, document downloads | Arbitrary filesystem read/write outside storage sandbox | `sanitize_path()` rejects directory traversal (`..`, absolute paths) |
| **Malformed Base64 DoS** | `POST /analyze`, `POST /releases` | Memory exhaustion, regex catastrophic backtracking | `validate_base64_payload()` validates length, charset regex, and bounds before full decoding |
| **State-Machine Inconsistency** | `POST /releases/{id}/provenance`, `POST /releases/{id}/decrypt` | Replayed provenance events, unauthorized ledger insertion | Strict document/release ID binding, ML-DSA-65 signature verification, anti-replay nonce pinning |
| **Evidence Poisoning** | `POST /analyze`, `POST /evidence/decryption-events` | Framing innocent recipients via forged LLR, NaN/Inf score injection | `sanitize_evidence_observation()`, fail-closed threshold ($Z \ge 11.40$), contradiction detection |
| **CORS Misconfiguration** | All endpoints | Cross-site unauthorized invocation from malicious origins | Whitelist restricted to local development origins; credentials handled securely |
