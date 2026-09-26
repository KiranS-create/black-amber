# SIH26237 — Backend Integration & API Contract Design

**Document Version**: 2.0.0  
**Status**: Stabilized Post-Security Integration Design  
**Author**: Agent 6: Principal Backend + Systems Integration Engineer  
**Classification**: Cryptographic Architecture & Forensic Orchestration  

---

## 1. Architectural Overview & Design Principles

The SIH26237 platform provides post-quantum cryptographic security, traitor-tracing provenance, and fail-closed leak attribution for sensitive document distribution. The backend orchestration layer bridges low-level cryptographic primitives, traitor-tracing providers, and multi-channel evidence fusion engines into a unified, hardened, offline-first REST API.

### 1.1 Core System Lifecycle & Trust Boundary

```
                     [ ISSUING AUTHORITY ]
                               │
                               ▼
        1. DOCUMENT REGISTRATION (Data Plane: ORIGINAL_DOCUMENT_HASH)
                               │
                               ▼
        2. RECIPIENT ENROLLMENT (ML-KEM-768 & ML-DSA-65 Public Keys)
                               │
                               ▼
        3. CAPACITY PLANNING (TardosCapacityPlanner validation)
                               │
                               ▼
        4. ENVELOPE ENCRYPTION (AES-256-GCM + Domain-Separated HKDF + ML-KEM)
                               │
                               ▼
        5. MULTI-RECIPIENT RELEASE (Isolated Packages per Recipient)
                               │
   ============================│===========================================
   TRUST BOUNDARY: DECENTRALIZED CLIENT (OFFLINE / CLIENT HARDWARE)
   ============================│===========================================
                               ▼
        6. RECIPIENT FETCHES ISOLATED PACKAGE (GET /releases/{id}/packages/{my_id})
                               │
                               ▼
        7. CLIENT-SIDE ML-KEM DECAPSULATION & AES-256-GCM DECRYPTION
           [Client holds private KEM key; server has zero key custody]
                               │
                               ▼
        8. RECIPIENT-SIDE TRACEABILITY MARKING & EMBEDDING
                               │
                               ▼
        9. CLIENT-SIDE PROVENANCE SIGNING (ML-DSA-65)
           [Client signs EvidenceEvent with private ML-DSA key]
                               │
   ============================│===========================================
   TRUST BOUNDARY: SERVER INGESTION & AUDIT
   ============================│===========================================
                               ▼
       10. SERVER SIGNATURE & BINDING VERIFICATION (POST /evidence/decryption-events)
           ├── Cryptographic ML-DSA-65 verification against enrolled public key
           ├── Release, Document, and Recipient binding validation
           ├── Anti-replay check (unique event_id)
           └── Hash-chain continuity verification (previous_event_hash)
                               │
                               ▼
       11. IMMUTABLE TAMPER-EVIDENT LEDGER LOGGING
                               │
                               ▼
       12. LEAK EVENT OCCURS (Exfiltration / Interception)
                               │
                               ▼
       13. LEAK INGESTION & FORENSIC ATTRIBUTION
           ├── Tardos Traitor-Tracing Codewords Extraction
           ├── Watermark Payload Extraction (Adapter boundary)
           ├── Verified Decryption Provenance Correlation
           └── Multi-Channel Bayesian Evidence Fusion (Fail-Closed)
                               │
                               ▼
       14. FORENSIC EXPLANATION & VERDICT (ATTRIBUTED / NO_SIGNAL / INSUFFICIENT / CONFLICT)
```

---

## 2. Separation of Planes: Control vs. Data Plane

To ensure maximum performance, support massive documents, and eliminate memory bloat, the architecture enforces a strict boundary between Control Plane metadata and Data Plane artifact storage.

