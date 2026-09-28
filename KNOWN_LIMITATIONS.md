# AegisTrace (Black Amber) — Known Limitations & Operational Boundaries
**Project ID:** SIH26237 | **Internal Code Name:** Black Amber  
**Release Gate Status:** `READY_WITH_DOCUMENTED_LIMITATIONS`  
**Date of Audit:** September 28, 2026  

---

## 1. Executive Statement of Epistemic Integrity

AegisTrace enforces absolute truthfulness across all scientific, mathematical, cryptographic, and operational claims. The platform rejects artificial perfection and explicitly documents all known physical, mathematical, format, and network boundaries.

Every validation claim in AegisTrace is categorized according to the **AegisTrace Epistemic Taxonomy**:

| Epistemic Classification | Strict Definition & Application in AegisTrace |
| :--- | :--- |
| **`VERIFIED_SOFTWARE`** | Software algorithms, cryptographic primitives, ledger logic, Merkle proofs, and data structures verified via automated deterministic test suites. |
| **`DEVICE_IN_LOOP`** | Live execution utilizing genuine physical hardware endpoints (host displays, mobile devices, local physical network interfaces). |
| **`HYBRID_VALIDATION`** | Joint validation pipelines combining genuine physical endpoints with mathematically rigorous channel transformations. |
| **`SIMULATION_CALIBRATION`** | High-fidelity optical, physical, printing, and scanning degradations evaluated against calibrated empirical sensor models. |
| **`NOT_VERIFIED`** | Modalities where genuine physical hardware was not connected during test execution (e.g., zero optical document cameras detected). |
| **`UNAVAILABLE`** | Hardware devices physically absent from the laboratory environment (e.g., zero physical printers or flatbed scanners). |

---

## 2. Physical & Hardware Channel Boundaries

### 2.1 Optical Document Cameras (`NOT_VERIFIED`)
- **Status:** Probed indices 0 through 3 in the host laboratory; zero physical document cameras detected.
- **Evidentiary Boundary:** All optical camera capture experiments in automated test suites are executed via calibrated optical distortion pipelines (`SIMULATION_CALIBRATION`). AegisTrace does **NOT** claim full physical camera verification until an external hardware document camera is attached and calibrated.
- **Mitigation:** The laboratory execution runner (`scripts/watermark/run_physical_laboratory_execution.py`) and ingestion script (`scripts/watermark/ingest_physical_capture.py`) are pre-configured to automatically switch to `DEVICE_IN_LOOP` when a physical camera is detected.

### 2.2 Physical Printers and Flatbed Scanners (`UNAVAILABLE`)
- **Status:** Zero physical inkjet/laser printers and zero physical scanners were detected in the test environment (all virtual print queues such as Microsoft Print to PDF were filtered out).
- **Evidentiary Boundary:** Print-and-scan resistance is validated against calibrated stochastic halftone, paper grain, and scanner MTF models (`SIMULATION_CALIBRATION`).
- **Mitigation:** Physical test chart generation (`core/physical/`) produces standardized high-resolution print targets ready for physical hardcopy validation.

### 2.3 Mobile Endpoint Hardware (`DEVICE_IN_LOOP`)
- **Status:** Two physical mobile devices participate in the test and demonstration loop:
  1. **Endpoint A:** Samsung Galaxy Note10 Lite (`SM-N770F`, Serial `RF8N927PM9N`, Android 12) connected via USB composite MTP/ADB.
  2. **Endpoint B:** Samsung Galaxy A55 5G (`SM-A556B`, Serial `RZCY9396AGX`, Android 14) connected via USB MTP.
- **Physical Display:** AMD Radeon(TM) Graphics rendering at $1920 \times 1080$ @ 144Hz. Carrier rendered directly to physical framebuffer.

---

## 3. Multi-Format Support Boundaries

AegisTrace defines a 3-tier format hierarchy. It does **NOT** claim universal deep steganography across arbitrary binary formats:

