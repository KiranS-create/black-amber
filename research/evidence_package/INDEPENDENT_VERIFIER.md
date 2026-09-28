# AegisTrace Independent Offline Verifier Architecture (v1.0)
**Execution Mode:** Air-Gapped / Zero Network Egress / Standalone CLI  
**Executable:** `aegistrace_verify.py`  
**Core Engine:** `core.evidence_package.verifier.OfflineEvidenceVerifier`  
**Author:** AegisTrace Cryptographic Architecture Group  

---

## 1. Trust Boundary & Philosophy

In judicial proceedings and multi-agency intelligence audits, forensic software must not operate as a "black box" that phones home to a centralized server. The **AegisTrace Independent Offline Verifier** is designed from first principles to execute in **hostile, air-gapped environments**:

```
+---------------------------------------------------------------------------------+
|                       AIR-GAPPED JUDICIAL AUDIT BOUNDARY                        |
|                                                                                 |
|  [ Evidence Package ] -----> [ OfflineEvidenceVerifier ] -----> [ Final Verdict ]
|   (.zip or directory)             (12-Pillar Engine)             (VERIFIED/INVALID)
|                                           |                                     |
|             +-----------------------------+-----------------------------+       |
|             |                             |                             |       |
|      [ NO Sockets ]                 [ NO Database ]               [ NO Cloud ]  |
|      (socket.socket                 (Zero SQL or                 (Zero KMS or   |
|       disabled)                      driver imports)              API endpoints)|
+---------------------------------------------------------------------------------+
```

### Absolute Isolation Guarantees
1. **Network Denial:** The verifier makes zero network socket calls. In automated tests (`test_airgap_and_scale.py`), monkeypatching `socket.socket` to raise exceptions proves zero egress.
2. **Database Independence:** The verifier requires no database credentials, drivers, or active connections. Even if the originating application database is corrupted or wiped, verification succeeds with identical results.
3. **Deterministic Canonical Re-Execution:** Every hash, Merkle root, DAG topological sort, and ML-DSA-65 signature is re-evaluated locally from raw bitstreams.

---

## 2. Command-Line Interface (CLI) Usage

The standalone CLI entrypoint is `aegistrace_verify.py`:

```bash
# Verify a directory package
python aegistrace_verify.py /path/to/evidence_package_dir/

# Verify a compressed ZIP archive package
python aegistrace_verify.py /path/to/evidence_package.zip

# Enforce tenant isolation check
python aegistrace_verify.py /path/to/evidence_package.zip --tenant tenant-defense-01

# Output machine-readable JSON for integration into court case management systems
python aegistrace_verify.py /path/to/evidence_package.zip --json
```

---

## 3. Human-Readable Audit Report Example

```
======================================================================
AEGISTRACE FORENSIC EVIDENCE PACKAGE VERIFICATION REPORT
======================================================================
Package ID:           pkg_case_golden_leak_2026_20260927150000
Overall Status:       VERIFIED
Verified At:          2026-09-27T15:00:05.123456+00:00
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

## 4. Machine-Readable JSON Schema (`--json`)

```json
{
  "package_id": "pkg_case_golden_leak_2026_20260927150000",
  "overall_status": "VERIFIED",
  "verified_at": "2026-09-27T15:00:05.123456+00:00",
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
  "decision_consistent": true,
  "step_details": {
    "pillar_1_structure": {"passed": true},
    "pillar_2_manifest_signature": {"passed": true},
    "pillar_3_merkle_root": {"passed": true},
    "pillar_4_object_hashes": {"passed": true, "object_count": 9},
    "pillar_5_dag": {"passed": true},
    "pillar_6_receipt_signatures": {"passed": true, "receipt_count": 1},
    "pillar_7_historical_keys": {"passed": true},
    "pillar_8_ledger_proofs": {"passed": true, "proof_count": 1},
    "pillar_9_watermark_binding": {"passed": true},
    "pillar_10_lineage": {"passed": true},
    "pillar_11_custody_chain": {"passed": true, "event_count": 6},
    "pillar_12_decision": {"passed": true}
  },
  "errors": [],
  "warnings": []
}
```

---

## 5. Security & Failure Handling

| Fault Condition | Verifier Response | Exit Code |
|---|---|---|
| Tenant mismatch (`--tenant foreign`) | `TENANT_ISOLATION_VIOLATION` | 4 |
| Manifest altered | `MANIFEST_DIGEST_MISMATCH` | 4 |
| Manifest signature corrupted | `MANIFEST_SIGNATURE_INVALID` | 4 |
| Merkle leaf modified | `MERKLE_ROOT_MISMATCH` | 4 |
| Recipient signature forged | `Receipt 'rec_id' invalid ML-DSA-65 signature` | 4 |
| Key used after revocation | `POST_REVOCATION_REJECTION` | 4 |
| DLT quorum shortfall | `Quorum threshold not met: 1 valid votes < 2 required` | 4 |
| Dependency DAG cycle injected | `DAG_CYCLE_DETECTED` | 4 |
| Fabricated attribution principal | `ABSTAINED decision must NOT attribute a principal` | 4 |