```
+──────────────────────────────────────────────────────────────────────────+
|                              CONTROL PLANE                               |
|                                                                          |
|  - Document Metadata:  document_id, document_name, original_hash, size   |
|  - Release Metadata:   release_id, issuer_id, recipient_ids, parameters   |
|  - Leak Metadata:      leak_id, leak_hash, suspected_scope, timestamps    |
|  - Job Manager:        analysis_id, status (QUEUED/RUNNING/COMPLETED)     |
|  - Ledger Events:      event_id, event_hash, previous_event_hash, sig    |
+──────────────────────────────────────────────────────────────────────────+
                                     │
                     References by Immutable Content Hash
                                     │
+──────────────────────────────────────────────────────────────────────────+
|                                DATA PLANE                                |
|                                                                          |
|  - Stored on Filesystem: data/artifacts/{artifact_id}.bin                |
|  - Content-Addressed, Immutable, Isolated Directory                      |
|  - Abstracted via ArtifactStorage Protocol:                              |
|      * store_artifact(data, artifact_type, expected_hash)                |
|      * retrieve_artifact_bytes(artifact_id)                              |
|      * retrieve_metadata(artifact_id)                                    |
|  - Ready for seamless transition from local disk to S3/GCS without       |
|    changing internal business logic or API contracts                     |
+──────────────────────────────────────────────────────────────────────────+
```

---

## 3. Endpoints & API Contract Specification

### 3.1 Document Lifecycle

#### `POST /documents`
Register an original master document into Data Plane storage.
- **Authorization**: `Bearer <token>` with role `authority` or `system`.
- **Request**: `multipart/form-data` with `file`, optional `document_name`, `document_id`.
- **Response** (`201 Created`):
```json
{
  "document_id": "doc_a1b2c3d4_8f12a3",
  "document_name": "CLASSIFIED_PROJECT_SPEC.pdf",
  "original_document_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "size_bytes": 1048576,
  "mime_type": "application/pdf",
  "created_at": "2026-09-26T12:00:00Z",
  "artifact_id": "art_original_doc_e3b0c44298fc_8a1b2c"
}
```

#### `GET /documents/{document_id}/download`
Download master document bytes. Enforces strict `Content-Disposition` header sanitization to prevent CRLF splitting.

---

### 3.2 Recipient Lifecycle

#### `POST /recipients`
Enroll a new recipient.
- **Key Custody Guarantee**: Returns **only public cryptographic identities**. Private keys are never returned or persisted in API responses.
- **Response** (`201 Created`):
```json
{
  "recipient_id": "bob",
  "name": "Bob Smith",
  "kem_public_key_b64": "...",
  "dsa_public_key_b64": "...",
  "algorithm_kem": "ML-KEM-768",
  "algorithm_dsa": "ML-DSA-65",
  "created_at": "2026-09-26T12:00:00Z",
  "status": "ACTIVE"
}
```

---

### 3.3 Release & Provenance Lifecycle

#### `POST /releases`
Create a multi-recipient quantum-resistant release package.
- **Authorization**: Role `authority` or `system`.
- **Response** (`200 OK`):
```json
{
  "release_id": "rel_20260926120000_a1b2c3",
  "document_id": "doc_a1b2c3d4_8f12a3",
  "document_name": "CLASSIFIED_PROJECT_SPEC.pdf",
  "original_hash": "e3b0c442...",
  "issuer_id": "HQ_AUTHORITY",
  "recipient_ids": ["alice", "bob", "charlie"],
  "packages": {
    "bob": {
      "release_id": "rel_20260926120000_a1b2c3",
      "document_id": "doc_a1b2c3d4_8f12a3",
      "recipient_id": "bob",
      "kem_ciphertext_b64": "...",
      "wrapped_doc_key_b64": "...",
      "encrypted_doc_nonce_b64": "...",
      "encrypted_doc_tag_b64": "...",
      "encrypted_doc_ciphertext_b64": "...",
      "algorithm_kem": "ML-KEM-768",
      "algorithm_sym": "AES-256-GCM",
      "document_hash": "e3b0c442...",
      "timestamp": "2026-09-26T12:00:00Z"
    }
  }
}
```

#### `GET /releases/{release_id}/packages/{recipient_id}`
Retrieve the isolated encrypted package for a designated recipient.
- **Authorization**: Caller must be the designated `recipient` or `system` (enforces IDOR prevention).

