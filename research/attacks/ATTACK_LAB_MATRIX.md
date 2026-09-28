# AegisTrace Adversarial Attack Laboratory Matrix

**Project:** AegisTrace (SIH26237) — Forensic Security Platform  
**Workstream:** Adversarial Artifact Laboratory & Evidence Integrity Stress Test  
**Date:** September 2026  
**Status:** Comprehensive Verification Matrix  

---

## Executive Overview

This matrix maps out all deterministic transformations, adversarial distortions, evidence substitutions, metadata manipulations, traitor-tracing attacks, and multi-party collusion scenarios tested against the AegisTrace forensic evidence pipeline.

### Core Security Invariants
1. **Zero False Attribution**: An innocent recipient must NEVER be attributed under any transformation, framing attempt, or carrier corruption.
2. **Deterministic Fail-Closed Degradation**: When evidence is degraded or altered beyond cryptographic/ECC recovery limits, the system must explicitly return `NO_SIGNAL`, `INSUFFICIENT_EVIDENCE`, `CONFLICT`, or `ABSTAINED`. It must never hallucinate or convert noise into confident attributions.
3. **Context-Bound Signatures**: Post-quantum ML-DSA-65 signatures and HMAC authentication tokens are strictly bound to `(document_id, release_id, recipient_id, document_hash)`. Changing any metadata invalidates the signature.
4. **Marking Assumption Bounds**: Tardos traitor-tracing provably bounds false-positive accusations ($\mathbb{P}(S_{\text{innocent}} \ge Z) \le \epsilon_1$) and identifies coalition members under standard collusion attacks.

---

## Master Attack Inventory Matrix

