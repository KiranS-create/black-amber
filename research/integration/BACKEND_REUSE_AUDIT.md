# SIH26237 — Backend Reuse Audit & Component Integration Matrix

**Author**: Agent 6: Principal Backend + Systems Integration Engineer  
**Date**: 2026-09-26  
**Scope**: `apps/api/**`, `tests/integration/**`, `docs/INTEGRATION_DESIGN.md`, `research/integration/**`, `artifacts/integration/**`, `scripts/integration/**`  
**Classification**: Engineering Research & Integration Audit  

---

## 1. Executive Summary

This audit establishes the **Reuse-First** architectural baseline for the SIH26237 backend orchestration layer. SIH26237 contains extensive, mathematically verified implementations of post-quantum cryptography (FIPS 203 / FIPS 204), traitor-tracing (Symmetric Tardos codes), Bayesian multi-channel evidence fusion, and tamper-evident audit ledgers.

The application backend must **orchestrate** these capabilities cleanly across the document distribution, leak detection, and attribution lifecycle without duplicating or re-implementing low-level algorithms.

---

## 2. Inventory of Existing Codebase Assets

### 2.1 Post-Quantum Cryptography & Key Management (`core/crypto/**`)
* **ML-KEM-768 (`core/crypto/kem.py`)**: 
  - Standardized NIST Post-Quantum Key Encapsulation Mechanism.
  - Generates keypairs, encapsulates shared secrets, and decapsulates ciphertexts.
  - Used for recipient envelope isolation.
* **ML-DSA-65 (`core/crypto/signatures.py`)**:
  - NIST Post-Quantum Digital Signature Standard.
  - Signs and verifies provenance claims with non-repudiation guarantees.
* **AES-256-GCM & Key Wrapping (`core/crypto/symmetric.py`)**:
  - Authenticated symmetric payload encryption with domain-separated AAD.
  - AES Key Wrap (RFC 3394 / NIST SP 800-38F) wrapping ephemeral document keys.
* **Key Derivation (`core/crypto/key_derivation.py`)**:
  - HKDF-SHA256 with explicit domain separation strings for per-recipient key derivation.

### 2.2 Identity & Release Packaging (`core/recipient.py`, `core/release.py`)
* **`RecipientRegistry` (`core/recipient.py`)**:
  - Enrolls recipients, generating isolated ML-KEM-768 and ML-DSA-65 keypairs.
  - Provides `to_public()` projections to strip private keys before network transmission.
* **`ReleaseManager` (`core/release.py`)**:
  - Takes document bytes, computes `ORIGINAL_DOCUMENT_HASH` (SHA-256).
  - Encrypts document once under ephemeral `K_doc`.
  - Encapsulates `K_doc` individually for each recipient using their respective ML-KEM public keys.
  - Emits `DocumentRelease` containing per-recipient `ReleaseRecipientPackage` instances.

### 2.3 Provenance & Decryption (`core/provenance/decryption.py`, `core/ledger/ledger.py`)
* **`RecipientDecryptionClient` (`core/provenance/decryption.py`)**:
  - Simulates recipient-side decryption using the recipient's private key.
  - Decapsulates KEM shared secret, unwraps document key, verifies document hash.
  - Embeds recipient-specific traceability marker.
  - Signs decryption provenance event with recipient's ML-DSA private key.
  - Appends signed event to the ledger.
* **`TamperEvidentLedger` (`core/ledger/ledger.py`)**:
  - Hash-chained audit log with anti-replay detection and chronological verification (`verify_chain()`).

### 2.4 Traceability & Traitor Tracing (`core/traceability/**`)
* **`PrototypeTraceabilityProvider` (`core/traceability/provider.py`)**:
  - HMAC-SHA256 authenticated recipient marker embedded directly into document streams.
* **`TardosTraceabilityProvider` (`core/traceability/provider.py`)**:
  - Full traitor-tracing provider based on Symbol-Symmetric Tardos codes.
  - Enforces `TardosCapacityPlanner` checks before codebook generation.
  - Provides `analyze_collusion_leak()` to score observed symbols against all registered recipients under the Marking Assumption.
* **`TardosCapacityPlanner` (`core/traceability/planner.py`)**:
  - Validates available carrier symbol budget against target coalition size $c$, population $N$, and false accusation bound $\epsilon_1$.

