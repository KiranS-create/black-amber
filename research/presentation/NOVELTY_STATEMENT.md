# SIH26237 — System-Level Novelty & Prior Art Differentiation Statement

**Classification:** Technical Defensibility & Intellectual Property Analysis  
**Project:** SIH26237 — Secure Document Distribution, Post-Quantum Provenance & Robust Leak Attribution  
**Audience:** Competition Judges, Cryptographic Evaluators, and Systems Architecture Reviewers  

---

## 1. Executive Statement of Novelty

SIH26237 does **NOT** claim the invention of foundational mathematical algorithms (such as Tardos traitor tracing, Reed-Solomon error correction, NIST ML-KEM/ML-DSA lattice cryptography, or OpenCV ArUco fiducials).

Instead, SIH26237’s core novelty lies in the **unification, architectural synthesis, and fail-closed forensic integration** of these isolated disciplines into a cohesive, air-gapped, post-quantum document distribution and leak attribution platform.

```
                      PRIOR ART (ISOLATED)                              SIH26237 NOVELTY (INTEGRATED)
  +----------------------------------------------------+    +----------------------------------------------------+
  | - Cryptographic envelopes stop at decryption.       |    | Unified release-to-physical provenance binding     |
  | - Watermarking lacks post-quantum non-repudiation. | -> | Sovereign recipient decryption + digital signature |
  | - Traitor tracing assumes clean digital bitstrings.|    | Spatial DSSS + ECC for physical channel recovery   |
  | - Attribution engines naively sum correlated scores|    | Dependency-aware graph fusion (Anti-Double-Count)  |
  | - Legacy systems force binary accusations.         |    | Fail-closed zero-trust decision protocol           |
  +----------------------------------------------------+    +----------------------------------------------------+
```

---

## 2. Component-by-Component Prior Art Differentiation

### A. Post-Quantum Cryptographic Trust Layer

| Component | Standard / Prior Art Foundation | SIH26237 System-Level Contribution |
| :--- | :--- | :--- |
| **Key Encapsulation** | NIST FIPS 203 (`ML-KEM-768` / Kyber) | Ephemeral symmetric document key ($K_{\text{doc}}$) encapsulation per recipient envelope, preventing server-side key reuse. |
| **Digital Signatures** | NIST FIPS 204 (`ML-DSA-65` / Dilithium) | Non-repudiable decryption provenance signing tied to sovereign recipient keypairs and sequential hash-chained ledger. |
| **Symmetric Encryption** | `AES-256-GCM` + `HKDF-SHA256` | Target-bound envelope packaging cryptographically linking `(document_id, release_id, recipient_id, payload_hash)`. |
| **Key Custody Architecture** | Centralized server key management (Legacy DRM) | **Sovereign Client Key Isolation**: The distribution server never generates, stores, or holds custody of recipient private decapsulation or signing keys. |

---

### B. Traitor-Tracing & Collusion Resistance

| Component | Foundational Literature | SIH26237 Implementation & Novelty |
| :--- | :--- | :--- |
| **Traceability Codes** | Symmetric Tardos Codes (*G. Tardos, STOC 2003*; *Skoric et al., 2008*) | Dynamic Capacity Planner (`TardosCapacityPlanner`) mapping physical document carrier capacity (pixels/blocks) to optimal code length ($m$), cutoff parameter ($t$), and false accusation bound ($\epsilon_1$). |
| **Collusion Strategy** | Theoretical Boneh-Shaw / Tardos scoring | Implementation of symbol-symmetric score accumulation with numerical stabilization against divide-by-zero on extreme bias distributions. |
| **Separation Metric** | Single candidate threshold exceeding $\tau$ | **Candidate Separation Margin ($\Delta = S_{(1)} - S_{(2)} \ge 2.5$)**: Prevents false accusations in collusion scenarios where two colluders have close scores. |

---

### C. Physical-Carrier Watermarking & Optical Recovery

| Component | Open-Source / Standard Tools | SIH26237 System-Level Contribution |
| :--- | :--- | :--- |
| **Spatial Modulation** | Direct-Sequence Spread Spectrum (DSSS) | Multi-channel carrier allocation: Rendered Page Canvas, Graphical ROI, and Security Background Textures. |
| **Error Correction** | Reed-Solomon ($RS(255, 223)$ / $RS(63, 31)$) | Bitstream interleaving and block-level redundancy designed to survive non-uniform optical blur and camera tilt. |
| **Geometric Synchronization** | OpenCV ArUco / QR Fiducials | Four-corner ArUco fiducial embedding with perspective homography rectification (`cv2.warpPerspective`) restoring optical captures before signal demodulation. |
| **Physical Channel Strategy** | Uncalibrated optical assumptions | Rigorous separation of **simulated optical channels** (`PrintCameraSimulationAttack`) from **physical laboratory validation protocols**. |

