# SIH26237 — Attack & Robustness Tooling Research

**Author**: Agent 3 (Principal Security Testing + Adversarial Robustness Engineer)  
**Date**: 2026-09-26  
**Status**: Comprehensive Baseline Review & Selection  
**Workstream**: Attack & Robustness Laboratory  

---

## Executive Summary

The SIH26237 system provides post-quantum cryptographic protection (ML-KEM-768, ML-DSA-65, AES-256-GCM), decentralized decryption provenance logging via a tamper-evident hash-chained ledger, and fail-closed leak attribution. The objective of the **Attack & Robustness Laboratory** is to subject released documents and digital assets to realistic, adversarial, and destructive transformations across multiple channels:
1. **Digital Image Transformations** (compression, geometric, filtering, noise, re-encoding)
2. **PDF / Document Structural Attacks** (object rewriting, metadata manipulation, page surgery, rasterization, split/merge)
3. **Print-to-Camera Capture & Cross-Medium Transformations** (optical blur, perspective skew, non-uniform lighting, paper grain, sensor noise, downsampling)
4. **Collusion Attacks** (averaging, interleaving, majority voting, random selection, erasure, symbol substitution)
5. **Cryptographic & Integrity Attacks** (tampered ciphertext, forged provenance events, ledger chain corruption, recipient substitution)

In accordance with the integration mandate, **we do not build image filtering kernels or PDF binary parsers from scratch**. Instead, we systematically evaluated open-source tooling, academic benchmarks, and forensic frameworks to establish clear **REUSE**, **ADAPT**, **IMPLEMENT**, and **REJECT** decisions.

---

## 1. Evaluation Matrix & Dependency Classification

