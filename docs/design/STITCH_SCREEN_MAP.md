# AegisTrace Stitch Screen Inventory Map

This map catalogs all 17 core redesigned screens for AegisTrace (*Black Amber*), detailing purpose, visual grammar, primary and secondary actions, desktop layout, and responsive collapse rules.

---

## Screen Inventory

### 1. Workstation Sign-In (`LoginScreen`)
* **Purpose:** High-security access portal for forensic operators and evaluation judges.
* **Composition:** Centered monolithic workstation card with subtle hairline grid texture backdrop.
* **Primary Action:** `[ Sign in ]`
* **Secondary Actions:** `[ Autofill ]` (Instant evaluation mode for `admin`/`admin`), `[ Open AegisTrace Verify ]` (Direct auditor shortcut).
* **Responsive:** Full-width centered container, tap-friendly inputs on mobile viewports.

### 2. Forensic Workspace Registration (`SignUpScreen`)
* **Purpose:** Workspace creation interface for organizational deployments.
* **Composition:** Structured vertical card with operational role, organization affiliation, and passkey configuration.
* **Primary Action:** `[ Create workspace ]`
* **Secondary Action:** `[ Back to sign in ]`

### 3. Operational Overview (`OverviewTab`)
* **Purpose:** Quiet cockpit communicating real operational posture.
* **Empty State:** Clean, intentional invitation: `Workspace ready. No protected artifacts yet.` with primary `[ Import artifact ]`.
* **Populated State:** Overall status (System Operational, Active Envelopes, Recent Verifications), triage pathways.
* **Prohibitions:** Banned fake KPI counters (`99.9%`, `42 Documents`) and non-existent telemetry feeds.

### 4. Protected Document Registry (`DocumentsTab`)
* **Purpose:** Central artifact inventory for classified assets and carriers.
* **Composition:** Wide data table (Name, Format, Size, Classification, Protection, Enrolled Recipients, Timestamp, Action) with top filter controls.
* **Primary Action:** `[ Import artifact ]` (Invokes native system file chooser).
* **Secondary Action:** Filter by classification (`TOP_SECRET`, `SECRET`, `CONFIDENTIAL`), Search by name/hash.

### 5. Document Import & Ingestion Experience (`DocumentsTab - Import Dropzone`)
* **Purpose:** Native file upload and format validation.
* **Composition:** Clean dual-mode zone: prominent `[ Browse Files ]` button and secondary drag-and-drop target.
* **Supported Formats:** Strictly verified Tier-1 formats: `PDF · DOCX · PPTX · XLSX · PNG · JPEG`.
* **States:** `Empty` → `File Selected` → `Validating Format` → `Ingesting Artifact` → `Watermarking Envelope` → `Ready`.

### 6. Document Forensic Inspector (`DocumentsTab - Drawer`)
* **Purpose:** Contextual examination of a selected document.
* **Composition:** Right-sliding drawer with SHA-256 content hash, carrier binding, format adapter details, and release status.
* **Primary Action:** `[ Create release for document ]`

### 7. Document Protection Pipeline (`ReleaseTab - Protection Section`)
* **Purpose:** Configure post-quantum protection envelopes and recipient-specific watermark keys.
* **Composition:** Clean 3-step configuration: Select Document, Select Enrolled Recipients, Choose Protection Profile.
* **Primary Action:** `[ Protect document ]` (No low-level cryptographic jargon).

### 8. Document Releases & Distribution (`ReleaseTab`)
* **Purpose:** Track multi-recipient forensic releases and distribution receipts.
* **Composition:** Structured distribution log detailing Release ID, Bound Artifact, Recipient Organization, and Transmission Timestamp.
* **Primary Action:** `[ Distribute release ]`

### 9. Recipient Identity Registry (`RecipientsTab`)
* **Purpose:** Enrolled human operators and custody trustees.
* **Composition:** Identity table with Name, Organization, Security Clearance, Device Binding ID, and Public Key Status.
* **Primary Action:** `[ Enroll new recipient ]`

### 10. Organization Directory (`DirectoryTab`)
* **Purpose:** Institutional hierarchy and departmental group memberships.
* **Composition:** Departmental tree view and identity list.

### 11. Forensic Investigation Workstation (`InvestigationsTab`)
* **Purpose:** The operational heart of AegisTrace—correlating leaked artifacts against forensic signals.
* **Composition (Asymmetric 4-Zone):**
  - **Left (260px):** Incident & Evidence Event Timeline.
  - **Center:** Main Recovered Artifact Viewer with watermark channel indicators.
  - **Right (320px):** Attribution Findings, Posterior Confidence, Epistemic Limitations, and Bayesian LLR panel.
  - **Bottom:** Multi-Channel Evidence Dependency Chain.
* **Primary Action:** `[ Analyze leak artifact ]` / `[ Upload suspect file ]`

### 12. Investigation Finding & Statistical Inspector (`InvestigationsTab - Drawer`)
* **Purpose:** Progressive disclosure of mathematical evidence fusion.
* **Composition:** LLR decomposition, Tardos score distribution, watermark bit accuracy, and anti-double-counting graph.

### 13. Evidence Examination Surface (`EvidenceTab`)
* **Purpose:** Review cryptographically sealed evidence bundles.
* **Composition:** Large primary evidence object with decisive verdict badge (`VERIFIED: 12/12 checks passed`) and Merkle path details.
* **Primary Action:** `[ Export signed evidence bundle ]`

### 14. AegisTrace Verify (`VerifyTab`)
* **Purpose:** Standalone, air-gapped evidence verifier for judges, inspectors, and independent auditors.
* **Composition:** Ultra-simple dropzone: `Drop evidence package here or [ Browse Files ]` → `[ Verify ]` → Instant Verdict.
* **Primary Action:** `[ Verify package ]`

### 15. Provenance DAG Visualizer (`ProvenanceTab`)
* **Purpose:** Visual lineage of custody transfers, releases, and investigations.
* **Composition:** Full-canvas directed acyclic graph (DAG) with node selection and contextual inspector.

### 16. Audit Ledger Explorer (`LedgerTab`)
* **Purpose:** Append-only cryptographic ledger tracking every operational event.
* **Composition:** Dense verifiable table with block numbers, SHA-256 block hashes, Merkle root commitments, and tamper detection.

### 17. System Health & Diagnostics (`SystemHealthTab` & `SettingsTab`)
* **Purpose:** Honest diagnostics of backend services, format adapters, and security trust boundaries.
* **Composition:** Service connectivity, database status, format adapter registry, and post-quantum crypto module health.
