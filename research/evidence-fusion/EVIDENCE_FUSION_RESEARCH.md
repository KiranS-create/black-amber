# SIH26237 — Multi-Channel Evidence Fusion & Forensic Attribution Research

**Author**: Agent 5 (Principal Security Architecture + Evidence Fusion Engineer)  
**Date**: 2026-09-26  
**Status**: Completed Baseline Research & Architecture Selection  
**Workstream**: Multi-Channel Evidence Fusion & Fail-Closed Attribution  

---

## Executive Summary

In cryptographic leak attribution, a leaked artifact rarely presents a single, unequivocal, uncorrupted piece of evidence. In operational environments, security teams receive heterogeneous, noisy, and potentially adversarial signals across multiple channels:
1. **Traitor-Tracing Codewords** (e.g. Tardos continuous scores, binary symbol observations, accusation thresholds)
2. **Physical/Digital Watermarks** (e.g. recovered payloads, bit error rates, synchronization correlation, print-cam channel status)
3. **Decryption Provenance Records** (e.g. post-quantum ML-DSA-65 signed decryption events, anti-replay nonces)
4. **Tamper-Evident Ledger Chains** (e.g. SHA-256 hash-chain tip verification, sequence continuity)
5. **Cryptographic Integrity & Envelope Authentication** (e.g. ML-KEM-768 decapsulation, AES-256-GCM authentication tags)
6. **Document Structural Evidence** (e.g. release markers, trailer blocks, metadata dictionaries)
7. **Adversarial Attack Context** (e.g. JPEG recompression, perspective distortion, crop, print-to-camera capture)

A critical failure mode in multi-sensor security systems is **naive score summation** (e.g. summing raw confidence percentages or $p$-values without accounting for dependencies or signal degradation), which leads to **evidence double-counting**, **vulnerability to framing attacks**, and **false accusations**.

Our primary objective is to build a **rigorous, explainable, and fail-closed evidence fusion architecture**. This document surveys mature forensic evidence evaluation frameworks, probabilistic fusion formalisms, and belief aggregation theories to establish our design decisions.

---

## 1. Survey of Evidence Fusion Formalisms & Frameworks

| Methodology / Framework | Theoretical Basis | Key Strengths | Key Weaknesses | Suitability for SIH26237 | Decision |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ENFSI Guideline / Likelihood Ratio (LR) Framework** | Bayesian Decision Theory & Evidentiary Likelihood Ratios ($\text{LR} = \frac{P(E \mid H_p)}{P(E \mid H_d)}$) | International gold-standard in forensic science (ENFSI, NIST). Clearly separates evidence strength from prior odds. Transparent and court-admissible. | Requires explicit modeling of alternative hypotheses ($H_d$) and background error distributions. | **Extremely High**: Directly models propositions (e.g. "Recipient $X$ leaked" vs "Unknown attacker forged mark") and transparently combines independent channels via log-likelihood multiplication. | **ADAPT** |
| **Dempster-Shafer Theory of Evidence (DST)** | Belief functions ($\text{Bel}(A)$), Plausibility ($\text{Pl}(A)$), and Dempster's Rule of Combination | Explicitly represents epistemic ignorance ($m(\Theta)$), missing information, and conflicting evidence. Distinguishes "lack of evidence" from "evidence of innocence". | High computational complexity for large candidate spaces. Sensitive to total conflict ($\kappa \to 1$) unless regularized (e.g. Yager, Smets Transferable Belief Model). | **High**: Excellent for modeling missing provenance vs affirmative proof of tampering, and detecting irreconcilable conflicts between channels. | **ADAPT** |
| **Reliability-Aware Weighted Score Fusion** | Multi-Criteria Decision Analysis (MCDA) with dynamic reliability weighting ($w_i(A)$) | Computationally lightweight, deterministic, explainable, and easily parameterized by attack severity metrics (e.g. crop %, JPEG quality, noise). | Can degenerate into arbitrary heuristic weights if not bounded by calibration thresholds. | **High**: Ideal as a deterministic operational engine with strict margin and threshold enforcement. | **ADAPT** |
| **Probabilistic Graphical Models (Bayesian Networks)** | Directed Acyclic Graphs (DAG) representing conditional dependencies | Naturally handles complex dependency topologies and derived evidence without double-counting. | Complex state space specification; requires heavy inference engine (e.g. `pgmpy`) introducing unwanted runtime bloat. | **Medium**: Conceptual dependency modeling is essential, but full PGM solver is over-engineered for our 7-channel scope. | **ADAPT (Graph Topology) / REJECT (Full Solver)** |
| **Deep Learning / Neural Classifier Fusion** | Multi-layer Perceptron / Softmax Classifier | Can learn non-linear cross-channel correlations. | Complete black box. Lacks forensic explainability. Zero provable bounds against false positives. Violates strict non-black-box constraint. | **Unsuitable**: Forensics and court attribution require inspectable, explainable proof, not uncalibrated neural probabilities. | **REJECT** |
| **Simple Heuristic Addition ($\sum w_i S_i$)** | Linear combination of raw scores | Trivial to implement. | Disregards channel dependencies, causes catastrophic double-counting, cannot handle conflict, vulnerable to spoofing. | **Unsuitable**: Dangerous for security attribution. | **REJECT** |

