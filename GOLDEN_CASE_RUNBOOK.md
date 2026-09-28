# AegisTrace Golden Case Runbook

**Document:** Operational Demonstration Runbook for SIH Evaluators & Forensic Examiners  
**Case Title:** Operation Amber Horizon - Classified Strategic Directive Leak Investigation  
**Case ID:** `CASE_SIH_GOLDEN_001`  
**Classification:** TOP SECRET // SIH-RESTRICTED  

---

## 1. Scenario Context & Objective

In this operational simulation:
- **Issuer:** Strategic Command (`HQ_STRATCOM`)
- **Document:** `Master_Operational_Brief_2026.pdf`
- **Authorized Recipients:**
  1. `Alice Vance` (`alice@defense.gov` - Workstation TPM)
  2. `Bob Martin` (`bob@defense.gov` - Secure Enclave Mobile)
  3. `Charlie Knox` (`charlie@defense.gov` - Hardware Token)
- **Incident:** A leaked document artifact is recovered from an unauthorized public paste/repository.
- **Forensic Goal:** Ingest leak artifact, extract dynamic watermark, verify ledger signatures and consensus, build evidence package, and execute offline verification.

---

## 2. Execution Runbook

### Step 1: Execute Complete Pipeline Benchmark
Run the automated integration benchmark and artifact generator:
```bash
python scripts/benchmark_end_to_end_stitch.py
```
This generates:
- `artifacts/integration/end_to_end_benchmark.json`
- `artifacts/integration/END_TO_END_BENCHMARK_REPORT.md`
- `artifacts/golden_case/golden_case_evidence_package.json`
- `artifacts/golden_case/golden_case_verification_report.json`
- `artifacts/conformance/sih_problem_statement_matrix.json`

---

### Step 2: Inspect Golden Case Verification Report
Inspect the machine-readable offline verification verdict:
```json
{
  "package_id": "pkg_CASE_SIH_GOLDEN_001",
  "overall_status": "VERIFIED",
  "manifest_signature_valid": true,
  "merkle_root_valid": true,
  "object_hashes_valid": true,
  "dependency_graph_valid": true,
  "recipient_signature_valid": true,
  "historical_keys_valid": true,
  "ledger_proof_valid": true,
  "watermark_binding_valid": true,
  "lineage_valid": true,
  "custody_chain_valid": true,
  "decision_consistent": true
}
```

---

### Step 3: Run the Independent Offline Verifier CLI
Export the golden case to a standalone `.zip` and audit on an air-gapped machine:
```bash
python aegistrace_verify.py artifacts/golden_case/golden_case_evidence_package.zip --tenant tenant_golden_case
```

**Expected Console Output:**
```
======================================================================
AEGISTRACE FORENSIC EVIDENCE PACKAGE VERIFICATION REPORT
======================================================================
Package ID:           pkg_CASE_SIH_GOLDEN_001
Overall Status:       VERIFIED
Verified At:          2026-09-27T21:40:00Z
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

## 3. Adversarial Demonstration Runbook

### Test 1: Forging Recipient Signature
Attempt to modify the recipient ML-DSA-65 signature on the DecryptionReceipt:
- **Result:** Fails Pillar 6 (`recipient_signature_valid = false`, Status: `INVALID`).

### Test 2: Altering Evidence Document Object
Attempt to modify 1 byte in the leak artifact payload:
- **Result:** Fails Pillar 4 (Content Hash mismatch) and Pillar 3 (Merkle Root mismatch, Status: `INVALID`).

### Test 3: Cross-Tenant Injection
Attempt to verify the Defense evidence package under a Finance tenant context:
- **Result:** Fails Pillar 1 (`TENANT_ISOLATION_VIOLATION`, Status: `INVALID`).
