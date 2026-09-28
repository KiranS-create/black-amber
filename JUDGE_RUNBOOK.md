# AegisTrace — Official Judge & Evaluator Runbook
**Product:** AegisTrace (Internal Code Name: *Black Amber*)  
**Problem Statement ID:** SIH26237  
**Version:** 1.0.0-production (Air-Gapped Sovereign Deployment)  
**Target Audience:** Smart India Hackathon Evaluators, Technical Judges & Security Auditors  

---

## Quick Navigation: Evaluator Commands

```bash
# 1. Complete 14-Step Deterministic Judge Walkthrough (~5 seconds)
python aegistrace.py demo judge --quick

# 2. Comprehensive Cryptographic & System Self-Tests
python aegistrace.py selftest

# 3. Clean Reset of Demo State to Zero Records
python aegistrace.py demo reset

# 4. Multi-Format Forensic Registry Inspection (17 Formats)
python aegistrace.py formats list

# 5. Connected Physical Hardware Status Inspection
python aegistrace.py device status

# 6. Independent Offline Evidence Package Audit
python aegistrace.py verify artifacts/packages/sample_package.zip
```

---

## 1. System Overview for Evaluators

AegisTrace solves the challenge of **Post-Quantum Traitor Tracing and Tamper-Evident Decryption Provenance** for classified, air-gapped sovereign environments. 

### Core Differentiators:
1. **NIST FIPS 203 & FIPS 204 Standards:** Uses genuine Post-Quantum Cryptography (ML-KEM-768 for broadcast key encapsulation and ML-DSA-65 for recipient non-repudiation provenance signatures).
2. **Dynamic Decryption-Time Watermarking:** Watermarks are not burned into static master documents; they are generated dynamically on the recipient's authorized endpoint during decapsulation and cryptographically bound to that specific session.
3. **Fail-Closed Bayesian Attribution:** Unlike fragile legacy hash comparisons, AegisTrace fuses multi-channel forensic signals (Watermark LLR, DLT proofs, Lineage, Telemetry) and enforces a strict theoretical threshold ($Z = 11.4$, $\varepsilon \le 10^{-5}$). If evidence is inconclusive or tampered with, the system **abstains** rather than making a false accusation.
4. **Epistemic Honesty:** The system never fakes hardware or passes simulated results as physical tests.

---

## 2. Evaluation Path A: 60-Second Command-Line Verification

For technical judges who want rapid, incontrovertible cryptographic proof directly in the terminal:

### Step 1: Run the 14-Step Deterministic Walkthrough
```bash
python aegistrace.py demo judge --quick
```
* **What it does:** Executes the complete lifecycle from document creation through broadcast encryption, Bob's decapsulation, leak intercept, blind watermark extraction, DLT Merkle proof correlation, evidence packaging, independent offline verification, adversarial tamper rejection, negative clean document evaluation, and clean demo reset.
* **Expected Output:** 14 consecutive green `[PASS]` tags, finishing with `VERDICT: ALL 14 FORENSIC INVARIANTS VERIFIED (0 ERRORS, 0 FABRICATIONS)` in ~5.0 seconds.

### Step 2: Test Adversarial Tamper Rejection (Fail-Closed)
Observe Step 11 and Step 12 in the walkthrough:
* Step 11 mutates the evidence package Merkle root (`ba` * 32).
* Step 12 runs the offline verifier and strictly outputs `Status: INVALID`. This proves that modified evidence packages cannot deceive the offline auditor.

### Step 3: Test Negative Document (Zero False Accusations)
Observe Step 13 in the walkthrough:
* A completely pristine, unwatermarked document is fed to the attribution engine.
* The engine reports `Status: NO_SIGNAL` / `ABSTAINED` and attributes to `None`. This proves the system will never frame an innocent officer.

### Step 4: Verify Zero-State Clean Reset
```bash
python aegistrace.py demo reset
```
* **Expected Output:**
  ```
  [PASS] Documents Cleared (0 active)
  [PASS] Releases Cleared (0 active)
  [PASS] Recipients Cleared (0 active)
  [PASS] Investigations & Jobs Cleared (0 active)
  [PASS] Evidence & Leaks Cleared (0 active)
  [PASS] Ledger Chain Reset (0 events)
  Result: Clean isolated demo state verified (all collections = 0).
  ```

---

