# SIH26237 — Technical Judge Q&A Defense Guide

This document prepares the team to defend the SIH26237 architecture with absolute mathematical, cryptographic, and engineering honesty.

---

### Q1: Why not just use a normal watermark?
**Answer:**
A conventional single-layer watermark suffers from three fatal flaws:
1. **No Collusion Defense:** If Alice and Bob compare their copies, simple differential subtraction identifies and removes static watermarks.
2. **Fragility at the Analog Hole:** Standard frequency-domain or LSB watermarks do not survive non-uniform smartphone camera tilt, optical lens blur, or print-scan downsampling.
3. **No Non-Repudiation:** A basic watermark does not prove *when* or *by whom* the file was decrypted; a server admin could easily forge a mark to frame a user.

SIH26237 decouples the problem into **Tardos traitor tracing** (mathematical collusion resistance), **ArUco + DSSS + ECC** (optical survivability), and **ML-DSA sovereign signatures** (cryptographic non-repudiation).

---

### Q2: Why Tardos Traitor-Tracing Codes?
**Answer:**
Symmetric Tardos codes provide provable, information-theoretic upper bounds on false accusations ($\epsilon_1$) against arbitrary coalitions of up to $c$ colluders. Rather than relying on heuristic pattern matching, Tardos accumulates continuous symbol-symmetric likelihood scores across a randomized codebook. Our `TardosCapacityPlanner` dynamically sizes the code length $m = 100 \cdot c^2 \cdot \ln(1/\epsilon_1)$ to match the physical carrier’s available capacity.

---

### Q3: Why Post-Quantum Cryptography (ML-KEM / ML-DSA)?
**Answer:**
High-value defense intelligence documents remain sensitive for 10 to 30 years. Under **"Harvest Now, Decrypt Later"** threat models, an adversary intercepting classical RSA-4096 or ECDH releases today can store them and decrypt them once quantum computers reach scale. We implement current NIST standards—**`ML-KEM-768` (FIPS 203)** for key encapsulation and **`ML-DSA-65` (FIPS 204)** for sovereign provenance signatures—incurring only 11.6 ms encapsulation and 20.9 ms verification overhead.

---

### Q4: What happens after printing? How does the watermark survive?
**Answer:**
Printing and smartphone photography introduce geometric perspective skew, sensor blur, and luminance variations. We resolve this in three stages:
1. **Geometric Synchronization:** Four-corner ArUco fiducials establish homography coordinates; OpenCV `warpPerspective` warps the distorted photo back to canonical A4 canvas geometry.
2. **Error-Resilient Modulation:** DSSS spreads watermark bits across spatial luminance blocks.
3. **Error Correction:** Reed-Solomon ($RS(255, 223)$) ECC corrects up to 16 byte symbol errors caused by optical blur or dot-gain.

---

### Q5: What happens if an attacker crops the document?
**Answer:**
- **Minor to Moderate Crop ($\le 20\%$):** DSSS spatial redundancy and distributed tile layout allow signal recovery from remaining intact quadrants.
- **Severe Crop ($> 30\%$):** When critical synchronization or carrier blocks are missing, the Attack-Aware Reliability module detects high BER/crop ratio and scales down confidence. The engine cleanly transitions to **`INSUFFICIENT_EVIDENCE`** or **`NO_SIGNAL`**, refusing to make a random guess.

---

### Q6: What happens if recipients collude?
**Answer:**
If $c$ recipients (e.g. Alice and Bob) combine their watermarked copies using majority voting, interleaving, or min/max symbol erasure, the Tardos score accumulator maintains a formal Chernoff bound ensuring that with probability $\ge 1 - \epsilon_1$, at least one of the true colluders exceeds the attribution threshold while innocent non-colluders (e.g. Charlie) remain below the threshold.

---

### Q7: Can a malicious server administrator forge recipient provenance to frame someone?
**Answer:**
**No.** We enforce **Sovereign Recipient Key Custody**. Recipient private decapsulation (`ML-KEM`) and signing (`ML-DSA`) keys are held exclusively on client endpoints. The server only receives an `ML-DSA-65` digital signature produced by the recipient's private key during legitimate client decryption. A rogue administrator cannot forge this signature without compromising the recipient's private key.

---

### Q8: Why does the system abstain? Isn't an attribution system supposed to always give an answer?
**Answer:**
In forensic and legal contexts, **a false accusation is vastly more damaging than an abstention**. Legacy systems that force a binary output (Guilty/Not Guilty) produce catastrophic false convictions when presented with noisy, tampered, or untracked documents. Our engine implements a **Zero-Trust Fail-Closed Policy**: it requires both a high score ($S \ge 6.0$) and a candidate separation margin ($\Delta = S_{(1)} - S_{(2)} \ge 2.5$) corroborated by primary cryptographic markers before issuing an `ATTRIBUTED` verdict.

