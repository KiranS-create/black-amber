# SIH26237 — Physical / Print-Camera Watermark Benchmark Report

**Generated:** September 2026  
**Environment:** Windows, Python 3.9, 100% CPU Offline Execution  
**Channel Tested:** Compound Print-Camera Simulation (Perspective 0.06, Blur sigma=1.2, Lighting Gradient 25%, Noise sigma=10, Paper Texture 0.05, Downsample 0.75, JPEG Q=75)  

---

## 1. Quantitative Performance & Accuracy Metrics

| Metric | Measured Value | Requirement / Target | Status |
| :--- | :--- | :--- | :--- |
| **Encoding Latency** | `74.14 ms` | `< 100 ms` | **PASS** |
| **Decoding & Sync Latency** | `91.04 ms` | `< 150 ms` | **PASS** |
| **Tardos Scoring Latency** | `10.26 ms` | `< 25 ms` | **PASS** |
| **Total End-to-End Pipeline Latency** | `175.44 ms` | `< 250 ms` | **PASS** |
| **Visual Quality (PSNR)** | `28.70 dB` | `> 28.0 dB` | **PASS** |
| **Carrier Mean Squared Error (MSE)** | `87.7393` | `< 100.0` | **PASS** |
| **Geometric Reprojection Error** | `0.4486 px` | `< 0.75 px` | **PASS** |
| **Pre-ECC Raw Bit Error Rate (BER)** | `11.67%` | `< 18.0%` | **PASS** |
| **Post-ECC Bit Error Rate** | **`0.0%` (Bit-Exact)** | `0.0%` | **PASS** |
| **Codeword Recovery Rate** | **`100.0%` (125/125 bits)** | `100.0%` | **PASS** |
| **Attribution Verdict** | `ATTRIBUTED (Alice)` | `ATTRIBUTED` | **PASS** |
| **Guilty Score Margin (S_alice - Z)** | `+32.53` | `> 0` | **PASS** |
| **Innocent False Accusations** | **`0` (Zero innocent accused)** | `0` | **PASS** |
| **Unmarked Document False Detection** | **`NO_SIGNAL` (Confidence: 0.0)** | Fail-Closed | **PASS** |

---


## 2. Generated Artifacts

- **Watermarked Document:** `artifacts/watermark/sample_watermarked_document.png`
- **Simulated Camera Photograph:** `artifacts/watermark/sample_captured_simulation.png`
- **Rectified Canonical Canvas:** `artifacts/watermark/sample_rectified_canvas.png`

---

## 3. Physical Channel Telemetry Summary

```json
{
  "sync": {
    "sync_success": true,
    "detected_markers": [
      2,
      1,
      3,
      0
    ],
    "reprojection_error": 0.4486018717288971,
    "homography_matrix": [
      [
        1.5938402089749173,
        -0.009135473823188436,
        -29.15838087285149
      ],
      [
        0.14132108279630962,
        1.5296364901156894,
        -70.69339965129218
      ],
      [
        0.00016174706921424432,
        3.0676910436325914e-05,
        1.0
      ]
    ]
  },
  "demod": {
    "demodulated_bits": 480,
    "tile_count": 2,
    "fine_offset": [
      0,
      0
    ],
    "mean_absolute_score": 1.5299383401870728,
    "min_margin": 0.017099915072321892
  },
  "ecc": {
    "ecc_success": true,
    "crc_verified": true,
    "binding_verified": true,
    "errata_count": 7,
    "uncorrectable": false,
    "codeword_length": 125
  },
  "reprojection_error": 0.4486018717288971
}
```