| Tool / Framework / Library | Primary Purpose | License | Maintenance / Maturity | Classification | Key Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Pillow (PIL Fork)** | Digital image I/O, format conversion, recompression, resizing, cropping | HPND (MIT-like) | Active (v9.4.0 installed) | **REUSE** | Gold-standard Python imaging library. Handles JPEG/PNG/WEBP encoders, spatial subsampling, affine resampling, and format metadata cleanly without native C build friction. |
| **OpenCV (`opencv-python`)** | Fast perspective warping, spatial filtering, blur, morphological kernels, matrix math | Apache 2.0 | Active (v4.13.0 installed) | **REUSE** | High-performance C++ backend. Essential for accurate perspective transforms (homography), Gaussian/bilateral blurs, sharpen matrices, and lighting gradient generation. |
| **NumPy** | Array transformations, deterministic noise sampling, vector distance metrics | BSD-3-Clause | Active (v1.26.4 installed) | **REUSE** | Foundational numerical substrate. Enables vectorized bit survival rate, Hamming distance, normalized cross-correlation, and seeded pseudorandom noise injection. |
| **SciPy** | Mathematical operations, signal convolution, statistical correlation | BSD-3-Clause | Active (v1.10.0 installed) | **REUSE** | Provides robust statistical correlation (`pearsonr`, `spearmanr`) and signal processing routines for extraction scoring. |
| **pypdf** | PDF object tree manipulation, page operations, metadata rewriting, stream manipulation | BSD-3-Clause | Active (v6.19.0 installed) | **REUSE** | Modern pure-Python PDF toolkit. Already vetted in repository. Supports page deletion, extraction, duplication, reordering, merging, splitting, and metadata modification without external binaries. |
| **ReportLab** | Document synthesis, synthetic PDF test fixture generation | BSD | Active (v5.0.1 installed) | **REUSE** | Pure-Python PDF rendering engine. Already vetted in repository. Essential for creating deterministic multi-page, image-bearing, and carrier-annotated baseline documents. |
| **PyMuPDF (`fitz`)** | High-speed PDF rendering, rasterization, text extraction | AGPL-3.0 / Commercial | Active | **REJECT** | **License Conflict**: AGPL-3.0 is viral and conflicts with commercial/Apache 2.0 governance requirements. Requires external C binaries. We achieve rasterization and page extraction using `pypdf` + ReportLab + Pillow without AGPL exposure. |
| **pdf2image** | PDF to image rendering via Poppler | MIT | Active | **REJECT** | Requires external Poppler binaries (`pdftoppm`) on the Windows host PATH, introducing brittle external environment dependencies. Documented alternative handles rasterization without external CLI dependencies. |
| **Pikepdf / QPDF** | Low-level PDF object graph rewriting | MPL-2.0 | Active | **REJECT** | Requires QPDF native binaries. `pypdf` v6.19 already satisfies our object extraction, trailer surgery, and page transformation requirements with zero native build baggage. |
| **AugLy (Meta Research)** | Data augmentations for image/audio/video robustness | MIT | Active | **ADAPT** | High-quality parameterizations for adversarial transforms (e.g. screenshot simulation, perspective warp, compression artifacts). Adapt specific parameter logic into our modular pipeline without pulling in heavy PyTorch/Torchvision dependencies. |
| **Albumentations** | Fast image augmentations for ML robustness | MIT | Active | **ADAPT** | Industry standard for computer vision corruption sweeps. We adapt the mathematical formulations for salt-and-pepper noise, Gaussian noise, and lens distortion directly into OpenCV/NumPy kernels. |
| **ImageNet-C / imagecorruptions** | Academic benchmark for corruption robustness (Hendrycks & Dietterich 2019) | Apache 2.0 | Reference Standard | **ADAPT** | Defines 5 severity levels across 15 corruption types. We adapt the severity scale and parameter mappings for noise, blur, and digital compression sweeps. |
| **StirMark Benchmark** | Classic academic watermark robustness benchmark (Petitcolas et al. 1998) | Academic / Non-commercial restrictions | Historic / Inactive | **ADAPT** | Landmark conceptual taxonomy: geometric attacks (rotation, crop, shearing, aspect ratio), signal processing (filtering, noise, JPEG), and random non-linear distortion. We adapt the taxonomy and test vectors into our modern Python harness, avoiding legacy C code and restrictive licensing. |
| **Checkmark / WToolbox** | Watermarking attack suites for DCT/DWT | Academic | Inactive | **ADAPT** | Informs our metric definitions: distinguishing between perceptual quality (PSNR/SSIM) vs. watermark payload recovery vs. attribution thresholding. |
| **DocPhoto / StegaStamp / PIMoG** | Print-to-camera / screen-shooting physical degradation research | Academic | Active Research | **ADAPT** | Deep empirical insights into the physical capture channel: gamma distortion, perspective trapezoid skew, specular illumination, optical defocus, sensor grain, paper texture. We implement a multi-stage simulation reproducing these exact channel components. |
| **Tardos Collusion Benchmarks** | Academic collusion attack formulations (Tardos 2003, Skoric 2008) | N/A (Theoretical) | Reference | **IMPLEMENT** | Collusion attacks (averaging, interleaving, majority, minority, random selection, erasure) operate on abstract symbol vectors. We implement clean, deterministic, seed-controlled primitives independent of specific codebook representations. |
| **Custom Cryptographic Fixtures** | Adversarial tampering fixtures for SIH26237 ledger & packages | N/A (Internal) | N/A | **IMPLEMENT** | Specific to SIH26237 data contracts (`EvidenceEvent`, `ReleaseRecipientPackage`, `TamperEvidentLedger`). Implements targeted adversarial mutations (signature corruption, bit flips, metadata swaps, replay). |

---

## 2. Detailed Technical Analysis by Attack Domain

### 2.1 Digital Image Transformations

#### Reusable Tooling
- **Pillow (v9.4.0)**:
  - `Image.save(format="JPEG", quality=Q, subsampling=sub)`: Full control over quantization matrices and chroma subsampling (4:4:4, 4:2:2, 4:2:0).
  - `Image.resize(size, resample=Image.Resampling.LANCZOS / BILINEAR / NEAREST)`: Controlled scaling and downsampling/upsampling cycles.
  - `ImageOps` & `ImageEnhance`: Deterministic brightness, contrast, sharpness, grayscale conversions.
  - `Image.crop(box)`: Precise bounding-box cropping and partial boundary slicing.
- **OpenCV (v4.13.0)**:
  - `cv2.warpPerspective(src, M, dsize)`: Exact 4-point projective homography for perspective distortion.
  - `cv2.getRotationMatrix2D` & `cv2.warpAffine`: Arbitrary angle sub-pixel rotations with edge clamping or background filling.
  - `cv2.GaussianBlur`, `cv2.medianBlur`, `cv2.filter2D`: Frequency filtering, unsharp masking, and directional motion blur.
  - `cv2.cvtColor`: Robust color-space conversions (RGB to BGR, HSV, LAB, YCrCb, Grayscale).

