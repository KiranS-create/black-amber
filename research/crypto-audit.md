# Cryptographic Trust, Correctness & Foundation Audit Report
**Smart India Hackathon 2026 — Project SIH26237**
**Author:** Principal Cryptography Engineer & Security Reviewer (Agent 1)
**Date:** September 2026
**Target Milestone:** v0.1 Foundation Audit & Hardening

---

## 1. Executive Verdict
**VERDICT: GREEN (Hardened & Verified)**

The cryptographic foundation of SIH26237 has undergone a comprehensive trust and correctness audit. The initial prototype's reliance on non-PQC simulation fallbacks has been fully eliminated. Genuine NIST FIPS 203 (ML-KEM-768) and NIST FIPS 204 (ML-DSA-65) lattice cryptography engines are now integrated with standardized key sizes, implicit rejection, and non-repudiation digital signatures. Envelope encryption, domain-separated key wrapping, recipient isolation, anti-replay provenance events, and hash-chained ledger tamper detection have all been verified through 48 automated test cases with 100% pass rates.

---

## 2. Current Implementation Architecture
- **KEM Layer (`core/crypto/kem.py`)**: Abstract `MLKEMProvider` interface supporting native `OQSMLKEMProvider` (liboqs C engine) and `StandardMLKEM768Provider` (pure Python NIST FIPS 203 lattice implementation via `kyber_py`).
- **Signature Layer (`core/crypto/signatures.py`)**: Abstract `MLDSAProvider` interface supporting native `OQSMLDSAProvider` and `StandardMLDSA65Provider` (pure Python NIST FIPS 204 lattice implementation via `dilithium_py`).
- **Symmetric Layer (`core/crypto/symmetric.py`)**: Authenticated AES-256-GCM (NIST SP 800-38D) with unique 96-bit nonces, 128-bit authentication tags, and authenticated key wrapping.
- **Key Derivation Layer (`core/crypto/key_derivation.py`)**: RFC 5869 HKDF-SHA256 with domain separation binding protocol version, release ID, document ID, recipient ID, and algorithm name.
- **Decryption Provenance (`core/provenance/decryption.py`)**: Client-side recipient decapsulation, hash verification, marker issuance, and ML-DSA event signing with anti-replay nonces.
- **Audit Ledger (`core/ledger/ledger.py`)**: Hash-chained tamper-evident ledger with duplicate event detection and chain verification.

---

## 3. Dependency Provenance
| Package | Version | Source | License | Security Role | In Production Path? | Fallback Status | Concerns |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `kyber-py` | 1.2.0 | PyPI | MIT | NIST FIPS 203 ML-KEM-768 Engine | YES | NO (Primary PQC Engine) | None; exact NIST parameter invariants verified |
| `dilithium-py` | 1.4.0 | PyPI | MIT | NIST FIPS 204 ML-DSA-65 Engine | YES | NO (Primary PQC Engine) | None; exact NIST parameter invariants verified |
| `pycryptodome` | 3.23.0 | PyPI | BSD / Public Domain | AES-256-GCM & SHA Primitives | YES | NO (Hardened Symmetric Core) | None; stable across all Windows/Linux architectures |
| `cryptography` | 43.0.3 | PyPI | Apache 2.0 / BSD | System Crypto Provider | OPTIONAL | NO | OpenSSL DLL loading instability on Windows 11 isolated |
| `liboqs` / `liboqs-python` | Optional | GitHub | MIT | C-Native PQC Provider | CONDITIONAL | Optional acceleration | Requires native C compilation; transparently detected |

---

## 4. ML-KEM-768 Verification (FIPS 203)
1. **Key Generation**: Generates exact 1184-byte public keys and 2400-byte private keys matching FIPS 203 ML-KEM-768 specification.
2. **Encapsulation**: Generates 1088-byte ciphertexts and 32-byte shared secrets bound to the recipient's public key.
3. **Decapsulation**: Decapsulates using recipient private key; verified identical 32-byte shared secret recovery.
4. **Implicit Rejection**: FIPS 203 IND-CCA2 implicit rejection verified. Tampered ciphertexts or wrong recipient private keys derive pseudorandom mismatched secrets rather than leaking oracle exceptions, preventing Bleichenbacher-style side-channel attacks.
5. **Key Independence**: Alice's encapsulation is computationally independent of Bob's and Charlie's encapsulations.

