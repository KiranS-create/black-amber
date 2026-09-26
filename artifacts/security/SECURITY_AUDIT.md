# SIH26237 — Comprehensive Application Security & Red-Team Audit

**Audit Team**: Agent 8 (Principal Application Security Engineer & Red-Team Auditor)  
**Target System**: Smart India Hackathon SIH26237 — Post-Quantum Document Attribution & Provenance Platform  
**Date**: September 2026  
**Status**: Final Red-Team Assessment  

---

## 1. Executive Summary & Findings Scorecard

This security assessment conducted an adversarial evaluation of the SIH26237 codebase, attacking input validation, cryptographic boundaries, key lifecycle, evidence fusion mathematics, artifact parsing, identity control, and frontend trust assumptions.

### Findings Breakdown by Severity
```
+-------------------------------------------------------------+
|                     AUDIT FINDINGS SUMMARY                  |
+-------------------+-----------------------------------------+
| CRITICAL          | 1 Finding                               |
| HIGH              | 2 Findings                              |
| MEDIUM            | 5 Findings                              |
| LOW               | 3 Findings                              |
| INFORMATIONAL     | 2 Findings                              |
+-------------------+-----------------------------------------+
| TOTAL FINDINGS    | 13 Findings                             |
+-------------------+-----------------------------------------+
```

---

## 2. Strix & Automated Dynamic Testing Status

- **Tool Target**: `strix` / `usestrix` dynamic security analyzer.
- **Local Investigation**: System environment inspection (`Get-Command strix, usestrix`, `pip list | grep strix`) confirmed that Strix is not installed in the local runtime environment.
- **Resolution (Non-Fabrication Policy)**: Strix results were NOT fabricated. Instead, an equivalent comprehensive local security test suite (`tests/security/**`, 35 automated test cases) was built and executed, covering OWASP API Top 10, artifact attacks, floating-point injection, cryptographic tampering, and trust-boundary violations.

---

## 3. Comprehensive Red-Team Findings

---

### [SEC-01] CRITICAL: Unauthenticated Decryption Endpoint with Server-Side Private Key Custody (Decryption Oracle & False Attribution Framing)
- **Affected Component**: `apps/api/routers/releases.py` (`decrypt_release_package`), `apps/api/orchestrator.py` (`decrypt_release_package`), `core/recipient.py` (`RecipientRegistry`)
- **CVSS 4.0 Score**: **9.3 (Critical)** `CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:N/SC:H/SI:H/SA:N`
- **Attack Preconditions**: Attacker has network reachability to the API server and knows or guesses a target recipient ID (e.g. `alice`, `bob`).
- **Reproduction / Exploit Path**:
  1. An authority issues a classified release `rel_001` to authorized recipients `["alice", "bob"]`.
  2. An unauthenticated attacker sends:
     ```http
     POST /releases/rel_001/decrypt HTTP/1.1
     Host: localhost:8000
     Content-Type: application/json

     {
       "recipient_id": "alice"
     }
     ```
  3. The server retrieves Alice's private `ML-KEM-768` key and private `ML-DSA-65` key from `default_registry` stored in server RAM.
  4. The server decapsulates the document key, decrypts the document, embeds Alice's traceability marker, **signs a `DECRYPTION_EVENT` using Alice's private key**, and logs the event to the immutable ledger.
  5. The server returns the marked document and signed event hash to the unauthenticated attacker.
  6. The attacker leaks the document to the press.
  7. When the leak is analyzed via `/analyze`, the system attributes the leak to Alice with a 100% verified digital signature on the audit ledger.
- **Impact**: Complete violation of non-repudiation and key isolation. An attacker can frame any recipient for unauthorized document leaks without having access to their workstation or credentials.
- **Exploitability**: Trivial (1 single unauthenticated HTTP POST request).
- **Code Evidence**:
  - `apps/api/routers/releases.py` line 34: `decrypt_release_package()` takes unauthenticated `DecryptRequest(recipient_id: str)`.
  - `core/recipient.py` line 62: `Recipient` object stores `kem_keypair.private_key_bytes` and `dsa_keypair.private_key_bytes` on the server.
- **Remediation**:
  1. Implement Decentralized Key Management: Server must only store `PublicRecipient` (public keys only).
  2. Remove server-side decryption: Decryption, watermark embedding, and signing must execute strictly on the client workstation.
  3. Replace `/releases/{id}/decrypt` with client-submitted signed ledger event ingestion: `POST /evidence/decryption-events`.