#### Adaptation Strategy
Rather than maintaining arbitrary ad-hoc image scripts, we implement an **Attack Executor Pipeline**:
1. Input validation & hash computation (`SHA-256`)
2. Format normalization (PIL Image $\leftrightarrow$ NumPy `ndarray` $\leftrightarrow$ Raw bytes)
3. Deterministic parameter validation using Pydantic models
4. Transformation execution with tool telemetry capture
5. Output hash computation, difference metrics (PSNR, SSIM, MAE), and machine-readable result packaging.

---

### 2.2 PDF / Document Structural Attacks

#### Reusable Tooling
- **`pypdf` (v6.19.0)**:
  - `PdfReader` & `PdfWriter`: Complete access to trailer dictionaries, Catalog, Info dictionary, page tree nodes (`/Pages`), and content streams (`/Contents`).
  - Metadata Operations: Stripping `/Info` and `/Metadata` (XMP) streams, injecting spoofed dates, authors, and classification tags.
  - Page Surgery:
    - Page extraction (`writer.add_page(reader.pages[i])`)
    - Page deletion (omitting indices)
    - Page duplication (re-adding identical references)
    - Page reordering (permuting page list)
    - Document split & merge (`writer.append()`)
  - Compression / Stream Surgery:
    - `writer.compress_identical_objects()`
    - Recompressing or uncompressing streams (`FlateDecode` toggle)
- **`reportlab` (v5.0.1)**:
  - Generates high-fidelity, deterministic benchmark documents with structured text, vector rules, and embedded images.
  - Enables "text extraction + re-generation" attacks: parsing textual contents from an existing document and re-rendering into a visually similar fresh PDF, stripping all binary markers and structural trailers.

#### Rejection of PyMuPDF & pdf2image
- PyMuPDF uses AGPL-3.0 licensing, creating compliance risks for commercial or Apache 2.0 downstream applications.
- `pdf2image` requires external `pdftoppm` C++ binaries that are typically absent from standard Windows production environments.
- By relying on `pypdf` and Pillow/ReportLab, our entire attack laboratory remains **pure Python, zero-host-binary-dependent, and 100% reproducible**.

---

### 2.3 Print / Camera Simulation Research & Cross-Medium Degradation

#### Literature Grounding
Cross-medium attacks (printing a document and photographing it with a mobile smartphone) represent the most common real-world vector for leaking classified documents. Academic literature (e.g., *StegaStamp* [Tancik et al., CVPR 2020], *PIMoG* [Fang et al., ACM MM 2022], *DocPhoto* [Pramila et al.]) identifies the physical channel transfer function as a composition of discrete phenomena:

$$\mathcal{I}_{\text{captured}} = \mathcal{C}_{\text{JPEG}} \circ \mathcal{N}_{\text{sensor}} \circ \mathcal{L}_{\text{illum}} \circ \mathcal{B}_{\text{optics}} \circ \mathcal{W}_{\text{perspective}} \circ \mathcal{T}_{\text{color}} (\mathcal{I}_{\text{printed}})$$

1. **Color Tone Curve & Desaturation ($\mathcal{T}_{\text{color}}$)**: Printer CMYK gamut compression, non-linear tonal transfer curves, and desaturation.
2. **Perspective Warp ($\mathcal{W}_{\text{perspective}}$)**: Off-axis smartphone camera capture produces trapezoidal projective distortion.
3. **Optical Defocus & Blur ($\mathcal{B}_{\text{optics}}$)**: Lens point spread function (PSF), slight hand jitter, and depth-of-field falloff.
4. **Uneven Illumination & Ambient Gradients ($\mathcal{L}_{\text{illum}}$)**: Directional desk lamp, room lighting gradients, or specular reflections creating low-frequency intensity modulations across the page.
5. **Sensor & Paper Noise ($\mathcal{N}_{\text{sensor}}$)**: CMOS sensor read noise (Poisson-Gaussian noise at high ISO) plus fibrous paper texture.
6. **Lossy Compression Artifacts ($\mathcal{C}_{\text{JPEG}}$)**: High-ratio smartphone camera JPEG encoding (typically quality 70–85) causing high-frequency DCT blocking.

