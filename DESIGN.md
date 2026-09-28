# Design System: AegisTrace (Black Amber)

## 1. Visual Theme & Atmosphere
AegisTrace is a high-assurance forensic investigation and cryptographic document security workstation. The atmosphere is **Forensic Luxury**—calm, precise, operational, and deeply trustworthy. Like a Leica rangefinder or a Swiss-engineered laboratory instrument, every element exists to serve clarity, truth, and verifiable integrity.

* **Density:** Cockpit Dense (8/10). Dense where operational analysis demands it (tables, evidence chains, timeline events, metadata inspectors), but generous in negative space around critical focal objects.
* **Variance:** Offset Asymmetric (7/10). Each page has an authored visual grammar tailored to its task rather than generic repeating card grids.
* **Motion:** Restrained Fluid CSS (5/10). Subtle spring transitions (`stiffness: 120, damping: 22`) for drawers and state changes; infinite micro-pulses for active verification. Zero gratuitous sci-fi scanning animations.
* **The Car Analogy:** The user operates the **steering wheel** (`Import`, `Protect`, `Distribute`, `Investigate`, `Verify`, `Export`). The **engine** (ML-KEM-768, ML-DSA-65, 2D DSSS, Tardos codes, Bayesian fusion, Merkle trees) operates silently below the abstraction boundary and is exposed only through contextual **Technical Details** inspectors.

---

## 2. Color Palette & Roles
The color palette is strictly calibrated for dark-first forensic operation with a warm graphite baseline and an authoritative petrol signature.

* **Canvas Deep** (`#0B1015`) — Deepest background canvas (Level 0).
* **Surface Workstation** (`#121B23`) — Primary operational panel and container background (Level 1).
* **Surface Subtle** (`#0E151C`) — Secondary recessed surface, sidebar background, table headers.
* **Surface Elevated** (`#17222C`) — Raised inspectors, popovers, active cards, filter containers (Level 2).
* **Glass Overlay** (`rgba(23, 34, 44, 0.76)`) — Strictly restricted to floating modals, drawers, and command palette (Level 3).
* **Hairline Border** (`rgba(255, 255, 255, 0.08)`) — 1px crisp structural definition. Never glowing.
* **Strong Border** (`rgba(255, 255, 255, 0.14)`) — Focus outlines, selected items, active splitters.
* **Warm Ivory** (`#F2EFE8`) — Primary text and headers. High-contrast, gentle on dark backgrounds.
* **Slate Gray** (`#A9B3BD`) — Secondary text, labels, descriptions, column headers.
* **Muted Graphite** (`#73808C`) — Tertiary text, inactive states, timestamp metadata.
* **Petrol Teal** (`#4C9A9A`) — Signature accent for primary actions, selected indicators, and trace connectors.
* **Jade Verified** (`#4FA77B`) — Forensic confirmation, verified evidence, passed checks, valid ledger.
* **Amber Warning** (`#C59645`) — Downstream gap, simulation calibration, missing channels, cautionary notes.
* **Crimson Danger** (`#C86464`) — Tamper detected, verification failed, revoked identity, compromised node.
* **Slate Blue Info** (`#7187B9`) — Informational notes, directory metadata, system diagnostics.

---

## 3. Typography Rules
Typography establishes clear editorial and forensic hierarchy.

* **Display & Titles:** `Geist`, `-apple-system`, `BlinkMacSystemFont`, `Segoe UI`, `sans-serif`. Track-tight (`-0.02em`), controlled scale. Never shouting.
  - Page Titles: `20px` / `1.3` (Semi-bold 600)
  - Section Headers: `14px` / `1.4` (Medium 500, uppercase letter-spacing `0.06em`)
  - Body Text: `13px` / `1.5` (Regular 400, Slate `#A9B3BD`)
  - Micro-metadata: `11px` / `1.4` (Graphite `#73808C`)
* **Monospace & Cryptographic Data:** `JetBrains Mono`, `IBM Plex Mono`, `ui-monospace`, `Menlo`, `monospace`.
  - Used strictly for: SHA-256 hashes, Merkle roots, candidate IDs, block indices, KEM public keys, timestamps, LLR values.
  - Scale: `11.5px` with subtle tracking (`0.02em`).
* **Banned Fonts:** `Inter` (overused SaaS default), Comic/decorative fonts, generic unstyled serifs in software dashboards.

