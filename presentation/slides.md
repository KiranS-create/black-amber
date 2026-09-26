# SIH26237 — Presentation Slide Deck

**Title:** Post-Quantum Leak Attribution for Documents: From Encrypted Release to Physical-Capture Traceability  
**Target Duration:** 8–10 Minutes Presentation + 5 Minutes Live Q&A  
**Slides:** 11 Structured Technical Slides  

---

<!-- SLIDE 1 -->
## Slide 1: Title & Core Value Proposition

### **Post-Quantum Leak Attribution for Documents**
#### *From Encrypted Release to Physical-Capture Traceability*

**SIH26237 — Team Technical Presentation**

---

### **The Core Engineering Challenge**
Traditional document protection frameworks safeguard files *in transit* and *at rest*, but **fail completely the moment an authorized recipient renders the document to a screen or prints it on paper**.

### **The SIH26237 Solution**
An integrated, air-gapped forensic framework that:
1. Enforces **NIST post-quantum cryptographic isolation** (`ML-KEM-768`, `ML-DSA-65`) during document distribution.
2. Embeds **collusion-resistant traitor-tracing codes** (`Symmetric Tardos`) within optical carriers surviving print-and-smartphone capture.
3. Evaluates forensic signals via **dependency-aware evidence fusion** that mathematically refuses to accuse when evidence is weak or contradictory (**Fail-Closed Zero-Trust**).

> [!NOTE]
> **Core Architecture Principle**: The system does not rely on a single vulnerable watermark; it correlates independently auditable cryptographic, statistical, and physical layers.

---

<!-- SLIDE 2 -->
## Slide 2: The Physical Leakage Boundary Problem

### **Why Conventional Enterprise DRM Fails**

```
  +-----------------------+
  |   DIGITAL CONTROLS    |  AES-256 Encryption, TLS, Access Control Lists, Passwords
  +-----------+-----------+
              |
              v (Authorized User Opens & Renders Document)
  +-----------------------+
  |   RENDERED CONTENT    |  Computer Screen, Tablet Display, Printed Paper
  +-----------+-----------+
              |
              v [ THE PHYSICAL LEAKAGE BOUNDARY ] (Out-of-band capture)
  +-----------------------+
  |  SMARTPHONE PHOTOGRAPHY  Optical Distortions, Sensor Noise, Perspective Skew, Cropping
  +-----------+-----------+
              |
              v
  +-----------------------+
  | ANONYMOUS PUBLIC LEAK |  Digital Rights Management (DRM) & Metadata Stripped
  +-----------------------+
```

### **The Engineering Gap**
- **Symmetric Keys Are Shared**: Standard encrypted PDFs cannot identify *which* recipient leaked plaintext after decryption.
- **Metadata Is Trivial to Strip**: EXIF data, watermarks in PDF headers, and digital signatures are eliminated by simple screenshotting or printing.
- **Physical Optical Attacks Destroy Naive Watermarks**: Sensor blur, paper reflectance, perspective skew, and downsampling wipe out fragile spatial marks.

---

<!-- SLIDE 3 -->
## Slide 3: Threat Model & Defense-in-Depth Matrix

| Threat Actor | Attacker Capabilities | Implemented Defense Layer | System Outcome |
| :--- | :--- | :--- | :--- |
| **Malicious Recipient** | Possesses valid private key; leaks decrypted document | **Individualized Tardos Fingerprinting + DSSS Watermark** | Recipient accurately attributed via unique spatial codebook |
| **Colluding Coalition** | 2 to $c$ recipients combine copies to erase markings | **Symmetric Tardos Traitor-Tracing Codes** ($c=3$, $\epsilon_1=10^{-4}$) | Collusion-resistant score accumulation identifies ringleaders |
| **Physical Capture Attacker** | Prints document; captures via smartphone camera | **ArUco Perspective Homography + Reed-Solomon ECC** | Homography restores geometry; DSSS recovers bitstream |
| **Artifact Tampering Attacker** | Crops content, applies heavy blur, downsamples | **Attack-Aware Dynamic Reliability Scaling** | Attenuates weak signals; transitions to `ABSTAIN` |
| **Evidence Poisoning Attacker** | Injects duplicate records; forges server provenance | **Dependency Graph Lineage + ML-DSA Signatures** | Deduplicates repeats; verifies Merkle hash chain |

