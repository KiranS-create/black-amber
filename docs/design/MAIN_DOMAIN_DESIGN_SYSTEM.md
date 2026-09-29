# Stitch Design System: AegisTrace Main Domain
**Semantic Design System & DNA for the High-End Forensic Instrument**

---

## 1. Visual Theme & Atmosphere

- **Atmosphere**: An austere, clinical, and exquisitely quiet forensic workstation. It possesses the gravitas of a cryptographic laboratory and the restraint of an authored physical instrument.
- **Density**: 4/10 ("Daily App Balanced" with generous whitespace, breathing margins, and high signal-to-noise ratio).
- **Variance**: 5/10 (Offset asymmetry with strong anchored headers and structured data planes).
- **Motion**: 4/10 (Restrained, spring-physics micro-interactions; zero glowing scanlines, zero cyberpunk decorative noise).

The visual feeling is **light on chrome, heavy on substance**. The user immediately understands what document is protected, what recipient was identified, and whether the cryptographic proof is mathematically sound—without having to parse paragraphs of explanatory jargon.

---

## 2. Color Palette & Roles

| Token Name | Hex / Value | Semantic Role |
| :--- | :--- | :--- |
| **Canvas Deep** | `#090C0F` | Primary application canvas (dark obsidian, non-pure black) |
| **Surface Raised** | `#12161B` | Primary cards, table bodies, inspection panels |
| **Surface Overlay** | `#181E26` | Drawers, modals, hover states, dropdown menus |
| **Hairline Border** | `rgba(255, 255, 255, 0.07)` | Hairline structural dividers, card outlines |
| **Border Active** | `rgba(255, 255, 255, 0.16)` | Selected state borders, focused inputs |
| **Ivory Primary** | `#EDEDE8` | Headings, active values, primary numbers |
| **Muted Slate** | `#8E98A5` | Secondary text, column headers, metadata labels |
| **Dim Carbon** | `#525D6B` | De-emphasized timestamps, inactive icons |
| **Forensic Jade** | `#22C55E` | Verified cryptographic state, valid signatures, intact Merkle root |
| **Amber Caution** | `#F59E0B` | Insufficient evidence, downstream custody gap, demo mode indicator |
| **Crimson Tamper**| `#EF4444` | Tamper detected, signature invalid, verification failed |
| **Petrol Accent** | `#38BDF8` | Single subtle focus accent for active tabs and primary buttons |

### Banned Color Patterns:
- ❌ Neon purple / magenta button glows or borders.
- ❌ Cyberpunk cyan grids or laser scanlines.
- ❌ Rainbow gradient headers.
- ❌ Pure black (`#000000`) surfaces.

---

## 3. Typography Rules

- **Display & Section Titles**: `Geist` (or system `system-ui, -apple-system, sans-serif`), weight 500-600, track-tight (`letter-spacing: -0.02em`). Scale is controlled (max 24px-28px on desktop), never shouting.
- **Body & Controls**: `Geist`, 13px-14px, line-height 1.5, regular (400) or medium (500). Max line-length 65ch.
- **Monospace Values**: `JetBrains Mono` / `IBM Plex Mono`, 11px-12px, tabular figures (`font-variant-numeric: tabular-nums`). Exclusively reserved for:
  - Document & release IDs (`doc_...`, `rel_...`)
  - Content SHA-256 digests
  - Public keys (ML-KEM-768, ML-DSA-65)
  - Bit-error rates and posterior probability percentages.

---

## 4. Component Stylings

### Left Sidebar:
- **Width**: Slim 200px (collapses to 56px on mobile/tablet).
- **Primary Items (4 total)**:
  1. `Overview` (Command center)
  2. `Documents` (Master document registry & ingestion)
  3. `Investigations` (Leak attribution & Bayesian findings)
  4. `Evidence` (Verification & immutable chain of custody)
- **Secondary / Utility**:
  - `Settings / More` (Compact trigger opening enrolled principals, directory, and system logs)
- **Visual Design**: Transparent backdrop, single vertical 1px hairline border, quiet icon + 13px label. Active item indicated by a clean, left-aligned 2px slate pill indicator.

### Header:
- **Height**: 48px.
- **Elements**: Discreet `AegisTrace` mark, active view breadcrumb, compact `DEMO DATA` status pill (when demo auth is active), theme toggle, and user sign-out icon.
- **Noise Elimination**: No duplicate search bars, no rows of 6 redundant status badges.

### Primary Buttons:
- Flat, tactile, 8px rounded corners.
- Primary: Subtle ivory fill (`#EDEDE8`) with deep obsidian text (`#090C0F`), font-weight 600.
- Secondary / Ghost: Surface raised fill with hairline border and ivory text.
- Interaction: Micro `-1px` translateY on active press. Zero glowing neon shadows.

### File Drop Zone (Import):
- Generous, uncluttered rectangular zone.
- Clear title: **"Import artifact"**
- Explicit supported list: `PDF · DOCX · PPTX · XLSX · PNG · JPEG`
- Primary button: **"Browse Files"** connected to native `<input type="file">`.
- Full drag-and-drop support with visual border highlight.

### Technical Details (Progressive Disclosure):
- Collapsible accordion or side drawer labeled **"Technical details"**.
- Contains full cryptographic parameters (ML-KEM-768 ciphertexts, ML-DSA-65 signatures, Tardos length $m=2048$, Dirichlet priors, Merkle leaf hashes).
- Hidden by default so casual evaluators see clean answers, while forensic auditors can expand on demand.

---

## 5. Anti-Patterns (Strictly Banned)

1. No decorative technology badges cluttering primary views.
2. No 12-item navigation bars.
3. No AI marketing clichés ("Elevate your security posture", "Seamless next-gen protection").
4. No fake metrics or ungrounded statistics.
5. No cluttered card grids with 10 duplicate counters.
6. No breaking native HTML file inputs.
