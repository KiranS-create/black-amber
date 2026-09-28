# AegisTrace (Black Amber) — Clean-Room Independent Reproduction Guide
**Smart India Hackathon 2026** | **Problem Statement ID:** SIH26237  
**Version:** 1.0.0-rc1 | **Date:** September 28, 2026  
**Auditor Classification:** Third-Party Technical Evaluator Guide  

---

## 1. Clean-Room Reproduction Objective

This guide enables any independent auditor, technical judge, or security researcher to verify every claim in the AegisTrace repository from scratch in an isolated clean-room environment (e.g., fresh virtual machine or container) without prior state.

---

## 2. Environment Preparation

### Step 1: Clone Repository
```bash
git clone https://github.com/Kirans-create/black-amber.git
cd black-amber
```

### Step 2: Initialize Clean Python Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Frozen & Hash-Pinned Dependencies
```bash
pip install -r requirements.txt
```

---

## 3. Automated 6-Stage Reproduction Runner

The fastest way to verify end-to-end system invariants is the automated clean-room reproduction script:

```bash
python scripts/reproduce_clean_environment.py
```

### Expected Output (< 5.0 Seconds):
```
===========================================================================
  AEGISTRACE CLEAN-ROOM INDEPENDENT REPRODUCTION RUNNER
  Smart India Hackathon 2026 — Zero-Trust PQC Forensic Platform
===========================================================================

--> [Stage 1/6] Auditing Canonical Source Tree Integrity...
--> [Stage 2/6] Executing Cryptographic & Runtime Self-Tests...
--> [Stage 3/6] Executing 24-Step Multi-Recipient Golden Pipeline...
--> [Stage 4/6] Verifying Offline Evidence Package Invariants...
--> [Stage 5/6] Executing Blind Signal Separation & Negative Testing...
--> [Stage 6/6] Running Composed Red-Team Attack Chains (A-G)...

===========================================================================
  INDEPENDENT REPRODUCTION EXECUTION SCORECARD
===========================================================================
  [PASS] 1 Source Tree Integrity                    (  190.2 ms)
  [PASS] 2 Startup Self Tests                       (  313.5 ms)
  [PASS] 3 Golden Pipeline                          ( 3619.4 ms)
  [PASS] 4 Offline Verification                     (  121.8 ms)
  [PASS] 5 Blind Evaluation                         (  101.0 ms)
  [PASS] 6 Composed Attack Chains                   (  636.5 ms)
---------------------------------------------------------------------------
  Overall Reproduction Status: PASS
  Total Execution Time:        4.98 seconds
  Physical Attestation:        NOT_VERIFIED (Simulated optical test fixture)
  Reproduction Report Path:    artifacts/reproduction/reproduction_report.json
===========================================================================
```

---

## 4. Air-Gapped Standalone Verifier Execution

To verify that forensic evidence can be inspected independently without network access:

```bash
python aegistrace_verify.py artifacts/demo/golden_case/golden_evidence_package.zip
```

### Expected Output:
```
======================================================================
AEGISTRACE FORENSIC EVIDENCE PACKAGE VERIFICATION REPORT
======================================================================
Package ID:           pkg_CASE_SIH_rel_2026_...
Overall Status:       VERIFIED
Verified At:          2026-09-28T...
----------------------------------------------------------------------
Manifest Signature:   VALID (ML-DSA-65)
Merkle Commitment:    VALID (RFC-6962)
Content-Addressed:    VALID (SHA-256)
Dependency DAG:       VALID (Acyclic Grounded)
Recipient Signature:  VALID (ML-DSA-65)
Historical Key Bound: VALID (Temporal Invariant)
Ledger / DLT Proof:   VALID (Quorum Verified)
Watermark Binding:    VALID (Artifact Bound)
Lineage Integrity:    VALID (Boundary Preserved)
Chain of Custody:     VALID (Append-Only Hash Chain)
Attribution Decision: CONSISTENT (Ground Truth Followed)
======================================================================
```

---

## 5. Automated Regression Test Suite

Execute all 1,098 unit, integration, and security tests:

```bash
pytest -q
```
- **Expected Outcome:** `1,098 passed, 0 failed in ~12m`.

---

## 6. Static Secret & Credential Audit

Run the static secret scanner across the source code:

```bash
python scripts/deployment/scan_secrets.py --strict
```
- **Expected Outcome:** `Files scanned: 965+, Findings detected: 0 [OK]`.
