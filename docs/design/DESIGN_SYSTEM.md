# AegisTrace Design System Documentation

## Overview & Architecture
This document details the forensic design system for **AegisTrace** (Internal engineering code name: *Black Amber*, SIH26237). 
It translates the Google Stitch design guidelines and the **Car Analogy** into concrete UI tokens, component structures, typography scales, and interaction paradigms.

---

## 1. Design DNA & Token Specifications

### 1.1 Color Tokens
| Token | Value | Role |
| :--- | :--- | :--- |
| `--bg` | `#0B1015` | Level 0 Canvas — Deepest workstation base |
| `--bg-elevated` | `#0F161D` | Level 0.5 Canvas highlight |
| `--surface` | `#121B23` | Level 1 Workstation Panels — Standard operational surface |
| `--surface-subtle` | `#0E151C` | Level 1 Recessed — Sidebar and table header backgrounds |
| `--surface-elevated` | `#17222C` | Level 2 Raised Cards & Inspectors |
| `--surface-hover` | `#17232E` | Interactive hover state |
| `--glass-surface` | `rgba(23, 34, 44, 0.76)` | Level 3 Floating Overlays & Drawers (Backdrop filter 16px) |
| `--border` | `rgba(255, 255, 255, 0.08)` | Hairline structural divider (1px solid) |
| `--border-strong` | `rgba(255, 255, 255, 0.14)` | Selected boundaries and input focus rings |
| `--text` | `#F2EFE8` | Warm Ivory — Primary readable text |
| `--text-secondary` | `#A9B3BD` | Slate Gray — Subheadings, column labels, secondary notes |
| `--text-tertiary` | `#73808C` | Muted Graphite — Timestamps, hashes, inactive metadata |
| `--primary` | `#4C9A9A` | Petrol Teal — Primary actions and active indicators |
| `--success` | `#4FA77B` | Jade — Formally verified integrity |
| `--warning` | `#C59645` | Amber — Downstream gaps and calibration warnings |
| `--danger` | `#C86464` | Crimson — Tamper detection and cryptographic failures |

### 1.2 Spacing & Geometry
* **Base Unit:** 4px grid (`--space-1`: 4px, `--space-2`: 8px, `--space-3`: 12px, `--space-4`: 16px, `--space-6`: 24px, `--space-8`: 32px, `--space-12`: 48px).
* **Corner Radii:**
  - Micro controls & badges: `4px` (`--radius-xs`)
  - Buttons & form inputs: `6px` (`--radius-sm`)
  - Panels & tables: `8px` (`--radius-md`)
  - Drawers & modals: `12px` (`--radius-xl`)

### 1.3 Typography Scale
* **Display / Workstation Header:** `20px` / `1.3`, weight `600`, letter-spacing `-0.015em`
* **Section Header:** `14px` / `1.4`, weight `500`, uppercase letter-spacing `0.05em`
* **Body Text:** `13px` / `1.5`, weight `400`
* **Micro Metadata:** `11px` / `1.4`, weight `400`
* **Monospace Hash / ID:** `11.5px` / `1.5`, font family `JetBrains Mono`

---

## 2. Component System

### 2.1 Buttons & Controls
* **Primary Action:** Solid Petrol `#4C9A9A`, dark text `#0B1015`, subtle active state (`transform: translateY(1px)`).
* **Secondary Action:** Surface elevated `#17222C`, hairline border, ivory text `#F2EFE8`.
* **Danger Action:** Tinted crimson background, red border, crimson text.

### 2.2 Native File Input & Dropzone
* Direct native `<input type="file">` hooked to standard `[ Browse Files ]` button.
* Drag-and-drop region with subtle border highlight on drag-over.
* Visibly lists Tier-1 verified formats: `PDF · DOCX · PPTX · XLSX · PNG · JPEG`.
* Communicates full progression states: `Empty` → `Validating` → `Ingesting` → `Watermarking` → `Ready`.

### 2.3 Tables & Registries
* Table headers stick to the top with subtle background `--surface-subtle`.
* Divider lines are 1px hairline borders (`rgba(255, 255, 255, 0.06)`).
* Row hover provides subtle visual feedback without jarring background switches.

### 2.4 Progressive Technical Details Drawer
* Overlays the screen from the right with smooth cubic-bezier motion (`0.24s`).
* Encapsulates mathematical and low-level cryptographic parameters:
  - NIST FIPS 203 ML-KEM-768 ciphertext & shared secret confirmation
  - NIST FIPS 204 ML-DSA-65 digital signature verification
  - 2D DSSS + RS(255, 223) watermark decoding statistics (correlation peak, bit error rate)
  - Bayesian multi-channel fusion: Log-likelihood ratio (LLR), prior probability, decision boundary threshold
  - RFC 6962 Merkle tree inclusion proofs and audit ledger block hash chains

---

## 3. Epistemic Transparency Guidelines
AegisTrace never overstates scientific or forensic confidence:
1. **Device-in-Loop:** Confirmed only when hardware key attestation and OS TPM receipt match.
2. **Downstream Gap:** Marked clearly when the chain of custody leaves known enrolled recipients.
3. **Simulation Calibration:** Explicitly labeled on optical print/screen transforms to indicate algorithmic model calibration rather than physical scanner verification.