---

### D. Multi-Channel Evidence Fusion Engine (`core/attribution/`)

**This represents the primary algorithmic and systems innovation of the repository.**

```
                                EVIDENCE DEPENDENCY GRAPH
                                
                                [ Document Registration ]
                                           |
                                [ Release Distribution ]
                                           |
                              [ Decryption Provenance Event ]
                                           |
                        +------------------+------------------+
                        |                                     |
              [ Physical Watermark ]                [ Tamper-Evident Ledger ]
                        |                                     |
              (Extracted Bitstream)                 (Merkle Hash Integrity)
                        |                                     |
              [ Derived Tardos Code ]                         |
                        |                                     |
                        +------------------+------------------+
                                           |
                                           v
                              [ Transitive Lineage Bound ]
                             max(Score_watermark, Score_tardos)
                                           |
                                           v
                             [ Fail-Closed Decision Engine ]
```

1. **Transitive Derivation Lineage (Anti-Double-Counting)**:
   - *Problem*: In conventional forensic systems, finding a physical watermark and computing a Tardos score from that same watermark leads to additive score summation ($S_{\text{fused}} = S_{\text{wm}} + S_{\text{tardos}}$), creating false certainty.
   - *SIH26237 Solution*: Derivation tree tracking via `EvidenceDependencyGraph`. Derived evidence is bounded by the **Maximum Evidentiary Bound**:
     $$\text{Score}_{\text{cluster}} = \max_{n \in \text{Tree}}(\rho_n \cdot \text{LLR}_n(c))$$
     Parent and child observations cannot artificially multiply confidence.

2. **Adversarial Deduplication**:
   - Automated payload fingerprinting (`compute_signal_fingerprint()`) collapses repeated identical submissions into a single observation.

3. **Attack-Aware Dynamic Reliability Scaling**:
   - Soft channel weights $\rho_i$ are dynamically attenuated based on detected channel degradation metrics (Bit Error Rate, SSIM, Crop Ratio, Peak Signal-to-Noise Ratio).

4. **Fail-Closed Zero-Trust Decision States**:
   - Rather than forcing a binary output (Guilty / Not Guilty), the engine yields five explicit cryptographic states:
     - `ATTRIBUTED`: Mathematical and cryptographic proof meets strict thresholds with primary corroboration.
     - `NO_SIGNAL`: Unwatermarked or untracked artifact.
     - `INSUFFICIENT_EVIDENCE`: Carrier degraded beyond statistical recovery.
     - `CONFLICT`: Irreconcilable contradictory evidence across independent channels.
     - `REVIEW_REQUIRED`: Primary markers present but candidate separation margin is marginal.

---

## 3. What We Do NOT Claim

To ensure absolute scientific honesty during competition review:

- **We do NOT claim 100% field accuracy under arbitrary destruction**: If an attacker shreds a document or crops 90% of the carrier, the signal is destroyed. The system correctly identifies this state as `NO_SIGNAL` or `INSUFFICIENT_EVIDENCE` and refuses to accuse.
- **We do NOT claim uncalibrated frequentist probabilities**: The fused score represents an ordinal Bayesian log-likelihood ratio bounded by heuristic policy parameters, not a frequentist guarantee of guilt.
- **We do NOT claim complete physical hardware validation in the automated test runner**: All automated test suite metrics reflect simulated optical models (`PrintCameraSimulationAttack`); physical printing and smartphone camera captures are specified via a standalone laboratory ingestion harness (`scripts/watermark/ingest_physical_capture.py`).
- **We do NOT claim unbreakable cryptography**: We implement current NIST FIPS post-quantum standards (`ML-KEM-768`, `ML-DSA-65`).

---

## 4. Summary Table of Defensible Novelties

| Domain | Prior Art Baseline | SIH26237 Defensible Novelty |
| :--- | :--- | :--- |
| **Trust Model** | Post-decryption security gap | Recipient-sovereign ML-KEM/ML-DSA envelope + signed provenance chain |
| **Physical Survivability** | Digital-only bitstrings | ArUco perspective rectification + DSSS spatial carrier modulation |
| **Collusion Defense** | Static watermarking | Dynamic capacity-planned Symmetric Tardos codes with separation margins |
| **Forensic Fusion** | Linear weighted sum (Double-counting risk) | Transitive derivation tree bounding + Conflict detection + Fail-closed abstention |
| **Deployment** | Cloud-dependent / multi-service SaaS | 100% offline, air-gapped, zero-cloud single-command execution (< 350ms startup) |
