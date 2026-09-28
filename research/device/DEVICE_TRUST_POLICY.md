# AegisTrace Trust Policy & Access Enforcement

## 1. Overview

AegisTrace implements an adaptive, risk-based **Trust Policy Engine** governing all critical forensic actions:
- `DECRYPT_RELEASE`: Decrypting an encrypted broadcast package.
- `VIEWER_SESSION_OPEN`: Initializing an interactive controlled viewer session.
- `EXPORT_DOCUMENT`: Exporting a watermarked derivative copy.
- `FORWARD_COPY`: Forwarding a protected instance along the lineage graph.
- `PRINT_DOCUMENT`: Rendering a document for physical print watermark embedding.

---

## 2. Operation Assurance Levels

The Trust Policy Engine supports three operational profiles:

```
+--------------------------------------------------------------------------+
|                     OPERATION ASSURANCE LEVELS                           |
+--------------------------------------------------------------------------+
| 1. HIGH_ASSURANCE                                                        |
|    - Target: Defense, Intelligence, Zero-Trust High-Security Perimeters. |
|    - Requirement: Strictly requires genuine hardware attestation        |
|      (DEVICE_ATTESTED via TPM 2.0 / Secure Enclave / StrongBox / FIDO2). |
|    - Enforcement: Fails closed on DEVICE_UNATTESTED or SOFTWARE_FALLBACK.|
+--------------------------------------------------------------------------+
| 2. STANDARD                                                              |
|    - Target: Commercial Enterprise, Financial Services, Regulated Corp.  |
|    - Requirement: Permits registered UNATTESTED software devices with    |
|      mandatory audit logging (audit_flags=['UNATTESTED_DEVICE_AUDIT']).  |
|    - Enforcement: Blocks REVOKED, SUSPENDED, and MISMATCHED devices.    |
+--------------------------------------------------------------------------+
| 3. RESTRICTED                                                            |
|    - Target: Active Incident Response, Compartmented Access, Auditing.   |
|    - Requirement: Denies untrusted/unattested endpoints; triggers alerts.|
+--------------------------------------------------------------------------+
```

---

## 3. Policy Decision Matrix

| Device Attestation State | Administrative Status | STANDARD Policy | HIGH_ASSURANCE Policy | RESTRICTED Policy |
| :--- | :--- | :---: | :---: | :---: |
| **DEVICE_ATTESTED** | ACTIVE | **ALLOW** | **ALLOW** | **ALLOW** |
| **DEVICE_UNATTESTED** | ACTIVE | **ALLOW** (Audited) | **BLOCK** | **BLOCK** |
| **DEVICE_KEY_MATCH** | ACTIVE | **ALLOW** (Audited) | **BLOCK** | **BLOCK** |
| **DEVICE_KEY_MISMATCH** | Any | **BLOCK** | **BLOCK** | **BLOCK** |
| **ATTESTATION_INVALID** | Any | **BLOCK** | **BLOCK** | **BLOCK** |
| **ATTESTATION_EXPIRED** | Any | **BLOCK** | **BLOCK** | **BLOCK** |
| Any | SUSPENDED | **BLOCK** | **BLOCK** | **BLOCK** |
| Any | REVOKED | **BLOCK** (Hard Tombstone) | **BLOCK** (Hard Tombstone) | **BLOCK** (Hard Tombstone) |

---

## 4. Device-Bound Session Lifecycle

To prevent token theft and session hijacking, sessions are bound cryptographically to:
$$H_{session} = \text{SHA-256}(session\_id \parallel recipient\_id \parallel device\_id \parallel device\_key\_id \parallel doc\_hash \parallel nonce \parallel epoch)$$

### 4.1 Cross-Device Session Replay Prevention
When a client presents an active session token:
1. Verifier extracts `device_id` from the session record.
2. Verifier checks presenting device's identity:
   $$\text{presenting\_device\_id} \stackrel{?}{=} \text{session.device\_id}$$
3. If an attacker extracts session token $S$ from Device A and replays it from Device B, the engine rejects the request with an explicit error:
   `DEVICE_SESSION_MISMATCH: Session 'S' is bound to device 'dev_A', but access was attempted from 'dev_B'.`

### 4.2 Document Scope Enforcement
Sessions cannot be used to decrypt or view documents outside their initial authorization scope:
$$\text{presented\_doc\_hash} \stackrel{?}{=} \text{session.document\_root\_hash}$$
Any mismatch produces an immediate `DOCUMENT_HASH_MISMATCH` denial.
