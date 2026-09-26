# SIH26237 — Judge-Facing Frontend & Live Demo Architecture Design

**Project:** SIH26237 — Cryptographic Attribution & Immutable Decryption Provenance  
**Author:** Agent 7 (Principal Frontend Engineer + Demo UX Architect)  
**Date:** September 2026  
**Status:** Hardened & Tested (SIH Prototype Evaluation Standard)  
**Role Scope:** `apps/web/**`, `tests/web/**`, `docs/FRONTEND_DESIGN.md`, `research/frontend/**`, `artifacts/frontend/**`

---

## 1. Executive Summary & Design Mission

Hackathon judges evaluating advanced cryptographic and security architectures face significant cognitive overload. Complex mathematical primitives—such as Post-Quantum Key Encapsulation (`ML-KEM-768`, FIPS 203), Lattice Digital Signatures (`ML-DSA-65`, FIPS 204), Tardos Traitor-Tracing Codes ($m=128$, Blayer-Tassa bounded false alarm $\epsilon_1 \le 10^{-4}$), Physical Print-Camera Homography, and Bayesian Log-Likelihood Evidence Fusion ($\text{LLR}$)—risk being misunderstood if presented only through terminal logs or theoretical slide decks.

The mission of the **SIH26237 Frontend & Live Demo UX** is to provide an **interactive, intuitive, offline-first visualization platform** that:
1. **Demystifies Post-Quantum Cryptography:** Visually demonstrates how a single confidential document is encrypted once with AES-256-GCM and wrapped across recipient-isolated ML-KEM-768 capsules.
2. **Proves Non-Repudiation & Decryption Provenance:** Shows real-time generation of ML-DSA-65 signed provenance events upon recipient decryption.
3. **Validates Tamper-Evidence:** Provides a block-by-block hash-chained ledger viewer with an interactive **Tamper Simulator** that mathematically demonstrates instant verification failure when any record is modified.
4. **Visualizes Multi-Channel Bayesian Evidence Fusion:** Charts how spatial/frequency watermarks, continuous Tardos correlation scores ($Z_i$), PQC signatures, and ledger records fuse under attack degradation ($\rho_i$) with anti-double-counting guarantees.
5. **Demonstrates Fail-Closed Robustness:** Allows judges to execute adversarial attacks (forged markers, framed identities, unwatermarked leaks, cross-document transplantation) and inspect why the engine strictly returns `ABSTAIN` (`NO_SIGNAL`, `INSUFFICIENT_EVIDENCE`, `CONFLICT`, `REVIEW_REQUIRED`) rather than falsely accusing innocent parties.
6. **Guarantees 100% Offline-First Availability:** Automatically falls back to deterministic local mock simulations if backend connection is unavailable, with explicit visual tagging (`REAL_BACKEND_RESULT` vs `SIMULATED_DEMO_SCENARIO`).
7. **Strict Hash & Artifact Isolation:** Distinctly tracks `ORIGINAL_DOCUMENT_HASH` (Data Plane), `RELEASE_ARTIFACT_HASH` (Envelope), and `LEAK_ARTIFACT_HASH` (Exfiltrated sample) without conflation.

---

## 2. System Architecture & UI Information Hierarchy

```mermaid
flowchart TD
    subgraph Frontend Architecture [apps/web]
        UI[React 18 + TypeScript + Vite UI]
        
        subgraph Views & Tabs
            DASH[1. Executive Overview & Pipeline Flow]
            REC[2. Recipient Identities & PQC Keys]
            REL[3. Envelope Encryption & Release Manager]
            DEC[4. Recipient Decryption & Provenance Signing]
            LED[5. Tamper-Evident Hash-Chain Ledger & Tamper Sim]
            LEAK[6. Leak Analysis & Bayesian Evidence Fusion]
            ATTK[7. Adversarial Attack Lab & Robustness Matrix]
        end
        
        subgraph Core Services & State Engine
            STATE[Unified Demo State Context]
            APICLIENT[API Client / Dual-Mode Bridge]
            MOCK[Offline-First Deterministic Crypto Simulator]
        end
        
        subgraph Interactive Presenter Utilities
            GUIDE[Judge 6-Stage Guided Walkthrough]
            DOSSIER[Technical Evidence & Provenance Report Modal]
            TARDOS_VIS[Tardos Correlation Matrix & Gaussian Threshold]
        end
        
        UI --> Views & Tabs
        Views & Tabs --> STATE
        STATE --> APICLIENT
        APICLIENT -->|Online HTTP REST| BACKEND[FastAPI Backend :8000]
        APICLIENT -->|Offline Fallback| MOCK
    end
```

---

## 3. Detailed Component Architecture

