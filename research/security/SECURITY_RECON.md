# SIH26237 — Application Security Reconnaissance & Boundary Map
**Author**: Agent 8 (Principal Application Security Engineer & Red-Team Auditor)  
**Date**: September 2026  
**Scope**: Smart India Hackathon 26237 — Post-Quantum Document Attribution, Watermarking & Cryptographic Provenance Platform

---

## 1. Executive Reconnaissance Summary

This security reconnaissance analyzes the architectural surfaces, data flows, and trust boundaries across the SIH26237 repository. The system is designed to provide post-quantum cryptographic envelope encryption (`ML-KEM-768`), digital signature provenance (`ML-DSA-65`), mathematical traitor-tracing (`Symmetric Tardos Codes`), physical print-scan resilient watermarking (`DSSS + Reed-Solomon + ArUco`), tamper-evident audit logging (`SHA-256 Hash Chain`), and fail-closed multi-channel Bayesian evidence fusion.

Our passive and active reconnaissance identified **critical architectural trust mismatches**, **unauthenticated decryption endpoints**, **server-side private key custody**, and **evidence fusion edge cases** that violate the security policy stated in `SECURITY.md`.

---

## 2. Trust Boundary Mapping

```
                                  [ EXTERNAL UNTRUSTED ZONE ]
                                                |
               +--------------------------------+--------------------------------+
               |                                                                 |
    [ Client / Operator Browser ]                                    [ Leak Submitter / Attacker ]
    (apps/web - React 18 + Vite)                                    (Raw HTTP, Malicious Artifacts)
               |                                                                 |
~~~~~~~~~~~~~~~|~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|~~~~~~~~~~~~~~~~~~~~~~~~~~~~
               | [HTTP Boundary: CORS (* with credentials), Unauthenticated API] |
               v                                                                 v
+------------------------------------------------------------------------------------------------------------+
| CONTROL PLANE & API ORCHESTRATION (apps/api)                                                               |
|                                                                                                            |
|  - main.py: FastAPI entrypoint, correlation middleware, global error handling                              |
|  - routers/: documents, recipients, releases, leaks, analysis, evidence, system                            |
|  - orchestrator.py: Central coordinator between crypto, storage, jobs, and attribution engines            |
|  - storage.py: Filesystem Data Plane (data/artifacts) + SQLite Control Plane (data/metadata.sqlite3)       |
|  - security.py: Path sanitization, MIME detection, role boundary check (disabled by default)               |
+------------------------------------------------------------------------------------------------------------+
       |                           |                               |                        |
       | [Data Plane]              | [Crypto Boundary]             | [Traceability Bound.]  | [Ledger Boundary]
       v                           v                               v                        v
+------------------+    +-----------------------+     +------------------------+  +-------------------+
| Artifact Storage |    | Post-Quantum Core     |     | Traitor Tracing        |  | Hash-Chained      |
| (data/artifacts) |    | (core/crypto)         |     | (core/traceability)    |  | Audit Ledger      |
| Content-addressed|    | - ML-KEM-768          |     | - Symmetric Tardos     |  | (core/ledger)     |
| .bin payloads    |    | - ML-DSA-65           |     | - Cutoff t=1/(300c)    |  | Sequential SHA256 |
|                  |    | - AES-256-GCM / KW    |     | - Chernoff Bound Z     |  | Anti-replay nonce |
+------------------+    | - HKDF-SHA256         |     +------------------------+  +-------------------+
                        +-----------------------+                  |                        |
                                   |                               |                        |
                                   v                               v                        v
                        +-----------------------------------------------------------------------------+
                        | FORENSIC EVIDENCE FUSION ENGINE (core/attribution)                          |
                        |                                                                             |
                        | - Dependency Graph & Anti-Double-Counting (gamma=0.65 correlation discount) |
                        | - Attack-Aware Reliability Calibrator (PSNR, SSIM, Crop degradation)       |
                        | - Fail-Closed Decision Policy (Score >= 6.0, Margin >= 2.5, Conflict >= 5.0)|
                        | - Multi-Channel Bayes Likelihood Ratio Accumulation                         |
                        +-----------------------------------------------------------------------------+
                                                                   ^
                                                                   | [Watermark Bridge]
                                                      +------------------------+
                                                      | Watermark Pipeline     |
                                                      | (core/watermark)       |
                                                      | - ArUco Sync           |
                                                      | - Reed-Solomon ECC     |
                                                      | - DSSS 2D Modulator    |
                                                      +------------------------+
```

---

## 3. Comprehensive Boundary Analysis

### 3.1. Input Boundaries
1. **Multipart Upload Boundary (`POST /documents`, `POST /leaks`)**:
   - Accepts binary files via FastAPI `UploadFile`.
   - Files are validated via `validate_uploaded_payload()` for size (`config.max_upload_size_bytes = 50 MB`) and magic bytes (`%PDF`, `\x89PNG`, `\xff\xd8\xff`).
   - **Vulnerability**: Fallback allows `application/octet-stream` without restricting executable structures or deeply checking internal PDF/JPEG dictionary recursion.
   - **Vulnerability**: Document names provided by users or filenames in multipart headers are reflected directly into the `Content-Disposition` HTTP header in `GET /documents/{id}/download` without CRLF or quote stripping, enabling **HTTP Response Splitting / Header Injection**.

