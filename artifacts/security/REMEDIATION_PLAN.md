# SIH26237 — Security Remediation Plan & Non-Scope Patch Specifications

**Author**: Agent 8 (Principal Application Security Engineer & Red-Team Auditor)  
**Date**: September 2026  
**Policy Compliance**: Strict File Scope Adherence (No silent edits to external agents' code)  

---

## 1. Overview & Remediation Strategy

In accordance with SIH26237 parallel workstream rules, Agent 8 has isolated all active security test suites and reusable defense helpers in:
- `security/**`
- `tests/security/**`
- `research/security/**`
- `artifacts/security/**`
- `docs/SECURITY_ARCHITECTURE.md`
- `scripts/security/**`

This document details the exact, line-by-line patch specifications for vulnerabilities that lie outside our permitted editing scope (`apps/api/**`, `core/attribution/**`, `core/recipient.py`, `apps/web/**`). Maintainers and assigned workstream agents can apply these patches directly.

---

## 2. Priority 1: Critical & High Severity Remediations

---

### Patch 1: [SEC-02] Fix Contradiction Suppression in Evidence Fusion Engine
- **Severity**: **HIGH**
- **Vulnerable File**: `core/attribution/fusion.py`
- **Vulnerable Function**: `EvidenceFusionEngine.fuse()`, Step 5 (lines 254–284)
- **Exact Issue**: The condition `separation_margin < self.policy.min_separation_margin` prevents a conflict from triggering if the top candidate's score is significantly higher than the runner-up, even when the runner-up has a verified, independent cryptographic signature.
- **Recommended Patch**:

```python
<<<<
        # Step 5: Check for Conflict (distinct reliable independent sources pointing to different candidates)
        if (
            len(sorted_candidates) > 1
            and runner_up_score >= self.policy.conflict_runnerup_threshold
            and separation_margin < self.policy.min_separation_margin
        ):
====
        # Step 5: Check for Conflict (distinct reliable independent sources pointing to different candidates)
        # Safety Rule: If the runner-up independently crosses the conflict threshold,
        # and has independent primary cryptographic corroboration OR insufficient separation margin, declare CONFLICT.
        runner_up_evaluation = evaluations[1] if len(evaluations) > 1 else None
        runner_up_has_crypto = False
        if runner_up_evaluation:
            runner_up_obs = [
                o for o in valid_observations if o.source_id in runner_up_evaluation.supporting_observations
            ]
            runner_up_has_crypto = any(
                o.family in primary_crypto_families for o in runner_up_obs
            )

        if (
            len(sorted_candidates) > 1
            and runner_up_score >= self.policy.conflict_runnerup_threshold
            and (separation_margin < self.policy.min_separation_margin or runner_up_has_crypto)
        ):
>>>>
```

---

### Patch 2: [SEC-03] Enforce Size Limits & Safe Base64 Decoding on Analysis Endpoints
- **Severity**: **HIGH**
- **Vulnerable File**: `apps/api/orchestrator.py`
- **Vulnerable Function**: `SystemOrchestrator.analyze_leak()` (lines 318–336)
- **Exact Issue**: Inline `leaked_document_base64` is decoded without pre-checking length against `config.max_upload_size_bytes`, enabling heap exhaustion DoS.
- **Recommended Patch**:

```python
<<<<
        elif leaked_document_base64:
            try:
                leak_bytes = base64.b64decode(leaked_document_base64)
            except Exception:
                raise APIException(
                    code=ErrorCode.INVALID_ANALYSIS_REQUEST,
                    message="Invalid base64 payload for leaked document."
                )
====
        elif leaked_document_base64:
            from security.defense import validate_base64_payload
            try:
                leak_bytes = validate_base64_payload(
                    leaked_document_base64,
                    max_size_bytes=config.max_upload_size_bytes
                )
            except Exception as e:
                raise APIException(
                    code=ErrorCode.PAYLOAD_TOO_LARGE if "exceeds" in str(e).lower() else ErrorCode.INVALID_ANALYSIS_REQUEST,
                    message=f"Invalid or oversized base64 payload: {str(e)}",
                    status_code=413 if "exceeds" in str(e).lower() else 400
                )
>>>>
```

---

### Patch 3: [SEC-01] Eliminate Server-Side Private Key Custody & Decryption Oracle
- **Severity**: **CRITICAL**
- **Vulnerable Files**:
  1. `core/recipient.py` (`RecipientRegistry`)
  2. `apps/api/routers/releases.py` (`decrypt_release_package`)
  3. `apps/api/orchestrator.py` (`decrypt_release_package`)
- **Exact Issue**: The server stores recipient private keys and executes decryptions/signings on behalf of unauthenticated callers.
- **Recommended Remediation Architecture**:
  1. In `core/recipient.py`, modify `enroll()` so that client workstations submit only their `PublicRecipient` (public keys).
  2. Deprecate `/releases/{release_id}/decrypt` on the server.
  3. Introduce client-side decryption CLI / desktop tool (`scripts/client_decrypt.py`) where the recipient decapsulates locally and signs their provenance event.
  4. Create `POST /evidence/decryption-events` endpoint where clients submit the signed `EvidenceEvent` to append to the server ledger:
     ```python
     @router.post("/events/decryption", response_model=Dict[str, Any])
     def submit_decryption_event(event: EvidenceEvent):
         # Verify signature against enrolled public key before appending
         recipient = default_registry.get(event.recipient_id)
         if not recipient:
             raise HTTPException(status_code=404, detail="Recipient not enrolled")
         # Verify ML-DSA-65 signature on event payload
         # Append to ledger
         event_hash = default_ledger.append_event(event)
         return {"status": "RECORDED", "event_hash": event_hash}
     ```

---

## 3. Priority 2: Medium Severity Remediations

---

### Patch 4: [SEC-04] Secure CORS Configuration in FastAPI Entrypoint
- **Severity**: **MEDIUM**
- **Vulnerable File**: `apps/api/main.py` (lines 58–64)
- **Exact Issue**: Wildcard origin `allow_origins=["*"]` combined with `allow_credentials=True`.
- **Recommended Patch**:

```python
<<<<
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
====
# Explicit trusted origins for local development and production
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID", "X-API-Role"],
)
>>>>
```

---

### Patch 5: [SEC-07] Prevent Header Injection in Document Download Endpoint
- **Severity**: **MEDIUM**
- **Vulnerable File**: `apps/api/routers/documents.py` (lines 43–53)
- **Exact Issue**: `doc.document_name` is formatted directly into `Content-Disposition` without CRLF or quote sanitization.
- **Recommended Patch**:

```python
<<<<
@router.get("/{document_id}/download")
def download_document(document_id: str):
    """Download pristine master document bytes from Data Plane storage."""
    doc = default_orchestrator.get_document(document_id)
    doc_bytes = default_orchestrator.get_document_bytes(document_id)
    return Response(
        content=doc_bytes,
        media_type=doc.mime_type,
        headers={"Content-Disposition": f'attachment; filename="{doc.document_name}"'}
    )
====
@router.get("/{document_id}/download")
def download_document(document_id: str):
    """Download pristine master document bytes from Data Plane storage."""
    from security.defense import sanitize_header_value
    doc = default_orchestrator.get_document(document_id)
    doc_bytes = default_orchestrator.get_document_bytes(document_id)
    safe_filename = sanitize_header_value(doc.document_name, fallback="document.pdf")
    return Response(
        content=doc_bytes,
        media_type=doc.mime_type,
        headers={"Content-Disposition": f'attachment; filename="{safe_filename}"'}
    )
>>>>
```

---

### Patch 6: [SEC-06] Replace Hardcoded Master Fallback Keys with KMS / Env Ingestion
- **Severity**: **MEDIUM**
- **Vulnerable Files**:
  - `core/traceability/provider.py` (lines 91, 259)
  - `core/traceability/tardos.py` (line 49)
- **Recommended Patch**:
  Load master keys from environment variables (`os.getenv("SIH_TARDOS_MASTER_KEY")`) and raise an explicit warning or error if running in production without an injected key:

```python
import os
import warnings

def _load_master_secret(env_var: str, default_bytes: bytes) -> bytes:
    env_val = os.getenv(env_var)
    if env_val:
        return env_val.encode('utf-8')
    if os.getenv("ENVIRONMENT") == "production":
        raise RuntimeError(f"CRITICAL: Environment variable '{env_var}' must be set in production mode!")
    warnings.warn(f"Using insecure default master key for {env_var}. Set {env_var} in production.", UserWarning)
    return default_bytes
```

---

## 4. Priority 3: Low Severity & Dependency Remediations

---

### Patch 7: [SEC-10] Upgrade Vite & Esbuild in Frontend Dependencies
- **Severity**: **LOW**
- **Vulnerable File**: `apps/web/package.json`
- **Recommended Patch**:
  Update `"vite": "^5.4.14"` or `"vite": "^6.0.0"` and run `npm audit fix`.

---

### Patch 8: [SEC-11] Upgrade Pillow in Python Dependencies
- **Severity**: **LOW**
- **Vulnerable File**: `requirements.txt`
- **Recommended Patch**:
  Add `pillow>=10.3.0` to `requirements.txt`.

---

### Patch 9: [SEC-09] Explicit Visual Banner on Frontend Simulated Fallback
- **Severity**: **LOW**
- **Vulnerable File**: `apps/web/src/App.tsx`, `apps/web/src/services/api.ts`
- **Recommended Patch**:
  When `isForceOffline()` or `!isOnline()` is active, display an amber banner at the top of the interface:
  `⚠ OFFLINE SIMULATION MODE: Displaying mock recipients and simulated attribution results. Connect to live backend for cryptographic verification.`