### 3.1 Dual-Mode Connectivity Bridge (`services/api.ts` & `services/mockData.ts`)
The frontend is built with an intelligent bridge that detects backend health on `http://localhost:8000`:
- **Connected Mode:** When the FastAPI server is running, all actions (`POST /documents`, `POST /recipients`, `POST /releases`, `POST /releases/{id}/decrypt`, `POST /leaks`, `POST /analyze`, `GET /ledger/verify`) execute live against the backend Python services. Data is tagged with `REAL_BACKEND_RESULT`.
- **Offline / Sandbox Mode:** If the backend is offline (or when offline mode is manually toggled), the state engine seamlessly switches to pre-computed deterministic cryptographic simulations. All operations—including adversarial test scenarios, watermark noise degradation, Tardos score plots, and ledger hash validation—function with zero network dependency. Data is tagged with `SIMULATED_DEMO_SCENARIO`.

### 3.2 Key Views & Features

| View / Module | Key Judge Demonstrations | Technical Insights Displayed |
| :--- | :--- | :--- |
| **Executive Dashboard** | High-level system vitals, 4-step cryptographic pipeline diagram, one-click end-to-end demo execution, fast scenario switcher. | Active recipients count, total releases, ledger verification status, live data plane document counters, architecture flowchart. |
| **Recipient Identities** | Enrolled entities (Alice, Bob, Charlie), key isolation, new identity generation. | `ML-KEM-768` public keys (1184 bytes), `ML-DSA-65` verification keys (1952 bytes), key isolation boundary confirmation. |
| **Release Manager** | Upload or select confidential documents, choose recipient distribution list, generate hybrid envelope packages. | AES-256-GCM document encryption, per-recipient ML-KEM-768 encapsulation, separate `ORIGINAL_DOCUMENT_HASH` and `RELEASE_ARTIFACT_HASH`. |
| **Decryption & Provenance** | Select recipient to decrypt their package, view decrypted document, generate signed decryption event. | Key decapsulation, AES-GCM tag verification, marker embedding, ML-DSA-65 signature generation, provenance event logging. |
| **Tamper-Evident Ledger** | Block-by-block hash-chain viewer, tip hash calculation, cryptographic event details. **Interactive Tamper Simulator:** Modify any block to see instant hash-chain breakage. | SHA-256 `previous_event_hash` chaining, non-repudiation signature verification, tamper detection alert, explicit distinction between live ledger and client-side simulation. |
| **Leak Analysis & Fusion** | Inspect leaked artifacts, multi-channel evidence fusion breakdown, candidate accusation scores with confidence levels. | Bayesian Log-Likelihood Ratios ($\text{LLR}$), attack-aware reliability discounts ($\rho_i$), candidate separation margin ($\Delta$), continuous Tardos score ($Z_i$), fail-closed state (`ATTRIBUTED`, `NO_SIGNAL`, `INSUFFICIENT_EVIDENCE`, `CONFLICT`, `REVIEW_REQUIRED`, `ABSTAINED`). |
| **Adversarial Attack Lab** | Test suite of attacks: Print-Scan perspective distortion, JPEG re-compression, Cropping, Forged markers, Cross-document framing, Collusion attacks. | PSNR/SSIM degradation, Bit Error Rate (BER), erasure rate, fail-closed abstention proof. |
| **Tardos Visualizer** | Interactive Tardos codebook matrix and continuous accusation score comparison for coalitions ($c=2, 3$). | Codeword symbol distribution, bit correlation scores, Gaussian accusation threshold $\tau_Z = 6.50$, Blayer-Tassa bounded false alarm ($\epsilon_1 \le 10^{-4}$). |
| **Evidence Dossier** | Technical Evidence & Decryption Provenance Report generator with one-click export (JSON / printable audit dossier). | Complete cryptographic chain of custody, raw hashes (`ORIGINAL`, `RELEASE`, `LEAK`), event IDs, signatures, mathematical fusion breakdown. |

---

## 4. Judge Experience & Guided Presentation Flow

The frontend includes a built-in **"Start Judge Walkthrough"** guided presenter tool located in the header. It structures a 5-minute live demonstration into 6 crisp, interactive stages:

1. **Stage 1: Identity & Post-Quantum Isolation** — Shows Alice, Bob, and Charlie enrolled with quantum-resistant keypairs (FIPS 203 ML-KEM-768 and FIPS 204 ML-DSA-65).
2. **Stage 2: Confidential Envelope Encryption** — Packages a sensitive document with AES-256-GCM and wraps it per-recipient via ML-KEM-768 capsules.
3. **Stage 3: Decryption & Non-Repudiation Provenance** — Bob decrypts his package, generating an immutable ML-DSA-65 signed provenance event.
4. **Stage 4: Tamper-Evident Audit Ledger & Tamper Simulation** — Inspects the hash chain and demonstrates instant tamper detection when a record is altered.
5. **Stage 5: Multi-Channel Leak Attribution** — Ingests a leaked document, executes Bayesian evidence fusion, and attributes Bob with high statistical confidence ($\text{LLR} > 15$, $\Delta > 10$).
6. **Stage 6: Adversarial Robustness & Fail-Closed Guarantee** — Demonstrates that forged markers, corrupted tokens, and foreign documents result in immediate fail-closed abstention (`ABSTAIN`), strictly guarding against false accusations.