2. **Inline JSON Base64 Boundary (`POST /releases`, `POST /analyze`, `POST /leaks/analyze`)**:
   - Accepts base64 encoded document bytes directly in the JSON body.
   - **Vulnerability**: Unlike multipart uploads, inline base64 payloads bypass `validate_uploaded_payload()`. A client sending a 500 MB base64 string in JSON causes FastAPI and Python's `base64.b64decode()` to allocate gigabytes of heap memory, triggering **Denial of Service (DoS via Memory Exhaustion)**.

3. **Analysis Request Boundary (`POST /analyze`)**:
   - Accepts `leak_id` (pre-stored) or `leaked_document_base64` (inline).
   - If `leaked_document_base64` is supplied, it is auto-ingested to disk via `ingest_leak()` before any forensic verification, enabling unauthenticated disk exhaustion.

---

### 3.2. Authentication & Authorization Boundaries
1. **Zero Authentication on Decryption (`POST /releases/{release_id}/decrypt`)**:
   - The endpoint expects `{"recipient_id": "bob"}`.
   - There is NO authentication token, signature verification of caller, or password.
   - Any caller on the network can decrypt any release for any recipient!

2. **Server-Side Private Key Custody (Oracle Exploit)**:
   - In `core/recipient.py`, `RecipientRegistry` stores complete `Recipient` instances containing `kem_keypair.private_key_bytes` (ML-KEM secret key) and `dsa_keypair.private_key_bytes` (ML-DSA secret key).
   - When `/releases/{release_id}/decrypt` is called, the server uses the victim recipient's private key to decapsulate, generate the traceable document, sign an `EvidenceEvent` with the recipient's private key, and write it to the ledger.
   - **Critical Threat**: An attacker can force the server to decrypt a document on behalf of an innocent user (e.g. Alice), generate Alice's watermarked copy, leak it, and the system will falsely attribute the leak to Alice with a genuine ML-DSA-65 signature on the ledger as "indisputable proof"!
   - **Policy Violation**: Directly violates `SECURITY.md` Section 4: *"Key Isolation: Recipient private keys are strictly local and never exposed or stored on the distribution server."*

3. **Insecure Role Boundary Check (`apps/api/security.py`)**:
   - `verify_role_boundary` checks `X-API-Role` header.
   - `config.require_role_header` is `False` by default (disabled).
   - When enabled, it merely checks `x_api_role in ["authority", "recipient", "auditor", "system"]` without any cryptographic authentication, API key, or HMAC token. An attacker can set `X-API-Role: system` to bypass all checks.

4. **Insecure Direct Object Reference (IDOR)**:
   - `GET /releases/{release_id}/packages/{recipient_id}`: Any client can fetch any recipient's encrypted package.
   - `GET /documents/{document_id}/download`: Any client can download any registered master document.

---

### 3.3. Cryptographic Boundaries
1. **Envelope Encryption & Key Derivation**:
   - Document key ($K_{doc}$) is generated via `os.urandom(32)` (AES-256).
   - Encapsulation is performed via genuine FIPS 203 (`ML-KEM-768`).
   - Domain-separated wrapping key derived via standard HKDF-SHA256 incorporating `protocol_version`, `algorithm_id`, `release_id`, `document_id`, `recipient_id`.
   - Document key wrapped with authenticated release context.
   - Document encrypted with AES-256-GCM with associated data `DOC-RELEASE:{release_id}:{document_id}`.
   - **Strength**: Cryprographic key derivation and encapsulation structures are mathematically sound and post-quantum secure.

2. **Hardcoded Master Fallback Keys**:
   - `core/traceability/provider.py`:
     - Line 91: `DEFAULT_SECRET_KEY = b"SIH26237-TRACEABILITY-PROTOTYPE-HMAC-KEY-V1"`
     - Line 259: `DEFAULT_SECRET_KEY = b"SIH26237-TARDOS-PROVIDER-SECRET-KEY-V1"`
   - `core/traceability/tardos.py`:
     - Line 49: `DEFAULT_MASTER_KEY = b"SIH26237-TARDOS-SYMMETRIC-MASTER-KEY-V1"`
   - **Risk**: If the server runs without explicitly injecting an external KMS key, these hardcoded constants are used. An attacker who clones the repo can generate valid HMAC signature tokens for arbitrary documents and precalculate all Tardos biases and codebooks.

---

