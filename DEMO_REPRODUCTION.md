# AegisTrace Evaluator Reproduction Runbook: Golden Forensic Investigation
**Smart India Hackathon 2026 — Project ID: SIH26237**  
**Code Name:** Black Amber | **Classification:** Official Evaluation Runbook  
**System Integrity:** Strictly Air-Gapped // Zero Network Dependencies // Fully Deterministic

---

## 1. Executive Summary

This runbook guides evaluators, judges, and third-party auditors through the deterministic, bite-for-byte reproduction of the **AegisTrace Final Golden Forensic Investigation**.

The scenario demonstrates the sovereign end-to-end lifecycle:
$$\text{Canonical Artifact} \longrightarrow \text{PQC Cohort Distribution} \longrightarrow \text{Volatile Decryption \& Watermarking} \longrightarrow \text{Blind Leak Seizure} \longrightarrow \text{Blind Demodulation \& DLT Correlation} \longrightarrow \text{Bayesian Evidence Fusion} \longrightarrow \text{Court-Admissible Evidence Package} \longrightarrow \text{Controlled Tamper Attack} \longrightarrow \text{Fail-Closed Rejection} \longrightarrow \text{Restoration \& Zero-State Reset}$$

### Epistemic & Operational Guarantees
- **Strict Isolation**: All demo data operates inside `artifacts/demo/golden_run/` and is prefixed with `demo-` / tagged `DEMO DATA`.
- **Zero Production Pollution**: No records are ever written to production databases (`data/metadata.sqlite3`) or live stores.
- **Air-Gap Verification**: Operates completely offline with zero calls to internet services or cloud key management systems.
- **Fail-Closed Security**: Any mutation to evidence packages triggers immediate and strict verification rejection (`INVALID`).

---

## 2. Environment Prerequisites

Ensure you are in the repository root directory `c:\Projects\SIH26237` with an active Python 3.9+ environment containing project dependencies:

```powershell
# Verify Python runtime
python --version
# Expected: Python 3.9.x or higher

# Verify repository location
pwd
# Expected: c:\Projects\SIH26237
```

---

## 3. Fast-Path: Single-Command Judge Walkthrough

To execute the entire golden investigation in a single, automated, human-readable pass:

```powershell
python aegistrace.py demo judge
```

### Expected Output
```text
======================================================================
  AEGISTRACE SOVEREIGN FORENSIC PLATFORM — GOLDEN INVESTIGATION
  Smart India Hackathon 2026 — SIH26237 // Code Name: Black Amber
  Status: [DEMO MODE ACTIVE] // Isolated Boundary: artifacts/demo/golden_run/
======================================================================

  [1/7] Artifact Creation ............ PASS (~45 ms)
  [2/7] Cohort PQC Distribution ...... PASS (~2100 ms)
  [3/7] Blind Leak Seizure ........... PASS (~35 ms)
  [4/7] Multi-Channel Investigation .. PASS (~95 ms)
  [5/7] Evidence Package & Audit ..... PASS (~500 ms)
  [6/7] Controlled Tamper Attack ..... REJECTED (~130 ms)
  [7/7] Canonical Restoration ........ PASS (~125 ms)

----------------------------------------------------------------------
  GOLDEN INVESTIGATION OUTCOME SUMMARY:
  * Attributed Recipient:  demo-recipient-b (Demo Recipient B)
  * Posterior Confidence:  99.85% (p-value: 1.2e-9)
  * 12-Pillar Verification: VERIFIED
  * Tamper Defense Result:  INVALID (Attacks fail-closed)
  * Restoration Status:    VERIFIED
  * Total Run Duration:    ~3200 ms
======================================================================
```

To export the complete execution report in machine-readable JSON:
```powershell
python aegistrace.py demo judge --json
```

---

## 4. Granular Stage-by-Stage Forensic Progression

Evaluators wishing to audit each forensic milestone independently can execute the sequential subcommands detailed below.

### Stage 1: Canonical Document Generation
Generates the standard 800x1000 test canvas with explicit demo classification banners, structured metadata box, and ArUco corner fiducials.

```powershell
python aegistrace.py demo start
```
- **Generated Artifacts**:
  - `artifacts/demo/golden_run/original_document.png` (Canonical test image)
  - `artifacts/demo/golden_run/artifact.json` (Document metadata & SHA-256)
  - `artifacts/demo/golden_run/run_manifest.json` (Demonstration state tracker)
- **Verification**:
  - Document ID: `doc_controlled_forensic_test`
  - Dimensions: 800x1000, 3-channel RGB

---

### Stage 2: Multi-Recipient PQC Distribution & Volatile Decryption
Enrolls 3 synthetic recipients (`demo-recipient-a`, `b`, `c`), 3 DLT validators (`val_delhi_01`, `val_mumbai_02`, `val_bengaluru_03`), and chief examiner keypair. Encrypts document with AES-256-GCM + ML-KEM-768 encapsulation. Simulates recipient volatile decryptions, generating distinct dynamic 2D DSSS watermarks and ML-DSA-65 signed receipts anchored in DLT Block 101.

