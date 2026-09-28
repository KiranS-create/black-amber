# AegisTrace — Forensic Calibration & Statistical Validation Report

## 1. Executive Summary & Forensic Calibration Principles

AegisTrace implements an experimental, empirical error analysis and statistical calibration framework for forensic multi-channel document attribution. In forensic and legal environments, automated attribution algorithms cannot simply report point-estimate accuracies without rigorous uncertainty intervals, formal abstention mechanics, and explicit domain boundaries.

### Core Forensic Invariants:
1. **Never Force an Attribution**: When forensic signals are corrupted, absent, contradictory, or below calibrated decision boundaries, the system transitions to fail-closed abstention (`NO_SIGNAL`, `INSUFFICIENT_EVIDENCE`, `CONFLICT`, or `REVIEW_REQUIRED`).
2. **Honesty Boundary on Unknown Downstream Transitions**: When a cryptographic copy chain exhibits an unmonitored transfer ($A \rightarrow B \rightarrow \text{unknown} \rightarrow \text{leak}$), the engine explicitly declares `LAST_KNOWN_HOLDER` / `DOWNSTREAM_GAP` rather than synthesizing a fraudulent accusation.
3. **Strict Hardware Boundary**: Because physical printer/scanner testbeds require laboratory optical capture rigs, physical hardware recovery is explicitly marked **`NOT_VERIFIED`** in software-only simulation environments.
4. **Empirical Precision Over False Certainty**: False-positive rates are reported strictly as empirical counts ($0 / N_{\text{tested}}$) with 95% Wilson Score and Clopper-Pearson exact binomial confidence bounds.

---

## 2. Formal Decision State Definitions

AegisTrace formalizes seven mutually exclusive forensic attribution outcomes:

| Outcome State | Prerequisites & Conditions | Confidence Behavior | Forbidden Transitions | Audit Representation |
| :--- | :--- | :--- | :--- | :--- |
| **`ATTRIBUTED`** | Valid cryptographic provenance signature, verified DLT quorum, matching document root hash, fused score $S \ge S_{\text{min}}$ (default $\ge 6.0$), candidate separation $\Delta S \ge 2.5$. | High ($\ge 0.95$) or Medium ($\ge 0.85$). | Cannot transition to `ATTRIBUTED` if signature verification fails, document binding mismatches, or candidate margin $\Delta S < 2.5$. | Full cryptographic receipt, Merkle inclusion proof, signature payload hash, and identity summary. |
| **`NO_SIGNAL`** | Carrier artifact contains zero detectable fiducials, carrier textures, or cryptographic headers (clean unwatermarked document or carrier destroyed). | None ($0.0$). | Cannot attribute to any candidate when $0$ symbols are recovered. | Carrier visual metrics, geometric synchronization log, and abstention rationale. |
| **`INSUFFICIENT_EVIDENCE`** | Signal detected but corrupted, uncorrectable ECC errata, or fused log-likelihood score $0 < S < S_{\text{min}}$. | Low or None ($< 0.50$). | Cannot elevate to `ATTRIBUTED` without additional corroborated evidence. | Raw bit error rate (BER), errata count, and margin below threshold. |
| **`CONFLICT`** | Multi-sensor signals point to conflicting candidates ($S_{\text{Alice}} \ge 5.0, S_{\text{Bob}} \ge 5.0$), or document binding hash mismatches target document. | None ($0.0$). | Cannot arbitrarily pick one candidate when conflicting independent channels exist. | Conflict matrix detailing candidate scores and channel origins. |
| **`REVIEW_REQUIRED`** | Boundary case where technical evidence is intact but account/device attestation mismatch suggests potential credential compromise. | Medium ($0.75 - 0.85$). | Cannot produce automated final conviction without human expert audit. | Detailed device anomaly report, session timestamps, and EDR/IdP correlation. |
| **`ABSTAINED`** | Generic fail-closed abstention triggered by policy constraints, expired sessions, or revoked keys. | None ($0.0$). | Forbidden to emit candidate ID. | Policy rule violation record and key revocation timestamp. |
| **`FAILED`** | Malformed input, unparseable byte stream, or unexpected internal execution exception. | None ($0.0$). | Cannot fail open under any circumstance. | Error trace and sanitized diagnostic payload. |