---

## 2. Deep Dive: Selected Hybrid Architecture

To satisfy the requirements of **mathematical soundness, strict fail-closed abstention, zero double-counting, and explainable forensic transparency**, we adopt a **Hybrid Evidentiary Fusion Architecture**:

$$\text{Decision} = \mathcal{P}\Big(\mathcal{F}_{\text{fusion}}\big(\{ \mathcal{O}_i \}, \mathcal{G}_{\text{dep}}, \mathcal{R}_{\text{attack}}\big)\Big)$$

Where:
1. **$\mathcal{O}_i$ (Evidence Observations)**: Structured, typed evidence from each distinct channel with extraction confidence, parameter bounds, and validation checks.
2. **$\mathcal{G}_{\text{dep}}$ (Evidence Dependency Graph)**: Explicit taxonomy classifying signals into `INDEPENDENT`, `PARTIALLY_DEPENDENT`, or `DERIVED` to eliminate double-counting.
3. **$\mathcal{R}_{\text{attack}}$ (Attack-Aware Reliability Modifiers)**: Dynamic reliability discounting factors $\rho_i \in [0, 1]$ computed from observed attack degradation (e.g. high-ratio compression, optical blur, geometric cropping).
4. **$\mathcal{F}_{\text{fusion}}$ (Log-Evidentiary Ratio & Reliability Aggregator)**: Computes calibrated likelihood ratios and candidate margin scores across all registered keyholders.
5. **$\mathcal{P}$ (Fail-Closed Decision Policy)**: Evaluates strict abstention, conflict detection, and candidate separation margin thresholds.

```
+-----------------------------------------------------------------------------------+
|                            EVIDENCE FUSION PIPELINE                               |
+-----------------------------------------------------------------------------------+
                                          |
     +-------------------+----------------+-------------------+-------------------+
     |                   |                |                   |                   |
     v                   v                v                   v                   v
[ Traceability ]   [ Watermark ]   [ Provenance ]     [ Cryptographic ]    [ Ledger & Doc ]
(Tardos/Codeword)  (Payload/BER)   (ML-DSA Signature) (AES-GCM / ML-KEM)   (Chain / Marker)
     |                   |                |                   |                   |
     +-------------------+----------------+-------------------+-------------------+
                                          |
                                          v
                    +-------------------------------------------+
                    |        Attack Context Calibration         |
                    |   (JPEG, Crop, Print-Cam, Noise, Scale)   |
                    +---------------------+---------------------+
                                          |
                                          v
                    +-------------------------------------------+
                    |        Evidence Dependency Filter         |
                    |   (INDEPENDENT vs PARTIAL vs DERIVED)     |
                    +---------------------+---------------------+
                                          |
                                          v
                    +-------------------------------------------+
                    |    Multi-Candidate Evidentiary Scoring    |
                    |  - Reliability-Weighted Likelihood Ratios |
                    |  - Conflict & Discrepancy Detection       |
                    |  - Candidate Separation Margin ($\Delta$) |
                    +---------------------+---------------------+
                                          |
                                          v
                    +-------------------------------------------+
                    |        Fail-Closed Decision Policy        |
                    |  - Score >= Threshold?                    |
                    |  - Margin >= Min Separation?              |
                    |  - Critical Verification Intact?          |
                    |  - Cross-Source Conflict?                 |
                    +---------------------+---------------------+
                                          |
             +----------------------------+----------------------------+
             |                            |                            |
             v                            v                            v
      [ ATTRIBUTED ]                 [ CONFLICT ]                 [ ABSTAIN ]
  (Statistically Proved)        (Irreconcilable Sources)     (NO_SIGNAL / INSUFFICIENT)
```

