# AegisTrace — Architectural Integration & Cryptographic Binding Map
**Specification Version**: `SIH26237-v1.0`  
**Security Level**: NIST Post-Quantum Cryptography Category 3 (AES-192 Equivalent)  
**Evaluation Standard**: Fail-Closed Forensic Multi-Channel Evidence Fusion  

---

### Executive Overview

AegisTrace is a forensic security platform providing non-repudiable document release, recipient-specific traitor tracing, cryptographic provenance, multi-channel evidence fusion, and mathematically bounded fail-closed attribution.

This document reconstructs the actual, implemented architecture of the system based directly on the core codebase (`core/`), adversarial fixtures (`attacks/`), REST gateway (`apps/api/`), and test harnesses (`tests/`).

```
[ Master Plaintext Document ]
              │
              ▼
   (1) Canonical Identity & Hash (SHA-256: ORIGINAL_DOCUMENT_HASH)
              │
              ▼
   (2) Recipient Enrollment (ML-KEM-768 & ML-DSA-65 Key Isolation)
              │
              ▼
   (3) Multi-Recipient Hybrid Release (AES-256-GCM + Domain-Separated HKDF Key Wrap)
              │
              ▼
   (4) Client-Side Sovereign Decapsulation & Integrity Verification
              │
              ▼
   (5) Recipient Traceability Embedding (Tardos Codewords + Spatial/ArUco Carrier)
              │
              ▼
   (6) Client-Side Provenance Signing (ML-DSA-65 Non-Repudiation)
              │
              ▼
   (7) Server-Side Provenance Verification & SHA-256 Tamper-Evident Ledger
              │
              ▼
   (8) Leaked Carrier Artifact Ingestion & Identity Resolution
              │
              ▼
   (9) Multi-Channel Evidence Extraction (Watermark, Tardos, Provenance, Ledger)
              │
              ▼
  (10) Anti-Double-Counting Dependency Graph (Max Tree Bound + Gamma Discount)
              │
              ▼
  (11) Fail-Closed Bayesian Evidence Fusion (7 Mutually Exclusive Decision States)
```

---

### 1. Canonical Identifiers & Schema Nomenclature

The platform strictly differentiates identities across all lifecycle stages. Under no circumstances are document hashes, release hashes, and leak artifact hashes collapsed.

| Identifier | Format & Generation | Scope | Binding Contract |
| :--- | :--- | :--- | :--- |
| `document_id` | `doc_<hash[:8]>_<uuid[:6]>` | Master document | Primary key for immutable master content |
| `original_document_hash` | SHA-256 64-character lowercase hex digest | Master document | Content-addressed cryptographic digest of pristine plaintext |
| `recipient_id` | `rec_<name>_<hex[:6]>` or `alice`, `bob`, `charlie` | Recipient identity | Enrolled participant; binds public KEM/DSA keys |
| `release_id` | `rel_<timestamp>_<hex[:6]>` | Distribution package | Scoped distribution authorized for recipient cohort |
| `traceable_artifact_hash` | SHA-256 64-character lowercase hex digest | Decrypted copy | Content-addressed hash of recipient-marked document |
| `leak_artifact_hash` | SHA-256 64-character lowercase hex digest | Intercepted leak | Content-addressed hash of intercepted leak artifact |
| `event_id` | `evt_dec_<rel[:12]>_<rec_id>_<hex[:6]>` | Provenance event | Unique transaction ID in audit ledger; anti-replay |
| `previous_event_hash` | SHA-256 64-character lowercase hex digest | Ledger block | Cryptographic parent pointer to tip of hash-chain |
| `event_hash` | SHA-256 64-character lowercase hex digest | Ledger block | Deterministic hash of serialized canonical event JSON |
| `watermark_id` / `source_id` | `wm_obs_<hex[:8]>` | Evidence channel | Unique identifier of physical watermark extraction |
| `traceability_key_id` | `epoch_<year>_<quarter>` | Key epoch | Rotation epoch for Tardos codebooks and seeds |

---

### 2. Cryptographic Protocol & Version Metadata

AegisTrace enforces pure-Python and standard-library implementations of post-quantum standards with optional C-accelerators, guaranteeing zero cloud dependencies:

1. **Protocol Identifier**: `PROTOCOL_VERSION = "SIH26237-v1.0"`
2. **Post-Quantum KEM**: NIST FIPS 203 **ML-KEM-768**
   - Public Key Size: 1,184 bytes
   - Ciphertext Size: 1,088 bytes
   - Shared Secret: 32 bytes (256 bits)
3. **Post-Quantum Digital Signature**: NIST FIPS 204 **ML-DSA-65**
   - Public Key Size: 1,952 bytes
   - Signature Size: 3,309 bytes