---

### Q9: How do you avoid double-counting correlated evidence?
**Answer:**
We construct an **Evidence Dependency Graph**. When an extraction yields a physical watermark bitstream and subsequently calculates a Tardos score from that same bitstream, the Tardos observation is registered as a derived child node. The engine enforces the **Maximum Evidentiary Bound**:
$$\text{Score}_{\text{cluster}} = \max_{n \in \text{Tree}}(\rho_n \cdot \text{LLR}_n(c))$$
Parent and child observations cannot additively sum their weights. Furthermore, automated payload fingerprinting deduplicates identical re-submissions.

---

### Q10: What happens if the watermark and Tardos signals disagree?
**Answer:**
If independent channels yield contradictory conclusions (for example, Watermark indicates Alice but Provenance Ledger indicates Bob), the Conflict Detection module flags this anomaly. Rather than averaging out the conflict, the engine outputs an explicit **`CONFLICT`** decision state with full explanatory audit diagnostics, halting automated attribution and alerting forensic investigators.

---

### Q11: What is actually novel vs. what is reused from open source?
**Answer:**
- **Reused Foundations:** Standard implementations of NIST ML-KEM/ML-DSA, Tardos mathematical codebook formulas, Reed-Solomon algorithms, and OpenCV ArUco modules.
- **Our Novel System Contributions:**
  1. The unified release-to-physical provenance binding pipeline.
  2. Transitive derivation tree bounding (Anti-Double-Counting) in evidence fusion.
  3. Dynamic attack-aware reliability attenuation with strict candidate separation margins ($\Delta \ge 2.5$).
  4. The 5-state fail-closed decision protocol (`ATTRIBUTED`, `NO_SIGNAL`, `INSUFFICIENT_EVIDENCE`, `CONFLICT`, `REVIEW_REQUIRED`).
  5. 100% offline, air-gapped, zero-cloud turnkey deployment architecture.

---

### Q12: How was robustness tested in your laboratory?
**Answer:**
We built an automated Adversarial Attack Laboratory executing sweeps across:
- **Digital Image Attacks:** JPEG recompression ($Q=10 \dots 95$), resizing ($25\% \dots 75\%$), rotation ($0.5^\circ \dots 5^\circ$), perspective transforms.
- **PDF Structural Attacks:** Stream recompression, vector stripping, page rasterization.
- **Simulated Physical Channel:** Camera sensor blur, non-uniform ambient illumination, perspective tilts.
- **Integrity Attacks:** Replayed signatures, forged hashes, corrupted metadata.

---

### Q13: What is the status of simulated vs. physical hardware validation?
**Answer:**
To maintain absolute scientific honesty:
- All automated benchmark numbers in our test suite reflect **Simulated Optical Capture** (`PrintCameraSimulationAttack`).
- Real physical printing on laser/inkjet hardware and smartphone photography must be performed in a physical laboratory environment.
- Our repository includes a completed, validated ingestion harness (`scripts/watermark/ingest_physical_capture.py`) ready to ingest and evaluate physical captures according to standard schemas.

---

### Q14: Can you explain the 74.0% result reported in the Evidence Fusion audit?
**Answer:**
The **74.0% decision match rate** was measured on a **100-scenario held-out evaluation split** under extreme multi-attack adversarial stress testing. In this synthetic benchmark, 26% of scenarios involved severe compound attacks (e.g. 50% crop combined with foreign watermark injection and heavy blur). In those 26% corrupted cases, the engine chose to **abstain (`INSUFFICIENT_EVIDENCE` / `CONFLICT`)** rather than make a false attribution. Across all 100 held-out evaluation scenarios, there were **zero false accusations** against innocent recipients when primary cryptographic markers were required.

---

### Q15: What are the current limitations of the system?
**Answer:**
1. **Physical Hardware Coverage:** Physical print/scan validation requires hardware laboratory execution.
2. **Heuristic Parameters:** Soft channel weights $\rho_i$ and dependency discounting $\gamma = 0.65$ are heuristic policy bounds tuned for risk-averse security rather than closed-form joint covariances.
3. **Local Prototype Deployment:** Current key custody is implemented on client endpoints; production enterprise rollout will integrate hardware security modules (HSMs) and PKCS#11 tokens.
