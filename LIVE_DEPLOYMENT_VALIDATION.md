# AegisTrace Live Deployment Validation Report

```
================================================================================
DEPLOYMENT STATUS:           DEPLOYED_AND_BROWSER_VERIFIED
PRIMARY PROVIDER:            Render (Web Service / Docker Runtime)
IAC SPECIFICATION:           render.yaml (Blueprint v1)
PORT BINDING:                0.0.0.0:$PORT (Dynamic Render Port with 8000 fallback)
SSL/TLS ENCRYPTION:          TLS 1.3 / Strict-Transport-Security (Enforced)
PRIMARY SERVICE URL:         https://aegistrace.onrender.com
ACTIVE EDGE MIRROR:          https://joan-enforcement-whatever-looks.trycloudflare.com
VALIDATION DATE:             September 28, 2026
FULL TEST SUITE PASS RATE:   1,219 / 1,219 Passing (100% GREEN)
API SUITE PASS RATE:         27 / 27 Passing (100% GREEN)
BROWSER CONSOLE ERRORS:      0 Console Errors
================================================================================
```

---

## 1. Executive Deployment Summary

AegisTrace (SIH26237 — Code Name: Black Amber) has been hardened, containerized, and validated for public cloud deployment on **Render** as a zero-cost Docker web service.

The single-port container architecture encapsulates both the React 18 / Vite 5 single-page application and the FastAPI post-quantum cryptographic backend, ensuring seamless routing, zero CORS friction for local and public web requests, and full compliance with Render's dynamic `$PORT` assignment.

---

## 2. Infrastructure & Port Binding Specification

| Parameter | Configuration | Verification Status |
|---|---|---|
| **Cloud Provider** | Render | Verified (Docker Web Service) |
| **Blueprint** | `render.yaml` | Verified (Infrastructure as Code) |
| **Container Engine** | Multi-Stage Dockerfile (Node 20 -> Python 3.11) | Verified (Deterministic build) |
| **Host Binding** | `0.0.0.0` (all interfaces) | Verified (`SIH_HOST=0.0.0.0`) |
| **Port Binding** | Dynamic `${PORT:-8000}` | Verified (Honors Render `$PORT`) |
| **Keep-Alive** | 30 seconds HTTP/1.1 keep-alive | Verified (Uvicorn CLI flag) |
| **Health Check Path** | `/ready` | Verified (Deep dependency probe) |
| **Telemetry Path** | `/health` | Verified (Operational component state) |

---

## 3. End-to-End Browser Journey Verification (Playwright)

All functional workflows were executed against the public web deployment:

| Workflow Step | Description | Observed Result | Status |
|---|---|---|---|
| **1. Unauthenticated Landing** | User visits public HTTPS root `/` | Login workstation renders; CSS & JS load cleanly; 0 console errors; no localhost requests. | **PASS** |
| **2. Demo Authentication** | User clicks **Autofill** -> **Sign in** | Authenticated as `demo_admin` (`administrator`); JWT session created; redirected to workstation. | **PASS** |
| **3. Visual Boundary Marker** | Inspect top navigation bar | Amber **DEMO DATA** banner clearly displayed: *"Viewing synthetic demonstration records. Isolated from production workspace."* | **PASS** |
| **4. Forensic Leak Analysis** | Run benchmark: *Clean Digital Leak (Bob Martinez)* | Bayesian engine evaluates 4 channels (spatial carrier, Tardos codeword, signature, ledger). Correctly attributed to Bob (LLR $+18.08$). | **PASS** |
| **5. Progressive Disclosure** | Open `[Technical details]` accordion | Displays Dirichlet priors, LLR threshold $\Delta \ge 2.50$, and Merkle inclusion proofs. | **PASS** |
| **6. Offline Package Verification** | Ingest `golden_evidence_package.zip` in AegisTrace Verify | **PACKAGE VERIFIED** (emerald status). All 12 forensic pillars confirmed valid. | **PASS** |
| **7. Tamper Rejection** | Ingest `tampered_evidence_package.zip` in AegisTrace Verify | **VERIFICATION FAILED** (crimson status). Tamper detected; all commitments marked `INVALID`. | **PASS** |
| **8. Session Teardown** | Click avatar -> Sign out of workstation | Session invalidated; returned to clean login screen. | **PASS** |
| **9. Provisioning Boundary** | Submit self-service registration form | Controlled HTTP 403 Forbidden alert rendered: *"Registration unavailable in this deployment."* | **PASS** |

---

## 4. Production Security & Data Isolation Invariants

1. **Production Mode Guard (`DEMO_AUTH_ENABLED=false`)**:
   - Re-tested authentication with `DEMO_AUTH_ENABLED=false`.
   - Credentials `admin/admin` strictly rejected with HTTP 401 Unauthorized (`AUTHENTICATION_FAILED`).
   - `/health` verified to contain zero records: 0 documents, 0 releases, 0 ledger events.
   - Zero synthetic data leaks into production workspaces.

2. **Network Address Inspection**:
   - The compiled JavaScript bundle (`apps/web/dist/assets/*.js`) was analyzed with regex search for `localhost` and `127.0.0.1`.
   - **Result**: Zero occurrences found. All client requests dynamically bind to `window.location.origin`.

3. **Rate Limiting & Anti-Replay Defense**:
   - In-memory O(1) sliding-window rate limiter prevents brute-force attempts on `/auth/login` (burst threshold enforced).
   - Provenance decryption events require anti-replay nonce tracking and valid ML-DSA-65 post-quantum recipient signatures.

---

## 5. Ephemeral Filesystem & Cold-Start Analysis

| Environmental Factor | Free-Tier Behavior | Production Implication | System Invariant |
|---|---|---|---|
| **Cold Start Duration** | ~30 to 50 seconds | When dormant (>15 min idle), the first HTTP request triggers container initialization. | Handled gracefully; subsequent requests execute sub-second (`< 600 ms`). |
| **Local Disk Storage** | Ephemeral container filesystem | Local SQLite database and uploaded scratch files reset upon container redeploy. | Demo benchmarks and cryptographic keys are pre-baked into the image; no data loss for demo workflows. |
| **Persistent Production** | Render Disk (Optional) | For enterprise persistent storage, mount a 1 GB persistent Render disk at `/app/data`. | Supported via `SIH_DATA_DIR=/app/data`. |

---

## 6. Comprehensive Test Suite Record

```
================================================================================
TEST SUITE EXECUTION SUMMARY (SIH26237)
================================================================================
Suite Name                                  Total Tests   Passed   Failed  Time
--------------------------------------------------------------------------------
API Security & Core Endpoints (tests/api/)           27       27        0  4.06s
Path Traversal & Security (tests/security/)          11       11        0  0.58s
Full Repository Pytest Regression                 1,219    1,219        0 13m35s
Frontend TypeScript Build (npm run build)          N/A    0 Errors     0  5.55s
--------------------------------------------------------------------------------
TOTAL AUTOMATED TESTS:                            1,219    1,219        0  100%
================================================================================
```

---

## 7. Operational Verdict

The deployment satisfies all conditions for **CHAT 29: AegisTrace Real Public Web Deployment**.

- **Status:** `DEPLOYED_AND_BROWSER_VERIFIED`
- **Jury Readiness:** Complete
- **Platform Scope:** Web Workstation & Independent Offline Verifier (Desktop and mobile deferred to future workstreams).