4. **Symmetric Encryption**: NIST SP 800-38D **AES-256-GCM**
   - Key: 256 bits ($K_{doc}$)
   - Nonce: 96 bits (12 bytes)
   - Tag: 128 bits (16 bytes)
   - Authenticated Associated Data (AAD): `DOC-RELEASE:{release_id}:{document_id}`
5. **Key Wrapping**: RFC 3394 / NIST SP 800-38F **AES Key Wrap**
   - Wrapping Key ($K_{wrap}$): 256 bits derived via HKDF-SHA256
   - Authenticated Context: `KEY-WRAP-AUTH:{release_id}:{recipient_id}`
6. **Key Derivation**: RFC 5869 **HKDF-SHA256**
   - Salt: `SHA256("SALT:{protocol_version}:{algorithm_id}:{release_id}")`
   - Info Context: `"DOC-KEY-WRAP:{protocol_version}:{algorithm_id}:{release_id}:{document_id}:{recipient_id}"`
7. **Traitor-Tracing Code**: Symmetric **Tardos Code**
   - Length: $m=128$ bits (configurable up to $m=2048$)
   - Coalition Bound: $c \le 5$ colluders
   - Symmetric Cutoff: $Z = 11.40$
   - Accusation Threshold: $\tau_Z = 6.50$
   - Theoretical False Alarm Upper Bound: $\epsilon \le 10^{-5}$
8. **Watermark Physical Carrier**: **DSSS Spatial & ArUco Synchronization**
   - Dictionary: OpenCV ArUco `DICT_4X4_50`
   - Synchronization: 4-Corner 4-point RANSAC Homography
   - Error Correction: Reed-Solomon RS(255, 223) with $t=16$ bytes error correction

---

### 3. Module Contracts & Data Interfaces

#### A. Document & Recipient Subsystem (`core/recipient.py`)
- **`Recipient`**: Sovereign entity holding private keypair (`kem_keypair.private_key_bytes`, `dsa_keypair.private_key_bytes`).
- **`PublicRecipient`**: Sanitized projection containing only public keys in Base64 (`kem_public_key_b64`, `dsa_public_key_b64`).
- **Invariant**: Private keys never leave the client device; the server registry only stores public keys.

#### B. Release Subsystem (`core/release.py`)
- **`ReleaseManager.create_release(...)`**:
  - Encrypts master document once with random $K_{doc}$ under AES-256-GCM.
  - Computes `associated_data = f"DOC-RELEASE:{rel_id}:{doc_id}"`.
  - For each recipient, executes ML-KEM-768 encapsulation, derives domain-separated $K_{wrap}$, and wraps $K_{doc}$ with `associated_data = f"KEY-WRAP-AUTH:{rel_id}:{r_id}"`.
  - Produces isolated `ReleaseRecipientPackage` per recipient.

#### C. Client Decryption & Provenance Subsystem (`core/provenance/decryption.py`)
- **`RecipientDecryptionClient.decrypt_package(...)`**:
  - Enforces `recipient.recipient_id == package.recipient_id`.
  - Executes ML-KEM-768 decapsulation $\rightarrow$ unwrap $K_{doc}$ $\rightarrow$ AES-GCM decryption.
  - Verifies `SHA256(plaintext) == package.document_hash`.
  - Embeds recipient-specific marker $\rightarrow$ produces `traceable_copy`.
  - Generates client-side ML-DSA-65 digital signature over canonical preimage:
    ```
    DECRYPTION_PROVENANCE:{event_id}:{document_id}:{release_id}:{recipient_id}:{traceable_hash}:{previous_event_hash}:{timestamp}
    ```
  - Appends signed `EvidenceEvent` to `TamperEvidentLedger`.

#### D. Ledger Subsystem (`core/ledger/ledger.py`)
- **`TamperEvidentLedger`**:
  - Enforces single-chain sequential linkage from `GENESIS_HASH` (`0000...0000`).
  - Strict anti-replay: duplicate `event_id` unconditionally rejected via `_seen_event_ids`.
  - Tip validation: `event.previous_event_hash == get_last_event_hash()`.
  - Chain audit: `verify_chain()` verifies that every block hash matches canonical JSON serialization.

#### E. Forensic Attribution & Evidence Fusion (`core/attribution/`)
- **`EvidenceBundle`**: Target-bound container holding multi-channel observations.
- **`EvidenceDependencyGraph`**:
  - Validates `TargetBinding` (`document_id`, `release_id`, `recipient_id`, `artifact_hash`).
  - Deduplicates identical observation fingerprints.
  - Derivation trees: uses Maximum Evidentiary Bound across trees ($LLR_{fused} \le \max_k(LLR_k)$), banning additive summation of derived signals.
  - Partially dependent channels discounted by $\gamma = 0.65$.