> [!IMPORTANT]
> **Zero-Trust Rule**: In the presence of hostile tampering or contradictory signals, the system never guesses; it triggers an explicit `CONFLICT` or `INSUFFICIENT_EVIDENCE` state.

---

<!-- SLIDE 4 -->
## Slide 4: End-to-End System Architecture

```
ORIGINAL DOCUMENT (Master PDF / Image)
       │
       ▼
 [ ReleaseManager ] ──► Generates Ephemeral Symmetric Key (K_doc)
       │
       ├─────────────────────────┬─────────────────────────┐
       ▼                         ▼                         ▼
[ ML-KEM-768 Encap ]      [ ML-KEM-768 Encap ]      [ ML-KEM-768 Encap ]
  (Alice Public Key)        (Bob Public Key)        (Charlie Public Key)
       │                         │                         │
       ▼                         ▼                         ▼
  Alice Release             Bob Release             Charlie Release
                                 │
                                 ▼ (Bob Decrypts Sovereign Key)
                    [ Signed Provenance Event ] ──► [ Tamper-Evident Ledger ]
                                 │
                                 ▼
                    [ Tardos + DSSS Watermark ] ──► Printed / Rendered Document
                                 │
                                 ▼ [ PHYSICAL LEAKAGE BOUNDARY ]
                    [ Attack / Camera Capture ]
                                 │
                                 ▼
                    [ ArUco Perspective Rectification ]
                                 │
                                 ▼
                   ┌─────────────┴─────────────┐
                   ▼                           ▼
          Watermark Observation       Tardos Observation
                   │                           │
                   └─────────────┬─────────────┘
                                 │
                                 ▼
              [ Multi-Channel Evidence Fusion Engine ]
              (Anti-Double-Counting Lineage Traversal)
                                 │
                                 ▼
          ┌──────────────────────┼──────────────────────┐
          ▼                      ▼                      ▼
    [ ATTRIBUTED ]         [ CONFLICT ]           [ ABSTAIN ]
```

---

<!-- SLIDE 5 -->
## Slide 5: Cryptographic Trust & Recipient Isolation

### **Post-Quantum Cryptographic Primitives (NIST Standards)**
- **NIST FIPS 203 (`ML-KEM-768`)**:
  - Lattice-based key encapsulation for asymmetric document key transport.
  - Measured encapsulation latency: **11.61 ms** | Decapsulation: **12.4 ms**.
- **NIST FIPS 204 (`ML-DSA-65`)**:
  - Sovereign digital signatures for decryption event provenance.
  - Measured signature latency: **124.33 ms** | Verification: **20.97 ms**.
- **Authenticated Symmetric Envelope**:
  - `AES-256-GCM` with unique 96-bit IV per release payload (**0.30 ms**).
  - Key derivation via `HKDF-SHA256` with strict target binding.

### **Sovereign Recipient Key Custody**
- Central server generates **only** the encrypted envelope.
- Recipient private keys are stored exclusively on client endpoints.
- Decryption produces a non-repudiable, digitally signed provenance ticket committed to the **SHA-256 hash-chained audit ledger**.

---

<!-- SLIDE 6 -->
## Slide 6: Tardos Traitor-Tracing & Physical Carrier

### **1. Tardos Codebook (WHO: Mathematical Attribution)**
- Implements **Symmetric Tardos Traitor-Tracing Codes** (*Tardos 2003, Skoric 2008*).
- Dynamic `TardosCapacityPlanner` calculates code length $m$ based on carrier capacity:
  $$m = 100 \times c^2 \times \ln(1/\epsilon_1)$$
- Symbol-symmetric scoring function $U_{ic}$ accumulates evidence across extracted bits.
- Candidate Separation Margin ($\Delta = S_{(1)} - S_{(2)} \ge 2.5$) prevents false accusations.

### **2. Physical Watermark Carrier (HOW: Surviving the Optical Channel)**

```
TARDOS CODE BITS ──► REED-SOLOMON ECC ──► INTERLEAVING ──► DSSS SPATIAL MODULATION ──► ARUCO SYNC
```