```powershell
python aegistrace.py demo distribute
```
- **Generated Artifacts**:
  - `artifacts/demo/golden_run/recipient_state.json` (PQC public/private key pairs)
  - `artifacts/demo/golden_run/distribution.json` (Broadcast release & DLT commitments)
  - `artifacts/demo/golden_run/watermarked_demo_recipient_a.png`
  - `artifacts/demo/golden_run/watermarked_demo_recipient_b.png`
  - `artifacts/demo/golden_run/watermarked_demo_recipient_c.png`
- **Key Assertions**:
  - Structural Similarity: $\text{SSIM} \ge 0.80$ (measured ~0.8406) across all 3 copies
  - Peak Signal-to-Noise Ratio: $\text{PSNR} \ge 28.0\text{ dB}$
  - Visual Equivalence: Evaluated as `True`

---

### Stage 3: Blind Leak Artifact Seizure
Simulates discovery of an unauthorized leaked document copy on an unencrypted external storage drive. The suspect identity is intentionally withheld from the leak metadata to enforce a blind investigation.

```powershell
python aegistrace.py demo leak --recipient demo-recipient-b
```
- **Generated Artifacts**:
  - `artifacts/demo/golden_run/leak.png` (Seized artifact byte stream)
  - `artifacts/demo/golden_run/leak.json` (Chain of custody seizure record)
- **Key Assertions**:
  - Suspect identity absent from `leak.json` context
  - Investigation status set to `PENDING_FORENSIC_ANALYSIS`

---

### Stage 4: Blind Watermark Demodulation & Evidence Fusion
Performs blind 2D DSSS spatial demodulation, evaluates bit error rates against registered cohort commitments, verifies ML-DSA-65 recipient signature and DLT Block 101 inclusion proof, and executes Bayesian evidence fusion across 5 independent telemetry pillars.

```powershell
python aegistrace.py demo investigate
```
- **Generated Artifacts**:
  - `artifacts/demo/golden_run/investigation.json` (Complete forensic report)
- **Key Assertions**:
  - Bit Error Rate (BER) for `demo-recipient-b`: **0.0000** (100% symbol recovery)
  - Bit Error Rate (BER) for `demo-recipient-a`: **~0.5000** (Orthogonal noise)
  - Bit Error Rate (BER) for `demo-recipient-c`: **~0.5000** (Orthogonal noise)
  - Posterior Attribution Confidence: **99.85%** ($p\text{-value} = 1.2 \times 10^{-9}$)
  - Attribution Verdict: `demo-recipient-b`

---

### Stage 5: Court-Admissible Evidence Package Assembly & Offline Audit
Assembles 9 formal evidence objects into a DAG-anchored package, binds append-only chain of custody events, signs manifest with Chief Examiner's NIST FIPS 204 ML-DSA-65 key, and runs the standalone `OfflineEvidenceVerifier`.

```powershell
python aegistrace.py demo verify
```
- **Generated Artifacts**:
  - `artifacts/demo/golden_run/evidence_package.zip` (Portable standalone archive)
  - `artifacts/demo/golden_run/evidence_package.json` (Package manifest)
  - `artifacts/demo/golden_run/verification.json` (12-pillar audit log)
- **12-Pillar Verification Check**:
  1. Tenant Boundary Isolation: `PASS`
  2. ML-DSA-65 Manifest Signature: `PASS`
  3. Merkle Tree Commitment Root: `PASS`
  4. Content-Addressed Object Hashes: `PASS`
  5. Dependency DAG Acyclicity & Completeness: `PASS`
  6. Recipient ML-DSA-65 Provenance Signature: `PASS`
  7. Historical Key Validity & Revocation Checks: `PASS`
  8. DLT Quorum Multi-Signature Inclusion Proof: `PASS`
  9. Dynamic Watermark Token Cryptographic Binding: `PASS`
  10. Lineage Graph Boundary Preservation: `PASS`
  11. Append-Only Chain of Custody Hash Linkage: `PASS`
  12. Evidence Decision Consistency: `PASS`

---

### Stage 6: Controlled Tamper Attack (Merkle Root Mutation)
Simulates an adversarial tampering attempt where an attacker modifies the evidence manifest's Merkle commitment root. Executes `OfflineEvidenceVerifier` against the tampered package.

```powershell
python aegistrace.py demo tamper
```
- **Generated Artifacts**:
  - `artifacts/demo/golden_run/evidence_package_tampered.zip`
  - `artifacts/demo/golden_run/tamper.json`
- **Key Assertions**:
  - Verifier Verdict: `INVALID`
  - Strict Fail-Closed Execution: Rejection confirmed with exact error codes recorded.

---

### Stage 7: Pristine Package Restoration
Re-runs the independent offline audit on the pristine `evidence_package.zip`, proving the attack was contained and the original evidence remains verifiable.