- **`AttackAwareReliabilityCalibrator`**:
  - Computes effective reliability $\rho_i \in [0, 1]$ based on attack telemetry (BER, SSIM, crop, execution mode).
  - Enforces $\rho_i = 0.0$ if Tardos `margin_over_threshold <= 0` or if signature is invalid.
- **`EvidenceFusionEngine`**:
  - Evaluates Bayesian log-likelihood ratio scores.
  - Enforces fail-closed policy:
    - Target binding violation $\rightarrow$ `CONFLICT`.
    - No valid signals $\rightarrow$ `NO_SIGNAL`.
    - Missing mandatory provenance signature $\rightarrow$ `INSUFFICIENT_EVIDENCE`.
    - Non-cryptographic channels lacking primary marker corroboration $\rightarrow$ `INSUFFICIENT_EVIDENCE`.
    - Disagreement between independent channels (e.g. WM Bob vs Tardos Charlie) $\rightarrow$ `CONFLICT`.
    - Score below threshold ($S < 6.0$) or narrow margin ($\Delta < 2.5$) $\rightarrow$ `INSUFFICIENT_EVIDENCE`.
    - Clean unanimous evidence meeting all criteria $\rightarrow$ `ATTRIBUTED`.

---

### 4. Vulnerability Surface & Binding Integrity Points

The following matrix documents every point where identity, scope, or cryptographic binding could theoretically be attacked, along with the AegisTrace architectural defense:

| Threat Vector | Attack Mechanism | AegisTrace Countermeasure | Defense Layer |
| :--- | :--- | :--- | :--- |
| **Package Transplantation** | Attacker takes package for Release R1 and attaches it to Release R2 | AES-256-GCM decryption fails because AAD binds `DOC-RELEASE:{rel_id}:{doc_id}` | Cryptographic AAD |
| **Key Theft / Swap** | Bob attempts to decrypt Alice's package using his own private key | ML-KEM shared secret is different; HKDF info string binds `recipient_id`; AES unwrap tag check fails | HKDF Domain Separation & AES Key Wrap |
| **Document Substitution** | Malicious actor swaps decrypted plaintext with unrelated decoy | Post-decryption check compares `SHA256(plaintext)` against `package.document_hash` | Integrity Assertion |
| **Fiducial Erasure** | Attacker crops or whites out ArUco markers | Homography fails $\rightarrow$ Watermark decoder outputs `NO_SIGNAL` $\rightarrow$ Engine abstains | Fail-Closed Decoder |
| **Marker Forgery** | Attacker modifies recipient ID in carrier marker | HMAC-SHA256 token validation fails $\rightarrow$ Output marked `INVALID` $\rightarrow$ `INSUFFICIENT_EVIDENCE` | Cryptographic Token |
| **Provenance Signature Forgery** | Attacker counterfeits ML-DSA-65 signature on evidence event | Server verifies signature against enrolled public key $\rightarrow$ Verification fails $\rightarrow$ Event rejected | Post-Quantum Signature |
| **Provenance Event Replay** | Attacker replays valid historical decryption event | Ledger maintains `_seen_event_ids` set $\rightarrow$ Raises `ValueError("Replay detected")` | Anti-Replay Store |
| **Ledger History Tampering** | Attacker modifies historical event payload | Downstream `previous_event_hash` chain breaks $\rightarrow$ `verify_chain()` flags corruption $\rightarrow$ Engine abstains | Hash-Chained Ledger |
| **Cross-Channel Contradiction** | Attacker splices Bob's watermark into Charlie's signed document | Multi-channel fusion detects conflicting candidates with $\Delta < \tau$ $\rightarrow$ `CONFLICT` | Multi-Source Fusion Policy |
| **Duplication Attack** | Attacker submits same leak or observation 10 times | Dependency graph deduplicates by payload fingerprint $\rightarrow$ Fused score remains invariant | Dependency Graph |
| **Derived Signal Double-Counting** | Attacker scores watermark bitstream and Tardos codeword additively | Derivation tree applies Maximum Evidentiary Bound instead of summing | Evidentiary Bound Rule |
| **Cross-Document Scope Contamination** | Evidence bundle mixes observations from Doc A and Doc B | `validate_bundle_binding()` checks `TargetBinding.document_id` $\rightarrow$ Emits `CONFLICT` | Target Binding Guard |

---

### 5. Architectural Invariant Summary

1. **Identity Isolation**: The master document hash, decrypted traceable artifact hash, and leak artifact hash represent three distinct points in time and must never be unified into a single database column or schema field.
2. **Cryptographic Sovereign Custody**: Private keys for post-quantum KEM decapsulation and DSA non-repudiation signing are held exclusively by the recipient endpoint.
3. **Fail-Closed Guarantee**: In any ambiguous, degraded, corrupted, contradictory, or tampered forensic state, AegisTrace unconditionally abstains from attribution.
