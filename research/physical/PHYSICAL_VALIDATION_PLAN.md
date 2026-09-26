# SIH26237 — Physical Validation Plan & Protocol

**Project:** SIH26237 — Cryptographic Attribution & Immutable Decryption Provenance  
**Author:** Agent 4 (Principal Digital Watermarking + Robustness Research Engineer)  
**Date:** September 2026  
**Status:** Approved Specification  

---

## 1. Scope & Objective

This document defines the rigorous experimental protocol for verifying the physical leakage channel of watermarked confidential documents in SIH26237:
$$\text{Digital PDF} \longrightarrow \text{Print Output} \longrightarrow \text{Physical Paper} \longrightarrow \text{Smartphone Camera} \longrightarrow \text{Captured Image} \longrightarrow \text{Decoder} \longrightarrow \text{Attribution}$$

A core scientific integrity requirement of SIH26237 is:
> **NEVER present simulated print-camera results as actual physical validation.**
> All test artifacts, telemetry, logs, and benchmark reports MUST strictly segregate and label tests as either **REAL PHYSICAL TEST** or **SIMULATED PHYSICAL TEST**.

---

## 2. Distinction: Real Physical Test vs. Simulated Physical Test

| Dimension | Real Physical Test (`PHYSICAL`) | Simulated Physical Test (`SIMULATED`) |
| :--- | :--- | :--- |
| **Execution Medium** | Physical laser / inkjet printer, physical standard paper (A4 / US Letter), genuine smartphone camera sensor. | Synthetic mathematical transformations applied in-memory via OpenCV/NumPy to digital raster images. |
| **Channel Transformations** | Authentic continuous-to-discrete halftoning, physical ink bleeding, paper grain scattering, genuine optical point-spread function (PSF), ambient 3D lighting, phone ISP tone mapping. | Programmatic color shifts, 2D projective homography matrix warping, additive Gaussian paper noise, synthetic lighting gradient ramps, downsampling, and PIL/libjpeg recompression. |
| **Hardware Dependency** | Physical printer, smartphone (iOS/Android), camera operator, physical environment. | Zero external hardware; fully automated and reproducible in headless CI/CD test runs. |
| **Telemetry Recorded** | Printer model, DPI, paper type, phone model, camera sensor, exposure time, capture distance (cm), capture angle (°), lux level. | Distortion parameter dictionary (perspective factor, blur sigma, noise sigma, lighting strength, JPEG quality, random seed). |
| **Ingestion Pipeline** | `attacks.physical.capture.PhysicalArtifactCaptureImporter` | `attacks.physical.simulation.PrintCameraSimulationAttack` |
| **Attribution Weight** | Primary empirical evidence for real-world court/forensic admissibility. | Statistical robustness sweeps and failure boundary characterization during development. |

---

## 3. Real Physical Test Protocol (Laboratory Capture)

### 3.1 Hardware & Environment Prerequisites
1. **Printing Equipment:**
   - Standard Office Monochrome Laser Printer (e.g., HP LaserJet, Brother HL-series, $\ge 600$ DPI).
   - Standard Color Inkjet Printer (e.g., Canon PIXMA, Epson EcoTank, standard 300/600 DPI).
2. **Paper Substrates:**
   - Standard 80 gsm white multi-purpose copy paper.
   - Standard 75 gsm recycled office paper.
3. **Capture Devices:**
   - Primary: High-end smartphone (e.g., iPhone 13/14/15/16 Pro, Google Pixel 7/8/9, Samsung Galaxy S23/S24) using native Camera app (JPEG format, 12MP default output).
   - Secondary: Mid-range / budget smartphone (e.g., Redmi Note, Samsung Galaxy A-series) to test lower-grade optics and sensor noise.
4. **Illumination Conditions:**
   - Condition L1: Uniform diffused office fluorescent / LED ceiling lighting ($\approx 400\text{--}600$ lux).
   - Condition L2: Directional desk lamp creating a 2D intensity gradient across the page ($\approx 200\text{--}800$ lux gradient).
   - Condition L3: Low ambient light with phone LED flash enabled (specular glare hot-spot).

### 3.2 Step-by-Step Laboratory Workflow
1. **Document Issuance:**
   - Issue a recipient-specific copy for Recipient $R_i$ with document ID $D$ and release ID $L$.
   - The watermark engine encodes the Tardos codeword $X_i \in \{0, 1\}^m$ into the rendered page canvas.
   - Export to standard print-ready PDF/PNG.
2. **Physical Printing:**
   - Print at $100\%$ scale (no "fit to printable area" distortion) on target paper.
   - Log printer make, model, toner type, and paper weight in metadata.
