# SIH26237 Requirement Traceability & Conformance Matrix

**Specification:** Complete System Requirement Verification & Traceability  
**Standard:** ISO/IEC 27037 (Digital Evidence Handling) & NIST SP 800-208 (PQC)  
**Conformance Verdict:** 100% Fully Conforming  

---

## 1. Traceability Matrix

| Requirement ID | Requirement Name | Core Subsystem Module | Primary Test Suite | Verification Status |
|---|---|---|---|---|
| **REQ-01** | **Post-Quantum Cryptography** | `core/crypto/kem.py`, `core/crypto/signatures.py` | `tests/integration_e2e/test_problem_statement_conformance.py` | `VERIFIED` |
| **REQ-02** | **Broadcast Encryption & Key Wrapping** | `core/release.py`, `core/crypto/symmetric.py` | `tests/integration_e2e/test_golden_sih_case.py` | `VERIFIED` |
| **REQ-03** | **Client-Side Provenance & Private Decryption** | `core/provenance/decryption.py` | `tests/integration_e2e/test_golden_sih_case.py` | `VERIFIED` |
| **REQ-04** | **Dynamic Invisible Watermarking** | `core/watermark/dynamic.py`, `core/watermark/carrier.py` | `tests/integration_e2e/test_multi_recipient_equivalence.py` | `VERIFIED` |
| **REQ-05** | **Recipient-Owned ML-DSA-65 Signatures** | `core/provenance/decryption.py`, `core/ledger/dlt.py` | `tests/integration_e2e/test_golden_sih_case.py` | `VERIFIED` |
| **REQ-06** | **Permissioned DLT Consensus & Merkle Inclusion** | `core/ledger/dlt.py` | `tests/integration_e2e/test_dlt_integration.py` | `VERIFIED` |
| **REQ-07** | **Memory-Bounded Sparse Lineage Indexing** | `core/lineage/scale.py` | `tests/integration_e2e/test_lineage_integration.py` | `VERIFIED` |
| **REQ-08** | **Hardware Device Attestation & Telemetry** | `core/evidence_package/models.py` | `tests/integration_e2e/test_telemetry_integration.py` | `VERIFIED` |
| **REQ-09** | **Visual Equivalence vs Forensic Distinction** | `core/integration/equivalence.py` | `tests/integration_e2e/test_multi_recipient_equivalence.py` | `VERIFIED` |
| **REQ-10** | **Robust Watermark Recovery & DLT Lookup** | `core/watermark/pipeline.py`, `core/ledger/dlt.py` | `tests/integration_e2e/test_golden_sih_case.py` | `VERIFIED` |
| **REQ-11** | **Fail-Closed Attribution & Boundary Preservation** | `core/integration/orchestrator.py` | `tests/integration_e2e/test_unknown_downstream_case.py`, `test_insufficient_evidence_case.py` | `VERIFIED` |
| **REQ-12** | **Self-Contained Evidence Packages (17 Schemas)** | `core/evidence_package/builder.py`, `models.py` | `tests/integration_e2e/test_origin_server_absence.py` | `VERIFIED` |
| **REQ-13** | **Independent Air-Gapped Offline Verification** | `core/evidence_package/verifier.py`, `aegistrace_verify.py` | `tests/integration_e2e/test_airgap_e2e.py`, `test_independent_verifier_e2e.py` | `VERIFIED` |
| **REQ-14** | **Multi-Tenant Partition & Isolation** | `core/evidence_package/verifier.py`, `orchestrator.py` | `tests/integration_e2e/test_cross_tenant_e2e.py` | `VERIFIED` |
| **REQ-15** | **Disaster Recovery & State Continuity** | `core/ledger/dlt.py` | `tests/integration_e2e/test_recovery_e2e.py` | `VERIFIED` |

---

## 2. Requirement Proof Summaries

### REQ-01: Post-Quantum Cryptography
- **Implementation:** Genuine FIPS 203 ML-KEM-768 for recipient key encapsulation and FIPS 204 ML-DSA-65 for all digital signatures (recipients, validators, and forensic examiners).
- **Proof:** Zero reliance on legacy RSA or ECC. Verified in `test_req_01_post_quantum_cryptography`.

### REQ-02: Broadcast Encryption
- **Implementation:** Documents encrypted once using AES-256-GCM with authenticated domain-separated associated data (`DOC-RELEASE:rel_id:doc_id`). Individual recipient wrapping keys derived via HKDF-SHA256 wrap the document key via AES-KW.
- **Proof:** Same document ciphertext $C_{\text{doc}}$ distributed across Alice, Bob, and Charlie with unique KEM capsules. Verified in `test_req_02_broadcast_encryption`.

### REQ-04 & REQ-09: Dynamic Watermarking & Visual Equivalence
- **Implementation:** Dynamic identities generated on-the-fly at decryption time binding document root hash, recipient ID, session ID, and copy instance. Spatial DSSS carrier embeds 128-symbol codeword.
- **Proof:** Multi-recipient decryptions achieve $\text{SSIM} \ge 0.70$, $\text{PSNR} \ge 28.0\text{ dB}$, while dynamic codewords exhibit pairwise cross-correlation $\le 0.35$ and distinct tokens. Verified in `test_multi_recipient_equivalence_and_isolation`.

### REQ-05 & REQ-06: Recipient Signatures & Permissioned DLT
- **Implementation:** Recipient client signs canonical `DecryptionReceipt` with own ML-DSA-65 private key. Receipt committed to permissioned DLT ledger where a 3-of-4 validator quorum endorses the block header containing the RFC 6962 Merkle tree.
- **Proof:** Verified in `test_dlt_ledger_consensus_and_merkle_inclusion`.

### REQ-12 & REQ-13: Portable Evidence Packages & 12-Pillar Verifier
- **Implementation:** 17 strongly-typed schemas packaged into `.zip` or directory structure with an RFC 6962 Merkle tree over all content hashes and an ML-DSA-65 signature over the manifest. Audited by `aegistrace_verify.py` with sockets disabled.
- **Proof:** Verified in `test_strict_airgap_pipeline_and_verifier` and `test_independent_verifier_cli_on_zip_and_directory`.