### 2.5 Multi-Channel Evidence Fusion (`core/attribution/**`)
* **`AttributionEngine` (`core/attribution/engine.py`)**:
  - Evaluates direct leaked artifacts, extracts markers, correlates ledger events, verifies signatures, and determines attribution.
* **`EvidenceFusionEngine` (`core/attribution/fusion.py`)**:
  - Multi-channel Bayesian evidence fusion across Tardos, Watermark, Provenance, and Ledger channels.
  - Applies `EvidenceDependencyGraph` to eliminate double-counting and enforce the Maximum Evidentiary Bound.
  - Enforces `DecisionPolicy` with fail-closed abstention rules:
    - Never force an attribution.
    - Abstain if candidate separation margin $\Delta < \text{min\_separation\_margin}$.
    - Transition to `CONFLICT` if multiple independent channels point to distinct recipients.
    - Transition to `NO_SIGNAL` or `INSUFFICIENT_EVIDENCE` when signals are weak or unauthenticated.

### 2.6 Robustness Laboratory (`attacks/**`)
* **`AttackResult` (`attacks/base.py`)**:
  - Standardized machine-readable schema for adversarial transformations (digital crop, JPEG compression, physical print-camera simulation, collusion, integrity tampering).
  - Captures `attack_id`, `attack_family`, `parameters`, `input_hash`, `output_hash`, and `DegradationMetrics`.

---

## 3. Gap Analysis & Missing Contracts

While the core modules are feature-complete, the existing application layer (`apps/api/main.py`) suffers from critical limitations:

1. **Monolithic Base64 Payloads**: All document bytes are transmitted as base64 strings inline in JSON request bodies. There is no separation between Control Plane metadata and Data Plane artifact storage.
2. **Missing Document Management**: There is no `/documents` endpoint to upload, validate, register, and store original master documents prior to release creation.
3. **Missing Leak Staging**: Leaks are submitted directly to an analysis route with raw base64 payloads without an independent artifact identity or storage record.
4. **Lack of Asynchronous Job Model**: Analysis runs synchronously. For large documents or high-order Tardos evaluations, this risks HTTP timeouts.
5. **Coupling Risks with Parallel Agents**:
   - The watermark agent is actively modifying `core/watermark/**`. The API must not directly import or couple to unstable watermark internals.
   - The evidence fusion agent is actively refining `core/attribution/**`. The API must consume the standard `EvidenceBundle` contract rather than replicating fusion logic.
6. **Inadequate Error Taxonomy**: Errors currently return generic HTTP 400/404 messages with plain text details, lacking structured error codes (`DOCUMENT_NOT_FOUND`, `CAPACITY_INSUFFICIENT`, etc.).
7. **Security Boundary Omissions**: Missing file upload size caps, MIME sniffing (magic bytes validation), path traversal protection on artifact retrieval, and object authorization verification.

---

## 4. Architectural Decisions: Reuse / Adapt / Implement / Reject

