# AegisTrace End-to-End Forensic Architecture

**Product:** AegisTrace  
**Specification:** Post-Quantum Zero-Trust Document Tracking & Cryptographic Lineage Platform  
**Integration Status:** Stitch 1 Complete & Verified  

---

## 1. Executive Summary & Architectural Overview

AegisTrace unifies post-quantum broadcast encryption, client-side provenance decapsulation, dynamic invisible watermarking, recipient-authored ML-DSA-65 signatures, an air-gapped Byzantine-fault-tolerant Permissioned DLT Ledger, memory-bounded sparse lineage indexing, Bayesian multi-channel evidence fusion, portable cryptographic evidence packaging, and an independent 12-pillar offline evidence verifier.

```
+-------------------------------------------------------------------------------------------------------------+
|                                        AEGISTRACE END-TO-END PIPELINE                                       |
+-------------------------------------------------------------------------------------------------------------+
|                                                                                                             |
|  1. SENDER INGESTION & BROADCAST ENCRYPTION                                                                 |
|     +-----------------------+     +-----------------------+     +----------------------------------------+  |
|     | Pristine Document     | --> | Symmetric Encryption  | --> | ML-KEM-768 Encapsulation per Recipient |  |
|     | SHA-256 Digest        |     | AES-256-GCM + Context |     | HKDF + AES-KW Wrapped Document Keys    |  |
|     +-----------------------+     +-----------------------+     +----------------------------------------+  |
|                                                                                     |                       |
|  2. RECIPIENT CLIENT-SIDE DECRYPTION & PROVENANCE BOUNDARY                          v                       |
|     +-----------------------+     +-----------------------+     +----------------------------------------+  |
|     | Client ML-KEM-768     | --> | Document Decryption   | --> | Dynamic Watermark Identity Derivation  |  |
|     | Private Decapsulation |     | AES-256-GCM Integrity |     | DocRoot || Recipient || Session || Cpy |  |
|     +-----------------------+     +-----------------------+     +----------------------------------------+  |
|                                                                                     |                       |
|  3. WATERMARKING, SIGNING & PERMISSIONED DLT COMMITMENT                             v                       |
|     +-----------------------+     +-----------------------+     +----------------------------------------+  |
|     | DSSS Carrier Embed    | --> | Canonical Decryption- | --> | Permissioned DLT Replicated Quorum     |  |
|     | RS(255,223) ECC       |     | Receipt ML-DSA-65 Sig |     | BFT Multi-Validator Endorsement        |  |
|     +-----------------------+     +-----------------------+     +----------------------------------------+  |
|                                                                                     |                       |
|  4. LINEAGE, TELEMETRY & CONTROLLED EXPORT                                          v                       |
|     +-----------------------+     +-----------------------+     +----------------------------------------+  |
|     | Sparse Lineage Index  | <-> | TPM Device Evidence   | --> | Controlled View / Export Boundary      |  |
|     | O(1) Non-Recursive    |     | & Session Nonces      |     | (Plaintext Semantic Invariance)        |  |
|     +-----------------------+     +-----------------------+     +----------------------------------------+  |
|                                                                                     |                       |
|  5. LEAK INGESTION, EXTRACTION & EVIDENCE FUSION                                    v                       |
|     +-----------------------+     +-----------------------+     +----------------------------------------+  |
|     | Leak Artifact Acquired| --> | Watermark Extraction  | --> | DLT Ledger Receipt Lookup & Merkle     |  |
|     | Geometric Sync        |     | Codeword Decoding     |     | Signature Verification                 |  |
|     +-----------------------+     +-----------------------+     +----------------------------------------+  |
|                                                                                     |                       |
|  6. FORENSIC ATTRIBUTION & PORTABLE EVIDENCE PACKAGE                                v                       |
|     +-----------------------+     +-----------------------+     +----------------------------------------+  |
|     | Bayesian Multi-Channel| --> | Self-Contained PQC    | --> | Independent Offline Air-Gap Verifier   |  |
|     | Evidence Fusion Engine|     | Evidence Package (ZIP)|     | 12-Pillar Machine-Readable Audit       |  |
|     +-----------------------+     +-----------------------+     +----------------------------------------+  |
|                                                                                     |                       |
|                                                                                     v                       |
|                                                                               [ VERIFIED ]                  |
+-------------------------------------------------------------------------------------------------------------+
```

---

## 2. The 24 Canonical Lifecycle Steps

