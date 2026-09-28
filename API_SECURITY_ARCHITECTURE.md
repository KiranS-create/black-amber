# AegisTrace API Security & Zero-Trust Operational Architecture

**Document Version:** 1.0.0  
**Status:** PRODUCTION HARDENED  
**Classification:** Critical Security Specification  
**Environment:** Air-Gapped / Offline-First Post-Quantum Forensic Platform  

---

## 1. Executive Summary & Zero-Trust Perimeter

AegisTrace operates on a strict **Zero-Trust Security Architecture** where the application programming interface (API) serves as an authentic, non-bypassable security boundary. Under zero-trust principles:
1. **Never Trust, Always Verify:** Every incoming request is cryptographically authenticated, authorized against an immutable role hierarchy, validated for syntax and semantic bounds, and checked against multi-tenant isolation rules.
2. **Server-Side Identity Context:** No client-supplied headers (such as `X-API-Role`, `X-Tenant-ID`, or `X-Actor-ID`) are trusted to grant privileges. Identity and authorization context are resolved exclusively server-side from cryptographically verified tokens or client signatures.
3. **Fail-Closed Default:** If an identity cannot be verified, if a tenant boundary is ambiguous, or if evidence is contradictory, the API unconditionally fails closed (`401 UNAUTHORIZED`, `403 FORBIDDEN`, or `500 INTERNAL_ERROR` with a sanitized payload).
4. **Air-Gapped Autonomous Operation:** The security perimeter requires zero external cloud dependencies, zero external key management services (KMS), and zero third-party identity provider connectivity during runtime evaluation.

```
                      +---------------------------------------+
                      |         EXTERNAL HTTP CLIENT          |
                      +---------------------------------------+
                                          |
                                          v
                      +---------------------------------------+
                      | 1. HTTP Middleware Layer              |
                      | - Sliding-Window Rate Limiting (429)  |
                      | - Correlation ID (X-Request-ID)       |
                      | - Security Headers (nosniff, CSP, etc)|
                      +---------------------------------------+
                                          |
                                          v
                      +---------------------------------------+
                      | 2. Authentication Boundary            |
                      | - Offline Bearer Token Resolution     |
                      | - Strict Server-Side Principal Binding|
                      +---------------------------------------+
                                          |
                                          v
                      +---------------------------------------+
                      | 3. Zero-Trust Authorization & RBAC    |
                      | - Role Hierarchy Matrix Check (403)   |
                      | - Scope Enforcement                   |
                      +---------------------------------------+
                                          |
                                          v
                      +---------------------------------------+
                      | 4. Multi-Tenant & IDOR Boundary       |
                      | - Strict Tenant Scoping (A vs B)      |
                      | - Recipient Ownership Enforcement     |
                      | - Master Document Access Control      |
                      +---------------------------------------+
                                          |
                                          v
                      +---------------------------------------+
                      | 5. Input Validation & Anti-Polyglot   |
                      | - Safe Regex Identifiers (1-128 chars)|
                      | - Magic Byte MIME Sniffing            |
                      | - Executable (MZ/ELF) & Script Defense|
                      +---------------------------------------+
                                          |
                                          v
                      +---------------------------------------+
                      | 6. State Machine & Anti-Replay        |
                      | - Recipient Revocation Check          |
                      | - Sliding Nonce Replay Cache (409)    |
                      +---------------------------------------+
                                          |
                                          v
                      +---------------------------------------+
                      | 7. Core Cryptographic & Ledger Layer  |
                      | - ML-KEM-768 / ML-DSA-65 / AES-256    |
                      | - Hash-Chained Tamper-Evident Ledger  |
                      +---------------------------------------+
```

---

## 2. Enterprise Role Hierarchy & Permissions

AegisTrace defines seven distinct enterprise operational roles plus legacy aliases to support backward compatibility with earlier prototypes:

| Enterprise Role | Description | Permitted Capabilities | Inherited Roles |
| :--- | :--- | :--- | :--- |
| **`administrator`** | Platform & security administrator | Recipient enrollment, key revocation, tenant configuration, audits, all operational actions | `operator`, `viewer`, `investigator`, `authority`, `auditor` |
| **`investigator`** | Forensic forensic analyst | Leak ingestion, multi-channel forensic attribution, audit ledger inspection, verification | `viewer`, `auditor` |
| **`operator`** | Document release manager | Master document registration, recipient targeting, quantum-resistant release generation | `viewer` |
| **`viewer`** | Read-only auditor | Read non-sensitive metadata, inspect sanitized telemetry, view public recipient directory | None (Leaf role) |
| **`recipient`** | Enrolled document recipient | Isolated package download, local decapsulation, signed provenance event submission | None (Leaf role) |
| **`device`** | Edge kiosk or display device | Telemetry reporting, dynamic watermark session renewal | None (Leaf role) |
| **`service_account`**| Automated ingestion agent | Automated document staging, pipeline triggering | `operator`, `viewer` |
| *`system`* | Internal root daemon | Unrestricted cross-tenant verification, internal ledger compaction | All roles |

### Role Hierarchy Definition
Role evaluation uses directed set inclusion via `has_role_permission(principal_role, required_role)`. An `operator` cannot enroll or revoke recipients; a `viewer` cannot upload documents or trigger forensic jobs; a `recipient` cannot download pristine master documents or issue releases.

---

## 3. Multi-Tenant Boundary Isolation

AegisTrace implements rigorous multi-tenant data and cryptographic isolation:

1. **Explicit Resource Ownership:** Every registered master document, release package, ingested leak artifact, and forensic analysis job is tagged with an immutable `tenant_id`.
2. **Strict Boundary Verification:** When a principal requests access to any resource, `verify_tenant_boundary(resource_tenant_id, principal)` is evaluated:
   ```python
   if principal.role != "system" and principal.tenant_id != resource_tenant_id:
       raise TenantBoundaryViolationError(
           resource_type=resource_type,
           resource_id=resource_id,
           principal_tenant=principal.tenant_id,
           resource_tenant=resource_tenant_id
       )
   ```
3. **No Cross-Tenant Metadata Leakage:** Listing endpoints (`GET /documents`, `GET /releases`, `GET /analysis`) dynamically filter by the caller's `tenant_id`. Caller B cannot determine whether a document ID exists in Tenant A. Direct ID queries across tenants yield a standardized `403 TENANT_BOUNDARY_VIOLATION`.

---

## 4. Insecure Direct Object Reference (IDOR) Protections

In addition to tenant separation, AegisTrace enforces fine-grained resource entitlement:

- **Recipient Cross-Package Exfiltration:** When Bob attempts to fetch Alice's package (`GET /releases/{release_id}/packages/alice`) or decrypt Alice's package (`POST /releases/{release_id}/decrypt`), `require_recipient_access(recipient_id, principal)` rejects the call with `403 FORBIDDEN`.
- **Master Document Protection:** Master documents contain un-watermarked pristine source files. Only authorized enterprise roles (`administrator`, `operator`, `investigator`, `system`) are allowed to download pristine documents via `require_document_access(document_id, principal)`. Recipients are strictly confined to their own traceable, watermarked copies.
- **Client Provenance Impersonation:** Submissions to `/evidence/decryption-events` must match the caller's authenticated recipient identity, and the event must be signed with the matching enrolled ML-DSA-65 private key.

---

## 5. Input Validation, Sanitization & Defense-in-Depth

The API strictly rejects malformed inputs before reaching business logic or cryptographic handlers:

### 5.1 Identifier Format Regular Expressions
All `document_id`, `release_id`, `recipient_id`, `leak_id`, `analysis_id`, and `event_id` fields are validated against:
`^[a-zA-Z0-9_\-\.]{1,128}$`
Any presence of directory traversal characters (`..`, `/`, `\`) or null bytes (`\x00`) immediately aborts execution.

### 5.2 Artifact Upload Verification & Polyglot Defense
Uploaded payloads are inspected via `validate_uploaded_payload`:
1. **Size Limits:** Enforces hard ceiling (`max_upload_size_bytes = 50 MB`). Over-limit payloads receive `413 PAYLOAD_TOO_LARGE`.
2. **Magic-Byte Sniffing:** MIME headers from HTTP clients are untrusted. The system inspects file magic bytes (`%PDF`, `\x89PNG\r\n\x1a\n`, `\xff\xd8\xff`).
3. **Executable Rejection:** Windows PE executables (`MZ` header), Linux ELF binaries (`\x7fELF`), and shell scripts (`#!`) are rejected with `415 UNSUPPORTED_ARTIFACT_TYPE`.
4. **Active Script Detection:** Payload prefixes are scanned for `<script` and `javascript:` tags to prevent stored XSS or polyglot PDF attacks.

### 5.3 HTTP Response Splitting & Header Injection Defense
All dynamic Content-Disposition filenames are sanitized through `sanitize_header_value`, stripping all Carriage Return (`\r`), Line Feed (`\n`), and quote characters to prevent CRLF injection.

---

## 6. State-Machine Lifecycle Enforcements

AegisTrace guarantees cryptographic integrity by evaluating lifecycle state machines prior to state changes:

1. **Recipient Revocation:**
   - Enrolled recipients maintain an active or revoked state.
   - When a recipient is revoked via `POST /recipients/{recipient_id}/revoke`, their public keys are flagged `REVOKED`.
   - Creating a release that targets a revoked recipient is rejected (`400 INVALID_RELEASE`).
   - Attempting to decrypt a package with a revoked recipient key is rejected (`400 INVALID_STATE`).
   - Historical ledger records remain immutable and valid for future forensic attribution.
2. **Immutable Provenance Hash-Chain:**
   - Decryption provenance events are committed to a tamper-evident hash-chain ledger.
   - Every event must reference the current tip hash (`previous_event_hash`).
   - A global recursive lock (`threading.RLock`) protects concurrent ledger insertions, preventing ledger forks and race conditions.
3. **Anti-Replay Protection:**
   - Single-use nonces and provenance event IDs are recorded in `ReplayProtectionCache`.
   - Submitting an identical signed provenance event twice is rejected with `409 REPLAY_DETECTED`.

---

## 7. Operational Transport & Response Headers

Every HTTP response emitted by the API includes hardened defense-in-depth headers:
- `X-Content-Type-Options: nosniff` (Prevents MIME-sniffing confusion attacks)
- `X-Frame-Options: DENY` (Mitigates clickjacking)
- `Strict-Transport-Security: max-age=31536000; includeSubDomains` (Enforces HTTPS)
- `Content-Security-Policy: default-src 'self'` (Restricts resource loading)
- `Cache-Control: no-store, no-cache, must-revalidate, private` (Applied to all artifact downloads, key packages, and decryption endpoints to prevent disk caching of sensitive cryptographic assets).
