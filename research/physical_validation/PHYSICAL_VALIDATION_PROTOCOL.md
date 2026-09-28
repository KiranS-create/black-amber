# AegisTrace (SIH26237) — Standardized Physical Watermark Validation Protocol

**Document Version:** 2.0.0  
**Status:** Canonical Experimental Protocol  
**Authority:** Agent 4 (Principal Physical Watermarking & Forensics Architecture)  
**Date:** September 2026  

---

## 1. Scientific Integrity Policy & Modality Segregation

A fundamental forensic and scientific requirement of the AegisTrace platform is the **unconditional segregation** of simulation benchmarks from authentic hardware validation runs:

> **CRITICAL RULE:**
> 1. Simulated optical degradations (`PrintCameraSimulationAttack`) must NEVER be represented as physical laboratory captures.
> 2. Every benchmark dataset, log file, JSON record, and audit report MUST explicitly state:
>    - `"modality": "PHYSICAL_CAPTURE"` for real printer & camera tests.
>    - `"modality": "SIMULATION"` for mathematical in-memory transforms.
> 3. If no physical hardware capture was executed in the active runner, the platform MUST report:
>    $$\text{REAL PHYSICAL CAPTURE EXECUTED} = 0$$

---

## 2. Physical Channel Leakage Model

The physical print-and-camera leakage channel encompasses the following discrete stages:

$$\text{Digital PDF} \xrightarrow[\text{Modulation}]{\text{DSSS + RS-ECC}} \text{Print Canvas} \xrightarrow[\ge 600\text{ DPI}]{\text{Physical Halftoning}} \text{Paper Substrate} \xrightarrow[\text{Ambient Lux}]{\text{Smartphone Optics}} \text{RGB Sensor} \xrightarrow[\text{ISP Pipeline}]{\text{JPEG Compression}} \text{Captured Image} \xrightarrow[\text{ArUco Homography}]{\text{Rectification}} \text{Demodulator} \xrightarrow[\text{Tardos}]{\text{Attribution}}$$

### Key Physical Transfer Functions & Channel Distortions:
1. **Halftone Dithering & Ink Absorption:** Non-linear micro-scale dot gain, ink bleeding into paper fibers, substrate reflectance variation.
2. **Optical Point-Spread Function (PSF):** Camera lens defocus, chromatic aberration, sensor Bayer filtering, motion blur.
3. **Geometric Perspective Distortion:** Non-coplanar optical axis (pitch $\theta \in [0^\circ, 35^\circ]$, yaw $\phi \in [0^\circ, 35^\circ]$, roll $\psi \in [0^\circ, 360^\circ]$).
4. **Non-Uniform Illumination Field:** 2D spatial irradiance gradients $I(x,y) = I_0(1 + \alpha x + \beta y)$, specular hot-spots from phone LED flash, localized cast shadows.
5. **Lossy Compression & Tone Mapping:** Mobile ISP HDR local tone mapping, noise suppression filters, standard 4:2:0 JPEG DCT quantization ($Q \in [30, 95]$).

---

## 3. Laboratory Execution Matrix & Equipment Requirements

### 3.1 Hardware Specifications
- **Monochrome Laser Printer:** HP LaserJet Pro M404n / Brother HL-L2350DW ($\ge 600$ DPI, PCL6/PostScript).
- **Color Inkjet Printer:** Canon PIXMA TS8320 / Epson EcoTank ET-2800 (300/600 DPI).
- **Substrates:** Standard 80 gsm uncoated multi-purpose wood-free office paper (A4 / US Letter).
- **Capture Devices:**
  - *Tier 1 (Flagship):* Apple iPhone 15 Pro (48MP main sensor binned to 12MP JPEG, $f/1.78$).
  - *Tier 2 (Mainstream):* Samsung Galaxy S23 / Google Pixel 8 (12MP JPEG default).
  - *Tier 3 (Budget/Adversarial):* Redmi Note 12 / Samsung Galaxy A14 (standard 12MP lower-grade ISP).

### 3.2 Lighting Protocols
- **Condition L1 (Uniform Diffuse):** Overhead office LED/fluorescent ceiling illumination ($400\text{--}600\text{ lux}$, uniformity $> 85\%$).
- **Condition L2 (Directional Gradient):** Single off-axis desk lamp at $45^\circ$ distance $50\text{ cm}$, producing a $\approx 25\text{--}40\%$ intensity gradient across the page.
- **Condition L3 (Low Light + Direct Flash):** Dim ambient room ($< 50\text{ lux}$) with smartphone LED torch/flash enabled at normal distance ($\approx 35\text{ cm}$).

### 3.3 Geometric Capture Matrix
- **Distance:** $d \in \{25\text{ cm}, 35\text{ cm}, 45\text{ cm}\}$.
- **Pitch Angle:** $\theta \in \{0^\circ \text{ (normal)}, 15^\circ \text{ (moderate)}, 30^\circ \text{ (severe)}\}$.
- **Framing:** Full page frame (4 fiducials visible) vs. marginal crop (boundary markers partially clipped).

---

## 4. Evaluation Criteria & Thresholds

| Metric | Scientific Target | Fail-Closed Policy Threshold |
| :--- | :--- | :--- |
| **Geometric Registration (Reprojection Error)** | $< 0.75\text{ px}$ | Homography rejected if error $> 2.5\text{ px}$ or conditioning $\kappa(H) > 10^6$ |
| **Preamble Sync Correlation** | Peak Correlation $> 0.70$ | Demodulation aborted if preamble correlation $< 0.40$ |
| **Pre-ECC Bit Error Rate (Raw BER)** | $< 12.0\%$ | RS-ECC corrects up to $t = \lfloor \text{parity}/2 \rfloor$ byte errors ($15.6\%$ byte BER) |
| **Post-ECC Bit Error Rate** | **$0.0\%$ (Bit-Exact)** | If $> 0.0\%$, payload is NOT recovered; status set to `PARTIAL` or `INVALID` |
| **False Accusation Rate (Negative Corpus)** | **$0.0\%$ ($0 / 100$)** | **Zero tolerance:** Any false accusation on negative corpus is an immediate failure |
| **End-to-End Decode Latency** | $< 150\text{ ms}$ (CPU) | Standard single-core CPU processing budget |

---

## 5. Threshold Calibration & Evaluation Split Protocol

To prevent threshold overfitting:
1. **Calibration Set (50% Split):** Used to tune carrier modulation gain ($\alpha \in [8, 18]$), ArUco corner refinement parameters, and matched-filter correlation thresholds.
2. **Evaluation Set (50% Split):** Fresh, strictly held-out partition across multiple recipients and carrier strategies (`RENDERED_PAGE_CANVAS`, `GRAPHICAL_ROI`, `SECURITY_BACKGROUND_TEXTURE`).
3. **Negative Corpus ($N \ge 100$):** Blank pages, random noise, unwatermarked business letters, mutilated markers, transplanted payloads, and corrupted CRC tokens.
