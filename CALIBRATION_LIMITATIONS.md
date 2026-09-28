# AegisTrace — Forensic Calibration Boundaries & Operational Limitations

## 1. Classification of Evidentiary Claims

To prevent overclaiming in technical and judicial contexts, all performance statements in AegisTrace are categorized under strict epistemic tags:

| Epistemic Tag | Definition | Examples in AegisTrace |
| :--- | :--- | :--- |
| **`OBSERVED`** | Directly measured empirical result on a finite, verified evaluation corpus. | $0$ false positives observed across $N = 200$ negative test samples. |
| **`ESTIMATED`** | Statistical point estimates and confidence intervals derived from empirical observations. | Wilson $95\%$ upper confidence bound on FPR is $1.88\%$. |
| **`THEORETICAL`** | Closed-form mathematical bounds derived from cryptographic or coding-theory theorems. | Tardos false-accusation probability $\epsilon_1 \le e^{-c_1 m}$ (Chernoff bound). |
| **`PROJECTED`** | Scaled extrapolation based on asymptotic models. | Projected threshold requirement $S_{\text{min}}(N) = 15.21$ for $N = 10,000$ candidates. |
| **`NOT_VERIFIED`** | Operational capabilities that require physical hardware testbeds not present in the current software execution environment. | Real-world optical recovery from physical smartphone camera shots on laser-printed paper. |

---

## 2. Explicit Operational Boundaries & Limitations

### A. Physical Print-Camera Capture Testbed Limitation
- **Status**: **`NOT_VERIFIED`** (Physical Hardware) / **`OBSERVED`** (Digital Print-Camera Simulation).
- **Limitation**: AegisTrace includes simulated print-camera transforms (perspective homography warps, lighting gradients, optical blur, JPEG recompression, sensor noise). However, real-world physical captures depend on specific printer toner absorption, paper grain, smartphone lens distortion, and ambient illuminance. Without physical hardware testbench captures, physical hardware FPR/FNR remains unverified.

### B. The Downstream Honesty Boundary
- **Status**: **`OBSERVED`** (Honesty Invariant Enforced).
- **Limitation**: If Recipient $A$ decrypts a document, generates an authorized copy, and gives a physical printout or raw monitor photograph to Person $X$ (off-ledger), the system cannot mathematically identify Person $X$. The engine attributes the leak to **Recipient $A$ as the Last Known Holder** (`LAST_KNOWN_HOLDER`), explicitly documenting the downstream custody gap. It strictly refuses to guess or fabricate downstream actors.

### C. Account Compromise vs Device Attestation
- **Status**: **`OBSERVED`**.
- **Limitation**: If an attacker steals Recipient $A$'s enterprise credentials and signs in from an un-enrolled device or Bob's workstation, the engine flags `REVIEW_REQUIRED` (or `ACCOUNT_DEVICE_MISMATCH`). Forensic evidence identifies that Recipient $A$'s key signed the decryption receipt, but highlights the attestation anomaly to alert investigators to possible account compromise.

### D. Finite Sample Uncertainty Bounds
- **Status**: **`ESTIMATED`**.
- **Limitation**: Observing $0$ false positives across $200$ negative samples does not prove that the system will never produce a false positive on $1,000,000$ unseen adversarial artifacts. It provides a formal $95\%$ upper bound of $1.83\%$ (Clopper-Pearson exact). Larger negative corpora are required to asymptotically tighten the bound.