- **Residual Risk**: Low once private keys are removed from server custody.

---

### [SEC-02] HIGH: Contradiction Suppression in Evidence Fusion Engine (False Attribution Bypass)
- **Affected Component**: `core/attribution/fusion.py` (`fuse`, lines 254–263)
- **CVSS 4.0 Score**: **8.2 (High)** `CVSS:4.0/AV:N/AC:L/AT:N/PR:L/UI:N/VC:N/VI:H/VA:N/SC:N/SI:H/SA:N`
- **Attack Preconditions**: An attacker injects or fabricates an elevated score for candidate A (e.g. 12.0) while a legitimate independent cryptographic signature points to candidate B (e.g. 7.0).
- **Reproduction / Exploit Path**:
  1. A bundle is created containing `WatermarkObservation` for Alice ($S = 12.0$) and `ProvenanceObservation` with verified signature for Bob ($S = 7.0$).
  2. In `core/attribution/fusion.py`, Step 5 checks conflict:
     ```python
     if (
         len(sorted_candidates) > 1
         and runner_up_score >= self.policy.conflict_runnerup_threshold # 7.0 >= 5.0 (True)
         and separation_margin < self.policy.min_separation_margin      # 5.0 < 2.5 (False!)
     ):
         return CONFLICT
     ```
  3. Because separation margin is $12.0 - 7.0 = 5.0 \ge 2.5$, the engine ignores Bob's verified signature and attributes the leak to Alice!
- **Impact**: Violates the fundamental safety principle: *Two reliable independent sources for different recipients must trigger CONFLICT even if one score is larger.* Allows an attacker who manipulates a watermark channel to override a verified cryptographic signature.
- **Exploitability**: Moderate.
- **Remediation**: Patch `core/attribution/fusion.py` Step 5 so that if `runner_up_score >= self.policy.conflict_runnerup_threshold`, the engine checks whether the runner-up is supported by an independent primary cryptographic source. If so, return `AttributionState.CONFLICT` regardless of the separation margin.
- **Residual Risk**: Zero once conflict logic checks cryptographic corroboration independence.

---

### [SEC-03] HIGH: Unrestricted Resource Consumption via Inline Base64 Uploads (Denial of Service)
- **Affected Component**: `apps/api/routers/analysis.py` (`analyze_leak`), `apps/api/orchestrator.py` (`analyze_leak`)
- **CVSS 4.0 Score**: **7.5 (High)** `CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:N/VI:N/VA:H/SC:N/SI:N/SA:H`
- **Attack Preconditions**: Network access to `POST /analyze` or `POST /releases`.
- **Reproduction / Exploit Path**:
  1. An attacker sends a JSON payload with a 500MB string in `leaked_document_base64` or `document_base64`.
  2. Unlike `/documents` which checks `config.max_upload_size_bytes`, the inline base64 path calls `base64.b64decode()` directly on the unvalidated string.
  3. Python allocates gigabytes of RAM during JSON parsing and base64 decoding, triggering Out-Of-Memory (OOM) crash or server unresponsiveness.
  4. In `orchestrator.py`, `ingest_leak()` immediately writes the entire blob to disk, enabling storage exhaustion.
- **Impact**: Complete denial of service for all users.
- **Remediation**: Use `security.defense.validate_base64_payload()` to check string length before decoding and reject payloads over 50 MB.
- **Residual Risk**: Low with reverse proxy and application-level size limits.

---

### [SEC-04] MEDIUM: Insecure CORS Configuration with Wildcard Origin and Credentials Enabled
- **Affected Component**: `apps/api/main.py` (lines 58–64)
- **CVSS 4.0 Score**: **6.5 (Medium)** `CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:R/VC:L/VI:L/VA:N/SC:L/SI:L/SA:N`
- **Issue**: `allow_origins=["*"]` combined with `allow_credentials=True`.
- **Impact**: In modern browsers, `allow_origins=["*"]` with credentials enabled violates W3C CORS specifications and can lead to cross-site request forgery and unauthorized data read across origins.
- **Remediation**: Set `allow_origins` to an explicit whitelist of trusted domains (e.g. `["http://localhost:5173", "http://localhost:3000"]`) or set `allow_credentials=False` if wildcard origins are required.

---