```powershell
python aegistrace.py demo restore
```
- **Generated Artifacts**:
  - `artifacts/demo/golden_run/restore.json`
- **Key Assertions**:
  - Verifier Verdict: `VERIFIED`

---

### Stage 8: Zero-State Purge & Isolation Reset
Purges all files in `artifacts/demo/golden_run/` and clears any memory structures, returning the platform to its zero-state.

```powershell
python aegistrace.py demo reset
```
- **Expected Output**:
  - Disk Artifacts Purged: 17 files removed
  - Documents Cleared: 0 active
  - Releases Cleared: 0 active
  - Recipients Cleared: 0 active
  - Investigations Cleared: 0 active
  - Evidence Cleared: 0 active
  - Ledger Chain Reset: 0 events

---

## 5. Automated Negative Control & Boundary Verification

AegisTrace guarantees zero false accusations when presented with unwatermarked clean documents or incomplete downstream lineages.

### Negative Control: Clean Document Abstention
```powershell
pytest tests/demo/test_demo_negative_case.py -v
```
- **Expected Result**: `NO_SIGNAL` / `should_abstain: True`, `attributed_recipient: None`, 0 false accusations.

### Lineage Boundary: Downstream Gap Case
```powershell
pytest tests/demo/test_demo_downstream_gap.py -v
```
- **Expected Result**: `DOWNSTREAM_GAP` / `INSUFFICIENT_EVIDENCE`, `last_known_holder: demo-recipient-b`, `attributed_principal: None`.

---

## 6. Full Automated Test Suite Execution

To execute the entire 10-test suite verifying golden case execution, isolation, determinism, tamper resistance, and zero production database leakage:

```powershell
pytest tests/demo/ -v
```

### Expected Output
```text
tests/demo/test_demo_downstream_gap.py::test_downstream_gap_abstention PASSED
tests/demo/test_demo_isolation.py::test_demo_isolation_and_tagging PASSED
tests/demo/test_demo_negative_case.py::test_clean_document_abstention PASSED
tests/demo/test_demo_no_production_leakage.py::test_no_production_database_leakage PASSED
tests/demo/test_demo_reproducibility.py::test_deterministic_reproducibility PASSED
tests/demo/test_demo_reset.py::test_demo_reset_zero_state PASSED
tests/demo/test_demo_reset.py::test_orchestrator_demo_reset_collections PASSED
tests/demo/test_demo_tamper.py::test_tamper_attack_fail_closed PASSED
tests/demo/test_golden_case.py::test_golden_case_lifecycle PASSED
tests/demo/test_golden_case.py::test_golden_case_run_judge PASSED

============================= 10 passed in ~25s =============================
```

---

## 7. Artifact Manifest Table

| Artifact Name | MIME Type | Epistemic Category | Cryptographic Guarantee |
|---|---|---|---|
| `original_document.png` | `image/png` | Ground Truth Source | Canonical 800x1000 canvas, SHA-256 sealed |
| `artifact.json` | `application/json` | Source Metadata | Strict `DEMO DATA` labeling, immutable hash |
| `recipient_state.json` | `application/json` | Cryptographic Keystore | NIST FIPS 203 ML-KEM-768 + FIPS 204 ML-DSA-65 keys |
| `distribution.json` | `application/json` | Broadcast Commitment | AES-256-GCM ciphertext, DLT Block 101 Merkle root |
| `watermarked_demo_recipient_*.png` | `image/png` | Dynamic Modulated Copy | 2D DSSS carrier, SSIM $\ge 0.80$, visual equivalence |
| `leak.png` | `image/png` | Seized Evidence | Blind seizure copy with suspect identity withheld |
| `leak.json` | `application/json` | Ingestion Chain | Timestamped seizure record, zero-knowledge attribution context |
| `investigation.json` | `application/json` | Forensic Attribution Report | 0 BER correlation, 99.85% Bayesian confidence, timeline |
| `evidence_package.zip` | `application/zip` | Portable Legal Bundle | 9 objects, DAG dependency edges, ML-DSA-65 signature |
| `evidence_package.json` | `application/json` | Package Metadata | Merkle root commitment, examiner identity |
| `verification.json` | `application/json` | Standalone Audit Log | Independent 12-pillar audit results, verified offline |
| `tamper.json` | `application/json` | Adversarial Security Record | Merkle root forgery detection, fail-closed validation |
| `restore.json` | `application/json` | Fixture Integrity Record | Canonical package re-verification after tamper test |
| `run_manifest.json` | `application/json` | Lifecycle Manifest | Complete audit trace connecting all 10 JSON artifacts |

---

## 8. Summary of Evaluator Commands

```powershell
# 1. Automated Judge Walkthrough (Recommended)
python aegistrace.py demo judge

# 2. Reset Demo State (Restores Zero-State)
python aegistrace.py demo reset

# 3. Execute Complete Demo Test Suite
pytest tests/demo/ -v
```
