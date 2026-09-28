# AegisTrace Secure Operations & Zero-Trust Administration Runbook

**Document Version:** 1.0.0  
**Classification:** Operational Runbook  
**Audience:** System Administrators, Security Engineers, Forensic Investigators  

---

## 1. Overview & Operational Principles

AegisTrace is engineered to operate in **completely isolated, air-gapped secure enclaves**. It has zero reliance on public cloud authentication, third-party Key Management Services (KMS), or external NTP servers. All operational activities must follow the standardized procedures outlined below.

---

## 2. Air-Gapped Deployment & Initialization

### 2.1 Pre-Flight Environment Verification
Before starting the AegisTrace API service in production, verify that external network access is blocked and all local post-quantum libraries are verified:

```powershell
# 1. Verify air-gapped isolation (no external egress)
Test-NetConnection -ComputerName 8.8.8.8 -Port 53 -InformationLevel Quiet
# Expected output: False (must fail to connect)

# 2. Verify post-quantum cryptographic dependencies
python -c "from core.crypto.kem import MLKEM768; from core.crypto.signatures import MLDSA65; print('PQC Providers OK')"
# Expected output: PQC Providers OK
```

### 2.2 Enabling Production Zero-Trust Mode
In production enclaves, strict Zero-Trust authentication must be active. Set environment variable or configure `apps/api/config.py`:
```python
# In apps/api/config.py:
enforce_auth = True          # Strict Bearer token requirement
require_role_header = False  # Client headers never trusted
rate_limit_enabled = True    # Sliding-window rate limiting active
```

### 2.3 Starting the Server
Start the hardened Uvicorn server bound to localhost or the secure enclave interface:
```powershell
uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --workers 4
```

---

## 3. Token Provisioning & Rotation Procedures

### 3.1 Generating Secure Principal Tokens
All authentication tokens are provisioned server-side using cryptographically secure pseudorandom generators (`secrets.token_urlsafe(32)`):

```python
import secrets

def generate_principal_token():
    return f"aegis_{secrets.token_urlsafe(32)}"
```

### 3.2 Provisioning a New Enterprise Principal
To provision access for a new investigator or operator:
1. Generate a new secure token.
2. Add the token mapping into `config.local_auth_tokens` (or encrypted local credential store):
   ```python
   "aegis_xK92Lp0Q...": {
       "role": "investigator",
       "actor_id": "investigator_sharma",
       "tenant_id": "defense_hq",
       "scopes": ["read", "analyze"]
   }
   ```
3. Securely distribute the token to the authorized investigator over an encrypted channel.

### 3.3 Emergency Token Revocation & Rotation
If a principal's token is suspected of compromise:
1. Immediately remove the token entry from `config.local_auth_tokens`.
2. Any subsequent HTTP requests using that token will instantly fail with `401 UNAUTHORIZED`.
3. Issue a new replacement token to the operator.

---

## 4. Operational Monitoring & Ledger Audit

### 4.1 Periodic Cryptographic Ledger Verification
Run a verification of the immutable provenance ledger to confirm hash-chain continuity:

```bash
curl -s -H "Authorization: Bearer token_investigator_tenant_a" \
     http://127.0.0.1:8000/ledger/verify
```

**Expected Healthy Response:**
```json
{
  "is_valid": true,
  "total_events": 142,
  "chain_tip": "a7f23c91d8e0349b1...",
  "errors": []
}
```
If `is_valid` is `false`, the ledger has encountered data corruption or unauthorized tampering. Alert security personnel immediately.

### 4.2 Security Log Correlation & Auditing
Every request is stamped with an `X-Request-ID` and logged. Monitor server logs for security anomalies:
- `TENANT_BOUNDARY_VIOLATION` (403): Indicates an unauthorized cross-tenant query or IDOR attempt.
- `FORBIDDEN` (403): Indicates privilege escalation attempt by a lower-privileged role.
- `RATE_LIMITED` (429): Indicates automated scraping or DoS flood.
- `REPLAY_DETECTED` (409): Indicates provenance packet replay or network duplication.

---

## 5. Incident Handling: Forensic Leak Investigation

When an unauthorized document or screenshot is discovered in the wild:

1. **Ingest Leak Artifact:**
   ```bash
   curl -X POST http://127.0.0.1:8000/leaks \
     -H "Authorization: Bearer token_investigator_tenant_a" \
     -F "file=@intercepted_leak.pdf" \
     -F "suspected_document_id=doc_classified_2026"
   ```
2. **Execute Multi-Channel Attribution:**
   ```bash
   curl -X POST http://127.0.0.1:8000/analyze \
     -H "Authorization: Bearer token_investigator_tenant_a" \
     -H "Content-Type: application/json" \
     -d '{
       "leak_id": "leak_20260927_01",
       "expected_document_id": "doc_classified_2026"
     }'
   ```
3. **Inspect Attribution Findings:**
   - If `state == "ATTRIBUTED"`: The candidate recipient, confidence score, and forensic evidence channels are confirmed.
   - If `state == "INSUFFICIENT_EVIDENCE"`: The fail-closed policy has prevented a false accusation. Do not take punitive action without additional evidentiary corroboration.

---

## 6. Emergency Recipient Key Revocation

If an employee leaves the organization or their device is reported compromised:

```bash
curl -X POST http://127.0.0.1:8000/recipients/bob/revoke \
  -H "Authorization: Bearer token_admin_tenant_a"
```

**Verification:**
- Bob's status transitions to `REVOKED`.
- Bob can no longer decrypt existing packages (`400 INVALID_STATE`).
- Bob cannot be added to any future document releases (`400 INVALID_RELEASE`).
- Historical ledger events signed by Bob remain intact for forensic accountability.