#### Dual-Tier Implementation Approach
1. **Tier 1 — PHYSICAL (Real Capture Pipeline)**:
   - Metadata schema and ingestion interface for authentic physical captures: recording printer make/model, paper stock (e.g. standard A4 80gsm), camera device (e.g. iPhone 15 Pro, Pixel 8), distance, angle, and ambient lighting conditions.
2. **Tier 2 — SIMULATED (Controlled Synthetic Pipeline)**:
   - High-fidelity, deterministic composite simulation reproducing the six physical phenomena using parameterized OpenCV and NumPy algorithms.
   - All results explicitly tagged with `physical_or_simulated: "SIMULATED"` to prevent misleading claims.

---

### 2.4 Collusion Attack Primitives

#### Theoretical Foundations (Boneh-Shaw & Tardos Models)
In traitor tracing, a coalition $C = \{u_1, u_2, \dots, u_c\}$ of $c$ colluders combines their respective personalized copies $\mathbf{x}^{(1)}, \dots, \mathbf{x}^{(c)}$ to construct a forged artifact $\mathbf{y}$.

Under the **Marking Assumption**:
- If all colluders share the same symbol at position $j$ ($x_j^{(1)} = x_j^{(2)} = \dots = x_j^{(c)} = b$), they cannot change it without destroying the carrier: $y_j = b$.
- If colluders observe differing symbols ($x_j^{(u)} \neq x_j^{(v)}$), they can select any observed symbol, synthesize an intermediate symbol, or attempt to erase the mark.

#### Implemented Generic Primitives
Our collusion primitives operate on abstract symbol sequences (`Sequence[int]`, `Sequence[float]`, or `bytes`), ensuring **complete decoupling from Tardos or other watermark internals**:

1. **Averaging Collusion**:
   $$y_j = \text{round}\left(\frac{1}{c} \sum_{i=1}^c x_j^{(i)}\right)$$
2. **Interleaving / Cut-and-Paste Collusion**:
   Adversaries divide the carrier into blocks or segments, alternating pieces from different colluders.
3. **Majority Voting Collusion**:
   $$y_j = \text{mode}\left(\{x_j^{(1)}, \dots, x_j^{(c)}\}\right)$$
4. **Random Symbol Selection Collusion**:
   $$y_j = x_j^{(k)}, \quad k \sim \text{Uniform}(\{1, \dots, c\})$$
5. **Erasure / Puncture Collusion**:
   For positions where colluders disagree, the symbol is blanked or replaced with an erasure token ($-1$ or null).
6. **Minority / Adversarial Selection**:
   Colluders intentionally choose the least frequent symbol to stress-test extraction thresholds.
7. **Symbol Flipping / Substitution**:
   Forced bit inversion or symbol replacement at parameterized rates.
8. **Codeword Mixing / Partial Collusion**:
   A subset of the coalition colludes on a fraction of the carrier while retaining original marks elsewhere.

---

### 2.5 Cryptographic & Integrity Attack Fixtures

The SIH26237 cryptographic core enforces strict fail-closed security properties:
- `ReleaseRecipientPackage` authenticated encapsulation
- `EvidenceEvent` digital signatures (ML-DSA-65)
- `TamperEvidentLedger` hash chaining ($H_i = \text{SHA-256}(H_{i-1} \parallel \text{Payload}_i)$)
- `AttributionEngine` fail-closed evaluation (`ATTRIBUTED` vs `ABSTAIN`)

Our attack laboratory provides dedicated test fixtures that systematically challenge these boundaries:
1. **Ciphertext Bit-Flipping**: Tampering with AES-256-GCM ciphertext or authentication tag to verify authenticated decryption failure.
2. **Metadata Tampering**: Altering recipient IDs, document IDs, or release IDs in transit.
3. **Signature Corruption**: Corrupting DSA signature bytes or substituting keys to verify signature verification rejection.
4. **Ledger Tampering**:
   - In-place event modification
   - Event deletion (causing broken hash links)
   - Event reordering (causing sequence and hash mismatch)
   - Event duplication (anti-replay violation)
5. **Document & Identity Substitution**: Pairing legitimate markers or signatures from document $A$ with document $B$, verifying strict scope-mismatch abstention.

---

## 3. Robustness Measurement Methodology