---

## 3. Evidence Dependency Model & Preventing Double-Counting

A primary vulnerability in naive multi-channel attribution is **double-counting derived signals**. For example:
- A digital watermark payload might contain the Tardos codeword symbols.
- A Tardos accusation score is calculated from those exact symbols.
- A provenance event signs the hash of the marked document.

If an engine adds "+0.95 for watermark" and "+0.95 for Tardos score" and "+0.95 for provenance", it is counting the **same underlying bit pattern three times**.

### 3.1 Three-Tier Dependency Classification
Every evidence observation is explicitly categorized:
1. **`INDEPENDENT`**: The evidence source relies on a distinct physical or cryptographic channel (e.g. ML-DSA-65 signature on the ledger vs. a spatial watermark embedded in document graphics).
2. **`PARTIALLY_DEPENDENT`**: The evidence sources share contextual bindings or channel degradation but evaluate distinct representations (e.g. document trailer structural marker and spatial watermark both affected by PDF page extraction).
3. **`DERIVED`**: The evidence source is a direct mathematical derivative of another observation (e.g. Tardos continuous score computed directly from the extracted watermark bits).

### 3.2 Anti-Double-Counting Fusion Rule
When aggregating evidence for candidate $c$:
- For `INDEPENDENT` channels, evidence log-weights combine additively:
  $$\mathcal{L}_{\text{total}}(c) = \sum_{i \in \text{Independent}} \rho_i \cdot \ln(\text{LR}_i(c))$$
- For `DERIVED` channels, the engine applies the **Maximum Evidentiary Bound**:
  $$\mathcal{L}_{\text{family}}(c) = \max_{j \in \text{Family}} \big(\rho_j \cdot \ln(\text{LR}_j(c))\big)$$
  ensuring that a derived Tardos score and its underlying symbol recovery rate do not artificially inflate attribution confidence.
- For `PARTIALLY_DEPENDENT` channels, correlated components are discounted via a correlation factor $\gamma \in [0.5, 0.8]$:
  $$\mathcal{L}_{\text{partial}}(c) = (1 - \gamma) \cdot \mathcal{L}_1(c) + \gamma \cdot \min(\mathcal{L}_1(c), \mathcal{L}_2(c))$$

---

## 4. Attack-Aware Reliability Calibration

The evidentiary weight of an observation depends fundamentally on the transmission channel and adversarial distortions.

| Attack / Degradation Context | Impact on Evidence Interpretation | Reliability Modifier ($\rho$) Rule |
| :--- | :--- | :--- |
| **Clean Digital Release (No Attack)** | Pristine transmission. Expected BER $\approx 0.0$. Any bit error or missing signature is significant. | $\rho = 1.0$ (Baseline). |
| **Severe JPEG Compression ($Q \le 30$)** | High-frequency DCT coefficients destroyed. High watermark BER is expected due to channel noise, not necessarily forging. | $\rho_{\text{wm}} = \max(0.3, Q/100)$; increases tolerance for BER while requiring higher sync correlation. |
| **Severe Crop ($\ge 30\%$)** | Partial carrier loss. Codeword recovery rate is degraded. Accusation threshold must be recalculated for effective code length $m_{\text{obs}}$. | $\rho_{\text{wm}} = (1 - \text{crop\_fraction})$; enforces length-adjusted thresholding. |
| **Simulated Print-Camera Attack** | Multi-stage distortion. Synthetic evidence labeled `SIMULATED`. | $\rho = 0.85$; explicitly tags decision with simulation caveat. |
| **Physical Hardware Capture** | Genuine real-world optical capture with smartphone camera/scanner. | $\rho = 0.95$; genuine physical robustness evidence. |
| **Cryptographic Tampering (Tag/Sig Failure)** | Adversarial tampering with ciphertext or digital signature. | $\rho_{\text{crypto}} = 0.0$; immediately triggers strict fail-closed ABSTAIN. |

---

## 5. Candidate Separation Margin ($\Delta$) & Multi-Candidate Discipline

A system that accuses candidate $A$ with score 70.1 when candidate $B$ has score 69.9 is fragile and prone to false positives under noisy conditions.

