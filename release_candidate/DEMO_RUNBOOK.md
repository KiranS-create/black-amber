# AegisTrace (Black Amber) — Golden Demonstration Runbook
**Smart India Hackathon 2026** | **Problem Statement ID:** SIH26237  
**Version:** 1.0.0-rc1 | **Date:** September 28, 2026  
**Auditor Classification:** Judge Evaluation Script (14-Step Walkthrough)  

---

## 1. Demonstration Overview

This runbook guides an evaluator through the authoritative **14-Step Golden Forensic Demonstration** of AegisTrace. It showcases the complete lifecycle from document authoring to leak detection, multi-channel attribution, tamper defense, and offline courtroom verification.

```bash
# Execute the complete automated 14-step walkthrough:
python scripts/deployment/run_judge_demo.py
# or via master CLI:
python aegistrace.py demo
```

---

## 2. The 14-Step Forensic Execution Sequence

### [STEP 1] Isolated Demo Environment Initialization
- **Action:** Initializes isolated workspace in memory and clean local storage.
- **Output:** Clean ledger instance created with genesis block hash.

### [STEP 2] Master Artifact Registration
- **Action:** Ingests confidential document (`Project_Black_Amber_Spec.pdf`). Computes SHA-256 canonical digest.
- **Invariant:** Master document is registered without pre-existing watermarks.

### [STEP 3] Recipient Cryptographic Enrollment
- **Action:** Enrolls three authorized recipients:
  - **Alice** (Lead Engineer): `ML-KEM-768` Encapsulation Key + `ML-DSA-65` Verification Key.
  - **Bob** (Contractor): `ML-KEM-768` Encapsulation Key + `ML-DSA-65` Verification Key.
  - **Charlie** (External Auditor): `ML-KEM-768` Encapsulation Key + `ML-DSA-65` Verification Key.
- **Cryptographic Grounding:** Conforms to NIST FIPS 203 and FIPS 204.

### [STEP 4] Broadcast Release Creation
- **Action:** Generates release `rel_2026_sih`. Encrypts master payload with ephemeral 256-bit AES-GCM key $K_{\text{doc}}$.
- **Multi-Recipient Encapsulation:** Produces 3 independent KEM ciphertexts ($C_{\text{Alice}}, C_{\text{Bob}}, C_{\text{Charlie}}$).
- **Ledger Invariant:** Release event committed to tamper-evident ledger with RFC-6962 Merkle proof.

### [STEP 5] Recipient Decapsulation & Provenance Signing
- **Action:** Recipient **Bob** accesses release envelope. Bob's client decapsulates $K_{\text{doc}}$ using Bob's private ML-KEM-768 key.
- **Provenance Receipt:** Bob's client creates a canonical `DecryptionReceipt` and signs it using Bob's local private ML-DSA-65 key.
- **Ledger Invariant:** Receipt anchored to ledger; consensus quorum verified.

### [STEP 6] Dynamic Decryption Watermarking
- **Action:** Decryption engine synthesizes a personalized, imperceptible forensic watermark embedding:
  $$\text{Payload} = \{\text{Recipient: Bob}, \text{Release: rel\_2026\_sih}, \text{Timestamp}, \text{Receipt Hash}\}$$
- **Fidelity:** Modulated into DCT/spatial carrier with SSIM $\ge 0.99$. Rendered into decrypted output.

### [STEP 7] Intercepted Leak Ingestion
- **Action:** An unauthorized leak appears (simulated smartphone photograph taken at a $15^\circ$ oblique angle with optical glare, blur, and cropping).
- **Zero-Prior Knowledge:** Leak is ingested into AegisTrace **without investigator-supplied suspect names**.

### [STEP 8] Automated Homography & Distortion Rectification
- **Action:** Computer vision pipeline detects corner registration fiducials, estimates the $3 \times 3$ projective homography matrix $H$, and rectifies perspective distortion back to canonical coordinate space.

### [STEP 9] Blind Watermark Demodulation
- **Action:** Spatial DSSS demodulator correlates pixel residuals with pseudorandom carrier bases. Decodes payload bits through Reed-Solomon $(255, 223)$ error correction.

### [STEP 10] Multi-Channel Evidence Fusion & Attribution
- **Action:** Fusion engine correlates demodulated mark bits with DLT decryption receipts and Merkle inclusion proofs.
- **Result:**
  - Posterior Confidence: **$\ge 99.9\%$** ($p\text{-value} \le 1.2 \times 10^{-9}$)
  - Attributed Culprit: **Bob (Recipient B)**
  - Innocent Exclusion: **Alice** and **Charlie** provably excluded.

### [STEP 11] Standalone Forensic Evidence Package Production
- **Action:** Automatically compiles a sealed, self-contained evidence package (`golden_evidence_package.zip`) containing all 10 canonical artifacts:
  1. `manifest.json` (SHA-256 digests of all package artifacts)
  2. `manifest.sig.json` (ML-DSA-65 signature of Release Authority)
  3. `leak_artifact.raw` (Intercepted leaked document)
  4. `rectified_canvas.png` (Geometrically rectified canonical image)
  5. `demodulated_signal.json` (Extracted mark bits & bit error rates)
  6. `dlt_merkle_proof.json` (RFC-6962 Merkle inclusion proof)
  7. `decryption_receipt.json` (Bob's signed provenance receipt)
  8. `attribution_verdict.json` (Calibrated Bayesian fusion output)
  9. `chain_of_custody.json` (Sequential SHA-256 custody log)
  10. `device_attestation.json` (Device-in-loop hardware telemetry)

### [STEP 12] Independent Offline Verification
- **Action:** Evaluator runs standalone CLI verifier on package:
  ```bash
  python aegistrace_verify.py artifacts/demo/golden_case/golden_evidence_package.zip
  ```
- **Result:** All 11 verification dimensions output **`VALID`** with overall status **`VERIFIED`**.

### [STEP 13] Adversarial Tamper Injection & Fail-Closed Rejection
- **Action:** Simulator injects malicious bit-flips into the evidence package (corrupts the Merkle root or manifest signature).
- **Result:** The offline verifier immediately detects modification and halts:
  $$\text{Verdict} = \mathbf{TAMPER\_DETECTED} \quad (\text{Fail-Closed Defense Invariant})$$

### [STEP 14] Negative Control & Clean Document Abstention
- **Action:** Submits an unwatermarked, external clean document into the forensic pipeline.
- **Result:** Engine detects absence of carrier signal and outputs **`NO_SIGNAL` / `ABSTAINED`**. Demonstrates zero false accusations on negative corpus.
