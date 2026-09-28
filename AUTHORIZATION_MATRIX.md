# AegisTrace API Authorization & Endpoint Security Matrix

**Document Version:** 1.0.0  
**Status:** PRODUCTION HARDENED  
**Standard:** NIST SP 800-207 Zero Trust Architecture  

---

## 1. Global Security Policy Defaults

- **Authentication Protocol:** Offline Bearer token mapping to authenticated `SecurityPrincipal`.
- **Default Authorization:** Fail-closed (`401 UNAUTHORIZED` if unauthenticated; `403 FORBIDDEN` if role insufficient).
- **Tenant Isolation Policy:** Strict partition. Cross-tenant access forbidden (`403 TENANT_BOUNDARY_VIOLATION`).
- **Identifier Syntax:** Strict regex `^[a-zA-Z0-9_\-\.]{1,128}$` on all ID path and form parameters.
- **Cache Policy:** `Cache-Control: no-store` on all key packages, decryptions, and artifact downloads.

---

## 2. Comprehensive Endpoint Authorization Matrix

| Route | Method | Required Roles | Tenant Scoping | IDOR / Resource Ownership | Rate Tier | Validation / Sanitization | State Preconditions |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `/health` | `GET` | *Public / Any* | None | None | Exempt | None | Service running |
| `/capabilities` | `GET` | *Public / Any* | None | None | Default | None | Service running |
| `/ledger/verify` | `GET` | `administrator`, `investigator`, `auditor`, `system` | None (Global) | None | Crypto | None | Ledger initialized |
| `/documents` | `POST` | `operator`, `administrator`, `authority`, `system` | Tenant-Scoped | Bound to caller `tenant_id` | Upload | Magic bytes, max 50MB, PE/ELF/Script rejection | Valid active tenant |
| `/documents` | `GET` | `operator`, `administrator`, `investigator`, `viewer`, `auditor`, `system` | Tenant-Scoped | Filtered by caller `tenant_id` | Default | Pagination bounds (1-100) | Valid active tenant |
| `/documents/{document_id}` | `GET` | `operator`, `administrator`, `investigator`, `viewer`, `auditor`, `system` | Tenant-Scoped | Verified `verify_tenant_boundary` | Default | ID regex check | Document exists in tenant |
| `/documents/{document_id}/download` | `GET` | `operator`, `administrator`, `investigator`, `viewer`, `auditor`, `system` | Tenant-Scoped | Verified `require_document_access` (Recipients blocked) | Default | ID regex, CRLF header sanitization | Document exists |
| `/recipients` | `POST` | `administrator`, `authority`, `system` | Global / Tenant | Enrolled key generation | Default | ID regex, string length bounds | Unique `recipient_id` |
| `/recipients` | `GET` | *Authenticated* | Global | Public keys only | Default | None | None |
| `/recipients/{recipient_id}` | `GET` | *Authenticated* | Global | Public keys only | Default | ID regex check | Recipient exists |
| `/recipients/{recipient_id}/revoke` | `POST` | `administrator`, `authority`, `system` | Global / Tenant | Authority only | Default | ID regex check | Recipient active |
| `/releases` | `POST` | `operator`, `administrator`, `authority`, `system` | Tenant-Scoped | Bound to caller `tenant_id` | Crypto | ID regex on all recipients, base64 payload bounds | All recipients must be `ACTIVE` |
| `/releases` | `GET` | `operator`, `administrator`, `investigator`, `viewer`, `auditor`, `system` | Tenant-Scoped | Filtered by caller `tenant_id` | Default | None | None |
| `/releases/{release_id}` | `GET` | `operator`, `administrator`, `investigator`, `viewer`, `auditor`, `system` | Tenant-Scoped | Verified `verify_tenant_boundary` | Default | ID regex check | Release exists in tenant |
| `/releases/{release_id}/packages/{recipient_id}` | `GET` | *Authenticated* | Tenant-Scoped | `require_recipient_access` (Caller must match recipient) | Default | ID regex check | Package exists |
| `/releases/{release_id}/decrypt` | `POST` | *Authenticated* | Tenant-Scoped | `require_recipient_access` (Caller must match recipient) | Crypto | ID regex check | Recipient status `ACTIVE`, package un-revoked |
| `/releases/{release_id}/provenance` | `POST` | *Authenticated* | Tenant-Scoped | `require_recipient_access` | Crypto | ID regex, ML-DSA-65 signature verification | Release matches event |
| `/leaks` | `POST` | `investigator`, `administrator`, `operator`, `auditor`, `system` | Tenant-Scoped | Bound to caller `tenant_id` | Upload | Magic bytes, max 50MB, PE/ELF/Script rejection | Valid suspected IDs |
| `/leaks/{leak_id}` | `GET` | `investigator`, `administrator`, `viewer`, `auditor`, `system` | Tenant-Scoped | Verified `verify_tenant_boundary` | Default | ID regex check | Leak exists in tenant |
| `/leaks/{leak_id}/download` | `GET` | `investigator`, `administrator`, `auditor`, `system` | Tenant-Scoped | Verified `verify_tenant_boundary` | Default | ID regex check | Leak exists in tenant |
| `/analyze` | `POST` | `investigator`, `administrator`, `auditor`, `system` | Tenant-Scoped | Verified on `leak_id` and `release_id` | Crypto | ID regex, base64 validation | Referenced artifacts exist in tenant |
| `/analysis` | `GET` | `investigator`, `administrator`, `viewer`, `auditor`, `system` | Tenant-Scoped | Filtered by caller `tenant_id` | Default | None | None |
| `/analysis/{analysis_id}` | `GET` | `investigator`, `administrator`, `viewer`, `auditor`, `system` | Tenant-Scoped | Verified `verify_tenant_boundary` | Default | ID regex check | Job exists in tenant |
| `/evidence/{release_id}` | `GET` | `investigator`, `administrator`, `viewer`, `auditor`, `system` | Tenant-Scoped | Verified `verify_tenant_boundary` on release | Default | ID regex check | Release exists in tenant |
| `/evidence/decryption-events` | `POST` | *Authenticated* | Tenant-Scoped | `require_recipient_access`, anti-replay nonce check | Crypto | ID regex, ML-DSA-65 signature verification | Nonce fresh, recipient active |
| `/directory/search` | `GET` | *Authenticated* | Global | Read-only directory metadata | Default | Query max length 200, limit 1-100 | Directory available |
| `/directory/identities/{identity_id}` | `GET` | *Authenticated* | Global | Read-only directory metadata | Default | ID regex check | Identity exists |
| `/directory/groups` | `GET` | *Authenticated* | Global | Read-only group metadata | Default | None | None |
| `/directory/groups/{group_id}/members` | `GET` | *Authenticated* | Global | Read-only membership | Default | ID regex check | Group exists |