Our engine enforces a **Candidate Separation Margin Rule**:
Let $S_{(1)}$ be the highest candidate score and $S_{(2)}$ be the second-highest score:
$$\Delta = S_{(1)} - S_{(2)}$$

- **Sufficient Separation**: If $S_{(1)} \ge \tau_{\text{attr}}$ and $\Delta \ge \tau_{\text{margin}}$, candidate $(1)$ is eligible for attribution.
- **Insufficient Separation / Ambiguity**: If $S_{(1)} \ge \tau_{\text{attr}}$ but $\Delta < \tau_{\text{margin}}$, the engine refuses to guess and yields **`INSUFFICIENT_EVIDENCE`** (or `REVIEW_REQUIRED`) with candidate ranking diagnostics.

---

## 6. Comprehensive Decision State Semantics

1. **`ATTRIBUTED`**:
   - At least one primary independent evidence source strongly points to recipient $X$.
   - No conflicting reliable source points to a different recipient.
   - Candidate separation margin $\Delta \ge \tau_{\text{margin}}$.
   - All cryptographic integrity and document identity bindings are valid.
   - Overall calibrated confidence $\ge \tau_{\text{attr}}$.
   - `should_abstain: false`.

2. **`NO_SIGNAL`**:
   - Leaked artifact contains zero detectable markers, zero watermark payload, and no traceable signal.
   - Cannot determine origin; clean fail-closed exit.
   - `should_abstain: true`.

3. **`INSUFFICIENT_EVIDENCE`**:
   - Signals are detected, but combined evidentiary weight is below $\tau_{\text{attr}}$, or candidate separation margin $\Delta < \tau_{\text{margin}}$, or critical corroborating provenance is missing.
   - `should_abstain: true`.

4. **`CONFLICT`**:
   - Two or more reliable evidence channels point to mutually exclusive recipients (e.g. Tardos fingerprint indicates Bob, but verified digital watermark payload indicates Charlie).
   - Prevents framing and flags potential collusion or multi-recipient splicing.
   - `should_abstain: true`.

5. **`REVIEW_REQUIRED`**:
   - Highly degraded physical capture or partial collusion anomaly that passes basic integrity but falls in the discretionary forensic review window ($\tau_{\text{review}} \le S < \tau_{\text{attr}}$).
   - `should_abstain: true`.

---

## 7. Component Reuse, Adaptation & Implementation Summary

| Component | Classification | Source / Library | Rationale |
| :--- | :--- | :--- | :--- |
| **Pydantic Data Models** | **REUSE** | `pydantic` v2 | Type validation, serialization, and schema validation. |
| **Vector Math & Matrix Scoring** | **REUSE** | `numpy` v1.26 | Vectorized candidate log-likelihood ratios, distances, and score sorting. |
| **Statistical Calculations** | **REUSE** | `scipy.stats` | Normal/binomial tail probabilities and false-accusation bounds. |
| **Tardos Traceability Provider** | **REUSE** | `core/traceability/provider.py` | Consume existing `TardosAccusationResult` and codebook scoring via public interface. |
| **Attack Result Ingestion** | **REUSE** | `attacks/base.py` / `artifacts/attacks/` | Ingest `AttackResult` and `DegradationMetrics` to calibrate channel reliability. |
| **Provenance & Ledger Verification** | **REUSE** | `core/provenance/` & `core/ledger/` | Verify ML-DSA signatures and SHA-256 ledger integrity. |
| **Evidentiary Dependency Graph** | **IMPLEMENT** | Pure Python in `core/attribution/` | Explicit multi-channel relationship and anti-double-counting filter. |
| **Attack-Aware Calibrator** | **IMPLEMENT** | Pure Python in `core/attribution/` | Parameterized reliability modifiers based on distortion severity. |
| **Fail-Closed Fusion Engine** | **IMPLEMENT** | Pure Python in `core/attribution/` | Multi-candidate score fusion, conflict detector, margin checker, and forensic explanation generator. |

---

## 8. Licensing Compliance

All utilized algorithms and dependencies are 100% permissively licensed:
- Python Standard Library (`math`, `json`, `typing`, `dataclasses`, `enum`)
- `Pydantic` (MIT)
- `NumPy` (BSD 3-Clause)
- `SciPy` (BSD 3-Clause)

No GPL, AGPL, or restrictive proprietary dependencies are introduced.
