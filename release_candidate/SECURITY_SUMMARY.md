# AegisTrace (Black Amber) — Release Candidate Security Summary
**Smart India Hackathon 2026** | **Problem Statement ID:** SIH26237  
**Version:** 1.0.0-rc1 | **Date:** September 28, 2026  

---

## 1. Post-Quantum Cryptographic Grounding

AegisTrace implements the post-quantum standards published by the National Institute of Standards and Technology (NIST) in August 2024:

- **NIST FIPS 203 (ML-KEM):** ML-KEM-768 for multi-recipient asymmetric key encapsulation.
- **NIST FIPS 204 (ML-DSA):** ML-DSA-65 for manifest signing, release authority certification, and recipient decryption provenance receipts.
- **NIST SP 800-38D (AES-GCM):** AES-256-GCM authenticated encryption with 96-bit unique IV for document payloads.
- **RFC 6962:** Double-domain SHA-256 Merkle trees for immutable append-only ledger commitments.

---

## 2. Zero-Trust Perimeter & Air-Gap Enforcement

- **100% Offline Capability:** Complete cryptographic operations, dynamic watermarking, DLT consensus, and offline evidence verification operate with zero internet connectivity.
- **Air-Gap Guard:** Validated by `tests/deployment/test_airgap_guard.py` (outbound socket connections are intercepted and blocked).
- **Client Key Isolation:** Recipient private keys are generated and stored exclusively on client endpoints. The AegisTrace server never holds recipient signing keys.

---

## 3. Red-Team Attack Resistance

The platform was subjected to automated red-team adversarial attacks (Chains A through G):

1. **Collusion Resistance ($c \le 4$):** Tardos arcsine codes detect coalition members with false-positive rate $\epsilon \le 10^{-3}$. When $c > 4$ or mark corruption exceeds $45\%$, the engine strictly abstains (`ABSTAINED`).
2. **Adversarial Framing Defense:** Fabricated or spliced mark substitutions are rejected because attribution requires dual correlation: watermark demodulation **AND** recipient provenance receipt signed by the recipient's ML-DSA-65 private key.
3. **Tamper Rejection Invariant:** Injected bit-flips into evidence packages (corrupted Merkle roots, modified payloads, altered manifests) are immediately detected and rejected with `TAMPER_DETECTED`.
4. **Secret Scanning:** 965 repository files scanned; 0 hardcoded credentials or private keys detected.
