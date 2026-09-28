# AegisTrace API STRIDE Threat Model & Security Analysis

**Document Version:** 1.0.0  
**Classification:** Confidential / Forensic Architecture  
**Methodology:** Microsoft STRIDE Threat Modeling Framework & OWASP API Top 10 (2023)  

---

## 1. Scope & Objective

This document analyzes threat vectors targeting the AegisTrace API layer. Because AegisTrace is a cryptographic forensic attribution system, attacks on the API seek to accomplish one of four catastrophic objectives:
1. **False Accusation:** Frame an innocent recipient for an unauthorized leak.
2. **Attribution Evasion:** Leak a protected document without the system identifying the true leaker.
3. **Forensic Evidence Tampering:** Modify or suppress cryptographic audit ledger provenance records.
4. **Data Exfiltration:** Bypass multi-tenant or recipient boundaries to steal sensitive documents.

---

## 2. STRIDE Threat Matrix & Defenses

### 2.1 Spoofing (Identity & Caller Authenticity)

| Threat ID | Threat Description | Attack Vector | Severity | Implemented Mitigation & Verification |
| :--- | :--- | :--- | :--- | :--- |
| **S-01** | **Role Header Spoofing** | Attacker sends `X-API-Role: administrator` without cryptographic credentials. | **HIGH** | Under Zero-Trust (`enforce_auth=True`), client headers are untrusted. Tokens are resolved server-side from `config.local_auth_tokens`. Unauthenticated requests yield `401 UNAUTHORIZED`. |
| **S-02** | **Recipient Impersonation** | Attacker claims to be Alice when decrypting a release package. | **CRITICAL** | `require_recipient_access` validates caller identity. On provenance submission, server cryptographically verifies ML-DSA-65 post-quantum signature against Alice's enrolled public key. |
| **S-03** | **Tenant Context Spoofing** | Tenant B attacker passes `X-Tenant-ID: tenant_a` to access Tenant A data. | **HIGH** | `get_current_actor` overrides client-supplied tenant headers using the token's authenticated server-side principal record. |

---

### 2.2 Tampering (Data & Integrity Attacks)

| Threat ID | Threat Description | Attack Vector | Severity | Implemented Mitigation & Verification |
| :--- | :--- | :--- | :--- | :--- |
| **T-01** | **Audit Ledger Event Rewriting** | Attacker attempts to alter an existing provenance event in the ledger. | **CRITICAL** | The ledger is an immutable hash chain (`TamperEvidentLedger`). Any modified bit invalidates `event_hash` and breaks downstream hashes. `GET /ledger/verify` detects tampering. |
| **T-02** | **CRLF Header Injection (HTTP Splitting)** | Attacker registers document with `\r\nX-Injected: evil` in name to split HTTP headers. | **MEDIUM** | `sanitize_header_value` strips all carriage returns, line feeds, and quotes before writing `Content-Disposition`. |
| **T-03** | **Polyglot & Executable Uploads** | Attacker uploads Windows PE (`MZ`) or script disguised as PDF to execute on server/client. | **HIGH** | `validate_uploaded_payload` performs magic-byte sniffing, checks for executable headers (`MZ`, `ELF`, `#!`), and scans for script injections, rejecting with `415 UNSUPPORTED_MEDIA_TYPE`. |
| **T-04** | **Path Traversal via Identifiers** | Attacker passes `../../etc/passwd` or `..\win.ini` in document/release IDs. | **HIGH** | Strict ID validation via `validate_id_format` enforcing `^[a-zA-Z0-9_\-\.]{1,128}$` and explicitly banning traversal sequences. |

---

### 2.3 Repudiation (Disavowing Actions)

| Threat ID | Threat Description | Attack Vector | Severity | Implemented Mitigation & Verification |
| :--- | :--- | :--- | :--- | :--- |
| **R-01** | **Decryption Disavowal** | Recipient decrypts document, leaks it, and claims they never accessed the file. | **CRITICAL** | Decryption requires client decapsulation and produces a client-signed `EvidenceEvent` with NIST FIPS 204 ML-DSA-65 post-quantum signature anchored to previous ledger state. Non-repudiation is absolute. |
| **R-02** | **Release Denial** | Issuer denies having created an unauthorized or leaked release. | **HIGH** | Release creation records issuer identity, timestamp, and document hash in signed metadata and ledger entries. |

