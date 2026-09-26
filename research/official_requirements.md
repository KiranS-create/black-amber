# SIH26237 — Official Requirements Compliance Matrix

## Problem Statement Summary
**Title:** Cryptographic Attribution and Immutable Decryption Provenance for Multi-Recipient Encrypted Document Distribution.

---

## 1. MUST HAVE (Milestone v0.1 & Core Compliance)
- [x] **Multi-Recipient Document Distribution**: Single document encrypted once with an ephemeral symmetric key (`AES-256-GCM`), wrapped for multiple recipients using Post-Quantum Key Encapsulation (`ML-KEM`).
- [x] **Recipient Identity & Key Isolation**: Distinct cryptographic identities for all recipients (Alice, Bob, Charlie) with isolated keypairs. Packages contain only recipient-specific material.
- [x] **Post-Quantum Cryptographic Primitives**:
  - Key Encapsulation: `ML-KEM-768` (Kyber-768 standard).
  - Digital Signatures: `ML-DSA-65` (Dilithium3 standard) / Ed25519 fallback for tamper-evident provenance event signing.
  - Document Encryption: `AES-256-GCM` with 256-bit ephemeral keys and unique 96-bit nonces.
- [x] **Decryption Provenance & Tamper-Evident Ledger**:
  - Signed decryption events generated upon authorized recipient decryption.
  - Hash-chained tamper-evident audit ledger linking `previous_event_hash`, `artifact_hash`, `evidence_hash`, `recipient_id`, `release_id`.
  - Ledger verification mechanism detecting any historical tampering or event deletion.
- [x] **Traceability & Marker Embedding**:
  - `TraceabilityProvider` interface with `issue_marker`, `extract_marker`, `verify_marker`, `get_evidence`, and `estimate_confidence`.
  - Recipient-bound cryptographic marker embedding in recipient copy.
- [x] **Attribution Engine & Fail-Closed Logic**:
  - Engine evaluation states: `ATTRIBUTED`, `CONFLICT`, `INSUFFICIENT_EVIDENCE`, `NO_SIGNAL`.
  - Attribution of authentic leaks to the specific decrypting recipient.
  - Strict abstention (`ABSTAIN`) on missing, forged, corrupted, or altered evidence.
- [x] **End-to-End Automated Testing & CLI Demo**: Full automated verification cycle (`demo/end_to_end.py`) testing Alice, Bob, Charlie leaks and adversarial forgeries.

---

## 2. SHOULD HAVE (Milestone v0.2 & Extended Robustness)
- [ ] **Collusion-Resistant Tardos Codes**: Tardos fingerprinting code matrix generation and probabilistic accusation scoring.
- [ ] **Multi-Channel Evidence Fusion**: Multi-source evidence combining Tardos fingerprint, visual/document markers, and ledger provenance.
- [ ] **Digital Attack Laboratory**: Benchmarking against JPEG re-encoding, resizing, cropping, rotation, metadata stripping, PDF flattening.
- [ ] **Interactive Web UI**: React/TypeScript dashboard displaying document distribution graph, recipient identities, decryption ledger, leak analysis, and verified attribution chain.

---

## 3. OPTIONAL (Milestone v0.3 & Physical Prototyping)
- [ ] **Physical Print-and-Scan Channel**: Camera capture perspective correction and physical print robust extraction.
- [ ] **Hardware Security Token / Smart Card Interop**: PKCS#11 key storage integration.
- [ ] **Air-Gapped Deployment Package**: Offline containerized self-hosted distribution.

---

## 4. OUT OF SCOPE
- Centralized DRM / remote screen capture blocking (focus is cryptographic attribution and post-breach accountability).
- Unverifiable proprietary closed-source watermarking algorithms without public verification mathematics.
- Re-encrypting entire large multi-gigabyte files separately per recipient (must use hybrid envelope encryption).

---

## Module Mapping
| Requirement Category | Implementation Module |
| :--- | :--- |
| Key Encapsulation (ML-KEM) | `core/crypto/kem.py` |
| Symmetric Encryption (AES-GCM) | `core/crypto/symmetric.py` |
| Digital Signatures (ML-DSA / Ed25519) | `core/crypto/signatures.py` |
| Key Derivation (HKDF-SHA256) | `core/crypto/key_derivation.py` |
| Traceability Framework | `core/traceability/provider.py` |
| Decryption & Provenance | `core/provenance/decryption.py` |
| Tamper-Evident Audit Ledger | `core/ledger/ledger.py` |
| Attribution Engine | `core/attribution/engine.py` |
| API Service | `apps/api/` |
| Web Application | `apps/web/` |
| Attack Lab | `attacks/` |