---

## 5. ML-DSA-65 Verification (FIPS 204)
1. **Key Dimensions**: Public keys are exactly 1952 bytes; secret keys are exactly 4000 bytes.
2. **Signature Dimensions**: Signatures are exactly 3293 bytes.
3. **Unforgeability**: Mismatched messages, corrupted signature bits, or verification against wrong recipient public keys are strictly rejected.
4. **Non-Repudiation**: Recipient signs provenance events using their local private key; the server cannot forge or simulate recipient signatures.

---

## 6. Document Encryption (AES-256-GCM)
1. **Key Length**: Strictly enforced 256 bits (32 bytes). Shorter or longer keys raise explicit exceptions.
2. **Nonce Handling**: 96-bit cryptographically random nonces (`os.urandom(12)`). Tested across 500 consecutive encryptions with zero collisions.
3. **Authenticated Associated Data (AAD)**: Binds `DOC-RELEASE:<release_id>:<document_id>` preventing ciphertext relocation attacks.
4. **Tamper Rejection**: Any 1-bit modification to ciphertext or authentication tag raises an authentication failure.

---

## 7. Key Wrapping & HKDF Domain Separation
1. **Formula**:
   $$\text{Salt} = \text{SHA256}(\text{"SALT:SIH26237-v1.0:ML-KEM-768:"} \parallel release\_id)$$
   $$\text{Info} = \text{"DOC-KEY-WRAP:SIH26237-v1.0:ML-KEM-768:REL="} \parallel release\_id \parallel \text{":DOC="} \parallel doc\_id \parallel \text{":REC="} \parallel recipient\_id$$
2. **Context Binding**: Key wrapping uses AES-GCM with associated data `KEY-WRAP-AUTH:<release_id>:<recipient_id>`. Wrapping keys cannot be swapped between recipients or releases.

---

## 8. Key Management & Secret Handling Audit
1. **Source Code Inspection**: A full repository search confirmed zero hardcoded private keys or test secret material in tracked code.
2. **API Exposure Audit**: `PublicRecipient` models strip private keys; `GET /recipients` only exports public key material.
3. **Decryption Response**: `POST /releases/{id}/decrypt` outputs decrypted traceable content and ledger metadata; recipient private keys remain on the client.
4. **Git Protection**: `.gitignore` updated to strictly exclude `.env`, `keystore/`, `*.key`, `*.pem`, `*.priv`, `*.der`.

---

## 9. Recipient Isolation Audit
Full $3 \times 3$ permutation matrix tested:
- Alice package + Alice key = SUCCESS
- Bob package + Bob key = SUCCESS
- Charlie package + Charlie key = SUCCESS
- Alice package + Bob key = FAILURE (Implicit rejection / unwrap auth failure)
- Alice package + Charlie key = FAILURE
- Bob package + Alice key = FAILURE
- Bob package + Charlie key = FAILURE
- Charlie package + Alice key = FAILURE
- Charlie package + Bob key = FAILURE
Package swapping and ciphertext substitution attacks were verified as strictly failing.

---

## 10. Provenance Signature & Anti-Replay Audit
1. **Signature Anchoring**: Event payload signed by recipient includes:
   `DECRYPTION_PROVENANCE:<event_id>:<doc_id>:<rel_id>:<recipient_id>:<traceable_hash>:<prev_event_hash>:<timestamp>`
2. **Anti-Replay**: Each decryption event includes an unforgeable anti-replay nonce (`os.urandom(16).hex()`). The ledger rejects duplicate event IDs.
3. **Tampering Detection**: Modifying event timestamps, recipient fields, or document hashes invalidates the ML-DSA signature.

---

## 11. Tamper-Evident Ledger Audit
1. **Chain Chaining**: Genesis anchor is $0^{64}$. Every event is linked via $H_{prev}$.
2. **Adversarial Resilience**:
   - Event modification $\rightarrow$ FAILS (`verify_chain` catches hash mismatch).
   - Event deletion / reordering $\rightarrow$ FAILS (chain linkage broken).
   - Duplicate event submission $\rightarrow$ FAILS (rejected on append).