| Subsystem / Interface | Status | Decision | Implementation Rationale |
| :--- | :--- | :--- | :--- |
| **ML-KEM-768 / ML-DSA-65 / AES-256-GCM** | Existing (`core/crypto`) | **REUSE** | Direct reuse via existing release and decryption services. No cryptographic primitives will be duplicated in FastAPI. |
| **RecipientRegistry** | Existing (`core/recipient.py`) | **REUSE** | Direct reuse for enrollment and public key exposure. API will expose only `to_public()` projections. |
| **ReleaseManager** | Existing (`core/release.py`) | **REUSE** | Direct reuse for release creation and package retrieval. Orchestrator connects stored document bytes to the release manager. |
| **RecipientDecryptionClient** | Existing (`core/provenance/decryption.py`) | **REUSE** | Direct reuse for simulated recipient decryption and ledger signing. |
| **TamperEvidentLedger** | Existing (`core/ledger/ledger.py`) | **REUSE** | Direct reuse for event query and full chain verification (`verify_chain()`). |
| **TardosCapacityPlanner & Engine** | Existing (`core/traceability`) | **REUSE** | Direct reuse. Orchestrator calls planner to ensure feasibility and uses engine for collusion analysis. |
| **AttributionEngine & EvidenceFusionEngine** | Existing (`core/attribution`) | **REUSE** | Direct reuse. Orchestrator constructs `EvidenceBundle` and delegates decision to the fusion engine. |
| **AttackResult Schema** | Existing (`attacks/base.py`) | **REUSE** | Ingest schema to attach attack telemetry to analysis sessions. |
| **Watermark Channel** | Active Development | **ADAPT** | Create `WatermarkAnalysisAdapter` boundary. If watermark extraction is unavailable or fails, gracefully return empty observation without interrupting fusion. |
| **Artifact Storage Service** | Missing | **IMPLEMENT** | Build `ArtifactStorageService` (Protocol + Filesystem implementation) to separate Control Plane from Data Plane. |
| **Job Management** | Missing | **IMPLEMENT** | Build lightweight in-process `JobManager` supporting `QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`, and `ABSTAINED` states. |
| **Defensive Security & Validation** | Missing | **IMPLEMENT** | Implement path normalization, MIME magic-byte validation, file size limits, and role authorization headers. |
| **Custom Fusion Logic in API** | In Proposal | **REJECT** | **STRICTLY REJECT**. Do NOT re-implement likelihood ratios, Bayesian scoring, or decision thresholds in the API. |
| **External Message Broker (Redis/Celery)** | In Proposal | **REJECT** | **REJECT**. Requirement specifies offline single-laptop operation. An in-process threadpool/job manager provides required async capabilities without external daemon dependencies. |

---

## 5. Artifact Identity & Separation of Planes

The backend establishes an unequivocal separation between **Control Plane** (metadata, references, hashes) and **Data Plane** (binary bytes on disk):

```
CONTROL PLANE (Metadata in Memory / SQLite)
- Document Record: (document_id, document_name, ORIGINAL_DOCUMENT_HASH, size_bytes, storage_key)
- Release Record:  (release_id, document_id, issuer_id, recipient_ids, RELEASE_ARTIFACT_HASH)
- Leak Record:     (leak_id, LEAK_ARTIFACT_HASH, size_bytes, storage_key, mime_type)
- Analysis Job:    (analysis_id, leak_id, release_id, status, result, error)

DATA PLANE (Filesystem Storage: data/artifacts/{storage_key})
- Raw master document bytes
- Encrypted release package archives
- Decrypted recipient traceable documents
- Uploaded leak artifact bytes
```

### Hash Identity Invariants:
1. `ORIGINAL_DOCUMENT_HASH`: $H(D_{\text{orig}})$ — Computed from master document plaintext.
2. `RELEASE_ARTIFACT_HASH`: $H(E(D_{\text{orig}}))$ — Computed from encrypted recipient package or bundle.
3. `LEAK_ARTIFACT_HASH`: $H(D_{\text{leak}})$ — Computed immediately upon leak upload.

---

## 6. Integration Risks & Mitigations

1. **Risk: Parallel Agent Interface Drifts in `core/attribution`**  
   *Mitigation*: Interface only with high-level contracts: `EvidenceBundle`, `EvidenceObservation`, `AttributionState`, and `AttributionEngine.analyze_leak()`. Do not bind to low-level internal helper methods.
2. **Risk: Missing Watermark Channel Blocks Execution**  
   *Mitigation*: The backend treats watermark signals as an optional channel. The `EvidenceFusionEngine` natively handles missing channels without error, maintaining fail-closed safety.
3. **Risk: Long-Running Tardos Collusion Analysis Causes HTTP Gateway Timeout**  
   *Mitigation*: The `/analyze` endpoint supports both synchronous execution (for demo speed) and `async_execution: true` returning an `analysis_id` with polling via `GET /analysis/{analysis_id}`.
4. **Risk: Path Traversal on Artifact Retrieval**  
   *Mitigation*: Storage keys are strictly derived from SHA-256 hashes and alphanumeric IDs. All paths are resolved with `os.path.abspath` and verified against the storage root.

---

## 7. Conclusion

All components needed for a quantum-resistant, tamper-evident document distribution and attribution system exist in the repository. The application layer's role is to act as an orchestrator, enforcing data isolation, fail-closed validation, defensive error handling, and offline-first performance.