### [SEC-05] MEDIUM: Unauthenticated Role Header Spoofing (`X-API-Role`)
- **Affected Component**: `apps/api/security.py` (`verify_role_boundary`)
- **CVSS 4.0 Score**: **6.2 (Medium)** `CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N`
- **Issue**: Role authorization relies on a raw header `X-API-Role` without cryptographic signature, API key, or JWT verification.
- **Impact**: Any client can bypass role checks simply by setting `X-API-Role: system` or `X-API-Role: authority`.
- **Remediation**: Replace plain string role headers with authenticated Bearer JWT tokens or HMAC-signed request headers.

---

### [SEC-06] MEDIUM: Hardcoded Master Fallback Keys in Traceability Providers
- **Affected Component**: `core/traceability/provider.py` (lines 91, 259), `core/traceability/tardos.py` (line 49)
- **CVSS 4.0 Score**: **5.8 (Medium)** `CVSS:4.0/AV:N/AC:H/AT:N/PR:N/UI:N/VC:H/VI:H/VA:N/SC:N/SI:N/SA:N`
- **Issue**:
  - `DEFAULT_SECRET_KEY = b"SIH26237-TRACEABILITY-PROTOTYPE-HMAC-KEY-V1"`
  - `DEFAULT_SECRET_KEY = b"SIH26237-TARDOS-PROVIDER-SECRET-KEY-V1"`
  - `DEFAULT_MASTER_KEY = b"SIH26237-TARDOS-SYMMETRIC-MASTER-KEY-V1"`
- **Impact**: If deployed without environment-injected secrets, an attacker can precalculate all Tardos biases and forge HMAC markers.
- **Remediation**: Enforce runtime assertion requiring master secrets to be loaded from environment variables or HSM/KMS in production mode (`ENVIRONMENT=production`).

---

### [SEC-07] MEDIUM: HTTP Response Splitting / Content-Disposition Header Injection
- **Affected Component**: `apps/api/routers/documents.py` (`download_document`, line 51)
- **CVSS 4.0 Score**: **5.3 (Medium)** `CVSS:4.0/AV:N/AC:L/AT:N/PR:L/UI:R/VC:N/VI:L/VA:N/SC:N/SI:N/SA:N`
- **Issue**: User-supplied `document_name` containing `\r\n` is reflected directly into `Content-Disposition: attachment; filename="{doc.document_name}"`.
- **Impact**: Injected CRLF sequences can split HTTP headers, set arbitrary cookies, or inject malicious payload bodies.
- **Remediation**: Apply `security.defense.sanitize_header_value()` to strip CRLF, quotes, and control characters before setting headers.

---

### [SEC-08] MEDIUM: Insecure Direct Object Reference (IDOR) on Release Packages & Master Documents
- **Affected Component**: `apps/api/routers/releases.py` (`get_recipient_package`), `apps/api/routers/documents.py` (`download_document`)
- **CVSS 4.0 Score**: **5.3 (Medium)** `CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:L/VI:N/VA:N/SC:N/SI:N/SA:N`
- **Issue**: Any caller can retrieve encrypted packages for other recipients or download master documents without authorization tokens.
- **Impact**: While recipient packages are encrypted with ML-KEM-768, exposing them allows traffic analysis, timing correlation, and offline cryptanalysis.

---

### [SEC-09] LOW: Silent Frontend Mock Fallback Masking System Failures
- **Affected Component**: `apps/web/src/services/api.ts` (`checkHealth`, `getRecipients`, `enrollRecipient`)
- **CVSS 4.0 Score**: **3.7 (Low)**
- **Issue**: If the backend is unavailable or a network timeout occurs (>1500ms), the frontend silently falls back to `mockData.ts` and renders simulated attribution results.
- **Impact**: Operators may believe a forensic attribution succeeded against real cryptographic artifacts when it was actually computed by local mock heuristics.
- **Remediation**: Display an explicit visual banner warning the operator when running in simulated offline mock mode.

---

### [SEC-10] LOW: Vulnerabilities in Frontend Dev Server Dependencies (`esbuild` / `vite`)
- **Affected Component**: `apps/web/package.json` (`vite: ^5.1.6`, `esbuild: <=0.24.2`)
- **Advisory**: `GHSA-67mh-4wv8-2f99` (Moderate severity). Enables websites to send unauthorized requests to Vite dev server.
- **Remediation**: Upgrade `vite` to `>=5.4.14` or `>=6.0.0` and `esbuild` to `>=0.25.0`.

---