3. **Integrity Language**: Formally categorized as **Tamper-Evident Ledger** (not claiming absolute physical immutability).

---

## 12. Traceability Limitations (Milestone v0.1 Boundary)
- **Current Mechanism**: `PrototypeTraceabilityProvider` using HMAC-SHA256 authenticated metadata markers.
- **Fail-Closed Verification**: Correctly identifies authentic recipient copies and strictly outputs `ABSTAIN` on missing, forged, corrupted, or framed markers.
- **Boundary Guarantee**: The `TraceabilityProvider` abstraction is cleanly isolated, enabling Agent 2 to implement `TardosProvider` (collusion-resistant fingerprinting) without requiring any architectural changes to `core/crypto/`, `core/release.py`, or `core/ledger/`.

---

## 13. Vulnerabilities Found in v0.1 Scaffold & Fixes Applied
| ID | Finding / Weakness | Risk Level | Fix Applied | Status |
| :--- | :--- | :--- | :--- | :--- |
| **VULN-01** | Simulated SHA3 KEM fallback used when liboqs was missing | HIGH | Integrated genuine NIST FIPS 203 `StandardMLKEM768Provider` (`kyber_py`) | RESOLVED |
| **VULN-02** | Classical Ed25519 used while claiming ML-DSA-65 | HIGH | Integrated genuine NIST FIPS 204 `StandardMLDSA65Provider` (`dilithium_py`) | RESOLVED |
| **VULN-03** | Missing domain separation in HKDF key wrapping | MEDIUM | Implemented `derive_recipient_wrapping_key` binding release, doc, recipient, and protocol version | RESOLVED |
| **VULN-04** | Lack of explicit associated data in key wrapping | MEDIUM | Bound `KEY-WRAP-AUTH:<rel>:<rec>` associated data to `wrap_key_aes_kw` | RESOLVED |
| **VULN-05** | Ledger allowed duplicate `event_id` replay | MEDIUM | Added `_seen_event_ids` deduplication set and replay rejection on ledger append | RESOLVED |
| **VULN-06** | Test suite tested non-standard exception on wrong KEM key | LOW | Corrected test to verify NIST FIPS 203 implicit rejection | RESOLVED |

---

## 14. Performance Baseline
Measured on Windows 11 (Python 3.9, standard CPU):
- **ML-KEM-768 Key Generation**: Mean 13.50 ms | Median 12.54 ms | P95 21.09 ms
- **ML-KEM-768 Encapsulation**: Mean 15.99 ms | Median 14.46 ms | P95 25.67 ms
- **ML-KEM-768 Decapsulation**: Mean 17.40 ms | Median 16.77 ms | P95 22.51 ms
- **ML-DSA-65 Key Generation**: Mean 30.69 ms | Median 28.70 ms | P95 51.65 ms
- **ML-DSA-65 Signing**: Mean 115.06 ms | Median 111.12 ms | P95 148.10 ms
- **ML-DSA-65 Verification**: Mean 42.84 ms | Median 32.88 ms | P95 176.06 ms
- **AES-256-GCM Encrypt (100KB)**: Mean 0.33 ms | Median 0.33 ms | P95 0.42 ms
- **AES-256-GCM Decrypt (100KB)**: Mean 0.49 ms | Median 0.39 ms | P95 1.33 ms
- **Release Creation (100KB, 3 Recipients)**: Mean 45.97 ms | Median 45.59 ms | P95 53.92 ms

---

## 15. Exact Commands & Tests Used
```powershell
# Run the complete cryptographic test suite (48 tests)
python -m pytest -v

# Run the performance benchmark
python scripts/benchmark_crypto.py

# Run the end-to-end multi-scenario CLI demo
python demo/end_to_end.py
```

---

## 16. Recommendation & Clean Handoff for Agent 2 (Tardos)
The cryptographic foundation is now robust, verified, and post-quantum compliant.
Agent 2 can immediately proceed with implementing `TardosProvider` within `core/traceability/` adhering to the established `TraceabilityProvider` interface without needing to alter the underlying post-quantum envelope or ledger provenance pipeline.