- **4-Corner ArUco Fiducials**: Provide perspective homography rectification (`cv2.warpPerspective`) under severe camera tilt ($\pm 30^\circ$).
- **Multi-Channel Modality**:
  - *Rendered Page Canvas*: Discrete Cosine Transform (DCT) mid-frequency embedding.
  - *Graphical ROI & Security Background Textures*: Robust spatial luminance modulation.
- **Physical Status**: Automated metrics reflect **Simulated Physical Capture** (`PrintCameraSimulationAttack`); physical laboratory protocol ready via `scripts/watermark/ingest_physical_capture.py`.

---

<!-- SLIDE 7 -->
## Slide 7: Adversarial Attack Laboratory & Robustness

### **Systematic Attack Benchmark Matrix**

| Attack Category | Specific Transformations | Measured Impact on Carrier | Engine Decision |
| :--- | :--- | :--- | :--- |
| **Digital Image** | JPEG Recompression ($Q=10 \dots 95$), Downsampling ($25\% \dots 75\%$) | PSNR: $33.6\text{ dB} \dots 62.3\text{ dB}$ | **ATTRIBUTED** (Robust signal recovery) |
| **Geometric Distortion** | Rotation ($0.5^\circ \dots 5.0^\circ$), Perspective Warping | SSIM: $0.79 \dots 0.85$ | **ATTRIBUTED** (ArUco homography corrects) |
| **Aggressive Cropping** | Center / Edge crop ($10\% \dots 30\%$) | Spatial loss of carrier blocks | **ATTRIBUTED** ($\le 20\%$) / **ABSTAIN** ($> 30\%$) |
| **Simulated Physical** | Print-camera optical blur, non-uniform lighting | Pre-ECC BER: $0\% \dots 15\%$ | **ATTRIBUTED** (Post-ECC BER: $0.0\%$) |
| **PDF Manipulation** | Stream recompression, font stripping, rasterization | Strips vector tags | **ATTRIBUTED** (Pixel carrier intact) |
| **Evidence Tampering** | Replayed signatures, forged document IDs | Cryptographic signature failure | **CONFLICT / ABSTAIN** (Fail-closed) |

> [!TIP]
> **Key Insight**: Severe attacks that obliterate signal do **not** cause false accusations; they cleanly force the engine to **abstain**.

---

<!-- SLIDE 8 -->
## Slide 8: Multi-Channel Evidence Fusion & Anti-Double-Counting

### **The Fundamental Forensic Problem: Correlated Evidence**
If an engine extracts a physical watermark and then calculates a Tardos score from that same watermark, naively adding both scores creates **artificial confidence** and risks catastrophic false accusations.

```
                           EVIDENCE LINEAGE GRAPH
                        [ Physical Watermark Observation ]
                                       │
                                       ▼ (Derived Signal)
                         [ Tardos Score Observation ]
                                       │
                                       ▼
                       [ Transitive Derivation Bounding ]
                      Score = max(Score_WM, Score_Tardos)
                                       │
                                       ▼
                     [ Dynamic Reliability Attenuation ]
                     (Scaled by BER, SSIM, and Crop Ratio)
                                       │
                                       ▼
                       [ Primary Marker Corroboration ]
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        ▼                              ▼                              ▼
  ATTRIBUTED                       CONFLICT                        ABSTAIN
(Passed Δ ≥ 2.5)           (Contradictory Sources)          (Weak / Destroyed)
```

### **Core Fusion Invariants**
1. **Transitive Lineage Derivation**: Derived child evidence can never exceed the Maximum Evidentiary Bound of its parent tree.
2. **Adversarial Deduplication**: Submitting 100 identical observations collapses into a single evidence unit.
3. **Primary Marker Gate**: High-level structural signals cannot convict without cryptographic corroboration.

---

<!-- SLIDE 9 -->
## Slide 9: Live Demonstration Workflow (Turnkey 3-Minute Flow)