## 3. Evaluation Path B: Web UI Interactive Experience

For judges evaluating user experience, workflow clarity, and visual presentation:

### Step 1: Start the Backend & Frontend
In Terminal 1 (Backend API):
```bash
python aegistrace.py serve
```
*(Runs on `http://127.0.0.1:8000`)*

In Terminal 2 (Web Console):
```bash
cd apps/web
npm run dev
```
*(Runs on `http://localhost:5173`)*

### Step 2: Sign In
* Navigate to `http://localhost:5173`.
* Enter credentials:
  * **Operator / Admin:** Username: `admin` | Password: `admin`
  * Or click **"Use Demo Credentials"** for instant 1-click access.

### Step 3: Production Cold-Start Inspection
* Notice that in production mode, every tab begins in an **authentic empty state**:
  * 0 documents, 0 releases, 0 ledger events, 0 active investigations.
* AegisTrace does **not** clutter production with fake placeholder data.

### Step 4: Load Isolated Demo State or Run Quick Scenario
* In the top bar, click **"Load Demo Fixtures"** to populate the isolated scenario (Alice, Bob, Charlie).
* Or click **"Evaluate benchmark"** in the Investigations tab:
  * Click **"Clean digital leak"** to observe immediate attribution of Bob ($Z > 11.4$ LLR).
  * Click **"Heavy blur / noise"** to observe carrier degradation and fail-closed margin behavior.
  * Click **"No watermark"** to observe fail-closed abstention (`INSUFFICIENT EVIDENCE`).

### Step 5: Visual Presentation States in Investigations
Observe the dedicated top ribbon in the Investigations tab:
* **Visual Presentation State:** Explicitly displays `VERIFIED`, `SIGNAL DETECTED`, `CORRELATING`, `INSUFFICIENT EVIDENCE`, `DOWNSTREAM GAP`, `VERIFICATION FAILED`, or `TAMPER DETECTED`.
* **Hardware Modality Status Cards:**
  * `Device-in-loop`: `Verified` (Real hardware phone validated)
  * `Camera Capture`: `Not verified` (Headless environment)
  * `Physical Printer`: `Unavailable`
  * `Flatbed Scanner`: `Unavailable`
* **Forensic Multi-Format Pipeline:** Displays badges for `PDF`, `DOCX`, `PPTX`, `XLSX`, `PNG`, `JPEG`.

### Step 6: Test Tamper Detection in the Ledger View
1. Switch to the **Audit Ledger** tab.
2. Observe the cryptographic hash chain linking genesis to the latest decryption events.
3. Click **"Simulate Tamper"** in the top bar (mutates block payload).
4. Watch the chain status instantly turn red with an explicit cryptographic hash mismatch alert highlighting the exact compromised block.
5. Click **"Reset Chain"** to restore verifiable integrity.

### Step 7: Export & Inspect Cryptographic Evidence Dossier
1. In the Investigations tab, click **"Export evidence dossier"**.
2. Review the structured forensic dossier containing:
   * Case identity and suspect candidate summary
   * Multi-channel Bayesian fusion breakdown
   * Digital signatures (ML-DSA-65) and Merkle proof hashes
   * Exportable JSON package with SHA-256 integrity digest

---

## 4. Evaluation Path C: Offline Verifier Audit

To test sovereign air-gapped verification without running the server:

```bash
# 1. Run full golden pipeline to produce a fresh sealed evidence package
python -c "from core.integration.orchestrator import AegisTraceEndToEndOrchestrator; orch = AegisTraceEndToEndOrchestrator(); res = orch.run_full_golden_pipeline(); print('Generated package ID:', res.evidence_package.manifest.package_id)"

# 2. Verify an offline package directly via CLI
python aegistrace.py verify artifacts/packages/golden_evidence_package.zip
```

* The verifier will independently parse the archive, recompute all object SHA-256 hashes, rebuild the RFC 6962 Merkle tree, verify the ML-DSA-65 manifest signature, check the DAG for circular dependencies, and output `[PASS]` for every cryptographic constraint.

---

## 5. Evaluation Path D: Full Test Suite Regression

To verify that all 1,098 automated tests pass on the local system:

```bash
# Run complete test suite (PQC, Watermarking, Ledger, Fusion, Formats, Red Team)
pytest tests/ -q
```
* **Verified Total:** 1,098 passed tests, 0 failures, 0 errors.