#### `POST /evidence/decryption-events` & `POST /releases/{release_id}/provenance`
**Decentralized Provenance Ingestion Endpoints**:
Accept a client-side signed `EvidenceEvent`. The server cryptographically verifies the `ML-DSA-65` digital signature against the recipient's enrolled public identity before appending the event to the immutable ledger.
- **Request Body**:
```json
{
  "event_id": "evt_dec_rel_20260926_bob_1a2b3c",
  "event_type": "DECRYPTION_EVENT",
  "timestamp": "2026-09-26T12:01:00Z",
  "document_id": "doc_a1b2c3d4_8f12a3",
  "release_id": "rel_20260926120000_a1b2c3",
  "recipient_id": "bob",
  "algorithm": "ML-DSA-65",
  "artifact_hash": "7f83b165...",
  "evidence_hash": "4a5b6c...",
  "previous_event_hash": "0000000000000000000000000000000000000000000000000000000000000000",
  "signature": "BASE64_ML_DSA_65_SIGNATURE...",
  "signer_public_key_b64": "BASE64_PUBLIC_KEY...",
  "metadata": {
    "recipient_name": "Bob",
    "original_document_hash": "e3b0c442...",
    "anti_replay_nonce": "9d974f80ebad8cc8"
  }
}
```
- **Response** (`201 Created`):
```json
{
  "status": "SUCCESS",
  "event_id": "evt_dec_rel_20260926_bob_1a2b3c",
  "event_hash": "9c1b7f...",
  "release_id": "rel_20260926120000_a1b2c3",
  "recipient_id": "bob"
}
```

#### `POST /releases/{release_id}/decrypt`
`[DEMO / SIMULATION ORACLE ONLY]`
Simulates local recipient decapsulation, AES-GCM decryption, marker embedding, and provenance recording for local rapid prototyping.
- **Authorization**: Caller must be authorized for `recipient_id`.
- **Response**: Returns `DecryptionResponse` with `simulation_mode: true` and `provenance_mode: "SIMULATED_LOCAL_ORACLE"`.

---

### 3.4 Leak Ingestion & Forensic Attribution

#### `POST /leaks`
Ingest intercepted leak artifacts into Data Plane storage.

#### `POST /analyze`
Execute multi-channel Bayesian evidence fusion under fail-closed policy.
- **Response** (`200 OK`):
```json
{
  "analysis_id": "job_anlz_9f8e7d6c5b",
  "status": "COMPLETED",
  "result": {
    "state": "ATTRIBUTED",
    "candidate": {
      "recipient_id": "bob",
      "name": "Bob",
      "confidence": 0.99,
      "verified_events": ["evt_dec_rel_20260926_bob_1a2b3c"]
    },
    "confidence": 0.99,
    "confidence_level": "HIGH",
    "evidence_items": [
      {
        "source": "TRACEABILITY_MARKER",
        "title": "Traceability Marker Verification",
        "is_valid": true,
        "confidence": 0.99
      },
      {
        "source": "AUDIT_LEDGER",
        "title": "Tamper-Evident Ledger Integrity",
        "is_valid": true,
        "confidence": 1.0
      },
      {
        "source": "RECIPIENT_SIGNATURE",
        "title": "Recipient Digital Signature Verification",
        "is_valid": true,
        "confidence": 1.0
      }
    ],
    "should_abstain": false
  }
}
```

---

### 3.5 System & Capabilities

#### `GET /capabilities`
Machine-readable capability discovery documenting cryptographic primitives, custody model, authentication mode, and client workflow endpoints.

#### `GET /ledger/verify`
Validates hash chain integrity and cryptographic consistency of the tamper-evident ledger.

---

## 4. Error Taxonomy

- `DOCUMENT_NOT_FOUND` (`404`): Master document ID does not exist.
- `RECIPIENT_NOT_FOUND` (`404`): Recipient ID not found in registry.
- `RELEASE_NOT_FOUND` (`404`): Release package not found.
- `ARTIFACT_NOT_FOUND` (`404`): Data Plane artifact key not found.
- `ARTIFACT_HASH_MISMATCH` (`400`): Declared SHA-256 does not match computed bytes.
- `INVALID_RELEASE` (`400`): Incomplete recipients, corrupt package, or decapsulation failure.
- `INVALID_ANALYSIS_REQUEST` (`400`): Empty payload, missing leak identifier, or corrupt base64.
- `INVALID_SIGNATURE` (`400`): Cryptographic ML-DSA-65 signature verification failure on submitted provenance event.
- `CAPACITY_INSUFFICIENT` (`400`): Carrier symbol capacity is smaller than Tardos requirement.
- `UNSUPPORTED_ARTIFACT_TYPE` (`415`): Magic bytes do not match supported MIME types.
- `PAYLOAD_TOO_LARGE` (`413`): Upload exceeds 50MB ceiling.
- `UNAUTHORIZED` (`401`): Missing or invalid Bearer authentication token.
- `FORBIDDEN` (`403`): IDOR breach, role boundary violation, or path traversal attempt.
- `INTERNAL_ERROR` (`500`): Sanitized server error.