### 3.4. Evidence & Attribution Fusion Boundaries
1. **Contradiction Disappearance Bug (False Attribution Risk)**:
   - In `core/attribution/fusion.py` (lines 254-263):
     ```python
     if (
         len(sorted_candidates) > 1
         and runner_up_score >= self.policy.conflict_runnerup_threshold
         and separation_margin < self.policy.min_separation_margin
     ):
         return FusedAttributionResult(state=AttributionState.CONFLICT, ...)
     ```
   - If candidate A has score 12.0 and candidate B has a verified ML-DSA-65 provenance signature with score 7.0:
     - `runner_up_score = 7.0 >= 5.0` (conflict threshold met).
     - However, `separation_margin = 12.0 - 7.0 = 5.0 >= 2.5` (min separation threshold met).
     - The engine treats this as sufficient separation and attributes to Candidate A, ignoring Candidate B's verified signature!
     - This breaks the fundamental safety axiom: *Two reliable independent sources for different recipients must trigger CONFLICT even if one score is larger.*

2. **Floating-Point NaN / Infinity Injection**:
   - `candidate_scores: Dict[str, float]` and `log_likelihood_ratio: float`.
   - In `compute_fused_candidate_scores`: `candidate_scores[c] += max(0.0, max_contrib)`.
   - In Python, `max(float('nan'), 0.0)` is `nan`.
   - If `float('inf')` is injected for a candidate, `inf >= 12.0` evaluates to True, allowing an unvalidated source to force a `HIGH` confidence attribution if not strictly sanitized.

3. **TargetBinding Isolation**:
   - `TargetBinding.matches()` validates `(document_id, release_id, artifact_hash)` across observations.
   - `EvidenceDependencyGraph.validate_bundle_binding()` detects cross-document contamination and correctly abstains when bindings clash.

---

### 3.5. Storage & Artifact Boundaries
1. **Filesystem Content-Addressed Storage**:
   - Stored in `data/artifacts/art_{type}_{hash}_{uuid}.bin`.
   - Filenames are sanitized with `sanitize_path()`.
   - Direct path traversal via `..` in artifact IDs is blocked.
2. **SQLite Control Plane Metadata**:
   - Stored in `data/metadata.sqlite3`.
   - Uses parameterized SQL statements (`?`), mitigating classical SQL injection.

---

### 3.6. Frontend / Backend Trust Boundaries
1. **CORS Misconfiguration (`apps/api/main.py`)**:
   - `allow_origins=["*"]` combined with `allow_credentials=True`.
   - Modern browsers and W3C fetch specifications disallow `Access-Control-Allow-Origin: *` when credentials (cookies, authorization headers) are transmitted. In Starlette/FastAPI, this creates CSRF and credential exposure vulnerabilities.
2. **Silent Mock Fallback (`apps/web/src/services/api.ts`)**:
   - If the backend is down or any request times out (>1500ms), the frontend silently switches to `mockData.ts` and renders simulated attribution results and mock ledger status.
   - Operators can be misled into believing an analysis was executed against the real cryptographic core when it was actually evaluated by local frontend mock heuristics.
3. **Hardcoded API URL**:
   - `const API_BASE = 'http://localhost:8000'` in `apps/web/src/services/api.ts` and `apps/web/src/App.tsx`.
   - In deployment, the frontend cannot be pointed to an HTTPS reverse proxy without editing source code.

---

## 4. Summary Matrix of Discovered Vulnerabilities

| ID | Title | Affected Area | Severity |
|---|---|---|---|
| SEC-01 | Unauthenticated Decryption Endpoint & Key Custody Failure | `apps/api/routers/releases.py`, `core/recipient.py` | **CRITICAL** |
| SEC-02 | Contradiction Disappearance in Evidence Fusion (False Accusation) | `core/attribution/fusion.py` | **HIGH** |
| SEC-03 | Unrestricted Resource Consumption via Inline Base64 Uploads | `apps/api/orchestrator.py`, `apps/api/routers/analysis.py` | **HIGH** |
| SEC-04 | Insecure CORS Configuration (`allow_origins=["*"]` + `credentials=True`) | `apps/api/main.py` | **MEDIUM** |
| SEC-05 | Insecure Role Header Spoofing (`X-API-Role` unauthenticated) | `apps/api/security.py` | **MEDIUM** |
| SEC-06 | Hardcoded Default Master Keys for HMAC & Tardos Codebook | `core/traceability/provider.py`, `core/traceability/tardos.py` | **MEDIUM** |
| SEC-07 | Content-Disposition Header Injection / HTTP Response Splitting | `apps/api/routers/documents.py` | **MEDIUM** |
| SEC-08 | Insecure Direct Object Reference (IDOR) on Packages & Artifacts | `apps/api/routers/releases.py`, `apps/api/routers/documents.py` | **MEDIUM** |
| SEC-09 | Silent Mock Data Fallback Masking Network/Backend Failures | `apps/web/src/services/api.ts` | **LOW** |
| SEC-10 | Dependency Vulnerabilities in Dev Server (esbuild / vite) | `apps/web/package.json` | **LOW** |
| SEC-11 | Outdated Pillow Version with Known Vulnerabilities | Python Environment (`requirements.txt`) | **LOW** |