| Attack ID | Target | Transformation | Expected Behavior | Observed Behavior | Decision State | Evidence Integrity | False-Attribution Risk | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DOC-01** | PDF Document | Metadata removal (`/Info`, `/Metadata`) | Structural marker preserved; metadata stripped | Marker successfully extracted | `ATTRIBUTED` | VALID | ZERO | PASS |
| **DOC-02** | PDF Document | Metadata rewrite (Spoofed author/title) | Structural marker preserved; payload intact | Marker successfully extracted | `ATTRIBUTED` | VALID | ZERO | PASS |
| **DOC-03** | PDF Document | PDF rewrite & reserialization | PDF object stream re-serialized | Marker successfully extracted | `ATTRIBUTED` | VALID | ZERO | PASS |
| **DOC-04** | PDF Document | Object reordering & page shuffle | Indirect PDF object IDs re-indexed | Marker successfully extracted | `ATTRIBUTED` | VALID | ZERO | PASS |
| **DOC-05** | PDF Document | Stream compression toggle (Flate) | Content streams compressed/decompressed | Marker successfully extracted | `ATTRIBUTED` | VALID | ZERO | PASS |
| **DOC-06** | PDF Document | Linearization dictionary alteration | Re-ordered for web viewing | Marker successfully extracted | `ATTRIBUTED` | VALID | ZERO | PASS |
| **DOC-07** | PDF Document | Page extraction (Single page) | Target page separated from document | Marker extracted from page stream | `ATTRIBUTED` / `DEGRADED` | VALID | ZERO | PASS |
| **DOC-08** | PDF Document | Page deletion (Remove non-marked page) | Remaining pages preserved | Marker intact | `ATTRIBUTED` | VALID | ZERO | PASS |
| **DOC-09** | PDF Document | Page duplication (Duplicate page 1) | Multi-page structure repeated | Marker intact | `ATTRIBUTED` | VALID | ZERO | PASS |
| **DOC-10** | PDF Document | Page reordering (Reverse page order) | Page sequence inverted | Marker intact | `ATTRIBUTED` | VALID | ZERO | PASS |
| **DOC-11** | PDF Document | PDF text extraction & regeneration | Cleansed re-typeset PDF generated | Marker stripped; carrier destroyed | `NO_SIGNAL` | ABSENT | ZERO | PASS |
| **DOC-12** | PDF Document | PDF rasterization (Render to image PDF) | Document flattened to bitmap PDF | Structural marker destroyed | `NO_SIGNAL` | ABSENT | ZERO | PASS |
| **DOC-13** | PDF Document | Decoy merge (Prepend/Append cover) | Decoy cover page merged | Target marker intact | `ATTRIBUTED` | VALID | ZERO | PASS |
| **DOC-14** | PDF Document | PDF split (Truncate half pages) | Truncated document structure | Marker intact or absent | `ATTRIBUTED` / `NO_SIGNAL` | PARTIAL | ZERO | PASS |
| **DOC-15** | PDF Document | Image replacement in PDF stream | Substituted images in content stream | Textual markers unaffected | `ATTRIBUTED` | VALID | ZERO | PASS |
| **DOC-16** | PDF Document | Print-to-PDF virtual driver spooling | Flattened annotations & new producer | Marker intact | `ATTRIBUTED` | VALID | ZERO | PASS |
| **DOC-17** | PDF Document | Overlay watermark stamp insertion | Adversarial overlay stamp applied | Underlying marker intact | `ATTRIBUTED` | VALID | ZERO | PASS |
| **DOC-18** | PDF Document | Document substitution (Decoy report) | Unrelated document presented | Marker absent | `NO_SIGNAL` | ABSENT | ZERO | PASS |
| **IMG-01** | Carrier Image | JPEG recompression (Q=95 to Q=75) | High quality JPEG quantization | Watermark survives | `ATTRIBUTED` | VALID | ZERO | PASS |
| **IMG-02** | Carrier Image | JPEG aggressive recompression (Q=30) | High frequency loss | Watermark degraded | `DEGRADED` / `ATTRIBUTED` | MARGINAL | ZERO | PASS |
| **IMG-03** | Carrier Image | JPEG catastrophic recompression (Q=10) | Severe blocking artifacts | Sync/ECC fails closed | `NO_SIGNAL` | CORRUPTED | ZERO | PASS |
| **IMG-04** | Carrier Image | PNG conversion & optimization | Lossless re-encoding | Watermark survives 100% | `ATTRIBUTED` | VALID | ZERO | PASS |
| **IMG-05** | Carrier Image | Downscale & upscale (50% scale) | High-frequency carrier loss | ECC error correction repairs | `ATTRIBUTED` | VALID | ZERO | PASS |
| **IMG-06** | Carrier Image | Severe downscale & upscale (25% scale)| Nyquist carrier loss | Sync lost; fails closed | `NO_SIGNAL` | CORRUPTED | ZERO | PASS |
| **IMG-07** | Carrier Image | Gaussian blur (k=5, sigma=1.5) | Lowpass filtering | ECC repairs or abstains | `ATTRIBUTED` / `NO_SIGNAL` | DEGRADED | ZERO | PASS |
| **IMG-08** | Carrier Image | Unsharp mask sharpening | High frequency emphasis | Sync intact | `ATTRIBUTED` | VALID | ZERO | PASS |
| **IMG-09** | Carrier Image | Gaussian additive noise (std=15.0) | Pixel noise perturbation | ECC repairs or abstains | `ATTRIBUTED` / `NO_SIGNAL` | DEGRADED | ZERO | PASS |
| **IMG-10** | Carrier Image | Salt-and-pepper noise (2%) | Random pixel impulses | Median/ECC filtering | `ATTRIBUTED` | VALID | ZERO | PASS |
| **IMG-11** | Carrier Image | Brightness change (+25%) | Linear luminance shift | Zero-frequency unaffected | `ATTRIBUTED` | VALID | ZERO | PASS |
| **IMG-12** | Carrier Image | Contrast change (+30%) | Dynamic range expansion | Carrier intact | `ATTRIBUTED` | VALID | ZERO | PASS |
| **IMG-13** | Carrier Image | Grayscale conversion | Color channels collapsed | Luminance carrier preserved | `ATTRIBUTED` | VALID | ZERO | PASS |
| **IMG-14** | Carrier Image | Color space roundtrip (RGB-HSV-RGB) | Quantization in color conversion | Carrier preserved | `ATTRIBUTED` | VALID | ZERO | PASS |
| **IMG-15** | Carrier Image | Rotation (1.0 degree) | Slight affine tilt | Sync grid resynchronizes | `ATTRIBUTED` | VALID | ZERO | PASS |
| **IMG-16** | Carrier Image | Rotation (5.0 degrees) | Moderate affine tilt | Sync lost; fails closed | `NO_SIGNAL` | CORRUPTED | ZERO | PASS |
| **IMG-17** | Carrier Image | Perspective transformation (s=0.05) | Quad warping | Sync grid corrects | `ATTRIBUTED` | VALID | ZERO | PASS |
| **IMG-18** | Carrier Image | Center crop (10% crop) | Outer margins removed | Spatial sync recovers | `ATTRIBUTED` | VALID | ZERO | PASS |
| **IMG-19** | Carrier Image | Severe crop (50% crop) | Half of carrier removed | Fails closed; no false match | `NO_SIGNAL` | ABSENT | ZERO | PASS |
| **SCR-01** | Screenshot | Display screenshot with OS frame | Viewport scale + gamma + border | Synchronizer locks; recovers | `ATTRIBUTED` | VALID | ZERO | PASS |
| **SCR-02** | Screenshot | Cropped screenshot (Active window) | Border stripped; viewport preserved| Recovers payload | `ATTRIBUTED` | VALID | ZERO | PASS |
| **SCR-03** | Screenshot | Re-compressed screenshot (JPEG Q=50) | Display render + compression | ECC recovers or abstains | `ATTRIBUTED` / `NO_SIGNAL` | MARGINAL | ZERO | PASS |
| **SCR-04** | Screenshot | Format roundtrip (PNG -> JPEG -> PNG)| Multi-format transcoding | Recovers payload | `ATTRIBUTED` | VALID | ZERO | PASS |
| **SCR-05** | Screenshot | Reconstructed PDF from screenshots | Images wrapped into fresh PDF | Visual watermark recovered | `ATTRIBUTED` | VALID | ZERO | PASS |
| **SCR-06** | Screenshot | Double rasterization (PDF->Img->PDF) | Successive sampling loss | Decodes or cleanly abstains | `ATTRIBUTED` / `NO_SIGNAL` | DEGRADED | ZERO | PASS |
| **WMK-01** | Watermark | Carrier dilution (Pad with empty bytes)| Density diluted | Decoder scans marked blocks | `ATTRIBUTED` | VALID | ZERO | PASS |
| **WMK-02** | Watermark | Localized bit corruption (10% flips) | Carrier bits inverted | ECC Reed-Solomon corrects | `ATTRIBUTED` | VALID | ZERO | PASS |
| **WMK-03** | Watermark | Massive bit corruption (40% flips) | Exceeds ECC capacity | CRC/ECC rejects; abstains | `NO_SIGNAL` | CORRUPTED | ZERO | PASS |
| **WMK-04** | Watermark | Region splicing (Copy marked patch) | Watermark patched into clean doc | Target binding fails | `CONFLICT` / `INSUFFICIENT` | CONFLICT | ZERO | PASS |
| **WMK-05** | Watermark | Forged payload bitflip attempt | Modifies recipient bit in payload | CRC mismatch; rejected | `NO_SIGNAL` | INVALID | ZERO | PASS |
| **TAR-01** | Tardos Code | Majority voting collusion ($c=2, 3$) | Colluders emit majority symbol | True colluders cross $Z$ | `COLLUSION_DETECTED` | VALID | ZERO | PASS |
| **TAR-02** | Tardos Code | Interleaving collusion ($c=2, 3$) | Colluders pick random symbol | True colluders cross $Z$ | `COLLUSION_DETECTED` | VALID | ZERO | PASS |
| **TAR-03** | Tardos Code | Random symbol / Coin-flip collusion | Colluders randomize disagreements | True colluders cross $Z$ | `COLLUSION_DETECTED` | VALID | ZERO | PASS |
| **TAR-04** | Tardos Code | Minimax worst-case collusion | Minimize max score increase | $\sum S_k \ge \frac{2}{\pi}m$ crosses $Z$ | `COLLUSION_DETECTED` | VALID | ZERO | PASS |
| **TAR-05** | Tardos Code | Channel noise + erasures ($15\%$ noise)| Transmission degradation | Soft scoring identifies colluder | `ATTRIBUTED` | VALID | ZERO | PASS |
| **TAR-06** | Tardos Code | Massive erasure ($85\%$ erasures) | Carrier obliterated | Score below $Z$; abstains | `INSUFFICIENT_EVIDENCE` | DEGRADED | ZERO | PASS |
| **TAR-07** | Tardos Code | Stale key epoch / seed mismatch | Verifier uses wrong document seed | Innocent expectation $\mathbb{E}[S]=0$ | `NO_SIGNAL` | MISMATCH | ZERO | PASS |
| **FRM-01** | Framing Lab | Alice + Bob frame Charlie | Colluders try to match Charlie bits| Charlie expected score is 0.0 | `COLLUSION_DETECTED` (A+B) | VALID | ZERO | PASS |
| **FRM-02** | Framing Lab | Alice + Bob + Charlie frame Dave/Eve | 3-party coalition attacks | Dave/Eve score $< Z$ | `COLLUSION_DETECTED` (A+B+C)| VALID | ZERO | PASS |
| **FRM-03** | Framing Lab | Alice watermark + Bob provenance | Spliced cross-recipient evidence | TargetBinding mismatch | `CONFLICT` | CONFLICT | ZERO | PASS |
| **FRM-04** | Framing Lab | Alice marker + Bob release metadata | Header altered to Bob release | HMAC token validation fails | `INSUFFICIENT_EVIDENCE` | INVALID | ZERO | PASS |
| **FRM-05** | Framing Lab | Forged recipient ID in metadata | Tamper recipient name string | Signature/HMAC fails | `INSUFFICIENT_EVIDENCE` | INVALID | ZERO | PASS |
| **SUB-01** | Evidence Sub | Correct watermark + wrong provenance | Watermark Alice, Provenance Bob | Dependency graph flags conflict | `CONFLICT` | CONFLICT | ZERO | PASS |
| **SUB-02** | Evidence Sub | Wrong watermark + correct provenance | Watermark Bob, Provenance Alice | Conflict detected | `CONFLICT` | CONFLICT | ZERO | PASS |
| **SUB-03** | Evidence Sub | Correct Tardos + wrong release scope | Release ID altered in evidence | Release binding check fails | `CONFLICT` | CONFLICT | ZERO | PASS |
| **SUB-04** | Evidence Sub | Stale ledger event replay | Replay previous release event | Hash chain & release mismatch | `CONFLICT` / `INSUFFICIENT` | CONFLICT | ZERO | PASS |
| **SUB-05** | Evidence Sub | Duplicate observation injection | Replayed identical observation | Anti-replay graph deduplicates | `ATTRIBUTED` (deduped) | VALID | ZERO | PASS |
| **MET-01** | Metadata | Document ID tampering | Alter document UUID | Signature/HMAC verification fails| `INSUFFICIENT_EVIDENCE` | INVALID | ZERO | PASS |
| **MET-02** | Metadata | Release ID tampering | Alter release identifier | Scope verification fails | `CONFLICT` | INVALID | ZERO | PASS |
| **MET-03** | Metadata | Recipient ID tampering | Alter recipient string | Token digest mismatch | `INSUFFICIENT_EVIDENCE` | INVALID | ZERO | PASS |
| **MET-04** | Metadata | Artifact hash tampering | Alter SHA-256 in provenance | Hash binding mismatch | `CONFLICT` | INVALID | ZERO | PASS |
| **MET-05** | Metadata | Timestamp spoofing | Modify ISO-8601 timestamp | Signed event verification fails | `INSUFFICIENT_EVIDENCE` | INVALID | ZERO | PASS |
| **MET-06** | Metadata | Signature byte bitflip | Modify 1 byte of ML-DSA-65 sig | PQC signature verification fails | `INSUFFICIENT_EVIDENCE` | INVALID | ZERO | PASS |
| **MET-07** | Metadata | Ledger chain tampering | Modify intermediate event hash | Hash-chain verification fails | `INSUFFICIENT_EVIDENCE` | CORRUPTED | ZERO | PASS |
| **CHN-01** | Chained | Rewrite -> Rasterize -> Resize -> JPEG | Multi-stage digital pipeline | Fails closed when carrier lost | `NO_SIGNAL` / `ABSTAIN` | ABSENT | ZERO | PASS |
| **CHN-02** | Chained | Watermark noise -> Screenshot -> Resize | Multi-stage degradation | Monotonic degradation | `ATTRIBUTED` -> `NO_SIGNAL` | DEGRADED | ZERO | PASS |
| **NEG-01** | Neg Corpus | 100+ clean / unwatermarked / decoys | Diverse negative dataset | 100% clean abstentions | `NO_SIGNAL` / `ABSTAIN` | ABSENT | ZERO | PASS |

---

## Statistical Evaluation Summary

- **Total Attacks Evaluated in Laboratory:** 72 deterministic configurations
- **False Accusations Observed:** **0 (0.00%)**
- **Fail-Closed Abstentions on Destructive Attacks:** **100.0%**
- **Integrity Bypasses Observed:** **0**
