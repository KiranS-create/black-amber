# AegisTrace Main Domain Screen Map & Workflow Architecture

This document establishes the user journeys, screen composition, and navigation topology for the redesigned Main Domain (`https://aegistrace-kirans-create.vercel.app`).

---

## 1. Core Workflow Topology

```
[Login Screen] (Autofill: admin/admin)
      │
      ▼
[Main Application Shell]
      ├── 1. Overview (Command Center: System state, quick metrics, recent alerts)
      │
      ├── 2. Documents (Content-addressed Registry & Ingestion)
      │         ├── Import Zone (Drag & drop + working native "Browse Files")
      │         ├── Document List (Filter by name, type, date)
      │         └── Document Inspection Drawer
      │               ├── "Protect document" (Select recipients: Alice, Bob, Charlie)
      │               ├── "Create release" (PQC encapsulation + Tardos code)
      │               └── Collapsible "Technical details"
      │
      ├── 3. Investigations (Forensic Attribution & Bayesian Evidence)
      │         ├── Active Leak Cases (Ingest intercepted document)
      │         ├── Suspect Finding Card (Attributed Leaker, Posterior Probability)
      │         ├── Multi-Channel Corroboration (Digital watermarks, PQC receipts, timing)
      │         └── Collapsible "Technical details" (Log-likelihood, Merkle roots)
      │
      ├── 4. Evidence (Verification & Custody Examination)
      │         ├── Forensic Package Summary (Manifest, Signed Objects, Custody Chain)
      │         ├── "Export evidence package (.zip)" (1-click signed download)
      │         └── AegisTrace Verify (Zero-server offline dropzone)
      │
      └── 5. Settings / More Modal
                ├── Enrolled Principals (Alice, Bob, Charlie public keys)
                ├── Enterprise Directory & Groups
                ├── Audit Ledger Events (Tamper-evident hash chain)
                └── System & PQC Health Diagnostics
```

---

## 2. Page-by-Page Specifications

### Screen 1: Login & Authentication
- **Purpose**: Fast, friction-free access for judges and forensic examiners.
- **Header**: Minimal logo `AegisTrace`.
- **Form**:
  - `Username` input.
  - `Password` input with show/hide password toggle.
  - `Sign in` button.
- **Demonstration Access**: Subtle pill `DEMO ACCESS: admin / admin` with instant `Autofill` action.
- **Zero-Server Link**: `Judicial examiner or auditor? Verify evidence package →` (direct link to standalone verifier mode).

### Screen 2: Overview (Command Center)
- **Primary Hero Banner**: Workspace status (`Operational`), PQC Engine (`ML-KEM-768 / ML-DSA-65`), Evidence Chain (`Verified`).
- **High-Signal Metrics**: 3 compact stats only (Total Documents, Active Releases, Enrolled Recipients).
- **Primary Call to Action**: `Import artifact` or `Investigate leak`.
- **Recent Activity Stream**: Live feed of cryptographic events (Document sealed, Package decrypted, Audit ledger appended).

### Screen 3: Documents (Registry & Ingestion)
- **Top Row**: Section title `Document Registry`, count indicator, and `Import artifact` button.
- **Import Drop Zone**:
  - Drag-over border highlight.
  - Clear text: `Drop document here or click to browse`.
  - Button: `Browse Files` (binds to native file dialog).
  - Explicit formats: `PDF · DOCX · PPTX · XLSX · PNG · JPEG · TXT · CSV · RTF · ZIP`.
- **Document Table**:
  - Columns: Name, Format, Original SHA-256 (truncated monospace), Created, Status, Actions.
  - Action: `Inspect` opens `DocumentDetailDrawer`.
- **Document Detail Drawer**:
  - Document metadata.
  - Primary button: `Protect & Release`.
  - Recipient selection checkboxes (Alice, Bob, Charlie).
  - `Generate PQC Packages` trigger.
  - Collapsible `Technical details`.

### Screen 4: Investigations (Attribution Workstation)
- **Header**: Section title `Investigations`, active case count.
- **Leak Intake**: Dropzone to submit intercepted leaked file.
- **Primary Finding Card**:
  - Attribution Banner: `Attributed to Bob (usr_test_bob)`.
  - Posterior Confidence: `99.8%` (Forensic Jade badge).
  - Corroborating Channels: 3 channels active (Physical watermark match, PQC decryption signature verified, Decryption timestamp correlation).
  - Known Limitations: `Zero downstream custody gap detected`.
- **Collapsible Technical Details**:
  - Bayesian log-likelihood ratio.
  - Tardos code symbol match matrix.
  - Recipient decryption receipt hash.

### Screen 5: Evidence & Offline Verifier
- **Header**: Section title `Evidence & Verification`.
- **Integrity Status Card**: Overall status `VERIFIED` with tamper-evident Merkle tree guarantee.
- **Actions**:
  - `Export Signed Evidence Package (.zip)`
  - `Verify Package (Zero-Server)`
- **Verifier Sub-Surface**:
  - Dropzone for `.zip` evidence archive.
  - Immediate client/server validation: Manifest signature, Merkle root, SHA-256 object digests, custody continuity.
  - Result: Large `VERIFIED` badge with detailed cryptographic checklist.

### Screen 6: More / Settings (Contextual Modal)
- Houses all secondary administration surfaces without cluttering daily workflows:
  - **Principals**: Alice, Bob, Charlie enrolled public keys.
  - **Ledger**: Tamper-evident hash-chained events.
  - **System**: PQC health, memory, database latency.
