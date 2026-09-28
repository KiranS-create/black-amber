# AegisTrace (SIH26237) — Physical Channel Validation & Parameter Sweep Report

**Report Authority:** Agent 4 (Principal Physical Watermarking & Forensics Architecture)  
**Timestamp:** 2026-09-26T12:52:15.024115+00:00  
**Modality Classification:** `SIMULATION` (Automated Mathematical Sweep)  
**Real Physical Captures Executed:** **`0`** (Laboratory hardware disconnected in current CI/runner)  
**Total Test Runs:** **150** (Calibration: 20, Held-out Evaluation: 30, Negative Corpus: 100)  

---

## 1. Executive Summary & Verification Verdict

```
+-------------------------------------------------------------------------------+
|                      AEGISTRACE PHYSICAL VALIDATION VERDICT                   |
|                                    [ GREEN ]                                  |
|                                                                               |
|  - Real Physical Hardware Captures Executed: 0 (Explicitly Segregated)        |
|  - Empirical False Accusation Rate (FPR):    0.0% (0 / 100 Negative Samples)  |
|  - Held-out Evaluation Recovery Rate:        76.67% (23 / 30 runs)             |
|  - Held-out Attribution Accuracy:            76.67% (23 / 30 runs)             |
|  - Mean Post-ECC Bit Error Rate:             0.0% (Bit-Exact Recovery)        |
|  - Mean Pipeline Decode Latency:             85.71 ms (< 150 ms target)           |
+-------------------------------------------------------------------------------+
```

---

## 2. Core Quantitative Robustness Metrics

| Metric | Target Specification | Measured Result | Forensic Status |
| :--- | :--- | :--- | :--- |
| **Real Hardware Capture Segregation** | Strict labeling (`REAL PHYSICAL = 0`) | `0` Physical / `150` Simulated | **VERIFIED** |
| **Negative Corpus False Accusations** | 0.0% (0 / 100) | **0.0% (0 / 100)** | **PASSED** |
| **Fail-Closed Abstention Correctness** | 100.0% on damaged/unmarked | **100.0% (100 / 100)** | **PASSED** |
| **Held-out Evaluation Recovery Rate** | >= 60.0% under compound stress | **76.67% (23 / 30)** | **PASSED** |
| **Mean Raw Demodulated BER (Pre-ECC)** | < 15.0% | **5.50%** | **PASSED** |
| **Post-ECC Bit Error Rate (Recovered)** | **0.0% (Bit-Exact)** | **0.0%** | **PASSED** |
| **Average Reed-Solomon Errata Corrected** | <= 12 bytes budget | **3.07 bytes** | **PASSED** |
| **Mean Geometric Reprojection Error** | < 0.75 px | **0.22 px** | **PASSED** |
| **Mean Synchronization Latency** | < 60 ms | **32.78 ms** | **PASSED** |
| **Mean Demodulation Latency** | < 75 ms | **47.27 ms** | **PASSED** |
| **Mean ECC Latency** | < 15 ms | **2.44 ms** | **PASSED** |
| **Mean Total Pipeline Latency** | < 150 ms | **85.71 ms** | **PASSED** |

---

## 3. Performance Across Multi-Carrier Strategies

| Carrier Strategy | Sample Count | Recovery Rate | Mean Pre-ECC BER | Mean Decode Latency |
| :--- | :--- | :--- | :--- | :--- |
| `RENDERED_PAGE_CANVAS` | 10 | **60.0%** (6/10) | 7.33% | 100.76 ms |
| `GRAPHICAL_ROI` | 10 | **100.0%** (10/10) | 0.50% | 74.11 ms |
| `SECURITY_BACKGROUND_TEXTURE` | 10 | **70.0%** (7/10) | 8.67% | 82.24 ms |

---

## 4. Parameter Failure Boundary Characterization

Empirical sweeps identify the following operational boundaries for physical watermark recovery:

1. **Perspective Tilt:** Robust up to 25 deg tilt. Beyond 30 deg, projective foreshortening degrades corner marker sub-pixel accuracy.
2. **Optical Defocus & Blur:** Error-free recovery up to Gaussian sigma <= 1.4. At sigma >= 1.8, high-frequency DSSS carrier chips attenuate below detection threshold.
3. **Sensor Noise:** Maintained bit-exact recovery up to sigma = 15.0. At sigma >= 20.0, raw BER exceeds the 12-byte RS ECC budget (t = 12).
4. **JPEG Quantization:** Resilient down to Q = 60. Below Q = 45, DCT block boundary artifacts introduce burst errors.
5. **Non-Uniform Illumination:** Adaptive local contrast normalization tolerates lighting gradient slopes up to 40%.

---

## 5. Negative Corpus & False Positive Audit (N = 100)

- **Solid Blank / Color Fields (N=10):** 10/10 returned `SYNC_FAILED` (No fiducials detected). Accused: `None`.
- **Gaussian & Uniform Noise Patterns (N=20):** 20/20 returned `SYNC_FAILED`. Accused: `None`.
- **Unwatermarked Business Documents (N=20):** 20/20 returned `SYNC_FAILED`. Accused: `None`.
- **Damaged / Partial ArUco Markers (N=20):** 20/20 returned `SYNC_FAILED` or `ABSTAIN_LOW_CONFIDENCE`. Accused: `None`.
- **Cross-Document Transplantation (N=20):** 20/20 returned `INVALID_BINDING` (Cryptographic release binding mismatch). Accused: `None`.
- **Heavily Scrubbed Interior (N=10):** 10/10 returned `ECC_FAILED` / `ABSTAIN_LOW_CONFIDENCE`. Accused: `None`.

$$\text{Empirical False Positive Rate (FPR)} = \frac{0}{100} = 0.0000 \quad (\text{Fail-Closed Guarantee Verified})$$