3. **Smartphone Photography:**
   - Position the printed page on a flat desk.
   - Hold the smartphone at designated distance $d \in [25\text{ cm}, 45\text{ cm}]$.
   - Capture photographs at three designated angles:
     - **Normal Angle:** $\approx 0^\circ$ (camera plane parallel to page).
     - **Moderate Pitch:** $\approx 15^\circ\text{--}20^\circ$ tilt.
     - **Severe Angle:** $\approx 30^\circ\text{--}35^\circ$ oblique perspective.
   - Repeat with partial framing (capturing the entire page vs. slight edge margin crop).
4. **Telemetry Logging & Ingestion:**
   - Transfer uncompressed or native camera JPEG images to `attacks/corpus/physical_captures/`.
   - Ingest using `PhysicalArtifactCaptureImporter` recording complete `PhysicalCaptureMetadata`.
5. **Decoded Signal Extraction & Tardos Scoring:**
   - Feed captured image into `WatermarkDecoder.decode()`.
   - Measure synchronization success, BER, and confidence.
   - Feed recovered symbols into Tardos scoring.

---

## 4. Simulated Physical Test Protocol (Automated Testbed)

### 4.1 Automated Degradation Pipeline
The automated testbed executes via `PrintCameraSimulationAttack`, systematically sweeping parameter bounds:

1. **Perspective Homography:**
   - Simulates off-axis camera pitch and yaw by perturbing the 4 canonical corner coordinates by up to $\pm 10\%$ of image dimensions.
2. **Optical Defocus & Blur:**
   - Gaussian point-spread function ($\sigma \in [0.5, 2.5]$).
3. **Uneven Illumination Gradient:**
   - 2D planar lighting ramp simulating an off-center light source ($I(x,y) = I_0 \cdot (1 + \alpha x + \beta y)$ with gradient strength up to $40\%$).
4. **Paper Surface & Halftone Noise:**
   - Zero-mean Gaussian noise ($\sigma \in [5, 25]$) added to simulate paper fibers and print halftone dithering.
5. **Sensor Downsampling:**
   - Downsampling the image to $50\%\text{--}75\%$ resolution followed by bilinear interpolation, simulating low-resolution smartphone capture or distant capture.
6. **Lossy JPEG Recompression:**
   - Quality factor $Q \in [40, 95]$ using standard JPEG DCT quantization tables.

---

## 5. Metrics & Pass/Fail Criteria

Every physical or simulated evaluation must compute and report:

| Metric | Definition | Threshold for Success |
| :--- | :--- | :--- |
| **Synchronization Rate** | Percentage of captures where fiducial frame is detected and rectified. | $\ge 98\%$ on valid captures |
| **Raw Bit Error Rate (BER)** | Hamming distance between raw demodulated bits and ground truth divided by payload length. | $\le 18\%$ (within RS ECC correction budget) |
| **Post-ECC BER** | Bit error rate after Reed-Solomon decoding. | **$0.0\%$ (Bit-exact payload recovery)** |
| **Abstention Correctness** | Percentage of unwatermarked or destroyed images returning `NO_SIGNAL` or `INVALID` rather than false positives. | **$100.0\%$ (Zero false attributions)** |
| **Tardos Accusation Margin** | Normalized score $S_{\text{guilty}} / Z$ vs $S_{\text{innocent}} / Z$. | $S_{\text{guilty}} \ge Z$ and $S_{\text{innocent}} < Z$ |
| **Execution Latency** | End-to-end CPU time for synchronization + demodulation + RS ECC. | $< 150\text{ ms}$ on standard laptop CPU |

---

## 6. Real vs. Simulated Reporting Template

When documenting test outputs in benchmark logs or final reports, always use the following structured table:

```markdown
### Physical Robustness Evaluation Report

| Test ID | Test Category | Target Device / Simulation Config | Angle / Skew | Sync Status | Raw BER | Post-ECC BER | Observation Status | Attribution Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| PHYS-01 | **REAL PHYSICAL** | iPhone 15 Pro, HP LaserJet (600 DPI) | ~15° tilt | OK | 3.2% | 0.0% | RECOVERED | Accused: Recipient_03 |
| PHYS-02 | **REAL PHYSICAL** | Galaxy S23, Canon Inkjet (300 DPI) | ~25° tilt | OK | 6.8% | 0.0% | RECOVERED | Accused: Recipient_03 |
| SIM-01  | **SIMULATED**    | Default Simulation (perspective=0.06, Q=75) | 1.5° rot | OK | 1.8% | 0.0% | RECOVERED | Accused: Recipient_03 |
| SIM-02  | **SIMULATED**    | Severe Simulation (perspective=0.10, Q=50)  | 4.0° rot | OK | 8.5% | 0.0% | RECOVERED | Accused: Recipient_03 |
| NEG-01  | **UNWATERMARKED**| Clean Unmarked Document                     | 0°       | NO_MARK | N/A | N/A | NO_SIGNAL | Abstain (Fail-Closed) |
```