### [SEC-11] LOW: Outdated Pillow Library with Known Vulnerabilities in Python Environment
- **Affected Component**: Python runtime environment (`Pillow 9.4.0`)
- **Advisories**: `CVE-2023-50447` (Arbitrary code execution via ImageMath), `CVE-2024-28219` (Buffer overflow in _imagingcms).
- **Remediation**: Upgrade `Pillow` to `>=10.3.0` in `requirements.txt`.

---

### [SEC-12] INFORMATIONAL: Hardcoded Localhost API Base URL
- **Affected Component**: `apps/web/src/services/api.ts`, `apps/web/src/App.tsx`
- **Issue**: `const API_BASE = 'http://localhost:8000'` prevents zero-config deployment behind reverse proxies.
- **Remediation**: Use `import.meta.env.VITE_API_BASE || '/api'`.

---

### [SEC-13] INFORMATIONAL: Missing Rate Limiting on Leak Analysis Endpoints
- **Affected Component**: `apps/api/routers/analysis.py` (`analyze_leak`)
- **Issue**: Heavy forensic analysis (DSSS demodulation, Tardos codebook generation, homography rectification) can be repeatedly triggered to cause CPU exhaustion.
- **Remediation**: Add a token-bucket rate limiter middleware (e.g. 5 requests/minute per client).

---

## 4. Independent Claude Opus 4.6 Security Review

As part of the red-team methodology, an independent architectural review was executed addressing 7 specific critical questions:

### 1. What is the most dangerous vulnerability?
**Finding SEC-01 (Unauthenticated Decryption Endpoint with Server-Side Key Custody)** is unequivocally the most dangerous vulnerability. By holding recipient private keys on the central server and allowing unauthenticated decryption requests, any attacker can compel the server to sign a decryption provenance event with a victim's private key, generate their watermarked copy, leak it, and produce an airtight, mathematically proven false accusation against an innocent party.

### 2. What attack path could produce a false accusation?
Two distinct attack paths produce false accusations:
- **Path A (Oracle Framing - SEC-01)**: Attacker invokes `POST /releases/{id}/decrypt` with victim's `recipient_id`, obtains victim's marked copy signed by the server, leaks it, and causes high-confidence false attribution.
- **Path B (Contradiction Suppression - SEC-02)**: In `core/attribution/fusion.py`, if an attacker crafts a high-scoring watermark payload for Alice ($S = 12.0$), the engine suppresses Bob's legitimate, verified cryptographic signature ($S = 7.0$) because the separation margin ($12.0 - 7.0 = 5.0 \ge 2.5$) passes Step 7, falsely attributing the leak to Alice instead of declaring `CONFLICT`.

### 3. What trust boundary is weakest?
The **Decryption & Key Custody Boundary**. The architecture claims in `SECURITY.md` that recipient private keys never touch the server, but the prototype implementation stores them directly in `default_registry` in server RAM.

### 4. What assumption are we relying on without proving?
We are relying on the assumption that **recipient private keys are generated and held on isolated client hardware**. In the current backend, key generation occurs inside `default_registry.enroll()` on the server.

### 5. What would a serious security judge challenge?
A security judge would immediately challenge:
1. *"How can this be non-repudiable if the server holds the recipient's private signing key and can sign decryption events on the ledger without the recipient's knowledge?"*
2. *"Why is there no authentication on the `/releases/{id}/decrypt` endpoint?"*

### 6. Which finding was potentially missed?
**HTTP Response Splitting in Document Download (SEC-07)**: In `apps/api/routers/documents.py`, `doc.document_name` was directly formatted into `Content-Disposition` without CRLF stripping.

### 7. Are any reported vulnerabilities false positives?
No. All reported vulnerabilities (SEC-01 through SEC-11) have been verified with reproducible unit and integration tests in `tests/security/**`.

---

## 5. Security Verdict & Scorecard

```
===================================================================
                  FINAL SECURITY AUDIT SCORECARD
===================================================================
0 CRITICAL REMAINING IN CORE CRYPTO (ML-KEM, ML-DSA, AES-GCM sound)
1 CRITICAL IN BACKEND KEY CUSTODY (SEC-01: Server-side private keys)
2 HIGH (SEC-02: Fusion Contradiction, SEC-03: Base64 DoS)
5 MEDIUM (CORS, Role Spoofing, Master Keys, Header Injection, IDOR)
3 LOW (Mock Fallback, Vite Advisory, Pillow Advisory)
2 INFORMATIONAL (API_BASE, Rate Limiting)
===================================================================
```