---

## 4. Component Stylings
Every component has defined shape, depth, border, and interaction behavior.

* **Buttons:**
  - *Primary:* Solid Petrol fill (`#4C9A9A`), Dark text (`#0B1015`), font-weight 600, radius `6px`. Subtle `-1px` push on active.
  - *Secondary:* Surface elevated fill (`#17222C`), Hairline border (`rgba(255,255,255,0.1)`), Warm Ivory text (`#F2EFE8`).
  - *Ghost / Tertiary:* Transparent background, Slate text, hover surface highlight.
  - *Danger:* Crimson subtle fill (`rgba(200, 100, 100, 0.12)`), Crimson text (`#DE7B7B`), border (`rgba(200, 100, 100, 0.28)`).
* **Native File Chooser / Dropzone:**
  - Must provide a primary, clearly clickable `[ Browse Files ]` button and secondary native drag-and-drop.
  - Fully reachable `<input type="file">` accepting all Tier-1 production formats: `.pdf, .docx, .pptx, .xlsx, .png, .jpg, .jpeg`.
  - Visual validation state changes: `EMPTY` → `VALIDATING` → `UPLOADING` → `WATERMARKING` → `READY`.
* **Data Tables:**
  - High-density, border-bottom divider rows (`1px solid rgba(255,255,255,0.06)`).
  - Sticky header with uppercase subtle metadata labels.
  - Row hover highlight (`#17232E`) and subtle selection state with a 2px left Petrol bar.
* **Contextual Drawers:**
  - Slide out from right edge with 320px–480px width, `rgba(23, 34, 44, 0.94)` background, hair-line border.
  - Dedicated to progressive disclosure of Technical Details (Bayesian priors, Merkle paths, KEM fingerprints).
* **Status Badges & Pills:**
  - Compact geometry (height 20px, radius 4px, font-size 11px).
  - Subtle tinted background (`rgba(..., 0.12)`) + 1px border (`rgba(..., 0.28)`) + high-contrast text. No glowing halos.

---

## 5. Layout Principles & Page Grammar
Generic card grids are prohibited. Each surface is composed around its functional objective.

* **Overview:** Quiet operational cockpit. When empty: single calm invitation `[ Import artifact ]`. When populated: operational health, recent real activity, and direct workflow pathways.
* **Documents:** Forensic registry. Wide structured table with multi-format metadata, quick filter rail, and a prominent `[ Browse Files ]` import action.
* **Investigations:** Asymmetric 4-zone workstation:
  - *Left (260px):* Vertical evidence & incident timeline.
  - *Center (Flexible):* Recovered/suspect artifact examination canvas.
  - *Right (320px):* Case findings, attribution confidence, epistemic limitations, and technical LLR details.
  - *Bottom (Full-width):* Multi-channel evidence correlation chain.
* **Evidence:** Large examination viewer centered on the evidence record with verdict validation cards (`VERIFIED: 12/12 checks passed`).
* **Provenance:** Large DAG canvas with clean contextual node inspector.
* **Audit Ledger:** Dense, verifiable chronological table with selected block cryptographic inspector.

---

## 6. Epistemic Honesty & Forensic Boundaries
The interface must communicate scientific truth and physical limitations transparently:

* `VERIFIED` — Formally proven with end-to-end cryptographic and watermark match.
* `DEVICE_IN_LOOP` — Hardware attestation verified on enrolled client device.
* `SIMULATION_CALIBRATION` — Calibrated under optical print/scan or lossy format transformation models.
* `DOWNSTREAM_GAP` — Controlled custody ended; no verified data exists beyond this physical/human boundary.
* `UNAVAILABLE` — Physical channel or hardware absent in current execution context.
* `NOT_VERIFIED` — Unverified candidate or unauthenticated artifact.

---

## 7. Anti-Patterns (Strictly Banned)
* ❌ No neon cyan, purple cyberpunk glows, or rainbow gradient text.
* ❌ No decorative matrix-style code rain, particles, or fake scanning HUD lasers.
* ❌ No 3-equal-card marketing dashboard layouts as default.
* ❌ No fake metrics, fake documents, fictional recipient cards, or fabricated telemetry.
* ❌ No dead buttons or non-functional file dropzones.
* ❌ No raw unhandled exceptions or Python tracebacks exposed to end-users.
* ❌ No emojis in formal forensic records.
