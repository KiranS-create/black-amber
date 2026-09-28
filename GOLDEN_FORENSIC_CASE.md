# AegisTrace: Golden Forensic Case Replay Specification

**Document ID:** `SIH26237-GOLDEN-CASE-V1`  
**Classification:** RESTRICTED / FORENSIC BENCHMARK  
**Case ID:** `CASE-2026-AEGIS-GOLDEN-01`  
**Evaluation Standard:** SIH Core Attribution & Leak Reconstruction Benchmark  
**Artifact Manifest:** [`artifacts/golden_case/golden_case_manifest.json`](file:///C:/Projects/SIH26237/artifacts/golden_case/golden_case_manifest.json)  

---

## 1. Executive Walkthrough

This document defines two canonical, deterministically reproducible forensic investigation scenarios for AegisTrace:

1. **Scenario 1 (Direct Leak):**  
   A classified document is broadcast-encrypted and distributed to Alice, Bob, and Charlie. Alice independently decrypts the document, generating a recipient-unique dynamic watermark and signing an `ML-DSA-65` decryption receipt committed to the offline permissioned DLT. A leaked copy of Alice's decrypted artifact is provided to an investigator. The forensic engine extracts the watermark, matches the commitment on the ledger, independently verifies the recipient signature and Merkle inclusion proof, and attributes the leak to Alice's identity **without the investigator providing Alice's name**.

2. **Scenario 2 (Downstream Unmonitored Transition):**  
   Alice decrypts and signs her receipt. Alice subsequently transfers the physical or digital document to Bob via an unmonitored channel (off-ledger). The document later leaks to the public. Rather than fabricating that Alice personally executed the downstream leak, AegisTrace reports `LAST_KNOWN_HOLDER` / `DOWNSTREAM_GAP`, preserving strict scientific honesty.

---

## 2. Golden Case 1: Direct Leak Investigation

### 2.1 Document Issuance & Broadcast Encryption
- **Document Title:** `golden_shield.png`
- **Security Label:** `TOP SECRET // NOFORN`
- **Pristine Plaintext Hash (SHA-256):**  
  `3188eb22fa674b9eb98a72834b693358053a47926e84d4ae89e223b2aa1e3cf5`
- **Issuer ID:** `iss_secdef`
- **Encryption Algorithm:** AES-256-GCM under single document key $K_{\text{doc}}$ (256-bit entropy).
- **Authorized Recipients:**
  - Alice Strategic: `rec_38b0e2c5b2b6ecf5` (ML-KEM-768 PK + ML-DSA-65 PK)
  - Bob Logistics: `rec_79e8c71bfa982a10` (ML-KEM-768 PK + ML-DSA-65 PK)
  - Charlie Tactical: `rec_c319e0811e55b62e` (ML-KEM-768 PK + ML-DSA-65 PK)
- **Shared Ciphertext Storage:** $O(1)$ master document ciphertext stored once in `SharedDocumentPayload`.

### 2.2 Independent Decryption & Recipient Signing (Alice)
- **Decryption Client:** `RecipientDecryptionClient` executing inside volatile memory on Alice's workstation.
- **KEM Decapsulation:** Alice uses her private ML-KEM-768 key to decapsulate $K_{\text{doc}}$.
- **Dynamic Watermark Identity:**
  - `session_id`: `ses_20260927_alice_01`
  - `event_id`: `evt_exp_alice_01`
  - `watermark_token`: `5f91b72a088df6c230678d462ab6ee1782e4414df87ba579`
  - `watermark_commitment`: `8a164c09d57a2f24d27192cf2333bd29ebca890c58e8b394142cfeb08b49e08b`
  - `dynamic_codeword`: 128-bit sequence derived from token via HMAC-SHA256 expansion.
- **Embedding Strategy:** 2D spatial direct sequence spread spectrum (DSSS) with 4-corner ArUco fiducials.
- **Visual Equivalence Measured:**
  - $\text{SSIM} = 0.9951 \ge 0.98$
  - $\text{PSNR} = 51.32\text{ dB} \ge 35.0\text{ dB}$
  - Legitimate copy is visually indistinguishable from pristine original.
- **Recipient Digital Signature:**
  - Alice signs canonical payload `AEGIS-DECRYPTION-RECEIPT:v1:{...}` using her **private ML-DSA-65 key**.
  - Server possesses only Alice's public key; server custody of private keys is strictly eliminated.

### 2.3 Offline Permissioned DLT Commitment
- **Receipt ID:** `rcpt_evt_exp_alice_01`
- **Consensus Round:** 3 independent post-quantum validators (`val_1`, `val_2`, `val_3`).
- **Quorum Requirement:** $Q = \lfloor 2 \times 3 / 3 \rfloor + 1 = 3$ votes required and obtained.
- **Block Committed:** Block Height 1, Tip Hash `2a6bc841...`
- **Merkle Tree Inclusion Proof:**
  - Leaf Hash: `_hash_leaf(receipt.compute_receipt_hash())` (prefix `0x00`)
  - Root Hash: `_hash_children(...)` (prefix `0x01`)
  - Status: Cryptographically verified (`proof.verify() == True`).

### 2.4 Autonomous Leak Analysis & Forensic Attribution
The leaked file (`alice_leak_artifact.png`) is presented to the investigator:
1. **Geometric Synchronizer:** Detects 4 ArUco fiducials, estimates homography, rectifies canvas coordinates.
2. **Watermark Demodulator:** DSSS matched-filter extracts 128-bit raw symbol vector; Reed-Solomon $(255, 223)$ corrects optical channel noise; CRC32 verifies integrity.
3. **DLT Query:** In-memory ledger index looks up `watermark_commitment` $\to$ locates `rcpt_evt_exp_alice_01`.
4. **Signature Verification:** Engine verifies Alice's ML-DSA-65 signature against her registered public key.
5. **Merkle Verification:** Audit path to Block 1 Merkle root verifies receipt inclusion.
6. **Directory Resolution:** Engine maps opaque principal `rec_38b0e2c5b2b6ecf5` to enterprise identity `Alice Strategic` (`alice@command.mil`).
7. **Final Security State:** `AttributionState.ATTRIBUTED` with `should_abstain = False`.

---

## 3. Golden Case 2: Downstream Unmonitored Transition

### 3.1 Scenario Description
- **Legitimate Decryption Actor:** Alice Strategic (`rec_38b0e2c5b2b6ecf5`) decrypts and signs her receipt.
- **Unmonitored Transition:** Alice prints or passes the document off-ledger to Bob.
- **Public Leak Occurs:** The document is discovered in the public domain.

### 3.2 System Determination & Honesty Invariant
When the forensic engine analyzes this artifact:
- Watermark extraction recovers Alice's session token and commitment.
- Ledger proof verifies Alice signed the original decryption event.
- **Crucial Distinction:** The system **refuses to fabricate** that Alice personally leaked the file.
- **Forensic Attribution Level:** `LEVEL_2_ORIGINAL_RECIPIENT_IDENTIFIED`
- **Forensic Boundary State:** `LAST_KNOWN_HOLDER`
- **Honesty Declaration Emitted:**
  > `"PROVED: This exact recipient performed this signed decryption event. NOT AUTOMATICALLY PROVED: This human personally leaked the file downstream."`

---

## 4. Deterministic Replay & Independent Verification Instructions

To execute and verify both golden cases deterministically on any air-gapped host:

```powershell
# 1. Run the Golden Case automated tests in pytest
python -m pytest tests/conformance/test_sih_problem_statement_conformance.py -k "test_golden_case" -v

# 2. Re-run the standalone artifact verification script
python scripts/generate_conformance_artifacts.py

# 3. Inspect the verified JSON manifest
cat artifacts/golden_case/golden_case_manifest.json
```

### Expected Output Checklist
- [x] `test_golden_case_1_direct_leak_proven_attribution` **PASSED**
- [x] `test_golden_case_2_unmonitored_downstream_transition` **PASSED**
- [x] Quorum verified: `True`
- [x] Merkle inclusion verified: `True`
- [x] Recipient signature verified: `True`
- [x] Candidate derived autonomously: `Alice Strategic`
- [x] Honesty declaration strictly present in results.