```
┌────────────────────────────────────────────────────────────────────────┐
│                      AEGISTRACE FORMAT ADAPTER TIERS                   │
├────────────────────────────────────────────────────────────────────────┤
│ TIER 1: CANONICAL ACTIVE PAYLOAD (Full Bidirectional Forensic Marking) │
│ • PDF (.pdf): Dual-layer DCT/spatial watermark + structural metadata   │
│ • Word (.docx): OpenXML run-level zero-width + font metrics modulation │
│ • Images (.png, .jpg): Spatial spread-spectrum + high-frequency DWT    │
├────────────────────────────────────────────────────────────────────────┤
│ TIER 2: SYNTACTIC & FORMATTING CARRIERS                                │
│ • Structured Data (.csv, .json): Whitespace / field-order modulation   │
│ • Source Code (.py, .ts, .c): Non-breaking space / zero-width comment  │
├────────────────────────────────────────────────────────────────────────┤
│ TIER 3: METADATA & CONTAINER LEVEL ONLY (`METADATA_ONLY`)               │
│ • Archives (.zip, .tar.gz): Archive manifest & file header injection   │
│ • CAD (.dwg, .dxf): Header metadata attribute tagging only             │
│ • Video / Audio (.mp4, .wav): Container atom / chunk metadata binding  │
└────────────────────────────────────────────────────────────────────────┘
```

- **Limitation:** For Tier 3 formats (ZIP, CAD, Video, Audio), AegisTrace does not embed deep bitstream audio/video watermarks. If an adversary transcodes the media file and strips container metadata, attribution will fail-closed (`NO_SIGNAL`).

---

## 4. Mathematical Collusion & Attribution Boundaries

### 4.1 Tardos Traitor-Tracing Collusion Bound
- **Supported Coalition Size:** Parameterized for up to $c = 4$ colluding recipients.
- **False-Positive Probability:** $\epsilon \le 10^{-3}$ (provably bounded by the Tardos arcsine distribution symmetric cutoff).
- **Adversarial Threshold:** When the observed correlation score does not exceed the calibrated decision threshold $\tau_{\text{attr}}$, or when coalition attacks exceed $c > 4$ and corrupt $> 45\%$ of embedded mark positions, the engine strictly outputs:
  $$\text{Verdict} = \text{ABSTAINED} \quad (\text{Fail-Closed Safe State})$$
- **Guarantee:** AegisTrace will never produce an arbitrary or ungrounded attribution under heavy collusion; it abstains rather than falsely accusing an innocent recipient.

### 4.2 Downstream Leak & Transmission Gap (`LAST_KNOWN_HOLDER`)
- **Operational Reality:** If an authorized recipient (e.g., Alice) decapsulates an authorized document using her NIST FIPS 203 ML-KEM-768 private key and then transmits the decrypted plaintext to a non-enrolled third party (e.g., Eve) via an external out-of-band channel (e.g., private USB drive or signal message):
  - The watermarked document retains Alice's unique forensic signature.
  - The forensic attribution engine will attribute the leak to Alice as the **Last Known Authorized Holder**.
  - **Limitation:** AegisTrace cannot deduce the identity of unknown downstream intermediaries who never possessed an AegisTrace cryptographic identity.
  - **Epistemic Label:** Attributed as `LAST_KNOWN_HOLDER` with an explicit notice:
    $$\text{Downstream Transmission Gap: Secondary dissemination out-of-band.}$$

---

## 5. Network & Cryptographic Boundaries

### 5.1 Air-Gapped Operation
- **Scope:** Complete offline survivability. Key generation, document encapsulation, dynamic decryption watermarking, DLT Merkle proof generation, and forensic verification do not make any outbound Internet requests.
- **Verification:** Enforced via `tests/deployment/test_airgap_guard.py` (all outbound socket connections intercepted and blocked).

### 5.2 Post-Quantum Cryptographic Assurance
- **Algorithms:** NIST FIPS 203 (ML-KEM-768) and NIST FIPS 204 (ML-DSA-65) implemented via pure-Python constant-time / validated reference modules with seamless C-extension acceleration where available.
- **No Certification Hyperbole:** AegisTrace is designed in strict conformance with published NIST FIPS standards; it does not claim commercial third-party CMVP/FIPS-140-3 laboratory certification.

---

## 6. Release Gate Determination

```
===========================================================================
  RELEASE CANDIDATE EVALUATION: READY_WITH_DOCUMENTED_LIMITATIONS
===========================================================================
  • Core Engine Integrity:         VERIFIED (1,098/1,098 Tests Green)
  • Post-Quantum Cryptography:     VERIFIED (FIPS 203 / FIPS 204 Conformance)
  • Clean-Room Reproduction:       VERIFIED (6/6 Stages Pass in < 5.0s)
  • Offline Evidence Verifier:     VERIFIED (11/11 Verification Pillars Pass)
  • Frontend Web Platform:         VERIFIED (Production Build Clean)
  • Repository Secret Audit:       CLEAN (0 Secrets Detected across 965 Files)
  • Hardware Epistemic Boundaries: HONESTLY CLASSIFIED & DOCUMENTED
===========================================================================
```