---

## 5. Security & Defensive Controls

1. **Decentralized Key Custody**: Private keys are generated and held exclusively by the recipient. The server possesses only public keys (`kem_public_key_b64`, `dsa_public_key_b64`).
2. **Pre-Decoding Base64 Payload Validation**: All inline base64 fields (`document_base64`, `leaked_document_base64`) are validated for length and alphabet before memory allocation.
3. **CORS Hardening**: Strict origin whitelisting (`allowed_cors_origins`) replacing wildcards with credentials.
4. **Header Sanitization**: Response headers (e.g. `Content-Disposition`) are sanitized using `sanitize_header_value` to strip CRLF, null bytes, and quotes.
5. **Role & Actor Authorization**: Bearer tokens resolve server-side to `(role, actor_id)` preventing client-controlled role spoofing.
6. **Insecure Direct Object Reference (IDOR) Protection**: Package retrieval and decryption require actor ownership matching `recipient_id`.
7. **Fail-Closed Contradiction Handling**: The Bayesian fusion engine enforces strict corroboration margins (`check_evidence_contradiction`) to abstain if competing signals emerge.

---

## 6. Offline-First Operation

The system operates fully in air-gapped environments:
- Zero external REST API or cloud dependencies.
- Zero external key-vault or SaaS inference calls.
- Pure in-process execution for cryptography, Tardos planning, and Bayesian evidence fusion.

---

## 7. Recipient Key Custody & Non-Repudiation Model

### 7.1 Trust Boundary Axioms

> [!IMPORTANT]
> 1. **The server verifies a recipient-signed event; the server does NOT possess the recipient's private signing key.**
> 2. **A server-generated event MUST NEVER be termed "recipient non-repudiation."** Non-repudiation exists if and only if the event is digitally signed by the recipient's un-shared private key on the recipient's trusted hardware.

### 7.2 Standard Client-Side Workflow (10 Steps)

1. **Authenticate**: Client authenticates to the API and obtains an authorization token.
2. **Fetch Package**: Client fetches their isolated package (`GET /releases/{release_id}/packages/{my_id}`).
3. **ML-KEM Decapsulation**: Client decapsulates `kem_ciphertext_b64` using their local `ML-KEM-768` private key to recover the shared secret.
4. **Domain Key Derivation**: Client derives the wrapping key via `HKDF-SHA256` with release/recipient domain separation.
5. **Key Unwrapping & AES-GCM Decryption**: Client unwraps the document symmetric key and decrypts the document ciphertext.
6. **Integrity Check**: Client computes SHA-256 hash of the decrypted plaintext and verifies match against `package.document_hash`.
7. **Traceability Marking**: Client embeds the recipient-specific traceability marker.
8. **Construct & Sign Provenance Payload**: Client constructs the canonical provenance string bound to `event_id`, `document_id`, `release_id`, `recipient_id`, `artifact_hash`, `previous_event_hash`, and `timestamp`, then signs it using their `ML-DSA-65` private signing key.
9. **Submit Provenance**: Client submits the signed `EvidenceEvent` to `POST /evidence/decryption-events` (or `POST /releases/{release_id}/provenance`).
10. **Server Verification & Ledger Recording**: The server verifies the ML-DSA-65 signature against the recipient's enrolled public key, verifies release/document binding and anti-replay constraints, and appends the event to the immutable ledger.

### 7.3 Web Demo vs. Production Operational Model

- **Production Mode**: Recipient client CLI or workstation executes steps 1–9 locally. The API server executes step 10 only.
- **Web Demo / Simulated Mode**: The web demo UI can invoke `POST /releases/{release_id}/decrypt` which runs a local oracle simulation explicitly flagged with `simulation_mode: true` and `provenance_mode: "SIMULATED_LOCAL_ORACLE"`.