```
STEP 1: Document Vault Ingestion  ──► Register "Defense_Intelligence_Brief.pdf" into Vault
                 │
STEP 2: Multi-Recipient Release   ──► Package unique releases for Alice, Bob, and Charlie
                 │
STEP 3: Decryption Provenance     ──► Bob performs ML-KEM decapsulation & signs audit ledger
                 │
STEP 4: Physical Leak Ingestion   ──► Simulated leak "bob_leak.pdf" submitted to analysis API
                 │
STEP 5: Multi-Channel Analysis    ──► Homography -> Watermark extraction -> Tardos correlation
                 │
STEP 6: Forensic Fused Output     ──► FUSED DECISION: ATTRIBUTED -> Bob (Score: 14.2, Δ: 8.4)
                 │
STEP 7: Hostile Attack Scenario   ──► Heavy crop + blur + foreign watermark injected
                 │
STEP 8: Fail-Closed Protection    ──► FUSED DECISION: INSUFFICIENT_EVIDENCE / CONFLICT
```

### **Three Demo Modes Built-in**
- **Mode 1 (Live Web UI)**: Interactive dashboard on `http://127.0.0.1:5173`.
- **Mode 2 (Deterministic Local)**: Instant script walkthrough via `python scripts/demo/run_live_demo.py`.
- **Mode 3 (CLI Fallback)**: Pure Python interactive terminal walkthrough (`scripts/deployment/run_demo_cli.py`).

---

<!-- SLIDE 10 -->
## Slide 10: Measured Benchmarks & Empirical Telemetry

| Category | Benchmark Metric | Measured Performance | Source & Test Conditions |
| :--- | :--- | :--- | :--- |
| **Post-Quantum Cryptography** | `ML-KEM-768` Encapsulation<br/>`ML-DSA-65` Signature<br/>`AES-256-GCM` Envelope | **11.61 ms**<br/>**124.33 ms**<br/>**0.30 ms** | `scripts/benchmark_crypto.py`<br/>Isolated CPython 3.9 CPU benchmarks |
| **Physical Watermark Recovery** | Sync Latency (ArUco)<br/>Demodulation Latency<br/>False Accusations on Negatives | **26.50 ms**<br/>**36.31 ms**<br/>**0.0% (0 / 50)** | `research/physical/SIMULATED_RESULTS.md`<br/>75 simulated optical capture runs |
| **Evidence Fusion Evaluation** | Held-Out Scenario Match Rate<br/>False Accusation on Clean/Conflict<br/>Safety Invariants Validated | **74.0%** (74 / 100)<br/>**0.0%**<br/>**9 / 9 Invariants** | `artifacts/evidence-fusion/calibration_vs_evaluation.json`<br/>100-scenario held-out evaluation split |
| **Deployment & Startup** | Demo Reset Latency<br/>Deterministic Fixture Gen<br/>Full Test Suite Execution | **349.11 ms**<br/>**140.49 ms**<br/>**39 / 39 PASSED (9.0s)** | `artifacts/deployment/startup_benchmark.json`<br/>Clean Windows AMD64 environment |

> [!NOTE]
> **Scientific Honesty on the 74% Result**: The 74% decision match rate reflects a high-stress adversarial synthetic test set with extreme multi-parameter attack corruptions where the engine safely abstained rather than making false claims.

---

<!-- SLIDE 11 -->
## Slide 11: Engineering Boundaries, Future Roadmap & Conclusion

### **Honest Engineering Boundaries & Current Limitations**
1. **Physical Hardware Validation**: Automated test suite runs on simulated optical channels; true physical print-and-scan requires physical lab hardware (`scripts/watermark/ingest_physical_capture.py`).
2. **Heuristic Reliability Scaling**: Channel weights $\rho_i$ and dependency discounting $\gamma = 0.65$ are heuristic policy bounds tuned for risk-aversion, not closed-form covariances.
3. **Local Prototype Key Custody**: Current prototype implements sovereign client decapsulation; enterprise HSM/PKCS#11 key custody is targeted for production release.

### **Future Work Roadmap**
- Automated ICC profile color compensation for consumer inkjet printers.
- Hardware-accelerated WebAssembly decapsulation module for zero-install client viewing.
- Decentralized multi-authority threshold Tardos codebook generation.

---

### **Conclusion**

> ### *"Designed to attribute when evidence is mathematically overwhelming — and fail-closed with complete integrity when it is not."*

**Thank you. We welcome your technical questions.**