### 3.1 Separation of Concerns
A critical failure mode in academic watermarking literature is conflating **visual quality** with **traceability robustness**. Our laboratory enforces three distinct metric tiers:

```
+-------------------------------------------------------------------+
|                        ATTACK EVALUATION                          |
+---------------------------------+---------------------------------+
                                  |
         +------------------------+------------------------+
         |                        |                        |
         v                        v                        v
[ Tier 1: Image Quality ] [ Tier 2: Signal Survival ] [ Tier 3: Attribution ]
- PSNR (Peak SNR)         - Bit Error Rate (BER)       - Decision (ATTRIBUTED /
- SSIM (Structural Sim)   - Symbol Recovery Rate         ABSTAIN)
- Mean Absolute Error     - Normalized Cross-Corr      - Confidence Level
- File Size Ratio         - Hamming Distance           - False Accusation Margin
```

1. **Perceptual Image Quality (Tier 1)**: Measures document distortion visible to the human eye. Low PSNR indicates heavy visual degradation.
2. **Traceability Signal Survival (Tier 2)**: Measures raw symbol/bit fidelity after the attack channel, independent of the attribution rule.
3. **Attribution Outcome (Tier 3)**: Evaluates whether the downstream attribution system correctly attributes the culprit, detects a conflict, or properly **abstains** (`NO_SIGNAL` or `INSUFFICIENT_EVIDENCE`).

### 3.2 Decision Thresholds & The Four Outcomes
Every attack execution within our evaluation matrix maps to one of four rigorous states:
- **`PASS`**: The traceability signal survived intact (recovery rate $\ge \tau_{\text{pass}}$) and was correctly attributed with high confidence.
- **`DEGRADE`**: The signal suffered degradation ($\tau_{\text{abstain}} \le \text{survival} < \tau_{\text{pass}}$) but retained sufficient marginal evidence for attribution or partial coalition identification.
- **`FAIL`**: The attack altered the signal such that an innocent party was accused, or an inconsistent state was produced without abstaining (critical security failure).
- **`ABSTAIN`**: The attack destroyed the signal ($\text{survival} < \tau_{\text{abstain}}$) and the system correctly refused to attribute (`NO_SIGNAL` or `INSUFFICIENT_EVIDENCE`), preserving zero-false-positive guarantees.

---

## 4. Architectural Integration & File Placement

```
attacks/
├── __init__.py
├── base.py                   # Generic Attack, AttackInput, AttackOutput, AttackResult abstractions
├── digital/
│   ├── __init__.py
│   ├── image_attacks.py      # JPEG, PNG, noise, blur, rotate, crop, perspective, screenshot
│   └── document_attacks.py   # PDF metadata, rewrite, page delete/reorder/extract, split/merge
├── physical/
│   ├── __init__.py
│   ├── simulation.py         # Multi-stage Print-Camera simulation pipeline
│   └── capture.py            # Physical capture ingestion & metadata tracker
├── collusion/
│   ├── __init__.py
│   └── primitives.py         # Averaging, interleaving, majority, erasure, random, mixing
├── integrity/
│   ├── __init__.py
│   └── adversarial_fixtures.py # Ledger tampering, signature corruption, package bit-flips
├── measurement/
│   ├── __init__.py
│   ├── metrics.py            # PSNR, SSIM, BER, Hamming distance, normalized correlation
│   └── evaluator.py          # Matrix evaluation, parameter sweeping, timing benchmarks
└── corpus/
    ├── __init__.py
    └── baseline_generator.py # Deterministic test corpus (text, multi-page, image, carrier)
```

---

## 5. Licensing and Third-Party Attribution

All libraries and toolkits utilized by the attack laboratory conform to permissive open-source licenses:
- **Pillow**: Historical Permission Notice and Disclaimer (HPND / MIT-equivalent) — fully compliant.
- **OpenCV (`opencv-python`)**: Apache License 2.0 — fully compliant.
- **NumPy**: BSD 3-Clause License — fully compliant.
- **SciPy**: BSD 3-Clause License — fully compliant.
- **pypdf**: BSD 3-Clause License — fully compliant.
- **ReportLab**: BSD License — fully compliant.
- **Pydantic / Pytest**: MIT License — fully compliant.

No AGPL, GPL, or restrictive proprietary dependencies are introduced.