---

## 3. Evaluation Populations (A through L)

The empirical validation suite partitions test cases into 12 rigorous evaluation populations:

```
+-----------------------------------------------------------------------------------+
|                            AEGISTRACE TEST POPULATIONS                             |
+-----------------------------------------------------------------------------------+
| A. Positive / Attributable      | Legitimate release, signed provenance, intact wm |
| B. Negative / Clean Carrier     | Unwatermarked documents, blank pages, pure noise |
| C. Wrong-Recipient Attack       | Forged signature claiming unregistered principal  |
| D. Wrong-Document Transplant    | Watermark from Doc A spliced into Doc B          |
| E. Tampered / Corrupted         | High BER, erased symbols, broken ECC framing     |
| F. Replayed Evidence            | Stale release nonce replayed against new release |
| G. Conflicting Multi-Sensor     | Tardos -> Alice, Spatial Watermark -> Bob        |
| H. Insufficient Evidence        | Sub-threshold SNR, heavy blur, incomplete marker |
| I. Unknown Downstream Hop       | Alice -> Bob -> Unknown -> Leak (Honesty Guard)  |
| J. Account / Device Mismatch    | Alice account authenticated from Bob workstation |
| K. Telemetry Gap                | Valid crypto/watermark with dropped EDR packets  |
| L. Out-of-Envelope Distortion   | Extreme 45° rotation, 90% crop, extreme noise    |
+-----------------------------------------------------------------------------------+
```

---

## 4. Strict Dataset Partitioning & Manifest Isolation

Datasets are deterministically generated and partitioned with zero overlap:
- **`CALIBRATION` (50%, 600 samples)**: Used for tuning thresholds, channel prior weights, and reliability discount factors.
- **`VALIDATION` (25%, 300 samples)**: Used for hyperparameter tuning, grid search validation, and Pareto frontier selection.
- **`HELD_OUT_TEST` (25%, 300 samples)**: Strictly sequestered and evaluated **once** using fixed thresholds to prove generalization without data snooping.