---

### 2.4 Information Disclosure (Privacy & Boundary Leaks)

| Threat ID | Threat Description | Attack Vector | Severity | Implemented Mitigation & Verification |
| :--- | :--- | :--- | :--- | :--- |
| **I-01** | **Cross-Tenant IDOR (Insecure Direct Object Reference)** | Tenant B user passes Tenant A `document_id` or `release_id`. | **CRITICAL** | `verify_tenant_boundary` validates resource tenant against principal tenant. Cross-tenant access is rejected with `403 TENANT_BOUNDARY_VIOLATION`. Lists are automatically filtered. |
| **I-02** | **Cross-Recipient Package Theft** | Bob accesses Alice's release package endpoint `/releases/{id}/packages/alice`. | **HIGH** | `require_recipient_access` ensures recipient roles can only access packages matching their own `recipient_id`. |
| **I-03** | **Pristine Master Document Theft** | Recipient downloads clean master document to distribute without watermarks. | **CRITICAL** | `require_document_access` blocks `recipient` and `device` roles from pristine master downloads (`/documents/{id}/download`). Recipients only receive watermarked copies. |
| **I-04** | **Internal Stack Trace & Secret Leaks** | Unhandled server exceptions expose file system paths or private keys. | **MEDIUM** | Global exception handlers (`register_error_handlers`) sanitize responses into uniform `ErrorResponse` objects, stripping internal traceback lines and directory structures. |

---

### 2.5 Denial of Service (Resource & Algorithmic Exhaustion)

| Threat ID | Threat Description | Attack Vector | Severity | Implemented Mitigation & Verification |
| :--- | :--- | :--- | :--- | :--- |
| **D-01** | **API Flooding & DoS** | Malicious client overwhelms server with rapid HTTP requests. | **HIGH** | In-memory `SlidingWindowRateLimiter` enforces tiered rate limits (100 req/min general, 20 req/min crypto, 10 req/min upload). Exceeded limits return `429 RATE_LIMITED` with `Retry-After`. |
| **D-02** | **Decompression & Memory Bombs** | Attacker uploads 500 MB binary to exhaust server memory. | **HIGH** | Hard payload ceiling (`max_upload_size_bytes = 50 MB`). Over-limit uploads immediately fail with `413 PAYLOAD_TOO_LARGE`. |
| **D-03** | **Replay Flood on Ledger** | Attacker captures valid signed evidence event and replays it thousands of times. | **HIGH** | `ReplayProtectionCache` maintains a 5-minute sliding window of seen nonces and timestamps. Replays are rejected with `409 REPLAY_DETECTED`. Ledger deduplicates by `event_id`. |

---

### 2.6 Elevation of Privilege (Access Control Defeats)

| Threat ID | Threat Description | Attack Vector | Severity | Implemented Mitigation & Verification |
| :--- | :--- | :--- | :--- | :--- |
| **E-01** | **Viewer Privilege Escalation** | Read-only viewer attempts to invoke `POST /releases` or `POST /documents`. | **HIGH** | `require_role(["operator", "administrator", "system"])` checks principal's effective role set. Viewers lack mutation permissions and receive `403 FORBIDDEN`. |
| **E-02** | **Operator Identity Management Escalation** | Document operator attempts to enroll or revoke recipient cryptographic keys. | **HIGH** | `POST /recipients` and `POST /recipients/{id}/revoke` strictly require `administrator`, `authority`, or `system` role. Operator role hierarchy explicitly excludes `authority`. |
| **E-03** | **Revoked Recipient Decryption** | Revoked employee uses previously cached tokens to decrypt a new release package. | **CRITICAL** | State-machine checks in `orchestrator.decrypt_release_package` verify recipient status is `ACTIVE`. Revoked recipients are rejected with `400 INVALID_STATE`. |