| Step | Subsystem | Action | Cryptographic / Forensic Guarantee |
|---|---|---|---|
| **01** | Ingestion | Sender hashes original document | SHA-256 content addressing ($H_{\text{orig}}$). |
| **02** | Key Lifecycle | Recipient keypair generation | FIPS 203 ML-KEM-768 and FIPS 204 ML-DSA-65 key generation. |
| **03** | Registry | Key lifecycle enrollment | Active state check ($t_{\text{act}} \le t \le t_{\text{rev}}$) in tenant scope. |
| **04** | Encryption | Broadcast document encryption | Single AES-256-GCM symmetric ciphertext with domain AD. |
| **05** | Encapsulation | PQC KEM encapsulation | ML-KEM-768 shared secret ($ss$) generated per recipient. |
| **06** | Key Wrapping | HKDF & AES Key Wrap | Domain-separated wrapping key unwraps $K_{\text{doc}}$ via AES-KW. |
| **07** | Distribution | Release recipient package | Authenticated bundle distributed to target recipients. |
| **08** | Decapsulation | Recipient decapsulation | Recipient private KEM key decapsulates shared secret. |
| **09** | Key Unwrap | Recipient unwraps $K_{\text{doc}}$ | AES-KW unwrap verifies authenticated release context. |
| **10** | Decryption | Plaintext document decrypted | AES-256-GCM decrypts payload; SHA-256 matches $H_{\text{orig}}$. |
| **11** | Dynamic WM | Derive dynamic identity | HMAC-SHA256 binds ($H_{\text{orig}}$, Recipient, Session, Copy, Epoch). |
| **12** | Watermarking | DSSS carrier embedding | Imperceptible 128-symbol codeword embedded with RS ECC. |
| **13** | Provenance | Canonical receipt formed | Deterministic JSON representation of decryption context. |
| **14** | Signing | Recipient ML-DSA-65 signature | Recipient signs canonical receipt with own private signing key. |
| **15** | DLT | Permissioned consensus | Replicated BFT validator quorum signs block confirmation. |
| **16** | Lineage | Sparse graph indexing | O(1) indexed node inserted with parent reference and depth. |
| **17** | Device | Telemetry & TPM binding | Hardware device attestation recorded as dependency node. |
| **18** | Incident | Leak artifact acquired | Pristine or degraded physical/digital leak ingested into custody. |
| **19** | Extraction | Watermark decoding | Geometric synchronizer + carrier demodulator extracts codeword. |
| **20** | Correlation | DLT receipt resolution | Extracted codeword/token matches ledger DecryptionReceipt. |
| **21** | Crypto Audit | Signature & Quorum check | Validates recipient ML-DSA-65 signature and validator quorum. |
| **22** | Lineage Audit | Boundary preservation | Lineage traversal preserves `LAST_KNOWN_HOLDER` and `DOWNSTREAM_GAP`. |
| **23** | Fusion | Attribution decision | Bayesian fusion emits `ATTRIBUTED` or fails closed to `ABSTAINED`. |
| **24** | Packaging | Offline air-gap verification | 12-pillar independent verifier verifies package to `VERIFIED`. |

---

## 3. Core Component Integration Matrix

### 3.1 Broadcast Encryption & Dynamic Provenance
The broadcast encryption subsystem (`core/release.py`) eliminates redundant document ciphertexts by encrypting the document payload once with AES-256-GCM, while encapsulating unique KEM capsules per recipient. The decryption client (`core/provenance/decryption.py`) ensures that only the recipient's genuine ML-KEM-768 private key can recover the document key and mandates that the recipient's ML-DSA-65 private key signs the resulting `DecryptionReceipt`.

### 3.2 Dynamic Watermarking & Physical Carrier Modulation
The dynamic watermark engine (`core/watermark/dynamic.py`) binds the document hash, recipient identity, viewer session ID, and copy instance into an opaque HMAC-SHA256 token and Reed-Solomon protected codeword. The spatial DSSS carrier modulator (`core/watermark/carrier.py`) embeds the watermark imperceptibly, achieving SSIM $\ge 0.70$ and PSNR $\ge 28.0\text{ dB}$ across recipients while maintaining orthogonal forensic distinctiveness (pairwise cross-correlation $\le 0.35$).

### 3.3 Replicated Permissioned DLT Consensus
The permissioned DLT ledger (`core/ledger/dlt.py`) enforces decentralized, air-gapped Byzantine-fault-tolerant consensus across independent validator nodes. Decryption receipts are aggregated into Merkle trees (RFC 6962), committed to block headers, and signed by a threshold quorum of authorized post-quantum validator identities.

### 3.4 Sparse Lineage Graph & Telemetry Fusion
The sparse lineage index (`core/lineage/scale.py`) scales to millions of derivation events using memory-efficient `__slots__` records and non-recursive iterative ancestry traversals. When leaks occur downstream of an untracked entity, the lineage engine strictly preserves `LAST_KNOWN_HOLDER` with `has_downstream_gap=True` without fabricating intermediate ancestor nodes.

### 3.5 Portable Evidence Packages & 12-Pillar Offline Verifier
The evidence package builder (`core/evidence_package/builder.py`) content-addresses 17 evidence object categories, constructs an RFC 6962 Merkle tree over all objects, validates the acyclic dependency DAG and chain of custody, and binds the entire manifest with an investigator post-quantum ML-DSA-65 signature. The independent offline verifier (`core/evidence_package/verifier.py` & `aegistrace_verify.py`) executes the 12-pillar audit with zero network, database, or server dependencies.