Partition verification:
- Sample ID disjointness: $\text{Calib} \cap \text{Val} = \emptyset$, $\text{Calib} \cap \text{Test} = \emptyset$, $\text{Val} \cap \text{Test} = \emptyset$.
- Content hash disjointness: Verified across all 1,200 evaluation items in [`dataset_manifest.json`](file:///C:/Projects/SIH26237/artifacts/calibration/dataset_manifest.json).

---

## 5. Held-Out Empirical Performance & Error Rates

Results evaluated on `HELD_OUT_TEST` ($N = 300$ samples):

```
+-----------------------------------------------------------------------------------+
|                           HELD-OUT CONFUSION MATRIX                               |
+-----------------------------------------------------------------------------------+
| True Positives (TP) : 100          | False Positives (FP) : 0                     |
| False Negatives (FN): 0            | True Negatives (TN)  : 200                   |
| Abstentions (Valid) : 0            | Abstentions (Neg)    : 200                   |
+-----------------------------------------------------------------------------------+
```

### Classification Metrics:
- **Precision**: $1.0000$ ($95\%\text{ Wilson CI: } [0.9630, 1.0000]$)
- **Recall (Sensitivity)**: $1.0000$ ($95\%\text{ Wilson CI: } [0.9630, 1.0000]$)
- **Specificity**: $1.0000$
- **$F_1$ Score**: $1.0000$
- **Empirical False Positive Rate (FPR)**: $0 / 200$
  - Point Estimate: $0.0000$
  - $95\%$ Wilson Score Interval: $[0.0000, 0.0188]$
  - $95\%$ Clopper-Pearson Exact Interval: $[0.0000, 0.0183]$
- **Empirical False Negative Rate (FNR)**: $0 / 100$
  - Point Estimate: $0.0000$
  - $95\%$ Wilson Score Interval: $[0.0000, 0.0370]$
  - $95\%$ Clopper-Pearson Exact Interval: $[0.0000, 0.0362]$

---

## 6. Abstention-Aware Risk-Coverage Metrics

Because AegisTrace explicitly abstains on ambiguous cases, traditional accuracy is augmented with Selective Accuracy $A_{\text{sel}}$ and Coverage $C$:

$$\text{Coverage } C = \frac{\text{Attributed Decisions}}{\text{Total Inquiries}}$$

$$\text{Selective Accuracy } A_{\text{sel}} = \frac{\text{Correct Attributions}}{\text{Attributed Decisions}}$$

$$\text{Selective Risk } R_{\text{sel}} = 1 - A_{\text{sel}}$$

### Risk-Coverage Pareto Profile:
Across all threshold sweep levels $S_{\text{min}} \in [2.0, 14.0]$:
- At default operational threshold $S_{\text{min}} = 6.0$:
  - Coverage: $0.3333$ ($100\%$ on positive population, $0\%$ on negative/adversarial populations)
  - Abstention Rate: $0.6667$
  - Selective Accuracy: $1.0000$
  - Selective Risk: $0.0000$
  - Conditional False Positives: $0$

---

## 7. Evidence Confidence Calibration (ECE & Brier Score)

Evaluates whether reported posterior probabilities $\hat{p} = \frac{1}{1 + e^{-S}}$ correspond to empirical truth:

- **Expected Calibration Error (ECE)**: $0.0033$ ($0.33\%$)
- **Maximum Calibration Error (MCE)**: $0.0100$ ($1.00\%$)
- **Brier Score**: $0.0001$
- **Brier Skill Score**: $0.9995$

---

## 8. Summary of Validation Artifacts

All machine-readable empirical results are preserved in [`artifacts/calibration/`](file:///C:/Projects/SIH26237/artifacts/calibration/):
1. [`dataset_manifest.json`](file:///C:/Projects/SIH26237/artifacts/calibration/dataset_manifest.json) — Full 1,200 sample cryptographic manifest with split tags.
2. [`threshold_sweep.json`](file:///C:/Projects/SIH26237/artifacts/calibration/threshold_sweep.json) — Multi-parameter grid search across attribution thresholds.
3. [`confusion_matrix.json`](file:///C:/Projects/SIH26237/artifacts/calibration/confusion_matrix.json) — Held-out test confusion matrix and rate summaries.
4. [`coverage_risk.json`](file:///C:/Projects/SIH26237/artifacts/calibration/coverage_risk.json) — Selective accuracy and risk-coverage curve points.
5. [`calibration_metrics.json`](file:///C:/Projects/SIH26237/artifacts/calibration/calibration_metrics.json) — ECE, MCE, Brier score, and 10-bin reliability diagram.
6. [`negative_corpus_results.json`](file:///C:/Projects/SIH26237/artifacts/calibration/negative_corpus_results.json) — Stress test results on 200 negative/adversarial samples.
7. [`positive_corpus_results.json`](file:///C:/Projects/SIH26237/artifacts/calibration/positive_corpus_results.json) — Stress test results on 100 positive samples.
8. [`adversarial_results.json`](file:///C:/Projects/SIH26237/artifacts/calibration/adversarial_results.json) — Security invariant preservation under active attacks.
9. [`temporal_results.json`](file:///C:/Projects/SIH26237/artifacts/calibration/temporal_results.json) — Key rotation, revocation, and session boundary validation.
10. [`recipient_separation.json`](file:///C:/Projects/SIH26237/artifacts/calibration/recipient_separation.json) — Codeword separation across $N \in \{10, 100, 1000\}$ recipients.
11. [`visual_equivalence.json`](file:///C:/Projects/SIH26237/artifacts/calibration/visual_equivalence.json) — SSIM and PSNR distributions across document renders.
12. [`uncertainty_intervals.json`](file:///C:/Projects/SIH26237/artifacts/calibration/uncertainty_intervals.json) — 95% Wilson Score and Clopper-Pearson exact confidence intervals.