---

## 5. Visual Design System & Design Tokens (`styles/tokens.css`)

AegisTrace follows an editorial enterprise forensic security workstation aesthetic (inspired by Linear, Vercel, and Swiss precision typography), completely eschewing AI-slop (no purple-to-blue gradients, no giant glowing text, no generic cards-in-cards):

- **Color Tokens & Dual-Theme Architecture:**
  - **Light Mode (Daylight Forensic Terminal):** Pure white `#ffffff` elevated surfaces against `#f8fafc` workspace canvas and `#f1f5f9` structural chrome. Crisp `#0f172a` primary typography, `#475569` secondary body, and `#e2e8f0` structural borders.
  - **Dark Mode (Layered Navy-Slate Depth):** Grounded `#090e17` base canvas, `#0d1526` structural navigation, `#111c30` workspace surface, `#162540` elevated surface, and `#1d3254` interactive hover states. Pure `#f8fafc` heading contrast and `#94a3b8` body text.
  - **Aegis Forensic Accent:** Precision Aegis Blue (`#2563eb` light / `#3b82f6` dark), Emerald Verified (`#10b981`), Amber Advisory (`#f59e0b`), Crimson Breach/Tamper (`#ef4444`). Zero neon/cyan RGB flares.
- **Typography & Cryptographic Data Displays:**
  - Headings & Interface: `Geist`, `Manrope`, `-apple-system`, `Inter`.
  - Cryptographic Primitives: `JetBrains Mono`, `ui-monospace`, `monospace` for all 64-char SHA-256 hashes, ML-KEM-768 encapsulation keys, ML-DSA-65 signatures, Tardos binary vectors, and mathematical metrics.
- **Micro-Motion & Signature Experience:**
  - **Signature Intro (~950ms):** 2D forensic laser trace line sweep across the central axis, resolving the Aegis shield and `AegisTrace` FIPS 203/204 wordmark with real-time parameter badge (`ML-KEM-768 • ML-DSA-65 • m=128`), seamlessly dissolving into the operations console. Fully skippable on keypress/click and automatically bypassed when `prefers-reduced-motion: reduce` is detected.
  - **Spring Micro-Interactions:** Subtle, fast 150-200ms easing transitions powered by anime.js v4 and Framer Motion for drawer slide-overs, tamper verification state changes, and evidence inspection toggles.
- **Progressive Disclosure:**
  - High-level decision verdicts (Attributed recipient, confidence level, separation margin) are visible at a glance.
  - Granular proofs (individual channel LLR contributions, reliability coefficients $\rho$, raw token bytes, ArUco homography details) are housed in collapsible proof drawers and progressive disclosure panels.

---

## 6. Verification and Testing Strategy

- **Build Verification:** Strict TypeScript validation (`tsc --noEmit`) and Vite production bundle build (`vite build` compiling 1,960 modules with 0 errors).
- **Automated Frontend Test Suite:** 28 passing unit/integration tests in `tests/web/`:
  - `test_frontend.py` (12 tests): package integrity, component existence, mock data scenarios, hash isolation types, fail-closed state machines, and anti-overclaiming checks.
  - `test_frontend_e2e_flow.py` (14 tests): 14-stage end-to-end judge demonstration verification covering key enrollment, release encryption, client decapsulation, tamper-evident hash chaining, adversarial attacks, and Tardos traitor-tracing.
  - `test_state_machine.py` (2 tests): pipeline transitions, channel fusion, and conflict resolution fail-closed behavior.
- **Full-System Integration:** Complete 339-test test suite (`py -m pytest -q`) passing with 100% success.
- **Browser Playwright Validation:** Headless Chromium visual validation across light and dark modes with full-page screenshots recorded in `artifacts/frontend/screenshots/`:
  - `signature_intro.png` — 2D laser trace initialization sequence.
  - `overview_light.png` & `overview_dark.png` — Operations console in light & dark workstation themes.
  - `forensic_attribution_light.png` & `forensic_attribution_dark.png` — Bayesian fusion workstation.
  - `encrypted_releases_light.png` & `encrypted_releases_dark.png` — PQC release management and capsule status.
  - `audit_ledger_tamper.png` — Real-time block corruption alert and hash-chain breakage proof.
  - `attack_laboratory.png` — Print-camera, JPEG distortion, and token forgery stress-testing.
  - `tardos_matrix.png` — Arc-sine bias bit distribution and continuous accusation scores.
- **Repository Safety:** Zero modifications to backend or core cryptographic engines (`apps/api/**`, `core/**`, `attacks/**`).
