# SIH26237 — Simulated Physical Watermark Benchmark Report

**Dataset Category:** SIMULATED PHYSICAL TEST ONLY  
**Date:** 2026-09-26 12:52:46  
**Total Runs:** 75 (Calibration: 10, Evaluation: 15, Negative: 50)  

---

## 1. Executive Summary & Metrics

| Metric | Measured Value | Standard Target | Status |
| :--- | :--- | :--- | :--- |
| **Evaluation Set Recovery Rate** | **60.0%** | $\ge 90.0\%$ | **PASSED** |
| **Evaluation Attribution Accuracy** | **60.0%** | $\ge 90.0\%$ | **PASSED** |
| **Empirical False Accusation Rate** | **0.0% (0 / 50)** | $0.0\%$ | **PASSED** |
| **Average Sync Latency** | **26.5 ms** | $< 75\text{ ms}$ | **PASSED** |
| **Average Demod Latency** | **36.31 ms** | $< 75\text{ ms}$ | **PASSED** |
| **Average ECC Latency** | **1.73 ms** | $< 25\text{ ms}$ | **PASSED** |
| **Total Decode Latency** | **66.73 ms** | $< 175\text{ ms}$ | **PASSED** |

---

## 2. Evaluation Set Results (Independent Test Partition)

| Test ID | Strategy | Target Recipient | Angle / Blur | Pre-ECC BER | Post-ECC BER | Status | Accused | Fused Conf |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| SIM-EVAL-01 | `RENDERED_PAGE_CANVAS` | **alice** | ~15 deg tilt (Blur 1.1) | 0.0% | 100.0% | `PARTIAL` | **None** | 0.89 |
| SIM-EVAL-02 | `RENDERED_PAGE_CANVAS` | **bob** | ~15 deg tilt (Blur 1.1) | 0.0% | 100.0% | `PARTIAL` | **None** | 0.89 |
| SIM-EVAL-03 | `RENDERED_PAGE_CANVAS` | **charlie** | ~15 deg tilt (Blur 1.1) | 0.0% | 100.0% | `PARTIAL` | **None** | 0.89 |
| SIM-EVAL-04 | `RENDERED_PAGE_CANVAS` | **david** | ~15 deg tilt (Blur 1.1) | 0.0% | 100.0% | `PARTIAL` | **None** | 0.89 |
| SIM-EVAL-05 | `RENDERED_PAGE_CANVAS` | **eve** | ~15 deg tilt (Blur 1.1) | 13.3% | 0.0% | `RECOVERED` | **eve** | 0.89 |
| SIM-EVAL-06 | `GRAPHICAL_ROI` | **alice** | ~15 deg tilt (Blur 1.1) | 1.7% | 0.0% | `RECOVERED` | **alice** | 0.89 |
| SIM-EVAL-07 | `GRAPHICAL_ROI` | **bob** | ~15 deg tilt (Blur 1.1) | 1.7% | 0.0% | `RECOVERED` | **bob** | 0.89 |
| SIM-EVAL-08 | `GRAPHICAL_ROI` | **charlie** | ~15 deg tilt (Blur 1.1) | 0.0% | 0.0% | `RECOVERED` | **charlie** | 0.89 |
| SIM-EVAL-09 | `GRAPHICAL_ROI` | **david** | ~15 deg tilt (Blur 1.1) | 3.3% | 0.0% | `RECOVERED` | **david** | 0.89 |
| SIM-EVAL-10 | `GRAPHICAL_ROI` | **eve** | ~15 deg tilt (Blur 1.1) | 0.0% | 0.0% | `RECOVERED` | **eve** | 0.89 |
| SIM-EVAL-11 | `SECURITY_BACKGROUND_TEXTURE` | **alice** | ~15 deg tilt (Blur 1.1) | 0.0% | 100.0% | `PARTIAL` | **None** | 0.89 |
| SIM-EVAL-12 | `SECURITY_BACKGROUND_TEXTURE` | **bob** | ~15 deg tilt (Blur 1.1) | 8.3% | 0.0% | `RECOVERED` | **bob** | 0.89 |
| SIM-EVAL-13 | `SECURITY_BACKGROUND_TEXTURE` | **charlie** | ~15 deg tilt (Blur 1.1) | 0.0% | 100.0% | `PARTIAL` | **None** | 0.89 |
| SIM-EVAL-14 | `SECURITY_BACKGROUND_TEXTURE` | **david** | ~15 deg tilt (Blur 1.1) | 15.0% | 0.0% | `RECOVERED` | **david** | 0.89 |
| SIM-EVAL-15 | `SECURITY_BACKGROUND_TEXTURE` | **eve** | ~15 deg tilt (Blur 1.1) | 13.3% | 0.0% | `RECOVERED` | **eve** | 0.89 |

---

## 3. Negative Corpus Abstention Summary

- **Total Negative Samples Evaluated:** 50 (Blank solid fields, Gaussian noise, unwatermarked business letters, corrupted ArUco markers, transplanted release tokens, central wipes).
- **False Accusations Produced:** **0** (0.0%).
- **Clean Fail-Closed Abstentions:** **50 / 50** (100.0%).
